# Prompt pour ChatGPT — audit de la chaîne de raisonnement

> À coller tel quel. Autoportant.

---

Tu es auditeur méthodologique. Ta tâche n'est **pas** de proposer une liste de tâches — une
autre ronde l'a déjà fait et ses conclusions sont appliquées. Ta tâche est d'**auditer la
logique** d'un projet de post-traitement de prévisions de qualité de l'air : où un pas ne suit
pas de ses prémisses, quelle explication alternative n'a pas été écartée, et quelle
connaissance du domaine — physique, chimie atmosphérique, métrologie — le projet ignore alors
qu'elle est à sa portée.

Grok 4.5 reçoit le même état avec une consigne complémentaire : auditer ce qu'on **possède et
n'exploite pas**, et les angles morts opérationnels. **Ne traite pas ça.** Ton angle est la
**validité inférentielle** et la **connaissance du domaine non mobilisée**.

---

## 1. Le système

Correction apprise (MOS) des prévisions CAMS Europe (0,1° ≈ 8 km, J+1 à J+3) pour O₃, NO₂ et
PM2,5, entraînée en France, évaluée sur l'Occitanie. Le modèle apprend le **résidu**
`observation − CAMS`, agrégé à la **grandeur réglementaire** du polluant : max glissant 8 h
(O₃), max horaire (NO₂), moyenne journalière (PM2,5). Gradient boosting, validation par
**stations entièrement exclues**.

**Les 53 prédicteurs, par famille** — c'est le point le plus important de ce document :

| famille | nombre | contenu |
|---|---|---|
| paysage | 28 | essences forestières, distances et densités multi-rayons (100 m → 30 km) |
| relief | 9 | position topographique multi-échelle, pente, encaissement, profondeur de vallée |
| calendrier | 6 | heure, jour de l'année, semaine, projections circulaires |
| trafic / population | 5 | réseau routier hiérarchisé BD TOPO, population |
| **CAMS** | **2** | la concentration prévue **du polluant modélisé**, et l'échéance |
| position | 3 | latitude, longitude, altitude |

**Aucune variable météorologique. Aucune concentration d'un autre polluant. Aucune observation
passée. Aucune dispersion d'ensemble.**

## 2. Ce qui est établi, avec les chiffres

**Contre le produit corrigé officiel de Copernicus** (`optimised-at-observation-sites`),
18/01 → 31/12/2024, mêmes stations et mêmes jours :

| polluant | grain | CAMS brut | MOS officiel | nous |
|---|---|---|---|---|
| O₃ | horaire | 17,30 | 14,43 (+16,6 %) | 13,55 (+21,7 %) |
| O₃ | **max 8 h** (réglementaire) | 12,08 | 11,85 (**+2,0 %**) | 9,49 (+21,5 %) |
| NO₂ | horaire | 7,75 | 6,45 (+16,7 %) | 7,54 (**+2,7 %**) |
| NO₂ | **max horaire** | 15,13 | 12,03 (+20,5 %) | 10,34 (+31,6 %) |
| PM2,5 | horaire | 5,17 | 4,68 (+9,5 %) | 4,11 (+20,5 %) |
| PM2,5 | **moyenne jour** | 3,79 | 3,22 (+15,0 %) | 2,69 (+29,1 %) |

**Le +2,0 % annuel de l'ozone masque un changement de signe** : −19,1 % sur la saison ozone
(avril-septembre, fenêtre LCSQA) et +18,7 % hors saison. Le produit officiel dégrade le brut
**8 mois sur 12**, au pire −43,2 % en juin, avec un biais négatif chaque mois.

**Expérience contrôlée** (même modèle, mêmes lignes, mêmes plis, **seule la cible change**) :

| polluant | grain réglementaire | horaire → agrégé | cible directe | écart |
|---|---|---|---|---|
| O₃ | max 8 h (**maximum**) | +17,50 % | +23,30 % | **+5,8 pts** |
| NO₂ | max horaire (**maximum**) | +25,56 % | +32,11 % | **+6,5 pts** |
| PM2,5 | moyenne jour (**moyenne**) | +27,60 % | +26,11 % | **−1,5 pt** |

**Antériorité assumée** : Bertrand, Meleux, Ung, Descombes & Colette 2023, *ACP* 23, 5317
(doi:10.5194/acp-23-5317-2023) — l'article décrivant le produit officiel, écrit par ses auteurs
— rapporte 20,5 % contre 32,8 % pour le même changement de cible et recommande le MOS
journalier. Notre factoriel est une **réplication**, pas une découverte.

**Validation** :

| propriété | mesure |
|---|---|
| généralisation spatiale (stations exclues) | **+29,7 %**, σ 1,2, aucun pli négatif |
| généralisation temporelle (mois caché) | +6,7 %, pire pli **−35,5 %**, 5 négatifs sur 17 |
| double aveugle (station *et* mois) | **+1,5 %**, pire pli −41,4 %, **8 négatifs sur 17** |

Le réglage des hyperparamètres, choisi contre une validation **spatiale**, gagne 5 points en
spatial et en **perd 3** en temporel.

**Hors fenêtre d'apprentissage** (1ᵉʳ semestre 2025, 21 stations occitanes, 3 353 jours-station,
163 dépassements), seuils calibrés sur 2024 et appliqués en aveugle aux trois produits. Après
bootstrap apparié par blocs (stations × blocs calendaires, 3 longueurs, 2 000 tirages) :
**une seule comparaison survit** — RMSE contre le MOS officiel, −3,22 [−4,87 ; −1,74]. Les
écarts de CSI (+0,107) et de POD (−0,147) sont **non concluants**.

**Autres résultats** :

- classification calibrée du dépassement : POD 0,345 → **0,663**, Brier skill +0,460 ;
- perte pondérée : queue haute −3,1 % → **+3,1 %** à RMSE global inchangé ;
- trafic hiérarchisé : **+13,0 %** sur NO₂ ; la population n'ajoute rien ;
- variable la plus utile sur O₃ : le **calendrier** (la retirer coûte +9,1 %) ;
- plancher de représentativité intra-maille : **3,61 µg/m³**, 26 % du RMSE ;
- le gain suit le défaut du forçage amont : **+0,953** en ΔMSE, et +14,0 % quand CAMS est bon
  contre +23,6 % quand il dérive — une part du gain est une régression du forçage ;
- MQI FAIRMODE au grain du référentiel : O₃ 0,255 · NO₂ 0,485 · PM2,5 0,354, tous conformes.

## 3. Trois expériences récentes, dont deux négatives

**Détecteur d'anomalies sur l'état d'entrée** (IForest et ECOD, hors échantillon par stations) :

- il est **aveugle** aux ruptures documentées de la chaîne CAMS (13/11 et 03/12/2024) —
  55ᵉ et 48ᵉ percentile, soit le hasard ;
- le score porte pourtant une information au-delà de la valeur de CAMS (90 % des bandes de
  CAMS, écart médian +31,5 de MSE), mais **de sens inverse à l'hypothèse** : la correction
  gagne **plus** sur les états d'entrée inhabituels ;
- sur le décile le plus anormal, **aucune politique alternative ne bat « corriger toujours »** :
  s'abstenir coûte +2,60 µg/m³, un modèle dédié aux journées anormales coûte +1,37.

**Moniteur de dérive sur le résidu** : la dérive y est réelle (+4,76 µg/m³ le 13/11, détectée
en 13 jours ; +2,87 le 03/12, non détectée), et la théorie prédit l'observation — il faut 10 et
28 jours d'accumulation contre un bruit quotidien de σ = 3,87. Mais ce bruit porte déjà sur une
moyenne de 259 stations : **c'est de la variabilité synoptique en mode commun**, que davantage
de stations ne réduira pas. Au seuil de 95 %, l'alarme sonne une fois tous les 20 jours.

**Plafond de la météo** (ERA5 ajoutée au même protocole) :

| polluant | RMSE base | gain | relatif | IC95 | décile haut |
|---|---|---|---|---|---|
| O₃ | 8,378 | +0,654 | **+7,8 %** | [+0,53 ; +0,78] | −0,42 *(meilleur)* |
| PM2,5 | 2,971 | +0,199 | **+6,7 %** | [+0,15 ; +0,25] | −0,55 *(meilleur)* |
| NO₂ | 15,036 | +0,400 | +2,7 % | [+0,21 ; +0,61] | −1,35 *(meilleur)* |

ERA5 étant une réanalyse, **c'est un plafond, pas un gain déployable**.

## 4. Contraintes

- Toute entrée doit être disponible **à l'heure d'émission de la prévision**. C'est la raison
  d'être de l'exclusion de la météo et des observations récentes.
- Critère d'arrêt : gain ≥ **0,3 µg/m³**, IC95 > 0, sans dégrader le RMSE du décile haut de
  plus de 0,3 ni le CSI. *(Ce critère vient d'être reconnu défectueux : il est en unités
  absolues et s'applique à des polluants dont le RMSE varie d'un facteur 5.)*
- Registre imposé : rigueur, pas compétition.
- Déjà écartés et mesurés : architectures alternatives, spatialisation EPCI, `log(1+résidu)`,
  exclusion des stations difficiles, recherche exhaustive d'hyperparamètres.

---

## Ce que je te demande

### A. Audit de la chaîne inférentielle

Reprends les conclusions de la section 2 **une par une** et, pour chacune, réponds à trois
questions :

1. **La conclusion suit-elle des données montrées ?** Si non, dis quel pas manque.
2. **Quelle explication alternative n'a pas été écartée ?** Sois précis : nomme le confondant
   et la mesure qui le trancherait.
3. **La conclusion est-elle énoncée dans la bonne portée ?** (population, période, grandeur)

Concentre-toi sur les inférences **structurantes**, pas sur les décimales. Je cherche les
endroits où j'ai conclu plus que ce que j'ai montré.

### B. Trois incohérences apparentes que je n'arrive pas à réconcilier

Explique-les, ou dis qu'elles sont normales :

1. Le **calendrier** est la variable la plus utile sur l'ozone (+9,1 % si retirée), et la
   généralisation **temporelle** est le point faible. Est-ce le même fait vu deux fois, ou une
   contradiction ? Que devrais-je mesurer pour trancher ?
2. Un détecteur d'anomalies sur les entrées trouve que la correction gagne **plus** sur les
   états inhabituels, alors que la généralisation temporelle échoue sur des mois entiers.
   Comment ces deux faits coexistent-ils ?
3. La correction gagne **+23,6 %** quand le forçage dérive contre +14,0 % quand il est bon.
   Est-ce une propriété désirable, un artefact de régression vers la moyenne, ou le signe que
   le modèle apprend surtout un débiaisage conditionnel ?

### C. La connaissance du domaine que je n'ai pas mobilisée

C'est la partie qui m'intéresse le plus. Mes 53 prédicteurs sont listés en section 1 : je ne
donne au modèle **aucune chimie**, aucune concentration d'un autre polluant, aucune dispersion
d'ensemble, aucune observation passée.

- Quels **mécanismes physico-chimiques** de formation et de transport de l'ozone, du NO₂ et des
  particules laissent une trace exploitable dans l'erreur d'un modèle de chimie-transport à
  maille 8 km ? Nomme-les, et pour chacun dis **quelle variable observable** en porte la
  signature.
- Le couplage **NO₂ ↔ O₃** (titration, régimes limités par les COV ou par les NOₓ) est
  élémentaire, et j'ai la prévision CAMS de NO₂ sous la main sans rien télécharger. Qu'est-ce
  que je devrais construire exactement, et qu'est-ce que cela devrait améliorer — le niveau
  moyen, les maxima, les stations urbaines, la nuit ?
- Quelles grandeurs **dérivées** de la météo (et non les variables brutes) sont connues pour
  gouverner ces polluants ? Je pense aux indicateurs de stagnation, de ventilation, de
  stabilité, de rétro-trajectoire. Donne les formules ou les définitions opérationnelles.
- Qu'est-ce que la littérature de **métrologie** de la qualité de l'air dit sur la
  représentativité spatiale d'une station, que je pourrais utiliser autrement que comme une
  limite subie ? Mon plancher intra-maille de 3,61 µg/m³ est-il cohérent avec les valeurs
  publiées ?

### D. Ce que je devrais arrêter de faire

Nomme jusqu'à cinq choses présentes dans ce projet qui, à ton avis, **ne portent pas leur
coût** — en calcul, en complexité, ou en risque d'erreur. Justifie par un chiffre de la
section 2 quand c'est possible.

Sois direct. Si une partie de l'état ci-dessus te paraît mal raisonnée, dis-le avant de
répondre au reste.
