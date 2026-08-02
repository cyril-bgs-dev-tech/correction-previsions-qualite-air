# Prompt pour Grok 4.5 — les 30 prochaines actions, angle valeur et usage

> À coller tel quel. Le document est autoportant.

---

Tu es le relecteur adverse d'un projet de science des données sur la qualité de l'air, destiné
à une **candidature spontanée à ATMO Occitanie le 22 août 2026**. Ta tâche : **proposer les 30
prochaines actions**, ordonnées par valeur décroissante.

ChatGPT reçoit le **même état** avec une consigne opposée : validité statistique, protocole,
falsifiabilité, bibliographie. **N'écris pas là-dessus.** Ton angle est celui du **destinataire** :

- ce qu'une AASQA ferait réellement de ce travail, un mardi matin, en astreinte prévision ;
- ce qui distingue ce dossier de ceux qu'un recruteur voit passer ;
- les angles morts — ce que je *vois* sans l'*observer*, alors que ça vaudrait cher ;
- ce que je dis mal, ou trop, ou pas assez.

Tu as un droit de contradiction total, y compris sur la prémisse que ce projet vaille la peine.

---

## 1. Ce qu'est le projet

Post-traitement statistique des prévisions CAMS Europe (grille 0,1°, ≈ 8 km, échéances J+1 à
J+3) pour O₃, NO₂ et PM2,5. Le modèle apprend le **résidu** `observation − CAMS` à partir de la
météo ECMWF, du relief, du paysage, du trafic hiérarchisé et du calendrier, puis corrige la
prévision aux stations.

Le contexte métier : une AASQA publie chaque jour un **indice ATMO** par EPCI et déclenche des
**procédures préfectorales** quand un seuil est franchi. Les seuils réglementaires ne portent
pas sur des concentrations horaires mais sur des **agrégats** : maximum glissant 8 h pour
l'ozone (120 µg/m³), maximum horaire pour le NO₂, moyenne journalière pour les PM2,5.

## 2. Les résultats, sans emballage

**Contre CAMS brut**, 17 mois, stations entièrement exclues de l'entraînement :
O₃ **+19,3 %** de RMSE en moins, NO₂ **+29,7 %**.

**Contre le produit corrigé que Copernicus publie déjà** (`optimised-at-observation-sites`,
gratuit, réentraîné en continu), année 2024 complète :

| polluant | grain | CAMS brut | MOS officiel | nous |
|---|---|---|---|---|
| O₃ | horaire | 17,30 | 14,43 (+16,6 %) | 13,55 (+21,7 %) |
| O₃ | **max 8 h** (le grain réglementaire) | 12,08 | 11,85 (**+2,0 %**) | 9,49 (**+21,5 %**) |
| NO₂ | horaire | 7,75 | 6,45 (+16,7 %) | 7,54 (**+2,7 %**) |
| NO₂ | **max horaire** | 15,13 | 12,03 (+20,5 %) | 10,34 (+31,6 %) |
| PM2,5 | horaire | 5,17 | 4,68 (+9,5 %) | 4,11 (+20,5 %) |
| PM2,5 | **moyenne jour** | 3,79 | 3,22 (+15,0 %) | 2,69 (+29,1 %) |

Ma lecture actuelle : **le grain sur lequel on corrige décide du résultat**. Leur
post-traitement est horaire ; les seuils sont des maxima, donc des statistiques d'ordre, que
toute réduction de variabilité dégrade. La réciproque me condamne aussi : sur NO₂ horaire je
n'apporte que **+2,7 %**, parce que j'ai optimisé l'autre grain. Le phénomène est **publié**
(Huang et al. 2017) — je le quantifie, je ne le découvre pas.

**Test hors fenêtre d'apprentissage** — appris jusqu'au 31/12/2024, appliqué au 1ᵉʳ semestre
2025, 21 stations occitanes, 3 353 jours-station, 163 dépassements observés :

| produit | RMSE | POD@120 | FAR | CSI |
|---|---|---|---|---|
| CAMS brut | 11,04 | 0,331 | 0,069 | 0,323 |
| MOS officiel | 13,56 | 0,460 | 0,312 | 0,381 |
| nous | **10,33** | 0,239 | 0,049 | 0,236 |

Avec un **seuil de décision recalibré sur 2024** puis appliqué en aveugle sur 2025 — tous les
produits recalibrés de la même façon :

| produit | POD | FAR | CSI |
|---|---|---|---|
| CAMS brut | 0,515 | 0,229 | 0,447 |
| MOS officiel | **0,718** | 0,543 | 0,387 |
| nous | 0,571 | **0,212** | **0,495** |

Autrement dit : mon POD de 0,239 était un artefact de seuil, pas une incapacité. Mais **je ne
domine pas** — le produit officiel détecte davantage, en acceptant plus d'une fausse alerte sur
deux.

**Le reste, en vrac** :

- généralisation **spatiale** solide : +19,4 %, σ 1,2 sur les plis ;
- généralisation **temporelle** faible : double aveugle (station *et* mois cachés) **+1,5 %**,
  pire pli **−14,6 %** ;
- classifier le dépassement plutôt que régresser la concentration : POD 0,345 → **0,663** ;
- perte pondérée : la queue haute passe de −3,1 % à **+3,1 %** sans coûter de RMSE global ;
- trafic hiérarchisé (BD TOPO) : **+13,0 %** sur NO₂ ; la population n'ajoute rien ;
- sur O₃ la variable la plus utile est le **calendrier** — la retirer coûte +9,1 % ;
- plancher de représentativité intra-maille : **3,61 µg/m³**, soit 26 % du RMSE actuel ;
- deux **ruptures du forçage CAMS** (13/11 et 03/12/2024) : corrélation **+0,913** entre le saut
  de biais et le gain de ma correction — une part de mon gain est une régression du forçage,
  pas une découverte.

## 3. Ce qui existe comme livrable

- Une **présentation de 10 pages** en HTML et une bibliothèque de **9 figures** — mais elles
  citent encore des chiffres d'une fenêtre de 11 mois, désormais périmés.
- Une **démo Streamlit** à 6 pages.
- Une **fiche opérationnelle** (quelles entrées sont garanties à l'heure d'émission) — écrite
  mais **non validée**, ce qui bloque l'usage des observations récentes en entrée.
- Un **manifeste de reproductibilité** : versions, empreintes des données, fraîcheur de chaque
  rapport.
- Un **archivage quotidien de l'indice ATMO officiel** (cron installé) — le flux est glissant
  et destructif, il fallait le capturer pour pouvoir se comparer plus tard.

## 4. Les faiblesses que je connais déjà

1. **Aucune observation métropolitaine en 2025** (flux EEA rompu) : toute ma validation
   inter-annuelle tient sur 21 stations occitanes.
2. La **spatialisation à l'EPCI** — le dernier maillon vers l'indice réellement publié — est
   abandonnée faute de temps. L'écart résiduel est de **−0,72 classe** d'indice.
3. « Station inconnue » veut dire *autre station du même réseau*, pas *lieu quelconque* : ma
   meilleure revendication est plus étroite qu'elle n'en a l'air.
4. Une station et une maille de 0,1° ne décrivent pas le même objet (écart 5 à 30 µg/m³).
5. Le **MQI FAIRMODE** est calculé en horaire pour les trois polluants alors que le référentiel
   le définit en max 8 h (O₃) et journalier (PM2,5) : la conformité annoncée sort du cadre.
6. La méthode est **déjà industrialisée** : PREV'AIR corrige par apprentissage, Copernicus
   publie un produit MOS. Je n'invente rien.

## 5. Contraintes dures

- **22 août 2026**, arrêt des calculs 10 jours ouvrés avant.
- **Registre imposé : rigueur, pas arrogance.** Pas de « je bats Copernicus ». Énoncer les
  faits, et dire d'abord que j'ignore les contraintes qui ont motivé leurs choix.
- Déjà tranché, ne pas rouvrir : architectures alternatives (mesurées, écartées),
  spatialisation EPCI, exclusion des stations difficiles, recherche exhaustive
  d'hyperparamètres.

---

## Ce que je te demande

**30 actions, numérotées, de la plus utile à la moins utile**, dans un tableau à ces colonnes :

| # | Action | Pour qui elle compte (prévisionniste / direction / recruteur / jury) | Coût (h) | Ce qu'elle rend possible qui ne l'est pas aujourd'hui |

Contraintes de rédaction :

1. Au moins **10 des 30** ne doivent produire **aucun calcul** — démonstration, formulation,
   figure, entretien, mise en situation. Un dossier ne se juge pas au RMSE.
2. Au moins **5** doivent viser une **faiblesse de la section 4** en la transformant en atout
   énonçable, sans la masquer.
3. Aucune action ne doit reposer sur une donnée que je n'ai pas. Si tu en proposes une, dis
   explicitement où la prendre et en combien de temps.
4. Sois **concret**. « Améliorer la narration » ne vaut rien ; « remplacer la page 3 par la
   comparaison des trois grains, parce que c'est le seul résultat qu'un prévisionniste ne
   connaît pas déjà » vaut quelque chose.

Puis, hors tableau :

- **A.** Un prévisionniste d'astreinte lit ce dossier en 4 minutes. **Qu'est-ce qu'il retient**,
  et **qu'est-ce qui l'agace** ?
- **B.** Le tableau de la section 2 dit que je gagne peu en horaire sur NO₂ (+2,7 %). Est-ce une
  faiblesse à corriger, ou la **preuve de ma thèse** qu'il faut mettre en avant ? Argumente les
  deux côtés puis tranche.
- **C.** « Je vois mais je n'observe pas » : nomme **trois choses présentes dans mes données ou
  mes résultats** que je n'exploite pas et qui vaudraient plus que le prochain point de RMSE.
- **D.** Quelle est la **question de jury** à laquelle je ne sais pas répondre aujourd'hui, et
  qui a le plus de chances d'être posée ?
- **E.** Si tu devais **supprimer 5 choses** du projet pour le rendre meilleur, lesquelles ?
- **F.** Le projet mérite-t-il un poste, ou seulement un entretien ? Réponds franchement, et dis
  ce qui manque pour passer de l'un à l'autre.

Ne me ménage pas. Si le cadrage est mauvais, dis-le avant de répondre au reste.
