# Règles du projet — apprises à la dure

Ce fichier ne décrit pas le projet : il consigne les **erreurs déjà commises** et la règle
qui empêche chacune de revenir. Chaque règle porte le chiffre qui l'a fait naître.

À relire avant d'écrire du code d'entrée/sortie, de lancer un traitement long, ou de
conclure d'une mesure.

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

**Et ce garde ment dans les deux sens — le motif doit désigner le processus, pas son
nom.** Le 08/08 à 23 h 06, `pgrep -f "[m]ethode_maximale.py"` a refusé de démarrer le lot
en annonçant un jumeau : il avait matché **le shell qui lançait ce lot**, dont la ligne de
commande contenait le nom du script parce qu'elle enchaînait un `pgrep` de vérification.
Aucun jumeau n'existait. Un garde en faux positif est pire qu'un garde absent — il bloque
le travail *et* son message affirme le contraire de la réalité, ce qui envoie chercher un
processus fantôme. Ancrer le motif sur l'**invocation réelle** —
`pgrep -f "python3 -u scripts/[m]ethode_maximale\.py"` — et se rappeler que toute commande
qui mentionne le motif entre elle-même dans `ps` : le contrôle et la chose contrôlée
partagent le même espace de noms.

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

## 5. Ce qui relie ces cinq règles

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
