# Prompt GPT — R13 · Comprendre, pas seulement mesurer

> À coller tel quel. Rédigé le 02/08/2026.
> Les prompts R11 et R12 portaient sur les données, le réglage et la détection. Celui-ci
> porte sur **la connaissance du domaine** — l'une des missions statutaires d'une AASQA, et
> celle sur laquelle je serai jugé en entretien autant que sur le code.

---

## Ce que je cherche

Je ne cherche pas un cours de qualité de l'air. Je cherche à **comprendre mes propres
résultats**, à savoir ce qui est spécifique à l'Occitanie, et à connaître l'horizon
réglementaire.

La partie A est la plus importante : j'ai des mesures solides dont je ne sais pas toujours
expliquer le mécanisme. Un chiffre qu'on ne sait pas expliquer ne se défend pas.

---

## Partie A — Expliquer mes résultats mesurés

Contexte : je corrige statistiquement les prévisions **CAMS Europe** (grille 0,1°, soit
≈ 8 km × 11 km aux latitudes françaises) sur les stations françaises, à l'échéance J+1,
en cible journalière. Le modèle apprend le résidu `observation − CAMS`. Corpus de 36 mois,
476 stations. Évaluation avec stations **et** mois cachés simultanément.

Voici huit faits mesurés. **Pour chacun, je veux le mécanisme atmosphérique**, pas une
reformulation.

### A1 — La hiérarchie entre polluants

| polluant | gain de RMSE contre CAMS brut |
|---|---|
| NO₂ | **+36,7 %** |
| PM10 | +7,5 % |
| O₃ | +6,9 % |
| PM2,5 | +4,5 % |

**Question.** Pourquoi le NO₂ est-il de très loin le plus corrigeable ? Mon hypothèse est
que son erreur est dominée par un **défaut de résolution** — une émission très locale, un
gradient fort sur quelques centaines de mètres, une durée de vie courte — donc une erreur
*systématique par site*, apprenable. Alors que l'erreur sur l'ozone et les PM2,5 serait
dominée par des processus **régionaux et épisodiques**, donc variables dans le temps et non
apprenables depuis la position. Est-ce le bon mécanisme ? Que corrige-t-on exactement quand
on corrige un modèle de chimie-transport à 10 km sur du NO₂ ?

### A2 — La typologie de station : décisive sur NO₂, strictement nulle ailleurs

Quatre colonnes décrivant la station — densité ordinale urbain → rural, et indicatrices
fond / trafic / industriel — valent **+8,9 points sur NO₂**, et **zéro** sur O₃ et PM2,5
(intervalles de confiance contenant zéro).

**Question.** Cette dichotomie est-elle la signature attendue ? Je comprends que l'ozone se
comporte à l'inverse près du trafic — **titration par le NO** — mais j'aimerais que ce soit
posé proprement : quels régimes chimiques, quelle échelle spatiale, et pourquoi la typologie
ne capte-t-elle rien de l'ozone alors qu'elle décrit précisément les lieux où l'ozone est
*détruit* ? Devrais-je m'attendre à un effet **de signe opposé** plutôt qu'à un effet nul ?

### A3 — CAMS sous-estime le NO₂ urbain de fond de 11,6 µg/m³

**Question.** D'où vient ce biais ? Inventaire d'émissions, résolution, chimie nocturne,
profil vertical, hauteur de prélèvement ? Est-il documenté dans les évaluations publiées
de CAMS, et avec quelle amplitude ?

### A4 — Toute la contribution de la météo sur le NO₂ vient de la **pluie**

Sur l'ozone, le gain météo se répartit entre pluie, vent et rayonnement. Sur le NO₂,
**la pluie porte la totalité** du gain ; le point de rosée est redondant.

**Question.** Le lessivage humide du NO₂ est pourtant réputé faible — sa solubilité est
modeste. La pluie agit-elle ici comme **indicateur** d'autre chose : passage frontal,
ventilation, couche limite haute, réduction du trafic ? Comment démêler l'effet direct de
l'effet de proxy ?

### A5 — Les pires plis de l'ozone sont des mois d'**hiver**

Nos plis les plus dégradés sur O₃ sont novembre 2023 et février 2026, où la correction
**détériore** la prévision de 24 à 35 %.

**Question.** Pourquoi l'ozone hivernal serait-il plus difficile ? Régime limité par les
NOx plutôt que par les composés organiques volatils, faible production photochimique,
dominance de la titration et du transport, contribution stratosphérique, inversions ?
Et surtout : l'ozone hivernal a-t-il un **intérêt sanitaire ou réglementaire** ? Si la
réponse est non, je peux restreindre l'évaluation à la saison photochimique et le dire.

### A6 — Les feux apportent peu, et le sol rien

Les émissions de feux valent **+3,0 % sur les PM2,5**, avec un mécanisme confirmé mais une
anisotropie marginale. Le type de sol et la géologie ne valent **rien** — et un témoin sur
l'ozone réfute le mécanisme que j'avais supposé.

**Question.** Quelle est la contribution réelle des feux de biomasse aux PM2,5 en France
métropolitaine, et par quel chemin — feux locaux, brûlage agricole, panaches lointains
ibériques ou nord-africains ? La remise en suspension de poussières de sol est-elle une
source significative de PM2,5 en France, ou seulement de PM10 ?

### A7 — La dispersion d'ensemble est nulle comme prédicteur mais discrimine la fiabilité

La dispersion entre les membres de l'ensemble CAMS **n'améliore pas** la prévision. Mais
le gain de notre correction est **6,6 fois plus grand** dans le décile où les membres
divergent que dans celui où ils concordent.

**Question.** Est-ce le comportement attendu d'un ensemble multi-modèles ? Que signifie
physiquement une divergence entre les sept modèles de l'ensemble régional CAMS — désaccord
sur les émissions, sur la couche limite, sur la chimie ? Et pourquoi la correction
statistique en profite-t-elle autant ?

### A8 — Le modèle n'utilise **aucune** variable météorologique en production

Notre configuration déployée n'a ni température, ni vent, ni précipitation. Elle atteint
malgré tout les chiffres du tableau A1. Ajouter ERA5 apporte +7,8 % sur l'ozone — mais
ERA5 est une réanalyse, donc indisponible en prévision.

**Question.** Est-ce surprenant ? Mon interprétation est que **CAMS contient déjà la météo**,
puisqu'il est forcé par une prévision météorologique — donc la météo n'ajoute de
l'information que là où le modèle la traduit mal en concentration. Est-ce le bon cadre ?

---

## Partie B — Le régime de pollution en Occitanie

Je candidate à l'association de surveillance d'Occitanie. Je dois connaître **sa** région,
pas la France en moyenne.

1. Quels sont les **régimes de pollution caractéristiques** de l'Occitanie, et en quoi
   diffèrent-ils du reste de la France ? Je pense à l'ozone méditerranéen estival, aux
   poussières sahariennes, au chauffage au bois dans les vallées pyrénéennes, à
   l'agglomération toulousaine, au littoral et à sa brise de mer.
2. Quel rôle jouent les **circulations locales** — brise de mer et brise de terre, tramontane,
   vent d'autan, effets de vallée pyrénéens, drainage nocturne ? Lesquelles sont mal
   représentées par un modèle à 10 km ?
3. Quelles sont les **spécificités d'émission** régionales : agriculture et ammoniac,
   viticulture et produits phytosanitaires, industrie, transit autoroutier, proximité de
   l'étang de Berre et du couloir rhodanien ?
4. Existe-t-il des **études publiées propres à l'Occitanie** — campagnes de mesure,
   attribution de sources, épisodes documentés — que je devrais connaître ?
5. Quels sont les **enjeux actuels** de l'association d'Occitanie, tels qu'ils ressortent de
   ses publications : plans de protection de l'atmosphère, zones à faibles émissions,
   pesticides dans l'air, pollens, air intérieur ?

---

## Partie C — L'horizon réglementaire

1. La **directive (UE) 2024/2881** révise les normes de qualité de l'air. Quelles valeurs
   limites changent, de combien, et à quelle échéance ? Quelles conséquences concrètes pour
   les organismes de surveillance français — densité de réseau, polluants à surveiller,
   obligations de modélisation et de prévision ?
2. Elle introduit ou renforce des obligations sur les **prévisions à court terme** et
   l'information du public. Lesquelles précisément ? C'est le cœur de mon sujet.
3. Quels **polluants émergents** entrent dans le champ — particules ultrafines, carbone suie,
   ammoniac, potentiel oxydant ? Avec quel statut : surveillance obligatoire, indicative,
   ou recherche ?
4. Où en sont les **lignes directrices de l'OMS de 2021** par rapport au droit européen, et
   quel est l'écart restant ?
5. La décision d'exécution **(UE) 2026/1208** sur les aires de représentativité spatiale :
   que change-t-elle concrètement pour un réseau de mesure et pour la modélisation ?

---

## Partie D — Ce que fait une AASQA, au quotidien

1. Quelles sont ses **missions statutaires** exactes, et comment se répartissent ses moyens
   entre surveillance, prévision, information, amélioration des connaissances et
   accompagnement des décideurs ?
2. Comment s'articulent **AASQA, LCSQA, INERIS et PREV'AIR** ? Qui produit quoi, qui valide
   quoi, et où se prend la décision d'alerte ?
3. Comment fonctionne la **chaîne de décision d'un épisode** — constat, prévision, procédure
   préfectorale d'information puis d'alerte, mesures d'urgence ? Quels sont les délais réels ?
4. Quelles sont les **compétences techniques** attendues d'un profil « données et
   modélisation » dans une AASQA aujourd'hui ? Quels outils, quels langages, quelles
   pratiques ?
5. Quelles sont les **limites reconnues** des systèmes actuels, celles dont les praticiens
   parlent entre eux ? C'est là que je peux être utile, et je préfère le savoir avant.

---

## Contraintes de réponse

- **Cite tes sources.** Article, rapport, texte réglementaire, année, lien.
- **Sur la partie A, va au mécanisme.** Je n'ai pas besoin qu'on me redise mes chiffres :
  j'ai besoin de savoir *pourquoi* ils sont ce qu'ils sont, et si un praticien les trouverait
  attendus ou surprenants.
- **Dis-moi quand un de mes résultats est contre-intuitif** au regard de la littérature. Un
  résultat qui surprend un spécialiste est soit une découverte, soit un bogue — et je veux
  savoir lequel avant l'entretien, pas pendant.
- **Distingue** l'établi, le débattu, ton extrapolation.
- Réponds en français, avec les termes techniques français employés dans le métier.
