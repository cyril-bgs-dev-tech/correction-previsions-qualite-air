# Comparaison à PREV'AIR — la base appariée

Un tableau de scores dit qui gagne. Il ne permet de recalculer **rien**. Ce dossier porte les
valeurs alignées — **mêmes stations, mêmes jours, les trois systèmes côte à côte** — pour
qu'une AASQA puisse refaire le calcul sur *son* périmètre : ses départements, ses typologies,
ses seuils, sa saison.

## Ce qui est comparé

| | ce que c'est | résolution |
|---|---|---|
| `cams` | la prévision européenne **brute**, telle que reçue | 10 km |
| `prevair` | **AS-CHI** — le produit réellement diffusé par PREV'AIR | 1,7 km |
| `corrige` | **notre sortie** | 10 km corrigés |
| `observe` | la mesure de référence | station |

Le fichier archivé de PREV'AIR porte dans sa métadonnée `CHIMERE combined to surface real
time observations` : c'est leur **adaptation statistique**, avec assimilation et krigeage —
pas leur sortie brute. C'est la référence honnête, et c'est un adversaire plus fort.

## Les fichiers

- **`<P>_apparie.csv`** — une ligne par station × jour, avec le nom de la commune, la position
  et la typologie. C'est la base de travail.
- **`<P>_analyse_apparie.csv`** — la même chose contre leur champ **analysé**, qui a vu les
  observations du jour. C'est un **plafond**, pas un adversaire : aucun système sans
  assimilation ne peut l'égaler, et le comparer à notre prévision serait malhonnête.
- **`../duel_prevair_<P>.csv`** — l'agrégat en trois lignes (biais, RMSE, MAE, corrélation).

## 🔴 Les trois réserves, à lire avant de citer un chiffre

**① La fenêtre est courte, et ce n'est pas réparable.** PREV'AIR n'expose que **six jours
glissants** sur data.gouv.fr. Cette archive s'est constituée jour après jour et **ne peut pas
remonter le temps** — l'archive complète existe à l'INERIS mais n'est pas téléchargeable.
Une vingtaine de jours ne conclut pas : c'est un **ordre de grandeur**, mesuré à armes égales
sur la période disponible.

**② Les deux systèmes connaissent leurs stations.** Les nôtres par l'entraînement, les leurs
par le krigeage. La comparaison est équitable sur ce point précis — aucun des deux n'est
avantagé — mais elle ne dit rien de la performance en un point **non instrumenté**.

**③ Ce ne sont pas des chaînes de même ampleur.** Ils tournent à 1,7 km avec assimilation
d'observations et krigeage ; nous corrigeons un ensemble européen à 10 km. Le dire vaut mieux
que de l'ignorer : l'écart mesuré n'est pas « notre méthode bat la leur », c'est « sur ces
jours et ces stations, notre sortie s'écarte moins de la mesure que la leur ».

## Comment lire l'écart

Les écarts publiés se lisent **dans un seul sens** : de combien *leur* RMSE dépasse *la nôtre*.
Rapportée à la leur, la même réduction s'écrirait autrement — un pourcentage de comparaison
sans son dénominateur est indéfendable.

## Recalculer vous-même

```python
import pandas as pd
d = pd.read_csv("NO2_apparie.csv")

# votre périmètre : par exemple les stations trafic d'Occitanie
d = d[(d.type_station == "trafic") & (d.commune.notna())]

for c in ("cams", "prevair", "corrige"):
    e = d[c] - d.observe
    print(f"{c:9s} biais {e.mean():+6.2f}  RMSE {(e**2).mean()**.5:6.2f}")
```

## Régénérer

```bash
python3 scripts/archiver_prevair.py                          # la fenêtre glissante, chaque jour
python3 scripts/duel_prevair.py --polluant <P> --horizon 2   # J+1
```

⚠️ **`archiver_prevair.py` doit tourner quotidiennement** : ce qui n'est pas archivé un jour
donné est perdu définitivement.
