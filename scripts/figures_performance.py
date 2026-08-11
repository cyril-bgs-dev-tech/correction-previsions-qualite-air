#!/usr/bin/env python3
"""Nos mesures, rendues comparables entre territoires — figures SVG en ligne.

Pourquoi ce module est SÉPARÉ de `figures_territoire`
------------------------------------------------------
Les pages tiennent une frontière que rien ne doit brouiller : d'un côté ce que des tiers
publient sur un territoire, de l'autre ce que **nous** y mesurons. Deux modules, deux
sections, deux encadrés. Un seul fichier qui produirait les deux finirait par les mélanger
au premier ajout — et un « 66 % des NOx » d'Atmo passerait pour une de nos mesures.

Ce que ces figures réparent
---------------------------
La vue nationale coloriait treize régions par leur **gain moyen sur quatre polluants**.
Une moyenne cache que le NO₂ gagne trois fois ce que gagne l'ozone, et treize moyennes
comprises entre +19,7 et +33,1 % donnent treize bleus qu'on ne distingue pas. Le détail
par polluant existait pourtant : `page_territoire` le calculait puis le jetait.

Décisions de forme, prises avant la couleur
--------------------------------------------
- **Le polluant est sur un AXE**, comme dans `figures_territoire` et pour la même raison :
  la palette catégorielle à quatre teintes des jetons du site échoue à la validation
  (or↔vert à ΔE 12,7 en vision *normale*, sous le plancher de 15).
- **Le gain est une polarité** — on fait mieux ou moins bien que la chaîne en service —
  donc échelle **divergente** ancrée à zéro : `--azur` au-dessus, `--brique` en dessous.
  Paire validée dans les deux thèmes (ΔE 17,7 protan clair, 19,7 sombre, contraste ≥ 3:1).
- **Chaque barre porte sa valeur en chiffres.** L'identité ne repose jamais sur la couleur
  seule, et la figure reste lisible en noir et blanc comme en vision altérée.
"""
from __future__ import annotations

import html
from statistics import median

JOLI = {"NO2": "NO₂", "O3": "O₃", "PM10": "PM10", "PM25": "PM2,5", "PM2.5": "PM2,5"}
ORDRE = ["NO2", "O3", "PM10", "PM25"]


def _e(t: object) -> str:
    return html.escape(str(t or ""), quote=True)


def _cls(v: float) -> str:
    return "b-pos" if v >= 0 else "b-neg"


def profil_polluants(par_polluant: dict[str, float],
                     reference: dict[str, float] | None = None,
                     nom_ref: str = "médiane nationale") -> str:
    """Le gain de ce territoire, polluant par polluant, contre une référence.

    C'est la figure qui casse la moyenne : elle montre que le territoire ne gagne pas
    autant partout, ce qu'un seul chiffre ne peut pas dire.
    """
    items = [(p, par_polluant[p]) for p in ORDRE if p in par_polluant]
    items += [(p, v) for p, v in par_polluant.items() if p not in ORDRE]
    if not items:
        return ""
    ech = max(12.0, max(abs(v) for _p, v in items),
              max((abs(v) for v in (reference or {}).values()), default=0))
    lignes = []
    for p, v in items:
        # Deux demi-pistes autour d'un zéro central : une barre négative part à gauche,
        # une positive à droite, et l'œil lit le signe avant le chiffre.
        larg = 50 * abs(v) / ech
        x = 50 - larg if v < 0 else 50
        marque = ""
        if reference and p in reference:
            r = reference[p]
            xr = 50 + 50 * r / ech
            marque = (f'<i class="ref" style="left:{xr:.1f}%" '
                      f'title="{_e(nom_ref)} : {r:+.1f} %"></i>')
        lignes.append(
            f'<li><span class="pp-nom">{_e(JOLI.get(p, p))}</span>'
            f'<span class="pp-piste"><b class="{_cls(v)}" '
            f'style="left:{x:.1f}%;width:{larg:.1f}%"></b>'
            f'<u class="zero"></u>{marque}</span>'
            f'<span class="pp-val {_cls(v)}">{v:+.1f} %</span></li>')
    leg = (f'<p class="fig-note"><span class="ref-leg"></span> {_e(nom_ref)} · '
           f'barre à droite du trait = mieux que la chaîne en service</p>'
           if reference else
           '<p class="fig-note">Barre à droite du trait = mieux que la chaîne en service.</p>')
    return f'<ul class="pp-liste">{"".join(lignes)}</ul>{leg}'


def rang_departements(liste: list[dict], mediane_fr: float | None = None,
                      courant: str | None = None) -> str:
    """Les départements d'une région, rangés par gain moyen.

    `courant` met en relief un département — c'est ce qui permet à sa propre page de
    montrer où il se situe chez lui, sans dupliquer la figure.
    """
    if not liste:
        return ""
    ordonne = sorted(liste, key=lambda x: -x["gain_moyen"])
    ech = max(12.0, max(abs(x["gain_moyen"]) for x in ordonne), abs(mediane_fr or 0))
    lignes = []
    for x in ordonne:
        v = x["gain_moyen"]
        larg = 50 * abs(v) / ech
        xx = 50 - larg if v < 0 else 50
        ici = ' class="ici"' if courant and str(x.get("code")) == str(courant) else ""
        lien = x.get("fichier")
        nom = (f'<a href="{_e(lien)}">{_e(x["nom"])}</a>' if lien else _e(x["nom"]))
        lignes.append(
            f'<li{ici}><span class="pp-nom">{nom}</span>'
            f'<span class="pp-piste"><b class="{_cls(v)}" '
            f'style="left:{xx:.1f}%;width:{larg:.1f}%"></b><u class="zero"></u></span>'
            f'<span class="pp-val {_cls(v)}">{v:+.1f} %</span></li>')
    med = median([x["gain_moyen"] for x in ordonne])
    note = (f'<p class="fig-note">Médiane de la région <b>{med:+.1f} %</b>'
            + (f' · médiane des 84 départements <b>{mediane_fr:+.1f} %</b>'
               if mediane_fr is not None else "")
            + ' · gain de RMSE contre la chaîne en service, moyenné sur les polluants '
              'mesurés.</p>')
    return f'<ul class="pp-liste rang">{"".join(lignes)}</ul>{note}'


def position_nationale(valeur: float, toutes: list[float], etiquette: str) -> str:
    """Où ce territoire se place parmi tous les autres — une bande, un repère.

    Un rang seul (« 12ᵉ sur 84 ») ne dit pas s'il est serré contre le 13ᵉ ou très
    au-dessus. La bande montre la DISPERSION, le rang n'en est que le résumé.
    """
    if not toutes:
        return ""
    lo, hi = min(toutes), max(toutes)
    etendue = max(hi - lo, 1e-6)
    pos = lambda v: 100 * (v - lo) / etendue        # noqa: E731
    rang = 1 + sum(1 for v in toutes if v > valeur)
    points = "".join(
        f'<i style="left:{pos(v):.2f}%"></i>' for v in toutes)
    med = median(toutes)
    return (f'<div class="pos-bande">{points}'
            f'<u class="pos-med" style="left:{pos(med):.2f}%" '
            f'title="médiane {med:+.1f} %"></u>'
            f'<b class="pos-moi" style="left:{pos(valeur):.2f}%" '
            f'title="{_e(etiquette)} : {valeur:+.1f} %"></b></div>'
            f'<p class="fig-note"><b>{rang}<sup>e</sup> sur {len(toutes)}</b> · '
            f'{_e(etiquette)} à <b>{valeur:+.1f} %</b>, médiane <b>{med:+.1f} %</b>, '
            f'étendue de {lo:+.1f} à {hi:+.1f} %. Chaque trait est un territoire.</p>')


def matrice_territoires(lignes: list[dict], titre_col: str = "polluant") -> str:
    """Territoire × polluant — la table que la moyenne écrasait.

    Remplace treize bleus indiscernables par une lecture à deux entrées : on voit d'un
    coup que le NO₂ porte le gain partout, et où l'ozone décroche.
    """
    cols = [p for p in ORDRE if any(p in x.get("par_polluant", {}) for x in lignes)]
    if not cols or not lignes:
        return ""
    vals = [v for x in lignes for p, v in x.get("par_polluant", {}).items() if p in cols]
    ech = max(abs(min(vals)), abs(max(vals)), 1e-6)
    tetes = "".join(f"<th>{_e(JOLI.get(c, c))}</th>" for c in cols)
    corps = []
    for x in sorted(lignes, key=lambda z: -z["gain_moyen"]):
        cases = []
        for c in cols:
            v = x.get("par_polluant", {}).get(c)
            if v is None:
                # Non mesuré ≠ mesuré à zéro. La case le dit, elle ne le colorie pas.
                cases.append('<td class="nm" title="polluant non mesuré ici">·</td>')
                continue
            # Opacité ∝ |gain| sur une teinte par signe : c'est une échelle divergente,
            # pas un arc-en-ciel, et le chiffre reste écrit dans la case.
            o = 0.14 + 0.72 * abs(v) / ech
            teinte = "var(--azur)" if v >= 0 else "var(--brique)"
            cases.append(
                f'<td class="cell" style="background:color-mix(in srgb,{teinte} '
                f'{o * 100:.0f}%, transparent)" title="{_e(x["nom"])} · '
                f'{_e(JOLI.get(c, c))} : {v:+.1f} %">{v:+.0f}</td>')
        nom = (f'<a href="{_e(x["fichier"])}">{_e(x["nom"])}</a>'
               if x.get("fichier") else _e(x["nom"]))
        corps.append(f'<tr><th scope="row">{nom}</th>{"".join(cases)}'
                     f'<td class="moy">{x["gain_moyen"]:+.1f}</td></tr>')
    return (f'<div class="fig-scroll"><table class="mat">'
            f'<thead><tr><th scope="col">territoire</th>{tetes}'
            f'<th scope="col">moyenne</th></tr></thead>'
            f'<tbody>{"".join(corps)}</tbody></table></div>'
            f'<p class="fig-note">Gain de RMSE contre la chaîne en service, en %. '
            f'Bleu = mieux, brique = moins bien, intensité ∝ ampleur. '
            f'<span class="nm">·</span> = polluant non mesuré sur ce territoire — '
            f'une absence de mesure, jamais un zéro.</p>')


CSS = """
/* ── Figures de performance ──────────────────────────────────────────────────
   Aucune couleur littérale : les jetons de la page portent les deux thèmes. */
.fig-perf{margin:16px 0 6px}
.fig-perf h4{margin:0 0 2px;font-size:.86rem;font-weight:620}
.fig-perf .sous{margin:0 0 10px;font-size:.76rem;color:var(--doux);line-height:1.45}
.fig-note{margin:8px 0 0;font-size:.72rem;color:var(--doux);line-height:1.5}

.pp-liste{list-style:none;margin:0;padding:0;display:grid;gap:4px}
.pp-liste li{display:grid;grid-template-columns:minmax(88px,1fr) minmax(120px,3fr) 58px;
 gap:10px;align-items:center;font-size:.79rem}
.pp-liste li.ici{font-weight:660}
.pp-liste li.ici .pp-nom{color:var(--azur)}
.pp-nom{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pp-nom a{color:inherit;text-decoration:none;border-bottom:1px solid var(--trait)}
.pp-nom a:hover{border-bottom-color:var(--azur)}
.pp-piste{position:relative;height:13px;background:var(--sur2);border-radius:3px}
.pp-piste b{position:absolute;top:2px;height:9px;border-radius:2px}
/* 2 px de surface entre la barre et le trait de zéro : sans cet écart les deux marques
   se touchent et l'on ne voit plus où commence la barre. */
.pp-piste b.b-pos{background:var(--azur);margin-left:2px}
.pp-piste b.b-neg{background:var(--brique);margin-right:2px}
.pp-piste u.zero{position:absolute;left:50%;top:-2px;width:1px;height:17px;
 background:var(--doux);opacity:.55}
.pp-piste i.ref{position:absolute;top:-3px;width:2px;height:19px;background:var(--texte);
 opacity:.55;border-radius:1px;cursor:help}
.ref-leg{display:inline-block;width:2px;height:9px;background:var(--texte);opacity:.55;
 vertical-align:baseline;margin-right:3px}
.pp-val{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:.76rem;
 text-align:right}
.pp-val.b-pos{color:var(--azur)}
.pp-val.b-neg{color:var(--brique)}

.pos-bande{position:relative;height:26px;background:var(--sur2);border-radius:4px;
 margin:4px 0 0;border:1px solid var(--trait)}
.pos-bande i{position:absolute;top:7px;width:1px;height:12px;background:var(--doux);
 opacity:.5}
.pos-bande u.pos-med{position:absolute;top:2px;width:1px;height:22px;background:var(--doux);
 cursor:help}
.pos-bande b.pos-moi{position:absolute;top:0;width:3px;height:26px;background:var(--azur);
 border-radius:2px;box-shadow:0 0 0 2px var(--sur);cursor:help}

.mat{border-collapse:collapse;font-size:.78rem;width:100%}
.mat th{font-family:var(--mono);font-size:.68rem;text-transform:uppercase;
 letter-spacing:.07em;color:var(--doux);font-weight:600;padding:0 7px 6px;text-align:center}
.mat th[scope=row]{text-align:left;text-transform:none;font-family:inherit;font-size:.79rem;
 letter-spacing:0;color:var(--texte);font-weight:600;padding:4px 10px 4px 0;
 white-space:nowrap}
.mat th[scope=row] a{color:inherit;text-decoration:none;border-bottom:1px solid var(--trait)}
.mat th[scope=row] a:hover{border-bottom-color:var(--azur)}
/* 2 px de surface entre deux cases pleines : sans l'écart, deux intensités voisines se
   lisent comme une seule plage. */
.mat td{text-align:center;font-family:var(--mono);font-variant-numeric:tabular-nums;
 padding:5px 8px;border:2px solid var(--sur);border-radius:3px;cursor:help}
.mat td.moy{background:none;border-color:transparent;color:var(--doux);font-weight:600;
 cursor:auto}
.mat td.nm{color:var(--doux);opacity:.6;background:none;cursor:help}
.mat tbody tr:hover th[scope=row]{color:var(--azur)}
"""
