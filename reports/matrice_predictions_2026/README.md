# Matrice de prédictions 2026 — les valeurs, pas les scores

Un pourcentage dit *combien* le système gagne. Il ne dit pas *ce qu'il prédit*. Cette
matrice porte les valeurs elles-mêmes, station par station et heure par heure, pour que
n'importe qui puisse **recalculer nos chiffres sans nous croire sur parole** — et regarder
les cas où la correction échoue autant que ceux où elle réussit.

## Les colonnes

| colonne | ce que c'est |
|---|---|
| `station_id` · `nom` · `commune` | le point de mesure, nommé — pas seulement un code |
| `lat_wgs84` · `lon_wgs84` · `altitude` | sa position |
| `typologie_zone` · `type_station` | urbain / périurbain / rural, et trafic / fond / industriel |
| `polluant` · `echeance` | l'espèce et l'échéance, **dérivée** et non recopiée (voir plus bas) |
| `timestamp_utc` | l'heure de validité, en UTC |
| **`observe`** | la mesure de référence, µg/m³ |
| **`cams`** | la prévision européenne brute, telle que reçue |
| **`corrige`** | **notre sortie** — celle qu'on propose d'utiliser |

Les trois dernières côte à côte suffisent à recalculer RMSE, biais, corrélation, taux de
dépassement, ou n'importe quel critère — le vôtre compris.

## L'échéance, et pourquoi elle est dérivée

Les fichiers sources s'appellent `mos_<polluant>_J<h>.csv` où **`h` est l'horizon, pas
l'échéance** : `J1` y désigne l'horizon 1, c'est-à-dire **J0**. Ce projet a appelé « J+1 »
du J0 pendant des semaines à cause de ce nom. La colonne `echeance` de cette matrice est
donc **calculée** par `aq.rapport.libelle_echeance`, jamais écrite à la main.

**Tout ce qui est publié ici est à J+1** — les heures 25 à 48 d'une sortie de 00 UTC.

## Ce que ces valeurs ne sont pas

Ce ne sont **pas** des prévisions opérationnelles produites en temps réel. Ce sont les
sorties du modèle sur la période évaluée, rejouées dans le protocole du dossier : un point
donné est prédit par un modèle qui **n'a pas vu ses observations**. C'est la condition de
déploiement — prévoir là où personne ne mesure — et c'est ce qui rend ces valeurs
comparables à une prévision réelle plutôt qu'à un ajustement a posteriori.

## Formats

- **`<P>_Jplus1.parquet`** — la matrice complète. Compression zstd ; se lit en une ligne :
  ```python
  import pandas as pd
  d = pd.read_parquet("NO2_Jplus1.parquet")
  ```
- **`<P>_Jplus1_extrait.csv`** — les 2 000 premières lignes, pour regarder sans outil.
- **`resume.csv`** — une ligne par polluant : effectifs, période, RMSE avant/après, biais.

> 💡 **Pas besoin de cloner le dépôt.** GitLab sert chaque fichier individuellement :
> `.../-/raw/main/reports/matrice_predictions_2026/NO2_Jplus1.parquet` télécharge le seul
> polluant qui vous intéresse.

## Régénérer

```bash
python3 scripts/fit_mos.py --polluant <P> --horizon 2     # les prédictions
python3 scripts/matrice_predictions.py --horizon 2 --annee 2026
```

## Licence et réserves

Code sous MIT. Les **observations** proviennent du dispositif national de surveillance
(LCSQA / AASQA) et les **prévisions brutes** du service Copernicus CAMS : leurs conditions
d'usage respectives s'appliquent, et ce dépôt ne les redistribue pas au-delà de ce qui est
nécessaire pour vérifier les chiffres publiés.
