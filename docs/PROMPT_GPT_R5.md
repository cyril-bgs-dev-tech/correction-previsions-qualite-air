# Prompt ChatGPT R5 — extraire le maximum des tests déjà réalisés

**L'intention.** Ne pas lui faire produire une revue de littérature générique : lui donner
**la table complète de nos mesures fraîches** (recalcul 17 mois du 30/07) et lui demander
ce qu'on peut légitimement en tirer. Trois livrables attendus, dans cet ordre de valeur :

1. quelles **affirmations** ces mesures autorisent — et lesquelles elles n'autorisent pas ;
2. pour chaque résultat, le **petit complément** qui le ferait passer d'« intéressant » à
   « démontré » — nous avons un jour, pas trois semaines ;
3. le **situer dans la littérature**, pour savoir si nos gains sont normaux ou suspects.

Ce cadrage exploite le fait que nous avons maintenant huit expériences chiffrées : la
valeur marginale d'une mesure de plus est faible, celle d'une bonne lecture est élevée.

À coller tel quel.

---

> Tu es chercheur en post-traitement statistique des prévisions de qualité de l'air, et tu
> as l'habitude de relire des travaux avant soumission. Je te donne **les résultats réels**
> d'un projet et je veux que tu m'aides à en **extraire le maximum**, pas à en produire de
> nouveaux : il me reste un jour de calcul, pas trois semaines.
>
> **Règles de réponse, strictes.**
> 1. Tout chiffre de comparaison que tu cites vient d'une **publication identifiable**
>    (auteurs, année, revue, DOI) avec polluant, horizon, métrique et domaine géographique.
>    Sans ces quatre éléments, un gain de RMSE n'est pas comparable au mien.
> 2. Faute de source, écris **Inconnu**. Une valeur inventée me ferait annoncer une
>    comparaison fausse en entretien — pire que le silence.
> 3. Quand tu cites la littérature, distingue les gains mesurés **sur stations vues** à
>    l'entraînement de ceux mesurés **sur stations exclues**. Les miens sont tous sur
>    stations exclues.
> 4. Ne me propose aucune expérience qui demande plus de **quelques heures** de calcul.
>
> ## Le dispositif
>
> Correction apprise (LightGBM) des prévisions **CAMS Europe** (0,1°, ~8 km, J+1 à J+3)
> **aux stations de mesure**. France entière à l'entraînement, 476 stations, **17 mois**
> d'observations horaires appariées (août 2023 → décembre 2024). Validation par plis de
> **stations entièrement exclues** ; intervalles de confiance bootstrapés **par station**
> (jamais par ligne — la pseudo-réplication élargit d'un facteur 23). Variables : sorties
> CAMS, météo ERA5, calendrier, 38 descripteurs de paysage, 9 de relief, trafic hiérarchisé
> (BD TOPO), population communale. **Aucune observation récente de la station n'est utilisée
> comme prédicteur.**
>
> ## Les mesures — RMSE en µg/m³, J+1, sur stations exclues
>
> **A. Performance générale**
>
> | | CAMS brut | corrigé | gain |
> |---|---|---|---|
> | O₃ (3,23 M paires, 270 stations) | 16,97 | 13,69 | **+19,3 %** |
> | NO₂ (3,99 M paires, 343 stations) | 12,87 | 9,05 | **+29,7 %** |
>
> La dégradation de CAMS de J+1 à J+3 est faible (NO₂ 12,87 → 13,09 ; O₃ 16,97 → 17,84).
>
> **B. Contre des baselines, sur échantillon strictement commun** (3,19 M couples
> identiques, O₃) : persistance 21,07 · climatologie horaire 19,65 · CAMS brut 16,97 ·
> corrigé 13,71. Biais : persistance +0,06 · CAMS +6,01 · corrigé −0,06.
>
> **C. Ablation par famille de variables** (O₃, perte de RMSE quand on retire la famille) :
> calendrier **+9,1 %** · relief +2,9 % · routes +0,6 % · coordonnées +0,6 % ·
> forêt **−1,0 %** · échéance **−0,5 %** (les deux dernières *améliorent* si on les retire).
>
> **D. Covariables de terrain contre interpolation spatiale du résidu** (O₃) :
> CAMS 16,97 · + résidu interpolé seul 15,85 (+6,6 %) · + apprentissage sans terrain 14,67
> (+13,6 %) · + apprentissage avec terrain **13,69** (+19,4 %) · **+ terrain et résidu
> interpolé 14,20** (+16,4 %) — empiler les deux fait **moins bien** que le terrain seul.
>
> **E. Hiérarchie routière** (NO₂) : sans aucune route 10,79 · routes pondérées par la
> longueur 10,41 · **trafic hiérarchisé 9,05** · + population 9,01. La hiérarchie vaut
> **+13,0 %** contre la longueur seule, IC95 [+10,4 ; +15,5], 100 % de tirages positifs.
> La population n'ajoute rien de mesurable.
>
> **F. Les extrêmes — mon point faible.** Décile supérieur d'ozone (> 85,6 µg/m³) :
> CAMS 15,18 · correction par **erreur quadratique 15,65** (soit **−3,1 %**, pire que le
> brut) · quantile pinball q=0,90 : 11,85 (+21,9 % sur la queue, mais RMSE global 20,90,
> pire que CAMS) · **quadratique pondérée par la concentration : 13,89** (+8,5 % sur la
> queue, pour un RMSE global de 14,86, encore +12,4 % contre CAMS).
>
> **G. Par régime météo** (O₃, gains) : stagnation **+25,7 %** · photochimique +17,7 % ·
> ventilé +14,7 % · précipitations +9,2 %. **Mais croisé avec le décile supérieur, les
> gains s'effondrent** : photochimique +1,2 %, précipitations −4,8 %, stagnation −6,7 %,
> ventilé −8,8 %.
>
> **H. Service rendu.** La correction améliore 57,9 % des heures mais seulement 16,2 %
> changent de classe d'indice. Rappel des jours « Mauvais » : 0,24 (brut) → 0,47 (corrigé),
> précision 0,47 → 0,79.
>
> ## Les six questions
>
> **1. Ce que ces mesures autorisent à dire — et ce qu'elles ne permettent pas.** Passe en
> revue A à H et sépare : (i) les affirmations solides, formulées comme je devrais les
> énoncer ; (ii) celles que je risque de surinterpréter, avec la formulation prudente qui
> les remplace. Traite en particulier **D** (empiler interpolation et terrain dégrade) et
> **C** (retirer la forêt améliore) : ai-je le droit d'en conclure quelque chose, ou est-ce
> du bruit ?
>
> **2. Le complément court qui décuple un résultat existant.** Pour les trois mesures que
> tu juges les plus fortes, dis quel **test de quelques heures** les ferait passer
> d'« intéressant » à « démontré ». Exemples du genre attendu : un témoin manquant, une
> ventilation supplémentaire, un test de significativité. Sois précis sur le protocole.
>
> **3. Le témoin que je n'ai pas et qui me sera reproché.** Je n'ai **jamais mesuré une
> correction sans apprentissage** — par exemple retrancher à CAMS le biais moyen par station
> (ou par station × mois) estimé sur la période d'entraînement seule. Si ce témoin capture
> l'essentiel du gain, mon apport en apprentissage est faible. Comment le construire
> proprement (quelle granularité, quel risque de fuite), et à quel niveau de performance
> devrais-je m'attendre d'après la littérature ?
>
> **4. Les observations récentes de la station.** Je ne les utilise pas, alors que la
> persistance seule atteint 21,07 de RMSE — l'information existe. En post-traitement
> opérationnel, quel gain la littérature attribue-t-elle à la dernière mesure disponible à
> l'émission ? Et quelles précautions : que devient la généralisation à une station **non
> instrumentée**, et que se passe-t-il si le flux temps réel tombe (c'est arrivé en France,
> l'ozone EEA est rompu depuis le 01/07/2025) ?
>
> **5. L'écrasement des extrêmes (F et G).** Ce phénomène est-il **nommé** dans la
> littérature, et quelles solutions sont publiées **avec leurs gains** — pertes
> asymétriques, modèles à deux régimes, régression quantile, apprentissage sur les seuls
> dépassements, mélange d'experts ? Ma perte pondérée est-elle l'état de l'art ou une
> approximation grossière ?
>
> **6. Situer.** Mes +19,3 % (O₃) et +29,7 % (NO₂) sur stations exclues sont-ils bas,
> normaux, ou assez hauts pour que je doive me méfier d'une fuite ? Et où me situent mes
> POD/FAR par rapport à ce qui est publié et à ce qu'une AASQA obtient réellement ?
>
> **Termine par deux listes courtes.** D'abord les **trois choses à faire en priorité** avec
> un jour de calcul, classées par valeur ajoutée rapportée à l'effort. Ensuite les points
> classés **Inconnu**.
>
> **Format.** Une section par question, réponse d'abord, sources ensuite. Pas
> d'introduction, pas de résumé de mes propres résultats.
