# R12 — La détection, et rien d’autre

## Verdict

Le renversement `1,7–4,1× → 0,85×` ne permet pas encore de conclure à un écrasement de queue : le protocole et le détecteur ont changé en même temps. La première expérience doit donc être une comparaison appariée, sur les **mêmes prédictions hors pli double aveugle**, du CAMS brut, du régresseur seuillé et du classifieur. Les chiffres du projet cités ci-dessous sont ceux du prompt ; je ne les ai pas reproduits à partir des données.

En revanche, le mécanisme soupçonné est solidement documenté. Sur CAMS O₃, un GBM peut faire partie des meilleurs modèles en RMSE et corrélation tout en sous-estimant la variabilité et en dégradant la détection des plus hauts seuils ; FAIRMODE observe lui aussi qu’une application satisfaisant son critère continu peut être moins bonne que la persistance sur les dépassements ([Petetin et al., 2022, DOI 10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022) ; [Vitali et al., 2023, DOI 10.5194/gmd-16-6029-2023](https://doi.org/10.5194/gmd-16-6029-2023)).

Le point réglementaire doit rester explicite : en France, le seuil d’information-recommandation pour l’ozone est **180 µg/m³ en moyenne horaire**. Ce n’est ni une MDA8 à 120 µg/m³, ni une classe d’indice, ni un rang ([Code de l’environnement, art. R. 221-1](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000022964539)).

---

## 1. Améliorer la RMSE tout en dégradant les extrêmes

### 1.1 Le phénomène est-il documenté ?

**Établi.** C’est précisément le résultat de Petetin et al. sur le post-traitement du médian d’ensemble CAMS régional O₃ dans la péninsule Ibérique, sur 2018–2019, 455 stations, horizons J+1 à J+4. Selon l’échelle et l’horizon, le MOS fait passer les nRMSE brutes de 20–40 % à 10–30 % et les corrélations de 0,7–0,8 à 0,8–0,9 ; pourtant le GBM sous-estime encore la variabilité d’environ 10 %, et les méthodes complexes les plus favorables à la RMSE ne sont pas les meilleures au CSI/PSS des pics ([Petetin et al., 2022](https://doi.org/10.5194/acp-22-11603-2022)).

Leur diagnostic va au-delà d’une interprétation : pour les maxima horaires supérieurs à 90 ppbv, le GBM a de faibles capacités de détection malgré ses bons scores continus. Pondérer les cas éloignés de la moyenne augmente à la fois les hits et les fausses alertes, améliore légèrement CSI/PSS, mais détériore RMSE et corrélation ; l’article ne donne pas dans le texte une amélioration numérique unique transférable à votre cas ([Petetin et al., 2022, §3.4.5](https://acp.copernicus.org/articles/22/11603/2022/)).

**Limite de comparabilité.** Les corrections de Petetin sont locales, appliquées séparément à chaque station, avec historique croissant et stations connues ; ce n’est donc pas une validation station + période exclues. Le mécanisme est comparable, pas l’ampleur attendue dans votre double aveugle ([Petetin et al., 2022, §2.2–2.3](https://acp.copernicus.org/articles/22/11603/2022/)).

**Confirmation indépendante.** FAIRMODE a constaté sur cinq applications européennes que le critère continu F-MQO pouvait être satisfait alors que la plupart des applications ne battaient pas la persistance sur les métriques de dépassement à plus de la moitié des stations ; seule l’application régionale faisait régulièrement exception ([Vitali et al., 2023, §4.1](https://doi.org/10.5194/gmd-16-6029-2023)).

**Jugement pour votre cas.** L’hypothèse « la perte quadratique apprend le centre et comprime la queue » est crédible. Le fait que la compression soit *plus forte parce que la station est inconnue* reste toutefois une hypothèse locale à tester : aucune publication trouvée ne chiffre ce différentiel sous exclusion simultanée station × période.

### 1.2 Comment mesurer le rétrécissement ?

Il n’existe pas un indicateur unique obligatoire. Le paquet de diagnostic défendable est le suivant :

1. `SDR = sd(ŷ) / sd(y)` et, mieux, ce ratio par station et par mois ; `SDR < 1` signale une amplitude prédite trop faible. Petetin emploie une différence normalisée de dispersion et une pente modèle-observation pour rendre visible le lissage que RMSE masque ([Petetin et al., 2022, annexe E et §3.3](https://doi.org/10.5194/acp-22-11603-2022)).
2. Régression d’**amplitude** `ŷ = a + b y` : `b < 1` décrit directement la compression des prédictions relativement aux observations. Il faut la nommer ainsi, car la pente de calibration usuelle emploie souvent l’orientation inverse `y = a + b ŷ` ; les deux pentes ne sont pas réciproques dès qu’il y a du bruit ([Petetin et al., 2022](https://doi.org/10.5194/acp-22-11603-2022)).
3. Ratios des quantiles `Q90/Q95/Q99` prédits-observés et biais conditionnel par classes d’**observation**. Ces diagnostics sont descriptifs : sélectionner ensuite le modèle sur le seul sous-échantillon observé extrême crée le *forecaster’s dilemma* ([Lerch et al., 2017, DOI 10.1214/16-STS588](https://doi.org/10.1214/16-STS588)).
4. Pour une probabilité de dépassement, diagramme de fiabilité `P(Y>s | p dans le bin)` avec effectifs et intervalles, plus décomposition calibration–discrimination–incertitude. La calibration conditionnelle et sa décomposition isotone sont formalisées par Gneiting et Resin ([2023, DOI 10.1214/23-EJS2180](https://doi.org/10.1214/23-EJS2180)).

**Test décisif.** Produire ces quatre diagnostics sur les mêmes OOF double aveugle pour CAMS, régression et classification, puis les répéter sur les stations vues. L’interaction `modèle × station_inconnue` sur SDR, pente et ratios de quantiles testera directement votre mécanisme.

### 1.3 Quelles corrections préservent la queue ?

| Famille | Ce qu’elle garantit réellement | Preuve utile et limite |
|---|---|---|
| Perte pinball / régression quantile | Cible un quantile conditionnel, pas la moyenne ; permet `P(Y>s)` à partir d’une distribution de quantiles. | Pour les épisodes NO₂ à Madrid, la régression quantile a surpassé les prévisions ponctuelles et fourni des distributions jugées fiables et précises ; l’article accessible ne fournit toutefois pas un gain POD/CSI directement comparable au vôtre ([Aznarte, 2017, DOI 10.1016/j.envpol.2017.05.079](https://doi.org/10.1016/j.envpol.2017.05.079)). |
| Quantiles non croisés | Empêche `q0.95 < q0.90`, donc rend la CDF exploitable. | Cannon le démontre pour des extrêmes de précipitation ; ce n’est pas une preuve de gain en qualité de l’air ([2018, DOI 10.1007/s00477-018-1573-6](https://doi.org/10.1007/s00477-018-1573-6)). |
| EMOS / NGR | Calibre une loi prédictive, sa position et sa dispersion ; permet une probabilité de seuil. | Référence fondatrice sur ensembles météo : Gneiting et al. ([2005, DOI 10.1175/MWR2904.1](https://doi.org/10.1175/MWR2904.1)). Aucun résultat trouvé ne démontre un gain au seuil O₃ français sur stations et périodes exclues. |
| Pondération de queue | Force le modèle à consacrer de la capacité aux cas rares. | Chez Petetin, CSI/PSS progressent légèrement, mais RMSE/PCC se dégradent raisonnablement ; pas de chiffre textuel unique et pas de station exclue ([Petetin et al., 2022, §3.4.5](https://acp.copernicus.org/articles/22/11603/2022/)). |
| Classification directe | Optimise la discrimination du dépassement plutôt que l’erreur de concentration. | Sur CAMS Europe J+1, test 2019 mais stations présentes à l’apprentissage, le meilleur MOS O₃ journalier atteint CSI 0,34 contre 0,22 pour la persistance au seuil 180 µg/m³ ; cette étude ne prouve pas la généralisation à une station nouvelle ([Bertrand et al., 2023, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)). |
| Isotone conditionnelle | Peut corriger la calibration d’un score déjà discriminant. | Elle ne crée pas de rang utile si les extrêmes ont déjà été comprimés ensemble ; sa valeur doit être mesurée par Brier/reliability, pas par le seul déplacement du seuil ([Gneiting et Resin, 2023](https://doi.org/10.1214/23-EJS2180)). |
| Inflation de variance | Élargit une distribution prédictive trop étroite. | C’est une correction probabiliste plausible, mais je n’ai trouvé **rien de probant** donnant simultanément un gain de détection O₃/PM et une RMSE déterministe non dégradée sous un protocole comparable au vôtre. |

**Réponse stricte à « sans perdre en RMSE, et de combien ? » : rien de probant dans un protocole station + période exclues.** Ce n’est pas surprenant : la perte quadratique cible l’espérance conditionnelle, tandis que pinball, Brier ou une perte pondérée ciblent d’autres fonctionnelles ([Gneiting, 2011, DOI 10.1198/jasa.2011.r10138](https://doi.org/10.1198/jasa.2011.r10138)). Une méthode peut conserver une RMSE proche, mais ce n’est pas une propriété garantie.

### 1.4 Existe-t-il une frontière centre–queue ?

**Oui comme pratique d’évaluation, non comme courbe réglementaire universelle.** Les scores pondérés propres — quantile-weighted CRPS, threshold-weighted CRPS, Brier par seuil — permettent de choisir explicitement la région de la distribution valorisée sans évaluer seulement les jours devenus extrêmes ([Gneiting et Ranjan, 2011, DOI 10.1198/jbes.2010.08110](https://doi.org/10.1198/jbes.2010.08110)).

Les diagrammes de Murphy comparent deux prévisions pour toute une famille de pertes cohérentes ; une courbe partout meilleure établit une dominance, sinon elle montre où le classement s’inverse ([Ehm et al., 2016, DOI 10.1111/rssb.12154](https://doi.org/10.1111/rssb.12154)). En apprentissage, une grille `Lλ = (1−λ) MSE + λ Lqueue`, évaluée une seule fois hors pli, produit une **frontière empirique de Pareto** `RMSE ↔ Brier/CSI/twCRPS`. C’est mon extrapolation méthodologique, pas un standard AASQA.

---

## 2. Évaluer sous blocage conjoint station × période

### 2.1 Pooling ou moyenne des plis ?

**Réponse.** Pour votre question principale — performance sur une occurrence station-jour future tirée de la population cible — agrégez toutes les prédictions OOF, construisez **une table de contingence micro-agrégée**, puis calculez POD, FAR, CSI, Brier et PR. Le référentiel français procède lui aussi par cumul des occurrences pour les seuils, plutôt que par moyenne de ratios de plis ([LCSQA, RTN « Évaluation des prévisions », applicable au 01/01/2022](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).

Publiez en sensibilité la distribution par pli et une moyenne macro **pondérée par le nombre de positifs** pour le POD. Une moyenne non pondérée répond à une autre question — « mois typique » — et donne le même poids à un pli contenant un dépassement et à un pli en contenant vingt. Le choix doit donc être fixé par l’unité de décision, pas par le résultat le plus favorable.

Pour éviter une autre fuite, le seuil, les poids de classe et la calibration doivent être choisis uniquement dans les plis internes ; le pli externe ne sert qu’une fois. Toutes les variantes comparées après lecture du double aveugle font partie de la sélection et doivent être comptées.

### 2.2 Plis sans positif

Le rappel d’un pli sans positif est **indéfini (`NA`)**, ni zéro ni un. Ses négatifs restent néanmoins utiles pour compter les fausses alertes, le taux de faux positifs, le Brier et la table cumulée. Il ne faut donc ni supprimer le pli du jeu OOF, ni inventer un POD local.

Dans le rapport, donner `(nombre de plis avec ≥1 positif) / (nombre total de plis)`, les positifs par pli, et la concentration des événements par mois. Si l’estimand est la capacité à avertir un épisode régional, fusionner aussi les jours consécutifs/spatialement liés selon une règle préspécifiée ; le LCSQA distingue déjà les occurrences en station de l’évaluation spatiale AMU ([LCSQA, RTN 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).

### 2.3 Quelles métriques résistent au taux de base ?

| Mesure | Usage honnête | Point faible |
|---|---|---|
| POD / rappel | Coût des manqués ; toujours avec TP et FN. | Un modèle annonçant tout atteint 1. |
| FAR au sens AASQA `FP/(TP+FP)` et SR `1−FAR` | Charge de fausses alertes parmi les alertes. | Dépendent fortement de la prévalence. Ne pas confondre avec `FPR=FP/(FP+TN)`. |
| CSI `TP/(TP+FP+FN)` | Résumé événementiel sans vrais négatifs ; standard dans PREV’AIR. | Dépend du taux de base et ne représente pas un coût utilisateur ([Schaefer, 1990, DOI 10.1175/1520-0434(1990)005%3C0570:TCSIAA%3E2.0.CO;2](https://doi.org/10.1175/1520-0434(1990)005%3C0570:TCSIAA%3E2.0.CO;2)). |
| Peirce/TSS `POD−FPR` | Sépare discrimination et prévalence dans la population théorique. | Avec très peu de positifs, sa variance reste dominée par le POD. |
| PR-AUC / Average precision | Informative quand la classe positive est rare ; montre le front précision–rappel. | Sa ligne de base est la prévalence : deux AUC-PR de taux de base différents ne se comparent pas directement ([Saito et Rehmsmeier, 2015, DOI 10.1371/journal.pone.0118432](https://doi.org/10.1371/journal.pone.0118432)). |
| PR-Gain | Transforme précision et rappel en gains par rapport au hasard ; la référence devient 0. | À publier avec la prévalence et la courbe originale ([Flach et Kull, 2015, NeurIPS](https://papers.nips.cc/paper/2015/hash/33e8075e9970de0cfea955afd4644bb2-Abstract.html)). |
| Brier + décomposition | Évalue des probabilités : fiabilité, résolution, incertitude ; Brier Skill relatif à une climatologie OOF. | Un score global peut être dominé par les nombreux non-événements ([Murphy, 1973, DOI 10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2)). |

**Normalisation conseillée.** À côté de l’AP brute, donner la prévalence `π` et `AP-skill = (AP−π)/(1−π)` comme transformation descriptive, puis AUPRG. Ce `AP-skill` est une dérivation simple, pas une norme FAIRMODE ou LCSQA ; pour comparer des périodes de prévalence différente, le mieux reste une évaluation appariée sur exactement les mêmes cas.

### 2.4 Intervalle de confiance avec une trentaine d’événements

Avec 30 positifs indépendants et un POD voisin de 0,5, l’intervalle de Wilson à 95 % a déjà une demi-largeur d’environ 0,17 ; la dépendance spatiale et temporelle l’élargit. Pour votre résultat `3/32`, l’IC de Wilson binomial est approximativement **[0,032 ; 0,242]**, avant toute correction de dépendance ([Wilson, 1927, DOI 10.1080/01621459.1927.10502953](https://doi.org/10.1080/01621459.1927.10502953)).

Le bootstrap principal doit conserver l’unité qui crée la dépendance : resampler des **épisodes/jours régionaux** si la décision porte sur l’épisode, puis resampler les stations à l’intérieur ou appliquer un bootstrap multiway station × bloc temporel. Les méthodes de bootstrap pour données à grappes et de dépendance multiway sont documentées par Field et Welsh ([2007, DOI 10.1111/j.1467-9868.2007.00593.x](https://doi.org/10.1111/j.1467-9868.2007.00593.x)) et Davezies et al. ([2021, DOI 10.3982/ECTA15383](https://doi.org/10.3982/ECTA15383)).

Avec seulement 32 occurrences, rapporter aussi un intervalle exact/score sur TP sur N, la table brute et la fraction de réplications sans positif. Si les événements régionaux uniques sont beaucoup moins de 32, l’intervalle événementiel — probablement très large — est le résultat honnête.

---

## 3. Ce que vérifient réellement PREV’AIR, les AASQA, CAMS et FAIRMODE

### 3.1 France : protocole et valeurs publiées

Le RTN LCSQA applicable depuis le 1er janvier 2022 demande un bilan annuel, au moins 75 % de couples modèle-observation disponibles, des scores continus par station puis synthétisés, et des tables de contingence avec POD, FAR, SR, biais de fréquence et CSI. Il évalue notamment l’O₃ en maximum horaire journalier d’avril à septembre à 180 µg/m³ et les PM10 en moyenne journalière annuelle à 50 µg/m³, pour J0 et J1 ([LCSQA, RTN 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).

Le rapport PREV’AIR 2023 évalue O₃, NO₂, PM10 et PM2,5 de J0 à J+3 contre GEOD’air. À J0, France métropolitaine, PM10 > 50 µg/m³, il compte 393 occurrences observées : MOCAGE obtient 52 TP et 253 FP (`POD=13 %`, `SR=17 %`), CHIMERE 120 TP et 574 FP (`POD=31 %`, `SR=17 %`), et l’adaptation statistique CHIMERE 131 TP et 131 FP (`POD=33 %`, `SR=50 %`) ([LCSQA/INERIS, *Performances PREV’AIR en 2023*, pp. 31–33](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf)).

Pour O₃ > 180 µg/m³, le même rapport ne compte que 45 occurrences sur 28 jours en 2023, à J0 ; il conclut que l’adaptation statistique fait à peine plus de détections que le brut, ajoute des fausses alertes et que l’année est trop modérée pour conclure ([LCSQA/INERIS, 2024, pp. 21–23](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf)). Ces résultats sont des occurrences station-jour sur stations de fond connues, pas une généralisation à de nouvelles stations.

Le dernier bilan public trouvé, celui de 2024 publié le 8 avril 2026, annonce que 85 % des objectifs sont satisfaits sur 13 plateformes métropolitaines et 5 ultramarines, 97 % en excluant l’outre-mer ; ce pourcentage agrège des objectifs et ne constitue pas un POD d’épisode ([LCSQA/INERIS, *Performances PREV’AIR en 2024*](https://www.lcsqa.org/fr/rapport/performances-prevair-en-2024)).

### 3.2 CAMS Europe

CAMS vérifie quotidiennement biais, RMSE, erreur fractionnelle et corrélation contre les stations, et publie des rapports trimestriels d’EQC ; le service régional décrit ces évaluations comme un contrôle des prévisions à partir des observations disponibles ([CAMS, *Regional services*](https://atmosphere.copernicus.eu/regional-services)).

Le rapport EQC du premier trimestre 2026 fixe, pour la prévision régionale, des cibles de RMSE de 18 µg/m³ pour le maximum quotidien O₃, 25 pour le maximum quotidien NO₂, et 18 pour les moyennes quotidiennes PM10 et PM2,5 ; ces cibles continues ne sont pas des seuils POD/FAR ([CAMS, *2026 Q1 Ensemble EQC report*](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/DJF-2026/CAMS283bis_2024SC1_D83bis.1.3.1-2026Q1_202604_ENSEMBLE_EQC_report_v1.pdf)). Pour une comparaison à votre système, il faut extraire dans ce rapport le même trimestre, horizon, polluant et agrégat ; une cible contractuelle n’est pas une performance atteinte.

### 3.3 FAIRMODE pour la prévision

La référence actuelle est la **Guidance WG3 Forecast, version 2026**, publiée le 30 avril 2026. Le groupe vise explicitement le benchmark contre la persistance et la capacité à anticiper les dépassements réglementaires ([FAIRMODE WG3, 2026](https://knowledge4policy.ec.europa.eu/file/fairmode-guidance-wg3-forecast-version-2026_en)).

Dans la formulation publiée et reproductible, `MQI_f` compare la RMSE de la prévision à celle d’une persistance dépendant de l’horizon et intégrant l’incertitude de mesure. Le F-MQO est satisfait à une station si `MQI_f ≤ 1`, et une application passe le benchmark si au moins 90 % des stations satisfont cette condition ; FAIRMODE précise que c’est nécessaire, non suffisant ([Vitali et al., 2023, §2.1 et §4.1](https://doi.org/10.5194/gmd-16-6029-2023)).

La courbe d’incertitude utilisée dans cette publication est

`U(O) = Ur(RV) × sqrt((1−α²) O² + α² RV²)`.

Les paramètres publiés en 2023 sont : NO₂ `(Ur=0,24; RV=200; α=0,20)`, O₃ `(0,18; 120; 0,79)`, PM10 `(0,28; 50; 0,25)` et PM2,5 `(0,36; 25; 0,50)` ; l’implémentation retient le 95e percentile des incertitudes instrumentales ([Vitali et al., 2023, annexe A et table A1](https://gmd.copernicus.org/articles/16/6029/2023/gmd-16-6029-2023.html)). **À vérifier dans le PDF 2026/Delta Tool avant calcul**, car FAIRMODE travaillait encore en 2025 sur l’évolution des paramètres d’incertitude ([FAIRMODE, compte rendu technique 2025](https://knowledge4policy.ec.europa.eu/sites/default/files/20251008_FAIRMODE_TM_Malta_Minutes_CLEAN_0.pdf)).

Le `MQI = RMSE/(β RMS_U)` avec `β=2` est le MQI d’**évaluation/assessment**, pas le F-MQI principal de prévision ; les confondre produirait un résultat faux ([Vitali et al., 2023, annexe C](https://doi.org/10.5194/gmd-16-6029-2023)). Le target plot représente le biais et l’erreur centrée, avec la distance à l’origine égale au MQI pertinent ; les MPI comparent en plus l’erreur fractionnelle à la persistance et à l’incertitude ([Vitali et al., 2023, §2.1](https://doi.org/10.5194/gmd-16-6029-2023)).

### 3.4 Scores de détection comparables et « acceptable »

La meilleure comparaison scientifique accessible est Bertrand et al. : CAMS Europe, J+1, test 2019, stations déjà représentées à l’apprentissage. Au seuil O₃ maximum horaire journalier de 180 µg/m³, les MOS journaliers atteignent `CSI=0,30–0,40`, le meilleur GBM global `0,34`, contre `0,22` pour la persistance ; pour PM10 moyenne journalière > 50 µg/m³, `POD=0,42–0,51`, `SR=0,59–0,68`, `CSI=0,35–0,40` ([Bertrand et al., 2023, §5.3](https://doi.org/10.5194/acp-23-5317-2023)).

Ces nombres ne sont **pas** un objectif contractuel et ne sont pas comparables à votre double aveugle. Le rapport PREV’AIR 2023 est plus opérationnel mais porte sur J0, pas J+1 ; il faut donc recalculer ou extraire J1 avant de placer vos résultats à côté ([LCSQA/INERIS, 2024](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf)).

**Rien de probant pour un seuil universel acceptable.** FAIRMODE écrivait en 2023 que le critère « good enough » des indicateurs de dépassement n’était pas fixé ; le compte rendu 2025 confirme que le MQI_f est important mais insuffisant et que les critères de dépassement restent prioritaires ([Vitali et al., 2023, §4](https://doi.org/10.5194/gmd-16-6029-2023) ; [FAIRMODE, 2025](https://knowledge4policy.ec.europa.eu/sites/default/files/20251008_FAIRMODE_TM_Malta_Minutes_CLEAN_0.pdf)).

Je n’ai trouvé aucune doctrine publique française disant « une procédure préfectorale est acceptable à partir de POD=x ou FAR=y ». L’arrêté impose les seuils, la surface/population/persistance et l’information quotidienne des autorités ; il ne prescrit pas un score minimal du modèle ([arrêté du 7 avril 2016, art. 2 et 7](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376954)). La décision combine produits, expertise et traçabilité ; la valeur numérique d’un arbitrage interne propre à ATMO Occitanie est **à vérifier auprès de l’AASQA**.

---

## 4. Évaluer la décision par le coût–perte

### 4.1 Formulation exacte

Dans le modèle binaire simple, agir coûte `C`, ne pas agir lorsqu’un événement survient entraîne une perte `L`, et une prévision probabiliste calibrée déclenche l’action si `q > C/L`. Pour des fréquences normalisées de hits `h`, fausses alertes `f` et manqués `m`, la dépense prévue est

`Eforecast = C(h+f) + Lm`.

Avec une fréquence climatologique d’événement `p`, `Eclim = min(C, pL)`, `Eperfect = pC`, puis la valeur économique relative est

`V = (Eclim − Eforecast) / (Eclim − Eperfect)`.

Cette formulation et la comparaison des utilisateurs selon `C/L` viennent du modèle coût–perte de Murphy ([1977, DOI 10.1175/1520-0493(1977)105%3C0803:TVOCCA%3E2.0.CO;2](https://doi.org/10.1175/1520-0493(1977)105%3C0803:TVOCCA%3E2.0.CO;2)) et de sa présentation opérationnelle par Richardson ([2000, DOI 10.1002/qj.49712656313](https://doi.org/10.1002/qj.49712656313)). `V>0` signifie mieux que la meilleure stratégie climatologique pour ce rapport de coût ; `V=1` égale l’information parfaite.

### 4.2 Application à l’air et choix de C/L

Le cadre a bien été appliqué à l’ozone. Pagowski et Grell utilisent sept modèles sur l’est des États-Unis et le sud du Canada, été 2004, plus de 350 sites, maxima 1 h et MDA8, seuils 50/70/85 ppbv ; l’ensemble probabiliste a généralement une valeur supérieure aux déterministes, mais la calibration aide surtout l’événement fréquent à 50 ppbv et peut perdre de la valeur aux seuils plus hauts ([Pagowski et Grell, 2006, DOI 10.1029/2006JD007124](https://doi.org/10.1029/2006JD007124)). C’est une validation de la méthode, pas un `C/L` français.

**Rien de probant pour un rapport C/L unique « restriction de circulation / santé » applicable à une AASQA.** Le coût d’une action dépend de sa nature, de sa durée et des acteurs ; la perte sanitaire dépend de la population, de l’exposition, du polluant et de la réponse réellement obtenue. Transformer ces composantes en un seul nombre exige un commanditaire et une décision précisément définie, pas seulement une table de contingence.

La présentation défendable est donc une courbe pour `C/L ∈ (0,1)`, en marquant les intervalles où chaque système a `V>0` et où il domine les références, sans baptiser une valeur « réaliste » sans étude de coûts française.

### 4.3 Valeur et fatigue des alertes

Des effets comportementaux et sanitaires sont mesurés, mais ils ne donnent pas directement le coût d’une fausse procédure préfectorale. À Sydney, une alerte a réduit le vélo de 14 % en OLS à 35 % en variable instrumentale ; lors d’un second jour consécutif, la réponse estimée tombe à 2 % et n’est plus significative, résultat compatible avec une fatigue d’alerte mais fondé sur un sous-échantillon plus petit ([Saberian et Heyes, 2017, DOI 10.1016/j.reseneeco.2017.05.004](https://doi.org/10.1016/j.reseneeco.2017.05.004)).

En Angleterre, une étude de panel estime qu’un avertissement réduit de 8 % les admissions d’urgence pour asthme des enfants, toutes choses observées égales dans son modèle ([Janke, 2014, DOI 10.1016/j.jhealeco.2014.07.002](https://doi.org/10.1016/j.jhealeco.2014.07.002)). À Toronto, une analyse en discontinuité de régression a évalué l’effet sanitaire des alertes, mais son contexte et sa règle de déclenchement ne sont pas directement transposables à l’Occitanie ([Chen et al., 2018, DOI 10.1016/S2542-5196(17)30185-7](https://doi.org/10.1016/S2542-5196(17)30185-7)).

**Rien de probant** n’a été trouvé quantifiant causalement, pour les alertes françaises de pollution, la perte de confiance produite par *une fausse alerte supplémentaire*. Le résultat de Sydney concerne surtout la répétition des alertes, pas leur fausseté vérifiée ; il ne faut pas convertir son 2 % en coût d’un faux positif.

### 4.4 Une dominance sur un intervalle est-elle défendable ?

Oui : c’est exactement l’intérêt de la courbe de valeur. Dire « A domine B pour `C/L ∈ [a,b]`, sur cet échantillon et avec cet intervalle de confiance » est plus informatif que d’imposer un seul seuil. Pagowski et Grell montrent d’ailleurs que l’ordre des systèmes varie avec `C/L` et avec le seuil d’ozone ([2006](https://doi.org/10.1029/2006JD007124)).

Ce serait un habillage seulement si l’intervalle était choisi après lecture du test, si aucun utilisateur plausible ne lui correspondait, ou si l’incertitude n’était pas montrée. Dans votre dossier : publier toute la courbe, le support des événements, la référence climatologique, les bandes bootstrap appariées et les zones préspécifiées ; ne pas résumer par l’aire sous la courbe sans justification décisionnelle.

---

## 5. Le seuil réglementaire O₃ à 180 µg/m³

### 5.1 Que peut-on apprendre avec 32 dépassements ?

`3/32` donne un POD ponctuel de 0,094 et un IC95 binomial optimiste d’environ `[0,032 ; 0,242]`. Avec la dépendance d’un même épisode entre stations, l’information effective est inférieure à 32 ; le nombre d’épisodes régionaux uniques doit être publié à côté du nombre d’occurrences station-jour ([Wilson, 1927](https://doi.org/10.1080/01621459.1927.10502953) ; [LCSQA, RTN 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).

Les options praticables sont :

- entraîner une probabilité de plusieurs seuils emboîtés `120/130/150/170/180`, avec contrainte monotone, pour mutualiser le signal ; la validité finale reste jugée à 180 ;
- entraîner des quantiles élevés puis convertir la CDF en `P(Y>180)` ; empêcher le croisement des quantiles ([Cannon, 2018](https://doi.org/10.1007/s00477-018-1573-6)) ;
- pondérer les fortes concentrations dans un pli interne, comme Petetin, mais sélectionner sur Brier/twCRPS et non sur le POD seul ([Petetin et al., 2022](https://doi.org/10.5194/acp-22-11603-2022)) ;
- classifier directement, puis recalibrer sur des prédictions internes hors pli ; Bertrand montre l’intérêt possible au seuil 180, mais seulement avec stations vues ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)).

L’apprentissage à un seuil plus bas n’autorise pas à annoncer une performance à 180 : c’est un transfert/extrapolation à valider sur les 32 cas laissés totalement hors sélection. Le sur-échantillonnage ou les poids de classe modifient la distribution d’apprentissage ; les probabilités doivent donc être recalibrées sur une prévalence naturelle OOF.

### 5.2 Théorie des valeurs extrêmes

L’EVT/POT est établie pour décrire les queues de pollution : Eastoe et Tawn ajustent des extrêmes non stationnaires d’ozone de surface ([2009, DOI 10.1111/j.1467-9876.2008.00638.x](https://doi.org/10.1111/j.1467-9876.2008.00638.x)), et Küchenhoff et Thamerus modélisent maxima, dépassements et grappes pour O₃/NO₂ à deux sites de Munich ([1996, DOI 10.1007/BF02427858](https://doi.org/10.1007/BF02427858)). Ces travaux portent sur l’inférence de queue/retour, pas sur un système opérationnel J+1 évalué par POD/FAR/CSI.

**Réponse stricte : rien de probant trouvé pour un système opérationnel de qualité de l’air où l’EVT améliore, avec chiffre publié, la détection J+1 au seuil réglementaire par rapport au CTM brut.** Avec 36 mois et 32 occurrences, ajouter une GPD covariable riche risque surtout d’augmenter la variance. L’EVT est une analyse secondaire raisonnable, pas le premier test de 48 h.

### 5.3 Remplacer un seuil par un rang

Un rang ou un budget `top-N` est légitime pour une décision à capacité fixe — par exemple choisir N journées à examiner — et mesure alors `precision@N`, `recall@N` ou la valeur au budget. C’est une **couche de triage**, pas une prévision réglementaire de dépassement.

Il ne remplace pas le seuil français de 180 µg/m³ horaire, ni les critères de surface, population et persistance prévus pour la procédure ([Code de l’environnement, art. R.221-1](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000022964539) ; [arrêté du 7 avril 2016](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376954)). La formulation honnête est : « le score priorise l’expertise ; la décision réglementaire reste calculée en concentration et selon l’AMU ».

### 5.4 Existe-t-il une preuve qu’aucune méthode ne bat le brut ?

**Non : rien de probant sous forme de résultat d’impossibilité.** Bertrand montre au contraire que certains MOS améliorent le CSI à 180 µg/m³ sur stations vues ; Petetin montre que le meilleur modèle en RMSE peut rester médiocre aux plus hauts seuils et que les gains de pondération sont faibles ; FAIRMODE montre que battre la persistance sur les dépassements reste difficile même lorsque le critère continu est satisfait ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023) ; [Petetin et al., 2022](https://doi.org/10.5194/acp-22-11603-2022) ; [Vitali et al., 2023](https://doi.org/10.5194/gmd-16-6029-2023)).

La conclusion défendable pour votre corpus est plus étroite : **avec 32 occurrences et 3 hits, le projet ne démontre pas aujourd’hui une amélioration au seuil réglementaire O₃**. Ce constat ne prouve ni que CAMS est imbattable, ni que le classement observé sera stable.

---

## Plan exécutable en 48 heures, sans nouvelle donnée

| Priorité | Expérience | Sortie minimale | Décision |
|---:|---|---|---|
| 1 | Rejouer sur les mêmes OOF double aveugle CAMS, régresseur seuillé et classifieur ; mêmes lignes, même cible, même horizon. Choisir calibration et seuil dans le pli interne. | TP/FP/FN/TN, POD/FAR/SR/CSI, AP/AUPRG, Brier/BSS aux seuils 120/130/150/170/180 ; courbes PR appariées. | Si le `0,85×` disparaît, le renversement venait du protocole/détecteur ; sinon il devient un fait robuste à expliquer. |
| 2 | Diagnostiquer le rétrécissement OOF. | `sd(ŷ)/sd(y)`, pente `ŷ~y`, pente `y~ŷ`, biais et ratio Q90/Q95/Q99, par stations vues/inconnues et mois vus/inconnus. | Une interaction nette avec station inconnue soutient votre hypothèse ; sinon retirer cette causalité du récit. |
| 3 | Évaluer des **probabilités**, pas seulement un seuil. | Fiabilité avec effectifs, Brier décomposé, BSS contre climatologie OOF, twCRPS/quantile loss ; IC multiway. | Une calibration meilleure sans gain d’AP signifie calibration seulement, pas meilleure détection. |
| 4 | Petite grille de pertes : MSE, poids de queue modéré, LightGBM quantiles `0,50/0,80/0,90/0,95/0,98`, classifieur direct. | Front de Pareto `RMSE globale ↔ Brier/CSI/twCRPS`, évalué une fois dans le pli externe. | Retenir un modèle de queue seulement si le gain externe dépasse l’incertitude et ne dépend pas d’un seul mois. |
| 5 | Deux unités d’analyse. | Occurrences station-jour **et** épisodes régionaux uniques selon une règle figée ; bootstrap épisode + sensibilité station × blocs 7/14 jours. | Si l’avantage n’existe qu’en station-jour, le présenter comme localisation, pas comme meilleure détection d’épisodes. |
| 6 | Courbe coût–perte complète, sans choisir un C/L a posteriori. | `V(C/L)` de CAMS, produit officiel et modèles, avec bandes appariées ; indiquer prévalence et horizon. | Revendiquer seulement les intervalles de dominance dont l’IC reste positif. |
| 7 | Calcul strictement comparable AASQA. | O₃ maximum horaire >180, avril–septembre, stations de fond, J+1 ; PM10 moyenne jour >50 si disponible. | Ne plus utiliser le résultat MDA8 120 pour parler de procédure réglementaire. |

### Phrase de synthèse pour l’entretien

> « Notre correction améliore nettement l’erreur moyenne, mais nous ne revendiquons pas encore un meilleur déclenchement réglementaire : à 180 µg/m³, nous n’avons que 3 détections sur 32. La littérature CAMS et FAIRMODE documente exactement ce conflit entre score continu et dépassements. Nous le traitons par une évaluation OOF identique des détecteurs, des diagnostics de compression de variance, des probabilités calibrées et une frontière explicite RMSE–queue, avec le protocole LCSQA comme point d’arrivée. »
