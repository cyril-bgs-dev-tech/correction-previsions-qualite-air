# 70 questions pour Grok 4.5 — la qualité de l'air telle qu'on la pratique

> À coller tel quel. ChatGPT reçoit 70 questions sur la **physico-chimie et la métrologie** :
> ne va pas là-dessus. Ton angle est le **métier** — ce qu'un prévisionniste d'AASQA sait et
> qu'aucun article n'écrit, ce qui se décide vraiment, et ce qui coince en vrai.
>
> Réponds dans l'ordre, en numérotant. Sois direct. **Quand une question repose sur une
> prémisse fausse, dis-le au lieu d'y répondre.**

---

## Ce que je sais déjà

Post-traitement des prévisions CAMS Europe (8 km) pour O₃, NO₂ et PM2,5, France, cible = résidu
à la grandeur réglementaire. 17 mois, 270 stations, validation par stations exclues. Finalité :
candidature à ATMO Occitanie.

Acquis, inutile d'y revenir : le grain d'apprentissage décide (+5,8 pts sur O₃) · les
copolluants n'ajoutent rien, deux formulations testées · la météo ERA5 rend +7,8 % mais c'est
une réanalyse · **l'observation à J−2 rend +8,9 % sur O₃ et +21,9 % sur NO₂**, déployable · le
MOS officiel de Copernicus dégrade le brut 8 mois sur 12 au grain réglementaire, dont −19,1 %
en saison ozone · généralisation spatiale solide, temporelle non démontrée.

---

## A. La salle de prévision (1-12)

1. Que fait concrètement un prévisionniste d'AASQA entre 8 h et 11 h un jour ordinaire ?
2. Et un jour d'épisode — qu'est-ce qui change dans son ordre des gestes ?
3. Sur quoi se fonde-t-il réellement pour décider : le modèle, les observations de la nuit,
   l'expérience du site, un coup de fil à un collègue ?
4. Quels écrans a-t-il sous les yeux, et lequel regarde-t-il en premier ?
5. Qu'est-ce qui le fait douter d'une sortie de modèle ?
6. Quand corrige-t-il un modèle à la main, et sur quelle base ?
7. Quelle est la part de subjectivité assumée dans une prévision publiée, et comment est-elle
   encadrée ?
8. Qu'est-ce qui l'agace le plus dans les outils qu'on lui fournit ?
9. Combien de temps a-t-il pour évaluer un nouvel outil avant de le rejeter ?
10. Qu'est-ce qui fait qu'un outil entre réellement dans la routine, plutôt que de rester une
    curiosité ?
11. Comment garde-t-il la mémoire des épisodes passés — un carnet, une base, sa tête ?
12. Quelles erreurs de prévision lui sont pardonnées, et lesquelles ne le sont pas ?

## B. La décision et ses coûts (13-24)

13. Quel est le coût réel d'une fausse alerte pour une AASQA — en crédibilité, en relations
    préfectorales, en usure du public ?
14. Et celui d'un épisode manqué ?
15. Ce rapport de coûts est-il explicite quelque part, ou reste-t-il implicite ?
16. Qui décide en dernier ressort du déclenchement — l'AASQA, la préfecture, un automatisme ?
17. Que se passe-t-il quand l'AASQA et la préfecture ne sont pas d'accord ?
18. Une procédure déclenchée puis démentie a-t-elle un coût mesurable, et lequel ?
19. Comment les seuils d'information et d'alerte ont-ils été fixés, et sont-ils contestés ?
20. Un modèle qui améliore le rappel au prix du taux de fausse alerte est-il acceptable, et à
    quel taux devient-il inacceptable ?
21. Les mesures d'urgence — circulation différenciée, réduction de vitesse — ont-elles un effet
    mesuré, et cela influence-t-il la volonté de déclencher ?
22. Quelle est la latence entre décision et effet sur le terrain ?
23. Existe-t-il une saisonnalité politique du déclenchement — élections, vacances, épisodes
    médiatisés ?
24. Comment une AASQA justifie-t-elle *a posteriori* une décision contestée ?

## C. L'institution et son écosystème (25-36)

25. Comment se répartissent les rôles entre AASQA, LCSQA, INERIS, Météo-France et le ministère ?
26. Qu'est-ce que le LCSQA valide exactement, et avec quelle latence ?
27. Que fait une AASQA que PREV'AIR ne fait pas, et réciproquement ?
28. Comment une AASQA finance-t-elle son fonctionnement, et qu'est-ce que cela contraint ?
29. Quels sont les livrables réglementaires obligatoires, et lesquels coûtent le plus cher à
    produire ?
30. Quelle est la taille typique d'une équipe technique en AASQA, et quels profils la
    composent ?
31. Quelle est la part du temps passée en développement contre exploitation ?
32. Qu'est-ce qui bloque l'adoption d'une méthode nouvelle dans ce milieu — technique, humain,
    réglementaire ?
33. Comment les AASQA échangent-elles entre elles, et existe-t-il une mutualisation des outils ?
34. Quel est le rapport de l'institution aux micro-capteurs et à la mesure citoyenne ?
35. Comment une AASQA gère-t-elle la pression médiatique pendant un épisode ?
36. Qu'est-ce qui a le plus changé dans ce métier depuis dix ans ?

## D. Ce que les données ne disent pas (37-46)

37. Quelles informations un prévisionniste possède et qu'aucune base ne contient ?
38. Quels sites du réseau sont connus pour être « bizarres », et pourquoi ces anomalies ne
    figurent nulle part ?
39. Comment sait-on qu'une station est mal placée, et que fait-on quand c'est le cas ?
40. Quelles sources locales — une usine, un port, une carrière — expliquent des motifs
    inexplicables autrement ?
41. Existe-t-il des épisodes récurrents connus des locaux et absents de toute documentation ?
42. Comment reconnaît-on un épisode importé sans attendre l'analyse chimique ?
43. Que sait-on des travaux, chantiers et déviations qui modifient temporairement le trafic ?
44. Quels événements calendaires locaux — feux agricoles, fêtes, transhumance — laissent une
    trace mesurable ?
45. Comment gère-t-on les périodes où plusieurs stations tombent simultanément ?
46. Qu'est-ce qui n'est jamais archivé et manque cruellement trois ans plus tard ?

## E. L'Occitanie en particulier (47-56)

47. Qu'est-ce qui rend la qualité de l'air occitane différente de la moyenne française ?
48. Quels sont les épisodes types de la région, par saison ?
49. Comment la géographie — Méditerranée, Pyrénées, Massif central, vallée de la Garonne —
    structure-t-elle les régimes ?
50. Toulouse et Montpellier ont-elles des signatures distinctes, et lesquelles ?
51. Quel rôle joue le transport depuis l'Espagne, la vallée du Rhône, la mer ?
52. Les zones rurales occitanes ont-elles un problème d'ozone comparable à celui du sud-est ?
53. Quels secteurs d'activité pèsent le plus sur les émissions régionales ?
54. Quelles sont les particularités du réseau de mesure occitan ?
55. Qu'est-ce qui préoccupe ATMO Occitanie aujourd'hui, au-delà du réglementaire ?
56. Quels projets récents cette AASQA a-t-elle menés, et qu'y a-t-elle appris ?

## F. Ce que je n'ai pas vu (57-64)

57. Au vu de mes résultats listés en tête, qu'est-ce qui te paraît **anormal** pour quelqu'un
    qui connaît ce métier ?
58. Le +21,9 % du NO₂ avec l'observation de la veille — un praticien le trouve-t-il évident,
    surprenant, ou suspect ?
59. Mon exclusion initiale des observations récentes révèle-t-elle une méconnaissance
    caractéristique du métier ?
60. Quelle question un ingénieur d'AASQA me poserait-il en premier, et à laquelle je ne saurais
    pas répondre ?
61. Qu'est-ce qui, dans un projet comme le mien, sonne « étudiant » plutôt que
    « professionnel » ?
62. Quel geste métier élémentaire n'ai-je manifestement pas fait ?
63. Quelle donnée publique gratuite existe et que personne n'exploite ?
64. Si tu étais prévisionniste et qu'on te présentait ce travail, quelle serait ta première
    objection ?

## G. Où va le métier (65-70)

65. Que changeront concrètement les seuils de la directive 2024/2881 en 2030 pour une AASQA ?
66. Les modèles de fondation atmosphériques — Aurora, AIFS — sont-ils regardés dans ce milieu,
    ou ignorés ?
67. Quelle compétence manque le plus aux AASQA aujourd'hui ?
68. Qu'est-ce qui sera automatisé dans cinq ans, et qu'est-ce qui ne le sera pas ?
69. Quel problème non résolu ferait la vraie différence s'il l'était ?
70. Quelle question aurais-je dû poser dans cette liste et que je n'ai pas posée ?
