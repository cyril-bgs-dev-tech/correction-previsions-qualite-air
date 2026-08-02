# GROK R3 — Trancher (23 jours), actualité, angles morts (29 juillet 2026)

Archive projet : **24 mois (2023-07 → 2025-06)**. Sources datées ; **jugement** ≠ **publié**. Verdicts en tête de question quand la question en appelle un.

---

## Trancher, avec 23 jours

### 1. Courbe d'apprentissage (gain × mois) — convainc-t-elle ?

**Verdict : une seule courbe, oui ; une planche de courbes, non.**

**Publié.** Les bilans de performances AASQA/LCSQA rapportent des indicateurs opérationnels (seuils, classes), pas des learning curves académiques ([LCSQA, performances des prévisions](https://www.lcsqa.org/fr/performances-des-previsions)).  
**Jugement.** Un jury regarde **30 secondes** une figure qui répond à une objection qu’il a déjà : « trois mois ne suffisent pas / 24 mois changent-ils la donne ? ».  
Utile si : axe clair (mois d’archive → gain leave-station ou leave-year), **plateau visible**, une phrase « au-delà de N mois le gain stagne ».  
Inutile si : cinq variantes de modèle, sans lien indice/seuil.  
**Action 23 j.** Une figure max, en annexe ou slide 1 bis — pas le héros du pitch.

### 2. Validation inter-annuelle vs dix figures de diagnostic ?

**Verdict : garder la validation inter-annuelle. Couper les dix diagnostics à deux.**

**Publié.** Avec 24 mois (2023-07 → 2025-06), un split **train ~2023-07→2024-06 / test 2024-07→2025-06** (ou 12/12) est enfin possible — c’était l’objection centrale du corpus à 3 mois.  
**Jugement.** C’est la **seule** figure qui transforme le récit (« j’ai un trou d’été » → « je généralise d’une année sur l’autre »).  
Les dix diagnostics (ablation, régimes, relief…) prouvent la rigueur **en annexe** ; à l’oral ils diluent.  
**Une chose à garder au centre :** tableau + carte d’erreur **année test tenue à l’écart**, O₃ prioritaire, baseline CAMS.  
Deux diagnostics satellites max : (a) queue/pics, (b) spatial leave-station ou EPCI.

### 3. 13 rapports + présentation 10 pages — trop ? Que couper ?

**Verdict : oui, trop en surface. 10 pages OK si un fil ; les 13 rapports restent coulisse.**

Inventaire vérifié le 29/07/2026 : **13** `reports/*.md` (ABLATION, BASELINES, CAMS_BENCHMARK, COMPARAISON_COMMUNE, COVARIABLES_VS_INTERPOLATION, INDICE_ATMO, INDICE_BOUT_EN_BOUT, MOS, PRESERVER_LA_QUEUE, QUALITE_DONNEES, REGIMES_METEO, RELIEF, SPATIALISATION).  
**Jugement — couper du pitch (pas détruire) :** REGIMES_METEO, RELIEF, COMPARAISON_COMMUNE, MOS multi-horizons détaillés, multi-polluants à parité.  
**Garder dans les 10 pages :** problème métier O₃ Occitanie → méthode → **inter-annuel** → leave-station/covariables → queue → indice/EPCI ou aide au jour → limites.  
**Règle :** un rapport = une preuve citée en bas de slide, pas une slide.

### 4. Page Streamlit « aide à l'expertise du jour » vs un point de RMSE ?

**Verdict : la page vaut mieux qu’un point de RMSE *si* elle rejoue un jour réel d’épisode 2026 ; sinon c’est une histoire.**

**Publié.** Atmo décrit sa chaîne comme mesure + stats + CHIMERE + **expertise humaine** quotidienne ([actu ozone 19/06/2026](https://www.atmo-occitanie.org/actualites/pollution-atmospherique-lozone-les-realites-de-la-qualite-de-lair-en-occitanie)). PREV’AIR vise les **seuils** via correction ML ([prevair.org, prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
**Jugement.** RMSE seule = langage candidat ML. Divergence modèle/mesure + confiance = langage salle de prévision.  
Test anti-self-fooling : en 90 s, un non-auteur comprend-il **s’il alerte** ? Si non, retomber sur le tableau inter-annuel.  
Ne pas opposer les deux : RMSE/inter-annuel **légitime** l’outil ; l’outil **vend** l’usage.

### 5. Risque réel de sur-livrer ?

**Verdict : réel. Le signal est « n’a pas su choisir », pas « a trop travaillé ».**

**Jugement.** Symptômes : 10 pages sans phrase unique ; 5 architectures ; tous les polluants ; démo + 13 PDF envoyés.  
Antidote : **une promesse** (« correction CAMS O₃, validée année tenue à l’écart, utile le matin ») + tout le reste en lien.  
Sur-livrer devient un atout seulement si la **hiérarchie** est visible en 10 secondes (titres, gras, une slide « ce que je ne revendique pas »).

---

## Ce que je ne peux pas voir

### 6. CAMS et PREV’AIR — six derniers mois

**Publié, vérifiable 29/07/2026.**

| Date | Fait | Source |
|------|------|--------|
| **12–13/05/2026** | Upgrade CAMS global **IFS 50r1** : dépôt sec O₃ amélioré Europe/NA, BVOC en ligne (MEGAN), émissions anthro mises à jour, GFAS+VIIRS, assims OMPS/TROPOMI/S3 | [CAMS, 13/05/2026](https://atmosphere.copernicus.eu/cams-global-system-gets-upgrade) |
| **29/06/2026** | Assessment Report European AQ **2025** (tendances ↓, épisodes chaleur/feux/Sahara) | [CAMS, 29/06/2026](https://atmosphere.copernicus.eu/cams-releases-annual-assessment-report-european-air-quality-2025-0) |
| **06–20/07/2026** | Feux Canada, ICAP, IWGGMS (contexte panaches / GHG) | [CAMS news](https://atmosphere.copernicus.eu/news) |
| **Juin 2024+** (toujours affiché) | PREV’AIR **J+0…J+5**, correction **ML** + krigeage | [prevair.org](https://www.prevair.org/) |
| **Été 2026** | Bulletins PREV’AIR chaleur/ozone (ex. 19/06, 10/07/2026) ; feux Gironde fin juillet | [prevair.org/actualites](https://www.prevair.org/actualites) |

**À vérifier.** Changement de version du **CAMS regional ensemble** Europe (nombre de membres, biais O₃ surface) sur votre fenêtre 2023–2025 — peut créer un **saut de distribution** mid-series.  
**Impact projet :** mentionner 50r1 en une ligne (« le fond européen bouge ; ma correction est version-consciente ») sans refaire l’étude.

### 7. Épisodes marquants Occitanie — été 2026

**Verdict : oui — en parler. Trois familles.**

**Publié** ([historique épisodes Atmo Occitanie](https://www.atmo-occitanie.org/episodes-pollution), consulté 29/07/2026) :

1. **Ozone caniculaire** — ex. 08–09/07/2026 : O₃ information puis **alerte** sur 31, 30, 34, 65.  
2. **Feux / fumées** — 06–07/07/2026 : PM10 info/alerte **66** (incendie PO) ; 25–27/07/2026 : PM10 multi-départements (12, 30, 34, 46, 48, 81, 82…), communiqués citant **incendies**.  
3. **Poussières désertiques** — 24/06/2026 : PM10 alerte 09, 31, 65 (apport désertique Ouest) ; 13–14/07/2026 : PM10 66 puis extension multi-départements.  

Actu Atmo (19/06/2026) : 2025 = 3ᵉ été le plus chaud régional ; **12 procédures / 8 jours** entre 20/06 et 16/08/2025 ; O₃ moyen encore **+40 à +70 %** vs guide OMS « pic saisonnier » ([actu ozone](https://www.atmo-occitanie.org/actualites/pollution-atmospherique-lozone-les-realites-de-la-qualite-de-lair-en-occitanie)).  
**Jugement pitch :** « mon outil est fait pour *ces* matins-là » + rejouer **un** jour (ex. 09/07 O₃ ou 27/07 PM feux) en démo.  
**Limite honnête :** archive d’apprentissage s’arrête en **2025-06** — l’été 2026 est un **test hors échantillon narratif**, pas un score déjà dans les CSV.

### 8. ATMO Occitanie — angle récent

**Publié.**

- Recrute **Responsable projets IA** (CDI) + **Data scientist junior** (CDD) ([recrutement](https://www.atmo-occitanie.org/recrutement), offres 04/2026 et 07/2026).  
- **19/06/2026** : ozone = défi structurel, CHIMERE + expertise locale, lien Europe→territoire ([actu](https://www.atmo-occitanie.org/actualites/pollution-atmospherique-lozone-les-realites-de-la-qualite-de-lair-en-occitanie)).  
- **22/07/2026** : bilans QAI 2025 grandes villes.  
- **29/06/2026** : baisse émissions 2023.  
- PPA Nîmes (27/05/2026), covoiturage Montpellier, Poll’Occ, AtmoViz.  

**Angle candidat :** coller mot pour mot au discours ozone du 19/06 (« prévisions européennes → réalité locale ») + montrer que l’IA sert l’**expertise**, pas la remplace — aligné fiche IA.

### 9. AASQA / travaux correction ML 2025-2026

**Publié.** PREV’AIR industrialise la correction ML + spatialisation krigeage (doc site, toujours d’actualité 2026) ([prevair.org](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
Bilans performances prévision 2022 encore en ligne côté LCSQA (pas un boom de papiers ML AASQA 2025–26 repéré ici) ([LCSQA](https://www.lcsqa.org/fr/performances-des-previsions)).  
**À vérifier.** Thèses/rapports internes Ineris, notes non indexées, posters FAIRMODE 2025–26.  
**Jugement.** Le sujet n’est **pas vide** (PREV’AIR) mais les **publications AASQA grand public sur “notre ML”** restent rares — place pour un candidat qui parle métier + mesure, pas pour inventer la correction nationale.

### 10. « IA et qualité de l'air » en 2026 — porteur ou saturé ?

**Verdict : porteur à l’embauche, saturé en discours vague.**

**Publié.** Offres Atmo Occitanie IA/data actives ; directive 2024/2881 + décision modélisation 2026/1208 renforcent le rôle des modèles ([dir. 2024/2881](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=OJ:L_202402881) ; [déc. 2026/1208](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).  
**Jugement.** « On fait de l’IA » sans protocole = bruit. « Correction CAMS O₃, inter-annuelle, bascule humaine, indice » = différenciant.  
Porteur = **IA sous contrainte réglementaire** ; saturé = démos agentiques / fondations sans µg/m³.

---

## Mes angles morts, encore

### 11. Faiblesse qui reste après les corrections

**Verdict (jugement) : le maillon décisionnel bout-en-bout sous contraintes d’exploitation réelle.**

Même avec 24 mois et leave-year :  
- **Cut-off opérationnel** (quelles entrées à 7 h, pas la réanalyse du soir) — **à démontrer explicitement**.  
- **Comparaison à la chaîne locale** (CHIMERE régional / PREV’AIR corrigé), pas seulement CAMS brut — sinon « j’améliore un produit que la salle n’utilise pas seul ».  
- **2026 hors archive** : feux + Sahara + O₃ de cet été ne sont pas dans l’apprentissage.  
- **Indice / EPCI** : si encore fragile, le pitch station reste un cran sous le produit publié.  
- **Version CAMS** (50r1 mai 2026) et homogénéité 2023–2025.

### 12. Questions ingénieur sur trafic et population — sans réponse prête

Préparer ou marquer **à vérifier** :

1. **Année et résolution** du proxy trafic (TMJA ?) — alignée sur 2023–2025 ou figée ancienne ?  
2. **Trafic = cause ou corrélat du type de station** déjà capté par « proximité voirie » ?  
3. Population : **résidents nuit vs population présente jour** — l’indice/exposition veut laquelle ?  
4. Les variables changent-elles assez **dans le temps** pour un modèle de prévision J+1, ou sont-elles quasi statiques (LUR) ?  
5. **Colinéarité** relief / urbanisme / trafic — importance de permutation ou VIF ?  
6. Hors stations : extrapolation vers une cellule sans mesure — **carte d’erreur** ou silence ?

Sans réponses chiffrées, dire : « statiques, apport leave-station mesuré, pas d’attribution causale trafic. »

### 13. Présenter les négatifs — ce qui se retourne

**Se retourne contre vous :**

- Trois échecs d’affilée **sans** « donc en prod je fais X ».  
- Ton confessional / trop long sur le −19 % alors que 24 mois l’ont peut‑être refermé — **recalculer** et ne pas recycler l’ancien récit.  
- Négatif utilisé pour paraître humble mais **chiffres flous**.  
- Mettre le négatif en slide 2 avant d’avoir établi un positif net.

**Formule sûre :** positif (inter-annuel) → limite restante (une) → règle de bascule.

### 14. Pari : raison d’écartement

**Jugement.**  
1. **Pas de lien clair avec la décision du jour** (indice/épisode) malgré la technique.  
2. Ou **ignorance de PREV’AIR/CHIMERE local** (« je remplace la chaîne »).  
3. Ou oral confus / sur-livraison sans choix.  
Moins probable : RMSE insuffisante si le protocole est propre.

### 15. Pari : raison de rétention

**Jugement.**  
1. **Protocole adulte** : inter-annuel + leave-station + limite dite + bascule humaine.  
2. **Collage ozone Occitanie 2025–2026** (leur discours public du 19/06).  
3. **Outil d’aide** aligné fiche IA / data (pas un papier orphelin).  
4. Capacité à **couper** et expliquer un arbitrage queue/RMSE en une minute.

---

## Plan de 23 jours (synthèse)

| Priorité | Livrable | Couper |
|----------|----------|--------|
| P0 | **Split inter-annuel O₃** + tableau vs CAMS | Nouvelles archis |
| P0 | Une slide « ce que je ne revendique pas » | 13 rapports en PJ mail |
| P1 | Démo **un** épisode été 2026 (O₃ 8–9/07 ou PM feux 26–27/07) | Dix diagnostics |
| P1 | Réponses trafic/pop en 6 lignes honnêtes | Feature store élargi |
| P2 | Courbe d’apprentissage 1 figure | GNN, agents |
| P2 | Mention PREV’AIR + CHIMERE local + 50r1 | Guerre des baselines exotiques |

### Phrase unique du dossier

> *Je corrige CAMS sur l’ozone (et le nécessaire pour l’indice), avec une année entière jamais vue, des stations jamais vues, un arbitrage explicite sur les pics, et un mode « ne pas suivre la correction » — pour les matins d’épisode comme l’Occitanie en vit en 2025–2026.*

---

*Complète `REPONSES_GROK.md` et `REPONSES_GROK_2.md`. Re-vérifier l’historique des épisodes la veille de l’entretien (page Atmo mise à jour en continu).*
