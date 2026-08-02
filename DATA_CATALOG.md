# Catalogue des sources de données

> Scan réalisé le 2026-07-28 par vérification en ligne. **VÉRIFIÉ** signifie qu'une
> ressource a été effectivement atteinte (fichier téléchargé, endpoint interrogé),
> pas seulement qu'une page de documentation a été lue.
>
> **Couverture du scan : 4 domaines sur 6.** Les domaines *émissions & proxys
> d'activité* et *couches géospatiales vectorielles* n'ont pas été couverts (§7).

---

## 1. Synthèse — chiffres établis

| Fait | Valeur | Statut |
|---|---|---|
| Stations enregistrées (historique complet) | **868**, 18 AASQA | Recalculé depuis « Dataset D » du 09/12/2025 |
| Actives, France entière | **515** | ⚠️ **inclut l'Outre-mer** |
| Actives, **France métropolitaine** | **476** | L'effectif réellement mobilisable |
| Actives, Outre-mer | 39 (Réunion, Antilles, Guyane, Mayotte, Saint-Martin) | À exclure : régime tropical |
| Actives, Occitanie (`NET-FR068A`) | **38** (sur 61 enregistrées) | Recalculé |
| **Stations de fond actives, métropole** | **312** | Base du calcul de l'indice ATMO |
| **Stations de fond actives, Occitanie** | **23** | Base du calcul de l'indice ATMO |
| Stations au portail open data Atmo Occitanie | 58 (périmètre plus large, fenêtre 1 an) | VÉRIFIÉ |
| Profondeur historique fiable | **2013 →** (2002-2012 via Airbase) | VÉRIFIÉ |
| Latence données provisoires (E2a/UTD) | **1 à 2 h** | VÉRIFIÉ empiriquement |
| Latence données validées (E1a) | **30 septembre de l'année N+1** (~9 mois) | VÉRIFIÉ |
| Stations météo France (toutes catégories) | 14 729 référencées / 13 362 ouvertes ; réseau temps réel RADOME = 554 | VÉRIFIÉ (ventilation Occitanie non faite) |

**Le périmètre France → Occitanie est confirmé, et pour la bonne raison.**
En ne comptant que la métropole : **476 / 38 ≈ 12,5**. Et sur le critère qui compte
réellement pour l'indice ATMO — les stations **de fond** — **312 / 23 ≈ 13,6**.
L'entraînement national multiplie donc bien l'effectif utile par plus de dix.
Avec 23 points, l'estimation d'une fonction de transfert spatiale serait exsangue.

> **Trois pièges d'identification vérifiés sur les données réelles :**
> 1. Le chiffre de 515 qui circule **inclut l'Outre-mer**. Les 39 stations tropicales
>    dégraderaient un entraînement métropolitain.
> 2. **Le préfixe du code station n'est pas le département.** `FR34051` est
>    « Chateauroux Sud », dans l'Indre — pas dans l'Hérault. Une sélection régionale
>    par le code produit un jeu silencieusement faux.
> 3. **Une emprise rectangulaire ne délimite pas l'Occitanie** : 8 stations actives
>    d'autres réseaux (Avignon, Arles, Aurillac, Le Puy, Marmande…) tombent dans la
>    boîte englobante. L'appartenance passe par le réseau exploitant ou par une
>    jointure sur le polygone officiel.
>
> **Quatrième point, à traiter :** 39 stations déclarent des classifications
> divergentes selon le polluant (ex. « MEZE TRAFIC » : 4 points *traffic*, 1
> *background*). Le référentiel retient le mode et compte les divergences plutôt que
> de prendre la première valeur rencontrée.

---

## 2. Mesures de concentration

### 2.0 ⚠️ Anomalie critique vérifiée — flux temps réel O₃ rompu depuis le 01/07/2025

**Les séries O₃ du jeu temps réel (`dataset=1`, UTD) s'arrêtent net le 1ᵉʳ juillet 2025
pour la France entière.** Vérifié sur données réelles : 20 des 22 séries d'Occitanie et
8 stations françaises sur 12 tirées au hasard s'interrompent à cette date exacte. NO₂ et
PM2.5 du même flux sont à jour à l'heure près.

Un arrêt simultané et à la minute près sur des dizaines de stations n'est pas une panne
d'instrument : c'est une rupture de chaîne de transmission ou d'ingestion.

> **Conséquence opérationnelle.** Un projet qui se serait appuyé sur le seul flux temps
> réel aurait entraîné un modèle O₃ sur des données absentes depuis plus d'un an, sans
> aucun message d'erreur — les lignes n'existent simplement pas.
>
> **Parade :** l'ozone historique vient du jeu **validé E1a** ; le flux temps réel n'est
> utilisable pour l'O₃ que jusqu'au 30 juin 2025. Croiser avec Geod'Air ou le portail
> Atmo Occitanie pour combler la période récente.

### 2.0 bis — Les trois jeux s'emboîtent : ~25 ans disponibles

| `dataset` | Nom | Période vérifiée | Statut des données |
|---|---|---|---|
| **3** | Airbase historique | **2001 → 2012** | Validées (102 885 h valides sur une station testée) |
| **2** | **E1a validé** | **2013 → 2025-01-01** | Validées — **le corpus d'entraînement** (104 112 h valides sur une station) |
| **1** | UTD temps réel | 2025-01-01 → aujourd'hui | Provisoires · ⚠️ **O₃ rompu au 01/07/2025** |

Les bornes se raccordent presque exactement, et la profondeur réelle (**1999 → aujourd'hui,
27,6 ans**) dépasse largement les 8 ans visés.

> ⚠️ **Trou systématique d'une heure au raccord 2012/2013.** L'heure du
> **2013-01-01 00:00 UTC est absente pour toutes les séries simultanément** :
> Airbase s'arrête à 2012-12-31 23:00, E1a démarre à 2013-01-01 01:00. Vérifié sur
> les 65 séries d'Occitanie — 43 mesures valides à l'heure précédente, 41 à la
> suivante, **zéro** entre les deux. Sans documentation, cela ressemblerait à une
> panne régionale synchronisée.

**Corpus effectivement constitués** (vérifiés, sur disque) :

| Panneau | Stations | Séries | Lignes | Période | Couverture active médiane |
|---|---|---|---|---|---|
| `panel_metropole_ds2` | **430** | 894 | **94 041 648** | 2013 → 2025 | 97,2 % (29/894 sous 75 %) |
| `panel_occitanie_complet` | 32 | 65 | 15 710 045 | **1999 → 2026** | 97,2 % |
| `panel_occitanie_ds2` | 32 | 64 | 6 732 288 | 2013 → 2025 | 98,2 % |

Téléchargement du corpus national : 894 séries et 71,8 M de lignes brutes en **82 s**.

⚠️ **Piège d'implémentation :** le jeu Airbase laisse des valeurs manquantes dans les
colonnes `Validity` / `Verification`. Un cast en entier non nullable échoue ; et une
comparaison sur entier nullable produit `<NA>`, que le masque interpréterait comme
« valide ». Une validité absente doit être traitée comme invalide, jamais l'inverse.

### 2.1 EEA Air Quality Download Service — **point d'entrée recommandé**
- **Producteur :** Agence européenne pour l'environnement
- **Accès :** API REST POST, **aucune authentification** ·
  `https://eeadmz1-downloads-api-appservice.azurewebsites.net/swagger/index.html`
- **Contenu :** `Samplingpoint, Pollutant, Start, End, Value, Unit, AggType, Validity,
  Verification, ResultTime, DataCapture`
- **Pas de temps :** horaire · **Unités :** `ug.m-3` (vocabulaire contrôlé Eionet)
- **Profondeur :** Airbase 2002-2012 · E1a validé 2013 → N-1 · E2a/UTD continu depuis 2023
- **Format :** Parquet · limite 600 Mo/requête, endpoint asynchrone pour gros volumes
- **Latence mesurée :** 1-2 h sur le flux E2a
- **Statut :** **VÉRIFIÉ de bout en bout** (requête POST exécutée, Parquet téléchargé
  et parsé, stations toulousaines identifiées) · **Score 5/5**
- **Atout décisif :** les colonnes `Validity` et `Verification` distinguent nativement
  provisoire et validé — indispensable pour instrumenter le décalage train/production.

### 2.2 Geod'Air (LCSQA / Ineris) — référence nationale
- **Accès :** API REST `https://www.geodair.fr/api-ext` · **inscription + validation
  manuelle**, quota **15 requêtes/heure** · export CSV manuel · fichiers sur data.gouv.fr
- **Contenu :** moyennes horaires, journalières, max horaire journalier, moyennes
  annuelles + métadonnées stations / points de prélèvement / réseaux
- **Unités :** µg/m³, mg/m³ pour CO · **CRS :** EPSG:4326
- **Volumétrie :** ~17 M données/an, > 170 M depuis 2013
- **Licence :** Licence Ouverte 2.0
- **Statut :** VÉRIFIÉ · **Score 5/5**
- ⚠️ **Le quota et la validation manuelle imposent de demander l'accès dès maintenant.**

### 2.3 Métadonnées de stations — « Dataset D » (LCSQA, via data.gouv.fr)
Très riches, et directement exploitables pour la modélisation spatiale :
- coordonnées (EPSG:4326) et altitude ;
- `AreaClassification` : urban / suburban / rural-nearcity / rural-regional / rural-remote ;
- `StationClassification` : background / traffic / industrial ;
- **conditions de dispersion** : distance au carrefour, trafic, largeur de rue,
  hauteur des façades — utilisable directement en micro-échelle urbaine ;
- `ActivityBegin` / `ActivityEnd` par station, avec versions successives horodatées
  en cas de déplacement — permet de tracer les **ruptures de série** ;
- méthodes de mesure et limites de détection par polluant.
- **Statut :** VÉRIFIÉ (fichier .xls de 7,9 Mo téléchargé et parsé)

### 2.4 Atmo Occitanie Open Data (ArcGIS Hub)
- **Accès :** API REST/JSON Esri **sans authentification** + WFS/WMS + export CSV/SHP
- **Contenu :** NO, NO₂, PM10, PM2.5, O₃, CO avec `typologie`, `influence`
  (Fond/Trafic/Industrielle), `statut_valid`
- **CRS :** géométrie Web Mercator, **mais champs `x_l93` / `y_l93` en Lambert-93 fournis**
- **Licence :** ODbL 1.0
- ⚠️ **Profondeur limitée à 1 an glissant** sur le jeu journalier → croiser avec
  Geod'Air ou l'EEA pour l'historique long.
- **Statut :** VÉRIFIÉ (requête réelle exécutée) · **Score 5/5 pour le régional**

### 2.5 Atmo Data / atmo-france.org — ⚠️ **piège de nommage**
Malgré son nom, l'**API REST ne sert pas les concentrations** : uniquement l'indice
ATMO et les sous-indices qualitatifs (1-6) par commune/EPCI, les épisodes de pollution
et les émissions régionales. Jeton JWT valable 1 h, inscription avec validation manuelle.
Les concentrations par station existeraient via les **flux WFS** (`map.atmo-france.org/flux`)
— **non vérifiés**, page dynamique inaccessible. · **Score 2/5** en l'état.

### 2.6 Sources complémentaires
| Source | Verdict |
|---|---|
| **OpenAQ v3** | Clé API **désormais obligatoire** (changement vs v2). Redondant avec Geod'Air/EEA pour la France. Score 2/5 |
| **Sensor.Community** | 521 capteurs actifs en France (VÉRIFIÉ). PM uniquement, non calibrés au sens réglementaire. Densification spatiale possible mais à qualifier. Score 2/5 |

---

## 3. Météorologie

### 3.1 Le problème de l'archive de prévisions — et sa solution

> **Contrainte structurante :** le portail Météo-France ne conserve que **14 jours**
> de sorties AROME/ARPEGE. Impossible d'y entraîner un modèle sur 8 ans.
>
> Or s'entraîner sur des **réanalyses** (ERA5) puis servir sur des **prévisions** crée
> une fuite : le modèle apprend avec une météo parfaite qu'il n'aura jamais en
> production. Il faut de vraies archives de prévisions passées.

| Archive | Période | Contenu | Verdict |
|---|---|---|---|
| **ECMWF IFS ENS** (source.coop / dynamical.org) | **mars 2016 → aujourd'hui** | 51 membres, 0,25°, Zarr/S3, sans authentification | **La trouvaille du scan.** ~10 ans de vraies prévisions d'ensemble |
| **MeteoNet** (Météo-France/CNRM) | 2016-2018 | AROME 2,5 km + ARPEGE 10 km réels, France NO et SE | Haute résolution mais 3 ans seulement |
| **TIGGE** | depuis oct. 2006 | Multi-centres, inclut PEARP | Profondeur maximale, accès à creuser |
| **GEFS Reforecast v12** | 2000-2019 | NOAA, sur AWS S3 | Secours |

⚠️ La disponibilité de la PBLH dans l'archive ECMWF ENS n'est **pas confirmée** — à
tester sur un fichier réel. C'est le point de vérification prioritaire.

### 3.2 ERA5 (Copernicus CDS) — la réanalyse de référence
- **PBLH confirmée :** variable `blh` (code GRIB 159), définie par le nombre de
  Richardson critique 0,25
- **Couverture :** globale, 0,25° · **horaire** · **1940 → aujourd'hui** · latence ~5 jours
- **Unités :** blh en m · T en K · précipitations en **m accumulés** · pression en Pa
  → conversions gérées par `src/aq/harmonize/units.py`
- ⚠️ **Migration effectuée :** un **compte ECMWF** est requis, les anciens identifiants
  CDS sont caducs ; client `cdsapi` à mettre à jour ; le CDS Toolbox a été supprimé.
- **Statut :** VÉRIFIÉ · **Score 5/5**

### 3.3 Autres sources météo
| Source | Points clés |
|---|---|
| **Météo-France API** | Gratuit depuis le 01/01/2024. Compte obligatoire, **quota 50 req/min**. PBLH = paramètre `H_COULIM` (m) dans AROME/ARPEGE. AROME 1,3-2,5 km, 48 h ; ARPEGE 102 h |
| **PEARP** | **35 membres**, ~0,1° (~10 km) — la réponse française pour l'incertitude météo. Doc technique de mars 2025 |
| **ECMWF Open Data** | **Fully open depuis le 01/10/2025**, CC-BY-4.0, 0,25° (0,1° prévu en 2026). ENS 51 membres. PBLH non confirmée |
| **ERA5-Land** | 9 km, horaire, 1950 → présent. Meilleure résolution mais **pas de PBLH** |
| **SAFRAN / SIM2** | 8 km, **quotidien**, 1958-2024. Pas de PBLH ni de vent 3D |

---

## 4. Modèles de chimie-transport et satellite

### 4.1 CAMS — le baseline à battre

| Produit | Résolution | Période | Usage |
|---|---|---|---|
| **Réanalyse régionale européenne** | **0,1°** (~10 km), horaire | **2013 → ~2024** | Entraînement du MOS |
| **Prévisions régionales** | 0,1°, horaire, jusqu'à J+4 | **3 ans glissants seulement** | Évaluation et déploiement opérationnel |
| **EAC4 global** | ~0,75° (~80 km) | 2003 → 2025 | AOD, poussières, conditions aux limites. Trop grossier pour la France |

Ensemble multi-modèles de 9 à 11 systèmes (CHIMERE, EMEP, EURAD-IM, LOTOS-EUROS,
MATCH, MOCAGE, SILAM, DEHM…), produit « ENSEMBLE » = médiane.
Accès ADS, compte gratuit. Volumétrie France 8 ans : quelques dizaines à ~150 Go.

> ⚠️ **Piège de circularité à traiter explicitement.** La réanalyse régionale CAMS
> **assimile les observations de surface EEA** — c'est-à-dire les mesures que le projet
> cherche à prédire. L'utiliser comme variable d'entrée d'un modèle de correction de
> biais est partiellement circulaire : la cible est déjà injectée dans l'entrée. Cela
> gonflerait les scores sans qu'aucune métrique ne le signale.
> **Parade :** privilégier les *prévisions* CAMS (non assimilées pour les dates
> futures), et mesurer explicitement l'écart de performance entre les deux régimes.

### 4.2 PREV'AIR — baseline nationale
- **Accès :** data.gouv.fr, **sans compte**, NetCDF, ~2 km sur la France
- **Polluants :** O₃, NO₂, PM10, PM2.5 — **pas de SO₂**
- Prévision jusqu'à **J+5** (étendu en juin 2024) · modèles CHIMERE + MOCAGE
- Fichiers légers (~1,6 Mo/jour) → quelques Go sur 8 ans
- ⚠️ Profondeur d'archive et CRS exact **non confirmés** — à inspecter dans un NetCDF réel
- **Score 4/5**

### 4.3 Satellite
| Source | Points clés |
|---|---|
| **MODIS MCD19A2 (MAIAC)** | AOD **1 km**, quotidien, depuis 2000. Grille sinusoïdale à reprojeter. Le plus mûr et simple. **Score 4/5** |
| **Sentinel-5P / TROPOMI** | NO₂ à **5,5 × 3,5 km** au nadir (depuis août 2019), revisite quotidienne. Depuis 2017-2018 |
| **VIIRS AOD** | Complément MODIS, résolution native plus grossière hors produit L2 6 km |
| **FIRMS / EFFIS** | Feux actifs (VIIRS 375 m). Pertinence limitée hors événements |

⚠️ **TROPOMI, deux réserves majeures.** (1) La mesure est une **colonne troposphérique**
(mol/m²), pas une concentration de surface : la conversion exige des hypothèses de
profil vertical qui dépendent justement de la couche limite. (2) La **couverture
nuageuse** élimine une large part des pixels, avec des trous fréquents en hiver et sur
le pourtour méditerranéen. → covariable spatiale, jamais vérité de surface. **Score 3/5**

⚠️ **Accès CDSE :** la bascule OpenSearch → STAC/OData était planifiée au 02/03/2026,
donc théoriquement effective. Tout code basé sur OpenSearch serait cassé.
**À tester en conditions réelles avant d'écrire quoi que ce soit.**

---

## 5. Verrous d'accès — actions à engager

| Priorité | Verrou | Action |
|---|---|---|
| **1** | Geod'Air : validation manuelle + quota 15 req/h | **Demander l'accès immédiatement** (délai d'approbation inconnu) |
| **2** | ERA5/CAMS : compte ECMWF requis, anciens identifiants caducs | Créer le compte, mettre à jour `cdsapi` |
| 3 | PBLH dans l'archive ECMWF ENS non confirmée | Tester sur un fichier réel |
| 4 | CDSE : bascule OpenSearch → STAC/OData | Tester avant d'écrire du code Sentinel-5P |
| 5 | Flux WFS Atmo France non vérifiés | `GetCapabilities` dédié |
| 6 | PREV'AIR : archive et CRS non confirmés | Inspecter un NetCDF |

**Aucun verrou bloquant :** l'EEA (sans authentification, vérifié de bout en bout) et
Atmo Occitanie (accès libre) permettent de démarrer immédiatement, pendant que les
demandes d'accès Geod'Air et ECMWF cheminent.

---

## 6. Pièges d'harmonisation identifiés

1. **La définition de « station » varie** : 515 (réglementaire national) vs 38
   (réglementaire Occitanie) vs 58 (portail Occitanie, périmètre élargi). Documenter
   la définition avant toute comparaison.
2. **Unités hétérogènes** : µg/m³ partout **sauf CO en mg/m³**. Vérifier champ par champ.
3. **CRS multiples** : EPSG:4326 (Geod'Air, EEA) · Lambert-93 fourni en parallèle
   (Atmo Occitanie) · sinusoïdale (MODIS) · grille satellite native (TROPOMI).
4. **Unités des réanalyses** : ERA5 donne K, Pa, mètres d'eau accumulés, J/m² accumulés
   — jamais les unités canoniques du projet.
5. **Validation asynchrone par conception** : un point mesuré peut passer de provisoire
   à corrigé lors de la validation de septembre N+1. Le pipeline doit prévoir une
   **ré-ingestion versionnée**, pas traiter l'UTD comme définitif.
6. **Le décalage train/production est de ~9 mois** : entraîner sur du validé et servir
   sur du provisoire crée un décalage de distribution silencieux. À mesurer via les
   colonnes `Validity`/`Verification` de l'EEA.

---

## 7. Couches géospatiales vectorielles (socle S3 — Land-Use Regression)

### 7.1 Couches indispensables

| Source | Contenu | CRS natif | Millésime | Statut |
|---|---|---|---|---|
| **BD TOPO®** (IGN) | Routes, bâti **avec hauteur**, hydrographie, végétation, orographie — trois variables LUR en une source | **EPSG:2154** | Édition **hebdomadaire** (BD TOPO Express depuis mai 2025) | VÉRIFIÉ · 5/5 |
| **BD Forêt® V2** (IGN) | 32 postes : essence dominante, mélange, densité. **UMC 0,5 ha** | EPSG:2154 | ⚠️ **statique 2007-2018** | PARTIEL · 5/5 |
| **RGE ALTI® 5 m** (IGN) | MNT, dalles de 5 km². LiDAR depuis 2010 (précision verticale 0,2-0,5 m) | EPSG:2154 | ⚠️ **mise à jour arrêtée en 2024** | PARTIEL · 4/5 |
| **HISTOLITT®** (SHOM/IGN) | **Trait de côte officiel France**, Méditerranée incluse, > 1/25 000 | **EPSG:2154** | TCHV2 | VÉRIFIÉ · 5/5 |
| **HRL Tree Cover Density** (Copernicus) | % de couvert arboré, **10 m** | EPSG:3035 | **série annuelle 2017-2021** (publiée mai 2025) | VÉRIFIÉ · 4/5 |

> **Le trait de côte est réglé** : HISTOLITT est la référence française, libre, et
> **déjà en Lambert-93** — aucune reprojection avant calcul de la distance à la mer.

> ⚠️ **Limite structurelle de BD Forêt V2.** Ce n'est pas une photographie unique mais
> une **mosaïque de millésimes départementaux étalés de 2007 à 2018**, sans cycle de
> mise à jour et sans indicateur de fraîcheur au niveau du polygone. Pour un LUR daté
> de 2020, certains départements seront décrits par une donnée vieille de plus de dix
> ans, en silence. La **BD Forêt V3** (35 classes, taux de couvert arboré, hauteur de
> canopée) est en production sur 5 départements pilotes depuis juillet 2026, couverture
> nationale visée **2027** : inutilisable pour ce projet.
>
> **Parade retenue :** croiser BD Forêt V2 (composition en essences — indispensable et
> sans substitut pour le potentiel d'émission d'isoprène) avec la série **annuelle**
> HRL Tree Cover Density, qui rafraîchit la densité arborée entre deux millésimes figés.

### 7.2 Couches complémentaires

| Source | Points clés | Score |
|---|---|---|
| **OCS GE** (IGN) | Découverte du scan. Couverture/usage séparés, précision RGE, millésimes **2017-2020 / 2021-2023** + un 3ᵉ en production, cycle **3 ans**. Bien plus fin que Corine et avec un vrai suivi temporel | 4/5 |
| **CLC+ Backbone** (Copernicus) | 11 classes, **10 m**, millésimes 2018 et 2021, cycle 2 ans | 4/5 |
| **HRL Imperviousness** | Imperméabilisation 0-100 %, 10 m, millésime 2018 (2021 non confirmé) | 3/5 |
| **OpenStreetMap** | Mise à jour continue. ⚠️ **Aucun extrait « Occitanie »** : découpage sur les anciennes régions — Midi-Pyrénées (390 Mo) + Languedoc-Roussillon (294 Mo) à fusionner, ou découpe depuis France (4,7 Go) | 3/5 |
| **Corine Land Cover** | Millésimes 1990→**2018**. UMC 25 ha. CLC2024 attendu mi-2026, non disponible. Lacune de 6-8 ans | 3/5 |

### 7.3 À exclure

| Source | Raison |
|---|---|
| **Natural Earth coastline** | ⚠️ **Piège de nommage** : le « 10m » désigne l'échelle **1:10 000 000**, pas 10 mètres. Erreurs de plusieurs kilomètres sur un littoral découpé comme le golfe du Lion et ses étangs — précisément la zone d'intérêt |
| **SRTM** | Obsolète face au Copernicus DEM GLO-30 |
| **EU-Hydro coastline** | HISTOLITT est supérieur et déjà en Lambert-93 |
| **Copernicus DEM GLO-30** | 30 m et MNS (inclut bâti et canopée), pas un MNT. À garder en secours seulement |

### 7.4 Écosystème Python vérifié

| Besoin | Outil retenu | Note |
|---|---|---|
| Extraction OSM régionale | **pyrosm** | ~2,7× plus rapide qu'OSMnx sur une région entière ; OSMnx reste adapté aux requêtes ponctuelles autour d'une station |
| Statistiques zonales | **exactextract** | Les moteurs serial/parallel/dask de `rasterstats` sont **dépréciés**. Gère correctement les pixels partiellement couverts |
| Indices topographiques | **whitebox / WhiteboxTools**, **xDEM** | TPI, `MultiscaleTopographicPositionImage`, `HorizonAngle` (sky view factor). ⚠️ Maintenance de `richdem` non confirmée |
| Distances vectorisées | **Shapely ≥ 2.0** + GeoPandas | STRtree intégré, opérations en ufuncs. `dask-geopandas` au-delà de la RAM |

### 7.5 Verrous et pièges

1. **`cartes.gouv.fr` est une application JavaScript** — le scraping HTML échoue. Passer
   par l'**API Atom de la Géoplateforme** (`data.geopf.fr/telechargement/capabilities`)
   ou les flux WFS/OGC API Features (limite 10 req/s).
2. Plusieurs PDF techniques IGN historiques redirigent en 301 ou sont mal formés.
3. **Copernicus CLMS** (HRL, CLC, CLC+) exige une inscription gratuite.
4. **Trois CRS natifs à réconcilier** : `EPSG:2154` (tout IGN + HISTOLITT) ·
   `EPSG:3035` (tout Copernicus/EEA) · `EPSG:4326` (OSM, DEM natif).
   Reprojection systématique vers Lambert-93 **avant** tout calcul métrique — le λ de la
   décroissance exponentielle doit être en mètres, jamais en degrés.
5. **Volumétrie RGE ALTI 5 m Occitanie : ~25-35 Go** décompressé, 13 départements.
   *Estimation par extrapolation, non officielle.*

---

## 8. Émissions et proxys d'activité

### 8.1 Le diagnostic central — l'écart horaire est confirmé

> **Aucun inventaire d'émissions français actuellement maintenu ne fournit nativement
> de résolution horaire.** CITEPA SECTEN est national et annuel ; l'IGT est communal,
> annuel, et couvre les GES seulement ; l'inventaire régional ATMO Occitanie est annuel
> à la maille EPCI (année de référence 2019). L'ancien **INS** — seul produit français
> qui promettait maille kilométrique *et* résolution horaire — semble **à l'arrêt** :
> site injoignable, dernier millésime identifié 2012. À confirmer auprès d'INERIS/CITEPA
> avant d'en faire une hypothèse de travail.

**Conséquence pour la conception du projet.** L'horaire ne doit pas être traité comme
une propriété de l'inventaire, mais comme le **produit d'un modèle de désagrégation** :

```
émissions horaires ≈ inventaire annuel fin  ×  profils sectoriels génériques
                     (ATMO Occitanie / IREP)   (CAMS-TEMPO)
                   + proxys d'activité réellement horaires (trafic, transport)
```

Les profils CAMS-TEMPO dérivent de GENEMIS (Stuttgart, années 1990), recalés par pays :
le profil de chauffage résidentiel occitan n'est pas le profil allemand générique, et le
trafic local n'est pas la moyenne nationale. **Cette incertitude doit être une limite
méthodologique explicitement énoncée du projet, pas un angle mort.**

### 8.2 Sources retenues

| Source | Contenu | Granularité | Statut |
|---|---|---|---|
| **CAMS-TEMPO** (Copernicus/LSCE/TNO) | Facteurs **mensuels, hebdomadaires et horaires** par secteur GNFR. NetCDF via ECCAD | Europe 0,1°×0,05° | VÉRIFIÉ · **5/5** — le chaînon manquant |
| **IREP / Géorisques** | ~50 polluants air **par établissement géolocalisé, avec tonnages**. ~17 000 déclarants/an | Point · annuel · **depuis 2002-2003** | VÉRIFIÉ · **5/5** |
| **Inventaire régional ATMO Occitanie** | ~50 polluants + 30 GES, méthodo ATMO_IRS_V5 | Commune → EPCI · annuel, réf. 2019 | VÉRIFIÉ · 4/5 |
| **RPG** | Contours de parcelles + **350 cultures précises depuis 2015** | Parcelle (1:5000) · annuel · depuis 2007 | VÉRIFIÉ · 5/5 |
| **INSEE Filosofi** | Population carroyée | **200 m** · millésimes 2015/2017/2019/2021 | VÉRIFIÉ · 4/5 |
| **E-PRTR / portail industriel européen** | Cross-check du registre français, seuils IED/LCP différents | Établissement · annuel · depuis 2007 (⚠️ trou 2005-2006) | PARTIEL · 4/5 |

### 8.3 Proxys d'activité horaires — le vrai signal fin

| Source | Points clés | Score |
|---|---|---|
| **Comptages IoT Upcity, Toulouse Métropole** | **Horaire confirmé** (créneaux `started_at`/`ended_at`), géolocalisé, avec `car_count`, `heavy_vehicle_count`, `bike_count`, `pedestrian_count`. ⚠️ Couverture spatiale réelle non documentée et historique limité à 2024-2025 — **à vérifier en priorité** | **5/5 sous réserve** |
| **Tisséo GTFS-RT** | Temps réel transport urbain, proxy d'activité | 3/5 |
| **transport.data.gouv.fr** | Débits et vitesses toutes les 6 min, mais **réseau national non concédé** — pas la voirie toulousaine intra-muros | 2/5 |
| **Comptages routiers Toulouse (tubes)** | TMJO **hebdomadaire**, capteurs non permanents, depuis 2014 | 2/5 |
| **Enedis Open Data** | Consommation par IRIS/commune et secteur NAF, **annuel** 2011-2024, avec indicateur de **thermosensibilité** | 3/5 |
| **Agreste cheptels** | Communal mais **décennal** (2010, 2020) — faible pour un usage causal fin sur le NH₃ | 4/5 |
| **DJU** | Diffusion gratuite seulement national/régional/départemental. → **calculer soi-même** les degrés-jours à partir des températures de stations, gratuites | 5/5 si recalculé |

### 8.4 ZFE de Toulouse — calendrier pour l'analyse causale

| Date | Mesure |
|---|---|
| **1ᵉʳ mars 2022** | Crit'Air 5 et non classés — **utilitaires et poids lourds seulement** |
| **1ᵉʳ septembre 2022** | Extension Crit'Air 4, même catégorie |
| **1ᵉʳ janvier 2023** | Extension à **tous les véhicules motorisés**, Crit'Air 4, 5 et non classés |
| 1ᵉʳ janvier 2024 | Crit'Air 3 — **SUSPENDUE** (décision métropolitaine, automne 2023). Arrêté non abrogé, aucun calendrier fixé |
| 21 mai 2026 | Le Conseil constitutionnel censure la suppression nationale des ZFE (cavalier législatif) |

Périmètre : intérieur de la rocade + portions de Colomiers et Tournefeuille, ~72 km².

> **Le 1ᵉʳ janvier 2023 est la meilleure quasi-expérience** : c'est la seule étape qui
> touche les véhicules particuliers, donc le gros du parc. Les étapes 2022 ne concernent
> qu'utilitaires et poids lourds — effet attendu plus faible mais non nul sur le NO₂.
> L'étape Crit'Air 3 suspendue offre en prime un **contrôle négatif** : une date
> annoncée puis sans traitement réel, où l'on ne doit observer aucun effet. Trouver un
> effet là serait le signe d'un artefact de méthode.
>
> ⚠️ La date exacte de la délibération de suspension n'a pas été retrouvée au jour près.

### 8.5 Verrous
1. L'**ex-INS** (maille km + horaire) probablement abandonné — à confirmer auprès d'INERIS.
2. Couverture spatiale et profondeur réelles du jeu **Upcity** non documentées.
3. GRDF ne descend pas à la commune (EPCI/département), contrairement à Enedis.
4. Date au jour près de la suspension Crit'Air 3 à retrouver (PV du conseil métropolitain).
