# Audit éditorial du portefeuille — contradictions, jargon, rendu et état d'achèvement

## Synthèse — les 5 choses à corriger en premier
- Corriger le contresens mathématique `observation − CAMS` : cette correction s'ajoute à CAMS, elle ne se retranche pas.
- Réécrire le chiffre FAIRMODE de l'accueil : `96,2 %` vaut aux stations ; le produit `PARTOUT` reste à `87,9 %`, sous le seuil de 90 %.
- Unifier les résultats de `anomaly_tabular` et restreindre la conclusion de `anomaly_tsad` à la haute dimension réellement positive.
- Retirer les affirmations de déploiement GitHub Pages et la fiche Vision vide ; elles annoncent deux livrables qui n'existent pas.
- Traiter les sept tabsets Quarto comme un défaut bloquant : sur GitHub, ils cassent aussi la hiérarchie et la divulgation progressive.

## Défauts

### 🔴 bloquant D — Les tabsets cassés font plus qu'afficher deux lignes parasites
- **Où** : `aegis-rca/README.md`, `anomaly_tabular/README.md`, `anomaly_tsad/README.md`, `projets_Competitions/README.md`, `projets_Master_1/README.md`, `projets_Master_2/README.md` et `vigilance/README.md`, de `::: {.panel-tabset}` au `:::` final
- **Ce qui est écrit** : `::: {.panel-tabset}`
- **Le problème** : sur GitHub, le marqueur est visible, les deux onglets deviennent deux sections successives et tout le détail technique est déplié. Le défaut est donc plus grave qu'estimé : il ajoute du bruit, supprime la hiérarchie prévue et allonge chaque fiche dès la première lecture.
- **Ce qu'un lecteur en conclut** : le portefeuille n'a pas été relu dans son format de publication réel.
- **Remplacement proposé** : conserver `## 🧑‍💼 Vue d'ensemble`, puis remplacer `## 🔧 Détails techniques` par `<details>` suivi de `<summary><strong>Détails techniques</strong></summary>` à la ligne suivante, remplacer le `:::` final par `</details>` et supprimer le `::: {.panel-tabset}` initial.
- **Ce que ça retire** : les deux marqueurs Quarto visibles et le détail technique imposé au premier passage.

### 🔴 bloquant A — La correction du résidu est décrite avec le mauvais signe
- **Où** : `projets_Qualite_Air/README.md`, introduction
- **Ce qui est écrit** : « le modèle apprend le **résidu** `observation − CAMS` et le retranche »
- **Le problème** : si le résidu est `observation − CAMS`, il faut l'ajouter à CAMS. La phrase actuelle décrit l'opération inverse.
- **Ce qu'un lecteur en conclut** : soit la méthode est fausse, soit son auteur ne maîtrise pas sa propre formule.
- **Remplacement proposé** : « le modèle apprend la correction `observation − CAMS`, puis l'ajoute à la prévision CAMS »
- **Ce que ça retire** : le mot « résidu » dans la phrase d'ouverture, inutile pour comprendre l'opération.

### 🔴 bloquant A — Le `96,2 %` de l'accueil change silencieusement de produit
- **Où** : `README.md` et `index.qmd`, carte « Correction apprise » ; à comparer avec `projets_Qualite_Air/README.md` § « L'horizon réglementaire »
- **Ce qui est écrit** : « Le critère européen de qualité est atteint sur 41,4 % des stations NO₂ avec la prévision brute, **96,2 %** après correction »
- **Le problème** : la fiche détaillée donne trois périmètres : `41,4 %` brut, `87,9 %` corrigé `PARTOUT`, `96,2 %` corrigé aux stations. L'accueil associe la promesse « là où personne ne mesure » au chiffre station-assisté sans le dire.
- **Ce qu'un lecteur en conclut** : le chiffre le plus favorable a été choisi en masquant sa condition d'observation locale.
- **Remplacement proposé** : « **Sans observation locale**, la part des stations NO₂ qui satisfait le critère européen passe de 41,4 % à **87,9 %**, encore sous le seuil de 90 %. **Aux stations**, avec leur historique, elle atteint 96,2 %. »
- **Ce que ça retire** : la question rhétorique « Assez bon pour servir en réglementaire ? » et l'ambiguïté de « après correction ».

### 🔴 bloquant A — Le résultat tabulaire change entre l'accueil, le site et la fiche
- **Où** : `README.md` § « Recherche Compositionnelle », `index.qmd` § « Recherche compositionnelle », `anomaly_tabular/README.md` § « L'extension par domaines »
- **Ce qui est écrit** : « **72.5 AUROC** [...] oracle à 78.3 », « **+2.7 pts AUROC** » et « **72.8** [...] bat KNN de **+3.0 pts** [...] oracle **78.7** »
- **Le problème** : trois pages donnent deux scores, deux gains et deux plafonds pour ce qui est présenté partout comme le même routeur par domaine. Aucun libellé ne permet de comprendre qu'il s'agirait de variantes différentes.
- **Ce qu'un lecteur en conclut** : les chiffres phares ne sont pas maîtrisés.
- **Remplacement proposé** : sur `README.md` et `index.qmd`, mettre exactement « **Routeur source-strict : 72,8 AUROC**, contre 69,8 pour le meilleur détecteur unique (**+3,0 points**) ; oracle du pool : 78,7. »
- **Ce que ça retire** : `72.5`, `+2.7`, `78.3`, le `p=5×10⁻⁷` isolé et le mot anglais « single ».

### 🔴 bloquant A — La conclusion TSAD affirme l'inverse du résultat global
- **Où** : `anomaly_tsad/README.md`, vue d'ensemble, § 5 et aparté
- **Ce qui est écrit** : « le système obtient de meilleurs résultats que n'importe quel modèle utilisé seul » et « **la composition bat le champion** »
- **Le problème** : le tableau donne `−0.01` sur tout le multivarié, `+0.03` seulement pour `d ≥ 8` et `+0.07` pour `d ≥ 20`. La conclusion générale efface la strate négative.
- **Ce qu'un lecteur en conclut** : la réserve est dans le tableau, mais le récit publicitaire l'annule.
- **Remplacement proposé** : « Sur l'ensemble multivarié, le routage ne bat pas le meilleur modèle seul (`−0,01`). Le gain apparaît à partir de huit variables (`+0,03`) et atteint `+0,07` à partir de vingt : la composition est donc une piste pour la haute dimension, pas un gain général. »
- **Ce que ça retire** : l'affirmation universelle et la métaphore « chef d'orchestre » utilisée pour la soutenir.

### 🔴 bloquant E — Une fiche publique annonce explicitement qu'elle est vide
- **Où** : `projets_Tuning_Data_Augmentation_Vision/README.md`, § « Projets »
- **Ce qui est écrit** : « `### [À compléter avec les fichiers du projet]` »
- **Le problème** : tout le reste de la page est une liste générique de techniques prétendument maîtrisées, sans réalisation, résultat ni artefact.
- **Ce qu'un lecteur en conclut** : une page de remplissage a été publiée pour donner du volume au portefeuille.
- **Remplacement proposé** : retirer cette fiche de la navigation et du portefeuille jusqu'à l'existence d'un projet vérifiable ; ne publier aucun texte de remplacement.
- **Ce que ça retire** : la fiche entière, soit 213 mots de promesses sans preuve.

### 🔴 bloquant A — Une correction annoncée comme faite subsiste dans deux pages
- **Où** : `about.qmd` § « Michelin » et `projets_Master_2/README.md` § « Missions réalisées »
- **Ce qui est écrit** : « Algorithmes de fuzzy matching — augmentation considérable du taux de détection des correspondances »
- **Le problème** : le brief indique que cette formulation a été retirée parce que la méthode n'était ni employée ni sourcée. Elle reste pourtant publiée deux fois.
- **Ce qu'un lecteur en conclut** : les corrections ne sont pas propagées et une compétence non démontrée reste revendiquée.
- **Remplacement proposé** : « Rapprochement automatisé de données de pricing hétérogènes et tests de non-régression »
- **Ce que ça retire** : la méthode non employée et l'adjectif invérifiable « considérable ».

### 🔴 bloquant E — Le portefeuille prétend être en ligne et déployé alors qu'il n'a jamais été construit
- **Où** : `README.md`, badge d'ouverture et pied de page
- **Ce qui est écrit** : « Portfolio en ligne », « *Portfolio construit avec passion | Quarto + GitHub Pages* » et « Deployed on GitHub Pages »
- **Le problème** : le brief précise que le site Quarto n'a jamais été construit. Ce n'est pas le 404 du compte qui crée le défaut : les libellés annoncent un déploiement inexistant.
- **Ce qu'un lecteur en conclut** : le premier appel à l'action et le dernier badge sont faux.
- **Remplacement proposé** : supprimer le badge « Portfolio en ligne », la ligne « Portfolio construit avec passion | Quarto + GitHub Pages », les badges Quarto et GitHub Pages ; conserver seulement les liens de contact et la date.
- **Ce que ça retire** : quatre promesses de publication non tenues.

### 🟠 important A — Aegis est simultanément en phases A/B et au banc de phase C
- **Où** : `aegis-rca/README.md`, tableau « Preuves » et § « Limites honnêtes »
- **Ce qui est écrit** : « Incidents à cause connue (**gate Phase C**, 14 cas...) » et « Prototype de 3 jours de développement, **Phase A/B seulement** »
- **Le problème** : les deux statuts ne peuvent pas décrire le même état sans expliquer la différence entre un banc exécuté et une phase terminée.
- **Ce qu'un lecteur en conclut** : l'étiquette de maturité est ajustée selon le paragraphe.
- **Remplacement proposé** : « Prototype de 3 jours : composants des phases A/B fonctionnels et banc d'entrée de phase C exécuté sur 14 cas ; aucune validation en production. »
- **Ce que ça retire** : « Phase A/B seulement » et l'ambiguïté du mot « gate ».

### 🟠 important A — Neuf domaines sont annoncés, mais dix sont énumérés
- **Où** : `anomaly_tsad/README.md`, § « Spécialiser le benchmark »
- **Ce qui est écrit** : « caractérisé en **9 domaines applicatifs** (aérospatial, SCADA industriel, serveurs/ITops, éolien-solaire, médical cardiaque, médical neuro, robotique/drones, finance, wearables, eau/environnement) »
- **Le problème** : la parenthèse contient dix catégories.
- **Ce qu'un lecteur en conclut** : même un décompte simple n'a pas été contrôlé.
- **Remplacement proposé** : « caractérisé en **10 domaines applicatifs** »
- **Ce que ça retire** : rien.

### 🟠 important C — Deux piles différentes partagent le même libellé J+1
- **Où** : `projets_Qualite_Air/README.md`, § « Le résultat » puis § « Une affirmation [...] réfutée »
- **Ce qui est écrit** : O₃ vaut `+17,9 %` à J+1 dans le premier tableau et `+9,1 %` à J+1 dans le second ; NO₂ vaut respectivement `+39,6 %` et `+37,1 %`.
- **Le problème** : le second tableau utilise une pile réduite commune aux quatre horizons, mais la page ne le dit pas. Le lecteur voit deux valeurs concurrentes du même résultat.
- **Ce qu'un lecteur en conclut** : le score change sans raison selon la section.
- **Remplacement proposé** : introduire le second tableau par « **Sensibilité d'échéance sur une pile réduite identique de J0 à J+3 — ces scores ne sont pas ceux de la pile complète J+1 ci-dessus :** »
- **Ce que ça retire** : « Poussé jusqu'à J+3 — la dernière que CAMS Europe produise : »

### 🟠 important A — Le récit du Master 1 dit que la présentation progresse, puis que le dernier projet régresse
- **Où** : `projets_Master_1/README.md`, vue d'ensemble, projet 10 et « Synthèse des feedbacks »
- **Ce qui est écrit** : « s'est nettement améliorée au fil des projets (voir le dernier...) », puis « il faut faire un effort sur la présentation des résultats » et « P10 (soutenance confuse) »
- **Le problème** : le dernier projet est donné à la fois comme preuve de progrès et comme contre-exemple.
- **Ce qu'un lecteur en conclut** : le récit force une progression que les retours ne montrent pas.
- **Remplacement proposé** : « Les retours confirment une base technique solide. La communication est restée un axe de progression : plusieurs projets sont jugés clairs, mais le projet 10 signale encore une soutenance confuse. »
- **Ce que ça retire** : « s'est nettement améliorée », « voir le dernier » et la ligne « Présentations de plus en plus fluides et structurées ».

### 🟠 important A — `35+ compétitions complétées` contredit les compétitions abandonnées
- **Où** : `projets_Competitions/README.md`, « Comment lire ce palmarès » et tableau « Statistiques globales »
- **Ce qui est écrit** : « D'autres ont été engagées puis laissées de côté » et « Compétitions complétées | 35+ »
- **Le problème** : « engagée », « classée » et « complétée » ne sont pas synonymes. La page ne donne pas le nombre réellement terminé.
- **Ce qu'un lecteur en conclut** : le volume est gonflé par une définition mouvante.
- **Remplacement proposé** : « **35+ compétitions engagées**, dont 7 classements dans le top 4 % et 3 dans le top 1 %. »
- **Ce que ça retire** : « Compétitions complétées » et « 35+ sujets distincts en 5 ans ».

### 🟠 important C — La répartition Kaggle dépasse le total sans annoncer les chevauchements
- **Où** : `projets_Competitions/README.md`, tableau « Répartition par Type de Problème »
- **Ce qui est écrit** : `10+`, `12+`, `6+`, `4+`, `5+`, `3+` pour un total annoncé de `35+`
- **Le problème** : les minima totalisent déjà 40. Si une compétition appartient à plusieurs catégories, il faut le dire ; sinon le tableau contredit le total.
- **Ce qu'un lecteur en conclut** : les catégories ont été estimées plutôt que comptées.
- **Remplacement proposé** : renommer le titre « **Répartition non exclusive par type de problème** » et ajouter juste dessous « Une compétition peut relever de plusieurs catégories ; ces comptes ne s'additionnent pas. »
- **Ce que ça retire** : rien ; à défaut de confirmer les chevauchements, supprimer le tableau.

### 🟠 important C — Le nombre de notebooks mesure le stockage, pas la performance
- **Où** : `projets_Competitions/README.md`, paragraphe « ≈ 1 050 notebooks » et tableau « Statistiques globales »
- **Ce qui est écrit** : « **≈ 1 050 notebooks** : **499** dans l'espace de travail Kaggle, majoritairement privés, et **551 en local** »
- **Le problème** : le chiffre est invérifiable pour un visiteur et récompense le nombre de brouillons. Il détourne l'attention des sept rangs publics, qui sont la preuve utile.
- **Ce qu'un lecteur en conclut** : le volume remplace la qualité quand les artefacts ne sont pas montrables.
- **Remplacement proposé** : supprimer le paragraphe et la ligne du tableau sans remplacement.
- **Ce que ça retire** : 76 mots défensifs et un indicateur sans valeur comparative.

### 🟠 important G — La tendance « agentique » est présentée comme un fait sans preuve
- **Où** : `projets_Competitions/README.md` § « Ce qui change en ce moment », `README.md` et `index.qmd` carte Kaggle
- **Ce qui est écrit** : « La stratégie gagnante se déplace vers l'**agentique** »
- **Le problème** : aucune compétition, mesure ou source du corpus n'établit cette tendance. Le passage sert surtout à raccrocher Kaggle aux autres projets.
- **Ce qu'un lecteur en conclut** : un mot à la mode est utilisé pour donner une actualité artificielle au palmarès.
- **Remplacement proposé** : « **Expérimentation actuelle** : automatiser une partie de l'exploration des variables et des modèles, sans résultat de classement attribuable à cette approche à ce stade. »
- **Ce que ça retire** : la généralisation à tous les compétiteurs et « redéfinir ce que veut dire bien travailler ».

### 🟠 important G — L'accroche d'accueil est une suite d'auto-évaluations génériques
- **Où** : `README.md`, titre et § « À Propos »
- **Ce qui est écrit** : « Data Scientist | MLOps Engineer | Problem Solver », « Data Scientist passionné », « perspective unique », « communication efficace »
- **Le problème** : aucune de ces expressions ne différencie le profil ni ne donne une preuve. « Problem Solver » et « passionné » sont des formules de CV que le lecteur doit croire sur parole.
- **Ce qu'un lecteur en conclut** : le candidat se décrit avant de montrer ce qu'il sait faire.
- **Remplacement proposé** : « **Data scientist — modèles évalués rigoureusement et systèmes mis en production**<br><br>Je construis des modèles de détection et de prévision, puis les entoure des contrôles, interfaces et garde-fous nécessaires à leur usage. »
- **Ce que ça retire** : la citation « Transformer des données complexes... » et le paragraphe d'auto-qualification.

### 🟠 important F — Trente-quatre badges transforment la stack en inventaire
- **Où** : `README.md`, § « Stack Technique »
- **Ce qui est écrit** : les groupes « Langages & Frameworks », « Machine Learning & IA », « LLMs utilisés », « Agentic », « MLOps & Infrastructure » et « Visualisation & BI »
- **Le problème** : « avoir utilisé » Claude, Grok ou Kimi n'est pas une compétence au même niveau que Python, SQL ou Docker. La quantité de badges empêche d'identifier la stack réellement défendue par les projets.
- **Ce qu'un lecteur en conclut** : chaque outil aperçu est revendiqué comme compétence.
- **Remplacement proposé** : « **Stack principale** : Python · SQL · scikit-learn · PyTorch · LightGBM/XGBoost · Docker · Redis · PostgreSQL · Streamlit · Prometheus/Grafana.<br><br>**Pratiques** : évaluation de modèles, séries temporelles, détection d'anomalies, orchestration d'agents et observabilité. »
- **Ce que ça retire** : tous les badges de stack, les listes de marques de LLM et les rubriques redondantes.

### 🟠 important G — L'expérience DELTAMU emploie deux superlatifs sans résultat mesuré
- **Où** : `README.md` et `index.qmd`, expérience DELTAMU
- **Ce qui est écrit** : « algorithme de niveau recherche » et « Augmentation colossale de la capacité de compréhension des données »
- **Le problème** : « niveau recherche » n'est pas un critère et « colossale » n'a ni mesure ni objet précis.
- **Ce qu'un lecteur en conclut** : l'impact n'est pas quantifiable, donc il est amplifié par le vocabulaire.
- **Remplacement proposé** : « Analyse de plusieurs centaines de capteurs industriels, caractérisation des régimes de fonctionnement et optimisation en Rust du cœur de calcul. »
- **Ce que ça retire** : les deux auto-évaluations et la puce redondante « analyses statistiques avancées ».

### 🟠 important C — L'impact Michelin repose sur des adjectifs, pas sur un avant/après
- **Où** : `README.md`, `about.qmd`, `index.qmd` et `projets_Master_2/README.md`, expérience Michelin
- **Ce qui est écrit** : « augmentation considérable », « résultats jugés excellents », « accélération considérable »
- **Le problème** : quatre pages répètent les mêmes appréciations sans volume traité, taux de rapprochement, durée avant/après ni périmètre plus précis que « continental » et « mondial ».
- **Ce qu'un lecteur en conclut** : la confidentialité empêche peut-être les chiffres, mais le portefeuille essaie de les remplacer par des superlatifs.
- **Remplacement proposé** : « POC de rapprochement de données de pricing hétérogènes, mené jusqu'à la préparation de mise en production puis repris par les équipes. Tests de non-régression et contrôles de qualité inclus. »
- **Ce que ça retire** : « considérable », « excellents » et la répétition « niveau continental / pricing mondial ».

### 🟠 important F — La page À propos répète l'accueil au lieu d'ajouter un angle humain
- **Où** : `about.qmd`, §§ « Réalisations marquantes » et « Compétences techniques »
- **Ce qui est écrit** : les blocs Kaggle, ADBench/TSB-AD, Vigilance, Aegis-RCA et la stack complète, déjà présents dans `README.md` et `index.qmd`
- **Le problème** : la page annoncée « À propos » consacre l'essentiel de ses 1 195 mots à une troisième version des mêmes projets et technologies.
- **Ce qu'un lecteur en conclut** : changer de page ne change pas de contenu.
- **Remplacement proposé** : remplacer ces deux sections par « **Ce parcours relie trois expériences : la rigueur opérationnelle acquise dans l'armée, la compréhension du besoin client dans le commerce, puis la conception de systèmes data évaluables et utilisables. Les preuves techniques sont regroupées dans les fiches projet de l'accueil.** »
- **Ce que ça retire** : les sections « Réalisations marquantes », « Compétences techniques » et environ 650 mots dupliqués.

### 🟠 important H — Un classement Kaggle est rangé parmi les diplômes
- **Où** : `about.qmd` et `index.qmd`, sections « Certifications et Diplômes » / « Certifications »
- **Ce qui est écrit** : « **Kaggle Competitions** : Top 1% mondial (3 compétitions) »
- **Le problème** : un classement de compétition n'est ni un diplôme ni une certification.
- **Ce qu'un lecteur en conclut** : les catégories sont élargies pour faire paraître le parcours plus certifié.
- **Remplacement proposé** : renommer la section « **Formation et résultats publics** » et séparer « Diplômes » des « Classements Kaggle » ; ou, plus court, supprimer la ligne Kaggle déjà présente plus haut.
- **Ce que ça retire** : la fausse qualification de certification.

### 🟠 important C — « Reproductions exactes » est généralisé au-delà de ce qui est montré
- **Où** : `README.md` § « Faits marquants », `anomaly_tabular/README.md` vue d'ensemble et tableau ADBench
- **Ce qui est écrit** : « Reproductions exactes validées » et « reproduire exactement ces résultats »
- **Le problème** : la fiche tabulaire donne seulement cinq scores reproduits, sans scores publiés en face ; elle ne permet donc pas de constater une égalité. Les égalités littérales visibles concernent TSB-AD (`0.4234`, `0.3501`).
- **Ce qu'un lecteur en conclut** : une preuve acquise sur un volet est étendue à tous les benchmarks.
- **Remplacement proposé** : « **TSB-AD : deux scores reproduits à l'identique ; ADBench : cinq détecteurs réexécutés sous un protocole commun.** »
- **Ce que ça retire** : l'affirmation globale « reproductions exactes ».

### 🟠 important A — `9 workers × 4 réplicas` ne correspond pas à l'architecture détaillée
- **Où** : `README.md`, badges Vigilance et « Faits marquants » ; `vigilance/README.md` § « Exécution distribuée »
- **Ce qui est écrit** : « Workers — 9 × 4 réplicas » et « DAG 9 workers, 4 réplicas », alors que la fiche décrit « 3 réplicas de workers universels » et « 1 worker CUDA »
- **Le problème** : le badge se lit comme 36 workers. La fiche semble plutôt décrire neuf étapes logiques exécutées par quatre processus.
- **Ce qu'un lecteur en conclut** : l'échelle du système a été grossie par une multiplication ambiguë.
- **Remplacement proposé** : « **DAG : 9 étapes logiques · exécution : 3 processus CPU + 1 GPU** »
- **Ce que ça retire** : `9 × 4 réplicas` et l'ambiguïté entre étape, worker et réplica.

### 🟠 important B — Les cartes d'accueil parlent d'abord aux spécialistes
- **Où** : `README.md`, cartes Vigilance, Aegis-RCA et Recherche compositionnelle
- **Ce qui est écrit** : « DAG event-driven », « DLQ », « RASCI », « RAG », « cgroups », « SOTA », « VUS-PR », « AUROC », « préenregistré »
- **Le problème** : ces termes arrivent sur la page destinée au premier passage, souvent non spécialiste. Leur accumulation oblige à décoder la méthode avant de comprendre le résultat.
- **Ce qu'un lecteur en conclut** : le portefeuille confond précision technique et clarté.
- **Remplacement proposé** : « **Vigilance** : neuf étapes de traitement reprennent après une panne et regroupent les alertes d'un même incident. **Aegis-RCA** : un modèle local rassemble métriques et procédures, puis propose un diagnostic validé par un humain. **Recherche** : le meilleur détecteur change selon les données ; un routeur choisit parmi 18 méthodes et gagne 3,0 points d'AUROC sur le volet tabulaire. »
- **Ce que ça retire** : les acronymes de l'accueil ; ils restent dans les fiches techniques.

### 🟠 important E — La fiche Master 2 contient encore une alternative de gabarit
- **Où** : `projets_Master_2/README.md`, projet 6
- **Ce qui est écrit** : « Framework : TensorFlow/Keras **ou** PyTorch » et « Technologies : Python, TensorFlow/PyTorch »
- **Le problème** : « ou » montre que la page ne sait pas quel framework a réellement servi. Les listes de ResNet, VGG et EfficientNet prennent alors l'allure d'un programme pédagogique recopié plutôt que d'un projet exécuté.
- **Ce qu'un lecteur en conclut** : cette fiche n'a pas été reconstruite depuis le livrable réel.
- **Remplacement proposé** : supprimer les deux lignes jusqu'à vérification du livrable, puis ne conserver que le framework et les architectures effectivement utilisés.
- **Ce que ça retire** : une compétence alternative invérifiable.

### 🟡 confort E — Douze règles sont annoncées, mais dix seulement sont décrites comme exécutables et aucune n'est listée
- **Où** : `projets_Qualite_Air/README.md`, fin de « Les défauts trouvés »
- **Ce qui est écrit** : « Douze règles, dont dix exécutables. »
- **Le problème** : la phrase promet un inventaire ou une preuve que la page ne fournit pas. Le nombre précis attire une question sans donner de sortie.
- **Ce qu'un lecteur en conclut** : deux règles manquent ou l'inventaire existe ailleurs sans lien.
- **Remplacement proposé** : « Les erreurs répétées sont désormais transformées en contrôles exécutables dans le dépôt. »
- **Ce que ça retire** : les comptes `12` et `10` non vérifiables depuis la page.

### 🟡 confort G — « Prochaines actions intelligentes » s'auto-évalue
- **Où** : `anomaly_tabular/README.md` et `anomaly_tsad/README.md`
- **Ce qui est écrit** : « Prochaines actions intelligentes »
- **Le problème** : le titre juge les actions au lieu de les nommer.
- **Ce qu'un lecteur en conclut** : même la feuille de route doit être valorisée par un adjectif.
- **Remplacement proposé** : « Prochaines étapes »
- **Ce que ça retire** : « intelligentes ».

### 🟡 confort H — La forme oscille sans règle entre français et anglais
- **Où** : ensemble du portefeuille, notamment `README.md` et les fiches de formation
- **Ce qui est écrit** : « Highlights », « Stack Technique », « Feedback », « Time Series », « feature engineering », « single », ainsi que `0.5%`, `72.8` et `+3.0 pts`
- **Le problème** : les termes métier utiles se mélangent à des anglicismes décoratifs ; les décimales alternent point et virgule dans des pages françaises.
- **Ce qu'un lecteur en conclut** : les pages ont été assemblées à des moments différents sans passe éditoriale finale.
- **Remplacement proposé** : appliquer partout « Points clés », « Technologies », « Retour », « séries temporelles », « création de variables », « détecteur unique », puis `0,5 %`, `72,8` et `+3,0 points`.
- **Ce que ça retire** : les anglicismes qui n'apportent pas de précision technique.

### 🟡 confort G — Le pied de page se termine par une citation et trois badges sans fonction
- **Où** : `README.md`, pied de page
- **Ce qui est écrit** : « *Le code ne ment jamais, les commentaires oui* — Linus Torvalds » et « Portfolio construit avec passion »
- **Le problème** : l'attribution n'est pas établie dans le corpus et la citation ne donne aucune information sur le candidat. Après le contact, elle ajoute une posture de développeur et repousse la vraie fin de page.
- **Ce qu'un lecteur en conclut** : le portefeuille se termine sur une formule empruntée plutôt que sur une action claire.
- **Remplacement proposé** : terminer la page après les quatre liens de contact et « Dernière mise à jour : août 2026 ».
- **Ce que ça retire** : la citation, « construit avec passion » et les trois badges de pied de page.

## Ce qui est bien

- La fiche qualité de l'air publie ses échecs et distingue explicitement ce que le projet ne démontre pas ; cette discipline ne doit pas disparaître lors du raccourcissement.
- Les statuts « fait / pas encore fait » d'Aegis-RCA et Vigilance donnent une base honnête ; il faut seulement résoudre leurs contradictions locales.
- Les rangs Kaggle comportent systématiquement leur dénominateur, ce qui permet de comprendre immédiatement la difficulté relative.
- Les pages de recherche montrent les résultats négatifs par strate au lieu de ne conserver que les gains ; c'est précisément ce qui a permis de repérer l'excès de la conclusion TSAD.
- Le portefeuille contient plusieurs formulations accessibles réussies, notamment « apprendre l'erreur du modèle européen, et la retirer » et l'explication en clair du rôle d'Aegis-RCA ; elles doivent devenir la norme de l'accueil.
