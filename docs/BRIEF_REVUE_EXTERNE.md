# Revue adverse demandée — correction statistique de prévisions de qualité de l'air

**Ce qu'on attend de vous : attaquer, pas valider.** Le projet a cinq jours avant remise.
Un point faible trouvé maintenant vaut mieux qu'un compliment.

---

## 1. Le système, en six lignes

On corrige les prévisions de l'ensemble européen **CAMS** (0,1°, ~10 km) aux stations de
mesure françaises, par apprentissage du **résidu** `observation − CAMS` avec LightGBM.
Cible journalière, échéance J+1. Entrées : CAMS, terrain, calendrier, typologie de station.
**Aucune observation au moment de la correction** (sauf un levier « veille » isolé) — c'est
un choix : le produit doit exister **là où il n'y a pas de capteur**.

Corpus : 37 mois (2023-08 → 2026-08), ~29,5 M d'enregistrements horaires, 438 stations
réellement évaluées.

## 2. Le concurrent : PREV'AIR / AS-CHI (INERIS)

Chaîne nationale française. Part de **CHIMERE** en configuration nationale (1,7 km,
inventaire d'émissions français, assimilation), puis **AS-CHI** = **krigeage à dérive
externe** du résidu observation−modèle (krigeage ordinaire à l'origine, dérive externe
depuis 2010).

**Leurs gains publiés** (rapport *Performances Prev'air en 2024*, J0, France, chacun contre
son propre brut) :

| polluant | CHIMERE brut | AS-CHI | gain |
|---|---:|---:|---:|
| O₃ (avr-sep) | 13,9 | 13,3 | **+4,3 %** |
| NO₂ | 16,7 | 11,2 | **+32,9 %** |
| PM10 | 9,9 | 4,7 | **+52,5 %** |
| PM2,5 | 7,65 | 3,05 | **+60,1 %** |

**Nos gains, recalculés sous LEUR convention** (référentiel LCSQA : stations de fond
seules, disponibilité ≥ 75 %, score par station puis moyenne non pondérée, ozone en max
horaire avril-septembre), échéance J+1 :

| polluant | CAMS brut | nous | gain |
|---|---:|---:|---:|
| O₃ | 10,062 | 7,879 | **+21,7 %** |
| NO₂ | 15,458 | 10,101 | **+34,7 %** |
| PM10 | 6,349 | 4,236 | **+33,3 %** |
| PM2,5 | 3,936 | 2,772 | **+29,6 %** |

→ **On domine largement sur l'ozone, on est à égalité sur le NO₂, ils nous dépassent
nettement sur les particules.**

Écarts de protocole restants, **tous à notre désavantage** : leur échéance est J0 (plus
facile), leur panel inclut les DROM, et notre épreuve cache **station ET mois** quand la
leur ne cache que le mois.

---

## 3. 🔴 QUESTION PRINCIPALE — l'écart sur les particules

**Notre hypothèse, sur laquelle on vient d'engager le temps restant :** l'avantage PM
d'AS-CHI vient de ce que leur CHIMERE ingère l'**inventaire d'émissions français**, alors
que nos 58 prédicteurs ne contiennent **aucune variable d'émission**.

Inventaire exact de nos 58 prédicteurs (PM10) :

| famille | n | contenu |
|---|---:|---|
| végétation | **28** | essences (chêne, conifère, feuillu) à 6 rayons — un proxy **BVOC**, conçu pour l'ozone |
| relief | 10 | altitude, TPI, rugosité, pente, profondeur de vallée |
| routes | 5 | distance, longueurs à 5 rayons |
| calendrier | 4 | jour de l'année (sin/cos), jour de semaine, week-end |
| typologie | 4 | densité, fond/industriel/trafic |
| CAMS | 2 | valeur journalière et moyenne |
| coordonnées | 2 | lat, lon |
| autre | 3 | échéance, heure (sin/cos) |

**Aucune émission, aucun bâti, aucune population, aucune agriculture, aucune météo.**

**L'action engagée :** on télécharge 6 variables de **spéciation CAMS** qu'on n'utilisait
pas — le catalogue ADS en expose **28**, on n'en prenait que **4** (les masses totales) :

- `residential_elementary_carbon` — traceur du **chauffage au bois**, 1ʳᵉ source française
  de PM2,5 (7,4 M de logements équipés) ;
- `secondary_inorganic_aerosol`, `pm2.5_nitrate` — la fraction NH₃→nitrate des épisodes de
  printemps ;
- `dust`, `pm10_wildfires`, `pm2.5_total_organic_matter`.

Raisonnement : on corrige un **résidu**, donc lui donner la **composition** du champ permet
d'apprendre des biais **par source** au lieu d'un biais moyen.

### Ce qu'on vous demande

1. **L'hypothèse est-elle la bonne ?** Y a-t-il une explication plus probable de l'écart PM
   (par ex. purement l'échelle 1,7 km contre 10 km, ou l'assimilation, ou le fait que le
   résidu PM est simplement plus krigeable) ? **Si l'écart est irréductible sans
   observations, dites-le** — on préfère l'écrire que le découvrir devant un jury.
2. **Manque-t-il une variable évidente** dans la liste des 6 ? Faut-il `ammonia`,
   `pm2.5_ammonium`, `pm2.5_sulphate`, `total_elementary_carbon` plutôt que certaines ?
3. ⚠️ Copernicus ne valide contre observations que NO, NO₂, SO₂, O₃, PM2,5, PM10 et `dust`.
   Les autres sont **expérimentales**. Est-ce disqualifiant comme prédicteurs ?

---

## 4. Ce qui a DÉJÀ été réfuté — ne pas le proposer

Chaque ligne est une mesure, pas une intuition.

| piste | verdict mesuré |
|---|---|
| **réglage d'hyperparamètres** (Optuna, 200 essais/polluant) | +4 à +7 % sur l'axe **spatial**, **~0 sur l'axe temporel**. Confirmé par deux protocoles indépendants : `défaut` bat `optuna` **3/3** en temporel |
| plus de capacité (arbres 400→3000) | **dégrade** en temporel 3/3 |
| GNN / voisinage spatial | +0,28 pt — sous le seuil |
| sol, géologie | 11× sous le critère de rétention |
| contexte spatial du champ CAMS (moy/max à 50-200 km) | discrimination **−0,0005** |
| dispersion d'ensemble comme prédicteur | nulle (utile seulement comme **indice de fiabilité**) |
| classification / pondération / régression quantile pour la détection | n'ajoutent rien — **c'est le rang qui décide** |
| capteur d'anomalie sur les entrées | négatif |
| GEOS-CF (modèle NASA indépendant) | **+2,5 à +2,8 %** — réel mais petit ; flux v1 arrêté 2025-12 |
| feux (GFAS) | +3,0 % sur PM2,5 seulement |
| météo ERA5 | plafond **+7,8 %** sur O₃ — mais c'est une **réanalyse**, indisponible à l'émission. La prévision IFS en récupère 64 % |

**Leviers qui marchent réellement**, par ordre : biais glissant par station (**+43,1 % sur
NO₂ sans aucun apprentissage**), typologie de station (+8,5 à +8,9 pts sur NO₂), dynamique
de CAMS (`tendance`), moyenne d'ensemble.

---

## 4 bis. 🆕 Résultat tombé pendant la rédaction de ce brief — un réseau bat les arbres sur PM10

On a porté **RealMLP-TD** (Holzmüller et al., *Better by Default*) en régression sur ce
jeu, réglé par Optuna **sur l'axe temporel** (60 essais), et comparé à LightGBM. Mesure
sur un test temporel jamais consulté :

| polluant | CAMS brut | LightGBM | **RealMLP** | moyenne 50/50 | ρ des erreurs |
|---|---:|---:|---:|---:|---:|
| NO₂ | 22,745 | **12,3882** | 12,4578 | 12,2603 | 0,961 |
| O₃ | 13,118 | 12,3073 | **11,9808** | 12,0277 | 0,962 |
| **PM10** | 7,340 | 6,2010 | **5,6405** | 5,7731 | 0,899 |
| PM2,5 | 3,750 | 3,8492 | **3,7908** | 3,7494 | 0,928 |

**RealMLP gagne 3/4, et de −9,0 % sur PM10** — le polluant où l'on décroche justement face
à AS-CHI. Trois observations :

1. ⚠️ **La comparaison n'est pas à armes égales** : RealMLP a eu 60 essais, LightGBM tourne
   aux défauts. Le réglage LightGBM au même budget et sur le même objectif temporel est en
   cours. Atténuation connue : la table à 4 configurations montre `défaut` battant `optuna`
   **3/3** en temporel, donc LightGBM au défaut est déjà proche de son optimum sur cet axe.
2. La **moyenne 50/50 nuit** sur O₃ (−0,39 %) et PM10 (−2,35 %) : elle tire le meilleur
   modèle vers le moins bon. Un ridge pondéré **hors-pli** est en cours d'écriture.
3. 🔴 **Sur PM2,5, LightGBM (3,849) est PIRE que CAMS brut (3,750)** — la correction
   *dégrade* sur cet axe. RealMLP aussi (3,791). Ce n'est pas un problème d'algorithme.

### Ce qu'on vous demande là-dessus

- **Pourquoi un MLP gagnerait-il 9 % sur PM10 et rien sur NO₂ ?** Y a-t-il une raison
  structurelle (lissage spatial des champs de particules, non-linéarités douces, seuils
  d'accumulation) ou est-ce un artefact du protocole ?
- **PM2,5 : que se passe-t-il ?** La correction dégrade en temporel alors qu'elle gagne
  +29,6 % en convention AASQA. Piste sur l'origine de la contradiction ?

## 5. QUESTION SECONDAIRE — quelles sciences n'avons-nous pas explorées ?

Balayage du dépôt (nombre de fichiers mentionnant l'approche) :

| approche | présence |
|---|---|
| quantiles | 55 |
| krigeage | 21 |
| couche limite | 6 — **en donnée seulement, jamais dans le modèle déployé** |
| Venn-Abers / conformal | 4 |
| valeurs extrêmes, rétrotrajectoires, représentativité | 2-4 chacune |
| **filtre de Kalman / espace d'états** | **0** |

**Notre seule piste identifiée :** le levier le plus fort du projet est le **biais glissant**
(moyenne mobile de l'erreur sur 7 jours, +43,1 % sur NO₂). C'est la version fruste d'un
**filtre de Kalman sur un biais qui dérive** — la méthode classique du MOS opérationnel en
prévision numérique. Jamais essayée ici.

**Question : que manque-t-il d'autre ?** Physique de couche limite, géostatistique,
quantification d'incertitude, théorie de la décision, assimilation, apprentissage
multi-tâches, transport… Pour chaque suggestion, **dites ce qu'elle apporterait
concrètement** sur ce système-là, et à quel coût.

---

## 6. Deux points faibles connus, à challenger aussi

1. **Les pics.** Le classement des journées à risque est bon (rang percentile 0,872 les
   jours de dépassement) mais **l'amplitude prédite vaut 51 % de l'observée**. Une
   recalibration en distribution porte les détections de 39 à 131 **au prix de la
   précision**. Y a-t-il mieux qu'un mapping de quantiles ?
2. **Le double aveugle.** Contre les épisodes **réellement déclenchés** par l'AASQA, on
   n'en attrape que **2 sur 33** (PM10) — l'observation elle-même n'en attrape que 21.
   C'est la mesure la plus dure du dossier.

---

## 7. Contraintes

- **5 jours** avant remise. Toute suggestion doit être chiffrable en temps.
- Machine : 32 cœurs, RTX 5090 (34 Go), **instable — 17 paniques noyau**, tout lot doit
  être reprenable.
- Accès : Copernicus ADS/CDS, flux LCSQA national, data.gouv.fr, archive ECMWF sur AWS.
- **Aucune observation au moment de la correction** — c'est le choix qui fonde le produit,
  pas une limite technique. Une suggestion qui l'enfreint doit le dire explicitement.
