# Seconde revue adverse — décision statistique et plan à quatre jours

## 1. Tous les effets du chantier neuronal sont-ils sous la barre de bruit ?

### Verdict

**Aucun des quatre effets n'est actuellement démontré, mais pas parce qu'il serait permis
de les comparer directement à ±2,02 points.** Cette barre a été mesurée sur un **score
absolu O₃ non apparié**. La comparaison RealMLP–LightGBM est appariée : mêmes lignes,
même partition, mêmes observations. Le déplacement commun provoqué par une partition se
soustrait en grande partie. Le dépôt l'explique déjà explicitement dans
[`stabilite_apport_geoscf.py`](../scripts/stabilite_apport_geoscf.py#L4-L18).

La quantité à estimer n'est donc pas la dispersion de chacun des deux scores, mais celle de
leur **différence de pertes sur les mêmes observations**.

Il reste en outre une erreur de transcription O₃ dans le second brief. Les artefacts donnent :

| polluant | LightGBM réglé | RealMLP réglé | gain RealMLP contre LightGBM |
|---|---:|---:|---:|
| O₃ | 12,1320 | **11,9808** | **+1,25 %** |
| NO₂ | **12,3476** | 12,4578 | −0,89 % |
| PM10 | 5,7943 | **5,6405** | **+2,66 %** |
| PM2,5 | 3,7911 | **3,7908** | +0,01 % |

Le 12,1320 attribué à RealMLP dans le brief est le LightGBM réglé
([artefact LightGBM](../reports/optuna_lgbm_O3_temporel.csv)); le vrai score RealMLP est
11,9808 ([artefact RealMLP](../reports/optuna_realmlp_O3.csv)). Ce point doit être corrigé
avant tout nouveau calcul.

### Test exact : différence appariée et équivalence pratique

Pour chaque ligne testée, enregistrer `jour`, `station_id`, `obs`, `pred_lgbm` et
`pred_realmlp`. Calculer la différence de perte quadratique

\[
d_{s,t}=(y_{s,t}-\hat y^{MLP}_{s,t})^2-(y_{s,t}-\hat y^{LGBM}_{s,t})^2,
\]

puis réestimer le gain de RMSE dans un bootstrap **croisé** :

- blocs temporels primaires : mois calendaires entiers ;
- sensibilité obligatoire : blocs mobiles de deux mois ;
- blocs spatiaux : 20 groupes géographiques fixes, construits par `KMeans(n_clusters=20,
  random_state=20260816)` sur les coordonnées projetées ;
- à chaque tirage, rééchantillonner indépendamment blocs temporels et blocs spatiaux, puis
  garder leur produit cartésien ;
- 10 000 tirages ; intervalle percentile à 95 % ;
- correction de Holm des quatre tests d'amélioration.

Interface de commande à implémenter, sans option supplémentaire à régler après lecture des
résultats :

```powershell
python scripts/poids_melange.py --polluant PM10 --sauver-predictions
python scripts/bootstrap_paire_modeles.py `
  --predictions reports/predictions_modeles_PM10.parquet `
  --reference pred_lgbm --candidat pred_realmlp `
  --blocs-mois 1 2 --clusters-stations 20 --tirages 10000 `
  --marge-equivalence-pt 2 --correction-multiple holm
```

Répéter la seconde commande pour les quatre polluants. Le calcul bootstrap agrège des
prédictions déjà produites : il ne réentraîne pas 10 000 modèles.

### Seuil de décision

Trois conclusions, exclusives :

1. **Avantage démontré et utile** : borne basse de l'IC 95 % du gain strictement positive,
   après Holm, même signe avec blocs de un et deux mois, et gain ponctuel ≥ 2,0 points.
2. **Équivalence pratique** : IC 90 % entièrement compris dans [−2,0 ; +2,0] points
   (TOST avec marge préenregistrée de 2 points).
3. **Indéterminé** : tout le reste. « Non significatif » ne devient pas « équivalent » si
   l'intervalle est simplement trop large.

Le test fixe peut établir une différence **conditionnelle à ce test**. Il ne restaure pas
un test final vierge : les scores et les poids optimaux sur ce bloc ont déjà été consultés.
Toute conclusion confirmatoire devra attendre un nouveau bloc futur.

### Ce qu'il faut écrire si aucun effet ne passe

> À budget de réglage égal, nous n'avons pas mis en évidence d'avantage généralisable du
> réseau sur LightGBM. Les écarts rétrospectifs vont de −0,89 % à +2,66 %, mais ne
> franchissent pas simultanément nos critères d'incertitude appariée et de pertinence
> pratique. Nous conservons donc LightGBM, plus simple, et publions ce résultat négatif
> plutôt que de sélectionner le meilleur polluant a posteriori.

**Coût : 3 à 4 h**, dont environ 2 h pour faire persister les prédictions et écrire le
bootstrap, moins d'une heure de calcul, puis une heure de contrôle et rédaction.

### Le poids NO₂ : ce n'est pas une validation honnête du combineur

Le bloc appelé validation dans [`poids_melange.py`](../scripts/poids_melange.py#L47-L80)
a déjà servi :

- à sélectionner les hyperparamètres Optuna ;
- à arrêter RealMLP de façon anticipée ;
- puis à sélectionner le poids du mélange.

Il est hors du **fit**, mais pas hors du **processus de sélection**. Le qualifier de poids
« honnête » est trop fort ; il faut le renommer `poids_developpement`.

Les trois phénomènes proposés sont présents :

1. le bloc ne prédit pas bien la covariance des erreurs sur le test ;
2. les vallées sont plates — sur NO₂, de nombreux poids intérieurs diffèrent de quelques
   centièmes de RMSE seulement ;
3. le même bloc a été réutilisé, ce qui favorise la configuration qui s'y est déjà adaptée.

**Décision pratique : abandonner la sélection de poids pour ce dossier.** Une moyenne 50/50
serait plus simple, mais la choisir maintenant parce qu'elle paraît bonne sur le test serait
encore une décision postérieure à l'observation. Elle peut être préenregistrée pour le
prochain bloc futur, pas promue aujourd'hui. Le produit citable reste le LightGBM seul tant
que le réseau ne passe pas le test ci-dessus.

Pour réouvrir l'ensemble plus tard, il faudra quatre rôles chronologiques distincts — fit,
réglage/arrêt, méta-validation du poids, test final — ou une validation imbriquée à origine
glissante.

**Seuil de réouverture :** sur au moins trois origines futures, le poids 0,5 préenregistré
doit avoir un gain médian ≥ 1 %, une borne basse bootstrap > 0 et aucune origine < −1 %.

**Si cela échoue, écrire :**

> Les erreurs des deux modèles sont trop corrélées et leur covariance trop instable dans le
> temps pour qu'un ensemble apporte un gain reproductible ; aucun combineur n'est déployé.

## 2. Spéciation : téléchargement, époques et ablation exacte

### 2.1 Télécharger d'abord sel marin et carbone total

**Oui.** Une heure de réseau est faible devant le coût de refaire toute l'ablation. Le sel
marin est surtout un régime PM10 grossier distinct des cinq variables présentes ; son
absence laisserait précisément l'ablation PM10 incomplète. Le carbone total permet de
tester si `ecres_conc` apporte le chauffage résidentiel ou seulement un proxy de combustion
générale.

Ne pas ajouter les deux champs au lot existant de six : celui-ci utilise déjà environ 89 %
du plafond ADS et un lot de huit le dépasserait. Télécharger un **complément séparé** sous
des noms distincts, avec les clés ADS officielles `pm10_sea_salt_dry` et
`pm2.5_anthropogenic_total_carbon` ([documentation CAMS](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).

```powershell
python scripts/telecharger_speciation_complement.py `
  --debut 2024-01 --fin 2026-08 --paralleles 3 `
  --variables pm10_sea_salt_dry pm2.5_anthropogenic_total_carbon
python scripts/extraire_speciation.py --scope metropole --complement
```

Le script complémentaire doit écrire `speciation_complement_AAAAMM.nc`, contrôler les deux
variables nommément avant renommage, puis l'extracteur doit exiger leurs colonnes dans les
32 fichiers. Une simple relance du script actuel ne fonctionne pas : son contrôle par taille
saute les fichiers mensuels déjà présents.

**Seuil :** 32/32 mois ouverts, deux variables présentes, fenêtre temporelle J+1 complète,
aucune station hors emprise, taux de valeurs non finies < 0,1 %. Sinon l'ablation ne démarre
pas.

**Coût : 2 h** — environ 1 h de téléchargement, 30 à 45 min d'extraction, 15 min de contrôle.

**Si le téléchargement échoue, écrire :**

> Le sel marin et le carbone élémentaire total ont été identifiés comme prédicteurs
> physiquement pertinents, mais leur archive opérationnelle n'a pas pu être constituée et
> vérifiée dans le délai. L'ablation publiée est donc explicitement limitée aux cinq
> traceurs disponibles et ne permet pas de conclure sur ces deux sources.

### 2.2 Bornes CAMS utilisables

Les bornes documentées sont :

| époque | intervalle à utiliser | traitement |
|---|---|---|
| U8 stable | 2023-11-21 → 2024-05-31 | U8 a été mise en production le 21 novembre 2023 ([annonce](https://forum.ecmwf.int/t/upgrade-u8-to-the-cams-european-air-quality-products/1540)) |
| transition U8b | 2024-06-01 → 2024-06-30 | **exclure** : CAMS ne publie que « juin 2024 », sans jour exact |
| U8b stable | 2024-07-01 → 2024-11-12 | avant le changement émissions/IFS de U9 |
| U9 stable, socle | 2024-11-13 → 2025-11-12 | émissions et cycle 49r1 changent le 13 novembre 2024 ([annonce](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219)) |
| nitrate disponible | à partir du 2024-12-03 | NO₃/NH₄/SO₄ ajoutés le 3 décembre 2024, donc nitrate séparé du début de U9 |
| U10 stable | à partir du 2025-11-13 | U10 mise en production le 13 novembre 2025 ([annonce](https://forum.ecmwf.int/t/upgrade-u10-to-the-cams-european-air-quality-products/14390)) |

Pour l'ablation, exclure juin 2024 ainsi que les 7 jours centrés sur les transitions connues.
Ne pas inventer une date quotidienne pour U8b.

### 2.3 Rupture de version contre saisonnalité

Une comparaison mensuelle avant/après ne peut pas identifier la cause : les trois mises à
jour principales surviennent en novembre, en même temps que le chauffage. Le test exploitable
est une **discontinuité quotidienne à date imposée** : la saison évolue normalement de façon
lisse, tandis qu'une mise en production peut produire une marche au jour documenté.

Test exact sur le résidu CAMS brut, avant tout MOS :

- réponse : médiane nationale quotidienne du résidu stationnel, calculée sur le même panel
  de stations de fond de part et d'autre ;
- fenêtre : 42 jours avant et 42 jours après la date, transition exclue ;
- régression locale linéaire avec pente distincte avant/après, effets fixes station et jour
  de semaine ;
- incertitude par bootstrap des jours en blocs de 7 jours et des 20 groupes spatiaux ;
- placebos : toutes les coupures espacées de 7 jours entre septembre et février qui sont à
  plus de 42 jours d'une vraie mise à jour ;
- effectuer le test séparément par polluant et sur le biais ainsi que la RMSE quotidienne.

```powershell
python scripts/ruptures_cams.py `
  --dates 2023-11-21 2024-11-13 2025-11-13 `
  --fenetre-jours 42 --bloc-jours 7 --clusters-stations 20 `
  --placebos saison --tirages 10000 --panel fond-commun
```

**Seuil :** IC 95 % de la marche excluant zéro, amplitude absolue supérieure au 97,5e
percentile des marches placebo, et même signe dans au moins deux des trois plis spatiaux.
Si seul le premier critère passe, écrire « rupture compatible avec la version », jamais
« effet causal de la version ». U8b n'entre pas dans ce test faute de date exacte.

**Coût : 5 à 6 h**, script, agrégation, placebos et figures compris.

**Si le test échoue, écrire :**

> Les performances varient entre époques CAMS, mais le corpus ne permet pas de séparer une
> rupture de version d'une évolution saisonnière ou météorologique. Nous stratifierons donc
> les scores par version sans attribuer causalement les écarts aux mises à jour.

### 2.4 Ablation à deux étages

Utiliser LightGBM par défaut, sans nouvelle optimisation. Deux plis temporels prospectifs,
croisés avec trois groupes de stations fixes :

- pli U9 : entraînement 2024-01-01 → 2024-10-31 ; test 2024-12-03 → 2025-10-31 ;
- pli U10 : entraînement 2024-01-01 → 2025-10-31 ; test 2025-12-01 → 2026-07-31 ;
- dans chaque pli, exclure du fit toutes les stations du groupe testé.

Étape de garde, trois configurations seulement :

1. `base` : prédicteurs déployés ;
2. `base + core5` ;
3. `base + core7` : les cinq, sel marin et carbone total.

```powershell
python scripts/ablation_speciation.py `
  --polluants PM10 PM25 --configs base core5 core7 `
  --plis-temporels U9 U10 --plis-stations 3 `
  --bootstrap-mois 1 2 --clusters-stations 20 --tirages 10000 `
  --checkpoint reports/ablation_speciation_etat.json
```

**Garde :** ne lancer le leave-one-out que si `core7` gagne ≥ 1,0 % contre `base`, borne
basse IC 95 % > 0, dans chacun des deux plis temporels. Si le gain n'est présent que dans
une époque, le résultat est une interaction de version, pas un apport déployable général.

Si la garde passe, retirer successivement chaque variable de `core7`. Une variable est
retenue si son retrait dégrade d'au moins 0,5 %, avec IC 90 % entièrement positif, sans
dégradation > 1 % dans l'autre époque. Les importances LightGBM ne sont pas un substitut à
ce retrait apparié.

Le nitrate fait l'objet d'une expérience récente séparée, car le pli U9 précédent ne peut
pas entraîner une variable encore inexistante :

- nitrate-A : entraînement 2024-12-03 → 2025-05-31 ; test 2025-06-01 → 2025-10-31 ;
- nitrate-B : entraînement 2024-12-03 → 2025-10-31 ; test 2025-12-01 → 2026-07-31.

Comparer `core7+nitrate` à `core7` sur exactement ces mêmes lignes. Ne jamais comparer son
score à une configuration entraînée sur 32 mois ou sur un panel différent.

**Coût : 7 à 8 h** si la garde échoue, 10 à 12 h si tout le leave-one-out est déclenché.

**Si la garde échoue, écrire :**

> L'ajout groupé des traceurs CAMS de composition n'améliore pas la correction de façon
> stable à travers U9 et U10. La composition simulée n'apporte donc pas, dans ce protocole,
> l'information d'émission ou d'innovation observationnelle qui manque au produit sans
> capteur ; ces variables ne sont pas déployées.

### 2.5 Bootstrap commun aux expériences

Réponse directe : **un mois** pour l'analyse primaire, **deux mois** en sensibilité ;
**20 groupes géographiques de stations**, pas des paquets aléatoires de taille arbitraire ;
**10 000 tirages**. Cinq mille suffisent pour une exploration, mais dix mille coûtent peu
une fois les prédictions persistées et stabilisent mieux les quantiles publiés.

Un résultat n'est citable que si son signe et son verdict de seuil sont inchangés entre les
blocs d'un et de deux mois.

## 3. PDF : la réparation devient une porte de livraison

Le correctif d'écrêtage interne dans [`exporter_pdf.py`](../scripts/exporter_pdf.py#L70-L99)
est pertinent. Il manque toutefois encore une propriété : prouver que les **valeurs
citables attendues** sont présentes dans le PDF final. Le script
[`verifier_source_pdf.py`](../scripts/verifier_source_pdf.py#L88-L108) avertit lorsqu'un
mot-clé est absent mais retourne actuellement zéro ; une automatisation peut donc encore
livrer un PDF sémantiquement amputé.

### Test exact

Ajouter une option `--require` qui rend le code 1 pour tout motif absent, puis exécuter :

```powershell
python scripts/exporter_pdf.py presentation_atmo.html --pages-min 40
python scripts/verifier_source_pdf.py --local `
  reports/figures/presentation_atmo.pdf --require `
  "seul citable" "4,236" "2,772" "double aveugle" "limites"
```

Les valeurs exactes de `--require` doivent être produites par le générateur depuis le
manifeste des chiffres citables, pas recopiées une seconde fois à la main. Contrôler
visuellement les seules pages qui contiennent un tableau large après rendu raster.

### Seuil de décision

- zéro conteneur avec `scrollWidth - clientWidth > 2 px` en média `print` ;
- largeur globale ≤ 718 px ;
- au moins 40 pages ;
- zéro erreur JavaScript ;
- 100 % des motifs obligatoires retrouvés dans le texte extrait ;
- inspection visuelle des pages signalées sans colonne coupée ni corps illisible.

**Coût : 3 h** pour durcir le contrôle, régénérer et vérifier les pages à risque.

**Si le test échoue, écrire dans le journal de livraison — et ne pas joindre le PDF :**

> L'export PDF n'a pas satisfait le contrôle d'intégrité visuelle et sémantique ; la version
> imprimée n'est pas livrée. Le document HTML reste l'artefact canonique jusqu'à correction.

## 4. Arbitrage : les deux lignes à garder

### Ligne 1 — audit des ruptures CAMS

**Gardée**, selon le test de § 2.3. Sans elle, le contraste spatial/temporel PM2,5 et les
effets de spéciation restent impossibles à interpréter.

- **Seuil :** marche au vrai jour > 97,5e percentile placebo, IC 95 % hors zéro, signe
  cohérent spatialement.
- **Coût :** 5 à 6 h.
- **Si échec :** phrase de non-identification donnée en § 2.3 ; publier seulement les scores
  stratifiés, sans causalité.

### Ligne 2 — ablation de spéciation, après complément de deux variables

**Gardée**, selon le test en garde de § 2.4. Les données sont presque prêtes, le coût réseau
supplémentaire est borné, et le test répond directement à l'hypothèse centrale sur les PM.

- **Seuil :** ≥ 1 % et borne basse IC 95 % > 0 dans U9 **et** U10.
- **Coût :** 9 à 14 h téléchargement compris, selon déclenchement du leave-one-out.
- **Si échec :** ne pas déployer les traceurs et publier le résultat négatif donné en § 2.4.

### Lignes écartées et texte à mettre dans le dossier

#### IFS / couche limite

**Écartée maintenant.** Onze mois, aucune hauteur de couche limite et une fenêtre qui se
termine pendant U9 ne permettent pas une conclusion générale. Étendre correctement l'archive
est un chantier de données, pas une ablation de quatre heures.

> Les covariables IFS ont fourni un signal préliminaire sur onze mois, mais l'archive ne
> couvre ni plusieurs cycles saisonniers ni la hauteur de couche limite. Nous ne généralisons
> pas ce résultat et différons l'évaluation opérationnelle sur une archive complète.

**Coût évité : 8 à 12 h** de téléchargement, extraction, contrôle et réévaluation.

#### Modèle à régimes

**Écarté.** Il serait prématuré d'ajouter une porte ou des interactions avant de démontrer
que le bloc de composition lui-même transfère entre U9 et U10.

> Un modèle conditionné par régime de source n'a pas été ajusté : la première étape est de
> vérifier que les traceurs de régime apportent un signal hors époque. Ajouter une porte
> avant cette vérification multiplierait les degrés de liberté sans preuve d'information.

**Coût évité : 6 à 10 h.**

#### Prévision probabiliste

**Écartée.** Elle améliorerait la représentation de l'incertitude et la décision, mais pas
le rang des épisodes tant qu'aucun nouveau prédicteur informatif n'est validé.

> La calibration probabiliste des dépassements n'a pas été menée dans ce délai. Elle peut
> améliorer la fiabilité des probabilités, mais ne résout pas l'absence actuelle de signal
> discriminant pour les épisodes PM10 ; elle est reportée après l'évaluation des nouveaux
> prédicteurs.

**Coût évité : 6 à 8 h.**

#### Apprentissage multi-tâches PM2,5 / fraction grossière

**Écarté.** C'est une nouvelle formulation de cible, avec contrôles de cohérence et nouveau
protocole, sans résultat préalable dans le dépôt.

> La cohérence jointe PM2,5–PM10 constitue une piste identifiée mais non mesurée. Sa mise en
> œuvre exige une cible grossière, des contraintes de masse et une validation dédiée ; elle
> n'a pas été ouverte à quatre jours de la remise.

**Coût évité : 8 à 12 h.**

## 5. Filtre de Kalman pour `AUX STATIONS`

### Avis révisé

**Je ne maintiens pas la dépriorisation pour cette variante.** Dès lors que `AUX STATIONS`
assume l'observation récente, un état de biais adaptatif est exactement dans son périmètre.
Le gain de +43,1 % de la moyenne glissante rend le mécanisme prioritaire à tester.

Mais un filtre local linéaire à rapport de variances constant converge vers une **EWMA**.
Le Kalman ne mérite d'être retenu que s'il bat à la fois la fenêtre fixe de 7 jours et cette
baseline exponentielle plus simple, notamment en présence de manquants ou de rupture.

### Test exact

État journalier par station :

\[
b_{s,t}=b_{s,t-1}+\eta_{s,t}, \qquad
r_{s,t}=b_{s,t}+\epsilon_{s,t}, \qquad
r_{s,t}=obs_{s,t}-CAMS_{s,t}.
\]

Comparer quatre systèmes NO₂ : CAMS brut, moyenne des 7 derniers résidus disponibles,
EWMA et Kalman local-level. Apprendre un seul rapport `q/r` national, puis éventuellement
un rapport par typologie seulement si la variante nationale passe. Ne pas ajuster un
`q/r` par station dans ce délai.

Découpage :

- estimation des paramètres : 2023-08-01 → 2025-07-31 ;
- validation de `q/r` ou `alpha` : 2025-08-01 → 2025-10-31 ;
- test préquentiel : 2025-12-01 → 2026-07-31, novembre 2025 exclu ;
- à chaque date, mettre à jour l'état uniquement avec la dernière observation qui aurait
  été disponible à l'heure réelle d'émission ; test principal avec latence 24 h, sensibilité
  avec 48 h ;
- en cas de mesure manquante, étape de prédiction sans mise à jour, sans imputation future.

```powershell
python scripts/banc_kalman_biais.py `
  --polluant NO2 --horizon 2 `
  --train-fin 2025-07-31 --validation-fin 2025-10-31 `
  --test-debut 2025-12-01 --test-fin 2026-07-31 `
  --latences-heures 24 48 --baselines moyenne7 ewma kalman `
  --bootstrap-mois 1 2 --clusters-stations 20 --tirages 10000 `
  --checkpoint reports/kalman_NO2_etat.json
```

### Seuil de décision

Déployer Kalman seulement si, contre la meilleure de `moyenne7` et `ewma` :

- gain RMSE ≥ 1,0 % à latence 24 h ;
- borne basse IC 95 % > 0 pour blocs d'un et deux mois ;
- aucune dégradation > 2 % dans une typologie ;
- gain non négatif à latence 48 h ;
- meilleure adaptation durant les 30 premiers jours de U10, sans réglage sur ces jours.

Si Kalman égale l'EWMA, déployer l'EWMA : elle possède le même cœur adaptatif avec moins de
paramètres, moins de modes d'échec et une explication plus simple.

**Coût : 5 h** — environ 3 h d'implémentation et contrôles anti-fuite, 1 h de calcul,
1 h de bootstrap et rédaction.

**Si le test échoue, écrire :**

> Sur la variante AUX STATIONS, un filtre d'état du biais a été comparé en préquentiel à la
> moyenne glissante 7 jours et à une moyenne exponentielle, avec la latence observationnelle
> opérationnelle. Il n'apporte pas au moins 1 % de RMSE de façon stable ; la fenêtre fixe
> demeure donc le choix le plus robuste.

## 6. Exécution sous la contrainte de quatre jours

### Budget ferme de 32 heures

| tâche | plafond |
|---|---:|
| Durcir et vérifier le PDF | 3 h |
| Corriger le tableau neuronal et lancer le test apparié | 4 h |
| Audit des ruptures CAMS | 6 h |
| Télécharger/extracter le complément de spéciation | 2 h |
| Garde puis éventuelle ablation de spéciation | 8 h |
| Banc Kalman `AUX STATIONS` | 5 h |
| Intégration, contrôle des artefacts et rédaction | 4 h |
| **Total** | **32 h** |

Le leave-one-out de spéciation ne dispose donc que des heures restantes dans son enveloppe :
s'il menace le plafond, publier le test groupé `base/core5/core7` et s'arrêter. Il vaut mieux
une conclusion de bloc valide qu'une attribution par variable inachevée.

### Règles de reprise imposées par l'instabilité de la machine

- une ligne CSV ou Parquet écrite après chaque pli ;
- un manifeste JSON atomique listant les plis terminés et leur empreinte de données ;
- aucune commande de calcul de plus de deux heures sans reprise ;
- graines, groupes géographiques et dates écrits dans l'artefact, pas seulement dans le code ;
- une configuration incomplète n'entre ni dans une moyenne ni dans un intervalle ;
- le PDF n'est généré qu'à partir des CSV finaux validés.

### Conclusion à porter dans le dossier si les deux chantiers scientifiques échouent

> Deux hypothèses ciblées ont été falsifiées sous protocole prospectif et spatialement
> bloqué : les traceurs CAMS de composition n'ont pas fourni de gain stable entre versions,
> et les ruptures apparentes n'ont pas pu être attribuées aux mises à jour plutôt qu'à la
> saison. Ces résultats négatifs bornent le produit : sans observation récente, il corrige
> les biais structurés de CAMS mais ne recrée pas les innovations d'épisode. Nous avons
> conservé les composants simples dont le gain est reproductible et documenté les pistes
> non mesurées plutôt que de les présenter comme des améliorations acquises.
