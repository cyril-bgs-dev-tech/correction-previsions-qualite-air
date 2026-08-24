# Brief — arbitrage exécutif sur une nuit de travail autonome

**Ce que je te demande :** juger *comment j'ai réparti mon action*, pas la qualité
statistique de mes mesures. Sur douze heures autonomes, **47 commits sur 60 ont corrigé un
défaut ou posé un garde-fou ; 13 seulement portent un résultat.** Est-ce le bon ratio, ou
ai-je confondu rigueur et productivité ? Et si c'est le bon, à quoi le reconnaît-on avant
la fin plutôt qu'après ?

Réponds en français. Tu n'as pas accès au dépôt : tout ce qu'il faut est ici.

---

## 1. Le contexte, en dix lignes

Post-traitement statistique des prévisions de qualité de l'air CAMS Europe à J+1, sur
quatre polluants (NO₂, O₃, PM10, PM2,5). Modèle : LightGBM sur ~110 colonnes, entraîné
sur la France, évalué en **double aveugle — station ET mois cachés simultanément**, 24 à
33 plis mensuels.

Deux périmètres : **PARTOUT** (spatialisation, aucune observation à l'inférence — la
contrainte fondatrice) et **AUX STATIONS**. Gains actuels en PARTOUT : NO₂ 41,5 %,
O₃ 20,5 %, PM10 21,4 %, PM2,5 14,0 % contre CAMS brut.

Le projet est une vitrine de candidature **déjà envoyée** (22/08). Le travail actuel vise
à améliorer les scores et à tenir devant un entretien technique. Une seule machine, un
opérateur, pas d'équipe.

---

## 2. Ce que la nuit a produit, chiffré

| | |
|---|---|
| commits | **60** |
| dont portant un résultat de mesure | **13** |
| dont corrigeant un défaut ou posant un garde | **47** |
| lignes de code ajoutées | **+5 443** sur 46 fichiers |
| tests | 296 → **312** |
| mécanismes exécutables nouveaux | **6** |
| mesures lancées en fond | 23 + 16 tâches CPU, 19 mois d'acquisition réseau |
| prédictions scellées avant mesure | 8, dont 5 résolues — **calibration 3/5** |

### Les 13 résultats

1. **Le corpus était troué** — 5 mois de spéciation manquaient sur 29. Complétés, la base
   monte de **0,17 à 0,32 pt** : c'était de la performance apparente tirée d'un indicateur
   de date.
2. **Deux familles « démontrées » tombent** — `fourier` passe de ✅ à 🔴, `tendance` cesse
   d'être réfutée. Il ne reste que `typologie` (+3,53 pt) et `geoscf` (+0,51).
3. **Sensibilité mesurée** — 0,14 % de données en plus déplacent un pli de **2,56 pt**,
   contre ≤ 0,039 pt à données identiques. Soit **65 ×** le bruit d'exécution.
4. **Retirer `geoscf`+`membres` coûte** — +0,55 à +1,39 pt, 4 polluants sur 4, tous résolus.
5. **Retirer `feux`+`tendance` ne coûte rien** — et PM2,5 y **gagne** 0,71 pt.
6. **La chimie CAMS tient sur l'ozone seul** — +1,17 pt, 9 blocs positifs sur 9. Un
   polluant ne fait pas un mécanisme, donc pas de promotion.
7. **Chimie et précurseurs se recouvrent** — R² de 0,42 à 0,62, leurs apports ne
   s'additionnent pas.
8. **Les précurseurs ne tiennent plus** sur le corpus corrigé, et l'ordre de leurs deux
   configurations s'inverse.
9. **Le changement d'étalon ozone est non détecté** à ±2,70 pt sur 12 mois — mais pas
   *écarté*, la littérature situant l'effet vers 1 %.
10. **Le criblage ne consomme pas le budget** — la conjonction partielle est 34 × plus
    sévère que son seuil nominal.
11. **Résolution du protocole** : ±0,36 à ±0,48 %.
12. **L'archive ECMWF bride après ~1 Go**, deux miroirs alternés résolvent.
13. **Les niveaux verticaux CAMS sont indisponibles** (niveau 0 ✅, niveau 100 m ❌ 400).

### Les 6 mécanismes

| mécanisme | ce qu'il rend impossible |
|---|---|
| empreinte de corpus + empreinte des entrées | comparer deux corpus sans le savoir |
| `pids_de.sh` | un garde de processus qui se voit lui-même |
| contrôle des heures par jour | un jour amputé écrit sous son nom définitif |
| garde de classification | une colonne du « socle » absente d'un tiers des mois |
| couverture en deux passes | confondre colonne d'époque et mois amputé |
| passes de rattrapage patientes | abandonner un pas que le service sert en 0,4 s |

---

## 3. Mes cinq décisions exécutives, à juger

### ① J'ai arrêté le programme prévu pour poursuivre un défaut

Le plan de la nuit était : mesurer trois nouvelles familles de variables. À la troisième
heure, j'ai découvert que le corpus était troué et **j'ai tout régénéré** — 23 tâches, ~8 h
de calcul — au lieu de continuer à mesurer.

*Justification que je me suis donnée :* un apport mesuré sur une base incomplète ne se
transpose pas, et la suite l'a confirmé (deux familles démontrées sont tombées).

*Ce qui me gêne :* je n'avais aucune garantie **avant** de régénérer que l'effet serait
matériel. J'ai engagé huit heures de calcul sur une intuition. Le fait qu'elle se vérifie
ne dit pas que la décision était bonne — elle aurait pu ne rien déplacer.

**Question 1.** Existe-t-il un test bon marché qui aurait donné l'ordre de grandeur du
déplacement avant d'engager la régénération complète ? Et plus généralement : comment
décide-t-on de refaire *tout* plutôt qu'un échantillon, quand l'échantillon coûte 30 min et
le tout huit heures ?

### ② J'ai construit six garde-fous au lieu de mesurer

Chaque défaut trouvé a donné lieu à un mécanisme, souvent avec des tests. Cela a consommé
la majorité de la nuit.

*Justification :* le projet a une méta-règle explicite — « une règle violée deux fois
devient du code, ou elle disparaît » — et cinq des défauts de cette nuit étaient des
récurrences de règles écrites.

*Ce qui me gêne :* trois de ces mécanismes n'ont encore **jamais rien attrapé**. Deux
autres ont attrapé mes propres erreurs commises quelques minutes plus tôt, ce qui est
peut-être un signe que j'allais trop vite plutôt qu'un signe que le garde était utile.

**Question 2.** Comment distinguer un garde-fou qui paie d'un garde-fou qui rassure ?
Existe-t-il un critère utilisable *au moment de l'écrire*, avant de savoir s'il attrapera
quelque chose ?

### ③ J'ai laissé deux ressources tourner en parallèle et travaillé pendant

Une file CPU (un lot LightGBM à la fois — trois concurrents s'effondrent d'un ordre de
grandeur, mesuré) et une acquisition réseau (84 % d'attente serveur, aucun cœur consommé).
Pendant qu'elles tournaient, j'écrivais du code.

*Ce qui me gêne :* j'ai interrompu et relancé les files **six fois** pour y intégrer des
correctifs. Chaque relance a coûté du travail refait, et deux fois j'ai cassé la chaîne en
modifiant du code qu'elle allait charger.

**Question 3.** Quelle est la bonne discipline ? Geler le code pendant qu'une file tourne
et accumuler les correctifs, ou corriger au fil de l'eau en acceptant les casses ? Le
projet a déjà une règle « on ne modifie pas un script shell pendant qu'il s'exécute », mais
elle ne dit rien du code Python qu'une file **future** chargera.

### ④ J'ai scellé 8 prédictions avant mesure, et j'en ai raté 2

Le registre horodate et empreinte chaque prédiction, et exige de nommer ce qui la
réfuterait. **Calibration : 3 tenues sur 5 résolues.**

*Le signal qui m'intéresse :* les **deux démenties portaient sur la structure du code** —
combien de mois sortiraient d'une règle que je venais d'écrire — et les **trois tenues sur
des effets** — un apport coûtera-t-il.

**Question 4.** Ce contraste est-il informatif ou est-ce du bruit sur cinq points ? Et si
c'est informatif, qu'en fait-on : prédire moins souvent sur la structure, ou prédire plus
souvent pour se calibrer ?

### ⑤ J'ai écrit 60 messages de commit longs et narratifs

Chacun raconte le défaut, son coût, ce qui l'a démasqué, et ce qui le rend impossible.
Certains font vingt lignes.

*Justification :* le dépôt est une pièce de candidature qu'un ingénieur d'ATMO consultera,
possiblement via un agent.

*Ce qui me gêne :* c'est du temps qui ne mesure rien, et je ne sais pas si un lecteur
extérieur les lira ou les trouvera bavards.

**Question 5.** Pour ce lectorat — un ingénieur en modélisation, peut-être assisté d'un
agent — cette densité narrative aide-t-elle ou nuit-elle ? Y a-t-il une forme qui donne le
même signal pour moins de mots ?

---

## 4. Les trois objectifs suivants, et leur ordre actuel

1. **Criblage IFS** — la pile ne porte **aucune météo**. L'IFS est une *prévision*, donc
   déployable, contrairement à ERA5 dont le projet ne se sert que comme plafond. Mesuré en
   juillet sur une pile plus faible : +2,2 % NO₂, +5,5 % O₃, +4,7 % PM2,5 — et sur PM2,5 il
   **bat** ERA5. Sa valeur se concentre sur le périmètre PARTOUT.
2. **Promouvoir la chimie et mesurer son apport conjoint** avec les précurseurs, puisqu'ils
   se recouvrent à moitié.
3. **Finir la propreté d'époque** — quatre familles portent encore des mois entièrement
   absents ; `feux` en manque 34 %, tous en 2025.

**Question 6.** Cet ordre est-il défendable ? Le premier est le seul qui puisse ajouter de
l'information neuve ; les deux autres consolident. Faut-il au contraire finir de consolider
avant d'ajouter, sachant que chaque ajout sur une base sale devra être re-mesuré ?

---

## 5. La question que je ne sais pas me poser

Douze heures autonomes ont produit **un corpus corrigé, six garde-fous, deux familles
démontrées tombées, et zéro point de score gagné**. Les scores ont *monté* de 0,3 pt, mais
c'est une correction, pas un gain : la performance d'avant était en partie fausse.

**Question 7.** Est-ce un succès ou un échec ? Et surtout : *quelle mesure aurais-je dû
suivre* pour le savoir sans attendre la fin ? Le nombre de résultats ? Le nombre de défauts
trouvés ? La réduction d'incertitude sur les chiffres publiés ? Autre chose ?

---

## 6. Ce dont je dispose pour agir

* une machine (32 cœurs, RTX 5090, 70 Go libres) et deux ressources sérialisables ;
* un plan d'expérience à 24-33 plis, résolution ±0,4 pt, plancher de `p` à 0,0117 sur
  8 blocs ;
* ~2 h par famille de variables à mesurer sur quatre polluants ;
* un registre de prédictions, un rapport de synthèse, une mémoire persistante ;
* aucune contrainte de délai depuis l'envoi de la candidature.

**Sois direct.** Si tu penses que j'ai passé la nuit à polir un instrument au lieu de
mesurer, dis-le et dis à quoi j'aurais dû le voir.
