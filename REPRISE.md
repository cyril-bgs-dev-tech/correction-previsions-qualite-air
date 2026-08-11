# Reprise — l'état du projet

> **Écrit le 11/08/2026 à 14 h 30, mis à jour à 17 h 45.** Si la date ci-dessus a plus de deux jours, **méfie-toi de ce
> fichier** : sur ce projet il a déjà été périmé de dix jours tout en s'annonçant comme l'état
> courant. Vérifie par `git log --oneline -5` et `ls -lt reports/` avant de croire ce qui suit.

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
| **Dossier** | ✅ **déposable**. HTML autonome **8 pages**, PDF **56 p.**, dépôt public à jour, artefact **republié le 11/08 à 17 h 35** |
| **Git** | ✅ arbre propre hors lot en cours, HEAD `65a01d1` |
| **Machine** | ✅ libre · 🔴 **matériel défaillant**, voir § ⑤ — la VM est tombée le 11/08 à ~16 h 58 |
| **Ce qui tourne** | `lot_duel_chimere.sh O3` (lancé 17 h 39) · `prevair-archive.timer` (automatique, ne rien faire) |
| **Chiffres** | `VERITE_DOSSIER.md` — **165 lignes**, régénéré le 11/08 à 16 h 50 |
| **Contrôle** | `verifier_dossier_candidature.py` → **20 vérifiés, 0 en écart** (11/08 17 h 20) |

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
| `reports/figures/presentation_atmo.html` — **8 pages** (07 = duel PREV'AIR), autonome | ✅ | 11/08 17:30 |
| PDF **56 pages** — régénéré par `exporter_pdf.py`, échelle 1:1 vérifiée | ✅ | 11/08 17:30 |
| **Artefact publié** `6ff4908f-bdb3-4a6b-8499-65aa7a688e98` | ✅ **privé**, à jour | 11/08 17:35 |
| 106 pages territoriales (84 dép. + 13 rég. + index + champs) | ✅ | 10/08 |
| `docs/NOTE_ATMO_OCCITANIE.md` · `SOUTENANCE_*` · `LETTRE_*` | ✅ **gitignorés** | 10/08 |
| Démo Streamlit `app.py` | 🟠 **la pièce la moins à jour** | 02/08 |
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
| **3 bis** | 🟠 **Duel contre LEUR MÉTHODE** — `lot_duel_chimere.sh`, en cours sur O₃ depuis 17 h 39 | moyen | AS-CHI est un **krigeage** du résidu, pas un apprentissage. CHIMERE étant un membre de CAMS archivé ici, on rejoue leur chaîne depuis **leur** point de départ, sur nos lignes et sur trois ans — ce que les onze jours du duel direct ne permettent pas. ⚠️ **Ce n'est pas PREV'AIR** : leur CHIMERE est national et assimilé, le nôtre est le membre européen à 10 km |
| ~~4~~ | ✅ **FAIT le 11/08** — `reports/figures/vue_territoires.html`, **publiée** : https://claude.ai/code/artifact/90a78c8f-b714-4b61-adf8-5cb292a6a0e5 (**privée**, à partager). Carte cliquable France → 13 régions → 96 départements, 4 polluants, échéance 2030, et le contexte **sourcé item par item** sur 84 départements. Régénérable : `python3 scripts/vue_territoires.py` puis réinjecter le JSON dans `_vue_template.html` | — | — |
| **5** | Rafraîchir `app.py` (02/08) | moyen | Antérieur à GEOS-CF en production, à `tendance` et aux PM10. Pas faux — le contrôle des 20 chiffres passe — mais le moins à jour. |
| **6** | 🔴 **Re-mesurer la part de stations dégradées** (NO₂ et les autres) | faible | L'ancien `REPRISE.md` annonçait « 23 % » ; **ce chiffre ne trace nulle part** (vérifié le 11/08). La réserve est réelle, le chiffre est perdu. **Le re-mesurer ou cesser de la chiffrer.** |

---

## ⑤ 🔴 LA MACHINE — à lire avant de lancer quoi que ce soit

**Le matériel corrompt la mémoire.** Ce n'est pas une hypothèse : c'est mesuré, et le diagnostic
est clos depuis le 11/08.

📏 **14 kernel panics** dans `%LOCALAPPDATA%\Temp\wsl-crashes\`, du 04/08 au 11/08. Signature
**unanime** : `release_pages` / `free_pages_and_swap_cache` / `do_vmi_align_munmap` **14/14**,
zéro panic hors de ce chemin, et le contrôle `CONFIG_DEBUG_LIST` du noyau qui **ne se déclenche
que sur un pointeur corrompu**.

C'est **la même corruption** que les segfauts pandas/LightGBM et que les `TypeError: 'UTC' object
cannot be interpreted as an integer` — pointeur noyau corrompu → panic ; pointeur utilisateur
corrompu → segfault ; valeur corrompue → exception absurde. **Un seul défaut, trois visages.**

**Ce que ça implique en pratique :**

- **Aucune ligne de Python ne réparera cela.** Ce qui paie est la **reprise** : les lots relisent
  leur `.partiel` et reprennent sur le **nom** des configurations déjà mesurées.
- **Les résultats ne sont PAS faux.** Vérifié : deux exécutions séparées par sept crashs rendent
  les mêmes chiffres à la décimale. **Les pannes sont bruyantes, pas silencieuses.**
- La mémoire est **hors de cause** (pic 18,9 Go sur 70 ; hôte jamais sous 52 Go libres).
- ⚠️ `kern.log` **ne sert plus qu'à dater** : depuis `PYTHONFAULTHANDLER=1`, les signaux 11 sont
  la **ré-émission** par faulthandler. **Ne rien conclure d'un RIP.**

**Les deux réparations, dans cet ordre — elles n'appartiennent qu'à Cyril :**
① retirer les **deux barrettes de 16 Go** (4 DIMM de **deux kits différents** = hors spec ; garder
les 2 × 32 Go) · ② si ça persiste, **RMA Intel** sur l'i9-13900KF (garantie étendue à 5 ans ;
`WHEA-Logger ID 19 — Internal parity error` est journalisé et suffit au dossier).

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
