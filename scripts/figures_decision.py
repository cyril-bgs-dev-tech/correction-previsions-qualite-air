#!/usr/bin/env python3
"""Quatre figures pour un public non technique — ce que la correction change à la décision.

Le principe qui gouverne ces figures
--------------------------------------
Un public non technique ne lit pas un taux. « POD 0,097 » ne dit rien ; « sur 390 épisodes,
la prévision brute en voit 26 et la nôtre 38 » se comprend sans explication.

Donc : **des comptes d'événements réels, jamais des rapports**. Et le format le plus
persuasif n'est pas un agrégat, c'est un **désaccord daté** — *ce jour-là, la prévision
brute n'alertait pas, la nôtre si, et il y a eu dépassement.*

⚠️ Ce que ces figures comparent, et ce qu'elles NE comparent PAS
------------------------------------------------------------------
La référence est la **prévision CAMS Europe brute**. Ce n'est **pas** le produit d'Atmo
Occitanie, qui repose sur CHIMERE en configuration nationale, assimilé et déjà corrigé
statistiquement. Aucune de ces figures ne dit ce que notre méthode ferait face à leur
chaîne — elle dit ce qu'elle fait face à la prévision européenne libre.

Toute légende qui laisserait entendre l'inverse serait fausse. Elles portent donc toutes la
mention « prévision brute », jamais « produit officiel ».

Les quatre panneaux
--------------------
1. **Le biais** — l'écart moyen entre prévu et mesuré, avant et après. Le résultat le plus
   simple à valider : « leur prévision est systématiquement trop basse de N µg/m³ ».
2. **Le compteur d'épisodes** — en nombres absolus : combien d'épisodes réels, combien vus
   par chacun, combien de fausses alertes.
3. **Le calendrier des désaccords** — jour par jour, les journées où l'un alerte et pas
   l'autre, avec la vérité. Vert au-dessus : sauvées. Rouge en dessous : perdues.
4. **Le taux de change** — combien d'épisodes de plus par fausse alerte supplémentaire
   acceptée. La traduction en langage de décideur de la courbe coût-perte.

Usage : python3 scripts/figures_decision.py --polluant PM10 --horizon 2
Sortie : reports/figures/decision_<polluant>_h<n>.html
"""

from __future__ import annotations

import argparse
import base64
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from recalibrer_amplitude import cartographie_quantiles  # noqa: E402

SEUILS = {"PM10": (50.0, "seuil d'information français, moyenne journalière"),
          "PM25": (50.0, "repère indicatif — aucun seuil français à ce grain"),
          "O3": (120.0, "valeur cible européenne — pas le seuil d'information de 180"),
          "NO2": (200.0, "seuil d'information français, maximum horaire")}
NOM = {"PM10": "Particules PM10", "PM25": "Particules fines PM2,5",
       "O3": "Ozone", "NO2": "Dioxyde d'azote"}

VERT, ROUGE, ORANGE, BLEU = "#3fa860", "#d1495b", "#e0a458", "#4a7fb5"


def barres(donnees: list[tuple[str, float, str]], unite: str, largeur: int = 560,
           h_barre: int = 26) -> str:
    """Barres horizontales en SVG — nettes à toute taille, lisibles sans légende."""
    if not donnees:
        return ""
    vmax = max(abs(v) for _, v, _ in donnees) or 1.0
    zero_a_gauche = min(v for _, v, _ in donnees) >= 0
    x0 = 190
    util = largeur - x0 - 70
    h = len(donnees) * (h_barre + 8) + 10
    out = [f'<svg viewBox="0 0 {largeur} {h}" width="100%" role="img">']
    for i, (nom, v, couleur) in enumerate(donnees):
        y = i * (h_barre + 8) + 5
        if zero_a_gauche:
            xa, w = x0, util * abs(v) / vmax
        else:
            centre = x0 + util / 2
            w = (util / 2) * abs(v) / vmax
            xa = centre if v >= 0 else centre - w
        out.append(f'<text x="{x0 - 10}" y="{y + h_barre * 0.68}" text-anchor="end" '
                   f'font-size="13" fill="#c3c2b7">{nom}</text>')
        out.append(f'<rect x="{xa:.1f}" y="{y}" width="{max(w, 1.5):.1f}" '
                   f'height="{h_barre}" rx="3" fill="{couleur}"/>')
        out.append(f'<text x="{xa + w + 8:.1f}" y="{y + h_barre * 0.68}" font-size="13" '
                   f'font-weight="600" fill="#fff">{v:+,.1f}{unite}</text>'
                   if not zero_a_gauche else
                   f'<text x="{xa + w + 8:.1f}" y="{y + h_barre * 0.68}" font-size="13" '
                   f'font-weight="600" fill="#fff">{v:,.0f}{unite}</text>')
    if not zero_a_gauche:
        c = x0 + util / 2
        out.append(f'<line x1="{c}" y1="0" x2="{c}" y2="{h}" stroke="rgba(255,255,255,.45)" '
                   f'stroke-width="1.5"/>')
    out.append("</svg>")
    return "".join(out)


def calendrier(d: pd.DataFrame, v: np.ndarray, a_ref: np.ndarray,
               a_nous: np.ndarray) -> tuple[str, dict]:
    """Bandes journalières : au-dessus les journées sauvées, en dessous les perdues."""
    t = pd.DataFrame({"jour": pd.to_datetime(d["jour"]).dt.floor("D"),
                      "sauve": v & a_nous & ~a_ref,
                      "perdu": v & a_ref & ~a_nous,
                      "commun": v & a_ref & a_nous,
                      "manque": v & ~a_ref & ~a_nous})
    par = t.groupby("jour")[["sauve", "perdu", "commun", "manque"]].sum()
    par = par.reindex(pd.date_range(par.index.min(), par.index.max(), freq="D"),
                      fill_value=0)
    n = len(par)
    hmax = max(int(par[["sauve", "perdu"]].to_numpy().max()), 1)
    # Image d'un pixel par jour : la même logique que les cartes de chaleur — la couleur
    # reste exacte, c'est la définition qui baisse, et le navigateur agrandit.
    haut = 60
    img = np.full((haut * 2 + 1, n, 3), 26, dtype="uint8")
    for c, col, sens in (("sauve", VERT, -1), ("perdu", ROUGE, +1)):
        rvb = tuple(int(col[k:k + 2], 16) for k in (1, 3, 5))
        vals = par[c].to_numpy()
        for i, val in enumerate(vals):
            if val <= 0:
                continue
            k = min(int(round(haut * val / hmax)), haut)
            if sens < 0:
                img[haut - k:haut, i] = rvb
            else:
                img[haut + 1:haut + 1 + k, i] = rvb
    img[haut, :] = 90
    from PIL import Image
    im = Image.fromarray(img, mode="RGB").resize((n * 3, (haut * 2 + 1) * 2),
                                                 Image.NEAREST)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    png = base64.b64encode(buf.getvalue()).decode()

    reperes = []
    jours = list(par.index)
    for dt in jours:
        if dt.day == 1 and dt.month == 1:
            reperes.append(f'<span class="an" style="left:'
                           f'{100 * jours.index(dt) / n:.3f}%">{dt:%Y}</span>')
    largeur = max(680, n * 2)
    bloc = (f'<div class="defile"><div class="cal" style="min-width:{largeur}px">'
            f'<img src="data:image/png;base64,{png}" alt="calendrier des désaccords">'
            f'<div class="reperes">{"".join(reperes)}</div></div></div>')
    return bloc, {k: int(par[k].sum()) for k in ("sauve", "perdu", "commun", "manque")}


def taux_de_change(v: np.ndarray, score: np.ndarray, n_pts: int = 60) -> list[tuple]:
    """Détections en fonction des fausses alertes, **en comptes** — pas en taux."""
    ordre = np.argsort(-score, kind="stable")
    vt = v[ordre]
    tp = np.cumsum(vt)
    fp = np.cumsum(~vt)
    pas = max(len(vt) // n_pts, 1)
    return [(int(fp[i]), int(tp[i])) for i in range(0, len(vt), pas)]


def courbe(points_a: list, points_b: list, n_total: int, largeur: int = 560,
           haut: int = 300) -> str:
    fmax = max(max(f for f, _ in points_a), max(f for f, _ in points_b)) or 1
    tmax = n_total or 1
    px = lambda f: 46 + (largeur - 70) * min(f / fmax, 1.0)   # noqa: E731
    py = lambda t: haut - 34 - (haut - 60) * min(t / tmax, 1.0)  # noqa: E731
    out = [f'<svg viewBox="0 0 {largeur} {haut}" width="100%" role="img">']
    out.append(f'<line x1="46" y1="{haut - 34}" x2="{largeur - 24}" y2="{haut - 34}" '
               f'stroke="rgba(255,255,255,.25)"/>')
    out.append(f'<line x1="46" y1="26" x2="46" y2="{haut - 34}" '
               f'stroke="rgba(255,255,255,.25)"/>')
    for nom, pts, col in (("prévision brute", points_a, BLEU),
                          ("notre correction", points_b, VERT)):
        chemin = " ".join(f"{'M' if i == 0 else 'L'}{px(f):.1f},{py(t):.1f}"
                          for i, (f, t) in enumerate(pts))
        out.append(f'<path d="{chemin}" fill="none" stroke="{col}" stroke-width="2.4"/>')
    out.append(f'<text x="{largeur / 2}" y="{haut - 8}" text-anchor="middle" '
               f'font-size="12" fill="#c3c2b7">fausses alertes acceptées</text>')
    out.append(f'<text x="12" y="20" font-size="12" fill="#c3c2b7">épisodes détectés '
               f'(sur {n_total})</text>')
    for frac in (0.25, 0.5, 0.75, 1.0):
        out.append(f'<text x="40" y="{py(tmax * frac) + 4:.0f}" text-anchor="end" '
                   f'font-size="11" fill="#8d8c85">{int(tmax * frac)}</text>')
    out.append("</svg>")
    return "".join(out)


def main(polluant: str, horizon: int, typologie: bool) -> int:
    suff = f"_h{horizon}" + ("_typo" if typologie else "")
    f = RACINE / f"data/interim/oof/oof_{polluant}{suff}.parquet"
    if not f.exists():
        raise SystemExit(f"absent : {f.name} — lancer oof_double_aveugle.py --horizon "
                         f"{horizon} d'abord")
    o = pd.read_parquet(f)
    d = o[o["epreuve"] == "double aveugle"].copy()
    d["jour"] = pd.to_datetime(d["jour"])
    d["mois"] = d["jour"].dt.strftime("%Y-%m")
    d = d.sort_values("jour").reset_index(drop=True)
    seuil, statut = SEUILS[polluant]

    # Recalibration sur l'historique antérieur seul — identique à recalibrer_amplitude.py.
    d["pred_qm"] = np.nan
    for m in sorted(d["mois"].unique()):
        hist, cur = d[d["mois"] < m], d["mois"] == m
        if len(hist) < 500:
            continue
        d.loc[cur, "pred_qm"] = cartographie_quantiles(
            hist["pred"].to_numpy(), hist["valeur"].to_numpy(),
            d.loc[cur, "pred"].to_numpy())
    e = d.dropna(subset=["pred_qm"]).reset_index(drop=True)

    obs = e["valeur"].to_numpy()
    v = obs > seuil
    N = int(v.sum())
    a_ref = e["cams_jour"].to_numpy() > seuil
    a_nous = e["pred_qm"].to_numpy() > seuil
    echeance = "J0 (jour même)" if horizon == 1 else f"J+{horizon - 1} (lendemain)"
    print(f"{polluant} · {len(e):,} jours-station · {N} dépassements · {echeance}",
          flush=True)
    if N < 30:
        print(f"  ⚠️ {N} dépassements — figures produites, conclusions à ne pas tirer.")

    # ── ① Le biais ────────────────────────────────────────────────────────────
    biais = [("prévision brute", float(np.mean(e["cams_jour"] - obs)), ROUGE),
             ("notre correction", float(np.mean(e["pred"] - obs)), VERT)]
    svg_biais = barres(biais, " µg/m³")

    # ── ② Le compteur ─────────────────────────────────────────────────────────
    tp_ref, fp_ref = int((v & a_ref).sum()), int((~v & a_ref).sum())
    tp_nous, fp_nous = int((v & a_nous).sum()), int((~v & a_nous).sum())
    svg_compteur = barres([
        ("épisodes réellement survenus", N, "#6b6a63"),
        ("vus par la prévision brute", tp_ref, BLEU),
        ("vus par notre correction", tp_nous, VERT),
        ("fausses alertes — brute", fp_ref, ORANGE),
        ("fausses alertes — nous", fp_nous, ORANGE)], "")

    # ── ③ Le calendrier des désaccords ────────────────────────────────────────
    cal, comptes = calendrier(e, v, a_ref, a_nous)

    # ── ④ Le taux de change ───────────────────────────────────────────────────
    svg_courbe = courbe(taux_de_change(v, e["cams_jour"].to_numpy()),
                        taux_de_change(v, e["pred"].to_numpy()), N)

    nom = NOM[polluant]
    html = f"""<title>{nom} — ce que la correction change à la décision</title>
<style>
.doc{{--plane:#0d0d0d;--surface:#1a1a19;--txt:#fff;--txt2:#c3c2b7;--bd:rgba(255,255,255,.12);
 background:var(--plane);color:var(--txt);font-family:system-ui,-apple-system,sans-serif;
 line-height:1.6;margin:0}}
.shell{{max-width:1180px;margin:0 auto;padding:0 clamp(14px,3vw,28px) 60px}}
h1{{font-size:clamp(1.5rem,3.4vw,2.1rem);letter-spacing:-.02em;margin:1.2em 0 .1em}}
h2{{font-size:1.06rem;margin:0 0 .1em;letter-spacing:-.01em}}
.lede{{color:var(--txt2);max-width:72ch;margin:.3em 0 1.6em}}
.bloc{{background:var(--surface);border:1px solid var(--bd);border-radius:10px;
 padding:16px 18px;margin:16px 0}}
.sous{{color:var(--txt2);font-size:.85rem;margin:.1em 0 14px;max-width:72ch}}
.cle{{font-size:1.32rem;font-weight:660;letter-spacing:-.01em;margin:12px 0 0}}
.cle span{{color:var(--txt2);font-size:.86rem;font-weight:400;display:block}}
.defile{{overflow-x:auto;padding-bottom:2px}}
.cal{{position:relative}}
.cal img{{display:block;width:100%;height:auto;image-rendering:pixelated;border-radius:3px}}
.reperes{{position:relative;height:15px;margin-top:3px}}
.an{{position:absolute;font-size:.72rem;font-weight:650;color:var(--txt);
 border-left:2px solid rgba(255,255,255,.5);padding-left:4px}}
.leg{{display:flex;gap:18px;flex-wrap:wrap;font-size:.8rem;color:var(--txt2);margin-top:10px}}
.leg i{{width:11px;height:11px;border-radius:2px;display:inline-block;margin-right:5px;
 vertical-align:-1px}}
.note{{background:var(--surface);border:1px solid var(--bd);border-left:3px solid #eb6834;
 border-radius:10px;padding:14px 18px;margin:22px 0}}
p{{max-width:74ch}}
footer{{color:var(--txt2);font-size:.78rem;border-top:1px solid var(--bd);
 margin-top:30px;padding:18px 0}}
</style>
<div class="doc"><div class="shell">
<h1>{nom} — ce que la correction change à la décision</h1>
<p class="lede">Échéance <b>{echeance}</b>. Seuil de <b>{seuil:.0f} µg/m³</b> ({statut}).
Période de {e['mois'].nunique()} mois, {len(e):,} journées-station,
<b>{N} dépassements réellement survenus</b>. Chaque station est prédite par un modèle qui
ne l'a jamais vue, sur un mois qu'il n'a jamais vu.</p>

<div class="bloc"><h2>① La prévision brute est systématiquement trop basse</h2>
<p class="sous">Écart moyen entre ce qui est annoncé et ce qui est mesuré. À gauche du trait :
sous-estimation.</p>{svg_biais}
<p class="cle">{biais[0][1]:+.1f} µg/m³ → {biais[1][1]:+.1f} µg/m³
<span>le biais disparaît après correction</span></p></div>

<div class="bloc"><h2>② Sur {N} épisodes réels, combien sont vus ?</h2>
<p class="sous">En nombre de journées-station, pas en pourcentage. Les fausses alertes sont
comptées sur la même période.</p>{svg_compteur}
<p class="cle">{tp_ref} → {tp_nous} épisodes détectés
<span>et {fp_ref} → {fp_nous} fausses alertes</span></p></div>

<div class="bloc"><h2>③ Les journées où les deux ne disent pas la même chose</h2>
<p class="sous">Un trait par jour. Au-dessus de la ligne : les journées où <b>notre
correction alerte et la prévision brute non — alors qu'un dépassement a bien eu lieu</b>.
En dessous : l'inverse.</p>
{cal}
<div class="leg"><span><i style="background:{VERT}"></i>journées gagnées :
<b>{comptes['sauve']}</b></span>
<span><i style="background:{ROUGE}"></i>journées perdues : <b>{comptes['perdu']}</b></span>
<span><i style="background:#6b6a63"></i>vues par les deux : {comptes['commun']}</span>
<span><i style="background:#3a3a37"></i>manquées par les deux : {comptes['manque']}</span></div>
<p class="cle">{comptes['sauve']} gagnées contre {comptes['perdu']} perdues
<span>au prix de {fp_nous - fp_ref:+,d} fausses alertes — c'est l'échange, pas un gain
gratuit. Le panneau ④ montre à quelle vitesse il se dégrade.</span></p></div>

<div class="bloc"><h2>④ Combien d'épisodes de plus par fausse alerte acceptée ?</h2>
<p class="sous">Chaque courbe montre, pour un nombre de fausses alertes toléré, combien
d'épisodes sont détectés. Plus la courbe monte vite, plus le système est utile à qui doit
décider.</p>{svg_courbe}
<div class="leg"><span><i style="background:{BLEU}"></i>prévision brute</span>
<span><i style="background:{VERT}"></i>notre correction</span></div></div>

<div class="note">
<p><b>Ce que ces figures comparent.</b> La référence est la <b>prévision CAMS Europe
brute</b>, librement accessible. Ce n'est pas le produit d'une association agréée de
surveillance, qui repose sur un modèle national plus fin, assimilé et déjà corrigé
statistiquement. Aucune de ces figures ne dit ce que la méthode ferait face à une telle
chaîne.</p>
<p><b>Et ce qu'elles coûtent.</b> Le panneau ③ utilise une correction recalibrée en
distribution : elle détecte davantage d'épisodes <b>et déclenche davantage de fausses
alertes</b>. Le panneau ④ montre précisément cet échange ; il n'y a pas de réglage
gratuit.</p>
</div>
<footer>Prévisions Copernicus CAMS Europe · observations LCSQA ·
généré par <code>scripts/figures_decision.py</code></footer>
</div></div>"""

    (RACINE / "reports/figures").mkdir(parents=True, exist_ok=True)
    sortie = RACINE / f"reports/figures/decision_{polluant.lower()}_h{horizon}.html"
    sortie.write_text(html, encoding="utf-8")
    print(f"  ① biais {biais[0][1]:+.2f} → {biais[1][1]:+.2f}")
    print(f"  ② détections {tp_ref} → {tp_nous} · fausses {fp_ref} → {fp_nous}")
    print(f"  ③ gagnées {comptes['sauve']} · perdues {comptes['perdu']} · "
          f"solde {comptes['sauve'] - comptes['perdu']:+d}")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--sans-typologie", action="store_true")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, not n.sans_typologie))
