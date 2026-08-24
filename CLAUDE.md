# Règles du projet — apprises à la dure

Ce fichier ne décrit pas le projet : il consigne les **erreurs déjà commises** et la règle
qui empêche chacune de revenir. Chaque règle porte le chiffre qui l'a fait naître.

À relire avant d'écrire du code d'entrée/sortie, de lancer un traitement long, ou de
conclure d'une mesure.

---

## 0. Les règles exécutables — et la règle qui borne ce fichier

### Le constat qui a produit cette section — mesuré le 16/08/2026

Ce fichier est passé de **440 à 1 062 lignes en huit jours (+141 %)**, et les pertes ont
continué **après** : les **31 heures** du 14/08 sont arrivées sous une règle 1 bis vieille
de seize jours, et le 16/08 j'ai violé **quatre règles que j'avais en contexte au moment
même** — code de sortie lu sur un `echo`, conclusion tirée d'un seul polluant, mécanisme
publié sur trois plis, `cd` traversant quatre commandes.

Le registre complet compte **≈ 88 heures documentées**. Sa colonne décisive n'est pas le
montant, c'est *la règle existait-elle ?* — les pertes précoces ont **créé** les règles, les
pertes tardives sont arrivées **malgré** elles.

> **Le facteur limitant n'est pas la connaissance, c'est l'instant d'application.** Chaque
> ligne de prose ajoutée augmente le coût de récupération sans augmenter l'exécution.

Ce qui a réellement tenu sur ce dépôt n'est jamais narratif : `src/aq/ingest/controle.py`,
la reprise native d'Optuna, le contrôle d'échelle du PDF, le garde-jumeau du relanceur.
**Elles se déclenchent sans qu'on s'en souvienne.**

### 🔑 La méta-règle

> **Une règle violée deux fois après avoir été écrite devient du code, ou elle disparaît.**

La prose qui n'a pas tenu deux fois ne tiendra pas la troisième. Cette règle **borne** le
corpus : `CLAUDE.md` doit *rétrécir* à mesure que `controle.py` grossit. Une règle qu'on ne
sait pas mécaniser et qui a échoué deux fois est un aveu, pas un garde-fou.

### Les six règles, et leur état de mécanisation

Aucune ne porte de constante : c'est ce qui les rend **adaptatives**.

| | règle | mécanisée par |
|---|---|---|
| **A** | **Tout seuil se recalcule depuis la passe unitaire de CETTE exécution.** Aucun délai, budget ou intervalle de veille écrit en dur ni repris d'une exécution précédente. | ⬜ **non mécanisée** — et le dire vaut mieux que d'écrire un utilitaire que personne n'appellerait : du code non adopté n'est pas une mécanisation, c'est de la prose exécutable. |
| **B** | **Un budget par unité, jamais un compteur pour deux.** Événements, durée et volume se comptent séparément, et le message de fin **nomme** celui qui a cédé. | ✅ les 5 relanceurs |
| **C** | **Le code de sortie appartient à la dernière commande.** Donc jamais de `$?` après un tube ou un `echo` — et le verdict porte sur l'**artefact**, qui doit exister *et* avoir été réécrit. | ✅ `scripts/lancer_controle.sh` |
| **D** | **Une affirmation comparative nomme son axe.** Si la référence en utilise un autre, on **mesure sur le sien** avant de publier — la réserve ne tient pas lieu de mesure (§ 4 ter). | ✅ `tracer_chiffres_soutenance.py` · `axes_manquants()` |
| **E** | **Un mécanisme n'est publiable qu'après avoir tenu sur deux sous-ensembles indépendants.** Trois plis ne font pas une loi ; un polluant ne fait pas un mécanisme. | ✅ `aq.eval.critere.tient_sur_sous_ensembles` |
| **F** | **L'état d'un shell ne traverse pas une commande.** Chemins absolus, ou résolus depuis la racine du dépôt — jamais depuis `$PWD`. | ✅ en-tête de `lancer_controle.sh` |
| **G** | **Une file par RESSOURCE : sérialiser dedans, paralléliser entre.** Avant de lancer le premier travail, inventorier les ressources et affecter chaque tâche à la sienne. **Une ressource au repos pendant qu'une tâche attend ailleurs est un défaut**, pas une prudence. | ✅ `scripts/file_ressource.sh` |
| **H** | **Une colonne porte un RÔLE, jamais une identité.** `rmse_candidat` + une colonne `modele`, pas `rmse_realmlp`. Une étiquette qui nomme une identité affirme deux choses ; seule la première survit à une généralisation, et **rien ne voit la seconde mentir**. | ✅ `aq.rapport.exiger_etiquettes_vraies` |
| **I** | **La concurrence se compte par RESSOURCE, jamais par processus.** § 1 interdit d'empiler sur *la même* ; **G** exige de remplir les *distinctes*. Ce ne sont pas deux avis : c'est une seule question — *quelle ressource ce travail consomme-t-il, et combien en reste-t-il ?* | ✅ `file_ressource.sh` (verrou **par nom de ressource**) |
| **J** | **Une leçon vit à UN endroit ; les autres la CITENT.** Le premier lieu où elle est écrite fait foi. Toute récurrence est une **instance** — une ligne, un renvoi — jamais une réénonciation. | ✅ `scripts/auditer_regles.py` |
| **K** | **Toute règle ajoutée solde une dette.** Elle nomme ce qu'elle remplace, ou dit pourquoi rien ne peut l'être. Un corpus qui ne fait que croître se lit de moins en moins. | ✅ `auditer_regles.py` (croissance) |
| **M** | **Deux mesures ne se comparent que sur le MÊME corpus.** *(Ne remplace rien : aucune règle ne portait sur l'identité des ENTRÉES entre deux exécutions — les § 2 bis et 4 portent sur une exécution isolée.)* Ni la fenêtre, ni le nombre de mois, ni le nombre de colonnes, ni le nombre de lignes de test ne le montrent : compléter une famille jointe en `left` ne change que les VALEURS. | ✅ `aq.ingest.controle.empreinte_corpus` · `empreinte_entrees` de la pile |
| **N** | **Une unité présente n'est pas une unité complète** — instance de la § 4, au niveau en dessous : le § 4 exige un artefact complet, N exige que chaque unité DEDANS le soit. Un mois à moitié livré, un jour amputé de trois heures, une colonne du « socle » absente d'un tiers des mois. **Elle remplace le corollaire « vérifier la structure » de la § 4**, qui ne disait pas à quelle profondeur s'arrêter. | ✅ contrôle des heures de `extraire_ifs` · garde de classification de `charger_speciation` |
| **L** | **Une statistique ajustée sur un pli doit être DÉFINIE sur l'autre.** Quand le protocole cache une dimension (station, groupe, mois), toute statistique ajustée *le long* de cette dimension est introuvable de l'autre côté : elle replie, et les deux blocs se retrouvent sur des **échelles différentes** sans qu'aucune exception ne lève. La référence vient d'un découpage qui **croise** la dimension cachée, jamais du pli lui-même. | ✅ `aq.eval.critere.exiger_couverture_de_reference` |

### Ce que chacune a coûté

- **A** — le 10/08 (61 min de gel sous un moniteur à seuil fixe) et le 14/08 (**31 h** sous
  un budget dimensionné la veille). Deux morts par constante périmée.
- **B** — le 14/08 : 20 passes censées protéger d'un défaut structurel, brûlées en
  **40 minutes** à écrire « un lot tourne déjà ». Le garde-fou s'est épuisé à regarder.
- **C** — le 16/08, deux fois en une session. La seconde a fait annoncer « archivage
  PREV'AIR terminé, exit 0 » pour un script qui **n'avait pas tourné** : le `$?` venait de
  l'`echo`, et la redirection avait échoué faute de répertoire. *Un rapport de succès sur un
  travail non fait est pire qu'une erreur : il ferme la question.*
- **D** — le 16/08 : la § 10 sexies de `VERITE_DOSSIER` opposait notre gain de réglage
  (+3,98 à +7,12 %, axe **spatial**) au leur (+1,01 %, axe **temporel**) en concluant « au
  même traitement ». Mesuré sur *leur* axe, le nôtre tombe à **−0,14 à +1,92 %** — du même
  ordre que le leur. La réserve existait, 28 lignes plus bas, et la phrase en gras
  l'affirmait à l'envers.
- **E** — le 15/08 : « le réglage profite aux stations trafic », bâti sur trois plis de NO₂.
  Réfuté deux fois le lendemain — à niveau de pollution comparable p = 0,42, et sur quatre
  polluants **le sens s'inverse**.
- **F** — le 16/08 : un `cd data/raw/prevair` a persisté et cassé quatre commandes, dont
  celle qui a produit le faux succès de **C**. Les deux défauts se sont composés.
- **G** — le 16/08 au soir, relevé par Cyril et non par moi : **charge 0,45 sur 32 cœurs,
  GPU à 1 %**, alors que trois chantiers longs étaient identifiés et attendaient leur tour.
  J'enchaînais **à la main**, un travail après l'autre, en confondant « la concurrence
  n'est pas la réponse par défaut » (§ 1) avec « ne rien lancer en parallèle ». Or la § 1
  dit l'inverse : la concurrence ne sert que si **la ressource est réellement libre** — et
  elles l'étaient.

  **Les ressources de cette machine, et leur limite mesurée :**

  | ressource | plafond mesuré | d'où vient la mesure |
  |---|---|---|
  | service ADS | **3 requêtes simultanées** (6 rejetées, puis HTTP 400 muet) | § 1 |
  | CPU / LightGBM | `n_jobs=4`, **un seul lot** — trois lots concurrents s'effondrent d'un ordre de grandeur | § 1 |
  | GPU | **un entraînement à la fois** | RTX 5090, 34 Go |
  | mémoire | plafond `systemd-run` par lot | § 1 quater |
  | réseau ≠ CPU | l'attente ADS est **84 %** du coût d'une requête et ne consomme aucun cœur | § 1 |

  La dernière ligne est celle qui décide : **une file bloquée sur du temps serveur
  n'occupe rien**, donc elle n'excuse jamais un CPU ou un GPU au repos.

  Et le maillon de chaînage est l'**artefact**, jamais le code de sortie — sinon la file
  suivante démarre sur un travail qui n'a rien produit (§ 0, règle C).
- **H** — le 16/08 au soir. `optuna_realmlp.py` a été généralisé à LightGBM par un paramètre
  `--modele`. La **valeur** est devenue paramétrique, l'**étiquette** est restée écrite en
  dur : `reports/optuna_lgbm_PM10_temporel.csv` portait une colonne `rmse_realmlp`
  contenant… le LightGBM réglé.

  **Coût réel :** j'en ai tiré « RealMLP bat LightGBM de **9 %** sur PM10 », je l'ai écrit
  dans un brief envoyé à un relecteur externe, et c'est **lui** qui a relu le fichier —
  correctement — pour trouver **2,65 %**. *Un tiers a corrigé un chiffre que mon propre
  nommage rendait infalsifiable.*

  > **Une étiquette est une promesse que rien ne vérifie.** `rmse_realmlp` affirme
  > « c'est une RMSE » **et** « c'est RealMLP » ; le premier survit à un refactoring, le
  > second non, et aucune relecture du fichier ne peut le contredire — la valeur est
  > plausible, la colonne existe, le fichier s'ouvre.

  C'est la famille des § 4 bis (un **nom de fichier** ment) et § 4 ter (un **nom d'axe**
  ment), au niveau de la colonne. Le contrôle mécanisé attrape les quatre familles —
  modèle, polluant, axe, échéance — et il **aurait attrapé le défaut J0/J+1 du 02/08**,
  qui avait fait appeler « J+1 » du J0 pendant des semaines.

  ⚠️ **Ce que le garde ne peut pas faire, et c'est structurel** : il ne réfute que les
  identités que l'appelant **déclare** dans son contexte. On ne réfute pas ce qui n'est pas
  affirmé. Déclarer le contexte est donc l'acte qui arme le garde-fou, et il revient à
  celui qui écrit — lui seul sait ce qu'il a calculé.

- **L — la transformation ajustée sur un pli, indéfinie sur l'autre.** *17/08.* Le mécanisme
  de la spéciation venant d'être établi (§ 12 ter du dossier), j'ai voulu remplacer chaque
  composante par son **anomalie** à la climatologie station × mois, et j'ai ajusté cette
  climatologie sur le **pli d'apprentissage** — le geste correct partout ailleurs.

  Il est faux ici : le protocole cache la station **et** le mois, donc **les stations de test
  sont absentes de l'apprentissage par construction**. Leur climatologie n'existait pas,
  chaque ligne repliait sur la moyenne globale, et le modèle apprenait sur des anomalies
  centrées pour prédire sur des valeurs brutes décalées d'une constante.

  > **Deux échelles de part et d'autre du modèle, et rien ne lève.** Le lot tourne, écrit son
  > CSV, rend 0. Le nombre obtenu aurait été lu comme « l'anomalie n'apporte rien », et la
  > piste abandonnée sur un artefact d'implémentation.

  Ce qui l'a attrapé n'est pas une relecture : c'est d'avoir **redemandé d'où venait chaque
  ligne du pli de test**, en écrivant la docstring. La bonne référence est *toutes les
  stations, mois de test exclu* — ce que la production peut faire, puisqu'en un point non
  instrumenté l'archive CAMS existe et que seul le futur n'existe pas.

  **La dette soldée** : § 2 quater demandait de *compter le repli*, et je le comptais — sur le
  périmètre des lignes. Le repli portait ici sur l'**échelle des variables**, que personne ne
  comptait. `exiger_couverture_de_reference` rend le comptage obligatoire au lieu de le
  laisser à la mémoire, et **il a été éprouvé sur le défaut réel** : rejoué avec l'ancienne
  référence, il lève « 100 % du bloc test replie ».

### Le fil commun avec le reste du fichier

Les règles 1 à 4 disent *quoi vérifier*. Celle-ci dit *pourquoi les lire ne suffit pas*, et
impose la seule réponse qui a marché sur ce dépôt : **déplacer la vigilance du lecteur vers
l'exécutable.** Une règle mécanisée n'a plus besoin d'être crue.

---

## 1. La passe unitaire — obligatoire avant tout lot

### La règle

**Jamais de lot lancé en aveugle** — et l'unité testée doit être l'**unité définitive**.
Quatre étapes, dans cet ordre, qui ne se réordonnent pas :

1. **Interroger les limites du service** — plafond par requête, concurrence admise,
   fenêtre d'archive. `estimate_costs` ou équivalent le donne avant tout envoi.
2. **Dimensionner la requête à ces limites** — viser 70-90 % du plafond.
3. **Tester cette requête-là**, sur les deux axes ci-dessous.
4. **Lancer le lot.**

**L'erreur à ne pas refaire : calibrer sur une unité non optimisée.** J'ai testé une
requête d'un mois, puis regroupé par quatre mois, puis réutilisé le débit mesuré sur la
première. Une unité qui n'est pas celle du lot ne calibre rien. Mesurer après coup ne
répare pas non plus : le temps est déjà dépensé.

**Axe résultat — ce que je reçois est-il ce que je crois ?**

- le format est-il celui attendu ? *(un `.nc` peut être une archive ZIP)*
- le contenu est-il **complet** ? compter les pas de temps, les variables, les membres
- les conventions sont-elles celles supposées ? axes, unités, fuseau, ordre

**Axe coût — le lot entier est-il tenable ?**

- interroger la **limite** du service et le **coût** de la requête : `estimate_costs` ou
  équivalent. Viser **70-90 % du plafond**, pas 20 %
- chronométrer la requête unitaire, puis **extrapoler : `t_unitaire × N`**. Si le total
  est inacceptable, corriger la granularité *maintenant*
- si c'est lent, ventiler avant de conclure : attente en file (`created`→`started`),
  calcul serveur (`started`→`finished`), transfert (taille ÷ débit). Comparer au
  **plancher théorique** — volume ÷ débit. Un écart d'un ordre de grandeur désigne autre
  chose que le réseau

Ces deux contrôles coûtent quelques minutes et se rentabilisent dès la première erreur
évitée.

### L'erreur qui a produit cette règle

ERA5 découpé **par mois**, en suivant la consigne du fournisseur « submit small
requests… download one month at a time ». Lot de 144 requêtes lancé, **13 heures** plus
tard, mesure :

- attente en file **756 s** (84 %) · calcul serveur 145 s (16 %) · transfert ~1 s (0,1 %)
- coût de la requête : **26 784 champs pour un plafond de 121 000** — soit **22 %** du
  volume autorisé

Le coût est **par requête**, pas par champ. Demander quatre mois d'un coup tenait sous le
plafond et aurait divisé le temps total par ~4. J'ai payé quatre fois le prix du billet
pour transporter un quart de la charge — et je ne l'ai su qu'une fois le lot presque fini.

**Le plus rageant : j'avais fait la passe unitaire.** Un test sur un mois, qui a bien
attrapé le piège du ZIP. Mais je l'avais menée sur le seul **axe résultat**, sans jamais
interroger le coût ni extrapoler la durée. Une ligne — `estimate_costs` — aurait suffi.
La discipline à moitié appliquée ne protège de rien.

### Les corollaires

- **La consigne du fournisseur répond à SA question, pas à la tienne.** « Petites
  requêtes » protège son service de la saturation ; elle ne dit rien de ton débit. Lire
  l'intention derrière la consigne, puis mesurer.
- **Un coût fixe par requête impose de regrouper ; un coût proportionnel impose de
  découper.** Déterminer lequel s'applique *avant* de choisir la granularité.
- **La concurrence n'est pas la réponse par défaut.** Elle ne sert que si la ressource
  est réellement libre. Deux mesures sur ce projet, l'une distante et l'autre locale :
  - **côté service** — 3 requêtes ADS simultanées passent, **6 sont rejetées**, et le
    client échoue ensuite en HTTP 400 sans nommer la cause ;
  - **côté machine** — un ajustement LightGBM en `n_jobs=-1` prend **5 minutes seul**.
    Trois de ces ajustements lancés ensemble sur 32 cœurs demandent 96 fils : **deux ont
    été tués à 90 minutes sans finir**. Ce n'est pas un ralentissement de 3×, c'est un
    effondrement d'un ordre de grandeur — la contention porte sur la bande passante
    mémoire, pas sur les cœurs.

  **Une bibliothèque qui prend déjà tous les cœurs ne se parallélise pas en la lançant
  plusieurs fois.** Soit on enchaîne, soit on borne `n_jobs` explicitement.
- **Instrumenter le lot dès son lancement** : journal horodaté, compteur de progression,
  et de quoi extrapoler la fin. Un lot muet ne se corrige qu'une fois terminé.

---

## 1 bis. Piloter un lot lancé — « lancé » n'est pas « fait »

### La règle

Un lot lancé n'est pas un lot en cours, et un lot en cours n'est pas un lot qui
progresse. Quatre gestes, dans cet ordre :

**Avant de lancer.** Vérifier qu'un jumeau ne tourne pas déjà — `ps aux | grep` le nom du
script. Après un `pkill`, **vérifier qu'il a pris effet** : le code de sortie ne suffit
pas.

**Et ce garde ment dans les deux sens.** Un faux positif est pire qu'un garde absent : il
bloque le travail *et* affirme le contraire de la réalité, ce qui envoie chercher un
processus fantôme. Coût : 08/08 à 23 h 06, lot refusé pour un jumeau inexistant.

> **Mécanisé le 24/08 — `scripts/pids_de.sh`.** Trois formes du même défaut ont
> échoué : le `[m]` ne protège que contre soi, pas contre une autre occurrence dans
> la même commande (17/08) ; exclure `$$`/`$PPID` laisse passer le grand-parent d'une
> substitution (23/08) ; et exclure toute la lignée laisse encore passer les commandes
> qui **mentionnent** le motif. Le script lit `/proc`, exclut ses ancêtres et compare
> aux **arguments** un par un. Adopté par les trois gardes du dépôt.

**Si la conception du lot a changé, recalibrer.** La passe unitaire de la règle 1 vaut
pour la granularité qu'elle a mesurée. Regrouper les requêtes, changer l'emprise ou le
nombre de variables **invalide l'étalonnage**.

**Installer le contrôle avant d'annoncer une durée.** Un `Monitor` qui remonte la
progression, les erreurs serveur et surtout **l'arrêt du processus** rend l'estimation
réfutable. Un lot mort est silencieux : sans surveillance de l'arrêt, on croit qu'il
tourne encore.

**Pendant, se demander : qu'est-ce qui est bloqué si je l'arrête maintenant ?** Si la
réponse est « rien », arrêter. Un téléchargement à 92 % dont les 8 % restants ne servent
à rien est terminé.

**Le journal du lot ne filtre jamais sur les seules lignes de succès.** Un
`| grep -E "Écrit|0 échec"` jette précisément ce qu'on avait besoin de lire. Et le contrôle
de fin porte sur l'**artefact attendu**, jamais sur le code de sortie : `[ -f "$cible" ] ||
echo "AUCUN fichier écrit"`.

**On ne modifie pas un script shell pendant qu'il s'exécute.** Bash relit le fichier au fil
de l'exécution, à un décalage d'octets ; une insertion en amont décale tout ce qui suit et
le lot meurt sur une `syntax error` dans un fichier pourtant valide. Éditer une copie, puis
remplacer une fois le lot fini.

### Les erreurs qui ont produit cette règle — toutes le 29/07, toutes en une journée

- **« Dans une heure ce sera fini. »** Deux heures et demie plus tard : zéro fichier
  écrit, et je ne l'ai su qu'en étant interrogé. L'estimation venait d'un débit mesuré sur
  des requêtes **d'un mois**, réutilisé après un regroupement **par quatre mois** — la
  part serveur quadruple, seule l'attente en file est amortie.
- **Deux processus concurrents sur le même service**, lancés à six heures d'intervalle
  sans vérifier le premier : **six requêtes parallèles au lieu de trois**, soit exactement
  la condition de rejet documentée plus haut. **Dix-sept heures** de boucle sur des
  erreurs 500 — alors que le service fonctionnait, récupération testée en 0,4 s.
- **Un téléchargement poursuivi vingt heures** pour compléter des mois de 2019, alors que
  la seule analyse qui l'utilise porte sur 2024, déjà complet.

### Et la récidive, le 31/07 — les deux mêmes gestes, deux jours plus tard

- **Deux `lot_ifs.sh` concurrents**, lancés à dix minutes d'écart sans vérifier le premier.
  Ils parcouraient la **même liste de mois** avec reprise par existence de fichier : le
  second allait écrire `ifs_metropole_202411.parquet.partiel` pendant que le premier
  l'écrivait. Deux mois — **2024-09 et 2024-10** — sont sortis du lot **sans parquet**,
  alors que leurs 30 jours affichaient « 0 échec(s) ». Re-décodés seuls après l'arrêt du
  doublon : succès immédiat, 114 240 lignes. La collision était bien la cause.
- **Et je ne l'ai pas vu**, parce que le lot filtrait sa sortie sur
  `grep -E "Écrit|aucun|échec\(s\)$"` : la trace de l'exception ne correspondait à aucun
  motif et a été jetée. **Le journal montrait un lot sain, deux mois manquaient.** C'est
  la version shell du `except: continue` que la règle 2 bis interdit — le même défaut,
  déplacé d'un langage à l'autre.
- **Puis j'ai réparé le journal pendant que le lot tournait**, et le lot est mort sur une
  `syntax error near unexpected token 'done'` — dans un fichier que `bash -n` valide.

### Le fil commun

Ces défauts ne cassent rien et ne lèvent aucune erreur. Ils coûtent des heures **en
silence** — exactement comme les erreurs de données que ce projet traque par ailleurs.
C'est la même vigilance, appliquée à l'exécution plutôt qu'aux résultats.

---

## 1 ter. Une mesure n'est pas une propriété

### La règle

**Un débit mesuré une fois n'est pas un débit.** Sur un service distant et partagé, une
durée est un **échantillon** : elle dépend de la charge du serveur, du cache, de l'heure.
Avant toute extrapolation, mesurer **au moins deux fois, à des moments distincts**, et
extrapoler depuis la **pire** valeur — jamais la meilleure, jamais la première.

Et son corollaire, qui est le même défaut vu de l'autre bout :

**Un code 200 n'est pas un résultat.** Comparer le **volume reçu** au volume demandé.
Une réponse de 92 octets pour une requête de 1,1 Mo n'est pas un téléchargement rapide,
c'est une page d'erreur.

```python
# ✗  une mesure, une conclusion, un plan
t = chrono(requete)                 # 29 s
print(f"extrapolation : {t * N / 3600:.1f} h")

# ✓  plusieurs mesures espacées, la pire retenue, et le reçu vérifié
durees = []
for _ in range(3):
    t0 = time.time(); r = requete(); durees.append(time.time() - t0)
    if len(r) < attendu * 0.9:
        raise ValueError(f"{len(r)} octets reçus pour {attendu} demandés")
    time.sleep(30)                  # espacer : mesurer trois fois d'affilée mesure le cache
print(f"médiane {median(durees):.0f} s · pire {max(durees):.0f} s → "
      f"extrapolation {max(durees) * N / 3600:.1f} h")
```

### Les erreurs qui ont produit cette règle — le 04/08, sur GEOS-CF

- **29 s mesurées une fois, citées trois fois.** Une requête OPeNDAP de 4 variables ×
  120 échéances a mis 29 s. J'en ai tiré « 60 fois moins cher », « ~45 min à quatre
  ouvriers », et je me suis reproché de ne pas l'avoir adoptée. Refaite : **76 s** pour
  **cinq fois moins** de données, puis **504 Gateway Time-out**. La première mesure
  bénéficiait d'un cache et d'un serveur au repos.
- **Trois codes 200 pris pour trois services disponibles.** `curl -o /dev/null -w "%{http_code}"`
  sur trois points d'entrée OPeNDAP a rendu `200, 200, 200`. C'étaient trois pages
  d'erreur HTML : *« is not an available dataset »*. Il a fallu demander le `.dds` pour
  le voir.

### Le fil commun

Les deux fois, j'ai conclu depuis un **signal disponible** plutôt que depuis le **signal
demandé** — une durée au lieu d'une distribution, un code de statut au lieu d'une charge
utile. C'est la règle 2 bis appliquée au réseau : *compter le reçu contre le demandé*.

---

## 1 quater. Un lot se borne sur la ressource qu'il partage avec sa machine

### La règle

Les règles 1 et 1 bis bornent le lot en **durée** et en **coût de service**. Celle-ci le
borne sur la ressource qu'il ne possède pas : la machine elle-même. Un lot qui déborde ne
ralentit pas — **il tue son hôte, et un hôte mort n'écrit rien.**

Trois gestes, avant le lancement, jamais après :

1. **Plafonner le processus plutôt qu'espérer qu'il se tienne.**
   `systemd-run --user --scope -p MemoryMax=<plafond> -p MemorySwapMax=0 -- <commande>`.
   Un processus qui déborde **dans un cgroup borné meurt seul**, code 137, machine
   intacte ; le même processus non borné emporte la VM et n'explique rien. Le plafond
   n'est pas une optimisation : c'est ce qui rend la panne **observable**.
2. **Échantillonner pendant le lot, et écrire la trace là où elle survivra.**
   `scripts/veille_memoire.sh` : sortie dans `$HOME`, **jamais sur `/mnt/d`**, et un
   `sync` par ligne. Sans le `sync`, les dernières secondes — les seules qui expliquent la
   mort — restent dans le cache et disparaissent avec la VM.
3. **Faire la passe unitaire sur le garde-fou, pas seulement sur le lot.** Demander 2 Go
   sous un plafond de 256 Mo et exiger le code 137. Un garde-fou non testé est une
   croyance, et il se testera tout seul le jour où il aura échoué.

### Le corollaire de diagnostic — où une coupure est écrite

**Une machine qui tombe sans laisser de trace n'est pas un mystère : c'est une absence
d'instrumentation.** Trois sources existent déjà, aucune n'est dans un script :

- `/var/log/kern.log` — segfauts, OOM, paniques. **Une coupure sans trace noyau n'est pas
  un plantage interne** : le noyau tourne encore quand la VM disparaît ;
- les **horodatages** de `logs/` et des `.partiel` — ils datent la mort à la minute et
  disent quel lot tournait ;
- les **transcripts de session** (`~/.claude/projects/<projet>/*.jsonl`) — ils disent ce
  qui était **lancé** à cette seconde-là.

### L'erreur qui a produit cette règle — le 08/08, trois coupures en vingt-six minutes

WSL est tombé à **19 h 23, 19 h 33 et 19 h 50**. L'hypothèse de départ — « ça coupe en
traitant le `.md` de R17 » — était la seule disponible, et elle était **fausse** : le
fichier fait 93 Ko. Les trois coupures suivent trois lancements de
`lot_maximale_tendance.sh` (19 h 14, 19 h 26, 19 h 39), **8 à 11 minutes plus tard**,
toujours à la même configuration : la 8ᵉ, `★ MAXIMALE — AUX STATIONS` d'O₃.

Pourquoi la fausse piste tenait : une session Claude Code **lit d'abord, lance ensuite**.
Les deux gestes sont toujours enchaînés, donc la corrélation ne les sépare pas. **Quand
deux gestes sont inséparables dans le temps, seule une trace qui les distingue tranche** —
ici l'horodatage de `logs/maximale_O3.log` (19 h 48) et l'existence de
`reports/methode_maximale_O3_h2.csv.partiel`, qui prouvent qu'un lot tournait, ce que la
lecture d'un `.md` ne produit jamais.

**Ce qui est établi** : un lot tournait aux trois coupures ; aucune des trois n'a laissé
de trace noyau ; l'hypothèse du fichier est réfutée.

### Ce que l'instrumentation a rendu dans l'heure qui a suivi

Le plafond et `PYTHONFAULTHANDLER` ont produit en une heure ce que sept heures de
réessais n'avaient pas donné :

- **le segfault n'est pas dans LightGBM.** La pile au moment du signal désigne tantôt
  **pandas** (`PeriodIndex`, au chargement), tantôt **LightGBM** (`fit`) — deux
  bibliothèques, deux sites, même intermittence. Le diagnostic du matin nommait la
  seconde parce que le journal noyau ne montre que le `.so` où le compteur s'arrête ;
- **la mémoire est hors de cause** : pic mesuré à **11,6 Go au chargement**, palier à
  5,2 Go, sur une VM de 70 Go. Un lot qui n'utilise pas 17 % de sa machine ne l'étouffe
  pas ;
- **le défaut est intermittent, pas déterministe** — et je m'y suis laissé prendre une
  seconde fois : deux échecs de suite sur la dernière configuration m'ont fait écrire
  qu'elle était le coupable ; la tentative suivante l'a passée. **Deux essais ne font pas
  une propriété** (règle 1 ter), y compris quand ils pointent le même endroit ;
- et surtout : **la machine a tenu**, une heure et une douzaine de segfauts plus tard.

**La bonne réponse n'était donc pas de trouver la cause, mais de rendre l'échec non
fatal.** `methode_maximale.py` relit son `.partiel` et reprend sur le **nom** des
configurations déjà mesurées : à ~1 échec sur 2, un lot qui repart de zéro n'aboutit
jamais, un lot qui reprend aboutit en six tentatives — mesuré, c'est exactement ce qu'il a
fallu.

> **Quand un défaut est intermittent, l'ingénierie qui paie est la reprise, pas le
> diagnostic.** Chercher la cause est sans fin ; conserver le travail déjà fait coûte
> trente lignes et rend le lot insensible au reste.

### 🔴 Le signal qui change la nature du problème — et la vérification qui rassure

À 22 h 17, une tentative n'a pas segfauté : elle a **levé**.

```
TypeError: 'UTC' object cannot be interpreted as an integer
  pandas/_libs/tslibs/vectorized.pyx  → ints_to_pydatetime
  pandas/_libs/tslibs/timestamps.pyx  → create_timestamp_from_ts
```

**Un objet Python parfaitement valide est arrivé dans un emplacement d'argument entier.**
Ce n'est pas une installation mélangée — les `.so` de `pandas/_libs/tslibs` portent tous la
même date. C'est une **valeur qui atterrit au mauvais endroit** : quand elle tombe sur un
pointeur, ça segfaute ; quand elle tombe sur un contrôle de type, ça lève. Le même défaut,
vu de deux côtés. Avec les segfauts dans **trois binaires distincts** (pandas, LightGBM,
`python3.12` — dont plusieurs `ip 0000000000000000`) et des morts de VM sans trace noyau,
le faisceau désigne l'**instabilité de la plateforme**, pas une bibliothèque.

> **À faire côté machine, pas côté code** : test mémoire de l'hôte (`mdsched.exe`), et
> vérifier si un profil XMP/EXPO est actif. Aucune ligne de Python ne corrigera cela.

#### ✅ Tranché le 09/08 — et la piste XMP/EXPO était fausse

**La trace existait depuis le début. Elle était dans le journal d'événements Windows, que
personne n'avait ouvert.** Trois jours passés dans `kern.log`, dans les piles Python et dans
la consommation mémoire, pour un défaut journalisé par l'hôte.

| source Windows | ce qu'elle rend |
|---|---|
| `WHEA-Logger` **ID 19** ×3 | « erreur matérielle corrigée · **cœur du processeur** · Corrected Machine Check · **Internal parity error** · APIC 33 » |
| `Kernel-Power` **41** ×6 en 2 mois | **c'est Windows qui s'arrête**, pas WSL — dont le 08/08 à **22 h 56 49**, la « 4ᵉ coupure WSL » du journal |
| `WER-SystemErrorReporting` **1001** | `0x00020001` **HYPERVISOR_ERROR** (08/08 et 21/06) · `0x0A` IRQL_NOT_LESS_OR_EQUAL · `0x50` PAGE_FAULT_IN_NONPAGED_AREA |

**XMP/EXPO est réfuté, par la mesure** : `ConfiguredVoltage 1100` (1,1 V, JEDEC de base) et
`ConfiguredClockSpeed == Speed`. Aucun profil n'est actif, il n'y a rien à désactiver. La
mémoire n'est pas non plus saturée — 3,6 Go sur 70 à la seconde d'une coupure.

Ce qui reste, mesuré : un **i9-13900KF** (Raptor Lake, microcode **0x12B** déjà appliqué —
BIOS ASUS 1805 du 30/10/2024, donc la dégradation ne progresse plus mais celle déjà subie
est permanente), et une configuration mémoire **hors spécification** : 4 DIMM issus de
**deux kits différents** — 2 × `F5-6000J3040G32G` (32 Go, DDR5-6000 CL30) et
2 × `F5-6800J3445G16G` (16 Go, DDR5-6800 CL34).

> **La leçon de méthode, et elle vaut plus que le diagnostic : quand l'hôte tombe, la trace
> est chez l'hôte.** Le corollaire ci-dessus listait trois sources, toutes *dans* la VM. Il
> en manquait une, la seule qui survive à la mort de la VM. La règle 1 quater se cherchait
> elle-même du mauvais côté de la frontière de virtualisation.

**Quatrième source, à ajouter aux trois du corollaire :**

```bash
powershell.exe -NoProfile -Command "Get-WinEvent -FilterHashtable @{LogName='System';Id=41} -MaxEvents 8 | Format-Table TimeCreated"
powershell.exe -NoProfile -Command "Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Microsoft-Windows-WHEA-Logger'} -MaxEvents 15 | Format-List TimeCreated,Id,Message"
```

**Et la question qui compte davantage : les résultats sont-ils faux ?** Vérifié en
comparant deux exécutions indépendantes de la pile O₃, séparées par sept crashs :

| | 19 h 48 | 21 h 53 |
|---|---|---|
| base · membres · feux · geoscf · tendance · MAXIMALE | +7,01 · +9,83 · +11,93 · +13,75 · +15,83 · +15,83 | **identiques à la décimale** |
| typologie | +6,88 | +6,87 *(écart ~1 × 10⁻⁴, ordre de réduction des 8 fils)* |

**Les pannes sont bruyantes, pas silencieuses** : quand le calcul aboutit, il rend le même
chiffre. C'est exactement l'inverse des défauts que le reste de ce fichier traque — pour
une fois, l'échec se voit. Cela ne dispense pas de réparer la machine ; cela dit seulement
que les mesures déjà publiées ne sont pas à re-vérifier une par une.

### La confirmation du 08/08 à 22 h 53 — quatrième coupure, et deux points fixés

La VM est retombée à ~22 h 53, pendant la 6ᵉ tentative sur NO₂. Trois observations, toutes
tirées de l'instrumentation, aucune d'une intuition :

- **Le mécanisme « argument au mauvais endroit » a une seconde occurrence, plus explicite
  que la première :**

  ```
  ValueError: Invalid frequency: 2023-12-15 12:00:00+00:00
    ← levé depuis pd.PeriodIndex(pd.to_datetime(jeu["timestamp_utc"]), freq="M")
  ```

  Une **valeur du tableau de données** est arrivée dans le paramètre `freq`. Ce n'est pas
  une donnée fausse — `freq="M"` est écrit en dur dans `fit_mos.py:132`, il n'y a aucun
  chemin de code par lequel un horodatage puisse s'y rendre. Le `TypeError` de 22 h 17 et
  ce `ValueError` sont **le même défaut à deux endroits différents**, ce qui retire à
  chacun son statut d'anomalie isolée.

- **La mémoire est disculpée une seconde fois, et cette fois à la seconde de la coupure.**
  L'échantillonneur, écrit hors `/mnt/d`, a survécu : **pic à 3,6 Go sur 70**, swap à zéro,
  aucun `code=137` en 40 exécutions. La coupure tombe pendant une *montée* de RSS
  (5 → 2 180 Mo en 27 s), c'est-à-dire un chargement qui **démarrait**. Un plafond de 24 Go
  jamais approché ne peut pas être la cause de ce qu'il n'a pas plafonné.

- ⚠️ **`kern.log` ne dit plus rien sur le site du fault — il ne sert plus qu'à dater.**
  Les **22 signaux 11** enregistrés depuis 22 h 11 portent tous `ORIG_RAX: 0xea`
  (syscall 234, `tgkill`) et le **même offset libc** `…a642c` — seule la base ASLR change.
  C'est `faulthandler` qui, après avoir imprimé la pile, ré-émet le signal : le noyau
  journalise donc **la ré-émission**, jamais le fault. Conséquence directe : les
  « trois binaires distincts » notés plus haut restent valides pour les signaux **antérieurs**
  à l'instrumentation, mais **plus aucune conclusion ne doit être tirée d'un RIP postérieur**.
  La pile Python de `logs/maximale_*.log` est désormais la seule source sur le site.

  C'est le corollaire de la règle 1 ter appliqué à soi-même : *l'instrumentation change ce
  que la mesure mesure.* Avoir rendu l'échec lisible côté Python a rendu le journal noyau
  aveugle, et ne pas le savoir aurait produit un quatrième faux diagnostic.

**Et la reprise a payé une fois de plus** : les 5 configurations de NO₂ déjà mesurées à
22 h 51 ont été relues telles quelles après le redémarrage. La coupure a coûté le
redémarrage, pas le travail.

### Le fil commun

C'est la règle 5 appliquée à la machine plutôt qu'aux données : *si ce lot tuait son hôte,
est-ce que je saurais pourquoi ?* Sans plafond ni échantillonnage, la réponse est non — et
la panne se déguise alors en propriété de ce qu'on était en train de lire.

---

## 1 quinquies. Un lot vivant n'est pas un lot qui avance

### La règle

La règle 1 bis dit de surveiller l'**arrêt** du lot. Insuffisant : un lot peut rester
vivant et ne plus rien produire, et c'est le cas contre lequel aucun contrôle n'existait.
Trois gestes.

**① Surveiller l'ARTEFACT, jamais le processus.** Un moniteur qui teste `kill -0` remonte
la mort et rien d'autre. **Mesurer l'intervalle naturel entre deux écritures pendant la
passe unitaire**, puis alerter à ~5 × cet intervalle. Le seuil se calcule sur une cadence
observée, jamais sur une intuition.

```bash
# ✗  surveille la mort ; muet pendant un gel, et le silence se lit comme une bonne nouvelle
kill -0 "$PID" || { echo "arrêté"; break; }

# ✓  surveille la PRODUCTION, avec un seuil dérivé de la cadence mesurée
age=$(( $(date +%s) - $(stat -c %Y "$artefact") ))
[ "$age" -gt "$((5 * INTERVALLE_MESURE))" ] && echo "⚠️ GEL : rien écrit depuis ${age}s"
```

**② L'instrument ne doit pas peser plus que ce qu'il mesure.** Une veille échantillonne à
la période de ce qui change, et **ne force jamais de barrière de durabilité à haute
fréquence**. Un `sync` par ligne toutes les 2 s, c'est ~30 barrières par minute imposées à
un système de fichiers que le lot utilise aussi.

**③ Séparer « le disque peine » de « le noyau est figé ».** Deux lignes, avant toute
hypothèse sur le matériel ou l'espace disque :

```bash
cat /sys/block/<dev>/inflight     # 0 0  →  RIEN n'attend le périphérique
awk '$3=="<dev>"' /proc/diskstats # figé →  rien ne circule
```

Des tâches en `D` **avec un périphérique au repos** désignent un blocage **noyau**, pas un
disque. L'inverse — `inflight` non nul qui ne décroît pas — désigne le stockage.

### L'erreur qui a produit cette règle — le 10/08, et je l'ai annoncée moi-même

Lot lancé à **15:15:18**. Dernière ligne écrite à **15:20:32**. À **16:16**, soit
**61 minutes de temps réel pour 5,2 minutes de travail**, le processus était toujours
vivant, en état `R`, et **n'avait rien produit depuis une heure**.

**Le moniteur est resté muet 56 minutes**, parce qu'il surveillait le pid — qui existait.
J'avais annoncé « ~30 min si tout passe, ~1 h dans le cas défavorable » en présentant cette
estimation comme *réfutable* : elle ne l'était pas, puisque le seul contrôle installé ne
pouvait pas la contredire. Et la cadence normale était connue — **un mois toutes les 30 à
36 s**, dans les deux exécutions précédentes. Cinq minutes de silence valaient déjà **10 ×**
l'intervalle attendu.

### L'instrument comme cause — une occurrence, pas une propriété

`veille_memoire.sh` fait un `sync` après **chaque** ligne, toutes les 2 s. Le gel apparaît
à 15:20:32, **cinq minutes après l'avoir armé pour la première fois à côté d'un lot** :

- `sync` (pid 6861) bloqué en `jbd2_log_wait_commit` pendant **61 minutes** ;
- **huit `systemd-journald`** en `D`, relancés toutes les ~7,5 min, tous bloqués ;
- ~170 barrières forcées en 5,5 min, sur le même système de fichiers que le lot.

**Une occurrence ne fait pas une cause** (§ 1 ter), et je ne la présente pas autrement.
Mais le correctif ne coûte rien : suivre un RSS **n'exige aucune durabilité**. Et la leçon
dépasse ce script —

> **Le corollaire de la § 1 ter va plus loin qu'on ne l'avait écrit : l'instrumentation ne
> change pas seulement ce que la mesure mesure, elle peut CAUSER la panne qu'elle observe.**

### La mesure qui a renversé le diagnostic

`inflight = 0 0`, et `/proc/diskstats` **strictement identique sur 10 s**. Le périphérique
était **au repos**, pas en souffrance. Sans cette ligne je partais sur l'espace disque de
l'hôte — et j'y aurais trouvé un leurre parfait : `E:` à **3,3 Go libres sur 233,9**, alors
que la distribution vit sur `C:` (88,4 Go libres). Un chiffre alarmant, vrai, et sans
aucun rapport.

### Ce que le garde-fou posé le matin même a rendu

La veille hôte a réfuté, en une lecture, l'hypothèse que je portais depuis midi :
**pic `vmmemWSL` à 21,70 Go**, minimum de mémoire libre **51,71 Go sur 95,8**, et
`vm_vivante=1` **sur tout l'échantillon**. La charge d'engagement n'est donc pour rien
dans cet épisode — et surtout, **la VM n'a pas disparu cette fois : elle a gelé.** Deux
modes de panne distincts dans la même journée, qu'aucun instrument ne séparait la veille.

### Le corollaire d'arrêt — quand rien en espace utilisateur ne peut plus aider

`kill` puis `kill -9` sur le processus Python : **survécu**, toujours en `R` après
**68 minutes**. Un processus que SIGKILL ne fauche pas signale un noyau qui ne traite plus
ses signaux ; aucune commande ne le récupérera, seul un redémarrage de la VM le fera.

Et dans le même geste, **§ 1 bis rejouée à la lettre** : `pkill -f "veille_memoire.sh"` a
tué **le shell qui exécutait la commande**, dont la ligne de commande contenait le motif.

> **On ne tue jamais par motif** — `scripts/pids_de.sh` rend les pid, puis on vérifie que
> le kill a pris.

### Le fil commun

C'est la règle 5 appliquée **au contrôle lui-même** : *si mon moniteur ne remontait rien,
est-ce que je saurais que c'est parce qu'il n'y a rien à voir ?* Un moniteur qui ne
surveille que la mort est muet pendant un gel — et son silence se lit comme une bonne
nouvelle. C'est exactement le « zéro de non-lecture indiscernable d'un zéro de
non-occurrence » de la § 4 bis, déplacé de la recherche vers la surveillance.

---

## 2. Lecture de fichiers — charger avant d'indexer

### La règle

**Sur un accès non séquentiel, charger le bloc entier puis indexer en mémoire.** Une
lecture paresseuse avec des indices désordonnés dégénère en lecture point par point.

Vérifier systématiquement : *combien d'appels d'entrée/sortie mon indexation
déclenche-t-elle ?* Si la réponse est « un par élément », c'est un défaut.

### L'erreur qui a produit cette règle

Extraction CAMS aux 476 stations : `sel(...)` sur un jeu `xarray` resté paresseux, avec
des indices de stations non triés. Le backend netCDF4 renonçait à la lecture par
hyperslab et lisait élément par élément.

**52,7 s par journée de prévision → 0,13 s** en chargeant d'abord (`.load()`), soit
**400×**. Sur le corpus complet : **33 heures → 5 minutes.**

Le profilage l'a montré en une commande : 52,5 s des 52,8 s dans
`_operator.getitem` du backend.

### Le corollaire

**Profiler avant de réécrire.** `cProfile` sur un cas unitaire désigne le coupable en
quelques secondes ; l'intuition se trompe. Ici j'avais d'abord accusé le tri des
longitudes — à tort, il ne coûtait rien.

---

## 2 bis. Charger — vérifier la **demande**, jamais la vraisemblance

### La règle

**Tout chargement se termine par une assertion sur ce qui a été demandé.** Pas sur ce qui
paraît normal. Et une assertion qui échoue **lève** — elle ne journalise pas, elle n'écrit
rien sur disque.

Quatre contrôles, à écrire **avant** de lancer, jamais après avoir vu le résultat :

1. **Nommer ce qu'on lit.** Une colonne se désigne par son nom ou un motif qui n'en
   sélectionne **qu'une** — jamais par sa position, jamais par « la première qui n'est ni…
   ni… ». Zéro correspondance et deux correspondances sont **toutes deux** des erreurs.
2. **Compter le reçu contre le demandé.** Variables, mois, membres, pas de temps : un
   service qui ignore un nom invalide sert le reste sans lever.
3. **Ne jamais taire une exception de chargement.** `except: continue` transforme un
   plantage en fichier vide, et un fichier vide ne se distingue pas d'une absence de données.
4. **Rejeter les colonnes constantes.** Une colonne plate est presque toujours le signe
   qu'on a lu autre chose que ce qu'on croyait.

Outillage : `src/aq/ingest/controle.py` — `colonne_unique`, `exiger_variables`, `exiger_axe`,
`exiger_variation`, `exiger_lignes`, `exiger_couverture`. Les utiliser plutôt que de réécrire
un contrôle ad hoc à chaque script, qui est justement la façon dont les trois défauts sont nés.

### Les erreurs qui ont produit cette règle — toutes le 31/07, toutes en trois heures

Trois bogues distincts, **une seule cause** : l'échec produisait un objet d'allure normale au
lieu de lever.

- **Colonne prise par position.** « La première colonne qui n'est ni une clé ni une maille » a
  sélectionné la coordonnée `level`, constante à 0. Six membres d'ensemble, six colonnes de
  zéros, **dispersion de 0,00 µg/m³** — parfaitement cohérente et parfaitement fausse. Écrite
  sur seize mois avant d'être vue.
- **`xarray.open_datasets` n'existe pas** — la fonction appartient à `cfgrib`. L'appel levait,
  un `except: continue` l'avalait, et l'extraction rendait **0 ligne, 0 colonne, aucun
  message**. Découvert seulement en décodant un fichier à la main.
- **Deux variables demandées à GFAS, une seule reçue.** Le nom du flux de PM2,5 était invalide ;
  le service a servi le reste sans broncher. Mon contrôle vérifiait qu'aucune variable n'était
  nulle — pas qu'elles étaient **toutes là**. Il est passé au vert sur un résultat incomplet.

### Le contrôle mal posé coûte autant que l'absence de contrôle

Le même jour, en miroir : un test exigeait « un axe de taille 24 » alors que le service aplatit
date × échéance en un axe de **744**. La structure était conforme ; **c'est le contrôle qui
était faux**, et il a fait rejeter seize mois valides.

> Calculer la valeur attendue **depuis la demande** — jours × échéances — jamais depuis une
> intuition de forme.

### Le fil commun avec le reste de ce fichier

Ces défauts ne plantent pas. Ils produisent des zéros, des tables vides, des variables
manquantes — tous plausibles. C'est exactement ce que la règle 5 énonce : *si ce traitement
produisait un résultat incomplet, est-ce que je m'en apercevrais ?* Pour un chargement, la
réponse est non par défaut. Il faut donc l'instrumenter **par construction**, pas au coup par
coup.

---

## 2 ter. Écrire — le chiffre affiché n'est pas le chiffre enregistré

### La règle

La règle 2 bis protège la **lecture**. Celle-ci protège l'**écriture**, et le défaut est
symétrique : un résultat s'affiche à l'écran, semble juste, et **n'entre dans aucun
fichier**. Le rapport a le bon nombre de colonnes, le script rend 0, et la mesure a disparu.

Deux gestes, qui coûtent trois lignes :

1. **Construire l'objet enregistré au plus tard.** `pd.DataFrame(lignes)` fige une **copie**
   des dictionnaires ; toute mutation postérieure de `lignes` n'y entre jamais. La table se
   construit après le dernier calcul, jamais avant.
2. **Exiger nommément les colonnes attendues avant d'écrire**, et lever si l'une manque.
   Un `nan` dans une colonne de référence s'imprime `+nan%` sans que rien ne s'en émeuve.

```python
# ✗  la copie est prise avant les mesures suivantes ; elles n'y seront jamais
t = pd.DataFrame(lignes)
...
for r in lignes: r.update(critiques_vues=...)   # mute les dicts, pas `t`

# ✓  construire en dernier, puis exiger ce qu'on croit avoir mesuré
t = pd.DataFrame(lignes)
if manque := [c for c in ATTENDUES if c not in t]:
    raise SystemExit(f"colonnes absentes du rapport : {manque}")
```

### Les deux erreurs qui ont produit cette règle — le 03/08

- **Les situations critiques, affichées et jamais écrites.** `tableau_comparatif.py`
  construisait sa table **avant** le bloc qui compte les détections. Les six chiffres qui
  décident de tout le dossier s'affichaient à l'écran ; les quatre CSV portaient 15 colonnes
  d'allure parfaitement normale et **aucune** de ces mesures. Découvert par hasard, en
  comptant les colonnes pour autre chose.
- **La référence sortie en `nan`.** L'ancre de la chaîne concurrente héritait des trous de
  CHIMERE/MOCAGE — un filtre `notna().mean() > 0.3` tolérait 70 % de manquants. Trois
  polluants sur quatre ont affiché `+nan%` dans la colonne de gain, **sans rien lever**.
  Seul PM10, qui repliait sur CAMS, a produit un chiffre.

### Le fil commun avec le reste du fichier

Aucun des deux n'a planté. Le premier a produit un fichier **complet en apparence**, le
second une colonne **vide en apparence normale**. C'est exactement la règle 5, appliquée à
la sortie plutôt qu'à l'entrée : *si ce traitement n'enregistrait pas ce qu'il affiche,
est-ce que je m'en apercevrais ?*

---

## 2 quater. Une condition de disponibilité ne change jamais le périmètre en silence

### La règle

Les règles 2 bis et 2 ter protègent la lecture et l'écriture. Celle-ci protège **ce qui est
comparé**. Le défaut n'est ni une donnée fausse ni une donnée perdue : c'est un `if` sur la
**disponibilité** qui décide, tout seul, **de quoi on parle**.

> **Un seuil de couverture, une exception avalée ou un pli écarté ne sont pas des détails
> d'implémentation : ce sont des décisions de protocole.** Toute condition portant sur la
> disponibilité des données doit soit **replier ligne à ligne en comptant le repli**, soit
> **être exposée en option de ligne de commande** — jamais trancher en dur.

Trois formes, un seul mécanisme :

| forme | ce qui change en silence |
|---|---|
| `if colonne.notna().mean() > 0,3:` fait entrer un système | le **corpus**, par intersection des systèmes finis |
| `except Exception: pass` autour d'une jointure | une **famille de variables** disparaît du modèle |
| `if len(te) < 200: continue` | le **dénominateur** : des plis sortent du compte |

Et le contrôle qui les attrape toutes : **afficher le périmètre effectif, pas le périmètre
demandé.** Lignes retenues, mois retenus, plis exécutés sur plis prévus, familles réellement
jointes. Un script qui n'imprime que son résultat ne permet pas de voir qu'il a changé de
question.

### L'erreur qui a produit cette règle — le 05/08

`tableau_comparatif.py` décidait d'inclure CHIMERE dans l'échelle des systèmes par
`d["chimere"].notna().mean() > 0.3`. Les six systèmes partageant les mêmes lignes — `ok` prend
l'**intersection** des systèmes finis — franchir ce seuil restreint **tout le tableau** à la
fenêtre des membres.

Sur PM10, dont les membres n'existent que depuis 2025-01, cela a troqué **39 % du corpus
(31 mois → 19) contre deux lignes**, sans un mot. Personne ne l'a décidé : un `0.3` codé en
dur l'a fait. Et j'ai d'abord **rationalisé ce défaut après coup**, en le présentant comme un
arbitrage réfléchi — ce qui est pire que le défaut lui-même.

Le comble : les deux tables étaient légitimes, chacune avec ses lignes communes. **Il n'y avait
rien à trancher.** `--membres auto|non` les publie toutes les deux. Et la variante longue s'est
révélée être **à la fois le plus grand corpus et le test le plus dur** — le substitut ancré sur
CAMS (RMSE 7,20) est un adversaire plus fort que la chaîne réelle (7,63).

### La bonne forme existait déjà dans le dépôt

`maximum_deployable.py` a exactement le même seuil `> 0.3` et ne souffre pas du défaut, parce
qu'il fait les deux gestes :

```python
# ✗  le seuil bascule tout le périmètre, en silence
a_chimere = d["chimere"].notna().mean() > 0.3     # …puis `ok` intersecte, 39 % du corpus part

# ✓  repli ligne à ligne, et le repli est COMPTÉ
brut = d[dispo].mean(axis=1).to_numpy()
replis = ~np.isfinite(brut)
if replis.any():
    nom += " (CAMS en repli)"
    print(f"  ⚠️ {replis.sum():,} lignes sans {'/'.join(dispo)} — repli sur CAMS")
brut = np.where(replis, socle, brut)
```

**Replier conserve le périmètre ; basculer le détruit.** Et un repli compté est une réserve
publiable ; un repli muet est un chiffre faux.

### Les jumeaux trouvés au scan du 05/08

- ✅ `tableau_comparatif.py` — `except Exception: pass` **entièrement muet** autour des
  jointures de familles. **Corrigé** : il journalise la cause et imprime les familles
  réellement jointes (`feux(3) · membres✗`), c'est-à-dire le périmètre effectif.
- 🟠 `if len(te) < 200 or len(tr) < 1000: continue` — le scan du 06/08 en trouve **vingt**
  occurrences, pas cinq, dont **dix-huit sans compteur**. **Les cinq qui produisent des
  chiffres publiés sont corrigés** (`methode_maximale`, `double_aveugle_journalier`,
  `oof_double_aveugle`, `banc_lcsqa`, `tableau_comparatif`) : ils nomment les plis écartés
  avec leurs effectifs et impriment « N exécutés sur M prévus ». **Treize restent**, tous
  hors chemin de publication.

  ⚠️ **Et la phrase que portait cette entrée était fausse.** Il était écrit « PM10 a tourné
  sur 24 plis au lieu de 29 sans que rien ne le dise ». Vérification faite sur les CSV :
  `n_plis == n_mois` sur les **quatre** polluants, donc **zéro pli écarté**. Les 24 mois de
  PM10 sont sa **fenêtre de couverture GEOS-CF v1** (2024-01→2025-12), que le script
  **imprime déjà**. Le défaut était réel comme risque latent, pas comme corruption réalisée
  — et l'attribuer à un chiffre qu'il n'avait pas produit est exactement l'erreur que ce
  fichier reproche ailleurs : *conclure depuis un signal disponible plutôt que depuis le
  signal demandé*.
- ✅ Faux positifs, à ne pas « corriger » : les `notna().mean()` de `apport_tropomi`,
  `extraire_sol`, `krigeage_du_biais`, `champ_region` **rapportent** une couverture sans rien
  décider — c'est précisément ce que la règle demande. Et `corriger_chimere.py:214` ne gouverne
  qu'un affichage.

### Le fil commun

C'est la règle 5 appliquée à la **question posée** plutôt qu'aux données : *si ce traitement
répondait à une autre question que celle que je crois avoir posée, est-ce que je m'en
apercevrais ?* Sans affichage du périmètre effectif, la réponse est non.

---

## 2 quinquies. Un seuil doit regarder du côté où le défaut pousse

### La règle

Un contrôle de sortie ne suffit pas : encore faut-il qu'il porte sur une grandeur qui
**empire quand le défaut s'aggrave**. Un plancher — « au moins N pages », « au moins N
lignes » — ne voit rien d'une dégradation qui **diminue** la quantité mesurée : le défaut
s'installe *en s'éloignant* du seuil.

Deux gestes, à écrire en même temps que le seuil :

1. **Se demander dans quel sens le défaut pousse le chiffre.** S'il le pousse du côté
   confortable, le seuil est décoratif. Il en faut un autre, sur une autre grandeur.
2. **Comparer à la version précédente, pas à une constante.** Un artefact régénéré se
   compare d'abord à lui-même : « 54 pages hier, 49 aujourd'hui, +1 page de contenu » est
   une alerte que nul plancher ne produira.

### L'erreur qui a produit cette règle — le 11/08, sur la pièce jointe du dossier

L'ajout de la page 07 a fait passer `presentation_atmo.pdf` de **54 à 49 pages**. Rien
n'était perdu : Chromium avait mis **tout le document à l'échelle 0,90** — corps de texte
de 9,75 pt tombé à 8,75. Cause, trouvée par bissection du DOM et non par intuition : la
**8ᵉ entrée du sommaire** portait la largeur de mise en page à 772 px pour **718 px
imprimables**, et le navigateur réduit le document entier plutôt que de couper. Une ligne
— `.somm { flex-wrap: wrap }` — et le PDF est revenu à 56 pages à l'échelle 1:1.

`exporter_pdf.py` contrôlait pourtant sa sortie, et son commentaire annonçait « un PDF
d'une page est un échec de rendu ». Mais il testait `pages >= 40`. **Le défaut produit
moins de pages : 49 passait le contrôle exactement comme 54, et l'aurait passé à 41.**

> **Le contrôle qui l'attrape est en amont de l'artefact** : mesurer la largeur de mise en
> page à la largeur imprimable, refuser tout débordement, et **nommer l'élément fautif** —
> un contrôle qui dit « ça déborde » sans dire « où » envoie chercher au hasard.

### Le fil commun

C'est la règle 5 posée au contrôle plutôt qu'au traitement : *si mon seuil était franchi
du mauvais côté, est-ce que je m'en apercevrais ?* Et c'est le même défaut que « ne jamais
comparer un compte à un compte » (§ 4), déplacé du contenu vers la **forme** : ici le
contenu était complet, c'est sa mise à l'échelle qui avait changé.

---

## 3. Volume — ne télécharger que la fenêtre utile

### La règle

**Avant de télécharger une archive complète, chercher si la source expose un accès
partiel :** service d'interrogation par emprise, requêtes par plage HTTP, format
« nuage » (COG, Zarr, Parquet partitionné). Le gain est de plusieurs ordres de grandeur,
pas de quelques pourcents.

### Les erreurs et non-erreurs qui ont produit cette règle

- **Modèle de terrain.** Le RGE ALTI pèse 5,5 Go pour la seule Occitanie, sans aucun
  service d'interrogation — donc des dizaines de Go pour la France. Le Copernicus GLO-30
  est en COG sur un stockage objet public qui accepte les requêtes par plage :
  **476 stations en 7 minutes, zéro octet stocké.** Vérifié avant de s'engager, par un
  `curl -r 0-2000000` qui a répondu HTTP 206.
- **Paysage.** Les archives couvrant l'Occitanie pèsent ~10 Go ; interroger un disque
  autour de chaque station via le service WFS donne exactement la même information.
- **Et son revers :** 476 requêtes individuelles auraient retéléchargé les mêmes objets
  (distance médiane au plus proche voisin : 4,1 km, pour un rayon de 30 km). Le
  regroupement par proximité a ramené 11,9 Go à 4,6 Go. **Le bon découpage n'est ni le
  plus fin ni le plus gros — il se calcule.**

---

## 4. Reprise — un artefact au nom définitif doit être complet

### La règle

**Écrire sous un nom provisoire, vérifier, puis renommer.** Et faire porter le test de
reprise sur le **contenu attendu**, jamais sur la seule existence du fichier ou du
dossier.

### Les erreurs qui ont produit cette règle

- Un dossier CAMS partiel (**9 jours sur 31**) était compté comme complet par la reprise :
  il n'aurait plus jamais été retéléchargé, et le trou ne serait apparu que dans les
  métriques finales.
- Un mois ERA5 arrivé avec **un seul de ses deux flux** a été extrait et écrit sous son
  nom définitif — table sans précipitation ni rayonnement, sautée à jamais ensuite.

Dans les deux cas : aucune erreur levée, aucun signal, propagation silencieuse.

### Le complément du 03/08 — **d'où vient l'attendu**

La règle dit de tester le **contenu attendu**. Elle ne dit pas **d'où l'attendu est
calculé**, et c'est exactement là que le défaut est revenu **trois fois en une journée**,
sous trois formes différentes :

| | forme prise | ce qui décidait à tort |
|---|---|---|
| matin | `telecharger()` testait `is_dir()` quand `acheve()` testait la complétude | **le plus faible des deux contrôles** |
| midi | l'artefact ne portait pas son échéance dans son nom | un lot J+1 **écrasait** un lot J0 |
| soir | reprise comptant les fichiers d'un dossier **de deux mois** contre le calendrier d'**un seul** | 11 mois sur 36 sautés en silence |

Le fil commun n'est pas « tester le contenu » — c'était fait à chaque fois. C'est que
**l'attendu venait d'ailleurs que de la demande** : d'un autre contrôle, d'un nom sans
échéance, d'un total au lieu d'une liste.

> **Ne jamais comparer un compte à un compte.** Nommer les artefacts attendus un par un,
> et vérifier leur présence individuellement.

```python
# ✗  un total, qui passe pour complet dès qu'un autre mois a rempli le dossier
if len(list(dossier.glob("J3_*.nc"))) >= jours_du_mois: sauter()

# ✓  la liste nommée de ce qui est demandé
jours = pd.date_range(f"{an}-{mo:02d}-01", periods=jours_du_mois)
presents = sum((dossier / f"J3_{d:%Y-%m-%d}.nc").exists() for d in jours)
```

**Et le contrôle qui a réellement attrapé le défaut n'était dans aucun script** : c'est
d'avoir recompté les mois disponibles *à côté*, et vu que « 11 déjà faits » ne collait pas
avec un corpus de 36 mois complets. **Un script ne peut pas s'auditer sur une hypothèse
qu'il porte lui-même.** Le lot annonçait « 0 échec » avec la moitié du travail non faite.

### Le corollaire

**Vérifier la structure, pas seulement l'ouverture.** Un fichier tronqué s'ouvre souvent
sans erreur. Contrôler le nombre de pas de temps, de variables, de membres — et rejeter
en nommant précisément ce qui manque.

---

## 4 bis. Un nom de fichier n'est pas une source de vérité

### La règle

**Ne jamais déduire d'un nom de fichier la fenêtre de données qu'il contient.** Les
bornes se lisent **dans les données** — `min()` et `max()` de la colonne temporelle,
liste effective des variables présentes. Le nom sert à retrouver le fichier, à rien
d'autre.

Et si un nom doit malgré tout être analysé, **une expression ancrée à droite est
suspecte par construction** : `_(\d{6})\.parquet$` sur `..._o3_202308_202309.parquet`
capture `202309` et perd `202308`, sans lever la moindre erreur. Un nom qui porte
plusieurs jetons exige de tous les capturer — ou de ne pas être analysé du tout.

### Les erreurs qui ont produit cette règle — le même motif, trois fois

- **Le nom d'espèce.** `_([a-z0-9]+)_(\d{6})$` sur un dossier groupé capturait `202402`
  au lieu de `o3` : les trois polluants s'écrasaient l'un l'autre sous une même clé.
- **La fenêtre d'observations, dans `fit_mos.py`.** Même motif, un an plus tard dans le
  même projet : les six dossiers bi-mensuels n'ont livré que leur **second mois**.
  **11 mois retenus sur 17**, soit **2,09 M de paires au lieu de 3,23 M — 35 % du jeu
  d'entraînement perdu en silence.** Découvert seulement parce qu'une courbe
  d'apprentissage s'est arrêtée à trois points au lieu de six.
- **Le benchmark CAMS**, même ligne recopiée. Impact plus faible — la fenêtre y étant
  contiguë du min au max, seul le mois du bord était amputé — mais c'est la **référence
  contre laquelle tout le projet se mesure**.

### Le corollaire, qui est le vrai enseignement

**Corriger un défaut à l'endroit où il fait mal ne suffit pas : il faut chercher ses
jumeaux.** J'avais corrigé le premier cas sans jamais lancer le `grep` qui aurait
trouvé les deux autres — trente secondes de recherche contre 35 % des données.

> Toute correction d'un motif de code se termine par une recherche du même motif
> ailleurs. Pas d'exception.

Et pour rendre le trou impossible à ignorer, **afficher la couverture obtenue** :
`fit_mos.py` annonce désormais « *N mois appariés sur M prévus* » et nomme les
manquants. Un mois sans observation reste légitime — 2025 n'en a aucune — mais il est
désormais dit, jamais deviné.

### 🔴 Et l'outil de cette règle ment — mesuré le 09/08

**`grep`, dans une session Claude Code, n'est pas GNU grep.** C'est une **fonction shell**
qui appelle `ugrep --ignore-files` — laquelle **respecte `.gitignore`** et saute donc en
silence tout ce que le dépôt ignore. Aucun message, aucun code d'erreur : juste zéro
correspondance.

```bash
grep -rl --include="*.html" "" .          # 0 fichier   ← ugrep, filtré par .gitignore
command grep -rl --include="*.html" "" .  # 139 fichiers ← le vrai grep
type grep                                 # « grep is a function » : le tell
```

Sur ce dépôt, le filtre porte exactement sur **les pièces que le recruteur lit** :
`.gitignore` l. 18 masque `reports/figures/*.html` — **toute la présentation et ses
fragments** — et l. 72-98 masquent `NOTE_ATMO_OCCITANIE.md`, `SOUTENANCE_*`, `LETTRE_*`,
`MAIL_*`. Un fichier peut même être **suivi par git *et* ignoré par ugrep** :
`presentation_atmo.html` est commité dans `adb4637` et invisible au `grep` de session.

**Ce que ça a failli coûter.** L'audit R17 § ③ — « zéro formulation proscrite dans les cinq
pièces » — a été mené au `grep`, donc sur trois pièces jamais ouvertes. Refait au
`command grep` : **mêmes chiffres, 0 partout et 13 « déclench… »**. La conclusion tenait,
mais par chance, pas par contrôle : un zéro de non-lecture est indiscernable d'un zéro de
non-occurrence. Et le même défaut a bel et bien caché un jumeau réel le même jour — la
promesse « volume d'alertes choisi » dans le schéma de la page 03, que la recherche initiale
depuis `.` n'a pas vue.

> **Pour chercher un jumeau, `command grep` — jamais `grep`.** Et le contrôle qui l'attrape
> en une ligne : comparer `grep -rl "" <chemin> | wc -l` à `command grep -rl "" <chemin> | wc -l`.
> S'ils diffèrent, la recherche a filtré ce qu'elle prétendait balayer.

C'est le corollaire de la règle 1 ter appliqué à l'outillage : *l'instrumentation change ce
que la mesure mesure.* Et c'est la règle 5 sous sa forme la plus pure — **le contrôle rend
« rien », et « rien » ne se distingue pas de « rien cherché ».**

---

## 4 ter. Un axe de données n'est pas ce que son nom annonce

### La règle

**L'unité d'un axe se lit dans les données, jamais dans le nom de la variable qui le
porte.** Échéance, horizon, niveau, fuseau, référence temporelle : ce sont des
**conventions du fournisseur**, et une convention non vérifiée est une hypothèse.

Le contrôle tient en une ligne et se fait **avant** d'écrire le premier chiffre :
prendre une valeur de l'axe, afficher l'horodatage qu'elle porte, et vérifier qu'il
correspond à ce que le nom promet.

```python
# échéance 0 h → quel horodatage, quel jour ?
print(t[t.echeance_h == 0][["timestamp_utc"]].head(1))
```

Et le corollaire qui coûte le plus cher : **un nom faux se propage plus loin que le
code.** Il entre dans les rapports, les figures, la mémoire du projet et les phrases
qu'on prépare pour un entretien. Le corriger dans le script ne suffit pas ; il faut le
chercher partout où il a été écrit — c'est la règle 4 bis appliquée au vocabulaire.

### L'erreur qui a produit cette règle — le 02/08

`TRANCHES = {1: (1, 24), 2: (25, 48), 3: (49, 72)}`, et tout le projet a appelé
`horizon=1` « **la prévision à J+1** » pendant des semaines.

C'est faux. La sortie CAMS de référence est à **00 UTC**, et l'échéance 0 h porte
l'horodatage **du même jour**. Les échéances 1 à 24 h couvrent donc les heures 1 à 24 du
jour de la sortie : c'est **J0**, le jour courant. Le vrai J+1 est `TRANCHES[2]`.

Personne ne l'a détecté parce que **rien ne plantait** : les appariements étaient
corrects, les scores cohérents, les contrôles au vert. Seul le **nom** était faux — et
c'est le nom qui allait dans le dossier.

Le coût réel : une comparaison au produit officiel construite sur un handicap
**imaginaire**. J'ai expliqué que notre rappel plus faible s'expliquait par « J+1 contre
leur J0 », alors que les deux systèmes étaient au même horizon. J'ai excusé un écart au
lieu de le regarder.

### Le corollaire — signaler un défaut n'est pas le corriger

Dans le même échange, j'ai écrit :

> « La comparaison n'est pas équitable — stations connues contre inconnues — mais elle ne
> nous est pas favorable, et il faut le dire ainsi. »

**Écrire qu'une mesure est biaisée puis la publier quand même, c'est la valider.** La
réserve honnête ne remplace pas la mesure juste : elle sert quand on ne *peut* pas
corriger, jamais quand on ne l'a pas *fait*. Ici, rétablir l'équité coûtait une option de
ligne de commande.

> Avant d'écrire « attention, cette comparaison est imparfaite », se demander : **est-ce
> que je peux la rendre équitable ?** Si oui, la réserve est une paresse déguisée en
> rigueur.

Et cela vaut dans les deux sens. S'infliger un protocole plus dur que celui de la
référence n'est pas de la prudence : c'est **fausser la comparaison contre soi**, ce qui
est aussi peu informatif que la fausser en sa faveur. Deux systèmes se comparent à armes
égales, ou la comparaison ne dit rien.

---

## 5. Ce qui relie toutes ces règles

### Les cinq tensions que l'audit a trouvées — et leur résolution

`python3 scripts/auditer_regles.py` les relève à chaque exécution. Aucune n'est une
contradiction de fond : ce sont des **leçons qui ont essaimé**, et la règle J les range.

| tension | résolution |
|---|---|
| § 1 « la concurrence n'est pas la réponse par défaut » **contre** § 0-G « paralléliser entre ressources » | **règle I** — § 1 parle de *la même* ressource, G des *distinctes*. Je les ai confondues le 16/08 et laissé CPU et GPU au repos. |
| « un nom ment » en **3 sections** (§ 0-H colonne, § 4 bis fichier, § 4 ter axe) | § 4 bis fait foi ; les deux autres en sont des **instances**. Même défaut, trois supports. |
| « contrôler l'artefact » en **2 sections** (§ 0-C, § 1 bis) | § 1 bis fait foi ; § 0-C en est la forme *exécutable*. |
| « une mesure ne fait pas une propriété » en **3 sections** (§ 0-E, § 1 ter, § 1 quater) | § 1 ter fait foi. |
| « un seuil dérivé » en **2 sections** (§ 0-A, § 1 quinquies) | § 1 quinquies fait foi. |

⚠️ **Et le renvoi de ce titre était faux** : il annonçait « ces **cinq** règles » alors que
le fichier en compte **17 sections et 11 lettres**. C'est la règle H — une étiquette qui
ment — appliquée au document lui-même, et elle a menti pendant treize jours.

### 🔴 La dette que ce fichier n'a pas soldée

**440 lignes le 03/08 → 1 181 aujourd'hui, +168 %.** La méta-règle exige l'inverse. Le
solde honnête, à la date d'écriture :

- **converti en code** : C, D, E, F, G, H, I, J, K — neuf règles sur onze s'exécutent ;
- **non soldé** : les § 1 bis, 1 ter, 4 bis et 4 ter gardent leur récit *en plus* de leur
  forme exécutable. Ce sont **eux** que la prochaine passe doit réduire à leur instance.

> Écrire une règle contre la croissance puis ajouter cent vingt lignes le même soir n'est
> pas une contradiction si la dette est **nommée**. Elle l'est ici. Elle ne le sera plus
> deux fois.

### Le fil commun

Aucune de ces erreurs n'a provoqué de plantage. Toutes produisaient un résultat
plausible : un téléchargement qui avance, un fichier qui s'ouvre, un traitement qui rend
la main. **C'est exactement ce qui les rend coûteuses.**

La question à se poser avant de laisser tourner quoi que ce soit :

> Si ce traitement était dix fois trop lent, ou s'il produisait un résultat incomplet,
> **est-ce que je m'en apercevrais ?**

Si la réponse est non, instrumenter d'abord.

Et la forme courte, à appliquer sans y réfléchir :

> **Une unité, deux contrôles — résultat et coût — puis le lot.**

Les deux contrôles ensemble, jamais l'un sans l'autre : c'est l'oubli du second qui a
coûté treize heures.

---

## Voir aussi

- **`REPRISE.md` — l'état du projet, à lire en premier après ce fichier.** Ce que ces règles
  ont produit, ce qui est fait, ce qui reste, et ce qui a été délibérément écarté.
- `reports/VERITE_DOSSIER.md` — **source unique des chiffres**, régénérable par
  `python3 scripts/verite_dossier.py`. Tout chiffre du dossier absent d'ici est à retirer ou
  à re-mesurer.
- `reports/` — chaque rapport porte les mesures qui étayent ces règles.
- Mémoire du projet : conventions de données vérifiées, pièges métier, périmètre exact
  de ce qui est prouvé.
