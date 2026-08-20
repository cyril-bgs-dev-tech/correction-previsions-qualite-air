# Audit design, UX et récit graphique du portefeuille

## Les trois choses à faire en premier
- **V1** : remplacer la ligne de badges du projet qualité de l'air par quatre barres directement étiquetées ; le résultat principal devient compréhensible en cinq secondes.
- **V2** : remplacer l'architecture ASCII de Vigilance par un flux vertical à cinq étapes ; c'est la preuve la plus simple que le projet est un système, pas un notebook.
- **V3** : montrer le NO₂ face à la barre FAIRMODE de 90 % ; ce visuel empêche de confondre `87,9 % PARTOUT` et `96,2 % aux stations`.

## Diagnostic par page

### `README.md` — une page d'accueil riche, mais son premier écran ressemble à un inventaire d'outils
- **Ce qui fonctionne** : les trois blocs Kaggle / recherche / MLOps donnent une structure de preuve ; les cinq fiches phares ont chacune un lien et un résultat identifiable.
- **Ce qui coûte au lecteur — A, B, I** : « Data Scientist | MLOps Engineer | Problem Solver », six badges de contact puis « Transformer des données complexes en décisions business impactantes » retardent la première preuve. **Remplacement proposé** : « **Data scientist — modèles évalués rigoureusement et systèmes utilisables en production**<br><br>Trois preuves : 3 classements Kaggle dans le top 1 %, un système MLOps temps réel et des recherches reproduites sur benchmarks publics. » Le tableau des trois preuves vient immédiatement après ; l'expérience et la formation passent après les projets.
- **Ce qui coûte au lecteur — B, C, E** : les 34 badges de « Stack Technique » ont tous le même poids visuel. **Remplacement proposé** : « **Stack principale** : Python · SQL · scikit-learn · PyTorch · LightGBM/XGBoost · Docker · Redis · PostgreSQL · Streamlit · Prometheus/Grafana. » Supprimer les rubriques « LLMs utilisés » et « Agentic » ; les projets montrent déjà l'usage réel.
- **Ce qui coûte au lecteur — K** : « 96,2 % après correction » apparaît dans la carte `PARTOUT` sans préciser que ce chiffre exige l'historique de la station. **Remplacement proposé** : intégrer V3 et remplacer la puce par « Sans observation locale : 41,4 % → 87,9 %, encore sous le seuil de 90 % ; aux stations : 96,2 %. »

### `about.qmd` — le parcours personnel existe, mais il est noyé dans une seconde page d'accueil
- **Ce qui fonctionne** : « armée → commerce → data science » est une trajectoire mémorisable ; les lettres de recommandation apportent une voix extérieure.
- **Ce qui coûte au lecteur — B, F, I** : « Réalisations Marquantes », « Compétences Techniques » et « Centres d'Intérêt » répètent presque tout `README.md`. **Remplacement proposé** : garder « Mon parcours », les deux expériences et trois recommandations ; remplacer les trois sections répétées par « **Les preuves techniques et leurs résultats sont regroupés dans les fiches projet.** → [Voir les projets](index.qmd#projets-phares). »
- **Ce qui coûte au lecteur — L** : la page se termine par une date après les recommandations, sans sortie vers un projet. **Remplacement proposé** : « **Commencer par :** [qualité de l'air](projets_Qualite_Air/) pour la rigueur expérimentale · [Vigilance](vigilance/) pour le MLOps · [Kaggle](projets_Competitions/) pour les résultats externes. » Cette ligne remplace la répétition du bloc Contact.

### `aegis-rca/README.md` *(fiche du portefeuille)* — la vue d'ensemble est claire, puis le lecteur tombe dans une nomenclature d'implémentation
- **Ce qui fonctionne** : « un humain valide toujours » pose immédiatement la limite ; l'erreur de banc à 100 % est une bonne histoire de rigueur.
- **Ce qui coûte au lecteur — B, D** : la liste commence par « consommateur Redis at-least-once, anti-poison », « RAG hybride (Qdrant) » et « cgroups pids-limit anti fork-bomb ». **Remplacement proposé** : insérer V9 après « Comment ça marche, en clair », puis placer « Architecture », « Méthode » et « Preuves » dans `<details><summary><strong>Implémentation et bancs de mesure</strong></summary>…</details>`.
- **Ce qui coûte au lecteur — I, K** : « 1 succès mesuré » est répété dans le statut, la vue d'ensemble, le tableau et les limites. **Remplacement proposé** : le dire une seule fois dans le tableau de preuves : « Auto-correction : un cas exécuté avec succès ; aucun taux de réussite estimable. »

### `Portfolio/anomaly_tabular/README.md` — une bonne question, mais six niveaux de preuve se disputent le premier plan
- **Ce qui fonctionne** : « aucun détecteur ne domine partout » est une thèse simple ; le tableau qui va de 63,8 à 78,7 donne une échelle complète.
- **Ce qui coûte au lecteur — B, C** : « LODO préenregistré », « routeur source-strict », « rails », « oracle » et « méta-features label-free » précèdent l'explication du gain. **Remplacement proposé** : « **Sur 502 jeux de données, le routeur choisit parmi 18 détecteurs et atteint 72,8 d'AUROC, contre 69,8 pour le meilleur détecteur utilisé partout.** » V7 remplace ensuite le tableau visible ; les termes de protocole passent dans le détail replié.
- **Ce qui coûte au lecteur — D** : les cinq étapes, l'aparté et cinq prochaines actions restent toutes ouvertes. **Remplacement proposé** : laisser visibles « question », « résultat » et « limite » ; replier les §§ 1 à 4 sous « Comment le résultat a été établi » et la feuille de route sous « Travaux suivants ».

### `Portfolio/anomaly_tsad/README.md` — l'idée de spécialisation est accessible, mais la conclusion n'affiche pas immédiatement sa condition
- **Ce qui fonctionne** : le contraste entre séries univariées et multivariées donne un fil narratif ; les résultats négatifs sont visibles.
- **Ce qui coûte au lecteur — C, K** : « le système obtient de meilleurs résultats que n'importe quel modèle utilisé seul » arrive avant le tableau où le gain global vaut `−0.01`. **Remplacement proposé** : « **Le routage ne gagne rien sur l'ensemble multivarié (`−0,01`), mais devient positif à partir de huit variables (`+0,03`) et atteint `+0,07` à partir de vingt.** » V8 remplace le tableau de strates et la métaphore du chef d'orchestre.
- **Ce qui coûte au lecteur — B, D** : quatre tableaux et les noms de modèles occupent la lecture avant la condition `d ≥ 8`. **Remplacement proposé** : garder V8 et une phrase sur PaAno ; replier les reproductions et classements complets sous « Résultats techniques ».

### `index.qmd` — une deuxième page d'accueil à maintenir, sans différence de récit
- **Ce qui fonctionne** : les liens Quarto sont plus directs et la page est moins décorée que `README.md`.
- **Ce qui coûte au lecteur — E, I** : la page reprend profil, faits marquants, formation, stack, expériences et cinq projets dans un ordre presque identique. **Remplacement proposé** : faire de `README.md` la source unique et remplacer le corps de `index.qmd` par une inclusion du contenu commun, avec seulement le front matter Quarto propre au site. Si l'inclusion du README complet n'est pas retenue, supprimer au minimum les sections Formation, Stack et Expérience de `index.qmd` et les lier depuis l'accueil.
- **Ce qui coûte au lecteur — K** : deux accueils écrits à la main garantissent des chiffres divergents au prochain changement. Le gain attendu n'est pas seulement visuel : une seule source empêche la désynchronisation.

### `projets_Competitions/README.md` — le palmarès est convaincant dans les quinze premières lignes, puis il se dilue sur 1 900 mots
- **Ce qui fonctionne** : rang, dénominateur et percentile sont présents ; les trois domaines des top 1 % montrent l'adaptation.
- **Ce qui coûte au lecteur — B, I** : « ≈ 1 050 notebooks », la justification des compétitions abandonnées et « La stratégie gagnante se déplace vers l'agentique » précèdent la vue d'ensemble. **Remplacement proposé** : après la ligne « 35+ compétitions · 7 top 4 % · 3 top 1 % », conserver seulement le tableau des sept meilleurs rangs et la phrase « Investissement variable selon les compétitions ; seuls les rangs publics sont présentés comme résultats. »
- **Ce qui coûte au lecteur — D, E** : « Méthodologie Générale », « Technologies Maîtrisées », « Valeur Ajoutée » et « Leçons Apprises » sont des listes génériques. **Remplacement proposé** : supprimer ces quatre sections ; sous chacun des trois top 1 %, garder une seule ligne « difficulté → choix décisif → rang ». Placer les détails de modélisation dans un `<details>` unique.

### `projets_Master_1/README.md` — dix projets de poids égal empêchent de voir la progression annoncée
- **Ce qui fonctionne** : les citations d'évaluateurs sont des preuves externes ; les domaines montrent une base large.
- **Ce qui coûte au lecteur — B, I** : les dix blocs répètent « Statut / Contexte / Réalisation / Outils / Feedback ». **Remplacement proposé** : garder quatre cas représentatifs — SQL immobilier, librairie/statistiques, Tableau/eau, faux billets — dans un tableau `problème | livrable | compétence | retour`; replier les six autres sous « Autres projets validés ».
- **Ce qui coûte au lecteur — C** : le lecteur ne voit aucune sortie, capture ou livrable malgré « disponibles sur demande ». **Remplacement proposé** : « **Inventaire de formation — livrables non publics. Cette page documente les compétences évaluées, pas des projets reproductibles.** » Cette phrase remplace « pour garder le dépôt léger » et règle l'attente sans ajouter une fausse preuve.

### `projets_Master_2/README.md` — Michelin devrait être le récit principal, mais partage l'espace avec sept fiches pédagogiques
- **Ce qui fonctionne** : le POC repris par les équipes et les retours externes sont plus utiles à un recruteur que la liste des cours.
- **Ce qui coûte au lecteur — I** : « Alternance Michelin » est suivie de sept projets académiques au même niveau. **Remplacement proposé** : renommer la page « **Alternance Michelin et sélection de projets Master 2** » ; conserver Michelin, puis trois projets seulement — énergie, NLP, POC TabPFN — dans un tableau compact. Replier les quatre autres.
- **Ce qui coûte au lecteur — K, E** : « TensorFlow/Keras ou PyTorch » révèle un contenu non vérifié. **Remplacement proposé** : supprimer la ligne et toute architecture dont l'usage réel n'est pas confirmé par le livrable.

### `projets_Qualite_Air/README.md` — le meilleur récit du portefeuille, mais quatre histoires fortes restent empilées sans priorité visuelle
- **Ce qui fonctionne** : la contrainte « prévoir là où personne ne mesure » est immédiatement compréhensible ; résultats, usage réglementaire, erreurs découvertes et limites forment un récit rare et crédible.
- **Ce qui coûte au lecteur — B, I** : résultat principal, mécanisme chimique, réfutation J+3, erreurs silencieuses, seuils 2030, FAIRMODE et protocole sont tous visibles au même niveau. **Remplacement proposé** : garder avant le premier `<details>` : la contrainte, V1, V3 et trois limites. Replier « mécanisme », « défauts trouvés » et « protocole » ; V4 et V5 remplacent les deux tableaux réglementaire/échéances.
- **Ce qui coûte au lecteur — C** : « Citer deux chiffres, jamais un » est une instruction d'auteur au milieu de la page. **Remplacement proposé** : « **Deux usages, deux scores : 39,6 % sans observation locale ; 45,7 % lorsqu'un historique de station est disponible.** »

### `projets_Tuning_Data_Augmentation_Vision/README.md` — une page non commencée ne peut pas avoir d'UX satisfaisante
- **Ce qui fonctionne** : le titre annonce clairement le domaine.
- **Ce qui coûte au lecteur — E, K** : « `[À compléter avec les fichiers du projet]` » suit une liste de techniques maîtrisées sans artefact. **Remplacement proposé** : retirer la page du portefeuille jusqu'à ce qu'un projet existe ; aucun visuel ne peut remplacer l'absence de contenu.

### `vigilance/README.md` — la promesse est claire, mais la preuve visuelle est remplacée par une documentation d'architecture
- **Ce qui fonctionne** : « un épisode = un ticket » est une excellente conclusion métier ; la distinction fait / prévu / exploratoire inspire confiance.
- **Ce qui coûte au lecteur — J, F** : le diagramme ASCII de 100 caractères de large est illisible à 380 px et oblige à suivre neuf noms de workers. **Remplacement proposé** : V2, vertical, remplace le diagramme et les trois puces « Choix de topologie défendus ».
- **Ce qui coûte au lecteur — B, D** : sept sections détaillent queues, TTL, `SET NX`, `GETDEL`, registries et warm-up avant de montrer un usage. **Remplacement proposé** : garder visibles la vue d'ensemble, V2, « un épisode = un ticket » et le statut ; placer Exécution, Détecteurs, Observabilité, Interprétabilité et Bootstrap dans `<details><summary><strong>Architecture et garanties techniques</strong></summary>`.

### `correction-previsions-qualite-air/README.md` *(dépôt de code)* — un excellent journal d'audit occupe la place de l'explication initiale
- **Ce qui fonctionne** : installation testée, commandes de reproduction et limites donnent une sortie claire au lecteur technique ; les sources sont attribuées.
- **Ce qui coûte au lecteur — A, I** : quatre paragraphes de blockquote commencent par « mesures principales refaites », « pour la première fois un intervalle », « affirmation réfutée » et « erreur d'étiquette corrigée » avant que le projet ne soit expliqué. **Remplacement proposé** : ouvrir par « **Ce dépôt corrige les prévisions CAMS à J+1, y compris là où aucune observation locale n'est disponible. Sur 24 mois communs, l'erreur baisse de 11,8 % à 39,6 % selon le polluant.** » Déplacer le blockquote sous `<details><summary><strong>Corrections méthodologiques d'août 2026</strong></summary>` après le résultat principal.
- **Ce qui coûte au lecteur — B, K** : neuf tableaux et plusieurs instructions « Citer deux chiffres, jamais un » se concurrencent. **Remplacement proposé** : V1, V3, V4, V5 et V6 deviennent les cinq éléments visibles ; les tableaux complets restent dans `reports/` ou sous `<details>`.
- **Ce qui coûte au lecteur — L** : les trois commandes arrivent tard mais constituent la bonne sortie. Les renommer « **Reproduire le résultat principal en trois commandes** » et ajouter ce lien dans le sommaire suffit ; ne pas ajouter de nouvelle section de conclusion.

### `anomaly_tabular/README.md` *(dépôt de code)* — compact et traçable, mais encore écrit comme une note de laboratoire
- **Ce qui fonctionne** : les chemins `results/router_v5.csv` et `results/auroc_par_domaine.md` rendent le score traçable ; le statut dit clairement que le harnais n'est pas encore republié.
- **Ce qui coûte au lecteur — B, C** : « harvest multi-sources », « argmax », « oracle-lift », « rare class », « gap de sélection » et « screening » entourent le tableau principal. **Remplacement proposé** : V7 remplace le tableau visible et la phrase « Ce que ça vaut » ; mettre l'infrastructure et le registre des négatifs dans `<details><summary><strong>Protocole et infrastructure</strong></summary>`.
- **Ce qui coûte au lecteur — L** : le lien principal mène à la présentation interactive inaccessible dans le contexte décrit. Sans traiter le 404 lui-même, la page doit avoir une sortie locale : placer `results/router_v5.csv` immédiatement sous V7 et garder le portfolio comme lien secondaire.

### `anomaly_tsad/README.md` *(dépôt de code)* — le plus court des README de recherche, mais sa thèse générale masque la strate qui fonctionne
- **Ce qui fonctionne** : les scores publié/reproduit sont dans le même tableau ; les CSV de classement sont directement liés.
- **Ce qui coûte au lecteur — K** : « la composition rapporte au-dessus du SOTA » est la promesse d'ouverture, alors que le tableau donne `−0.01` sur tout le multivarié. **Remplacement proposé** : « **La composition devient utile lorsque les séries sont réellement multivariées : +0,03 à partir de huit variables, +0,07 à partir de vingt.** » V8 remplace le tableau de strates.
- **Ce qui coûte au lecteur — B** : « endpoint natif », « LODO », « PaAno », « VUS-PR » et « warm-start » sont nécessaires au spécialiste mais pas à l'entrée. **Remplacement proposé** : garder la définition de VUS-PR en une note et replier les reproductions détaillées ; le CSV reste la sortie technique.

## Visuels proposés

#### V1 — Réduction de l'erreur à J+1, sans observation locale — **priorité 1**
- **Où** : `README.md` § « Correction apprise », après la phrase « Apprendre l'erreur du modèle européen » ; même image réutilisée dans `projets_Qualite_Air/README.md` et `correction-previsions-qualite-air/README.md` au début des résultats
- **Le message unique** : la correction réduit l'erreur des quatre polluants, avec un gain particulièrement fort sur le NO₂.
- **La forme** : quatre barres horizontales partant de zéro, triées par gain, plutôt qu'un tableau ; les catégories sont nominales et la longueur permet de comparer instantanément les amplitudes.
- **Les données** : chiffres du § 5 — NO₂ `39,6`, PM10 `20,2`, O₃ `17,9`, PM2,5 `11,8`, condition `PARTOUT`, double aveugle J+1.
- **Ce que ça REMPLACE** : les quatre badges « Protocole / NO₂ / Stations / Sources » et la puce « −39,6 % [...] −11,8 % » de l'accueil ; le premier tableau `PARTOUT` visible dans les deux README détaillés.
- **En noir et blanc et à 380 px** : barres gris foncé, valeur écrite au bout de chaque barre, noms à gauche ; aucun axe secondaire, aucune légende, aucun recours à la couleur.
- **Texte alternatif** : « Réduction de l'erreur CAMS à J+1 sans observation locale : NO₂ 39,6 %, PM10 20,2 %, ozone 17,9 % et PM2,5 11,8 %. »

#### V2 — De trois signaux à un ticket opérateur — **priorité 2**
- **Où** : `vigilance/README.md`, à la place de « Architecture Réelle du DAG (9 workers) »
- **Le message unique** : Vigilance transforme plusieurs détections parallèles en un incident unique, expliqué et suivi.
- **La forme** : flux vertical en cinq blocs — `capteurs → trois détecteurs en parallèle → fusion → ticket unique → tableau de bord` — plutôt qu'un diagramme d'infrastructure ; le sens de lecture porte le processus métier, pas les noms de fichiers.
- **Les données** : contenu de la fiche Vigilance : trois canaux (statique, temporel ponctuel, temporel séquentiel), fusion XGBoost, interprétation, cycle de vie d'alarme et dashboard.
- **Ce que ça REMPLACE** : le diagramme ASCII complet et les trois puces « Choix de topologie défendus » ; le détail des workers reste dans un `<details>`.
- **En noir et blanc et à 380 px** : blocs empilés, trois sous-blocs numérotés `1/2/3`, flèches épaisses et libellés courts ; une bordure double distingue le ticket final sans couleur.
- **Texte alternatif** : « Les flux de capteurs alimentent trois détecteurs parallèles ; leurs résultats sont fusionnés et expliqués, puis regroupés en un ticket unique affiché dans le tableau de bord. »

#### V3 — Le NO₂ s'approche du critère FAIRMODE, mais ne le franchit partout qu'aux stations — **priorité 3**
- **Où** : `README.md` § « Correction apprise », à la place de la puce réglementaire ; réutilisé dans les deux README qualité de l'air à l'entrée de la section FAIRMODE
- **Le message unique** : sans observation locale, la correction progresse fortement mais reste sous la barre de 90 % ; avec l'historique de station, elle la dépasse.
- **La forme** : axe horizontal de 0 à 100 avec trois points reliés (`41,4`, `87,9`, `96,2`) et une barre verticale à `90`, plutôt que trois barres ; la position relative au seuil est le message.
- **Les données** : chiffres du § 5 — NO₂ : CAMS brut `41,4 %`, corrigé `PARTOUT` `87,9 %`, corrigé aux stations `96,2 %`, seuil `90 %`.
- **Ce que ça REMPLACE** : la phrase « Le critère [...] 41,4 % [...] 96,2 % après correction », le tableau FAIRMODE visible et les deux répétitions « Citer les deux chiffres, jamais un ».
- **En noir et blanc et à 380 px** : formes distinctes `○`, `◆`, `●`, libellés directs et seuil en trait vertical pointillé annoté `90 %` ; la lecture ne dépend pas de vert/rouge.
- **Texte alternatif** : « Pour le NO₂, 41,4 % des stations satisfont le critère avec CAMS brut, 87,9 % après correction sans observation locale et 96,2 % avec historique de station ; le seuil est 90 %. »

#### V4 — Le changement de seuil fait passer 6 stations à 109
- **Où** : `projets_Qualite_Air/README.md` et `correction-previsions-qualite-air/README.md`, au début de « L'horizon réglementaire »
- **Le message unique** : à pollution 2025 constante, les seuils 2030 multiplient par 18,2 le nombre de stations en dépassement.
- **La forme** : slopegraph à deux colonnes `seuil actuel` / `seuil 2030`, avec trois pentes NO₂ `5→57`, PM10 `1→37`, PM2,5 `0→57` et le total `6→109` mis en annotation ; une pente montre mieux le basculement qu'un tableau à six colonnes.
- **Les données** : § 5 et tableau du dépôt : NO₂ `5→57`, PM10 `1→37`, PM2,5 `0→57`, union `6→109`, scénario « air constant ».
- **Ce que ça REMPLACE** : le tableau `VL en vigueur / VL 2030 / évaluées / dépassements` dans le README du dépôt et les deux paragraphes qui répètent `6 → 109` dans la fiche portefeuille.
- **En noir et blanc et à 380 px** : trois types de trait (plein, tireté, pointillé), noms et valeurs directement aux extrémités ; sous-titre obligatoire « scénario à air 2025 constant ».
- **Texte alternatif** : « À pollution 2025 constante, les stations dépassant les seuils passent de 5 à 57 pour le NO₂, de 1 à 37 pour les PM10 et de 0 à 57 pour les PM2,5 ; l'union passe de 6 à 109. »

#### V5 — NO₂ reste stable jusqu'à J+3, l'ozone se dégrade
- **Où** : `projets_Qualite_Air/README.md` § « Une affirmation [...] réfutée » et `correction-previsions-qualite-air/README.md` § « Les échéances, et leur nom »
- **Le message unique** : la stabilité avec l'échéance vaut pour le NO₂, pas pour l'ozone.
- **La forme** : deux courbes directement étiquetées sur quatre positions ordonnées J0 à J+3 ; la ligne est préférable au tableau parce que le message est une évolution.
- **Les données** : § 5 — NO₂ `37,1; 37,1; 36,9; 36,7`, O₃ `9,3; 9,1; 8,5; 7,0`.
- **Ce que ça REMPLACE** : le tableau à deux polluants de la fiche portefeuille ; dans le dépôt, il remplace les deux lignes NO₂/O₃ visibles tandis que PM10/PM2,5 passent dans un tableau replié.
- **En noir et blanc et à 380 px** : NO₂ en trait plein avec cercles, O₃ en tirets avec triangles, valeurs J0 et J+3 écrites, axes sans grille sauf la ligne zéro.
- **Texte alternatif** : « De J0 à J+3, le gain NO₂ varie peu, de 37,1 % à 36,7 %, tandis que le gain ozone baisse de 9,3 % à 7,0 %. »

#### V6 — Ce que chaque étage ajoute au NO₂
- **Où** : `correction-previsions-qualite-air/README.md`, après « La pile complète » ; version miniature possible dans `projets_Qualite_Air/README.md` avant « Le mécanisme est établi »
- **Le message unique** : l'essentiel du gain vient de la base et de la typologie ; les étages suivants ajoutent des progrès plus petits.
- **La forme** : escalier de points reliés, avec valeur cumulée à chaque étage, plutôt qu'un waterfall rempli ; les données sont des scores cumulés et non des contributions indépendantes.
- **Les données** : § 5 — base `26,6`, typologie `35,6`, membres `36,1`, feux `36,4`, GEOS-CF `38,7`, tendance `38,9`, spéciation `40,2` pour le NO₂.
- **Ce que ça REMPLACE** : le paragraphe dense sur « sept traceurs de composition » comme première explication de la pile ; les intervalles des quatre polluants restent dans le détail.
- **En noir et blanc et à 380 px** : points noirs, valeur au-dessus, noms abrégés sur deux lignes ; aucun aplat ni dégradé, le saut `base→typologie` reste visible.
- **Texte alternatif** : « Pour le NO₂, le gain cumulé passe de 26,6 % avec la base à 35,6 % avec la typologie, puis progresse par étapes jusqu'à 40,2 % avec la spéciation. »

#### V7 — Le routeur tabulaire gagne 3 points sur le meilleur détecteur unique
- **Où** : `Portfolio/anomaly_tabular/README.md` § « L'extension par domaines » et `anomaly_tabular/README.md` *(dépôt de code)* § « Résultats »
- **Le message unique** : choisir le détecteur selon la source fait mieux que déployer le même détecteur partout.
- **La forme** : dot plot horizontal des cinq systèmes, plutôt qu'un tableau ; les écarts entre `69,8`, `71,3`, `72,8` et le plafond `78,7` sont plus lisibles sur un axe commun.
- **Les données** : après arbitrage de la valeur canonique, `results/router_v5.csv` et tableau courant : IsolationForest `63,8`, KNN `69,8`, fusion `71,3`, routeur `72,8`, oracle `78,7`.
- **Ce que ça REMPLACE** : le tableau des cinq systèmes dans les deux README et le paragraphe « combien gagne-t-on au-dessus d'un système SOTA ? ».
- **En noir et blanc et à 380 px** : cinq points avec noms à gauche et valeurs à droite ; le routeur est un losange plein, l'oracle un cercle vide, sans couleur ni légende.
- **Texte alternatif** : « AUROC moyen : IsolationForest 63,8, KNN 69,8, fusion de 18 détecteurs 71,3, routeur 72,8 et sélection parfaite théorique 78,7. »

#### V8 — Le routage temporel ne devient utile qu'en dimension suffisante
- **Où** : `Portfolio/anomaly_tsad/README.md` et `anomaly_tsad/README.md` *(dépôt de code)*, à la place du tableau « Gain routage / plafond oracle »
- **Le message unique** : le routage est négatif sur l'ensemble, puis positif à partir de huit variables et plus net à partir de vingt.
- **La forme** : trois barres divergentes autour d'une ligne zéro ; ce format rend immédiatement visible le changement de signe.
- **Les données** : tableaux courants — `d ≥ 2 : −0,01`, `d ≥ 8 : +0,03`, `d ≥ 20 : +0,07` en VUS-PR.
- **Ce que ça REMPLACE** : le tableau de strates, la phrase « le gain croît avec la dimensionnalité » et l'aparté qui affirme que la composition bat le champion.
- **En noir et blanc et à 380 px** : ligne zéro épaisse, barre négative hachurée à gauche, deux barres pleines à droite, valeurs et seuils `d` écrits directement.
- **Texte alternatif** : « Le gain du routage vaut moins 0,01 pour toutes les séries multivariées, plus 0,03 à partir de huit variables et plus 0,07 à partir de vingt. »

#### V9 — Aegis-RCA prépare un diagnostic, l'humain décide
- **Où** : `aegis-rca/README.md`, entre « Comment ça marche, en clair » et « Ce qui distingue ce projet »
- **Le message unique** : l'agent rassemble les preuves et propose une action, mais aucune action réelle ne part sans validation humaine.
- **La forme** : flux horizontal à quatre étapes sur écran large et vertical à 380 px — `incident → métriques + procédures → diagnostic recommandé → validation humaine` — plutôt qu'un schéma de composants ; la frontière de décision est le message.
- **Les données** : contenu de la fiche : tickets Vigilance, métriques Prometheus, base documentaire RAG, LLM local, validation humaine.
- **Ce que ça REMPLACE** : le paragraphe « Comment ça marche, en clair » après sa première phrase et les cinq lignes de fichiers de la section Architecture visible.
- **En noir et blanc et à 380 px** : quatre blocs numérotés ; le dernier porte un cadre double et le mot `DÉCISION`, les sources métriques/procédures sont deux entrées distinctes.
- **Texte alternatif** : « Aegis-RCA reçoit un incident, rassemble métriques et procédures, rédige un diagnostic et une recommandation, puis attend la décision d'un humain. »

## Ce qu'il faut RETIRER

- `README.md` : supprimer la citation générique, 34 badges de stack et les badges de pied de page — environ **90 lignes et deux écrans mobiles** gagnés avant même de toucher aux projets.
- `about.qmd` : retirer les réalisations et compétences déjà présentes sur l'accueil — environ **650 mots**, soit plus de la moitié de la page.
- `projets_Competitions/README.md` : retirer le compte de notebooks, le détour agentique, la méthodologie générique, « Valeur ajoutée » et « Leçons apprises » — environ **800 mots** ; le palmarès reste intact.
- `projets_Master_1/README.md` : ne laisser ouverts que quatre projets représentatifs et replier les six autres — environ **600 mots de lecture imposée** gagnés.
- `projets_Master_2/README.md` : retirer les listes génériques de compétences et de technologies, garder Michelin et trois projets — environ **450 mots**.
- `projets_Tuning_Data_Augmentation_Vision/README.md` : retirer la fiche entière — **213 mots** et une promesse inachevée en moins.
- `vigilance/README.md` : remplacer l'ASCII et replier l'implémentation — environ **900 mots** sortent du premier passage sans perdre la documentation.
- `correction-previsions-qualite-air/README.md` : déplacer le journal de corrections et les tables secondaires dans des `<details>` — le résultat principal apparaît environ **quatre écrans mobiles plus tôt**.
- Les fiches `Portfolio/anomaly_*` : retirer les feuilles de route détaillées de la lecture ouverte ; les dépôts de code sont l'endroit naturel pour ces listes.

## Ce qui est bien et ne doit pas être cassé

- La promesse « prévoir là où personne ne mesure » est le meilleur exemple du portefeuille : un problème difficile expliqué sans jargon.
- Les limites et résultats négatifs sont publiés au même niveau que les gains ; les raccourcir ne doit jamais les faire disparaître.
- Les rangs Kaggle incluent rang, dénominateur et percentile : c'est déjà la bonne unité visuelle.
- Les statuts « fait / prévu / exploratoire » d'Aegis-RCA et Vigilance donnent une maturité honnête aux projets.
- Le vocabulaire des pages HTML annexes — question en titre, trois chiffres clés, démarche numérotée — est une bonne référence ; il faut en reprendre la hiérarchie, pas leur CSS ni leur interactivité.
