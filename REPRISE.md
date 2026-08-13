# Reprise — l'état du projet

> **Écrit le 11/08/2026 à 14 h 30, mis à jour le 13/08 à 22 h.** Si la date ci-dessus a plus de deux jours, **méfie-toi de ce
> fichier** : sur ce projet il a déjà été périmé de dix jours tout en s'annonçant comme l'état
> courant. Vérifie par `git log --oneline -5` et `ls -lt reports/` avant de croire ce qui suit.

---

## 🟠 LE 13/08 — UN LOT TOURNE : le lire AVANT de lancer quoi que ce soit

**`lot_optuna_reglage.sh`**, lancé le **13/08 à 20 h 36**, porte NO₂ / PM10 / PM2,5 à
**200 essais Optuna** chacun — la cible d'O₃, sans quoi les quatre ne se comparent pas.

| | |
|---|---|
| **Durée attendue** | **~12 h** — fin vers le **14/08 au matin**. ⚠️ L'extrapolation de la passe unitaire (10 essais → 2 h/polluant) était **optimiste** : la cadence réelle à 68 essais donne **~4 h/polluant**. § 1 ter, une fois de plus |
| **Reprise** | **native** : Optuna vit dans `reports/optuna/mos_<P>_lgbm.db`, un segfaut ne perd que l'essai en cours |
| **Relanceur hôte** | ✅ **lancé** — `relance_optuna_reglage.ps1`, journal `C:\Users\Cyril\relance_optuna_reglage.log` (le lire avec `Get-Content -Encoding UTF8`) |
| **Où en est-il** | `bash scripts/optuna_reglage_complete.sh` — rend 0 quand les trois sont à 200 |
| **À faire quand il finit** | `python3 scripts/gain_reglage.py --tous` (≈ 10 min), puis `python3 scripts/page_duel_prevair.py && python3 scripts/injecter_pages.py && python3 scripts/exporter_pdf.py && python3 scripts/verite_dossier.py`, puis **republier l'artefact** |

**Ce qu'il complète** : le bloc ③ de la page 07 et la § 10 sexies affichent *« en cours »*
dans la colonne « notre réglage ». Le reste de la page est **complet et citable**.

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
| **Objectif** | candidature spontanée à **Atmo Occitanie** — échéance **22/08/2026**, soit **11 jours** |
| **Dossier** | ✅ **déposable**. HTML autonome **9 pages**, PDF **60 p.**, dépôt public **à jour et poussé** |
| **Git** | ✅ arbre propre, HEAD `75a5670` — **synchronisé et POUSSÉ** vers `origin/main` |
| **Machine** | 🟠 **occupée** — un lot tourne, voir ci-dessous · 🔴 **matériel défaillant**, voir § ⑤ |
| **Ce qui tourne** | 🟠 **`lot_optuna_reglage.sh`** (depuis le 13/08 20 h 36, ~12 h) + son relanceur hôte · `prevair-archive.timer` (automatique, ne rien faire) |
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

📏 **16 kernel panics** dans `%LOCALAPPDATA%\Temp\wsl-crashes\`, du 04/08 au 11/08 — dont **deux
le 11/08 au soir** (17 h 00 et 18 h 10). Signature **unanime** : `release_pages` /
`free_pages_and_swap_cache` / `do_vmi_align_munmap` **16/16**, zéro panic hors de ce chemin, et le
contrôle `CONFIG_DEBUG_LIST` du noyau qui **ne se déclenche que sur un pointeur corrompu**.

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
