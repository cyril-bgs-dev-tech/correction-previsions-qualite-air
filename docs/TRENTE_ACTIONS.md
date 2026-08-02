# Les 30 prochaines actions — arrêté au 31/07/2026

*Ordonné par valeur décroissante. Chaque ligne porte ce qui l'enterrerait, faute de quoi ce
n'est pas une action mais une intention.*

Rappel du cadre : échéance **22 août 2026**, arrêt des calculs dix jours ouvrés avant. Critère
d'arrêt du projet — gain ≥ 0,3 µg/m³, IC95 > 0, sans dégrader le décile haut de plus de 0,3 ni
le CSI. **Ce critère est reconnu défectueux** entre polluants d'échelles différentes : le lire
aussi en relatif.

---

## A — Consolider ce qui est acquis *(1-8, priorité absolue)*

| # | Action | Coût | Ce qui l'enterrerait |
|---|---|---|---|
| 1 | **Intégrer l'observation à J−2 au modèle du dossier** et régénérer `VERITE_DOSSIER` — c'est le plus fort levier mesuré et il n'est dans aucun livrable | 2 h | rien : le gain est établi sur trois polluants, IC95 tous positifs |
| 2 | **Publier la distinction des deux périmètres** — A « corriger aux stations » avec observations, B « prédire là où rien ne mesure » sans. Ne jamais citer l'un pour l'autre | 1 h | rien ; c'est une exigence d'honnêteté, pas un résultat |
| 3 | **Republier `figures.html`** — jamais confronté à sa version en ligne, et l'écart local/publié s'est déjà produit une fois | 1 h | la version en ligne est identique |
| 4 | **Traiter les 7 signalements bloquants restants** de `AUDIT_COHERENCE.md` | 2 h | ils sont déjà corrigés — à vérifier un par un |
| 5 | **Ajouter la dispersion d'ensemble comme pastille de méfiance** dans la présentation, pas comme prédicteur | 1 h | — |
| 6 | **Régénérer le manifeste** et vérifier qu'aucun rapport n'est antérieur à son script | 20 min | tout est déjà vert |
| 7 | **Geler la version d'envoi** — étiquette, PDF, liste datée de ce qui n'est pas inclus | 1 h | — |
| 8 | **Relire les pages 1 à 5** de la présentation contre `VERITE_DOSSIER` — elles datent d'avant les résultats de détection | 2 h | aucun chiffre ne diverge |

## B — La météo prévue, priorité de mesure *(9-14)*

Grok la classe premier levier ; son avertissement tient lieu de garde-fou : *« 168 Go d'IFS sans
**un** tableau leave-station sur grandeur réglementaire »* serait du travail pour rien.

✅ **Débloqué le 31/07.** La piste était déclarée infaisable — 17 échecs pour 16 pas, 94 h
extrapolées. Mesure du débit réel : **le service accepte 288 requêtes/minute sans limite**, les
rejets étant aléatoires. Mes temporisations de 8 à 40 s étaient l'unique goulot. Après
correction : **0 échec sur 40 pas, 1,2 Go en 56 s** → moins de deux heures pour 17 mois.

Et le regroupement des plages embarque **les 13 niveaux de pression gratuitement** — vent,
température, géopotentiel, humidité. Le vent en couche mélangée et le Richardson bulk
deviennent calculables sans requête supplémentaire.

| # | Action | Coût | Ce qui l'enterrerait |
|---|---|---|---|
| 9 | ✅ **Un mois d'IFS extrait** — 77 colonnes, dont 13 niveaux de pression | fait | — |
| 10 | **Étendre à la fenêtre complète** puis mesurer le gain contre le plafond ERA5 (+7,8 % O₃) | 2 h | la météo prévue rend moins de la moitié du plafond : le conditionnement ne survit pas au passage réanalyse → prévision |
| 11 | **Comparer IFS et AIFS** sur les mêmes stations et dates — un modèle neuronal lisse-t-il au point d'être un moins bon conditionneur d'un maximum ? | 3 h | les deux donnent le même gain à 0,05 près : la question n'a pas d'objet |
| 12 | **Mesurer la dégradation avec l'échéance** J+1 → J+3, seul chiffre qui dise si la piste tient en exploitation | 2 h | le gain s'effondre dès J+2 |
| 13 | **Vérifier si les grandeurs dérivées** — ventilation, Richardson — apportent au-delà du vent à 10 m, dont l'apport marginal n'est que +0,067 | 3 h | elles n'ajoutent rien : six champs de surface suffisent, et le lot passe de 168 Go à une fraction |
| 14 | **Encadrer par la météo persistée** — borne basse sans aucun téléchargement, à comparer au plafond ERA5 | 2 h | — |

## C — Étendre ce qui a marché *(15-21)*

| # | Action | Coût | Ce qui l'enterrerait |
|---|---|---|---|
| 15 | **Membres d'ensemble pour NO₂ et PM2,5** — seul O₃ est téléchargé | 4 h | la dispersion est nulle comme prédicteur sur O₃ ; ne le faire que pour la pastille de méfiance |
| 16 | **Feux sur O₃** — mesuré seulement sur PM2,5 | 1 h | l'ozone photochimique ne devrait pas répondre aux panaches : un gain serait suspect |
| 17 | **Détection à budget égal sur PM2,5 hors échantillon**, comme fait sur O₃ | 2 h | — |
| 18 | **Rejouer davantage de matinées** — trois font une illustration, une saison ferait une preuve | 6 h | — |
| 19 | **Modéliser les PM10**, polluant qui a déclenché l'épisode du 25/07 et que le projet ignore | 8 h | les données PM10 s'arrêtent au 01/01/2025 : vérifier la source avant |
| 20 | **Observations récentes sur le test 2025** — l'usage A n'y a jamais été mesuré | 2 h | — |
| 21 | **Étendre l'observation J−2 aux trois horizons** J+1, J+2, J+3 : sa valeur décroît sûrement | 2 h | le gain disparaît à J+3 — auquel cas le dire |

## D — Diagnostiquer plutôt qu'optimiser *(22-26)*

| # | Action | Coût | Ce qui l'enterrerait |
|---|---|---|---|
| 22 | **Diagnostiquer le 25/07/2026** : clé FIRMS ou couches EFFIS, puissance radiative du 23 au 27, comparée aux dates d'émission | 3 h | aucun feu en amont : l'hypothèse tombe, et c'est une poussière |
| 23 | **Récupérer les PM10 de juillet 2026** pour le rapport granulométrique — poussière minérale ou fumée ? | 2 h | — |
| 24 | **Cartographier les jours où la correction dégrade** un CAMS déjà bon — distribution, pas anecdote | 3 h | — |
| 25 | **Vérifier la stabilité du seuil de décision** entre mois, par origine glissante interne à 2024 | 2 h | l'écart-type des seuils dépasse 5 µg/m³ : le point de fonctionnement est instable |
| 26 | **Exploiter l'archive de l'indice ATMO** — capturée depuis le 30/07, jamais analysée : couverture, trous, cohérence des millésimes | 3 h | — |

## E — Ce qui appartient à l'entretien, pas au dossier *(27-30)*

| # | Action | Coût | Pourquoi ce n'est pas du calcul |
|---|---|---|---|
| 27 | **Fiche opérationnelle** : quelles entrées sont garanties à l'heure d'émission, et **qui opère la bascule si une source manque à 3 h du matin** — question posée par la relecture, jamais traitée | — | décision de service |
| 28 | **Six questions pièges préparées** : ERA5, temporel faible, 21 stations, MQI, « pourquoi pas PREV'AIR », POD officiel supérieur | 3 h | oral |
| 29 | **Le budget de fausses alertes réel** d'ATMO Occitanie — la relecture le situe à 20-40 % en interne, bien moins en communication publique | — | à leur demander |
| 30 | **Le grain horaire du NO₂** : un prévisionniste regarde-t-il ces séries pour décider ? Si non, notre +2,7 % n'a aucune valeur opérationnelle | — | question à poser, pas à résoudre |

---

## Ce qui est écarté, mesuré, et ne doit pas revenir

- **Modèle spécialiste « feu »** ou « journées anormales » : le dédié perd (14,70 contre 13,32).
  Un garde-fou coûte moins et fait le même travail.
- **Classification, perte pondérée, quantile** comme améliorations de détection : nuls dès que
  le seuil est libre.
- **Copolluants et chimie inter-espèces** : deux formulations testées, les deux nulles.
- **Architectures alternatives, spatialisation EPCI, exclusion des stations difficiles,
  recherche exhaustive d'hyperparamètres** : tranchés de longue date.
- **Aurora en inférence** : exige des conditions initiales 3D globales. En veille, pas en
  chantier — mais la question *« son avantage survit-il au grain réglementaire ? »* vaut d'être
  posée en entretien.

## Trous déclarés

- **Novembre 2023** des membres d'ensemble : deux échecs HTTP 400 consécutifs, rejet persistant
  du service. Un mois d'automne absent de toute mesure saisonnière.
- **GFAS s'arrête au 03/12/2025** et quitte l'ADS le 04/12 : ne couvre pas juillet 2026.
- **PM10 s'arrêtent au 01/01/2025** : le test granulométrique de l'épisode est impossible en
  l'état.
