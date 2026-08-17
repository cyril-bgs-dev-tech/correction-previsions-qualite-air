#!/usr/bin/env python3
"""Page 07 — la barre réelle : leur PRODUIT, leur MÉTHODE, et ce que le réglage y change.

Pourquoi une page de plus, alors que la 04 donne déjà des gains
----------------------------------------------------------------
Toutes les pages précédentes comparent à **CAMS brut**, que personne ne consomme. Une
AASQA reçoit **PREV'AIR**. Cette page porte les deux seules confrontations qui n'aient rien
à neutraliser, et elles sont complémentaires par construction :

| | ce qui est comparé | fenêtre | ce que ça coûte |
|---|---|---|---|
| ① | leur **PRODUIT**, ligne à ligne | **~17 jours**, et le compte est DÉRIVÉ | ce n'est PAS PREV'AIR qui borne — voir ci-dessous |
| ② | leur **MÉTHODE**, depuis **leur** départ | **3 ans** | ce n'est plus leur produit, c'est leur famille de méthode |

Aucune des deux ne suffit seule : ① mesure la bonne chose sur trop peu de jours, ② mesure
sur trois ans une chose légèrement différente. Les publier ensemble est le seul cadrage
honnête — et l'écart entre les deux est lui-même une information.

③ Et la réserve qui ne pouvait pas rester une affirmation
-----------------------------------------------------------
`duel_chimere_krigeage.py` fige la variante de krigeage adverse pour ne pas « lui donner
deux chances quand nous n'en prenons qu'une ». C'était une précaution **non mesurée**. Elle
l'est désormais, des deux côtés — `optimisation_krigeage.py` et `gain_reglage.py` — et le
bloc ③ la rend au lecteur au lieu de la lui demander sur parole.

> **Avant d'écrire « attention, cette comparaison est imparfaite », se demander : est-ce
> que je peux la rendre équitable ?** (`CLAUDE.md` § 4 ter)

⚠️ Les chiffres viennent des CSV, jamais d'une saisie : la page est régénérée par ce script
à chaque changement de mesure. Un chiffre recopié à la main dans un fragment HTML est un
chiffre qui se périmera en silence.

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


# ══ ① Leur PRODUIT — le duel direct ═══════════════════════════════════════════════
#
# ⚠️ **Ce qui borne cette fenêtre n'est pas PREV'AIR** — mesuré le 16/08/2026, après y
# avoir cru et l'avoir écrit dans l'en-tête pendant deux semaines. Les trois sources, ce
# jour-là : PREV'AIR jusqu'au 16/08 (timer systemd, 21 jours d'affilée), CAMS brut jusqu'au
# 07/08, observations LCSQA jusqu'au 10/08. Le duel s'arrêtait au 08/08.
#
# La chaîne à rejouer pour l'étendre, et **chaque maillon est un plafond distinct** :
#   1. `download_copernicus.py --service cams_prevision`  (le `.nc` brut)
#   2. `extract_copernicus_stations.py --service cams_prevision`  ← **le maillon oublié** :
#      télécharger le `.nc` ne sert à rien tant que l'extraction aux stations n'est pas
#      refaite. C'est elle que `charger()` lit, pas le `.nc`.
#   3. `ingerer_lcsqa.py --debut … --fin …` puis `panel_unifie.py`  (les observations)
#   4. `duel_prevair.py --polluant <P>` pour les quatre
#
# Fait le 16/08 : la fenêtre est passée de **11 à 17 jours**, et les quatre écarts ont
# BAISSÉ de 4 à 14 points. Une fenêtre courte flattait — c'est la raison de dériver le
# compte plutôt que de l'écrire.
def bloc_produit() -> dict:
    lignes, jours, debuts, fins = [], [], [], []
    for p in NOM:
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
            "n": int(nous["n"]),
            "cams": round(float(brut["rmse"]), 2),
            "nous": round(float(nous["rmse"]), 2),
            "prevair": round(float(pv["rmse"]), 2),
            "ecart": round(100 * (float(pv["rmse"]) / float(nous["rmse"]) - 1), 1),
        })
        jours.append(int(nous["jours"]))
        debuts.append(str(nous["debut"]))
        fins.append(str(nous["fin"]))
    if not lignes:
        raise SystemExit("aucun duel_prevair_<P>.csv — lancer scripts/duel_prevair.py")
    return {"lignes": lignes, "jours_max": max(jours),
            "debut": min(debuts), "fin": max(fins)}


# ══ ② Leur MÉTHODE, depuis LEUR départ — trois ans ════════════════════════════════
def bloc_methode() -> dict:
    """§ 10 quinquies : CHIMERE brut → krigeage, contre la médiane CAMS → apprentissage.

    Le résultat à porter n'est PAS notre gain — c'est que le point de départ pèse autant
    que la méthode. Les six systèmes sont notés sur exactement les mêmes lignes.
    """
    # Les systèmes se retrouvent par leur PRÉFIXE, jamais par leur position dans le CSV
    # (§ 2 bis : nommer ce qu'on lit ; zéro et deux correspondances sont deux erreurs).
    cles = {"chimere": "CHIMERE brut", "chim_krig": "CHIMERE + krigeage",
            "cams": "CAMS médiane brute", "cams_krig": "CAMS + krigeage du biais",
            "nous": "CAMS + notre correction"}
    lignes, mois = [], None
    for p in NOM:
        f = RACINE / f"reports/duel_chimere_{p}_h2.csv"
        if not f.exists():
            continue
        t = pd.read_csv(f)
        pris = {}
        for cle, prefixe in cles.items():
            m = t[t["systeme"].str.startswith(prefixe)]
            # « CAMS + notre correction » préfixe aussi « … + krigeage » : on prend la
            # PLUS COURTE, sinon deux lignes correspondent et la table serait fausse.
            if len(m) == 0:
                raise SystemExit(f"{f.name} : aucun système « {prefixe} »")
            pris[cle] = float(m.loc[m["systeme"].str.len().idxmin(), "rmse"])
        lignes.append({
            "polluant": NOM[p], "n": int(t["n"].iloc[0]), **{k: round(v, 2)
                                                             for k, v in pris.items()},
            # Le départ, isolé : CHIMERE contre la médiane de l'ensemble dont il est membre.
            "depart_pct": round(100 * (1 - pris["chimere"] / pris["cams"]), 1),
            # Leur méthode sur leur départ : ce que le krigeage retire à CHIMERE.
            "leur_gain_pct": round(100 * (1 - pris["chim_krig"] / pris["chimere"]), 1),
            # À départ ÉGAL : apprentissage contre interpolation, tous deux sur CAMS.
            "krig_sur_cams_pct": round(100 * (1 - pris["cams_krig"] / pris["cams"]), 1),
            "nous_sur_cams_pct": round(100 * (1 - pris["nous"] / pris["cams"]), 1),
        })
        mois = int(t["n"].iloc[0])
    if not lignes:
        raise SystemExit("aucun duel_chimere_<P>_h2.csv — lancer "
                         "bash scripts/lot_duel_chimere.sh")
    # Les trois lectures que la table autorise, DÉRIVÉES et non écrites en dur : elles se
    # périmeraient à la première re-mesure sans que rien ne le signale (§ 2 ter).
    pires = [l for l in lignes if l["depart_pct"] < 0]
    return {"lignes": lignes,
            "n_depart_perdant": len(pires),
            "n_total": len(lignes),
            "pire_depart": round(min(l["depart_pct"] for l in lignes), 1),
            "leur_gain_max": round(max(l["leur_gain_pct"] for l in lignes), 1),
            "nous_devant": sum(1 for l in lignes
                               if l["nous_sur_cams_pct"] > l["krig_sur_cams_pct"]),
            "mois": mois}


# ══ ③ Et si on réglait les deux méthodes par polluant ? ═══════════════════════════
def bloc_reglage() -> dict:
    """La réserve « on ne leur donne pas deux chances », enfin chiffrée des deux côtés.

    ⚠️ Deux axes différents, et il faut le dire : leur krigeage est choisi sur la 1ʳᵉ
    moitié du calendrier et noté sur la 2ᵈᵉ (axe TEMPOREL) ; notre réglage est choisi par
    validation imbriquée sur des groupes de stations et noté sur des stations jamais
    consultées (axe SPATIAL). Les deux sont des hors-échantillon honnêtes, ce ne sont pas
    les mêmes hors-échantillon.

    🔴 **Et le dire ne suffisait pas** (règle D de `CLAUDE.md`, 16/08). Cette page a
    juxtaposé « nous +3,98 % » et « leur +1,01 % » avec la réserve en note, ce qu'un
    lecteur lit comme un facteur quatre. Mesuré sur LEUR axe, notre réglage vaut
    **−0,14 à +1,92 %** — du même ordre que le leur. La colonne temporelle est donc dans le
    tableau, pas dans une note : *la réserve ne tient pas lieu de mesure.*
    """
    lignes = []
    for p in NOM:
        fk = RACINE / f"reports/optimisation_krigeage_{p}_h2.csv"
        fn = RACINE / f"reports/gain_reglage_{p}.csv"
        ft = RACINE / f"reports/gain_reglage_{p}_temporel.csv"
        if not fk.exists():
            continue
        k = pd.read_csv(fk)
        k = k[k["depart"] == "CHIMERE"]
        if len(k) != 1:
            raise SystemExit(f"{fk.name} : {len(k)} ligne(s) pour le départ CHIMERE, 1 attendue")
        k = k.iloc[0]
        l = {"polluant": NOM[p],
             "leur_majorant": round(float(k["gain_majorant_pct"]), 2),
             "leur_honnete": round(float(k["gain_honnete_pct"]), 2),
             "leur_variante": str(k["variante_choisie_1re_moitie"]),
             "notre_gain": None, "notre_essais": None, "notre_gain_temporel": None}
        if fn.exists():
            n = pd.read_csv(fn).iloc[0]
            l["notre_gain"] = round(float(n["gain_reglage_pct"]), 2)
            l["notre_essais"] = int(n["essais_complets"])
        if ft.exists():
            l["notre_gain_temporel"] = round(
                float(pd.read_csv(ft)["gain_reglage_pct"].iloc[0]), 2)
        lignes.append(l)
    if not lignes:
        return {"lignes": [], "mesures": 0, "attendus": len(NOM)}
    faits = [l for l in lignes if l["notre_gain"] is not None]
    return {"lignes": lignes,
            "mesures": len(faits), "attendus": len(NOM),
            # Le périmètre EFFECTIF, pas le périmètre demandé (§ 2 quater).
            "leur_max": round(max(l["leur_honnete"] for l in lignes), 2),
            "leur_negatifs": sum(1 for l in lignes if l["leur_honnete"] < 0),
            "notre_min": round(min([l["notre_gain"] for l in faits]), 2) if faits else None,
            "notre_max": round(max([l["notre_gain"] for l in faits]), 2) if faits else None,
            # La mesure sur LEUR axe. Sans elle, la colonne « notre réglage » se lit comme
            # un facteur quatre sur la leur, ce qu'elle n'est pas.
            "tempo_min": round(min(t), 2) if (t := [l["notre_gain_temporel"] for l in lignes
                                                    if l["notre_gain_temporel"] is not None]) else None,
            "tempo_max": round(max(t), 2) if t else None,
            "tempo_mesures": len(t)}


def donnees() -> dict:
    return {"genere": datetime.now().isoformat(timespec="seconds"),
            "produit": bloc_produit(), "methode": bloc_methode(),
            "reglage": bloc_reglage()}


SECTION = """<!-- ══════════════════════ PAGE 7 ══════════════════════════════════════ -->
<section class="page" id="prevair">
  <div class="chapeau-page">
    <p class="eyebrow">Page 07 — La barre réelle</p>
    <h1>Contre le produit que les AASQA reçoivent vraiment</h1>
    <p class="chapeau">
      Tout ce qui précède se compare à <strong>CAMS brut</strong>, que personne ne
      consomme. Une AASQA reçoit <strong>PREV'AIR</strong>&#8239;: 1,7&nbsp;km, avec
      assimilation d'observations et krigeage. Cette page le confronte deux fois, et les
      deux lectures sont complémentaires par construction&#8239;: <strong>leur produit</strong>
      sur <b id="p7-jours3">—</b> jours, <strong>leur méthode</strong> sur trois ans.
    </p>
    <p class="these">
      Aucune des deux ne suffit seule. La première mesure exactement la bonne chose, sur
      <b id="p7-jours">—</b> jours&#8239;; la seconde mesure sur <strong>trois ans</strong>
      une chose légèrement différente — leur <em>famille de méthode</em>, pas leur produit.
      <strong>L'écart entre les deux est lui-même une information</strong>, et c'est
      pourquoi elles sont publiées ensemble plutôt qu'au choix.
    </p>
  </div>

  <h2 class="p7-h2"><span>①</span> Leur produit, ligne à ligne</h2>
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

  <h2 class="p7-h2"><span>②</span> Leur méthode, depuis leur point de départ</h2>
  <div class="p7-src">
    <b>Ce que la fenêtre de <span id="p7-jours4">—</span> jours interdisait</b> — PREV'AIR
    ne part pas de CAMS&#8239;:
    il part de <strong>CHIMERE</strong>, et son adaptation statistique <code>AS-CHI</code>
    <strong>krige</strong> le résidu observation−modèle au lieu de l'apprendre. Or CHIMERE
    est un <strong>membre de l'ensemble CAMS</strong>, archivé ici aux stations&#8239;: leur
    chaîne se rejoue donc sur <strong>nos lignes et sur trois ans</strong>. Les six systèmes
    sont notés sur <strong>exactement les mêmes lignes</strong>, échéance J+1, station cachée.
  </div>

  <div class="fig-scroll">
    <table class="p7-tab" id="p7-tab2"></table>
  </div>

  <p class="p7-cle" id="p7-cle"></p>

  <div class="p7-reserves">
    <div class="reserve">
      <b>Leur méthode fonctionne, et il faut le dire.</b> Le krigeage retire jusqu'à
      <b id="p7-leurgain">—</b>&nbsp;% de la RMSE de CHIMERE. Ce dossier ne conteste pas
      l'adaptation statistique de PREV'AIR&#8239;: il la mesure, puis se compare à elle à
      départ égal.
    </div>
    <div class="reserve rouge">
      <b>Ce n'est PAS PREV'AIR, et la nuance est décisive.</b> Leur CHIMERE tourne en
      configuration <strong>nationale</strong> — maille plus fine, inventaire français,
      assimilation de données&#8239;; le nôtre est le membre <strong>européen à 10&nbsp;km</strong>
      de l'ensemble CAMS. Ce tableau dit ce que leur <em>famille de méthode</em> vaut sur
      les entrées dont nous disposons. Il ne dit rien de leur produit — que seul le bloc
      ① mesure, sur <b id="p7-jours5">—</b> jours.
    </div>
  </div>

  <h2 class="p7-h2"><span>③</span> Et si l'on réglait les deux méthodes&#8239;?</h2>
  <div class="p7-src">
    Le bloc ② fige la variante de krigeage adverse — 30&nbsp;j · 200&nbsp;km · p=1 · même
    typologie — pour ne pas lui donner deux chances quand nous n'en prenons qu'une.
    <strong>C'était une précaution non mesurée</strong>, c'est-à-dire une réserve qu'il
    fallait croire sur parole. Elle est ici chiffrée <strong>des deux côtés</strong>&#8239;:
    on règle leur krigeage par polluant, on règle nos hyperparamètres par polluant, et on
    regarde qui y gagne quoi.
  </div>

  <div class="fig-scroll">
    <table class="p7-tab" id="p7-tab3"></table>
  </div>

  <p class="p7-cle" id="p7-cle3"></p>

  <div class="p7-reserves">
    <div class="reserve">
      <b>Deux hors-échantillon, pas le même.</b> Leur variante est choisie sur la
      <strong>première moitié du calendrier</strong> et notée sur la seconde — axe
      <em>temporel</em>. Notre réglage est choisi par validation imbriquée sur des
      <strong>groupes de stations</strong> et noté sur des stations jamais consultées — axe
      <em>spatial</em>. Les deux sont honnêtes&#8239;; ce ne sont pas les mêmes épreuves, et
      les additionner serait faux.
    </div>
    <div class="reserve">
      <b>Le majorant est là pour être écarté.</b> La colonne « au mieux » prend la
      meilleure des 100 variantes <em>sur les lignes qui la notent</em>&#8239;: c'est le biais
      de criblage, mesuré <strong>×2 à ×4</strong> sur ce dépôt. Elle borne ce que le
      réglage pourrait rapporter en trichant — la colonne citable est la suivante.
    </div>
  </div>

  <p class="regle">
    Ce que cette page autorise à dire&#8239;: <em>« sur la seule fenêtre où les deux
    produits sont comparables ligne à ligne, la correction fait mieux que l'adaptation
    statistique en service, sur les quatre polluants — sur <b id="p7-jours2">—</b> jours
    d'été&#8239;; et sur trois ans, à départ égal, l'apprentissage bat l'interpolation du
    biais sur <b id="p7-nousdevant">—</b> polluants sur <b id="p7-nbtot">—</b>. »</em>
    Rien de plus, et surtout pas un classement des deux <em>systèmes</em>.
  </p>
  <p class="sig3" id="p7-sig"></p>
</section>
"""

STYLE = """/* ── Page 07 · duel PREV'AIR ─────────────────────────────────────────── */
.p7-src{font-size:.92rem;line-height:1.6;margin:0 0 1.1rem}
.p7-h2{font-size:1.02rem;letter-spacing:.01em;margin:1.6rem 0 .7rem;
  display:flex;align-items:baseline;gap:.5rem}
.p7-h2 span{font-family:var(--mono,monospace);font-size:.86rem;opacity:.6}
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
.p7-tab .perd{color:#b4342b}
.p7-tab .sep{border-left:1px solid var(--bord,#d3dbe1)}
.p7-fen{font-size:.8rem;opacity:.72;font-variant-numeric:tabular-nums}
.p7-reserves{display:flex;flex-direction:column;gap:.7rem;margin:1.2rem 0}
.p7-cle{font-size:.94rem;line-height:1.62;margin:.9rem 0 0;padding:.7rem .9rem;
  border-left:3px solid var(--accent,#2f6f8f);background:var(--accent-pale,#eef4f8)}
.p7-attente{font-size:.84rem;opacity:.72;font-style:italic}
"""

SCRIPT = """(function(){
  var d = JSON.parse(document.getElementById("p7-data").textContent);
  var pr = d.produit, me = d.methode, rg = d.reglage;
  function pose(id, v){ var e = document.getElementById(id); if (e) e.textContent = v; }
  // Toutes les mentions de fenêtre et de compte DÉRIVENT de la donnée. Une seule écrite
  // en dur (« sur dix jours d'été ») contredisait déjà l'autre : PM10 en compte onze.
  ["p7-jours", "p7-jours2", "p7-jours3", "p7-jours4", "p7-jours5"]
    .forEach(function(id){ pose(id, pr.jours_max); });
  pose("p7-leurgain", me.leur_gain_max);
  pose("p7-nousdevant", me.nous_devant);
  pose("p7-nbtot", me.n_total);

  function tableau(id, entetes, corps){
    var t = document.getElementById(id); if (!t) return;
    t.innerHTML = '<thead><tr>' + entetes + '</tr></thead><tbody>' + corps + '</tbody>';
  }
  function num(v, n){ return v.toFixed(n === undefined ? 2 : n); }
  function signe(v, n){ return (v > 0 ? '+' : '') + v.toFixed(n === undefined ? 2 : n) + ' %'; }

  // ── ① leur produit ──────────────────────────────────────────────────────────
  tableau("p7-tab",
    '<th>Polluant</th><th>Fenêtre</th><th>Lignes</th><th>CAMS brut</th>'
    + '<th>Nous</th><th>PREV\\u2019AIR</th><th>Écart / nous</th>',
    pr.lignes.map(function(l){
      return '<tr><td>' + l.polluant + ' <span class="p7-fen">' + l.produit + '</span></td>'
        + '<td class="p7-fen">' + l.jours + ' j</td>'
        + '<td>' + l.n.toLocaleString("fr-FR") + '</td>'
        + '<td>' + num(l.cams) + '</td>'
        + '<td class="nous">' + num(l.nous) + '</td>'
        + '<td>' + num(l.prevair) + '</td>'
        + '<td class="ecart">+' + l.ecart.toFixed(1) + ' %</td></tr>';
    }).join(""));

  // ── ② leur méthode ──────────────────────────────────────────────────────────
  tableau("p7-tab2",
    '<th>Polluant</th><th>Lignes</th><th>CHIMERE brut</th>'
    + '<th>+ leur krigeage</th><th class="sep">CAMS médiane</th>'
    + '<th>+ krigeage</th><th>+ nous</th>',
    me.lignes.map(function(l){
      return '<tr><td>' + l.polluant + '</td>'
        + '<td class="p7-fen">' + l.n.toLocaleString("fr-FR") + '</td>'
        + '<td>' + num(l.chimere) + '</td>'
        + '<td>' + num(l.chim_krig) + '</td>'
        + '<td class="sep">' + num(l.cams) + '</td>'
        + '<td>' + num(l.cams_krig) + '</td>'
        + '<td class="nous">' + num(l.nous) + '</td></tr>';
    }).join(""));

  // La phrase clé est DÉRIVÉE : elle se périmerait en silence si on l'écrivait.
  var cle = document.getElementById("p7-cle");
  if (cle) cle.innerHTML =
    '<b>Le point de départ pèse autant que la méthode.</b> CHIMERE brut est plus mauvais '
    + 'que la <strong>médiane de l\\u2019ensemble dont il est membre</strong> sur '
    + '<strong>' + me.n_depart_perdant + ' polluants sur ' + me.n_total + '</strong> — '
    + 'jusqu\\u2019à <strong>' + Math.abs(me.pire_depart).toFixed(0) + ' %</strong>. '
    + 'Moyenner sept modèles vaut mieux que le meilleur d\\u2019entre eux, et aucune '
    + 'comparaison de méthodes ne le montre si les deux partent du même endroit.';

  // ── ③ le réglage, des deux côtés ────────────────────────────────────────────
  tableau("p7-tab3",
    '<th>Polluant</th><th>Leur krigeage, au mieux</th>'
    + '<th>Leur krigeage, honnête<br><small>axe temporel</small></th>'
    + '<th class="sep">Notre réglage<br><small>axe spatial</small></th>'
    + '<th>Notre réglage<br><small>axe temporel — le leur</small></th><th>Essais</th>',
    rg.lignes.map(function(l){
      var n = l.notre_gain === null
        ? '<td class="sep p7-attente">en cours</td><td class="p7-attente">—</td>'
          + '<td class="p7-attente">—</td>'
        : '<td class="sep nous">' + signe(l.notre_gain) + '</td>'
          + '<td class="' + (l.notre_gain_temporel < 0 ? 'perd' : '') + '">'
          + (l.notre_gain_temporel === null ? '—' : signe(l.notre_gain_temporel)) + '</td>'
          + '<td class="p7-fen">' + l.notre_essais + '</td>';
      return '<tr><td>' + l.polluant + '</td>'
        + '<td class="p7-fen">' + signe(l.leur_majorant) + '</td>'
        + '<td class="' + (l.leur_honnete < 0 ? 'perd' : '') + '">'
        + signe(l.leur_honnete) + '</td>' + n + '</tr>';
    }).join(""));

  var c3 = document.getElementById("p7-cle3");
  if (c3) {
    var t = '<b>Le figeage ne décide de rien.</b> Réglé par polluant sur son propre '
      + 'départ, leur krigeage gagne <strong>au plus ' + rg.leur_max.toFixed(2)
      + ' %</strong>, et il <strong>perd</strong> sur ' + rg.leur_negatifs + ' polluants '
      + 'sur ' + rg.lignes.length + ' — régler une interpolation sur le passé ne dit pas '
      + 'qu\\u2019elle sera meilleure ensuite.';
    if (rg.mesures > 0) {
      t += ' Notre méthode gagne <strong>'
        + rg.notre_min.toFixed(2) + ' à ' + rg.notre_max.toFixed(2) + ' %</strong> sur '
        + 'l\\u2019axe <strong>spatial</strong>'
        + (rg.mesures < rg.attendus
            ? ' (mesuré sur ' + rg.mesures + ' polluants sur ' + rg.attendus + ')' : '')
        + '.';
      // ⚠️ Sans la phrase qui suit, les deux colonnes se lisent comme un facteur quatre.
      // La réserve ne tient pas lieu de mesure : on a mesuré (règle D).
      if (rg.tempo_mesures > 0) {
        t += ' <strong>Mais les deux colonnes ne se comparent pas terme à terme :</strong> '
          + 'la leur est un hors-échantillon <strong>temporel</strong>, la nôtre '
          + '<strong>spatial</strong>. Rejoué sur <em>leur</em> axe, notre réglage vaut '
          + '<strong>' + rg.tempo_min.toFixed(2) + ' à ' + rg.tempo_max.toFixed(2)
          + ' %</strong> — <strong>du même ordre que le leur</strong>. Le gain du réglage '
          + 'est un phénomène de l\\u2019axe spatial ; ce qui se compare à armes égales est '
          + 'la colonne de droite.';
      }
    } else {
      t += ' Notre côté est en cours de mesure.';
    }
    c3.innerHTML = t;
  }

  var s = document.getElementById("p7-sig");
  if (s) s.textContent = "RMSE en µg/m³ · ① " + pr.debut + " → " + pr.fin
      + " · ② trois ans, station cachée, mêmes lignes pour les six systèmes"
      + " · généré le " + d.genere.replace("T", " ");
})();
"""


def main() -> int:
    d = donnees()
    (FIG / "p7_donnees.json").write_text(
        json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (FIG / "_p7_section.html").write_text(SECTION, encoding="utf-8")
    (FIG / "_p7_style.css").write_text(STYLE, encoding="utf-8")
    (FIG / "_p7_script.js").write_text(SCRIPT, encoding="utf-8")

    pr, me, rg = d["produit"], d["methode"], d["reglage"]
    print(f"① leur PRODUIT — {pr['jours_max']} jours")
    for l in pr["lignes"]:
        print(f"  {l['polluant']:6s} {l['jours']:2d} j · {l['n']:>6,} lignes · "
              f"CAMS {l['cams']:6.2f} · nous {l['nous']:6.2f} · "
              f"PREV'AIR {l['prevair']:6.2f} · écart +{l['ecart']:.1f} %")
    print("\n② leur MÉTHODE — trois ans, depuis leur départ")
    for l in me["lignes"]:
        print(f"  {l['polluant']:6s} {l['n']:>7,} lignes · CHIMERE {l['chimere']:6.2f} "
              f"→ {l['chim_krig']:6.2f} · CAMS {l['cams']:6.2f} → {l['cams_krig']:6.2f} "
              f"(krig) / {l['nous']:6.2f} (nous) · départ {l['depart_pct']:+.1f} %")
    print(f"  → départ perdant sur {me['n_depart_perdant']}/{me['n_total']} · "
          f"pire {me['pire_depart']:+.1f} % · nous devant l'interpolation "
          f"{me['nous_devant']}/{me['n_total']}")
    print(f"\n③ le RÉGLAGE des deux côtés — {rg['mesures']} polluants mesurés de notre "
          f"côté sur {rg['attendus']}")
    for l in rg["lignes"]:
        n = f"{l['notre_gain']:+.2f} %" if l["notre_gain"] is not None else "en cours"
        # La console montre les DEUX axes, comme la page. Un journal qui n'affiche que la
        # colonne flatteuse fait relire à l'opérateur autre chose que ce que lit le jury.
        t = ("—" if l["notre_gain_temporel"] is None
             else f"{l['notre_gain_temporel']:+.2f} %")
        print(f"  {l['polluant']:6s} leur krigeage {l['leur_honnete']:+.2f} % (temporel) "
              f"· nous {n} (spatial) / {t} (temporel, LEUR axe)")
    if rg.get("tempo_mesures"):
        print(f"  → sur leur axe, notre réglage vaut {rg['tempo_min']:+.2f} à "
              f"{rg['tempo_max']:+.2f} % — du même ordre que leur "
              f"{min(l['leur_honnete'] for l in rg['lignes']):+.2f} … "
              f"{rg['leur_max']:+.2f} %")

    print(f"\nÉcrit : 4 fragments p7 dans {FIG.relative_to(RACINE)} "
          f"· fenêtre ① {pr['debut']} → {pr['fin']} ({pr['jours_max']} j max)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
