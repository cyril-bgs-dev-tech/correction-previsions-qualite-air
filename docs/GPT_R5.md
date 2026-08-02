## 1. L’ordre de grandeur

### Réponse

La seule comparaison trouvée qui exclut réellement des stations de l’apprentissage est
Riccio et Chianese (2024). Pour CAMS Europe à J+1 en Italie, leur post-traitement réduit la
RMSE de 34,8 % pour la moyenne journalière de PM10 (12,21 → 7,96 µg/m³), de 27,4 % pour
la moyenne journalière de PM2.5 (7,91 → 5,74), de 28,5 % pour le maximum journalier
horaire de NO₂ (26,59 → 19,02) et de 29,9 % pour le maximum journalier 8 h d’O₃
(19,97 → 13,99). Ce sont des **stations exclues**, mais pas des concentrations horaires :
ce n’est donc pas une comparaison métrique exacte avec vos résultats.

Sur **stations vues**, Bertrand et al. (2023) obtiennent, pour la première journée de
prévision CAMS en Europe et sur concentrations horaires, des baisses de RMSE de 29 % pour
l’O₃, 29–33 % pour le NO₂, 25 % pour les PM10 et 20–22 % pour les PM2.5, selon l’approche
locale ou globale retenue. La même publication montre des gains plus élevés quand le
modèle vise directement une statistique journalière : comparer votre RMSE horaire à une
RMSE de maximum journalier avantagerait artificiellement l’article.

**Jugement, non résultat publié.** Votre +29,7 % en NO₂ est normal : il coïncide presque
avec le résultat italien sur stations exclues et avec la plage européenne sur stations
vues. Votre +19,3 % en O₃ est plutôt bas par rapport au seul repère horaire européen
trouvé, mais reste plausible compte tenu de votre contrainte spatiale plus sévère. Ni
l’un ni l’autre n’est, à lui seul, un signal de fuite. Une fourchette robuste propre aux
**stations exclues, données horaires, France, J+1** est **Inconnu**.

### Sources

- Riccio, A. et Chianese, E. (2024), *Atmospheric Chemistry and Physics*,
  « Technical note: Accurate, reliable, and high-resolution air quality predictions… »,
  [doi:10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024),
  tableau 2 ; validation sur des stations italiennes retirées de l’apprentissage.
- Bertrand, J.-M., Meleux, F., Ung, A., Descombes, G. et Colette, A. (2023),
  *Atmospheric Chemistry and Physics*, « Improving the European air quality forecast… »,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023),
  tableau 2 ; première journée, Europe, stations présentes dans l’apprentissage.

## 2. Ce qui explique les écarts entre études

### Réponse

Le classement quantitatif défendable est seulement **partiel** :

1. **Protocole spatial.** Chez Riccio et Chianese (2024), le gain tombe, entre les
   stations d’apprentissage et les stations exclues, de 58,4 à 34,8 % pour les PM10,
   de 53,9 à 27,4 % pour les PM2.5, de 54,2 à 28,5 % pour le NO₂ et de 65,7 à 29,9 %
   pour l’O₃. L’écart de protocole atteint donc 23,6 à 35,8 points : c’est le premier
   facteur mesuré.
2. **Polluant et cible temporelle.** Dans un protocole unique sur stations vues,
   Bertrand et al. (2023) trouvent des gains horaires allant de 20 à 33 % selon le
   polluant, et montrent qu’extraire le maximum journalier d’une correction horaire
   donne 20,5 % de gain, contre 32,8 % lorsque le modèle est entraîné directement sur
   ce maximum.
3. **Site et réseau.** À Stockholm, Zhang et al. (2024) concluent que la variation de
   performance dépend davantage du polluant et du site que de l’algorithme ; l’étude
   porte toutefois sur seulement quatre stations et ne quantifie pas un effet causal
   de la densité du réseau.
4. **Durée d’apprentissage.** Bertrand et al. (2023) observent un bénéfice en passant
   de quatre à huit mois estivaux pour l’O₃, mais ne donnent pas dans le texte une
   différence unique transposable à votre dispositif.
5. **Saison.** Petetin et al. (2022) documentent des performances dépendant de la saison
   pour l’O₃ ibérique, sans expérience permettant d’isoler un « effet saison » universel.

**Jugement.** Seuls les deux premiers rangs sont soutenus par des écarts contrôlés. Entre
densité du réseau, durée et saison, un classement par ampleur est **Inconnu** ; annoncer
un ordre plus précis transformerait des comparaisons entre études en effets causaux.

### Sources

- Riccio et Chianese (2024), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024), tableau 2.
- Bertrand et al. (2023), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023),
  tableaux 2–3 et section 4.
- Zhang, Z., Johansson, C., Engardt, M., Stafoggia, M. et Ma, X. (2024),
  *Atmospheric Chemistry and Physics*, « Improving 3-day deterministic air pollution
  forecasts using machine learning algorithms »,
  [doi:10.5194/acp-24-807-2024](https://doi.org/10.5194/acp-24-807-2024).
- Petetin, H. et al. (2022), *Atmospheric Chemistry and Physics*, « Model output
  statistics applied to CAMS O₃ forecasts… »,
  [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).

## 3. Les variables que la littérature juge décisives

### Réponse

Les familles récurrentes sont : prévision du modèle de chimie-transport pour le polluant
cible et les copolluants ; observations récentes ; météo prévue, notamment vent,
température et hauteur de couche limite ; calendrier ; puis des variables spatiales
statiques pour transférer entre sites. Ce dernier groupe est particulièrement pertinent
pour votre objectif « station exclue », mais les études de prévision trouvées n’en
publient pas une ablation directement comparable à vos 38 descripteurs de paysage.

**Oui, les observations récentes de la station sont employées.** Bertrand et al. (2023)
utilisent la valeur observée la veille à la même heure dans leur MOS horaire européen,
ainsi qu’un biais récent par station dans l’approche globale. Zhang et al. (2024)
utilisent des mesures retardées, dont une moyenne retardée de 24 h ; elles figurent parmi
les variables importantes pour le NOx, les PM10 et l’O₃ à Stockholm. Vasseur et Aznarte
(2021) emploient pour le NO₂ madrilène les retards de 1 à 5 h et des retards saisonniers
jusqu’à plusieurs jours dans des prévisions allant jusqu’à 60 h.

Le **gain marginal isolé** de « dernière observation disponible » n’est pas publié dans
ces expériences : **Inconnu**. Le gain total du MOS de Bertrand et al. ne peut pas lui
être attribué, car modèle CAMS, météo, copolluants et observation retardée entrent
ensemble. Leur ajout chez vous conserverait une validation par station exclue au sens de
l’ajustement, mais changerait la promesse : le modèle généraliserait à une station
instrumentée disposant d’un flux récent, et non à un lieu sans capteur.

**Jugement.** C’est la variable non testée la plus crédible pour améliorer rapidement la
prévision temporelle. Il faut cependant comparer deux produits distincts : un modèle
« avec mesure récente » et un repli « sans mesure », sans imputer les absences futures.

### Sources

- Bertrand et al. (2023), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023),
  tableau 1 et sections 3.3–4.
- Zhang et al. (2024), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-24-807-2024](https://doi.org/10.5194/acp-24-807-2024),
  sections 3 et 4 et annexes de l’importance des variables.
- Pérez Vasseur, S. et Aznarte, J. L. (2021), *Scientific Reports*,
  « Comparing quantile regression methods for probabilistic forecasting of NO₂
  pollution levels »,
  [doi:10.1038/s41598-021-90063-3](https://doi.org/10.1038/s41598-021-90063-3).

## 4. Les architectures

### Réponse

Le gradient boosting n’est pas un état de l’art universel, mais les données publiées ne
montrent pas non plus qu’un réseau le remplace systématiquement. Sur les mêmes stations
européennes, Bertrand et al. (2023) trouvent les régressions ridge ou LASSO meilleures
pour plusieurs cibles journalières, et la forêt aléatoire meilleure pour les cibles
horaires ; le GBM n’est donc pas le vainqueur général, même face à des modèles simples.

À Stockholm, sur quatre stations et des horizons de 1 à 3 jours, Zhang et al. (2024)
comparent RF, XGBoost et LSTM : les écarts dépendent davantage du polluant et du site que
de l’architecture. Lors du transfert entre rues, RF et XGBoost n’améliorent pas
systématiquement les PM10 et le LSTM n’apporte qu’un bénéfice limité sur certains sites :
ce résultat est plus proche de votre question spatiale qu’un simple partage temporel.

Une architecture plus lourde peut gagner dans un autre régime. Pour l’O₃ à 72 h dans la
Grande Baie chinoise en 2023, AirQFormer réduit la RMSE de 11 % (1,4 ppbv) par rapport à
un LSTM et de 33 % (6,5 ppbv) par rapport à CMAQ ; Hu et al. (2025) évaluent toutefois les
mêmes stations dans le temps, pas des stations entièrement exclues. Ce chiffre ne
justifie donc pas d’attendre le même gain sur votre protocole.

**Jugement.** LightGBM est un choix défendable et compétitif, pas une revendication
d’état de l’art. Aucun article comparatif trouvé ne fournit un seuil de nombre de
stations, de mois ou d’observations à partir duquel LSTM, transformeur ou GNN devient
préférable : **Inconnu**. Aucun écart GNN–boosting comparable sur stations exclues,
CAMS Europe et J+1–J+3 n’a été trouvé : **Inconnu**.

### Sources

- Bertrand et al. (2023), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023), tableau 2.
- Zhang et al. (2024), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-24-807-2024](https://doi.org/10.5194/acp-24-807-2024).
- Hu, M., Lu, X., Chen, Y., Li, Z., Wang, Y. et Fung, J. C. H. (2025),
  *Sustainable Cities and Society*, « AirQFormer: Improving regional air quality
  forecast with a hybrid deep learning model »,
  [doi:10.1016/j.scs.2024.106113](https://doi.org/10.1016/j.scs.2024.106113).

## 5. Le problème des extrêmes

### Réponse

Votre constat est connu comme une **sous-estimation de la variabilité et des fortes
concentrations sous déséquilibre de la cible** ; « régression vers la moyenne » en est
une description correcte, mais Petetin et al. (2022) parlent surtout du faible poids des
rares épisodes dans l’objectif optimisant la RMSE. Sur l’O₃ CAMS de la péninsule Ibérique
à J+1–J+4, leur GBM améliore les scores continus tout en écrasant les valeurs hautes et
peut détecter moins bien les dépassements que des méthodes simples. Les stations sont
vues à l’apprentissage.

Les solutions effectivement publiées sont :

- **pondération des fortes concentrations ou des fortes erreurs** : Petetin et al.
  améliorent les détections mais signalent un gain faible sur CSI/PSS et un compromis
  avec les fausses alertes ; le gain numérique isolé est **Inconnu** ;
- **perte pondérée dans un réseau de correction** : pour l’O₃ horaire d’est de la Chine,
  aux horizons 24, 48, 72 et 96 h, le W-AlexNet de Li et al. (2024) réduit en moyenne la
  RMSE de 25,71 % par rapport à NAQPMS ; l’article ne publie pas dans son résumé le gain
  incrémental de la pondération seule, et les stations exclues sont **Inconnu** ;
- **régression quantile/probabiliste** : à une station de Madrid, jusqu’à 60 h, Pérez
  Vasseur et Aznarte (2021) trouvent les arbres de gradient quantiles meilleurs au
  classement conjoint RMSE–CRPS ; l’écart de RMSE attribuable à la perte quantile et la
  généralisation spatiale sont **Inconnu** ;
- **méthode adaptée à la cible événementielle** : Petetin et al. montrent que moyenne
  mobile, filtre de Kalman réglé sur un score catégoriel ou quantile mapping peuvent
  mieux préserver certains seuils que le GBM ; il n’existe pas de gagnant unique à tous
  les horizons et seuils.

**Jugement.** Votre perte quadratique pondérée est une réponse publiée au bon mécanisme,
pas une approximation aberrante. Elle n’est pas démontrée « état de l’art » : votre
propre résultat montre précisément le front de Pareto entre RMSE globale et queue. La
bonne revendication est que vous avez rendu explicite ce compromis sur stations exclues.
Un gain publié comparable pour modèle à deux régimes, mélange d’experts ou entraînement
sur les seuls dépassements est **Inconnu**.

### Sources

- Petetin et al. (2022), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022),
  sections 4–5.
- Li, Q., Li, J., Wang, Z., Liu, B., Wang, W. et Wang, Z. (2024),
  *Atmospheric Environment*, « Development of a city-level surface ozone forecasting
  system using deep learning techniques and air quality model… »,
  [doi:10.1016/j.atmosenv.2024.120865](https://doi.org/10.1016/j.atmosenv.2024.120865).
- Pérez Vasseur et Aznarte (2021), *Scientific Reports*,
  [doi:10.1038/s41598-021-90063-3](https://doi.org/10.1038/s41598-021-90063-3).
- Zhen, L., Chen, B., Wang, L., Yang, L., Xu, W. et Huang, R.-J. (2025),
  *Atmospheric Environment*, « Data imbalance causes underestimation of high ozone
  pollution… »,
  [doi:10.1016/j.atmosenv.2024.120952](https://doi.org/10.1016/j.atmosenv.2024.120952).

## 6. L’évaluation des épisodes

### Réponse

Il n’existe pas de seuil universel publié à partir duquel POD, FAR ou CSI deviendrait
« acceptable ». Ces scores dépendent du seuil de concentration, de la fréquence de base,
de l’unité de comptage et du coût relatif d’une alerte manquée et d’une fausse alerte.
Petetin et al. (2022) le montrent sur l’O₃ ibérique : le classement des méthodes change
avec le seuil, l’horizon et le score optimisé.

Deux repères opérationnels publiés donnent néanmoins l’échelle :

- pour le dépassement O₃ du maximum journalier à 180 µg/m³ en Europe, première journée
  et stations vues, le MOS de Bertrand et al. (2023) atteint un CSI de 0,30 à 0,40 selon
  la méthode ; le meilleur CSI rapporté est 0,34 pour le GBM journalier global ;
- pour le dépassement de la moyenne journalière PM10 à 50 µg/m³, même domaine et même
  horizon, le POD vaut 0,42–0,51, le taux de succès 0,59–0,68 — donc un FAR au sens
  `1 − précision` de 0,32–0,41 — et le CSI 0,35–0,40.

À titre historique, PREV’AIR détectait à J+1 seulement 20,4 à 22,5 % des dépassements
du maximum journalier O₃ à 180 µg/m³ selon le type de station en Europe sur 2004–2006
(Honoré et al., 2008). Ce résultat porte sur un seuil rare et sur une ancienne chaîne ;
ce n’est ni un objectif actuel ni une mesure propre à ATMO Occitanie.

**Jugement.** Votre POD « Mauvais » passant de 0,24 à 0,47 est du même ordre que le POD
PM10 publié par Bertrand et al., mais la comparaison s’arrête là : votre événement est
une classe d’indice multi-polluant, pas un dépassement PM10 station-jour. Sans votre
table de contingence et une convention d’agrégation identique, FAR et CSI sont
**Inconnu**. Une performance publique, récente et auditée d’une AASQA française sur cette
même classe, avec DOI, est **Inconnu**.

### Sources

- Bertrand et al. (2023), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023),
  figures 5–6 et section 5.
- Petetin et al. (2022), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).
- Honoré, C. et al. (2008), *Journal of Geophysical Research: Atmospheres*,
  « Predictability of European air quality: Assessment of 3 years of operational
  forecasts and analyses by the PREV’AIR system »,
  [doi:10.1029/2007JD008761](https://doi.org/10.1029/2007JD008761).

## Trois leviers non testés, classés par gain attendu rapporté à l’effort

1. **Ajouter les observations récentes de la station**, avec un modèle de repli sans
   observation. **Jugement :** meilleur rapport information/effort, car la littérature
   opérationnelle les utilise systématiquement ; gain marginal chiffré : **Inconnu**.
2. **Optimiser et calibrer une probabilité de dépassement**, par gradient boosting
   quantile ou classification, au lieu de déduire l’épisode d’une moyenne conditionnelle.
   **Jugement :** effort modéré et objectif aligné sur POD/FAR/CSI ; gain comparable sur
   stations exclues : **Inconnu**.
3. **Combiner deux sorties sur un front de Pareto**, modèle quadratique pour le fond et
   modèle pondéré pour la queue, avec seuil choisi uniquement sur validation.
   **Jugement :** vos modèles existent déjà ; le travail porte surtout sur la règle de
   décision. Gain publié d’un mélange comparable : **Inconnu**.

## Points classés Inconnu

- Fourchette de gain RMSE pour CAMS, France, données horaires, J+1, stations exclues.
- Ordre quantitatif entre densité du réseau, durée d’apprentissage et saison.
- Gain marginal isolé des observations récentes de la station.
- Volume de données à partir duquel un réseau dépasse le gradient boosting.
- Écart GNN–LightGBM comparable sur stations exclues et prévisions CAMS J+1–J+3.
- Gain incrémental isolé de la pondération du W-AlexNet.
- Gain comparable des modèles à deux régimes, mélanges d’experts ou modèles entraînés
  seulement sur les dépassements.
- Seuil universel d’acceptabilité pour POD, FAR ou CSI.
- FAR et CSI de votre classe « Mauvais » à partir du seul rappel communiqué.
- Performance récente d’une AASQA française, publiée avec DOI, pour cette même classe et
  la même unité de comptage.
