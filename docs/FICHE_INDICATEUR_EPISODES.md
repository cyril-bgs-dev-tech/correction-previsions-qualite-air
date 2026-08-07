# Fiche indicateur — Rappel des dépassements à qualité d'annonce fixée

| | |
|---|---|
| **Code** | `RAPPEL_BUDGET_FA` |
| **Version** | 1.0 — 06/08/2026 |
| **Statut** | mesuré sur corpus historique · **non déployé en exploitation** |
| **Fréquence proposée** | mensuelle, consolidation annuelle |
| **Source unique des valeurs** | `reports/VERITE_DOSSIER.md` § 8 · régénérable par `python3 scripts/verite_dossier.py` |

---

## 1. La question métier

> *À qualité d'annonce donnée — celle que le réseau accepte de tenir — combien de
> dépassements réels attrape-t-on ?*

Ce n'est pas la question que posent les scores usuels. Un CSI ou un F1 **choisit le seuil
qui maximise le score**, ce que personne ne fait en exploitation : un service subit une
contrainte de crédibilité. Au-delà d'une certaine proportion d'alertes démenties par les
faits, l'alerte cesse d'être écoutée — et le coût n'est pas dans la métrique, il est dans
le partenaire qui n'ouvre plus le message.

L'indicateur inverse donc l'ordre habituel : **on fixe d'abord la qualité d'annonce, on
mesure ensuite ce qu'on attrape.**

## 2. Définition exacte

**Événement.** Un *jour-station* dont le maximum glissant sur 8 h d'ozone dépasse
**120 µg/m³** — valeur cible européenne (directive 2008/50/CE). C'est une **valeur cible**,
pas un seuil de procédure préfectorale : voir la limite ① au § 6.

**Table de contingence**, sur l'ensemble des jours-station évalués :

| | dépassement observé | pas de dépassement |
|---|---|---|
| **alerte émise** | `a` bonnes détections | `b` fausses alertes |
| **pas d'alerte** | `c` manques | `d` bons rejets |

**Les deux grandeurs :**

```
rappel  (POD) = a / (a + c)      part des dépassements réels qui ont été annoncés
budget  (FAR) = b / (a + b)      part des ALERTES ÉMISES qui se révèlent fausses
```

⚠️ **Le budget porte sur les alertes émises, pas sur les jours calmes.** « Budget ≤ 30 % »
signifie *au plus 3 alertes fausses sur 10 émises*, soit une **précision ≥ 70 %**. Il ne
signifie pas « 30 % des jours calmes déclenchent une alerte » — ce serait un taux de fausse
alerte au sens du taux de faux positifs, un tout autre nombre. Les deux se notent souvent
« FAR » dans la littérature ; celui-ci est le *False Alarm Ratio*.

**L'indicateur** est le rappel atteint sous la contrainte `FAR ≤ budget`, pour une série de
budgets. Un produit qui ne peut satisfaire la contrainte à aucun seuil est déclaré
**« budget inatteignable »** — c'est une information, pas une valeur manquante.

## 3. Méthode de calcul

1. Agréger l'horaire au journalier selon la grandeur réglementaire du polluant
   (max glissant 8 h pour l'ozone), en rejetant les jours trop lacunaires.
2. Ordonner les jours-station par le score du système.
3. **Choisir le seuil sur d'autres stations que celles évaluées** — le point de
   fonctionnement est hors échantillon. Un seuil choisi sur les stations où on le mesure
   fabriquerait le résultat.
4. Appliquer le seuil, dresser la contingence, retenir le rappel si `FAR ≤ budget`.

Implémentation : `scripts/detection_maximale.py`, contingence dans
`scripts/scores_episodes.py`.

## 4. Périmètre — et il y en a **deux**, jamais interchangeables

| périmètre | ce qu'il suppose | où il s'applique |
|---|---|---|
| **PARTOUT** | aucune observation passée de la station | **là où rien ne mesure** — spatialisation |
| **aux stations** | l'historique du point est disponible | uniquement là où un capteur existe déjà |

C'est la distinction la plus facile à perdre, et la plus coûteuse : les deux chiffres sont
justes, ils ne répondent pas à la même question.

## 5. Valeur mesurée

**Ozone · 2 293 dépassements sur 134 423 jours-station (1,71 %)** · échéance J+1 ·
point de fonctionnement hors échantillon.

| budget (FAR ≤) | CAMS brut | correction seule — *PARTOUT* | correction + obs. passées — *aux stations* |
|---|---|---|---|
| 10 % | *inatteignable* | 0,206 | **0,355** |
| 20 % | 0,080 | 0,396 | **0,529** |
| **30 %** | **0,184** | **0,558** | **0,656** |
| 40 % | 0,383 | 0,697 | **0,752** |

**À 30 % de budget — donc à 7 alertes justes sur 10 :**
- périmètre **PARTOUT** : 0,558 contre 0,184, soit **3,0× plus de dépassements attrapés** ;
- périmètre **aux stations** : 0,656, soit **3,6×**.

À 20 % de budget, le facteur monte à **6,6×**. Et **CAMS brut n'atteint jamais 10 %** :
quel que soit son seuil, plus d'une de ses alertes sur dix est fausse.

**Le facteur se reproduit hors fenêtre d'apprentissage** — modèle appris jusqu'au
31/12/2024, seuils calibrés sur 2024, appliqués en aveugle au 1ᵉʳ semestre 2025 :
**3,5×** à 30 % et **6,8×** à 20 %. Les FAR constatés sur 2025 (0,030 à 0,165) restent
**sous** les budgets visés : les seuils calibrés sur l'année précédente sont conservateurs.

## 6. Limites connues — à lire avant toute citation

**① L'indicateur porte sur la valeur cible européenne, jamais sur le seuil de procédure.**
Au seuil français d'information — **180 µg/m³ en maximum horaire** — l'ozone ne compte que
**32 dépassements sur 60 400 jours-station** : CAMS en détecte 3, notre correction 2 à J+1,
et **aucun des deux à J+3**. Un modèle entraîné directement sur ce grain fait pareil.
L'échec est mécanique — 53 prédicteurs ne contiennent rien qui distingue un jour à
175 µg/m³ d'un jour à 185, et 32 événements ne permettent pas de l'apprendre. **Citer le
« 3,6× » en parlant de procédure préfectorale serait faux.**

**② L'indicateur n'a pas de sens sur tous les polluants.** Le NO₂ compte **270 dépassements
sur 161 637 jours-station (0,17 %)** au grain 120 µg/m³ en max horaire — dix fois plus rare
que l'ozone ou les PM2,5 — et **aucun budget ≤ 40 % n'y est atteignable**. Au seuil
d'information de 200 µg/m³, le panel unifié compte **6 dépassements sur 368 904
jours-station** (2023-06 → 2026-08, 344 stations, règle des 75 %) : un événement tous les
soixante mille jours-station. **À ce seuil, l'indicateur ne mesure pas une capacité de
détection — il mesure l'absence de ce qu'on cherche.**

> ✅ **Chiffre mesuré le 07/08/2026, après avoir été signalé la veille comme non établi.**
> `VERITE_DOSSIER` en donnait **2** au § 8 et **3** au § 10 bis, sur deux corpus différents
> (161 637 et 60 400 jours-station) — et **aucun des deux n'était calculé** : deux chaînes
> écrites en dur dans `verite_dossier.py`, donc deux chiffres recopiés. Ils sont remplacés
> par `compte_depassements_no2()`, qui lit le panel et nomme son corpus. La conclusion ne
> change pas ; c'était bien la contradiction qu'il fallait lever, pas le verdict.

*Un seuil sans événements ne mesure pas une incapacité à détecter : il mesure l'absence de
ce qu'on cherche.* Compter les positifs avant de conclure.

**③ Le classement généralise mieux que la valeur.** La précision ponctuelle généralise mal
dans le temps (+1,1 % en saison ozone, prospectif strict) alors que le **classement des
jours par risque** tient. Le modèle sait ordonner ce qu'il ne sait pas chiffrer — et c'est
l'ordre qui décide d'une alerte. L'indicateur exploite cette propriété ; il ne prouve pas
que les concentrations prédites sont justes.

**④ L'échantillon hors fenêtre est petit** — 21 stations, ~160 dépassements sur 2025. La
**reproduction du facteur** est plus informative que sa valeur au centième.

**⑤ La latence de validation gouverne la date de calcul.** L'indicateur se calcule contre
des observations validées ; tout l'ozone du flux national bascule en code de validité 4
après le 01/07/2025 (les mesures continuent, la validation s'est arrêtée). **La fréquence
mensuelle proposée est donc un objectif, pas une garantie** : elle dépend d'une chaîne de
validation qui n'est pas la nôtre.

## 7. Ce que l'indicateur ne dit pas

- Il ne compare **pas des équipes** : le post-traitement officiel répond à des contraintes
  d'exploitation — couverture européenne, réentraînement continu, publication horaire — que
  ce travail n'a pas.
- Il ne dit rien de l'**ampleur** d'un épisode, seulement de son occurrence. Le § 9 de
  `VERITE_DOSSIER` couvre ce volet (nombre de stations le même jour).
- Il ne dit rien du **coût** d'une fausse alerte rapporté à celui d'un manque. Ce taux de
  change appartient au destinataire, pas au producteur de l'indicateur — et c'est
  précisément pourquoi l'indicateur publie une **courbe** de budgets et non un seul nombre.

## 8. Destinataire et décision servie

| destinataire | décision | ce que la fiche lui donne |
|---|---|---|
| Prévisionniste AASQA | à quel seuil régler l'annonce du lendemain | le rappel qu'il achète à chaque niveau de crédibilité |
| Préfecture | déclencher ou lever une procédure | ⚠️ **rien directement** — voir limite ① |
| Direction, tutelle | l'évaluation annuelle imposée par l'article 13 de l'arrêté du 16/04/2021 | un indicateur reproductible, à protocole écrit |

## 9. Traçabilité

| | |
|---|---|
| Valeurs | `reports/VERITE_DOSSIER.md` § 8 |
| Calcul | `scripts/detection_maximale.py` · `scripts/scores_episodes.py` |
| Sortie brute | `reports/detection_maximale_O3.csv` · `reports/detection_2025_O3.csv` |
| Régénération | `python3 scripts/verite_dossier.py` |
| Contrôle | `python3 scripts/verifier_dossier_candidature.py` — recalcule les chiffres cités depuis les artefacts |

**Règle de gouvernance de cette fiche :** toute valeur qui y figure doit exister dans
`VERITE_DOSSIER.md`. Une valeur recopiée d'une note et absente de la source est à retirer
ou à re-mesurer — c'est la règle qui a déjà rattrapé, sur ce dossier, une table de
réconciliation portant des chiffres périmés qu'aucun fichier ne produisait.
