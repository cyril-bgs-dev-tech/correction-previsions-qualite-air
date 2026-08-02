# Stratégie narrative

## 1. La perception recherchée

À la fin de l’entretien, le jury devrait pouvoir résumer le candidat ainsi :

> « Il sait construire un modèle, mais surtout définir le service, trouver les comparateurs gênants, retirer une affirmation quand le test la réfute et transformer une limite en protocole opérationnel. »

La compétence rare à rendre visible n’est donc pas « LightGBM ». C’est l’assemblage de quatre réflexes : mesure à la bonne grandeur, validation hostile, comparaison au produit réellement disponible et traduction en décision.

## 2. Les préoccupations du jury

Le récit doit répondre, dans cet ordre, aux questions silencieuses d’un ingénieur d’AASQA :

1. **À quoi cela sert-il demain matin ?**
2. **À quoi le comparez-vous réellement ?**
3. **Les données existent-elles à l’heure d’émission ?**
4. **Le gain tient-il sur des stations et des dates jamais vues ?**
5. **Que se passe-t-il sur les épisodes et les extrêmes ?**
6. **Quand l’outil se trompe-t-il, et comment revient-on au produit de référence ?**
7. **Que demandez-vous à ATMO Occitanie pour passer du prototype au service ?**

L’architecture, les 53 variables et les hyperparamètres ne viennent qu’après, si une question les appelle.

## 3. L’accroche recommandée

> **« Au début, je cherchais à améliorer CAMS. Puis j’ai obtenu près de 30 % de gain spatial et découvert que ce chiffre pouvait masquer l’essentiel : un modèle peut être meilleur en moyenne et continuer à manquer les jours qui déclenchent une décision. J’ai donc changé la question : à budget de fausses alertes égal, combien de dépassements retrouve-t-on — et quand faut-il ne pas croire la correction ? »**

Cette ouverture contient une promesse, une tension et une décision. Elle évite deux erreurs : commencer par la technologie et annoncer `3,6×` avant que le dénominateur soit compris.

## 4. L’arc en six mouvements

### Mouvement 1 — L’appel : corriger un forçage européen aux stations

Point de départ sobre : CAMS Europe donne le fond régional ; les observations montrent des erreurs locales et de grain. Le projet apprend le résidu aux stations avec des sorties CAMS, le calendrier et des descripteurs de paysage, relief et trafic.

Phrase orale :

> « Mon premier objectif était volontairement simple : mesurer ce qu’une correction apprise apporte à des stations qu’elle n’a jamais vues. »

### Mouvement 2 — Le premier succès, insuffisant

La généralisation spatiale atteint `+29,7 %`, avec un écart-type entre plis de `1,2` et aucun pli spatial négatif. Ce chiffre prouve une capacité d’interpolation vers d’autres stations du réseau ; il ne prouve ni un champ continu ni la robustesse demain.

Phrase orale :

> « Le résultat spatial est solide, mais une station inconnue reste une station du même réseau. Je n’en ai pas fait une carte de France ni une promesse temporelle. »

### Mouvement 3 — Les épreuves qui font tomber le récit facile

Le mois caché donne `+6,7 %`, avec un pire pli à `−35,5 %`. Le blocage station × mois ne donne que `+1,5 %`, avec un pire pli à `−41,4 %`. Une affirmation antérieure — généralisation temporelle démontrée — a donc été retirée.

Phrase orale :

> « Le test qui m’a le plus appris est celui qui a fait baisser mon résultat : cacher aussi le temps a montré que la robustesse temporelle n’était pas acquise. »

### Mouvement 4 — Le déplacement vers la décision

Apprendre directement la grandeur réglementaire apporte `+5,8 points` sur le maximum glissant 8 h d’O₃ et `+6,5 points` sur le maximum horaire de NO₂, mais `−1,5 point` sur la moyenne journalière de PM2,5. C’est une réplication de Bertrand et al. (2023), pas une découverte.

La question devient ensuite : à taux de fausses alertes fixé, quel système ordonne le mieux les jours à risque ? À `30 %` de FAR maximum, CAMS rappelle `0,184` des dépassements d’O₃ et la correction complète `0,656`, soit `3,6×`. Le facteur observé hors fenêtre est `3,5×` avec les seuils fixés sur 2024.

Phrase orale :

> « Le modèle sait mieux ordonner les jours qu’il ne sait en chiffrer exactement la concentration. Pour une aide à l’attention, cet ordre peut être plus utile que quelques dixièmes de RMSE. »

### Mouvement 5 — Les limites qui définissent le produit

- NO₂ : seulement 270 événements au seuil étudié, aucun budget de FAR ≤ 40 % atteignable ; ne pas promettre sa détection.
- Temps : la stabilité temporelle reste le risque principal.
- Support : prédire une station exclue n’équivaut pas à prédire n’importe quel point du territoire.
- Météo : ERA5 apporte un plafond de `+7,8 %` sur O₃, mais ce n’est pas disponible à l’émission ; IFS/AIFS doivent mesurer la part récupérable.
- Produit officiel : en Occitanie 2025, seule la différence de RMSE face au MOS officiel est statistiquement concluante (`−3,22 µg/m³`, IC95 `[−4,87 ; −1,74]`) ; les différences de détection restent descriptives.

Phrase orale :

> « Je ne propose pas une alerte automatique. Je propose un signal de risque borné, avec un comparateur, un seuil choisi par le métier et un repli quand le cas sort du domaine appris. »

### Mouvement 6 — Le retour : ce que le candidat apporte à ATMO

Le livrable n’est pas seulement un modèle : c’est une méthode de décision expérimentale.

- partir de l’heure d’émission et des variables effectivement disponibles ;
- évaluer la grandeur qui déclenche l’action ;
- fixer un budget de fausses alertes ;
- conserver un jeu hors temps et hors stations ;
- comparer au MOS et aux observations récentes, pas au seul CAMS brut ;
- définir avant déploiement les conditions d’abstention et de repli.

Clôture :

> « Je voudrais maintenant confronter trois choix à votre pratique : l’heure de coupure réelle, le budget de fausses alertes acceptable et l’unité utile — station, zone ou commune. Ce sont eux qui décideront du bon modèle, pas l’inverse. »

## 5. Hiérarchie des preuves

### Les trois chiffres à retenir

1. **`+29,7 %`** : capacité spatiale sur stations exclues ; toujours ajouter « mais temporalement +1,5 % en double aveugle ».
2. **`0,184 → 0,656` à FAR ≤ 30 %** : traduction en décision, soit `3,6×` plus de dépassements rappelés.
3. **`−3,22 µg/m³` face au MOS officiel en Occitanie 2025**, IC95 `[−4,87 ; −1,74]` : seule comparaison prospective contre l’officiel qui soit concluante.

### Les trois limites à retenir

1. généralisation temporelle non démontrée ;
2. NO₂ non détectable au seuil et au grain étudiés ;
3. correction aux stations, pas indice officiel spatialisé.

### Les trois comportements à rendre mémorables

1. une affirmation fausse a été retirée ;
2. un benchmark gênant — le MOS officiel — a été ajouté ;
3. les variables disponibles après l’émission ont été séparées des variables déployables.

## 6. Ce qu’il ne faut pas raconter

- Une chronologie exhaustive de scripts et téléchargements.
- Une compétition d’algorithmes : LightGBM, XGBoost et CatBoost diffèrent peu ici.
- Le mythe du modèle « qui découvre la physique ».
- Un voyage du héros centré sur le candidat brillant contre les systèmes existants.
- Une controverse artificielle contre PREV’AIR, CAMS ou Copernicus.
- Une avalanche de métriques sans décision associée.

La controverse utile est méthodologique : **optimiser la concentration moyenne n’est pas nécessairement optimiser la journée sur laquelle un service doit agir.**

