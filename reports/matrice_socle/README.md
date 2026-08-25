# Les prédictions du socle — valeurs réelles, station par station, jour par jour

**C'est le modèle que le dossier revendique.** Pour chaque station et chaque jour :
la mesure de référence, la prévision européenne brute, et notre sortie.

| colonne | |
|---|---|
| `observe` | la mesure de référence (µg/m³) |
| `cams` | la prévision européenne **brute**, telle que reçue |
| **`corrige`** | **notre sortie**, celle qu'on propose d'utiliser |

Plus `nom`, `commune`, `typologie_zone`, `type_station`, `lat_wgs84`, `lon_wgs84`,
`altitude`, `metropole` — pour qu'un identifiant devienne un lieu.

| | lignes | stations | mois | fenêtre | gain |
|---|---:|---:|---:|---|---:|
| NO₂ | 105 823 | 344 | 33 | 2023-09 → 2026-07 | **+41,09 %** |
| O₃ | 84 806 | 271 | 33 | 2023-09 → 2026-07 | **+19,44 %** |
| PM10 | 93 617 | 317 | 32 | 2024-01 → 2026-08 | **+23,67 %** |
| PM2,5 | 74 515 | 236 | 34 | 2023-09 → 2026-07 | **+14,54 %** |

## ✅ Ces fichiers reproduisent le chiffre du dossier — recalculez-le

Le `gain_pct` de `resume.csv` est calculé **depuis ces colonnes seules**, et il retombe sur la
valeur publiée à la deuxième décimale. Rien à croire sur parole :

```python
import pandas as pd, numpy as np
d = pd.read_parquet("NO2_socle_Jplus1.parquet")
r = lambda a, b: np.sqrt(np.mean((a - b) ** 2))
print(100 * (1 - r(d.observe, d.corrige) / r(d.observe, d.cams)))   # → 41.09
```

## 🔴 Ce que ces valeurs sont, et ce qu'elles ne sont pas

**Ce ne sont pas des prévisions opérationnelles.** Ce sont les sorties du modèle dans le
protocole du dossier — **chaque point est prédit par un modèle qui n'a vu ni sa station, ni son
mois.** C'est plus dur qu'un déploiement réel, où le passé de la station serait connu ; c'est
la condition qui permet de dire que le chiffre vaut **là où rien ne mesure**.

**Le grain est le jour**, pas l'heure. La cible est la grandeur réglementaire de chaque
polluant — moyenne journalière, ou maximum journalier de la moyenne glissante 8 h pour l'ozone.

**L'échéance est J+1**, et elle est **dérivée** par `aq.rapport.libelle_echeance`, jamais
écrite à la main : le nom de fichier `mos_<P>_J<h>.csv` porte l'**horizon**, pas l'échéance, et
ce projet a appelé « J+1 » du J0 pendant des semaines à cause de ce nom.

## ⚠️ Il existe une seconde matrice, et ce n'est pas une autre version

`reports/matrice_predictions_2026/` publie les sorties de la chaîne **horaire** — plus fine en
temps, bâtie sur le post-traitement **de base**, et son `resume.csv` annonce **+19,2 %** sur le
NO₂. Les deux sont justes.

| | cette matrice | la matrice horaire |
|---|---|---|
| **grain** | **journalier** | horaire |
| **modèle** | le **socle** — huit familles | post-traitement de base |
| **protocole** | double aveugle — station **et** mois cachés | spatial — station cachée, mois connu |
| **période** | 32 à 34 mois, propre à chaque polluant | l'année 2026 en continu |
| **répond à** | *de combien peut-on corriger, partout ?* | *que prédit-on, ici, à cette heure ?* |

> **Confondre les deux discrédite le dossier plus sûrement qu'un chiffre faux** : un chiffre
> faux se corrige, une confusion de périmètre jette le doute sur tout le reste.

## ⚠️ Les quatre polluants ne se comparent pas entre eux

Leurs fenêtres diffèrent, et sous ce protocole deux fenêtres différentes n'ont même pas les
mêmes lignes de test — la rotation des groupes de stations est indexée sur le **rang** du mois.
Comparez les écarts mesurés sur les **mêmes** lignes, jamais les niveaux entre colonnes.

Et les niveaux se citent **arrondis** — ≈ 41 · ≈ 19 · ≈ 24 · ≈ 15 % : l'enveloppe mesurée vaut
**0,7 à 3,0 pt** selon le polluant.

*Régénérable : `python3 scripts/matrice_socle.py`. Format Parquet zstd, un fichier par
polluant, plus un extrait CSV de 2 000 lignes lisible sans outil.*
