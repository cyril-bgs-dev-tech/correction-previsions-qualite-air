# Rapport agent Grok — mission 48 h

*Mis à jour au fil de l’eau. Statut : Phases 1–3 **terminées** (30–31/07/2026).*

**Règles respectées :** pas d’édition de `presentation.html` / `LIVRABLE.md` / `app.py` / `figures/` ; un fit à la fois ; passe unitaire avant lot rolling-origin ; sorties en `.partiel` puis rename.

---

## Phase 1 — Audit de cohérence

**Livrable :** [`reports/AUDIT_COHERENCE.md`](AUDIT_COHERENCE.md)

| | |
|--|--|
| Fichiers scannés | `presentation.html`, `LIVRABLE.md`, `figures.html`, `app.py`, `PROGRAMME_RECHERCHE.md` |
| Signalements | **14 issues** dont **7 bloquants** |
| Sans trou bloquant | `app.py`, `PROGRAMME_RECHERCHE.md` |

**Top bloquants (correction humaine requise) :**

| # | Où | Problème |
|---|-----|----------|
| 1 | `LIVRABLE.md:323` | « battu de **13 %** en double aveugle » vs **+1,5 %** |
| 2 | prés. + LIVRABLE | MQI **0,39–0,87** vs VERITE **0,255 / 0,485 / 0,354** |
| 3 | `presentation.html:461` | « chiffre du dossier » max 8 h **+28,9 %** vs VERITE vs officiel **+21,5 %** |
| 4 | JS `D` prés. + figures | MOS O₃ **12,61** périmé |
| 5 | prés. / LIVRABLE | Spatial **+29,7 %** vs VERITE §7 **+19,4 %** — **trancher la source** |
| 6 | idem | Pire temporel **−35,5** vs VERITE **−14,6** |
| 7 | `figures.html:251` | Double aveugle **−13 %** introuvable |

**Phrase dossier autorisée :**  
> Les livrables HTML/Markdown contiennent encore des scores de fenêtres et de grains non alignés sur `VERITE_DOSSIER.md` ; la source unique n’est pas encore l’unique source affichée.

---

## Phase 2 — Jumeaux de défauts

Détail dans `AUDIT_COHERENCE.md` § Phase 2.

| Motif | Résultat |
|-------|----------|
| Regex multi-mois | Corrigé dans `extract_copernicus_stations` — pas de jumeau vivant |
| `columns` / altitude | Pas de jumeau apply |
| Jointure ERA5 morte | Déjà retirée de `test_hors_echantillon_2025` |
| **Grandeur `max_8h` en dur** | **JUMEAU confirmé** : `comparer_mos_officiel.py:116-117` appelle `journalier()` sans grandeur → NO₂/PM agrégés en max 8 h. Le jumeau **corrigé** est `comparer_mos_officiel_annee.py`. |

**Phrase dossier autorisée :**  
> Un script de comparaison au MOS officiel agrège encore tous les polluants en max 8 h par défaut ; la variante annuelle porte déjà le dictionnaire par polluant.

---

## Phase 3.1 — Rolling-origin O₃ max 8 h *(faite)*

| | |
|--|--|
| Script | `scripts/rolling_origin_o3.py` |
| Log | `reports/log_rolling_origin_O3.txt` |
| Sortie | `reports/rolling_origin_O3.csv` (16 plis) |

### Protocole

- `charger("O3",1)` → `agreger_journalier(..., "max_8h")`  
- Pour chaque mois M sauf le premier : train = `jour < début(M)`, test = mois M  
- Assert : `max(train) < min(test)` — **tous les plis OK**  
- LightGBM `REGLE`, résidu vs `cams_jour`, stations toutes vues  
- Réf. blocage conjoint annoncé : **+1,5 %**

### Passe unitaire

2024-06 : **82,8 s**, gain **−7,32 %**, ordre OK → extrapolation ~11–22 min — lot lancé.

### Résultats (16 mois : 2023-09 → 2024-12)

| Stat | Valeur |
|------|--------|
| Gain moyen | **+6,34 %** |
| Médiane | **+6,08 %** |
| σ (plis) | 8,76 |
| Pire | **−7,32 %** (2024-06) |
| Meilleur | **+21,42 %** (2024-12) |
| Plis négatifs | **4 / 16** (2023-09, 2024-05, 2024-06, 2024-09) |
| Saison ozone AMJJAS | moyenne **+1,13 %**, **4 négatifs / 7** |

Tous les `ok_ordre=True`.

### Critère d’enterrement

> *Enterré si gain prospectif ≈ +1,5 % avec même dispersion.*

**Non enterré au sens « le protocole conjoint surestimait »** : le rolling-origin est **plus favorable en moyenne** (+6,3 % vs +1,5 %), et le pire (−7 %) est **bien moins violent** que le pire double-blocage (−41 %).  
**Le vocabulaire « double aveugle » reste abusif** pour le blocage conjoint (pas d’ordre temporel forcé).  
**La généralisation temporelle reste non démontrée** en saison ozone (+1 % moyen, majorité de plis faibles/négatifs).

### Phrase que le dossier a le droit d’écrire

> En validation **prospective stricte** (rolling-origin, train uniquement antérieur au mois testé, O₃ max 8 h, 16 mois), le gain moyen est de **+6,3 %** (pire **−7,3 %**, 4 plis négatifs). Ce n’est pas le protocole « mois caché » du dossier (+1,5 % en blocage conjoint station×mois) : le rolling-origin ne reproduit pas un effondrement à −40 %, mais **ne démontre pas non plus** une généralisation temporelle robuste en saison ozone (+1,1 % sur avril–septembre).

---

## Phase 3.2 — Dispersion intra-maille par strates *(faite)*

| | |
|--|--|
| Script | `scripts/dispersion_intra_maille_strates.py` |
| Sortie | `reports/dispersion_intra_maille_O3.csv` |
| Log | `reports/log_dispersion_intra_maille.txt` |

### Protocole

- Paires **simultanées** (même maille 0,1°, même **jour**, moyenne des obs horaires)  
- Strates : typologie homogène × bande de distance (0–2 / 2–5 / 5+ km)  
- Bootstrap **par maille** (500 tirages), IC95  

### Résultats O₃

| Strate | n_mailles | dispersion (µg/m³) | IC95 |
|--------|-----------|-------------------|------|
| background, 2–5 km | 12 | 6,28 | [4,80 ; 8,49] |
| background, 5 km+ | 9 | 5,62 | [4,04 ; 7,57] |
| **toutes** | 21 | **6,11** | **[5,04 ; 7,57]** |

- **Aucune paire trafic/industriel** dans une maille multi-stations du corpus MOS O₃ (seulement background + mixte absent).  
- Variation distance 2–5 vs 5+ : ~12 % (< 30 %).  
- IC relatif large (~40 % de la moyenne).  
- Valeur **6,11 ≠ 3,61** (l’ancien chiffre venait d’une autre construction — écart-type de résidus / autre grain).

### Critère d’enterrement

> *Enterré si variation < 30 % entre typologies et IC étroit → réhabiliter « plancher ».*

**Non réhabilité.** Une seule typologie exploitable ; IC non étroit ; le nombre 3,61 n’est pas reproduit. Le mot **plancher** reste interdit.

### Phrase dossier autorisée

> Sur paires simultanées jour×maille (O₃, 21 mailles multi-stations), la dispersion moyenne des observations est de **6,1 µg/m³** (IC95 bootstrap maille [5,0 ; 7,6]). Elle ne varie guère avec la distance au-delà de 2 km, mais le réseau ne fournit presque que des paires de fond : ce n’est **pas** une borne irréductible démontrée, ni le chiffre 3,61 antérieur.

---

## Phase 3.3 — Capteur d’anomalies, variables dynamiques *(faite)*

| | |
|--|--|
| Script | `scripts/capteur_dynamique_seul.py` |
| Sorties | `reports/capteur_dynamique_O3_dynamique.csv`, `..._era5.csv` |

### Protocole

- IForest hors station (3 plis), scores sur :  
  - **dynamique** : `cams_jour`, `cams_moy_jour`, calendrier circulaire (7 features)  
  - **era5** : 8 vars météo (+ lat/lon maille)  
- Mêmes Q1 (ruptures 13/11 & 03/12), Q2 (contrôle décile CAMS), Q3 (corriger vs s’abstenir sur décile haut) — sans modèle dédié CUDA.

### Verdicts

| Variante | Q1 dérive | Q2 au-delà de CAMS | Q3 politiques |
|----------|-----------|--------------------|---------------|
| dynamique | percentile **58** — aucun signal | constance **50 %** — non | corriger bat abstention de **+2,5 µg/m³** |
| era5 | percentile **61** — aucun signal | constance **90 %** — **oui** (sens : anormal → *plus* de gain) | corriger bat abstention de **+3,3 µg/m³** |

### Critère d’enterrement

> *Enterré si les trois verdicts inchangés → conclusion négative renforcée.*

**Partiellement enterré / renforcé :**  
- Sur **dynamique seule**, les trois questions restent négatives comme le script d’origine (pas de détection de rupture, pas de levier d’abstention).  
- Sur **ERA5**, Q2 change (le score dit quelque chose au-delà de CAMS) mais dans le **sens inverse** de l’hypothèse « anomalie = risque » : les jours anormaux météo sont ceux où corriger **gagne plus**. Q1 et Q3 restent négatifs pour un usage « couper la correction ».

### Phrase dossier autorisée

> Restreindre le détecteur d’anomalies aux variables dynamiques (CAMS + calendrier) ne fait pas apparaître les ruptures CAMS ni un régime où s’abstenir bat « corriger toujours ». Avec la météo ERA5, le score d’anomalie sépare le gain au-delà de CAMS, mais les jours « anormaux » sont ceux où la correction est **plus** utile — inutile comme coupe-circuit.

---

## Phase 3.4 — MQI par station *(faite)*

| | |
|--|--|
| Script | `scripts/mqi_par_station.py` |
| Sorties | `reports/mqi_par_station.csv` (842 lignes), `mqi_par_station_resume.csv` |

### Résultats (grain FAIRMODE v3.2, correction)

| Polluant | n stations | Taux MQI≤1 | Médiane | p90 | Pire |
|----------|------------|------------|---------|-----|------|
| O₃ max 8 h | 270 | **100 %** | 0,234 | 0,318 | 0,611 |
| NO₂ horaire | 343 | **98,5 %** | 0,383 | 0,633 | **1,239** |
| PM2,5 jour | 229 | **100 %** | 0,304 | 0,467 | 0,951 |

NO₂ trafic : conforme **95 %**, médiane 0,549, p90 0,794.

### Critère d’enterrement

> *Enterré si 100 % des stations conformes sur les trois polluants.*

**Non enterré pour NO₂** : **1,5 %** des stations (surtout trafic) ont MQI_correction > 1. O₃ et PM2,5 : l’agrégat ne masquait rien.

### Phrase dossier autorisée

> Au grain FAIRMODE, la correction est conforme (MQI≤1) sur **100 %** des stations O₃ et PM2,5. Pour le NO₂, **98,5 %** des stations sont conformes ; le pire MQI atteint **1,24** (stations trafic). L’agrégat national ne doit pas être cité comme une conformité station par station pour le NO₂.

---

## Fichiers produits par l’agent

| Fichier | Rôle |
|---------|------|
| `reports/AUDIT_COHERENCE.md` | Phase 1 + 2 |
| `reports/RAPPORT_AGENT.md` | Ce document |
| `scripts/rolling_origin_o3.py` | 3.1 |
| `reports/rolling_origin_O3.csv` | 3.1 résultats |
| `scripts/dispersion_intra_maille_strates.py` | 3.2 |
| `reports/dispersion_intra_maille_O3.csv` | 3.2 résultats |
| `scripts/capteur_dynamique_seul.py` | 3.3 |
| `reports/capteur_dynamique_O3_*.csv` | 3.3 résultats |
| `scripts/mqi_par_station.py` | 3.4 |
| `reports/mqi_par_station.csv` | 3.4 résultats |

---

## Synthèse exécutive (48 h)

1. **Livrable encore non gelé** sur VERITE (7 bloquants) — priorité humaine avant envoi.  
2. **Jumeau code** `comparer_mos_officiel.py` (max_8h pour tout polluant).  
3. **Rolling-origin** : +6,3 % moyen, pas de catastrophe −40 %, mais été fragile — reformuler la temporalité.  
4. **« Plancher » 3,61** : non réhabilité (dispersion paires ~6,1, une typologie).  
5. **Capteur d’anomalies** : conclusion négative opérationnelle renforcée (dynamique) ; ERA5 informative mais pas un coupe-circuit.  
6. **MQI** : OK O₃/PM ; **NO₂ pas 100 %** des stations.
