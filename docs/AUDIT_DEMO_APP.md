# Audit de `app.py` — la pièce opérée en direct

> Réponse au brief `docs/BRIEF_AUDIT_DEMO_KIMI.md`. Méthode : chaque chiffre cité ici a
> été **re-mesuré** en rejouant le code de la démo sur `data/demo/*.parquet` (17/08/2026),
> pas relevé à l'écran. Les numéros de ligne renvoient à `app.py` sauf mention contraire.
>
> Verdict en une ligne : **la démo ne plante pas, mais elle affiche trois valeurs
> plausibles et fausses** — dont une bannière rouge qui contredit son propre graphique
> sur le polluant affiché par défaut — et **aucun de ses chiffres ne se réconcilie avec
> une famille publiée du dossier**.

---

## ⓪ Réponse directe au piège connu (§ 2 du brief)

**La démo et le dossier ne parlent pas du même système — et la démo ne le dit nulle
part.** Vérifié dans la chaîne :

| | démo | dossier (chiffres publiés) |
|---|---|---|
| fichier source | `reports/mos_<P>_J1.csv` (`build_demo_data.py:48`) | `methode_maximale`, `oof_double_aveugle`, … |
| échéance réelle | **J0** — `fit_mos.py:60` `TRANCHES[1] = (1, 24)` | J+1 à J+2 |
| grain | horaire | journalier (grandeur réglementaire) |
| pile | **base seule** — CAMS + terrain + calendrier (`fit_mos.py:164-177` exclut `type_station`, tout le reste est statique) | pile complète : + typologie, membres, feux, geoscf, tendance |
| épreuve | stations exclues, mois vus (`mos.py:134-136`) | double aveugle (station **et** mois cachés) |
| corpus | 2023-08 → 2026-07 (PM10 : 2024-01 → 2026-08) — mesuré | ① 2025-01→2026-08 · ②③ 29 mois · ⑤ 17-30 plis |

1. **Échéance** : la démo calcule J0, et **le dit** (l. 165-168) — le correctif du 11/08
   est bien en place. Mais le nom du fichier source continue de mentir : `mos_O3_J1.csv`
   contient du J0. C'est la § 4 ter encore vivante **dans le nom de l'artefact**.
2. **Pile** : la démo tourne sur la pile de base ; les chiffres publiés sur la pile
   complète. Ce n'est pas le même produit.
3. **Concordance** : mesuré — les gains globaux affichés (O₃ **+16,5 %**, NO₂ **+19,2 %**,
   PM2,5 **+14,4 %**, PM10 **+17,5 %**) ne correspondent à **aucune** des cinq familles du
   § 7 ter (①b O₃ +27,19 % · ③ +15,83 % · ⑤ +3,31 %…). Un juré qui compare l'écran au
   dossier ne tombe sur rien d'identique, et **aucune ligne de la démo ne dit pourquoi**.
   Aucun des deux n'est faux : ce sont deux configurations différentes, et la démo est une
   sixième, non publiée. **Correction en règle** : un bandeau fixe portant les trois mots
   du dépôt — *périmètre · épreuve · échéance* — plus la pile et le corpus :
   « pile de base · stations exclues (mois vus) · J0 · horaire · 2023-08→2026-07 — les
   chiffres publiés sont à J+1/J+2, pile complète, double aveugle : ils ne se comparent
   pas terme à terme ». Sans cela, chaque page cite des pourcentages sans leurs trois
   mots — la faute que la doctrine interdit (§ 7 ter).

---

## ① Concordance des chiffres écran ↔ dossier

Au-delà du problème structurel ci-dessus, deux constats :

### 1.1 🔴 « Elle repose sur trois mois de 2024 » — faux, périmé

- **Affirmé** (l. 274-275) : la page ① « repose sur trois mois de 2024 ».
- **Réel** : `predictions.parquet` couvre **2023-08-01 → 2026-07-31** (PM10 : 2024-01 →
  2026-08-08), soit ~36 mois. Mesuré sur le fichier.
- C'est une réserve d'une version antérieure, restée après l'extension du corpus. Elle
  joue *contre* nous (elle sous-déclare le corpus) et elle est **réfutable en dix
  secondes** par quiconque ouvre le sélecteur de date.
- **Correction** : dériver la fenêtre des données elles-mêmes
  (`p["jour"].min()` → `max()`), jamais l'écrire en dur — c'est la règle A du dépôt
  appliquée à une phrase.

### 1.2 🟠 Les métriques par station de la page « Station par station »

L. 432-434 : « RMSE CAMS » / « RMSE corrigé » sont calculées sur **tout le corpus**, sans
que l'étiquette le dise, à côté d'un graphique qui n'affiche qu'**un mois**. Un juré
lira le chiffre comme celui du mois montré. Correction : ajouter « (36 mois) » à
l'étiquette.

---

## ② Étiquettes et périmètres

### 2.1 🔴 La bannière « épisodes manqués » somme des ensembles emboîtés — verdict faux sur O₃

- **Affirmé** (l. 508-516) : une bannière verte/rouge totalise les « épisodes manqués »
  de CAMS brut et du corrigé, **tous seuils confondus**.
- **Réel** (mesuré en rejouant le code) : les seuils sont **emboîtés** — une heure à
  140 µg/m³ manquée compte dans ≥ 50, ≥ 100 *et* ≥ 130. La somme est dominée par le seuil
  ≥ 50 (« Moyen »), qui couvre **4,26 M d'heures, 60 % du corpus** — ce n'est pas un
  épisode, c'est le régime courant.

  | O₃ horaire (J0) | CAMS brut | Corrigé |
  |---|---|---|
  | ≥ 50 — rappel | 0,932 | 0,856 |
  | ≥ 100 — rappel | 0,489 | **0,584** |
  | ≥ 130 — rappel | 0,179 | **0,286** |
  | **bannière affichée** | — | **rouge : « 282 224 épisodes manqués de plus »** |

  Aux deux seuils sévères, le corrigé manque **moins** d'épisodes ; la bannière conclut
  l'inverse à cause du seuil trivial. Le texte joint — « la correction échange du rappel
  contre de la précision, c'est le mauvais côté de l'échange » — est donc **faux sur le
  polluant affiché par défaut** (O₃ est premier dans `NOM`, l. 30), un clic après la vue
  par défaut de la page. Et il contredit le dossier (§ 8 : à budget égal, le rappel
  *progresse*).
- **Correction en règle** : ne jamais sommer des événements emboîtés — la bannière porte
  sur **un** seuil, le plus strict ayant assez d'occurrences, ou sur le delta par seuil
  sans total. (Les bannières NO₂/PM2,5/PM10 sont vertes ; l'échelle journalière est
  verte, +3 618 : le défaut n'est pas le signe, c'est l'arithmétique.)

### 2.2 🔴 « Jeu égal dans la queue » — démenti par le graphique qui lui fait face

- **Affirmé** (l. 306-310) : « le gain se concentre sur les valeurs basses, et la
  correction fait **jeu égal** dans la queue. »
- **Réel** (mesuré sur les mêmes bandes que le graphique) :

  | polluant | bande basse | bande médiane | queue visible |
  |---|---|---|---|
  | O₃ | 0-50 : **+29,4 %** | 50-100 : **−12,7 %** ⚠️ | 130-240 : **+21,9 %** |
  | NO₂ | 0-40 : +14,4 % | 40-90 : +25,5 % | 120-230 : +12,5 % |
  | PM2,5 | 0-10 : +11,9 % | 20-25 : +16,9 % | ≥ 50 : +9,3 % |
  | PM10 | 0-20 : **+2,7 %** | 40-50 : +22,0 % | ≥ 100 : **+17,6 %** |

  Aucun des quatre polluants ne suit la phrase : sur PM10 le gain est le plus **faible**
  en bas et le plus fort en queue ; sur O₃ la bande 50-100 est **dégradée** — un fait
  réel, visible à l'écran, et tu partout. Un juré voit la barre orange au-dessus de la
  bleue sur O₃ pendant que la légende dit « jeu égal ».
- **Correction** : la phrase doit décrire le graphique, pas le récit d'une version
  antérieure. (« C'est voulu — une version antérieure… » est, lui, sourcé : `mos.py`
  l. 121-128.) Et la dégradation O₃ 50-100 mérite d'être dite : c'est exactement la
  posture du dossier.

### 2.3 🟠 L'encart « l'horaire perd en rappel » est faux aux seuils sévères

L. 526-533 : « À l'échelle horaire, la correction … gagne en précision et **perd en
rappel**. » Vrai à ≥ 50 ; **faux à ≥ 100 et ≥ 130** (tableau du 2.1 : rappel *et*
précision progressent). L'explication par l'« amortissement rattrapé par le maximum » est
un mécanisme publié sur un sous-ensemble (règle E). Correction : restreindre l'affirmation
aux seuils bas, ou la régénérer depuis la table affichée.

### 2.4 ✅ « Validation par station exclue » — vrai, et il manque sa réserve

L. 336-337 et 363-365 : « chacune est prédite par un modèle qui ne l'a jamais vue ».
**Vérifié** : `mos.py:134-136` tire des plis de **stations** entières. Mais les plis ne
sont **pas bloqués spatialement** — le dossier le mesure (§ 11 : O₃ +28,6 % → +18,5 %
avec fossé de 50 km). Le score de la démo est donc **optimiste** au sens du § 11, et la
réserve qui l'accompagne dans le dossier n'a pas traversé vers la démo. C'est le point
④ du brief : les stations ne sont pas connues du modèle, **leurs voisines si**, et ce
n'est pas écrit. Correction : une ligne — « stations entièrement exclues, sans fossé
spatial : le § 11 du dossier mesure l'optimisme résiduel (jusqu'à −10 pts sur O₃) ».

### 2.5 🟠 Le régime du jour : trois défauts de périmètre

L. 213-248 :

1. **L'objet n'est pas celui de l'étude.** `REGIMES_METEO.md` classe chaque
   **station × heure** (`erreur_par_regime_meteo.py:61-69`) ; la démo classe la
   **moyenne nationale des 24 h** (`m["couche_limite_m"].mean()`, l. 221-223) puis applique
   les mêmes seuils. Rejouée sur tout le corpus, cette classification donne : ventilé
   51,7 %, photochimique 44,9 %, **stagnation 3,4 %** — le régime qui porte le message de
   prudence ne se déclenche presque jamais, et une journée ventilée à Brest et stagnante à
   Lyon reçoit une seule étiquette.
2. **Le « 17 % » est sourcé mais déplacé** (l. 243) : −17,0 % (ventilé) / −17,6 %
   (stagnation) sont mesurés à **J+1, par station-heure, sur trois mois de 2024, pour
   l'ozone seul**. Affichés sans ces trois mots, sur un objet différent.
3. **PM10 n'a jamais été mesuré dans ce rapport** (O₃, NO₂, PM2,5 seulement) — la
   démo lui applique pourtant le message vert « elle peut être suivie sur les pics ».
   Le régime « précipitations » de l'étude a en outre disparu de la classification.

   **Correction** : classer par station (le code existe) ou afficher le régime comme
   descriptif et attacher la confiance à son périmètre mesuré ; exclure PM10 du verdict.

### 2.6 🟠 Détection journalière : deux non-dits et un label décalé

- La vue « Classe d'indice journalière » **ignore le sélecteur de polluant** (l. 490 :
  `detection_journaliere(pred)` sur tout le corpus). C'est justifié — l'indice est
  multi-polluants — mais rien ne le dit ; un juré choisit PM10 puis regarde une table
  dominée par l'ozone.
- `indice_complet_seulement(indices, n_requis=3)` (l. 99) : sur 467 262 jours-station
  observés, 49 % sont retenus ; **54 % des jours retenus n'ont que 3 polluants sur 4** —
  le module lui-même avertit qu'un indice sur sous-ensemble est **optimiste par
  construction** (`indice_atmo.py:164-171`). Jamais affiché.
- Le docstring de l. 83-84 dit « l'échelle de ce qui est publié au public » ; le module
  dit l'inverse (`indice_atmo.py:9-13` : l'indice publié est **spatialisé**, pas calculé
  station par station). C'est la même *règle* d'agrégation, pas le même indice.
- Les seuils horaires sont étiquetés d'un cran à côté (l. 71-76) : « ≥ 50 — Moyen » alors
  que 50 arrondi reste « Bon » (`sous_indice`, borne supérieure incluse). Effet numérique
  minime ; le principe — une étiquette ne promet que ce que la donnée tient — s'applique.

### 2.7 🟡 Menus

- L. 141 : « 476 stations » — c'est le nombre de stations **paysagées** ; la carte en
  évalue 236 à 344 selon le polluant (mesuré). À dire, ou à aligner.
- L. 169-172 : « mesures : EEA » — le corpus est **LCSQA** pour l'essentiel (EEA ≤ 2023).
- `data/demo/cams_benchmark.parquet` et `indice_detection.parquet` sont **embarqués,
  périmés et jamais lus** par `app.py` (14 mois, J+1 ; leurs n_evenements ne coïncident
  pas avec les nôtres). Un fichier mort qui contredit les chiffres vivants est un jumeau
  en embuscade (§ 4 bis) : régénérer ou retirer.

---

## ③ Ce qui casse en direct

**Ce qui plante : rien de trouvé.** Tous les chemins vides sont gardés (l. 198, 424, 493) ;
désélectionner toutes les typologies donne une carte et un tableau vides sans exception
(silencieux, bénin) ; le sélecteur de polluant est piloté par la donnée (l. 153).

**Ce qui affiche une valeur plausible et fausse** : voir 2.1, 2.2, 1.1 — et :

### 3.1 🔴 « Météo non extraite » s'affiche **à tort** sur le jour montré par défaut

L. 215 construit `era5_metropole_{mois}.parquet` avec `mois = %Y%m`. Or 2025 est stocké en
fichiers **groupés** (`era5_metropole_202501_04.parquet`, `…_202505_06.parquet`) et
2025-07 → 2026-06 est **absent**. Conséquences mesurées :

- pour **2025-01 → 2025-06**, la donnée existe mais le chemin construit ne la trouve pas →
  « Météo non extraite pour 202501 » — une **fausse absence**, le défaut du nom groupé de
  la § 4 bis, que `fit_mos.py` documente déjà (l. 107-113) ;
- le jour affiché **par défaut** (médiane du corpus : **2025-01-30** pour O₃) tombe dans
  cette fenêtre → le message faux est sur le **premier écran** de la page ① ;
- pour ~50 % des jours du corpus, le bloc « régime et confiance » est absent — l'une des
  trois promesses de la page s'effondre sans un mot d'explication.

**Correction** : résoudre le chemin par glob (`era5_metropole_{mois}*.parquet` + filtre
sur le contenu, jamais le nom — § 4 bis), et dire la couverture réelle de la météo.

### 3.2 🟠 Premier affichage de la page « Détection » : **90 s sans spinner**

`detection_journaliere` (l. 82) groupe 28,9 M lignes trois fois, avec `iterrows` dans
`sous_indices_journaliers`. Mesuré deux fois, espacées : **> 120 s** (timeout), puis
**37 + 26 + 25 = 90 s** — la pire valeur fait foi : au moins 90 s, une fois par session,
avec `show_spinner=False` — aucun retour visuel. Le brief n'autorise le sujet performance que si ça casse la démonstration :
**c'est le cas**. Correction sans refonte ni dépendance : matérialiser la table (quelques
dizaines de lignes) dans `build_demo_data.py` — qui existe précisément pour ça — ou, au
minimum, `show_spinner=True` et une visite de chauffe avant l'entrée du jury.

### 3.3 🟡 La carte écrête les gains au-delà de ±50 %

L. 384 : `cmin=-50, cmax=50`. Mesuré : **13 stations NO₂ et 2 O₃** dépassent, dont une à
**−396,9 %**, affichée du même rouge qu'une −50 %. Le survol donne le vrai chiffre, mais
la couleur ment par saturation. Correction : échelle en quantiles, ou borne dérivée de la
donnée affichée.

---

## ④ Ce que la démo ne dit pas et devrait dire

Récapitulatif des réserves **manquantes** (les présentes — prototype non validé l. 272,
CAMS ≠ PREV'AIR l. 353, insuffisance de détection l. 535 — sont bonnes, ne pas y
toucher) :

1. **Les trois mots** — périmètre · épreuve · échéance — plus pile et corpus : absents de
   toutes les pages sauf l'échéance (⓪). Le défaut structurel.
2. **Plis non bloqués spatialement** (2.4) — le dossier le mesure, la démo le tait.
3. **Indice journalier partiel** (2.6) — 54 % des jours retenus calculés sur 3 polluants.
4. **PM10 non mesuré** dans le rapport de régimes (2.5.3).
5. **La bande O₃ 50-100 dégradée** (2.2) — un échec visible, tu : l'inverse de la posture
   du dossier.

---

## Hiérarchie — s'il n'y a le temps que d'un seul correctif

| # | défaut | nature | coût |
|---|---|---|---|
| **1** | **2.1 — la bannière « épisodes manqués »** | **verdict faux**, auto-contradictoire, sur le polluant par défaut | ~5 lignes : un seuil, pas une somme |
| 2 | ⓪/1.1 — les trois mots + corpus périmé « trois mois de 2024 » | réconciliation impossible avec le dossier, réserve réfutable | un bandeau + une fenêtre dérivée |
| 3 | 2.2 — « jeu égal dans la queue » | phrase démentie par son propre graphique | réécrire depuis les bandes |
| 4 | 3.1 — « Météo non extraite » faux sur l'écran par défaut | fausse absence, première impression | un glob + un filtre contenu |
| 5 | 3.2 — 90 s sans spinner | gel en direct | pré-calcul au build (ou spinner) |

**Le n° 1**, parce que c'est le seul endroit où la démo **calcule et affiche un verdict
faux** — pas une réserve manquante, pas une étiquette floue : une phrase rouge qui dit
l'inverse de ses propres barres et du dossier, à un clic de la vue par défaut. Tout le
reste se défend à l'oral ; celui-là contredit l'orateur pendant qu'il parle.
