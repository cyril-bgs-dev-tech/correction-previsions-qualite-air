# Reprendre les mesures de score — dans n'importe quelle session

*Écrit le 24/08/2026. Ce fichier remplace les lanceurs qui vivaient dans le répertoire
temporaire de session et disparaissaient avec elle.*

## En une commande

```bash
cd /mnt/d/Projet_Air_Quality
scripts/reprise/relancer.sh --plan       # ce qui reste, et pourquoi
scripts/reprise/relancer.sh --avec-ifs   # lance tout : mesures + acquisition réseau
```

**Relancer est sûr.** Le plan se dérive des artefacts, donc rien n'est refait inutilement ;
le verrou `flock` interdit deux files sur la même ressource ; et chaque tâche est jugée sur
son artefact, une tâche qui n'écrit rien arrêtant la file.

## Ce que « déjà fait » veut dire ici

Un artefact **existe** ne suffit pas. Beaucoup datent d'avant la correction du corpus du
23/08 vers 20 h 26 — cinq mois de spéciation ajoutés, qui ont déplacé la base de 0,17 à
0,32 pt et fait tomber `fourier` de « démontré » à « non confirmé ».

Une tâche est donc **à refaire si son artefact est plus ancien que le plus récent fichier
de spéciation**. Le repère se lit sur disque ; il n'est écrit nulle part.

⚠️ Pour les ablations jointes, le repère porte sur la **pile réduite**, pas sur le verdict
qui la relit : le verdict se réécrit en secondes, la pile demande vingt minutes.

## Les deux ressources, et pourquoi elles tournent ensemble

| ressource | ce qui y passe | verrou |
|---|---|---|
| **cpu** | **quatre lots à `n_jobs=8`** — mesuré le 24/08 : 11,9 cœurs sur 32, 28 Go sur 68 | `/tmp/aq-file-cpu.lock` |
| **réseau ECMWF** | acquisition IFS — 84 % d'attente serveur, aucun cœur consommé | aucun, mais un garde de jumeau |

⚠️ **La ligne « un lot à la fois » a été fausse pendant huit jours.** Elle venait d'un essai
en `n_jobs=-1`, où trois ajustements demandaient 96 fils sur 32 cœurs. À `n_jobs=8` la
situation n'est pas la même, et LightGBM plafonne de toute façon à ~1,5 cœur par lot : la
parallélisation utile est **entre** les ajustements. Le 24/08 à 13 h, la file sérialisée
tournait à **charge 0,09 sur 32 cœurs** — une constante appliquée hors de son domaine de
mesure, ce que la règle A interdit.

Les faire tourner en parallèle est correct et souhaitable : une ressource au repos pendant
qu'une tâche attend ailleurs est un défaut, pas une prudence.

## Lancer en parallèle, et juger sur l'artefact

```bash
python3 scripts/plan_scores.py --taches | scripts/lancer_en_parallele.sh 3 90 20G cpu logs/reprise.log
#                                                                        │  │   │   └ ressource verrouillée
#                                                                        │  │   └ plafond mémoire par tâche
#                                                                        │  └ décalage des démarrages (le pic est au CHARGEMENT)
#                                                                        └ tâches simultanées
#
# 🔴 Le cinquième argument est le JOURNAL, et il n'est pas un confort : sans lui on écrit
#    « ... | tee logs/x.log », et le code de sortie appartient alors à `tee`. Le 24/08, le
#    garde a imprimé « ⛔ ABSENT » sur QUATRE artefacts et la commande a rendu 0 — règle C
#    violée dans la commande de lancement elle-même.
```

Le lanceur consomme **le format que `plan_scores.py --taches` émet déjà** (`cible :: commande`),
et son verdict porte sur l'artefact : il exige qu'il **existe** *et* qu'il soit **postérieur au
lancement**. Éprouvé sur trois tâches rendant toutes 0 — l'une écrivant, l'une laissant un
fichier d'hier, l'une n'écrivant rien : seule la première passe.

## Savoir ce qui est périmé — sans le refaire

```bash
python3 scripts/descendance.py                    # ce qui est périmé aujourd'hui, et par quel parent
python3 scripts/descendance.py --si data/processed/meteo/speciation_metropole_202312.parquet
python3 scripts/descendance.py --graphe           # la descendance déclarée, en entier
```

C'est la mécanisation de la plus grosse perte mesurée : le 23/08, compléter la spéciation a
périmé des mesures publiées **sans que rien ne le dise**, et je l'ai découvert en les
refaisant (3 h). La même question se répond maintenant en 6 s — la spéciation porte
**100 artefacts**.

⚠️ Il rend un **minorant** de la péremption, jamais un certificat de fraîcheur : une date
postérieure ne prouve pas que l'artefact a été calculé sur ce parent-là. D'où le troisième
état, `inaudité`, pour ceux qui n'ont pas d'empreinte d'entrées — là, la question ne peut
pas être tranchée, et le script le dit au lieu de supposer.

## Vérifier que ça avance

```bash
tail -f logs/suite_cpu.log                       # ou le journal de la file en cours
scripts/pids_de.sh scripts/methode_maximale.py --details   # jamais pgrep : il se voit
python3 scripts/registre.py etat                 # les prédictions scellées
python3 scripts/plan_scores.py                   # l'avancement
```

## Ce que chaque étape débloque

| étape | ce qu'elle décide |
|---|---|
| **reference** | tout se compare à elle — un apport sur base périmée est deux mesures |
| **fenetre-complete** | onze blocs rendent-ils testable ce que neuf ne résolvent pas ? *(prédiction `a2706756`)* |
| **pre-moyennes** | précurseurs à 4 colonnes plutôt que 8 *(prédiction `bb74bc95`)* |
| **core7** | ce que valent les colonnes de spéciation qui datent le mois *(prédiction `281e97ca`)* |
| **auditable** | le prix de l'auditabilité, en apparié et non en soustraction de gains |
| **ablations-jointes** | `feux+tendance` coûte-t-il ? `geoscf+membres` ? |
| **ifs** | la pile ne porte **aucune météo**, et l'IFS est prévu donc déployable |

## Les pièges déjà payés, à ne pas refaire

* **Ne jamais comparer deux gains publiés.** 0,14 % de données déplacent un pli de 2,56 pt,
  soit 65 × le bruit d'exécution. Seul l'écart **apparié** — mêmes plis, même graine — porte
  une conclusion. `scripts/comparer_piles.py` le fait et refuse les corpus différents.
* **Ne jamais tuer par motif.** `scripts/pids_de.sh`, jamais `pgrep -f` : le motif figure
  dans la ligne de commande qui l'évalue.
* **Lire le bloc « CONSERVÉES »** que la pile imprime : quatre familles portent des mois
  entièrement absents, et c'est un indicateur d'époque implicite.
* **`command grep`**, jamais `grep` : le second respecte `.gitignore` et saute en silence.

## Où sont les résultats

* `reports/PALIER_A.md` — la synthèse, tenue à jour ;
* `reports/verdict_apport_*.csv` — les verdicts par famille ;
* `reports/apport_derniere_position.csv` — ce que chaque famille de la pile paie ;
* `reports/registre_predictions.jsonl` — les prédictions scellées et leur calibration.
