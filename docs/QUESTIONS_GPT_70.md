# 70 questions pour ChatGPT — comprendre la qualité de l'air, pas seulement la prédire

> À coller tel quel. Réponds dans l'ordre, en numérotant. Une réponse courte et sourcée vaut
> mieux qu'un développement. **Quand tu ne sais pas, écris-le** — une incertitude nommée m'est
> plus utile qu'une affirmation lisse.

---

## Ce que je sais déjà, pour que tu ne me le répètes pas

Post-traitement des prévisions CAMS Europe (0,1° ≈ 8 km) pour O₃, NO₂ et PM2,5, en France,
cible = résidu `observation − CAMS` à la grandeur réglementaire du polluant. 17 mois,
270 stations, validation par stations entièrement exclues.

**Mesuré et acquis** — inutile d'y revenir :

- le **grain d'apprentissage décide** : apprendre directement le max 8 h plutôt que corriger
  l'horaire puis agréger vaut +5,8 points sur O₃, +6,5 sur NO₂, **−1,5 sur PM2,5** (dont le
  grain réglementaire est une moyenne) ; publié par Bertrand et al. 2023 ;
- **les copolluants n'ajoutent rien** : concentrations brutes +0,069 µg/m³ (IC contenant zéro),
  et la formulation chimique correcte — Ox molaire, fraction de partition, résumés nocturnes —
  fait **pire** (−0,076) ;
- **la forêt dégrade** : la retirer améliore le modèle de 1,9 % ;
- **la météo aide** : ERA5 rend +7,8 % (O₃), +6,7 % (PM2,5), +2,7 % (NO₂), queue meilleure
  partout — mais c'est une réanalyse, donc un plafond ;
- **l'observation à J−2 rend +8,9 % (O₃) et +21,9 % (NO₂)**, déployable ;
- le **calendrier** est la variable la plus utile sur O₃ (+9,1 % si retirée) ;
- généralisation **spatiale** solide (+29,7 %, σ 1,2), **temporelle** non démontrée
  (prospectif strict +6,3 %, mais +1,1 % seulement en saison ozone) ;
- divergence intra-maille : 3,61 µg/m³ en médiane horaire, 6,1 en moyenne journalière.

Ma lecture provisoire : *une correction n'ajoute que là où le modèle amont est aveugle à
lui-même.* Tu m'as déjà dit qu'elle est trop absolue comme conclusion scientifique — je la
garde comme règle d'allocation de l'effort.

---

## A. La chimie de l'ozone (1-12)

1. Sur le domaine français, quelle fraction du territoire est en régime limité par les NOₓ et
   quelle fraction par les COV, et comment cela varie-t-il entre l'été et l'hiver ?
2. Quelles observations disponibles gratuitement permettraient de **diagnostiquer** ce régime,
   station par station, sans colonne satellitaire ?
3. Pourquoi l'ozone rural dépasse-t-il l'ozone urbain, et quelle est l'amplitude typique de cet
   écart en France ?
4. Quelle est la durée de vie de l'ozone dans la couche limite en été, et que cela implique-t-il
   sur la distance de transport pertinente pour une prévision à J+1 ?
5. Comment la production d'ozone dépend-elle de la température au-delà de l'effet sur la
   photolyse — que fait exactement le PAN ?
6. Qu'est-ce que le « week-end effect » sur l'ozone, dans quel sens joue-t-il, et est-il
   observable en France ?
7. Quel rôle joue l'ozone importé — fond hémisphérique, stratosphère, transport
   transatlantique — dans les épisodes français, et comment le distinguerait-on du local ?
8. Pourquoi les modèles de chimie-transport sous-estiment-ils typiquement les pics d'ozone, et
   sur-estiment-ils les valeurs basses ?
9. Le dépôt sec d'ozone sur la végétation dépend de l'ouverture stomatique. Quelles conditions
   la ferment, et quel effet cela a-t-il sur les concentrations en période de sécheresse ?
10. Que se passe-t-il chimiquement lors d'une canicule, qui n'est pas simplement « plus de
    soleil et plus de chaleur » ?
11. Quelle est l'échelle spatiale de corrélation de l'ozone MDA8 en France — à partir de quelle
    distance deux stations deviennent-elles indépendantes ?
12. Les incendies — français ou importés — laissent-ils une signature reconnaissable dans
    l'ozone, distincte de celle dans les particules ?

## B. NO₂ et les oxydes d'azote (13-22)

13. Quelle est la durée de vie du NO₂ dans la couche limite, en hiver et en été, et qu'est-ce
    qui la contrôle ?
14. Comment le rapport NO/NO₂ évolue-t-il avec la distance à une source routière, et sur quelle
    échelle spatiale ?
15. Pourquoi une maille de 8 km sur-estime-t-elle systématiquement le NO₂ de fond et le
    sous-estime-t-elle en proximité trafic ?
16. Qu'est-ce que la « rue canyon » change quantitativement aux concentrations, et existe-t-il
    un paramètre géométrique simple qui le prédit ?
17. Les évolutions du parc automobile — normes Euro, part du diesel, électrification — ont-elles
    produit des ruptures datables dans les séries de NO₂ français ?
18. Quelle part du NO₂ urbain vient du chauffage plutôt que du trafic, et comment cela
    varie-t-il en hiver ?
19. Pourquoi le NO₂ est-il le polluant où les modèles ont le plus mauvais R², et est-ce
    réductible autrement que par la résolution ?
20. Quelles émissions de NOₓ sont les plus mal représentées dans les inventaires — navires,
    engins de chantier, agriculture, aviation au sol ?
21. Le NO₂ mesuré par les analyseurs à chimiluminescence souffre d'une interférence connue.
    Quelle est son ampleur, et biaise-t-elle nos observations de référence ?
22. Existe-t-il une saisonnalité du NO₂ indépendante des émissions, purement météorologique ?

## C. Particules (23-34)

23. Quelle est la composition typique des PM2,5 en France, par saison et par région, et quelle
    fraction est **secondaire** ?
24. Le nitrate d'ammonium est semi-volatil. À quelle température bascule-t-il, et quelles
    conséquences pour les épisodes de printemps ?
25. Pourquoi les épisodes de particules de mars-avril en France sont-ils si particuliers, et
    quel rôle joue l'agriculture ?
26. Quelle est la contribution du chauffage au bois aux PM2,5 hivernales, et comment se
    reconnaît-elle dans les données ?
27. Comment distingue-t-on, à partir des seules mesures disponibles, un épisode importé
    (poussières sahariennes, feux) d'un épisode local ?
28. Les sels de mer contribuent-ils significativement aux PM2,5 sur la façade méditerranéenne,
    et cela perturbe-t-il la comparaison modèle-mesure ?
29. Quelle est la relation empirique entre PM10 et PM2,5 en France, et est-elle stable ?
30. Pourquoi les modèles peinent-ils davantage sur les PM2,5 que sur les PM10, ou l'inverse ?
31. L'humidité relative affecte-t-elle la mesure des particules, et les corrections normatives
    sont-elles homogènes entre réseaux ?
32. Quel rôle joue la couche limite nocturne dans les épisodes hivernaux, et quelle hauteur
    est critique ?
33. Existe-t-il des traceurs simples, mesurés en routine, qui identifient la source dominante
    d'un épisode de particules ?
34. Que sait-on de la formation d'aérosol organique secondaire en France, et est-elle
    représentée dans CAMS ?

## D. Météorologie et transport (35-45)

35. Quelles configurations synoptiques produisent les épisodes de pollution en France, et
    combien de types distincts faut-il pour les couvrir ?
36. Quelle définition opérationnelle d'un « jour de stagnation » est utilisée en Europe, avec
    ses seuils exacts ?
37. Comment la hauteur de couche limite se dérive-t-elle d'un profil vertical, et quelles
    méthodes divergent le plus ?
38. Le coefficient de ventilation est-il un bon prédicteur pour les trois polluants, ou
    seulement pour les primaires ?
39. Quelles brises — de mer, de vallée, de pente — modifient significativement la qualité de
    l'air en Occitanie, et à quelle échelle temporelle ?
40. Le mistral et la tramontane ont-ils un effet documenté et quantifié sur l'ozone et les
    particules ?
41. Comment les inversions de vallée se forment-elles et se rompent-elles, et existe-t-il un
    indicateur simple de leur rupture ?
42. Que valent les rétro-trajectoires pour attribuer une origine à un épisode, et à quelle
    latence sont-elles calculables ?
43. Quelle est l'erreur typique d'une prévision IFS à J+1 sur la température à 2 m, le vent à
    10 m et la hauteur de couche limite en Europe ?
44. Un modèle de prévision neuronal — AIFS, GraphCast — lisse-t-il les extrêmes davantage
    qu'un modèle physique, et est-ce documenté quantitativement ?
45. Le changement climatique modifie-t-il déjà la statistique des épisodes en France de façon
    détectable sur vingt ans ?

## E. Métrologie et données (46-55)

46. Quelle est l'incertitude de mesure d'un analyseur de référence pour O₃, NO₂ et PM2,5, et
    comment se compare-t-elle à l'erreur de nos modèles ?
47. Que dit la littérature sur la **représentativité spatiale** d'une station de fond urbaine,
    et quelles valeurs sont publiées ?
48. Comment les stations sont-elles classées — fond, trafic, industrielle — et cette
    classification est-elle homogène entre pays européens ?
49. Quels artefacts connus affectent les séries longues : changement d'analyseur, déplacement
    de station, changement de méthode de référence ?
50. Comment détecte-t-on un capteur dérivant ou gelé sans intervention humaine ?
51. Que valent les micro-capteurs bas coût aujourd'hui, et sont-ils utilisables en entrée d'un
    modèle de correction ?
52. Quelles données satellitaires — TROPOMI, MODIS — sont exploitables pour la qualité de
    l'air de surface, et avec quelle latence ?
53. Quelle est la latence réelle de publication des observations dans le réseau français, et
    quelle part est validée à J+1 ?
54. Les données horaires « temps réel » diffèrent-elles des données validées, et de combien ?
55. Existe-t-il des jeux de données de référence en France pour la composition chimique des
    particules, exploitables gratuitement ?

## F. Modélisation et post-traitement (56-64)

56. Quelle est la structure d'erreur typique d'un modèle de chimie-transport : biais constant,
    erreur de phase, erreur d'amplitude ? Comment les sépare-t-on ?
57. Que sait-on de la propagation d'erreur des émissions vers les concentrations — quel facteur
    d'amplification ?
58. Les inventaires d'émissions ont une incertitude. Laquelle, par secteur, et quelle en est la
    conséquence sur une prévision ?
59. Comment les profils temporels d'émission sont-ils construits, et à quel point sont-ils
    datés ?
60. Quelles méthodes d'assimilation de données sont employées en qualité de l'air, et
    qu'apportent-elles par rapport à un post-traitement ?
61. Un modèle qui corrige les résidus apprend-il quelque chose de transférable à un autre
    modèle amont, ou seulement les défauts de celui-ci ?
62. Que se passe-t-il quand le modèle amont est mis à jour — combien de temps un
    post-traitement reste-t-il valide ?
63. Quelles métriques la communauté considère-t-elle comme trompeuses en qualité de l'air, et
    lesquelles sont sous-utilisées ?
64. Existe-t-il des travaux sur la correction de biais **conditionnelle au régime météo**, et
    que concluent-ils ?

## G. Ce que je risque d'ignorer (65-70)

65. Quel phénomène important en qualité de l'air un data scientist venu d'un autre domaine
    ignore-t-il presque systématiquement ?
66. Quelle erreur d'interprétation revient le plus souvent dans les articles de post-traitement
    de qualité de l'air ?
67. Si tu devais me poser **une** question pour vérifier que je comprends vraiment mon objet,
    laquelle ?
68. Quelles trois publications récentes devrais-je avoir lues et n'ai probablement pas lues ?
69. Qu'est-ce qui, dans mes résultats listés en tête, te paraît **anormal** au regard de ce que
    la littérature rapporte — et donc mérite une vérification ?
70. Quelle question aurais-je dû te poser dans cette liste et que je n'ai pas posée ?
