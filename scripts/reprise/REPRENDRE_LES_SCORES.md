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
| **cpu** | un lot LightGBM à la fois — trois concurrents s'effondrent d'un ordre de grandeur | `/tmp/aq-file-cpu.lock` |
| **réseau ECMWF** | acquisition IFS — 84 % d'attente serveur, aucun cœur consommé | aucun, mais un garde de jumeau |

Les faire tourner en parallèle est correct et souhaitable : une ressource au repos pendant
qu'une tâche attend ailleurs est un défaut, pas une prudence.

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
