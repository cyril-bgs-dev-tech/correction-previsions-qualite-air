# Fiche opérationnelle — émission, entrées, décision, repli

> **Statut : canevas à valider.** Les deux relectures externes du 30/07 désignent l'absence
> de cette fiche comme **le plus grand risque du dossier**, avant tout enjeu technique
> (`GPT_R6.md` Q30, `GROK_R5.md` Q43-44). Elle fixe simultanément quatre choses : la
> **légalité** des observations récentes comme prédicteurs, l'**horizon** utile, le **coût
> relatif** d'une alerte manquée face à une fausse alerte, et la **métrique principale**.
>
> Tout ce qui est marqué **⟨À VALIDER⟩** est une hypothèse que je ne peux pas trancher :
> elle relève d'un choix métier ou d'une vérification auprès de l'AASQA. Ne pas les
> présenter comme établies en entretien.

---

## 1. Qui, quoi, quand

| | |
|---|---|
| **Utilisateur** | ⟨À VALIDER⟩ le prévisionniste d'astreinte de l'AASQA, qui valide l'indice du lendemain avant publication |
| **Décision servie** | ⟨À VALIDER⟩ retenir, corriger ou écarter l'indice prévu par la chaîne, zone par zone — **aide à l'expertise**, pas automatisation |
| **Heure d'émission visée** | ⟨À VALIDER⟩ avant **13 h locale**, l'indice officiel étant publié « du jour et du lendemain » vers **14 h** (Atmo France) |
| **Horizon** | **J+1** en priorité — le seul évalué sur 17 mois ; J+2 et J+3 mesurés, dégradation faible |
| **Ce que le produit n'est pas** | un système d'alerte automatique. Voir §5 |

## 2. Entrées, et leur disponibilité réelle à l'heure d'émission

C'est le point qui décide de tout le reste : **une variable non garantie à l'émission ne peut
pas entrer dans le modèle de production**, quelle que soit sa valeur prédictive mesurée.

| Entrée | Garantie à 13 h ? | Fondement |
|---|---|---|
| Prévisions **CAMS Europe** J+1 | ⟨À VALIDER⟩ oui | run quotidien ; **l'heure exacte de mise à disposition reste à confirmer** sur le catalogue ADS |
| Météo prévue | ⟨À VALIDER⟩ oui | notre chaîne utilise ERA5, qui est une **réanalyse** — donc **indisponible en opérationnel**. Il faudrait une prévision météo, non testée à ce jour |
| Variables statiques (paysage, relief, trafic, population) | **oui** | invariantes ; extraites une fois |
| Calendrier | **oui** | déterministe — et c'est notre variable la plus utile (+9,1 %) |
| **Observations récentes** de la station | **non garanties** | le temps réel O₃ de l'EEA est **rompu pour la France depuis le 01/07/2025**. Une source nationale (Geod'Air) est à instruire |

**Deux conséquences immédiates.**

D'abord, l'usage d'ERA5 est une **limite de transférabilité** que le dossier doit énoncer :
la performance mesurée suppose une météo de qualité réanalyse, alors qu'un système réel
n'aurait qu'une météo prévue. L'écart n'est pas mesuré. ⟨À VALIDER⟩ le refaire avec une
prévision météo serait le test le plus honnête, hors périmètre du temps restant.

Ensuite, les observations récentes — que la littérature désigne comme le levier restant le
plus crédible — exigeraient **deux produits** : l'un avec, l'autre en repli sans. Sans flux
garanti, seul le second est livrable.

## 3. Ce que le produit sort réellement — deux quantités, pas une

Les mesures du 30/07 ont changé la réponse à cette question. Le produit ne doit pas sortir
une concentration corrigée seule, mais **deux quantités de nature différente** :

| Sortie | Comment | Pour quoi |
|---|---|---|
| **Concentration corrigée** sur la grandeur réglementaire du jour | apprise **directement** sur cette grandeur (max 8 h pour O₃, max horaire pour NO₂) — et non par agrégation d'une correction horaire, ce qui coûtait 5,8 à 6,5 points | renseigner une valeur, alimenter une carte |
| **Probabilité de dépassement** du seuil | classifieur dédié, calibré (Brier skill **+0,460**) | décider s'il faut regarder |

C'est la seconde qui rend le service. Une régression optimise une erreur **moyenne** : elle
sous-annonce structurellement les dépassements — biais de fréquence 0,43 à 0,68 selon la
variante. Le classifieur atteint **1,09**, c'est-à-dire une annonce non biaisée.

### La métrique principale

⟨À VALIDER⟩ **POD, FAR et CSI sur la grandeur réglementaire**, jamais le RMSE global.

Justification mesurée : la correction améliore 57,9 % des heures mais seulement **16,2 %**
changent de classe d'indice. Un gain de concentration n'est pas un gain de service. Le
référentiel LCSQA applicable depuis le 01/01/2022 impose d'ailleurs POD, FAR, SR, FB et CSI,
avec 75 % de couples disponibles, et évalue l'ozone d'**avril à septembre**.

Le RMSE reste un diagnostic interne, jamais un argument principal.

### Le point de fonctionnement — à choisir, pas à subir

⟨À VALIDER⟩ Le seuil de probabilité décide de l'arbitrage. Mesuré sur O₃ à 120 µg/m³ :

| Seuil | POD | FAR | CSI | Lecture |
|---|---|---|---|---|
| p ≥ 0,10 | **0,737** | 0,466 | 0,448 | on manque un quart des épisodes, une alerte sur deux est fausse |
| p ≥ 0,20 | 0,663 | 0,393 | **0,464** | meilleur compromis au sens du CSI |
| p ≥ 0,50 | 0,493 | 0,264 | 0,419 | prudent : peu de fausses alertes, un épisode sur deux manqué |

Ce choix n'est pas technique : il dépend du coût d'une alerte manquée face à celui d'une
fausse alerte, qui relève de la communication préfectorale et non de la statistique. **Aucun
ratio universel n'est publié** — c'est une politique locale.

## 4. Repli — que fait-on quand une entrée manque

| Panne | Comportement attendu |
|---|---|
| CAMS indisponible | **pas de sortie.** La correction est un post-traitement : sans forçage, il n'y a rien à corriger |
| Météo dégradée ou partielle | ⟨À VALIDER⟩ sortie produite, **signalée comme dégradée** ; l'ampleur de la perte n'est pas mesurée |
| Observations récentes absentes | bascule sur le modèle **sans observations** — celui qui est validé aujourd'hui |
| Station nouvelle, jamais instrumentée | fonctionne : c'est la **généralisation spatiale**, notre résultat le plus solide (+19,4 %, σ 1,2) |
| Mois atypique | **risque assumé** : le pire pli temporel donne −14,6 %, et −24,9 % en double aveugle. Un réentraînement glissant est la parade ⟨À VALIDER⟩ |

## 5. Ce que nous ne signons pas

À dire avant qu'on ne le demande — c'est ce qui rend le reste crédible.

- **Pas d'alerte automatique.** Le rappel des jours « Mauvais » passe de 0,24 à 0,47 : plus
  d'un épisode sur deux reste manqué.
- **Pas de pic de NO₂.** Sur le maximum horaire, le POD est de 0,015 et le biais de fréquence
  de 0,04 — sous-annonce d'un facteur 20. Une maille de 8 × 11 km ne résout pas un bord de route.
- **Pas l'indice officiel.** Le nôtre est calculé **en station**, sur trois polluants ;
  l'officiel est spatialisé commune → EPCI et en porte cinq.
- **Pas un gain garanti sur un mois inconnu.** Voir le repli ci-dessus.
- **Pas une amélioration du système d'ATMO.** Nous corrigeons un **forçage européen** à 8 × 11 km,
  utile **en amont** d'une chaîne locale — pas une chaîne kilométrique avec prévisionniste.

## 6. La phrase d'usage, à tester en entretien

> ⟨À VALIDER⟩ « À 13 h, avant la publication de l'indice du lendemain, le prévisionniste voit
> pour chaque zone deux choses : le maximum 8 h d'ozone corrigé, et la **probabilité** que le
> seuil de 120 µg/m³ soit franchi. Là où cette probabilité dépasse le seuil qu'ATMO a choisi,
> il sait qu'il doit regarder. Le produit ne décide pas — il **oriente l'attention**. Sur nos
> mesures, il fait passer la détection des dépassements d'ozone d'**un tiers à deux tiers**,
> et son annonce n'est plus biaisée. »

Les chiffres sont mesurés sur 17 mois et 270 stations **exclues de l'entraînement** : POD de
0,345 (correction horaire agrégée) à **0,663** (classification à p ≥ 0,20), biais de fréquence
de 0,43 à **1,09**, Brier skill **+0,460**.

**La phrase à ne pas prononcer** : « nous détectons les épisodes ». Un POD de 0,663 laisse un
tiers des dépassements hors du filet, et c'est sur l'ozone — le cas favorable. Sur le NO₂
horaire, le POD reste sous 0,06 : les pics de proximité routière échappent à une maille de
8 × 11 km, et aucun post-traitement ne les inventera.

---

## Ce qu'il reste à faire porter par Cyril

1. Trancher les ⟨À VALIDER⟩ du §1 — utilisateur, décision, heure.
2. Vérifier l'heure réelle de mise à disposition de CAMS Europe sur le catalogue ADS.
3. Décider si l'on assume ERA5 comme limite énoncée, ou si l'on tente une météo prévue.
4. Instruire l'accès Geod'Air, seule voie vers un flux d'observations garanti.
