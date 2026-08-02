# GROK 4.5 — Curiosité : améliorer le score final et la puissance à J+3…J+5

*Regard projet (29/07/2026). Distingue **déjà mesuré**, **piste à tester**, **à vérifier**.*

---

## 0. Où l’on en est (ce que le dépôt autorise à croire)

| Fait | Source projet |
|------|----------------|
| Erreur CAMS **presque plate** J+1→J+3 (+1–5 % RMSE selon polluant) | `reports/CAMS_BENCHMARK.md` |
| MOS résidu + geo + calendrier : gain spatial O₃ **~+28 %** J+1…J+3 | `reports/MOS.md` |
| Gain **temporel** fragile / négatif si été hors train | `MOS.md` (pli juillet −19 % sur 3 mois) |
| Archive annoncée **24 mois** (2023-07→2025-06) | contexte candidature |
| Horizons entraînés/exportés : **J+1, J+2, J+3** (pas J+4/J+5 dans `fit_mos` / CSV) | `scripts/valider_mos_aveugle.py` `choices=[1,2,3]` ; `mos_O3_J{1,2,3}.csv` |
| CAMS Europe prévisions : **~J+4** (96 h) documenté ADS ; PREV’AIR affiche **J+5** | `DATA_CATALOG.md` ; prevair.org |
| Features météo **interdites** si ERA5 (fuite) ; météo de **prévision** autorisée en principe | `src/aq/models/mos.py` |
| Ablation : calendrier lourd ; forêt **nuisible** au MOS ; relief utile ; routes ~0 sur O₃ | `reports/ABLATION.md` |
| Perte pondérée : échange gain global / queue | `reports/PRESERVER_LA_QUEUE.md` |

**Lecture physique (projet, avec réserve critique).** Une erreur structurelle (maille, inventaire, biais de régime) reste corrigeable loin dans l’horizon ; une erreur **météo chaotique** croît avec le lead time et limite le plafond du MOS à J+4/J+5. Le plat J+1→J+3 ne prouve pas que J+5 restera plat — **à mesurer**.

**Critique déjà écrite :** attribuer le plat « uniquement au modèle, zéro météo » est trop fort (`docs/CRITIQUE_ADVERSE.md`). Pour J+4/J+5, **mesurer d’abord** la pente RMSE CAMS brut, puis le gain MOS.

---

## 1. Améliorer le score final (J+1 d’abord — levier le plus rentable)

Ordre suggéré : **ce qui débloque le plafond**, pas ce qui change l’architecture pour le plaisir.

### 1.1 Données & protocole (souvent +plus que le modèle)

| Piste | Pourquoi | Effort | Risque |
|-------|----------|--------|--------|
| **Inter-annuel strict** (train 12 mois / test 12 mois) sur les 24 mois | Tue ou confirme le trou saisonnier ; seul score « final » crédible jury | Moyen (déjà partiellement engagé) | Peut baisser le % affiché — c’est sain |
| **Modèle par saison ou mois glissant** (retrain mensuel / expanding window) | Le calendrier pèse 15 % en ablation : mieux vaut un régime local qu’un `jour_annee` global | Moyen | Ops plus lourde |
| **Couper les features qui nuisent** (forêt sur O₃ MOS) | Ablation : −forêt → RMSE ↓ 1,9 % | Faible | À retester sur 24 mois |
| **Fenêtre d’échéances réellement dispo** (après 06h45 UTC ADS) | `MOS.md` le signale : J+1 « 1–6 h » est déjà du passé à réception | Faible | Change n et le récit |
| **Cibles validées seulement** | Déjà corrigé (+gain) ; vérifier que J+2/J+3 ont le même filtre | Faible | — |
| **Homogénéité version CAMS** sur 24 mois | Saut d’ensemble / cycle mid-series = faux « apprentissage » | Moyen | **À vérifier** logs ADS |
| **Typologie explicite** (fond / trafic / industriel) en feature ou modèles séparés | CAMS trafic NO₂ RMSE 19,5 vs fond 11,3 | Moyen | Sur-fit si peu de stations trafic |

### 1.2 Cible & perte

| Piste | Pourquoi | Effort |
|-------|----------|--------|
| **Garder cible = résidu** | Obs directe écrase la queue (mesuré) | — |
| **Perte pondérée par concentration** (déjà testée) comme **défaut O₃** | Métier = pics / classes d’indice | Faible à brancher en fit final |
| **Multi-objectif** : MSE fond + pinball q0.9 en mixture (α·L2 + (1−α)·pinball) | Évite l’échec « quantile seul pire que CAMS » | 1–2 j |
| **Perte sur max journalier 8 h (O₃)** en plus de l’horaire | L’indice et les seuils vivent en MD8 ; l’horaire optimal ≠ MD8 optimal | Moyen |
| **Calibration post-hoc** des quantiles (isotonic / conformal par saison) | Meilleure proba de dépassement sans retoucher le point estimate | Moyen |

### 1.3 Features à **pouvoir prédictif neuf** (là où CAMS est aveugle)

Principe ablation : *n’ajouter que ce que CAMS n’a pas déjà*.

| Feature | Pour qui | Comment sans fuite |
|---------|----------|-------------------|
| **Météo de prévision** (AROME/ARPEGE ou IFS open) : T, vent, rayonnement, PBLH, pluie | O₃ (photochimie), PM (dispersion), NO₂ (stabilité) | Run météo disponible **avant** l’échéance AQ ; archiver `run_time` |
| **Obs passées** jusqu’à T0−ε (persist. locale, residual hier même heure) | Tous, surtout J+1 | Strict : pas d’obs de l’échéance cible |
| **Écart CAMS − climatologie station** | Ancre le biais local | Calculable hors ligne |
| **Membres / spread ensemble CAMS** (si téléchargeables) | Incertitude + non-linéarité | **À vérifier** volumétrie ADS |
| **Indicateur de régime** (brise, anticyclone, panache) dérivé météo prévue | O₃ méditerranéen | Labels simples, pas 50 régimes |
| **Feux / AOD / poussières** (CAMS dust, GFAS, FIRMS) en entrée | PM J+1…J+5 épisodes 2026 | Surtout extrêmes ; sparse |
| **Trafic dynamique** (si existe) vs proxy statique | NO₂ | Statique = LUR, peu d’effet O₃ |

**Ne pas attendre de miracle de :** plus de leaves LightGBM, GNN sur 476 nœuds, RealMLP — tant que le protocole temporel et la météo prévue ne sont pas en place.

### 1.4 Entraînement

| Piste | Détail |
|-------|--------|
| **Un modèle par (polluant × horizon)** | Déjà l’esprit J1/J2/J3 ; ne pas partager un seul modèle multi-horizon sans feature `lead_time` bien validée |
| **Feature `lead_time_h` + interaction** | Un seul fit multi-échéance *si* ablation montre que ce n’est pas neutre (sur 3 mois, sans échéance = 0 % — à refaire sur 24 mois et J+4/5) |
| **Sample weight** jours d’épisode / stations sous-représentées | Complète la loss pondérée |
| **Early stopping sur pli temporel**, pas sur RMSE spatiale seule | Évite de sur-optimiser le leave-station |
| **n_jobs borné** en lots parallèles | Règle projet CLAUDE.md (contention mémoire) |

### 1.5 Cible métier = score « final » alternatif

Si le score final candidature est l’**indice / EPCI** (`LIVRABLE.md`) :

1. Optimiser / évaluer le **sous-indice O₃** et l’**accord de classe**, pas seulement RMSE horaire station.  
2. Apprendre éventuellement le biais **point → max zone** (−0,72 classe mesuré).  
3. Un +2 % RMSE station qui **+5 % accord de classe** gagne le pitch.

---

## 2. Pousser J+3, et ouvrir J+4 / J+5

### 2.1 Diagnostic obligatoire (1–2 jours) avant d’optimiser

```
Pour O₃ (puis NO₂, PM2.5) :
  RMSE_CAMS(h) pour h = 1..96 (ou 120 si dispo)
  RMSE_MOS(h)  modèle entraîné *par* bande d’échéance ou avec lead_time
  Gain(h) = 1 - RMSE_MOS/RMSE_CAMS
  + même courbe en MD8 / dépassement 180
```

**Hypothèses à départager :**

| Si… | Alors le levier est… |
|-----|----------------------|
| RMSE_CAMS plat jusqu’à J+5 | MOS « structurel » suffit ; recopier la recette J+1 |
| RMSE_CAMS grimpe après ~48–72 h | Ajouter **météo prévue** + **spread** ; baisser les ambitions de gain % |
| Gain MOS s’effondre alors que CAMS est plat | Le MOS J+1 **surfit** des corrélations court terme (obs retard, calendrier) — purge features |
| Gain MOS stable mais POD seuil meurt | Perte / calibration queue, pas plus de geo |

**Données :** CAMS regional forecast lead times — catalogue dit jusqu’à **J+4** ; J+5 peut exiger PREV’AIR ou un autre produit (**à vérifier** fichier NetCDF réel et `leadtime_hour` max déjà en `data/`).

### 2.2 Stratégies spécifiques long horizon

#### A. Modèles **dédiés par bande d’échéance**

- Bande A : 7–24 h (J+1 utile post-cut-off)  
- Bande B : 25–48 h (J+2)  
- Bande C : 49–72 h (J+3)  
- Bande D : 73–96 h (J+4)  
- Bande E : 97–120 h (J+5) si données  

Chaque bande a son LightGBM résidu. Coût : 5 fits ; bénéfice : pas de compromis J+1 vs J+5 sur les splits d’arbres.

#### B. **Météo prévue** comme second pilier (le plus gros delta attendu à J+3+)

Sans elle, le MOS corrige un biais moyen ; avec elle, il peut suivre un **changement de régime** annoncé (canicule J+4, pluie J+3).

| Source | Horizon utile | Note |
|--------|---------------|------|
| AROME | ~J+2 | Fine échelle Occitanie |
| ARPEGE | ~J+4 | Couvre mieux J+3…J+4 |
| ECMWF open IFS | ~J+5–J+10 | Plus grossier, gratuit |
| PEARP / ENS | spread | Proba dépassement |

Pipeline minimal : extraire T_2m, u/v10, rad, precip, PBLH aux stations pour le **même `forecast_reference_time`** que CAMS (ou le run météo le plus récent disponible à T_pub CAMS).

#### C. **Cascade / correction en deux temps**

1. Corriger le **biais structurel** (geo + type station + saison) — stable à tout horizon.  
2. Ajouter un terme **dynamique court** (obs récentes, tendance 24 h) **décayant** avec le lead time (poids ∝ exp(−h/h0)).  

À J+5, le terme (2) → 0 ; on ne pollue pas le long terme avec de la persistance morte.

#### D. **Ré-ancrage quotidien (update)**

En exploitation PREV’AIR-like : chaque nouveau run CAMS + dernières obs validées → MOS **incremental** ou re-fit rolling 365 j.  
Améliore J+3…J+5 *perçus* en production sans changer l’algo — **à séparer** de l’éval offline figée.

#### E. Ensemble

- Entrée : médiane CAMS + **p10/p90** des membres (si stockés).  
- Sortie : quantile forest / multi-quantile LGBM → proba seuil à J+3…J+5 (plus utile qu’un point RMSE).

#### F. Ne pas forcer un gain RMSE à J+5

Métier AASQA : l’arrêté épisodes et l’info quotidienne pèsent surtout **J0–J+1** ([référentiel LCSQA prévision](https://www.lcsqa.org/fr/rtn) — horizons d’éval classiques J0/J1).  
J+3…J+5 = **tendance et confiance**, pas le même KPI. Afficher :

- RMSE / biais  
- **fiabilité** de la proba de dépassement  
- taux de « confiance basse → bascule CAMS brut »

---

## 3. Plan d’expérience concret (ordre, ~effort)

### Phase 0 — Mesurer le plafond (2–3 j)

1. Courbe RMSE CAMS brut **par heure de lead time** 1…max sur 24 mois O₃.  
2. MOS actuel appliqué **tel quel** à chaque horizon déjà en base (J+1…J+3) en **leave-year**.  
3. Si lead ≥ 96 h absent : **une** requête ADS unitaire (règle CLAUDE.md : estimate_costs + test format) pour J+4.

**Go/no-go J+5 :** si pas de champ CAMS Europe au-delà de 96 h, documenter PREV’AIR ou arrêt à J+4.

### Phase 1 — Score final J+1 (5–8 j) — **priorité candidature**

1. Fit final O₃ : features sans forêt ; perte pondérée ; leave-year + leave-station.  
2. Brancher **obs retard** (t−24h, t−1h si dispo à cut-off) en ablation.  
3. Météo prévue **AROME T+vent** sur un mois test unitaire → extrapoler coût.  
4. Métrique slide : RMSE + POD MD8/seuil + accord classe indice si prêt.

### Phase 2 — J+3 robuste (3–5 j)

1. Modèles par bande 49–72 h.  
2. Météo ARPEGE/IFS sur cette bande.  
3. Comparer : MOS_J1 appliqué naïf à J+3 vs MOS_dédié vs MOS+météo.  
4. Publier table unique (comme `MOS.md` horizons) en leave-year.

### Phase 3 — J+4 / J+5 exploratoire (3–5 j si données)

1. Même protocole bande D/E.  
2. Accepter un gain RMSE plus faible ; pousser **calibration** proba.  
3. Démo : jour type canicule où J+4 météo annonce le pic — la correction suit-elle ?

### Ce que je **ne** ferais pas dans 23 jours

- GNN, foundation TS, assimilation 4D-Var.  
- Cinq polluants × cinq horizons × dix pertes.  
- Optimiser le % gain spatial leave-station au détriment du leave-year.

---

## 4. Idées « curiosité » (plus spéculatives, ROI incertain)

| Idée | Intuition | Comment tuer vite |
|------|-----------|-------------------|
| MOS sur **log(O₃)** ou **racine** | Stabilise la variance | 1 fit, courbe QQ |
| Co-krigeage résidus multi-polluants (O₃ residual ∼ f(NO₂ residual)) | Chimie locale | Ablation multi-sorties |
| Corriger d’abord le **biais par décile CAMS** (EMOS simple) puis GBM sur reste | EMOS cheap | Baseline 50 lignes |
| Distillation : prédire le **résidu PREV’AIR** si un jour accessible | Cible métier vraie | Licence / accès |
| Feature « distance au dernier épisode » | Mémoire d’été | Fuite si mal codée |
| Apprendre le **rang** dans la distribution saisonnière | Pics relatifs | vs pinball |

---

## 5. Métriques de succès (pour ne pas s’auto-tromper)

| Horizon | KPI principal | KPI secondaire | Garde-fou |
|---------|---------------|----------------|-----------|
| J+1 | RMSE leave-year O₃ + gain vs CAMS | POD/FAR seuil info ; classe indice | Queue décile haut ≥ CAMS |
| J+3 | Idem | Corrélation / biais saisonnier | Gain ≥ 0 sur l’été test |
| J+4/J+5 | Brier ou ECE proba dépassement | RMSE honnête même si +5 % | Courbe fiabilité ; rate bascule |

Toujours : **même stations, mêmes heures, cut-off respecté**, bootstrap **par station** (`MOS.md`).

---

## 6. Synthèse en une page

**Pour le score final :**  
leave-year sur 24 mois + purge features nuisibles + perte orientée pics + (si possible) météo *prévue* et obs retard propres + métrique indice/MD8.

**Pour J+3 :**  
déjà bon en spatial sur ancien protocole ; le refaire en **leave-year** ; modèle **dédié 49–72 h** ; météo prévue.

**Pour J+4/J+5 :**  
1) prouver que les champs existent ; 2) courber RMSE CAMS ; 3) MOS structurel + météo + incertitude ; 4) ne pas vendre le même +28 % — vendre une **tendance calibrée** et une règle de confiance.

**Levier n°1 sous-exploité dans le code actuel :** météo de prévision (explicitement prévue dans `mos.py`, absente du fit).  
**Levier n°1 méthodologique :** évaluation long horizon en **année tenue à l’écart**, pas seulement stations exclues.  
**Levier n°1 données :** lead times > 72 h réellement téléchargés et joints au panneau.

---

## 7. Prochaines commandes utiles (indicatif)

```bash
# Diagnostic pente d'erreur (à écrire si absent)
python scripts/benchmark_cams.py --horizons 1-96 --polluant O3

# MOS par horizon déjà supporté côté validation
python scripts/valider_mos_aveugle.py --polluant O3 --horizon 3

# Étendre fit_mos / download : leadtime 73-96 (unité d'abord, estimate_costs)
```

*Passe unitaire obligatoire avant tout lot ADS (CLAUDE.md règle 1).*

---

*Fichier de travail — pas un engagement de résultats. Toute piste « +X % » non mesurée ici reste une hypothèse.*
