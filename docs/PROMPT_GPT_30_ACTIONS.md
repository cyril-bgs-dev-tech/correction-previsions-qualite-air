# Prompt pour ChatGPT — les 30 prochaines actions, angle méthode

> À coller tel quel. Le document est autoportant : aucune pièce jointe n'est nécessaire.

---

Tu es relecteur méthodologique d'un projet de science des données appliqué à la qualité de
l'air. Ta tâche : **proposer les 30 prochaines actions**, ordonnées par valeur décroissante,
au vu de l'état ci-dessous.

Un second relecteur (Grok 4.5) reçoit le **même état** avec une consigne différente : valeur
opérationnelle, lisibilité par un recruteur, angles morts créatifs. **Ne traite pas ces
sujets.** Ton angle est la **validité** : protocole d'évaluation, inférence statistique,
falsifiabilité, ancrage bibliographique, honnêteté des énoncés.

---

## 1. Le projet en une phrase

Post-traitement statistique (MOS) des prévisions CAMS Europe de qualité de l'air, entraîné à
l'échelle de la France, évalué sur l'Occitanie, avec pour finalité une **candidature
spontanée à ATMO Occitanie (AASQA) le 22 août 2026**.

Sortie : correction du champ CAMS aux stations, à échéance J0 (1-24 h) à J+3, pour O₃, NO₂ et PM2,5.

## 2. Données réellement sur disque

| Jeu | Étendue | Réserve connue |
|---|---|---|
| Observations, panneau métropolitain | 2013 → **31/12/2024**, 430 stations, 94 M lignes | **aucune observation en 2025** (flux EEA rompu) |
| Observations, panneau occitan | 1999 → 2026, O₃ valide jusqu'à **juin 2025** | 21-23 stations seulement sur 2025 |
| Prévisions CAMS | juillet 2023 → juin 2025 (24 mois) | **17 mois appariés** à des observations |
| ERA5 | 12 mois de 2024 extraits | volontairement borné |
| MOS officiel Copernicus (`optimised-at-observation-sites`) | 12 mois 2024 × 3 polluants + 6 mois 2025 (O₃) | horaire, échéance 24-47 h |
| Statiques | 38 variables de paysage, 9 de relief, trafic hiérarchisé BD TOPO, population | 476 stations |

## 3. Protocole d'évaluation en vigueur

- **Validation par stations entièrement exclues** (leave-station-out) — le modèle ne voit
  jamais les stations de test.
- **Double aveugle** : station *et* mois cachés simultanément.
- Cible apprise : le **résidu** `observation − CAMS`, agrégé à la **grandeur réglementaire**
  du polluant — max glissant 8 h (O₃), max horaire (NO₂), moyenne journalière (PM2,5).
- Intervalles par **bootstrap par blocs** (station et temps), facteur de pseudo-réplication
  mesuré à **1,7×**.
- Métriques d'épisode selon le référentiel **LCSQA** : POD, FAR, SR, FB, CSI.
- Famille de modèles arrêtée : gradient boosting (XGBoost GPU / LightGBM / CatBoost tiennent
  en 0,3 point — le choix de bibliothèque ne compte pas).

## 4. Résultats acquis, avec leurs chiffres

**Gain contre CAMS brut** (17 mois, stations exclues) : O₃ **+19,3 %**, NO₂ **+29,7 %**.

**Contre le produit officiel de Copernicus**, année 2024 complète :

| polluant | grain | n | CAMS brut | MOS officiel | nous |
|---|---|---|---|---|---|
| O₃ | horaire | 1 648 619 | 17,30 | 14,43 (+16,6 %) | 13,55 (+21,7 %) |
| O₃ | **max 8 h** (réglementaire) | 73 108 | 12,08 | 11,85 (**+2,0 %**) | 9,49 (**+21,5 %**) |
| NO₂ | horaire | 1 300 663 | 7,75 | 6,45 (+16,7 %) | 7,54 (**+2,7 %**) |
| NO₂ | **max horaire** (réglementaire) | 57 824 | 15,13 | 12,03 (+20,5 %) | 10,34 (+31,6 %) |
| PM2,5 | horaire | 720 731 | 5,17 | 4,68 (+9,5 %) | 4,11 (+20,5 %) |
| PM2,5 | **moyenne jour** (réglementaire) | 31 960 | 3,79 | 3,22 (+15,0 %) | 2,69 (+29,1 %) |

Lecture actuelle : le **grain d'apprentissage décide du résultat**. Leur post-traitement est
horaire ; les seuils réglementaires sont des **maxima**, statistiques d'ordre sensibles à toute
réduction de variabilité. Symétriquement, **notre modèle n'apporte presque rien en horaire sur
NO₂ (+2,7 %)** — nous avons optimisé le grain journalier. Le phénomène est publié (Huang et al.
2017) : nous le quantifions, nous ne le découvrons pas.

**Test hors échantillon** — modèle appris jusqu'au 31/12/2024, appliqué au 1ᵉʳ semestre 2025
(21 stations occitanes, 3 353 jours-station, 163 dépassements) :

| produit | RMSE | biais | R² | POD@120 | FAR | CSI |
|---|---|---|---|---|---|---|
| CAMS brut | 11,04 | +0,23 | 0,724 | 0,331 | 0,069 | 0,323 |
| MOS officiel | 13,56 | −5,13 | 0,584 | 0,460 | 0,312 | 0,381 |
| nous | **10,33** | −0,38 | **0,758** | **0,239** | 0,049 | 0,236 |

**Seuil de décision recalibré sur 2024, appliqué en aveugle sur 2025** (tous les produits
recalibrés à l'identique) :

| produit | seuil | POD | FAR | CSI |
|---|---|---|---|---|
| CAMS brut | 113,5 | 0,515 | 0,229 | 0,447 |
| MOS officiel | 105,9 | **0,718** | 0,543 | 0,387 |
| nous | 111,7 | 0,571 | **0,212** | **0,495** |

→ Le POD de 0,239 était un **artefact de seuil** (+0,331 en recalibrant, contre +0,184 pour le
CAMS brut). Mais nous ne dominons pas : l'officiel détecte plus, en acceptant 2,5× plus de
fausses alertes.

**Métriques de rang (TSB-AD, tolérance ±3 jours)**, 2025 : AUC-PR 0,764 (brut) / 0,651
(officiel) / **0,786** (nous). VUS-PR 0,711 / 0,630 / **0,752**.

**Autres résultats établis** :

- généralisation **spatiale** : +19,4 %, σ 1,2 — le point solide ;
- généralisation **temporelle** : double aveugle **+1,5 %** seulement, pire pli **−14,6 %** ;
- classification calibrée du dépassement : POD 0,345 → **0,663**, Brier skill **+0,460** ;
- front de Pareto : queue haute −3,1 % → **+3,1 %** à RMSE global inchangé (perte pondérée) ;
- trafic hiérarchisé : **+13,0 %** sur NO₂, IC95 [+10,4 ; +15,5] ;
- variable la plus utile sur O₃ : le **calendrier** (la retirer coûte +9,1 %) ;
- plancher de représentativité intra-maille : **3,61 µg/m³**, soit 26 % du RMSE ;
- ruptures du forçage CAMS (13/11 et 03/12/2024) : corrélation **+0,913** entre le saut de
  biais brut et le gain de la correction — une part du gain est une régression du forçage ;
- biais d'écrêtage à zéro : négligeable (0,043 %).

## 5. Ce qui est ouvert, incertain ou fautif

1. **FAIRMODE** : α PM2,5 valait 0,13 (celui de PM10) au lieu de 0,30 — corrigé, MQI à
   recalculer. Le MQI est en outre calculé en **horaire** pour les trois polluants alors que le
   document le définit en max 8 h (O₃) et journalier (PM2,5). Reste à trancher : v3.2 (DOI
   10.2760/30226) ou v4.0 (mai 2026, β par polluant).
2. Les **livrables** (présentation 10 pages, 9 figures, démo Streamlit) citent encore les
   chiffres d'une fenêtre de 11 mois, périmés.
3. La **fiche opérationnelle** (quelles entrées sont garanties à l'heure d'émission) n'est pas
   validée — ce qui bloque l'usage des observations récentes en entrée.
4. Aucune **observation métropolitaine 2025** : la validation inter-annuelle repose sur 21
   stations occitanes.
5. Neuf **hypothèses implicites** relevées par une relecture antérieure, dont deux majeures :
   ① une station et une maille CAMS de 0,1° ne décrivent pas le même objet (écart 5-30 µg/m³) ;
   ⑨ « station inconnue » signifie *autre station du même réseau*, pas un lieu quelconque.
6. La **spatialisation à l'EPCI** — dernier maillon vers l'indice publié — est abandonnée faute
   de temps ; l'écart résiduel est de −0,72 classe d'indice.

## 6. Contraintes dures

- **Échéance 22 août 2026**, arrêt impératif des calculs **10 jours ouvrés** avant : ce temps
  va au récit, aux figures et à la relecture.
- **Critère d'arrêt déjà adopté** : aucun calcul supplémentaire si le meilleur candidat n'a pas
  démontré, sur prédictions appariées **hors station et hors mois**, une baisse ≥ **0,3 µg/m³**
  avec IC95 strictement au-dessus de zéro, **sans** dégrader le RMSE du décile haut de plus de
  0,3 ni le CSI.
- Machine : RTX 5090, 32 cœurs. Une bibliothèque saturant déjà les cœurs ne se parallélise pas
  en la lançant plusieurs fois.
- **Registre imposé : rigueur, pas compétition.** Pas de « nous battons Copernicus ». Énoncer
  les faits, et dire d'abord qu'on ignore les contraintes ayant motivé leurs choix.

## 7. Décisions déjà prises — ne pas les rouvrir

- ❌ Architectures alternatives (RealMLP, TabM, GNN) : écartées, mesurées.
- ❌ Spatialisation EPCI.
- ❌ `log(1 + résidu)` : domaine mathématiquement invalide.
- ❌ Exclure les stations difficiles : toute règle écrite après lecture des erreurs fabrique un
  score. Les stratifier, jamais les retirer.
- ❌ Recherche exhaustive d'hyperparamètres.

---

## Ce que je te demande

**30 actions, numérotées, de la plus utile à la moins utile**, dans un tableau à ces colonnes :

| # | Action | Ce qu'elle teste ou corrige | Coût (h) | Résultat qui la rendrait décisive | Résultat qui l'enterrerait |

Contraintes de rédaction :

1. Chaque action doit être **exécutable telle quelle** — pas « améliorer la validation » mais
   la manipulation précise, sur quelles données, avec quelle métrique.
2. Chaque action doit être **falsifiable** : la dernière colonne doit décrire un résultat
   concret qui conduirait à l'abandonner. Une action qu'aucun résultat ne peut enterrer est une
   croyance, pas un test.
3. Le coût doit être **compatible avec 3 semaines dont 2 de calcul**. Si la somme de tes 10
   premières actions dépasse ce budget, dis-le et arbitre.
4. Priorise ce qui **change une conclusion publiée** avant ce qui gagne des décimales. Une
   erreur qui invaliderait un énoncé du dossier passe avant un gain de RMSE.

Puis, en dehors du tableau, réponds à ces cinq questions :

- **A.** Parmi les résultats de la section 4, lequel est le **plus fragile** à une objection de
  jury, et quelle est l'objection exacte ?
- **B.** La recalibration de seuil (section 4) est-elle méthodologiquement propre, ou ai-je
  introduit une fuite ? Le seuil est cherché sur 2024 par maximisation du CSI, appliqué à 2025
  sans réajustement.
- **C.** Le rapprochement entre grain d'apprentissage et grain réglementaire est-il correctement
  attribué dans la littérature ? Donne les références que je dois citer, et dis si l'une
  d'elles rend mon résultat redondant.
- **D.** Avec 21 stations et 163 dépassements, quelle **puissance statistique** ai-je réellement
  sur le test 2025 ? Quels écarts puis-je légitimement déclarer, et lesquels dois-je présenter
  comme non concluants ?
- **E.** Quelles **trois actions de la section 6 de mon propre plan** devrais-je supprimer parce
  qu'elles ne survivraient pas au critère d'arrêt ?

Sois direct. Si une partie de l'état ci-dessus te paraît mal mesurée ou mal énoncée, dis-le
avant de proposer quoi que ce soit.
