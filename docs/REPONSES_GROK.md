# Réponses aux 30 questions — regard neuf (29 juillet 2026)

Sources croisées le **29/07/2026**. Toute affirmation non sourcée explicitement est marquée **à vérifier**. Six à dix lignes par question. Les questions **6, 8 et 21** sont traitées en priorité d’analyse.

---

## A. L'actualité que je ne peux pas connaître

### 1. Qu'est-ce qui a changé chez les AASQA françaises en 2025-2026 ?

Mutualisation data nationale : **Atmo Data** agrège indice ATMO, épisodes, émissions EPCI/région et indice pollen sous ODbL, avec carte, API et WFS ([Atmo France, notice Atmo Data, 1er avril 2025](https://www.atmo-france.org/sites/federation/files/medias/documents/2025-04/notice_Atmo_Data_1eravril2025.pdf)).  
Portail emplois fédéré sur [jobs.makesense.org/fr/partners/aasqa](https://jobs.makesense.org/fr/partners/aasqa) (6 offres visibles le 29/07/2026 : HdF, AuRA, Occitanie, Corse).  
LCSQA : guides modélisation urbaine 2025, intercomparaison Anvers 2025, notes ACSM/PMF juillet 2026 ([LCSQA, publications](https://www.lcsqa.org/fr/rapports-publies)).  
PREV’AIR affiche **J+0 à J+5** depuis juin 2024 et un espace PREV’AIR+ historique ([prevair.org, consulté 29/07/2026](https://www.prevair.org/)).  
Atmo Occitanie pousse AtmoViz, open data ArcGIS, bilans 2024–2025 et un **projet IA transversal** (offres 2026).  
**À vérifier** : état exact du SI national partagé (GEOD’AIR vs Atmo Data) et budgets d’investissement post-directive.

### 2. Transposition de la directive (UE) 2024/2881 — obligations 2026-2027

Directive publiée JOUE **20/11/2024** ; transposition des dispositions de fond **au plus tard le 11 décembre 2026** ; abrogation des directives 2004/107 et 2008/50 au **12 décembre 2026** ([dir. 2024/2881, art. 30–32](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=OJ:L_202402881)).  
Nouvelles valeurs limites / cibles à atteindre **au plus tard le 1er janvier 2030** (annexe I) ; feuilles de route qualité de l’air **avant 2030** si risque de non-atteinte.  
Décision d’exécution **(UE) 2026/1208** (9 juin 2026) : détails techniques modélisation et **représentativité spatiale** des points ; application **à compter du 30 juin 2028** ([EUR-Lex 32026D1208](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).  
Obligations immédiates pour 2026-2027 côté France : préparer transposition nationale, renforcer modélisation/incertitude, cartographier représentativité, anticiper obligation de réduction d’exposition moyenne PM2.5/NO₂.  
**À vérifier** : texte français de transposition (Legifrance) — non trouvé publié au 29/07/2026 ; statut des feuilles de route DREAL/AASQA.

### 3. ATMO Occitanie recrute-t-elle, et publie-t-elle ?

**Oui, deux offres actives** le 29/07/2026 sur [atmo-occitanie.org/recrutement](https://www.atmo-occitanie.org/recrutement) :  
- **Responsable de projets IA** (CDI, Toulouse, PDF avril 2026) : stratégie IA transverse, ML, automatisation, Python/JS/PHP, PostgreSQL.  
- **Data scientist junior** (CDD, Toulouse, PDF **23/07/2026**) : analyses exploratoires/prédictives, prototypes ML, Python/R/SQL, Pôle Partenariats.  
Travaux récents : bilan QAI 2025 grandes villes (actu 22/07/2026), pollens été (02/07/2026), inventaire émissions 2023 (29/06/2026), PPA Perpignan, Ginestous, carrière Liouc (juin 2026) ([atmo-occitanie.org](https://www.atmo-occitanie.org/)).  
Open data : [data-atmo-occitanie.opendata.arcgis.com](https://data-atmo-occitanie.opendata.arcgis.com/).  
**Signal fort** : l’organisme recrute explicitement sur IA/data — le projet CAMS du candidat est dans la cible, pas en marge.

### 4. Appels à projets / financements modélisation QA France

Pistes vérifiables : programme national LCSQA (ministère) ; **CAMS National Collaboration Programme** (ECMWF/CAMS pour États membres) ([atmosphere.copernicus.eu/cams-national-collaboration-programme](https://atmosphere.copernicus.eu/cams-national-collaboration-programme)) ; Horizon Europe / Life Clean Energy Transition (appels « air quality » à suivre sur Funding & Tenders).  
Côté France : ADEME (AAP air/climat, calendrier **à vérifier** mois par mois), ANR, financements régionaux/PPA/ZFE via collectivités adhérentes AASQA.  
FAIRMODE / CEN TC 264 structurent la qualité des modèles plus que le financement direct.  
**À vérifier aujourd’hui** : AAP ADEME ouverts au 29/07/2026 et enveloppes « IA pour l’environnement » des collectivités occitanes — non consolidés ici.

### 5. Évolutions récentes PREV’AIR, CHIMERE, CAMS

**PREV’AIR** : horizon **J+5** depuis juin 2024 ; correction statistique **par machine learning** puis krigeage des prévisions O₃/NO₂/PM10/PM2.5 (référence site) ([prevair.org, prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)) ; modèles CHIMERE + MOCAGE ; bulletins actifs juillet 2026 (ozone, feux Gironde).  
**CAMS** : Assessment Report European AQ **2025** publié **29/06/2026** (tendances ↓, épisodes persistants, feux, poussières sahariennes) ; ensemble régional **11 systèmes** ; outils d’attribution de sources ([CAMS news 29/06/2026](https://atmosphere.copernicus.eu/cams-releases-annual-assessment-report-european-air-quality-2025-0)).  
**CHIMERE** : chaîne opérationnelle PREV’AIR inchangée dans le discours public ; version exacte en prod **à vérifier** côté Ineris/CNRS.  
**Impact sur l’analyse du candidat** : la correction ML + krigeage n’est plus une niche — c’est le standard national. La valeur se déplace vers **complément local** (covariables, pics, saison, Occitanie) et **auditabilité**, pas vers « inventer la correction ».

---

## B. Les questions techniques restées ouvertes

### 6. Le krigeage à dérive CHIMERE capte-t-il déjà les covariables de terrain ? ★

**Réponse courte : partiellement le fond spatial, pas le contraste local non résolu par la maille.**  
La dérive CHIMERE injecte la structure spatio-temporel du CTM ; le krigeage des résidus lisse l’erreur aux stations. Il **n’encode pas explicitement** distance route, canyon, occupation du sol fine ni relief sub-maille — sauf si ces effets sont déjà dans CHIMERE ou corrélés spatialement aux résidus observés ([uEMEP, GMD 2022, DOI 10.5194/gmd-15-449-2022](https://doi.org/10.5194/gmd-15-449-2022)).  
Littérature LUR hybride : ajouter CTM + satellite à des covariables locales monte le \(R^2\) PM2.5 ~0,33–0,38 → ~0,60 ; NO₂ ~0,47–0,51 → ~0,58 ([de Hoogh et al., 2016, DOI 10.1016/j.envres.2016.07.005](https://doi.org/10.1016/j.envres.2016.07.005)). Les variables trafic restent majeures même avec dispersion ([Chen et al., 2019, DOI 10.1016/j.envint.2019.104934](https://doi.org/10.1016/j.envint.2019.104934)).  
**Donc** : le gain +18–21 pts des covariables *vs* interpolation seule est crédible ; le gain *vs* KED PREV’AIR **n’est pas encore prouvé** — c’est exactement ce qu’il reste à revendiquer.  
**Test sans sorties PREV’AIR** : (i) proxy local = CHIMERE/CAMS brut + krigeage des résidus sur un jeu de stations *held-out* ; (ii) même protocole + covariables ; (iii) carte du ΔRMSE par type de site (trafic/fond/rural). Si le gain disparaît hors stations d’entraînement, abandonner l’angle « descente d’échelle ».  
**À vérifier** : liste exacte des covariables et résolution de la chaîne Atmo Occitanie / KED national.

### 7. Jeu public pour comparer correction locale vs PREV’AIR ?

**Partiel.** Observations validées : **GEOD’AIR** / Atmo Data / open data AASQA (mesures stations).  
PREV’AIR : cartes et PREV’AIR+ historiques ([prevair.org](https://www.prevair.org/)) — accès programmatique multi-années aux **champs bruts émis à chaque run** (version, heure de cut-off) **à vérifier**.  
CAMS Europe ADS : analyses/prévisions ~3 ans glissants à 0,1° ([ADS CAMS Europe](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts)).  
Proxy honnête : calibrer sur CAMS, évaluer sur stations Geod’air **aux mêmes dates**, et comparer *a posteriori* aux cartes PREV’AIR archivées (PDF/web) sur quelques épisodes documentés — pas un benchmark pixel-parfait.  
**À vérifier** : conditions d’accès PREV’AIR+ pour un tiers et licence de réutilisation des grilles.

### 8. Pourquoi la correction dégrade les pics d’O₃ et améliore NO₂/PM2.5 ? ★

**Asymétrie physiquement plausible et partiellement documentée dans la littérature de post-traitement, sans être un théorème.**  
**O₃** : polluant secondaire, non linéaire (régimes NOx-limited vs VOC-limited), maxima diurnes sensibles à la météo et au transport ; une régression sur l’erreur moyenne **tire les extrêmes vers la moyenne** (régression vers la moyenne / lissage des quantiles hauts). Les pics d’ozone estivaux sont rares dans un corpus de 3 mois — le modèle n’a presque pas vu la queue.  
**NO₂ / PM2.5** : plus liés à sources locales et biais de fond plus stables ; la correction additive/multiplicative locale fonctionne mieux ; les pics trafic/chauffage sont plus fréquents et mieux échantillonnés.  
Documenté au sens large : biais des CTM et post-processing statistique améliorent souvent les scores moyens tout en **sous-estimant les extrêmes** si la perte est L2/RMSE ([literature bias-correction AQ ; voir aussi performances PREV’AIR centrées seuils](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
**Votre −19 % en validation temporelle estivale** colle à « domaine hors apprentissage » plus qu’à une fatalité O₃.  
**Test** : courbes fiabilité par quantile, CSI/POD aux seuils info/alerte, et régression quantile vs RMSE — si le POD O₃ chute et le CSI NO₂ monte, l’asymétrie est mesurée, pas racontée.  
**À vérifier** : publications Ineris/PREV’AIR sur scores par quantile O₃ post-ML (non extraites ici ligne à ligne).

### 9. Méthodes qui préservent la queue de distribution

- **Régression quantile** / forests quantiles : cibler q0.9–0.95 plutôt que la moyenne.  
- **Perte asymétrique** (pinball, weighted MSE sur excès de seuil, focal loss pour dépassements).  
- **Deux régimes** : classifieur « épisode / non-épisode » + régresseur conditionnel ; ou mixture.  
- **Copules / post-hoc calibration** (isotonic, conformal prediction) pour recalibrer les queues sans retoucher le cœur.  
- **Data augmentation** d’épisodes (années multiples, analogues météo).  
Référence méthodologique générale : Koenker quantile regression ; conformal prediction (Angelopoulos & Bates, 2023).  
En AQ opérationnelle, PREV’AIR vise explicitement les **seuils réglementaires** via ML ([prevair.org](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)) — s’aligner sur POD/FAR aux seuils, pas seulement RMSE.  
**Action 3 semaines** : une perte pinball + métriques seuil O₃/NO₂/PM, sans changer l’architecture.

### 10. Détecter l’extrapolation hors domaine en production

- **Distance au training** : Mahalanobis / kNN sur espace de features (météo, saison, CAMS brut, type station).  
- **Incertitude modèle** : écart-type d’ensemble (GBM bagging, MC dropout), **conformal prediction** avec couverture garantie sous échangeabilité.  
- **Règles métier** : saison absente de l’archive, type de site jamais vu, panne d’entrée, vent/température hors percentiles train.  
- **Monitoring** : drift de distribution (PSI, KS) des inputs jour J vs train ; alerte si residual vs stations voisines explose.  
- **Fail-safe** : revenir à PREV’AIR/CAMS brut si score de confiance < seuil.  
Réf. utiles : conformal prediction ; monitoring MLOps.  
**À vérifier** : ce que le référentiel LCSQA prévision exige déjà en traçabilité d’incertitude ([LCSQA RTN prévision](https://www.lcsqa.org/fr/rtn)).

---

## C. Ce qui aurait le plus de valeur pour ATMO Occitanie

### 11. Problème opérationnel méditerranéen le moins outillé

Candidats : **ozone estival** (photochimie, brises de mer, panaches urbains), **intrusions sahariennes** (PM), **feux de végétation**, et **exposition fine ZFE/métropoles** sous futures VL 2030.  
CAMS 2025 souligne encore épisodes chaleur/ozone et poussières ([CAMS AAR 2025, 29/06/2026](https://atmosphere.copernicus.eu/cams-releases-annual-assessment-report-european-air-quality-2025-0)).  
Atmo Occitanie alerte régulièrement ozone (ex. prévision 29–30/07/2026 sur le site) et PM sahariennes (ex. 13/07/2026 PO).  
**Hypothèse de valeur** : outillage semi-automatique *attribution d’épisode + confiance + message collectivités* plus que un point de RMSE national.  
**À vérifier** en entretien : ce qui consomme le plus d’heures expert l’été 2025–2026.

### 12. Détection automatique des apports sahariens

**Ni purement manuelle ni boîte noire unique.**  
Dispositif national **CARA** (composition chimique PM, ACSM, aethalomètres, filtres) + notes LCSQA en temps quasi-réel depuis 2015 ([LCSQA CARA](https://www.lcsqa.org/fr/le-dispositif-cara)).  
CAMS fournit poussières minérales et attribution ([CAMS AAR 2025](https://atmosphere.copernicus.eu/cams-releases-annual-assessment-report-european-air-quality-2025-0)).  
La **qualification réglementaire** « contribution naturelle » pour déduction de dépassement reste une procédure documentée (preuves, zones, concentrations) — expertise humaine + dossier ([dir. 2008/50 art. 20 héritage ; 2024/2881](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=OJ:L_202402881)).  
**À vérifier** : outil interne Atmo Occitanie (seuils auto + validation human-in-the-loop) et taux de jours PM₁₀ déduits Sahara sur 10 ans.

### 13. Charge de l’expertise quotidienne des prévisions

**Non chiffrée publiquement pour Occitanie.**  
Chaîne typique AASQA : lecture PREV’AIR/CAMS/modèle régional le matin, confrontation stations et météo, décision indice/alerte, rédaction message préfectoral/collectivités, suivi épisode.  
PREV’AIR émet des bulletins nationaux ; les AASQA portent l’expertise **régionale** et le lien préfets ([prevair.org système](https://www.prevair.org/le-systeme-prevair)).  
Ce qui allège : scores de confiance, check-lists d’épisode, pré-remplissage de bulletins, détection de divergence modèle/mesure, journal d’audit.  
**À vérifier** : ETP prévision chez Atmo Occitanie et outils déjà en place (SI, scripts).

### 14. Ce que demandent les collectivités et qui reste difficile

Demandes récurrentes (littérature fédérale + pratiques) : cartes **exposition population**, impact **ZFE/PPA**, aide à la **communication de crise**, scénarios « et si », données **quartier/école**, air intérieur, pesticides/pollens.  
Difficile : descente d’échelle **validée** (pas jolie carte), attribution causale robuste, délais courts, responsabilité juridique des chiffres.  
Directive 2024/2881 + décision 2026/1208 renforcent l’exigence de **qualité de modélisation documentée** — les collectivités voudront des chiffres « opposables ».  
**À vérifier** : cahiers des charges récents métropoles Toulouse/Montpellier/Nîmes auprès d’Atmo.

### 15. Données ouvertes Atmo Occitanie — usages non saturés

Portail ArcGIS open data + Atmo Data national (indices, épisodes, émissions, pollens) ([Atmo France Atmo Data](https://www.atmo-france.org/article/atmo-data-un-acces-unique-aux-donnees-produites-par-les-aasqa)).  
Déjà fait : indices communaux, cartes grand public, widgets.  
Peu saturé : **rejeu d’épisodes** avec incertitude, API de score de prévision locale, lien pollen×ozone santé, tableaux de bord ZFE pour élus, reconstitution sites non instrumentés avec carte d’erreur.  
**Piste projet** : productiser le leave-station-out comme service d’« angle mort du réseau ».

---

## D. Le sujet agentique, sans complaisance

### 16. Systèmes agentiques en recherche environnementale opérationnelle ?

**Presque aucun système agentique autonome en production réglementaire documenté.**  
Ce qui existe : pipelines automatisés (PREV’AIR 24/7), notebooks, assistants LLM pour littérature/code, prototypes recherche.  
Exemples « agents » médiatisés = démos, pas validation LCSQA.  
**À vérifier** : expérimentations internes Ineris/Météo-France/AASQA non publiées — par défaut, considérer **zéro déploiement autonome** sur la chaîne d’alerte.

### 17. Ce qui bloque l’adoption sous obligation réglementaire

- **Traçabilité** : qui a décidé quoi, sur quelles versions de données/modèles.  
- **Responsabilité** : le préfet/AASQA reste responsable de l’information ; un agent n’a pas de personnalité juridique.  
- **Reproductibilité** : même entrée → même sortie (LLM non déterministes = friction).  
- **Assurance qualité** : référentiels LCSQA, audits, comparaisons inter-labo.  
- **Sécurité** : pas d’exfiltration de données sensibles, pas d’action irréversible sans humain.  
Sans ces cinq points, l’outil reste un **assistant**, pas un opérateur.

### 18. Rendre auditable une chaîne agent pour un évaluateur LCSQA

Journal append-only : `run_id`, horodatage, commit code, versions datasets, prompts/outils appelés, sorties intermédiaires, hash des artefacts.  
Séparer **faits mesurés / sorties modèle / texte généré**.  
Tests de non-régression sur cas d’or (épisodes connus).  
Interdiction d’écrire en base réglementaire sans validation humaine.  
Format proche du [référentiel technique national prévision](https://www.lcsqa.org/fr/rtn) : qualité, traçabilité, métadonnées.  
**Livrable** : un rapport d’audit rejouable en une commande, pas un chat log.

### 19. Délégation admise vs non admise

**Admis (avec contrôle)** : collecte, nettoyage, calcul reproductible, rédaction de brouillon, détection d’anomalie, suggestion de diagnostic.  
**Non admis** : décision d’alerte réglementaire, modification silencieuse de données validées, communication publique non relue, arbitrage juridique de déduction Sahara.  
Règle simple : **l’humain signe** ; la machine propose.

### 20. Intérêt pour un candidat de mettre l’agentique en avant ?

**Oui en outil d’efficacité, non en promesse d’autonomie.**  
Atmo Occitanie recrute un **Responsable projets IA** centré déploiement maîtrisé — pas un agent libre.  
Mettre en avant : automatisation traçable, gains de temps expert, garde-fous.  
Contre-productif : jargon agentique, démo chatbot sans métrique AQ, contournement de la validation.  
**Positionnement** : « j’accélère l’expertise humaine sous contrainte LCSQA ».

---

## E. Les modèles, maintenant que le paysage est connu

### 21. Un GNN sur 476 stations vs modèle par station + covariables ? ★

**À ce jour, pas de preuve publiée que un GNN batte un GBM/MLP riche en covariables sur un graphe ~500 stations AQ françaises.**  
GNN AQ publiés (ex. PM2.5 Chine, réseaux urbains denses) montrent des gains quand la **topologie et le transport** dominent et que le graphe est dense/temporellement riche ; tailles souvent **≫ 500 nœuds** ou grilles régulières, pas un réseau réglementaire hétérogène.  
Sur graphe creux (distance médiane voisins ~km, types de sites hétérogènes), le message-passing apporte surtout un lissage spatial — **proche d’un krigeage / GAT léger**, redondant avec KED + covariables.  
Coût : fuite spatiale si validation mal faite, opacité, ops plus lourde.  
**Verdict opérationnel 2026** : baseline forte = **modèle tabulaire (GBM/RealMLP) par point + covariables + residual CTM** ; GNN = piste recherche si vous montrez un gain leave-location-out **et** leave-time-out sur O₃ estival.  
**À vérifier** : papiers 2024–2026 « graph neural air quality monitoring network » sur N≈10²–10³ — comparer N et protocole avant de promettre.

### 22. RealMLP / MLP moderne vs gradient boosting

**Preuves hors AQ** : RealMLP et MLP bien régularisés sont compétitifs voire supérieurs aux GBM sur certains benchmarks tabulaires récents (voir travaux Holzmüller et al. / notebooks RealMLP ; compétitions Kaggle tabulaires 2024–2025).  
**En AQ** : XGBoost/LightGBM restent le défaut des post-corrections et LUR modernes faute de benchmark public RealMLP×CAMS.  
Avantage MLP : multi-tâches multi-polluants, embeddings de station, incertitude.  
Avantage GBM : robustesse petit N, feature importance, ops simple.  
**Décision** : benchmark **identique** (mêmes plis spatiaux/temporels) ; ne pas remplacer le GBM tant que le gain < bruit de validation.  
Votre notebook `ps-s6-e7-realmlp-pytorch` est un atout **si** rejoué sur le protocole AQ du projet.

### 23. Modèles de fondation pour séries temporelles

Candidats : TimesFM, Chronos, Moirai, Lag-Llama, etc. (2024–2025).  
Transfert zéro-shot sur AQ **peu documenté** ; séries AQ = exogènes météo/CTM + multi-sites, mal couverts par fondations univariées.  
Tentatives « foundation air quality » : **à vérifier** au cas par cas ; aucune adoption AASQA connue.  
**Usage réaliste** : features / prior de tendance, pas remplacement de la correction CTM.  
Risque : coût, opacité, hors distribution saisonnière.

### 24. Architecture pour heures et polluants manquants

- Masques de disponibilité en entrée + loss masquée.  
- Multi-tâche partagé (backbone) + têtes par polluant.  
- Imputation **séparée** et documentée (ne pas confondre avec prévision).  
- Ne jamais entraîner sur cibles imputées pour la métrique officielle.  
Évaluer séparément : performance quand l’entrée CAMS est complète vs dégradée.

### 25. Assimilation de données vs correction a posteriori

**Assimilation** (3DVar/EnKF dans le CTM) : corrige l’état du modèle, propage physiquement, coûteux, réservé centres (CAMS, PREV’AIR analyses).  
**Post-correction ML** : cheap, locale, n’améliore pas la dynamique interne.  
**Combinables** : assimilation → analyse ; ML sur prévision brute pour J+1…J+5 ; c’est déjà l’esprit PREV’AIR (modèle + obs + ML + krigeage) ([prevair.org](https://www.prevair.org/le-systeme-prevair)).  
Le candidat ne concurrencera pas l’assimilation Ineris ; il peut **spécialiser** la post-correction occitane.

---

## F. Décider, avec trois semaines devant soi

### 26. Étendre l’archive à un an vs approfondir autre chose ?

**Pour un jury AASQA : un an d’archive bien validé bat une architecture neuve sur 3 mois.**  
Le −19 % estival est aujourd’hui l’objection fatale ; la fermer avec un été d’entraînement + un été test indépendant transforme le récit.  
Si le téléchargement un an est hors délai : au minimum **un second trimestre contrasté** + protocole temporel transparent.  
Approfondir covariables vs KED (Q6) est le 2ᵉ meilleur investissement — décide ce qui reste revendiquable face à PREV’AIR.

### 27. Démo interactive vs rapport écrit ?

Les deux, **rapport d’abord**.  
Jury technique AASQA lit : protocole, fuites évitées, métriques seuil, limites.  
La démo (carte, station held-out, épisode) **prouve** que ce n’est pas du vent — utile en entretien, insuffisante seule.  
Atmo recrute aussi un profil qui **vulgarise** (offre data junior) : 3 minutes de démo + 10 de méthodes.

### 28. Profondeur technique d’un jury mixte

Attendre : un expert modélisation/data capable d’attaquer validation et fuite ; des profils métier (prévision, partenariats) sensibles à l’utilité opérationnelle ; RH sur collaboration.  
Ne pas noyer sous GNN/agents ; tenir RMSE **et** POD au seuil **et** « comment on bascule en secours ».  
Connaître PREV’AIR/CHIMERE/CAMS/LCSQA par leur nom exact.

### 29. Signaux « opérationnel » plutôt que « prometteur »

- Dit ce qui **ne marche pas** (−19 %) et comment le corriger.  
- Protocole leave-station **et** leave-time, sans fuite.  
- Métadonnées run/version/horizon.  
- Comparaison honnête à un baseline national (CAMS/PREV’AIR), pas seulement à soi-même.  
- Code reproductible, pas une unique accuracy.  
- Vocabulaire métier (indice ATMO, seuil info/alerte, représentativité) avant jargon DL.

### 30. Une seule chose sur laquelle parier

**Fermer le trou temporel et prouver un gain résiduel des covariables contre un proxy KED/CTM — en leave-station-out.**  
Pourquoi : (1) l’objection saison est la seule qui tue la crédibilité actuelle ; (2) la Q6 décide si le projet apporte encore quelque chose que PREV’AIR n’a pas ; (3) Atmo Occitanie embauche pour **IA utile et déployable**, pas pour une 476ᵉ architecture.  
Trois semaines : archive étendue autant que possible → baseline CTM+krigeage résiduel → +covariables → métriques seuil O₃/NO₂/PM → une page « limites et bascule humaine ».  
Le reste (GNN, agents, RealMLP) est bonus **après** ces deux preuves.

---

## Focus — synthèse des trois questions prioritaires

| # | Question | Verdict au 29/07/2026 |
|---|----------|------------------------|
| **6** | Covariables vs dérive CHIMERE | Complémentarité **plausible** ; gain *vs* KED PREV’AIR **non démontré** — test held-out obligatoire |
| **8** | Pics O₃ ↓ / NO₂·PM ↑ | Asymétrie **cohérente** (secondaire non linéaire + sous-échantillonnage des queues + perte L2) ; la mesurer par quantiles/seuils |
| **21** | GNN vs tabulaire+covariables | **Pas de preuve** sur graphe ~500 stations hétérogènes ; baseline tabulaire d’abord |

---

*Document généré pour le dossier candidat ATMO Occitanie. Re-vérifier Legifrance (transposition FR) et l’état des offres d’emploi avant envoi de candidature.*
