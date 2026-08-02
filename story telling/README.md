# Storytelling du projet — mode d’emploi

Ce répertoire transforme les résultats techniques en une présentation adaptée à un jury d’AASQA. Le but n’est pas de « vendre du machine learning » : il est de rendre immédiatement visible une manière de travailler utile à ATMO Occitanie — partir d’une décision, comparer aux vrais produits disponibles, durcir les tests et dire précisément où l’outil doit s’abstenir.

## Source de vérité

Tout chiffre prononcé ou affiché doit venir de [`reports/VERITE_DOSSIER.md`](../reports/VERITE_DOSSIER.md). Ce document, généré le 31 juillet 2026, remplace les fenêtres et résultats plus anciens encore présents dans certains fichiers de `docs/`.

En particulier :

- ne plus présenter `+0,953` comme la preuve d’une dérive anticipée : la stratification utilise l’erreur réalisée et comporte un couplage arithmétique ;
- ne pas dire que la généralisation temporelle est démontrée ;
- ne pas appeler `3,61 µg/m³` un plancher ou une borne ;
- ne pas dire « nous battons Copernicus » : comparer sobrement deux produits et leurs contraintes ;
- ne pas présenter les `+7,8 %` d’ERA5 comme un gain opérationnel : c’est un plafond rétrospectif ;
- ne jamais présenter le système comme l’indice ATMO officiel ou comme une alerte automatique.

## Principe narratif

> **Une bonne moyenne peut encore manquer la décision. J’ai donc évalué la correction à budget de fausses alertes égal, puis j’ai cherché les conditions dans lesquelles elle ne devait pas être crue.**

Le récit n’a pas pour héros l’algorithme. Le héros est le prévisionniste qui doit décider où porter son attention avec un temps et un budget de fausses alertes limités. Le candidat est le guide qui apporte une mesure, ses limites et un protocole de repli.

## Ce qui vient des notes Marketing

Les documents de `C:\Users\Cyril\Desktop\Marketing\3 ------ Marketing` conduisent aux choix suivants :

| Principe | Traduction pour l’entretien |
|---|---|
| Attention / accroche | commencer par le paradoxe « meilleure RMSE, épisode encore manqué », pas par CAMS, LightGBM ou les 53 variables |
| Réceptivité | parler d’abord de décision, de faux signaux, de délai et de robustesse — préoccupations plausibles d’une AASQA |
| Acheteur potentiel / qualification | s’adresser au prévisionniste, à l’ingénieur d’études et au responsable opérationnel ; ne pas chercher à impressionner un jury ML imaginaire |
| Finalité | vendre la capacité à mieux cibler l’expertise humaine, pas un score ni une architecture |
| Caractère remarquable | faire de la falsification et des résultats retirés la singularité mémorable du projet |
| Visualisation | montrer une journée, un seuil et une décision avant les tableaux nationaux |
| Cadrage | sélectionner peu de chiffres, sans cacher les limites qui changent leur sens |
| Histoire | appel initial → épreuves → résultats qui tombent → déplacement de la question → retour avec un outil borné |
| Appel à agir | terminer par trois choix métier à discuter avec ATMO, plutôt que par « avez-vous des questions ? » |
| Réputation | gagner la confiance par une formulation plus prudente que les chiffres ne l’exigent, jamais par la surenchère |

## Fichiers

- [`01_STRATEGIE_NARRATIVE.md`](01_STRATEGIE_NARRATIVE.md) : positionnement, hiérarchie des messages et arc narratif.
- [`02_TRAME_PRESENTATION.md`](02_TRAME_PRESENTATION.md) : présentation recommandée en 10 écrans.
- [`03_PITCHES_ET_ACCROCHES.md`](03_PITCHES_ET_ACCROCHES.md) : ouvertures et versions 20 secondes, 60 secondes et 3 minutes.
- [`04_OBJECTIONS_ET_REPONSES.md`](04_OBJECTIONS_ET_REPONSES.md) : défense sans surpromesse face à un jury technique.
- [`05_REPETITION_ENTRETIEN.md`](05_REPETITION_ENTRETIEN.md) : protocole de répétition et critères de réussite.
- [`06_PISTES_CREATIVES.md`](06_PISTES_CREATIVES.md) : angles concurrents, métaphores et concepts visuels à tester.

## Règle de ton

Calme, précis, curieux. Une phrase de résultat doit presque toujours contenir son périmètre. Une faiblesse ne doit pas être récitée comme une confession : elle doit montrer la décision méthodologique qu’elle a provoquée.
