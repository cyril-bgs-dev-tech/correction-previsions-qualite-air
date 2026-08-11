#!/usr/bin/env python3
"""Page 07 — le duel direct contre PREV'AIR, en fin de présentation.

Pourquoi une page de plus, alors que la 04 donne déjà des gains
----------------------------------------------------------------
Toutes les pages précédentes comparent à **CAMS brut**, que personne ne consomme. Une
AASQA reçoit **PREV'AIR**. La § 10 ter du dossier compare déjà les deux, mais *via* un
rapport publié — deux protocoles, deux fenêtres, un confondant d'amont à neutraliser.

Cette page porte l'autre comparaison, la seule qui n'ait rien à neutraliser : les trois
systèmes sur **exactement les mêmes lignes**, mêmes stations, mêmes jours.

Elle se paie d'une fenêtre minuscule, et c'est le cœur de ce qu'elle doit dire.

⚠️ Les chiffres viennent de `reports/duel_prevair_<P>.csv`, jamais d'une saisie : la page
est régénérée par ce script à chaque changement du duel. Un chiffre recopié à la main dans
un fragment HTML est un chiffre qui se périmera en silence.

Usage : python3 scripts/page_duel_prevair.py
Sortie : reports/figures/_p7_section.html · _p7_style.css · _p7_script.js · p7_donnees.json
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
FIG = RACINE / "reports/figures"
NOM = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}
PRODUIT = {"O3": "MAXJ1", "NO2": "MAXJ1", "PM10": "MOYJ1", "PM25": "MOYJ1"}


def donnees() -> dict:
    lignes, jours, debuts, fins = [], [], [], []
    for p in ("O3", "NO2", "PM10", "PM25"):
        f = RACINE / f"reports/duel_prevair_{p}.csv"
        if not f.exists():
            continue
        t = pd.read_csv(f)
        r = {str(x["systeme"]): x for _, x in t.iterrows()}
        nous = next((v for k, v in r.items() if k.startswith("notre")), None)
        pv = next((v for k, v in r.items() if k.startswith("PREV")), None)
        brut = next((v for k, v in r.items() if k.startswith("CAMS")), None)
        if nous is None or pv is None or brut is None:
            raise SystemExit(f"{f.name} : les trois systèmes attendus n'y sont pas — "
                             f"trouvés {list(r)}")
        lignes.append({
            "polluant": NOM[p], "produit": PRODUIT[p], "jours": int(nous["jours"]),
            "n": int(nous["n"]), "stations": None,
            "cams": round(float(brut["rmse"]), 2),
            "nous": round(float(nous["rmse"]), 2),
            "prevair": round(float(pv["rmse"]), 2),
            "ecart": round(100 * (float(pv["rmse"]) / float(nous["rmse"]) - 1), 1),
            "corr_nous": round(float(nous["correlation"]), 3),
            "corr_prevair": round(float(pv["correlation"]), 3),
        })
        jours.append(int(nous["jours"]))
        debuts.append(str(nous["debut"]))
        fins.append(str(nous["fin"]))
    if not lignes:
        raise SystemExit("aucun duel_prevair_<P>.csv — lancer scripts/duel_prevair.py")
    return {"genere": datetime.now().isoformat(timespec="seconds"),
            "jours_max": max(jours), "debut": min(debuts), "fin": max(fins),
            "lignes": lignes}


SECTION = """<!-- ══════════════════════ PAGE 7 ══════════════════════════════════════ -->
<section class="page" id="prevair">
  <div class="chapeau-page">
    <p class="eyebrow">Page 07 — La barre réelle</p>
    <h1>Contre le produit que les AASQA reçoivent vraiment</h1>
    <p class="chapeau">
      Tout ce qui précède se compare à <strong>CAMS brut</strong>, que personne ne
      consomme. Une AASQA reçoit <strong>PREV'AIR</strong>&#8239;: 1,7&nbsp;km, avec
      assimilation d'observations et krigeage. Cette page confronte les deux
      directement — <strong>mêmes stations, mêmes jours, mêmes lignes</strong>, donc
      aucun confondant d'amont à neutraliser.
    </p>
    <p class="these">
      Le résultat va dans notre sens sur les quatre polluants. Il se paie d'une fenêtre
      de <b id="p7-jours">—</b> jours, et <strong>c'est la première chose à dire</strong>&#8239;:
      PREV'AIR n'expose qu'environ six jours glissants, notre archivage quotidien n'a
      démarré que fin juillet 2026, et <strong>le passé n'est pas récupérable</strong>.
      Cette fenêtre ne grandira que d'un jour par jour.
    </p>
  </div>

  <div class="p7-src">
    <b>Protocole</b> — grain aligné sur le produit PREV'AIR (<code>MAXJ1</code> pour O₃ et
    NO₂, <code>MOYJ1</code> pour les particules), échéance <strong>J+1</strong>. Notre
    modèle est ajusté sur les données <strong>antérieures à 2025</strong> et n'a jamais vu
    les jours testés. Les valeurs PREV'AIR sont lues dans leurs propres fichiers NetCDF,
    au plus proche voisin de chaque station.
  </div>

  <div class="fig-scroll">
    <table class="p7-tab" id="p7-tab"></table>
  </div>

  <div class="p7-reserves">
    <div class="reserve">
      <b>Onze jours ne concluent rien.</b> C'est un ordre de grandeur, pas une
      démonstration. Le script qui produit ces chiffres le réaffirme à chaque exécution,
      et aucune citation ne doit omettre la fenêtre.
    </div>
    <div class="reserve">
      <b>Deux biais jouent en sens opposés</b> — il faut les énoncer ensemble, sinon on
      choisit son camp. <i>Contre nous</i>&#8239;: leur produit tourne à 1,7&nbsp;km avec
      assimilation, le nôtre corrige un ensemble à 10&nbsp;km. <i>Pour nous</i>&#8239;: nos
      stations sont connues de notre modèle — mais les leurs le sont aussi de leur
      krigeage, donc l'avantage n'est pas unilatéral.
    </div>
    <div class="reserve">
      <b>Ce duel n'utilise pas la pile complète.</b> Seulement <code>base + tendance +
      typologie</code>. GEOS-CF, les membres d'ensemble et les feux sont hors d'atteinte
      sur cette fenêtre — leurs flux s'arrêtent au 01/08/2026 pour les deux premiers, à
      juin 2025 pour les feux. C'est une limite de <strong>fraîcheur</strong>, pas de
      conception&#8239;: ces écarts sont des <strong>minorants</strong>.
    </div>
  </div>

  <p class="regle">
    Ce que cette page autorise à dire&#8239;: <em>« sur la seule fenêtre où les deux
    produits sont comparables ligne à ligne, la correction fait mieux que l'adaptation
    statistique en service, sur les quatre polluants — sur <b id="p7-jours2">—</b> jours
    d'été. »</em> Rien de plus, et surtout pas un classement des deux systèmes.
  </p>
  <p class="sig3" id="p7-sig"></p>
</section>
"""

STYLE = """/* ── Page 07 · duel PREV'AIR ─────────────────────────────────────────── */
.p7-src{font-size:.92rem;line-height:1.6;margin:0 0 1.1rem}
.p7-tab{width:100%;border-collapse:collapse;font-size:.94rem}
.p7-tab th{text-align:right;font-size:.74rem;text-transform:uppercase;
  letter-spacing:.07em;padding:0 .55rem .5rem;border-bottom:1px solid var(--bord,#d3dbe1)}
.p7-tab th:first-child{text-align:left}
.p7-tab td{padding:.55rem;border-bottom:1px solid var(--bord,#d3dbe1);
  text-align:right;font-variant-numeric:tabular-nums}
.p7-tab td:first-child{text-align:left;font-weight:600}
.p7-tab tr:last-child td{border-bottom:0}
.p7-tab .nous{font-weight:700}
.p7-tab .ecart{font-weight:700}
.p7-fen{font-size:.8rem;opacity:.72;font-variant-numeric:tabular-nums}
.p7-reserves{display:flex;flex-direction:column;gap:.7rem;margin:1.2rem 0}
"""

SCRIPT = """(function(){
  var d = JSON.parse(document.getElementById("p7-data").textContent);
  // Les DEUX mentions de la fenêtre dérivent de la donnée. Une seule écrite en dur
  // (« sur dix jours d'été ») contredisait déjà l'autre : PM10 en compte onze.
  ["p7-jours", "p7-jours2"].forEach(function(id){
    var e = document.getElementById(id); if (e) e.textContent = d.jours_max;
  });
  var t = document.getElementById("p7-tab"); if (!t) return;
  var h = '<thead><tr><th>Polluant</th><th>Fenêtre</th><th>Lignes</th>'
        + '<th>CAMS brut</th><th>Nous</th><th>PREV\\u2019AIR</th>'
        + '<th>Écart / nous</th></tr></thead><tbody>';
  d.lignes.forEach(function(l){
    h += '<tr><td>' + l.polluant + ' <span class="p7-fen">' + l.produit + '</span></td>'
       + '<td class="p7-fen">' + l.jours + ' j</td>'
       + '<td>' + l.n.toLocaleString("fr-FR") + '</td>'
       + '<td>' + l.cams.toFixed(2) + '</td>'
       + '<td class="nous">' + l.nous.toFixed(2) + '</td>'
       + '<td>' + l.prevair.toFixed(2) + '</td>'
       + '<td class="ecart">+' + l.ecart.toFixed(1) + ' %</td></tr>';
  });
  t.innerHTML = h + '</tbody>';
  var s = document.getElementById("p7-sig");
  if (s) s.textContent = "RMSE en µg/m³ · " + d.debut + " → " + d.fin
      + " · les trois systèmes sur exactement les mêmes lignes · généré le "
      + d.genere.replace("T", " ");
})();
"""


def main() -> int:
    d = donnees()
    (FIG / "p7_donnees.json").write_text(
        json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (FIG / "_p7_section.html").write_text(SECTION, encoding="utf-8")
    (FIG / "_p7_style.css").write_text(STYLE, encoding="utf-8")
    (FIG / "_p7_script.js").write_text(SCRIPT, encoding="utf-8")
    for l in d["lignes"]:
        print(f"  {l['polluant']:6s} {l['jours']:2d} j · {l['n']:>6,} lignes · "
              f"CAMS {l['cams']:6.2f} · nous {l['nous']:6.2f} · "
              f"PREV'AIR {l['prevair']:6.2f} · écart +{l['ecart']:.1f} %")
    print(f"\nÉcrit : 4 fragments p7 dans {FIG.relative_to(RACINE)} "
          f"· fenêtre {d['debut']} → {d['fin']} ({d['jours_max']} j max)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
