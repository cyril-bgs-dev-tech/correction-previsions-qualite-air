# Pitches et accroches

## Accroches à tester

### Recommandée — paradoxe de décision

> « Un modèle peut gagner près de 30 % en erreur moyenne et continuer à manquer le jour sur lequel il faudrait agir. C’est ce paradoxe qui a déplacé tout mon projet. »

### Variante — budget opérationnel

> « La question n’est pas seulement : quel modèle a la meilleure RMSE ? C’est : avec le même nombre de fausses alertes, lequel retrouve le plus de dépassements ? »

### Variante — rigueur

> « Le résultat dont je suis le plus fier n’est pas le meilleur score. C’est une affirmation que j’ai retirée quand le test station × temps l’a réfutée. »

### Variante — grain réglementaire

> « J’ai changé davantage la performance en changeant la cible qu’en changeant d’algorithme : apprendre le maximum qui décide vaut plus que corriger vingt-quatre heures puis prendre leur maximum. »

## Accroches à ne pas utiliser

- « J’ai battu CAMS/Copernicus de 30 %. »
- « Mon IA détecte 3,6 fois plus d’épisodes. »
- « J’ai développé un modèle révolutionnaire pour ATMO Occitanie. »
- « Grâce à 53 variables et LightGBM… »

Elles surpromettent, déclenchent immédiatement une bataille de périmètre et forcent le jury à chercher la faille avant d’avoir compris la décision.

## Pitch 20 secondes

> « J’ai construit une correction de CAMS évaluée sur des stations entièrement exclues. Le résultat important n’est pas seulement le gain spatial : à budget de fausses alertes égal, le classement des jours d’ozone rappelle 3,6 fois plus de dépassements que CAMS brut. Mais la robustesse temporelle reste faible ; mon livrable est donc autant un protocole de garde-fou qu’un modèle. »

## Pitch 60 secondes

> « Mon projet part d’une correction apprise des prévisions CAMS aux stations. Sur des stations jamais vues, le gain spatial atteint 29,7 %, mais lorsque je cache simultanément stations et mois il tombe à 1,5 %, avec des plis négatifs. J’ai donc retiré l’idée d’une robustesse temporelle démontrée et déplacé l’évaluation vers le service : à budget de fausses alertes égal, combien de dépassements d’ozone sont rappelés ? À 30 % maximum, CAMS en rappelle 18,4 % et la correction complète 65,6 %, soit 3,6 fois plus ; le facteur est proche hors fenêtre en 2025. Je ne présente pas cela comme une alerte automatique : le NO₂ reste indétectable et le support est celui des stations. Ce que j’apporte surtout, c’est une méthode pour aligner cible, données disponibles à l’émission, comparateur et décision. »

## Pitch 3 minutes

> « Au départ, je cherchais simplement à savoir si une correction apprise pouvait améliorer CAMS aux stations. J’ai entraîné un modèle de résidu avec des sorties CAMS, le calendrier, le paysage, le relief et le trafic, puis évalué chaque station avec un modèle qui ne l’avait jamais vue. Le gain spatial atteint 29,7 %, stable entre les plis.
>
> Ce résultat était séduisant, mais incomplet. En cachant aussi le temps, le gain tombe à 1,5 % et le pire pli atteint −41,4 %. J’ai retiré l’affirmation de généralisation temporelle. Cette baisse a changé le projet : au lieu d’empiler les algorithmes, j’ai commencé à demander quelle grandeur et quelle décision le modèle devait réellement servir.
>
> L’expérience contrôlée la plus claire consiste à changer seulement la cible. Apprendre directement le maximum glissant 8 h d’ozone apporte 5,8 points par rapport à une correction horaire ensuite agrégée ; l’effet est de signe opposé pour la moyenne journalière PM2,5. C’est cohérent avec Bertrand et al. : je le présente comme une réplication, pas comme une découverte.
>
> Ensuite, j’ai comparé les produits à budget de fausses alertes égal. À 30 %, CAMS brut rappelle 18,4 % des dépassements d’ozone et la correction complète 65,6 %. Le facteur 3,6 se reproduit à 3,5 sur le premier semestre 2025 avec des seuils calibrés sur 2024. Cela montre une chose précise : le modèle sait mieux ordonner les jours par risque qu’il ne sait toujours en prévoir exactement la valeur.
>
> Le périmètre reste borné. La généralisation temporelle n’est pas acquise, le NO₂ a trop peu d’événements au seuil étudié et une station exclue n’est pas une commune non mesurée. Je ne propose donc ni indice officiel ni alerte automatique. Je propose une aide à l’attention, comparée au MOS existant, avec seuil choisi par le métier et règle de repli. Les trois questions que je voudrais confronter à ATMO sont l’heure d’émission, le budget acceptable de fausses alertes et l’unité géographique de la décision. »

## Réponse à « Parlez-nous de votre projet »

Utiliser la version 60 secondes, puis s’arrêter. Ne pas remplir le silence. Laisser le jury choisir le prochain niveau de détail : usage, méthode, résultat ou limite.

## Phrase de transition vers la technique

> « Si vous le souhaitez, je peux maintenant vous montrer soit le protocole qui rend ce chiffre comparable, soit les cas où il tombe. »

Cette phrase donne au jury une permission et qualifie son intérêt, conformément aux principes de réceptivité et de qualification des notes Marketing.

## Clôture recommandée

> « Ce projet m’a appris qu’un bon correcteur n’est pas celui qui corrige toujours : c’est celui dont on connaît le comparateur, l’heure d’information, la décision servie et les conditions de repli. Les trois paramètres que je voudrais apprendre de votre pratique sont l’heure de coupure, le budget de fausses alertes et l’échelle géographique utile. »

## Formule mémorable

> **« Le modèle sait mieux ordonner ce qu’il ne sait pas encore chiffrer. »**

Elle est fidèle aux résultats : la performance prospective en valeur reste limitée, tandis que les facteurs de rappel à FAR fixé se reproduisent. Toujours la faire suivre du périmètre O₃ et du caractère non automatique.

