# Questions à ChatGPT — bonnes pratiques sur les données et modèles qu'on vient d'ouvrir

> À coller tel quel. Grok reçoit un jeu complémentaire orienté **exploitation opérationnelle** :
> n'y va pas. Ton angle est la **rigueur méthodologique** — comment ne pas se tromper avec ces
> objets précis.
>
> Quand une question repose sur une prémisse fausse, dis-le au lieu d'y répondre.

---

## Ce qui vient de changer

Trois sources se sont ouvertes en vingt-quatre heures, et je n'ai jamais travaillé avec aucune
des trois dans ce projet.

| source | ce qu'on en a | état |
|---|---|---|
| **Membres de l'ensemble CAMS** | 6 modèles — CHIMERE, EMEP, MOCAGE, SILAM, LOTOS-EUROS, MATCH — O₃ horaire, grille 0,1°, **16 mois sur 17** (nov. 2023 manquant, HTTP 400) | téléchargé, **4,6 Go**, non extrait |
| **GFAS** | puissance radiative des feux + flux de PM2,5, 0,1°, quotidien, 2003 → **03/12/2025** | passe unitaire en cours |
| **IFS et AIFS** via seau AWS | prévisions physique **et** neuronale, 0,25°, surface + 13 niveaux de pression, depuis le 18/01/2023, lecture par **plage d'octets** | chaîne validée de bout en bout |

Le reste du projet, pour situer : correction du résidu `observation − CAMS` à la grandeur
réglementaire, 270 stations, validation par stations exclues. Meilleur résultat actuel — à
budget de fausses alertes égal, **3,6 fois plus de dépassements d'ozone détectés** que CAMS
brut, facteur reproduit hors fenêtre d'apprentissage.

---

## A. La dispersion d'ensemble (1-12)

Nous n'avions que la **médiane** des 11 modèles ; nous avons maintenant 6 membres individuels.

1. Quelle **statistique de dispersion** est la moins mauvaise avec seulement 6 membres —
   écart-type, étendue interquartile, étendue totale, écart médian absolu ? Et laquelle est
   biaisée par un si petit effectif ?
2. La dispersion d'un ensemble **multi-modèle** (modèles différents) ne mesure pas la même
   chose que celle d'un ensemble **perturbé** (mêmes équations, conditions initiales
   différentes). Qu'est-ce que la première capture réellement, et qu'ignore-t-elle ?
3. Quelle relation empirique entre dispersion et erreur est documentée en qualité de l'air ?
   Est-elle assez forte pour servir d'indicateur d'incertitude, ou notoirement faible ?
4. Comment tester correctement cette relation — corrélation dispersion/|erreur| par bandes,
   diagramme de fiabilité, autre ?
5. Un ensemble multi-modèle est typiquement **sous-dispersif**. Comment le diagnostiquer, et
   faut-il le corriger avant d'utiliser la dispersion comme variable ?
6. Six membres sur onze : le sous-échantillonnage biaise-t-il la dispersion, et dans quel sens ?
   Faut-il un facteur correctif ?
7. Vaut-il mieux donner au modèle les **6 valeurs brutes**, ou des **résumés** (médiane,
   dispersion, min, max) ? Le gradient boosting peut-il exploiter les 6 sans surajuster ?
8. Le **désaccord entre modèles n'est pas symétrique** : un modèle systématiquement haut n'a
   pas le même sens qu'un désaccord aléatoire. Quelle statistique distingue les deux ?
9. Nous cherchons un signal de dérive **ex ante** — disponible avant l'observation — pour
   remplacer une stratification par l'erreur réalisée, qui est mathématiquement couplée
   (`ΔMSE = 2em − m²`). La dispersion d'ensemble est-elle un bon candidat, et comment le
   vérifier sans retomber dans le même couplage ?
10. Les membres partagent conditions aux limites et météo. Leur désaccord sous-estime donc
    l'incertitude totale — de combien, d'après la littérature ?
11. Existe-t-il un risque de **fuite** en utilisant la dispersion comme prédicteur, si certains
    membres assimilent des observations de surface ?
12. Que dit la littérature sur les **poids** de combinaison d'un ensemble multi-modèle en
    qualité de l'air, et faut-il les apprendre ou rester sur la médiane ?

## B. Les feux comme sources ponctuelles (13-24)

Un feu a des coordonnées, une puissance et une date. Nous avons une fonction d'exposition
anisotrope conditionnée au vent, écrite et testée, jamais utilisée faute de sources géolocalisées.

13. Quelle **grandeur** de GFAS employer — puissance radiative, flux de PM2,5, flux de matière
    sèche ? Laquelle est la plus directe et laquelle ajoute une hypothèse de facteur d'émission ?
14. Sur quelle **échelle de distance** un panache de combustion affecte-t-il les concentrations
    de surface en Europe ? Donne des ordres de grandeur publiés.
15. Un panache s'élève : la **hauteur d'injection** décide s'il touche le sol ou passe au-dessus.
    GFAS la fournit-elle, et comment la traiter si non ?
16. Quelle **décroissance** avec la distance est physiquement justifiée — exponentielle,
    puissance, gaussienne ? Et quelle longueur caractéristique ?
17. Le **secteur au vent** doit-il être calculé avec le vent de surface ou le vent de la couche
    de transport ? Notre extraction ERA5 n'a que le vent à 10 m.
18. Quel **délai** entre émission et arrivée doit-on modéliser ? Un feu à 300 km n'affecte pas
    la station le même jour.
19. Comment éviter de fabriquer une variable qui **corrèle avec la saison** plutôt qu'avec les
    feux — les feux étant concentrés en été, comme l'ozone ?
20. Quel **contrôle négatif** poserait-tu pour vérifier qu'un gain vient bien des feux et non
    d'un artefact saisonnier ?
21. CAMS **ingère déjà** GFAS en conditions aux limites. Ajouter les feux au correcteur est-il
    donc redondant, et si non, pourquoi — latence d'assimilation, résolution, hauteur
    d'injection ?
22. Quelle est la **latence** réelle de GFAS, et une prévision à J+1 peut-elle contenir un feu
    allumé la veille ?
23. Les feux sont **rares** : quelle part des jours-station est concernée en France, et cela
    suffit-il à mesurer un effet ?
24. Comment évaluer proprement un gain qui ne s'applique qu'à une petite fraction des cas —
    l'évaluer sur tout le corpus le noierait.

## C. Le modèle spécialiste de régime (25-33)

L'idée testée : un modèle « situation habituelle » et un modèle « situation de feu », choisis
selon un détecteur.

25. Ce projet a déjà mesuré qu'un **modèle dédié aux journées anormales perd** (14,70 contre
    13,32 pour le modèle général). Qu'est-ce qui rendrait un spécialiste « feu » différent —
    ou faut-il s'attendre au même échec ?
26. Quelle taille minimale d'échantillon pour qu'un spécialiste batte un généraliste sur son
    propre régime ?
27. Vaut-il mieux **deux modèles et un routeur**, ou **un modèle avec l'indicateur de régime en
    variable** ? Que dit la littérature sur cet arbitrage ?
28. Comment évaluer un système à routeur **sans fuite** — le routeur doit-il être appris dans
    chaque pli ?
29. Un mélange d'experts pondéré vaut-il mieux qu'un choix dur ? Et comment calibrer les poids ?
30. Quel **critère d'arrêt** appliquer : si le spécialiste gagne sur son régime mais que le
    routeur se trompe, le système perd. Comment décomposer ces deux erreurs ?
31. Quelle est la bonne **définition d'un régime feu** — un seuil de puissance radiative amont,
    une exposition anisotrope, une composition d'aérosol ?
32. Un système à deux modèles est plus difficile à exploiter et à déboguer. Quel **gain minimal**
    justifierait cette complexité, selon la pratique du domaine ?
33. Existe-t-il des travaux publiés sur la correction de biais **conditionnée au régime feu** en
    qualité de l'air ? Que concluent-ils ?

## D. Modèles de fondation et prévisions neuronales (34-42)

34. Que sait-on de la **structure d'erreur** d'AIFS comparée à IFS — biais, dispersion,
    comportement dans les extrêmes ?
35. Un modèle neuronal **lisse-t-il** davantage ? Si oui, est-ce documenté quantitativement, et
    à quelles échéances ?
36. Ce projet a mesuré que l'écrasement de la variabilité coûte cher aux **statistiques d'ordre**
    (maxima). Un conditionnement par AIFS serait-il donc structurellement inférieur pour
    prédire un maximum ?
37. **Aurora** a une variante affinée sur les analyses CAMS, annoncée égalant ou dépassant CAMS
    sur 74 % des cibles. Sur quel grain cette comparaison est-elle faite, et survivrait-elle au
    maximum journalier 8 h ?
38. Un modèle affiné sur les **analyses** CAMS hérite-t-il de ses biais ? Comment le tester ?
39. Quelle est la bonne façon de comparer une prévision neuronale et une prévision physique **à
    armes égales** — mêmes échéances, mêmes stations, mêmes dates ?
40. Utiliser AIFS **et** IFS comme deux prédicteurs distincts a-t-il un sens, ou leur désaccord
    est-il le seul signal utile ?
41. Quels **pièges d'évaluation** propres aux modèles de fondation dois-je connaître — fuite par
    pré-entraînement sur des périodes que je crois hors échantillon, notamment ?
42. Aurora est-elle utilisable **en inférence** sans conditions initiales globales complètes ?

## E. Protocole d'ensemble (43-50)

43. J'ajoute trois familles de variables en peu de temps — dispersion d'ensemble, feux, météo
    prévue. Quel risque de **multiplicité** cela crée-t-il, et comment le contrôler sans tuer la
    puissance ?
44. Dans quel **ordre** les tester, pour que chaque mesure reste interprétable ?
45. Faut-il un jeu de **validation gelé** réservé au test final, distinct des plis
    d'exploration ? Comment le constituer sans perdre trop d'effectif ?
46. Mon critère d'arrêt est en **µg/m³ absolus** (0,3), appliqué à des polluants dont le RMSE
    varie d'un facteur 5. Quelle forme relative recommandes-tu, et avec quel seuil ?
47. Comment **pré-enregistrer** honnêtement une analyse quand on découvre les données en même
    temps qu'on les analyse ?
48. Quel est le bon **contrôle négatif** systématique — une variable aléatoire de même
    structure, une permutation de dates ?
49. Un mois manque à l'ensemble (novembre 2023, HTTP 400). Quel effet sur une mesure saisonnière,
    et faut-il l'exclure partout pour rester comparable ?
50. Si tu ne devais garder qu'**une** de ces trois pistes — ensemble, feux, météo prévue — au vu
    de ce que le projet a déjà mesuré, laquelle, et pourquoi ?
