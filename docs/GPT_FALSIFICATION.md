# Q1 — Antériorité

**Verdict : le noyau de la thèse est déjà publié ; les parties « elle gagne quand le forçage dérive », « observable à l’émission » et « corrigeable par abstention » ne le sont pas démontrées par cette antériorité.**

Le problème porte un nom général : **non-stationnarité de l’erreur du modèle amont**, ou *dataset/concept shift* du post-processeur après changement du système générateur. En météorologie, Demaeyer et Vannitsem écrivent explicitement qu’un changement du modèle de prévision rend les schémas de post-traitement moins efficaces et motive soit des reforecasts homogènes, soit une adaptation des coefficients. C’est presque exactement le mécanisme général revendiqué ici : Demaeyer et Vannitsem (2020), *Nonlinear Processes in Geophysics*, DOI : [10.5194/npg-27-307-2020](https://doi.org/10.5194/npg-27-307-2020).

Hamill (2017) montre que des changements du modèle et de l’assimilation modifient les caractéristiques statistiques des erreurs et compliquent l’usage des reforecasts pour le post-traitement, lequel suppose une erreur approximativement stable d’une année à l’autre : *Monthly Weather Review*, DOI : [10.1175/MWR-D-17-0067.1](https://doi.org/10.1175/MWR-D-17-0067.1). Un post-processeur adaptatif conçu précisément pour incorporer rapidement de nouvelles entrées ou mises à niveau du modèle amont est évalué par Roebber (2021), *Monthly Weather Review*, DOI : [10.1175/MWR-D-21-0089.1](https://doi.org/10.1175/MWR-D-21-0089.1).

L’antériorité existe aussi en qualité de l’air sur un point voisin : l’analogue de correction du système NOAA améliore la moyenne mais réduit la variabilité quotidienne et peut échouer sur les extrêmes non représentés, notamment feux d’artifice et fumées d’incendies. Huang et al. (2017), *Weather and Forecasting*, DOI : [10.1175/WAF-D-16-0118.1](https://doi.org/10.1175/WAF-D-16-0118.1).

Enfin, CAMS applique déjà cette logique à son propre MOS : sa documentation annonce qu’un changement d’un membre de l’ensemble ou des stations entraîne rapidement un nouveau modèle de correction ([documentation officielle CAMS MOS](https://confluence.ecmwf.int/x/WpwfHg), sans DOI). Les mises à niveau U9 du système régional sont bien documentées le **13 novembre 2024** — émissions et adaptation au cycle 49r1 — puis le **3 décembre 2024** — ajout de trois espèces ([annonce CAMS U9](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219), sans DOI).

L’élément éventuellement propre au projet n’est donc pas la thèse générale. Ce serait, au mieux, une **étude de cas CAMS Europe** montrant hors échantillon qu’un indicateur disponible avant observation prévoit le signe de la valeur ajoutée. Cette dernière démonstration n’existe pas encore.

# Q2 — Contre-explication

**Verdict : les trois « preuves » sont compatibles avec des explications plus simples et ne sont pas indépendantes.**

Premièrement, le gain relatif

\[
G=1-\frac{\mathrm{RMSE}_{corr}}{\mathrm{RMSE}_{CAMS}}
\]

contient précisément la RMSE CAMS qui sert aussi à définir sa « dégradation ». La corrélation entre ces deux quantités est donc exposée au **couplage mathématique** : même si la RMSE corrigée restait constante, une hausse du dénominateur ferait monter mécaniquement \(G\). Corréler un changement ou un pourcentage de changement à sa valeur de départ est un problème classique ; voir Tu (2016), *Scientific Reports*, DOI : [10.1038/srep23247](https://doi.org/10.1038/srep23247), et Moreno et al. (1986), *Journal of Applied Physiology*, DOI : [10.1152/jappl.1986.60.1.335](https://doi.org/10.1152/jappl.1986.60.1.335). La dépendance d’un skill score à sa référence est également discutée par Wheatcroft (2019), *International Journal of Forecasting*, DOI : [10.1016/j.ijforecast.2018.11.010](https://doi.org/10.1016/j.ijforecast.2018.11.010).

Deuxièmement, si « à saison égale » signifie août–décembre 2023 contre août–décembre 2024, la corrélation +0,913 repose sur **cinq paires mensuelles**. Elle est trop petite, sensible au retrait d’un mois et choisie après observation pour porter une thèse causale. Le test minimal est de publier \(n\), les cinq points, la corrélation leave-one-out et un intervalle bootstrap par mois.

Troisièmement, « six configurations ont le même pire mois » est de la **pseudo-réplication** : elles partagent les mêmes observations, le même CAMS, les mêmes stations et des modèles proches. Novembre 2023 peut simplement être un régime peu favorable aux corrections régressant vers la moyenne. Le résultat structural et la corrélation mensuelle proviennent d’ailleurs du même jeu de données ; ce ne sont pas deux preuves indépendantes.

Quatrièmement, le 26 juillet est un contre-exemple utile mais choisi après coup. Un cas ne distingue pas une dérive du modèle amont, une correction trop lissante, un événement fumées absent des variables, ou une erreur locale. Il contient aussi une incohérence réglementaire : **49,6 µg/m³ n’est pas un dépassement du seuil PM₁₀ de 50 µg/m³ en moyenne journalière**, sauf règle d’arrondi ou agrégation zonale documentée ; voir Code de l’environnement, article R.221-1 ([Légifrance](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000022964539)). La règle proposée n’aurait donc pas nécessairement été déclenchée par son propre cas fondateur.

Le test qui tranche avec les données existantes est le suivant :

1. remplacer le gain relatif par la différence absolue hors pli  
   \(\Delta L=(y-\hat y_{CAMS})^2-(y-\hat y_{corr})^2\) ;
2. montrer séparément la RMSE CAMS, la RMSE corrigée et \(\Delta L\), sans ratio ;
3. utiliser une validation **préquentielle** — entraînement uniquement sur le passé — car cacher un mois tout en entraînant sur des mois futurs ne simule pas une rupture opérationnelle ;
4. autour des 13 novembre et 3 décembre, comparer des fenêtres symétriques préfixées et les mêmes saisons, puis tester une rupture de \(\Delta L\), pas seulement de CAMS ;
5. construire un nul : correcteur fixe ou simple débiaisage, erreurs CAMS rééchantillonnées par mois, puis mesurer combien de simulations produisent une corrélation ≥0,913 ;
6. apprendre, uniquement dans les plis internes, la probabilité que \(\Delta L>0\) à partir de variables disponibles à l’émission, puis l’évaluer sur un mois totalement futur.

Si la corrélation disparaît en différence absolue, apparaît souvent sous le nul, ou si l’indicateur d’émission ne discrimine pas les corrections utiles, l’explication « régression vers la moyenne + couplage mathématique » suffit.

# Q3 — Portée

**Verdict : le risque est général, mais la loi « tout post-traitement gagne quand l’amont dérive et nuit quand il est juste » est fausse.**

Tout post-processeur appris suppose une certaine stabilité de \(P(Y\mid X)\). Un changement du modèle amont peut rompre cette relation ; les publications de Demaeyer et Vannitsem et de Hamill établissent ce risque. Elles ne disent cependant pas que la dérive **augmente** nécessairement le gain. Au contraire, leur problème de départ est qu’un post-traitement ajusté à l’ancien système devient moins efficace après une mise à niveau. Il ne gagne sur une dégradation nouvelle que si la correction ancienne reste fortuitement orientée dans le bon sens.

La formulation mathématique de la thèse est également trop forte. Un LightGBM de résidu sous perte quadratique apprend une approximation de la **moyenne conditionnelle** du résidu, pas sa distribution conditionnelle complète. Et il ne l’applique pas « inconditionnellement » : il la conditionne aux 52 variables fournies. Ce qui est appliqué hors domaine est une fonction conditionnelle apprise sous l’ancienne distribution.

PREV’AIR ou le MOS CAMS ne peuvent pas être assimilés au dispositif présenté sans connaître leur fenêtre d’apprentissage, leur fréquence de réentraînement, leurs observations récentes, leurs contrôles et l’intervention humaine. La documentation CAMS indique précisément une reconstruction rapide du MOS lorsque le système change. **Inconnu** pour les mécanismes internes équivalents de PREV’AIR.

Le projet possède au contraire plusieurs particularités susceptibles d’expliquer seul l’échec :

- 17 mois seulement et environ 1,5 cycle saisonnier ;
- modèle résiduel optimisé sous erreur quadratique, donc attiré vers les cas fréquents ;
- absence d’observations récentes de la station ;
- ERA5 réanalysée plutôt que météo disponible à l’émission ;
- évaluation temporelle pouvant employer des mois futurs si le pli ne masque qu’un mois ;
- événement fumées potentiellement hors support de l’apprentissage ;
- sélection a posteriori du cas et de la règle.

La portée défendable est donc : « ce correcteur précis présente une valeur ajoutée très dépendante du mois et du niveau d’erreur CAMS ». Généraliser à PREV’AIR ou à toute chaîne opérationnelle demande au minimum une seconde chaîne, une mise à niveau prospective et un protocole commun.

# Q4 — Inutilité et règle d’abstention

**Verdict : la règle actuelle est trop grossière et son exemple fondateur ne franchit même pas littéralement le seuil de 50 µg/m³.**

« Ne jamais corriger à la baisse quand CAMS annonce un dépassement » préserve les vraies alertes, mais préserve aussi les fausses alertes et interdit de corriger un biais positif connu. Elle introduit une discontinuité au seuil : 49,9 peut être fortement abaissé tandis que 50,1 est intouchable. Elle a en outre été conçue après lecture du 26 juillet ; l’évaluer sur ce même jour est circulaire.

L’abstention est une idée publiée sous les noms *selective prediction*, *reject option* et courbe **risque–couverture**. Elle échange couverture contre risque ; voir Shah et al. (2022), *Proceedings of Machine Learning Research* 162, [publication sans DOI](https://proceedings.mlr.press/v162/shah22a.html), et Franc, Průša et Voráček (2023), *Journal of Machine Learning Research* 24, [publication sans DOI](https://www.jmlr.org/papers/v24/21-0048.html). Cette antériorité rend l’abstention méthodologiquement recevable, mais ne valide pas le seuil CAMS proposé.

Un critère défendable doit prédire le **risque conditionnel de la correction**, pas utiliser la concentration brute comme substitut de sa justesse :

\[
\text{corriger si }
\mathbb E[L_{corr}-L_{CAMS}\mid X_{\mathrm{émission}}] < -\lambda,
\]

où \(X_{\mathrm{émission}}\) peut inclure concentration CAMS, distance au domaine d’apprentissage, dispersion de l’ensemble CAMS, régime météo, valeurs manquantes, cycle amont et désaccord entre plusieurs correcteurs. Le système revient à CAMS sinon. \(\lambda\) représente le coût asymétrique fixé avant évaluation.

Pour rendre la règle crédible :

1. fixer avant test la perte métier — par exemple coût d’un épisode manqué supérieur à celui d’une fausse alerte ;
2. produire toutes les décisions de garde hors pli, avec seuil choisi seulement dans les plis internes ;
3. comparer quatre politiques : toujours CAMS, toujours corrigé, règle « dépassement », sélecteur de risque ;
4. publier RMSE, POD, FAR, Brier score et courbe risque–couverture ;
5. exiger que le garde-fou améliore le pire mois et les épisodes sans dégrader significativement le score global ;
6. valider prospectivement sur des dates postérieures à décembre 2024, sans choisir les cas après observation.

Critère de falsification simple : si la règle « dépassement » n’améliore pas le coût hors pli par rapport à « toujours corrigé », ou si le sélecteur ne classe pas mieux les corrections nuisibles que la prévalence de base, l’abstention n’est pas encore actionnable.

# Verdict final

***La thèse est fausse dans sa formulation actuelle.*** Son noyau modeste — un post-processeur dépend de la stabilité statistique du modèle amont — est déjà publié. Le sens causal « il gagne quand CAMS dérive », l’observabilité à l’émission et l’efficacité de la règle d’abstention ne sont pas établis. La corrélation +0,913 est contaminée par le gain relatif et probablement fondée sur très peu de mois ; les six configurations ne sont pas des répétitions indépendantes ; le cas du 26 juillet est unique, postérieur au choix narratif et situé sous le seuil PM₁₀ de 50 µg/m³.

Une thèse plus étroite pourrait survivre : **« la valeur ajoutée de ce correcteur CAMS est temporellement instable ; un garde-fou appris hors pli peut éventuellement réduire son risque de nuisance »**. Mais le garde-fou doit encore être construit et falsifié prospectivement.
