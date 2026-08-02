# Prompt GPT — R14 · Ce qui sert vraiment à Atmo Occitanie

> À coller tel quel. Rédigé le 02/08/2026.
> Les prompts précédents portaient sur la méthode. Celui-ci porte sur **l'utilité pour un
> destinataire précis**. Je ne cherche pas à améliorer un score, je cherche à savoir ce qui
> manque à cette structure-là et que je pourrais combler.

---

## Ma situation, sans enjolivure

Je prépare une **candidature spontanée** à Atmo Occitanie, l'association agréée de
surveillance de la qualité de l'air de la région. Je ne réponds à aucune offre publiée. Mon
dossier est un projet technique réalisé seul, que je veux présenter comme une contribution
utile et non comme une démonstration de compétence hors-sol.

**Ce que le projet fait.** Post-traitement statistique des prévisions **CAMS Europe** sur
les stations de mesure françaises, à l'échéance J+1. Un modèle à gradient boosté apprend le
résidu `observation − CAMS` et le retranche. Corpus de 36 mois, 476 stations, observations
LCSQA.

**Ce qu'il obtient**, en cachant simultanément la station et le mois — la condition de
déploiement réelle :

| polluant | gain de RMSE contre CAMS brut |
|---|---|
| NO₂ | **+36,7 %** |
| PM10 | **+13,3 %** |
| O₃ | +6,9 % |
| PM2,5 | +4,5 % |

**Ce qu'il ne fait pas, et que je sais.** Sur la **détection de dépassement** — ce qui
déclenche réellement une procédure — l'avantage n'est pas démontré sur cet axe : à budget
d'alerte égal, ×1,18 sur PM10 avec un intervalle de confiance contenant zéro. Il est
significatif (×1,82) seulement quand le mois est connu. Et je sais que la méthode
elle-même n'est pas neuve : PREV'AIR applique déjà une adaptation statistique.

---

## Question 1 — Ce que fait Atmo Occitanie, précisément

1. Quelles sont ses **missions, son organisation, ses moyens** ? Effectif, budget,
   financeurs, gouvernance, implantations. Comment se répartit son activité entre
   surveillance, prévision, information, études et accompagnement ?
2. Quel est son **réseau de mesure** — nombre de stations, typologie, polluants suivis,
   couverture départementale ? Comment a-t-il évolué récemment ?
3. Quels **outils de modélisation et de prévision** utilise-t-elle ? Produit-elle ses
   propres cartes, ou relaie-t-elle une chaîne nationale ? Quel modèle méso-échelle,
   quelle résolution, quelle fréquence ?
4. Quels sont ses **produits publics** — indice quotidien, cartes, bulletins, données
   ouvertes, interfaces de consultation, applications ? Lesquels sont les plus utilisés ?
5. Quelles sont ses **publications récentes** — rapports d'activité, études thématiques,
   campagnes de mesure ? Quels sujets y reviennent, et lesquels ont émergé depuis deux ans ?

## Question 2 — Ses difficultés réelles, pas celles que je suppose

C'est la question la plus importante du prompt. Je veux éviter de proposer une solution à
un problème qu'ils n'ont pas.

1. Quelles **difficultés techniques** une AASQA de cette taille rencontre-t-elle
   concrètement en prévision — fiabilité des épisodes, résolution spatiale, stations peu
   représentatives, polluants mal modélisés, ressources de calcul, compétences ?
2. Quels sont les **manques identifiés dans leurs propres documents** ? Un rapport
   d'activité, un plan de surveillance ou un programme de travail nomme souvent les
   chantiers ouverts. Lesquels ?
3. Le **PRSQA** — programme régional de surveillance de la qualité de l'air — en cours
   pour l'Occitanie : quelles priorités affiche-t-il, sur quelle période, et quels axes
   concernent la modélisation et la prévision ?
4. Quelles **contraintes réglementaires nouvelles** vont peser sur eux à court terme —
   directive (UE) 2024/2881, décision (UE) 2026/1208 sur les aires de représentativité —
   et quel travail supplémentaire cela représente-t-il concrètement ?
5. Y a-t-il des **tensions connues** entre ce que le public attend et ce que la technique
   permet — finesse spatiale de l'indice, prévision à plus de trois jours, pollens,
   pesticides, air intérieur ?

## Question 3 — Où une correction statistique s'insère, ou ne s'insère pas

1. Dans la **chaîne opérationnelle** d'une AASQA, entre le modèle national et la
   publication, quels sont les points d'insertion possibles d'un post-traitement
   statistique ? Qui aurait la main dessus, et à quelles conditions ?
2. Les AASQA appliquent-elles déjà des corrections locales aux sorties de PREV'AIR ou de
   leur modèle régional ? Sous quelle forme — krigeage avec dérive externe, assimilation,
   correction de biais par station, expertise humaine ?
3. Quelle est la **valeur ajoutée réelle** d'une correction supplémentaire quand PREV'AIR
   fournit déjà une adaptation statistique ? Où reste-t-il de la place — polluants moins
   bien traités, sites atypiques, échéances plus lointaines, incertitude quantifiée ?
4. Un système qui améliore la **RMSE** sans améliorer significativement la **détection
   d'épisode** a-t-il une utilité opérationnelle pour une AASQA ? Ou est-ce que seule la
   détection compte ? Je veux une réponse franche : si la réponse est « peu d'intérêt »,
   je réoriente le dossier.
5. Quelle est l'attitude typique de ces structures face à une **contribution externe non
   sollicitée** ? Qu'est-ce qui la rend crédible plutôt qu'encombrante ?

## Question 4 — Ce qu'un dossier devrait démontrer

1. Pour un profil **données et modélisation** dans une AASQA, quelles compétences sont
   réellement recherchées aujourd'hui ? Quels outils, quels langages, quelles pratiques —
   et lesquelles sont sur-représentées dans les candidatures sans être utiles ?
2. Qu'est-ce qui **distingue** un bon dossier technique d'un exercice académique, aux yeux
   d'un recruteur de ce milieu ? La reproductibilité, la connaissance réglementaire, la
   prudence sur les résultats, la capacité à documenter les limites ?
3. Mon dossier publie ses propres résultats négatifs — détection non significative en
   double aveugle, quatre familles de prédicteurs mesurées nulles, une hypothèse réfutée
   par ma propre mesure. **Est-ce un atout ou un handicap** dans ce contexte ? Je pense
   que c'est un atout et j'ai peut-être tort.
4. Quels **formats de livrable** parlent le mieux à cette audience — note technique,
   démonstrateur interactif, jeu de données ouvert, dépôt de code documenté ?
5. Y a-t-il des **erreurs de posture** classiques dans une candidature spontanée à une
   AASQA — surestimer la nouveauté d'une méthode déjà industrialisée, ignorer la contrainte
   réglementaire, proposer un outil sans se soucier de son intégration ?

## Question 5 — Le territoire, ce qu'il a de particulier

1. Quels **enjeux spécifiques à l'Occitanie** une candidature devrait-elle montrer qu'elle
   connaît — ozone méditerranéen, poussières sahariennes, chauffage au bois pyrénéen,
   agglomération toulousaine, viticulture et pesticides, transit autoroutier, littoral ?
2. Quelles sont les **zones à enjeux réglementaires** de la région — plans de protection de
   l'atmosphère en vigueur, zones à faibles émissions, contentieux, dépassements
   persistants ?
3. Quels **épisodes marquants** des trois dernières années y ont été documentés, et
   comment ont-ils été gérés ?
4. Quelles **collaborations** structurent l'action régionale — collectivités, ARS, DREAL,
   universités, observatoires ? Y a-t-il des programmes de recherche locaux auxquels une
   compétence en modélisation statistique serait utile ?
5. Quels sont les sujets sur lesquels la structure **communique le plus** en ce moment ?
   C'est un indice de ce qui compte pour elle.

---

## Contraintes de réponse

- **Privilégie les sources primaires** : site et publications d'Atmo Occitanie, rapports
  d'activité, PRSQA, documents Atmo France, textes réglementaires, arrêtés préfectoraux.
  Donne les liens.
- **Distingue nettement** ce que tu lis dans leurs documents, ce qui est général aux AASQA,
  et ce que tu extrapoles. Je m'appuierai sur ces réponses en entretien : une extrapolation
  présentée comme un fait me coûterait cher.
- **Réponds franchement à la question 3.4.** Si un gain de RMSE sans gain de détection
  n'intéresse pas une AASQA, dis-le. Je préfère réorienter maintenant que défendre un
  travail mal ciblé.
- **Signale ce que tu ne trouves pas.** Une structure de cette taille ne publie pas tout ;
  savoir ce qui manque m'indique quoi demander directement.
- Réponds en français, avec la terminologie du métier.
