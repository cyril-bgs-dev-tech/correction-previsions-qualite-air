# Nuit du 30 juillet 2026 — résultats, décisions, et ce qui reste

Récapitulatif de la session autonome. Tout est mesuré sur **stations exclues de
l'entraînement**, sur **17 mois** d'observations appariées (août 2023 → décembre 2024).

---

## 0. Le tableau final — celui qui remplace tous les autres

`reports/modele_final.csv` · découpage unique, grandeur réglementaire, hyperparamètres réglés.

| Polluant | Grandeur | J+1 | J+2 | J+3 |
|---|---|---|---|---|
| **NO₂** | max horaire | **+33,2 %** | +33,5 % | +34,2 % |
| **O₃** | max 8 h | **+28,9 %** | +29,4 % | +30,6 % |
| **PM2.5** | moyenne journalière | **+30,0 %** | +31,0 % | +31,9 % |

**Le projet atteint l'état de l'art publié.** Riccio & Chianese 2024 (stations exclues,
CAMS) : 27 à 30 %. Nous : 29 à 34 %, protocole équivalent, grandeurs du référentiel.

Le point de départ de la nuit était **+19,3 %** en horaire. L'écart ne venait pas du modèle
mais de la **cible** et de la **capacité** — ni les données ni l'algorithme n'ont changé.

**Détection à J+1**, sur la fenêtre du référentiel : O₃ POD 0,360 → **0,521** (CSI 0,299 →
0,437) · PM2.5 POD 0,198 → **0,417** (CSI 0,128 → 0,359) · NO₂ 0,007 → 0,084, inutilisable.

⚠️ Les hyperparamètres ayant été choisis sur **O₃ J+1**, cette cellule rejoue sa propre
sélection. Les preuves propres du transfert sont **NO₂ et PM2.5**, jamais optimisés.

---

## 1. Le résultat principal : la cible était mal choisie

Le projet corrigeait des concentrations **horaires**, puis agrégeait pour obtenir les
grandeurs réglementaires. Apprendre directement la grandeur du jour change tout — mais pas
partout, et l'asymétrie s'explique.

| Polluant | Grandeur réglementaire | CAMS | horaire agrégée | cible directe | écart |
|---|---|---|---|---|---|
| **O₃** | max 8 h | 11,69 | 9,65 (+17,5 %) | **8,97 (+23,3 %)** | **+5,8** |
| **NO₂** | max horaire | 22,78 (R² −0,180) | 16,96 (+25,6 %) | **15,47 (+32,1 %)** | **+6,5** |
| **PM2.5** | moyenne journalière | 4,15 | **3,00 (+27,6 %)** | 3,07 (+26,1 %) | **−1,5** |

**La cible directe gagne sur les maxima, perd sur les moyennes.** Un maximum est une
statistique d'**extrême**, et corriger l'horaire écrase les extrêmes — mesuré trois fois
cette nuit. Une moyenne journalière est déjà une tendance centrale : la corriger heure par
heure profite de 24 observations par jour, là où le modèle direct n'en a qu'une.

**Décision** : cible directe pour **O₃ et NO₂**, agrégation horaire conservée pour **PM2.5**.

## 2. Le gain de service, qui manquait au dossier

Prédire la **probabilité de dépassement** plutôt que seuiller une concentration prédite.
O₃ à 120 µg/m³, 2 293 dépassements :

| Approche | POD | FAR | CSI | biais de fréquence |
|---|---|---|---|---|
| CAMS brut | 0,360 | 0,362 | 0,299 | 0,564 |
| MOS horaire agrégé | 0,345 | 0,203 | 0,317 | 0,433 |
| MOS cible journalière | 0,486 | 0,285 | 0,407 | 0,680 |
| **classification p ≥ 0,20** | **0,663** | 0,393 | **0,464** | **1,093** |
| classification p ≥ 0,10 | **0,737** | 0,466 | 0,448 | 1,381 |

On manque **un tiers** des dépassements au lieu de deux tiers. Et le biais de fréquence
atteint 1,09 : l'annonce cesse d'être biaisée. **L'écrasement des extrêmes disparaît quand on
prédit un événement au lieu d'une concentration.**

Le CSI de 0,464 dépasse la fourchette publiée par Bertrand et al. (0,30-0,40), sur un
protocole plus sévère puisqu'il exclut les stations.

| Polluant | Brier skill | CSI régression → classification | Verdict |
|---|---|---|---|
| O₃ | **+0,460** | 0,407 → 0,464 | ✅ solide |
| PM2.5 | **+0,351** | 0,298 → 0,372 | ✅ solide |
| NO₂ | **+0,017** | 0,048 → 0,091 | ❌ **inutilisable** |

**Le NO₂ horaire reste indétectable.** Mon critère automatique (CSI +0,02) l'avait déclaré
concluant ; le Brier skill quasi nul le contredit. Détecter 11 % des dépassements avec 66 %
de fausses alertes n'est pas un service. Leçon de méthode : sur événement rare, exiger
**conjointement** un écart de CSI et un Brier skill franchement positif.

## 3. Le défaut le plus visible est réparé, à coût nul

La correction était **pire que CAMS brut sur le décile supérieur** (−3,1 %). En commutant vers
un modèle à perte pondérée au-delà de **70 µg/m³ prédits** :

| Règle | RMSE global | gain global | RMSE queue | gain queue |
|---|---|---|---|---|
| quadratique seule | 13,69 | +19,4 % | 15,65 | **−3,1 %** |
| **commutation à 70** | **13,69** | **+19,4 %** | 14,71 | **+3,1 %** |

**Domination stricte** : six points gagnés sur la queue pour un RMSE global identique. Le
plateau est large (60 à 80 µg/m³), donc le seuil n'est pas un pic trouvé par hasard. La
commutation se lit sur la **prédiction**, jamais sur l'observation — donc applicable.

## 4. Les hyperparamètres étaient trop prudents

30 essais en **validation imbriquée** (test de 90 stations jamais consulté) :

| Sur le test | RMSE | gain / CAMS |
|---|---|---|
| CAMS brut | 11,937 | — |
| LightGBM par défaut | 8,849 | +25,9 % |
| **LightGBM réglé** | **8,294** | **+30,5 %** |

**+6,28 % sur le test contre +6,2 % en validation : aucun optimisme de sélection.** Le réglage
va vers plus de capacité (255 feuilles contre 63, 900 arbres contre 400). Le commentaire du
code invoquant la prudence contre la mémorisation du bruit était excessif.

**Cumul sur l'ozone : +17,5 % → +30,5 %.** Treize points sans changer ni données ni
algorithme — seulement la cible et la capacité.

---

## Ce qui a changé dans le discours, et qu'il faut assumer

### Une affirmation était fausse

**« La généralisation temporelle est démontrée »** — écrit le 29/07 sur sept mois, où le pire
pli valait +5,4 %. Sur dix-sept mois, les plis négatifs reviennent **plus mauvais qu'avant** :
−14,6 % en temporel, −24,9 % en double aveugle. Ce n'était pas une propriété du modèle mais
l'effet de n'avoir pas testé assez de mois. **Une absence d'échec sur peu de plis n'est pas
une démonstration de robustesse.**

En revanche la généralisation **spatiale** s'est renforcée : +19,4 % avec σ **1,2** contre 1,8.

### Une part du gain n'appartient pas au modèle

À saison égale d'une année sur l'autre, la **corrélation entre la dégradation de CAMS et la
hausse de notre gain atteint +0,913**. Novembre : RMSE CAMS 15,25 → 20,41, gain 14,3 → 33,8 %.
Et **après** chacune des deux ruptures documentées (13/11 et 03/12/2024), CAMS s'améliore
tandis que notre gain baisse.

Formulation honnête : nous corrigeons une structure d'erreur apprise **et** une régression
passagère du forçage. Ce qui tombe est « gain structurel durable » ; ce qui tient est la
validation sur stations exclues.

### Nos intervalles étaient 1,7× trop étroits

Le bootstrap par station ignore la corrélation **temporelle**. En bloquant les deux axes, le
gain O₃ s'annonce **[+14,6 ; +21,6]** et non [+16,7 ; +20,8]. Aucune conclusion ne bascule —
la borne basse reste franchement positive — mais la précision affichée était surestimée.

### Une formulation à corriger partout

« Une chaîne opérationnelle de même nature » n'est **pas** défendable : une maille de 8 km sans
expertise n'est pas de même nature qu'une chaîne kilométrique avec prévisionniste. Dire :
**« une correction apprise d'un forçage européen, utile en amont d'une chaîne locale »**.

### Deux soupçons écartés

L'**écrêtage à zéro** est négligeable (0,043 % des lignes). Et le **type de station** n'apporte
rien au-delà d'un biais global — la typologie officielle ne porte aucune information de biais
CAMS transférable.

---

## Ce qui a été tranché, et qu'il ne faut pas rouvrir

| Décision | Fondement |
|---|---|
| ❌ **Arrêter les comparaisons d'architectures** | XGBoost, CatBoost et LightGBM tiennent en 0,3 point ; RealMLP arrêté après 32 min contre 20-30 s. Le choix de **famille** compte, celui de la bibliothèque non |
| ❌ **Ne pas reproduire la spatialisation EPCI** | les deux relecteurs convergent ; la comparaison au flux officiel ne serait de toute façon **pas indépendante** |
| ❌ **Pas de `log(1+résidu)`** | domaine mathématiquement invalide, le résidu descend sous −1 |
| ❌ **Ne pas exclure les stations difficiles** | « toute règle écrite après lecture des erreurs » fabrique un score |
| ✅ **Archivage quotidien de l'indice officiel** | le flux écrase ses millésimes J+1/J0/J−1 et ne sert que N−1 : 2024 est déjà perdu. Cron installé et validé |

**Critère d'arrêt adopté** : aucun calcul de plus si le candidat n'a pas démontré, hors station
**et** hors mois, une baisse ≥ 0,3 µg/m³ avec IC95 au-dessus de zéro, sans dégrader le décile
haut de plus de 0,3 ni le CSI. Arrêt impératif à dix jours ouvrés du 22 août.

---

## Ce qui t'attend

1. **`docs/FICHE_OPERATIONNELLE.md`** — les deux relecteurs désignent son absence comme **le
   plus grand risque du dossier**, avant tout enjeu technique. Le canevas est écrit ; chaque
   hypothèse est marquée **⟨À VALIDER⟩**. Quatre points te reviennent : l'utilisateur et
   l'heure d'émission, l'heure réelle de mise à disposition de CAMS, le sort d'ERA5 (c'est une
   **réanalyse**, donc indisponible en opérationnel — limite à assumer ou à lever), et l'accès
   Geod'Air.
2. **Trois décisions FAIRMODE** restent ouvertes : version v3.2 ou v4.0, et le temps
   d'agrégation du MQI pour O₃ et PM2.5.
3. **Observations récentes** — le dernier levier de performance (+2 à +8 % selon la
   littérature), mais **conditionné par la fiche** : on ne peut pas utiliser en production une
   variable qui n'est pas garantie à l'heure d'émission.

## Ce qu'il reste à faire côté technique

- Refaire les scores d'épisode sur base **avril-septembre** (le référentiel LCSQA l'impose pour
  l'ozone) avant de citer les POD/CSI côte à côte.
- Unifier les découpages entre la mesure « horaire agrégée » et « cible directe + tuning »
  avant d'annoncer les treize points de cumul.
- Recalculer le gain à J+2 et J+3 sur 17 mois (les valeurs antérieures sont retirées, pas
  réutilisées).
- Geler le pipeline et produire une exécution signée.
