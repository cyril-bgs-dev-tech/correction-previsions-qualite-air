# Prompt ChatGPT R6 — 30 questions pour trancher, et pour aller chercher la performance

**Intention.** Les rondes précédentes ont servi à sourcer et à situer. Celle-ci sert à
**décider**. Le projet a huit expériences chiffrées, un GPU disponible, et trois semaines.
La question n'est plus « que pourrait-on faire » mais « qu'est-ce qui, dans ce dispositif,
plafonne le résultat — et quel est le test le moins cher qui tuerait chaque piste si elle
est mauvaise ».

L'ordre des blocs n'est pas décoratif : on demande le **plafond** avant les leviers, parce
qu'un levier ne vaut que rapporté à ce qui reste à gagner. Puis le **diagnostic** de ce qui
plafonne, puis les leviers, puis le protocole, et enfin la discrimination des actions.

À coller tel quel.

---

> Tu es un praticien de la data avec vingt ans de métier, dont une part en prévision
> environnementale opérationnelle. Tu as vu beaucoup de projets gagner trois points de RMSE
> sans jamais servir, et quelques-uns servir sans jamais gagner un point. Je te donne un
> dispositif complet et chiffré. Je veux que tu m'aides à **trancher**, pas à explorer.
>
> ## Règles de réponse — elles comptent autant que le contenu
>
> 1. **Aucune suggestion sans les quatre colonnes** : gain attendu (chiffré, ou
>    explicitement **Inconnu**), coût en heures de travail et de calcul, **test de
>    falsification** — l'expérience la moins chère qui la tue si elle est mauvaise — et
>    **critère d'abandon** : à quel résultat j'arrête d'y croire.
> 2. **Pas de généralités.** « Essayer un ensemble », « tuner les hyperparamètres », « faire
>    du feature engineering » ne sont pas des réponses. Ce qui compte est *quel* ensemble,
>    *quel* paramètre, *quelle* variable, et pourquoi celui-là plutôt qu'un autre dans **ce**
>    dispositif.
> 3. **Distingue toujours** ce qui est publié (avec DOI) de ton jugement de praticien.
>    Étiquette-le. Un jugement assumé m'est utile ; un jugement déguisé en fait me coûte
>    cher.
> 4. **Si une de mes prémisses est fausse, commence par le dire.** Je préfère perdre une
>    question à gagner une correction.
> 5. **Rien qui dépasse une journée de calcul.** J'ai un GPU RTX 5090 et trois semaines
>    calendaires, dont l'essentiel doit aller à la rédaction.
>
> ## Le dispositif
>
> Correction apprise des prévisions **CAMS Europe** (0,1° ≈ 8 km, J+1 à J+3) **aux stations
> de mesure**, France entière. **17 mois** d'observations horaires appariées (août 2023 →
> décembre 2024). Cible = **résidu** `observation − CAMS`, prédiction = `CAMS + résidu
> prédit`, écrêtée à zéro. Validation par plis de **stations entièrement exclues** ;
> intervalles bootstrapés **par station**. 52 variables : sorties CAMS, météo ERA5,
> calendrier, 38 descripteurs de paysage, 9 de relief, trafic hiérarchisé, population.
> **Aucune observation récente n'est utilisée comme prédicteur. Aucun hyperparamètre n'a été
> optimisé.**
>
> ### Performance — O₃ à J+1, 3,23 M de paires, 270 stations, stations exclues
>
> | Approche | RMSE | gain / CAMS |
> |---|---|---|
> | CAMS brut | 16,97 | — |
> | débiaisage **sans apprentissage** (biais moyen par mois) | 15,73 | +7,3 % |
> | Ridge (`RidgeCV`, 52 variables) | 15,47 | +8,9 % |
> | Forêt aléatoire (bridée) | 14,45 | +14,9 % |
> | CatBoost / XGBoost (GPU) | ≈ 14,0 | ≈ +12 % |
> | **LightGBM** | **13,68** | **+19,4 %** |
>
> NO₂ : 12,87 → 9,05 (**+29,7 %**), dont **+13,0 %** apportés par la seule hiérarchisation
> du trafic (BD TOPO `importance` au lieu de la longueur de voirie ; la population
> n'ajoute rien).
>
> ### Généralisation
>
> | Ce qui est caché | Plis | Gain | Étendue |
> |---|---|---|---|
> | Stations jamais vues | 3 | **+19,4 %** | +17,8 à +20,6 % (σ 1,2) |
> | Mois jamais vu | 18 | +14,4 % | **−14,6** à +32,6 % (σ 9,1) |
> | Stations **et** mois jamais vus | 18 | +8,7 % | **−24,9** à +29,7 % (σ 10,5) |
>
> ### Les extrêmes — mon échec le mieux établi
>
> Décile supérieur d'ozone (> 85,6 µg/m³) : CAMS 15,18 · correction par erreur quadratique
> **15,65 (−3,1 %, pire que le brut)** · quantile pinball q=0,90 : 11,85 (+21,9 % sur la
> queue mais RMSE global 20,90, pire que CAMS) · **quadratique pondérée par la
> concentration : 13,89 (+8,5 %)** pour un RMSE global de 14,86 (+12,4 %).
>
> Croisé avec les régimes météo, le gain sur le décile supérieur est **négatif dans presque
> tous** : photochimique +1,2 %, précipitations −4,8 %, stagnation −6,7 %, ventilé −8,8 %.
> Alors que sur l'ensemble de la distribution, ces mêmes régimes donnent +17,7 %, +9,2 %,
> +25,7 % et +14,7 %.
>
> ### Service rendu, format LCSQA (POD, FAR, CSI)
>
> | Polluant · seuil | POD brut → corrigé | FAR brut → corrigé | CSI brut → corrigé |
> |---|---|---|---|
> | PM2.5 · moyenne jour 25 | 0,198 → **0,372** | 0,734 → **0,277** | 0,128 → **0,325** |
> | O₃ · max 8 h 120 | 0,360 → **0,345** | 0,362 → **0,203** | 0,299 → 0,317 |
> | NO₂ · max horaire 120 | 0,007 → 0,015 | 0,818 → 0,733 | 0,007 → 0,014 |
>
> La correction améliore 57,9 % des heures mais seulement **16,2 %** changent de classe
> d'indice.
>
> ### Ablation (O₃, perte de RMSE quand on retire la famille)
>
> Calendrier **+9,1 %** · relief +2,9 % · routes +0,6 % · coordonnées +0,6 % ·
> **forêt −1,0 %** · **échéance −0,5 %** (les deux dernières *améliorent* si on les retire).
>
> Et : les covariables de terrain battent une **interpolation spatiale du résidu** (13,69
> contre 15,85) — mais **empiler les deux dégrade** (14,20).
>
> ### Repères de littérature déjà établis
>
> Riccio & Chianese 2024 (doi:10.5194/acp-24-1673-2024), CAMS Italie J+1, **stations
> exclues**, cibles journalières : O₃ +29,9 %, NO₂ +28,5 %, PM2.5 +27,4 %. Bertrand et al.
> 2023 (doi:10.5194/acp-23-5317-2023), CAMS Europe, **stations vues**, horaire : O₃ +29 %,
> NO₂ +29-33 %. Chez Riccio & Chianese, le gain chute de **24 à 36 points** entre stations
> vues et exclues. Mon O₃ à +19,3 % est donc plutôt **bas** même en tenant compte du
> protocole.
>
> ### Contraintes
>
> Aucune observation en 2025 (les mesures s'arrêtent au 31/12/2024) alors que les prévisions
> CAMS vont jusqu'à juin 2025. L'ozone temps réel de l'EEA est rompu pour la France depuis
> le 01/07/2025. Deux ruptures opérationnelles CAMS documentées, les 13/11 et 03/12/2024 —
> et c'est exactement là que le RMSE de CAMS grimpe et que mon gain explose (+30 à +34 %
> en octobre-décembre 2024 contre +14 à +22 % un an plus tôt à saison égale).
>
> ---
>
> ## Bloc A — Le plafond : combien reste-t-il vraiment à gagner ? (Q1-Q5)
>
> **Q1.** Quelle est l'**erreur irréductible** dans ma configuration ? Décompose-la :
> incertitude de mesure des stations de référence, erreur de **représentativité** entre une
> maille de 8 km et un point de mesure, et variabilité sous-maille intrinsèque. Donne des
> ordres de grandeur sourcés en µg/m³ pour O₃ et NO₂. Si mon RMSE résiduel de 13,68 est déjà
> proche de ce plancher, tout le reste de ce questionnaire est vain — dis-le.
>
> **Q2.** Comment **estimer empiriquement** ce plancher avec mes seules données ? Je pense à
> l'écart entre stations proches et de même typologie, ou à des stations co-localisées.
> Quelle méthode, quelle précaution, et quel biais aurait-elle ?
>
> **Q3.** Existe-t-il un plafond **théorique** connu au post-traitement statistique d'un
> modèle de chimie-transport ? Autrement dit : quelle part de l'erreur d'un CTM est
> structurellement corrigeable depuis l'aval, sans toucher aux émissions ni à la chimie ?
>
> **Q4.** Mon R² passe de 0,584 à 0,730 sur l'ozone. En prévision de qualité de l'air à
> J+1, quel R² sur **stations exclues** constitue un bon résultat, un résultat moyen, et un
> résultat suspect de fuite ?
>
> **Q5.** Vu l'écart entre mon +19,3 % et les +29 à +30 % publiés, dis-moi **où sont
> passés** ces dix points, par ordre de probabilité décroissante : cible horaire contre
> journalière, densité du réseau, absence d'observations récentes, absence de tuning,
> qualité de mes covariables, ou autre. Chiffre chaque hypothèse si tu peux.
>
> ## Bloc B — Diagnostiquer ce qui plafonne (Q6-Q11)
>
> **Q6.** Quelle **décomposition de l'erreur résiduelle** dois-je produire en priorité pour
> savoir où je perds : par station, par heure du jour, par niveau de concentration, par
> régime, par typologie ? Donne-m'en **une seule** — la plus discriminante — et dis ce que
> je devrais voir si l'erreur est du bruit, et ce que je verrais si elle est structurelle.
>
> **Q7.** Mon résidu après correction est-il **prévisible** ? Si j'ajuste un second modèle
> sur les résidus du premier et qu'il trouve du signal, que dois-je en conclure — capacité
> insuffisante, variables manquantes, ou fuite dans ma validation ?
>
> **Q8.** Comment séparer l'erreur qui vient de **CAMS** de celle qui vient de la
> **représentativité de la station** ? Si une station est structurellement irrécupérable,
> comment le démontrer plutôt que le supposer — et faut-il l'exclure de l'évaluation, ce qui
> serait suspect, ou la garder en la nommant ?
>
> **Q9.** Le **calendrier** est ma famille de variables la plus utile (+9,1 %). Est-ce bon
> signe — le modèle capte une saisonnalité réelle du biais — ou mauvais — il mémorise
> *quand* plutôt que d'apprendre *pourquoi*, ce qui expliquerait l'échec sur un mois inconnu ?
> Quelle expérience départage les deux ?
>
> **Q10.** Retirer la **forêt** et l'**échéance** *améliore* légèrement (−1,0 % et −0,5 %).
> Bruit d'échantillonnage, ou signal réel de variables nuisibles ? Quel test le tranche, et
> à partir de quel écart dois-je considérer une ablation comme concluante ?
>
> **Q11.** **Empiler** covariables de terrain et interpolation du résidu **dégrade** (13,69
> → 14,20). Quel mécanisme l'explique le plus probablement, et comment le vérifier ? Ce
> résultat est-il publié quelque part — il concerne directement les AASQA, qui pratiquent la
> fusion données-modèle par krigeage.
>
> ## Bloc C — Les leviers de performance (Q12-Q18)
>
> **Q12.** **Observations récentes.** Toute la littérature opérationnelle les emploie, leur
> gain marginal isolé n'est pas publié. Quelles variables exactement — dernière valeur
> disponible, moyenne des 24 h, biais récent de la station sur 7 jours, anomalie par rapport
> à sa climatologie ? Classe-les par gain attendu. Et comment construire proprement le
> **modèle de repli** pour une station sans flux, sans imputer une absence future ?
>
> **Q13.** **Copolluants.** Les concentrations CAMS de NO₂, NO, PM et COV comme prédicteurs
> de l'ozone — gain publié ? Et le risque : je corrélerais mes trois cibles entre elles.
>
> **Q14.** **Dispersion d'ensemble.** CAMS Europe est un ensemble de modèles. L'écart-type
> entre membres, à la maille et à l'heure, est-il un prédicteur utile de l'erreur —
> autrement dit une mesure d'incertitude exploitable ? Gain publié ?
>
> **Q15.** **Transformation de la cible.** Mon résidu est asymétrique et la queue est
> écrasée. Travailler en `log(1+y)`, en racine, ou en quantiles normalisés change-t-il
> quelque chose de mesurable — ou est-ce un déplacement du problème ?
>
> **Q16.** **Multi-tâches et multi-horizons.** Un modèle unique pour les trois polluants ou
> les trois échéances, contre un modèle par cible : que dit la littérature, et à partir de
> quel volume de données le partage de représentation devient-il payant ?
>
> **Q17.** **Hyperparamètres.** Je n'ai rien optimisé. Quel gain typique une recherche
> sérieuse apporte-t-elle sur du gradient boosting dans ce type de tâche — 1 %, 5 %,
> 15 % ? Et quels **deux ou trois** paramètres portent l'essentiel, pour que je ne dépense
> pas une nuit de GPU à explorer un espace inutile ?
>
> **Q18.** **Architecture.** Sur mes données, LightGBM (+19,4 %) devance la forêt (+14,9 %)
> et le linéaire (+8,9 %), et XGBoost comme CatBoost sont à 0,3 point de LightGBM. Je teste
> RealMLP et TabM sur GPU. Étant donné que l'écart entre bibliothèques de boosting est dix
> fois plus petit que celui entre familles de modèles, **est-ce que continuer à comparer des
> architectures est le bon emploi de mon temps** — ou ai-je déjà la réponse ?
>
> ## Bloc D — Les extrêmes, qui décident du service rendu (Q19-Q23)
>
> **Q19.** Ma correction est **pire que CAMS brut sur le décile supérieur**. Avant de
> chercher une solution : est-ce un défaut de la **perte**, de la **cible résiduelle**, du
> **déséquilibre** de la distribution, ou de l'**écrêtage à zéro** ? Comment attribuer ?
>
> **Q20.** Prédire directement la **probabilité de dépassement** par classification
> calibrée, au lieu de seuiller une moyenne conditionnelle : gain publié en POD/FAR/CSI ?
> Et quelle méthode de calibration sur des données spatialement corrélées ?
>
> **Q21.** Ma perte pondérée gagne +8,5 % sur la queue en cédant 7 points de gain global.
> Existe-t-il une formulation qui **domine** ce compromis plutôt que de s'y déplacer —
> régression composite, apprentissage à deux têtes, contrainte sur les quantiles ?
>
> **Q22.** Le POD baisse alors que le FAR s'effondre : ma correction rend le modèle
> **conservateur**. Pour une AASQA, quel est le bon arbitrage entre alerte manquée et fausse
> alerte, et existe-t-il une **règle publiée** ou un coût relatif documenté sur lequel
> m'appuyer plutôt que de choisir arbitrairement ?
>
> **Q23.** PM2.5 est le seul polluant où POD **et** FAR s'améliorent ensemble. Pourquoi
> celui-là ? Qu'est-ce que sa physique ou sa statistique a de différent, et cette
> explication suggère-t-elle un traitement spécifique pour O₃ et NO₂ ?
>
> ## Bloc E — Protocole : ne pas se tromper sur ce qu'on mesure (Q24-Q27)
>
> **Q24.** Mon gain temporel moyen est monté de +3,4 % (7 mois) à +14,4 % (17 mois) mais le
> pire pli est **descendu** de +5,4 % à −14,6 %. Comment distinguer proprement ces trois
> causes : **non-stationnarité** du système, **manque de données**, et simple **effet du
> nombre de plis** — on voit plus de mauvais mois quand on en teste plus ?
>
> **Q25.** Une part de mon gain vient peut-être d'une **dégradation de CAMS** fin 2024
> (ruptures documentées les 13/11 et 03/12/2024) plutôt que d'un progrès de mon modèle.
> Comment le mesurer proprement, et si c'est confirmé, comment le **présenter** sans
> détruire le résultat ni le dissimuler ?
>
> **Q26.** J'ai fait beaucoup de choix en regardant des résultats de validation
> (prétraitement, seuils, familles de variables). Comment estimer l'**optimisme** accumulé,
> et faut-il réserver dès maintenant un jeu de test définitivement intouché — sachant qu'il
> me coûterait des données que je n'ai pas en abondance ?
>
> **Q27.** Avec 18 plis temporels et 3 plis spatiaux, quelle est la **puissance
> statistique** de mes comparaisons ? Un écart de 0,3 point entre XGBoost et LightGBM est-il
> interprétable, ou dois-je le déclarer nul ? Quel test pour comparer deux modèles sur des
> résidus spatialement et temporellement corrélés ?
>
> ## Bloc F — Discriminer : que faire, et que ne pas faire (Q28-Q30)
>
> **Q28.** Ordonne **tout ce que j'ai listé** en trois catégories, et une seule fois chaque
> action : *à faire* (gain probable, coût maîtrisé, falsifiable vite), *à tester d'abord par
> un test tueur* (gain incertain, test court), *à ne pas faire* (gain faible, coût élevé, ou
> déjà répondu par ce que j'ai). Justifie chaque classement en une ligne.
>
> **Q29.** Quel est le **critère d'arrêt** de ce projet ? Formulé autrement : à quel moment
> un point de RMSE supplémentaire cesse de valoir la journée qu'il coûte, étant donné que le
> livrable est une candidature et non un système en production ? Donne un critère
> **opérationnel**, pas une maxime.
>
> **Q30.** Si tu ne devais garder qu'**une seule** de ces trente questions comme la plus
> déterminante pour la valeur finale du travail, laquelle, et pourquoi celle-là ? Et quelle
> question **essentielle ai-je omise** ?
>
> ---
>
> **Format.** Un bloc par section, une réponse par question, chacune avec les quatre
> colonnes exigées quand elle propose une action. Étiquette **[publié]** ou **[jugement]**.
> Pas d'introduction, pas de synthèse de mes propres résultats. Termine par les points
> classés **Inconnu** — et je les compte comme des réponses utiles, pas comme des échecs.
