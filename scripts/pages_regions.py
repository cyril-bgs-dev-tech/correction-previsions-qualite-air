#!/usr/bin/env python3
"""Le même dossier, mais à la maille **régionale** — celle des AASQA.

Pourquoi cette maille et pas une autre
----------------------------------------
La surveillance de la qualité de l'air en France est portée par des associations
**régionales** agréées : une AASQA par région, fédérées par Atmo France. Un chiffre
national ne dit donc rien à l'agent qui décide — il opère sur **son** territoire, avec
**ses** stations et **ses** épisodes.

Ces pages rejouent exactement les mêmes mesures, région par région : la même correction,
la même chaîne concurrente, les mêmes cartes de chaleur, mais restreintes aux stations du
territoire. Rien n'est réajusté — le modèle reste national, ce qui est le point : il est
entraîné sur toute la France et **évalué chez vous**.

Le rattachement des stations
------------------------------
Point-dans-polygone sur les contours administratifs projetés en Lambert-93, le système des
coordonnées déjà portées par `stations.parquet`. Aucune correspondance par nom de réseau :
les codes `NET-FR0xxA` ne suivent pas les fusions de régions de 2016, et s'y fier
rattacherait des stations à des territoires disparus.

Les stations qui ne tombent dans aucun polygone sont triées en **deux** catégories, jamais
confondues : celles qui sont **hors de l'emprise métropolitaine** — les DOM, légitimement
écartées puisque les contours chargés sont métropolitains — et celles qui sont **dedans**
sans rattachement, qui sont un vrai défaut et **lèvent**.

⚠️ Un identifiant de station comme `FR38003` porte un code de **réseau**, pas de
département : celui-ci désigne La Réunion, pas l'Isère. S'y fier pour deviner un
territoire est une erreur — d'où le point-dans-polygone.

Usage  : python3 scripts/pages_regions.py [--sortie reports/html/regions]
Sortie : <sortie>/index.html et <sortie>/<region>.html
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from contour_france import METROPOLE, douglas_peucker  # noqa: E402
from contexte_departements import (  # noqa: E402
    CSS as CSS_CONTEXTE, charger as charger_contexte, rapport_couverture,
    rendre as rendre_contexte,
)
from figures_territoire import (  # noqa: E402
    CSS as CSS_TERR, bloc_departement as fig_departement, bloc_region as fig_region,
)
from pages_soutenance import (  # noqa: E402
    BANDE_COULEUR, COURT, ISSUE, MIN_JOURS_STATION, NOM_BANDE, POLLUANTS, SEUIL,
    couverture_membres,
    _stations_geo, barres, charger, classe, couleur_gain, enveloppe, kpi, legende_gain,
    matrice, panneau, recaler, rvb_bandes, rvb_issues, rvb_valeurs, stats_mensuelles,
    stats_stations,
)

SOURCE_REGIONS = RACINE / "data/raw/geo/regions.geojson"
SOURCE_DEPARTEMENTS = RACINE / "data/raw/geo/departements.geojson"
MIN_STATIONS = 4        # sous ce seuil, une région n'a pas de carte de chaleur lisible
MIN_STATIONS_DEP = 2    # un département compte peu de stations : le seuil y est plus bas


def ardoise(nom: str) -> str:
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def charger_territoires(source: Path, tolerance: float = 1500.0) -> list[dict]:
    """Contours administratifs projetés en Lambert-93 et simplifiés.

    Le même code sert les **régions** et les **départements** : ce sont deux mailles du
    même référentiel, et en dupliquer le traitement ferait diverger deux rattachements qui
    doivent rester identiques.
    """
    from pyproj import Transformer

    if not source.exists():
        raise SystemExit(f"absent : {source.relative_to(RACINE)}")
    vers93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    brut = json.loads(source.read_text(encoding="utf-8"))
    out = []
    for f in brut["features"]:
        geom = f["geometry"]
        anneaux = (geom["coordinates"] if geom["type"] == "Polygon"
                   else [a for poly in geom["coordinates"] for a in poly])
        chemins, fins = [], []
        for anneau in anneaux:
            a = np.asarray(anneau, dtype="float64")
            if a.ndim != 2 or len(a) < 4:
                continue
            if not (METROPOLE[0] <= a[:, 0].mean() <= METROPOLE[2]
                    and METROPOLE[1] <= a[:, 1].mean() <= METROPOLE[3]):
                continue
            x, y = vers93.transform(a[:, 0], a[:, 1])
            p = np.column_stack([x, y])
            aire = 0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], -1))
                             - np.dot(p[:, 1], np.roll(p[:, 0], -1)))
            if aire < 8e6:
                continue
            s = douglas_peucker(p, tolerance)
            if len(s) >= 4:
                chemins.append(s)
                # ⚠️ La simplification sert le **tracé**, jamais le rattachement : à
                # 1 500 m elle rejette à la mer Sangatte, Pornichet ou Ajaccio, toutes
                # côtières. On garde donc une version fine pour le point-dans-polygone.
                fins.append(douglas_peucker(p, 120.0))
        if chemins:
            out.append({"code": f["properties"]["code"], "nom": f["properties"]["nom"],
                        "ardoise": ardoise(f["properties"]["nom"]),
                        "chemins": chemins, "chemins_fins": fins})
    return out


def charger_regions(tolerance: float = 1500.0) -> list[dict]:
    return charger_territoires(SOURCE_REGIONS, tolerance)


def rattacher(geo: pd.DataFrame, regions: list[dict],
              tolerance_km: float = 15.0) -> pd.DataFrame:
    """Point-dans-polygone. Les orphelines sont **nommées**, pas rapprochées d'office."""
    from matplotlib.path import Path as Chemin

    xy = geo[["x_l93", "y_l93"]].to_numpy()
    code = np.full(len(geo), "", dtype=object)
    for r in regions:
        dedans = np.zeros(len(geo), dtype=bool)
        for c in r["chemins_fins"]:
            dedans |= Chemin(c).contains_points(xy)
        code[dedans & (code == "")] = r["code"]
    g = geo.copy()
    g["region"] = code
    # ⚠️ Deux causes très différentes à un rattachement vide, qu'il faut séparer sous peine
    # de crier au défaut là où il n'y en a pas : une station **outre-mer** est
    # légitimement hors des polygones métropolitains — les identifiants `FR38xxx` sont des
    # codes de **réseau**, pas de département, et désignent ici La Réunion. Une station
    # **dans** l'emprise métropolitaine et non rattachée est, elle, un vrai défaut.
    tous = np.vstack([c for r in regions for c in r["chemins"]])
    bx = (tous[:, 0].min() - 20_000, tous[:, 0].max() + 20_000)
    by = (tous[:, 1].min() - 20_000, tous[:, 1].max() + 20_000)
    vide = g["region"] == ""
    dans_emprise = (g["x_l93"].between(*bx) & g["y_l93"].between(*by))
    hors = g[vide & ~dans_emprise]
    defaut = g[vide & dans_emprise]
    if len(hors):
        print(f"  {len(hors)} station(s) hors métropole — écartées comme prévu "
              f"({', '.join(hors['commune'].dropna().unique()[:4])}…)", flush=True)
    # Restent les stations littorales ou frontalières que le trait de côte du référentiel
    # place de quelques centaines de mètres du mauvais côté — une jetée, un port. On les
    # rattache au contour le PLUS PROCHE, mais seulement sous `tolerance_km`, et on les
    # nomme une par une. Au-delà, c'est une erreur de données et le script lève.
    if len(defaut):
        for i in defaut.index:
            p = np.array([g.at[i, "x_l93"], g.at[i, "y_l93"]])
            meilleur, dist = None, np.inf
            for r in regions:
                for c in r["chemins_fins"]:
                    d = float(np.min(np.hypot(c[:, 0] - p[0], c[:, 1] - p[1])))
                    if d < dist:
                        dist, meilleur = d, r
            if dist <= tolerance_km * 1000:
                g.at[i, "region"] = meilleur["code"]
                print(f"    {g.at[i, 'station_id']} ({g.at[i, 'commune']}) → "
                      f"{meilleur['nom']}, à {dist / 1000:.1f} km du contour", flush=True)
            else:
                raise SystemExit(
                    f"{g.at[i, 'station_id']} ({g.at[i, 'commune']}) est à "
                    f"{dist / 1000:.0f} km de tout contour régional — donnée à vérifier")
        print(f"  {len(defaut)} station(s) littorale(s) rattachées au contour le plus "
              f"proche", flush=True)
    return g


def echelle_pour(n_stations: int) -> int:
    """Une région de six stations donnerait six pixels de haut : on agrandit."""
    return int(np.clip(360 // max(n_stations, 1), 3, 14))


def bloc_region_polluant(polluant: str, d: pd.DataFrame, col: str, nom_aasqa: str,
                         min_stations: int = MIN_STATIONS) -> str | None:
    if d.empty or d["station_id"].nunique() < 2:
        return None
    o = d["valeur"].to_numpy()
    r_nous = float(np.sqrt(np.mean((d[col] - o) ** 2)))
    r_aasqa = float(np.sqrt(np.mean((d["aasqa"] - o) ** 2)))
    gain = 100 * (1 - r_nous / r_aasqa)
    sm = stats_mensuelles(d, polluant, f"{col}_r", "aasqa_r")
    tot_obs = int(sm["observees"].sum())
    tot_n, tot_a = int(sm["att_nous"].sum()), int(sm["att_aasqa"].sum())
    fx_n, fx_a = int(sm["faux_nous"].sum()), int(sm["faux_aasqa"].sum())
    est_crit = classe(o, polluant) >= 3
    budget = int((classe(d["aasqa_r"].to_numpy(), polluant) >= 3).sum())
    ordre = np.argsort(-d[f"{col}_r"].to_numpy(), kind="stable")
    egal = int(est_crit[ordre[:budget]].sum()) if budget else 0

    ss = stats_stations(d, col)
    part = 100 * float((ss["gain"] > 0).mean()) if len(ss) else float("nan")
    court = COURT[polluant]
    strip = ('<div class="strip">'
             + kpi("Gain contre la chaîne AASQA", f"{gain:+.1f} %",
                   f"RMSE {r_nous:.2f} contre {r_aasqa:.2f} µg/m³",
                   "pos" if gain > 0 else "neg")
             + kpi("Épisodes attrapés à volume égal", f"{egal}",
                   f"contre {tot_a} — mêmes {budget:,} alertes · {tot_obs} observés",
                   "pos" if egal >= tot_a else "neg")
             + kpi("Au seuil", f"{tot_n}", f"contre {tot_a} pour la chaîne",
                   "pos" if tot_n >= tot_a else "neg")
             + kpi("Fausses alertes", f"{fx_n}", f"contre {fx_a}",
                   "pos" if fx_n <= fx_a else "neg")
             + kpi("Stations améliorées", f"{part:.0f} %",
                   f"sur {len(ss)} station(s) d'au moins {MIN_JOURS_STATION} jours",
                   "pos" if part > 50 else "neg")
             + '</div>')

    if d["station_id"].nunique() < min_stations:
        return (strip + f'<p class="vide">Seulement {d["station_id"].nunique()} station(s) '
                f'{court} sur ce territoire — les cartes de chaleur ne sont pas tracées, '
                f'elles seraient illisibles et non représentatives.</p>')

    stations = (d.groupby("station_id")["valeur"].median()
                .sort_values(ascending=False).index.tolist())
    jours = sorted(pd.to_datetime(d["jour"].unique()))
    e = echelle_pour(len(stations))
    obs = matrice(d, "valeur", stations, jours)
    seuil = SEUIL[polluant]
    sous = f'{len(stations)} stations × {len(jours)} jours'
    ech_issues = ('<div class="echelle">'
                  f'<span><i class="sw" style="background:{ISSUE["attrapee"]}"></i>'
                  f'attrapé</span>'
                  f'<span><i class="sw" style="background:{ISSUE["ratee"]}"></i>'
                  f'<b>raté</b></span>'
                  f'<span><i class="sw" style="background:{ISSUE["fausse"]}"></i>'
                  f'fausse alerte</span>'
                  f'<span><i class="sw" style="background:{ISSUE["neutre"]}"></i>'
                  f'journée calme, bien prévue</span></div>')
    ech_bandes = ('<div class="echelle">' + "".join(
        f'<span><i class="sw" style="background:{BANDE_COULEUR[i]}"></i>'
        f'{NOM_BANDE[i].lower()}</span>' for i in range(5)) + '</div>')

    return (strip
            + f'<h2>Concentrations — même échelle pour les trois</h2>'
            + panneau(rvb_valeurs(obs, seuil), "Observé", sous, jours, "", e)
            + panneau(rvb_valeurs(matrice(d, "aasqa", stations, jours), seuil),
                      f"Chaîne AASQA — {nom_aasqa}", "", jours, "", e)
            + panneau(rvb_valeurs(matrice(d, col, stations, jours), seuil),
                      "Notre système", "", jours, "", e)
            + f'<h2>Bandes de l\'indice — ce que le public verrait</h2>'
            + panneau(rvb_bandes(obs, polluant), "Déclenchement parfait — observé",
                      sous, jours, ech_bandes, e)
            + panneau(rvb_bandes(matrice(d, "aasqa_r", stations, jours), polluant),
                      "Chaîne AASQA", "après recalage d'amplitude", jours, "", e)
            + panneau(rvb_bandes(matrice(d, f"{col}_r", stations, jours), polluant),
                      "Notre système", "après recalage d'amplitude", jours, "", e)
            + f'<h2>Issues des alertes</h2>'
            + panneau(rvb_issues(obs, matrice(d, "aasqa_r", stations, jours), polluant),
                      "Chaîne AASQA", sous, jours, ech_issues, e)
            + panneau(rvb_issues(obs, matrice(d, f"{col}_r", stations, jours), polluant),
                      "Notre système", sous, jours, "", e)
            + f'<h2>Épisodes attrapés, mois par mois</h2>{barres(sm)}')


def carte_regions(regions: list[dict], gains: dict, largeur: int = 620,
                  hauteur: int = 610) -> str:
    tous = np.vstack([c for r in regions for c in r["chemins"]])
    x0, y0 = tous[:, 0].min(), tous[:, 1].min()
    x1, y1 = tous[:, 0].max(), tous[:, 1].max()
    marge = 14
    ech = min((largeur - 2 * marge) / (x1 - x0), (hauteur - 2 * marge) / (y1 - y0))
    ox = (largeur - (x1 - x0) * ech) / 2
    oy = (hauteur - (y1 - y0) * ech) / 2
    el = []
    for r in regions:
        g = gains.get(r["code"])
        coul = couleur_gain(g) if g is not None else "var(--sur2)"
        polys = []
        for c in r["chemins"]:
            sx = ox + (c[:, 0] - x0) * ech
            sy = hauteur - oy - (c[:, 1] - y0) * ech
            polys.append('<polygon points="'
                         + " ".join(f"{u:.1f},{v:.1f}" for u, v in zip(sx, sy)) + '"/>')
        t = (f'{r["nom"]}\n' + (f'gain moyen {g:+.1f} % de RMSE' if g is not None
                                else 'aucune station exploitable'))
        el.append(f'<a href="{r["ardoise"]}.html" class="reg" style="--c:{coul}">'
                  f'<title>{html.escape(t)}</title>{"".join(polys)}</a>')
    return (f'<svg viewBox="0 0 {largeur} {hauteur}" class="carte" role="img" '
            f'aria-label="Régions, colorées par le gain moyen">'
            f'<g class="regions">{"".join(el)}</g></svg>')



def page_territoire(nom: str, code: str, jeux: dict, compositions: dict, cle: str,
                    eyebrow: str, retours: str, min_st: int,
                    supplement: str = "") -> tuple[str, dict] | None:
    """Une page de territoire — régionale ou départementale, même contenu.

    Les deux mailles répondent à la même question et doivent donc être produites par le
    même code : deux implémentations divergeraient au premier correctif, et la comparaison
    entre échelles cesserait d'être valide.
    """
    blocs, lignes = [], []
    for p, d in jeux.items():
        dt = d[d[cle] == code]
        corps = bloc_region_polluant(p, dt, "nous", compositions[p], min_st)
        if corps is None:
            continue
        o = dt["valeur"].to_numpy()
        g = 100 * (1 - float(np.sqrt(np.mean((dt["nous"] - o) ** 2)))
                   / float(np.sqrt(np.mean((dt["aasqa"] - o) ** 2))))
        lignes.append({"polluant": p, "gain": g, "n": len(dt),
                       "stations": dt["station_id"].nunique()})
        blocs.append((p, corps))
    if not blocs:
        return None
    onglets = "".join(
        f'<button role="tab" data-cle="{p}" '
        f'aria-selected="{"true" if i == 0 else "false"}">{COURT[p]}</button>'
        for i, (p, _) in enumerate(blocs))
    vues = "".join(
        f'<div class="vue" data-cle="{p}"{"" if i == 0 else " hidden"}>{corps}</div>'
        for i, (p, corps) in enumerate(blocs))
    moyen = float(np.mean([x["gain"] for x in lignes]))
    n_st = max(x["stations"] for x in lignes)
    corps = (
        f'<p class="eyebrow">{eyebrow}</p>'
        f'<h1>{html.escape(nom)}</h1>'
        f'<p class="chapo">Le modèle est <b>national</b> — entraîné sur toute la France, '
        f'puis évalué ici seulement. Rien n\'a été réajusté pour ce territoire : c\'est '
        f'ce qui rend le chiffre transposable. {n_st} stations, {len(lignes)} '
        f'polluant(s) mesuré(s). {retours}</p>'
        f'{supplement}'
        f'<nav class="ong" role="tablist">{onglets}</nav>{vues}')
    return corps, {"nom": nom, "code": code, "gain_moyen": moyen, "stations": n_st,
                   "polluants": len(lignes)}


CSS_SUP = """
.regions a polygon{fill:var(--c);stroke:var(--fond);stroke-width:1.1;
 stroke-linejoin:round;cursor:pointer}
.regions a:hover polygon{stroke:var(--texte);stroke-width:1.8}
.regions a:focus-visible polygon{stroke:var(--azur);stroke-width:2.4}
.grille-reg{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:9px;
 margin-top:16px}
.grille-reg a{display:block;padding:11px 13px;border:1px solid var(--trait);
 border-radius:9px;text-decoration:none;color:var(--texte);background:var(--sur)}
.grille-reg a:hover{border-color:var(--azur)}
.grille-reg .rn{font-weight:620;font-size:.9rem;display:block}
.grille-reg .rg{font-family:var(--mono);font-variant-numeric:tabular-nums;
 font-size:1.12rem;font-weight:600;display:block;margin-top:3px}
.grille-reg .rs{font-size:.76rem;color:var(--doux);display:block}
details.dep{margin:0 0 24px;border:1px solid var(--trait);border-radius:10px;
 background:var(--sur);overflow:hidden}
details.dep>summary{cursor:pointer;padding:13px 16px;font-weight:600;font-size:.92rem;
 list-style:none;display:flex;align-items:center;gap:9px}
details.dep>summary::-webkit-details-marker{display:none}
details.dep>summary::before{content:"▸";color:var(--azur);font-size:.9rem;
 transition:transform .15s}
details.dep[open]>summary::before{transform:rotate(90deg)}
details.dep>summary:hover{color:var(--azur)}
details.dep>summary:focus-visible{outline:2px solid var(--azur);outline-offset:-2px}
details.dep .grille-reg{margin:0;padding:0 14px 15px}
@media(prefers-reduced-motion:reduce){details.dep>summary::before{transition:none}}
"""

# La section de contexte régional reprend l'encadré du contexte départemental — même filet
# ambre, même promesse : ce qui est là-dedans vient de tiers, pas de nos mesures. Deux
# apparences différentes pour la même garantie la rendraient moins crédible, pas plus.
CSS_REGION_TERR = """
section.terr{margin:26px 0 4px;padding:18px 20px;border:1px solid var(--trait);
 border-radius:10px;background:var(--sur)}
section.terr>h2{margin:0 0 8px;font-size:1rem;font-weight:640}
.terr-garde{margin:0 0 14px;padding-left:11px;border-left:3px solid var(--or,#c98a1e);
 font-size:.79rem;line-height:1.5;color:var(--doux)}
.terr-garde b{color:var(--texte)}
"""


def main(horizon: int, sortie: str, departements: bool) -> int:
    dossier = RACINE / sortie
    dossier.mkdir(parents=True, exist_ok=True)
    regions = charger_territoires(SOURCE_REGIONS, 1500.0)
    geo = _stations_geo()
    par_region = dict(zip(*rattacher(geo, regions)[["station_id", "region"]]
                          .to_numpy().T))
    deps, par_dep, dep_de_region = [], {}, {}
    if departements:
        # 900 m au lieu de 1 500 : un département est dix fois plus petit qu'une région,
        # et le trait doit rester juste à cette échelle.
        deps = charger_territoires(SOURCE_DEPARTEMENTS, 900.0)
        par_dep = dict(zip(*rattacher(geo, deps)[["station_id", "region"]]
                           .to_numpy().T))

    jeux, compositions = {}, {}
    for p in POLLUANTS:
        d = charger(p, horizon)
        if d is None or d.empty:
            continue
        d = recaler(d, ["nous", "aasqa"])
        d["region"] = d["station_id"].map(par_region).fillna("")
        d["dep"] = d["station_id"].map(par_dep).fillna("")
        jeux[p] = d
        # La chaîne concurrente est nommée par sa composition RÉELLE : les membres ne
        # couvrent pas toute la fenêtre, et l'annoncer « CHIMERE+MOCAGE » partout serait
        # un nom faux — qui se propage plus loin que le code.
        compositions[p] = couverture_membres(p, d)["nom"]
    if not jeux:
        raise SystemExit("aucune prédiction — lancer d'abord production_reelle.py")

    # ── Rattacher chaque département à sa région, par majorité de ses stations ──
    if deps:
        une = next(iter(jeux.values()))
        appar = une[["station_id", "region", "dep"]].drop_duplicates()
        for code_d, grp in appar[appar["dep"] != ""].groupby("dep"):
            maj = grp["region"].mode()
            if len(maj):
                dep_de_region[code_d] = maj.iloc[0]

    # ── Les pages départementales, d'abord : la région les référencera ──────────
    #
    # Chaque page reçoit son **contexte territorial** : ce que les sources publiées disent
    # du territoire, quand nos mesures ne disent que de combien on l'améliore. Le
    # chargement est non strict à dessein — un département sans fiche reste une page
    # valide, et faire échouer toute la restitution sur un trou du corpus documentaire
    # serait faire décider à une condition de disponibilité ce qui est publié (§ 2 quater).
    # Ce qui manque est donc *nommé* après la boucle, jamais tu.
    contextes = charger_contexte(strict=False)
    (dossier / "dep").mkdir(parents=True, exist_ok=True)
    fiches_dep: dict[str, list[dict]] = {}
    n_dep, codes_pages = 0, []
    for dp in deps:
        res = page_territoire(
            f'{dp["nom"]} ({dp["code"]})', dp["code"], jeux, compositions, "dep",
            "Maille départementale · protocole d'exploitation · J0",
            f'<a href="../{ardoise(prochain_nom(regions, dep_de_region.get(dp["code"])))}'
            f'.html">← la région</a> · <a href="../index.html">toutes les régions</a>',
            MIN_STATIONS_DEP,
            # Le contexte en prose, puis SA FIGURE. Les deux viennent du même bloc sourcé :
            # la figure ne dit rien de plus, elle rend comparable ce que les puces ne
            # permettaient que de lire un département à la fois.
            (rendre_contexte(contextes[dp["code"]]) + fig_departement(contextes[dp["code"]])
             if dp["code"] in contextes else ""))
        if res is None:
            continue
        corps, r = res
        f = dossier / "dep" / f'{dp["code"]}-{dp["ardoise"]}.html'
        f.write_text(enveloppe(f'{dp["nom"]} — cartes de chaleur départementales',
                               corps, "maille départementale")
                     .replace("</style>", CSS_SUP + CSS_CONTEXTE + CSS_TERR + "</style>"),
                     encoding="utf-8")
        r["fichier"] = f"dep/{dp['code']}-{dp['ardoise']}.html"
        fiches_dep.setdefault(dep_de_region.get(dp["code"], ""), []).append(r)
        n_dep += 1
        codes_pages.append(dp["code"])
    if deps:
        print(f"  {n_dep} pages départementales", flush=True)
        rapport_couverture(contextes, codes_pages)

    # ── Les pages régionales ───────────────────────────────────────────────────
    gains, resume, faits = {}, [], 0
    for r0 in regions:
        liste = sorted(fiches_dep.get(r0["code"], []), key=lambda z: -z["gain_moyen"])
        sup = ""
        if liste:
            cases = "".join(
                f'<a href="{x["fichier"]}"><span class="rn">{html.escape(x["nom"])}</span>'
                f'<span class="rg {"pos" if x["gain_moyen"] > 0 else "neg"}">'
                f'{x["gain_moyen"]:+.1f} %</span>'
                f'<span class="rs">{x["stations"]} stations · {x["polluants"]} polluants'
                f'</span></a>' for x in liste)
            sup = (f'<details class="dep"><summary>Descendre au département '
                   f'— {len(liste)} disponibles, moins de stations par page donc des '
                   f'cartes de chaleur plus lisibles</summary>'
                   f'<div class="grille-reg">{cases}</div></details>')
        # ── Ce que les bilans publiés disent de CE territoire ────────────────────
        # Le rattachement passe par les CODES (`dep_de_region`), jamais par les noms : les
        # blocs écrivent « Auvergne-Rhone-Alpes » en ASCII quand la région s'appelle
        # « Auvergne-Rhône-Alpes », et un regroupement par nom perdrait la région entière.
        blocs_r = [contextes[c] for c, rc in dep_de_region.items()
                   if rc == r0["code"] and c in contextes]
        if blocs_r:
            sup += (
                '<section class="terr"><h2>Ce que les bilans disent de ce territoire</h2>'
                '<p class="terr-garde">Sources publiées par des tiers — Atmo régionales, '
                'DREAL, préfectures. <b>Aucun élément de cette section ne sort de notre '
                'modèle</b> : nos mesures sont dans les onglets. Chaque case et chaque '
                'pastille renvoie au texte source en infobulle.</p>'
                f'{fig_region(sorted(blocs_r, key=lambda b: str(b.get("code"))))}</section>')
        res = page_territoire(
            r0["nom"], r0["code"], jeux, compositions, "region",
            "Maille régionale · protocole d'exploitation · J0",
            '<a href="index.html">← toutes les régions</a>', MIN_STATIONS, sup)
        if res is None:
            gains[r0["code"]] = None
            continue
        corps, x = res
        f = dossier / f'{r0["ardoise"]}.html'
        f.write_text(enveloppe(f'{r0["nom"]} — cartes de chaleur régionales', corps,
                               "maille régionale")
                     .replace("</style>", CSS_SUP + CSS_TERR + CSS_REGION_TERR
                              + "</style>"), encoding="utf-8")
        gains[r0["code"]] = x["gain_moyen"]
        x["fichier"] = f'{r0["ardoise"]}.html'
        x["departements"] = len(liste)
        resume.append(x)
        faits += 1
        print(f'  {r0["nom"][:30]:32s} {x["gain_moyen"]:+6.2f} % · '
              f'{x["stations"]:3d} stations · {len(liste):2d} dép. · '
              f'{f.stat().st_size / 1024:6.0f} ko', flush=True)

    cartes = "".join(
        f'<a href="{x["fichier"]}"><span class="rn">{html.escape(x["nom"])}</span>'
        f'<span class="rg {"pos" if x["gain_moyen"] > 0 else "neg"}">'
        f'{x["gain_moyen"]:+.1f} %</span>'
        f'<span class="rs">{x["stations"]} stations · {x["polluants"]} polluants'
        + (f' · {x["departements"]} départements' if x.get("departements") else '')
        + '</span></a>' for x in sorted(resume, key=lambda z: -z["gain_moyen"]))
    corps = (
        f'<p class="eyebrow">Post-traitement statistique des prévisions CAMS · '
        f'maille des AASQA</p>'
        f'<h1>Choisir une région</h1>'
        f'<p class="chapo">La surveillance de la qualité de l\'air est portée par une '
        f'association agréée <b>par région</b>. Un chiffre national ne dit rien à qui '
        f'décide sur un territoire : ces pages rejouent les mêmes mesures, région par '
        f'région, et chaque région se laisse ouvrir <b>département par département</b> — '
        f'moins de stations par page, donc des cartes de chaleur plus lisibles. Le modèle '
        f'reste <b>national et inchangé</b>. <a href="../index.html">← vue nationale</a>'
        f'</p>'
        f'<div class="duo"><section class="bloc"><h2>Gain moyen par région</h2>'
        f'<p>Moyenne des gains de RMSE sur les polluants mesurés. Cliquez une région.</p>'
        f'{carte_regions(regions, gains)}{legende_gain()}</section>'
        f'<section class="bloc"><h2>Les {faits} régions</h2>'
        f'<p>Classées par gain moyen décroissant. {n_dep} pages départementales '
        f'disponibles depuis chacune.</p>'
        f'<div class="grille-reg">{cartes}</div></section></div>')
    idx = dossier / "index.html"
    idx.write_text(enveloppe("Cartes de chaleur par région", corps, "maille régionale")
                   .replace("</style>", CSS_SUP + "</style>"), encoding="utf-8")
    pd.DataFrame(resume).to_csv(RACINE / "reports/pages_regions.csv", index=False)
    print(f"\nÉcrit : {idx.relative_to(RACINE)} · {faits} régions · "
          f"{n_dep} départements")
    return 0


def prochain_nom(regions: list[dict], code: str | None) -> str:
    """Nom de la région portant ce code — « index » si le rattachement a échoué."""
    for r in regions:
        if r["code"] == code:
            return r["nom"]
    return "index"


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--horizon", type=int, default=1)
    a.add_argument("--sortie", default="reports/html/regions")
    a.add_argument("--sans-departements", action="store_true")
    n = a.parse_args()
    raise SystemExit(main(n.horizon, n.sortie, not n.sans_departements))
