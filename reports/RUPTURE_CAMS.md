# Une rupture dans CAMS vers octobre 2024

## Pourquoi cette vérification a été faite

Avant de lancer une validation inter-annuelle — entraîner sur une année, tester sur la
suivante — il fallait s'assurer que le **modèle amont n'avait pas changé** entre les deux.
Sinon l'expérience confondrait « année nouvelle » et « système différent », et son
résultat serait ininterprétable.

Les métadonnées ne portent pas de numéro de version : mêmes attributs, même grille
110 × 150, même producteur entre août 2023 et juin 2025. La question se tranche donc
**empiriquement** — si le système a changé, son erreur propre contre les observations
doit montrer une discontinuité.

## Le résultat

Erreur de CAMS brut contre les observations, mois par mois, ozone J+1, ~190 000 paires
par mois :

| Période | RMSE | Biais | R² |
|---|---|---|---|
| 2023-08 → 2024-09 (14 mois) | 14,45 – 18,60 | **+3,15 à +8,18** | **0,396 – 0,630** |
| **2024-10 → 2024-12** | 19,11 – 20,41 | **+9,45 à +12,43** | **0,187 – 0,311** |

**La comparaison entre mois homologues lève l'ambiguïté saisonnière :**

| Mois | 2023 | 2024 |
|---|---|---|
| Octobre | biais +8,18 · R² 0,452 | biais **+11,53** · R² **0,191** |
| Novembre | biais +4,47 · R² 0,493 | biais **+12,43** · R² **0,187** |
| Décembre | biais +5,80 · R² 0,496 | biais **+9,45** · R² 0,311 |

Novembre 2024 est **trois fois plus biaisé** que novembre 2023, avec un R² divisé par
2,6. Ce n'est pas la saison.

## Ce que cela implique

**Une cause reste à identifier — et la plus évidente a été écartée.** La documentation
ECMWF donne bien un changement dans le bon mois : mise à niveau **U9** le 13 novembre
2024, cycle global **cy49r1** la veille. J'ai d'abord conclu que c'était l'explication.

**Un détecteur journalier l'a démentie** (voir `DERIVE_CAMS.md`) : le déplacement est daté
du **24 octobre 2024** sur l'ozone, et entre le 24 octobre et le 4 novembre sur les trois
polluants — **huit à dix-neuf jours avant la bascule**. Les moyennes mensuelles de ce
rapport ne pouvaient pas faire cette distinction ; c'est précisément pourquoi elles ne
suffisaient pas à conclure.

Restent en concurrence : une évolution non documentée en amont, une modification du
réseau d'observation, ou un régime météorologique particulier à l'automne 2024. Les
discriminants calculés dans `DERIVE_CAMS.md` — concordance spatiale, et déplacement
comparé de l'observation et de la prévision d'une année sur l'autre — orientent la
réponse sans la trancher. **La cause n'est pas établie.**

**Pour l'évaluation, la conséquence est immédiate.** Une validation « train 2023-24 /
test 2024-25 » ne mesurerait pas la généralisation temporelle mais la **robustesse à un
changement de système amont**. Ce sont deux propriétés distinctes, et toutes deux
intéressantes — à condition de ne pas les confondre.

C'est d'ailleurs le test le plus exigeant que ce projet puisse mener : si la correction
tient malgré une dérive du modèle qu'elle corrige, elle a une valeur opérationnelle
réelle. Si elle ne tient pas, la limite doit être connue **avant** qu'un utilisateur la
découvre.

## Ce que cela apprend au passage

Une correction apprise dépend d'un modèle amont qui **évolue sans préavis**. C'est un
argument pour le **réentraînement glissant** plutôt que pour un modèle figé — et un
argument de plus en faveur d'un indicateur de dérive : comparer en continu l'erreur du
modèle amont à sa distribution historique signalerait ce genre de rupture au moment où
elle se produit, pas dix mois plus tard.

Cet indicateur a été construit depuis : `DERIVE_CAMS.md`. Il a fait deux choses que ce
rapport-ci ne pouvait pas faire — **dater** le déplacement au jour près, et **réfuter**
l'attribution à U9 que ce rapport avait acceptée.

La leçon vaut plus que le résultat : **une mesure agrégée au mois ne peut pas établir une
cause datée au jour.** Trouver un événement documenté dans le bon mois n'est pas une
preuve, c'est une coïncidence de granularité.

## Limite de l'archive

Les observations métropolitaines s'arrêtent au **1er janvier 2025**. Les prévisions CAMS
téléchargées pour 2025 sont donc inexploitables faute de référence. La fenêtre
réellement utilisable est **2023-08 → 2024-12**, soit 17 mois.
