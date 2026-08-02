# Prompt GPT — R15 · Élever la qualité du travail, pas le score

> À coller tel quel. Rédigé le 02/08/2026, après R14 qui a révélé qu'une **offre réelle**
> de data scientist junior est ouverte chez Atmo Occitanie, clôture le 22 août 2026, pôle
> Partenariats, avec « modèles simples » explicitement demandé.
>
> Les prompts précédents cherchaient des gains. Celui-ci cherche de la **qualité** : ce qui
> rend un travail reprenable, auditable et défendable par quelqu'un d'autre que son auteur.

---

## Où en est le travail

Post-traitement statistique des prévisions **CAMS Europe** à J+1 sur 476 stations
françaises, corpus de 36 mois, cible journalière, LightGBM sur le résidu `observation − CAMS`.

Évaluation avec station **et** mois cachés simultanément. Résultats du 02/08/2026 :

| variante | NO₂ | PM10 |
|---|---|---|
| base | +27,80 % | +11,36 % |
| + typologie de station | +36,64 % | +13,28 % |
| **+ observations antérieures (J−2)** | **+41,87 %** | **+22,08 %** |

L'écart-type entre plis tombe de 4,8 à **2,7** sur NO₂, avec zéro pli négatif.

En **détection** de dépassement, en revanche, rien n'est démontré sur cet axe : ×1,18 sur
PM10 à 50 µg/m³, intervalle de confiance contenant zéro.

---

## Question 1 — Les observations antérieures : légitimes, et à quel décalage ?

**Le fait.** Le levier le plus fort du projet est un jeu de variables construites à partir
des **mesures passées de la station elle-même** : observation décalée, erreur de CAMS
décalée, moyennes glissantes sur 3 et 7 jours, écart-type de l'erreur sur 7 jours, et un
indicateur de **fraîcheur** (nombre de jours depuis la dernière mesure valide).

Le décalage retenu est **2 jours**, par prudence : la prévision couvrant le jour J est
émise en J−1, donc rien de plus récent que la fin de J−2 n'est réputé disponible.

**Ce que je demande.**

1. Est-ce la **pratique standard** en post-traitement de prévision de qualité de l'air ?
   Comment ces variables sont-elles nommées et construites dans la littérature — persistance,
   analogues, biais récent, correction adaptative de biais ?
2. Le décalage de **2 jours est-il trop prudent** ? En opérationnel réel, à quelle heure les
   mesures d'une station sont-elles effectivement validées et disponibles ? Y a-t-il une
   distinction entre données brutes rapatriées et données validées ? Quel décalage utilisent
   les systèmes opérationnels publiés ?
3. Quels **risques** cette famille introduit-elle qu'un gain hors échantillon ne révèle
   pas : dépendance à la disponibilité du réseau, dégradation en cas de panne de station,
   effet de persistance qui rate précisément les ruptures — c'est-à-dire les épisodes ?
4. Comment **évaluer honnêtement** un modèle qui utilise le passé de la station, sachant
   qu'il n'est déployable qu'aux stations instrumentées ? Faut-il publier deux systèmes
   distincts, ou un système avec dégradation gracieuse ?
5. Existe-t-il des travaux mesurant **ce que la persistance seule** rapporte, pour savoir
   quelle part de mes +14 points n'est que de la persistance déguisée ?

## Question 2 — Reproduire exactement un protocole d'évaluation officiel

**Le contexte.** Le référentiel technique national du LCSQA, applicable depuis le
1ᵉʳ janvier 2022, définit comment une AASQA évalue sa prévision : bilan annuel, 75 % de
couples modèle-observation minimum, scores continus par station puis synthétisés, tables de
contingence avec POD, FAR, SR, biais de fréquence et CSI, ozone en maximum horaire
journalier d'avril à septembre à 180 µg/m³, PM10 en moyenne journalière à 50 µg/m³.

Je veux que mon banc d'évaluation **reproduise ce protocole exactement**, pour que mes
chiffres soient lisibles par un praticien sans traduction.

**Ce que je demande.**

1. Le détail complet de ce référentiel : quelles métriques, quelles agrégations, quelles
   règles de validité, quels seuils, quels horizons, quelle présentation attendue ?
2. Comment traite-t-il les **données manquantes ou invalidées** ? La règle des 75 % porte
   sur quoi exactement — l'année, la station, le couple ?
3. Le cadre **FAIRMODE** de prévision et son indicateur `MQI_f` : quelle est la formule
   exacte applicable en 2026, quels paramètres d'incertitude, et comment se calcule la
   persistance de référence selon l'horizon ?
4. Quelle est la **présentation graphique** canonique — diagramme cible, diagramme de
   Taylor, tables de contingence, séries temporelles ? Que reconnaît immédiatement un
   praticien du domaine ?
5. Y a-t-il des **implémentations de référence ouvertes** — Delta Tool de FAIRMODE, scripts
   R ou Python publiés — que je puisse utiliser plutôt que réécrire ?

## Question 3 — Quantifier l'incertitude, proprement

**Le fait.** Mon système rend une valeur ponctuelle. Une AASQA publie désormais un
intervalle de confiance de 10 à 20 % selon le polluant sur ses indicateurs d'exposition. Je
n'ai aucune quantification d'incertitude par prédiction.

**Ce que je demande.**

1. Quelles méthodes produisent un **intervalle de prédiction** valide pour un modèle à
   gradient boosté, sous **décalage de distribution** — prédiction conforme, conforme
   pondérée, Mondrian ou par groupe, Venn-Abers, régression quantile ? Laquelle conserve sa
   garantie quand la station de test est inconnue ?
2. La **garantie de couverture** de la prédiction conforme suppose l'échangeabilité. Elle
   est violée quand on cache une station et un mois. Quelles variantes traitent ce cas, et
   quelle couverture réelle observe-t-on en pratique ?
3. Comment **valider empiriquement** un intervalle : couverture par station, par mois, par
   décile de concentration ? Quelle est la bonne façon de montrer qu'un intervalle est
   honnête plutôt que simplement large ?
4. Pour un usage d'alerte, vaut-il mieux un **intervalle** ou une **probabilité de
   dépassement** ? Les deux sont-ils dérivables l'un de l'autre sans perte ?
5. Quel est le **coût** de ces méthodes — calcul, données de calibration, complexité de
   maintenance ? Une AASQA avec 56 salariés peut-elle raisonnablement en maintenir une ?

## Question 4 — Ce qui rend un dépôt de code reprenable

**Le contexte.** L'offre demande explicitement qualité, sécurité et gouvernance des
données, et le travail en binôme. Mon dépôt est propre mais personnel : il n'a jamais été
repris par quelqu'un d'autre.

**Ce que je demande.**

1. Qu'est-ce qui distingue, concrètement, un dépôt **reprenable** d'un dépôt simplement
   propre ? Je cherche une liste de contrôle, pas des principes.
2. Quelles pratiques sont **réellement attendues** dans une structure de cette taille —
   tests, intégration continue, versionnement des données, journal d'expériences, fiche de
   modèle, dictionnaire de données, gestion des secrets ? Lesquelles sont du luxe ?
3. Comment documenter un **pipeline de données** pour qu'un tiers puisse le rejouer :
   provenance, versions des sources, contrôles de qualité, gestion des ruptures de flux ?
4. Qu'est-ce qu'une **fiche de modèle** (model card) utile en qualité de l'air — quelles
   rubriques, quel niveau de détail, quels exemples publiés ?
5. Y a-t-il des **normes ou recommandations** applicables — FAIR pour les données, bonnes
   pratiques de recherche reproductible, exigences de traçabilité de la directive ?

## Question 5 — La dérive, et comment la surveiller

**Le fait non résolu.** Le projet a détecté une **rupture dans les prévisions CAMS en
octobre 2024** qui ne correspond pas à la date officielle de changement de version
(13 novembre 2024). Elle reste inexpliquée. Et le corpus couvre trois ans, pendant lesquels
la chaîne amont a changé plusieurs fois.

**Ce que je demande.**

1. Comment un système de post-traitement doit-il **traiter les changements de version** du
   modèle amont ? Réentraînement, fenêtre glissante, variable indicatrice de version,
   détection automatique de rupture ?
2. Quelles **méthodes de détection de rupture** sont adaptées à des séries de résidus
   multi-stations — tests de rupture structurelle, cartes de contrôle, tests séquentiels ?
   Lesquelles ont été appliquées à la qualité de l'air ?
3. Comment distinguer une **rupture du modèle amont** d'un changement réel de
   l'atmosphère ou du réseau de mesure ? Quels témoins utiliser ?
4. Quelle **cadence de réentraînement** est raisonnable, et sur quelle preuve la fixer
   plutôt que sur une habitude ?
5. Existe-t-il un **journal public des versions de CAMS** régional suffisamment détaillé
   pour aligner un corpus dessus ? Où le trouver et à quelle granularité ?

---

## Contraintes de réponse

- **Cite tes sources.** Article, rapport, documentation officielle, année, lien.
- **Sur la question 2, je veux du concret** : formules, seuils, règles. Un résumé de
  principes ne me permettra pas d'implémenter.
- **Distingue** ce qui est établi, ce qui est pratique courante, et ce que tu extrapoles.
- **Dis-moi ce qui est du luxe.** Il reste vingt jours ; une liste de bonnes pratiques
  irréalisable m'est moins utile qu'un sous-ensemble hiérarchisé.
- **Sois franc sur la question 1.5.** Si une grande part de mes +14 points n'est que de la
  persistance, je dois le savoir avant de l'écrire dans un dossier.
- Réponds en français, avec la terminologie du métier.
