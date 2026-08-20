# Reprise — l'état du projet

> **Mis à jour le 20/08/2026 à 11 h 30.** Si la date ci-dessus a plus de deux jours,
> **méfie-toi de ce fichier** : sur ce projet il a déjà été périmé de dix jours tout en
> s'annonçant comme l'état courant. Vérifie par `git log --oneline -5` et `ls -lt reports/`
> avant de croire ce qui suit.

---

## ⛔ 20/08 — LE BLOCAGE QUI PRIME SUR TOUT LE RESTE

**Le compte GitHub `cyril-bgs-dev-tech` rend 404 à tout visiteur non authentifié**, profil
compris. Mesuré depuis **deux réseaux indépendants**, avec témoins (`octocat`, `defunkt` →
200 depuis la même machine, à la même seconde). L'en-tête du 404 porte `server: github.com`
et un `x-github-request-id` : c'est GitHub qui répond, pas un cache. Quota anonyme à 57/60,
donc pas un 403 déguisé.

Trois faits qui s'ajoutent : Actions est désactivé **au niveau utilisateur**
(« Actions has been disabled for this user »), **zéro** exécution de workflow depuis la
création du compte le 31/05, et `cyril-bgs-dev-tech.github.io/Portfolio/` n'a **jamais** été
construit. Avec le jeton du propriétaire, tout existe et est marqué `public`.

**Conséquence : `docs/LETTRE_ATMO_OCCITANIE.md` renvoie deux fois à un dépôt qu'aucun
recruteur ne peut ouvrir** (l. 85 et la signature l. 96). La cause exacte n'est pas
observable — l'API n'expose aucun champ d'état au propriétaire ; « compte signalé » est une
**inférence** tirée de la signature, pas une déclaration de GitHub.

**Action, et elle n'appartient qu'à Cyril** : `support.github.com/contact/reinstatement`,
7 à 10 jours ouvrés annoncés. Prévoir une variante de lettre sans dépendance GitHub.

---

## ✅ 18-20/08 — CE QUI A ÉTÉ FAIT

**Tout est commité et poussé, des deux côtés.** L'avertissement « rien n'est commité » des
versions précédentes de ce fichier est périmé.

### L'argument réglementaire, qui n'était dans aucune pièce publiée

Mesuré le 18/08 : la présentation contenait **zéro** occurrence de « directive »,
« FAIRMODE », « MQI » ou « valeur limite ». Ses huit « 2030 » étaient des fragments de codes
station dans le JSON embarqué. Le README public non plus.

**Page 09 « L'horizon 2030 »** créée — `scripts/page_horizon_2030.py`, présentation à
**63 pages** :

- la directive **(UE) 2024/2881** divise les seuils par deux au 01/01/2030 *et* rend la
  modélisation obligatoire là où un seuil est dépassé — donc elle **multiplie** les zones où
  modéliser devient une obligation ;
- comptage à air constant : **6 stations en dépassement aujourd'hui → 109 en 2030**, ×18,2
  sur 408 évaluées. Occitanie 2 → 5, et **4 des 13 départements sans aucune station** (09, 11,
  46, 48) — le cas que la directive confie à la modélisation ;
- critère FAIRMODE de prévision à J+1 : NO₂ **41,4 %** brut → **96,2 %** corrigé ; PM10
  87,8 → 100 ; O₃ 93,6 → 99,2. **Publié avec ce qui ne passe pas** : sans observation du
  point, le NO₂ plafonne à **87,9 %**, sous la barre des 90 %.

Deux précisions mécanisées au passage : **§ 5 ter** entre dans `VERITE_DOSSIER` (ces parts
portaient l'argument sans y figurer), et **§ 5 porte enfin son échéance** — il est calculé
depuis `mos_<P>_J1.csv`, où le `J1` est l'**horizon**, donc **J0**, à côté d'un § 5 ter à J+1.

⚠️ **`MQI_f` ≠ MQI d'évaluation** : le premier rapporte l'erreur à une **persistance**, le
second vaut `RMSE / (β·RMS_U)`. Même sigle, deux questions. Ne jamais les citer côte à côte
sans les nommer.

### Le portefeuille GitHub, repris en profondeur

Voir la fiche mémoire dédiée. En bref : fiche qualité de l'air créée puis réécrite pour un
lecteur non spécialiste, volume corrigé (**213 M → 28 M**, le premier chiffre n'avait aucune
source), Master 2 à **7 projets** et non 8, DELTAMU doté de son impact et de son retour,
stack complétée, étiquettes GitHub posées sur les trois dépôts qui n'en avaient aucune.

🔴 **Reste ouvert** : 7 des 9 fiches contiennent `::: {.panel-tabset}`, syntaxe Quarto que
**GitHub affiche en clair** — et comme le site n'est pas construit, GitHub est le seul rendu.

### Un brief d'audit externe est prêt

`docs/BRIEF_AUDIT_PORTFOLIO_GPT.md` — 115 ko, **contenu intégral embarqué** parce que les URL
rendent 404. Huit familles de défaut pré-enregistrées, format de réponse imposé.

---

## 🔴 17/08 APRÈS-MIDI — LIRE CECI D'ABORD : les chiffres publiés ont changé

Tout ce qui suit dans ce fichier a été écrit **avant** trois corrections qui invalident
partiellement ses tableaux. La table publiée est désormais celle-ci :

| § ③ · double aveugle, **J+1**, 24 mois communs | O₃ | NO₂ | PM10 | PM2,5 |
|---|---:|---:|---:|---:|
| **PARTOUT** | **+17,90 %** | **+39,61 %** | **+20,23 %** | **+11,79 %** |
| AUX STATIONS | +24,05 % | +45,71 % | +26,25 % | +19,56 % |

Pile **identique aux quatre polluants** : base + typologie + GEOS-CF + tendance + `core7`.
Ni membres, ni feux, ni nitrate. Support commun vérifié, zéro valeur manquante.

### ① Le défaut qui a tout déclenché — « un mois absent est un code d'époque »

Quand une famille manque sur un mois entier, LightGBM apprend une direction par défaut pour
les `NaN` — donc il apprend **la date**. Le protocole cachant les mois, c'est une fuite.
**Trois occurrences** : GEOS-CF (vue à la conception), la spéciation (réintroduite le 17/08
par une jointure `how="left"` qui préservait le corpus — trouvée par une revue externe), puis
**les membres et les feux**, découverts en cherchant la cause d'une anomalie sur l'ozone.

Mesuré : sur le pli de **juillet 2025** en ozone, où les membres manquent à 97 %, l'étage
« + membres » rend **−126,48 %** de gain. C'est ce seul pli qui faisait chuter l'ozone.

🔑 **Le critère juste est un TAUX, et il a fallu trois versions du garde.** « Toutes les
colonnes vides » ratait ; « une colonne entièrement vide » ratait aussi — le fichier de juin
**déborde d'un jour** sur juillet, donc le mois n'est jamais *entièrement* vide. Mécanisé
dans `methode_maximale.py --support-complet` (`TAUX_MANQUE_MAX = 0.5`), qui **mesure** la
couverture au lieu de lister les familles à la main. Voir
[[un-mois-absent-est-un-code-d-epoque]].

### ② L'échéance était fausse, et elle nous flattait

`horizon=2` couvre les heures 25-48 : c'est **J+1**. Le dossier publiait **J+2**, sept fois.
Vérifié dans les données — `horizon=1` démarre le 2023-08-01, `horizon=2` le 02, `horizon=3`
le 03, `horizon=4` le 04. Une revue antérieure l'avait déjà classé P0 et déclaré corrigé ;
**le libellé était revenu**. C'est devenu du code : `aq.rapport.libelle_echeance()` dérive
`J+(horizon−1)` et refuse une entrée invalide.

### ③ Le dossier a enfin un INTERVALLE sur son protocole principal

Bootstrap **circulaire par blocs de mois**, 10 000 tirages, sur les différences appariées pli
à pli. Les plis ne sont pas indépendants — les groupes de stations tournent (`i mod 3`) et
deux plis partagent ~93 % de leur apprentissage.

| apport de la spéciation | point | IC95 blocs 3 mois | blocs 6 mois |
|---|---:|---|---|
| NO₂ | **+1,54 %** | [+0,85 ; +2,19] | [+0,90 ; +2,12] |
| O₃ | **+5,9 %** | [+3,4 ; +8,3] | [+3,5 ; +8,0] |
| PM10 | **+6,0 %** | [+4,2 ; +7,6] | [+4,5 ; +7,0] |
| PM2,5 | **+4,3 %** | [+2,4 ; +6,5] | [+2,5 ; +6,6] |

Bornes basses toutes positives, même verdict aux deux tailles de bloc, Holm franchi — les
trois seuils fixés avant lecture. `scripts/intervalle_apport.py`.

**Le nombre de décimales suit l'intervalle** (règle NIST GLP 9) : le NO₂ garde ses deux parce
que sa fourchette est serrée, les autres passent à une.

### ④ 🔴 Le balayage J0 → J+3 RÉFUTE une affirmation du dossier

Les échéances 73-96 h existaient en `.nc` mais **n'avaient jamais été extraites** : 86
parquets sur 90 s'arrêtaient à 72 h. Re-extraction → 164,9 M → **213,0 M lignes (+29,2 %)**,
zéro parquet dégradé. `TRANCHES[4] = (73, 96)` ajoutée.

| pile commune | J0 | J+1 | J+2 | J+3 | plage R | verdict |
|---|---:|---:|---:|---:|---:|---|
| **NO₂** | +37,10 | +37,10 | +36,89 | +36,72 | **0,38** | ✅ **stable** |
| PM10 | +15,14 | +15,22 | +14,58 | +15,26 | 0,69 | indéterminée |
| PM2,5 | +5,46 | +6,01 | +6,09 | **+7,03** | 1,57 | indéterminée |
| **O₃** | +9,25 | +9,12 | +8,53 | **+7,00** | **2,25** | 🔴 **réfutée** |

⭐ **Et le classement suit le mécanisme invoqué** : l'apport de la typologie de station vaut
**+9,03 pt sur NO₂** et **−0,23 sur O₃**. Le polluant dont le résidu est attaché au site
résiste à l'échéance ; celui qui ne l'est pas se dégrade. *L'affirmation était juste sur son
mécanisme et trop large dans sa portée.* Voir
[[la-stabilite-a-l-echeance-est-refutee-sur-l-ozone]].

### Ce qui a été propagé

`VERITE_DOSSIER` (§ ③, § 12 bis intervalle, § 12 quinquies balayage) · `page_synthese.py` et
`verite_dossier.py` pointent sur la passe contrôlée · présentation régénérée et **PDF exporté
à 61 pages, échelle 1:1**, trois gardes passés · `Découverte_ATMO` : pile régénérée depuis les
CSV, échéance et réserve de fenêtre corrigées · **les deux artefacts republiés**.

### Ce qui reste

- **§ C de la revue externe** : deux panneaux de comparaison, la persistance hors de `PARTOUT`.
- **40 tailles de police** de 8,2 à 34 px — le seul défaut de forme confirmé, sans échelle.
- ⚠️ **Rien n'est commité.**

---

## 🆕 LA NUIT DU 16 AU 17/08 — la spéciation CAMS, et deux revues externes

### ⭐ Le résultat : on téléchargeait 4 des 28 variables que CAMS expose

Le catalogue ADS expose **28 variables** pour `cams-europe-air-quality-forecasts` ; ce dépôt
en prenait **quatre** — NO₂, O₃, PM2,5, PM10, des masses totales sans décomposition. Les
sept traceurs de composition sont désormais téléchargés (32 mois, 8,6 Go + complément),
extraits aux stations, et **mesurés** :

| polluant | base J+1 | + spéciation | apport | **IC95** |
|---|---:|---:|---:|---|
| **PM10** | 6,0635 | **5,2563** | **+13,31 %** | [+10,17 ; +16,17] |
| O₃ | 13,2313 | 12,0952 | +8,59 % | [+4,59 ; +13,02] |
| NO₂ | 12,0263 | 11,2271 | +6,65 % | [+4,71 ; +8,55] |
| PM2,5 | 3,5814 | 3,3525 | +6,39 % | [+4,00 ; +9,14] |

Bootstrap **apparié**, 2 000 tirages, **17 blocs mensuels × 20 groupes géographiques** —
aucun tirage négatif sur aucun polluant.

**Le contrôle qui rend l'interprétation défendable** : configuration `T` = base + forme du
total CAMS (min, max, écart-type, P90−P10 des 24 échéances). Si le gain venait d'une simple
amplitude intra-journalière que la base n'a pas, il s'effondrerait. Il ne s'effondre pas :

| | T − B *(la forme)* | **S − T** *(la composition)* |
|---|---:|---:|
| PM10 | +1,38 % | **+12,10 %** |
| O₃ | +1,61 % | **+7,09 %** |
| PM2,5 | +0,20 % | **+6,21 %** |
| NO₂ | +1,30 % | **+5,41 %** |

### 🔴 Ce qu'on ne peut PAS en dire, et qui compte autant

- **Ce n'est pas le chauffage au bois.** L'hypothèse qui a lancé le chantier est **réfutée** :
  retirer `ecres_conc` seul *améliore* sur 3 polluants sur 4. Par groupes, c'est
  **combustion-organique** qui pèse le plus (O₃, NO₂, PM2,5) et **grossier-naturel** sur PM10.
- **Le corpus n'est pas celui de cette épreuve** : les pourcentages ci-dessus sont sur l'axe
  **temporel**. **Ils ne s'additionnent pas** aux +38,86 % publiés — voir la § suivante, qui
  donne le chiffre au protocole du dossier.

### ✅ 17/08 — le chiffre au PROTOCOLE DU DOSSIER, et la fenêtre est préservée

`methode_maximale --ablation` a tourné sur les quatre polluants. **La jointure est en
`how="left"`** : les mois antérieurs à 2024-01 gardent des `NaN` de composition que LightGBM
traite nativement, donc **le corpus est intégralement conservé** — 29, 29, 24 et 29 mois,
exactement ceux d'avant.

| polluant | mois | sans spéciation | **avec** | apport | AUX STATIONS |
|---|---:|---:|---:|---:|---:|
| **NO₂** | 29 | +38,86 % | **+40,16 %** | +1,30 pt | +46,81 % |
| **O₃** | 29 | +15,83 % | **+18,19 %** | **+2,36 pt** | +24,26 % |
| **PM10** | 24 | +17,88 % | **+20,71 %** | **+2,83 pt** | +26,47 % |
| **PM2,5** | 29 | +10,03 % | **+12,49 %** | **+2,46 pt** | +21,34 % |

**Les quatre valeurs « sans spéciation » reproduisent à la décimale les chiffres publiés au
§ ③ de `VERITE_DOSSIER`.** La chaîne est déterministe et la comparaison ne fait varier qu'une
seule chose. Le diff de couverture ancien → nouveau (§ regenerer-peut-degrader ②) est un
**enrichissement strict** : mêmes plis, 14 → 16 lignes.

⚠️ **PM10 est le seul dont la spéciation couvre tout le corpus** (24 mois à partir de
2024-01). Sur les trois autres, neuf mois entrent avec des `NaN` : l'apport mesuré est un
**minorant**. C'est cohérent avec l'ordre observé — PM10 obtient le plus gros apport.

### 🔴 17/08 — le MÉCANISME est tranché, et les deux explications concurrentes tombent

`scripts/mecanisme_speciation.py` — cinq configurations, **seuils écrits avant lecture**,
5 graines, mêmes lignes partout. Part du gain de la spéciation que chacune reproduit :

| | PM10 | PM2,5 | O₃ | NO₂ | seuil |
|---|---:|---:|---:|---:|---:|
| **C** climatologie station × mois | 1,1 % | 7,6 % | **−15,2 %** | **−2,7 %** | 70 % |
| **X** permutation **dans** station × mois | **1,9 %** | 5,2 % | 7,2 % | **−0,0 %** | 50 % |
| **P** totaux CAMS des 3 autres polluants | 28,2 % | 27,6 % | 34,7 % | 37,0 % | 70 % |
| **R** anomalie journalière | **89,2 %** | **110,7 %** | **127,3 %** | **95,1 %** | 70 % |
| **F** composition relative | 92,7 % | 89,4 % | 57,3 % | 86,3 % | — |

**`X` est le test décisif** : permuter la spéciation *à l'intérieur* de chaque (station, mois)
conserve **exactement** l'histogramme par site et par saison, et ne détruit que l'appariement
au **jour**. Il efface la totalité du gain, sur 4/4. **Le « proxy de régime » noté ci-dessus
comme l'objection la plus forte est donc réfuté** — `P` ne reprend qu'un tiers du gain avec
des données déjà présentes sur le disque.

Ce qui reste : **le modèle exploite l'écart du JOUR à la composition habituelle du site.**
Toujours aucune source nommée — l'attribution reste prédictive.

### ⭐ Et une piste que le mécanisme a ouverte : l'anomalie bat la valeur brute

`R` **dépasse** `S` sur O₃ (127 %) et PM2,5 (111 %) : la composante brute mélange le niveau
habituel du lieu et l'écart du jour, et retirer le premier aide — O₃ +8,94 → **+10,06 %**,
PM2,5 +11,55 → **+12,18 %** sur l'axe temporel. **C'est déployable** : la climatologie se
calcule sur les champs CAMS *prévus*, sans aucune observation.

### 🔴 …et la piste est RÉFUTÉE au protocole du dossier — 4/4, le signe s'inverse

| polluant | brute | anomalie | écart |
|---|---:|---:|---:|
| O₃ | +18,19 % | +17,14 % | **−1,04 pt** |
| PM2,5 | +12,49 % | +11,64 % | **−0,85 pt** |
| PM10 | +20,71 % | +20,01 % | **−0,70 pt** |
| NO₂ | +40,16 % | +39,66 % | **−0,50 pt** |

Sur l'axe temporel les stations sont **les mêmes** de part et d'autre : le modèle connaît
déjà chaque site, le niveau de composition y est redondant, et le retirer nettoie le signal.
En double aveugle la station est **inconnue**, et ce niveau est justement ce qui dit *quel
type de lieu c'est*. C'est `un-reglage-ne-vaut-que-pour-son-axe`, appliqué à une
transformation de variable. **On garde la spéciation brute.**

⚠️ **Sans le protocole du dossier, j'aurais publié un gain qui n'existe pas.**

Le défaut traversé pour y arriver a produit la **règle L** du § 0 (climatologie ajustée sur
le pli d'apprentissage, introuvable pour des stations cachées par construction) — mécanisée
par `aq.eval.critere.exiger_couverture_de_reference`, éprouvée sur le défaut réel.

### ✅ 17/08 — LE DOSSIER EST RÉGÉNÉRÉ avec la spéciation

- `VERITE_DOSSIER.md` : § ③ passe à **+40,16 / +18,19 / +20,71 / +12,49 %**, § ② aux stations
  à **+46,81 / +24,26 / +26,47 / +21,34 %**. Deux nouvelles sections : **§ 12 ter** (le
  mécanisme, avec l'échelle de falsification) et **§ 12 quater** (l'attribution de Shapley
  et son seuil de renoncement).
- La régénération a aussi rattrapé deux tables en attente : le **duel PREV'AIR passe de
  10-11 à 16-17 jours**, et la comparaison au krigeage n'est plus « en cours ».
- `presentation_atmo.html` : page 00 régénérée par `page_synthese.py`, plus **4 blocs écrits
  à la main** repris (bilan de tête, phrase AUX STATIONS).
- `Découverte_ATMO.html` : la pile cumulative gagne son étage **« + composition du champ
  CAMS »**, les deux lignes de maximum suivent.

🔴 **Ce que le contrôle automatique NE POUVAIT PAS attraper, et il faut le savoir** :
`tracer_chiffres_soutenance.py` n'a **pas** signalé `+38,86 %` comme périmé, parce que le
chiffre figure toujours dans la source — sur la ligne **`− speciation (ablation)`**. Même
nombre, autre protocole. Seul `+22,47 %`, qui n'avait pas de jumeau, est sorti. C'est la
réserve que le script énonce lui-même : *une correspondance est un candidat, pas une
validation*.

### 🔴 17/08 — la stabilité par époque, et la réserve qu'elle impose sur le NO₂

Le relecteur conditionnait la publication de la spéciation à un signe identique dans les
deux époques CAMS. Mesuré (`--epoque U9|U10`, 8 lots) :

| | PM10 | PM2,5 | O₃ | NO₂ |
|---|---:|---:|---:|---:|
| apport S − T · corpus entier | +9,42 | +5,88 | +4,11 | +2,78 |
| apport S − T · U9 | +10,09 | +9,75 | +6,12 | +2,53 |
| apport S − T · U10 | +14,44 | +5,49 | +16,28 | **−0,69** |
| part reproduite par **X** | 1,9 → 9,6 → 6,2 % | 5,2 → 8,9 → 19,4 % | 7,2 → 7,3 → 6,3 % | −0,0 → 12,8 → 23,6 % |

✅ **Le mécanisme est robuste** : sur les **12** mesures de `X`, la part reproduite va de
−0,0 % à 23,6 %, jamais près du seuil de 50 %.

🔴 **Mais l'apport change de signe sur le NO₂ en U10.** Le seuil du relecteur n'est pas
franchi : l'étage reste dans la pile (il est mesuré positivement au protocole du dossier sur
le corpus entier), mais **son apport ne se cite pas pour le NO₂**. C'est écrit dans
`VERITE_DOSSIER` § 12 ter, et le verdict y est **calculé**, pas rédigé.

⚠️ **Les dates de version n'ont pas pu être vérifiées** : le saut normalisé au 2025-11-13
(|z| médian 0,38) est indiscernable d'une date témoin arbitraire (0,37 au 2025-03-15). Le
découpage vaut comme deux sous-corpus disjoints, pas comme une expérience sur les versions.

### 17/08 — la démo corrigée sur les trois défauts que KIMI a mesurés

- 🔴 **La bannière « épisodes manqués » sommait des seuils EMBOÎTÉS.** Une heure à 140 µg/m³
  compte dans ≥ 50, ≥ 100 *et* ≥ 130 ; le total était dominé par le seuil trivial (60 % du
  corpus sur O₃) et annonçait **« 282 224 épisodes manqués de plus »** alors que le corrigé
  en manque **moins** aux deux seuils sévères. Elle porte désormais sur **un** seuil — le plus
  sévère qui ait ≥ 30 épisodes — et publie le détail par seuil, sans total. Rejoué sur les
  chiffres du défaut : rouge −310 637 → **vert +963**.
- 🔴 **« La correction fait jeu égal dans la queue »** était démenti par le graphique juste à
  côté. La légende se **calcule** maintenant depuis les mêmes bandes que la figure, et **dit**
  la dégradation (O₃ 50-100 : −12,7 %).
- 🔴 **« Météo non extraite » s'affichait sur le premier écran** : le chemin était construit
  en `%Y%m` alors que 2025 est en fichiers **groupés** (`era5_metropole_202501_04.parquet`).
  Index en cache lu **dans les données** (§ 4 bis), et la couverture réelle est annoncée.
- **« Elle repose sur trois mois de 2024 »** — réserve périmée qui sous-déclarait notre propre
  corpus. La fenêtre se dérive des données, et la phrase nomme les trois écarts au dossier
  (J0, horaire, base seule).

### 17/08 — les cinq défauts restants de la démo, fermés

- 🟠 **« La correction perd en rappel à l'échelle horaire »** — vrai au seuil trivial,
  **faux aux seuils sévères** (O₃ : rappel 0,489 → 0,584 à 100 µg/m³ ; 0,179 → 0,286 à 130).
  Une loi publiée sur un sous-ensemble (règle E). La phrase se **dérive** désormais de la
  table affichée et nomme les deux sens.
- 🟠 **La réserve du § 11 n'avait pas traversé** : les plis excluent des stations entières
  mais **ne sont pas bloqués spatialement**. Le modèle n'a pas vu la station, il a vu ses
  voisines. Écrit, avec le chiffre — jusqu'à −10 pts sur l'ozone.
- 🟠 **Le bloc « régime du jour » servait un verdict de confiance hors de son périmètre** :
  classification sur la **moyenne nationale des 24 h** quand l'étude classe station × heure
  (stagnation ne se déclenchait que **3,4 %** du temps) ; « −17 % » cité sans ses trois mots ;
  et **PM10 n'a jamais été mesuré** dans cette étude. Le verdict est **retiré** — le régime
  reste descriptif, et la réserve ne s'énonce que sur O₃/NO₂/PM2,5.
- 🟠 **Étiquettes décalées d'un cran** : `BORNES` porte les bornes **hautes**, borne incluse,
  donc 50 µg/m³ est encore « Bon ». On compte `>` et l'on étiquette « ou pire ».
- 🔴 **90 s de page blanche au premier clic sur « Détection »**, `show_spinner=False`. La
  table fait **huit lignes** : elle est précalculée par `build_demo_data.py` dans
  `src/aq/demo.py` (module partagé, pour ne pas importer une page Streamlit). Repli
  conservé mais **bruyant**.
- 🟡 **La carte écrêtait à ±50 %** : 13 stations NO₂ et 2 O₃ hors plage, dont une à
  **−396,9 %** peinte comme une −50 %. Borne dérivée du 98ᵉ centile (±74,5 % sur NO₂,
  ±29,1 % sur PM2,5), et le nombre de stations hors plage est annoncé.

> **Et le calcul est mort deux fois avant d'aboutir**, sur
> `SystemError: more argument specifiers than keyword list entries` dans
> `ints_to_pydatetime` — **le site exact** du `TypeError: 'UTC' object cannot be interpreted
> as an integer` du 08/08. Même signature d'instabilité de plateforme. La reprise a payé du
> premier coup (1,3 min) : *quand un défaut est intermittent, l'ingénierie qui paie est la
> reprise, pas le diagnostic.*

### 17/08 — deux défauts de forme, fermés et mécanisés

- **`var(--bord, #d3dbe1)` × 6 dans les pages 07/08 : `--bord` n'existe pas** (le jeton est
  `--trait`). Le repli s'appliquait à chaque bordure — invisible en clair, faux en sombre.
  `exporter_pdf.py` **refuse d'exporter** sur un jeton fantôme (garde éprouvé dans les deux sens).
- **41 `toFixed()` produisaient un point décimal** dans un document français. 33 sites
  d'affichage passés à la virgule, **la géométrie SVG épargnée nommément** : le PDF passe de
  135 à **11** décimales au point, et les onze restantes sont des licences (« ODbL 1.0 ») et
  un seuil ESA cité littéralement. 61 pages, échelle 1:1 — rien n'a bougé.

### Le contrôle des chiffres, rendu utilisable

`tracer_chiffres_soutenance.py` annonçait **2 780 chiffres sans trace** sur la présentation,
dont ~2 775 étaient des coordonnées de contours dans des `<script type="application/json">`.
Un contrôle qui rend 2 780 alertes ne se lit pas. Il exclut désormais les blocs `script` et
`style`, les attributs et les entités — **97 chiffres réellement lisibles sans trace**,
chacun pointant sa vraie ligne. Reste à arbitrer : ce sont des mesures réelles issues
d'**autres rapports** que la source unique.

### Le PDF était amputé, et aucun contrôle ne pouvait le voir

Une revue externe a établi que **le document imprimé ne contenait pas le chiffre qu'il
désigne lui-même comme le seul citable** : un tableau de 805 px dans une colonne de 615 px
défile à l'écran et **disparaît sur papier**. Le contrôle mesurait la largeur du *document*
(718 ≤ 718, vert) sans voir l'écrêtage *interne*.

**Six défauts**, dont **cinq largeurs plancher écrites en dur** et un `text-overflow:
ellipsis` qui supprimait une phrase éditoriale entière. Tous corrigés ; `exporter_pdf.py`
**refuse désormais d'exporter** un PDF écrêté et nomme l'élément fautif.

### Les règles nées de la nuit — `CLAUDE.md` § 0

**A** seuils dérivés · **B** un budget par unité · **C** le code de sortie appartient à la
dernière commande · **D** une comparaison nomme son axe · **E** deux sous-ensembles avant
publication · **F** l'état d'un shell ne traverse pas une commande · **G** une file par
ressource · **H** une colonne porte un rôle, jamais une identité · **I** la concurrence se
compte par ressource · **J** une leçon vit à un endroit · **K** toute règle solde une dette.

Neuf sur onze sont **exécutables** : `lancer_controle.sh`, `file_ressource.sh`,
`auditer_regles.py`, `aq.rapport`, `aq.eval.critere.tient_sur_sous_ensembles`.

### ⚠️ Rien n'est commité

**Une centaine de fichiers** modifiés ou créés. Sur une machine à dix-sept paniques noyau,
c'est le risque le plus concret de la nuit.

---

## 🟠 LE 15/08 — UN LOT TOURNE : le lire AVANT de lancer quoi que ce soit

**`lot_optuna_reglage.sh PM10 PM25`**, relancé le **15/08 à 09 h 32**, porte les deux derniers
polluants à **200 essais Optuna** — la cible d'O₃ et de NO₂, sans quoi les quatre ne se
comparent pas.

| | |
|---|---|
| **Où il en est** | ✅ **O₃ 201** (02/08) · ✅ **NO₂ 200** (14/08 01 h 37) · 🟠 **PM10 en cours** · ⬜ PM2,5 non commencé |
| **Durée attendue** | fin vers **23 h le 15/08**, extrapolée d'une cadence **mesurée** (~27 essais/h : 40 essais en 88 min) — pas d'une passe unitaire |
| **Reprise** | **native** : Optuna vit dans `reports/optuna/mos_<P>_lgbm.db`, un segfaut ne perd que l'essai en cours |
| **Relanceur hôte** | ✅ **lancé à 10 h 52**, 20 relances / **18 h** — journal `C:\Users\Cyril\relance_optuna_reglage.log` (le lire avec `Get-Content -Encoding UTF8`) |
| **Où en est-il, en une ligne** | `bash scripts/optuna_progression.sh PM10 PM25` — compte VIVANT lu dans le `.db`, avec l'âge de la dernière écriture |
| **Est-ce fini ?** | `bash scripts/optuna_reglage_complete.sh` — rend 0 quand les trois sont à 200 |
| **À faire quand il finit** | `python3 scripts/gain_reglage.py --tous` (≈ 10 min), puis `python3 scripts/page_duel_prevair.py && python3 scripts/injecter_pages.py && python3 scripts/exporter_pdf.py && python3 scripts/verite_dossier.py`, puis **republier l'artefact** |

**Ce qu'il complète** : le bloc ③ de la page 07 et la § 10 sexies affichent *« en cours »*
dans la colonne « notre réglage ». Le reste de la page est **complet et citable**.

**Le premier chiffre est tombé** : NO₂, 200 essais, test jamais consulté —
**RMSE 13,5616 → 12,8937, soit +4,92 %** sur l'axe **SPATIAL** (gain contre CAMS : +39,59 %
→ +42,57 %). À rapprocher d'O₃ à **+4,96 %**, et des **+1,01 % au plus** que le réglage
rapporte à leur krigeage. ⚠️ **Axe spatial pour nous, temporel pour eux — les deux ne
s'additionnent pas**, et un réglage gagnant en spatial peut perdre en temporel.

### 🔴 Ce que le 14/08 a coûté, et la règle qui en sort

**31 heures perdues.** Le lot du 13/08 est mort à **02 h 21** sur la **17ᵉ panique noyau**
(signature `release_pages` / `free_pages_and_swap_cache` — identique **17/17**, rien de neuf).
Le relanceur hôte, lui, était mort **quatre heures plus tôt**, à 22 h 27.

Pourquoi : ses **20 passes** ne distinguaient pas une **relance** d'une simple **constatation**
que le lot tourne encore. NO₂ ayant tourné 5 h d'un seul tenant, les 20 passes ont été brûlées
en **40 minutes** à écrire « un lot tourne déjà ». Le garde-fou s'est épuisé à regarder.

> **On borne un nombre d'ÉVÉNEMENTS et une DURÉE de surveillance séparément. Un compteur
> unique borne le mauvais.** Les cinq relanceurs sont corrigés (commit `3136d62`) : budget de
> relances d'un côté, échéance horaire de l'autre, et le message de fin **nomme** celle qui a
> cédé — « épuisé » et « expiré » appellent des gestes opposés.

⚠️ **Et la ligne de veille portait le défaut qu'elle prétendait corriger** : elle affichait le
compte du **CSV**, que `optuna_mos.py` n'écrit qu'à la **fin** d'une exécution. Trente-sept
lignes d'affilée annonçaient « PM10(0) » pendant que l'étude passait de 32 à 61 essais —
**un compteur immobile est indiscernable d'un lot gelé**. C'est la § 1 quinquies rejouée dans
le geste même qui prétendait l'appliquer.

---

## 🆕 LE 12/08 — nouvelle lane « Découverte », et c'est par là qu'on reprend

Cyril a ouvert un chantier distinct du dossier technique : **des documents simples, pour un
lecteur non spécialiste**. Le premier est **fini, vérifié au navigateur et publié**.

| | |
|---|---|
| **Fichier** | `reports/figures/Découverte_ATMO.html` — autonome, thème clair/sombre, sans dépendance externe |
| **Artefact** | **PRIVÉ** — `25b7f4bf-74b5-4b8f-8294-16dba1428ba0` · à partager depuis le menu de la page |
| **Trame** | 7 chapitres dictés par Cyril : effets sanitaires → sources de données → le RMSE → stratégie AASQA → ce qui améliore le score → directive 2024/2881 → spatialisation |
| **Nouveau calcul** | `scripts/exposition_oms.py` → `reports/exposition_oms.csv` |

**Le chiffre neuf que ce document a produit** : sur les moyennes annuelles 2025,
**238 stations PM2,5 sur 243 — 97,9 % — dépassent la ligne directrice OMS** (médiane 8,97 pour
une ligne à 5). NO₂ 62,8 %, PM10 47,8 %. En Occitanie, **17 stations PM2,5 sur 17**. Lu en
multiples de la ligne OMS, cela donne l'angle qui relie santé et droit : **la valeur limite
PM2,5 en vigueur vaut 5× la ligne sanitaire, celle de 2030 la vaudra encore 2×.**

⚠️ Ce comptage porte sur les **lignes directrices OMS**, pas sur les **valeurs limites** de la
§ 5 bis. Les deux ne se citent jamais l'une pour l'autre.

**➡️ La suite appartient à Cyril** : il a écrit « la 1ère », donc d'autres documents sont
prévus — **leur sujet n'est pas connu, le demander avant de commencer**.

**Trois pièges de mise en page rencontrés, tous muets** — détail dans la fiche mémoire
« Série Découverte » : une colonne de grille nommée ne traverse pas un descendant · un `<li>`
en grille à 2 colonnes avec 3 enfants écrase son texte sur 30 px (la page est passée de 24 000
à 47 600 px de haut sans rien lever) · un `style="margin: …"` en ligne écrase le débord.
**Le contrôle qui les attrape est la mesure au navigateur**, pas la relecture du CSS :
`scrollWidth` contre `innerWidth` à six largeurs, hauteur totale, géométrie des colonnes.

**Ordre de lecture pour arriver sur ce dépôt :**

1. **`CLAUDE.md`** — les règles, et les heures que chacune a coûtées. **Non négociable.**
2. **Ce fichier** — l'état, ce qui est fait, ce qui reste.
3. **`reports/VERITE_DOSSIER.md`** — **la source unique des chiffres**. Tout chiffre du dossier
   absent d'ici est à retirer ou à re-mesurer. Régénérable : `python3 scripts/verite_dossier.py`.

---

## ① En une minute

| | |
|---|---|
| **Objectif** | candidature spontanée à **Atmo Occitanie** — échéance **22/08/2026**, soit **7 jours** |
| **Dossier** | ✅ **déposable**. HTML autonome **9 pages**, PDF **60 p.**, dépôt public **à jour et poussé** |
| **Git** | arbre propre, HEAD `3136d62` |
| **Machine** | 🟠 **occupée** — un lot tourne, voir ci-dessus · 🔴 **matériel défaillant**, voir § ⑤ |
| **Ce qui tourne** | 🟠 **`lot_optuna_reglage.sh PM10 PM25`** (depuis le 15/08 09 h 32, fin ~23 h) + son relanceur hôte · `prevair-archive.timer` (automatique, ne rien faire) |
| **Chiffres** | `VERITE_DOSSIER.md` — **193 lignes de chiffres**, régénéré le 13/08 à 21 h 45 (**§ 10 sexies** ajoutée) |
| **Contrôle** | `verifier_dossier_candidature.py` → **20 vérifiés, 0 en écart** (11/08 23 h 55, après publication) |

🟢 **Reprise après extinction** — la session du 11/08 est intégralement poussée. Le récit
complet (résultats, décisions, suite) est dans la mémoire, fiche « Journée du 11 août ».
**Rien n'est à recalculer ni à revérifier.**

**Les pages territoriales ont gagné 7 figures** : contexte publié (calendrier d'épisodes,
régime de dispersion, apports extérieurs) et nos mesures (matrice territoire × polluant,
profil par polluant, rang des départements, position parmi les 84). Régénérables par
`python3 scripts/pages_regions.py` — ~6 min, aucune dépendance à un lot.

**Le geste à faire en arrivant** : `git status` doit être vide. `/mnt/d` a déjà perdu des
écritures **sans erreur** ; si des fichiers manquent, `git checkout` les restaure.

---

## ② Ce que le projet est, en trois phrases

Post-traitement statistique des prévisions **CAMS Europe** (maille 0,1°, soit ≈ 8 × 11 km aux
latitudes françaises). Un modèle à gradient boosté apprend le **résidu** `observation − CAMS` à
partir de variables disponibles à l'heure d'émission, station par station.

**Le cadrage n'est pas « j'ai construit un modèle »** — la méthode est publiée (Bertrand et al.
2023 ; PREV'AIR corrige déjà par apprentissage). C'est **« j'ai évalué des produits officiels
dans les conventions du référentiel, trouvé où ils échouent, et mesuré ce qu'une correction peut
et ne peut pas faire »**. L'article 13 de l'arrêté du 16/04/2021 impose précisément cette
évaluation annuelle à chaque AASQA.

---

## ③ Ce qui est FAIT — et ne se refait pas

### Les mesures

| famille | état | où |
|---|---|---|
| **La pile complète, 4 polluants** | ✅ clos, étage `tendance` compris | `VERITE_DOSSIER` § 12 |
| **L'ablation, 4 polluants** | ✅ **clos le 11/08** — la seule lecture indépendante de l'ordre | § 12 bis |
| Double aveugle journalier | ✅ 4 polluants | § 0 |
| Conformité **FAIRMODE** | ✅ NO₂ 41,4 % → **96,2 %** | § 5 |
| Détection, front précision–rappel | ✅ | § 8, § 10 |
| Épisodes réellement déclenchés | ✅ **2/33** — la mesure la plus défavorable, publiée | § 14 |
| Barre **PREV'AIR** | 🟠 mesurée sur **9 jours** seulement | § 10 ter |
| Champs spatialisés par région | ✅ France, Occitanie, Nouvelle-Aquitaine | — |

**Le résultat le plus fort de l'ablation** : `geoscf` est **le seul levier qui paie sur les quatre
polluants** (+1,62 à +2,34 pt) et le seul dont les deux lectures coïncident — parce que c'est la
seule information venue de **l'extérieur** de CAMS. Les autres réarrangent ce que CAMS contient
déjà, donc se recouvrent et se volent leur crédit selon leur rang dans l'empilement.

⚠️ **L'ablation est une MESURE, pas une SÉLECTION.** Élaguer les familles à faible apport puis
publier le score de la pile élaguée **sur ces mêmes plis** est le biais de criblage mesuré à
**×2 à ×4** sur ce dépôt.

### Les livrables

| pièce | état | date |
|---|---|---|
| **`reports/figures/vue_territoires.html`** — vue navigable France → rég. → dép. | ✅ **publiée** `90a78c8f-…` | 11/08 |
| `reports/figures/presentation_atmo.html` — **9 pages** (07 = duel PREV'AIR, 08 = la limite), autonome | ✅ | 11/08 23:50 |
| PDF **58 pages** — régénéré par `exporter_pdf.py`, échelle 1:1 vérifiée | ✅ | 11/08 23:50 |
| **Artefact publié** `6ff4908f-bdb3-4a6b-8499-65aa7a688e98` | ✅ **privé**, à jour (page 08) | 11/08 23:55 |
| 106 pages territoriales (84 dép. + 13 rég. + index + champs) | ✅ | 10/08 |
| `docs/NOTE_ATMO_OCCITANIE.md` · `SOUTENANCE_*` · `LETTRE_*` | ✅ **gitignorés** | 10/08 |
| Démo Streamlit `app.py` | ✅ **4 polluants, échéance J0 affichée**, piloté et vérifié | 11/08 |
| `reunions/` — 6 ateliers simulés | ✅ **gitignorés** (§ ⑦) | 11/08 |

🔴 **Deux gestes n'appartiennent qu'à Cyril** — personne d'autre ne peut les faire :
1. **Partager l'artefact** depuis le menu de la page. Il est **privé** : le lien ne s'ouvrira pas
   pour le destinataire tant que ce n'est pas fait.
2. **Le tester en navigation privée** avant l'envoi. En repli, la pièce jointe HTML ne dépend
   d'aucun service.

---

## ④ Ce qui RESTE — file d'attente, par ordre de valeur

| # | tâche | coût | pourquoi |
|---|---|---|---|
| ~~1~~ | ✅ **FAIT le 11/08** — le seuil 2030 est chiffré : `scripts/seuils_2030.py` → `VERITE_DOSSIER` **§ 5 bis**. **France : 6 stations en dépassement aujourd'hui → 109 en 2030, × 18,2.** Occitanie 2 → 5, et **4 départements sur 13 sans aucune station** : leur conformité 2030 ne peut pas être posée depuis la mesure | — | — |
| ~~2~~ | ✅ **FAIT le 11/08** — duel étendu à **10-11 jours** (28/07 → 08/08), **gagnant sur les 4 polluants** : O₃ +6,3 %, NO₂ **+48,1 %**, PM10 +38,9 %, PM2,5 **+59,9 %** de RMSE. ⚠️ **10 jours ne concluent rien** — ordre de grandeur, la fenêtre se cite toujours. Butée nommée : PREV'AIR n'a pas archivé le 08-09, notre CAMS s'arrête au 08-10 | — | — |
| ~~2 bis~~ | ✅ **FAIT le 11/08** — `duel_prevair.py` porte désormais `tendance` + `typologie` : O₃ **+6,0 %**, NO₂ **+51,0 %**, PM10 **+45,5 %**, PM2,5 **+60,9 %**. Les trois autres familles **ne peuvent pas** y entrer — GEOS-CF et les membres s'arrêtent au 01/08/2026, les feux à juin 2025. Limite de **fraîcheur**, pas de conception : ces écarts restent des **minorants** | — | — |
| ~~3~~ | ✅ **FAIT le 11/08** — **page 07 « La barre réelle »** dans la présentation (commit `c24c322`), PDF 56 p., artefact republié. Chiffres relus depuis `duel_prevair_<P>.csv`, jamais saisis ; la fenêtre est affichée dans le chapeau ET dans la règle finale, toutes deux dérivées de la donnée | — | — |
| ~~3 bis~~ | ✅ **FAIT le 11/08** — duel contre **LEUR MÉTHODE** sur les **4 polluants** (commit `ae3aca2`) → `VERITE_DOSSIER` **§ 10 quinquies**. Leur chaîne (CHIMERE + krigeage) contre la nôtre, J+1, station cachée : O₃ 13,55 → **10,76** · NO₂ 18,28 → **14,18** · PM10 7,74 → **6,05** · PM2,5 5,62 → **3,91**. 🔑 **Le résultat qui compte n'est pas notre gain : CHIMERE brut est plus mauvais que la médiane de l'ensemble dont il est MEMBRE sur 3 polluants sur 4** — jusqu'à 49 % sur O₃. Le point de départ pèse autant que la méthode, et cette table est la première à les séparer. Leur krigeage fonctionne (jusqu'à −27,4 % sur CHIMERE) ; à départ égal l'apprentissage le bat **4/4**. ⚠️ **Ce n'est pas PREV'AIR** : leur CHIMERE est national et assimilé, le nôtre est le membre européen à 10 km — la réserve accompagne le tableau | — | — |
| ~~4~~ | ✅ **FAIT le 11/08** — `reports/figures/vue_territoires.html`, **publiée** : https://claude.ai/code/artifact/90a78c8f-b714-4b61-adf8-5cb292a6a0e5 (**privée**, à partager). Carte cliquable France → 13 régions → 96 départements, 4 polluants, échéance 2030, et le contexte **sourcé item par item** sur 84 départements. Régénérable : `python3 scripts/vue_territoires.py` puis réinjecter le JSON dans `_vue_template.html` | — | — |
| ~~5~~ | ✅ **FAIT le 11/08** — démo rafraîchie, **PM10 ajouté**, et l'échéance **J0 enfin affichée** (elle n'était affirmée nulle part). ⚠️ **Deux des trois retards annoncés n'existaient pas** : `fit_mos.py` ne contient aucune occurrence de `tendance`, et pour cause — `tendance` et GEOS-CF vivent dans la chaîne **journalière**, la démo montre le MOS **horaire**. Les y attendre confondait deux piles. Le seul retard réel était PM10, et le blocage tenait en un mot : `choices=["O3","NO2","PM25"]` dans l'`argparse` de `fit_mos.py`, alors que panel, bandes ATMO et table des espèces le portaient tous. Ajusté en **5 min**. Vérifié en pilotant l'app (Playwright) : 4 polluants proposés, **6 pages sans exception** sous PM10 | — | — |
| ~~6~~ | ✅ **FAIT le 11/08** — part des stations dégradées re-mesurée → `VERITE_DOSSIER` **§ 11 bis**. Le « 23 % » est **retrouvé** : c'était l'épreuve *temporelle*, citée sans son épreuve. **La part va de 2,1 % à 42,5 % selon l'ÉPREUVE**, pas selon le polluant. Deux lectures qui n'étaient pas dans la réserve d'origine : le **NO₂ est à l'inverse des trois autres** (le plus dégradé station cachée, le moins station vue — son gain est un biais de *site*) ; et **une part élevée n'est pas une part grave** — 42,5 % sur PM2,5 s'adosse à un gain médian de **+2,5 %**, contre 7,8 % / **+35,6 %** sur NO₂ spatial. ⚠️ Mesuré sur une pile **sans l'étage `tendance`**, sens de l'écart non mesuré. Régénérable : `bash scripts/lot_oof_typo.sh` puis `python3 scripts/stations_degradees.py --variante typo` | — | — |
| ~~7~~ | ✅ **FAIT le 11/08** — **page 08 « La limite »** dans la présentation (commit `7980654`), PDF **58 p.** à l'échelle 1:1, artefact republié. C'est la seule page qui dise où la correction ÉCHOUE. Chiffres relus depuis `stations_degradees_h2.csv`, bornes de la thèse dérivées en JS ; le script **lève** si le CSV croise deux variantes | — | — |
| ~~8~~ | ✅ **FAIT le 13/08** — § 10 quinquies **fondue dans la page 07** (commit `75a5670`), qui porte désormais **trois lectures** : ① leur produit 11 j · ② leur méthode 3 ans · ③ le réglage des deux côtés. PDF **60 p.** à l'échelle 1:1, trois tables vérifiées **remplies** au navigateur. 🔑 Le résultat porté par ② est bien que **CHIMERE brut est moins bon que la médiane de l'ensemble dont il est MEMBRE sur 3/4 — jusqu'à 49 % sur O₃**, pas notre gain. Et ③ répond à une remarque de Cyril : la réserve « on ne leur donne pas deux chances » était une **affirmation non mesurée**, elle vaut **au plus +1,01 %** pour eux et **elle les fait perdre sur 2 polluants sur 4** → `VERITE_DOSSIER` **§ 10 sexies** | — | — |
| **8 bis** | Finir la **moitié « notre réglage »** du bloc ③ | faible, mais **long** | Le lot tourne (voir l'encadré 🟠 en tête). Quand `optuna_reglage_complete.sh` rend 0 : `gain_reglage.py --tous`, puis régénérer page + PDF + `VERITE_DOSSIER`, puis republier. ⚠️ **Le chiffre attendu n'est pas un détail** : O₃ donne déjà **+4,96 %** contre **+1,01 %** à leur krigeage — si les trois autres confirment, la précaution de la § 10 quinquies jouait **contre nous**, et les écarts publiés sont des minorants de ce côté-là aussi. ⚠️ Axe **SPATIAL** pour nous, **TEMPOREL** pour eux : les deux ne s'additionnent pas |
| **9** | Préparer la **soutenance** | moyen | Le dossier est fini ; ce qui reste risqué est de le défendre. La matière existe et n'a jamais été mise en forme d'oral : quel chiffre pour quel protocole, les objections attendues (périmètre, antériorité, 2 épisodes sur 33), et les réponses aux questions dures. **Le plus gros risque résiduel du projet à 11 jours de l'échéance.** |

---

## ⑤ 🔴 LA MACHINE — à lire avant de lancer quoi que ce soit

**Le matériel corrompt la mémoire.** Ce n'est pas une hypothèse : c'est mesuré, et le diagnostic
est clos depuis le 11/08.

📏 **17 kernel panics** dans `%LOCALAPPDATA%\Temp\wsl-crashes\`, du 04/08 au **14/08** — dont deux
le 11/08 au soir (17 h 00 et 18 h 10) et la **17ᵉ le 14/08 à 02 h 21**, qui a emporté le lot
Optuna. Signature **unanime** : `release_pages` / `free_pages_and_swap_cache` /
`do_vmi_align_munmap` **17/17**, zéro panic hors de ce chemin, et le contrôle
`CONFIG_DEBUG_LIST` du noyau qui **ne se déclenche que sur un pointeur corrompu**.

⚠️ Le 14/08, **Windows n'est pas tombé** — aucun `Kernel-Power 41`, le dernier date du 10/08.
C'est la **VM seule** qui est morte : précisément le mode que la reprise interne d'un lot ne
couvre pas, et que seul un relanceur hôte peut rattraper.

C'est **la même corruption** que les segfauts pandas/LightGBM et que les `TypeError: 'UTC' object
cannot be interpreted as an integer` — pointeur noyau corrompu → panic ; pointeur utilisateur
corrompu → segfault ; valeur corrompue → exception absurde. **Un seul défaut, trois visages.**

**Ce que ça implique en pratique :**

- **Aucune ligne de Python ne réparera cela.** Ce qui paie est la **reprise** : les lots relisent
  leur `.partiel` et reprennent sur le **nom** des configurations déjà mesurées.
- 🔴 **La reprise du lot ne suffit pas — elle ne couvre qu'UN des deux modes de mort.** Les
  `ESSAIS_MAX` d'un lot protègent du **segfault**, où le processus meurt et la boucle shell
  survit. Quand c'est **la VM** qui est démontée, la boucle meurt avec elle et *personne ne
  relance* : le 11/08, le duel est resté muet 25 minutes et son silence se lisait comme « ça
  tourne ». Il faut un relanceur qui vive **chez l'hôte** — `scripts/relance_ablation.ps1`,
  `scripts/relance_duel_chimere.ps1`. **Tout `lot_*.sh` qui dure se livre avec son
  `relance_*.ps1` ET son `*_complete.sh` : trois fichiers, pas un.** Deux pièges qui rendent le
  relanceur silencieusement mort — un `.ps1` **sans BOM UTF-8** ne parse pas (PowerShell 5.1 le
  lit en Windows-1252), et `wsl.exe -- bash -lc` est un shell de **login**, donc sans conda.
  🔴 **Troisième piège, mesuré le 14/08 : le relanceur se dimensionne sur la DURÉE du lot.**
  Un compteur unique de « passes » ne distingue pas **relancer** de **regarder**, et un lot
  sain qui tourne cinq heures épuise le budget en quarante minutes. Le relanceur meurt alors
  *avant* le lot qu'il protège, et son « ARRÊT SANS ABOUTIR » s'écrit à 22 h 27 dans un
  journal que personne ne lit. **Deux bornes séparées — un budget de relances, une échéance
  horaire — et le message de fin nomme celle qui a cédé.**
- **Les résultats ne sont PAS faux.** Vérifié : deux exécutions séparées par sept crashs rendent
  les mêmes chiffres à la décimale. **Les pannes sont bruyantes, pas silencieuses.**
- La mémoire est **hors de cause** (pic 18,9 Go sur 70 ; hôte jamais sous 52 Go libres).
- ⚠️ `kern.log` **ne sert plus qu'à dater** : depuis `PYTHONFAULTHANDLER=1`, les signaux 11 sont
  la **ré-émission** par faulthandler. **Ne rien conclure d'un RIP.**

**🔴 Les réparations, dans cet ordre — elles n'appartiennent qu'à Cyril. L'ordre a été CORRIGÉ
le 11/08 : les fiches antérieures mettaient la RAM en premier, et c'était mal classé.**

Ce que le matériel signe réellement, mesuré le 11/08 : **9 événements WHEA, dont ZÉRO ne mentionne
la mémoire** et **3 nomment le processeur** — « cœur du processeur · Corrected Machine Check ·
**Internal parity error** · APIC 33 ». La RAM était en tête parce que le geste est gratuit et prend
5 minutes, pas parce que la preuve la désignait.

① **Mettre à jour le BIOS.** 1805 date du 30/10/2024 et porte le microcode **0x12B** (confirmé au
registre : `2B010000`) — le correctif d'août 2024, qui *arrête* la dégradation Raptor Lake sans
annuler celle déjà subie. ASUS a publié depuis des versions plus récentes pour la PRIME Z790-A
WIFI. Gratuit, peu risqué, vise l'hypothèse principale.
② **RMA Intel** sur l'i9-13900KF si ça persiste — garantie étendue à 5 ans, et
`WHEA-Logger ID 19 — Internal parity error` est déjà journalisé : c'est la pièce du dossier.
③ **Retirer les 2 × 16 Go** — maintenu, mais requalifié en **expérience pour éliminer une
variable**, pas en réparation. Les 4 barrettes sont de la même marque (G.Skill) mais de deux
modèles : `F5-6000J3040G32G` (DDR5-6000 CL30-40, 32 Go) et `F5-6800J3445G16G` (DDR5-6800 CL34-45,
16 Go). ⚠️ **Les quatre tournent pourtant à la même vitesse configurée (3600) à 1,1 V JEDEC**,
bien sous les deux spécifications : la carte a déjà neutralisé l'écart. Ce qui reste mixte est la
capacité, donc probablement le **rang** — et le contrôleur mémoire est *dans le processeur*.
④ Pour trancher la RAM définitivement : **MemTest86 une nuit**, pas `mdsched.exe`.

⚠️ **Deux réserves, à ne pas escamoter** : les 3 erreurs WHEA datent du **24/06**, six semaines
avant la série de plantages — elles prouvent que ce processeur produit des erreurs de parité
internes, **elles ne datent pas les crashs**. Et une *corrected* machine check est corrigée : c'est
un marqueur, pas la cause directe. Ce qui penche : **une barrette défaillante corrompt à des
adresses particulières, un cœur fautif corrompt ce qu'il calcule, n'importe où** — et le défaut
observé se déplace (listes de pages du noyau, pandas, LightGBM, une valeur dans une fente
d'argument entier). C'est un profil de faute de calcul, pas de faute d'adresse.

---

## ⑥ Ce qui tourne tout seul — NE RIEN FAIRE

**`prevair-archive.timer`** est `enabled` + `active`, avec `Persistent=true` (rejoue au démarrage
la fenêtre manquée) et `Linger=yes`. **Éprouvé le 09/08 : il rejoue seul après un redémarrage.**

- Prochain tir : **20 h 03** · dernier passage : 11/08 14 h 04
- Une date **complète** vaut **40 fichiers**. Une date du jour incomplète l'après-midi est
  **normale**.
- ⚠️ La fenêtre publique est de **~6 jours** : chaque jour non archivé est **perdu
  définitivement**. C'est pourquoi le duel PREV'AIR ne porte que sur 18 dates.

---

## ⑦ Les pièges d'exécution qui ont TOUS récidivé

`CLAUDE.md` porte le détail. Les cinq qui coûtent le plus, en une ligne chacun :

1. 🔴 **`grep` n'est pas GNU grep** — c'est `ugrep --ignore-files`, qui **respecte `.gitignore`**
   et saute donc **toute la présentation** et NOTE/LETTRE/SOUTENANCE. **`command grep` toujours.**
   Contrôle : comparer `grep -rl "" <chemin> | wc -l` à `command grep …`.
2. 🔴 **Le contrôle et la chose contrôlée partagent l'espace de noms.** `pgrep`, `ps`, `grep`,
   `Get-CimInstance` : toute commande qui mentionne le motif entre elle-même dans le résultat.
   Crochets `[m]otif`, et exclure `$$` / `$PID`. **Un garde en faux positif est pire qu'un garde
   absent** — il bloque le travail *et* affirme le contraire de la réalité.
3. 🔴 **On ne tue jamais par motif.** PID explicites, puis **vérifier que le kill a pris**.
   ⚠️ Tuer la coquille d'un lot **ne tue pas son python** (`systemd-run --scope` le reparente).
4. 🔴 **On ne modifie pas un script shell pendant qu'il s'exécute** — bash relit le fichier à un
   décalage d'octets ; le lot meurt sur une `syntax error` dans un fichier pourtant valide.
5. 🔴 **Interop Windows↔WSL — trois frontières, chacune mange quelque chose** :
   un `.ps1` sans **BOM UTF-8** est lu en CP1252 (`—` devient un guillemet) · les **guillemets
   d'un motif** écrit en ligne se perdent dans `PowerShell → wsl.exe → bash -lc` · `bash -lc` est
   un shell de **login**, il ne source pas `~/.bashrc`, **donc pas conda**.
   👉 **Tout motif ou test qui traverse l'interop va dans un FICHIER de script.**

**Outillage de garde, à utiliser plutôt que de réécrire :**
`scripts/machine_libre.sh` (la machine est-elle libre ?) · `scripts/lot_en_cours.sh` (un lot
tourne-t-il ?) · `scripts/ablation_complete.sh` (l'artefact attendu est-il là ?) ·
`scripts/controle_reproduction.py` (les chiffres se reproduisent-ils ?) ·
`scripts/controle_fraicheur.py` (quel artefact est périmé ?) ·
`scripts/veille_hote.sh` (que fait l'hôte pendant un lot ?) ·
`src/aq/ingest/controle.py` (contrôles de chargement).

---

## ⑧ La doctrine des chiffres — à respecter sans exception

**Un gain ne se cite jamais sans trois mots : quel polluant, quelle épreuve, quel périmètre.**
Sur l'ozone, la même correction vaut **de +3,31 % à +22,47 %** selon l'épreuve. Cinq familles de
scores portent des noms voisins et répondent à des questions différentes : `VERITE_DOSSIER`
§ 7 ter les réconcilie. **Confondre deux lignes de ce tableau discrédite le dossier entier.**

**Les limites à énoncer soi-même, avant qu'on les trouve :**
- au seuil de procédure français (180 µg/m³ O₃) : **3 dépassements détectés sur 32** ;
- contre les épisodes **réellement déclenchés** : **2 sur 33** ;
- **une part des stations est dégradée malgré un gain médian positif** — ⚠️ **le chiffre de
  « 23 % » que portait l'ancien `REPRISE.md` est INTROUVABLE dans `VERITE_DOSSIER` et dans tous
  les artefacts** (vérifié le 11/08). **Ne pas le citer tant qu'il n'est pas re-mesuré** : c'est
  une réserve réelle, mais son chiffre ne trace plus ;
- **aucune variable d'émission** dans la pile, maille à 10 km, gradient urbain hors de portée ;
- aucune comparaison au modèle régional d'Atmo Occitanie — **aucun bilan chiffré public n'existe**
  (résultat de recherche, pas preuve d'absence).

> **Écrire qu'une mesure est biaisée puis la publier quand même, c'est la valider.** La réserve
> honnête sert quand on ne *peut* pas corriger, jamais quand on ne l'a pas *fait*.

---

## ⑨ Voir aussi

- `CLAUDE.md` — les règles et les erreurs qui les ont produites. **À relire avant tout code d'E/S,
  tout lot long, toute conclusion tirée d'une mesure.**
- `reports/VERITE_DOSSIER.md` — source unique des chiffres (165 lignes).
- `reports/VERIFICATION_CANDIDATURE.md` — 20 affirmations recalculées contre les pièces.
- `reunions/` — six ateliers **simulés** (aucune personne réelle, aucun propos tenu).
  **Gitignorés** : ils attribuent des positions à des organisations réelles et nommées, et sur un
  dépôt public le bandeau d'avertissement ne protège pas d'une lecture pressée.
- `docs/` — audits, critiques adverses, fiches opérationnelles.
- Mémoire de session : conventions vérifiées, pièges métier, périmètre exact de ce qui est prouvé.
