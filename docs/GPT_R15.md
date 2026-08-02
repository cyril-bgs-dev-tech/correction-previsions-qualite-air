# GPT R15 — Élever la qualité du travail, pas le score

**Légende.** **Établi** désigne un point directement documenté par une source. **Pratique** désigne une méthode publiée ou un usage opérationnel, sans obligation générale. **Recommandation** désigne mon jugement pour ce projet. **À vérifier** signale une information absente de la source publique ou une ambiguïté qui interdit une affirmation plus forte.

## 1. Observations antérieures : légitimes, mais pour quel produit ?

### 1.1 Oui : c'est du MOS autorégressif, pas une fuite par nature

**Établi.** Utiliser uniquement des observations disponibles avant l'heure d'émission est une pratique standard de *model output statistics* (MOS). Les noms utiles sont :

| Variable | Nom défendable | Ce qu'elle suppose |
|---|---|---|
| `obs(t−k)` | observation retardée, terme autorégressif, persistance | continuité du niveau observé |
| `obs(t−k) − CAMS(t−k)` | erreur ou biais récent, correction adaptative du biais | persistance de l'erreur du CTM |
| moyenne glissante du résidu | *running-mean bias correction* | biais local lentement variable |
| écart-type glissant du résidu | volatilité récente de l'erreur | régime d'erreur local relativement durable |
| âge de la dernière mesure | fraîcheur/*staleness* | fiabilité décroissante avec l'ancienneté |
| sélection de jours passés semblables | méthode des analogues | similarité dans l'espace météo–chimie, pas simple proximité temporelle |

Le MOS CAMS opérationnel utilise explicitement les « mesures du jour précédent », avec CAMS, météo IFS et observations récentes ; il est réentraîné chaque jour sur une fenêtre de trois jours ([documentation CAMS-MOS, mise à jour 2025](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation)). Bertrand et al. incluent également les observations de la veille dans leur jeu de prédicteurs ; leur correction dite « unbiased concentration » retranche le biais moyen récent du modèle ([Bertrand et al., 2023, *Atmospheric Chemistry and Physics*, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)). Petetin et al. distinguent persistance, moyenne mobile du biais, Kalman, analogues et GBM : ces termes ne sont donc pas synonymes ([Petetin et al., 2022, *ACP*, DOI 10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022)).

**Conclusion.** Cette famille de variables est légitime. La fuite apparaît si la jointure se fait sur la date de validité plutôt que sur l'heure réelle de disponibilité, si une valeur révisée ultérieurement remplace silencieusement la valeur disponible à l'émission, ou si une statistique glissante inclut le jour cible.

### 1.2 J−2 est cohérent pour une cible J+1 quotidienne

Notons `D` le jour d'émission et `T=D+1` le jour prévu. Une journée observée complète immédiatement antérieure à `D` est `D−1=T−2` : c'est donc bien **J−2 par rapport à la cible**. FAIRMODE formalise exactement ce décalage : pour l'horizon `FH=1`, la persistance du jour `i` utilise `O[i−2]` ; pour `FH=0`, elle utilise `O[i−1]` ([Vitali et al., 2026, *FAIRMODE Guidance WG3 Forecast*, équation 2, JRC146007](https://knowledge4policy.ec.europa.eu/file/fairmode-guidance-wg3-forecast-version-2026_en)).

Le système CAMS-MOS tourne à **06:30 UTC**, utilise les mesures de la veille et livre son produit avant 08:00 UTC ; cela établit qu'un système européen exploite opérationnellement le jour précédent, mais pas que ses données soient définitivement validées à cette heure ([documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation)). Les données EEA *up-to-date* sont expressément provisoires et peuvent n'être validées formellement que bien plus tard ; les réanalyses CAMS distinguent ce flux de la série validée ([documentation CAMS des réanalyses régionales, 2026](https://confluence.ecmwf.int/spaces/CKB/pages/228864840/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Breanalyses%2Bdata%2Bdocumentation)).

**À vérifier auprès d'Atmo Occitanie :** heure exacte de production quotidienne, statut des mesures accessibles à cette heure (`brute`, `contrôlée`, `validée`), politique de révision et délai par polluant. Aucune source publique trouvée ne fixe une heure universelle de validation pour toutes les AASQA.

**Recommandation.** Conserver J−2 pour le produit quotidien J+1 du dossier. Ajouter dans chaque ligne `forecast_issued_at`, `observation_available_at`, `observation_status` et `source_revision`. Un futur essai avec des heures de J−1 ne sera légitime que si un instantané historique prouve qu'elles étaient effectivement disponibles au *cut-off*.

### 1.3 Ce que le bon score ne révèle pas

Les risques opérationnels sont réels :

- le CAMS-MOS ne produit pas de valeur corrigée lorsque les observations récentes nécessaires manquent ; sa documentation avertit explicitement de ces trous ([documentation CAMS-MOS, rubrique *Guidelines*](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation)) ;
- la persistance réagit avec retard aux débuts et fins d'épisodes ; Bertrand et al. montrent que son biais de fréquence est mécaniquement proche de 1 parce qu'elle décale les dépassements, et que son score dépend de la durée des épisodes ([Bertrand et al., 2023, §5.3](https://doi.org/10.5194/acp-23-5317-2023)) ;
- une panne n'est pas forcément aléatoire : maintenance, saturation, invalidation ou communication peuvent être liées au site, à la saison ou à un épisode ; une validation faite seulement sur les lignes complètes mesure alors le meilleur cas ;
- déplacement de station, changement d'instrument ou révision de données peut créer une fausse « mémoire » locale ; CAMS conserve d'ailleurs des dates de début et de fin par position de station dans les métadonnées de son MOS ([documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation)).

**Recommandation d'évaluation.** Ajouter, sans réentraîner sur le test :

1. des pannes simulées par **blocs** de 1, 3, 7 et 14 jours, pas par cellules indépendantes ;
2. des résultats par âge de mesure `2`, `3–4`, `5–7`, `>7 jours` ;
3. une analyse spécifique des commencements et fins d'épisodes ;
4. le taux de disponibilité du produit et pas seulement son RMSE quand il répond ;
5. un test après déplacement/changement de station, si les métadonnées le permettent.

### 1.4 Deux usages, donc deux estimands

Le pli « station cachée + mois caché » avec l'observation passée de la station test évalue un modèle transféré à **une station instrumentée dont on connaît le passé**, pas une prédiction sur un lieu sans capteur. Ce protocole est exigeant sur l'apprentissage spatial des paramètres, mais il ne rend pas la station inconnue au sens informationnel.

**Recommandation.** Publier un seul service avec trois modes de dégradation, mais deux résultats scientifiques distincts :

| Mode | Entrées | Population d'usage | Résultat à publier |
|---|---|---|---|
| `FULL` | CAMS + terrain + passé de la station | station instrumentée et flux frais | score principal « stations instrumentées » |
| `NO_LOCAL_OBS` | CAMS + terrain, sans passé local | nouvelle station ou panne | score « station réellement inconnue » |
| `RAW_FALLBACK` | CAMS seul | rupture du pipeline | disponibilité et score CAMS |

Le routage doit être déterministe, testé et journalisé. Afficher seulement `FULL` ferait croire à une capacité spatiale que le produit n'a pas ; afficher seulement `NO_LOCAL_OBS` cacherait un gain opérationnel parfaitement légitime aux stations.

### 1.5 Quelle part des +14 points est de la persistance ?

**Réponse franche : inconnue avec les résultats fournis.** Une ablation « sans/avec observations passées » donne l'apport du **bloc complet**, pas la part attribuable à la persistance simple, au biais récent ou à leurs interactions avec CAMS. Une importance LightGBM ou SHAP ne réalise pas cette décomposition causale lorsque les variables sont corrélées.

Sur données européennes, les observations de la veille font partie du jeu minimal performant ; la littérature confirme donc que le levier peut être grand, sans fournir un pourcentage transférable à vos plis NO₂/PM10 ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)). Pour O₃ et PM10, leurs MOS battent la persistance, tandis que Petetin et al. montrent qu'un GBM peut gagner en RMSE tout en détectant moins bien que la persistance : il faut comparer les deux objectifs ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023) ; [Petetin et al., 2022](https://doi.org/10.5194/acp-22-11603-2022)).

Le test minimal sur **exactement les mêmes lignes OOF** est :

```text
P0  = O[t-2]                                             # persistance FAIRMODE J+1, centre
P1  = CAMS[t] + (O[t-2] - CAMS[t-2])                   # dernier résidu
P3  = CAMS[t] + mean(O-CAMS sur t-2 ... t-4)           # biais récent 3 valeurs
P7  = CAMS[t] + mean(O-CAMS sur t-2 ... t-8)           # biais récent 7 valeurs
ML0 = modèle sans observation passée
ML1 = modèle complet
```

Pour chacun : RMSE, `MQI_f`, POD/SR/CSI au seuil, début/fin d'épisode, disponibilité, différence appariée et intervalle bootstrap par station et bloc temporel. La phrase sûre avant ce test est : **« le bloc de mémoire locale apporte 14 points ; sa part au-delà d'une persistance ou d'une correction de biais élémentaire n'est pas encore isolée ».**

---

## 2. Reproduire exactement les protocoles LCSQA et FAIRMODE

### 2.1 Ce que demande le RTN LCSQA applicable depuis 2022

La source nationale est le **Référentiel technique national — Évaluation des prévisions de qualité de l'air**, version applicable au 1er janvier 2022, 13 pages ([LCSQA, 2022, PDF](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).

#### Périmètre et agrégation

| Élément | O₃ | PM10 |
|---|---|---|
| Grandeur continue | maximum journalier | moyenne journalière |
| Période | avril à septembre | année entière |
| Stations | fond urbain, périurbain et rural | fond urbain, périurbain et rural |
| Horizons | J0 et J1 séparément | J0 et J1 séparément |
| Produits | brut et corrigé ; la cartographie la plus avancée disponible au prévisionniste doit être identifiable | idem |
| Synthèses | station, type, région et zones régionales avec critère préfectoral | idem |

Pour chaque station `s`, le référentiel calcule d'abord le score temporel sur ses couples valides, puis fait la moyenne arithmétique des scores de stations retenues :

```text
score_zone = mean_s(score_s)
```

Il ne faut donc pas mettre toutes les lignes station-jour dans une seule RMSE nationale : cela surpondérerait les stations les plus complètes. Le RTN demande biais, RMSE et corrélation de Pearson. Les objectifs graphiques indiqués sont : O₃ `biais ∈ [−10,+10] µg/m³`, `RMSE ≤ 25 µg/m³`, `r ≥ 0,70` ; PM10 `biais ∈ [−7,5,+7,5] µg/m³`, `RMSE ≤ 15 µg/m³`, `r ≥ 0,60` ([LCSQA, 2022, figure 1 et §2.1](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)). Ce sont les repères du RTN, pas des preuves de supériorité entre deux modèles.

Le RTN demande aussi les scores par classes de concentration observée et indique la fraction d'observations de chaque classe ; il recommande une perspective glissante de cinq ans pour replacer l'année courante ([LCSQA, 2022, §2.1](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).

#### Règle des 75 %

Pour une station, un polluant, un horizon, un produit et une période d'évaluation donnés :

```python
calendrier = dates officielles de la période      # O3: avr-sept; PM10: année
valide = is_valid(obs) & is_valid(pred)
station_retenue = sum(valide) >= 0.75 * len(calendrier)
score = metric(obs[valide], pred[valide])
```

La règle porte donc sur les **couples observation–prévision**, par station et période évaluée ; le dénominateur est le calendrier attendu, pas le nombre de lignes restant après suppression des manquants ([LCSQA, 2022, §2.1 et logigrammes](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)). Pour comparer brut et corrigé, ajouter une analyse appariée sur leur intersection commune ; sinon un produit peut sembler meilleur uniquement parce qu'il manque les jours difficiles. Cette intersection appariée est une **recommandation de comparaison**, pas une phrase explicite du RTN.

#### Dépassements

Le RTN utilise strictement :

- O₃ : maximum horaire journalier `> 180 µg/m³`, avril–septembre ;
- PM10 : moyenne journalière `> 50 µg/m³`, année entière ;
- J0 et J1 séparés ; toutes les stations de fond retenues.

Avec `a=TP`, `b=FP`, `c=FN`, `d=TN` :

```text
POD   = a / (a+c)
FAR   = b / (a+b)
SR    = a / (a+b) = 1-FAR
FBias = (a+b) / (a+c)
CSI   = a / (a+b+c)
```

Le tableau et le diagramme de performance regroupent les occurrences station-jour ; le RTN ne moyenne pas un CSI par station. Sa légende française de FAR contient une formulation éditoriale ambiguë, mais la formule `b/(a+b)` et la définition « fausses détections parmi les détections » ne le sont pas ([LCSQA, 2022, §2.2](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)). Toujours publier `a,b,c,d` afin d'empêcher toute confusion avec le taux de faux positifs `b/(b+d)`.

Le RTN compare en outre les critères de surface et de population des arrêtés préfectoraux, pour J0/J1, à une analyse de référence J−1 ; cette évaluation territoriale ne se déduit pas d'un simple dépassement station ([LCSQA, 2022, §2.3](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).

**Limite.** Ce RTN ne fournit pas de protocole continu ou de seuil d'épisode équivalent pour NO₂ et PM2.5. Les publier en complément est utile, mais les appeler « conformes au RTN 2022 » serait faux.

### 2.2 FAIRMODE Forecast 2026 : formule et implémentation

La référence en vigueur identifiée est la **FAIRMODE Guidance WG3 on Forecast, version 2026**, publiée le 30 avril 2026, JRC146007 ([Vitali et al., 2026](https://knowledge4policy.ec.europa.eu/file/fairmode-guidance-wg3-forecast-version-2026_en)). Elle traite NO₂ maximum journalier, O₃ maximum journalier de moyenne glissante 8 h, PM10 et PM2.5 moyennes journalières ; elle ne vérifie pas tout le profil horaire.

Pour une station et `N` jours :

\[
MQI_f=\sqrt{\frac{N^{-1}\sum_i(M_i-O_i)^2}{N^{-1}\sum_i(P_i-O_i)^2}}
=\frac{RMSE_M}{RMSE_P}.
\]

L'objectif est `MQI_f ≤ 1`. Il est évalué station par station ; l'application satisfait le critère si au moins 90 % des stations le satisfont, le 90e percentile des pires stations servant d'indicateur synthétique ([Vitali et al., 2026, §1.1](https://knowledge4policy.ec.europa.eu/file/fairmode-guidance-wg3-forecast-version-2026_en)).

La persistance utilise la même observation disponible au moment d'émission pour tout l'horizon :

\[
P_i=O_{i-1-FH}\ \pm\ U(O_{i-1-FH}).
\]

Donc `FH=0 → O[i−1]`, `FH=1 → O[i−2]`, `FH=2 → O[i−3]`. Le guide imprime bien `±U`, mais ne donne pas dans cette équation une règle algorithmique suffisante pour choisir le signe. **Ne pas inventer cette branche :** pour la valeur réglementaire incluant `U`, utiliser le Delta-tool Forecast ou vérifier sa version de code ; publier en plus `RMSE_M/RMSE_{Olag}` sans incertitude comme contrôle reproductible.

La fonction d'incertitude reproduite dans la publication FAIRMODE évaluée par les pairs est :

\[
U(O)=U_r(RV)\sqrt{(1-\alpha^2)O^2+\alpha^2RV^2}.
\]

| Polluant | `Ur(RV)` | `RV` (µg/m³) | `α` |
|---|---:|---:|---:|
| NO₂ | 0,24 | 200 | 0,20 |
| O₃ | 0,18 | 120 | 0,79 |
| PM10 | 0,28 | 50 | 0,25 |
| PM2.5 | 0,36 | 25 | 0,50 |

Ces valeurs viennent de l'annexe A, table A1, de Vitali et al. ([2023, *Geoscientific Model Development*, DOI 10.5194/gmd-16-6029-2023](https://doi.org/10.5194/gmd-16-6029-2023)). Le guide 2026 renvoie à Janssen et Thunis (2022) au lieu de réimprimer ce tableau. **À vérifier dans la configuration exacte du Delta-tool téléchargé en 2026** avant de figer des tests de conformité ; les chiffres ci-dessus sont publiés et traçables, mais le PDF 2026 ne garantit pas explicitement qu'aucun paramètre logiciel n'a changé.

FAIRMODE ajoute :

\[
MFE=\frac{2}{N}\sum_i\frac{|M_i-O_i|}{M_i+O_i},\qquad
MFU=\frac{1}{N}\sum_i\frac{2U(O_i)}{O_i},
\]

\[
MPI_1=MFE_f/MFE_p,\qquad MPI_2=MFE_f/MFU,
\]

avec critères `MPI1 ≤ 1` et `MPI2 ≤ 1`. Pour les dépassements, FAIRMODE 2026 calcule Accuracy, SR, POD, FBias, Threat Score `TS=CSI` et Gilbert Skill Score, mais **ne fixe aucun seuil d'acceptation** pour ces métriques ; il ne fixe pas non plus de critère pour l'indice de qualité de l'air ([Vitali et al., 2026, tables 2–3 et conclusions](https://knowledge4policy.ec.europa.eu/file/fairmode-guidance-wg3-forecast-version-2026_en)).

**Erreur à éviter.** `MQI = RMSE/(β·RMS_U)` avec `β=2` est le MQI d'**assessment**, pas le `MQI_f` de prévision. Vitali et al. séparent explicitement les deux cadres ([2023, annexe C](https://doi.org/10.5194/gmd-16-6029-2023)).

### 2.3 Figures qu'un praticien reconnaîtra

Le paquet minimal est :

1. LCSQA : biais, RMSE et corrélation par région/type/horizon, avec repères de qualité ; scores par classes de concentration et part des observations ; série annuelle et recul cinq ans ;
2. LCSQA : diagramme de performance `x=SR`, `y=POD`, isolignes `FBias`, contours `CSI`, plus table brute `TP/FP/FN/TN` ;
3. FAIRMODE : *Forecast Target Plot* où la distance à l'origine vaut `MQI_f`, l'ordonnée `BIAS/RMSE_p`, l'abscisse `CRMSE/RMSE_p` et le côté gauche/droit renseigne le rapport FA/MA ;
4. FAIRMODE : *MPI plot*, *Forecast Threshold Performance Plot*, résumé tabulaire et histogramme des catégories AQI ([Vitali et al., 2026, §2](https://knowledge4policy.ec.europa.eu/file/fairmode-guidance-wg3-forecast-version-2026_en)).

Le diagramme de Taylor est utile en recherche, mais n'est pas une sortie canonique exigée par le RTN LCSQA 2022 ni par le guide WG3 2026. Une série temporelle sur quelques épisodes est un diagnostic utile, pas un substitut aux agrégats.

### 2.4 Ne pas réécrire Delta

FAIRMODE publie désormais deux Delta-tools en Python, dont **Delta-tool Forecast**, avec application web, code source et fichier exemple ; la page a été mise à jour le 23 juillet 2026 ([FAIRMODE, *Benchmarking tools*](https://knowledge4policy.ec.europa.eu/fairmode-forum-air-quality-modelling/fairmode-benchmarking-tools_en)). La version scientifique reproductible de 2023 est archivée sur Zenodo ([Vitali et al., 2023, DOI 10.5281/zenodo.7949868](https://doi.org/10.5281/zenodo.7949868)).

**Recommandation.** Calculer soi-même les métriques LCSQA simples, mais traiter le résultat Delta comme oracle de conformité : petit fichier figé, comparaison à tolérance numérique, version/commit du tool dans le rapport. C'est particulièrement important pour `±U`, les percentiles de stations et les cas limites de division par zéro.

---

## 3. Incertitude prédictive : ce qui est garanti et ce qui ne l'est pas

### 3.1 La meilleure première étape ici

**Recommandation à vingt jours :** régression quantile LightGBM + **Conformalized Quantile Regression** (CQR) sur un jeu de calibration strictement séparé. CQR corrige les bornes quantiles par un quantile des scores de non-conformité et garantit une couverture marginale finie sous échangeabilité ; il s'adapte mieux à l'hétéroscédasticité qu'un intervalle symétrique autour du point ([Romano, Patterson et Candès, 2019, NeurIPS, arXiv 1905.03222](https://arxiv.org/abs/1905.03222)).

Procédure externe, pour chaque pli station × mois :

```text
1. train       : ajuste q_low(x), q_high(x), sans stations/mois externes
2. calibration : score r_i = max(q_low(x_i)-y_i, y_i-q_high(x_i))
3. qhat        : quantile fini ceil((n_cal+1)*(1-alpha))/n_cal des r_i
4. test        : [q_low(x)-qhat, q_high(x)+qhat]
```

La calibration ne peut pas être le jeu test et toutes les transformations, sélections de variables et hyperparamètres doivent être ajustés avant de le voir.

### 3.2 Station inconnue et mois inconnu : aucune variante simple ne sauve tout

| Méthode | Garantie publiée | Verdict pour ce projet |
|---|---|---|
| split conformal/CQR | couverture marginale si calibration et test sont échangeables | base honnête, mais garantie cassée par station et mois nouveaux |
| Mondrian/par groupe | couverture dans chaque groupe si échangeabilité au sein du groupe et effectif suffisant | utile par type de station/saison ; ne garantit pas une station jamais vue |
| conforme pondérée | covariate shift, si `P(Y|X)` reste invariant et si le rapport de densité test/train est connu ou bien estimé | intéressant, mais hypothèse forte et estimation fragile en grande dimension ([Tibshirani et al., 2019, NeurIPS](https://papers.neurips.cc/paper_files/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html)) |
| ACI/adaptive conformal | fréquence de couverture à long terme sous dérive séquentielle ; pas une couverture conditionnelle instantanée par station | candidat opérationnel après le dossier, avec retour des observations ([Gibbs et Candès, 2021, NeurIPS](https://papers.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html)) |
| Venn-Abers | calibration probabiliste, originellement classification ; hypothèse i.i.d./échangeabilité | approprié à une probabilité binaire de dépassement, pas le premier choix pour un intervalle continu ([Nouretdinov et al., 2018, PMLR 91](https://proceedings.mlr.press/v91/nouretdinov18a.html)) |
| quantile LightGBM seul | aucune garantie de couverture distribution-free | bon modèle de base ; CQR mesure et corrige sa sous-couverture |

Pour une station réellement nouvelle, la calibration doit laisser des **stations entières** de côté et traiter la station comme unité de généralisation. Une calibration sur toutes les journées de stations connues ne peut revendiquer une garantie « nouvelle station ». On peut calculer un quantile pondéré de scores par station, ou une procédure conforme hiérarchique, mais la garantie nécessite alors une hypothèse d'échangeabilité entre stations ; elle n'est pas automatique.

**Conclusion.** Aucune méthode identifiée ne conserve simultanément, sans hypothèse supplémentaire, une garantie finie sous station nouvelle, mois nouveau, dépendance temporelle et dérive CAMS. La formulation honnête est « couverture empirique sous protocole station × mois cachés », pas « intervalle valide sous tout décalage ».

### 3.3 Validation : calibration puis finesse

Un intervalle honnête doit atteindre la couverture visée **et** rester informatif. Le principe publié est de maximiser la finesse (*sharpness*) sous calibration ([Gneiting, Balabdaoui et Raftery, 2007, *JRSS B*, DOI 10.1111/j.1467-9868.2007.00587.x](https://doi.org/10.1111/j.1467-9868.2007.00587.x)). Rapporter :

- couverture marginale et largeur médiane/moyenne ;
- score d'intervalle de Winkler à 80 %, 90 % et 95 %, règle propre décrite par Gneiting et Raftery ([2007, *JASA*, DOI 10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437)) ;
- couverture et largeur par station, type, région, mois, décile observé, régime CAMS et fraîcheur de l'observation ;
- quantiles 10/50/90 de la couverture par station, pas seulement sa moyenne ;
- courbe couverture–largeur lorsque `α` varie ;
- effectifs et intervalles bootstrap par station/bloc.

Un intervalle `[−∞,+∞]` couvre parfaitement mais n'a aucune valeur : c'est pourquoi couverture sans largeur ni score propre est insuffisante. Pour les extrêmes rares, afficher aussi la couverture conditionnelle empirique, en précisant qu'elle n'est pas garantie par la couverture marginale.

### 3.4 Intervalle et probabilité de dépassement ne sont pas interchangeables

Une distribution prédictive complète `F(y|x)` fournit à la fois des quantiles et `P(Y>s)=1−F(s|x)`. Un seul intervalle central à 90 % ne détermine pas cette probabilité : il ne donne que deux quantiles et perd toute la forme de la queue.

Pour une décision asymétrique, produire directement une probabilité calibrée de dépassement et l'évaluer par table d'effectifs, diagramme de fiabilité avec barres d'incertitude, Brier/Brier Skill et courbe précision–rappel ; la calibration d'un ensemble AQ par diagramme de fiabilité et Brier est une pratique publiée ([Garaud et al., 2011, *JGR Atmospheres*, DOI 10.1029/2011JD015780](https://doi.org/10.1029/2011JD015780)). L'intervalle reste préférable pour communiquer l'incertitude sur la concentration et diagnostiquer l'hétéroscédasticité.

### 3.5 Coût réaliste pour une AASQA

| Option | Calcul | Maintenance | À faire maintenant ? |
|---|---:|---:|---|
| quantiles LightGBM + split CQR | ~2 ajustements par borne/pli | faible | **oui** |
| calibration binaire isotone/Venn-Abers | faible | faible, mais événements rares | oui seulement avec validation imbriquée et effectifs publiés |
| Mondrian type × saison | faible | moyenne : petits groupes | sensibilité, pas produit principal |
| conforme pondérée | moyenne | élevée : densité et dérive à surveiller | non en vingt jours |
| CV+/jackknife+ | plusieurs réajustements | moyenne | luxe ici |
| ensemble probabiliste complet/EMOS spatial | élevée | élevée | piste de recherche ; une chaîne EMOS-INLA CAMS existe ([Stortini et al., 2024, *ACP*, DOI 10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024)) |

**Dimension de l'organisation.** Je n'ai pas trouvé de source établissant qu'un effectif donné rend une méthode maintenable. Le critère pertinent est le nombre de composants, de jeux de calibration et d'alertes à exploiter. Pour ce dossier, CQR ajoute peu de code et une affirmation testable ; une plateforme conforme adaptative multi-régimes serait du luxe.

**Correction d'une prémisse.** Je n'ai pas trouvé de source publique établissant qu'Atmo Occitanie publie « désormais un intervalle de confiance de 10 à 20 % selon le polluant » pour ses prévisions quotidiennes. **À vérifier** : il peut s'agir d'incertitudes d'indicateurs d'exposition ou de modélisation, qui ne sont pas des intervalles de prédiction individuels.

---

## 4. Dépôt reprenable : audit et liste de contrôle

### 4.1 État observé du dépôt au 2 août 2026

**Constat local, pas littérature :** le projet a une architecture `src/`, un contrat de données (`configs/data_contract.yaml`) et 250 fonctions `test_*` dans 19 fichiers `tests/test_*.py`. En revanche, il n'a pas de `README.md` racine, pas de workflow `.github/workflows`, pas de fichier de verrouillage, et son `pyproject.toml` ne déclare que pandas, NumPy et PyYAML alors que le code importe notamment requests, scikit-learn, Shapely, Streamlit, Plotly, LightGBM et des lecteurs GRIB. Dans l'environnement Codex disponible, `pytest` n'était pas installé : les tests n'ont donc pas pu être rejoués pendant cet audit.

Ce diagnostic fait de la **recréation de l'environnement** le premier risque de reprise. Ajouter MLflow, Kubernetes ou un feature store avant de corriger cela serait du contre-ordre.

### 4.2 Définition opérationnelle de « reprenable »

Une personne qui ne connaît pas le projet doit pouvoir, avec un accès autorisé aux données :

1. installer l'environnement depuis un fichier figé ;
2. lancer un test rapide sans réseau ni secret ;
3. reconstruire un petit jeu de démonstration ;
4. exécuter une expérience nommée depuis une configuration ;
5. relier chaque tableau du dossier à un commit, une empreinte de données et une commande ;
6. comprendre les usages interdits, les échecs connus et le mode dégradé ;
7. diagnostiquer un flux absent sans appeler l'auteur.

La reproductibilité exige code, données/artefacts accessibles, protocole, hyperparamètres et incertitude ; la checklist NeurIPS a précisément été conçue pour rendre les résultats ML vérifiables ([Pineau et al., 2021, *JMLR* 22(164)](https://www.jmlr.org/papers/v22/20-303.html)).

### 4.3 P0 — indispensable avant la candidature

| Livrable | Contenu minimal | Critère d'acceptation |
|---|---|---|
| `README.md` | objectif, périmètre, architecture, installation, 3 commandes, données requises, résultat attendu | un tiers suit le *quick start* sans explication orale |
| environnement verrouillé | dépendances d'exécution, test et optionnelles ; versions verrouillées | installation dans un environnement vierge puis tests |
| commande unique | `test`, `demo`, `reproduce-table` via scripts stables | code retour non nul en cas d'échec |
| CI légère | lint minimal + tests unitaires + mini bout-en-bout sur fixture | aucun accès réseau/secret ; durée courte |
| manifeste de données | source/DOI/URL, licence, requête, run, date de collecte, empreinte, schéma, couverture, statut de validation | toute table d'entrée possède une ligne de manifeste |
| registre d'expériences | ID, commit, config, empreintes, plis, graine, métriques/IC, artefacts | chaque chiffre du dossier pointe vers un ID |
| fiche de modèle | voir §4.5 | une page principale + annexes automatiques |
| test de reprise | une personne rejoue le mini-pipeline et note les obstacles | zéro étape tacite bloquante |

Les tests doivent prioriser les erreurs déjà coûteuses : heure d'émission et disponibilité, unités, ordre longitude, échéance CAMS, double split station/mois, listes `year × month`, agrégats réglementaires, seuil strict `>`, couples valides à 75 %, absence d'observation passée et changement de cycle. L'acte d'exécution européen demande que les données d'entrée soient, lorsque possible, contrôlées avant chaque application et que l'évaluation des systèmes fusionnant mesures et modèles emploie des mesures indépendantes ; son annexe II formalise un *leave-one-out* des stations ([décision d'exécution (UE) 2026/1208, art. 3 et annexe II](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).

### 4.4 Provenance et rupture de flux

Chaque fichier ou partition doit porter, directement ou dans un manifeste immuable :

```yaml
dataset_id: cams-europe-air-quality-forecasts
provider: ECMWF/CAMS ADS
retrieved_at_utc: ...
request: {model: ensemble, leadtime_hour: ..., variable: ..., area: ...}
forecast_reference_time: ...
valid_time_range: ...
upstream_cycle: U8b          # inconnu si non démontré
source_revision: ...
license: ...
sha256: ...
bytes: ...
rows: ...
schema_version: ...
missingness_by_variable: ...
quality_checks: ...
```

Le pipeline doit écrire un statut `complete/degraded/failed`, la cause, les entrées manquantes, les lignes rejetées et le mode de repli choisi. CAMS recommande explicitement aux chercheurs de conserver les fichiers téléchargés pour la traçabilité, car l'archive NRT ne couvre que trois ans glissants ; les transferts opérationnels publient des manifestes MD5 une fois un lot complet ([documentation CAMS régionale](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation) ; [accès SFTP/HTTPS CAMS, 2026](https://confluence.ecmwf.int/spaces/CKB/pages/599163953/SFTP%2Band%2BHTTPS%2Baccess%2Bto%2BCAMS%2BEuropean%2Bair%2Bquality%2Bforecast%2Bdata)).

Les principes FAIR rendent les données trouvables, accessibles, interopérables et réutilisables ; ils ne garantissent à eux seuls ni exactitude ni reproduction d'un résultat ([Wilkinson et al., 2016, *Scientific Data*, DOI 10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18)). Une *datasheet* documente motivation, composition, collecte, prétraitements, usages et maintenance ([Gebru et al., 2021, *Communications of the ACM*, DOI 10.1145/3458723](https://doi.org/10.1145/3458723)).

### 4.5 Fiche de modèle utile ici

Les *model cards* ont été proposées pour documenter usage prévu, performance ventilée, limites et considérations d'emploi ([Mitchell et al., 2019, FAT*, DOI 10.1145/3287560.3287596](https://doi.org/10.1145/3287560.3287596)). Pour ce modèle :

- identifiant/version, date, propriétaire, code/commit et empreinte de l'artefact ;
- décision assistée : correction CAMS aux stations, pas remplacement de l'expertise ni carte sans capteur ;
- polluants, grandeurs journalières, horizon et heure d'émission ;
- population : `FULL` stations instrumentées versus `NO_LOCAL_OBS` ;
- sources, versions, statut temps réel/révisé et disponibilité attendue ;
- cible, unités, contrôles, exclusions et gestion des manquants ;
- algorithme, perte, hyperparamètres, contraintes et écrêtages ;
- split station × mois, baselines, effectifs, métriques/IC continus et épisodes ;
- performance par région/type/saison/concentration/fraîcheur/version CAMS ;
- limites : détection non démontrée, dépendance réseau, octobre 2024 inexpliqué, domaine français 36 mois ;
- seuils d'abstention, repli, journalisation, surveillance et déclencheurs de revue ;
- changements depuis la version précédente.

La directive 2024/2881 exige, lorsqu'un modèle sert à l'évaluation réglementaire, des références décrivant l'application et le calcul de l'objectif de qualité ; l'objectif doit être satisfait à au moins 90 % des points disponibles ([directive (UE) 2024/2881, annexe V](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)). L'acte 2026/1208 ajoute des exigences techniques sur entrées, représentativité, assurance qualité, indépendance des mesures de validation et résolution ([décision 2026/1208, art. 2–3](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)). Ces textes concernent l'usage réglementaire des modèles ; ils ne transforment pas automatiquement ce prototype de candidature en application réglementaire.

### 4.6 P1 utile, P2 luxe

**P1 si P0 est terminé :** image de conteneur légère ; cache de données adressé par contenu ; rapport automatique HTML/Markdown ; scan de secrets ; `CHANGELOG`; test de contrat avec un petit fichier CAMS ; matrice de compatibilité Windows/Linux.

**P2 — luxe dans les vingt jours :** Kubernetes, feature store, orchestration distribuée, registre de modèles serveur, observabilité 24/7, architecture microservices, data lake, traçage OpenTelemetry complet, certification ISO. MLflow ou DVC ne sont utiles maintenant que s'ils remplacent immédiatement un registre manuel fragile ; les introduire sans scénario de reprise serait du cérémonial.

---

## 5. Dérive : surveiller, attribuer, puis adapter

### 5.1 Les ruptures amont sont certaines ; celle d'octobre ne l'est pas

Le journal public CAMS donne : U7b en juin 2023, adapté à cy48r1 ; U8 en novembre 2023 ; U8b en juin 2024, décrit seulement comme des améliorations de modèles individuels ; U9 en novembre/décembre 2024 avec CAMS_REG.v7, adaptation cy49r1 et nouvelles fractions PM2.5 ; U10 en novembre 2025 ([historique CAMS régional, consulté en 2026](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)). L'annonce U9 date l'adaptation de la production au 13 novembre 2024 et les nouvelles fractions au 3 décembre ([ECMWF, annonce U9](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219)). Le cycle global cy49r1 a basculé le 12 novembre 2024 ([documentation CAMS globale](https://confluence.ecmwf.int/pages/viewpage.action?navigatingVersions=true&pageId=673323626)).

**Conclusion.** Une rupture détectée en octobre 2024 ne doit pas être appelée « effet U9 ». Causes encore possibles : évolution d'un membre non détaillée publiquement, composition/disponibilité de l'ensemble, saison, stations présentes, flux révisé, erreur de jointure ou vraie situation atmosphérique. **Inexpliquée** est le bon statut tant qu'un test d'attribution ne tranche pas.

### 5.2 Détection rétrospective et surveillance en ligne

**Pratique publiée, transposée au projet :**

- rétrospectif : PELT ou segmentation pénalisée sur médiane quotidienne robuste des résidus standardisés ; les méthodes, coûts et choix de pénalité sont synthétisés par Truong, Oudre et Vayatis ([2020, *Signal Processing*, DOI 10.1016/j.sigpro.2019.107299](https://doi.org/10.1016/j.sigpro.2019.107299)) ;
- multivarié : méthode non paramétrique par distance d'énergie sur un vecteur réduit de résidus région × polluant, adaptée aux changements de distribution ([Matteson et James, 2014, *JASA*, DOI 10.1080/01621459.2013.849605](https://doi.org/10.1080/01621459.2013.849605)) ;
- en ligne : cartes EWMA/CUSUM ou Page–Hinkley sur biais, MAE/RMSE glissants, taux de manquants et part des membres disponibles ;
- confirmation : n'ouvrir un incident qu'après persistance du signal et dégradation de performance, car un changement de distribution d'entrée ne prouve pas un changement de `P(Y|X)` ; les revues du *concept drift* séparent détection, compréhension et adaptation ([Lu et al., 2019, *IEEE TKDE*, DOI 10.1109/TKDE.2018.2876857](https://doi.org/10.1109/TKDE.2018.2876857)).

**À vérifier.** Je n'ai pas identifié une étude AASQA publiée qui établisse qu'un de ces détecteurs est le standard français des résidus multi-stations. Leur application proposée ici est une extrapolation méthodologique.

Procédure concrète : standardiser le résidu **dans la période d'apprentissage seulement**, retirer une saisonnalité apprise, former chaque jour la médiane par station stable puis par région/type, détecter sur cette série et confirmer sur les distributions stationnelles. Une seule moyenne nationale peut masquer des ruptures opposées ; 476 tests indépendants créent au contraire des faux signaux multiples.

### 5.3 Attribuer modèle, atmosphère ou réseau

| Signature | Modèle amont probable | Atmosphère réelle probable | Réseau/traitement probable |
|---|---:|---:|---:|
| saut CAMS et résidu simultané, observations sans saut, beaucoup de stations | fort | faible | faible |
| saut observations et CAMS cohérent avec météo, plusieurs systèmes/modèles | moyen | fort | faible |
| saut limité à une station/instrument, voisins stables | faible | faible | fort |
| changement du nombre de membres ou trous de fichiers | fort | faible | moyen |
| saut après révision historique mais absent des instantanés temps réel | faible | faible | fort |

Les témoins à conserver sont : CAMS brut par membre et ensemble, observations brutes/provisoires/validées, stations voisines, stations rurales stables, météo prévue, autres polluants, taux de données manquantes et métadonnées d'instrument/position. La décision 2026/1208 impose d'ailleurs des mesures indépendantes pour valider une application fusionnant mesures et modèles ; cette séparation est également la bonne logique d'attribution ([décision 2026/1208, art. 3(5) et annexe II](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).

Le test le plus probant serait une période où ancien et nouveau systèmes ont tourné en parallèle. À défaut, ajuster une régression interrompue autour des dates documentées, avec saison/météo et composition du réseau, puis tester la rupture sur stations stables. Cela soutient une attribution ; cela ne remplace pas un A/B parallèle.

### 5.4 Que faire après changement de version ?

1. **Geler** l'ancien modèle et son jeu de données ; ne pas réécrire l'historique.
2. **Quarantaine/challenger** : comparer CAMS brut, correcteur ancien, correcteur recalibré court et modèle sans mémoire locale sur une fenêtre post-changement.
3. **Réentraîner** dès que le nouveau régime contient assez de jours et de situations, mais conserver une fenêtre longue pondérée si elle améliore réellement le *walk-forward*.
4. **Variable de version** : utile pour expliquer l'historique, insuffisante seule pour un cycle futur jamais vu ; elle ne sait pas extrapoler l'effet d'U11.
5. **Fenêtre/cadence** : choisir par validation en origine glissante simulant plusieurs ruptures, avec temps de récupération, RMSE, `MQI_f`, épisode et stabilité ; ne pas choisir « 90 jours » par habitude.

Bertrand et al. documentent précisément le compromis : CAMS change un à deux fois par an ; leur MOS global, réentraîné quotidiennement sur 3 jours, s'adapte vite, tandis qu'un MOS local exploite un historique plus long ([2023](https://doi.org/10.5194/acp-23-5317-2023)). Cela prouve qu'une stratégie courte est viable dans leur système, pas que trois jours sont optimaux pour vos 476 stations et vos covariables.

**Recommandation initiale, à valider :** contrôle quotidien des flux ; tableau de bord mensuel ; challenger recalibré chaque mois ; décision de promotion trimestrielle ou après changement CAMS confirmé ; revue annuelle complète. Un déclenchement automatique de production sur un seul test de dérive serait prématuré.

### 5.5 Le journal CAMS est nécessaire, mais insuffisant

La page officielle donne une granularité de **release** U7b/U8/U8b/U9/U10 et quelques modifications globales ; U8b n'a ni jour exact ni détail public par membre ([historique CAMS régional](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)). Les annonces du forum donnent parfois des dates plus précises, mais U9 a été annoncé après certaines mises en production ([annonce U9](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219)). Ce n'est donc pas un registre assez fin pour attribuer seul une rupture journalière.

Le manifeste local doit au minimum archiver : date de téléchargement, `forecast_reference_time`, échéance, modèle/membre, liste de membres présents, cycle/release connu ou `unknown`, taille et SHA-256 des fichiers, requête ADS, version du décodeur, couverture et variables. CAMS demande explicitement de conserver les fichiers utilisés pour la traçabilité de la recherche, son archive de prévision étant glissante sur trois ans ([documentation CAMS régionale](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).

---

## Décision à vingt jours

### À faire, dans cet ordre

1. **Isoler la persistance** : P0/P1/P3/P7 contre ML0/ML1, mêmes lignes et plis ; renommer le gain de +14 points tant que ce test manque.
2. **Implémenter le banc LCSQA exact** : couples à 75 %, score par station puis moyenne, O₃/PM10 J0/J1, tables brutes et diagramme de performance.
3. **Brancher Delta-tool Forecast** sur un petit cas oracle ; ne pas recoder l'ambiguïté `±U` de mémoire.
4. **Rendre le dépôt installable** : README, dépendances complètes verrouillées, commande de démonstration, CI courte.
5. **Créer manifeste de provenance + registre d'expériences** pour relier chaque chiffre au commit et aux données.
6. **Publier les modes `FULL` et `NO_LOCAL_OBS`** et tester les pannes par blocs.
7. **Ajouter CQR simple** et rapporter couverture + largeur ; ne pas promettre une garantie sous double décalage.
8. **Tenir un journal CAMS local** et qualifier octobre 2024 d'inexpliqué jusqu'à attribution.

### À ne pas faire avant la candidature

- conforme pondérée complexe, ACI multi-régimes ou ensemble probabiliste spatial complet ;
- plateforme MLOps, Kubernetes, feature store ou orchestration distribuée ;
- réentraînement automatique déclenché par une seule alerte ;
- nouvelle architecture neuronale avant persistance, LCSQA, provenance et reprise.

Le gain le plus crédible à présenter n'est donc pas « LightGBM gagne 41,87 % », mais : **« une correction à trois modes, évaluée sur stations et mois cachés, dont la mémoire locale est comparée à la persistance FAIRMODE, dont l'indisponibilité est testée, et dont chaque résultat est rejouable ».**
