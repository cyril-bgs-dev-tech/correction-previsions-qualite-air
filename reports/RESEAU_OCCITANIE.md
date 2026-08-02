# Où le réseau sait, et où il devine

**Une lecture du réseau de surveillance d'Occitanie, à partir de données publiques.**
Analyse indépendante — 2 août 2026.

---

## Ce que ce document est, et ce qu'il n'est pas

Il **n'évalue pas** la chaîne de prévision d'Atmo Occitanie. Nos prédictions corrigent
**CAMS Europe**, pas CHIMERE ; nous ne disposons ni de la configuration régionale, ni de
l'adaptation statistique en place depuis 2023, ni de l'expertise des prévisionnistes.

Il **ne calcule pas** une aire de représentativité spatiale au sens de la décision
d'exécution (UE) 2026/1208, applicable au 30 juin 2028. Celle-ci se détermine par
modélisation, avec une tolérance sur les concentrations. Ce que nous proposons est un
**indicateur de prédictibilité**, obtenu par l'autre bout : *que saurait-on de ce lieu si
l'on n'y mesurait pas ?*

Il propose trois lectures chiffrées, destinées à éclairer des décisions d'évolution du
réseau, et il donne la méthode pour les rejouer.

**Sources.** Archive de l'indice publié par Atmo Occitanie (47 300 jours-zone, 164 EPCI,
335 jours) ; répertoire national des stations ; prévisions CAMS Europe et observations
réglementaires LCSQA sur 36 mois.

**Réserve d'emprise.** L'analyse retient les stations situées à moins de 60 km d'un
centroïde d'EPCI d'Occitanie — 123 stations. Ce tampon inclut **délibérément** des postes
de régions voisines (Pau, Lacq, Avignon, Brive, Le Puy…), parce qu'une station frontalière
informe la prédiction en Occitanie. Ce n'est donc pas la liste du réseau d'Atmo Occitanie,
et les postes hors région sont signalés comme tels dans le fichier détaillé.

---

## ① L'indice publié est, à 86 %, un indice d'ozone

Part des jours-zone où chaque sous-indice fixe la classe finale — calculée sur l'archive
publiée, en répartissant les ex æquo plutôt qu'en attribuant arbitrairement le maximum :

| sous-indice | part pilote |
|---|---|
| **O₃** | **86,0 %** |
| PM2,5 | 8,2 % |
| NO₂ | 3,2 % |
| PM10 | 2,5 % |
| SO₂ | 0,1 % |

**La décision que cela éclaire.** Tout effort portant sur la qualité de l'indice publié se
joue presque entièrement sur l'ozone. Une amélioration de la prévision NO₂ ou PM10, même
importante en concentration, ne déplacera la classe affichée que dans 3 à 6 % des
jours-zone.

C'est aussi une tension à documenter : les **procédures préfectorales** de 2025 se sont
déclenchées à 36 reprises sur les PM10 contre 12 sur l'ozone. L'indice quotidien et
l'alerte réglementaire ne sont donc pas pilotés par le même polluant — ce sont deux
produits distincts, et un gain sur l'un ne se transfère pas à l'autre.

---

## ② Un quart des intercommunalités n'a aucun point de mesure à moins de 30 km

| indicateur | valeur |
|---|---|
| distance médiane d'un EPCI au poste le plus proche | **19,2 km** |
| quartile supérieur | 30,7 km |
| maximum | **71,9 km** (CC Pyrénées Cerdagne) |
| EPCI sans station à moins de 30 km | **43 sur 164** |

Les dix plus éloignés :

| km | EPCI | poste le plus proche |
|---|---|---|
| 71,9 | CC Pyrénées Cerdagne | Perpignan St-Esteve |
| 64,5 | CC Capcir Haut-Conflent | Perpignan St-Esteve |
| 57,2 | CC Cœur de Lozère | Millau |
| 56,8 | CC Cazals-Salviac | Brive-Dalton |
| 54,5 | CC Randon-Margeride | Vals-près-le-Puy |
| 54,4 | CC de la Vallée du Lot et du Vignoble | Agen |
| 53,0 | CC du Gévaudan | Millau |
| 52,1 | CC du Causse de Labastide-Murat | Umicore Viviez |
| 51,7 | CC Pyrénées Audoises | Pamiers |
| 51,6 | CC Mont Lozère | Alès-Cévennes |

Le motif est net : **le relief**. Cerdagne, Capcir, Gévaudan, Mont Lozère, Aubrac,
Pyrénées Audoises — les zones les moins couvertes sont montagneuses, et ce sont aussi
celles où un modèle à maille kilométrique représente le plus mal la circulation locale.

**La décision que cela éclaire.** L'abaissement des valeurs limites au 1ᵉʳ janvier 2030
déplace l'enjeu du pic vers la cartographie fiable à basse concentration, sur l'ensemble du
territoire. Les EPCI ci-dessus sont ceux où l'estimation repose aujourd'hui le plus sur le
modèle et le moins sur la mesure.

---

## ③ L'information du réseau est concentrée dans les stations trafic

Voici le résultat le plus utile. Pour chaque station, nous mesurons l'erreur du modèle
**lorsque cette station est entièrement cachée de l'apprentissage** : ni son historique, ni
son biais propre ne sont connus. C'est la situation d'un lieu non instrumenté.

**NO₂ — 38 stations, RMSE médiane 11,66 µg/m³** (CAMS brut : 21,36) :

| RMSE station cachée | station | type |
|---|---|---|
| **6,41** | Peyrusse-Vieille | fond, rural éloigné |
| 7,18 | Castres stade Travet | fond, urbain |
| … | | |
| 38,75 | Montpellier Antigone | **trafic**, urbain |
| 41,96 | Perpignan bd Pyrénées | **trafic**, urbain |
| **51,30** | Montpellier Liberté | **trafic**, urbain |

**Un facteur huit entre les deux extrêmes.** Et le classement est presque parfaitement
ordonné par typologie : les stations de fond rural sont largement **interchangeables** —
leurs voisines suffisent à reconstituer leur signal ; les stations **trafic** portent une
information que rien d'autre dans le réseau ne fournit.

Le mécanisme est cohérent avec ce que nous mesurons par ailleurs : une maille de 8 × 11 km
ne distingue pas un site trafic d'un site de fond distants de 400 m. Ajouter la typologie
de station aux prédicteurs rapporte **+8,9 points** sur le NO₂ — précisément parce qu'elle
encode ce décalage sous-maille.

Sur **O₃**, l'écart est bien plus faible — RMSE médiane 9,35 contre 11,75 pour CAMS, et un
rapport de deux seulement entre extrêmes. L'ozone est régional : une station de fond en
prédit une autre. Les moins prédictibles sont des postes d'altitude ou de piémont (Pays du
Mezenc, Lourdes).

**Les décisions que cela éclaire.**

- **Un poste de fond rural déplacé coûte peu d'information régionale** ; un poste trafic
  déplacé en coûte beaucoup. La densification pour 2030 et la détermination des aires de
  représentativité pour 2028 n'ont pas le même enjeu selon la typologie.
- **Là où le réseau est le plus prédictible, la modélisation peut prendre le relais** ;
  là où il ne l'est pas, la mesure reste irremplaçable. C'est exactement l'arbitrage que
  pose la nouvelle réglementation entre mesures fixes et applications de modélisation.

---

## ④ Où une station neuve apporterait le plus

Croisement de l'éloignement et de l'imprédictibilité du voisinage — les deux normalisés,
pour que l'unité ne décide pas du classement :

| priorité | km | RMSE du voisin | EPCI |
|---|---|---|---|
| 0,439 | 36,8 | 13,03 | CC Aure-Louron |
| 0,388 | 56,8 | 9,26 | CC Cazals-Salviac |
| 0,388 | 71,9 | 8,19 | CC Pyrénées Cerdagne |
| 0,348 | 64,5 | 8,19 | CC Capcir Haut-Conflent |
| 0,333 | 48,8 | 9,26 | CC Quercy-Bouriane |
| 0,287 | 41,3 | 9,35 | CC Région Lézignanaise, Corbières et Minervois |
| 0,258 | 37,2 | 9,35 | CC Lodévois et Larzac |
| 0,246 | 34,2 | 9,54 | CC du Pays de Serres en Quercy |

**Limite explicite.** Ce classement ne tient compte ni de la population exposée, ni des
sources locales, ni du coût d'implantation, ni des obligations de représentativité par type
de zone. Il dit seulement *où l'incertitude est la plus grande*. C'est une entrée dans la
décision, pas la décision.

---

## Ce que nous proposons de vérifier ensemble

Cette analyse repose sur des données publiques et sur une correction de **CAMS**. Quatre
questions ne peuvent se trancher qu'avec les données internes :

1. **Le même exercice sur les sorties CHIMERE régionales** donnerait la prédictibilité
   réelle du réseau dans la chaîne opérationnelle, et non dans une chaîne européenne.
2. **La comparaison à l'adaptation statistique existante** — nos gains sont mesurés contre
   CAMS brut, ce qui ne dit rien de ce qu'ils vaudraient contre une chaîne déjà corrigée.
3. **Le point de coupure réel des observations** : notre convention retient les mesures
   jusqu'à la fin de J−2, par prudence. Si le rapatriement permet mieux, le levier des
   observations antérieures — le plus fort que nous mesurions, **+14 points sur NO₂** —
   gagnerait encore.
4. **Le protocole du référentiel LCSQA** appliqué à l'identique, pour que ces chiffres
   soient comparables au rapport d'évaluation annuel transmis à la DREAL.

---

## Reproductibilité

| | |
|---|---|
| calcul | `scripts/valeur_reseau_occitanie.py` |
| prédictions hors pli | `scripts/oof_double_aveugle.py` |
| sorties | `reports/reseau_occitanie_{stations,zones,pilote}.csv` |
| protocole | station **et** mois cachés simultanément ; masques d'entraînement explicites |
| corpus | 36 mois, observations LCSQA, prévisions CAMS Europe J+1 |

Le protocole d'évaluation, ses fuites identifiées et ses résultats négatifs sont documentés
dans le dépôt au même titre que les résultats favorables.
