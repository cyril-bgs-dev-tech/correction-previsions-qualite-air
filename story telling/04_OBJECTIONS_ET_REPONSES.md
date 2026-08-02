# Objections et réponses

Les réponses ci-dessous suivent une structure constante : **oui / preuve / limite / décision**. Ne jamais commencer par se défendre longuement.

## 1. « PREV’AIR et CAMS ont déjà un MOS. Qu’avez-vous apporté ? »

> « Oui, la correction statistique existe déjà et je ne la revendique pas. Mon apport de candidature est d’avoir mesuré le produit distribué au grain réglementaire, ajouté un benchmark MOS sur les mêmes stations et dates, puis évalué la décision à budget de fausses alertes égal. L’expérience sur la cible réplique Bertrand et al. ; ce qui m’intéresse est la caractérisation opérationnelle et les limites. »

## 2. « Vous comparez-vous vraiment à armes égales au MOS officiel ? »

> « Pas dans toutes les expériences. Le MOS officiel utilise des observations récentes ; mon modèle initial non. J’ai donc séparé deux usages : correction aux stations avec observations J−2, et transfert vers une station sans historique. La comparaison ne devient équitable que lorsque l’usage et les entrées sont identiques. »

## 3. « 29,7 %, c’est une fuite par station ? »

> « Les stations de test sont entièrement exclues de l’apprentissage et de la sélection du modèle dans le pli. En revanche, elles appartiennent au même réseau national et partagent des régimes avec les stations d’entraînement : je parle donc de transfert vers une autre station du réseau, pas vers n’importe quel lieu. »

## 4. « Votre généralisation temporelle échoue. Pourquoi présenter le modèle ? »

> « Parce que cette différence entre transfert spatial et temporel est précisément utile. Le double aveugle tombe à +1,5 % et contient huit plis négatifs ; cela interdit une promesse de correction stable sans suivi. En revanche, le classement des jours à risque conserve des facteurs proches hors fenêtre. Le produit doit donc être surveillé et réétalonné, pas déployé comme une fonction figée. »

## 5. « Le facteur 3,6 est-il choisi au meilleur seuil pour votre modèle ? »

> « Non. Je fixe d’abord un budget de fausses alertes et les seuils sont choisis hors des stations évaluées. À 30 % maximum, le rappel passe de 0,184 pour CAMS à 0,656 pour la correction complète. Le facteur n’a de sens qu’avec ce budget et pour l’ozone. »

## 6. « Pourquoi ne pas annoncer simplement POD, FAR et CSI ? »

> « Je les annonce, mais un seuil propre à chaque produit peut rendre la comparaison arbitraire. La courbe rappel–FAR montre ce que chaque produit fournit sous la même contrainte opérationnelle. Le CSI reste un résumé, pas la politique de décision. »

## 7. « Votre amélioration 2025 face au MOS est-elle démontrée ? »

> « Une seule différence l’est : la RMSE est inférieure de 3,22 µg/m³, IC95 de −4,87 à −1,74, robuste aux blocs de 3, 7 et 14 jours. Les écarts de CSI et de POD ne sont pas conclusifs sur 21 stations et environ 160 dépassements ; je les présente comme estimations ponctuelles. »

## 8. « Pourquoi le NO₂ ne marche-t-il pas ? »

> « Au seuil étudié, il n’y a que 270 dépassements sur 161 637 jours-station, dix fois moins proportionnellement que pour O₃ ou PM2,5. Aucun budget de fausses alertes inférieur à 40 % n’est atteignable. Une maille de 8 km ne résout en plus pas les pics de proximité. Je n’en fais pas un service de détection NO₂. »

## 9. « Utilisez-vous ERA5, donc une information future ? »

> « Pas dans le modèle de référence : ses 53 prédicteurs sont disponibles à l’émission. ERA5 est une expérience séparée qui mesure un plafond, +7,8 % sur O₃, et ne doit pas être présenté comme déployable. L’étape opérationnelle consiste à refaire strictement le test avec les prévisions IFS/AIFS archivées. »

## 10. « Pourquoi LightGBM ? »

> « Parce qu’il capture des interactions non linéaires avec un coût faible et une bonne stabilité. Mais ce n’est pas le résultat : LightGBM, XGBoost et CatBoost restent dans 0,3 point. Le choix de la cible et du protocole pèse bien davantage que celui de la bibliothèque. »

## 11. « Les covariables de paysage corrigent-elles la chimie ou le support station–maille ? »

> « Je ne peux pas attribuer tout le gain à la chimie. Deux stations dans la même maille partagent exactement CAMS mais pas leur micro-environnement ; une partie de la correction traite donc le changement de support. C’est pourquoi je retire le mot “plancher” pour les 3,61 µg/m³ et propose une décomposition erreur CTM / représentativité / bruit. »

## 12. « Pourquoi ne pas produire directement une carte communale ? »

> « Parce que la validation par stations exclues n’établit pas la validité hors du support du réseau. Avant une carte, il faut mesurer la distance de covariables hors réseau, cacher des régions entières et vérifier la cohérence spatiale. Le projet actuel prédit aux stations ; il ne calcule pas l’indice officiel. »

## 13. « Votre seuil de 120 µg/m³ est-il un seuil réglementaire d’épisode ? »

> « Je l’utilise comme seuil d’information pour la grandeur O₃ étudiée et je dois nommer exactement le texte et l’usage lorsque je le présente. Le projet ne reproduit pas à lui seul la procédure zonale, la population exposée ni la décision préfectorale. »

## 14. « Qu’est-ce qui vous ferait abandonner la piste météo ? »

> « Si IFS/AIFS, disponibles à l’émission, ne récupèrent pas un gain relatif préspécifié avec une borne d’intervalle positive, et n’améliorent ni queue ni classement à FAR fixé. ERA5 ne vaut que comme plafond ; il ne peut pas sauver une piste opérationnelle qui échoue avec la prévision. »

## 15. « Qu’auriez-vous fait différemment dès le début ? »

> « J’aurais écrit avant le premier modèle une fiche d’usage : utilisateur, heure de coupure, unité spatiale, comparateurs et budget de fausses alertes. Cela aurait évité d’exclure par analogie les observations J−2, de sélectionner trop longtemps sur le RMSE et de confondre transfert spatial et service opérationnel. »

## 16. « N’avez-vous pas multiplié les essais jusqu’à trouver un résultat ? »

> « Le risque existe. Je sépare donc exploratoire et confirmatoire, conserve les résultats négatifs et impose désormais une hiérarchie : critère primaire, validation temporelle gelée, stations exclues et seuils choisis hors test. Les chiffres déjà explorés ne deviennent pas rétroactivement pré-enregistrés. »

## 17. « Quand le système doit-il s’abstenir ? »

> « Aujourd’hui, je sais montrer des périodes où il perd, mais je n’ai pas encore validé un indicateur ex ante qui annonce ces pertes. La dispersion des membres CAMS est une piste, pas une règle acquise. En attendant, le repli doit être le produit de référence dès qu’une entrée manque, qu’une dérive est détectée a posteriori ou que le cas sort du domaine des données. »

## 18. « Quelle est votre contribution personnelle la plus convaincante ? »

> « Avoir changé la question quand les tests l’exigeaient : du gain moyen vers la décision à FAR fixé, puis avoir borné le résultat par le double aveugle et le benchmark officiel. Le code prouve que je sais construire ; les affirmations retirées montrent comment je travaille quand le résultat résiste. »

## Questions à poser au jury

Ces questions ne sont pas décoratives : leurs réponses changent la conception.

1. « À quelle heure et à quel grain géographique une information devient-elle encore actionnable pour vos prévisionnistes ? »
2. « Sur l’ozone, comment arbitrez-vous concrètement un épisode manqué contre une fausse alerte ? »
3. « Quel produit sert aujourd’hui de repli lorsqu’un membre, une observation ou une chaîne locale manque ? »
4. « Dans votre bilan, quelle métrique déclenche réellement une remise en cause de la chaîne ? »
5. « Préféreriez-vous que je poursuive ce prototype sur les observations récentes, la météo prévue ou l’analyse des jours où les modèles divergent ? »

