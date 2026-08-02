# Rapport de qualité — mesures Occitanie

> Panneau `data/processed/panel_occitanie_ds2.parquet`
> Jeu **E1a validé**, 2013-01-01 → 2025-01-01 · 64 séries · 32 stations · 6 732 288 lignes
> Généré le 2026-07-28

---

## 1. Vue d'ensemble

| Indicateur | Valeur |
|---|---|
| Stations occitanes actives | 38 |
| Stations mesurant au moins un des trois polluants cœur | **32** |
| Séries station × polluant | 64 (NO₂ 24 · O₃ 23 · PM2.5 17) |
| Profondeur | 12 ans |
| **Couverture médiane sur période active** | **98,2 %** |
| Séries réellement sous 75 % | **1 / 64** |
| Valeurs négatives | 5 212 |
| Plus longue répétition à l'identique | 26 h |

Six des 38 stations actives ne mesurent aucun des trois polluants cœur (elles suivent
SO₂, PM10 ou d'autres composés). Aucune station ne mesure les trois systématiquement :
le panneau est creux **par conception**, pas par défaut de qualité.

---

## 2. Le piège de la couverture — 21 faux positifs sur 22

Un premier calcul rapportant les heures valides à la grille complète signalait
**22 séries sur 64 sous le seuil de 75 %**. Après correction, il n'y en a **qu'une**.

La couverture globale confond trois situations sans rapport entre elles :

| Situation | Nature | Exemple réel |
|---|---|---|
| **Censure à gauche** — instrument pas encore installé | Pas un défaut | *Montpellier Antigone* : 8,2 % sur la grille, **98,4 % sur sa durée de vie** (ouverte en 2024) |
| **Censure à droite** — mesure arrêtée, station toujours active | Fait à documenter | *Perpignan bd Pyrénées* PM2.5 : 99,3 % en actif, mais **arrêt le 13/04/2022** |
| **Trous internes** | Le seul vrai défaut de couverture | *Montpellier Liberté* PM2.5 : **69,0 %**, trou interne de 6 672 h |

Le rapport expose donc deux dénominateurs : `couverture_grille` (position dans le
corpus, utile au dimensionnement) et `couverture_active` (qualité réelle de la mesure).
Le critère réglementaire de couverture ne porte que sur le second.

### Séries réellement dégradées

| Station | Polluant | Couv. active | Trou interne | Lecture |
|---|---|---|---|---|
| Montpellier Liberté | PM2.5 | **69,0 %** | 6 672 h (~9 mois) | Le seul vrai cas sous 75 % |
| Toulouse Mazades | PM2.5 | 77,8 % | **21 977 h (~2,5 ans)** | Interruption longue au milieu de la série |
| Peyrusse Vieille | PM2.5 | 82,9 % | 9 969 h | |
| Perpignan Les Carmes | PM2.5 / O₃ / NO₂ | 88 / 89 / 90 % | ~9 100 h **sur les trois** | Panne simultanée de tous les analyseurs |

*Perpignan Les Carmes* est le cas le plus instructif : un trou de même longueur sur les
trois polluants signale une coupure de site, pas trois défaillances d'instruments.

---

## 3. Anomalies de mesure

**Valeurs négatives — 5 212 occurrences, à conserver.** Elles portent le drapeau
`Validity == 1` : ce sont des données validées par le producteur. Il s'agit du bruit
instrumental normal autour de la limite de détection. Les ramener à zéro fabriquerait un
**biais positif systématique sur les faibles concentrations** — précisément la gamme où
se joue la distinction entre classes *Bon* et *Moyen* de l'indice ATMO.

**Répétitions à l'identique — maximum 26 h.** Une valeur figée plusieurs heures signale
un capteur bloqué, pas une atmosphère stable. Le maximum observé reste modéré ;
*Perpignan Les Carmes* atteint 17 h sur les PM2.5.

**Sentinelle `-999`.** Systématiquement associée à `Validity == -1`, correspondance
parfaite sur l'échantillon. Neutralisée dès l'ingestion. Une station de l'échantillon
temps réel était invalide à 100 % : une moyenne naïve aurait renvoyé −999.

---

## 4. Rupture d'ozone — flux temps réel

**Les séries O₃ du jeu temps réel s'arrêtent au 1ᵉʳ juillet 2025 pour la France entière.**
20 des 22 séries d'Occitanie et 8 stations françaises sur 12 tirées au hasard
s'interrompent à cette date exacte, alors que NO₂ et PM2.5 du même flux sont à jour.

Un arrêt synchrone à l'heure près sur des dizaines de stations n'est pas une panne
d'instrument. L'ozone historique doit venir du jeu validé ; le temps réel n'est
exploitable pour l'O₃ que jusqu'au 30 juin 2025.

---

## 5. Conséquences pour la modélisation

1. **Sélection des séries sur `couverture_active`**, jamais sur la couverture globale —
   sinon on écarte des stations récentes parfaitement saines, et on réduit encore un
   effectif spatial déjà faible.
2. **Les censures à gauche et à droite sont des dates, pas des trous.** Elles doivent
   entrer dans les métadonnées de série, et la validation temporelle doit en tenir
   compte pour éviter d'évaluer un modèle sur une période sans mesure.
3. **Ne jamais écrêter les valeurs négatives.**
4. **Documenter les ruptures de site** (*Toulouse Mazades*, *Perpignan Les Carmes*) :
   une reprise après 2,5 ans d'arrêt peut correspondre à un déplacement ou à un
   changement d'analyseur, donc à une rupture de série qui ressemblerait à une tendance.
