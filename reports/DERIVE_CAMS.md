# Voir la dérive du modèle amont le jour où elle se produit

## Le problème, tel qu'il s'est posé

L'erreur de CAMS s'est déplacée à l'automne 2024 : sur l'ozone, le biais de novembre passe de **+4,47 en 2023 à +12,43 en 2024**, et le R² de 0,493 à 0,187. Rien dans les fichiers ne le signale — mêmes attributs, même grille, même producteur d'un bout à l'autre de l'archive, aucun numéro de version.

Ce projet l'a découvert **plus de dix-huit mois plus tard**, et par accident : en vérifiant qu'une validation inter-annuelle avait un sens.

C'est cet écart de dix-huit mois qui est le problème, pas le déplacement lui-même. Un modèle amont évolue ; ce qui coûte, c'est de ne pas savoir quand.

C'est un problème pour toute structure qui exploite CAMS, et il est double : une correction apprise sur l'ancien régime devient partiellement fausse, et un prévisionniste qui accorde sa confiance au modèle continue de la lui accorder sans raison.

## Ce qui est mesuré ici

Horizon **J+1**. La saisonnalité du biais et le seuil d'alarme sont établis sur **les douze premiers mois seuls** (2023-08 → 2024-07), puis appliqués tels quels à la suite. **Rien de ce qui suit le 1er août 2024 n'entre dans le calibrage** — c'est ce qu'aurait fait un indicateur mis en service ce jour-là.

Trois précautions, dont chacune suffirait à rendre l'indicateur inutilisable :

- **Déssaisonnaliser d'abord.** Le biais de CAMS suit un cycle annuel de grande amplitude ; un seuil posé sur le biais brut se déclencherait chaque printemps.
- **Cumuler plutôt que seuiller.** Un changement de version produit un décalage *petit et permanent*, pas un pic. Un seuil instantané le rate ; une somme cumulée (CUSUM) l'accumule jusqu'à devenir indiscutable.
- **Calibrer le seuil sur les données.** Le biais journalier est autocorrélé — les régimes météo durent plusieurs jours — et les seuils tabulés sous indépendance donneraient bien plus de fausses alertes qu'annoncé.

## Le résultat

| Polluant | σ du biais | Seuil | Fausses alertes (12 mois) | 1ʳᵉ alarme | Écart à la bascule U9 |
|---|---|---|---|---|---|
| O3 | 3.63 µg/m³ | 17.0 σ | **0** | 24/10/2024 | **-20 j** *(avant)* |
| NO2 | 1.84 µg/m³ | 13.5 σ | **0** | 28/10/2024 | **-16 j** *(avant)* |
| PM25 | 1.54 µg/m³ | 24.0 σ | **0** | 04/11/2024 | **-9 j** *(avant)* |

La colonne qui donne sa valeur aux autres est celle des **fausses alertes** : le seuil est le plus petit qui n'en produise aucune sur les douze mois de référence. Sans elle, une détection ne prouverait rien — un indicateur qui crie tous les mois finit par « détecter » n'importe quoi.

## Le résultat que je n'attendais pas

**Les trois alarmes précèdent la bascule documentée**, de huit à dix-neuf jours, et sur trois polluants indépendants. La mise à niveau U9 du 13 novembre 2024 **n'explique donc pas** le déplacement : il avait déjà commencé.

C'est l'inverse de ce que j'avais écrit après avoir trouvé les dates dans la documentation ECMWF. J'avais une rupture mesurée sur des moyennes mensuelles, j'ai trouvé un changement documenté dans le bon mois, et j'ai conclu. Le découpage mensuel ne pouvait pas distinguer le 24 octobre du 13 novembre ; l'indicateur journalier le peut, et il dit autre chose.

> Les rapports `RUPTURE_CAMS.md` et `COURBE_APPRENTISSAGE.md` ont été corrigés en conséquence. **La cause du déplacement n'est pas établie.**

## Changement de modèle, ou météorologie ?

Comparer « avant » et « après » à l'intérieur d'une même saison serait fautif : le biais de l'ozone décroît fortement de l'automne à l'hiver, et ce déplacement saisonnier se lirait comme une dérive. La comparaison propre est **d'une année sur l'autre, aux mêmes jours** — 45 jours à partir de l'alarme, contre la même fenêtre calendaire de 2023.

Et le biais seul ne dit pas d'où vient le déplacement. On sépare donc la moyenne **observée**, qui bouge si la météorologie a changé, de la moyenne **prévue**, qui bouge si le modèle a changé.

| Polluant | Stations | Δ biais médian | Concordance | Observé 2023 → 2024 | Prévu 2023 → 2024 |
|---|---|---|---|---|---|
| O3 | 262 | +8.49 µg/m³ | **98 %** | 46.2 → 34.5 (-11.6) | 51.1 → 47.6 (-3.5) |
| NO2 | 322 | +2.12 µg/m³ | **85 %** | 15.6 → 15.5 (-0.1) | 8.6 → 11.3 (+2.7) |
| PM25 | 215 | +2.44 µg/m³ | **91 %** | 9.1 → 10.9 (+1.8) | 7.3 → 11.5 (+4.2) |

**La concordance est élevée partout** — 85 à 98 % des stations se déplacent dans le même sens. Ce n'est donc pas un épisode local : le phénomène est national. Cela n'arbitre pas encore entre un changement de modèle et une anomalie météorologique de grande échelle, qui produiraient tous deux cette signature.

**Les deux dernières colonnes arbitrent, et pas dans le même sens selon le polluant :**

- **O3** — observé -11.6 µg/m³ (25 %), prévu -3.5 µg/m³ (7 %) : le **réel s'est déplacé et la prévision ne l'a pas suivi** — insuffisance du modèle révélée par des conditions inhabituelles, plutôt que changement de code.
- **NO2** — observé -0.1 µg/m³ (1 %), prévu +2.7 µg/m³ (31 %) : **seule la prévision se déplace** — difficile à expliquer autrement que par le modèle lui-même.
- **PM25** — observé +1.8 µg/m³ (20 %), prévu +4.2 µg/m³ (58 %) : **les deux se déplacent**, la prévision 2.9 fois plus en relatif : une cause extérieure a pu s'ajouter à un changement du modèle, sans qu'on puisse les séparer.

**Ce que l'ensemble suggère, sans le démontrer.** Sur le NO₂ le déplacement est difficile à expliquer autrement que par le modèle : l'observation ne bouge pas et la prévision monte d'un tiers. Sur l'ozone c'est l'inverse — le réel a beaucoup baissé et CAMS ne l'a pas suivi, ce qui décrit une **insuffisance du modèle révélée par un automne atypique** plutôt qu'un changement de code. Deux mécanismes différents ont donc pu se superposer, et c'est précisément pourquoi une cause unique ne peut pas être affirmée.

## Les limites, qui sont réelles

- **Une seule rupture connue.** On mesure une date de détection, pas une puissance statistique. Rien ici ne dit ce que l'indicateur ferait d'un changement deux fois plus petit.
- **Le taux de fausses alertes est calibré sur douze mois**, donc connu à cette échelle seulement. En exploitation il se réestime chaque année.
- **L'indicateur date le déplacement, il ne l'explique pas.** Il dit *quelque chose a changé le jour J* ; c'est au service de confronter la date au journal des mises à niveau du fournisseur.
- **Il suppose un réseau d'observation stable.** Une modification massive du parc de stations produirait la même signature. La concordance spatiale y aide, sans lever complètement l'ambiguïté.

## Ce que cela coûte à mettre en service

Un calcul par jour sur des données déjà présentes : le biais moyen du réseau, sa valeur attendue de saison, et deux sommes cumulées. Aucune donnée nouvelle, aucun modèle à entraîner. La partie difficile n'est pas le calcul — c'est d'avoir décidé **avant** ce qui compte comme une alerte.

**Un prérequis, en revanche, est incontournable : douze mois d'historique.** Avec moins, la saisonnalité doit être extrapolée sur les jours de l'année jamais observés, et l'indicateur signale ce trou plutôt qu'une dérive. Le défaut a été trouvé par un test sur série synthétique — sans aucune rupture, une référence de huit mois déclenchait deux alarmes. Le code refuse désormais une référence de moins de 330 jours, en nommant la raison.

## Ce que cet indicateur aurait changé, concrètement

Le déplacement aurait été signalé **fin octobre 2024** au lieu de juillet 2026. Ce qu'un service en aurait fait :

- **interroger le fournisseur** sur un changement en cours, avec une date précise à lui opposer ;
- **réentraîner la correction** sur la période récente, au lieu de continuer avec des coefficients appris sur l'ancien régime ;
- **avertir les prévisionnistes** que le biais du modèle a changé de niveau — l'information la plus directement utile au poste de travail.

Aucune de ces trois actions ne demande de comprendre la cause. C'est le point : **savoir *quand* suffit à agir**, et c'est ce que l'indicateur fournit.
