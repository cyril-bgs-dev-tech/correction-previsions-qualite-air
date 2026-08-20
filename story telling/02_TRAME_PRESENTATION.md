# Trame de présentation — 12 écrans

> **Mise à jour du 20/08/2026.** L'écran 4 s'arrêtait au creux (+1,5 %) sans dire que les
> leviers trouvés depuis le comblent ; l'écran 9 décrivait une architecture qui n'est plus
> celle du système (membres et feux ont été **retirés** de la pile) ; et l'horizon
> réglementaire, qui est l'argument le plus direct pour une AASQA, était absent.

Format recommandé : 12 à 14 minutes, puis discussion. Un message et un visuel par écran. Les titres sont des conclusions, pas des rubriques.

## Écran 1 — « Une meilleure moyenne peut encore manquer l’épisode »

**Visuel.** Une journée réelle : trois repères seulement — observation, CAMS, correction — et le seuil de 120 µg/m³. Si aucun cas propre n’est figé dans la source de vérité, utiliser un schéma explicitement marqué « illustration », pas un chiffre reconstruit.

**À dire.** « J’ai commencé par vouloir réduire l’erreur de CAMS. Le projet m’a appris que la question utile est plutôt : à combien de fausses alertes sommes-nous prêts, et combien de jours à risque retrouvons-nous alors ? »

**À éviter.** Logo LightGBM, liste de données ou `+30 %` en plein écran.

## Écran 2 — « Le produit vise l’attention du prévisionniste, pas son remplacement »

**Visuel.** Flux simple : `CAMS + données disponibles à l’émission → risque + concentration → expertise humaine`.

**À dire.** « La sortie utile est un ordre de risque et une concentration corrigée. Le système indique où regarder ; il ne déclenche pas seul une procédure. »

**Question à laisser ouverte.** Heure de coupure et unité de décision réelles chez ATMO Occitanie.

## Écran 3 — « Le protocole exclut les stations qu’il évalue »

**Visuel.** Carte simplifiée avec stations d’entraînement d’une couleur et stations de test d’une autre ; encart `270 stations`, période et trois polluants selon `VERITE_DOSSIER.md`.

**À dire.** « Chaque station évaluée est prédite par un modèle qui ne l’a jamais vue. Cela teste le transfert vers une autre station du réseau — pas vers tout point du territoire. »

**Détail en réserve.** Covariables : CAMS, calendrier, paysage, relief, trafic ; observations passées seulement dans l’usage A.

## Écran 4 — « Spatialement, le signal est fort ; temporellement, il ne l’est pas »

**Visuel.** Trois barres : stations cachées `+29,7 %` ; mois caché `+6,7 %` ; station × mois `+1,5 %`. Sous chaque barre, pire pli : positif / `−35,5 %` / `−41,4 %`.

**À dire.** « C’est la slide de vérité. Le modèle transfère bien dans l’espace du réseau, mais sa robustesse à un mois nouveau n’est pas démontrée. »

**Effet recherché.** Installer la confiance avant les résultats favorables — et poser la question à laquelle l’écran suivant répond.

## Écran 4 bis — « Ce qui manquait était une information, pas un algorithme »

**Visuel.** Une flèche du `+1,5 %` de l’écran précédent vers quatre barres : O₃ `+17,9 %`, NO₂ `+39,6 %`, PM10 `+20,2 %`, PM2,5 `+11,8 %`. Mention obligatoire sous le visuel : **même protocole, station ET mois cachés, J+1**.

**À dire.** « Le levier décisif est arrivé tard : sept traceurs de composition du champ CAMS que le dépôt ne téléchargeait pas. Ils apportent de 1,5 % sur le NO₂ à 6 % sur les PM10, avec un intervalle qui exclut zéro sur les quatre polluants, après correction de Holm. »

**Et le mécanisme, si on vous le demande.** « J’ai permuté la composition à l’intérieur de chaque couple station-mois : ça conserve l’histogramme par site et par saison, et ne détruit que l’appariement au jour. Le gain disparaît en totalité, sur les quatre polluants. Ce n’est donc ni un encodeur de site, ni un proxy de saison : c’est l’écart du jour à la composition habituelle du lieu. »

**À éviter.** Montrer ce résultat avant l’écran 4. L’ordre fait toute la démonstration.

## Écran 5 — « La cible compte vingt fois plus que la bibliothèque »

**Visuel.** Tableau minimal : O₃ `+5,8 pts`, NO₂ `+6,5 pts`, PM2,5 `−1,5 pt` lorsqu’on apprend directement la grandeur réglementaire. À côté : écart entre bibliothèques `0,3 pt`.

**À dire.** « Pour un maximum, corriger l’heure puis agréger écrase de la variabilité. Pour une moyenne journalière, l’effet s’inverse. Bertrand et al. l’avaient déjà montré : ici, je le réplique sur une autre période et un autre algorithme. »

**À éviter.** Revendiquer la découverte.

## Écran 6 — « À budget de fausses alertes égal, l’ordre des jours change la décision »

**Visuel principal.** Courbe rappel–FAR ou quatre points aux budgets 10, 20, 30 et 40 %. Mettre en évidence à 30 % : CAMS `0,184`, correction complète `0,656`, soit `3,6×`.

**À dire.** « Un service ne choisit pas le seuil qui flatte un score ; il supporte un budget de fausses alertes. À budget identique, la correction rappelle beaucoup plus de dépassements d’O₃. »

**Nuance obligatoire.** Préciser que les seuils sont choisis hors échantillon.

## Écran 7 — « Le facteur se reproduit hors fenêtre, pas toute la précision ponctuelle »

**Visuel.** Petit tableau : à FAR ≤ 20/30/40 %, facteurs 17 mois `6,6× / 3,6× / 2,0×` et 2025 `6,8× / 3,5× / 1,9×`.

**À dire.** « Le modèle généralise mieux comme classement de risque que comme valeur exacte. Sur le test Occitanie 2025, la seule différence ferme face au MOS officiel reste la RMSE : −3,22 µg/m³, avec un intervalle entièrement négatif. Les écarts de détection sont descriptifs. »

**À éviter.** Dire que la supériorité en CSI 2025 est démontrée.

## Écran 8 — « Trois limites dessinent le périmètre utile »

**Visuel.** Trois cartes rouges sobres : temps, NO₂, support spatial.

- **Temps :** station × mois `+1,5 %`, 8 plis négatifs sur 17.
- **NO₂ :** 270 dépassements, aucun budget ≤ 40 % atteignable.
- **Support :** une station exclue n’est pas une commune non instrumentée.

**À dire.** « Ces limites ne sont pas une annexe. Elles définissent les garde-fous et les prochaines données à acquérir. »

## Écran 9 — « Les prochains leviers sont opérationnels, pas architecturaux »

**Visuel.** Trois marches : observations J−2 ; météo prévue IFS/AIFS ; spéciation et typologie déjà intégrées.

**À dire.** « Les observations passées sont le levier déployable le plus fort, notamment `+21,9 %` sur le NO₂ en RMSE. ERA5 donne un plafond, pas une performance ; l’étape correcte est de mesurer ce qu’IFS/AIFS en récupèrent à l’émission. »

**⚠️ Ce qui a été RETIRÉ de la pile, et pourquoi c’est une bonne histoire.** Les membres d’ensemble et les feux en faisaient partie jusqu’au 17/08. Quand une famille de variables manque sur un mois entier, l’algorithme apprend une direction par défaut pour les valeurs absentes — donc il apprend **la date**. Le protocole cachant les mois, c’est une fuite. Trois occurrences trouvées, deux étages retirés. **Ne pas décrire l’architecture avec des étages qui n’y sont plus.**

**À éviter.** Présenter des pistes comme des gains acquis.

## Écran 9 bis — « L'échéance 2030 rend la modélisation obligatoire, et le produit brut n'y passe pas »

**Visuel.** À gauche, deux barres : stations en dépassement `6` aujourd'hui, `109` en 2030 — même air, seuil divisé par deux. À droite, le critère FAIRMODE sur le NO₂ : `41,4 %` brut, `96,2 %` corrigé, avec la barre des 90 % tracée.

**À dire.** « La directive de 2024 fait deux choses qu'on cite toujours séparément : elle divise les valeurs limites annuelles par deux au 1ᵉʳ janvier 2030, et elle rend la modélisation obligatoire dans toute zone où un seuil est dépassé. Multipliées, elles signifient que le nombre de zones où modéliser devient une obligation légale augmente mécaniquement. Et là où le modèle devient opposable, sa qualité devient un point de contrôle. »

**Le chiffre qui parle à une AASQA d'Occitanie.** Quatre départements sur treize n'ont **aucune station** retenue au seuil 2030 : pour eux, la conformité ne peut pas être posée depuis la mesure. C'est exactement le cas que la directive confie à la modélisation.

**Nuance obligatoire.** Les moyennes 2025 ne sont pas une prévision de 2030 — les émissions baisseront. Cette mesure isole l'effet du **changement de seuil, à air constant**.

**Et le chiffre qui ne passe pas, à dire aussi.** Sans aucune observation du point, le NO₂ atteint 87,9 % — **sous** la barre des 90 %. Il ne la franchit qu'aux stations instrumentées.

## Écran 9 ter — « Contre le produit réellement diffusé »

**Visuel.** Trois paires de barres, mêmes stations et mêmes jours : O₃ `+13,7 %`, NO₂ `+59,8 %`, PM2,5 `+66,9 %`. En bas, en gros : **17 jours**.

**À dire.** « L'archive de PREV'AIR porte dans sa métadonnée qu'il s'agit de CHIMERE combiné aux observations — c'est-à-dire AS-CHI, leur adaptation statistique. C'est donc bien le produit en service, pas une reconstruction. »

**Réserve à énoncer AVANT qu'on la demande.** « Dix-sept jours ne concluent rien. Leur archive n'expose que six jours glissants et ne peut pas remonter le temps ; je l'ai constituée jour après jour. C'est un ordre de grandeur. »

**Effet recherché.** Montrer qu'on connaît la valeur exacte de son propre chiffre.

## Écran 10 — « Trois choix métier décideront du bon système »

**Visuel.** Trois questions, beaucoup d’espace blanc :

1. À quelle heure la décision doit-elle être disponible ?
2. Quel budget de fausses alertes est supportable selon le polluant ?
3. Le besoin porte-t-il sur une station, une zone ou une commune ?

**À dire.** « Je n’arrive pas avec un seuil à imposer. J’arrive avec un protocole pour mesurer la conséquence de chacun de ces choix. »

## Annexes indispensables

Préparer sans les montrer spontanément :

1. matrice complète CAMS / MOS officiel / projet par polluant et grain ;
2. intervalles bootstrap 2025 et longueurs de blocs 3, 7, 14 jours ;
3. conformité FAIRMODE v3.2 et limites station par station NO₂ ;
4. liste exacte des variables et disponibilité à l’émission ;
5. protocole de validation et choix des seuils hors échantillon ;
6. résultats négatifs : double aveugle, NO₂, détection d’anomalies, modèle spécialiste ;
7. distinction usage A — stations instrumentées — et usage B — lieux sans observation récente.

## Version courte en 5 écrans

Si le temps tombe à cinq minutes :

1. paradoxe RMSE / épisode ;
2. protocole stations exclues ;
3. le creux et sa sortie : double aveugle `+1,5 %` en base, `+17,9 %` O₃ et `+39,6 %` NO₂ avec la pile complète ;
4. l'usage : `6 → 109` stations en dépassement en 2030, et FAIRMODE `41,4 % → 96,2 %` sur le NO₂ ;
5. trois limites et trois questions métier.

