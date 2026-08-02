# Prompt GPT — R12 · La détection, et rien d'autre

> À coller tel quel. Rédigé le 02/08/2026.
> R11 portait sur les données et le réglage. Celui-ci porte sur **la seule chose qui compte
> en opérationnel : ne pas manquer un épisode**. Et sur un résultat qui me fait douter.

---

## Le contexte, en huit lignes

Post-traitement statistique des prévisions **CAMS Europe** sur les stations françaises. Le
modèle apprend le résidu `observation − CAMS` à J0 (1-24 h), cible journalière, LightGBM, corpus de
36 mois.

L'évaluation la plus dure cache **simultanément la station et le mois** — c'est la condition
de déploiement : une station nouvelle, une date future. J'appelle ça le « double aveugle ».

En **erreur quadratique**, la correction gagne partout : NO₂ +36,7 %, O₃ +6,9 %, PM2,5 +4,5 %.

En **détection d'épisode**, j'ai un problème.

---

## Question 1 — La correction améliore la RMSE et dégrade peut-être les extrêmes

**Le fait mesuré.** Sur un protocole où seules les stations sont exclues, notre correction
détecte, **à précision égale au produit officiel, 1,7× à 4,1× plus de dépassements**.

Sur le double aveugle — stations **et** mois cachés — la même comparaison a rendu **×0,85**,
c'est-à-dire un renversement complet. Le détecteur testé n'était pas identique (un classifieur
au lieu du score du régresseur), donc je dois refaire la mesure. Mais l'hypothèse que je
veux tester d'abord est physique, pas technique :

> Un modèle ajusté sur une perte quadratique **rétrécit vers la moyenne**. Sur une station
> jamais vue, il ne sait pas de combien elle s'écarte du comportement moyen, donc il rétrécit
> davantage. La correction améliorerait alors le centre de la distribution en **écrasant la
> queue** — exactement ce qu'il ne faut pas pour une alerte.

**Ce que je demande.**

1. Ce phénomène est-il **documenté** en post-traitement de prévision ? Je cherche des travaux
   montrant qu'une correction statistique **améliore l'erreur moyenne tout en dégradant la
   détection d'extrêmes**, en météorologie ou en qualité de l'air. Avec chiffres.
2. Existe-t-il une **caractérisation quantitative du rétrécissement** — pente de régression
   du prédit sur l'observé, ratio des variances, diagramme de fiabilité conditionné aux
   valeurs hautes — qui soit l'outil standard pour le diagnostiquer ?
3. Quelles **corrections publiées** préservent la queue : perte quantile ou pinball,
   régression quantile non croisée, EMOS / *non-homogeneous Gaussian regression*, inflation
   de variance, recalibration isotone conditionnelle, apprentissage direct d'une probabilité
   de dépassement ? Lesquelles ont **démontré** un gain de détection sans perdre en RMSE,
   et de combien ?
4. Existe-t-il une notion établie de **compromis explicite** entre exactitude moyenne et
   exactitude de queue — une frontière qu'on documente plutôt qu'un réglage qu'on choisit ?

## Question 2 — Évaluer un détecteur sous blocage conjoint station × période

**Le fait mesuré.** Nos épisodes sont rares et **très inégalement répartis** : certains mois
en concentrent la majorité. Quand je cache un mois entier, le pli de test peut contenir
zéro dépassement, ou en contenir beaucoup. Les métriques de détection deviennent alors
instables d'une façon dont je ne sais pas si elle est un artefact ou un signal.

**Ce que je demande.**

1. Quelle est la **pratique recommandée** pour estimer une performance de détection d'événement
   rare sous validation croisée **groupée** ? Faut-il agréger les prédictions de tous les plis
   avant de calculer la métrique (*pooling*), ou calculer par pli puis moyenner ? Ces deux
   choix donnent des réponses différentes et je ne sais pas lequel est défendable.
2. Comment traiter les **plis sans aucun événement positif** ? Les exclure biaise ; les
   compter comme échec ou succès biaise autrement.
3. Quelles **métriques** sont les plus robustes à un taux de base variable — aire sous la
   courbe précision-rappel, score de compétence, indice de succès critique, score de Peirce,
   score de Brier décomposé ? Les valeurs d'AUC-PR se comparent-elles seulement à taux de
   base égal, et comment le normalise-t-on ?
4. Comment construire un **intervalle de confiance** honnête sur un rappel estimé à partir de
   30 événements répartis sur 36 plis groupés ? Bootstrap par station, par mois, par bloc ?

## Question 3 — Comment les organismes de surveillance vérifient-ils réellement leurs prévisions ?

**Pourquoi je le demande.** Je prépare une candidature à une association agréée de surveillance
de la qualité de l'air. Comparer mon système au leur n'a de sens que **sur leurs métriques et
leur protocole**. Je ne veux pas gagner sur un critère que personne n'utilise.

**Ce que je demande.**

1. Quelles **métriques de vérification** sont réellement employées pour les prévisions
   opérationnelles de qualité de l'air en France et en Europe — PREV'AIR, les AASQA, le
   service européen CAMS ? Je cherche les documents de vérification publiés, avec les valeurs
   effectivement atteintes.
2. Le cadre **FAIRMODE** définit-il des critères de qualité de modèle applicables à la
   **prévision** — indicateur de qualité de modèle, objectifs et critères de qualité des
   données, diagramme cible ? Comment se calcule l'incertitude de mesure qui y entre ?
3. Existe-t-il des **scores de détection d'épisode publiés** par ces organismes — probabilité
   de détection, taux de fausse alerte, indice de succès critique — auxquels je puisse me
   comparer honnêtement ? Sur quel horizon et quel seuil ?
4. Quelle **performance est considérée acceptable** en interne pour déclencher une procédure
   préfectorale ? Y a-t-il une doctrine écrite sur l'arbitrage entre manquer un épisode et
   déclencher à tort ?

## Question 4 — Évaluer la **décision**, pas la prévision

**L'idée à valider.** Une AASQA ne publie pas une RMSE : elle décide de déclencher ou non une
procédure. Les coûts sont asymétriques — une alerte manquée et une fausse alerte n'ont pas le
même prix. En météorologie, la **valeur économique relative** d'une prévision en fonction du
rapport coût/perte de l'utilisateur me semble le cadre exactement adapté, et bien plus parlant
qu'une courbe précision-rappel.

**Ce que je demande.**

1. Le cadre **coût-perte** et la **courbe de valeur économique relative** sont-ils la référence
   pour évaluer l'utilité décisionnelle d'une prévision probabiliste ? Quelles sont les
   références fondatrices et les formulations exactes ?
2. Ce cadre a-t-il été **appliqué à la qualité de l'air** ou aux alertes sanitaires ? Avec
   quels rapports coût/perte plausibles pour une alerte de pollution — coût d'une restriction
   de circulation contre coût sanitaire d'un épisode non annoncé ?
3. Existe-t-il des travaux sur la **valeur des alertes de pollution** — impact sanitaire évité,
   observance du public, effet de la répétition des fausses alertes sur la crédibilité ? Le
   phénomène de « lassitude d'alerte » est-il quantifié ?
4. Quelle est la bonne façon de présenter un système qui **dominerait sur une plage de rapports
   coût/perte** sans dominer partout ? Est-ce défendable, ou est-ce un habillage d'un gain
   partiel ?

## Question 5 — Le seuil réglementaire, où nous sommes aveugles

**Le fait mesuré.** Au seuil d'information français de **180 µg/m³** sur l'ozone, nous
détectons **3 dépassements sur 32**. Notre avantage porte sur un point de fonctionnement
beaucoup plus bas. Nous l'écrivons contre nous dans le dossier.

**Ce que je demande.**

1. Que fait-on, en pratique, quand l'événement d'intérêt est **trop rare pour être appris** ?
   Existe-t-il des approches établies — apprentissage sur un seuil plus bas puis extrapolation,
   théorie des valeurs extrêmes, modèle de dépassement de seuil conditionnel, rééquilibrage —
   dont l'apport soit **mesuré** et pas seulement proposé ?
2. La **théorie des valeurs extrêmes** appliquée aux dépassements de qualité de l'air a-t-elle
   produit des systèmes opérationnels ? Avec quel gain sur quel horizon ?
3. Est-il légitime, et est-ce pratiqué, de **remplacer le seuil par un rang** — annoncer les
   N journées les plus à risque plutôt que celles dépassant une valeur ? Comment cela
   s'articule-t-il avec une obligation réglementaire exprimée en concentration ?
4. Contre-question : y a-t-il des travaux montrant qu'à ce niveau de rareté, **aucune méthode
   ne bat la prévision déterministe brute** ? Si c'est le cas, je préfère l'écrire.

---

## Contraintes de réponse

- **Cite tes sources** — article, année, revue ou organisme, lien. Sans source, inutilisable.
- **Précise le protocole d'évaluation de chaque chiffre cité.** Une détection mesurée sur
  stations vues n'est pas comparable à la nôtre, et c'est précisément le piège où je suis
  tombé.
- **Distingue** l'établi, le débattu, et ton extrapolation.
- **Dis-moi quand la réponse est « rien de probant ».** Sur les questions 1 et 5 en
  particulier, un résultat négatif documenté vaut plus qu'une piste.
- **Priorise ce qui est testable en 48 h** sur un corpus de 36 mois déjà constitué, sans
  nouvelle donnée. Le calendrier est court et la mesure prime sur la lecture.
