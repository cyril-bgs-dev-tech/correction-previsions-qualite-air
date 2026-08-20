# Pitches et accroches

> **Mis à jour le 20/08/2026.** La version du 31/07 s'arrêtait à la configuration de base et
> annonçait « le gain tombe à 1,5 % » comme mot de la fin. C'était vrai de la pile d'alors,
> et faux du projet : les leviers trouvés depuis ramènent ce même protocole — le plus dur —
> à **+17,9 % sur l'ozone et +39,6 % sur le NO₂**. Un pitch qui s'arrête au creux se dessert
> d'un facteur douze. Tous les chiffres viennent de `reports/VERITE_DOSSIER.md`.

## Accroches à tester

### Recommandée — paradoxe de décision

> « Un modèle peut gagner près de 30 % en erreur moyenne et continuer à manquer le jour sur lequel il faudrait agir. C'est ce paradoxe qui a déplacé tout mon projet. »

### Variante — budget opérationnel

> « La question n'est pas seulement : quel modèle a la meilleure RMSE ? C'est : avec le même nombre de fausses alertes, lequel retrouve le plus de dépassements ? »

### Variante — rigueur

> « Le résultat dont je suis le plus fier n'est pas le meilleur score. C'est une affirmation que j'ai retirée quand le test station × temps l'a réfutée. »

### Variante — grain réglementaire

> « J'ai changé davantage la performance en changeant la cible qu'en changeant d'algorithme : apprendre le maximum qui décide vaut plus que corriger vingt-quatre heures puis prendre leur maximum. »

### Variante — usage réglementaire · nouvelle, et c'est celle qui parle à une AASQA

> « La directive de 2024 divise les seuils par deux en 2030 et rend la modélisation obligatoire là où ils sont dépassés. Or le produit européen brut ne passe le critère de qualité européen que sur 41 % des stations de NO₂. C'est le problème que je traite. »

## Accroches à ne pas utiliser

- « J'ai battu CAMS/Copernicus de 30 %. »
- « Mon IA détecte 3,6 fois plus d'épisodes. »
- « J'ai développé un modèle révolutionnaire pour ATMO Occitanie. »
- « Grâce à 53 variables et LightGBM… »

Elles surpromettent, déclenchent immédiatement une bataille de périmètre et forcent le jury à chercher la faille avant d'avoir compris la décision.

## Pitch 20 secondes

> « J'ai construit une correction des prévisions européennes de qualité de l'air, évaluée sur des stations **et** des mois que le modèle n'a jamais vus — la condition d'un déploiement réel. Dans cette condition, l'erreur baisse de 17 % sur l'ozone et de 39 % sur le NO₂. Et le produit européen brut, qui ne satisfait le critère de qualité européen que sur 41 % des stations de NO₂, y passe à 96 %. »

## Pitch 60 secondes

> « Mon projet part d'une correction apprise des prévisions CAMS aux stations. Le premier résultat était séduisant : sur des stations jamais vues, le gain atteint 29,7 %. Mais quand je cache **aussi** le mois — une station nouvelle **et** une date future, ce qu'un déploiement demande vraiment — la première version tombait à 1,5 %, avec des plis négatifs. J'ai retiré l'affirmation, et cette chute a redéfini le projet.
>
> Il a fallu trouver ce qui manquait. Sept traceurs de composition du champ CAMS, que le dépôt ne téléchargeait pas, apportent de 1,5 à 6 % selon le polluant, avec un intervalle qui exclut zéro sur les quatre. Aujourd'hui, dans cette même condition double aveugle, la méthode complète rend **+17,9 % sur l'ozone et +39,6 % sur le NO₂**.
>
> Et le point qui compte pour une AASQA : à J+1, le produit européen brut ne satisfait le critère de qualité FAIRMODE que sur 41,4 % des stations de NO₂ — moins bien qu'une simple répétition de la mesure d'avant-veille. Après correction, 96,2 %. »

## Pitch 3 minutes

> « Au départ, je cherchais simplement à savoir si une correction apprise pouvait améliorer CAMS aux stations. J'ai entraîné un modèle de résidu avec des sorties CAMS, le calendrier, le paysage, le relief et le trafic, puis évalué chaque station avec un modèle qui ne l'avait jamais vue. Le gain spatial atteint 29,7 %, stable entre les plis.
>
> Ce résultat était séduisant, mais incomplet. En cachant aussi le temps, il tombait à 1,5 % et le pire pli atteignait −41,4 %. J'ai retiré l'affirmation de généralisation temporelle. Cette baisse a changé le projet : au lieu d'empiler les algorithmes, j'ai cherché quelle **information** manquait.
>
> Le levier décisif est arrivé tard : sept traceurs de composition du champ CAMS — nitrate, sulfate, ammonium, carbone — que le dépôt ne téléchargeait pas. Ils apportent de 1,5 % sur le NO₂ à 6 % sur les PM10, avec un intervalle de confiance qui exclut zéro sur les quatre polluants, après correction de Holm et sous deux longueurs de blocs.
>
> Et j'ai voulu savoir **pourquoi** ça marchait, parce qu'un gain dont on ignore le mécanisme n'est pas un résultat, c'est une coïncidence en attente. J'ai permuté la composition à l'intérieur de chaque couple station-mois : ça conserve exactement l'histogramme par site et par saison, et ça ne détruit que l'appariement au jour. Le gain disparaît en totalité, sur les quatre polluants. Ce n'est donc ni un encodeur de site ni un proxy de saison : le modèle exploite l'écart du jour à la composition habituelle du lieu.
>
> Aujourd'hui, en double aveugle — station et mois cachés ensemble — la méthode complète rend +17,9 % sur l'ozone et +39,6 % sur le NO₂.
>
> Reste la question de l'usage. La directive européenne de 2024 divise les valeurs limites annuelles par deux en 2030 et rend la modélisation obligatoire là où un seuil est dépassé. Sur le parc réel, à pollution inchangée, les stations en dépassement passent de 6 à 109. En Occitanie, quatre départements sur treize n'ont aucune station pour le constater — exactement le cas que la directive confie à la modélisation. Et là où le modèle devient opposable, sa qualité devient un point de contrôle : à J+1, le produit européen brut ne satisfait le critère FAIRMODE que sur 41,4 % des stations de NO₂ ; la correction l'y porte à 96,2 %.
>
> Le périmètre reste borné, et je le publie au même titre. Sans aucune observation du point, le NO₂ plafonne à 87,9 % — sous la barre des 90 % qu'exige le critère. Sur les épisodes réellement déclenchés par les préfectures, je n'en retrouve que 3 sur 33 — même si l'observation directe n'en attrape que 21 et le produit officiel 1, ce qui dit surtout que la décision préfectorale intègre des critères que la concentration ne contient pas. Une station exclue n'est pas une commune non mesurée. Je ne propose donc ni indice officiel ni alerte automatique : une aide à l'attention, avec seuil choisi par le métier et règle de repli. »

## Le duel, si on vous demande « et contre l'existant ? »

> « Contre le produit réellement diffusé — l'archive de PREV'AIR porte dans sa métadonnée qu'il s'agit de CHIMERE combiné aux observations, c'est-à-dire leur adaptation statistique AS-CHI — sur les mêmes stations et les mêmes jours : de +13,7 % sur l'ozone à +66,9 % sur les PM2,5.
>
> Mais je dois dire tout de suite la réserve : **dix-sept jours seulement**. Leur archive n'expose que six jours glissants et ne peut pas remonter le temps ; je l'ai constituée jour après jour. C'est un ordre de grandeur, pas une conclusion. »

## Réponse à « Parlez-nous de votre projet »

Utiliser la version 60 secondes, puis s'arrêter. Ne pas remplir le silence. Laisser le jury choisir le prochain niveau de détail : usage, méthode, résultat ou limite.

## Phrase de transition vers la technique

> « Si vous le souhaitez, je peux maintenant vous montrer soit le protocole qui rend ce chiffre comparable, soit les cas où il tombe. »

Cette phrase donne au jury une permission et qualifie son intérêt.

## Clôture recommandée

> « Ce projet m'a appris qu'un bon correcteur n'est pas celui qui corrige toujours : c'est celui dont on connaît le comparateur, l'heure d'information, la décision servie et les conditions de repli. Les trois paramètres que je voudrais apprendre de votre pratique sont l'heure de coupure, le budget de fausses alertes et l'échelle géographique utile. »

## Formule mémorable

> **« Le modèle sait mieux ordonner ce qu'il ne sait pas encore chiffrer. »**

Fidèle aux résultats : les facteurs de rappel à budget de fausses alertes fixé se reproduisent hors fenêtre, tandis que la détection des épisodes réellement déclenchés reste faible. Toujours la faire suivre du périmètre et du caractère non automatique.

## La seconde formule, pour le volet rigueur

> **« Une affirmation de ce dossier a été réfutée par sa propre mesure, et elle est publiée. »**

Le dossier affirmait que ses leviers ne se dégradent pas avec l'échéance. Poussé jusqu'à J+3, c'est vrai sur le NO₂ — 0,38 point d'écart de J0 à J+3 — et **faux sur l'ozone**, qui perd 2,25 points. L'affirmation était juste sur son mécanisme et trop large dans sa portée. C'est l'anecdote qui démontre le protocole mieux que n'importe quel score.
