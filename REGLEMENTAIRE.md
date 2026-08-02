# Référentiel réglementaire — qualité de l'air France / UE

> Établi le 2026-07-28 par vérification en ligne des textes (Légifrance, EUR-Lex,
> guide Atmo France, LCSQA, OMS, EEA, JRC/FAIRMODE).
> **Les valeurs marquées ⚠️ ne sont pas fiabilisées et doivent être revérifiées
> avant tout usage dans un calcul réglementaire.**

---

## 1. Indice ATMO

**Texte :** arrêté du 10 juillet 2020 (JO n°185 du 29/07/2020), pris en application de
l'art. R.221‑5 du code de l'environnement ; abroge l'arrêté du 22/07/2004.
**Guide de calcul :** *Indice ATMO — Guide de calcul*, Atmo France, v. 14/12/2020.

### 1.1 Grandeur retenue par sous-indice

| Polluant | Grandeur |
|---|---|
| PM2.5 | maximum des moyennes journalières sur la zone |
| PM10 | maximum des moyennes journalières |
| NO₂ | maximum des maxima horaires du jour |
| O₃ | maximum des maxima horaires du jour |
| SO₂ | maximum des maxima horaires du jour |

### 1.2 Bornes des classes (µg/m³)

| | Bon | Moyen | Dégradé | Mauvais | Très mauvais | Extrêmement mauvais |
|---|---|---|---|---|---|---|
| PM2.5 | 0–10 | 11–20 | 21–25 | 26–50 | 51–75 | > 75 |
| PM10 | 0–20 | 21–40 | 41–50 | 51–100 | 101–150 | > 150 |
| NO₂ | 0–40 | 41–90 | 91–120 | 121–230 | 231–340 | > 340 |
| O₃ | 0–50 | 51–100 | 101–130 | 131–240 | 241–380 | > 380 |
| SO₂ | 0–100 | 101–200 | 201–350 | 351–500 | 501–750 | > 750 |

### 1.3 Codes couleur officiels

| Qualificatif | Hex | RVB |
|---|---|---|
| Bon | `#50F0E6` | 80, 240, 230 |
| Moyen | `#50CCAA` | 80, 204, 170 |
| Dégradé | `#F0E641` | 240, 230, 65 |
| Mauvais | `#FF5050` | 255, 80, 80 |
| Très mauvais | `#960032` | 150, 0, 50 |
| Extrêmement mauvais | `#872181` | 135, 33, 129 |
| Indisponible (code 0) | `#DDDDDD` | 221, 221, 221 |
| Événement (code 7) | `#888888` | 136, 136, 136 |

### 1.4 Agrégation et territorialisation — **point structurant du projet**

- L'indice de la zone est le **sous-indice le plus dégradé** parmi les cinq.
- Calcul quotidien sur 24 h à partir de **0 h TU**, diffusion au plus tard à 12 h
  locales (tolérance 14 h).
- **Échelle de diffusion : commune ou EPCI**, jamais au-delà du périmètre de l'EPCI.
  L'ensemble des zones doit couvrir intégralement le territoire de l'AASQA.

> ⚠️ **Conséquence méthodologique majeure.** L'indice officiel n'est **pas** calculé
> à partir des mesures de stations : il provient d'une **modélisation méso-échelle
> spatialisée** (maximum modélisé par commune, puis maximum communal pour l'EPCI),
> les mesures ne servant qu'en assimilation ou à défaut. Seules les stations **de
> fond** entrent dans le calcul — jamais les stations trafic.
>
> Un recalcul « depuis les stations » divergera donc **par construction**. L'exercice
> de rapprochement doit être formulé comme la reconstitution d'une **chaîne de
> spatialisation**, ce qui déplace la modélisation spatiale du palier 3 au palier 1.

Absence de modèle disponible → code « indisponible ».
Aucun seuil de couverture temporelle chiffré n'est fixé par l'arrêté pour l'indice
lui-même (contrairement aux valeurs limites, cf. §6) ; en revanche la
**représentativité spatiale** est explicite (points réputés représentatifs de
plusieurs km², niveau maximum de fond).

---

## 2. Seuils d'information-recommandation et d'alerte

**Textes :** art. L.223‑1, R.221‑1 et R.223‑2 du code de l'environnement ;
**arrêté du 7 avril 2016** (JORF n°0084 du 09/04/2016, NOR DEVR1603792A), qui abroge
l'arrêté du 26 mars 2014. Le décret n°2010‑1250 a transposé la directive 2008/50/CE.

| Polluant | Information-recommandation | Alerte |
|---|---|---|
| NO₂ | 200 µg/m³ (horaire) | 400 µg/m³ (horaire) — ou 200 si dépassement la veille et risque le jour même ou le lendemain |
| SO₂ | 300 µg/m³ (horaire) | 500 µg/m³ (horaire, sur 3 h consécutives) |
| O₃ | 180 µg/m³ (horaire) | 240 / 300 / 360 µg/m³ (horaire, seuils progressifs) |
| PM10 | 50 µg/m³ (journalier) | 80 µg/m³ (journalier) |

### 2.1 Critères de déclenchement (arrêté du 7 avril 2016, art. 2)

Deux familles **alternatives** :
- **Superficie** : au moins **100 km²** touchés par un dépassement (O₃, NO₂, PM10) en
  situation de fond, estimé **par modélisation**.
- **Population** : ≥ **10 %** de la population du département s'il compte plus de
  500 000 habitants ; sinon ≥ **50 000 habitants**.
- Clause de situations locales particulières (vallées encaissées ou mal ventilées,
  proximité de voiries à fort trafic, bassins industriels), sans seuil chiffré.
- **SO₂ traité à part** : modalités fixées par arrêté préfectoral local, non
  harmonisées nationalement par le texte de 2016.

### 2.2 Déclenchement sur prévision — **fondement du volet probabiliste**

> « Lorsque le dépassement du seuil est issu d'une modélisation, le déclenchement des
> procédures préfectorales s'effectue **sans attendre la confirmation par mesure**. »

**Persistance** (PM10 et O₃) : dépassement constaté pendant **2 jours consécutifs**
(mesuré aux stations de fond ou modélisé) **et** prévision de dépassement le jour même
ou le lendemain — c'est ce qui fait basculer une procédure d'information en procédure
d'alerte. Les mesures prennent effet le jour même ou le lendemain.

L'AASQA informe le préfet **au moins une fois par jour** (constat + prévision) et tient
informés préfet et ARS (art. 9).

*Le dispositif réglementaire français est donc déjà prédictif : le volet P du projet
calque le fonctionnement réel, il ne le sophistique pas.*

---

## 3. Valeurs limites, valeurs cibles et objectifs de qualité **en vigueur**

Art. R.221‑1 du code de l'environnement, transposant la directive 2008/50/CE.

| Polluant | Objectif de qualité | Valeur cible | Valeur limite |
|---|---|---|---|
| PM10 | 30 µg/m³ annuel | — | 40 µg/m³ annuel ; 50 µg/m³ journalier (max 35 j/an) |
| PM2.5 | 10 µg/m³ annuel | 20 µg/m³ annuel | 25 µg/m³ annuel |
| NO₂ | 40 µg/m³ annuel | — | 40 µg/m³ annuel ; 200 µg/m³ horaire (max 18 dépassements/an) |
| NOx (végétation) | — | — | niveau critique 30 µg/m³ annuel |
| SO₂ | 50 µg/m³ annuel | — | 350 µg/m³ horaire (max 24/an) ; 125 µg/m³ journalier (max 3/an) ; niveau critique végétation 20 µg/m³ |
| O₃ (santé) | 120 µg/m³ (max journalier de la moyenne 8 h) | 120 µg/m³, max 25 j/an moyennés sur 3 ans | pas de valeur limite |
| O₃ (végétation) | AOT40 = 6 000 µg/m³·h | AOT40 = 18 000 µg/m³·h (moyenne sur 5 ans) | — |
| Benzène | 2 µg/m³ | — | 5 µg/m³ annuel |
| Plomb | 0,25 µg/m³ | — | 0,5 µg/m³ annuel |
| CO | — | — | 10 mg/m³ (max journalier, moyenne glissante 8 h) |
| Métaux (dans PM10) | — | As 6 ng/m³, Cd 5 ng/m³, Ni 20 ng/m³, B(a)P 1 ng/m³ | — |

**AOT40** : cumul, entre 8 h et 20 h de mai à juillet, des dépassements horaires d'O₃
au-dessus de 80 µg/m³ (40 ppb). Indicateur de protection de la végétation.

---

## 4. Directive (UE) 2024/2881 — **futur, en cours de transposition**

Adoptée le 23/10/2024, en vigueur depuis décembre 2024. Abroge et remplace les
directives 2004/107/CE et 2008/50/CE.

### 4.1 Valeurs limites applicables au 1ᵉʳ janvier 2030

| Polluant | Annuelle | Journalière | Horaire |
|---|---|---|---|
| PM2.5 | **10** µg/m³ (vs 25) | 25 µg/m³, max 18 j/an *(nouveau)* | — |
| PM10 | **20** µg/m³ (vs 40) | 45 µg/m³, max 18 j/an (vs 50 / 35 j) | — |
| NO₂ | **20** µg/m³ (vs 40) | 50 µg/m³, max 18 j/an *(nouveau)* | 200 µg/m³, max **3 h/an** (vs 18 h/an) |
| SO₂ | 20 µg/m³ *(nouveau)* | ⚠️ 50 µg/m³, max 18 j/an — **valeur contestée** | 350 µg/m³, max 3 h/an (vs 24 h/an) |
| O₃ | — | valeur cible santé 120 µg/m³, max 18 j/an sur 3 ans (vs 25 j) ; ⚠️ objectif long terme 100 µg/m³ | — |
| Benzène | 3,4 µg/m³ (vs 5) | — | — |
| CO | — | 4 mg/m³, max 18 j/an *(nouveau)* | max journalier 8 h glissant maintenu à 10 mg/m³ |

### 4.2 Nouveautés structurelles
- Surveillance de polluants non réglementés (**particules ultrafines, black carbon**)
  sur des « super-sites ».
- Feuilles de route qualité de l'air obligatoires pour atteindre les objectifs 2030.
- **Droit à réparation** pour dommage sanitaire lié au non-respect des normes.
- Report possible jusqu'en 2040 sous conditions (demande avant le 31/12/2028).

### 4.3 Calendrier et état de la transposition

| Étape | Date |
|---|---|
| Entrée en vigueur | décembre 2024 |
| **Transposition en droit national** | **au plus tard le 11 décembre 2026** |
| Application des nouvelles valeurs limites | 1ᵉʳ janvier 2030 (2040 si dérogation) |

**État au 28/07/2026 :** transposition **non achevée**. Groupe de travail trimestriel
piloté par le ministère (AASQA, Atmo France, LCSQA) ; projet de décret et d'arrêté en
consultation jusqu'à fin juin 2026. Aucun texte définitif publié.
⚠️ À reconfirmer sur Légifrance : l'échéance légale est dans moins de cinq mois.

---

## 5. Lignes directrices OMS 2021 — référence **sanitaire**, non contraignante

| Polluant | Annuelle | Court terme |
|---|---|---|
| PM2.5 | 5 µg/m³ | 15 µg/m³ (24 h, 99ᵉ percentile) |
| PM10 | 15 µg/m³ | 45 µg/m³ (24 h, 99ᵉ percentile) |
| NO₂ | 10 µg/m³ | 25 µg/m³ (24 h) |
| O₃ | — | 100 µg/m³ (8 h) ; 60 µg/m³ (pic saisonnier) |
| SO₂ | — | 40 µg/m³ (24 h) |
| CO | — | 4 mg/m³ (24 h) |

Nettement plus strictes que le réglementaire (PM2.5 : 5 OMS vs 25 en vigueur vs 10 en
2030). L'OMS estime que leur respect éviterait ~80 % des décès attribuables aux PM2.5.
Elles ont explicitement inspiré la directive 2024/2881.

---

## 6. Objectifs de qualité des données — **plancher d'erreur irréductible**

Directive 2008/50/CE, annexe I ; transposée par l'arrêté du 16 avril 2021 (annexe 5).

| Polluant | Mesures fixes | Mesures indicatives | Modélisation | Couverture minimale |
|---|---|---|---|---|
| SO₂, NO₂, NOx, CO | **15 %** | 25 % | 50 % (h/8 h), 30 % (annuel) | 90 % |
| Ozone (+ NO/NO₂ associés) | **15 %** | 30 % | 50 % (h/8 h) | 90 % été, 75 % hiver |
| PM10, PM2.5, plomb | **25 %** | 50 % | 50 % (annuel) | 90 % |
| Benzène | 25 % | 30 % | 50 % (annuel) | 90 % |

Incertitudes exprimées en **incertitude élargie, intervalle de confiance 95 %**.

> **À afficher dans toute évaluation de modèle.** L'incertitude admissible sur la
> mesure de référence elle-même est de 15 % pour les gaz et 25 % pour les particules.
> Aucun modèle ne peut sérieusement revendiquer une exactitude supérieure à celle de
> la donnée qui lui sert de vérité terrain.

⚠️ Table reconstituée par recoupement (LCSQA + version consolidée UE) : l'extraction
directe du PDF de l'arrêté du 16/04/2021 a échoué. À relire sur EUR-Lex
(CELEX:32008L0050, annexe I) si une exactitude absolue est requise.

---

## 7. FAIRMODE — MQI / MQO

Cadre méthodologique européen d'évaluation des modèles de qualité de l'air, piloté par
le JRC.

- **MQI** (*Model Quality Indicator*) : rapporte l'écart modèle-mesure à l'incertitude
  de mesure, pondérée par un facteur d'échelle β (usuellement β = 2).
  Principe : `MQI = RMSE / (β × RMSU)`, où RMSU dérive de l'incertitude élargie du §6.
  Avec β = 2, l'objectif tolère un écart allant jusqu'à deux fois l'incertitude de mesure.
- **MQO** (*Model Quality Objective*) : rempli lorsque **MQI ≤ 1 pour au moins 90 %
  des stations** de l'évaluation.
- **Outil :** le *Delta Tool* historique (IDL) est en cours de remplacement par des
  versions Python — *Delta Tool Assessment* et *Delta Tool Forecast*.
  Document de référence : *FAIRMODE WG2 Guidance Document on Modelling Quality
  Objectives and Benchmarking*, v4.0 (13/05/2026).

⚠️ La formule algébrique exacte (définition rigoureuse du RMSU, décomposition du RMSE)
n'a pas pu être extraite des PDF du JRC. Le principe est confirmé par deux sources
indépendantes, mais la formule doit être relue dans `Guidance_MQO_Bench_vs4.0` avant
d'implémenter le critère.

---

## 8. Missions réglementaires d'une AASQA

**Base légale :** art. L.221‑1 à L.221‑3 et R.221‑9 à R.221‑15 du code de
l'environnement ; arrêté du 16 avril 2021 (remplace celui du 19 avril 2017).

- **L.221‑1** — l'État fixe les normes, désigne le LCSQA comme organisme de
  coordination technique, fixe des objectifs pluriannuels de réduction.
- **L.221‑2** — la surveillance couvre l'intégralité du territoire national.
- **L.221‑3** — dans chaque région, l'État confie la surveillance à un **organisme
  agréé** à gouvernance quadripartite (État, collectivités, industriels,
  associations et personnalités qualifiées).

**Missions opérationnelles :**
1. Surveiller et évaluer la qualité de l'air (mesure fixe, indicative, **modélisation**).
2. Informer quotidiennement préfets et public — **constat et prévision**.
3. Calculer et diffuser l'**indice ATMO** (§1).
4. Élaborer les **inventaires régionaux d'émissions**.
5. Contribuer aux programmes de caractérisation chimique des particules.
6. Assurer, via le LCSQA, le **rapportage européen** (données transitant par Geod'Air).

*Les trois volets du projet — réglementaire, connaissances, probabiliste — recouvrent
directement les missions 1 à 4.*

---

## 9. Points à fiabiliser avant usage en calcul

| # | Point | Action |
|---|---|---|
| 1 | VL journalière SO₂ 2030 : 50 (EEA) vs 40 µg/m³ (synthèse CITEPA) | Trancher sur EUR-Lex |
| 2 | Objectif long terme O₃ 2024/2881 (100 µg/m³) | Recouper, source unique |
| 3 | Formule algébrique exacte du MQI / RMSU | Lire `Guidance_MQO_Bench_vs4.0` |
| 4 | Table annexe I (incertitudes / couverture) | Relire EUR-Lex CELEX:32008L0050 |
| 5 | État de la transposition française au jour J | Vérifier Légifrance (échéance 11/12/2026) |
