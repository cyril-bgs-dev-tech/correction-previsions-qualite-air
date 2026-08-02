# Audit de cohérence — livrables vs `reports/VERITE_DOSSIER.md`

*Agent Grok · 30–31/07/2026. Lecture seule des livrables (aucune édition).  
Référence : `VERITE_DOSSIER.md` généré le 30/07/2026 21 h 12.*

**Périmètre scanné :**  
`reports/figures/presentation.html` · `LIVRABLE.md` · `reports/figures/figures.html` ·  
`app.py` · `docs/PROGRAMME_RECHERCHE.md`  

**Hors périmètre (chiffres datés attendus) :** autres `docs/*.md` d’échanges relecteurs.

---

## Tableau des signalements

| # | fichier:ligne | valeur publiée | valeur de référence (VERITE) | nature | gravité |
|---|---------------|----------------|------------------------------|--------|---------|
| 1 | `LIVRABLE.md:323` | Titre « CAMS est battu — de **13 %** en double aveugle » | Double aveugle réglage retenu **+1,5 %** (pire −41,4 %) · §7 | portée abusive | **bloquant** |
| 2 | `presentation.html:323-324` · `LIVRABLE.md:164-168` | MQI « **0,39 à 0,87** », « conforme partout » sans grain FAIRMODE | MQI bon grain O₃ **0,255** · NO₂ **0,485** · PM2,5 **0,354** (§5) ; l’horaire est *hors cadre* | périmé | **bloquant** |
| 3 | `LIVRABLE.md:115` | FAIRMODE « 🟡 calculée, **paramètres à sourcer** » | §5 : v3.2 sourcée, grain par polluant, α PM documenté | périmé | **à corriger** |
| 4 | `presentation.html:461` | O₃ max 8 h leave-station : CAMS **11,69** → nous **8,31**, gain **+28,9 %** présenté comme « le chiffre du dossier » | Contre produit officiel, même fenêtre 18/01–31/12/2024 : brut **12,08** · nous **9,49** (**+21,5 %**) §1 — *autre protocole* | portée abusive | **bloquant** |
| 5 | `presentation.html:1210` (objet JS `D.mos.O3`) · `figures.html:220` | RMSE MOS graphique O₃ **12,61** (CAMS 17,58) | Plus dans VERITE comme score principal ; scores gelés §1 / leave-station à coller explicitement | périmé | **bloquant** |
| 6 | `presentation.html:273-279` vs `LIVRABLE.md:126` | Prés. barre CAMS O₃ **16,97** / biais **+6,01** (14 mois) ; LIVRABLE page 4 encore **19,11** / **+9,45** (déc. 2024 seul) | VERITE ne fige pas ce benchmark court ; les deux pages se contredisent entre elles | contradiction interne | **à corriger** |
| 7 | `presentation.html:446-449` · `LIVRABLE.md:304-307` | Gains horaires O₃ **+19,2 %** (16,97→13,71), PM **+18,1 %** en tête de résultats MOS | VERITE §1 privilégie le **grain réglementaire** vs officiel ; l’horaire reste licite *s’il est sous-titré* (faux positif grain) mais occupe encore le rôle de score-phare | portée abusive (hiérarchie) | **à corriger** |
| 8 | `presentation.html:557` · `LIVRABLE.md:338` | Spatial réglage retenu **+29,7 %** (σ 1,2) | VERITE §7 : spatial **+19,4 %**, σ 1,2 | contradiction interne | **bloquant** |
| 9 | `presentation.html:550-552` · `LIVRABLE.md:338-340` | Temporel **+6,7 %** / pire **−35,5** ; double aveugle **+1,5 %** / pire **−41,4** | VERITE §7 : temporel pire **−14,6 %** seulement ; double aveugle **+1,5 %** (OK) — le **pire temporel −14,6** ne matche pas −35,5 | contradiction interne | **bloquant** |
| 10 | `presentation.html:467-468` | POD **0,360→0,513**, CSI **0,299→0,431** (saison ozone, config leave-station) | VERITE §3 hold-out 2025 : CSI nous **0,495** (seuil cal.) vs officiel 0,387 — *autre test* ; ne pas fusionner mentalement | portée abusive (si lu comme 2025) | **à corriger** (libellé) |
| 11 | `LIVRABLE.md:323-327` + corps | Vocabulaire « **double aveugle** » pour blocage conjoint station×mois | VERITE / mission : terme abusif si non prospectif (dates train non strictement &lt; test) | portée abusive | **à corriger** |
| 12 | `figures.html:251` | Encadré « En double aveugle **−13 %** » | Ni +1,5 % (retenu) ni un gain négatif moyen documenté ainsi dans VERITE | introuvable / périmé | **bloquant** |
| 13 | `presentation.html:644-648` | Occitanie leave-region **+11,3 %** (était +18,8 % sur 11 mois) | Absent de VERITE § gelés — OK comme mesure annexe *si* non présenté comme §3 2025 | introuvable dans VERITE | **cosmétique** (à re-mesurer ou annexer hors vérité) |
| 14 | `presentation.html:1141` · `PROGRAMME_RECHERCHE.md:31` | ERA5 plafond O₃ **+7,8 %** | VERITE §6 : **+7,8 %** — OK **si** dit plafond | — | OK (contrôlé) |
| 15 | `presentation.html:780-804` | Tableau vs MOS officiel, fenêtre **18/01→31/12/2024**, saison −19,1 % | VERITE §1–2 : **aligné** | — | OK |
| 16 | `LIVRABLE.md:370-371` | +0,913 retiré, leave-one-out | VERITE §7 : ne pas citer +0,913 — **aligné** | — | OK |
| 17 | `app.py` | Pas de constantes RMSE/gain du dossier ; métriques calculées à la volée | — | — | **rien à signaler** (texte pédagogique « 13 % » L287 = anecdote historique, cosmétique) |
| 18 | `docs/PROGRAMME_RECHERCHE.md` | Chiffres §1/§3/ERA5 alignés VERITE ; pas « année 2024 complète » | — | — | **rien à signaler** hors piste ouverte |
| 19 | `presentation.html` / `LIVRABLE` | Mot « **plancher** » pour 3,61 µg/m³ | VERITE §7 : mot **retiré** | — | **non trouvé** dans les 5 fichiers (OK) |
| 20 | `presentation.html:431-434` | « 571 246 couples » puis « 3,19 M … 99 % » dans le même carton | Effectifs incompatibles dans un même paragraphe | contradiction interne | **à corriger** |

---

## Faux positifs examinés et écartés

| Cas | Décision |
|-----|----------|
| O₃ 13,55 (horaire) vs 9,49 (max 8 h) côte à côte § produit officiel | **Légitime** si grain annoncé (présentation page concurrent l’est) |
| Gains ERA5 +7,8 % présentés comme plafond | **Légitime** dans présentation + PROGRAMME |
| Réglage défaut vs retenu dans le même tableau de validation | **Légitime** si les deux colonnes restent |
| n = 73 108 vs millions d’horaires | **Légitime** (agrégation) |

---

## Synthèse comptable

| | |
|--|--|
| **Fichiers examinés** | 5 |
| **Nombres / claims repérés** (ordres de grandeur, lignes match) | ~120 lignes candidates dont ~40 claims chiffrés distincts confrontés à VERITE |
| **Signalements** | **20** lignes de tableau (dont 6 OK / non-issues) → **14 issues** |
| **Bloquants** | **7** (#1, #2, #4, #5, #8, #9, #12) |
| **À corriger** | **5** (#3, #6, #7, #10, #11, #20 — six si on compte #20) |
| **Cosmétiques** | **1–2** |

### Fichiers sans signalement bloquant propre

- **`app.py`** — aucun chiffre de vérité codé en dur ; rien de bloquant.  
- **`docs/PROGRAMME_RECHERCHE.md`** — cohérent avec VERITE (plafond météo, grain NO₂, registre).  

### Fichiers les plus chargés

- **`presentation.html`** — cœur du risque : JS `D` périmé, MQI ancien, spatial +29,7 vs VERITE +19,4, max 8 h +28,9 « chiffre du dossier » vs +21,5 vs officiel, pire temporel −35,5 vs −14,6.  
- **`LIVRABLE.md`** — titre double aveugle « −13 % / battu », MQI 0,39–0,87, page 4 benchmark 19,11 isolé, même tableau spatial/temporel que la prés.  
- **`figures.html`** — même payload `D` + encadré double aveugle **−13 %**.

---

## Lecture agent (pas une réécriture)

1. **Deux vérités coexistent encore** : (A) leave-station / 17 mois / gains +19–30 % horaires ou max 8 h *vs CAMS seul* ; (B) VERITE 18/01–31/12/2024 *vs MOS officiel*. La prés. contient les deux mais hisse encore (A) max 8 h +28,9 % comme « chiffre du dossier » alors que VERITE impose le cadrage (B) pour le concurrent public.  
2. **VERITE §7 elle-même peut être en retard** sur le spatial (+19,4 vs +29,7 documenté ailleurs avec « capacité triplée »). **Bloquant #8** : avant correction humaine, **trancher quelle ligne est la source** — régénérer `verite_dossier.py` ou rabaisser les slides. L’audit ne choisit pas : il signale l’écart.  
3. **Le titre LIVRABLE #1 est le plus dangereux en oral** : un recruteur ouvre à « double aveugle » et lit 13 % de triomphe alors que le corps dit +1,5 %.

---

## Phase 2 — jumeaux des défauts connus

*Recherche dans `scripts/` et `src/`. Liste **courte et sûre** — les ressemblances inoffensives sont écartées explicitement.*

### Motif 1 — Regex ancrée à droite / capture de fenêtre dans un nom

| Cible | Verdict |
|-------|---------|
| `scripts/extract_copernicus_stations.py:56,82` | **Déjà corrigé** : capture multi-segments `(\d{6}(?:_\d{6})*)` + espèces fermées. Commentaire documente l’ancien bug. **Pas un jumeau vivant.** |
| `src/aq/features/meteo.py:156` | `(\d{4})-(\d{2})-(\d{2})` sur nom de membre CAMS — date ISO unique, pas fenêtre multi-mois. **Écarté** (ne peut pas amputer une plage). |
| Autres `scripts/*.py` | **Aucun** `(\d{6})$` ancré droit restant sur noms parquet multi-mois. |

### Motif 2 — `columns=[...]` incomplet vs entraînement

| Cible | Verdict |
|-------|---------|
| `fit_mos.charger` charge `altitude` | OK |
| Scripts d’application via `charger` + `colonnes_admises` (`rejeu_episode`, `test_hors_echantillon_2025`, `double_aveugle_*`, …) | Héritent du schéma — **pas de jumeau** tant qu’ils n’overrident pas les colonnes stations |
| `benchmark_cams.py`, `diagnostics_legers.py`, `detecter_episodes_importes.py` | `columns=` sans altitude — **OK** : pas d’inférence MOS, pas de `colonnes_admises` |
| `apport_chimie.py` / `apport_copolluants.py` | Passent par `charger` — altitude présente |

**Aucun jumeau sûr** du bug « altitude ajoutée au train, oubliée à l’apply ».

### Motif 3 — Jointure morte

| Cible | Verdict |
|-------|---------|
| `test_hors_echantillon_2025.py` | Commentaire L83–89 : jointure ERA5 morte **déjà retirée** (était dépendance bloquante + fausse limite). |
| `erreur_par_regime_meteo.py` | Joint ERA5 et **utilise** les colonnes pour stratifier — usage diagnostic légitime. **Écarté.** |
| `apport_meteo.py` | Joint ERA5 pour mesurer un plafond — colonnes entrent dans le modèle de la voie testée. **Écarté.** |

**Aucun jumeau vivant** de jointure morte bloquante repéré.

### Motif 4 — Étiquette de grandeur codée en dur → **JUMEAU CONFIRMÉ**

| # | Fichier:ligne | Problème | Gravité code |
|---|---------------|----------|--------------|
| J1 | `scripts/comparer_mos_officiel.py:75` défaut `grandeur="max_8h"` | Default O₃-centré | risque |
| J2 | **`scripts/comparer_mos_officiel.py:116-117`** | Appels `journalier(...)` **sans** passer la grandeur du polluant — NO₂ et PM2,5 agrégés en **max 8 h** alors que le docstring du même fichier dit le contraire. `comparer_mos_officiel_annee.py` a déjà le fix (`GRANDEURS[polluant]`). | **bloquant si ce script est relancé pour NO₂/PM** |
| J3 | `scripts/cible_journaliere.py:78` défaut `"max_8h"` | Défaut dangereux pour tout nouvel appelant qui omet l’arg | à corriger (API) |
| J4 | `scripts/test_hors_echantillon_2025.py:116,133` | `"max_8h"` en dur — **OK** tant que le script ne traite que l’O₃ (seuil 120) ; piège si on l’étend | documenter / paramétrer |

**Écarté (pas nuisible) :** `verite_dossier.py`, `mqi_bon_grain.py`, `comparer_mos_officiel_annee.py`, `seuil_decision.py` — dictionnaire par polluant correct.

### Action code recommandée (hors mission d’édition livrable)

Corriger `comparer_mos_officiel.py` sur le modèle de `_annee.py` :
`grandeur = {"O3":"max_8h","NO2":"max_horaire","PM25":"moyenne_jour"}[polluant]`  
puis `journalier(..., grandeur)`. Retirer ou rendre obligatoire le défaut `max_8h` dans `agreger_journalier`.
