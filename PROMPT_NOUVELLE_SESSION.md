# Prompt de reprise — à coller tel quel dans la nouvelle session

---

Tu reprends un projet en cours, à quatre jours de son échéance. **Commence par lire
`CLAUDE.md` puis `REPRISE.md`**, dans cet ordre : le premier donne les règles nées d'erreurs
déjà commises, le second l'état exact du projet. Ne me demande pas de te réexpliquer ce qui
est déjà écrit dedans.

## En une phrase

Post-traitement statistique des prévisions de qualité de l'air CAMS Europe, destiné à une
candidature spontanée à **Atmo Occitanie**. **Échéance de travail : mercredi 5 août, 12 h**
(la candidature elle-même est au 22 août).

Le cadrage est celui de l'**évaluateur de modèles**, pas du constructeur : la méthode est
publiée, ce qui a de la valeur c'est d'avoir évalué des produits officiels dans les
conventions du référentiel LCSQA et d'avoir mesuré où ils échouent. L'article 13 de l'arrêté
du 16 avril 2021 impose cette évaluation annuelle à chaque AASQA.

## Comment je veux que tu travailles

- **Avance seul.** Je n'ai pas à te relancer entre deux étapes. Quand un calcul tourne, fais
  autre chose pendant ce temps.
- **Parallélise.** La machine a 32 cœurs et un RTX 5090. Une bibliothèque qui prend déjà tous
  les cœurs ne se parallélise pas en la lançant plusieurs fois — mais un lot GPU et un lot CPU
  cohabitent très bien, et j'ai constaté qu'on sous-exploitait la machine.
- **Rigoureux, pas arrogant.** Chaque chiffre porte sa fenêtre, sa population et sa
  convention. Les résultats négatifs se publient comme les autres.
- **Vérifie sur le disque, jamais de mémoire.** L'état d'un artefact se lit à son horodatage
  contre celui de ses sources. « C'est prêt » sans vérification est un défaut en soi — ça
  vient de nous coûter un panel périmé qui aurait faussé la mesure centrale.
- **Mesure avant d'expliquer.** Deux explications que le dossier affirmait se sont révélées
  fausses cette semaine, toutes deux plausibles et sourcées.

## L'environnement

```
interpréteur   /home/cyril/miniforge3/envs/llm-agent/bin/python3   (jamais `python3` nu)
décodage GRIB  environnement mamba « grib », appelé en sous-processus
matériel       32 cœurs · RTX 5090 · 68 Go de RAM
```

XGBoost 3.2 sur `device="cuda"`, LightGBM 4.6 sur CPU. Les scripts d'analyse écrivent dans
`reports/`, les pages dans `reports/figures/`.

Avant de republier une page : `python3 scripts/render_check.py <page>.html` — il teste les
deux thèmes, les erreurs de console et le débordement horizontal. **Republier sur l'URL
existante**, sinon une nouvelle est créée.

## Ce qui t'attend, par ordre de valeur

1. **Le code de validité 4 du LCSQA.** Tout l'ozone après le 01/07/2025 y bascule ; les
   mesures continuent, seule la validation s'est arrêtée. **Treize mois de données en
   dépendent.** La note explicative est sur la fiche data.gouv.fr du jeu temps réel.
2. **Fait le 02/08** — rayon de fossé rejoué à 150 km (O₃, PM2,5) et 75 km (NO₂) :
   **+10,46 %**, **+29,95 %**, **−9,04 %**. Attention à deux formulations fausses qui ont
   circulé : ce n'est **pas un variogramme** mais un corrélogramme par tranches à seuil
   choisi, et le fossé écarte **~111 stations par pli** sur PM2,5, jamais 333 — ce nombre
   additionne les trois plis.
3. **Propager les PM10** aux livrables qui ne les portent pas encore : calendriers de
   signalements et page « Anatomie ».
4. Optionnel : des graines sur l'axe temporel, seul moyen de trancher l'écart entre réglages.

`REPRISE.md` § 6 liste aussi ce qui **m'appartient** — lettre, marge d'utilité, décisions
FAIRMODE, fiche opérationnelle — et surtout ce qui a été **délibérément écarté**, avec la
raison. Ne rouvre pas ces pistes sans élément neuf.

## Les deux choses à ne pas rater

**Les pièges de données** de `REPRISE.md` § 5 sont vérifiés et chiffrés. Le plus coûteux : le
flux LCSQA étiquette l'heure par son **début**, notre chaîne par sa **fin** — sans cela chaque
observation s'apparie à la mauvaise heure de prévision, en silence.

**`reports/VERITE_DOSSIER.md` est la source unique des chiffres**, régénérable par
`python3 scripts/verite_dossier.py`. Tout chiffre du dossier absent d'ici est à retirer ou à
re-mesurer — et toute correction doit y être répercutée **et** dans les pages publiées, qui
ont déjà divergé une fois.

Commence par me dire, en quelques lignes, ce que tu comprends de l'état du projet et ce que tu
comptes faire en premier. Ensuite avance.
