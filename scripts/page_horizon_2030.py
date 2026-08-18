#!/usr/bin/env python3
"""Page 09 — l'horizon 2030 : ce que la directive rend obligatoire, et le droit d'y servir.

Pourquoi cette page existe
----------------------------
Le dossier portait deux résultats qui n'étaient **dans aucune pièce publiée** — ni dans la
présentation, ni dans le README public, ni dans la fiche de portefeuille :

1. le comptage des stations qui basculent en dépassement au seuil **2030**, à air constant ;
2. la part de stations où le produit européen satisfait le **critère de qualité FAIRMODE**,
   et ce qu'y change la correction.

Pris séparément, chacun est un chiffre. **Multipliés, ils sont l'argument** : la directive
(UE) 2024/2881 abaisse les valeurs limites annuelles *et* rend la modélisation obligatoire
là où un seuil est dépassé — donc abaisser le seuil **multiplie mécaniquement** le nombre de
zones où modéliser devient une obligation légale. Et là où le modèle devient opposable, sa
qualité cesse d'être une affaire d'ingénieur : elle devient un point de contrôle.

Ce que cette page refuse de faire
-----------------------------------
**Elle ne confond pas les deux indicateurs FAIRMODE.** `MQI_f` (critère de *prévision*,
l'erreur du modèle rapportée à celle d'une persistance) et le MQI d'*évaluation*
(`RMSE / (β · RMS_U)`) répondent à deux questions différentes. Les citer côte à côte sans
les nommer produirait exactement le défaut que `CLAUDE.md` § 0-D interdit : une affirmation
comparative qui ne nomme pas son axe. Cette page ne publie que le **MQI_f**, et le dit.

**Elle ne cache pas que le critère n'est pas franchi partout.** FAIRMODE demande ≥ 90 % de
stations conformes. Dans la condition de déploiement — aucune observation locale — le NO₂
plafonne sous cette barre. Le chiffre est publié tel quel, à côté de celui qui la franchit.

**Elle dérive son échéance** de `aq.rapport.libelle_echeance`, jamais d'un libellé écrit à la
main : c'est l'erreur J0/J+1 qui a coûté deux fois à ce dossier.

Usage : python3 scripts/page_horizon_2030.py
Sortie : reports/figures/_p9_section.html · _p9_style.css · _p9_script.js · p9_donnees.json
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
FIG = RACINE / "reports/figures"
sys.path.insert(0, str(RACINE / "src"))

from aq.rapport import libelle_echeance  # noqa: E402

# L'horizon du banc FAIRMODE. `h2` = horizon 2 = échéances 25-48 h après la sortie 00 UTC,
# c'est-à-dire J+1 — et c'est `libelle_echeance` qui l'écrit, pas cette ligne.
HORIZON = 2

NOM = {"NO2": "NO₂", "PM10": "PM10", "O3": "O₃", "PM25": "PM2,5"}

# Valeurs limites en moyenne annuelle : (en vigueur, applicable au 1ᵉʳ janvier 2030).
# Source : directive (UE) 2024/2881, annexe I, tableau 1. L'ozone est absent parce qu'il n'a
# pas de valeur limite annuelle mais une valeur cible sur le maximum journalier 8 h.
VL = {"NO2": (40, 20), "PM10": (40, 20), "PM25": (25, 10)}

# Les treize départements d'Occitanie. Sert à nommer ceux qui n'ont AUCUNE station retenue —
# le cas que la directive confie explicitement à la modélisation.
DEPTS_OCCITANIE = [9, 11, 12, 30, 31, 32, 34, 46, 48, 65, 66, 81, 82]
REGION_OCCITANIE = 76

# FAIRMODE : une application satisfait le critère si au moins 90 % des stations ont MQI ≤ 1.
SEUIL_FAIRMODE_PCT = 90.0

# Les trois régimes du banc, dans l'ordre où ils se lisent : le produit brut, puis notre
# correction SANS aucune observation du point (la condition de déploiement), puis avec.
MODES = [
    ("RAW", "CAMS brut", "le produit européen tel qu'il est diffusé"),
    ("NO_LOCAL_OBS", "corrigé · PARTOUT",
     "aucune observation du point, pas même celle de la veille"),
    ("FULL", "corrigé · aux stations", "avec l'historique de la station"),
]


def _f(x: float, n: int = 1) -> str:
    """Décimale française. Un point décimal dans un dossier francophone est une faute."""
    return f"{x:.{n}f}".replace(".", ",")


def bloc_seuils() -> dict:
    """Le comptage 2030, lu dans `reports/seuils_2030.csv` — jamais recopié."""
    f = RACINE / "reports/seuils_2030.csv"
    if not f.exists():
        raise SystemExit(f"artefact absent : {f} — lancer d'abord scripts/seuils_2030.py")
    g = pd.read_csv(f)

    manque = [c for c in ("polluant", "station_id", "region", "departement",
                          "depasse_actuel", "depasse_2030", "bascule") if c not in g.columns]
    if manque:
        raise SystemExit(f"colonnes absentes de seuils_2030.csv : {manque}")

    lignes = []
    for p, (va, v30) in VL.items():
        s = g[g["polluant"] == p]
        if s.empty:
            continue
        lignes.append({
            "polluant": NOM.get(p, p), "vl_actuelle": va, "vl_2030": v30,
            "evaluees": int(len(s)),
            "depasse_actuel": int(s["depasse_actuel"].sum()),
            "depasse_2030": int(s["depasse_2030"].sum()),
            "bascule": int(s["bascule"].sum()),
        })
    if not lignes:
        raise SystemExit("seuils_2030.csv ne contient aucun des trois polluants attendus")

    def uniques(d, col):
        return int(d.loc[d[col], "station_id"].nunique())

    a, b = uniques(g, "depasse_actuel"), uniques(g, "depasse_2030")
    tot = int(g["station_id"].nunique())

    occ = g[g["region"] == REGION_OCCITANIE]
    territoire = None
    if not occ.empty:
        presents = set(occ["departement"].dropna().astype(int))
        sans = sorted(set(DEPTS_OCCITANIE) - presents)
        territoire = {
            "actuel": uniques(occ, "depasse_actuel"), "en_2030": uniques(occ, "depasse_2030"),
            "evaluees": int(occ["station_id"].nunique()),
            "depts_total": len(DEPTS_OCCITANIE), "depts_sans": len(sans),
            "sans": [f"{d:02d}" for d in sans],
        }

    return {"lignes": lignes, "union_actuel": a, "union_2030": b, "parc": tot,
            "territoire": territoire}


def bloc_fairmode() -> dict:
    """Le critère de qualité, lu dans les bancs `banc_lcsqa_<P>_h<N>_double.csv`.

    Le compte des polluants **présents** est publié : PM2,5 n'a pas de banc, et un tableau
    à trois lignes qui n'annonce pas qu'il en manque une se lit comme un tableau complet.
    """
    lignes, absents = [], []
    for p in ("NO2", "PM10", "O3", "PM25"):
        f = RACINE / f"reports/banc_lcsqa_{p}_h{HORIZON}_double.csv"
        if not f.exists():
            absents.append(NOM.get(p, p))
            continue
        t = pd.read_csv(f)
        if "part_stations_mqi_ok_pct" not in t.columns:
            absents.append(NOM.get(p, p))
            continue
        cellules = {}
        for cle, _lib, _sous in MODES:
            r = t[t["mode"] == cle]
            if r.empty or pd.isna(r["part_stations_mqi_ok_pct"].iloc[0]):
                continue
            cellules[cle] = {
                "part": float(r["part_stations_mqi_ok_pct"].iloc[0]),
                "mqi": float(r["mqi_f_median"].iloc[0]),
                "biais": float(r["biais"].iloc[0]),
            }
        if len(cellules) != len(MODES):
            absents.append(NOM.get(p, p))
            continue
        lignes.append({"polluant": NOM.get(p, p),
                       "stations": int(t[t["mode"] == "RAW"]["n_stations"].iloc[0]),
                       **{k: v for k, v in cellules.items()}})
    if not lignes:
        raise SystemExit("aucun banc FAIRMODE lisible — lancer scripts/banc_lcsqa.py")
    return {"lignes": lignes, "absents": absents,
            "modes": [{"cle": c, "libelle": l, "sous": s} for c, l, s in MODES],
            "seuil": SEUIL_FAIRMODE_PCT, "echeance": libelle_echeance(HORIZON)}


SECTION = """<!-- ══════════════════════ PAGE 9 ══════════════════════════════════════ -->
<section class="page" id="horizon2030">
  <div class="chapeau-page">
    <p class="eyebrow">Page 09 — L'horizon 2030</p>
    <h1>Ce que la directive rend obligatoire, et le droit d'y servir</h1>
    <p class="chapeau">
      La directive <strong>(UE) 2024/2881</strong> fait deux choses que l'on cite toujours
      séparément&#8239;: elle <strong>divise par deux</strong> les valeurs limites annuelles
      au 1<sup>er</sup> janvier 2030, et elle rend la <strong>modélisation obligatoire</strong>
      dans toute zone où un seuil est dépassé. Transposition au plus tard le
      <strong>11 décembre 2026</strong>.
    </p>
    <p class="these">
      Multipliées, elles donnent l'argument que ni l'une ni l'autre ne porte seule&#8239;:
      abaisser le seuil <strong>multiplie mécaniquement</strong> le nombre de zones où
      modéliser devient une obligation légale — <b id="p9-avant">—</b> stations en
      dépassement aujourd'hui, <b id="p9-apres">—</b> en 2030, un facteur
      <b id="p9-facteur">—</b>, <strong>sans qu'un gramme de plus ait été émis</strong>.
      Et là où le modèle devient opposable, sa qualité devient un <strong>point de
      contrôle</strong>.
    </p>
  </div>

  <div class="p9-bloc">
    <h3>① Le mur, compté sur le parc réel</h3>
    <p class="p9-sous" id="p9-sous-seuils">—</p>
    <div class="fig-scroll">
      <table class="p9-tab" id="p9-tab-seuils"></table>
    </div>
  </div>

  <div class="p9-bloc" id="p9-territoire-bloc">
    <h3>② Le territoire — et l'angle mort que la mesure ne peut pas couvrir</h3>
    <p class="p9-territoire" id="p9-territoire">—</p>
  </div>

  <div class="p9-bloc">
    <h3>③ Le droit d'y servir — le critère de qualité européen</h3>
    <p class="p9-sous" id="p9-sous-fairmode">—</p>
    <div class="fig-scroll">
      <table class="p9-tab" id="p9-tab-fairmode"></table>
    </div>
  </div>

  <div class="p9-lectures">
    <div class="reserve">
      <b>Le NO₂ est le cas critique, et ce n'est pas une coïncidence.</b> C'est à la fois le
      polluant dont le produit européen échoue le plus au critère de qualité, et celui dont
      la valeur limite est <strong>divisée par deux</strong>. Le brut sous-estime de
      <span class="p9-val" id="p9-biais-raw">—</span>&nbsp;µg/m³&#8239;; la correction ramène ce biais à
      <span class="p9-val" id="p9-biais-full">—</span>. C'est ce décalage qui le faisait perdre contre une simple
      répétition de la mesure d'avant-veille.
    </div>
    <div class="reserve">
      <b>Le critère n'est pas franchi partout, et le dire fait partie du résultat.</b>
      FAIRMODE demande <span class="p9-val" id="p9-seuil">—</span>&nbsp;% de stations conformes. Dans la condition
      de déploiement — <em>aucune observation du point</em> — le NO₂ reste
      <strong>sous cette barre</strong>&#8239;; il ne la franchit qu'aux stations
      instrumentées. <strong>Citer les deux chiffres, jamais un.</strong>
    </div>
    <div class="reserve">
      <b>Deux indicateurs FAIRMODE portent le même sigle, et ce ne sont pas les mêmes.</b>
      Cette page publie le <code>MQI_f</code> — critère de <strong>prévision</strong>, qui
      rapporte l'erreur du modèle à celle d'une <strong>persistance</strong>. Le MQI
      d'<strong>évaluation</strong> (<code>RMSE / (β·RMS_U)</code>, β&nbsp;=&nbsp;2) répond à
      une autre question et donne d'autres chiffres. Les mélanger produirait une comparaison
      dont l'axe n'est pas nommé.
    </div>
    <div class="reserve">
      <b>Ce que le comptage 2030 ne dit pas.</b> Les moyennes de 2025 ne sont pas une
      prévision de 2030 — les émissions baisseront d'ici là. Il mesure une chose et une
      seule&#8239;: <strong>l'effet du changement de seuil, à air constant</strong>. C'est
      exactement la question qu'une collectivité doit se poser aujourd'hui pour bâtir sa
      feuille de route, pas un pronostic.
    </div>
  </div>

  <p class="regle">
    Ce que cette page autorise à dire&#8239;: <em>« la directive multiplie les zones où
    modéliser devient obligatoire, et le produit européen brut n'y satisfait pas le critère
    de qualité sur le NO₂&#8239;; une correction apprise l'y amène — complètement aux
    stations instrumentées, presque partout ailleurs. »</em> Rien de plus.
  </p>
  <p class="sig3" id="p9-sig"></p>
</section>
"""

STYLE = """/* ── Page 09 · l'horizon 2030 ────────────────────────────────────────── */
.p9-bloc{border-left:3px solid var(--trait);padding-left:.85rem;margin:0 0 1.15rem}
.p9-bloc h3{margin:0 0 .12rem;font-size:1rem;letter-spacing:-.01em}
.p9-bloc .p9-sous{margin:0 0 .5rem;font-size:.82rem;opacity:.72}
.p9-territoire{margin:.3rem 0 0;font-size:.92rem;line-height:1.5}
.p9-tab{width:100%;border-collapse:collapse;font-size:.92rem}
.p9-tab th{text-align:right;font-size:.72rem;text-transform:uppercase;
  letter-spacing:.07em;padding:0 .5rem .35rem;border-bottom:1px solid var(--trait)}
.p9-tab th:first-child{text-align:left}
.p9-tab td{padding:.4rem .5rem;border-bottom:1px solid var(--trait);
  text-align:right;font-variant-numeric:tabular-nums}
.p9-tab td:first-child{text-align:left;font-weight:600}
.p9-tab tr:last-child td{border-bottom:0}
.p9-fort{font-weight:700}
/* Une valeur POSÉE DANS une réserve ne doit pas hériter de `.reserve > b`, qui est le
   sélecteur de son CHAPEAU : display block, mono, majuscules, 9,4 px. Chaque nombre
   devenait sa propre ligne de titre au milieu d'une phrase — visible seulement au rendu,
   jamais dans le HTML. */
.p9-val{font-weight:700;font-variant-numeric:tabular-nums}
/* Conforme / non conforme : la couleur DOUBLE le signe ✓/✗, elle ne le remplace jamais —
   une information portée par la seule teinte est perdue en impression noir et blanc comme
   pour un lecteur daltonien. */
.p9-ok{color:var(--accent);font-weight:700}
.p9-non{color:var(--refute);font-weight:700}
.p9-sousmode{display:block;font-size:.68rem;font-weight:400;text-transform:none;
  letter-spacing:0;opacity:.66;margin-top:.15rem}
.p9-lectures{display:flex;flex-direction:column;gap:.7rem;margin:1.1rem 0}
"""

SCRIPT = """(function(){
  var d = JSON.parse(document.getElementById("p9-data").textContent);
  var vf = function(x, n){ return x.toFixed(n === undefined ? 1 : n).replace('.', ','); };
  var pose = function(id, txt){ var e = document.getElementById(id); if (e) e.textContent = txt; };

  // ── La thèse DÉRIVE du comptage. Écrite en dur, elle se périmerait à la première
  // re-mesure sans que rien ne le signale — c'est le défaut que ce dossier traque.
  var s = d.seuils;
  pose("p9-avant", String(s.union_actuel));
  pose("p9-apres", String(s.union_2030));
  pose("p9-facteur", "×" + vf(s.union_2030 / Math.max(s.union_actuel, 1)));
  pose("p9-sous-seuils",
       "moyennes annuelles " + d.annee + ", taux de saisie ≥ " + vf(d.saisie_min * 100, 0)
       + " % · " + s.parc + " stations évaluées · l'ozone est exclu : il n'a pas de valeur "
       + "limite annuelle mais une valeur cible sur le maximum 8 h");

  var h = "<thead><tr><th>Polluant</th><th>VL en vigueur</th><th>VL 2030</th>"
        + "<th>Évaluées</th><th>&gt; en vigueur</th><th>&gt; 2030</th><th>Basculent</th>"
        + "</tr></thead><tbody>";
  s.lignes.forEach(function(l){
    h += "<tr><td>" + l.polluant + "</td>"
       + "<td>" + l.vl_actuelle + " µg/m³</td>"
       + "<td class=\\"p9-fort\\">" + l.vl_2030 + " µg/m³</td>"
       + "<td>" + l.evaluees + "</td>"
       + "<td>" + l.depasse_actuel + "</td>"
       + "<td class=\\"p9-fort\\">" + l.depasse_2030 + "</td>"
       + "<td class=\\"p9-fort\\">+" + l.bascule + "</td></tr>";
  });
  document.getElementById("p9-tab-seuils").innerHTML = h + "</tbody>";

  // ── Le territoire : publié seulement s'il existe dans les données.
  var t = s.territoire, bloc = document.getElementById("p9-territoire-bloc");
  if (!t) { if (bloc) bloc.style.display = "none"; }
  else {
    pose("p9-territoire",
         "En Occitanie, " + t.actuel + " station(s) en dépassement aujourd'hui, " + t.en_2030
         + " en 2030, sur " + t.evaluees + " évaluées. Et " + t.depts_sans + " des "
         + t.depts_total + " départements n'ont aucune station retenue (" + t.sans.join(", ")
         + ") : pour eux, la conformité 2030 ne peut pas être posée depuis la mesure. "
         + "C'est exactement le cas que la directive confie à la modélisation.");
  }

  // ── Le critère de qualité, un régime par colonne.
  var f = d.fairmode;
  pose("p9-seuil", vf(f.seuil, 0));
  pose("p9-sous-fairmode",
       "part des stations satisfaisant MQI_f ≤ 1, échéance " + f.echeance
       + " · le critère est atteint à partir de " + vf(f.seuil, 0) + " %"
       + (f.absents.length ? " · non mesuré sur : " + f.absents.join(", ") : ""));

  var g = "<thead><tr><th>Polluant</th><th>Stations</th>";
  f.modes.forEach(function(m){
    g += "<th>" + m.libelle + "<span class=\\"p9-sousmode\\">" + m.sous + "</span></th>";
  });
  g += "</tr></thead><tbody>";
  f.lignes.forEach(function(l){
    g += "<tr><td>" + l.polluant + "</td><td>" + l.stations + "</td>";
    f.modes.forEach(function(m){
      var c = l[m.cle], ok = c.part >= f.seuil;
      g += "<td class=\\"" + (ok ? "p9-ok" : "p9-non") + "\\">"
         + vf(c.part) + " %&#8239;" + (ok ? "✓" : "✗") + "</td>";
    });
    g += "</tr>";
  });
  document.getElementById("p9-tab-fairmode").innerHTML = g + "</tbody>";

  // ── Le biais NO₂ cité dans la réserve vient de la table, pas d'une saisie.
  var no2 = f.lignes.filter(function(l){ return l.polluant === "NO₂"; })[0];
  if (no2) {
    pose("p9-biais-raw", vf(no2.RAW.biais, 2));
    pose("p9-biais-full", vf(no2.FULL.biais, 2));
  }

  pose("p9-sig", "Seuils : directive (UE) 2024/2881, annexe I · comptage sur "
       + d.annee + " · critère de qualité : MQI_f à l'échéance " + f.echeance
       + " · généré le " + d.genere.replace("T", " "));
})();
"""


def main() -> int:
    seuils = bloc_seuils()
    fairmode = bloc_fairmode()

    donnees = {
        "genere": dt.datetime.now().isoformat(timespec="seconds"),
        "annee": 2025,          # dernière année pleine du corpus, cf. scripts/seuils_2030.py
        "saisie_min": 0.75,     # taux de saisie exigé pour retenir une station
        "seuils": seuils,
        "fairmode": fairmode,
    }

    (FIG / "p9_donnees.json").write_text(
        json.dumps(donnees, ensure_ascii=False), encoding="utf-8")
    (FIG / "_p9_section.html").write_text(SECTION, encoding="utf-8")
    (FIG / "_p9_style.css").write_text(STYLE, encoding="utf-8")
    (FIG / "_p9_script.js").write_text(SCRIPT, encoding="utf-8")

    # Contrôle de sortie : l'artefact, jamais le code de retour (§ 0-C).
    ecrits = [FIG / n for n in ("p9_donnees.json", "_p9_section.html",
                                "_p9_style.css", "_p9_script.js")]
    vides = [f.name for f in ecrits if not f.exists() or f.stat().st_size == 0]
    if vides:
        print(f"AUCUN fichier écrit (ou vide) : {vides}")
        return 1

    s, f = seuils, fairmode
    print(f"Page 09 · seuil 2030 : {s['union_actuel']} → {s['union_2030']} stations "
          f"(×{s['union_2030'] / max(s['union_actuel'], 1):.1f}) sur {s['parc']} évaluées")
    if s["territoire"]:
        t = s["territoire"]
        print(f"          Occitanie : {t['actuel']} → {t['en_2030']} · "
              f"{t['depts_sans']}/{t['depts_total']} départements sans station "
              f"({', '.join(t['sans'])})")
    print(f"          FAIRMODE {f['echeance']} · critère ≥ {SEUIL_FAIRMODE_PCT:.0f} % "
          f"· {len(f['lignes'])} polluants"
          + (f" · non mesuré : {', '.join(f['absents'])}" if f["absents"] else ""))
    for l in f["lignes"]:
        etat = " ".join(
            f"{c}={l[c]['part']:.1f}%{'✓' if l[c]['part'] >= SEUIL_FAIRMODE_PCT else '✗'}"
            for c, _, _ in MODES)
        print(f"            {l['polluant']:6s} {etat}")
    print("Écrit : " + " · ".join(str(f.relative_to(RACINE)) for f in ecrits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
