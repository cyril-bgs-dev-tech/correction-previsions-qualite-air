# Prompt ChatGPT R8 — 50 questions pour blinder le résultat central

**Ce qui a changé.** Le projet ne démontre plus une compétence, il porte un **constat** : le
produit officiel de post-traitement de Copernicus n'apporte que **+2,0 %** sur la grandeur
réglementaire de l'ozone, et la **dégrade** d'avril à septembre. Les questions qui suivent
servent à le vérifier, le blinder, l'étendre — ou à l'abandonner s'il ne tient pas.

L'ordre est celui du risque : ce qui pourrait **détruire** le résultat vient en premier.

À coller tel quel.

---

> Tu es chercheur en post-traitement statistique des prévisions de qualité de l'air, et tu as
> déjà relu ce projet plusieurs fois. Je te soumets un résultat nouveau. **Commence par
> essayer de le détruire** ; ne passe à son exploitation que s'il survit.
>
> ## Règles
>
> 1. Toute affirmation d'antériorité s'accompagne d'un **DOI**. Sans source : **Inconnu**.
> 2. Étiquette **[publié]** / **[jugement]**. Un jugement assumé m'est utile.
> 3. Pour toute action proposée : gain attendu, coût en heures, **test qui la tue**, critère
>    d'abandon.
> 4. Rien au-delà d'une journée de calcul. Échéance : 22 août 2026.
>
> ## Le résultat
>
> Jeu ADS `cams-europe-air-quality-forecasts-optimised-at-observation-sites` : Copernicus
> publie depuis janvier 2024 une correction par apprentissage aux stations européennes
> (observations de fond + météo ECMWF + médiane d'ensemble CAMS), au **pas horaire**. C'est
> le **seul** produit post-traité de leur catalogue — vérifié.
>
> **France, année 2024 complète, ozone :**
>
> | Grain | CAMS brut | MOS officiel | Notre modèle |
> |---|---|---|---|
> | horaire — 1 648 619 obs. | 17,30 | 14,43 (**+16,6 %**) | 13,55 (+21,7 %) |
> | **maximum journalier 8 h** — 73 108 jours-station | 12,08 | **11,85 (+2,0 %)** | **9,49 (+21,5 %)** |
>
> **Le défaut est saisonnier** : sur le max 8 h, leur MOS **dégrade** le brut d'avril à
> septembre (juin : 14,65 contre 10,23 ; juillet : 14,05 contre 11,47) et l'améliore
> d'octobre à février (novembre : 11,19 contre 18,12). Son biais sur le max 8 h estival
> atteint **−6,76 µg/m³** et son POD tombe de 0,374 à **0,122**.
>
> **Explication proposée** : corriger au pas **horaire** écrase la variabilité ; le maximum
> d'une série écrasée s'effondre. Or toutes les grandeurs réglementaires sont des **maxima**
> (max 8 h pour O₃, max horaire pour NO₂). Nous avons mesuré indépendamment qu'apprendre
> **directement** la grandeur réglementaire rapporte +5,8 points sur O₃ et +6,5 sur NO₂.
>
> **Notre dispositif** : LightGBM/XGBoost sur résidu, validation par **stations exclues**,
> 17 mois (août 2023 → décembre 2024), 476 stations, 52 variables dont 38 de paysage et 9 de
> relief. Alignement temporel vérifié (décalage 0 h optimal).
>
> **Réserves connues** : notre modèle a **vu 2024** (sur d'autres stations) ; un seul polluant
> testé ; un seul pays. Un test hors échantillon sur le 1ᵉʳ semestre 2025 est en cours.
>
> ---
>
> ## Bloc A — Ce qui pourrait détruire le résultat (Q1-Q10)
>
> **Q1.** Ce phénomène — un post-traitement horaire qui dégrade les statistiques d'ordre —
> est-il **déjà publié** ? Je connais Huang et al. 2017 (doi:10.1175/WAF-D-16-0118.1) sur la
> réduction de variabilité par correction analogique. Existe-t-il mieux, et **spécifiquement
> sur le MOS de CAMS** ?
> **Q2.** Ma comparaison est-elle **équitable** ? J'oppose leur produit horaire agrégé à mon
> produit appris sur la grandeur agrégée. Un statisticien y verrait-il un biais de
> construction ?
> **Q3.** Existe-t-il une raison **légitime** pour laquelle Copernicus optimiserait l'horaire
> plutôt que les maxima ? Quel usage cela sert-il mieux ?
> **Q4.** Leur MOS est-il **évalué publiquement** quelque part, et sur quelles métriques ?
> S'ils publient déjà leurs propres scores sur les maxima, mon résultat est-il redondant ?
> **Q5.** Mon agrégation en max 8 h est-elle conforme à la définition réglementaire — fenêtre
> glissante, attribution au jour, seuil de complétude ?
> **Q6.** Le fait que mon modèle ait **vu 2024** peut-il expliquer un écart de 2,4 µg/m³ sur
> le max 8 h ? Quelle amplitude d'optimisme est plausible ?
> **Q7.** 73 108 jours-station suffisent-ils, compte tenu de la corrélation spatiale et
> temporelle ? Quel test d'écart apparié recommandes-tu ?
> **Q8.** Mon écart pourrait-il venir d'une **différence d'échantillon** — leur MOS absent sur
> certaines stations-jours, donc comparaison sur un sous-ensemble non aléatoire ?
> **Q9.** Y a-t-il un piège dans l'échéance ? J'utilise 24-47 h chez eux ; mon « J+1 » est-il
> la même chose ?
> **Q10.** Si tu devais parier, ce résultat tient-il ou s'effondre-t-il à la vérification ?
>
> ## Bloc B — Blinder ce qui survit (Q11-Q20)
>
> **Q11.** Quel est le **test minimal** qui rendrait ce résultat incontestable, et combien
> coûte-t-il ?
> **Q12.** Faut-il refaire la comparaison sur un **pays voisin** ? Lequel, et pourquoi ?
> **Q13.** Comment isoler proprement la part due à la **cible** de celle due au **modèle** ?
> **Q14.** Quel intervalle de confiance publier sur un écart de RMSE entre deux produits
> appariés, avec dépendance spatio-temporelle ?
> **Q15.** Dois-je publier la comparaison **par mois**, ou l'agrégat annuel suffit-il ?
> **Q16.** Comment traiter les stations où leur MOS est absent — les exclure biaise-t-il ?
> **Q17.** Quelle **métrique complémentaire** au RMSE rendrait le constat plus difficile à
> contester ?
> **Q18.** Faut-il vérifier que le phénomène existe aussi sur leurs **autres échéances**
> (48-71, 72-95) ?
> **Q19.** Que faudrait-il pour transformer ce constat en **recommandation** utilisable par
> une AASQA ?
> **Q20.** Quelle est la **plus petite** expérience qui prouverait le mécanisme — que c'est
> bien l'écrasement de variabilité et non autre chose ?
>
> ## Bloc C — Étendre (Q21-Q30)
>
> **Q21.** L'effet devrait-il exister aussi sur **NO₂** (max horaire) et **PM10/PM2.5**
> (moyenne journalière) ? Prédis le sens pour chacun **avant** que je teste.
> **Q22.** Une **moyenne** journalière devrait-elle être moins affectée qu'un maximum ?
> **Q23.** Le phénomène devrait-il s'aggraver avec l'**échéance** ?
> **Q24.** Existe-t-il d'autres produits opérationnels européens ou nord-américains où le
> même défaut serait mesurable ?
> **Q25.** PREV'AIR corrige aussi par apprentissage. Sait-on à quel pas de temps ?
> **Q26.** Le défaut affecterait-il aussi les **cartes** produites après post-traitement ?
> **Q27.** Quelles autres **statistiques d'ordre** sont concernées — percentiles, nombre de
> dépassements, AOT40 ?
> **Q28.** L'AOT40 et les indicateurs de végétation seraient-ils encore plus touchés ?
> **Q29.** Y a-t-il un effet sur les **classes d'indice** publiées au public ?
> **Q30.** Quel est l'usage réglementaire où ce défaut coûterait le plus cher ?
>
> ## Bloc D — La mécanique (Q31-Q40)
>
> **Q31.** Formalise le phénomène : pourquoi `E[max(f(X))] < max(E[f(X)])` dans ce contexte ?
> **Q32.** Quelle part de l'écrasement vient de la **perte quadratique**, quelle part de la
> **cible horaire** ?
> **Q33.** Un post-traitement horaire **quantile** échapperait-il au problème ?
> **Q34.** Pourquoi l'effet s'inverse-t-il en hiver ? Est-ce le rapport biais/variance ?
> **Q35.** Le POD qui tombe de 0,374 à 0,122 est-il cohérent avec un simple écrasement, ou
> demande-t-il une autre explication ?
> **Q36.** Existe-t-il une **correction de variance** applicable a posteriori à leur produit,
> sans réapprentissage ?
> **Q37.** L'inflation de variance (type *variance inflation* en downscaling) est-elle la
> réponse standard ? Gains publiés ?
> **Q38.** Peut-on **prédire** l'ampleur de l'écrasement à partir des propriétés du signal ?
> **Q39.** Y a-t-il un lien avec la calibration des prévisions probabilistes ?
> **Q40.** Comment un météorologue nommerait-il ce problème ?
>
> ## Bloc E — Valoriser (Q41-Q50)
>
> **Q41.** Ce résultat a-t-il une valeur **publiable** ? Sous quelle forme et où ?
> **Q42.** Faut-il le **signaler à Copernicus** ? Par quel canal, et avec quelles précautions ?
> **Q43.** Quel est le risque de se tromper publiquement contre un organisme européen ?
> **Q44.** Comment formuler le constat **sans accuser** — descriptif plutôt qu'accusatoire ?
> **Q45.** Quelle est la formulation d'une phrase qui résiste à un relecteur hostile ?
> **Q46.** Que répondre à « ils ont sûrement de bonnes raisons » ?
> **Q47.** Ce résultat change-t-il ce qu'il faut mettre en **première page** du dossier ?
> **Q48.** Faut-il en faire l'axe principal, ou le garder comme argument de second rang ?
> **Q49.** Quel serait le **contre-argument le plus fort** qu'on m'opposera ?
> **Q50.** Si ce résultat tient, qu'est-ce qui devient la **prochaine question** à traiter ?
>
> **Format.** Une réponse par question, sources ensuite. Termine par : *le résultat survit /
> est affaibli / est faux*, et par les points classés **Inconnu**.
