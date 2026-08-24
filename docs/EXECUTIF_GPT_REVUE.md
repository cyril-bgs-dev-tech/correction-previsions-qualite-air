# Arbitrage exécutif de la nuit autonome

## Verdict en une phrase

Cette nuit est un **succès de récupération et de fiabilisation**, mais un **échec du plan de découverte initial** et une **alerte sur la maîtrise du travail en cours**.

Le ratio 47 commits de correction ou de garde pour 13 commits de résultat n’est ni bon ni mauvais en soi. Il est justifié **après la découverte du corpus troué**, parce que continuer aurait multiplié des mesures non transposables. Il serait excessif comme régime normal : 78 % de commits défensifs, +5 443 lignes sur 46 fichiers, six interruptions de files et deux chaînes cassées ne peuvent pas devenir la cadence habituelle d’un opérateur seul.

La réponse directe à la question centrale est donc : **non, la nuit n’a pas été passée à polir inutilement l’instrument ; oui, elle a trop souvent réparé l’instrument pendant qu’il tournait**.

Aucun arbitrage proposé ici ne relâche la contrainte **PARTOUT** : aucune observation de qualité de l’air, directe ou dérivée, n’est ajoutée à l’inférence. L’IFS est priorisé précisément parce qu’il constitue une prévision déployable partout.

Ce verdict était reconnaissable avant la fin dès l’instant où trois faits étaient réunis :

1. le défaut modifiait le support temporel et créait un indicateur d’époque implicite ;
2. les expériences prévues dépendaient toutes de ce même corpus ;
3. la correction pouvait faire changer une décision de famille, pas seulement quelques décimales.

À partir de là, la campagne devait officiellement passer de **découverte** à **récupération d’incident**. Le tort n’a pas été de consacrer la nuit à la récupération ; il a été de continuer à mélanger récupération, nouvelles expériences, développement des gardes et exploitation de deux files actives.

## Jugement des cinq décisions

| Décision | Verdict | Ce qui était juste | Ce qui doit changer |
|---|---|---|---|
| **① Arrêter le programme et régénérer** | **Juste** | Le défaut violait l’identité du corpus et la comparabilité. Même avec un déplacement final nul, les anciennes mesures auraient dû être régénérées avant toute conclusion. | Distinguer « faut-il réparer ? » — oui automatiquement — de « faut-il mobiliser les huit prochaines heures maintenant ? », que peut informer un canari de 30 min. |
| **② Écrire six gardes** | **Globalement défendable, probablement un garde ou deux de trop** | Cinq défauts étaient des récidives de règles écrites ; les mécaniser est cohérent. Les gardes empêchant un faux résultat silencieux, une perte de donnée ou une collision n’ont pas besoin d’avoir déjà déclenché pour être utiles. | Exiger avant écriture un invariant, un scénario d’échec, un coût évité, un test d’évasion, un test de faux positif et une date de réexamen. Pour un risque réversible et bon marché, instrumenter d’abord. |
| **③ Faire tourner CPU + réseau et coder** | **Bonne architecture de ressources, mauvaise discipline de versions** | Une ressource CPU sérialisée et une ressource réseau majoritairement en attente peuvent tourner ensemble. Écrire du code pendant ce temps est rationnel. | Chaque génération de file doit exécuter un instantané immuable. Le développement continue ailleurs ; les correctifs n’entrent que dans la génération suivante, sauf arrêt d’urgence explicite. Six interruptions montrent que cette frontière manquait. |
| **④ Sceller huit prédictions** | **Bonne pratique, mauvaise classification de deux objets** | Sceller les effets attendus avant mesure donne une vraie information de calibration et limite la narration a posteriori. | Un nombre de mois produit par une règle de code n’est pas une prédiction empirique : c’est une assertion à calculer avant lancement. Cinq résolutions sont trop peu pour conclure à un contraste structure/effet. |
| **⑤ Écrire 60 messages narratifs** | **Contenu utile, granularité excessive** | Défaut, impact, cause, correctif et preuve sont exactement ce qu’un ingénieur ou un agent cherchera. | Mettre le récit long dans une fiche de décision ; garder dans Git une unité causale par commit et un corps court. Soixante commits narratifs en douze heures fragmentent plus qu’ils n’expliquent. |

## Question 1 — Quand régénérer tout le corpus ?

### Ici, la régénération était obligatoire avant même de connaître l’amplitude

Le corpus troué ne constituait pas seulement une petite erreur de valeur. Il changeait :

- le support temporel ;
- l’éligibilité de familles ;
- la présence d’un indicateur d’époque implicite ;
- la référence commune de toutes les expériences suivantes.

Un tel défaut est **stop-the-line**. Il invalide la comparabilité par construction. L’effet final de 0,17 à 0,32 point et la chute de deux familles confirment sa matérialité, mais ne sont pas nécessaires pour justifier la correction. Même si le score avait bougé de 0,00 point, la base publiée aurait dû être régénérée pour que cette absence de déplacement soit elle-même démontrée.

La vraie décision exécutive n’était donc pas « réparer ou non ». C’était :

> **Réparer immédiatement pendant huit heures, ou suspendre les conclusions, mesurer l’ordre de grandeur sur un canari, puis ordonnancer la régénération ?**

### Le test bon marché

Avant la régénération complète, lancer un **canari apparié** de 30 minutes :

1. construire l’ancien et le nouveau corpus avec les mêmes identifiants de lignes ;
2. choisir un polluant sensible aux familles trouées et un second polluant témoin ;
3. prendre 6 blocs couvrant au moins deux mois touchés, deux mois adjacents et deux mois propres ;
4. exécuter l’ancre et une configuration sentinelle, mêmes graines et mêmes plis ;
5. mesurer séparément le déplacement de l’ancre, le déplacement de l’apport et les changements d’éligibilité.

Seuil d’ordonnancement proposé :

- si une configuration change d’éligibilité, si un verdict change, ou si le déplacement dépasse **la moitié de la résolution du protocole**, soit environ 0,2 point, interrompre les nouvelles mesures et régénérer tout ;
- si le déplacement reste inférieur à 0,2 point sans changement de support ni d’éligibilité, planifier la régénération avant publication mais ne pas nécessairement monopoliser la nuit ;
- si le défaut touche cible, séparation train/test, observations disponibles à l’inférence ou identité du corpus, ne pas attendre le canari pour invalider les sorties existantes.

Le canari coûte environ 6 % du calcul complet dans les chiffres fournis. Il est rentable s’il peut changer **l’ordre de la file**. Il ne doit pas servir à autoriser la conservation d’un corpus structurellement invalide.

## Question 2 — Quand un garde-fou paie-t-il ?

Un garde n’est pas jugé au nombre de fois où il déclenche. Un détecteur d’incendie peut avoir une valeur sans incendie ; un avertissement bruyant peut être nuisible même s’il sonne souvent.

### Les six conditions avant écriture

Un garde mérite du code si les six réponses sont explicites :

1. **Invariant :** quelle propriété précise doit toujours être vraie ?
2. **Détectabilité :** peut-elle être calculée avant publication ou avant écriture définitive ?
3. **Sévérité :** l’échec produit-il un faux succès silencieux, une donnée perdue, une collision ou plus d’une heure de re-travail ?
4. **Exposition :** combien de prochaines exécutions peuvent rencontrer ce risque ?
5. **Évasion et faux positif :** un cas mauvais est-il refusé, et un cas bon accepté ?
6. **Remplacement :** quelle règle de prose, vérification manuelle ou branche spéciale disparaît grâce au garde ?

Si la sixième réponse est « aucune », le corpus de règles grandit sans simplification : c’est souvent un garde de réassurance.

### Une règle économique simple

Pour un risque non catastrophique :

```text
écrire le garde si
coût de construction + maintenance
< probabilité de récurrence × nombre d’expositions × coût d’une récurrence
```

Les valeurs peuvent rester en classes faible/moyen/fort ; une fausse précision n’est pas utile. Quelques conséquences :

- un garde de 30 minutes qui prévient une nouvelle régénération de 8 h est rentable avec une probabilité de récurrence très modeste ;
- un garde de 90 minutes qui évite une vérification manuelle de 2 minutes ne l’est probablement pas ;
- un garde empêchant un faux résultat silencieux ou une perte irréversible est obligatoire même si son rendement financier est difficile à chiffrer.

### Trois classes opérationnelles

- **Classe A — immédiat :** fuite d’évaluation, donnée définitivement perdue, corruption/collision, faux résultat silencieux.
- **Classe B — après deuxième occurrence :** plus d’une heure de re-travail, panne connue et détectable.
- **Classe C — télémétrie d’abord :** gêne réversible, message imparfait, contrôle de confort.

Les trois mécanismes qui n’ont encore rien attrapé ne sont pas condamnés pour autant. S’ils sont de classe A et testés par injection d’un cas fautif, ils paient déjà par la réduction du risque. S’ils sont de classe C, ils auraient dû commencer comme journal ou alerte, avec promotion en garde bloquant seulement après observation.

La règle « violée deux fois = code ou disparition » reste bonne, à condition d’ajouter : **« un garde codé remplace la règle de prose et porte une date d’expiration ou de réexamen »**.

## Question 3 — Travailler pendant que les files tournent

La bonne discipline n’est ni « geler tout le dépôt pendant huit heures » ni « corriger à chaud ». C’est **geler la génération en cours**.

### Contrat d’une génération

Chaque lancement CPU ou réseau enregistre avant la première tâche :

- empreinte du code ;
- empreinte du corpus et des entrées ;
- liste ordonnée des tâches ;
- paramètres et destinations ;
- identifiant de génération.

La file s’exécute depuis un instantané qui ne change plus. Le développement peut continuer dans un autre espace de travail, mais aucun fichier qu’une tâche future de la génération chargera ne doit muter sous elle.

### Quand interrompre

Interrompre la génération uniquement si le correctif change au moins un des éléments suivants :

- cible ou agrégation ;
- support du corpus ;
- séparation des plis ;
- colonnes réellement servies ;
- référence de comparaison ;
- calcul du score ou verdict ;
- intégrité de l’artefact final.

Dans ce cas, marquer toute la génération `invalidée`, conserver son journal, corriger, puis lancer une nouvelle génération. Pour une amélioration de journal, un message, une optimisation ou un garde non nécessaire à la validité des sorties en cours, laisser finir et appliquer à la génération suivante.

Les six interruptions de la nuit étaient peut-être chacune défendables isolément ; ensemble, elles prouvent que la file n’avait pas de contrat de génération. Les deux chaînes cassées par du Python qu’elles allaient charger sont précisément le défaut qu’un instantané immuable élimine.

### Limite de travail en cours

Pour un opérateur seul :

- une génération CPU ;
- une génération réseau ;
- une seule modification active susceptible de créer la génération suivante.

Toute nouvelle découverte va dans une file de corrections. Elle ne devient active qu’après classement stop-the-line/non bloquant.

## Question 4 — Que disent les cinq prédictions résolues ?

**Presque rien sur une différence générale entre structure et effets.** Deux échecs contre trois réussites sur cinq points peuvent être du bruit, et les objets n’étaient pas comparables.

Le contraste révèle surtout une erreur de catégorie :

- « combien de mois cette règle de code va produire » doit être évalué exactement par un préflight ou un test ;
- « cette famille apportera-t-elle au moins 0,4 point » est une incertitude empirique légitime.

Il ne faut donc ni moins prédire sur la structure, ni multiplier artificiellement ces prédictions. Il faut **cesser de les appeler prédictions** et les convertir en assertions exécutables.

Pour les effets, continuer le registre avec :

- direction et intervalle de magnitude attendus ;
- degré de confiance explicite, pas seulement vrai/faux ;
- critère précis de résolution ;
- date de scellement ;
- résultat et écart à l’attendu.

N’interpréter la calibration qu’après au moins une vingtaine de prédictions empiriques comparables. Avant cela, afficher les cas individuellement. Le signal actuel est encourageant — les prédictions d’effets ont été utiles — mais insuffisant pour affirmer une calibration 60 % ou une supériorité de jugement sur les effets.

## Question 5 — Quelle forme pour les commits ?

Le lectorat visé bénéficie de la causalité narrative, mais pas nécessairement dans chaque commit. Un ingénieur veut retrouver : pourquoi cela a changé, quel chiffre est affecté, quel garde empêche le retour et comment cela a été vérifié. Un agent le retrouvera mieux dans une structure stable que dans vingt lignes libres répétées soixante fois.

### Forme courte recommandée

```text
Sujet : Le corpus incomplet encodait cinq mois par leur absence

Invariant : toute famille du socle couvre chaque mois du périmètre.
Impact    : base déplacée de +0,17 à +0,32 pt ; 2 verdicts changent.
Correctif : rattrapage puis empreinte de couverture avant mesure.
Vérifié   : 312 tests ; décision DEC-2026-08-24-03.
```

Règle de taille :

- sujet causal ;
- quatre lignes de corps pour une correction ordinaire ;
- fiche de décision séparée pour une modification de protocole, un verdict renversé ou un incident coûteux ;
- un commit par unité causale et vérifiable, pas par micro-étape ni par narration chronologique.

Les 60 commits auraient probablement dû devenir environ **15 à 20 unités causales** : 13 résultats et 6 mécanismes constituent déjà une borne naturelle, avec regroupement lorsqu’un garde et son défaut sont indissociables. Le détail de la nuit appartient au journal ou aux fiches de décision, pas à la première vue de `git log`.

Pour une branche locale non partagée, condenser les micro-commits avant publication est préférable. Une correction scientifique déjà partagée doit rester un nouveau commit explicite.

## Question 6 — Ordre des trois prochains objectifs

L’ordre actuel **IFS → chimie → propreté d’époque** n’est pas défendable si IFS est mesuré sur la même base sale qui obligera à le mesurer de nouveau. Mais « finir la propreté » ne signifie pas forcément télécharger immédiatement tous les mois manquants de toutes les familles.

### Ordre recommandé

1. **Geler une référence propre immédiatement.** Utiliser le périmètre complet commun et exclure mécaniquement toute famille avec mois entier absent. Empreinte et rapport de couverture verts. Les rattrapages peuvent continuer en réseau sans entrer dans cette référence.
2. **Cribler IFS sur cette référence propre.** C’est la seule piste qui ajoute une information physique absente et ses gains antérieurs dépassent largement la résolution ±0,4 point. C’est le meilleur rendement informationnel.
3. **Confirmer IFS en pile complète propre** s’il franchit le criblage, sans modifier la génération en cours.
4. **Mesurer chimie + précurseurs conjointement.** Le recouvrement R² 0,42–0,62 et le bénéfice limité à O₃ rendent cette question moins urgente et moins susceptible d’une promotion multi-polluants.
5. **Réintégrer les familles rattrapées en un seul lot de confirmation**, pas à chaque mois récupéré. `feux`, avec 34 % de mois absents tous en 2025, reste hors référence tant que son support n’est pas propre.

En parallèle, acquérir les archives IFS ou CAMS qui risquent de se fermer, mais ne pas les laisser changer la référence avant la génération suivante.

Le principe exécutif est : **propreté minimale par exclusion d’abord, information neuve ensuite, restauration des familles optionnelles en parallèle**. Cela évite de passer plusieurs jours à consolider des familles faibles avant de tester la seule source susceptible de déplacer le plancher.

## Question 7 — Succès, échec, et mesure à suivre

### Le bon bilan

La nuit a réussi trois choses de grande valeur :

- elle a retiré de la performance apparente ;
- elle a renversé deux décisions de familles ;
- elle a rendu plusieurs classes de panne détectables avant publication.

Elle a échoué sur deux objectifs opérationnels :

- aucune famille nouvelle n’a été décidée ;
- le coût de reprise a été gonflé par six interruptions et deux chaînes cassées.

La formulation honnête est donc :

> **Succès de validité, zéro progrès de score, faible efficacité d’exploitation.**

Ce n’est pas un échec scientifique. Découvrir que deux familles « démontrées » ne le sont plus produit davantage d’information décisionnelle qu’un dixième de point supplémentaire. Ce serait un échec si la prochaine nuit répétait le même ratio après que la référence propre et les mécanismes sont stabilisés.

### Le tableau de bord à déclarer avant chaque bloc de travail

| Mesure | Définition | Cible pour le prochain bloc de 8 h |
|---|---|---:|
| **Décisions résolues** | familles ou hypothèses passant de « inconnue » à TIENT / RÉSERVE / SAUTE sur un corpus valide | ≥1 décision principale |
| **Dette de confiance ouverte** | invariants rouges pouvant invalider une conclusion publiée | 0 avant toute nouvelle promotion |
| **Débit expérimental fiable** | expériences quatre polluants terminées sur une même empreinte de corpus | ≥1 famille / 2 h une fois la base verte |
| **Taxe de reprise** | calcul jeté ou répété à cause d’une modification de génération | <10 % du temps machine |
| **Travail en cours** | générations actives + changements susceptibles de les invalider | 1 CPU + 1 réseau + 1 changement |
| **Rendement des gardes** | règles manuelles supprimées et classes de faux succès désormais impossibles | chaque garde supprime ≥1 règle |
| **Surface ajoutée** | fichiers et lignes ajoutés pour obtenir une décision | tendance décroissante ; revue si >10 fichiers par décision |
| **Échappements** | conclusions annoncées puis corrigées substantiellement | 0 |

La métrique principale n’est donc ni le nombre de résultats ni le nombre de défauts. C’est le nombre de **décisions rendues fiables par unité de temps**, accompagné de la dette de confiance et de la taxe de reprise.

Un défaut trouvé compte comme progrès seulement s’il ferme ou requalifie une décision réelle. Un garde compte comme progrès seulement s’il retire une vérification humaine ou empêche une classe de faux succès. Un résultat compte comme progrès seulement s’il porte la même empreinte de corpus que sa référence.

## Règle de répartition pour les prochaines sessions

Avant chaque bloc de huit heures, annoncer un mode unique :

### Mode découverte — référence verte

- 70 % mesure et analyse ;
- 20 % intégration/automatisation nécessaire ;
- 10 % documentation et consolidation ;
- bascule immédiate en récupération si un invariant critique devient rouge.

### Mode récupération — référence rouge

- 60 % correction et régénération ;
- 20 % canaris et vérifications ;
- 10 % gardes de classe A/B ;
- 10 % documentation ;
- aucune nouvelle promotion de famille.

Ces pourcentages sont des plafonds de gouvernance, pas des objectifs de remplissage. La nuit décrite devait passer en mode récupération à la troisième heure. Ses 47 commits défensifs deviennent alors compréhensibles. Mais le mode devait aussi imposer : une génération immuable, une seule réparation active, et aucune nouvelle famille avant retour au vert.

## Décision pour demain matin

1. Déclarer la récupération terminée seulement si la référence propre a une empreinte stable et zéro mois entier absent dans ses familles admises.
2. Laisser les rattrapages réseau continuer dans une génération figée.
3. Ne plus modifier les files actives ; préparer la génération suivante séparément.
4. Lancer le canari IFS, puis la mesure complète si son effet dépasse la résolution ou change une décision.
5. Reporter chimie + précurseurs après IFS.
6. Transformer les deux « prédictions structurelles » manquées en assertions de préflight.
7. Condenser l’histoire de la nuit en une fiche exécutive et 15–20 unités causales lisibles, sans effacer les corrections déjà partagées.

Si la prochaine session propre consacre encore plus de la moitié de son temps à de nouveaux gardes sans qu’un invariant critique ait été violé, alors oui : ce sera le signe que la rigueur est devenue une forme de procrastination technique. Cette nuit-ci n’a pas encore franchi cette ligne ; elle l’a approchée par la façon dont les correctifs ont été intégrés pendant l’exécution.
