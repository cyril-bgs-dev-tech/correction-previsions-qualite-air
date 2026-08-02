# Le test décisif : le terrain apporte-t-il plus que la position ?

## Pourquoi cette question était la seule qui restait

PREV'AIR corrige déjà ses sorties par apprentissage, puis les spatialise par **krigeage à
dérive externe** — la dérive étant le champ CHIMERE lui-même. La correction apprise n'est
donc pas une contribution : c'est l'architecture de la chaîne de référence.

La seule chose que ce projet pouvait encore revendiquer, c'était d'apporter des
**covariables physiques que cette chaîne n'utilise pas** : relief, occupation du sol,
réseau routier. Une note LCSQA de 2005 indique qu'altitude et occupation du sol n'étaient
pas opérationnelles dans PREV'AIR ; la littérature établit la complémentarité entre modèle
de chimie-transport et covariables de paysage (de Hoogh et al., 2016,
DOI 10.1016/j.envres.2016.07.005), mais **pas le gain marginal face à une interpolation
spatiale des résidus**, qui est, elle, déjà en place.

D'où ce test : si l'interpolation seule fait aussi bien, l'angle s'effondre.

## Le protocole

Stations **entièrement cachées**, quatre plis, ozone J+1, 577 589 paires, 270 stations.
Tous les prédicteurs reçoivent exactement la même information d'entraînement ; seul change
ce qu'ils en font.

| Prédicteur | Ce qu'il utilise en plus de CAMS |
|---|---|
| résidu interpolé | la **position** des stations d'entraînement (distance inverse) |
| apprentissage sans terrain | CAMS, calendrier, coordonnées |
| apprentissage avec terrain | + relief, forêt par essence, réseau routier |
| hybride | terrain **et** résidu interpolé |

## Le résultat

| Prédicteur | RMSE | R² | Gain / CAMS |
|---|---|---|---|
| CAMS brut | 17,58 | +0,529 | — |
| CAMS + résidu interpolé (position seule) | 15,79 | +0,620 | +10,2 % |
| CAMS + apprentissage sans terrain | 13,89 | +0,706 | +21,0 % |
| **CAMS + apprentissage avec terrain** | **12,58** | **+0,759** | **+28,4 %** |
| CAMS + terrain + résidu interpolé | 13,37 | +0,728 | +24,0 % |

**Gain marginal du terrain face à l'interpolation seule : +20,3 %**, intervalle de
confiance à 95 % **[+17,7 ; +23,2]**, obtenu par bootstrap sur les **stations** —
**100 % des tirages sont positifs**.

## Ce que cela établit, et ce que cela n'établit pas

**Établi.** Ce que le terrain dit d'une station n'est **pas réductible à sa position**.
L'interpolation spatiale ne capte que 10,2 % de l'erreur de CAMS, là où les covariables
en captent 28,4 %. Sur des stations jamais vues, connaître le relief et l'occupation du
sol autour d'un point vaut nettement mieux que connaître ses voisines.

**Non établi.** Le gain face au krigeage **opérationnel de PREV'AIR**, qui utilise le
champ CHIMERE comme dérive — un champ physique bien plus informatif qu'une distance
inverse entre stations. Ce test compare le terrain à une **interpolation nue**, pas à la
chaîne réelle. La comparaison honnête exigerait les sorties PREV'AIR elles-mêmes.

## Le résultat inattendu : l'hybride est moins bon

Ajouter le résidu interpolé au modèle qui a déjà le terrain le **dégrade** — 24,0 % contre
28,4 %. C'est le même phénomène que la forêt dans l'étude d'ablation : une information
redondante et bruitée sur laquelle le modèle surajuste.

Autrement dit, **le terrain contient déjà ce que le voisinage apporte, et davantage**.
L'ajouter ne complète pas, il perturbe.

## Ce qu'il faut en dire

*Les covariables de paysage apportent trois fois plus que l'interpolation spatiale seule,
et l'écart est robuste. Mais la comparaison qui compterait vraiment — face au krigeage à
dérive CHIMERE de PREV'AIR — reste à faire, et demanderait leurs sorties.*

C'est une hypothèse **falsifiable et partiellement falsifiée en sa faveur**, pas une
démonstration de supériorité opérationnelle.
