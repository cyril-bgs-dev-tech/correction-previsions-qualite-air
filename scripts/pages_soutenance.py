#!/usr/bin/env python3
"""Les pages de soutenance — carte de France, détections mensuelles, cartes de chaleur.

Ce que ces pages doivent permettre
------------------------------------
Un lecteur non technique doit voir, sans lire un tableau :

1. **où** la correction gagne — une carte de France, un point par station, coloré par le
   gain de RMSE contre la chaîne concurrente ;
2. **quand** elle attrape les épisodes — pour chaque mois, les alertes **attrapées** et
   **ratées** des deux systèmes ;
3. **la forme** de l'erreur — des cartes de chaleur station × jour à échelle identique,
   où un épisode manqué reste vert là où la vérité est rouge.

Le protocole affiché
----------------------
**Origine glissante** : pour le mois `M`, entraînement sur tout ce qui précède `M`. La
station est **connue** et sa mémoire est utilisée — c'est le cas d'usage d'exploitation sur
réseau existant, pas la généralisation à un site non instrumenté. Les chiffres du double
aveugle sont ailleurs et plus bas ; les confondre serait la faute la plus facile ici.

Échéance **J0** : la seule où les membres d'ensemble existent, donc la seule où la chaîne
concurrente est mesurable à armes égales.

Le recalage d'amplitude, appliqué **aux deux** systèmes
--------------------------------------------------------
Minimiser la RMSE impose `σx = r·σy` : l'optimum RMSE est sous-dispersé, donc franchit
rarement un seuil haut. Les panneaux d'alerte appliquent donc un recalage d'amplitude —
moments des mois **antérieurs**, station évaluée **exclue** — à notre modèle **et** à la
chaîne concurrente. Recaler seulement le nôtre fausserait la comparaison.

Parti pris graphique
----------------------
La rampe officielle de l'**indice européen de qualité de l'air** est la couche sémantique :
c'est elle que le public voit sur les bulletins, et elle est réservée aux bandes d'indice.
Le chrome de la page ne la concurrence jamais — encre bleu-vert froide, accent azur pour
notre système, brique pour le contre-accent. Les chiffres sont en chasse fixe à chiffres
tabulaires : c'est un document de mesure, pas un dépliant.

Aucune ressource externe n'est chargée : ni tuile, ni police, ni script distant.

Usage  : python3 scripts/pages_soutenance.py [--hybride] [--sortie reports/html]
Sortie : <sortie>/index.html et <sortie>/<polluant>.html
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from decomposition_information import moments_anterieurs  # noqa: E402
from heatmap_annuelle import couleur_continue  # noqa: E402
from tableau_comparatif import BANDES, NOM_BANDE, NOM_POLLUANT, SEUIL, classe  # noqa: E402

POLLUANTS = ("O3", "NO2", "PM10", "PM25")
COURT = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}
# La rampe officielle de l'indice européen de qualité de l'air. Réservée à la sémantique
# d'indice — jamais réutilisée pour le chrome de la page.
BANDE_COULEUR = ["#50f0e6", "#50ccaa", "#f0e641", "#ff5050", "#960032"]
ISSUE = {"neutre": "#1b2027", "attrapee": "#2f9e5f", "ratee": "#d8402f",
         "fausse": "#e0a03c"}
GRIS_MANQUANT = (46, 50, 56)
MIN_JOURS_STATION = 60
CONTOUR = RACINE / "data/processed/contour_france.json"
MOIS_COURT = ["jan", "fév", "mar", "avr", "mai", "juin", "juil", "août", "sep",
              "oct", "nov", "déc"]


# ── Chargement ───────────────────────────────────────────────────────────────
def charger(polluant: str, horizon: int) -> pd.DataFrame | None:
    f = RACINE / f"data/processed/predictions/production_{polluant}_h{horizon}.parquet"
    if not f.exists():
        return None
    d = pd.read_parquet(f)
    d["jour"] = pd.to_datetime(d["jour"])
    return d.sort_values(["jour", "station_id"]).reset_index(drop=True)


def hybrider(d: pd.DataFrame) -> pd.DataFrame:
    """Combinaison **chronologique** de notre modèle et de la chaîne concurrente.

    Pour le mois `M`, les coefficients viennent des moindres carrés sur les mois
    **antérieurs à M**. Aucun réajustement des modèles de base : c'est un empilage,
    déployable dès lors que les deux chaînes tournent. Les premiers mois, sans historique,
    reçoivent notre modèle seul — comportement d'une mise en service progressive.
    """
    d = d.copy()
    d["hybride"] = d["nous"].to_numpy()
    for m in np.sort(d["mois"].unique()):
        hist = d[d["mois"] < m]
        if len(hist) < 3_000:
            continue
        A = np.column_stack([hist["nous"], hist["aasqa"], np.ones(len(hist))])
        beta, *_ = np.linalg.lstsq(A, hist["valeur"].to_numpy(), rcond=None)
        cur = (d["mois"] == m).to_numpy()
        B = np.column_stack([d.loc[cur, "nous"], d.loc[cur, "aasqa"],
                             np.ones(int(cur.sum()))])
        d.loc[cur, "hybride"] = np.clip(B @ beta, 0, None)
    return d


def recaler(d: pd.DataFrame, colonnes: list[str],
            saison: int | None = 1) -> pd.DataFrame:
    """Recalage d'amplitude sans fuite — mois antérieurs, station évaluée exclue.

    `saison=1` restreint l'étalon aux mois du **même régime** (mois calendaire ± 1 mois,
    années antérieures). Un étalon tous mois confondus dilue juillet dans les hivers et
    laisse la prévision sous-dispersée là où les seuils se franchissent : mesuré sur
    l'ozone, σ prédite/σ observée valait **0,903** en juillet 2026 contre **0,972** après
    correction, et l'écart de détections face à la chaîne concurrente passait de −13 à +62.

    ⚠️ Le recalage ne crée **aucune information** : à budget d'alertes égal les comptes ne
    bougent pas. Il place le point de fonctionnement au bon endroit, rien de plus — et il
    est appliqué **aux deux systèmes**, sans quoi la comparaison serait truquée.
    """
    mom = moments_anterieurs(d, ["valeur"] + colonnes, saison=saison)
    mu_y, sd_y = mom["valeur"]
    d = d.copy()
    for c in colonnes:
        mu_x, sd_x = mom[c]
        ech = np.where(sd_x > 1e-9, sd_y / np.maximum(sd_x, 1e-9), 1.0)
        r = mu_y + ech * (d[c].to_numpy() - mu_x)
        d[f"{c}_r"] = np.clip(np.where(np.isfinite(r), r, d[c].to_numpy()), 0, None)
    return d


def chaine_concurrente(polluant: str, horizon: int) -> dict:
    """Nom **réel** de la configuration retenue pour la chaîne concurrente.

    ⚠️ `production_reelle.py` choisit la MEILLEURE des quatre configurations accessibles au
    concurrent — médiane CAMS ou CHIMERE+MOCAGE, avec ou sans krigeage du biais récent.
    Continuer d'afficher « CHIMERE+MOCAGE » serait un nom faux : mesuré le 04/08 à
    couverture pleine, CHIMERE+MOCAGE européen est **42 % pire que la médiane CAMS** sur
    l'ozone, et la référence retenue est donc souvent l'autre.

    On lit le nom dans le rapport produit par l'ajustement, jamais on ne le devine.
    """
    f = RACINE / f"reports/production_reelle_{polluant}_h{horizon}.csv"
    defaut = {"nom": "meilleure configuration disponible", "nomme": None, "rmse_nomme": None}
    if not f.exists():
        return defaut
    t = pd.read_csv(f)
    au_mieux = t[t["systeme"].str.contains("au MIEUX", na=False)]
    nomme = t[t["systeme"].str.contains("NOMMÉE", na=False)]
    if au_mieux.empty:
        return defaut
    return {"nom": au_mieux["systeme"].iloc[0].split("— ", 1)[-1],
            "nomme": (nomme["systeme"].iloc[0].split("— ", 1)[-1] if not nomme.empty
                      else None),
            "rmse_nomme": (float(nomme["rmse"].iloc[0]) if not nomme.empty else None),
            "rmse": float(au_mieux["rmse"].iloc[0])}


def couverture_membres(polluant: str, d: pd.DataFrame) -> dict:
    """Part des lignes évaluées où CHIMERE **et** MOCAGE existent vraiment.

    ⚠️ La chaîne concurrente est construite sur CHIMERE+MOCAGE **quand ils existent**, et
    retombe sur la médiane CAMS sinon. Ce repli est nécessaire — sans lui la référence
    sortirait `nan` — mais il change ce que la ligne mesure, et le taire reviendrait à
    nommer « CHIMERE+MOCAGE » un système qui n'en contient pas.

    Les membres n'ont pas la même profondeur selon le polluant : mesuré le 03/08, sur la
    fenêtre 2025-2026 ils couvrent 47 % des mois pour l'ozone, 37 % pour le NO₂, **16 %
    pour les PM2,5** et **aucun** pour les PM10.
    """
    import glob as _glob

    fs = sorted(_glob.glob(str(RACINE / "data/processed/meteo/"
                               f"membres_metropole_{polluant.lower()}_*.parquet")))
    vide = {"part": 0.0, "dernier": None, "nom": "médiane CAMS + krigeage du biais récent"}
    if not fs:
        return vide
    m = pd.concat([pd.read_parquet(f, columns=["station_id", "timestamp_utc",
                                               "chimere", "mocage"]) for f in fs],
                  ignore_index=True)
    if not {"chimere", "mocage"} <= set(m.columns):
        return vide
    m = m.dropna(subset=["chimere", "mocage"])
    if m.empty:
        return vide
    m["jour"] = pd.to_datetime(m["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    dispo = set(zip(m["station_id"], m["jour"]))
    couvert = np.fromiter((k in dispo for k in zip(d["station_id"],
                                                   pd.to_datetime(d["jour"]))),
                          dtype=bool, count=len(d))
    part = 100 * float(couvert.mean())
    dernier = (pd.PeriodIndex(m["timestamp_utc"], freq="M").astype(str).max()
               if len(m) else None)
    nom = ("CHIMERE+MOCAGE + krigeage du biais récent" if part >= 99 else
           f"CHIMERE+MOCAGE quand disponible ({part:.0f} % des lignes), "
           f"médiane CAMS sinon, + krigeage du biais récent")
    return {"part": part, "dernier": dernier, "nom": nom}


# ── Statistiques ─────────────────────────────────────────────────────────────
def stats_stations(d: pd.DataFrame, col: str) -> pd.DataFrame:
    g = d.groupby("station_id")
    o = g.apply(lambda t: pd.Series({
        "n": float(len(t)),
        "rmse_nous": float(np.sqrt(np.mean((t[col] - t["valeur"]) ** 2))),
        "rmse_aasqa": float(np.sqrt(np.mean((t["aasqa"] - t["valeur"]) ** 2)))}),
        include_groups=False).reset_index()
    o = o[o["n"] >= MIN_JOURS_STATION].copy()
    o["gain"] = 100 * (1 - o["rmse_nous"] / o["rmse_aasqa"])
    return o


def stats_mensuelles(d: pd.DataFrame, polluant: str, c_nous: str,
                     c_aasqa: str) -> pd.DataFrame:
    t = pd.DataFrame({
        "mois": d["mois"].to_numpy(),
        "obs": classe(d["valeur"].to_numpy(), polluant) >= 3,
        "n": classe(d[c_nous].to_numpy(), polluant) >= 3,
        "a": classe(d[c_aasqa].to_numpy(), polluant) >= 3})
    g = t.groupby("mois")
    s = pd.DataFrame({
        "observees": g["obs"].sum(),
        "att_nous": g.apply(lambda x: int((x["n"] & x["obs"]).sum()),
                            include_groups=False),
        "att_aasqa": g.apply(lambda x: int((x["a"] & x["obs"]).sum()),
                             include_groups=False),
        "faux_nous": g.apply(lambda x: int((x["n"] & ~x["obs"]).sum()),
                             include_groups=False),
        "faux_aasqa": g.apply(lambda x: int((x["a"] & ~x["obs"]).sum()),
                              include_groups=False)}).reset_index()
    return s.reset_index(drop=True)


# ── Images matricielles ──────────────────────────────────────────────────────
def _png(rvb: np.ndarray, echelle: int) -> str:
    from PIL import Image

    img = Image.fromarray(rvb.astype("uint8"), mode="RGB")
    if echelle > 1:
        img = img.resize((img.width * echelle, img.height * echelle), Image.NEAREST)
    t = io.BytesIO()
    img.save(t, format="PNG", optimize=True)
    return base64.b64encode(t.getvalue()).decode()


def _reperes(jours: list) -> str:
    premiers = sorted({pd.Timestamp(x).replace(day=1) for x in jours})
    pas = 1 if len(premiers) <= 15 else 2
    index = {pd.Timestamp(x): i for i, x in enumerate(jours)}
    out = []
    for x in premiers:
        if x not in index:
            continue
        pct = 100 * index[x] / len(jours)
        if x.month == 1:
            out.append(f'<span class="an" style="left:{pct:.3f}%">{x:%Y}</span>')
        elif (x.month - 1) % pas == 0:
            out.append(f'<span class="mo" style="left:{pct:.3f}%">'
                       f'{MOIS_COURT[x.month - 1]}</span>')
        else:
            out.append(f'<span class="tk" style="left:{pct:.3f}%"></span>')
    return "".join(out)


def panneau(rvb: np.ndarray, titre: str, sous: str, jours: list,
            legende: str = "", echelle: int = 3) -> str:
    largeur = max(820, int(len(jours) * 2.6))
    return (f'<figure class="pan"><figcaption><b>{html.escape(titre)}</b>'
            f'<span>{sous}</span></figcaption>'
            f'<div class="defile"><div class="cadre" style="min-width:{largeur}px">'
            f'<img src="data:image/png;base64,{_png(rvb, echelle)}" '
            f'alt="{html.escape(titre)}"><div class="rep">{_reperes(jours)}</div>'
            f'</div></div>{legende}</figure>')


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def matrice(d: pd.DataFrame, col: str, stations: list, jours: list) -> np.ndarray:
    p = d.pivot_table(index="station_id", columns="jour", values=col, aggfunc="mean")
    return p.reindex(index=stations, columns=jours).to_numpy(dtype="float64")


def rvb_valeurs(m: np.ndarray, seuil: float) -> np.ndarray:
    r = couleur_continue(m / seuil)
    r[~np.isfinite(m)] = GRIS_MANQUANT
    return r


def rvb_bandes(m: np.ndarray, polluant: str) -> np.ndarray:
    cl = classe(np.nan_to_num(m, nan=-1.0), polluant)
    r = np.zeros(m.shape + (3,), dtype="float64")
    for k, h in enumerate(BANDE_COULEUR):
        r[cl == k] = _hex(h)
    r[~np.isfinite(m)] = GRIS_MANQUANT
    return r


def rvb_issues(obs: np.ndarray, pred: np.ndarray, polluant: str) -> np.ndarray:
    ao = classe(np.nan_to_num(obs, nan=-1.0), polluant) >= 3
    ap = classe(np.nan_to_num(pred, nan=-1.0), polluant) >= 3
    r = np.zeros(obs.shape + (3,), dtype="float64")
    r[:] = _hex(ISSUE["neutre"])
    r[ao & ap] = _hex(ISSUE["attrapee"])
    r[ao & ~ap] = _hex(ISSUE["ratee"])
    r[~ao & ap] = _hex(ISSUE["fausse"])
    r[~np.isfinite(obs) | ~np.isfinite(pred)] = GRIS_MANQUANT
    return r


# ── La carte ─────────────────────────────────────────────────────────────────
def _projection(emprise, largeur, hauteur, marge=14):
    x0, y0, x1, y1 = emprise
    ech = min((largeur - 2 * marge) / (x1 - x0), (hauteur - 2 * marge) / (y1 - y0))
    ox = (largeur - (x1 - x0) * ech) / 2
    oy = (hauteur - (y1 - y0) * ech) / 2

    def proj(px, py):
        return ox + (px - x0) * ech, hauteur - oy - (py - y0) * ech
    return proj, ech


def couleur_gain(g: float) -> str:
    """Divergente autour de 0 — azur si nous gagnons, brique si la chaîne gagne."""
    t = max(-1.0, min(1.0, float(g) / 35.0))
    neutre = np.array([214, 216, 212], dtype=float)
    cible = np.array([26, 92, 148]) if t >= 0 else np.array([160, 58, 38])
    c = (neutre + (cible - neutre) * (abs(t) ** 0.7)).astype(int)
    return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"


def carte(pts: list[dict], largeur: int = 640, hauteur: int = 620) -> str:
    if not CONTOUR.exists():
        return ('<p class="vide">Contour de France absent — lancer '
                '<code>python3 scripts/contour_france.py</code>.</p>')
    geo = json.loads(CONTOUR.read_text(encoding="utf-8"))
    x0, y0, x1, y1 = geo["emprise"]
    proj, ech = _projection((x0, y0, x1, y1), largeur, hauteur)
    chemins = []
    for anneau in geo["chemins"]:
        a = np.asarray(anneau, dtype="float64")
        sx, sy = proj(a[:, 0], a[:, 1])          # une seule projection, celle des stations
        pts_txt = " ".join(f"{u:.1f},{v:.1f}" for u, v in zip(sx, sy))
        chemins.append(f'<polygon points="{pts_txt}"/>')

    cercles = []
    for p in sorted(pts, key=lambda z: abs(z["gain"])):
        cx, cy = proj(p["x"], p["y"])
        r = 3.0 + 4.2 * min(abs(p["gain"]) / 30.0, 1.0)
        t = (f'{p["nom"]} — {p["commune"]}\n{p["type"]} · {p["n"]:,} jours\n'
             f'gain {p["gain"]:+.1f} %  (RMSE {p["rmse_nous"]:.2f} contre '
             f'{p["rmse_aasqa"]:.2f} µg/m³)')
        cercles.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" '
                       f'fill="{couleur_gain(p["gain"])}">'
                       f'<title>{html.escape(t)}</title></circle>')
    ex, _ = proj(x0 + 100_000, y0)
    dx, dy = proj(x0, y0)
    barre = (f'<g class="ech"><line x1="{dx + 10:.0f}" y1="{hauteur - 26:.0f}" '
             f'x2="{dx + 10 + (ex - dx):.0f}" y2="{hauteur - 26:.0f}"/>'
             f'<text x="{dx + 10:.0f}" y="{hauteur - 32:.0f}">100 km</text></g>')
    return (f'<svg viewBox="0 0 {largeur} {hauteur}" class="carte" role="img" '
            f'aria-label="Gain par station sur la France métropolitaine">'
            f'<g class="terre">{"".join(chemins)}</g>'
            f'<g class="stations">{"".join(cercles)}</g>{barre}</svg>')


def legende_gain() -> str:
    pas = [-30, -15, 0, 15, 30]
    cases = "".join(f'<i style="background:{couleur_gain(v)}"></i>' for v in pas)
    return (f'<div class="lg"><span class="lgt">chaîne AASQA meilleure</span>'
            f'<div class="rampe">{cases}</div>'
            f'<span class="lgt">notre système meilleur</span></div>'
            f'<div class="lgs">−30 %　　−15　　0　　+15　　+30 % de RMSE · '
            f'la taille du point suit l\'ampleur du gain</div>')


# ── Détections mensuelles ────────────────────────────────────────────────────
def barres(stats: pd.DataFrame, largeur: int = 640, hauteur: int = 300) -> str:
    s = stats[stats["observees"] > 0]
    if s.empty:
        return ('<p class="vide">Aucun épisode de classe ≥ 3 observé sur la fenêtre — '
                'rien à détecter, donc rien à comparer.</p>')
    n = len(s)
    gauche, bas, haut_marge = 44, 46, 16
    hmax = max(1, int(s["observees"].max()))
    lw = (largeur - gauche - 12) / n
    base = hauteur - bas
    ech = (base - haut_marge) / hmax
    el = []
    for k in range(5):
        v = hmax * k / 4
        y = base - v * ech
        el.append(f'<line class="gr" x1="{gauche}" y1="{y:.1f}" x2="{largeur - 8}" '
                  f'y2="{y:.1f}"/>')
        el.append(f'<text class="ax" x="{gauche - 7}" y="{y + 3.5:.1f}" '
                  f'text-anchor="end">{v:.0f}</text>')
    for i, (_, r) in enumerate(s.iterrows()):
        x = gauche + i * lw
        bw = (lw - 7) / 2
        el.append(f'<rect class="fond" x="{x + 1:.1f}" y="{haut_marge - 6:.0f}" '
                  f'width="{lw - 3:.1f}" height="{base - haut_marge + 6:.1f}"/>')
        h_obs = r["observees"] * ech
        el.append(f'<rect class="obs" x="{x + 2:.1f}" y="{base - h_obs:.1f}" '
                  f'width="{lw - 5:.1f}" height="{h_obs:.1f}"/>')
        for k, (cle, cls, lib) in enumerate(
                (("att_aasqa", "ba", "chaîne AASQA"), ("att_nous", "bn", "notre système"))):
            h = r[cle] * ech
            bx = x + 2.5 + k * (bw + 1)
            el.append(
                f'<rect class="{cls}" x="{bx:.1f}" y="{base - h:.1f}" '
                f'width="{bw:.1f}" height="{h:.1f}" rx="1.5">'
                f'<title>{r["mois"]} · {lib} : {int(r[cle])} attrapées sur '
                f'{int(r["observees"])} — {int(r["observees"]) - int(r[cle])} ratées'
                f'</title></rect>')
        if n <= 20 or i % 2 == 0:
            el.append(f'<text class="ax" x="{x + lw / 2:.1f}" y="{base + 14:.0f}" '
                      f'text-anchor="middle">{r["mois"][5:]}</text>')
            if r["mois"].endswith("-01") or i == 0:
                el.append(f'<text class="an2" x="{x + lw / 2:.1f}" '
                          f'y="{base + 28:.0f}" text-anchor="middle">'
                          f'{r["mois"][:4]}</text>')
    el.append(f'<line class="ax0" x1="{gauche}" y1="{base}" x2="{largeur - 8}" '
              f'y2="{base}"/>')
    return (f'<svg viewBox="0 0 {largeur} {hauteur}" class="barres" role="img" '
            f'aria-label="Épisodes attrapés par mois">{"".join(el)}</svg>'
            f'<div class="lg2">'
            f'<span><i class="sw obs"></i>épisodes observés</span>'
            f'<span><i class="sw ba"></i>attrapés — chaîne AASQA</span>'
            f'<span><i class="sw bn"></i>attrapés — notre système</span></div>')


# ── Habillage ────────────────────────────────────────────────────────────────
CSS = """
:root{
 --encre:#0e1216; --papier:#f5f6f3; --fond:#0e1216; --sur:#141a21; --sur2:#1a212a;
 --texte:#e8eaec; --doux:#98a1ab; --trait:#242c36;
 --azur:#4d92cf; --azur-p:#2f6da4; --brique:#c9634a; --vert:#3aa96a;
 --or:#e0a03c; --rouge:#d8402f;
 --mono:ui-monospace,SFMono-Regular,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
 --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
}
@media (prefers-color-scheme:light){
 :root{--fond:#f5f6f3;--sur:#ffffff;--sur2:#eceee9;--texte:#141a1f;--doux:#5b656f;
  --trait:#dcdfd9;--azur:#2f6da4;--azur-p:#1a5c94;--brique:#a9482f;}
}
:root[data-theme="dark"]{--fond:#0e1216;--sur:#141a21;--sur2:#1a212a;--texte:#e8eaec;
 --doux:#98a1ab;--trait:#242c36;--azur:#4d92cf;--azur-p:#2f6da4;--brique:#c9634a;}
:root[data-theme="light"]{--fond:#f5f6f3;--sur:#ffffff;--sur2:#eceee9;--texte:#141a1f;
 --doux:#5b656f;--trait:#dcdfd9;--azur:#2f6da4;--azur-p:#1a5c94;--brique:#a9482f;}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--fond);color:var(--texte);font-family:var(--sans);
 font-size:15px;line-height:1.62;-webkit-font-smoothing:antialiased}
.page{max-width:1200px;margin:0 auto;padding:38px 22px 84px}
.eyebrow{font-size:.7rem;letter-spacing:.13em;text-transform:uppercase;color:var(--doux);
 font-weight:640;margin:0 0 10px}
h1{font-size:clamp(1.55rem,3.2vw,2.1rem);line-height:1.15;letter-spacing:-.025em;
 font-weight:680;margin:0 0 10px;text-wrap:balance}
h2{font-size:1.12rem;letter-spacing:-.012em;font-weight:660;margin:0 0 2px;
 text-wrap:balance}
.chapo{color:var(--doux);max-width:70ch;margin:0 0 28px}
.chapo b{color:var(--texte);font-weight:620}
.avert{border-left:2px solid var(--or);background:color-mix(in srgb,var(--or) 8%,transparent);
 padding:11px 15px;margin:20px 0;font-size:.88rem;border-radius:0 6px 6px 0}
.avert b{color:var(--or)}
nav.ong{display:flex;gap:2px;flex-wrap:wrap;margin:0 0 26px;border-bottom:1px solid var(--trait)}
.ong button{appearance:none;border:0;background:none;color:var(--doux);font:inherit;
 font-size:.92rem;font-weight:580;padding:10px 16px;cursor:pointer;
 border-bottom:2px solid transparent;margin-bottom:-1px}
.ong button:hover{color:var(--texte)}
.ong button[aria-selected="true"]{color:var(--texte);border-bottom-color:var(--azur)}
.ong button:focus-visible{outline:2px solid var(--azur);outline-offset:-2px;border-radius:3px}
.vue[hidden]{display:none}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:1px;
 background:var(--trait);border:1px solid var(--trait);border-radius:10px;overflow:hidden;
 margin:0 0 26px}
.kpi{background:var(--sur);padding:15px 17px}
.kpi .k{font-size:.68rem;letter-spacing:.09em;text-transform:uppercase;color:var(--doux);
 font-weight:640;display:block;margin-bottom:5px}
.kpi .v{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:1.62rem;
 font-weight:600;letter-spacing:-.02em;line-height:1.1;display:block}
.kpi .s{font-size:.78rem;color:var(--doux);display:block;margin-top:3px}
.pos{color:var(--azur)} .neg{color:var(--brique)}
.duo{display:grid;grid-template-columns:minmax(0,0.92fr) minmax(0,1.08fr);gap:26px;
 align-items:start}
@media(max-width:940px){.duo{grid-template-columns:1fr}}
.bloc{background:var(--sur);border:1px solid var(--trait);border-radius:12px;padding:18px 19px}
.bloc>h2+p{color:var(--doux);font-size:.85rem;margin:2px 0 14px;max-width:62ch}
.carte{width:100%;height:auto;display:block}
.terre polygon{fill:var(--sur2);stroke:var(--trait);stroke-width:.5;stroke-linejoin:round}
.stations circle{stroke:color-mix(in srgb,var(--fond) 60%,transparent);stroke-width:.6;
 cursor:crosshair}
.stations circle:hover{stroke:var(--texte);stroke-width:1.5}
.ech line{stroke:var(--doux);stroke-width:1.4}
.ech text{fill:var(--doux);font-size:10px;font-family:var(--mono)}
.barres{width:100%;height:auto;display:block}
.barres .gr{stroke:var(--trait);stroke-width:1}
.barres .ax0{stroke:var(--doux);stroke-width:1}
.barres .ax{fill:var(--doux);font-size:9.5px;font-family:var(--mono)}
.barres .an2{fill:var(--doux);font-size:9px;font-family:var(--mono);opacity:.75}
.barres .fond{fill:color-mix(in srgb,var(--doux) 7%,transparent)}
.barres .obs{fill:color-mix(in srgb,var(--doux) 24%,transparent)}
.barres .ba{fill:var(--brique)} .barres .bn{fill:var(--azur)}
.lg{display:flex;align-items:center;gap:10px;margin:12px 0 4px;font-size:.76rem;
 color:var(--doux)}
.rampe{display:flex;border-radius:3px;overflow:hidden;flex:0 0 150px}
.rampe i{display:block;height:11px;flex:1}
.lgs{font-size:.74rem;color:var(--doux);font-family:var(--mono)}
.lg2{display:flex;gap:15px;flex-wrap:wrap;margin-top:11px;font-size:.78rem;color:var(--doux)}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;
 vertical-align:-1px}
.sw.obs{background:color-mix(in srgb,var(--doux) 34%,transparent)}
.sw.ba{background:var(--brique)} .sw.bn{background:var(--azur)}
table{border-collapse:collapse;width:100%;font-size:.85rem;margin-top:6px}
th,td{padding:7px 10px;border-bottom:1px solid var(--trait);text-align:right}
th:first-child,td:first-child{text-align:left}
thead th{color:var(--doux);font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;
 font-weight:640}
td.n{font-family:var(--mono);font-variant-numeric:tabular-nums}
tbody tr:last-child td{border-bottom:0}
.enveloppe{overflow-x:auto}
.pan{margin:0 0 26px}
.pan figcaption{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;margin-bottom:7px}
.pan figcaption b{font-size:.97rem;font-weight:640}
.pan figcaption span{color:var(--doux);font-size:.82rem}
.defile{overflow-x:auto;border:1px solid var(--trait);border-radius:9px;background:var(--sur)}
.cadre{position:relative}
.cadre img{display:block;width:100%;height:auto;image-rendering:pixelated}
.rep{position:relative;height:20px;font-size:9.5px;color:var(--doux);font-family:var(--mono)}
.rep span{position:absolute;top:3px;transform:translateX(-50%);white-space:nowrap}
.rep .an{font-weight:700;color:var(--texte)}
.rep .tk{width:1px;height:5px;background:var(--trait);top:0}
.echelle{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px;font-size:.78rem;
 color:var(--doux)}
.vide{color:var(--doux);font-size:.88rem;font-style:italic}
.liens{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0 0}
.liens a{display:inline-block;padding:8px 15px;border:1px solid var(--trait);border-radius:8px;
 color:var(--texte);text-decoration:none;font-size:.88rem;font-weight:580;background:var(--sur)}
.liens a:hover{border-color:var(--azur);color:var(--azur)}
a{color:var(--azur)}
footer{margin-top:58px;padding-top:20px;border-top:1px solid var(--trait);color:var(--doux);
 font-size:.78rem;line-height:1.7}
@media(prefers-reduced-motion:no-preference){.kpi,.bloc{transition:border-color .18s}}
"""

JS = """
document.querySelectorAll('nav.ong').forEach(function(nav){
  nav.addEventListener('click',function(e){
    var b=e.target.closest('button'); if(!b) return;
    var hote=nav.parentElement;
    nav.querySelectorAll('button').forEach(function(x){
      x.setAttribute('aria-selected', String(x===b));});
    hote.querySelectorAll('.vue').forEach(function(v){
      v.hidden = (v.dataset.cle !== b.dataset.cle);});
  });
});
"""


def enveloppe(titre: str, corps: str, source: str) -> str:
    # Document complet et autonome : ces pages s'ouvrent en `file://`, où l'absence de
    # `<meta charset>` casse tous les accents sans le moindre avertissement.
    return (f'<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{html.escape(titre)}</title>\n<style>{CSS}</style>\n</head>\n<body>'
            f'<div class="page">{corps}\n<footer>'
            f'Observations : réseau national de surveillance (LCSQA / AASQA). '
            f'Modèles de chimie-transport : CAMS — Copernicus Atmosphere Monitoring '
            f'Service. Contours administratifs : IGN Admin Express via '
            f'<code>france-geojson</code>, licence ODbL.<br>'
            f'Protocole à origine glissante, échéance J0, {source}. '
            f'Page produite par <code>scripts/pages_soutenance.py</code> — aucune '
            f'ressource externe n\'est chargée.'
            f'</footer></div>\n<script>{JS}</script>\n</body>\n</html>')


def kpi(cle: str, valeur: str, sous: str, classe_v: str = "") -> str:
    return (f'<div class="kpi"><span class="k">{cle}</span>'
            f'<span class="v {classe_v}">{valeur}</span>'
            f'<span class="s">{sous}</span></div>')


# ── Assemblage des pages ─────────────────────────────────────────────────────
def _stations_geo() -> pd.DataFrame:
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "nom", "commune", "type_station",
                                  "x_l93", "y_l93"])
    return st.drop_duplicates("station_id").dropna(subset=["x_l93", "y_l93"])


def bloc_polluant(polluant: str, d: pd.DataFrame, col: str, nom_nous: str,
                  geo: pd.DataFrame, lien_page: str | None) -> tuple[str, dict]:
    """Le panneau d'un polluant : synthèse, carte, détections mensuelles."""
    o = d["valeur"].to_numpy()
    r_nous = float(np.sqrt(np.mean((d[col] - o) ** 2)))
    r_aasqa = float(np.sqrt(np.mean((d["aasqa"] - o) ** 2)))
    gain = 100 * (1 - r_nous / r_aasqa)

    sm = stats_mensuelles(d, polluant, f"{col}_r", "aasqa_r")
    tot_obs = int(sm["observees"].sum())
    tot_n, tot_a = int(sm["att_nous"].sum()), int(sm["att_aasqa"].sum())
    fx_n, fx_a = int(sm["faux_nous"].sum()), int(sm["faux_aasqa"].sum())

    ss = stats_stations(d, col).merge(geo, on="station_id", how="left").dropna(
        subset=["x_l93", "y_l93"])
    part = 100 * float((ss["gain"] > 0).mean()) if len(ss) else float("nan")
    pts = [{"x": float(r.x_l93), "y": float(r.y_l93), "gain": float(r.gain),
            "nom": str(r.nom), "commune": str(r.commune),
            "type": str(r.type_station), "n": int(r.n),
            "rmse_nous": float(r.rmse_nous), "rmse_aasqa": float(r.rmse_aasqa)}
           for r in ss.itertuples()]

    # ⚠️ Comparer les épisodes attrapés à seuil fixe suppose que les deux systèmes
    # émettent le même nombre d'alertes. Ce n'est pas le cas : nos prédictions sont moins
    # dispersées, donc franchissent moins souvent. Le chiffre qui décide est donc celui-ci
    # — **à volume d'alertes égal**, invariant par toute transformation monotone.
    est_crit = classe(o, polluant) >= 3
    budget = int((classe(d["aasqa_r"].to_numpy(), polluant) >= 3).sum())
    ordre = np.argsort(-d[f"{col}_r"].to_numpy(), kind="stable")
    egal = int(est_crit[ordre[:budget]].sum()) if budget else 0
    ecart_eg = (100 * (egal / tot_a - 1)) if tot_a else float("nan")

    strip = (
        '<div class="strip">'
        + kpi("Erreur — gain contre la chaîne AASQA", f"{gain:+.1f} %",
              f"RMSE {r_nous:.2f} contre {r_aasqa:.2f} µg/m³",
              "pos" if gain > 0 else "neg")
        + kpi("Épisodes attrapés à volume d'alertes égal", f"{egal}",
              f"contre {tot_a} — mêmes {budget:,} alertes émises"
              + (f", soit {ecart_eg:+.0f} %" if tot_a else ""),
              "pos" if egal >= tot_a else "neg")
        + kpi("Épisodes attrapés au seuil", f"{tot_n}",
              f"contre {tot_a} pour la chaîne, sur {tot_obs} observés",
              "pos" if tot_n >= tot_a else "neg")
        + kpi("Fausses alertes", f"{fx_n}",
              f"contre {fx_a} pour la chaîne", "pos" if fx_n <= fx_a else "neg")
        + kpi("Stations améliorées", f"{part:.0f} %",
              f"sur {len(ss)} stations d'au moins {MIN_JOURS_STATION} jours",
              "pos" if part > 50 else "neg")
        + '</div>')

    court = COURT[polluant]
    cm = couverture_membres(polluant, d)
    ch = chaine_concurrente(polluant, 1)
    cm["nom"] = ch["nom"]
    avert = ""
    if d["mois"].max() < "2026-01":
        avert += (f'<div class="avert"><b>Fenêtre écourtée.</b> Les prédictions '
                  f'{court} s\'arrêtent en {d["mois"].max()} : {d["mois"].nunique()} mois '
                  f'affichés au lieu des 19 attendus.</div>')
    # ⚠️ Nommer la chaîne concurrente « CHIMERE+MOCAGE » quand la majorité des lignes n'en
    # contient pas serait un nom faux — et un nom faux se propage plus loin que le code.
    # ⚠️ Dire quelle configuration porte réellement la chaîne concurrente, et ce que coûte
    # la stratégie **nommée** — sinon le lecteur croit qu'on l'a affrontée alors qu'on a
    # affronté mieux qu'elle.
    if ch.get("nomme") and ch.get("rmse_nomme") and ch["nomme"] != ch["nom"]:
        ecart = 100 * (1 - ch["rmse"] / ch["rmse_nomme"])
        avert += (
            f'<div class="avert"><b>Quelle chaîne concurrente, exactement.</b> La stratégie '
            f'nommée — <i>{html.escape(ch["nomme"])}</i> — donne une RMSE de '
            f'{ch["rmse_nomme"]:.2f} µg/m³ en configuration <b>européenne</b> à 0,1° sans '
            f'assimilation. La configuration <b>la meilleure</b> accessible au concurrent '
            f'avec nos entrées est <i>{html.escape(ch["nom"])}</i>, à {ch["rmse"]:.2f} — '
            f'soit <b>{ecart:.0f} % de mieux</b>. C\'est elle qui sert de référence ici : '
            f'se mesurer à la version faible de l\'adversaire gonflerait notre gain sans '
            f'rien prouver. Leur chaîne réelle tourne en version nationale assimilée, donc '
            f'au moins aussi bonne que celle retenue.</div>')
    if cm["part"] < 99:
        avert += (
            f'<div class="avert"><b>Ce que contient vraiment la chaîne concurrente.</b> '
            f'Les membres d\'ensemble CHIMERE et MOCAGE ne couvrent que '
            f'<b>{cm["part"]:.0f} %</b> des journées-station évaluées'
            + (f' (extraits jusqu\'à {cm["dernier"]})' if cm["dernier"] else '')
            + f'. Sur le reste, la chaîne est ancrée sur la <b>médiane CAMS</b> — le repli '
              f'qu\'appliquerait aussi une chaîne opérationnelle privée d\'un de ses '
              f'modèles. Le krigeage du biais récent, lui, s\'applique partout. '
              f'Compléter l\'extraction des membres est une reprise de téléchargement, '
              f'pas une limite de méthode.</div>')

    corps = (
        f'{avert}{strip}'
        f'<div class="duo">'
        f'<section class="bloc"><h2>Où la correction gagne</h2>'
        f'<p>Un point par station, coloré par le gain de RMSE contre la chaîne AASQA. '
        f'Survolez un point pour le détail.</p>'
        f'{carte(pts)}{legende_gain()}</section>'
        f'<section class="bloc"><h2>Épisodes attrapés, mois par mois</h2>'
        f'<p>Un épisode est une journée-station en classe « mauvais » ou pire au '
        f'sous-indice {court}. Chaîne concurrente : {cm["nom"]}. Les deux systèmes '
        f'sont recalibrés en amplitude à l\'identique — le cadran est accessible '
        f'aux deux.</p>'
        f'{barres(sm)}</section></div>')
    if lien_page:
        corps += (f'<div class="liens"><a href="{lien_page}">Cartes de chaleur '
                  f'temporelles — {court} →</a></div>')
    return corps, {"polluant": polluant, "gain": gain, "rmse_nous": r_nous,
                   "rmse_aasqa": r_aasqa, "att_nous": tot_n, "att_aasqa": tot_a,
                   "att_budget_egal": egal, "budget_alertes": budget,
                   "observes": tot_obs, "faux_nous": fx_n, "faux_aasqa": fx_a,
                   "stations": len(ss), "part_amelioree": part,
                   "mois": d["mois"].nunique(), "n": len(d), "nom_nous": nom_nous,
                   "couverture_membres_pct": cm["part"], "chaine": cm["nom"]}


def page_polluant(polluant: str, d: pd.DataFrame, col: str, nom_nous: str,
                  source: str, nom_aasqa: str) -> str:
    stations = (d.groupby("station_id")["valeur"].median()
                .sort_values(ascending=False).index.tolist())
    jours = sorted(pd.to_datetime(d["jour"].unique()))
    obs = matrice(d, "valeur", stations, jours)
    nous = matrice(d, col, stations, jours)
    aasqa = matrice(d, "aasqa", stations, jours)
    nous_r = matrice(d, f"{col}_r", stations, jours)
    aasqa_r = matrice(d, "aasqa_r", stations, jours)
    seuil = SEUIL[polluant]
    court = COURT[polluant]

    ech_bandes = ('<div class="echelle">' + "".join(
        f'<span><i class="sw" style="background:{BANDE_COULEUR[i]}"></i>'
        f'{NOM_BANDE[i].lower()} — {int(a)}'
        f'{"+" if np.isinf(b) else f"–{int(b)}"} µg/m³</span>'
        for i, (a, b) in enumerate(BANDES[polluant])) + '</div>')
    ech_issues = ('<div class="echelle">'
                  f'<span><i class="sw" style="background:{ISSUE["attrapee"]}"></i>'
                  f'épisode attrapé</span>'
                  f'<span><i class="sw" style="background:{ISSUE["ratee"]}"></i>'
                  f'épisode <b>raté</b></span>'
                  f'<span><i class="sw" style="background:{ISSUE["fausse"]}"></i>'
                  f'fausse alerte</span>'
                  f'<span><i class="sw" style="background:{ISSUE["neutre"]}"></i>'
                  f'journée calme, correctement prévue</span></div>')

    sous = (f'{len(stations)} stations × {len(jours)} jours · '
            f'{jours[0]:%b %Y} → {jours[-1]:%b %Y}')
    corps = (
        f'<p class="eyebrow">Cartes de chaleur temporelles · échéance J0</p>'
        f'<h1>{NOM_POLLUANT[polluant]} — la forme de l\'erreur, jour par jour</h1>'
        f'<p class="chapo">Une ligne par station, une colonne par jour, les stations '
        f'triées par niveau médian décroissant. Les trois premiers panneaux partagent '
        f'<b>exactement la même échelle</b>, ancrée sur le seuil de {seuil:.0f} µg/m³ : '
        f'un épisode manqué reste vert là où la vérité est rouge. '
        f'<a href="index.html">← retour à la carte et aux détections</a></p>'

        f'<h2>1 · Les concentrations</h2>'
        f'<p class="chapo">Échelle divergente ancrée au seuil réglementaire — c\'est lui '
        f'qui décide d\'une procédure, pas la moyenne.</p>'
        + panneau(rvb_valeurs(obs, seuil), "Observé — la vérité terrain", sous, jours)
        + panneau(rvb_valeurs(aasqa, seuil), f"Chaîne AASQA — {nom_aasqa}",
                  "mêmes stations, mêmes jours, même échelle", jours)
        + panneau(rvb_valeurs(nous, seuil), f"Notre système — {nom_nous}",
                  "mêmes stations, mêmes jours, même échelle", jours)

        + f'<h2>2 · Les bandes de l\'indice — ce que le public verrait</h2>'
        f'<p class="chapo">Couleurs officielles de l\'indice européen de qualité de '
        f'l\'air. Le premier panneau est le <b>déclenchement parfait</b> : ce qu\'un '
        f'système sans erreur aurait publié.</p>'
        + panneau(rvb_bandes(obs, polluant), "Déclenchement parfait — bandes observées",
                  sous, jours, ech_bandes)
        + panneau(rvb_bandes(aasqa_r, polluant), "Chaîne AASQA — bandes prédites",
                  "après recalage d'amplitude, sans fuite", jours)
        + panneau(rvb_bandes(nous_r, polluant), f"Notre système — bandes prédites",
                  "après recalage d'amplitude, sans fuite", jours)

        + f'<h2>3 · Les alertes — attrapées, ratées, fausses</h2>'
        f'<p class="chapo">Même information, recodée par <b>issue</b>. Le rouge est ce '
        f'qui coûte : un épisode réel que le système n\'a pas annoncé.</p>'
        + panneau(rvb_issues(obs, aasqa_r, polluant),
                  "Chaîne AASQA — issues des alertes", sous, jours, ech_issues)
        + panneau(rvb_issues(obs, nous_r, polluant),
                  f"Notre système — issues des alertes", sous, jours))
    return enveloppe(f"{NOM_POLLUANT[polluant]} — cartes de chaleur", corps, source)


def page_index(blocs: list[tuple[str, dict]], hybride: bool, source: str) -> str:
    resumes = [r for _, r in blocs]
    onglets = "".join(
        f'<button role="tab" data-cle="{r["polluant"]}" '
        f'aria-selected="{"true" if i == 0 else "false"}">{COURT[r["polluant"]]}</button>'
        for i, r in enumerate(resumes))
    vues = "".join(
        f'<div class="vue" data-cle="{r["polluant"]}"{"" if i == 0 else " hidden"}>'
        f'{corps}</div>' for i, (corps, r) in enumerate(blocs))

    lignes = "".join(
        f'<tr><td>{NOM_POLLUANT[r["polluant"]]}</td>'
        f'<td class="n">{r["rmse_aasqa"]:.2f}</td><td class="n">{r["rmse_nous"]:.2f}</td>'
        f'<td class="n {"pos" if r["gain"] > 0 else "neg"}">{r["gain"]:+.1f} %</td>'
        f'<td class="n">{r["att_aasqa"]}</td>'
        f'<td class="n {"pos" if r["att_budget_egal"] >= r["att_aasqa"] else "neg"}">'
        f'{r["att_budget_egal"]}</td>'
        f'<td class="n">{r["observes"]}</td>'
        f'<td class="n">{r["stations"]}</td><td class="n">{r["mois"]}</td></tr>'
        for r in resumes)

    nom = ("hybridation — notre modèle **et** la chaîne AASQA combinés"
           if hybride else "notre meilleur système déployable")
    titre = ("Hybridation contre chaîne AASQA" if hybride
             else "Notre système contre la chaîne AASQA")
    intro = (
        '<p class="chapo">Les deux chaînes sont combinées par empilage '
        '<b>chronologique</b> : pour chaque mois, les coefficients viennent des mois '
        'antérieurs uniquement. Aucun réajustement des modèles de base — c\'est '
        'déployable dès lors que les deux tournent.</p>' if hybride else
        '<p class="chapo">Notre système utilise le terrain, le calendrier, la typologie '
        'de station, les feux, les <b>six membres</b> de l\'ensemble CAMS, le biais '
        'krigé des voisins et la mémoire du site. <b>ERA5 est exclu</b> : c\'est une '
        'réanalyse, indisponible à l\'heure d\'émission — l\'inclure donnerait un '
        'plafond, pas une performance.</p>')

    corps = (
        f'<p class="eyebrow">Post-traitement statistique des prévisions CAMS · '
        f'protocole d\'exploitation</p>'
        f'<h1>{titre}</h1>'
        f'{intro}'
        f'<div class="avert"><b>Quel protocole, et ce qu\'il mesure.</b> Origine '
        f'glissante : pour le mois M, le modèle est entraîné sur <b>tout ce qui précède '
        f'M</b>, puis prédit M. La station est connue et sa mémoire utilisée — c\'est le '
        f'cas d\'usage d\'exploitation sur un réseau existant. Ce n\'est <b>pas</b> le '
        f'double aveugle, qui cache aussi la station pour mesurer la généralisation à un '
        f'site non instrumenté ; ses chiffres sont plus bas, et confondre les deux serait '
        f'la faute la plus facile à commettre ici.</div>'
        f'<div class="liens">'
        f'<a href="regions/index.html">Cartes de chaleur <b>par région</b> — '
        f'la maille des AASQA →</a>'
        f'<a href="champ_france.html">Champ spatialisé — <b>France</b> →</a>'
        f'<a href="champ_occitanie.html">Champ — <b>Occitanie</b> →</a>'
        f'<a href="champ_nouvelle-aquitaine.html">Champ — <b>Nouvelle-Aquitaine</b> →</a>'
        f'</div>'
        f'<nav class="ong" role="tablist" style="margin-top:26px">{onglets}</nav>{vues}'
        f'<h2 style="margin-top:42px">Les quatre polluants d\'un coup d\'œil</h2>'
        f'<p class="chapo">Mêmes lignes, même protocole, même échéance J0.</p>'
        f'<div class="enveloppe"><table><thead><tr><th>Polluant</th>'
        f'<th>RMSE chaîne</th><th>RMSE nous</th><th>Gain</th>'
        f'<th>Attrapés — chaîne</th><th>Attrapés — nous, à volume égal</th>'
        f'<th>Épisodes observés</th>'
        f'<th>Stations</th><th>Mois</th></tr></thead><tbody>{lignes}</tbody></table></div>'
        f'<p class="chapo" style="margin-top:14px;font-size:.85rem">Les épisodes sont '
        f'comptés après <b>recalage d\'amplitude des deux systèmes</b> : minimiser '
        f'l\'erreur quadratique impose une sous-dispersion qui fait manquer les seuils, '
        f'et ce réglage est accessible aux deux chaînes.</p>')
    return enveloppe(titre, corps, source)


def main(horizon: int, hybride: bool, sortie: str) -> int:
    dossier = RACINE / sortie
    dossier.mkdir(parents=True, exist_ok=True)
    geo = _stations_geo()
    col = "hybride" if hybride else "nous"
    nom_nous = ("hybridation modèle appris + chaîne AASQA" if hybride
                else "modèle appris, toutes familles déployables")
    blocs, resumes = [], []
    for p in POLLUANTS:
        d = charger(p, horizon)
        if d is None or d.empty:
            print(f"  {p} : aucune prédiction — polluant ignoré", flush=True)
            continue
        if hybride:
            d = hybrider(d)
        d = recaler(d, [col, "aasqa"])
        source = (f'{d["mois"].min()} → {d["mois"].max()}')
        corps, r = bloc_polluant(p, d, col, nom_nous, geo,
                                 None if hybride else f"{p}.html")
        blocs.append((corps, r))
        resumes.append(r)
        f = dossier / f"{p}.html"
        f.write_text(page_polluant(p, d, col, nom_nous, source,
                                   couverture_membres(p, d)["nom"]), encoding="utf-8")
        print(f"  {p:5s} · gain {r['gain']:+6.2f} % · épisodes {r['att_nous']:4d} "
              f"contre {r['att_aasqa']:4d} sur {r['observes']:4d} · "
              f"{f.stat().st_size / 1024:6.0f} ko", flush=True)

    if not blocs:
        raise SystemExit("aucun polluant exploitable — lancer d'abord "
                         "scripts/production_reelle.py")
    couv = f"{min(r['mois'] for r in resumes)}–{max(r['mois'] for r in resumes)} mois"
    idx = dossier / "index.html"
    idx.write_text(page_index(blocs, hybride, couv), encoding="utf-8")
    pd.DataFrame(resumes).to_csv(
        RACINE / f"reports/pages_soutenance{'_hybride' if hybride else ''}.csv",
        index=False)
    ou = idx.relative_to(RACINE) if idx.is_relative_to(RACINE) else idx
    print(f"\nÉcrit : {ou} ({idx.stat().st_size / 1024:.0f} ko) et "
          f"{len(blocs)} page(s) polluant")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--horizon", type=int, default=1)
    a.add_argument("--hybride", action="store_true",
                   help="comparer la chaîne AASQA à l'hybridation des deux méthodes")
    a.add_argument("--sortie", default="reports/html")
    n = a.parse_args()
    raise SystemExit(main(n.horizon, n.hybride, n.sortie))
