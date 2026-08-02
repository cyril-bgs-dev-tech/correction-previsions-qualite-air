# Répétition de l’entretien

## Objectif

La répétition ne sert pas à réciter. Elle sert à rendre stable une hiérarchie : décision → preuve → limite → prochaine action. Le candidat doit pouvoir raccourcir ou approfondir sans changer le sens des résultats.

## Trois formats à maîtriser

| Format | Contenu | Temps cible |
|---|---|---:|
| réponse spontanée | pitch 20 secondes | 15–25 s |
| « parlez-nous du projet » | pitch 60 secondes | 50–75 s |
| présentation demandée | 10 écrans | 9–11 min |

S’entraîner avec un chronomètre, puis retirer les mots — jamais accélérer le débit pour faire entrer trop de matière.

## Test de mémorisation

Après une répétition, demander à une personne de restituer :

1. la décision servie ;
2. les trois chiffres principaux ;
3. la limite principale ;
4. ce que le candidat veut apprendre d’ATMO.

Si elle retient « LightGBM, 53 variables, beaucoup de données », la narration a échoué. Si elle retient « 3,6× » sans « à FAR ≤ 30 % », elle est dangereuse.

## Grille de notation sur 20

| Critère | Points | Question de contrôle |
|---|---:|---|
| Accroche | 2 | le problème est-il compris en 20 secondes ? |
| Finalité | 3 | sait-on quelle décision humaine est aidée ? |
| Comparabilité | 3 | MOS, périmètre, dates et seuils sont-ils nommés ? |
| Rigueur | 4 | stations, temps, intervalles et résultats retirés sont-ils distingués ? |
| Lisibilité | 2 | trois chiffres au maximum restent-ils en mémoire ? |
| Domaine | 2 | CAMS, grain réglementaire et limites NO₂ sont-ils correctement cadrés ? |
| Posture | 2 | le candidat est-il guide, pas vendeur d’IA ? |
| Appel à agir | 2 | la fin ouvre-t-elle sur trois choix métier précis ? |

Seuil de passage : 16/20 sans aucune erreur de périmètre.

## Drill d’objections

Une seconde personne tire au hasard une objection de [`04_OBJECTIONS_ET_REPONSES.md`](04_OBJECTIONS_ET_REPONSES.md). Réponse en 45 secondes maximum selon quatre temps :

1. **Oui / non direct.**
2. **La mesure.**
3. **La limite de la mesure.**
4. **La décision qui en découle.**

Exemple : « Votre modèle généralise-t-il dans le temps ? »

> « Pas de manière démontrée. Le double aveugle ne gagne que 1,5 %, avec un pire pli à −41,4 %. En revanche, le classement à FAR fixé se reproduit hors fenêtre. J’en déduis qu’un déploiement devrait réétalonner et surveiller le modèle, pas le figer. »

## Drill de précision

Interdire pendant une répétition les mots suivants sans complément immédiat :

- « épisode » → préciser seuil, polluant, grain et unité de comptage ;
- « hors échantillon » → préciser station, date ou les deux ;
- « améliore » → préciser métrique, comparateur et période ;
- « opérationnel » → préciser disponibilité à l’émission et comportement de repli ;
- « officiel » → préciser produit MOS ou indice ATMO ;
- « significatif » → donner l’intervalle ou ne pas employer le mot.

## Drill de visualisation

Présenter l’écran 6 sans formule. Le jury doit pouvoir répondre à cette question :

> « Si j’accepte au maximum trois fausses alertes sur dix alertes, quel système me fait manquer le moins de vrais dépassements ? »

Si le visuel exige d’expliquer POD, FAR, CSI et Brier simultanément, le simplifier. Les définitions restent en annexe.

## Drill de contradiction

Faire jouer au contradicteur les positions suivantes :

1. « CAMS brut n’est pas votre vrai concurrent. »
2. « Votre validation spatiale avantage les covariables de site. »
3. « Votre facteur 3,6 est une optimisation de seuil. »
4. « ERA5 est une fuite. »
5. « Avec huit plis négatifs, votre outil n’est pas déployable. »
6. « Vous avez répliqué Bertrand, où est la nouveauté ? »

Le but n’est pas de gagner le débat. Le but est de montrer que l’objection est déjà dans le périmètre du projet et qu’elle change une décision précise.

## Préparation matérielle

- une présentation principale de 10 écrans, exportée en PDF ;
- une version de secours de 5 écrans ;
- annexes numérotées, accessibles en moins de dix secondes ;
- une fiche papier avec seulement 10 chiffres et leurs périmètres ;
- aucun tableau dont la source n’est pas `reports/VERITE_DOSSIER.md` ;
- captures ou figures utilisables hors connexion ;
- noms et DOI de Bertrand et du référentiel FAIRMODE prêts, sans bibliographie récitée.

## Les dix nombres de la fiche papier

1. `+29,7 %` — stations exclues.
2. `+6,7 %` — mois caché.
3. `+1,5 %` — station × mois.
4. `−41,4 %` — pire pli double aveugle.
5. `+5,8 pts` — cible directe O₃.
6. `0,184 → 0,656` — rappel O₃ à FAR ≤ 30 %.
7. `3,6×` — facteur correspondant.
8. `3,5×` — reproduction 2025.
9. `−3,22 µg/m³` — RMSE contre MOS officiel en Occitanie 2025.
10. `270` — dépassements NO₂, raison de ne pas promettre sa détection.

Chaque nombre doit pouvoir être développé en une phrase contenant comparateur, période et protocole.

## Critère final

La présentation est prête lorsque le candidat peut répondre sans slide :

> « Quel est le service ? Quel est le vrai concurrent ? Quelle preuve tient ? Quelle preuve tombe ? Que fait-on quand le modèle ne doit pas être cru ? »

