# Pistes créatives à tester

Les angles ci-dessous ne changent pas les résultats ; ils changent la porte d’entrée. L’angle recommandé est le premier. Les autres peuvent fournir une ouverture, une métaphore ou une réponse, mais ne doivent pas tous être mélangés dans la même présentation.

## 1. « La bonne question n’était pas la RMSE » — recommandé

**Promesse.** Montrer une capacité à déplacer le problème vers la décision réelle.

**Arc.** Gain moyen → épisode encore manqué → comparaison à FAR fixé → classement de risque → garde-fou.

**Pourquoi il convient à ATMO.** Il parle de vigilance, de faux signaux et d’expertise humaine avant de parler d’algorithme.

**Risque.** Faire croire que la RMSE ne sert à rien. Dire qu’elle reste indispensable pour la valeur continue et FAIRMODE, mais qu’elle ne suffit pas pour une décision rare.

**Image mentale.** Deux radars de même précision moyenne ; l’un place les jours dangereux en haut de la pile.

## 2. « Le projet qui s’est amélioré en perdant ses certitudes »

**Promesse.** Faire de la falsification le caractère remarquable du candidat.

**Arc.** Premier résultat séduisant → double aveugle → affirmation retirée → benchmark officiel → périmètre plus petit mais plus solide.

**Force.** Très mémorable en entretien ; rend visibles autonomie, honnêteté et capacité d’audit.

**Risque.** Une succession d’échecs peut faire oublier le service. Toujours revenir au résultat à FAR fixé et à la décision créée par chaque réfutation.

**Accroche.** « Mon meilleur test est celui qui a fait tomber mon meilleur récit. »

## 3. « Le modèle sait ordonner ce qu’il ne sait pas chiffrer »

**Promesse.** Expliquer la différence entre calibration de concentration et discrimination des jours à risque.

**Arc.** Seuil réglementaire fixe → écrasement des extrêmes → seuil calibré hors échantillon → courbe rappel–FAR stable.

**Force.** Porte naturellement vers un produit probabiliste et une aide à l’attention.

**Risque.** Sonner comme une formule publicitaire. L’accompagner immédiatement des valeurs `0,184 → 0,656`, du périmètre O₃ et de la limite temporelle.

**Image mentale.** Une pile de journées triées : la hauteur exacte est imparfaite, mais les dossiers urgents remontent.

## 4. « La cible vaut plus que l’algorithme »

**Promesse.** Se démarquer des candidatures ML centrées sur l’architecture.

**Arc.** Trois bibliothèques quasi équivalentes → cible réglementaire directe → signe opposé entre maximum et moyenne → réplication de Bertrand.

**Force.** Très clair techniquement et compatible avec un jury connaissant PREV’AIR/CAMS.

**Risque.** C’est un résultat déjà publié. L’utiliser pour démontrer le jugement expérimental, jamais comme nouveauté scientifique.

**Accroche.** « J’ai gagné vingt fois plus en posant la bonne cible qu’en changeant de bibliothèque. »

## 5. « Deux usages, deux produits »

**Promesse.** Clarifier la confusion entre station connue et lieu sans mesure.

**Arc.** Usage A avec observations J−2 → comparable au MOS ; usage B sans observation → transfert spatial ; entrées et revendications différentes.

**Force.** Très utile si le jury attaque la comparabilité ou demande le déploiement.

**Risque.** Trop conceptuel comme ouverture. Le garder comme écran de clarification ou réponse à une objection.

**Image mentale.** Deux voies qui se séparent après CAMS : « station instrumentée » et « station nouvelle ».

## 6. « Une chaîne de décisions, pas un modèle »

**Promesse.** Présenter le projet comme un système : données disponibles → prévision → risque → seuil métier → expertise → repli.

**Force.** Donne une forte impression d’opérationnalité et permet d’intégrer IFS/AIFS, membres CAMS et observations récentes.

**Risque.** Le prototype ne réalise pas encore toutes les briques. Distinguer visuellement « mesuré », « disponible » et « à valider ».

**Image mentale.** Un circuit avec portes vertes, orange et rouges ; jamais un cerveau IA au centre.

## Classement recommandé

| Rang | Angle | Usage optimal |
|---:|---|---|
| 1 | La bonne question n’était pas la RMSE | fil principal de la présentation |
| 2 | Le projet qui perd ses certitudes | posture et entretien |
| 3 | Le modèle sait ordonner… | formule de mémorisation / écran détection |
| 4 | La cible vaut plus que l’algorithme | preuve technique intermédiaire |
| 5 | Deux usages, deux produits | annexe ou objection MOS |
| 6 | Une chaîne de décisions | vision de déploiement / conclusion |

## Concepts visuels à prototyper

### A. La balance du service

À gauche : épisodes manqués. À droite : fausses alertes. Le curseur n’est pas choisi par le modèle mais par le métier. Montrer ensuite où se placent CAMS et la correction sous le même budget.

### B. Les trois niveaux de vérité

Trois marches :

1. **ça marche ailleurs** — stations exclues `+29,7 %` ;
2. **ça marche demain** — double aveugle `+1,5 %` ;
3. **ça aide à décider** — rappel à FAR fixé `0,184 → 0,656`.

La deuxième marche plus basse crée la tension ; la troisième change la métrique au lieu de cacher la faiblesse.

### C. Le tamis de falsification

Faire passer les affirmations dans quatre tamis : station cachée, temps caché, concurrent officiel, disponibilité à l’émission. Ce qui reste à la fin constitue le produit défendable.

### D. La fiche du jour

Une fausse interface très sobre montrant : risque O₃, valeur brute, valeur corrigée, confiance, raison du drapeau et produit de repli. À utiliser uniquement comme **projection d’usage**, clairement marquée « concept », jamais comme produit existant.

### E. La carte des promesses

Trois colonnes :

- **démontré** : transfert spatial, gain de RMSE contre MOS 2025 ;
- **indiqué** : stabilité du classement à FAR fixé hors fenêtre ;
- **non démontré** : robustesse temporelle de la valeur, carte communale, détection NO₂.

Cette visualisation peut remplacer une slide de limites défensive.

## Formulations à tester à voix haute

- « J’ai optimisé moins un modèle qu’une chaîne de preuve. »
- « Chaque gain a dû survivre à un comparateur plus gênant que le précédent. »
- « La station cachée teste le transfert ; le mois caché teste demain ; le FAR fixé teste la décision. »
- « Une variable indisponible à l’émission n’est pas une variable, c’est un plafond expérimental. »
- « Le produit ne décide pas : il hiérarchise l’attention. »

## Formulations trop théâtrales pour ce jury

- « L’IA voit les épisodes que CAMS ne voit pas. »
- « Le modèle a appris de ses échecs. » — c’est le chercheur qui a changé le protocole.
- « Le voyage d’un héros contre la pollution. »
- « Révolutionner la prévision d’ATMO. »
- « Transformer les données en impact. » — trop générique pour être mémorable.

## Décision proposée

Construire la présentation sur l’angle 1, emprunter la posture de l’angle 2 et réserver la formule de l’angle 3 pour l’écran rappel–FAR. Les angles 4 à 6 alimentent les preuves, les annexes et la conclusion ; ils ne deviennent pas des récits concurrents.

