# Mission 2 pour ChatGPT — encadrer le gain météo sans archive IFS

> À coller tel quel. Suite directe de `MISSION_GPT_SPECIFICATIONS.md`, dont les quatre
> livrables sont reçus et appliqués.

---

## Ce que ta réponse précédente a changé

Deux corrections retenues, et la première a redimensionné notre principale piste :

1. **L'open data ECMWF ne conserve que les 12 derniers runs** (2 à 3 jours) ; l'archive
   opérationnelle historique est dans MARS, sous droit d'accès. Le document de programme de
   recherche annonçait les prévisions IFS comme « disponibles opérationnellement » : c'était
   faux, c'est corrigé.
2. **« Une correction n'ajoute que là où la physique amont est aveugle »** est une règle
   d'allocation de l'effort, pas une conclusion scientifique : le nul des copolluants vaut
   conditionnellement à ces variables, cette cible, cette perte et ces 17 mois. C'est reformulé
   dans le dossier.

Tes six variables prioritaires (`t2m_max`, `ssrd_sum`, `vpd_max`, `vc_p10`, `stagnant_day`,
`dry_hours`) et leurs formules sont retenues telles quelles, ainsi que ton critère
d'invalidation à +3,9 points.

**Le problème qui reste** : je ne peux pas les calculer sur une **prévision** couvrant août 2023
→ décembre 2024. Je n'ai qu'ERA5, une réanalyse, qui donne un **plafond** — mesuré à **+7,8 %**
sur O₃, +6,7 % sur PM2,5, +2,7 % sur NO₂, IC95 tous positifs, décile haut meilleur partout.

---

## Livrable 1 — L'expérience d'encadrement *(la plus urgente)*

Une météo **prévue** est, en contenu informationnel, quelque part entre la **réanalyse** du jour
et une information **dégradée** dont je dispose déjà. L'idée : borner le gain d'une vraie
prévision par-dessous, sans télécharger quoi que ce soit.

**Spécifie l'expérience.** Les candidats évidents pour la borne basse sont la météo **persistée**
(ERA5 de J−1 utilisée comme si elle valait pour J) et la **climatologie** locale du jour de
l'année. Mais tu connais mieux que moi les propriétés d'erreur d'une prévision à J+1 à J+3, et
c'est là que je veux ton jugement :

- **Quelle dégradation d'ERA5 imite le mieux l'erreur d'une prévision IFS à J+1 ?** Persistance,
  bruit calibré sur les scores publiés de l'IFS, lissage spatial, décalage temporel ? Donne la
  transformation exacte, avec ses paramètres, et **pourquoi elle est conservative** — je veux
  une borne, pas une estimation optimiste.
- **Comment la faire varier avec l'échéance** J+1, J+2, J+3, puisque l'erreur météo croît et que
  c'est précisément ce qui déterminera si la piste tient à J+3.
- **Quels scores publiés** de l'IFS (RMSE de température à 2 m, de vent, de hauteur de couche
  limite, à ces échéances, en Europe) dois-je utiliser pour calibrer la dégradation ? Donne les
  valeurs et la source.
- **Le résultat qui enterre la piste** : sous quel gain de la borne basse dois-je conclure que
  le conditionnement météo ne survivra pas au passage en prévision ?

Contrainte : l'expérience doit tourner sur les données déjà présentes (ERA5 horaire, 69 mois,
2019-07 → 2026-07, 8 variables : précipitation, rayonnement, température, point de rosée,
pression, hauteur de couche limite, direction et vitesse du vent aux stations).

---

## Livrable 2 — Les archives de prévision réellement ouvertes

Je cherche une archive de **prévisions** météo, pas de réanalyse, couvrant la France, août 2023
→ décembre 2024, en accès libre.

Pour chaque source que tu identifies :

| source | modèle | emprise | profondeur d'archive | variables utiles disponibles | mode d'accès | ce qui bloque |

Candidats à examiner explicitement, et à écarter si nécessaire :

- les données publiques de **Météo-France** (AROME, ARPEGE) et leur portail ;
- les **archives de prévision** éventuellement redistribuées par des tiers ;
- les champs météo que **CAMS lui-même** embarque ou publie avec ses sorties — s'il en publie,
  c'est la solution idéale puisqu'ils sont par construction alignés sur la prévision que je
  corrige ;
- toute réanalyse à **courte latence** qui approcherait les conditions opérationnelles.

Sois concret sur la **profondeur d'archive** : c'est le critère qui a fait tomber l'IFS open
data. Une source qui ne remonte pas à août 2023 ne m'est d'aucune utilité pour l'entraînement,
et je préfère que tu l'écartes toi-même.

---

## Livrable 3 — La question que je devrais me poser et que je ne me pose pas

Sur ce point précis — le conditionnement météorologique d'une correction de prévision de qualité
de l'air — qu'est-ce que la littérature a établi que je risque de redécouvrir ?

Trois entrées maximum, chacune avec : ce qui est publié, sur quel système, et **ce que cela
implique pour la valeur de ma piste**. Si quelqu'un a déjà mesuré l'écart entre correction
conditionnée par réanalyse et par prévision, c'est exactement ce que je veux savoir avant de
dépenser une semaine.

---

## Contexte utile

- 17 mois appariés (août 2023 → décembre 2024), 270 stations, 134 423 jours-station sur O₃.
- Cible : résidu `observation − CAMS` à la grandeur réglementaire (max 8 h pour O₃).
- Validation par stations entièrement exclues ; IC par bootstrap de stations.
- Critère d'arrêt du projet : gain ≥ 0,3 µg/m³ **absolu** — critère reconnu défectueux entre
  polluants d'échelles différentes, désormais doublé d'une lecture en relatif.
- Échéance de candidature : 22 août 2026. Le dossier part sous 48 h ; cette piste est présentée
  comme un programme de recherche, pas comme un résultat.
