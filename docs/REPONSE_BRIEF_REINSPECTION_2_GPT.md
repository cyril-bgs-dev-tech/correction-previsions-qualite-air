# Contre-audit n°2 — défauts créés par les corrections

## Verdict en cinq lignes

- V6 est maintenant arithmétiquement juste, mais V7 contient le nouveau défaut bloquant : son +5,92 n'utilise pas le zéro annoncé par la figure.
- La correction « protocole unique » de V7 n'a pas gagné le récit autour : plusieurs textes et l'ancien `alt` comparent encore le routeur strict à un KNN d'un autre régime.
- La conclusion TSAD, le signe dans `index.qmd`, le statut Kaggle, les badges de workers et les promesses de déploiement montrent une propagation M4 encore incomplète.
- Les replis ont réellement allégé la lecture, mais un repli externe annule celui des six projets M1 et plusieurs résumés « Détails techniques » masquent aussi limites, résultats ou sorties.
- FAIRMODE, les deux piles QA, V1, V3, V4, V5, V6 et V8 tiennent ; l'existence des artefacts, variantes sombres et cibles réellement contrôlées n'est pas vérifiable dans le corpus fourni.

## ① Défauts iatrogènes — ce qu'une correction a créé

### 🔴 bloquant — mécanisme M3 · `v7_routeur_tabulaire_clair.svg` · le plafond ne part pas du zéro affiché

- **Citation exacte** : « Contre l'ensemble fixe de 18 détecteurs, le routeur source-strict gagne 1,48 point d'AUROC, la spécialisation par domaine 1,00, et la sélection parfaite 5,92. » La même figure fixe pourtant son zéro à « l'ensemble fixe de 18 détecteurs (71,31) ».
- **Ce qui cloche** : les trois barres partent graphiquement du même zéro, mais la troisième utilise un autre comparateur.
- **La preuve** : le README du dépôt donne les quatre moyennes du fichier strict : `router_src` 72,79 · `ens18` 71,31 · `tuned_dom` 72,31 · `oracle` 78,71. Donc 72,79 − 71,31 = **+1,48**, 72,31 − 71,31 = **+1,00**, et 78,71 − 71,31 = **+7,40**. Le **+5,92** affiché vaut 78,71 − 72,79 : c'est la marge entre l'oracle et le routeur, pas l'écart à l'ensemble fixe.
- **Réparation** : remplacer le `<title>` par « Contre l'ensemble fixe de 18 détecteurs, le routeur source-strict gagne 1,48 point d'AUROC, la spécialisation par domaine 1,00 et la sélection parfaite 7,40. » Remplacer l'étiquette `+5,92` par `+7,40` et recalculer cette seule barre sur la même échelle que les deux autres.
- **Ce que ça retire** : la valeur `+5,92` et la barre calculée depuis le routeur ; aucune nouvelle série n'est ajoutée.

### 🔴 bloquant — mécanisme M4 · `README.md` et `anomaly_tabular/README.md` · V7 a changé de protocole, pas son récit

- **Citation exacte** : l'alternative encore insérée dans la fiche dit : « Contre le meilleur détecteur unique, le routeur source-strict gagne 3,0 points d'AUROC, la spécialisation par domaine 2,5, et l'oracle 8,9. » L'accueil affirme de même : « routeur source-strict 72,8 AUROC [...] contre 69,8 pour le meilleur détecteur unique — soit +3,0 points ».
- **Ce qui cloche** : V7 a été refaite depuis `router_lodosrc_actions_strict.csv`, mais l'`alt`, le paragraphe d'ouverture, le tableau et l'accueil conservent la comparaison antérieure au KNN. Le dépôt avertit pourtant : « Les deux fichiers de routeur ne décrivent pas le même protocole » ; le fichier strict cité comme autorité ne contient que `router_src`, `ens18`, `tuned_dom` et `oracle`.
- **La preuve** : dans le seul régime source-strict documenté, le comparateur disponible est l'ensemble fixe à 71,31 et le gain du routeur vaut **+1,48**, non +3,0. Aucun score KNN source-strict n'est fourni au § 9 pour soutenir 72,79 − 69,8.
- **Réparation** : remplacer la phrase de l'accueil par « Tabulaire : **routeur source-strict 72,8 AUROC** (pré-enregistré, LODO groupé par source), contre **71,3** pour l'ensemble fixe évalué dans le même fichier — soit **+1,48 point** ; oracle du protocole à **78,7**. » Dans la fiche, remplacer « dépasse le meilleur détecteur unique de +3.0 points » par « dépasse l'ensemble fixe de 18 détecteurs de +1,48 point dans le protocole source-strict ». Après correction de V7, remplacer son `alt` par : « Contre l'ensemble fixe de 18 détecteurs à 71,31, le routeur source-strict gagne 1,48 point d'AUROC, la spécialisation par domaine 1,00 et la sélection parfaite 7,40. »
- **Ce que ça retire** : les comparaisons `+3,0`, `+2,5` et `+8,9` placées à côté du protocole strict ; les valeurs brutes 72,8 et 78,7 restent.

### 🔴 bloquant — mécanisme M4 · `anomaly_tsad/README.md` et `index.qmd` · l'universalité survit à sa réfutation

- **Citation exacte** : la fiche annonce encore que « le système obtient de meilleurs résultats que n'importe quel modèle utilisé seul » ; `index.qmd` conclut encore « la composition bat le champion global ».
- **Ce qui cloche** : la correction a bien rétabli la strate négative dans le dépôt de code et V8, mais n'a pas remplacé les deux conclusions générales.
- **La preuve** : le dépôt tranche littéralement : « tout le multivarié (d ≥ 2) : **−0,01** » et « Sur l'ensemble du multivarié, le routage **ne bat pas** le meilleur modèle seul. » Les gains ne deviennent positifs qu'à d ≥ 8 (+0,03) et d ≥ 20 (+0,07).
- **Réparation** : dans la fiche, remplacer la phrase universelle par « Sur l'ensemble multivarié, le routage ne bat pas le meilleur modèle seul (−0,01). Il devient positif à partir de huit variables (+0,03) et atteint +0,07 à partir de vingt. » Dans `index.qmd`, remplacer « la composition bat le champion global » par « la composition ne bat le champion qu'à partir de huit variables ; elle perd 0,01 sur l'ensemble multivarié ».
- **Ce que ça retire** : deux conclusions universelles ; la strate négative et les deux strates positives restent toutes trois visibles.

### 🟠 important — mécanisme M4 · portefeuille tabulaire · le même corpus a 19 et 20 domaines

- **Citation exacte** : l'accueil affiche « 502 datasets · 20 domaines » et la fiche répète « 502 datasets / 20 domaines applicatifs ». Le dépôt de code affiche « 502 jeux · 19 domaines · 440 sources » et précise que « dix domaines sur dix-neuf ne contiennent aucune anomalie native ».
- **Ce qui cloche** : le volume de 502 est stable, mais son découpage change sans qu'un périmètre distinct soit nommé.
- **La preuve** : `index.qmd` et le dépôt de code concordent sur 19 ; la fiche et le badge concordent sur 20. Le corpus ne fournit aucune vingtième catégorie ni table de passage 20 → 19.
- **Réparation** : remplacer `20 domaines` par `19 domaines` dans le badge de `README.md`, l'état du projet, la section « caractérisation des domaines » et le lien de projet frère de la fiche tabulaire. Si 20 désigne un ancien périmètre, ne le conserver qu'avec le nom explicite du domaine ensuite fusionné ou retiré.
- **Ce que ça retire** : quatre occurrences non expliquées de `20 domaines` ; aucun dataset ni domaine documenté n'est supprimé.

### 🟠 important — mécanisme M4 · `index.qmd` · la page de secours conserve trois formulations antérieures

- **Citation exacte** : `index.qmd` contient encore « 35+ compétitions complétées », « Apprendre l'erreur du modèle européen, et la retirer » et « Algorithme de niveau recherche validé par le responsable scientifique ».
- **Ce qui cloche** : les pages détaillées emploient respectivement « engagées », expliquent que la correction `observation − CAMS` est **ajoutée**, et la correction n° 10 annonce le remplacement des superlatifs DELTAMU. `index.qmd` est devenu un fossile cohérent avec l'état précédent, pas avec le corpus courant.
- **La preuve** : la page compétitions titre « 35+ compétitions engagées » ; les deux pièces QA disent « apprend la correction [...] puis l'ajoute » ; `corrige = cams + sortie` est la règle donnée au § 3.
- **Réparation** : remplacer les trois fragments par « 35+ compétitions engagées », « Apprendre la correction du modèle européen, et l'ajouter à sa prévision » et « Algorithme de détection d'anomalies validé par le responsable scientifique ».
- **Ce que ça retire** : `complétées`, `retirer` et `de niveau recherche` ; aucune réalisation n'est retirée.

### 🟠 important — mécanisme M4 · `README.md` · badges et pied de page ont échappé au correctif

- **Citation exacte** : le badge workers affiche encore « Workers — 9 × 4 réplicas » ; le badge recherche « Reproductions exactes validées » ; le pied de page conserve « Le code ne ment jamais, les commentaires oui », « Built with Quarto » et « Deployed on GitHub Pages ».
- **Ce qui cloche** : le tableau en tête dit déjà « pool de 3 réplicas CPU + 1 GPU », distingue « 2 scores reproduits à l'identique » de « 5 détecteurs réexécutés », et le § 3 dit que le site Quarto n'a jamais été construit. Le correctif a touché le texte, pas les objets décoratifs qui répètent l'ancien état.
- **La preuve** : les contradictions sont internes au même `README.md` ; aucune vérification externe n'est nécessaire.
- **Réparation** : supprimer les lignes des badges `Workers` et `Repro`, déjà redondantes avec les faits marquants corrigés. Supprimer la citation, le badge Quarto et le badge GitHub Pages du pied de page. Conserver « Sources et résultats bruts versionnés » et la date.
- **Ce que ça retire** : cinq lignes fausses ou redondantes ; rien n'est ajouté.

### 🟡 confort — mécanisme M4 · `about.qmd` et `projets_Master_2/README.md` · le retrait du jargon a dupliqué les tests

- **Citation exacte** : « Rapprochement automatisé de données de pricing hétérogènes, et tests de non-régression » est immédiatement suivi de « Tests de non régression » dans les deux fichiers.
- **Ce qui cloche** : la reformulation qui remplace le jargon a absorbé le contenu de la puce suivante sans supprimer cette dernière.
- **La preuve** : les deux lignes contiguës nomment la même action ; le doublon est reproduit à l'identique dans les deux pages.
- **Réparation** : conserver une seule puce : « Rapprochement automatisé de données de pricing hétérogènes et tests de non-régression. »
- **Ce que ça retire** : la puce isolée « Tests de non régression » et la virgule avant `et` dans les deux fichiers.

### 🟠 important — mécanisme M2 · `projets_Master_1/README.md` · le repli des six derniers replie aussi les quatre premiers

- **Citation exacte** : un premier bloc s'ouvre sur « Détails techniques » avant `## Vue d'Ensemble`; un second s'ouvre sur « Les six autres projets » avant le projet 5 ; la fermeture du premier n'arrive qu'après « Livrables complets [...] disponibles sur demande ».
- **Ce qui cloche** : la correction n° 16 voulait replier six projets sur dix. Le `<details>` externe replie en réalité les dix projets, la synthèse, la transition M2 et le contact ; les six derniers demandent deux ouvertures.
- **La preuve** : l'imbrication source est complète : projets 1 à 4 entre l'ouverture externe et l'ouverture interne, projets 5 à 10 dans les deux, puis synthèse et transition encore dans l'externe.
- **Réparation** : supprimer seulement l'ouverture `<details><summary>...Détails techniques...</summary>` placée avant `## Vue d'Ensemble` et son `</details>` final. Conserver intact le bloc « Les six autres projets » autour des projets 5 à 10.
- **Ce que ça retire** : un niveau de repli et deux balises ; aucun projet, feedback ou texte n'est ajouté.

### 🟠 important — mécanisme M2 · cinq fiches · « Détails techniques » replie autre chose que de la technique

- **Citation exacte** : le même résumé « Détails techniques » englobe `## Limites honnêtes` et `## Prochaine étape` dans Aegis ; `## Évolutions prévues` et « Code source » dans Vigilance ; `## Statistiques Globales` et les rangs dans Compétitions ; « Feedback Michelin » et les sept projets dans M2 ; « Prochaines actions intelligentes » et le dépôt dédié dans la fiche tabulaire.
- **Ce qui cloche** : la compression est défendable, mais le libellé promet un type de contenu plus étroit que le bloc réel. Dans Aegis et Vigilance, les deux diagrammes qui donnent le point d'entrée du système sont eux-mêmes repliés.
- **La preuve** : dans chaque source, les titres cités se trouvent entre l'ouverture et l'unique fermeture du bloc.
- **Réparation** : dans Aegis, déplacer l'ouverture juste avant `## Architecture` et la fermeture juste avant `## Limites honnêtes`. Dans Vigilance, laisser le Mermaid et son paragraphe avant l'ouverture, puis fermer avant `## Évolutions prévues`. Remplacer les trois autres résumés par « Palmarès détaillé, méthodes et évolution » (Compétitions), « Alternance Michelin et sept projets académiques » (M2) et « Benchmark, résultats détaillés et prochaines étapes » (tabulaire).
- **Ce que ça retire** : deux replis sur les diagrammes et quatre libellés trompeurs ; le contenu reste au même volume.

### 🟠 important — mécanisme M2 · Mermaid Aegis et Vigilance · le remplacement de l'ASCII n'a pas d'équivalent textuel

- **Citation exacte** : Aegis se contente de « La frontière est le sujet du projet » après son Mermaid ; Vigilance de « trois détections parallèles et décorrélées ne produisent pas trois alertes, mais un seul incident ». Le flux Aegis renvoie en outre un refus « au prévisionniste » alors que la page nomme partout un « opérateur ».
- **Ce qui cloche** : ces phrases donnent la conclusion, pas le parcours complet ni les embranchements. Le remplacement visuel a donc retiré l'équivalent textuel de la structure ; Aegis a aussi importé le mauvais métier.
- **La preuve** : aucun texte hors Mermaid n'énumère, pour Aegis, incident → contexte → RAG → LLM → validation → sandbox/refus ; ni, pour Vigilance, entrée → quatre canaux → fusion → explication → ticket → cockpit.
- **Réparation** : remplacer la phrase après V9 par : « **Alternative textuelle —** Un incident ouvert par Vigilance fournit métriques et logs ; le RAG sélectionne les procédures ; Qwen3.6:27B rédige diagnostic et recommandation ; un opérateur accepte leur exécution en sandbox isolée ou renvoie le dossier pour correction. Aucune action n'est exécutée sans validation humaine. » Remplacer `Retour au prévisionniste` par `Retour à l'opérateur`. Remplacer la phrase après V2 par : « **Alternative textuelle —** Les événements de trois machines passent par l'extraction de variables, puis par trois détecteurs parallèles — IsolationForest, résidu Ridge et reconstruction PCA — complétés par les règles capteur ; XGBoost fusionne les trois scores, SHAP explique l'événement, puis le système ouvre un ticket unique par épisode et l'affiche dans le cockpit Streamlit. »
- **Ce que ça retire** : les deux commentaires partiels et le terme `prévisionniste` ; aucune nouvelle section n'est créée.

### 🟠 important — mécanisme M6 · sept SVG · le contrôle responsive regarde le fichier, pas la taille rendue

- **Citation exacte** : les nouveaux SVG ont des `viewBox` de 700 à 780 px, des corps fréquents à `15.5`, parfois `13`, et sont insérés avec `width="100%"`.
- **Ce qui cloche** : les figures se réduisent désormais, mais leur typographie se réduit avec elles. Le correctif a agrandi la valeur source sans vérifier la valeur effective au viewport demandé.
- **La preuve** : à 380 px, V1 applique un facteur 380/700 : un corps 15,5 devient **8,4 px**. V5 applique 380/780 : ses annotations à 13 deviennent **6,3 px**. V6–V8 appliquent 380/760 : 15,5 devient **7,8 px** et un titre à 20 devient **10 px**. Le défaut annoncé à 6,6 px a donc changé de forme, pas disparu.
- **Réparation** : remplacer les sept versions par des compositions mobile-first avec `viewBox="0 0 380 …"`, aucun corps inférieur à `14`, titres et libellés longs sur deux lignes, puis laisser ces figures s'agrandir sur bureau. Conserver toutes les valeurs et tous les canaux non chromatiques.
- **Ce que ça retire** : les sept canevas larges actuellement réduits ; aucune règle CSS ni JavaScript n'est ajoutée.

### 🟡 confort — mécanisme M4 · `projets_Qualite_Air/README.md` · l'alternative de V6 n'a pas suivi la reconstruction

- **Citation exacte** : l'`alt` inséré dit seulement : « la pile passe de 26,6 % pour la base à 40,2 % avec la spéciation, la typologie de station apportant le plus gros saut. »
- **Ce qui cloche** : la correction n° 6 a précisément rétabli les sept étages et leurs apports ; l'alternative n'en restitue que le départ, l'arrivée et le plus gros saut.
- **La preuve** : le SVG contient six apports : +9,0 · +0,5 · +0,3 · +2,3 · +0,2 · +1,3, dont les deux étapes « membres » et « feux » que le § 5 interdit de reperdre.
- **Réparation** : remplacer l'`alt` par : « Sur le NO₂ à J+1 en double aveugle, la base vaut 26,6 %, puis la typologie 35,6 (+9,0), les membres 36,1 (+0,5), les feux 36,4 (+0,3), GEOS-CF 38,7 (+2,3), la tendance récente 38,9 (+0,2) et la spéciation 40,2 (+1,3) ; membres et feux ont ensuite été retirés de la pile publiée. »
- **Ce que ça retire** : l'alternative abrégée ; aucune information visible n'est ajoutée.

## ② Défauts d'origine encore présents

### 🟠 important · Aegis · phases incompatibles

La preuve annonce « Incidents à cause connue (**gate Phase C, 14 cas**) » alors que les limites disent « **Phase A/B seulement** ». Remplacement exact : « Prototype de trois jours : composants des phases A/B fonctionnels et banc d'entrée de phase C exécuté sur 14 cas ; aucune validation en production. » Cette phrase remplace les deux niveaux de phase contradictoires.

### 🟠 important · Master 1 · la progression annoncée est réfutée par le dernier projet cité

L'introduction affirme que la présentation « s'est nettement améliorée au fil des projets (voir le dernier [...], où ce retour a été le plus explicite) ». Le projet 10 conclut au contraire : « il faut faire un effort sur la présentation des résultats », et la synthèse nomme une « soutenance confuse ». Remplacement exact : « Les retours confirment une base technique solide. La communication est restée un axe de progression : plusieurs projets sont jugés clairs, mais le projet 10 signale encore une soutenance confuse. »

### 🟠 important · dépôt QA · J0 introduit une page dont le résultat est J+1

L'ouverture dit que le modèle apprend la correction « à l'échéance **J0** », puis `## Le résultat` annonce « Échéance **J+1**, les trois polluants au même horizon ». Le corpus ne dit pas si deux modèles distincts sont entraînés. Remplacement exact de l'ouverture : « Le modèle apprend la correction `observation − CAMS`, puis l'ajoute à la prévision CAMS. Les résultats principaux ci-dessous sont évalués à J+1, soit les heures 25–48. »

### 🟡 confort · Master 2 · un framework reste à l'état d'alternative de brouillon

Le projet 6 conserve « Framework : **TensorFlow/Keras ou PyTorch** », puis « Technologies : TensorFlow/PyTorch ». Le corpus ne permet pas de choisir lequel. Réparation : supprimer les deux mentions de framework ; le feedback prouve CNN, transfert et augmentation, pas la bibliothèque employée.

### 🟡 confort · Compétitions · une coquille rend la méthode indécidable

La F1 contient « Stacking avec **régression métique** ». Remplacement exact : « Stacking avec un méta-modèle de régression. »

### 🟡 confort · accueil · la proposition de valeur reste générique

« Data Scientist | MLOps Engineer | Problem Solver » et « passionné [...] perspective unique [...] communication efficace » précèdent toutes les preuves. Remplacement exact des deux blocs : « **Data Scientist — détection d'anomalies, évaluation rigoureuse et systèmes MLOps.** Je transforme des résultats expérimentaux en systèmes reproductibles : correction de prévisions de qualité de l'air, routage de détecteurs et pipelines temps réel observables. »

## ③ Ce que je n'ai PAS pu vérifier depuis le corpus fourni

### Artefacts tabulaires réellement publiés

Le corpus donne des liens vers `results/router_lodosrc_actions_strict.csv`, `router_v5.csv`, `router_vs_outformer_v2.csv` et `metaod_verdict.csv`, ainsi que quatre moyennes déclarées, mais aucun contenu CSV, taille, hash ni arbre du dépôt. Je peux vérifier l'arithmétique des nombres cités, pas que les fichiers existent, portent 502 lignes, ni que le premier est bien celui lu par la présentation. Il faudrait l'arbre du commit audité et les quatre fichiers eux-mêmes.

### Suppressions réelles

L'absence de `auroc_par_domaine.md` et de la fiche Vision dans un corpus composé d'extraits ne prouve pas leur suppression. Il faudrait un arbre complet du même commit, ou un diff qui montre leur retrait. Je ne transforme donc pas leur absence au § 9 en contrôle M5 réussi.

### Variantes sombres

Le § 9 fournit le source des sept variantes claires seulement. Les références `*_sombre.svg` sont visibles, mais ni leur contenu ni leurs contrastes ni l'identité de leurs données ne le sont. Je ne peux pas confirmer qu'une variante sombre n'a pas conservé l'ancienne V6 ou l'ancien V7.

### Résolution effective des chemins et liens

Les formes relatives sont maintenant logiques — `assets/` depuis la racine, `../assets/` depuis les fiches, `reports/figures/portefeuille/` depuis le dépôt QA — mais le corpus ne contient pas l'arborescence correspondante. Il ne permet pas davantage de contrôler les pages interactives, dépôts ou miroir public. Ce point M5 reste non vérifié, et non déclaré défectueux.

### Rendu réel des `<details>` et conflit propre au brief

Le § 4 affirme que la réserve TSAD est « visible, hors de tout bloc replié », tandis que l'extrait du § 9 place l'ouverture `<details>` avant `## 1` et sa fermeture après le contact ; V8 et la strate −0,01 se trouvent textuellement entre les deux. Sans rendu du fichier exact ou source corrigée concordante, je ne tranche pas sa visibilité et je ne répète pas le défaut réfuté.

### Cible réelle des contrôles

Les phrases « 273 passent » et « vérifié [...] par clone » ne sont accompagnées ni du journal d'exécution ni de l'URL/du SHA du clone. De même, rien ne prouve que la présentation consomme le CSV strict plutôt qu'un artefact homonyme. C'est précisément le risque M6 ; il faudrait la commande, son répertoire courant, le SHA contrôlé et la sortie qui nomme l'artefact lu.

## ④ Ce qui est mieux qu'avant — et ne doit pas être défait

- **V6 tient enfin.** Les sept niveaux sont présents et les valeurs arrondies se ferment : 26,6 + 9,0 + 0,5 + 0,3 + 2,3 + 0,2 + 1,3 = 40,2. « Membres » et « feux » doivent rester parce que la figure restitue la mesure historique du § 12.
- **FAIRMODE tient sur toutes les pièces visibles.** 87,9 % reste associé à `PARTOUT`, sous 90 %, et 96,2 % aux stations instrumentées ; V3, les deux README QA, l'accueil et `index.qmd` concordent.
- **Le signe et les deux piles QA sont correctement expliqués dans les trois pièces principales.** La correction `observation − CAMS` est ajoutée, et le balayage J0→J+3 annonce explicitement sa pile réduite avant V5 et avant le tableau.
- **Le dépôt TSAD conserve la réserve qu'il ne faut surtout pas lisser.** Il publie −0,01, +0,03 et +0,07, nomme le warm-start comme levier distinct et dit littéralement que le routage à froid ne bat pas PaAno de façon fiable.
- **Le repli du dépôt QA est bien délimité.** « Installer, vérifier, reproduire » contient exactement installation, commandes, protocole et organisation ; les résultats, réserves et sources restent dans le fil principal. Je n'ai par ailleurs trouvé aucun connecteur orphelin du type « comme vu plus haut » dans le corpus fourni.
