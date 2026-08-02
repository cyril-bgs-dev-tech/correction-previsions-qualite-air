# Mission — agent Grok, 48 heures sur `/mnt/d/Projet_Air_Quality`

> **Lis `CLAUDE.md` avant toute chose.** Il ne décrit pas le projet : il consigne les erreurs
> déjà commises et la règle qui empêche chacune de revenir. Chaque règle porte le chiffre
> qu'elle a coûté. Elles s'appliquent à toi.

---

## Règles d'engagement, non négociables

**Écriture.** Tu peux créer des fichiers dans `reports/` et `scripts/`. Tu ne modifies
**jamais** `reports/figures/presentation.html`, `LIVRABLE.md`, `app.py`, ni aucun fichier de
`reports/figures/`. Le dossier part sous 48 h ; une édition non vérifiée coûterait plus qu'un
signalement manqué. Tes constats vont dans un rapport, pas dans le livrable.

**GPU — le point qui peut tout casser.** Une autre session travaille sur ce dépôt et lance des
ajustements XGBoost sur le même GPU. Avant **chaque** lancement :

```bash
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv
ps -C python3 -o pid,etime,args=
```

S'il y a déjà un `python3 scripts/…` en cours, **attends**. Ce projet a mesuré ce que coûte
l'inverse : trois ajustements lancés ensemble sur 32 cœurs, **deux tués à 90 minutes sans
finir** — un effondrement d'un ordre de grandeur, parce que la contention porte sur la bande
passante mémoire, pas sur les cœurs. Un seul ajustement à la fois.

**Passe unitaire avant tout lot.** Toute mesure longue commence par **une** unité chronométrée,
puis une extrapolation `t_unitaire × N` écrite noir sur blanc. Si le total est inacceptable, tu
corriges la granularité *avant* de lancer, pas après.

**Journalise.** Tout lot écrit dans `reports/log_<nom>.txt` avec horodatage et compteur de
progression. Un lot muet ne se corrige qu'une fois terminé.

**Nom provisoire puis renommage.** Un artefact au nom définitif est réputé complet et sera
sauté à la reprise. Écris en `.partiel`, vérifie le **contenu attendu**, puis renomme.

---

## Phase 1 — heures 0 à 3 · audit de cohérence *(chemin critique)*

Le dossier a porté des chiffres de **trois fenêtres** (11 mois, 17 mois, 2024) et de **deux
configurations** (cible horaire par défaut, puis cible réglementaire réglée). Une source unique
a été instituée : **`reports/VERITE_DOSSIER.md`**, régénérée par `scripts/verite_dossier.py`.

**Vérifie que tout chiffre publié en dérive.** Balaye, dans cet ordre :
`reports/figures/presentation.html` · `LIVRABLE.md` · `reports/figures/figures.html` ·
`app.py` · `docs/PROGRAMME_RECHERCHE.md`.

Ignore les autres `docs/*.md` : ce sont des échanges avec des relecteurs, ils **doivent**
contenir des chiffres périmés puisqu'ils datent leur propre discussion.

**Signaux connus de péremption** — gain O₃ ≈ **+24 %** ou **+28,3 %**, RMSE corrigé **12,61**
ou **13,71** · Occitanie **+18,8 %** · temporel **+14,4 %**, double aveugle **−24,9 %**, pire
pli **−14,6 %** · CAMS brut O₃ **19,11 / +9,45** · « **année 2024 complète** » (le produit
officiel démarre le **18/01/2024**) · corrélation **+0,913** · le mot « **plancher** » appliqué
aux 3,61 µg/m³.

**Faux positifs à ne pas commettre** — ces écarts sont légitimes :

1. **Grain horaire ≠ grain réglementaire.** O₃ vaut 13,55 en horaire et 9,49 en max 8 h : deux
   grandeurs différentes, deux valeurs justes. Vérifie toujours quel grain le texte annonce.
2. **Effectifs différents** (571 246 couples contre 3,19 M) : le texte doit le dire, l'écart
   n'est pas une erreur.
3. **Réglage par défaut contre réglage retenu** affichés côte à côte : intentionnel.
4. **Plafond météo ≠ performance.** Les gains ERA5 (+7,8 % O₃, +6,7 % PM2,5, +2,7 % NO₂) sont
   un plafond — le modèle du dossier n'utilise aucune météo. Les présenter comme un plafond est
   correct ; les présenter comme un résultat du modèle est une **erreur grave**.

**Sortie** — `reports/AUDIT_COHERENCE.md`, un tableau trié par gravité :

| # | fichier:ligne | valeur publiée | valeur de référence | nature | gravité |

`nature` ∈ {périmé, contradiction interne, portée abusive, introuvable} ·
`gravité` ∈ {bloquant, à corriger, cosmétique}. **Toujours `fichier:ligne`** — un signalement
sans localisation n'est pas vérifiable et sera rejeté. Termine par *N nombres examinés, M
signalements, K bloquants*, et dis explicitement quels fichiers n'ont rien donné : un silence
ne se distingue pas d'un oubli.

---

## Phase 2 — heures 3 à 6 · chercher les jumeaux

Règle du projet : *toute correction d'un motif se termine par une recherche du même motif
ailleurs.* Elle est née d'un défaut corrigé une fois et resté deux fois, qui a fait perdre
**35 % du jeu d'entraînement** en silence. Quatre défauts réels ont été trouvés ; cherche leurs
jumeaux dans `scripts/` et `src/` :

1. **Expression régulière ancrée à droite sur un nom de fichier.** `_(\d{6})\.parquet$` sur
   `..._o3_202308_202309.parquet` capture `202309` et perd `202308` sans lever d'erreur.
2. **`columns=[...]` incomplet sur un référentiel.** Ajouter `altitude` à l'entraînement a
   cassé en silence un script d'application qui ne la chargeait pas. Cherche tout chargement
   qui pourrait diverger de ce que `fit_mos.colonnes_admises` produit.
3. **Jointure morte.** Deux scripts joignaient ERA5 sans qu'aucune colonne n'entre dans les
   prédicteurs — dont un qui en faisait une dépendance bloquante et **annonçait une fausse
   limite**. Cherche toute table lue puis jointe dont les colonnes ne servent nulle part.
4. **Étiquette de grandeur codée en dur.** Un script écrivait `"max_8h"` quel que soit le
   polluant, alors que NO₂ est en max horaire et PM2,5 en moyenne journalière.

**Sortie** — ajoute une section à `reports/AUDIT_COHERENCE.md`. Écarte explicitement les motifs
qui ressemblent mais ne peuvent pas nuire : je préfère une liste courte et sûre.

---

## Phase 3 — heures 6 à 48 · le programme de mesure

Quatre questions ouvertes, **par valeur décroissante**. Chacune a un protocole et un résultat
qui l'enterrerait. Fais-les dans l'ordre ; ne passe à la suivante que la précédente écrite.

### 3.1 — Validation prospective stricte *(la plus importante, ~15 h)*

**La critique.** Notre validation « mois caché » n'est **pas** prospective : rien ne garantit
que toutes les dates d'entraînement précèdent le mois testé. Le terme « double aveugle » est
donc abusif — c'est un *blocage conjoint station-mois*.

**À faire.** Un `rolling-origin` strict sur O₃, grain max 8 h : pour chaque mois M de la
fenêtre, entraîner **uniquement sur les dates < début de M** et prédire M. Vérifier
automatiquement `max(date_entraînement) < min(date_test)` et le journaliser. Comparer au gain
annoncé du blocage conjoint (**+1,5 %**).

**Passe unitaire obligatoire** : un mois d'abord, chronométré, puis extrapolation.

> **Enterré si** le gain prospectif moyen est du même ordre que +1,5 % avec la même dispersion :
> le protocole actuel ne surestimait rien, et seul le vocabulaire était fautif.

### 3.2 — La dispersion intra-maille est-elle une borne ? *(~8 h, CPU)*

**La critique.** Les 3,61 µg/m³ sont présentés comme un plancher irréductible. C'est une
**dispersion** qui mélange différence de support, gradients urbains réels, bruit instrumental
et sélection du réseau. Rien n'établit qu'aucune méthode ne descende sous cette valeur.

**À faire.** Décomposer : ne retenir que des **paires simultanées** de stations dans une même
maille de 0,1°, stratifier par **typologie** (fond/urbain/trafic/industriel) et par distance
entre stations, et **bootstrapper par maille** — jamais par paire, les paires d'une même maille
ne sont pas indépendantes. Donner la dispersion par strate avec IC.

> **Enterré si** la dispersion varie de moins de 30 % entre typologies et que l'IC est étroit :
> le mot « plancher » redevient défendable, et il faudra le réhabiliter.

### 3.3 — Le détecteur d'anomalies, sur les variables *dynamiques* seules *(~4 h)*

**La critique.** `scripts/capteur_situation_anormale.py` conclut qu'un score d'anomalie sur les
entrées n'aide pas. Mais **40 des 53 variables sont statiques** : IForest y détectait surtout
« station au paysage rare », pas « état atmosphérique rare ». Le test n'a jamais été fait.

**À faire.** Rejouer le script en restreignant le détecteur aux variables **dynamiques** —
`cams_jour`, `cams_moy_jour`, `echeance_h` et le calendrier — puis, en variante, aux seules
variables météo ERA5. Mêmes trois questions que le script d'origine (dérive, performance
conditionnelle avec contrôle sur la valeur de CAMS, modes fonctionnels).

> **Enterré si** les trois verdicts sont inchangés : la conclusion négative tient, et elle
> devient bien plus solide.

### 3.4 — MQI par station, pas en agrégé *(~3 h, CPU)*

**La critique.** Trois valeurs agrégées de MQI FAIRMODE (O₃ 0,255 · NO₂ 0,485 · PM2,5 0,354)
ne montrent pas la conformité **par station**. Un MQI global peut masquer des stations non
conformes par compensation.

**À faire.** Étendre `scripts/mqi_bon_grain.py` : distribution du MQI par station, **taux de
conformité** (part des stations à MQI ≤ 1), et ventilation par typologie. Rapporter aussi le
pire décile.

> **Enterré si** 100 % des stations sont conformes dans les trois polluants : l'agrégat ne
> masquait rien, et on peut le citer tel quel.

---

## Ce que je ne te demande pas

- Aucune proposition d'amélioration du modèle : d'autres rondes s'en chargent, et les
  architectures alternatives, la spatialisation EPCI, l'exclusion des stations difficiles et la
  recherche exhaustive d'hyperparamètres sont **déjà tranchées et mesurées**.
- Aucune réécriture de texte du dossier.
- Aucun téléchargement.

## Rendu

Un fichier `reports/RAPPORT_AGENT.md` mis à jour **au fil de l'eau**, pas à la fin — si tu es
interrompu à 30 h, ce qui est écrit doit valoir. Pour chaque mesure : le protocole exact, le
résultat, l'IC quand il a un sens, et **la phrase que le dossier aurait le droit d'écrire**.

Un résultat négatif proprement établi vaut ici autant qu'un positif : trois des découvertes les
plus utiles de ce projet sont des réfutations.
