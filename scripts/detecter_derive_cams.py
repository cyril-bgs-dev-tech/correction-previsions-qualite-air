"""Aurait-on vu la rupture CAMS le jour où elle s'est produite ?

Usage : python scripts/detecter_derive_cams.py [--horizon 1]
Sorties : reports/DERIVE_CAMS.md, reports/derive_cams_{polluant}.csv

**Le test est rétrospectif mais pas complaisant** : la saisonnalité et le seuil sont
établis sur les douze premiers mois **seuls**, puis appliqués tels quels à la suite.
Rien de ce qui suit le 1er août 2024 n'entre dans le calibrage. C'est exactement ce
qu'aurait fait un indicateur mis en service ce jour-là.

Ce qu'on cherche à savoir, dans l'ordre :

1. Combien de **fausses alertes** l'indicateur produit-il sur une année normale ? Sans
   cette réponse, une détection ne vaut rien : un indicateur qui crie tous les mois
   finirait ignoré, et il aurait « détecté » la rupture par hasard.
2. **Quel délai** entre la bascule et l'alarme ?
3. Le déplacement est-il **partagé par tout le réseau** — signature d'un changement de
   système — ou régional, donc plutôt météorologique ?
4. Est-il **concordant entre polluants** ? Une version change plusieurs espèces à la
   fois ; un épisode en touche une ou deux.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import derive  # noqa: E402
from fit_mos import paires_cams_observations  # noqa: E402

POLLUANTS = ("O3", "NO2", "PM25")

# Un an de référence : le minimum pour que la saisonnalité ne soit pas extrapolée.
DEBUT_SUIVI = pd.Timestamp("2024-08-01", tz="UTC")

# Dates publiées par ECMWF. cy49r1 bascule le 12/11/2024 et U9 suit le 13/11 ; U8b est
# daté de « juin 2024 » sans jour précis — d'où son absence de cette liste.
BASCULES = {
    "cy49r1 (cycle global)": pd.Timestamp("2024-11-12", tz="UTC"),
    "U9 (CAMS régional)": pd.Timestamp("2024-11-13", tz="UTC"),
}


def _fenetre(paires: pd.DataFrame, debut: pd.Timestamp, n_jours: int) -> pd.DataFrame:
    fin = debut + pd.Timedelta(days=n_jours)
    return paires[(paires["timestamp_utc"] >= debut) & (paires["timestamp_utc"] < fin)]


def comparaison_interannuelle(paires: pd.DataFrame, debut: pd.Timestamp,
                              n_jours: int = 45) -> dict:
    """Compare une fenêtre à **la même fenêtre calendaire de l'année précédente**.

    **Comparer « avant » et « après » à l'intérieur d'une même saison est fautif** : sur
    l'ozone, le biais décroît fortement de l'automne à l'hiver, si bien qu'un
    déplacement purement saisonnier s'y lit comme une dérive. La seule comparaison
    propre disponible est d'une année sur l'autre, aux mêmes jours de l'année.

    Et le biais seul ne dit pas d'où vient le déplacement. On sépare donc :
    la moyenne **observée** — qui bouge si la météorologie a changé — et la moyenne
    **prévue**, qui bouge si le modèle a changé. Si les deux se déplacent ensemble,
    c'est la saison ou la météo ; si seule la prévision bouge, c'est le modèle.
    """
    recente = _fenetre(paires, debut, n_jours)
    passee = _fenetre(paires, debut - pd.Timedelta(days=365), n_jours)
    if recente.empty or passee.empty:
        return {}

    def par_station(bloc):
        return (bloc["cams"] - bloc["valeur"]).groupby(bloc["station_id"]).mean()

    deplacement = (par_station(recente) - par_station(passee)).dropna()
    return {
        "n_stations": int(len(deplacement)),
        "deplacement_median": float(deplacement.median()),
        "concordance": derive.part_stations_concordantes(deplacement),
        "observe_passe": float(passee["valeur"].mean()),
        "observe_recent": float(recente["valeur"].mean()),
        "prevu_passe": float(passee["cams"].mean()),
        "prevu_recent": float(recente["cams"].mean()),
    }


def analyser(polluant: str, horizon: int) -> dict:
    paires = paires_cams_observations(polluant, horizon).dropna(
        subset=["valeur", "cams"])

    surveillance = derive.surveiller(paires, debut_suivi=DEBUT_SUIVI)
    journalier = surveillance.journalier
    reference = journalier["date"] < DEBUT_SUIVI

    # Fausses alertes de la période de référence, au seuil retenu : c'est le taux que
    # l'indicateur garantit, et il doit être annoncé avec sa durée de calibrage.
    trace_reference = derive.cusum(journalier.loc[reference, "z"].to_numpy(),
                                   h=surveillance.seuil)

    # **L'écart à la date documentée, signé.** Un délai suppose que la bascule est la
    # cause ; un écart signé laisse les données dire si l'alarme la précède — auquel cas
    # la bascule n'explique rien.
    premiere = (None if surveillance.alarmes.empty
                else surveillance.alarmes["date"].iloc[0])
    ecarts_bascules = {
        nom: None if premiere is None else int((premiere - date).days)
        for nom, date in BASCULES.items()
    }

    comparaison = (comparaison_interannuelle(paires, premiere)
                   if premiere is not None else {})

    journalier.to_csv(RACINE / f"reports/derive_cams_{polluant}.csv", index=False)

    return {
        "polluant": polluant,
        "seuil": surveillance.seuil,
        "sigma": surveillance.ecart_type_reference,
        "n_reference": surveillance.meta["n_reference"],
        "n_suivi": surveillance.meta["n_suivi"],
        "fausses_alertes_reference": len(trace_reference.alarmes),
        "alarmes": surveillance.alarmes,
        "premiere_alarme": premiere,
        "ecarts_bascules": ecarts_bascules,
        **comparaison,
    }


def lire_deplacement(r: dict) -> str:
    """Formule le verdict du discriminant observation / prévision.

    Trois cas, et le troisième est celui qu'on oublie : la prévision peut avoir
    **manqué** un déplacement réel. Cela creuse le biais exactement comme un changement
    de code, mais la cause est extérieure au modèle — et la conclusion opérationnelle
    n'est pas la même.
    """
    d_obs = r["observe_recent"] - r["observe_passe"]
    d_prev = r["prevu_recent"] - r["prevu_passe"]

    # **Comparer les déplacements en relatif, pas en absolu.** Un premier essai testait
    # `|Δprévu| > 2 × |Δobservé|` : sur les PM2,5 il concluait « seule la prévision
    # bouge » alors que l'observation avait gagné 1,8 µg/m³ sur un niveau de 9,1 — soit
    # 20 %. Les trois polluants n'ont pas le même ordre de grandeur ; un seuil en µg/m³
    # ne peut pas les départager.
    rel_obs = abs(d_obs) / max(r["observe_passe"], 1e-9)
    rel_prev = abs(d_prev) / max(r["prevu_passe"], 1e-9)

    if rel_obs < 0.05 and rel_prev > 0.10:
        verdict = ("**seule la prévision se déplace** — difficile à expliquer autrement "
                   "que par le modèle lui-même")
    elif rel_obs > rel_prev:
        verdict = ("le **réel s'est déplacé et la prévision ne l'a pas suivi** — "
                   "insuffisance du modèle révélée par des conditions inhabituelles, "
                   "plutôt que changement de code")
    else:
        verdict = ("**les deux se déplacent**, la prévision "
                   f"{rel_prev / max(rel_obs, 1e-9):.1f} fois plus en relatif : "
                   "une cause extérieure a pu s'ajouter à un changement du modèle, "
                   "sans qu'on puisse les séparer")

    return (f"**{r['polluant']}** — observé {d_obs:+.1f} µg/m³ ({100 * rel_obs:.0f} %), "
            f"prévu {d_prev:+.1f} µg/m³ ({100 * rel_prev:.0f} %) : {verdict}.")


def rediger(resultats: list[dict], horizon: int) -> str:
    lignes = [
        "# Voir la dérive du modèle amont le jour où elle se produit",
        "",
        "## Le problème, tel qu'il s'est posé",
        "",
        "L'erreur de CAMS s'est déplacée à l'automne 2024 : sur l'ozone, le biais de "
        "novembre passe de **+4,47 en 2023 à +12,43 en 2024**, et le R² de 0,493 à 0,187. "
        "Rien dans les fichiers ne le signale — mêmes attributs, même grille, même "
        "producteur d'un bout à l'autre de l'archive, aucun numéro de version.",
        "",
        "Ce projet l'a découvert **plus de dix-huit mois plus tard**, et par accident : "
        "en vérifiant qu'une validation inter-annuelle avait un sens.",
        "",
        "C'est cet écart de dix-huit mois qui est le problème, pas le déplacement "
        "lui-même. Un modèle amont évolue ; ce qui coûte, c'est de ne pas savoir quand.",
        "",
        "C'est un problème pour toute structure qui exploite CAMS, et il est double : "
        "une correction apprise sur l'ancien régime devient partiellement fausse, et un "
        "prévisionniste qui accorde sa confiance au modèle continue de la lui accorder "
        "sans raison.",
        "",
        "## Ce qui est mesuré ici",
        "",
        f"Horizon **J+{horizon}**. La saisonnalité du biais et le seuil d'alarme sont "
        "établis sur **les douze premiers mois seuls** (2023-08 → 2024-07), puis "
        "appliqués tels quels à la suite. **Rien de ce qui suit le 1er août 2024 "
        "n'entre dans le calibrage** — c'est ce qu'aurait fait un indicateur mis en "
        "service ce jour-là.",
        "",
        "Trois précautions, dont chacune suffirait à rendre l'indicateur inutilisable :",
        "",
        "- **Déssaisonnaliser d'abord.** Le biais de CAMS suit un cycle annuel de grande "
        "amplitude ; un seuil posé sur le biais brut se déclencherait chaque printemps.",
        "- **Cumuler plutôt que seuiller.** Un changement de version produit un décalage "
        "*petit et permanent*, pas un pic. Un seuil instantané le rate ; une somme "
        "cumulée (CUSUM) l'accumule jusqu'à devenir indiscutable.",
        "- **Calibrer le seuil sur les données.** Le biais journalier est autocorrélé — "
        "les régimes météo durent plusieurs jours — et les seuils tabulés sous "
        "indépendance donneraient bien plus de fausses alertes qu'annoncé.",
        "",
        "## Le résultat",
        "",
        "| Polluant | σ du biais | Seuil | Fausses alertes (12 mois) | 1ʳᵉ alarme | "
        "Écart à la bascule U9 |",
        "|---|---|---|---|---|---|",
    ]

    for r in resultats:
        ecart = r["ecarts_bascules"].get("U9 (CAMS régional)")
        if r["premiere_alarme"] is None:
            detection, texte_ecart = "**aucune**", "—"
        else:
            detection = r["premiere_alarme"].strftime("%d/%m/%Y")
            texte_ecart = (f"**{ecart:+d} j**"
                           + (" *(avant)*" if ecart < 0 else " *(après)*"))
        lignes.append(
            f"| {r['polluant']} | {r['sigma']:.2f} µg/m³ | {r['seuil']:.1f} σ | "
            f"**{r['fausses_alertes_reference']}** | {detection} | {texte_ecart} |"
        )

    lignes += [
        "",
        "La colonne qui donne sa valeur aux autres est celle des **fausses alertes** : le "
        "seuil est le plus petit qui n'en produise aucune sur les douze mois de "
        "référence. Sans elle, une détection ne prouverait rien — un indicateur qui crie "
        "tous les mois finit par « détecter » n'importe quoi.",
        "",
        "## Le résultat que je n'attendais pas",
        "",
        "**Les trois alarmes précèdent la bascule documentée**, de huit à dix-neuf jours, "
        "et sur trois polluants indépendants. La mise à niveau U9 du 13 novembre 2024 "
        "**n'explique donc pas** le déplacement : il avait déjà commencé.",
        "",
        "C'est l'inverse de ce que j'avais écrit après avoir trouvé les dates dans la "
        "documentation ECMWF. J'avais une rupture mesurée sur des moyennes mensuelles, "
        "j'ai trouvé un changement documenté dans le bon mois, et j'ai conclu. Le "
        "découpage mensuel ne pouvait pas distinguer le 24 octobre du 13 novembre ; "
        "l'indicateur journalier le peut, et il dit autre chose.",
        "",
        "> Les rapports `RUPTURE_CAMS.md` et `COURBE_APPRENTISSAGE.md` ont été corrigés "
        "en conséquence. **La cause du déplacement n'est pas établie.**",
        "",
        "## Changement de modèle, ou météorologie ?",
        "",
        "Comparer « avant » et « après » à l'intérieur d'une même saison serait fautif : "
        "le biais de l'ozone décroît fortement de l'automne à l'hiver, et ce déplacement "
        "saisonnier se lirait comme une dérive. La comparaison propre est **d'une année "
        "sur l'autre, aux mêmes jours** — 45 jours à partir de l'alarme, contre la même "
        "fenêtre calendaire de 2023.",
        "",
        "Et le biais seul ne dit pas d'où vient le déplacement. On sépare donc la moyenne "
        "**observée**, qui bouge si la météorologie a changé, de la moyenne **prévue**, "
        "qui bouge si le modèle a changé.",
        "",
        "| Polluant | Stations | Δ biais médian | Concordance | Observé 2023 → 2024 | "
        "Prévu 2023 → 2024 |",
        "|---|---|---|---|---|---|",
    ]
    for r in resultats:
        if "n_stations" not in r:
            continue
        lignes.append(
            f"| {r['polluant']} | {r['n_stations']} | "
            f"{r['deplacement_median']:+.2f} µg/m³ | "
            f"**{100 * r['concordance']:.0f} %** | "
            f"{r['observe_passe']:.1f} → {r['observe_recent']:.1f} "
            f"({r['observe_recent'] - r['observe_passe']:+.1f}) | "
            f"{r['prevu_passe']:.1f} → {r['prevu_recent']:.1f} "
            f"({r['prevu_recent'] - r['prevu_passe']:+.1f}) |"
        )

    lignes += [
        "",
        "**La concordance est élevée partout** — 85 à 98 % des stations se déplacent dans "
        "le même sens. Ce n'est donc pas un épisode local : le phénomène est national. "
        "Cela n'arbitre pas encore entre un changement de modèle et une anomalie "
        "météorologique de grande échelle, qui produiraient tous deux cette signature.",
        "",
        "**Les deux dernières colonnes arbitrent, et pas dans le même sens selon le "
        "polluant :**",
        "",
    ]
    for r in resultats:
        if "n_stations" not in r:
            continue
        lignes.append("- " + lire_deplacement(r))

    lignes += [
        "",
        "**Ce que l'ensemble suggère, sans le démontrer.** Sur le NO₂ le déplacement est "
        "difficile à expliquer autrement que par le modèle : l'observation ne bouge pas "
        "et la prévision monte d'un tiers. Sur l'ozone c'est l'inverse — le réel a "
        "beaucoup baissé et CAMS ne l'a pas suivi, ce qui décrit une **insuffisance du "
        "modèle révélée par un automne atypique** plutôt qu'un changement de code. Deux "
        "mécanismes différents ont donc pu se superposer, et c'est précisément pourquoi "
        "une cause unique ne peut pas être affirmée.",
        "",
        "## Les limites, qui sont réelles",
        "",
        "- **Une seule rupture connue.** On mesure une date de détection, pas une "
        "puissance statistique. Rien ici ne dit ce que l'indicateur ferait d'un "
        "changement deux fois plus petit.",
        "- **Le taux de fausses alertes est calibré sur douze mois**, donc connu à cette "
        "échelle seulement. En exploitation il se réestime chaque année.",
        "- **L'indicateur date le déplacement, il ne l'explique pas.** Il dit *quelque "
        "chose a changé le jour J* ; c'est au service de confronter la date au journal "
        "des mises à niveau du fournisseur.",
        "- **Il suppose un réseau d'observation stable.** Une modification massive du "
        "parc de stations produirait la même signature. La concordance spatiale y aide, "
        "sans lever complètement l'ambiguïté.",
        "",
        "## Ce que cela coûte à mettre en service",
        "",
        "Un calcul par jour sur des données déjà présentes : le biais moyen du réseau, "
        "sa valeur attendue de saison, et deux sommes cumulées. Aucune donnée nouvelle, "
        "aucun modèle à entraîner. La partie difficile n'est pas le calcul — c'est "
        "d'avoir décidé **avant** ce qui compte comme une alerte.",
        "",
        "**Un prérequis, en revanche, est incontournable : douze mois d'historique.** "
        "Avec moins, la saisonnalité doit être extrapolée sur les jours de l'année "
        "jamais observés, et l'indicateur signale ce trou plutôt qu'une dérive. Le "
        "défaut a été trouvé par un test sur série synthétique — sans aucune rupture, "
        "une référence de huit mois déclenchait deux alarmes. Le code refuse désormais "
        "une référence de moins de 330 jours, en nommant la raison.",
        "",
        "## Ce que cet indicateur aurait changé, concrètement",
        "",
        "Le déplacement aurait été signalé **fin octobre 2024** au lieu de juillet 2026. "
        "Ce qu'un service en aurait fait :",
        "",
        "- **interroger le fournisseur** sur un changement en cours, avec une date "
        "précise à lui opposer ;",
        "- **réentraîner la correction** sur la période récente, au lieu de continuer "
        "avec des coefficients appris sur l'ancien régime ;",
        "- **avertir les prévisionnistes** que le biais du modèle a changé de niveau — "
        "l'information la plus directement utile au poste de travail.",
        "",
        "Aucune de ces trois actions ne demande de comprendre la cause. C'est le point : "
        "**savoir *quand* suffit à agir**, et c'est ce que l'indicateur fournit.",
    ]
    return "\n".join(lignes) + "\n"


def main(horizon: int) -> int:
    resultats = []
    for polluant in POLLUANTS:
        print(f"\n── {polluant} ──", flush=True)
        try:
            r = analyser(polluant, horizon)
        except ValueError as exc:
            print(f"  ignoré : {exc}", flush=True)
            continue
        resultats.append(r)
        print(f"  σ {r['sigma']:.2f} · seuil {r['seuil']:.1f} · "
              f"fausses alertes sur la référence : {r['fausses_alertes_reference']}",
              flush=True)
        if r["alarmes"].empty:
            print("  aucune alarme sur la période surveillée", flush=True)
        else:
            for _, a in r["alarmes"].iterrows():
                print(f"  alarme {a['date'].date()} · sens {a['sens']:+d}", flush=True)
        for nom, ecart in r["ecarts_bascules"].items():
            if ecart is not None:
                print(f"  {nom} : alarme {ecart:+d} j "
                      f"({'avant' if ecart < 0 else 'après'} la bascule)", flush=True)
        if "n_stations" in r:
            print(f"  concordance {100 * r['concordance']:.0f} % sur "
                  f"{r['n_stations']} stations · Δbiais {r['deplacement_median']:+.2f}",
                  flush=True)
            print(f"  observé {r['observe_passe']:.1f} → {r['observe_recent']:.1f} · "
                  f"prévu {r['prevu_passe']:.1f} → {r['prevu_recent']:.1f}", flush=True)

    if not resultats:
        print("Aucun polluant exploitable.")
        return 1

    # **Persister les mesures, pas seulement le texte.** Une retouche de rédaction ne
    # doit pas coûter dix minutes de recalcul — et un chiffre du rapport doit pouvoir
    # être retrouvé sans relancer l'analyse.
    pd.DataFrame([{k: v for k, v in r.items()
                   if k not in ("alarmes", "ecarts_bascules")}
                  | {f"ecart_{n}": e for n, e in r["ecarts_bascules"].items()}
                  for r in resultats]).to_csv(
        RACINE / "reports/derive_cams_synthese.csv", index=False)

    (RACINE / "reports/DERIVE_CAMS.md").write_text(rediger(resultats, horizon))
    print("\nÉcrit : reports/DERIVE_CAMS.md")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    args = parseur.parse_args()
    raise SystemExit(main(args.horizon))
