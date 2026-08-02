# Bloc A — Le plafond : combien reste-t-il vraiment à gagner ?

**Correction préalable.** **[jugement]** `16,97 → 14,0` correspond à une baisse de RMSE
de **17,5 %**, pas d’environ 12 %. L’écart avec LightGBM est bien voisin de
0,32 µg/m³, mais l’écart de gain est d’environ 1,9 point. Il faut corriger la table avant
de comparer les architectures.

## Q1. Erreur irréductible

**[publié]** La prémisse d’un plancher décomposable en trois RMSE indépendantes est
fausse : erreur instrumentale, représentativité et erreur du modèle partagent des
composantes corrélées. On ne peut donc pas additionner trois ordres de grandeur en
quadrature sans les estimer conjointement.

FAIRMODE v3.2 paramètre une *incertitude de mesure utilisable pour le benchmarking*, pas
un bruit irréductible. Sa formule donne, à titre illustratif, environ 19 µg/m³ pour
O₃ = 80 µg/m³ et 13 µg/m³ pour NO₂ = 40 µg/m³ avec les paramètres du tableau 6 ; ces
valeurs ne sont ni des RMSE instrumentales observées ni des planchers de prévision
(Janssen et Thunis, 2020, JRC, [doi:10.2760/30226](https://doi.org/10.2760/30226)).

**[publié]** La représentativité est fortement dépendante du polluant et du site. Les
gradients urbains de NO₂ peuvent laisser un écart de 21 % entre mesures ponctuelles et
champ urbain même après harmonisation temporelle (Zhu et al., 2020, *ACP*,
[doi:10.5194/acp-20-13241-2020](https://doi.org/10.5194/acp-20-13241-2020)). Aucun
article trouvé ne fournit un plancher horaire France entière, maille de 8 km, en µg/m³.

**[jugement]** Rien ne permet de dire que 13,68 µg/m³ est proche du plancher. Le fait
qu’un autre post-traitement atteigne 13,99 µg/m³ sur une *autre cible* O₃, en Italie et
sur stations exclues, ne répond pas à cette question.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Information diagnostique ; gain RMSE **Inconnu** | 3–5 h · <1 h | Estimer les deux bornes de Q2 sur O₃ et NO₂ | Abandonner l’idée d’un plancher chiffré si les paires comparables sont trop rares ou donnent des estimations instables selon la distance |

## Q2. Estimation empirique du plancher

**[jugement]** Utiliser deux bornes. La borne basse est la variance des différences entre
analyseurs co-localisés, divisée par deux sous l’hypothèse d’erreurs indépendantes. La
borne haute est la même quantité pour des paires simultanées, proches et de même
typologie, après retrait d’un signal commun `heure × jour × CAMS`. Pour une paire
échangeable, `Var(y₁−y₂)/2` estime la variance non commune.

Cette borne haute surestime le plancher si les deux stations voient de vrais gradients ;
la borne basse le sous-estime car elle ne contient aucune représentativité
maille–station. Il faut apparier sur typologie, altitude, environnement routier et
distance, puis tracer l’estimation en fonction de la distance plutôt que choisir un
rayon après avoir vu le résultat.

**[publié]** L’usage de caractéristiques d’occupation du sol pour définir la
représentativité des stations et son importance pour la validation des modèles est établi
par Janssen et al. (2012, *Atmospheric Environment*,
[doi:10.1016/j.atmosenv.2012.05.028](https://doi.org/10.1016/j.atmosenv.2012.05.028)).

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Pas de gain direct ; borne empirique **Inconnu** | 4–6 h · <1 h | Courbe `sqrt(Var(diff)/2)` par distance, typologie et polluant avec bootstrap par paire | Arrêter si moins de 20 paires indépendantes par strate ou si l’IC95 varie de plus de 50 % entre deux découpages raisonnables |

## Q3. Plafond théorique du post-traitement

**[jugement]** Le seul plafond théorique est l’erreur de Bayes conditionnelle aux
variables disponibles : même le meilleur algorithme conserve
`E[Var(Y | X disponible à l’émission)]`. Elle n’a pas de valeur universelle. Une erreur
de chimie ou d’émissions est corrigeable en aval si elle laisse une signature stable
dans `X`; elle ne l’est pas si la cause change sans prédicteur observable.

**[publié]** FAIRMODE définit un objectif de qualité relatif à l’incertitude de mesure,
pas une limite de prévisibilité ni une fraction structurellement corrigeable
(Janssen et Thunis, 2020,
[doi:10.2760/30226](https://doi.org/10.2760/30226)). Bertrand et al. montrent en outre
qu’un MOS court peut s’adapter aux mises à jour du modèle amont, sans démontrer de plafond
universel (2023, *ACP*,
[doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Gain **Inconnu** ; mesure du signal restant | 2–3 h · 1–2 h | Second modèle strictement out-of-fold décrit en Q7 | Si son gain apparié est <0,5 % ou non positif dans au moins deux des trois plis spatiaux, considérer la capacité résiduelle comme non démontrée |

## Q4. Interprétation du R²

**[publié]** Il n’existe pas de seuil publié séparant R² « moyen », « bon » et
« suspect » pour O₃ horaire à J+1 sur stations exclues. Riccio et Chianese rapportent des
corrélations souvent supérieures à 0,9 après traitement, mais sur des agrégats
journaliers italiens ; leur carré n’est pas comparable à votre R² horaire
(2024, *ACP*,
[doi:10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024)).

**[jugement]** R² = 0,730 est utile parce qu’il est hors station, pas parce qu’il franchit
un seuil. Un score devient suspect par son protocole — coordonnées mémorisées, variables
postérieures à l’émission, prétraitement hors pli — et non par sa seule hauteur. Votre
double aveugle à +8,7 % et très variable rend au contraire peu plausible une fuite
massive et généralisée, tout en signalant une fragilité temporelle.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Aucun gain ; crédibilité accrue | 2 h · nul | Audit de disponibilité temporelle et recalcul de tout prétraitement dans chaque pli | Ne pas créer de catégories « bon/moyen » si aucune référence isométrique n’est trouvée |

## Q5. Où sont passés les dix points ?

1. **Cible horaire contre journalière — probabilité la plus forte. [publié]** Bertrand
   et al. obtiennent 20,5 % quand le maximum journalier est extrait d’un MOS horaire,
   contre 32,8 % quand le MOS vise directement le maximum : 12,3 points dans la même
   étude européenne CAMS, sur stations vues
   ([doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).
2. **Absence d’observation récente — forte. [publié]** Bertrand et al. et Zhang et al.
   l’emploient, mais son gain marginal isolé est **Inconnu**
   ([doi:10.5194/acp-24-807-2024](https://doi.org/10.5194/acp-24-807-2024)).
3. **Période, géographie et version de CAMS — forte. [jugement]** Les dix points ne sont
   probablement pas un « manque » unique : les études n’ont ni le même CAMS, ni les mêmes
   stations, ni le même épisode climatique. Gain attribuable : **Inconnu**.
4. **Qualité et densité des covariables — moyenne. [jugement]** Le NO₂ réagit fortement
   à votre trafic, mais l’O₃ beaucoup moins aux routes ; le gain possible est
   **Inconnu**.
5. **Absence de tuning — faible. [jugement]** Avec trois bibliothèques de boosting déjà
   proches, attendre dix points du tuning est irréaliste. J’attendrais 0–3 % relatifs,
   estimation de praticien et non résultat publié.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Diagnostic ; récupération totale **Inconnu** | 4 h · 3–5 h | Modèle O₃ de maximum journalier 8 h, mêmes plis et mêmes variables, puis ajout séparé des observations récentes | Si la cible journalière ne gagne pas ≥3 points de gain relatif et si les observations récentes n’ajoutent pas ≥1 %, cesser d’expliquer l’écart par ces deux facteurs |

### Références publiées du bloc A

- Janssen, S. et Thunis, P. (2020), *FAIRMODE Guidance Document*, v3.2,
  [doi:10.2760/30226](https://doi.org/10.2760/30226).
- Janssen, S. et al. (2012), *Atmospheric Environment*,
  [doi:10.1016/j.atmosenv.2012.05.028](https://doi.org/10.1016/j.atmosenv.2012.05.028).
- Zhu, Y. et al. (2020), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-20-13241-2020](https://doi.org/10.5194/acp-20-13241-2020).
- Bertrand, J.-M. et al. (2023), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).
- Riccio, A. et Chianese, E. (2024), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024).
- Zhang, Z. et al. (2024), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-24-807-2024](https://doi.org/10.5194/acp-24-807-2024).

# Bloc B — Diagnostiquer ce qui plafonne

## Q6. Une seule décomposition prioritaire

**[jugement]** Produire une matrice chronologique **mois de validation × décile de
concentration observée**, avec biais, RMSE corrigée et différence appariée de carré
d’erreur contre CAMS. C’est une seule décomposition à deux axes, et elle sépare
immédiatement vos deux fragilités : dérive temporelle et queue.

Si le résidu est surtout du bruit, son biais reste proche de zéro, sans blocs
chronologiques persistants, et l’échec du décile haut fluctue autour de zéro. S’il est
structurel, les mêmes cellules gardent un signe, les ruptures CAMS forment des colonnes,
ou la dégradation augmente monotoniquement avec le décile.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Diagnostic ; gain **Inconnu** | 2–3 h · <30 min | Carte avec IC par bootstrap station et nombre d’événements par cellule | Ne pas poursuivre une « cause » si son motif change de signe entre les trois plis spatiaux ou repose sur moins de 30 station-jours |

## Q7. Prévisibilité du résidu après correction

**[jugement]** Le second modèle doit apprendre uniquement des prédictions du premier
générées out-of-fold. Dans chaque pli externe, produire le résidu du premier modèle sur
un pli interne jamais vu, ajuster le second sur ces résidus internes, puis tester les deux
étages sur le pli externe. Ajuster le second étage aux résidus d’entraînement du premier
créerait artificiellement un signal.

Un gain externe avec les mêmes variables indique d’abord une capacité ou une perte
insuffisante ; un gain seulement après ajout d’une famille indique une variable manquante ;
un gain uniquement in-sample indique surapprentissage ou fuite.

**[publié]** Toute sélection ou optimisation doit être répétée à l’intérieur de la boucle
externe pour éviter le biais de sélection (Varma et Simon, 2006, *BMC Bioinformatics*,
[doi:10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91)).

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| 0–1 % **[jugement]** ; valeur surtout diagnostique | 3–4 h · 2–4 h | Second LightGBM très bridé sur résidus OOF, mêmes variables | Abandon si gain <0,5 % ou si un seul pli spatial sur trois est positif |

## Q8. CAMS contre représentativité de station

**[jugement]** Comparer trois écarts pour chaque station : erreur CAMS, erreur corrigée
OOF et désaccord avec des stations voisines appariées de même typologie. Une station dont
CAMS et le modèle corrigé échouent, mais qui désaccorde aussi durablement avec ses
voisines, porte une composante locale non résolue ; une station cohérente avec ses
voisines mais mal prédite pointe plutôt vers CAMS ou les variables.

Ne pas l’exclure après examen. La garder dans le score principal, la nommer dans une
strate « faible représentativité », et fournir une analyse de sensibilité avec exclusion
fondée sur une règle QC écrite avant recalcul.

**[publié]** La représentativité conditionne directement la validation des modèles
(Janssen et al., 2012,
[doi:10.1016/j.atmosenv.2012.05.028](https://doi.org/10.1016/j.atmosenv.2012.05.028)).

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Aucun gain garanti ; attribution de variance **Inconnu** | 4–6 h · <1 h | Corréler erreur OOF et désaccord inter-stations, stratifié par typologie | Abandonner l’étiquette « irrécupérable » si la station n’est pas aberrante dans au moins deux saisons et deux métriques |

## Q9. Calendrier : physique ou mémorisation

**[jugement]** Comparer, sous les seuls plis mois et station×mois : modèle complet ;
modèle sans calendrier ; modèle où le calendrier absolu est remplacé par sin/cos du jour
de l’année et de l’heure. Si les cycles physiques conservent le gain mais que mois/année
bruts le perdent, le calendrier capte une saisonnalité transférable. Si le gain disparaît
hors mois ou change de signe, il mémorise la période d’échantillonnage.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Conservation possible des 9,1 % ; gain additionnel 0–2 % **[jugement]** | 2–3 h · 2–4 h | Trois variantes sur les mêmes plis et graines | Retirer les variables absolues si leur IC apparié est négatif en double aveugle, même si elles aident le pli spatial |

## Q10. Forêt et échéance nuisibles

**[jugement]** Une ablation n’est concluante ni à 1 % ni à un autre seuil arbitraire :
elle l’est si la différence appariée de carré d’erreur a un IC95 excluant zéro, le même
signe dans les trois plis spatiaux, et aucun renversement majeur dans les plis temporels.
Utiliser exactement les mêmes lignes et hyperparamètres.

Les graines ne testent quelque chose que si sous-échantillonnage de lignes, colonnes ou
algorithme stochastique est actif. Sinon, répéter la même graine ne mesure rien.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Forêt +1,0 %, échéance +0,5 % selon vos résultats ; réplication **Inconnu** | 2 h · 2–3 h | Prédictions OOF appariées, bootstrap par station, contrôle des plis temporels | Conserver la variable si l’IC contient zéro ou si un gain spatial devient une perte temporelle >0,5 % |

## Q11. Terrain plus interpolation

**[jugement]** Le mécanisme le plus probable est un double comptage du même signal
spatial : LightGBM utilise déjà coordonnées, relief et occupation du sol ; interpoler le
résidu CAMS avant ou à côté peut réinjecter une structure que l’apprenant corrige une
seconde fois. Autres possibilités à exclure : interpolation utilisant indirectement la
station test, lissage excessif et covariable calculée avec un voisinage différent entre
train et test.

Le test décisif est de kriger **le résidu OOF de LightGBM**, pas le résidu brut de CAMS,
avec la station cible totalement retirée. Si le variogramme du résidu ML n’a plus de
portée ou si le krigeage n’améliore pas le score externe, il ne reste pas de signal
spatial exploitable.

**[publié]** Riccio et Chianese améliorent au contraire CAMS avec un deuxième étage
spatio-temporel ; cela établit la possibilité d’une complémentarité, pas son universalité
([doi:10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024)). Une
publication rapportant précisément une *dégradation* terrain + krigeage dans votre
protocole est **Inconnu**.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| 0–2 % **[jugement]** ; actuellement négatif | 3–4 h · 1–2 h | Variogramme puis krigeage des seuls résidus ML OOF | Abandon immédiat si absence de structure au variogramme ou gain <0,5 % dans deux plis sur trois |

### Références publiées du bloc B

- Varma, S. et Simon, R. (2006), *BMC Bioinformatics*,
  [doi:10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91).
- Janssen, S. et al. (2012), *Atmospheric Environment*,
  [doi:10.1016/j.atmosenv.2012.05.028](https://doi.org/10.1016/j.atmosenv.2012.05.028).
- Riccio, A. et Chianese, E. (2024), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024).

# Bloc C — Les leviers de performance

## Q12. Observations récentes

**[jugement]** Ordre de test, non ordre publié :

1. biais roulant de la station sur les 72 dernières heures disponibles ;
2. observation de la veille à la même heure et moyenne des 24 dernières heures ;
3. dernière valeur disponible et âge de cette valeur ;
4. anomalie par rapport à une climatologie station×heure calculée dans le pli.

Le biais roulant corrige directement une dérive locale de CAMS ; le même horaire de la
veille porte le cycle diurne ; la dernière valeur seule décroît vite à J+1. **[publié]**
Bertrand et al. emploient observation de la veille et biais récent, mais ne publient pas
leur gain marginal isolé
([doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).

Construire deux modèles, pas une imputation : modèle A avec retards, entraîné aussi avec
des blocs de flux entièrement masqués et un indicateur d’âge ; modèle B sans aucune
observation. À l’inférence, router vers B si le flux manque. Ne jamais remplir une
absence future avec une observation postérieure à l’heure d’émission.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| 2–8 % **[jugement]** ; gain publié isolé **Inconnu** | 5–8 h · 3–5 h | Ajouter les quatre groupes séquentiellement sur un pli spatial et trois mois difficiles ; simuler 20 % de pannes par blocs | Abandonner un retard si gain <0,5 % ou si une panne simulée dégrade de >1 % le routeur A/B contre B seul |

## Q13. Copolluants

**Correction de prémisse. [jugement]** « sorties CAMS » peut déjà inclure les
copolluants ; il faut d’abord vérifier la matrice de 52 variables. Si O₃, NO₂, PM10 et
PM2.5 CAMS sont déjà présents, cette action est faite.

**[publié]** Bertrand et al. incluent la prévision CAMS du polluant cible et des trois
autres polluants dans leur jeu de base européen ; le gain isolé des copolluants est
**Inconnu**
([doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).

Utiliser NO et COV CAMS ne « corrèle » pas illicitement les cibles : ce sont des
prévisions disponibles à l’émission. La fuite apparaîtrait si des observations
contemporaines ou futures des autres polluants entraient dans les variables.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| 0–2 % **[jugement]** ; publié isolément **Inconnu** | 1 h si déjà téléchargé, 4–8 h sinon · 1–2 h | Ablation groupée cible seule vs cible+copolluants, mêmes plis | Ne pas télécharger de nouvelles espèces si les quatre polluants CAMS déjà présents apportent <0,5 % |

## Q14. Dispersion de l’ensemble CAMS

**[publié]** Riccio et Chianese utilisent la variance inter-membres dans un EMOS dont la
variance prédictive dépend de la dispersion de l’ensemble CAMS
([doi:10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024)).
La dispersion peut donc calibrer l’incertitude ; elle n’est pas garantie prédictive de
l’erreur instantanée. Même un ensemble parfait peut avoir une faible corrélation
spread–skill (Whitaker et Loughe, 1998, *Monthly Weather Review*,
[doi:10.1175/1520-0493(1998)126<3292:TRBESA>2.0.CO;2](https://doi.org/10.1175/1520-0493%281998%29126%3C3292:TRBESA%3E2.0.CO;2)).

Tester moyenne, écart-type, étendue et désaccord du membre médian, à l’heure et à la
maille. Le gain marginal de RMSE moyenne pour votre configuration est **Inconnu**.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| RMSE 0–1 % **[jugement]** ; calibration potentiellement plus utile | 4–10 h de données · 1–2 h | Corrélation OOF entre spread et erreur absolue, puis ablation LightGBM | Abandon RMSE si corrélation conditionnelle et gain sont tous deux <0,05 et <0,5 % ; conserver éventuellement pour les probabilités |

## Q15. Transformation de la cible

**Correction de prémisse. [jugement]** `log(1+y)` n’est pas défini pour un résidu pouvant
être inférieur à −1. Un décalage arbitraire rend la retransformation dépendante du minimum
d’entraînement et crée un biais. La racine pose le même problème de signe.

Compresser la cible risque en outre d’aggraver précisément la queue. Le test pertinent
n’est pas log/racine, mais Huber, pseudo-Huber ou transformation signée
`sign(y)·log(1+|y|)`, évaluée simultanément en global et sur décile haut.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| 0–2 % global ; queue possiblement négative **[jugement]** | 2 h · 2–3 h | Trois pertes/transformations, mêmes prédictions OOF et courbe de Pareto | Abandonner toute transformation qui n’améliore pas d’au moins 0,5 % le global **et** la queue, ou qui nécessite un décalage appris globalement |

## Q16. Multi-tâches et multi-horizons

**[publié]** Des réseaux multi-tâches existent pour prédire plusieurs polluants, mais les
études trouvées ne fournissent pas de seuil de volume de données ni de comparaison
CAMS/LightGBM sur stations exclues. Le bénéfice et le seuil sont **Inconnu**. Les études
de multi-tâches sur estimation spatiale ne sont pas des preuves pour votre prévision
horaire ; par exemple, le gain de phyMTDNN concerne la télédétection simultanée de
polluants (Yang et al., 2023, *Science of the Total Environment*,
[doi:10.1016/j.scitotenv.2022.159542](https://doi.org/10.1016/j.scitotenv.2022.159542)).

**[jugement]** Avec LightGBM, un modèle commun n’apprend pas naturellement une
représentation partagée sans encoder polluant/horizon et homogénéiser les cibles. Cela
ajoute un risque élevé pour peu de valeur de candidature.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| **Inconnu** | 8–16 h · 6–12 h | Petit modèle commun sur O₃ J+1–J+3 seulement, un pli | Ne pas lancer sauf si un prototype existant bat de ≥1 % chacun des trois modèles séparés ; sinon abandon immédiat |

## Q17. Hyperparamètres

**[publié]** Aucun gain « typique » transférable n’est publié pour votre tâche :
**Inconnu**. Bertrand et al. utilisent des grilles limitées et montrent que le choix
d’algorithme dépend de la cible, sans isoler la valeur du tuning
([doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).

**[jugement]** Les paramètres porteurs sont : capacité (`num_leaves` avec
`max_depth`) ; régularisation locale (`min_data_in_leaf`) ; trajectoire
`learning_rate × n_estimators` avec early stopping. En second rang seulement :
`feature_fraction`, `bagging_fraction` et `lambda_l2`. Faire 25–30 essais bayésiens,
pas une grille cartésienne.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| 0–3 % **[jugement]** ; publié **Inconnu** | 3–4 h · 3–6 h | 30 essais sur un pli interne spatial, confirmation inchangée sur les trois plis externes | Arrêter si les 10 derniers essais n’améliorent pas de 0,1 % ou si le gagnant interne ajoute <0,5 % externe |

## Q18. Continuer les architectures ?

**[jugement]** Non. Vous avez déjà la réponse utile : la famille boosting domine le
linéaire et la forêt, tandis que LightGBM, XGBoost et CatBoost sont séparés d’environ
0,32 µg/m³. Finir une exécution RealMLP/TabM déjà engagée est acceptable ; ouvrir une
nouvelle campagne d’architectures ne l’est pas.

**[publié]** À Stockholm, la performance varie davantage avec polluant et site qu’avec
RF, XGBoost ou LSTM (Zhang et al., 2024,
[doi:10.5194/acp-24-807-2024](https://doi.org/10.5194/acp-24-807-2024)). Cela soutient
la décision, sans prédire votre classement exact.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| ≤0,3 µg/m³ **[jugement]**, probablement moindre après validation appariée | 1 h d’analyse · au plus une exécution <8 h | Un seul pli double aveugle pour le meilleur réseau déjà prêt | Arrêt si gain <0,3 µg/m³, si queue/CSI baisse, ou si préparation dépasse 2 h |

### Références publiées du bloc C

- Bertrand, J.-M. et al. (2023), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).
- Riccio, A. et Chianese, E. (2024), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024).
- Whitaker, J. S. et Loughe, A. F. (1998), *Monthly Weather Review*,
  [doi:10.1175/1520-0493(1998)126<3292:TRBESA>2.0.CO;2](https://doi.org/10.1175/1520-0493%281998%29126%3C3292:TRBESA%3E2.0.CO;2).
- Zhang, Z. et al. (2024), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-24-807-2024](https://doi.org/10.5194/acp-24-807-2024).
- Yang, Q. et al. (2023), *Science of the Total Environment*,
  [doi:10.1016/j.scitotenv.2022.159542](https://doi.org/10.1016/j.scitotenv.2022.159542).

# Bloc D — Les extrêmes, qui décident du service rendu

## Q19. Attribuer l’échec sur le décile supérieur

**[jugement]** Le responsable principal est déjà partiellement identifié :
**perte quadratique × déséquilibre**, puisque la pondération inverse le signe du gain sur
la queue. L’écrêtage à zéro ne peut affecter directement une prédiction haute que si la
prédiction non écrêtée est négative, cas à compter mais vraisemblablement marginal dans
le décile supérieur observé.

La cible résiduelle est secondaire : sous perte quadratique, prédire le résidu et ajouter
CAMS optimise exactement la même erreur finale avant écrêtage, même si la classe de
fonctions d’un arbre peut rendre la cible directe plus facile ou plus difficile.

**[publié]** Petetin et al. attribuent l’écrasement des forts O₃ au faible poids des
événements rares dans l’objectif, malgré de bons scores continus
([doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022)).
Zhen et al. documentent explicitement le déséquilibre comme cause de sous-estimation
(2025, *Atmospheric Environment*,
[doi:10.1016/j.atmosenv.2024.120952](https://doi.org/10.1016/j.atmosenv.2024.120952)).

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Attribution ; gain 0–3 % **[jugement]** | 3 h · 3–4 h | Plan 2×2 : résidu/direct × MSE/pondérée, plus score avant/après écrêtage | Innocenter une cause si la changer modifie la queue de <0,5 % à perte et échantillon identiques |

## Q20. Classification calibrée du dépassement

**[publié]** La classification directe d’un dépassement O₃ est publiée, mais les gains
POD/FAR/CSI comparables à votre CAMS, France, stations exclues sont **Inconnu**
(Gómez-Losada, 2018, *Atmospheric Pollution Research*,
[doi:10.1016/j.apr.2018.04.002](https://doi.org/10.1016/j.apr.2018.04.002)).
Les prévisions probabilistes permettent de choisir un seuil de décision selon le coût,
au lieu d’imposer 0,5 (Pagowski et Grell, 2006, *JGR*,
[doi:10.1029/2006JD007124](https://doi.org/10.1029/2006JD007124)).

Calibrer sur des prédictions internes spatialement exclues : régression logistique
sigmoïde si les événements sont rares ; isotonic seulement si chaque pli contient assez
d’événements. Mesurer Brier score, diagramme de fiabilité, POD/FAR/CSI sur le pli externe.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| CSI +0,02 à +0,08 **[jugement]** ; publié comparable **Inconnu** | 4–6 h · 2–3 h | LightGBM binaire + calibration sigmoïde OOF, mêmes seuils réglementaires | Abandon si Brier skill ≤0 contre fréquence climatologique ou si aucun seuil n’améliore CSI sans perdre >0,05 de POD |

## Q21. Dominer le compromis global–queue

**[jugement]** Aucune formulation ne garantit de dominer le front de Pareto. Le test le
moins cher est un mélange convexe de vos deux prédictions déjà calculées :
`ŷ = (1−w)ŷ_MSE + wŷ_pondérée`, avec `w` choisi dans un pli interne. Ensuite seulement,
tester une tête moyenne plus plusieurs quantiles avec perte composite.

**[publié]** Li et al. utilisent une perte pondérée pour l’O₃ horaire à 24–96 h, mais ne
publient pas le gain incrémental de la pondération seule
([doi:10.1016/j.atmosenv.2024.120865](https://doi.org/10.1016/j.atmosenv.2024.120865)).
Un modèle publié dominant simultanément votre RMSE globale et votre décile haut est
**Inconnu**.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| 0–2 % sur une métrique sans perte sur l’autre **[jugement]** | 1–2 h · nul pour le mélange | Balayer `w` sur prédictions OOF internes, évaluer une frontière externe | Abandonner l’architecture à deux têtes si aucun mélange simple ne domine déjà un des deux modèles avec une marge ≥0,5 % |

## Q22. Arbitrage alerte manquée–fausse alerte

**[publié]** Pour une probabilité calibrée, le seuil de décision optimal égale le rapport
coût de l’action/perte évitée dans le modèle coût–perte. Pagowski et Grell montrent que
le seuil optimal varie avec l’utilisateur ; ils ne définissent pas un coût AASQA unique
([doi:10.1029/2006JD007124](https://doi.org/10.1029/2006JD007124)).

**[jugement]** Une règle publique donnant un coût relatif officiel pour une alerte ATMO
française est **Inconnu**. Ne choisissez donc pas un point arbitraire : livrez la courbe
POD–FAR, CSI et valeur pour plusieurs rapports coût–perte, puis dites que le point
opérationnel appartient à l’autorité qui déclenche.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Pas de gain intrinsèque ; décision mieux alignée | 2–3 h · nul | Courbes pour tous les seuils de probabilité, bootstrap station | Ne publier aucun seuil « optimal » si le coût–perte n’est pas fourni ou si sa valeur change fortement entre plis |

## Q23. Pourquoi PM2.5 améliore POD et FAR

**[jugement]** Les trois tableaux ne démontrent aucune cause physique. Les explications
possibles sont une fréquence d’événement plus favorable, un biais CAMS plus monotone, une
distribution moins dominée par la chimie locale instantanée, ou simplement un seuil mieux
placé. Il faut d’abord comparer taux de base, histogrammes conditionnels et courbes
fiabilité/résolution.

**[publié]** Les performances catégorielles changent fortement avec polluant, seuil et
agrégation ; Bertrand et al. obtiennent pour PM10 un comportement différent de l’O₃ dans
le même dispositif
([doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).
Cela ne prouve pas l’explication de votre PM2.5.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Diagnostic ; gain **Inconnu** | 2–3 h · <1 h | Mettre les trois polluants à taux de base commun par sous-échantillonnage et comparer courbes ROC/PR et calibration | Abandonner l’explication « physique PM2.5 » si l’avantage disparaît après égalisation du taux de base |

### Références publiées du bloc D

- Petetin, H. et al. (2022), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).
- Zhen, L. et al. (2025), *Atmospheric Environment*,
  [doi:10.1016/j.atmosenv.2024.120952](https://doi.org/10.1016/j.atmosenv.2024.120952).
- Gómez-Losada, Á. (2018), *Atmospheric Pollution Research*,
  [doi:10.1016/j.apr.2018.04.002](https://doi.org/10.1016/j.apr.2018.04.002).
- Pagowski, M. et Grell, G. A. (2006), *Journal of Geophysical Research*,
  [doi:10.1029/2006JD007124](https://doi.org/10.1029/2006JD007124).
- Li, Q. et al. (2024), *Atmospheric Environment*,
  [doi:10.1016/j.atmosenv.2024.120865](https://doi.org/10.1016/j.atmosenv.2024.120865).
- Bertrand, J.-M. et al. (2023), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

# Bloc E — Protocole : ne pas se tromper sur ce qu’on mesure

## Q24. Non-stationnarité, volume et nombre de plis

**[jugement]** Faire trois comparaisons emboîtées :

1. **Effet volume :** évaluer 7 et 17 mois d’apprentissage sur les *mêmes sept mois de
   test* et les mêmes stations.
2. **Effet nombre de plis :** tirer plusieurs milliers de sous-ensembles de 7 plis parmi
   les 18 et comparer la distribution de leur minimum au minimum observé sur 7 plis.
3. **Non-stationnarité :** sur les 18 plis fixes, régresser la différence appariée
   d’erreur sur tendance, saison et indicateurs de rupture CAMS ; comparer aussi les
   mêmes mois d’une année à l’autre.

Le pire pli devient mécaniquement plus mauvais quand on augmente le nombre de plis ; seul
le deuxième calcul quantifie cet effet sans le confondre avec le modèle.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Aucun gain direct ; validité centrale | 4–6 h · 2–4 h si prédictions à refaire | Échantillonnage des minima + évaluation commune 7/17 mois | Abandonner l’explication « plus de données » si, à test commun, 17 mois n’améliorent pas la moyenne ; abandonner « nombre de plis » si −14,6 % tombe hors de l’IC95 des minima de 7 plis |

## Q25. Dégradation de CAMS fin 2024

**[jugement]** Calculer par station×jour l’erreur absolue de CAMS, celle du corrigé et
leur différence. Faire une étude d’événement autour des deux dates, avec fenêtres
pré-définies, puis une différence-de-différences contre les mêmes mois de 2023. La
question décisive est : votre RMSE corrigée reste-t-elle stable pendant que CAMS se
dégrade, ou se dégrade-t-elle aussi mais moins ?

Si elle reste stable, présenter le résultat comme **robustesse à une rupture amont**. Si
elle se dégrade aussi, rapporter séparément période normale et période perturbée, puis
leur moyenne pondérée. Ne jamais supprimer les dates.

**[publié]** Bertrand et al. insistent sur les mises à jour fréquentes de CAMS et sur
l’intérêt d’un MOS court pour s’y adapter
([doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).
Les deux dates précises sont ici des données fournies par le projet, non revérifiées dans
cette réponse.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Aucun gain ; attribution de 0 à une part **Inconnue** du gain observé | 3–4 h · <1 h | Étude d’événement et contrôle saison 2023, IC par station | Ne pas revendiquer la robustesse si la RMSE corrigée augmente de façon comparable à CAMS ou si l’effet précède les ruptures |

## Q26. Optimisme accumulé

**[publié]** Réutiliser une validation pour choisir prétraitements, variables et modèles
optimise le bruit de cette validation. Varma et Simon montrent sur données simulées que
l’estimation d’erreur après optimisation sur la même CV est biaisée et que la CV
imbriquée réduit fortement ce biais
([doi:10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91)).

**[jugement]** Il est trop tard pour rendre « intouchées » des données dont les scores ont
déjà orienté les choix. Geler maintenant le pipeline, réserver une dernière évaluation
station×mois qui ne servira plus à aucune décision, et effectuer le tuning uniquement
dans des plis internes. Documenter explicitement que le test final est un *lockbox
prospectif à partir de maintenant*, pas un test historiquement vierge.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Performance affichée possiblement −1 à −5 % **[jugement]**, crédibilité accrue | 2 h de gel · 4–8 h pour audit final | Une seule exécution finale après signature d’un manifeste de pipeline | Si le lockbox a déjà été consulté pour modifier le modèle, cesser de l’appeler test et rapporter une CV imbriquée |

## Q27. Puissance des comparaisons

**[jugement]** Trois plis spatiaux ne permettent pas d’estimer correctement une variance
par un simple t-test sur trois valeurs. Dix-huit plis temporels ne sont pas dix-huit
réplications indépendantes. Comparer les modèles sur les **mêmes observations** avec un
bootstrap apparié à deux niveaux : stations rééchantillonnées, puis blocs temporels
contigus de sept jours à l’intérieur des stations.

Un écart de 0,3 µg/m³ peut être réel, mais sa taille brute ne suffit pas. Déclarer égalité
pratique si l’IC95 de la différence inclut zéro ou si le signe n’est pas cohérent dans au
moins deux plis spatiaux et une majorité des mois.

**[publié]** Une CV aléatoire peut fortement sous-estimer l’erreur spatiale : Just et al.
rapportent 2,10 contre 3,11 µg/m³ pour PM2.5 selon partage aléatoire ou spatial
(2020, *Atmospheric Environment*,
[doi:10.1016/j.atmosenv.2020.117649](https://doi.org/10.1016/j.atmosenv.2020.117649)).
Cela justifie le blocage, pas un seuil de puissance universel.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Aucun gain ; décision LightGBM/XGB/CatBoost | 3–4 h · 1–2 h | 1 000 bootstraps appariés station + blocs de 7 jours sur prédictions déjà produites | Déclarer les modèles ex æquo si IC95 contient zéro ou si l’avantage relatif est <0,5 % |

### Références publiées du bloc E

- Bertrand, J.-M. et al. (2023), *Atmospheric Chemistry and Physics*,
  [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).
- Varma, S. et Simon, R. (2006), *BMC Bioinformatics*,
  [doi:10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91).
- Just, A. C. et al. (2020), *Atmospheric Environment*,
  [doi:10.1016/j.atmosenv.2020.117649](https://doi.org/10.1016/j.atmosenv.2020.117649).

# Bloc F — Discriminer : que faire, et que ne pas faire

## Q28. Classement unique des actions

**[jugement]** Le tableau attribue chaque action à une seule catégorie.

| Action | Catégorie | Gain attendu | Coût travail · calcul | Test tueur | Abandon |
|---|---|---:|---:|---|---|
| Décomposition mois×décile et ruptures CAMS | **À faire** | Diagnostic | 4 h · <1 h | Carte OOF + étude d’événement | Pas de motif stable entre plis |
| Observations récentes + vrai modèle de repli | **À faire** | 2–8 % | 5–8 h · 3–5 h | Un pli spatial + trois mois difficiles + pannes simulées | <1 % ou repli dégradé >1 % |
| Tuning LightGBM limité | **À faire** | 0–3 % | 3–4 h · 3–6 h | 30 essais puis confirmation externe | <0,5 % externe |
| Classification calibrée des seuils | **À faire** | CSI +0,02 à +0,08 | 4–6 h · 2–3 h | Brier skill et courbe POD–FAR externe | Brier skill ≤0 ou aucun seuil utile |
| Gel du pipeline et dernier lockbox | **À faire** | Crédibilité | 2 h · 4–8 h | Une seule exécution signée | Toute consultation suivie d’une modification |
| Ablations forêt et échéance | **À faire** | Jusqu’à 1,0 % | 2 h · 2–3 h | IC apparié station | IC contient zéro ou instabilité temporelle |
| Cible journalière O₃ max 8 h | **À tester d’abord par test tueur** | 0–12 points de gain relatif | 3 h · 2–3 h | Un seul pli, cible directe | <3 points |
| Plancher par paires de stations | **À tester d’abord par test tueur** | Diagnostic | 4–6 h · <1 h | Courbe variance–distance | Trop peu de paires ou IC instable |
| Second modèle de résidu | **À tester d’abord par test tueur** | 0–1 % | 3–4 h · 2–4 h | Résidus strictement OOF | <0,5 % dans deux plis |
| Calendrier cyclique contre calendrier absolu | **À tester d’abord par test tueur** | 0–2 % | 2–3 h · 2–4 h | Double aveugle | Perte ou changement de signe |
| Krigeage du résidu ML OOF | **À tester d’abord par test tueur** | 0–2 % | 3–4 h · 1–2 h | Variogramme résiduel | Aucune portée ou <0,5 % |
| Copolluants CAMS supplémentaires | **À tester d’abord par test tueur** | 0–2 % | 1–8 h · 1–2 h | Ablation groupée | <0,5 % |
| Dispersion inter-membres CAMS | **À tester d’abord par test tueur** | RMSE 0–1 % | 4–10 h · 1–2 h | Spread–skill puis ablation | Corrélation <0,05 et gain <0,5 % |
| Mélange MSE–pondéré | **À tester d’abord par test tueur** | 0–2 % | 1–2 h · nul | Balayage convexe OOF | Aucun point dominant |
| Transformation signée/Huber | **À tester d’abord par test tueur** | 0–2 % | 2 h · 2–3 h | Global + décile haut | N’améliore pas les deux |
| Continuer RealMLP/TabM/GNN | **À ne pas faire** | **Inconnu**, probablement faible | >8 h · jusqu’à 1 jour | Déjà répondu par trois boostings proches | Arrêt maintenant, sauf run déjà prêt |
| Recherche exhaustive d’hyperparamètres | **À ne pas faire** | **Inconnu** | >1 jour | Le test limité de 30 essais suffit | Toute absence de plateau n’autorise pas une seconde nuit |
| `log(1+résidu)` ou racine brute | **À ne pas faire** | Probablement négatif sur queue | 2 h · 2 h | Domaine mathématique invalide | Résidu <−1 |
| Modèle multi-tâches/multi-polluants profond | **À ne pas faire** | **Inconnu** | 8–16 h · 6–12 h | Aucun repère comparable, délai court | Ne pas lancer |
| Empilement actuel terrain + résidu CAMS interpolé | **À ne pas faire** | −3,7 % environ d’après vos RMSE | nul | Résultat déjà obtenu | Remplacer uniquement par test résidu ML |
| Exclure les stations difficiles après examen | **À ne pas faire** | Score artificiellement meilleur | nul | Analyse stratifiée suffit | Toute règle écrite après lecture des erreurs |

## Q29. Critère d’arrêt

**[jugement]** Geler le modèle dès que les trois actions « observations récentes »,
« tuning limité » et « classification calibrée » ont reçu leur test tueur, puis appliquer
une règle unique :

> Aucun calcul supplémentaire si le meilleur candidat restant n’a pas démontré, sur
> prédictions appariées hors station et hors mois, une baisse d’au moins **0,3 µg/m³**
> avec borne basse de l’IC95 au-dessus de zéro, **sans** dégrader le RMSE du décile haut de
> plus de 0,3 µg/m³ ni le CSI principal.

Le seuil de 0,3 est un choix de praticien lié à votre candidature et à l’écart déjà
observé entre bibliothèques, pas un standard publié. Arrêt impératif aussi lorsque dix
jours ouvrés restent avant le 22 août : ils appartiennent au récit, aux figures et à la
répétabilité.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Évite des gains marginaux non défendables | 1 h · nul | Appliquer la règle au backlog avant tout lancement | Tout candidat sous 0,3 µg/m³, IC non concluant ou métrique de service dégradée est arrêté |

## Q30. La question déterminante et la question omise

**[jugement]** Je garderais **Q24**. La chute jusqu’à −24,9 % en double aveugle peut
transformer le projet de « correcteur généralisable » en « correcteur de la période
apprise ». Distinguer volume, nombre de plis et non-stationnarité décide de la formulation
honnête de toute la candidature.

La question essentielle omise est :

> **À quelle heure exacte le produit est-il émis, pour quelle décision identifiée, et
> quelles variables sont réellement disponibles et garanties à cet instant ?**

Elle fixe simultanément la légalité des observations récentes, l’horizon utile, le coût
relatif POD/FAR, le plan de repli et la métrique principale. Sans utilisateur et heure
d’émission, une amélioration de RMSE peut rester un exercice rétrospectif.

| Gain attendu | Coût travail · calcul | Test de falsification | Critère d’abandon |
|---|---|---|---|
| Pas de gain RMSE ; valeur opérationnelle décisive | 2–4 h d’entretien/documentation · nul | Écrire une fiche d’une page « émission–entrées–décision–repli–SLA » | Si aucune décision ou heure d’émission ne peut être nommée, présenter le travail comme démonstrateur méthodologique, pas prototype opérationnel |

# Points classés Inconnu

- Plancher irréductible horaire en µg/m³ pour O₃ et NO₂, France, maille CAMS de 8 km.
- Décomposition additive indépendante entre mesure, représentativité et variabilité
  sous-maille.
- Fraction théorique universelle de l’erreur d’un CTM corrigeable en aval.
- Seuils de R² « moyen », « bon » et « suspect » sur stations exclues.
- Gain marginal isolé des observations récentes dans un protocole spatialement exclu.
- Part des dix points expliquée par période, géographie, densité et version CAMS.
- Publication montrant précisément une dégradation terrain + krigeage comparable.
- Gain isolé des copolluants CAMS pour l’O₃ dans votre protocole.
- Gain RMSE isolé de la dispersion inter-membres CAMS.
- Seuil de volume à partir duquel multi-tâches ou multi-horizons devient meilleur.
- Gain typique du tuning LightGBM pour ce problème.
- Gain POD/FAR/CSI d’une classification calibrée directement comparable.
- Formulation publiée garantissant de dominer le compromis RMSE globale–queue.
- Coût relatif officiel français d’une alerte manquée contre une fausse alerte AASQA.
- Cause physique de l’avantage PM2.5 à partir des seules tables de contingence.
- Optimisme numérique accumulé par les choix déjà effectués.
- Puissance exacte des 18 plis temporels et trois plis spatiaux sans covariance
  empirique des prédictions.
