#!/usr/bin/env python3
"""Illustrer ce que les bilans annuels disent des territoires — figures SVG en ligne.

Pourquoi ces figures existent
-----------------------------
Les 84 blocs de `docs/departements/` portent une connaissance **structurée** — régime
saisonnier des épisodes, effet du relief sur la dispersion, apports longue distance — et
elle n'était rendue qu'en **puces de texte**. On pouvait lire un département ; on ne pouvait
pas comparer les treize de sa région d'un coup d'œil, ni voir qu'un régime dominait.

Ces figures ne mesurent RIEN. Elles rendent visible ce que des tiers ont publié — Atmo
régionales, DREAL, préfectures — et l'encadré de `contexte_departements.py` qui le dit doit
rester au-dessus d'elles. **Aucun chiffre d'ici ne sort de notre modèle.**

Trois décisions de forme, prises avant la couleur
-------------------------------------------------
1. **Le polluant est sur un AXE, pas dans une teinte.** Une palette catégorielle de quatre
   teintes prise dans les jetons du site échoue à la validation : `#a9482f`↔`#1f7a4d` tombe
   à ΔE 5,4 en deutéranopie et la paire or↔vert à **12,7 en vision normale**, sous le
   plancher de 15. Mettre le polluant en colonne supprime le besoin de palette : il ne reste
   qu'une teinte et une présence. La forme a réglé le problème que la couleur ne pouvait pas.
2. **L'effet du relief est une POLARITÉ** — disperse ↔ piège — donc une échelle divergente,
   deux pôles et un neutre au milieu. Les deux pôles sont les jetons existants `--azur` et
   `--brique`, validés dans les deux thèmes (ΔE 17,7 protan en clair, 19,7 en sombre,
   contraste ≥ 3:1 des deux côtés).
3. **« Non renseigné » est un ÉTAT, jamais un blanc.** 18 départements sur 84 n'ont pas
   d'`effet` publié et 11 n'ont aucun régime d'épisodes. Les fondre dans « mixte » ou les
   laisser vides ferait lire une absence de source comme une absence de phénomène — le
   « zéro de non-lecture indiscernable d'un zéro de non-occurrence » que ce dépôt traque
   partout ailleurs. Ils sont hachurés et comptés dans la légende.

Usage : python3 scripts/figures_territoire.py --demo    (écrit un aperçu autonome)
"""
from __future__ import annotations

import argparse
import html
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from contexte_departements import JOLI_POLLUANT, JOLIE_SAISON, charger  # noqa: E402

# L'ordre des saisons est CELUI DU CALENDRIER, pas celui des effectifs : un tri par
# fréquence ferait bouger les lignes d'un département à l'autre et interdirait justement la
# comparaison que ces figures existent pour permettre.
SAISONS = ["hiver", "printemps", "ete", "automne", "toute_annee"]
# Libellé court là où le libellé long déborde sa gouttière. Vu à la capture, pas au code :
# « toute l'année » sortait de la marge et s'affichait « oute l'année ». Le libellé complet
# reste dans l'infobulle de la ligne, donc rien n'est perdu.
COURT_SAISON = {"toute_annee": "année"}
# PM10 76 · O3 39 · PM2.5 22 · puis SO2 4, benzène 1, NH3 1 — les trois derniers pèsent 6
# occurrences sur 141 et n'auront jamais leur colonne : ils sont repliés dans « autre »,
# qui reste cliquable en infobulle. Une colonne par polluant rare serait vide 83 fois sur 84.
COLONNES = [("PM10", "PM10"), ("PM2.5", "PM2,5"), ("O3", "O₃"), ("_autre", "autre")]
RARES = {"SO2", "benzene", "NH3", "NO2", "COV"}

CASE, GOUT = 26, 3          # côté d'une case, et l'écart de surface entre deux cases
LAB_G, LAB_H = 74, 16       # gouttières des libellés (gauche, haut)


def _e(t: object) -> str:
    return html.escape(str(t or ""), quote=True)


def _colonne_de(polluant: str) -> str:
    return polluant if polluant in {"PM10", "PM2.5", "O3"} else "_autre"


def grille_episodes(bloc: dict) -> dict[tuple[str, str], list[dict]]:
    """(saison, colonne) → les régimes documentés, pour les infobulles."""
    g: dict[tuple[str, str], list[dict]] = {}
    for e in bloc.get("regime_episodes") or []:
        s, p = e.get("saison"), e.get("polluant")
        if s not in SAISONS or not p:
            continue
        g.setdefault((s, _colonne_de(p)), []).append(e)
    return g


def calendrier(bloc: dict, titre: str | None = None) -> str:
    """Matrice saison × polluant d'un département — une case pleine = régime documenté.

    Une seule teinte : la case dit *présence*, pas *quantité*. Les libellés de ligne et de
    colonne portent l'identité, donc rien ne repose sur la couleur seule.
    """
    g = grille_episodes(bloc)
    lg = LAB_G + len(COLONNES) * (CASE + GOUT)
    ht = LAB_H + len(SAISONS) * (CASE + GOUT)
    out = [f'<svg class="fig-cal" viewBox="0 0 {lg} {ht}" width="{lg}" height="{ht}" '
           f'role="img" aria-label="Régimes d\'épisodes documentés, par saison et polluant">']
    if titre:
        out.append(f'<title>{_e(titre)}</title>')

    for j, (cle, court) in enumerate(COLONNES):
        x = LAB_G + j * (CASE + GOUT) + CASE / 2
        out.append(f'<text class="cal-col" x="{x:.0f}" y="11" text-anchor="middle">{_e(court)}</text>')

    for i, s in enumerate(SAISONS):
        y = LAB_H + i * (CASE + GOUT)
        long = JOLIE_SAISON.get(s, s)
        out.append(f'<text class="cal-lig" x="{LAB_G - 7}" y="{y + CASE * 0.68:.0f}" '
                   f'text-anchor="end">{_e(COURT_SAISON.get(s, long))}'
                   f'<title>{_e(long)}</title></text>')
        for j, (cle, _c) in enumerate(COLONNES):
            x = LAB_G + j * (CASE + GOUT)
            faits = g.get((s, cle)) or []
            if faits:
                # L'infobulle porte le MÉCANISME publié, pas un libellé inventé : c'est ce
                # qui distingue une illustration d'une décoration.
                bulle = " · ".join(
                    f"{JOLI_POLLUANT.get(f.get('polluant'), f.get('polluant'))} — "
                    f"{str(f.get('mecanisme') or '').strip()[:190]}" for f in faits)
                out.append(f'<rect class="cal-on" x="{x}" y="{y}" width="{CASE}" '
                           f'height="{CASE}" rx="3"><title>{_e(bulle)}</title></rect>')
            else:
                out.append(f'<rect class="cal-off" x="{x}" y="{y}" width="{CASE}" '
                           f'height="{CASE}" rx="3"/>')
    out.append("</svg>")
    return "".join(out)


def bandeau_dispersion(blocs: list[dict]) -> str:
    """Les départements d'une région, rangés par ce que leur relief fait à la dispersion.

    Échelle DIVERGENTE : `dispersif` et `piegeant` sont deux pôles opposés, `mixte` le
    neutre. « Non renseigné » est hachuré — il n'a pas de place sur l'axe, et lui en donner
    une reviendrait à affirmer une source qui n'existe pas.
    """
    rang = {"dispersif": 0, "mixte": 1, "piegeant": 2, None: 3}
    ordonne = sorted(blocs, key=lambda b: (rang.get((b.get("topographie_climat") or {}).get("effet"), 3),
                                           b.get("nom", "")))
    lignes = []
    for b in ordonne:
        topo = b.get("topographie_climat") or {}
        effet = topo.get("effet")
        classe = {"dispersif": "d-disp", "piegeant": "d-pieg", "mixte": "d-mixte"}.get(effet, "d-nr")
        vents = ", ".join(topo.get("vents_nommes") or [])
        bulle = (str(topo.get("libelle") or "").strip()[:230]
                 or "aucun élément publié sur le relief et la circulation")
        if vents:
            bulle += f" — vents nommés : {vents}"
        etiq = "non renseigné" if effet is None else _e(effet.replace("piegeant", "piégeant"))
        lignes.append(
            f'<li class="disp {classe}" title="{_e(bulle)}">'
            f'<b>{_e(b.get("nom"))}</b><span>{_e(b.get("code"))}</span>'
            f'<i>{etiq}</i></li>')
    n = Counter((b.get("topographie_climat") or {}).get("effet") for b in blocs)
    leg = (f'<p class="disp-leg">'
           f'<span class="pastille d-disp"></span> disperse ({n.get("dispersif", 0)}) · '
           f'<span class="pastille d-mixte"></span> mixte ({n.get("mixte", 0)}) · '
           f'<span class="pastille d-pieg"></span> piège ({n.get("piegeant", 0)}) · '
           f'<span class="pastille d-nr"></span> non renseigné ({n.get(None, 0)})</p>')
    return f'<ul class="disp-liste">{"".join(lignes)}</ul>{leg}'


def apports_exterieurs(blocs: list[dict]) -> str:
    """Ce qui arrive d'ailleurs — origines citées, et combien de départements les citent."""
    c = Counter()
    detail: dict[str, set[str]] = {}
    for b in blocs:
        for t in b.get("transport_longue_distance") or []:
            o = str(t.get("origine") or "").replace("_", " ")
            if not o:
                continue
            c[o] += 1
            detail.setdefault(o, set()).add(
                JOLI_POLLUANT.get(t.get("polluant"), str(t.get("polluant") or "")))
    if not c:
        return ""
    haut = c.most_common(6)
    m = haut[0][1]
    barres = "".join(
        f'<li title="{_e(o)} — {_e(", ".join(sorted(detail[o])))}">'
        f'<span class="ap-nom">{_e(o)}</span>'
        f'<span class="ap-piste"><i style="width:{100 * v / m:.0f}%"></i></span>'
        f'<span class="ap-val">{v}</span></li>' for o, v in haut)
    return (f'<ul class="ap-liste">{barres}</ul>'
            f'<p class="ap-note">Nombre de départements du territoire dont le bilan cite '
            f'cette origine. Survolez pour les polluants concernés.</p>')


CSS = """
/* ── Figures de contexte territorial ─────────────────────────────────────────
   Aucune couleur littérale : tout passe par les jetons de la page, donc les deux
   thèmes suivent sans second jeu de règles. */
.fig-terr{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));
 margin:14px 0 4px}
.fig-terr h4{margin:0 0 2px;font-size:.86rem;font-weight:620}
.fig-terr .sous{margin:0 0 9px;font-size:.76rem;color:var(--doux);line-height:1.45}
.fig-cal{max-width:100%;height:auto}
.fig-cal text{font-family:var(--mono);font-size:9.5px;fill:var(--doux)}
.fig-cal .cal-col{letter-spacing:.04em}
.cal-on{fill:var(--azur)}
.cal-off{fill:var(--sur2);stroke:var(--trait);stroke-width:1}
.fig-cal rect:hover{stroke:var(--texte);stroke-width:1.5}

.disp-liste{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:5px}
.disp{display:flex;align-items:baseline;gap:6px;padding:5px 9px;border-radius:6px;
 border:1px solid var(--trait);background:var(--sur2);font-size:.78rem;cursor:help}
.disp b{font-weight:620}
.disp span{font-family:var(--mono);font-size:.68rem;color:var(--doux)}
.disp i{font-style:normal;font-size:.66rem;letter-spacing:.05em;text-transform:uppercase;
 color:var(--doux)}
.disp.d-disp{border-left:4px solid var(--azur)}
.disp.d-pieg{border-left:4px solid var(--brique)}
.disp.d-mixte{border-left:4px solid var(--trait)}
/* Les hachures sont la SECONDE lecture de « non renseigné » : la teinte seule se
   confondrait avec « mixte » en impression noir et blanc ou en vision altérée. */
.disp.d-nr{border-left:4px solid var(--doux);
 background:repeating-linear-gradient(135deg,transparent 0 5px,var(--trait) 5px 6px)}
.disp-leg{margin:9px 0 0;font-size:.74rem;color:var(--doux)}
.pastille{display:inline-block;width:9px;height:9px;border-radius:2px;
 vertical-align:baseline;margin-right:2px}
.pastille.d-disp{background:var(--azur)}
.pastille.d-pieg{background:var(--brique)}
.pastille.d-mixte{background:var(--trait)}
.pastille.d-nr{background:repeating-linear-gradient(135deg,var(--sur2) 0 3px,var(--trait) 3px 4px)}

.ap-liste{list-style:none;margin:0;padding:0;display:grid;gap:5px}
.ap-liste li{display:grid;grid-template-columns:1fr 96px 26px;gap:9px;align-items:center;
 font-size:.78rem;cursor:help}
.ap-nom{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ap-piste{height:7px;background:var(--sur2);border-radius:4px;overflow:hidden}
.ap-piste i{display:block;height:100%;background:var(--azur);border-radius:4px}
.ap-val{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:.74rem;
 color:var(--doux);text-align:right}
.ap-note{margin:8px 0 0;font-size:.72rem;color:var(--doux);line-height:1.45}
.pm-multi{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(210px,1fr))}
.pm-multi figure{margin:0}
.pm-multi figcaption{font-size:.76rem;font-weight:600;margin:0 0 4px}
.pm-multi .nr{font-size:.72rem;color:var(--doux);font-style:italic}
"""


def bloc_departement(bloc: dict) -> str:
    """Les figures d'UNE page départementale."""
    cal = calendrier(bloc)
    n = len(bloc.get("regime_episodes") or [])
    manque = ('<p class="sous">Aucun régime saisonnier publié pour ce département — '
              'la case vide dit l\'absence de source, pas l\'absence de phénomène.</p>'
              if n == 0 else
              f'<p class="sous">{n} régime(s) documenté(s) dans les bilans cités plus bas. '
              f'Survolez une case pour le mécanisme publié.</p>')
    return (f'<div class="fig-terr"><div>'
            f'<h4>Quand les épisodes arrivent, et de quel polluant</h4>{manque}{cal}'
            f'</div></div>')


def bloc_region(blocs: list[dict]) -> str:
    """Les figures d'UNE page régionale — la comparaison entre ses départements."""
    if not blocs:
        return ""
    petits = []
    for b in sorted(blocs, key=lambda x: str(x.get("code"))):
        vide = not (b.get("regime_episodes") or [])
        petits.append(
            f'<figure><figcaption>{_e(b.get("nom"))} '
            f'<span class="nr">{_e(b.get("code"))}</span></figcaption>'
            f'{calendrier(b)}'
            + ('<p class="nr">aucun régime publié</p>' if vide else "")
            + "</figure>")
    ap = apports_exterieurs(blocs)
    bloc_ap = (f'<div><h4>Ce qui arrive d\'ailleurs</h4>'
               f'<p class="sous">Origines citées par les bilans des départements de cette '
               f'région.</p>{ap}</div>' if ap else "")
    return (
        f'<div class="fig-terr">'
        f'<div><h4>Ce que le relief fait à la dispersion</h4>'
        f'<p class="sous">Effet publié dans les bilans, département par département. '
        f'Survolez pour le texte source et les vents nommés.</p>'
        f'{bandeau_dispersion(blocs)}</div>'
        f'{bloc_ap}</div>'
        f'<h4 style="margin:18px 0 2px;font-size:.86rem">Quand les épisodes arrivent — '
        f'les départements côte à côte</h4>'
        f'<p class="sous" style="margin:0 0 10px">Une case pleine = un régime saisonnier '
        f'documenté pour ce polluant. Les colonnes et les lignes sont identiques partout, '
        f'donc les fiches se comparent.</p>'
        f'<div class="pm-multi">{"".join(petits)}</div>')


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--demo", action="store_true", help="écrit un aperçu autonome")
    a.add_argument("--region", default="Occitanie")
    v = a.parse_args()

    blocs = charger(strict=False)
    par_region = [b for b in blocs.values() if b.get("region", "").startswith(v.region[:7])]
    print(f"{len(blocs)} blocs chargés · {len(par_region)} dans « {v.region} »")
    n_effet = Counter((b.get("topographie_climat") or {}).get("effet") for b in blocs.values())
    print(f"  effet de dispersion : {dict(n_effet)}")
    print(f"  sans régime d'épisodes : "
          f"{sum(1 for b in blocs.values() if not b.get('regime_episodes'))}")
    if not v.demo:
        return 0
    if not par_region:
        raise SystemExit(f"aucun département pour « {v.region} »")
    sortie = RACINE / "reports/figures/_apercu_figures_territoire.html"
    sortie.write_text(
        "<!doctype html><meta charset=utf-8><title>aperçu</title>"
        "<style>:root{--fond:#f5f6f3;--sur:#fff;--sur2:#eceee9;--texte:#141a1f;"
        "--doux:#5b656f;--trait:#dcdfd9;--azur:#2f6da4;--brique:#a9482f;"
        "--mono:ui-monospace,monospace}"
        "@media(prefers-color-scheme:dark){:root{--fond:#0e1216;--sur:#141a21;"
        "--sur2:#1a212a;--texte:#e8eaec;--doux:#98a1ab;--trait:#242c36;"
        "--azur:#4d92cf;--brique:#c9634a}}"
        "body{background:var(--fond);color:var(--texte);font:15px/1.6 system-ui;"
        "margin:0;padding:28px;max-width:1100px}" + CSS + "</style>"
        f"<h2>{_e(v.region)} — aperçu</h2>{bloc_region(par_region)}"
        f"<h2 style='margin-top:30px'>Un département</h2>{bloc_departement(par_region[0])}",
        encoding="utf-8")
    print(f"Écrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
