# Structurer le projet quand toute correction amont invalide l’aval

## Décision exécutive

Le problème n°1 rend temporairement les six autres secondaires : **le projet n’a pas encore figé un estimand principal indépendant des familles candidates**. Tant qu’une nouvelle source peut raccourcir la fenêtre qui définit le score publié, le corpus, la puissance, les apports et le chiffre principal changent de question en même temps.

La priorité n’est donc pas un nouveau mécanisme statistique. C’est un contrat de produit :

> **Le chiffre principal décrit un socle auditable PARTOUT sur une fenêtre canonique fixée avant les candidats. Une famille à couverture plus courte devient un module optionnel ; elle ne raccourcit jamais rétroactivement cette fenêtre et son absence n’entre jamais comme feature.**

Les empreintes de corpus, d’entrées, le préflight et le contrat de génération sont la bonne architecture. Il ne faut pas inverser les dépendances ni chercher une ancre « insensible au corpus » : si les lignes d’apprentissage ou d’évaluation changent, l’effet relatif peut changer lui aussi. L’invalidation est parfois le résultat correct ; l’objectif est de la rendre explicite, ciblée et peu coûteuse.

Ordre recommandé :

1. figer produit, fenêtre et chiffre principal ;
2. versionner un benchmark propre et immuable ;
3. ouvrir un registre exhaustif avant tout nouveau criblage ;
4. recalibrer la règle de décision sous la puissance réelle ;
5. organiser les familles en groupes de déploiement ;
6. produire l’enveloppe de stabilité des scores absolus ;
7. simplifier le dossier autour de quatre chiffres principaux.

Aucune proposition ne relâche la contrainte **PARTOUT** : aucune observation de qualité de l’air n’est ajoutée à l’inférence.

## Architecture cible

```text
CONTRAT DE PRODUIT
auditable · PARTOUT · fenêtre canonique · métrique · plus petit effet utile
        │
        ▼
SNAPSHOT IMMUABLE DU CORPUS
manifestes de sources · couverture · empreintes · plis · cibles
        │
        ├──────────────► SOCLE TOUJOURS DISPONIBLE ──► chiffre principal
        │
        └──────────────► MODULES OPTIONNELS
                         GEOS-CF v1 · IFS incomplet · feux…
                         évalués appariés sur leur support propre
                         avec repli vers le socle à l’inférence
        │
        ▼
REGISTRE D’EXPÉRIENCES
lot d’hypothèses · configuration · issue · statut · empreinte d’artefact
        │
        ▼
DÉCISION HIÉRARCHIQUE
groupes de déploiement → familles conditionnelles → portefeuille final scellé
        │
        ▼
PUBLICATION
4 scores auditable PARTOUT · incertitude · modules et STATIONS en analyses secondaires
```

Cette architecture sépare trois questions aujourd’hui confondues :

- **Que vaut le produit toujours disponible ?** — socle, fenêtre canonique, chiffre principal.
- **Que gagne-t-on quand une source optionnelle est disponible ?** — effet apparié du module sur les mêmes mois.
- **Que déploie-t-on si la source manque ?** — retour explicite au socle, pas indicateur de manque appris par le même modèle.

## Question 1 — Une quatrième voie pour les fenêtres

### Oui : socle canonique et modèles modulaires par contrat de disponibilité

Les trois stratégies proposées échouent chacune à un endroit différent :

- l’intersection stricte laisse la famille la plus courte choisir la question pour toutes les autres ;
- les fenêtres multiples rendent les scores absolus non comparables ;
- l’imputation déclarée laisse le modèle utiliser l’absence comme calendrier.

La quatrième voie est un **produit à repli explicite** :

1. un socle utilise seulement les familles servant toutes les dates de la fenêtre canonique ;
2. chaque module incomplet possède son propre modèle, entraîné et évalué uniquement quand son contrat d’entrée est satisfait ;
3. son gain est toujours mesuré contre le socle **restreint aux mêmes lignes et aux mêmes mois** ;
4. si le module manque à l’inférence, le routeur choisit le socle avant prédiction ; l’absence n’est jamais transmise au modèle comme variable ;
5. un module ne rejoint le socle qu’après couverture propre de toute la prochaine version du benchmark et confirmation scellée.

Le routeur repose sur la disponibilité technique d’une source, pas sur une observation d’air. Il respecte donc PARTOUT.

### Application aux quatre familles

| Famille | Statut structurel recommandé | Raison |
|---|---|---|
| spéciation · précurseurs · chimie | **éligibles au socle temporel** | 37 mois complets ; leur utilité reste une décision séparée. |
| GEOS-CF v1 | **module historique versionné** | +0,51 point est proche de la résolution, alors que raccourcir de 37 à 29 mois réduit l’information de toutes les autres mesures. La v2 est un nouveau prédicteur, pas huit mois à concaténer à v1. |
| IFS | **module candidat, non promouvable avant rattrapage ou confirmation prospective** | fenêtre 2024-02→2026-07 : 24 mois servis et 6 trous. Son absence ne peut entrer dans le socle. Son mécanisme nouveau justifie de compléter la couverture en priorité. |
| feux | **expérimental / hors socle** | fenêtre courte, 3 trous et arrêt en 2025-05 ; le bénéfice doit être fort pour justifier un produit conditionnel. |

Le socle principal devrait donc être évalué sur la fenêtre maximale propre indépendante des modules — ici la fenêtre de 37 mois si les observations et les familles réellement retenues la couvrent. Cette version est ensuite figée ; les nouveaux mois alimentent le benchmark suivant, pas le benchmark en cours.

### Le critère n’est ni « maximiser les mois » ni « maximiser les familles »

La fonction de choix est :

> **maximiser la valeur de déploiement attendue, sous trois contraintes : contrat d’entrée fiable, nombre de blocs suffisant pour l’effet utile, et chiffre principal inchangé par l’arrivée d’un candidat.**

Avant d’admettre un module, simuler la capacité du support disponible à distinguer le plus petit effet utile. Si ce support ne peut pas résoudre environ 0,5 point avec le protocole actuel, le module reste RÉSERVE, même si son estimation ponctuelle est flatteuse.

Il ne faut pas choisir l’intersection après avoir vu +0,51 pour GEOS-CF. La fenêtre canonique se fixe au niveau du produit ; le gain conditionnel de GEOS-CF se mesure ensuite.

## Question 2 — Accepter l’invalidation, réduire son coût

### Il n’existe pas d’apport invariant à une extension du corpus

Un apport apparié soustrait le déplacement commun dû aux plis, aux graines et aux lignes partagées. C’est utile. Mais si l’on ajoute des mois ou corrige les données :

- la distribution cible change ;
- les modèles de l’ancre et du candidat sont réajustés ;
- les poids implicites des régimes saisonniers et des stations changent ;
- une interaction peut rendre une famille utile sur l’ancien corpus et inutile sur le nouveau.

La nuit décrite l’a démontré : deux familles ont changé de statut après cinq mois ajoutés. Une « ancre insensible » masquerait ce fait au lieu de le résoudre. Aucun ratio ni différence ne peut garantir la stabilité sans hypothèse de transport entre les deux distributions.

La bonne règle est :

- **correction historique** : elle crée une nouvelle version du benchmark et invalide réellement tout descendant dépendant ;
- **ajout de mois futurs** : il alimente une prochaine version prospective, sans modifier le benchmark de développement courant ;
- **modification d’une famille optionnelle** : elle n’invalide que son module et les portefeuilles qui le contiennent.

### Le graphe de calcul à conserver

```text
snapshot corpus
├── socle / plis / cibles
│   ├── score du socle
│   ├── ablations de groupes
│   └── modules appariés
└── portefeuille final
    ├── confirmation
    └── chiffres publiés
```

Chaque artefact est indexé par l’empreinte exacte de ses parents. Si une entrée change, seuls ses descendants deviennent périmés. Dans le cas d’une correction du corpus racine, le cône est naturellement large : ce n’est pas une faiblesse de l’architecture, c’est la vérité de la dépendance.

### Réduire le coût sans réduire l’honnêteté

1. **Benchmark figé par campagne.** Ne pas étendre en continu le corpus qui sert à choisir.
2. **Matrices de features et plis mis en cache par empreinte.** Une correction d’une source ne doit pas refaire les jointures inchangées.
3. **Canari d’invalidation.** Sur 6 blocs représentatifs, mesurer ancre + deux sentinelles avant d’ouvrir le cône complet.
4. **Recalcul par niveaux.** Socle quatre polluants, puis seulement les groupes dont le canari dépasse 0,2 point ou change de signe/verdict.
5. **Une seule confirmation globale.** Les candidats sélectionnés sont réunis, gelés, puis remesurés une fois sur le scellé.

Le canari priorise le recalcul ; il ne rend pas valide un descendant portant une ancienne empreinte.

## Question 3 — Que conclure d’un plan sous-puissant ?

### On ne peut pas distinguer les deux états demandés avec ces données

« L’effet existe mais le plan ne le voit pas » et « l’effet n’existe pas » produisent tous deux un résultat non concluant. Aucun changement d’étiquette ne crée l’information manquante. La catégorie **RÉSERVE — puissance insuffisante** est donc nécessaire et ne doit pas être comptée comme SAUTE.

Le double aveugle n’est pas trop exigeant : il correspond précisément à la promesse simultanée de généralisation spatiale et temporelle. Le relâcher pour faire passer un petit effet changerait le produit. Si une famille ne peut être démontrée avec ce plan, la conclusion honnête est que le corpus ne permet pas encore la revendication PARTOUT double aveugle.

### Ne pas passer de « deux polluants » à « un polluant » après les résultats

« Au moins un polluant » n’est pas seulement un estimand plus grossier ; c’est une autre revendication, beaucoup plus facile à satisfaire. Elle est légitime pour une famille conçue **avant mesure** pour un polluant précis — par exemple une hypothèse photochimique O₃ — mais pas comme repli après avoir observé que la conjonction à deux échoue.

### Trois corrections, dans cet ordre

1. **Calibrer la règle au plan réel.** Une taille réelle de 0,0015 pour un seuil annoncé à 0,05 signifie que la procédure est extrêmement conservatrice. Avant de collecter davantage, vérifier par simulation sous le plan exact qu’une règle directionnelle contrôle bien l’erreur au niveau voulu sans marge ×34. La forme statistique finale est à vérifier avant implémentation.
2. **Adopter une décision à trois zones.** TIENT, SAUTE et RÉSERVE, fondés sur effet, incertitude et utilité ; pas sur la seule p-value.
3. **Accumuler des blocs prospectifs pour les réserves utiles.** Plus de données temporelles réellement nouvelles est préférable à plus de graines si l’incertitude dominante vient du corpus.

Règle de décision provisoire :

- **TIENT** : gain estimé d’au moins 0,5 point dans la cible préenregistrée ou dans deux polluants, incertitude compatible avec un bénéfice, et coût de service accepté ;
- **SAUTE** : borne supérieure sous 0,5 point sur les cibles prévues, ou dommage matériel confirmé ;
- **RÉSERVE** : tout le reste, notamment quatre signes positifs sans résolution suffisante.

Le seuil de 0,5 point n’est pas une constante scientifique : il est aligné provisoirement sur la résolution ±0,36–0,48. Un seuil de 0,25 point serait actuellement plus précis que l’instrument.

Pour une décision d’ingénierie, le test d’hypothèse ne doit pas disparaître ; il devient une composante de l’incertitude. L’arbitrage final porte sur la probabilité que le gain dépasse l’effet utile, le coût du module et la valeur d’attendre de nouveaux blocs.

## Question 4 — Décider dans un espace redondant

### Promouvoir des unités de déploiement, diagnostiquer leurs familles

Une famille statistique n’est pas toujours la bonne unité de décision. Le groupe primaire doit correspondre à ce qui :

- décrit le même mécanisme ;
- dépend de la même source ou du même contrat de disponibilité ;
- tombe ou se maintient ensemble à l’inférence ;
- partage une grande partie de son pipeline de maintenance.

La corrélation aide à découvrir une redondance, mais ne doit pas former seule les groupes. Deux variables corrélées provenant de sources indépendantes peuvent avoir une valeur de secours ; deux variables peu corrélées mais indisponibles ensemble appartiennent au même contrat de service.

### Procédure hiérarchique bornée

1. Définir au plus **4 à 6 groupes parents** avant les scores.
2. Exécuter une ablation jointe par groupe contre la pile complète.
3. Écarter les groupes clairement sous l’effet utile ; placer les incertains en RÉSERVE.
4. À l’intérieur des seuls groupes retenus, comparer le groupe complet à la suppression de chaque famille.
5. Tester au plus deux interactions entre groupes lorsque les corrections résiduelles sont fortement liées ou que les ablations individuelles et conjointes se contredisent.
6. Confirmer une seule fois le portefeuille minimal restant.

La complexité devient de l’ordre du nombre de groupes plus du nombre de familles retenues, et non 2⁹.

### Cas chimie + précurseurs

Le groupe parent naturel est **chimie CAMS**. Quatre configurations suffisent :

| Configuration | Question |
|---|---|
| aucun des deux | valeur du socle sans chimie additionnelle |
| précurseurs seuls | valeur propre du premier encodage |
| chimie seule | valeur propre du second encodage |
| les deux | valeur maximale du groupe et interaction |

Promouvoir d’abord le parent si « les deux » dépasse le socle de façon utile. Choisir ensuite la configuration la moins coûteuse dont la performance reste à moins de 0,5 point de « les deux ». Les +1,63 et +1,17 individuels ne doivent jamais être additionnés.

Si le groupe n’aide que l’ozone, il peut devenir un module O₃ préenregistré ; cela ne justifie pas une promotion multi-polluants ni son entrée automatique dans les quatre modèles.

## Question 5 — Publier un modèle instable

### La deuxième décimale doit disparaître du récit principal

Les arbres de décision sont discontinus : une petite modification des lignes peut changer des coupures et donc un pli entier. Le fait important n’est pas le rapport 65× pris seul, mais la séparation des sources d’incertitude :

- bruit d’exécution à données identiques : ≤0,039 point par pli ;
- sensibilité à une version plausible du corpus : jusqu’à 2,56 points par pli et 0,23 agrégé ;
- incertitude d’échantillonnage des mois et stations : encore distincte.

Moyenner beaucoup de graines ne traite que la première, qui est la plus petite. Il faut prioriser les perturbations de corpus et le rééchantillonnage respectant le plan.

### Trois sorties, pas un point nu

Pour chaque polluant :

1. **estimation centrale** sur le snapshot canonique ;
2. **intervalle d’échantillonnage** respectant les blocs temporels et spatiaux ;
3. **enveloppe de version** sur quelques perturbations de corpus préenregistrées, présentée comme sensibilité et non comme intervalle probabiliste si sa loi n’est pas définie.

Plan de calcul proportionné :

- conserver les répétitions à données identiques déjà suffisantes pour borner le bruit numérique ;
- exécuter 6 à 10 perturbations de corpus plausibles et équilibrées avec une graine fixe ;
- pour les apports, réentraîner ancre et candidat appariés dans chaque perturbation ;
- ne pas croiser toutes les graines avec toutes les perturbations tant que le bruit de graine reste 65× plus petit.

### Présentation au lecteur

Dans le corps du dossier :

> **NO₂ : environ 40 % de réduction d’erreur sur le produit auditable PARTOUT.**

Dans la table technique :

```text
estimation centrale : 39,9 %
intervalle du plan  : [à calculer]
sensibilité corpus  : [min ; max] sur les perturbations préenregistrées
bruit d’exécution   : ≤0,04 point par pli
```

Tant que les deux bornes manquent, publier **≈40 %**, pas 39,94 %. Une décimale peut rester dans le tableau de reproductibilité ; elle ne doit pas être l’unité rhétorique de la conclusion.

Les écarts appariés restent la quantité principale pour décider des familles. Les gains absolus décrivent le produit figé, avec leur incertitude de version.

## Question 6 — Quel chiffre est « le » chiffre ?

Le chiffre principal doit être le plus proche de la promesse fondatrice et le moins dépendant d’un artefact d’époque : **auditable PARTOUT**.

Il faut quatre chiffres principaux, un par polluant, et non seize dans le récit :

| Produit principal — auditable PARTOUT | Valeur technique | Valeur à dire |
|---|---:|---:|
| NO₂ | 39,94 % | **≈40 %** |
| O₃ | 14,56 % | **≈15 %** |
| PM10 | 17,79 % | **≈18 %** |
| PM2,5 | 8,59 % | **≈9 %** |

Les trois autres colonnes ne sont pas trois réserves du même chiffre ; elles répondent à des questions différentes :

- **comparable PARTOUT** : sensibilité à la pile historique incluant des familles avec indicateur d’époque — borne descriptive, pas titre ;
- **auditable STATIONS** : autre produit, qui suppose un réseau instrumenté ;
- **comparable STATIONS** : combinaison la plus favorable et la moins adaptée à la promesse principale — annexe seulement.

Structure du dossier :

1. une table principale de quatre lignes auditable PARTOUT ;
2. une phrase séparée sur AUX STATIONS, sans juxtaposition ambiguë ;
3. la matrice 2×2 complète une seule fois dans l’annexe méthodologique ;
4. l’écart comparable/auditable expliqué comme coût mesuré de la propreté d’époque.

Le plus conservateur n’est pas choisi par modestie ; il est choisi parce qu’il correspond au produit revendiqué. Si le socle canonique proposé à la question 1 change la pile, ces quatre valeurs doivent être recalculées une fois sur ce socle avant de devenir les chiffres définitifs.

## Question 7 — Compter honnêtement le criblage

### Le CSV ne peut pas être le registre

Une configuration abandonnée après un résultat partiel a déjà influencé la sélection, même si aucun CSV final n’existe. La compter seulement lorsqu’un fichier est écrit sous-estime le nombre de degrés de liberté et rend le seuil 0,0974 non défendable comme compte exact.

Il faut étendre le registre avant toute opération qui peut révéler la performance. Mais il ne faut pas enregistrer chaque idée formulée dans une note : cela rendrait le registre illisible.

### Moment d’entrée au registre

Un candidat reçoit un identifiant **avant le premier calcul dépendant de la cible ou du score**, notamment :

- entraînement rapide ou complet ;
- calcul sur un seul polluant ;
- ablation partielle ;
- graphique de résidus utilisé pour décider ;
- proxy de performance pouvant conduire à abandonner ou promouvoir.

Une simple vérification de licence, de schéma, de coût ou de disponibilité reste une étude de faisabilité. Elle est tracée, mais ne consomme pas le lot d’hypothèses si aucune information de résultat n’a été consultée.

### États obligatoires

```text
PROPOSÉ
├── INÉLIGIBLE AVANT RÉSULTAT   -> tracé, ne compte pas dans la famille de tests
├── ÉCHEC TECHNIQUE             -> reste dans le registre
├── EXÉCUTÉ / REJETÉ            -> compte
├── EXÉCUTÉ / RÉSERVE           -> compte
└── EXÉCUTÉ / PROMU             -> compte
```

Chaque lot préenregistre aussi : familles de configurations, polluants cibles, effet utile, ordre des écrans, règle d’arrêt et traitement des échecs.

### Réparer rétrospectivement la campagne actuelle

1. inventorier scripts, historique de commandes, journaux, commits, sorties temporaires et notes ;
2. produire un **minimum certain** de configurations vues et un **maximum plausible** ;
3. recalculer la sensibilité de la décision aux deux bornes ;
4. qualifier les verdicts actuels d’exploratoires si la borne haute n’est pas maîtrisée ;
5. démarrer le registre prospectif avant le prochain IFS ou groupe chimique.

Il ne faut pas reconstruire un nombre précis si les traces ne le permettent pas. « Entre 10 et 17 configurations ont pu influencer la sélection » est plus honnête qu’un ajustement exact bâti sur dix CSV.

## Plan d’action priorisé

### P0 — Avant toute nouvelle mesure

1. Écrire le contrat : **auditable PARTOUT**, fenêtre canonique de campagne, métrique, effet utile provisoire 0,5 point.
2. Définir les familles du socle selon leur disponibilité complète, indépendamment de leur score.
3. Sortir GEOS-CF v1, IFS troué et feux du score absolu principal ; les déclarer modules.
4. Créer le snapshot immuable et son graphe de descendants.
5. Ouvrir le registre exhaustif des configurations.

### P1 — Avant un verdict TIENT/SAUTE

6. Recalibrer la règle multi-polluants sur le plan exact ; vérifier le sens et la taille réelle.
7. Formaliser TIENT / RÉSERVE / SAUTE et la valeur d’attendre de nouveaux mois.
8. Former 4 à 6 groupes de déploiement ; exécuter les ablations parentes.

### P2 — Avant publication ou entretien

9. Calculer l’enveloppe de stabilité des quatre scores auditable PARTOUT.
10. Remplacer les seize nombres dans le récit par quatre valeurs arrondies, la matrice complète restant en annexe.
11. Présenter GEOS-CF, IFS et feux comme modules conditionnels avec leur support et leur repli, jamais comme amélioration du même score sur une autre fenêtre.

## Ce qu’il ne faut pas construire

- pas d’ancre prétendument insensible aux corrections du corpus ;
- pas d’imputation accompagnée d’un drapeau de manque pour des mois entiers ;
- pas de nouvelle règle statistique choisie pour faire passer les trois familles positives ;
- pas de toutes les coalitions de neuf familles ;
- pas de moyenne massive sur les graines alors que le corpus domine le bruit ;
- pas de chiffre principal comparable STATIONS parce qu’il est plus flatteur ;
- pas de registre défini par les seuls fichiers qui ont survécu.

## Réponse finale à la question d’architecture

L’architecture actuelle — empreintes, intégrité, génération figée — est correcte. Elle n’a pas besoin d’être inversée. Il lui manque une couche supérieure : **le contrat immuable de la question mesurée**, puis une couche latérale : **les modules à disponibilité conditionnelle**.

Une correction amont continuera parfois à invalider tout l’aval. C’est sain lorsqu’elle change le corpus qui définit la preuve. La valeur organisationnelle vient de quatre propriétés : savoir immédiatement quel cône est périmé, ne jamais confondre ses résultats avec les nouveaux, réutiliser tout ce qui n’en dépend pas, et empêcher une famille candidate de redéfinir le benchmark sur lequel elle paraît utile.
