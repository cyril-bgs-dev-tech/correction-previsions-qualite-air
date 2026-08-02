# Accès aux sources — procédures et actions requises

> État au 2026-07-28. Les procédures ont été vérifiées par test réel (code HTTP
> obtenu, catalogue interrogé) ; les points marqués **ACTION** ne sont pas
> automatisables et doivent être faits manuellement.

---

## 1. Ce qui fonctionne déjà, sans aucune démarche

| Source | Accès | État |
|---|---|---|
| **EEA Air Quality Download** | API REST POST, aucune authentification | ✅ **En production** — 94 M de lignes ingérées |
| **Métadonnées stations (Dataset D, LCSQA)** | Téléchargement direct data.gouv.fr | ✅ **En production** — référentiel construit |
| **PREV'AIR** | data.gouv.fr, sans compte | Non encore exploité |
| **Atmo Occitanie (ArcGIS)** | API REST/JSON libre | Non encore exploité |

---

## 2. Copernicus — ERA5 (météo) et CAMS (qualité de l'air)

### 2.1 ACTION requise — création de compte

Aucune de ces étapes n'est automatisable en ligne de commande.

1. Créer un compte sur **`https://www.ecmwf.int/user/register`** *(HTTP 200 vérifié)*.
   Un **compte unique** dessert les deux services : l'authentification passe par un
   SSO Keycloak commun *(redirection HTTP 302 vérifiée)*.
2. Se connecter séparément sur les deux portails et y relever le **jeton d'accès
   personnel** (même compte, deux pages de profil) :
   - CDS — `https://cds.climate.copernicus.eu/`
   - ADS — `https://ads.atmosphere.copernicus.eu/`
3. **Accepter les licences, jeu par jeu**, via l'interface web. C'est le point le plus
   facile à oublier : le compte ne suffit pas, chaque jeu de données a sa propre
   licence à accepter en bas de son formulaire de téléchargement.
   - `reanalysis-era5-single-levels` (CDS)
   - `cams-europe-air-quality-reanalyses` (ADS)

### 2.2 Deux pièges de configuration

**Les deux services ont des URL d'API distinctes**, alors que `~/.cdsapirc` n'en porte
qu'une. Un projet qui interroge les deux doit instancier le client explicitement — ce
que fait `src/aq/ingest/copernicus.py` :

| Service | URL |
|---|---|
| CDS (ERA5) | `https://cds.climate.copernicus.eu/api` |
| ADS (CAMS) | `https://ads.atmosphere.copernicus.eu/api` |

**L'ancien format d'identifiant `UID:API-KEY` ne fonctionne plus.** La clé est
désormais un unique *personal access token*.

### 2.3 Bibliothèque

`pip install "cdsapi>=0.7.7"` — version actuelle **0.7.7** (30/09/2025), et celle que
référencent les guides officiels des deux portails. `ecmwf-datastores-client` (0.5.1)
existe mais reste en pré-1.0 et n'est pas le client documenté.

### 2.4 Ce qui est déjà vérifiable sans compte

Le catalogue est un **STAC public** : les noms de variables, les contraintes et les
formulaires de requête se lisent sans authentification. C'est ainsi que le format des
requêtes du module a été validé.

| Test | Résultat |
|---|---|
| `GET .../api/catalogue/v1/collections/reanalysis-era5-single-levels` | **200** — JSON STAC complet |
| `GET .../api/catalogue/v1/collections/cams-europe-air-quality-reanalyses` | **200** |
| `POST .../retrieve/v1/processes/<jeu>/execution` sans clé | **401** |

### 2.5 Volume et découpage

Découpage **mensuel obligatoire** — recommandation explicite du fournisseur (« submit
small requests… download one month at a time rather than requesting entire years »).
Les limites sont exprimées en nombre de champs, et une requête pluriannuelle passe
derrière les requêtes modestes dans la file d'attente.

Pour la France métropolitaine, 6 à 8 variables ERA5, horaire, 2013-2025 :
2 745 points de grille × 105 192 pas de temps × 6 variables ≈ **1,73 milliard de
valeurs**, soit ~6,9 Go en float32 brut, plutôt **3-4 Go** avec la compression NetCDF
habituelle. Réparti en **144 fichiers mensuels**. Volume sans difficulté.

⚠️ **CAMS ne propose ni découpage géographique ni sélection horaire** : le domaine
européen entier est livré, mois par mois. Le recadrage sur la France se fait localement.

---

## 3. Geod'Air (LCSQA) — à demander sans attendre

**ACTION** : demander l'accès à l'API sur `https://www.geodair.fr/donnees/api`.
L'inscription requiert une **validation manuelle** de délai inconnu, et le quota est de
**15 requêtes par heure**. À engager tôt, même si l'EEA couvre déjà le besoin principal.

Utilité propre : c'est la source qui fait autorité en France, et la seule à porter à la
fois les mesures et les métadonnées réglementaires complètes.

---

## 4. Rappel des pièges déjà vérifiés sur données réelles

1. **Le flux temps réel O₃ est rompu depuis le 01/07/2025** pour la France entière.
   L'ozone historique doit venir du jeu validé E1a.
2. **La réanalyse CAMS assimile les observations de surface EEA** — donc la cible que
   le projet prédit. L'employer comme variable d'entrée d'un modèle de correction de
   biais est partiellement circulaire.
3. **L'emprise ERA5 s'écrit `[Nord, Ouest, Sud, Est]`**, et non dans l'ordre usuel
   d'une bbox. L'intervertir renverrait une zone vide, sans erreur.
