# Contre-revue externe — réinspection après corrections

## Verdict en cinq lignes

- Les corrections de signe, FAIRMODE, 72,8 et de distinction entre les deux piles QA ont tenu.
- Une régression bloquante subsiste : V6 retranche deux étapes et attribue à GEOS un gain qui n'est pas le sien.
- Les nouveaux `<details>` cachent plusieurs preuves, deux visuels structurants et la réserve TSAD qui devait précisément rester visible.
- La propagation est incomplète dans les badges, `index.qmd`, les pieds de page et l'introduction du dépôt QA.
- Les chemins des sept SVG sont désormais cohérents, mais leur typographie devient illisible à 380 px et les deux Mermaid n'ont pas d'alternative textuelle complète.

## ① Régressions — ce qu'une correction a cassé

### R1 — Bloquant — V6 n'est plus une décomposition fidèle

**Où / quoi.** `projets_Qualite_Air/portfolio_project.qmd`, figure V6, et `assets/qa_gain_decomposition.svg`.

**Avant / après.** La série source comporte sept états : base 26,6 ; typologie 35,6 ; membres 36,1 ; feux 36,4 ; GEOS-CF 38,7 ; tendance 38,9 ; spéciation 40,2. V6 n'en montre que cinq : base, typologie, GEOS-CF, tendance, spéciation.

**Ce qui a été perdu.** Les gains « membres » (+0,5) et « feux » (+0,3) ont disparu. Leur +0,8 est absorbé par la barre GEOS-CF, étiquetée +3,1 alors que son gain marginal est +2,3. Le total final reste juste, mais le récit causal est faux. L'alternative textuelle ne révèle pas l'omission.

**Réparation exacte.** Régénérer V6 avec les sept lignes et ces deltas : base 26,6 ; typologie +9,0 ; membres +0,5 ; feux +0,3 ; GEOS-CF +2,3 ; tendance +0,2 ; spéciation +1,3. Remplacer simultanément l'alternative textuelle par cette séquence complète.

### R2 — Bloquant — la réserve TSAD reste fausse à l'écran et la preuve contraire est cachée

**Où / quoi.** `projets_anomaly_detection_tsad/portfolio_project.qmd`.

**Avant / après.** La correction annoncée devait remplacer la supériorité universelle par le résultat exact : −0,01 au global, puis +0,03 à partir de huit variables et +0,07 à partir de vingt. Or le premier écran affirme encore que « le système obtient de meilleurs résultats que n'importe quel modèle utilisé seul ». V8, qui montre le résultat négatif, a en plus été placé dans `<details>`.

**Ce qui a été perdu.** La limite la plus importante du projet n'est plus visible sans interaction ; le lecteur voit d'abord une conclusion contredite par les chiffres. Plus bas, « la composition bat le champion » conserve la même généralisation.

**Réparation exacte.** Remplacer le paragraphe d'ouverture par : « Sur l'ensemble multivarié, le routage ne bat pas le meilleur modèle seul (−0,01). Il devient positif à partir de huit variables (+0,03) et atteint +0,07 à partir de vingt. » Déplacer V8 juste après ce paragraphe, avant `<details>`. Remplacer « la composition bat le champion » par : « La composition ne bat pas le champion sur l'ensemble multivarié ; elle ne devient positive que pour d ≥ 8. »

### R3 — Important — les `<details>` avalent les sorties qui devaient rester publiques

**Où / quoi.** `projets_Aegis/portfolio_project.qmd`, `projets_Vigilance/portfolio_project.qmd`, les deux portfolios d'anomaly detection.

**Avant / après.** Le repli devait compacter les méthodes secondaires. Dans Aegis, il englobe V9, les limites, la prochaine étape, le code source et le contact. Dans Vigilance, il englobe V2, les évolutions, le code et le contact. Dans les deux pages anomaly detection, le lien de reproduction est lui aussi replié.

**Ce qui a été perdu.** Les schémas qui expliquent le système, les réserves et les appels à l'action deviennent invisibles au premier passage. Le libellé « Détails techniques » ne décrit pas ce qu'il masque réellement.

**Réparation exacte.** Dans Aegis et Vigilance, sortir V9 et V2 de `<details>` et fermer le bloc avant respectivement `## Limites honnêtes` et `## Évolutions prévues`. Dans les pages anomaly detection, fermer le bloc avant `---` afin que le lien de reproduction et le contact restent visibles. Ne laisser repliés que les protocoles, tableaux secondaires et détails d'implémentation.

### R4 — Important — le portfolio M1 n'a plus de preuve visible

**Où / quoi.** `projets_Master_1/portfolio_project.qmd`.

**Avant / après.** Un `<details>` externe commence avant les dix projets ; un second bloc imbriqué replie les six derniers. Le premier écran ne conserve donc que le titre, le statut et une vue d'ensemble.

**Ce qui a été perdu.** Aucun projet, aucun retour d'évaluation, aucune synthèse et aucune transition vers le M2 ne sont visibles sans deux niveaux d'ouverture. La phrase « la qualité s'est nettement améliorée » reste visible, tandis que le retour contradictoire du projet 10 — soutenance confuse — est doublement caché.

**Réparation exacte.** Supprimer uniquement le `<details>` externe et sa fermeture finale ; conserver le bloc interne « Voir les six autres projets ». Remplacer l'introduction par : « Les retours confirment une base technique solide. La communication est restée un axe de progression : plusieurs projets sont jugés clairs, mais le projet 10 signale encore une soutenance confuse. »

### R5 — Important — la page compétitions replie les résultats, mais laisse la défense au premier plan

**Où / quoi.** `projets_competitions/portfolio_project.qmd`.

**Avant / après.** Les rangs nommés, dont le top 1, ont été placés dans « Détails techniques ». Les longs paragraphes sur le nombre de notebooks, la non-exclusivité et le travail agentique restent visibles avant eux.

**Ce qui a été perdu.** La hiérarchie de lecture est inversée : les précautions occupent le premier passage et les preuves sont cachées. Le bloc agentique est correctement borné, mais il arrive avant les résultats auxquels il ne contribue pas.

**Réparation exacte.** Déplacer hors du `<details>` la table compacte des quatre meilleurs résultats déjà présente dans `README.md`, puis conserver dans le bloc replié les descriptions détaillées des solutions. Placer le paragraphe agentique après cette table, sans le supprimer ni lui attribuer de classement.

### R6 — Important — les SVG ne passent pas le test demandé à 380 px

**Où / quoi.** V1 et V3 à V8, dans `assets/*.svg`.

**Avant / après.** Les figures ont des `viewBox` de 720 à 820 px, des textes souvent réglés entre 11,5 et 13,5 px, puis sont affichées à `width="100%"`. À 380 px, la réduction ramène ces textes à environ 5,5–7,1 px ; dans V4, la barre « état actuel » tombe à environ 2,6 px de haut.

**Ce qui a été perdu.** Les axes, catégories, deltas et annotations ne sont plus lisibles sur le viewport explicitement demandé. La couleur n'est pas le seul canal, mais le texte qui porte le second canal devient trop petit.

**Réparation exacte.** Régénérer les sept SVG sur une grille mobile d'environ 380 px, avec corps minimal de 13–14 px dans le `viewBox`, libellés multilignes et graphiques verticaux quand nécessaire. Laisser le navigateur agrandir ces figures sur bureau, et non les réduire sur mobile.

### R7 — Important — les deux visuels QA déséquilibrent la page d'accueil

**Où / quoi.** `README.md`, première fiche projet QA.

**Avant / après.** V1 et V3 ont été insérés tous les deux en pleine largeur dans la même fiche. V3 répète presque exactement les deux chiffres FAIRMODE déjà donnés dans la puce qui le précède.

**Ce qui a été perdu.** La première fiche devient beaucoup plus haute que les suivantes et repousse Vigilance, Aegis et les projets anomaly detection. Le visuel n'a pas remplacé du texte : il s'y ajoute.

**Réparation exacte.** Conserver V1 sur l'accueil. Déplacer le bloc V3 dans `projets_Qualite_Air/portfolio_project.qmd`, à la place de la table FAIRMODE visible, dont son alternative textuelle reprend déjà les valeurs.

### R8 — Important — une même ligne a été créée deux fois

**Où / quoi.** `about.qmd` et `projets_Master_2/portfolio_project.qmd`.

**Avant / après.** La reformulation « Rapprochement automatisé de données de pricing hétérogènes, et tests de non-régression » est immédiatement suivie de « Tests de non régression ».

**Ce qui a été perdu.** La correction du jargon a introduit une répétition et une ponctuation lourde dans deux pages.

**Réparation exacte.** Garder une seule ligne : « Rapprochement automatisé de données de pricing hétérogènes et tests de non-régression. » Supprimer la ligne isolée dans les deux fichiers.

### R9 — Confort — V5 conserve le tableau qu'il devait remplacer

**Où / quoi.** `projets_Qualite_Air/portfolio_project.qmd`, comparaison des deux piles QA.

**Avant / après.** V5 montre les deux piles et leurs scores ; le tableau de deux lignes donnant les mêmes couples est toujours placé juste après.

**Ce qui a été perdu.** Le rythme n'a pas été allégé et le lecteur rencontre deux restitutions consécutives du même message.

**Réparation exacte.** Supprimer le tableau visible et conserver V5 avec son alternative textuelle complète. Si une table machine-lisible est souhaitée, la mettre dans le bloc de détails déjà présent.

### R10 — Confort — V9 nomme le mauvais métier

**Où / quoi.** Mermaid V9 dans `projets_Aegis/portfolio_project.qmd`.

**Avant / après.** La branche « refus / correction » renvoie vers « Retour au prévisionniste », alors que la page décrit un opérateur chargé de confirmer ou corriger l'incident.

**Ce qui a été perdu.** Un terme copié du contexte de prévision brouille le rôle humain du dispositif Aegis.

**Réparation exacte.** Remplacer « Retour au prévisionniste » par « Retour à l'opérateur ».

### R11 — Important — les Mermaid n'ont pas d'alternative textuelle complète

**Où / quoi.** V2 Vigilance et V9 Aegis.

**Avant / après.** Les SVG disposent d'un `alt` précis ; les blocs Mermaid reposent seulement sur une phrase adjacente partielle.

**Ce qui a été perdu.** Le flux, ses embranchements et la validation humaine ne sont pas restitués de façon équivalente sans le diagramme.

**Réparation exacte.** Remplacer, plutôt qu'ajouter, la phrase explicative adjacente à chaque Mermaid par une phrase préfixée « Alternative textuelle : » qui énumère les entrées, le traitement, la sortie et les branches humaines. Pour V9, inclure explicitement création du brouillon, validation, refus/correction et journalisation ; pour V2, les trois flux, l'ingestion, les règles, la carte, les alertes et les livrables.

## ② Corrections incomplètes

### C1 — Important — les promesses de déploiement et le pied de page ont survécu

`README.md` contient encore le badge « Deployed on GitHub Pages », le badge « Built with Quarto » et la citation attribuée à Linus Torvalds. La correction annoncée comme transversale n'a donc pas atteint le pied de page. **Réparation :** supprimer ces trois lignes ; elles ne prouvent ni le projet ni son état de disponibilité.

### C2 — Important — deux badges contredisent encore le texte corrigé

Dans `README.md`, Vigilance affiche encore « Workers — 9 × 4 réplicas » alors que le texte indique désormais un pool de trois workers CPU et un GPU. Le badge recherche affirme encore « Reproductions exactes validées » alors que la fiche détaillée formule plus prudemment les résultats. **Réparation :** remplacer le premier par « Workers — 3 CPU + 1 GPU » et le second par « Benchmarks rejoués — protocoles documentés ».

### C3 — Important — `index.qmd` n'a pas reçu trois corrections de fond

La page conserve « 35+ compétitions complétées », « la composition bat le champion global » et « 502 jeux / 19 domaines ». La première formulation contredit « compétitions engagées » ; la seconde contredit le résultat TSAD global à −0,01 ; la troisième contredit les « 20 domaines » encore affichés sur l'accueil et dans le portfolio tabulaire. **Réparation :** appliquer les formulations corrigées de `README.md` et du dépôt TSAD ; pour le benchmark tabulaire, utiliser 19 partout puisque le dépôt détaillé et `index.qmd` concordent, ou nommer explicitement le vingtième domaine si 20 correspond à un autre périmètre.

### C4 — Bloquant — le dépôt QA s'introduit encore avec le mauvais horizon

`projets_Qualite_Air/README.md` annonce en ouverture un apprentissage « à l'échéance J0 (1–24 h) », puis présente comme résultat principal la pile J+1 (25–48 h). La convention a été corrigée dans les tableaux, pas dans la phrase qui cadre le projet. **Réparation :** remplacer l'ouverture par : « Le modèle apprend la correction observation − CAMS puis l'ajoute. Les résultats principaux ci-dessous sont à J+1, soit les heures 25–48. »

### C5 — Important — la suppression des superlatifs DELTAMU n'est pas complète

« Augmentation colossale » a disparu, mais « algorithme de niveau recherche » reste dans `README.md` et `index.qmd`. **Réparation :** employer la description factuelle « nouvel algorithme de régression régularisée » dans les deux fichiers.

### C6 — Important — l'étiquette « dix domaines » est corrigée, pas la distinction avec les dix-huit catégories

Le portfolio TSAD nomme bien dix domaines ; le README du dépôt annonce ensuite un corpus étendu de dix-huit catégories. Les deux nombres peuvent être justes, mais leur relation n'est pas expliquée. **Réparation :** remplacer la première occurrence « dix domaines » par « dix domaines dans le benchmark principal ; dix-huit catégories dans l'extension du dépôt » et ne répéter ensuite que le nombre pertinent.

### C7 — Confort — la typographie numérique reste fragmentée

Les fiches anomaly detection affichent encore `+3.0`, `72.8` ou `-0.01`, alors que les pages francisées emploient la virgule. **Réparation :** réserver le point aux clés de code et passer les nombres narratifs en `+3,0`, `72,8` et `−0,01`.

### C8 — Important — les variantes sombres ne sont pas contrôlables dans le corpus livré

Les balises `<picture>` annoncent des fichiers `*_dark.svg`, mais l'annexe ne fournit que les variantes claires. Il est donc impossible de confirmer, depuis la seule source autorisée, que données, contrastes et alternatives sont identiques. **Réparation :** joindre les sept variantes sombres à la prochaine annexe de réinspection ou indiquer qu'elles sont strictement générées depuis les mêmes données.

## ③ Ce qui reste de ma première liste, et qui compte encore

### P1 — Important — la première vue reste générique

`README.md` ouvre toujours sur « Data Scientist | MLOps Engineer | Problem Solver » puis sur « passionné », « perspective unique » et « communication efficace ». Les preuves arrivent après l'expérience et le mur de stack. **Réparation :** remplacer ce bloc par une proposition factuelle en deux lignes centrée sur les trois preuves fortes — QA de l'air, routage d'anomalies, industrialisation — et placer `## Projets phares` avant `## Expérience professionnelle`.

### P2 — Important — les jugements Michelin sont toujours auto-attribués

« augmentation considérable », « résultats jugés excellents » et « accélération considérable » subsistent dans `README.md`, `about.qmd`, `index.qmd` et la page M2. **Réparation :** conserver les transformations observables — interface Excel, automatisation, optimisation des hyperparamètres — et supprimer ces trois évaluations sans mesure ni citation.

### P3 — Important — Aegis reste simultanément en phases A/B et en gate de phase C

La table annonce « gate Phase C, 14 cas » alors que les limites disent « Phase A/B seulement ». **Réparation :** employer une formulation unique : « Prototype de trois jours : composants des phases A/B fonctionnels et banc d'entrée de phase C exécuté sur 14 cas ; aucune validation en production. »

### P4 — Important — la page M2 conserve un choix technologique non résolu

`projets_Master_2/portfolio_project.qmd` contient encore « TensorFlow/Keras ou PyTorch ». **Réparation :** nommer le framework réellement utilisé ; s'il n'est pas traçable dans le corpus, supprimer entièrement la ligne plutôt que conserver une alternative de brouillon.

### P5 — Important — le dépôt QA commence encore par son journal de rectifications

Quatre paragraphes de correction et de prudence précèdent l'explication du projet dans `projets_Qualite_Air/README.md`. **Réparation :** ouvrir par objectif, données, horizon et résultat ; déplacer l'historique de rectification dans `## Limites et auditabilité`.

### P6 — Confort — la page À propos classe encore Kaggle parmi les certifications

`about.qmd` conserve « Kaggle Competitions » sous « Certifications et Diplômes » et une ligne « Open Source » sans contribution nommée. **Réparation :** déplacer Kaggle sous « Pratique compétitive » et supprimer « Open Source » tant qu'aucune contribution précise n'est citée.

### P7 — Confort — une instruction d'auteur reste publiée comme contenu

La page QA contient encore « Citer deux chiffres, jamais un ». **Réparation :** supprimer cette phrase éditoriale ; conserver directement les deux chiffres et leur périmètre dans le paragraphe précédent.

### P8 — Confort — le comptage « 12 règles / 10 exécutables » reste obscur

Le lecteur doit encore inférer que deux règles sont structurelles ou non exécutables. **Réparation :** remplacer le libellé par « 12 contrôles définis, dont 10 règles exécutables et 2 contrôles structurels » si c'est bien le découpage retenu ; sinon ne publier que le nombre traçable.

### P9 — Confort — une coquille et des titres de travail restent visibles

La page compétitions contient « régression métique » et les deux portfolios anomaly detection gardent « Prochaines actions intelligentes ». **Réparation :** écrire « méta-modèle de régression » et raccourcir les titres en « Prochaines étapes ».

## ④ Ce qui est mieux qu'avant

- Le signe de la correction QA est désormais cohérent dans le portfolio, le dépôt et le schéma V4 ; la distinction opérationnelle entre la pile 25–48 h et l'audit 1–24 h est également explicite dans la page détaillée.
- FAIRMODE est enfin raconté sans ambiguïté : 87,9 % des sites sont sous 90 %, tandis que 96,2 % des stations sont sous 100 % ; V3 rend la différence immédiatement perceptible.
- Le benchmark tabulaire est recentré sur le bon résultat : routeur source-strict à 72,8, soit +3,0 points par rapport au KNN global. V7 expose utilement l'écart avec l'oracle sans le masquer.
- Le README du dépôt TSAD est nettement plus honnête et lisible : le −0,01 global est visible, puis les gains conditionnels à partir de huit et vingt variables sont séparés.
- Le mur de badges a été fortement réduit, les chemins relatifs des sept SVG sont cohérents avec leurs pages d'insertion, et les alternatives des SVG restituent correctement leurs nombres — à l'exception de la décomposition incomplète de V6.
