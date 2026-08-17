"""Régresseur RealMLP-TD — l'architecture du notebook, une boucle d'entraînement à nous.

Pourquoi ne PAS sous-classer `RealMLP_TD_Classifier`
-----------------------------------------------------
Sa méthode `fit` fait 230 lignes d'un seul tenant : EMA, ordonnancement du pas et du
dropout, cinq groupes de paramètres, perte d'entropie croisée lissée. La sous-classer
imposerait de la recopier pour changer trois lignes, et une copie de 230 lignes se périme
en silence dès que l'amont bouge. On réutilise donc ce qui a de la valeur —
l'**architecture** `RealMLP` et les aides `apply_schedule` / `get_parameter_groups` — et on
écrit la boucle de régression, courte et lisible.

Ce qui change par rapport au classifieur, et rien d'autre
----------------------------------------------------------
1. `output_dim=1` et pas de `softmax` ;
2. perte de **Huber** plutôt qu'entropie croisée — la cible est un résidu continu, et ce
   dépôt travaille sur des distributions à queue lourde où la MSE se fait dicter par
   quelques journées de pic (§ « les pics sont un problème d'échelle ») ;
3. la prédiction est la **moyenne des `n_ens` têtes**, pas un argmax.

⚠️ **Ce modèle se juge sur l'axe TEMPOREL et en double aveugle.** Le régler sur l'axe
spatial reproduirait le mirage documenté en § 10 septies de `VERITE_DOSSIER` : +4 à +7 %
en spatial, ~0 en temporel. La condition vaut pour l'ensemble du chantier « booster
neuronal », pas seulement pour ce fichier.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from .realmlp import CONFIG, RealMLP, apply_schedule, get_parameter_groups


class RealMLPRegressor:
    """Interface minimale `fit` / `predict`, sur des entrées **numériques** uniquement.

    Le jeu MOS de ce dépôt est entièrement numérique — la typologie de station y est déjà
    encodée en amont par `optuna_mos.typologie`. On n'expose donc pas de chemin catégoriel :
    un paramètre qu'aucun appelant n'emprunte est un paramètre qui n'est jamais testé.
    """

    def __init__(self, cfg: dict | None = None, graine: int = 20260802,
                 patience: int = 3, bavard: bool = False):
        self.cfg = dict(CONFIG) | (cfg or {})
        self.graine, self.patience, self.bavard = graine, patience, bavard
        self.appareil = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── normalisation : médiane/IQR, ajustée sur l'ENTRAÎNEMENT seul ────────────────────
    def _ajuster_echelle(self, X: np.ndarray) -> None:
        # ⚠️ `nanmedian` et `nanpercentile` rendent du **float64** même sur une entrée
        # float32. Sans le cast, la division promeut tout le tenseur en double et
        # `einsum` casse contre des paramètres float32 — avec un message qui désigne la
        # couche d'embedding, pas la ligne fautive. Une promotion de type silencieuse est
        # exactement le genre de défaut que ce dépôt traque ailleurs.
        self.med_ = np.nanmedian(X, axis=0).astype(np.float32)
        q1, q3 = np.nanpercentile(X, [25, 75], axis=0)
        ecart = (q3 - q1).astype(np.float32)
        # Une colonne constante donnerait un écart nul et une division par zéro : on la
        # laisse à l'échelle 1 plutôt que de produire des inf que le réseau propagerait.
        self.ech_ = np.where(ecart > 1e-12, ecart, np.float32(1.0)).astype(np.float32)

    def _mettre_echelle(self, X: np.ndarray) -> torch.Tensor:
        Z = (np.asarray(X, dtype=np.float32) - self.med_) / self.ech_
        # `nan_to_num` APRÈS mise à l'échelle : un NaN d'entrée devient 0 = la médiane,
        # c'est-à-dire « pas d'information », et non une valeur extrême.
        Z = np.nan_to_num(Z, nan=0.0, posinf=0.0, neginf=0.0)
        return torch.from_numpy(np.clip(Z, -10.0, 10.0))

    def fit(self, X, y, X_val=None, y_val=None):
        torch.manual_seed(self.graine)
        np.random.seed(self.graine)
        X = np.asarray(X, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32)
        self._ajuster_echelle(X)

        # La cible est centrée-réduite pour que la perte de Huber garde son seuil au bon
        # endroit : `delta=1` sur des µg/m³ bruts n'aurait pas le même sens d'un polluant
        # à l'autre (RMSE de base de 2,7 à 14,4 selon l'espèce).
        self.y_moy_, self.y_ect_ = float(y.mean()), float(y.std() or 1.0)

        p = self.cfg
        n_ens = p["n_ens"]
        Xt = self._mettre_echelle(X).to(self.appareil)
        yt = torch.from_numpy((y - self.y_moy_) / self.y_ect_).to(self.appareil)
        vide = torch.zeros(len(X), 0, dtype=torch.long, device=self.appareil)

        self.model_ = RealMLP(output_dim=1, cat_dims=[], n_numerical=X.shape[1],
                              cfg=p).to(self.appareil)
        self.model_.softmax_sortie = False

        opt = torch.optim.AdamW(get_parameter_groups(self.model_, p),
                                betas=(p["mom"], p["sq_mom"]))
        perte = nn.HuberLoss(delta=1.0)

        if X_val is not None:
            Xv = self._mettre_echelle(np.asarray(X_val, dtype=np.float32)).to(self.appareil)
            yv = np.asarray(y_val, dtype=np.float32)
            vide_v = torch.zeros(len(Xv), 0, dtype=torch.long, device=self.appareil)

        bs, epochs = p["train_bs"], p["epochs"]
        pas_total = epochs * max(1, len(y) // bs)
        pas, meilleur, sans_gain, etat = 0, np.inf, 0, None

        for ep in range(epochs):
            self.model_.train()
            ordre = torch.randperm(len(y), device=self.appareil)
            for d in range(0, len(y) - bs + 1, bs):
                lot = ordre[d:d + bs]
                avance = pas / max(1, pas_total)
                for g in opt.param_groups:
                    g["lr"] = apply_schedule(g["lr_init"], avance, p["lr_sched"]) \
                        if "lr_init" in g else g["lr"]
                opt.zero_grad()
                sortie = self.model_(Xt[lot], vide[lot]).squeeze(-1)   # (bs, n_ens)
                l = perte(sortie, yt[lot].unsqueeze(1).expand(-1, n_ens))
                l.backward()
                torch.nn.utils.clip_grad_norm_(self.model_.parameters(), p["grad_clip"])
                opt.step()
                pas += 1

            if X_val is not None:
                r = float(np.sqrt(np.mean((self._brut(Xv, vide_v) - yv) ** 2)))
                if self.bavard:
                    print(f"    époque {ep + 1}/{epochs} · RMSE val {r:.4f}", flush=True)
                # ── Arrêt anticipé sur l'ARTEFACT de validation, pas sur la perte
                # d'entraînement : c'est la seule quantité qui puisse contredire
                # l'ajustement.
                if r < meilleur - 1e-6:
                    meilleur, sans_gain = r, 0
                    etat = {k: v.detach().clone() for k, v in self.model_.state_dict().items()}
                else:
                    sans_gain += 1
                    if sans_gain >= self.patience:
                        break
        if etat is not None:
            self.model_.load_state_dict(etat)
        self.rmse_val_ = meilleur if X_val is not None else None
        return self

    def _brut(self, Xt: torch.Tensor, vide: torch.Tensor) -> np.ndarray:
        self.model_.eval()
        with torch.no_grad():
            morceaux = [self.model_(Xt[i:i + 8192], vide[i:i + 8192]).squeeze(-1).mean(1)
                        for i in range(0, len(Xt), 8192)]
        z = torch.cat(morceaux).cpu().numpy()
        return z * self.y_ect_ + self.y_moy_

    def predict(self, X) -> np.ndarray:
        Xt = self._mettre_echelle(np.asarray(X, dtype=np.float32)).to(self.appareil)
        vide = torch.zeros(len(Xt), 0, dtype=torch.long, device=self.appareil)
        return self._brut(Xt, vide)
