# Cinquième revue — remplacer, réduire pour comparer les échéances, séparer les périmètres

## A — Remplacer la table, mais pas par la table `core7` actuelle sans un dernier garde

### Verdict

Je choisis l'option **1 — remplacer**. La table 29 mois n'est pas une sensibilité recevable :
elle contient un défaut de support identifié et reproduit. Elle peut rester dans l'historique
d'audit sous l'étiquette « invalidée », pas à côté du résultat principal comme une estimation
alternative de même statut.

En revanche, je ne publierais pas encore la table `core7` telle quelle. Le garde ajouté
contrôle parfaitement la spéciation, mais pas les autres familles de la pile. L'anomalie O3
révèle un second trou de support matériellement décisif.

### Ce qui arrive réellement à O3

La baisse de `15,83 %` à `9,07 %` de la pile sans spéciation n'est pas produite par la seule
composition des cinq mois de test retirés :

| calcul O3 sans spéciation | gain |
|---|---:|
| passe longue, 29 plis | +15,83 % |
| **mêmes modèles**, mais score limité aux 24 plis 2024–2025 | **+17,43 %** |
| modèles réajustés sur le corpus `core7`, 24 plis | **+9,07 %** |

Retirer les cinq mois de test augmente donc le score de `+1,60` point. La chute vient du
réajustement sans 2023 (`−8,36` points), et presque entièrement d'un seul pli : **juillet
2025**.

Sur ce pli, le fichier mensuel des membres CAMS n'existe pas. Les sept colonnes `ens_*` sont
entièrement manquantes au test. Dans le corpus long, novembre 2023 était également absent et
fournissait au train des exemples de cette branche de repli ; le filtre `core7` le retire.
Les résultats du pli sont alors :

| configuration O3, juillet 2025 | RMSE | gain contre CAMS |
|---|---:|---:|
| base + typologie | 11,68 | +8,15 % |
| **+ membres** | **28,79** | **−126,48 %** |
| pile sans spéciation | 25,51 | −100,62 % |
| pile avec spéciation | 20,28 | −59,54 % |
| pile sans membres | 10,46 | +17,75 % |

Sans ce pli — diagnostic d'influence, **pas** nouvelle estimation à publier — la pile
`core7` passe de `9,07 → 15,41 %` à `17,48 → 20,50 %`. L'apport relatif de la spéciation
reste positif, mais revient de `+6,97 %` à `+3,66 %`. Le triplement apparent de l'apport O3
est donc largement l'effet d'une spéciation qui amortit un modèle rendu aberrant par les
membres manquants.

Le contrôle des fichiers montre que le problème dépasse ce pli :

| famille, fenêtre 2024–2025 | couverture observée | décision |
|---|---|---|
| spéciation `core7` | 24/24 mois, après retrait commun du 01/01/2024 | conserver |
| GEOS-CF v1 | 24/24 mois | conserver à J+1 |
| membres NO2/O3 | 23/24 mois ; juillet 2025 absent | exclure ou compléter avant mesure |
| membres PM10 | 12/24 mois ; toute l'année 2024 absente | exclure |
| membres PM2,5 | 24/24 mois | techniquement complet |
| feux | 14/24 mois ; dix mois absents en 2025 | exclure ou compléter |

Le même principe appliqué à GEOS-CF puis à la spéciation doit s'appliquer ici : un mois
entièrement absent ne doit pas devenir un code d'époque. Garder les membres pour PM2,5 mais
pas pour les autres créerait en plus quatre piles principales différentes à la veille de la
livraison. La solution la plus courte et la plus auditable est donc une pile J+1 commune à
support complet : **base + typologie + GEOS-CF + tendance + `core7`**, sans membres ni feux.
Il suffit de rejouer les deux configurations avec/sans spéciation, pas les seize étages.

Deux défauts de métadonnées sont à corriger dans le même passage, sans en faire des résultats :

- les rapports NO2, O3 et PM2,5 annoncent encore `2023-08→2025-12`, `29 plis prévus` et
  `5 écartés`, alors que leurs fichiers par pli contiennent bien 24 mois de 2024-01 à
  2025-12 ;
- le fichier par pli PM2,5 ne contient que 11 des 16 configurations après reprise. Les deux
  configurations nécessaires au contraste sont présentes, mais cela reproduit exactement
  le défaut de checkpoint décrit dans la revue 4.

### Test et seuil fixés avant cette dernière passe

1. Construire les 24 plis sur les mêmes clés station–jour pour les deux configurations.
2. Exiger **zéro valeur manquante dans toutes les familles incluses**, pas seulement dans
   `core7`, 24 plis exécutés sur 24 et un fichier par pli complet.
3. Calculer le gain total et l'apport relatif de la spéciation par RMSE pondérée par
   `n_test`, bootstrap circulaire de 10 000 tirages par blocs de trois mois, sensibilité à
   six mois, puis Holm sur les quatre polluants.
4. Conserver l'attribution à la spéciation si le point est `≥ 2,0 %` relativement à la pile
   sans spéciation, la borne basse IC95 est `> 0`, Holm `< 0,05` et la décision est identique
   avec les blocs de six mois.
5. Pour O3, publier en plus les deux strates fixées maintenant : avril–septembre et
   octobre–mars. Si le retrait d'un seul mois déplace le gain annuel de plus de `2,0` points
   ou si l'IC95 total dépasse 10 points de largeur, le chiffre annuel ne paraît jamais seul :
   l'influence maximale et les deux saisons l'accompagnent.

Une plage formée par les deux anciens corpus ne serait pas un intervalle : l'un est invalide
et les modèles n'ont pas le même train. Le bon objet est le point `core7` propre accompagné
de son IC et, pour O3, des strates saisonnières préspécifiées.

### Décimales

La règle simple est : arrondir d'abord l'incertitude à deux chiffres significatifs, puis
l'estimation au même rang décimal. C'est notamment la règle de présentation du
[NIST GLP 9](https://www.nist.gov/system/files/documents/2019/05/14/glp-9-rounding-20190506.pdf).
Avec les intervalles observés ici, tous les gains principaux doivent être publiés à **une
décimale** : `+15,4 %`, pas `+15,41 %`. Les valeurs non arrondies restent dans les CSV.

### Ce qu'on écrit dans les deux issues

**Si la passe propre franchit les seuils :**

> Sur un support commun complet de 24 mois, la pile J+1 réduit le RMSE de [gain, IC95] par
> rapport à CAMS. L'ajout des sept traceurs de composition améliore la même pile sans
> spéciation de [apport relatif, IC95]. Les intervalles sont appariés par cycles mensuels et
> restent conditionnels à une pile sélectionnée sur ce corpus. Pour O3, la variabilité
> saisonnière est publiée séparément.

**Si le garde de support ou le seuil d'apport échoue :**

> Nous ne disposons pas d'une estimation publiable de l'apport de la spéciation pour
> [polluant] sur une pile à support complet. L'ancienne valeur est retirée ; aucune variante
> supplémentaire n'est sélectionnée sur ce corpus.

### NO2 et U10

Le résultat `core7` renforce la décision de **ne pas utiliser U10 comme veto** : sur le test
principal actuel, l'apport relatif NO2 vaut `+2,08 %`, IC95 bloc 3 `[1,49 ; 2,70]`, avec
22/24 plis positifs. Ces chiffres restent provisoires jusqu'à la pile sans familles trouées,
mais ils rendent moins plausible une instabilité générale.

U10 doit néanmoins rester visible. La formulation correcte devient :

> L'apport NO2 est stable sur l'épreuve double aveugle commune ; une sensibilité temporelle
> limitée à l'époque U10 rend un point négatif. Cette discordance borne la transférabilité
> récente du résultat, sans invalider le test principal ni justifier une ablation post-hoc.

## B — Balayer une pile réduite et fixe ; ne pas télécharger les trois tranches

### Verdict

Le balayage à pile réduite est utile et publiable, à condition de le nommer correctement :
il teste la **stabilité avec l'échéance d'une pile commune**, pas celle de la meilleure pile
J+1. Je le ferais. Je ne téléchargerais pas les trois tranches de spéciation.

La raison est décisive : ces 3,5 heures et 24 Go ne résoudraient pas le problème annoncé.
Même avec la spéciation aux quatre horizons :

- les membres ont été demandés uniquement pour leur tranche J+1
  ([`lot_membres_ensemble.py`](../scripts/lot_membres_ensemble.py)) ;
- GEOS-CF est joint par jour depuis une sortie J−1. Pour une cible J+2 ou J+3, cette sortie
  n'est pas disponible à l'origine CAMS correspondante ; l'utiliser ainsi serait une fuite
  d'heure d'émission ;
- les feux ont des mois entiers absents.

Acheter la spéciation seule produirait donc encore quatre piles différentes. Le coût ne peut
pas répondre à la question « pile complète à toutes les échéances ».

### Pile et protocole

La pile commune doit contenir seulement :

`totaux CAMS + terrain/calendrier + typologie + tendance récente de CAMS`.

La tendance est calculable séparément à chaque horizon à partir des sorties antérieures de
ce même horizon ; elle ne contient aucune observation locale. Membres, feux, GEOS-CF,
spéciation et veille sont exclus de ce balayage.

Le test exact est :

1. prendre l'intersection des clés `station × jour valide` disponible aux quatre horizons,
   sur une fenêtre identique ;
2. imposer les mêmes groupes de stations, les mêmes mois de test, la même graine, les mêmes
   hyperparamètres et les mêmes colonnes aux quatre horizons ;
3. entraîner un modèle distinct par horizon, car la relation résiduelle peut changer, mais
   ne changer aucun élément de la recette ;
4. publier RMSE CAMS, RMSE corrigée et
   `G_h = 100 × (1 − RMSE_corrigée,h / RMSE_CAMS,h)` ;
5. rééchantillonner les quatre horizons **ensemble** avec les mêmes tirages par cycles de
   trois mois, sensibilité à six mois.

La grandeur primaire par polluant est directement celle de l'affirmation :

`R = max(G_J0, G_J+1, G_J+2, G_J+3) − min(G_J0, G_J+1, G_J+2, G_J+3)`.

Le gain total de cette pile fixe est le bon objet. Un marginal de famille répondrait à une
autre question et redeviendrait dépendant de la composition de la pile.

### Seuil préenregistré et multiplicité

Le seuil reste celui déjà annoncé, sans l'assouplir après J+3 : stabilité si le point
`R < 1,0` point **et** si la borne supérieure unilatérale à 95 % de `R` est `< 1,0`, avec
le même verdict sous blocs de six mois.

Si le point est inférieur à 1 mais que sa borne supérieure le dépasse, la stabilité est
**indéterminée**, donc non établie. Si la borne inférieure dépasse 1, elle est réfutée.

Il n'y a pas seize tests. Les quatre horizons composent une seule statistique de plage par
polluant : la famille contient donc **quatre tests**, un par polluant. Pour quatre conclusions
individuelles, appliquer Holm à ces quatre tests unilatéraux. Pour la seule phrase globale
« stable sur les quatre polluants », exiger que les quatre passent ; cette intersection est
plus stricte et ne permet pas qu'un succès compense un échec.

Le statut est `sensibilité_préenregistrée — stabilité_échéance`. J+3 était non consulté et
peut falsifier la prédiction, mais cette expérience ne confirme pas la pile complète, qui
n'est pas celle évaluée.

Coût recommandé : **zéro téléchargement**, environ 2 h de garde/protocole et moins d'une
heure de calcul si les quatre polluants tournent en parallèle. Le résultat ne déclenche aucun
réglage par horizon.

### Ce qu'on écrit dans les deux issues

**Si les quatre tests passent :**

> Sur une pile réduite identique et un support station–jour commun, l'amélioration relative
> contre CAMS varie de moins d'un point entre J0 et J+3 pour les quatre polluants, borne
> supérieure d'incertitude comprise. Ce résultat soutient la stabilité avec l'échéance de la
> correction du biais de site ; il ne décrit pas la pile enrichie propre à J+1.

**Sinon :**

> Le critère préenregistré d'équivalence à un point n'est pas satisfait pour [polluant]. La
> stabilité avec l'échéance de la pile commune n'est pas établie [ou : est réfutée si la
> borne inférieure dépasse un point]. Aucun réglage spécifique à l'horizon n'est sélectionné
> sur cette épreuve.

## C — Deux panneaux de comparaison ; aucune fausse persistance `PARTOUT`

### Verdict

La persistance observationnelle ne doit pas figurer comme concurrent de la ligne principale
`PARTOUT`. Un tiret dans une grande table pousse malgré tout à lire les autres cellules comme
comparables. Il faut publier deux panneaux autonomes, avec un dénominateur et un périmètre
propres :

| panneau | systèmes comparables sur exactement les mêmes lignes |
|---|---|
| **PARTOUT** | CAMS brut ; pile commune corrigée ; éventuellement persistance du champ CAMS |
| **AUX STATIONS** | persistance observationnelle FAIRMODE ; CAMS brut ; pile `PARTOUT` restreinte aux mêmes stations ; éventuelle pile avec veille |

Le panneau AUX STATIONS ne sert pas à classer le produit `PARTOUT`. Il répond à une autre
question : que gagne-t-on là où une observation locale existe ? La phrase actuelle devient :

> À J+1 et au périmètre AUX STATIONS, CAMS brut fait moins bien que la persistance
> observationnelle au critère FAIRMODE sur 41,4 % des stations NO2 ; la correction satisfait
> le critère sur 96,2 % des stations évaluées.

FAIRMODE présente bien ses indicateurs de prévision comme comparés à un « persistence
model » ([WG3 Forecast 2026](https://knowledge4policy.ec.europa.eu/fairmode/quality-control-indicators-aq-forecasts-work-group-3_en)).
Cette référence est construite à partir de l'observation disponible à l'émission ; elle ne
devient pas spatiale parce qu'on l'affiche à côté d'un modèle spatial.

### La persistance du champ CAMS

Une référence sans observation locale est possible, mais il faut la nommer
**« persistance du champ CAMS »** ou **« champ CAMS initial maintenu »**, jamais simplement
« persistance » ni « persistance FAIRMODE ».

La définition opérationnelle défendable est : prendre, à chaque point, le dernier champ CAMS
spatial effectivement disponible à l'heure d'émission et le maintenir jusqu'au jour cible.
Elle mesure si la nouvelle prévision et sa correction battent le choix naïf « l'état du champ
ne change pas ». Elle constitue une référence interne pertinente pour la tendance récente,
mais je n'ai pas trouvé de source qui l'établisse comme substitut standard à la persistance
observationnelle FAIRMODE. Le choix d'une référence de skill doit de toute façon être déclaré :
l'[ECMWF](https://confluence.ecmwf.int/spaces/FUG/pages/673551834/Section%2B12.A%2BStatistical%2BConcepts%2B-%2BDeterministic%2BData)
rappelle que persistence, climatologie ou système alternatif sont des références possibles
et que le score dépend de ce choix.

### Test et seuil d'admission

Avant de l'afficher, construire pour chaque ligne un manifeste
`champ source → heure d'émission → jour cible`. La référence est admise si :

- `heure_disponibilité_source <= heure_émission` sur **100 %** des lignes ;
- aucune observation locale ni réanalyse future n'entre dans le champ ;
- les quatre horizons utilisent la même règle fondée sur l'origine, pas un décalage naïf du
  jour cible qui lirait le futur à J+2/J+3 ;
- elle est évaluée sur exactement les mêmes clés que CAMS et la pile commune.

Ce seuil est un garde de définition, pas un seuil de performance. Une référence peut être
mauvaise et rester utile ; elle ne peut pas être indisponible au moment prévu.

### Ce qu'on écrit dans les deux issues

**Si le manifeste passe :**

> La persistance du champ CAMS est une référence interne spatialement complète : le dernier
> champ disponible à l'émission est maintenu jusqu'à la cible. Elle ne requiert aucune
> observation locale et ne doit pas être confondue avec la persistance FAIRMODE.

**S'il échoue :**

> Aucune persistance sans observation locale n'est utilisée : la construction candidate
> emploierait une information indisponible à l'émission ou changerait de définition selon
> l'horizon. Les résultats de persistance restent confinés au panneau AUX STATIONS.

La bonne présentation n'essaie donc pas de remplir toutes les cellules. Elle montre deux
produits honnêtes, chacun contre les références réellement définies dans son périmètre.
