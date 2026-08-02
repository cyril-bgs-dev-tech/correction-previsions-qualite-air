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
