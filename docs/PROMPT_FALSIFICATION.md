# Deux prompts de falsification — casser la thèse, pas la reformuler

**Pourquoi ce format.** Une thèse validée par trois modèles qui la reformulent n'est pas
validée : elle est consensuelle. On leur donne donc la thèse **déjà écrite** et on leur
demande de la **détruire** — par antériorité (c'est déjà publié), par contre-exemple (mes
propres chiffres la contredisent), ou par inutilité (elle est vraie et ne sert à rien).

Les deux prompts sont courts. La longueur nuirait : on cherche une objection, pas un essai.

---

## Prompt 1 — ChatGPT : antériorité et falsification

> Tu es chercheur en post-traitement statistique des prévisions environnementales. Je te
> soumets une thèse tirée de mes propres mesures. **Ta tâche est de la détruire**, pas de la
> reformuler ni de l'améliorer.
>
> ## La thèse
>
> > Une correction apprise des sorties d'un modèle de chimie-transport n'améliore pas
> > uniformément ce modèle : elle apprend la **distribution conditionnelle des erreurs du
> > forçage sur la période observée**, et l'applique **inconditionnellement**. Elle gagne donc
> > quand le forçage dérive, et **nuit quand il est juste**. Cette dépendance est mesurable,
> > observable à l'émission, et corrigeable par une règle d'abstention.
>
> ## Mes trois preuves
>
> 1. **Statistique** — corrélation **+0,913**, à saison égale d'une année sur l'autre, entre
>    la dégradation du RMSE de CAMS et la hausse de mon gain. Novembre : RMSE CAMS 15,25
>    (2023) → 20,41 (2024) ; mon gain 14,3 % → 33,8 %. Deux ruptures opérationnelles CAMS
>    documentées (13/11 et 03/12/2024), et **après** chacune CAMS s'améliore tandis que mon
>    gain baisse.
> 2. **Structurel** — sur 17 mois et six configurations testées (deux jeux
>    d'hyperparamètres × trois épreuves), le pire pli temporel est **toujours novembre 2023**,
>    le mois où CAMS était le meilleur de sa saison.
> 3. **Situationnel** — le 26/07/2026, jour d'alerte PM en Occitanie : CAMS prévoit
>    **49,6 µg/m³**, l'observation est **46,8**, ma correction abaisse à **36,6**. Dégradation
>    de 12,9 µg/m³ d'une prévision juste.
>
> Contexte : correction LightGBM des prévisions CAMS Europe aux stations, France, 17 mois,
> validation par stations exclues, gains +28,9 à +34,2 % sur les grandeurs réglementaires.
>
> ## Les quatre questions
>
> **Q1 — Antériorité.** Ce phénomène est-il **déjà publié** ? A-t-il un nom ? Je cherche
> notamment du côté du *model output statistics* sous changement de modèle amont, de la
> dérive de concept par changement du générateur, et de l'évaluation de post-traitement sur
> des périodes couvrant une mise à jour opérationnelle. **Si c'est documenté, dis-le
> franchement** : ma contribution disparaît et je préfère le savoir maintenant. Donne les DOI.
>
> **Q2 — Contre-explication.** Mes trois preuves admettent-elles une explication plus simple
> que la thèse ? En particulier : la corrélation +0,913 ne serait-elle pas un simple artefact
> de **régression vers la moyenne** — plus l'erreur de départ est grande, plus une correction
> quelconque en retire ? Comment distinguer les deux avec mes données ?
>
> **Q3 — Portée.** Si la thèse est vraie, elle vaut aussi pour **PREV'AIR et toute chaîne
> opérationnelle** qui post-traite par apprentissage. Est-ce plausible, ou ma configuration
> a-t-elle une particularité qui l'expliquerait sans généraliser ?
>
> **Q4 — Inutilité.** Supposons la thèse vraie et non publiée. Est-elle **actionnable** ? Ma
> règle candidate est : *ne pas corriger à la baisse quand le forçage annonce déjà un
> dépassement*. Est-ce trop grossier pour valoir quelque chose, et que faudrait-il pour en
> faire un critère défendable ?
>
> **Format.** Une réponse par question, source ou DOI dès que tu affirmes une antériorité.
> Si tu ne trouves pas, écris **Inconnu** — c'est une réponse utile. Termine par : *la thèse
> survit / la thèse est affaiblie / la thèse est fausse*, et pourquoi.

---

## Prompt 2 — Grok : la thèse tient-elle devant un recruteur ?

> Tu es le responsable qui recrute à ATMO Occitanie. Un candidat t'a envoyé un dossier avec
> de bons chiffres. Il vient d'y ajouter une **thèse**, et te la présente comme sa
> contribution principale. Réponds en **une à trois lignes par question**, verdict d'abord.
>
> ## Sa thèse
>
> > « Ma correction n'améliore pas CAMS uniformément : elle a appris la signature des
> > défaillances de CAMS, donc elle gagne quand CAMS dérive et **nuit quand CAMS est juste**.
> > Je l'ai mesuré trois fois, et j'en tire une règle : ne pas corriger à la baisse quand
> > CAMS annonce déjà un dépassement. »
>
> Il l'appuie sur : une corrélation de **+0,913** entre dégradation de CAMS et son gain ; un
> pire mois toujours identique sur six configurations ; et un jour d'alerte réel — le
> 26/07/2026 — où CAMS prévoyait 49,6 pour 46,8 observés et où sa correction a abaissé à 36,6.
>
> Ses chiffres de performance restent bons : **+28,9 à +34,2 %** sur les grandeurs
> réglementaires, au niveau de la littérature publiée.
>
> ## Les questions
>
> 1. Cette thèse rend le dossier **plus fort ou plus fragile** ? Une phrase.
> 2. Est-ce de la lucidité, ou de l'**habillage intellectuel** d'un résultat moyen ?
> 3. Un candidat qui te dit « mon modèle nuit dans certains cas » : tu retiens la lucidité ou
>    le « nuit » ?
> 4. La règle proposée — ne pas corriger à la baisse quand CAMS annonce un dépassement —
>    est-elle **utilisable chez toi**, ou trop grossière ?
> 5. Préfères-tu ce dossier-là, ou le même sans la thèse et avec juste les +30 % ?
> 6. Le 26/07 où sa correction a dégradé une bonne prévision : ça te fait peur, ou ça te
>    rassure qu'il l'ait trouvé et publié ?
> 7. **Que ferais-tu de cette thèse** dans ton service, si elle est vraie ?
> 8. Quelle est la question que tu poserais pour la mettre en défaut ?
>
> Si une prémisse est fausse, dis-le à la question concernée.
