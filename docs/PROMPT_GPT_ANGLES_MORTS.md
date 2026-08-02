# Prompt ChatGPT — ce que j'ignore ignorer sur la qualité de l'air

**Le problème de la question.** Demander « qu'est-ce qui m'échappe ? » produit un catalogue.
Ce qu'on ignore ignorer ne se trouve pas en listant des sujets : il se trouve en **rendant
visibles les hypothèses implicites** et en **expliquant les anomalies déjà mesurées**.

Ce prompt est donc construit à l'envers des précédents. Il donne l'**inventaire exhaustif**
de ce que le projet utilise — car une absence ne se voit que sur fond de présence — puis
soumet cinq résultats **inexpliqués** obtenus sur données réelles, qui sont autant de portes
d'entrée vers ce qui manque.

Contrainte qui fait toute la valeur : chaque angle mort proposé doit venir avec son
**symptôme observable dans mes données**. Sans cela, impossible de savoir s'il compte.

À coller tel quel.

---

> Tu es un spécialiste de la physico-chimie atmosphérique et de la surveillance
> opérationnelle de la qualité de l'air, avec une pratique de terrain et pas seulement
> bibliographique. Je te donne l'inventaire complet de ce que mon dispositif utilise et
> ignore. **Ta tâche est de trouver ce que je ne sais pas que j'ignore** — pas de me lister
> ce que je fais déjà.
>
> ## Règles de réponse — elles décident de l'utilité
>
> 1. **Chaque angle mort doit venir avec son symptôme observable dans mes données.** « Vous
>    négligez X » ne me sert à rien ; « vous négligez X, et si c'est le cas vous devriez voir
>    Y dans vos résidus » me sert énormément. Sans symptôme testable, ne le proposez pas.
> 2. **Ne me parlez pas de ce que je fais déjà** — l'inventaire ci-dessous est exhaustif,
>    relisez-le avant de répondre.
> 3. Distinguez **[publié]** (avec DOI) de **[jugement de praticien]**. Le second m'intéresse
>    autant : le savoir de terrain ne se publie pas.
> 4. Classez chaque élément par **ampleur attendue de l'effet**, pas par élégance
>    intellectuelle. Un phénomène réel à 0,2 µg/m³ ne m'intéresse pas.
>
> ## Ce que le dispositif utilise — inventaire exhaustif
>
> **Prédicteurs (52)** : concentrations prévues **CAMS Europe** du polluant cible
> (0,1° ≈ 8 km, J+1 à J+3) · météo **ERA5** (réanalyse : vent, température, humidité,
> précipitations, rayonnement, hauteur de couche limite) · **calendrier** (heure et jour de
> l'année en sinus/cosinus, jour de semaine, week-end) · **38 descripteurs de paysage**
> (occupation du sol par classes dans des disques autour de la station) · **9 descripteurs de
> relief** (indice de position topographique, rugosité, à plusieurs rayons) · **trafic
> hiérarchisé** (BD TOPO, classes d'importance routière pondérées par le nombre de voies) ·
> **population communale** · coordonnées et **type de station**.
>
> **Cible** : le résidu `observation − CAMS`, écrêté à zéro après reconstruction.
>
> **Protocole** : validation par **stations entièrement exclues**, 17 mois (août 2023 →
> décembre 2024), 476 stations métropolitaines, grandeurs réglementaires (max 8 h pour O₃,
> max horaire pour NO₂, moyenne journalière pour PM2.5).
>
> **Ce que je ne modélise pas** : PM10, SO₂, NO, COV, pollens, métaux, HAP.
> **Ce que je n'utilise pas** : observations récentes de la station, concentrations CAMS des
> **copolluants**, dispersion entre membres de l'ensemble CAMS, inventaires d'émissions,
> imagerie satellite, données de trafic **en temps réel**, chauffage, agriculture.
>
> **Ce que je sais déjà** (inutile de me le réapprendre) : la titration nocturne de l'ozone
> par le NO en milieu urbain ; l'émission d'isoprène par les chênes, exponentielle avec la
> température ; les intrusions sahariennes ; les feux ; la brise de mer ; le fait que l'indice
> ATMO est spatialisé et non calculé aux stations ; la rupture du flux ozone de l'EEA en
> France depuis juillet 2025.
>
> ## Cinq résultats que je ne sais pas expliquer
>
> Ce sont mes meilleures portes d'entrée : si une explication existe, elle désigne
> probablement ce qui me manque.
>
> **E1.** Retirer les **descripteurs de forêt** *améliore* légèrement le modèle sur l'ozone
> (−1,0 % de RMSE). L'hypothèse isoprène prédisait l'inverse.
>
> **E2.** Le **type de station** officiel (urbain / périurbain / rural / trafic / industriel)
> n'apporte **rien** au-delà d'un biais global — alors que la même information reconstruite
> par les descripteurs de paysage, elle, apporte beaucoup.
>
> **E3.** Empiler covariables de terrain **et** interpolation spatiale du résidu **dégrade**
> le modèle (+19,4 % → +16,4 %), alors que chacune prise seule apporte.
>
> **E4.** Apprendre directement le **maximum journalier** gagne 5 à 6 points, mais apprendre
> directement la **moyenne journalière** en fait perdre 1,5. L'asymétrie est nette et
> reproductible sur trois polluants.
>
> **E5.** Sous 15,9 µg/m³ d'ozone observé, CAMS **surestime de +28 µg/m³** et ma correction
> encore de **+16**. Le modèle échoue massivement dans les très faibles concentrations, bien
> plus que dans les fortes.
>
> ## Les six questions
>
> **Q1 — Mes hypothèses implicites.** Quelles hypothèses mon dispositif fait-il **sans que je
> le sache** ? Je pense notamment à ce que suppose le fait de corriger un **résidu** plutôt
> qu'une concentration, d'écrêter à zéro, de traiter chaque station indépendamment, et de
> tenir les descripteurs de paysage pour **constants sur dix-sept mois**. Lesquelles sont
> fausses, et à quel coût ?
>
> **Q2 — Les cinq énigmes.** Prends E1 à E5 dans l'ordre. Pour chacune : l'explication
> physique ou statistique la plus probable, et **ce que je devrais observer** si elle est
> juste. Si l'une révèle une variable manquante, nomme-la.
>
> **Q3 — Ce que mes variables ne peuvent pas voir.** Quels processus qui affectent réellement
> les concentrations aux stations sont **structurellement invisibles** pour mon jeu de
> prédicteurs ? Classe par ampleur, en µg/m³ si tu peux. Je cherche en particulier ce qui
> varie **dans le temps** alors que je ne le décris que par des variables statiques.
>
> **Q4 — Les données qui existent et que j'ignore.** Quelles sources ouvertes, françaises ou
> européennes, apporteraient une information que je n'ai pas — et que les gens du métier
> utilisent sans que ça se publie ? Pour chacune : ce qu'elle apporte, sa latence, et si elle
> est utilisable **à l'heure d'émission** d'une prévision.
>
> **Q5 — Le savoir de terrain.** Qu'est-ce qu'un prévisionniste d'AASQA sait, après dix ans de
> métier, qui ne figure dans aucun article ? Les régularités locales, les signaux avant-coureurs,
> les cas où les modèles se trompent toujours de la même façon. C'est la question où ton
> jugement m'intéresse plus que tes sources.
>
> **Q6 — La question que je ne pose pas.** En lisant cet inventaire, quelle question un
> spécialiste du domaine trouverait-il **anormalement absente** ? Et si mon dispositif entier
> reposait sur un cadrage discutable — corriger les sorties d'un modèle plutôt que de modéliser
> autrement — quel serait l'angle mort de ce cadrage lui-même ?
>
> **Format.** Une section par question. Pour chaque angle mort : l'effet attendu, son ampleur,
> et **le symptôme à chercher dans mes données**. Termine par les trois éléments que tu juges
> les plus importants, et par ce que tu as classé **Inconnu**.
