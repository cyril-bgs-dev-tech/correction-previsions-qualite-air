# Prompt GPT — R11 · Les quatre murs mesurés

> À coller tel quel. Rédigé le 02/08/2026, après le passage du corpus à 36 mois.
> Chaque question part d'un **résultat mesuré chez nous**, pas d'une curiosité générale.

---

## Le contexte, en dix lignes

Post-traitement statistique des prévisions **CAMS Europe** (grille 0,1°, soit ≈ 8 km en
longitude × 11 km en latitude aux latitudes françaises) sur les stations de mesure
françaises. Le modèle apprend le **résidu** `observation − CAMS` à l'échéance J+1, cible
journalière, ~57 prédicteurs, LightGBM.

Corpus : **36 mois**, 476 stations, observations réglementaires LCSQA.

Protocole d'évaluation — c'est le point important : nous mesurons sur quatre cellules,
dont la plus dure cache **simultanément la station et le mois** (« double aveugle »).
C'est la condition de déploiement réelle : une station nouvelle, une date future.

Résultats en double aveugle, gain de RMSE contre CAMS brut :

| polluant | gain | σ entre plis | pire pli |
|---|---|---|---|
| NO₂ | **+27,8 %** | 4,8 | +17,0 % |
| NO₂ + typologie de station | **+36,7 %** | 4,1 | +28,1 % |
| O₃ | +6,9 % | 11,1 | −23,8 % |
| PM2,5 | **+4,5 %** | 11,1 | −24,8 % |

---

## Question 1 — Le mur des PM2,5

**Le fait mesuré.** Doubler le corpus de 18 à 36 mois n'a **rien** apporté aux PM2,5 :
+5,14 % → +4,47 %, c'est-à-dire une variation inférieure à notre barre de bruit
(±2,02 pt, établie par bootstrap de partitions). Seule la dispersion s'améliore
(σ 12,2 → 11,1). Sur la même opération, l'ozone gagne le double (+3,31 → +6,88 %).

Par ailleurs, quatre familles de prédicteurs testées se sont révélées **nulles** sur les
PM2,5 : typologie de station, sol et géologie, colonnes TROPOMI, chimie. Seuls les feux
apportent (+3,0 %), et la météo ERA5 apporte sur l'ozone mais peu ici.

**Ce que je demande.**

1. Dans la littérature de post-traitement statistique (MOS, model output statistics,
   bias correction) appliquée à la qualité de l'air, **quel est l'ordre de grandeur des
   gains publiés sur PM2,5 contre NO₂ et O₃** ? Y a-t-il un consensus sur le fait que les
   PM2,5 se corrigent moins bien, et si oui **quel mécanisme** est invoqué ?
2. Est-il établi que le résidu PM2,5 est dominé par des sources **non observables depuis
   les prédicteurs usuels** — chauffage résidentiel au bois, remise en suspension,
   aérosols organiques secondaires, transport longue distance ? Quelles études le
   quantifient ?
3. **Quels prédicteurs ont démontré un apport réel sur PM2,5 spécifiquement**, avec
   effet chiffré et protocole d'évaluation précisé ? Je cherche des candidats testables,
   pas une liste de plausibles. Le chauffage au bois m'intéresse particulièrement :
   existe-t-il un proxy opérationnel (degrés-jours de chauffage, densité de logements
   chauffés au bois, indicateur de combustion) qui ait été **mesuré** utile ?
4. La **hauteur de couche limite** est-elle un prédicteur retenu dans les études qui
   marchent ? Nous l'avons dans ERA5 mais son apport n'est pas isolé chez nous.

---

## Question 2 — Le réglage d'hyperparamètres dégrade, systématiquement

**Le fait mesuré.** Nous avons comparé quatre configurations — hyperparamètres par
défaut, réglage manuel, capacité augmentée (800 arbres), et une recherche Optuna de
200 essais — sur **4 polluants × 2 tailles de corpus × avec et sans typologie**.

Les hyperparamètres **par défaut gagnent ou égalent 10 fois sur 10** en double aveugle.
Le réglage perd systématiquement (jusqu'à −2,9 points sur O₃, −2,4 sur PM2,5). Optuna
n'apporte rien au-delà du bruit, pour un coût de 800 à 1 800 s contre 100 s.

Or le même réglage **gagne** sur une partition aléatoire classique. Le renversement se
produit exactement quand on cache conjointement la station et la date.

**Ce que je demande.**

1. Ce phénomène est-il **documenté** ? Je cherche des références sur la dégradation du
   réglage d'hyperparamètres **sous décalage de distribution** (distribution shift),
   et particulièrement sous **validation croisée groupée** (grouped / blocked CV) par
   opposition à une partition i.i.d.
2. Existe-t-il une littérature établissant que **la régularisation optimale sous
   généralisation spatiale est plus forte** que sous validation aléatoire ? Avec quel
   argument théorique — capacité effective, complexité de Rademacher, autre ?
3. Y a-t-il des **protocoles de réglage recommandés** quand la métrique cible est la
   généralisation hors-groupe : régler directement sur la CV groupée, régler sur le pire
   pli plutôt que la moyenne, contraindre a priori l'espace de recherche ?
4. Contre-question honnête : **existe-t-il des travaux qui montrent l'inverse** — que le
   réglage aide sous décalage de distribution ? Je veux les deux côtés.

---

## Question 3 — Encoder la représentativité d'une station

**Le fait mesuré.** Le levier le plus fort de notre projet est **quatre colonnes
catégorielles** décrivant la station : une densité ordinale (urbain → rural isolé) et
trois indicatrices (fond / trafic / industriel). Elles valent **+8,9 points sur NO₂ en
double aveugle** (36,7 % contre 27,8 %), et **rien du tout sur l'axe temporel** — un
non-effet qui confirme le mécanisme : elles ne servent que lorsque la station est
**inconnue**, où elles disent de quel *genre d'endroit* il s'agit.

Elles sont nulles sur O₃ et PM2,5, ce qui est cohérent avec un mécanisme sous-maille :
CAMS confond une station trafic et une station de fond distantes de 400 m.

**Ce que je demande.**

1. **Quel est l'état de l'art pour décrire la représentativité spatiale d'une station**
   de mesure de qualité de l'air, au-delà de la classification EEA fond/trafic/industriel ?
   Le concept d'« aire de représentativité » (representativeness area) est-il opérationnalisé
   quelque part sous forme de variables utilisables par un modèle ?
2. Quels **descripteurs géographiques mesurables** ont démontré un apport dans des
   travaux de spatialisation ou de post-traitement — densité de voirie dans un rayon
   donné, trafic annuel moyen, hauteur du bâti, facteur de vue du ciel (sky view factor),
   fraction imperméabilisée, distance à l'axe le plus proche ? Avec **effet chiffré** et
   **rayon optimal** quand il est publié.
3. La **modélisation par régression de l'usage des sols** (land use regression, LUR) est
   la famille de méthodes la plus proche de ce que nous faisons. Quels prédicteurs y sont
   systématiquement retenus, et à quels **rayons** (souvent 50 m, 300 m, 1 000 m, 5 000 m) ?
4. Ces descripteurs sont-ils disponibles en **libre accès sur la France** — CORINE Land
   Cover, OpenStreetMap, BD TOPO de l'IGN, Copernicus Urban Atlas, Global Human Settlement
   Layer ? Lesquels avec quelle résolution ?

---

## Question 4 — Les PM10 et les épisodes qui déclenchent réellement

**Le fait mesuré.** En Occitanie, sur la période que nous avons documentée, **40 des 52
procédures préfectorales** ont été déclenchées sur les **PM10** — pas sur l'ozone ni le NO₂.
C'est donc le polluant qui compte opérationnellement, et notre gain y est de **+7,5 %**
en double aveugle, avec 7 plis négatifs.

Une part importante des dépassements PM10 méditerranéens est attribuée aux **intrusions
de poussières sahariennes**.

**Ce que je demande.**

1. Quelle est la **part attribuable aux poussières désertiques** dans les dépassements
   PM10 en région méditerranéenne française, et comment est-elle établie ? La procédure
   d'« abattement » des sources naturelles prévue par la directive européenne est-elle
   appliquée en France, et selon quelle méthode ?
2. **CAMS représente-t-il bien les intrusions sahariennes** ? Y a-t-il des évaluations
   publiées de son biais sur ces épisodes spécifiquement ? Si CAMS les rate, une
   correction statistique ne peut pas les inventer — et il faut le dire.
3. Quelles **sources opérationnelles en accès libre** décrivent le panache désertique
   avec une latence compatible d'une émission à 3 h du matin pour J+1 ? Je connais le
   Barcelona Dust Regional Center mais son accès public est retardé. Existe-t-il des
   prévisions de poussières dans les flux ouverts d'ECMWF, ou dans CAMS lui-même
   (variable « dust aerosol optical depth ») ?
4. Plus généralement : pour les épisodes PM10, **quel signal précoce** est utilisé en
   opérationnel par les organismes de surveillance — indice de poussière, rétrotrajectoires,
   observation satellitaire, mesure amont ?

---

## Contraintes de réponse

- **Cite tes sources** — article, année, revue ou organisme, lien quand il existe. Une
  affirmation sans source m'est inutilisable : ce projet n'écrit aucun chiffre qu'il ne
  peut pas rattacher à une mesure ou à une référence.
- **Distingue explicitement** ce qui est établi, ce qui est débattu, et ce qui est ton
  extrapolation.
- **Quantifie** les effets quand la littérature le fait, et précise le **protocole
  d'évaluation** de chaque chiffre cité — une amélioration mesurée sur partition aléatoire
  n'est pas comparable à la nôtre.
- **Dis-moi quand la réponse est « rien de probant »**. Un résultat négatif documenté
  m'évite des jours de travail ; une piste plausible non étayée m'en coûte.
- Priorise ce qui est **testable sous 48 h** avec des données en accès libre sur la
  France. Le calendrier est court.
