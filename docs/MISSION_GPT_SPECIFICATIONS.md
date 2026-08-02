# Mission pour ChatGPT — produire des spécifications exécutables

> À coller tel quel. Autoportant.
> Tu n'as **pas** accès au dépôt : c'est délibéré. Un autre agent l'a, et exécutera ce que tu
> spécifies. Ta valeur ici est la **conception** et l'**ancrage bibliographique**, pas la
> mesure.

---

## Le contrat

Chaque livrable que je te demande doit être **implémentable sans te reposer une question**.
Formules explicites, unités, conventions temporelles, cas limites, et le critère qui dirait que
c'est mal implémenté. Une spécification qui commencerait par « il faudrait envisager de… » ne
sert à rien ici.

Quand une valeur numérique dépend d'un choix (seuil, fenêtre, coefficient), donne **la valeur
que tu retiens** et la source, pas un intervalle de possibilités.

---

## Contexte minimal

Post-traitement statistique des prévisions CAMS Europe (0,1° ≈ 8 km, J+1 à J+3) pour O₃, NO₂ et
PM2,5. Le modèle apprend le **résidu** `observation − CAMS` à la grandeur réglementaire du
polluant — max glissant 8 h (O₃), max horaire (NO₂), moyenne journalière (PM2,5). Gradient
boosting, validation par stations entièrement exclues, 17 mois (août 2023 → décembre 2024),
270 stations, 134 423 jours-station sur l'ozone.

**Les 53 prédicteurs** : 28 de paysage (essences, distances et densités de 100 m à 30 km), 9 de
relief (position topographique multi-échelle, pente, vallée), 6 de calendrier, 5 de trafic
hiérarchisé et population, 3 de position (lat, lon, altitude), et **2 seulement issus de
CAMS** — la concentration prévue du polluant modélisé, et l'échéance.

**Aucune météo.** C'est une précaution contre la fuite : toute entrée doit exister à l'heure
d'émission de la prévision.

### Ce qui a été mesuré et qui cadre tes livrables

| expérience | résultat |
|---|---|
| ajouter la météo **ERA5** | O₃ **+7,8 %** · PM2,5 **+6,7 %** · NO₂ +2,7 %, IC95 tous positifs, décile haut **meilleur partout** |
| ajouter les **concentrations CAMS des autres espèces** (µg/m³) | +0,069 µg/m³, IC95 [−0,083 ; +0,204] → **nul** |
| refaire avec la **chimie** : Ox molaire, fraction de partition, résumés nocturnes | **−0,076**, IC95 [−0,270 ; +0,087] → **nul, et pire** |
| retirer les variables **forestières** | le modèle **s'améliore** (−1,9 % de RMSE) |

La lecture retenue : *une correction apprise n'ajoute de valeur que là où le modèle amont est
aveugle à lui-même.* CAMS connaît sa chimie et ses émissions ; il ne connaît pas l'erreur de son
propre forçage météorologique, ni l'environnement sous-maille d'une station. **Si tu penses que
cette lecture est fausse, dis-le d'abord** — elle oriente tout ce qui suit.

---

## Livrable 1 — Le jeu de variables météo **opérationnel** *(le plus important)*

ERA5 est une **réanalyse** : elle n'existe pas à l'heure d'émission. Le +7,8 % est donc un
**plafond**, pas un gain déployable. Une chaîne réelle emploierait les **prévisions IFS**,
disponibles sur l'ADS/CDS, aux mêmes échéances que CAMS.

**Spécifie le jeu de variables météo qu'un service pourrait réellement brancher.** Pour chacune :

| champ | nom IFS / paramètre | niveau | agrégation journalière | pourquoi cette statistique |

Contraintes de conception, à respecter explicitement :

- **La statistique d'agrégation compte.** Ce projet a mesuré que corriger l'horaire puis agréger
  perd 5,8 points de gain contre apprendre directement le maximum. Applique le même
  raisonnement aux prédicteurs : pour chaque variable, dis si c'est la **moyenne**, le
  **maximum**, le **minimum**, un **cumul** ou une **heure d'occurrence** qui porte le
  mécanisme, et pourquoi.
- **Les directions sont circulaires.** Toute variable angulaire doit être spécifiée en
  projection, avec la pondération que tu retiens.
- **Les grandeurs dérivées priment sur les champs bruts.** Donne les formules complètes —
  coefficient de ventilation, indicateurs de stabilité, de stagnation, de déficit de saturation,
  d'accumulation depuis la dernière pluie. Précise les unités et les valeurs seuils que tu
  retiens, avec leur source.
- **Distingue les trois polluants.** Une variable utile à l'ozone ne l'est pas forcément aux
  particules. Indique pour chacune le ou les polluants visés.
- **Disponibilité.** Pour chaque champ, dis s'il est disponible en **prévision** à J+1..J+3, ou
  seulement en réanalyse. Ceux qui ne le sont pas doivent être écartés, pas signalés en note.

Termine par un **ordre de priorité** : si je ne peux implémenter que six variables, lesquelles,
et quelle part du plafond de +7,8 % espères-tu qu'elles capturent ?

---

## Livrable 2 — Protocole de décomposition de la dispersion intra-maille

Le dossier annonçait un « **plancher de représentativité** » de 3,61 µg/m³ — la dispersion
entre stations d'une même maille de 0,1°, soit 26 % du RMSE. Le mot « plancher » a été retiré :
cette dispersion mélange différence de support, gradients urbains réels, bruit instrumental et
sélection du réseau. Rien n'établit qu'aucune méthode ne descende sous cette valeur.

**Spécifie le protocole qui trancherait.** Il doit dire :

1. comment constituer les **paires comparables** (simultanéité, typologie, distance, altitude) ;
2. comment **décomposer la variance** entre ses composantes, avec le modèle statistique explicite ;
3. quelle **unité de rééchantillonnage** — les paires d'une même maille ne sont pas
   indépendantes ;
4. quel **résultat rétablirait** le mot « plancher », et lequel l'interdirait définitivement.

Et une question bibliographique : **quelles valeurs publiées** existent pour la représentativité
spatiale d'une station de fond en Europe, à quelle échelle, et notre 3,61 µg/m³ est-il
cohérent ? Donne les références et les ordres de grandeur.

---

## Livrable 3 — Spécification du `rolling-origin` strict

Tu as établi que notre « double aveugle » (station et mois cachés simultanément, gain +1,5 %)
n'est **pas** prospectif : rien ne garantit que toutes les dates d'entraînement précèdent le
mois testé.

**Spécifie l'évaluation prospective stricte** qu'un autre agent implémentera :

- la règle exacte de construction des plis, et l'**assertion automatique** qui doit échouer si
  elle est violée ;
- le traitement de la fenêtre d'échauffement — combien de mois d'historique minimum avant que
  le premier pli soit évaluable, et pourquoi ;
- ce qu'on fait des **stations** : les cache-t-on aussi, et si oui comment sans réduire
  l'effectif au point de rendre le test non concluant ;
- la **statistique de synthèse** : gain moyen, dispersion, ou distribution complète — et quel
  test compare ce résultat au +1,5 % actuel, sachant que les deux protocoles ne portent pas sur
  les mêmes plis ;
- le nombre de réajustements que cela représente, pour que je puisse extrapoler le coût avant
  de lancer.

---

## Livrable 4 — Ce que la littérature dit et que nous n'appliquons pas

Une liste courte — **cinq entrées maximum** — de pratiques établies en post-traitement de
prévisions de qualité de l'air que ce projet n'applique pas. Pour chacune :

| pratique | référence | ce qu'elle changerait ici | coût | pourquoi elle pourrait ne rien donner **dans notre cas** |

La dernière colonne est obligatoire. Elle doit tenir compte du constat central : *une correction
n'ajoute que là où la physique amont est aveugle*. Une pratique qui redonnerait au modèle ce que
CAMS calcule déjà est à écarter d'emblée, et je préfère que tu l'écartes toi-même plutôt que de
me la proposer.

---

## Ce que je ne te demande pas

- Aucune liste de tâches générale : deux rondes l'ont déjà produite.
- Aucune architecture de modèle : gradient boosting est arrêté, les alternatives ont été
  mesurées et écartées.
- Aucune spatialisation à l'EPCI : abandonnée, décision assumée.

Si l'un de ces quatre livrables te paraît mal posé, dis-le avant de le traiter.
