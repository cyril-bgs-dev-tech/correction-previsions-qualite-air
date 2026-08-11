#!/usr/bin/env python3
"""Page 08 — où la correction NUIT, station par station.

Pourquoi cette page existe
--------------------------
Toutes les pages précédentes disent de combien la correction améliore. Aucune ne dit **où
elle dégrade**, alors qu'une correction apprise n'améliore jamais tout le monde. Le dossier
publie déjà sa mesure la plus dure — 2 épisodes réellement déclenchés détectés sur 33 — et
cette page est de la même famille : elle ne défend rien, elle mesure une limite.

Elle répare aussi une dette. Un ancien `REPRISE.md` annonçait « 23 % de stations dégradées »
et ce chiffre ne traçait **nulle part**. Il est retrouvé — c'est l'épreuve *temporelle* — et
il lui manquait l'essentiel : **son épreuve**. Sans elle il varie d'un facteur 20.

⚠️ Les chiffres viennent de `reports/stations_degradees_h2.csv`, jamais d'une saisie.

Usage : python3 scripts/page_stations_degradees.py
Sortie : reports/figures/_p8_section.html · _p8_style.css · _p8_script.js · p8_donnees.json
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
FIG = RACINE / "reports/figures"
NOM = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}
EPREUVES = [
    ("spatiale", "Station cachée", "le site n'a jamais été vu — déploiement sur un point non instrumenté"),
    ("temporelle", "Mois caché", "le site est connu, la période non — le régime normal d'exploitation"),
    ("double aveugle", "Les deux cachés", "l'épreuve la plus dure du dossier"),
]


def donnees() -> dict:
    f = RACINE / "reports/stations_degradees_h2.csv"
    if not f.exists():
        raise SystemExit("reports/stations_degradees_h2.csv absent — lancer "
                         "`bash scripts/lot_oof_typo.sh` puis `scripts/stations_degradees.py`")
    t = pd.read_csv(f)

    # Le point de toute la mesure : une seule variante pour les quatre polluants. Publier
    # une table qui en croiserait deux donnerait quatre lignes justes et une comparaison
    # fausse — la page LÈVE plutôt que de l'afficher.
    if len(v := set(t["variante"])) > 1:
        raise SystemExit(f"variantes mélangées {sorted(v)} — la page croiserait deux protocoles")

    blocs = []
    for cle, titre, sous in EPREUVES:
        g = t[t["epreuve"] == cle]
        if g.empty:
            raise SystemExit(f"épreuve « {cle} » absente du CSV — trouvées {sorted(set(t['epreuve']))}")
        blocs.append({
            "cle": cle, "titre": titre, "sous": sous,
            "lignes": [{"polluant": NOM[r.polluant],
                        "stations": int(r.n_stations),
                        "degradees": int(r.n_degradees),
                        "part": round(float(r.part_degradees_pct), 1),
                        "median": round(float(r.gain_median_pct), 1),
                        "pire": round(float(r.perte_pire_pct), 1)}
                       for r in g.sort_values("polluant").itertuples()],
        })
    return {"genere": datetime.now().isoformat(timespec="seconds"),
            "variante": str(t["variante"].iloc[0]),
            "n_min": int(t["n_min_par_station"].iloc[0]),
            "ecartees": int(t["n_stations_ecartees"].max()),
            "blocs": blocs}


SECTION = """<!-- ══════════════════════ PAGE 8 ══════════════════════════════════════ -->
<section class="page" id="degradees">
  <div class="chapeau-page">
    <p class="eyebrow">Page 08 — La limite</p>
    <h1>Où la correction nuit, et de combien</h1>
    <p class="chapeau">
      Tout ce qui précède dit de combien la correction améliore. Une correction apprise
      n'améliore pourtant <strong>jamais tout le monde</strong>. Cette page dit combien de
      stations elle <strong>dégrade</strong>, une par une, sur des prédictions
      hors-échantillon déjà produites — donc <strong>aucun choix d'après coup</strong>.
    </p>
    <p class="these">
      La part dégradée dépend de <strong>l'épreuve</strong> bien plus que du polluant&#8239;:
      elle va de <b id="p8-min">—</b> à <b id="p8-max">—</b> selon qu'on cache la station,
      la période, ou les deux. <strong>Un tel chiffre cité sans son épreuve ne veut rien
      dire</strong> — et ce dossier en a porté un pendant des semaines.
    </p>
  </div>

  <div class="p8-grille" id="p8-grille"></div>

  <div class="p8-lectures">
    <div class="reserve">
      <b>Le NO₂ se comporte à l'inverse des trois autres.</b> Il est le plus dégradé quand
      la station est cachée, et le moins quand elle est vue&#8239;; O₃, PM10 et PM2,5 font
      exactement le contraire. Ce n'est pas un défaut, c'est le <strong>mécanisme</strong>&#8239;:
      sur NO₂ l'essentiel du gain est un biais <strong>de site</strong>, donc il s'apprend
      quand le site est connu et se transfère mal.
    </div>
    <div class="reserve">
      <b>Une part élevée n'est pas une part grave.</b> Là où la dégradation touche le plus
      de stations, le <strong>gain médian est le plus faible</strong>&#8239;: la correction y
      est quasi neutre et le signe bascule d'une station à l'autre. Une part de 42&nbsp;%
      adossée à +2,5&nbsp;% de gain médian ne décrit pas le même risque qu'une part de
      8&nbsp;% adossée à +36&nbsp;%. <strong>Ne jamais citer l'une sans l'autre.</strong>
    </div>
    <div class="reserve">
      <b>Les pires stations perdent beaucoup</b>, et la moyenne ne le dilue pas. C'est
      l'argument le plus fort en faveur d'un <strong>aiguillage par station</strong> plutôt
      que d'une correction uniforme — une piste, pas un résultat&#8239;: elle n'a pas été
      mesurée.
    </div>
    <div class="reserve">
      <b>Réserve de périmètre.</b> Ces prédictions viennent de la pile
      <strong>sans l'étage <code>tendance</code></strong>, passé en production après leur
      calcul. Le sens de l'écart <strong>n'a pas été mesuré</strong>&#8239;: il n'est pas
      supposé favorable.
    </div>
  </div>

  <p class="regle">
    Ce que cette page autorise à dire&#8239;: <em>« la correction dégrade une minorité de
    stations quand le site est connu, et jusqu'à quatre sur dix quand il ne l'est pas — mais
    là où elle en dégrade le plus, elle n'apporte presque rien&#8239;; le risque est une
    neutralité bruitée, pas une perte. »</em> Rien de plus.
  </p>
  <p class="sig3" id="p8-sig"></p>
</section>
"""

STYLE = """/* ── Page 08 · où la correction nuit ─────────────────────────────────── */
.p8-grille{display:flex;flex-direction:column;gap:1.15rem;margin:.2rem 0 1.2rem}
.p8-bloc{border-left:3px solid var(--bord,#d3dbe1);padding-left:.85rem}
.p8-bloc h3{margin:0 0 .12rem;font-size:1rem;letter-spacing:-.01em}
.p8-bloc .p8-sous{margin:0 0 .5rem;font-size:.82rem;opacity:.72}
.p8-tab{width:100%;border-collapse:collapse;font-size:.92rem}
.p8-tab th{text-align:right;font-size:.72rem;text-transform:uppercase;
  letter-spacing:.07em;padding:0 .5rem .35rem;border-bottom:1px solid var(--bord,#d3dbe1)}
.p8-tab th:first-child{text-align:left}
.p8-tab td{padding:.4rem .5rem;border-bottom:1px solid var(--bord,#d3dbe1);
  text-align:right;font-variant-numeric:tabular-nums}
.p8-tab td:first-child{text-align:left;font-weight:600}
.p8-tab tr:last-child td{border-bottom:0}
.p8-part{font-weight:700}
.p8-lectures{display:flex;flex-direction:column;gap:.7rem;margin:1.1rem 0}
"""

SCRIPT = """(function(){
  var d = JSON.parse(document.getElementById("p8-data").textContent);
  // Les bornes de la thèse DÉRIVENT de la table : écrites en dur, elles se périmeraient
  // à la première re-mesure sans que rien ne le signale.
  var parts = [];
  d.blocs.forEach(function(b){ b.lignes.forEach(function(l){ parts.push(l.part); }); });
  var mn = Math.min.apply(null, parts), mx = Math.max.apply(null, parts);
  var e;
  if ((e = document.getElementById("p8-min"))) e.textContent = mn.toFixed(1) + " %";
  if ((e = document.getElementById("p8-max"))) e.textContent = mx.toFixed(1) + " %";

  var g = document.getElementById("p8-grille"); if (!g) return;
  var h = "";
  d.blocs.forEach(function(b){
    // Le tableau vit dans `.fig-scroll` — six colonnes de chiffres débordent sur un écran
    // étroit, et c'est LA PAGE qui se mettrait à défiler latéralement sans ce conteneur.
    // Même idiome que la page 07 : on n'invente pas un mécanisme, on réemploie le sien.
    h += '<div class="p8-bloc"><h3>' + b.titre + '</h3>'
       + '<p class="p8-sous">' + b.sous + '</p><div class="fig-scroll">'
       + '<table class="p8-tab"><thead><tr><th>Polluant</th><th>Stations</th>'
       + '<th>Dégradées</th><th>Part</th><th>Gain médian</th><th>Pire station</th>'
       + '</tr></thead><tbody>';
    b.lignes.forEach(function(l){
      h += '<tr><td>' + l.polluant + '</td>'
         + '<td>' + l.stations + '</td>'
         + '<td>' + l.degradees + '</td>'
         + '<td class="p8-part">' + l.part.toFixed(1) + ' %</td>'
         + '<td>' + (l.median >= 0 ? "+" : "") + l.median.toFixed(1) + ' %</td>'
         + '<td>' + l.pire.toFixed(1) + ' %</td></tr>';
    });
    h += '</tbody></table></div></div>';
  });
  g.innerHTML = h;

  var s = document.getElementById("p8-sig");
  if (s) s.textContent = "Échéance J+1 · variante « " + d.variante + " » · au moins "
      + d.n_min + " jours par station (" + d.ecartees
      + " écartée(s) au plus, compte publié) · généré le " + d.genere.replace("T", " ");
})();
"""


def main() -> int:
    d = donnees()
    (FIG / "p8_donnees.json").write_text(
        json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (FIG / "_p8_section.html").write_text(SECTION, encoding="utf-8")
    (FIG / "_p8_style.css").write_text(STYLE, encoding="utf-8")
    (FIG / "_p8_script.js").write_text(SCRIPT, encoding="utf-8")
    parts = [l["part"] for b in d["blocs"] for l in b["lignes"]]
    for b in d["blocs"]:
        print(f"  {b['titre']:18s} " + " · ".join(
            f"{l['polluant']} {l['part']:4.1f} % (méd. {l['median']:+.1f} %)"
            for l in b["lignes"]))
    print(f"\nÉcrit : 4 fragments p8 dans {FIG.relative_to(RACINE)} "
          f"· part de {min(parts):.1f} % à {max(parts):.1f} %")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
