# Prompt Grok 4.5 R5 — 50 verdicts courts

**Pourquoi ce format-là.** Sa session ne tient pas longtemps : on ne lui demande donc pas
d'analyse longue (c'est le rôle de `PROMPT_GPT_R6.md`, 30 questions à quatre colonnes) mais
**cinquante verdicts d'une à trois lignes**. Les questions sont rangées par valeur
décroissante et regroupées par bloc, pour qu'une réponse tronquée reste exploitable.

On lui dit aussi que sa recommandation de la ronde 4 reposait sur une prémisse fausse —
c'est la condition pour qu'il se corrige au lieu de la répéter.

À coller tel quel.

---

> Tu m'as déjà relu trois fois. **Ne répète rien de général.** Réponds en français, **une à
> trois lignes par question**, verdict d'abord. Les blocs sont classés par valeur : si tu
> dois t'arrêter, arrête-toi à la fin d'un bloc plutôt qu'en survolant tout.
>
> Étiquette chaque réponse **[vu]** (tu l'as vérifié dans cette session), **[publié]** (tu
> peux citer une source) ou **[jugement]** (ton avis de praticien). Un jugement assumé m'est
> utile, un jugement déguisé en fait me coûte cher.
>
> **Correction de ta ronde précédente, à intégrer.** Tu recommandais « train 2023-2024, test
> 2025 calendaire, ~6-8 mois de test ». C'était **infaisable** : mes observations s'arrêtent
> au **31/12/2024** — il n'y a aucune mesure en 2025, seulement des prévisions. Le mois
> 2025-01 que mon compteur affichait contenait **894 lignes** contre 665 000 pour un mois
> plein. Ma couverture réelle est de **17 mois**, août 2023 → décembre 2024.
>
> ## Ce que je sais maintenant (tout est mesuré sur stations exclues, O₃ à J+1, 3,23 M de paires)
>
> **Échelle des approches** — CAMS brut 16,97 · débiaisage sans apprentissage +7,3 % ·
> Ridge +8,9 % · forêt aléatoire +14,9 % · XGBoost et CatBoost ≈ +12 % ·
> **LightGBM +19,4 %** (RMSE 13,68). NO₂ : +29,7 %, dont **+13,0 %** dus à la seule
> hiérarchisation du trafic ; la population n'apporte rien.
>
> **Généralisation** — spatiale **+19,4 %** avec σ 1,2 (solide, et renforcée) ; temporelle
> +14,4 % mais pire pli **−14,6 %** ; double aveugle +8,7 % mais pire pli **−24,9 %**.
> Le 29/07, sur 7 mois, j'avais conclu « généralisation temporelle démontrée, aucun pli
> négatif » — c'était faux : je n'avais pas testé assez de mois.
>
> **Extrêmes** — sur le décile supérieur d'ozone, ma correction est **pire que CAMS brut de
> 3,1 %**. Une perte pondérée rend +8,5 % sur la queue en cédant 7 points de gain global. Le
> gain sur la queue est négatif dans presque tous les régimes météo (−8,8 % en ventilé,
> −6,7 % en stagnation) alors qu'il est de +14 à +26 % sur l'ensemble de la distribution.
>
> **Service rendu (POD / FAR / CSI)** — PM2.5 : POD 0,198 → **0,372** et FAR 0,734 →
> **0,277**, le seul polluant où les deux progressent. O₃ : POD 0,360 → 0,345 (baisse) mais
> FAR 0,362 → 0,203. NO₂ : POD 0,007 → 0,015, indétectable avant comme après. La correction
> améliore 57,9 % des heures mais seulement **16,2 %** changent de classe d'indice.
>
> **Ablation** — calendrier +9,1 % (la plus utile), relief +2,9 %, routes +0,6 %, et retirer
> la forêt ou l'échéance *améliore* légèrement. Les covariables de terrain battent une
> interpolation du résidu (13,69 contre 15,85), mais **empiler les deux dégrade** (14,20).
>
> **Littérature** — Riccio & Chianese 2024, stations exclues : O₃ +29,9 %. Bertrand et al.
> 2023, stations vues : O₃ +29 %. Chez les premiers, le gain chute de 24 à 36 points entre
> stations vues et exclues. Mon +19,3 % reste donc plutôt bas.
>
> **Contraintes** — aucune observation 2025 · ozone temps réel EEA rompu en France depuis le
> 01/07/2025 · deux ruptures CAMS documentées (13/11 et 03/12/2024), exactement là où mon
> gain explose (+30 à +34 % contre +14 à +22 % un an plus tôt à saison égale) · GPU RTX 5090
> disponible · échéance de candidature **22 août 2026**.
>
> ---
>
> ## Bloc 1 — Verdicts sur ce que j'ai le droit d'affirmer (Q1-Q10)
>
> 1. « La correction améliore une chaîne opérationnelle de même nature que celle d'ATMO » —
>    défendable en entretien, oui ou non ?
> 2. Mon gain O₃ de +19,4 % sur stations exclues : bas, normal, ou suspect ?
> 3. Ai-je le droit de dire que la généralisation **spatiale** est démontrée avec seulement
>    **3 plis** ?
> 4. Puis-je annoncer un gain moyen temporel de +14,4 % **tout en** ayant un pli à −14,6 %,
>    ou ces deux chiffres s'annulent-ils devant un ingénieur ?
> 5. Le fait que ma correction soit **pire que CAMS sur le décile supérieur** disqualifie-t-il
>    le travail, ou est-ce présentable comme un compromis assumé ?
> 6. « Le trafic hiérarchisé vaut +13,0 % » : est-ce mon résultat le plus fort, ou en ai-je
>    un meilleur que je sous-estime ?
> 7. Le fait qu'un simple débiaisage atteigne +7,3 % dévalorise-t-il mon +19,4 %, ou le
>    crédibilise-t-il ?
> 8. Mon POD d'ozone qui **baisse** avec la correction : à cacher, à assumer, ou à mettre en
>    avant comme preuve d'honnêteté ?
> 9. Que **PM2.5** soit le seul polluant où la détection progresse : dois-je recentrer le
>    récit sur PM2.5 ?
> 10. Si tu devais retirer **une seule** affirmation de mon dossier parce qu'elle est
>     indéfendable, laquelle ?
>
> ## Bloc 2 — Mes angles morts (Q11-Q20)
>
> 11. Quelle erreur suis-je probablement en train de commettre **en ce moment** sans la voir ?
> 12. Une part de mon gain vient peut-être de la **dégradation de CAMS** fin 2024. Si c'est
>     vrai, qu'est-ce que ça détruit exactement dans mon dossier ?
> 13. Comment le mesurer en une heure ?
> 14. J'ai fait de nombreux choix en regardant des résultats de validation. Combien de points
>     de RMSE d'**optimisme** cela représente-t-il, à vue de praticien ?
> 15. Le **calendrier** est ma variable la plus utile. Bon signe ou mauvais signe ?
> 16. « Empiler interpolation et terrain dégrade » : résultat réel ou artefact ?
> 17. Retirer la forêt *améliore* de 1,0 %. Bruit, ou variables nuisibles ?
> 18. Mon écrêtage des prédictions à zéro crée-t-il un biais que je n'ai pas mesuré ?
> 19. Mes intervalles bootstrapés **par station** sont-ils suffisants, ou faut-il aussi
>     bloquer le temps ?
> 20. Qu'est-ce qu'un jury regarderait dans mon code avant de regarder mes chiffres ?
>
> ## Bloc 3 — Performance : où sont les points restants (Q21-Q30)
>
> 21. Les **observations récentes** de la station : combien de points de RMSE, à vue ?
> 22. Cet ajout change-t-il ma promesse au point de nuire au dossier ?
> 23. Le **tuning d'hyperparamètres** que je n'ai jamais fait : 1 %, 5 %, ou 15 % ?
> 24. Quels **deux** hyperparamètres de gradient boosting portent l'essentiel du gain ?
> 25. La **dispersion d'ensemble** de CAMS comme prédicteur de l'erreur : utile ?
> 26. Les **copolluants** CAMS comme prédicteurs de l'ozone : utile, ou circulaire ?
> 27. Transformer la cible (log, racine, quantiles) pour l'asymétrie : réel ou cosmétique ?
> 28. Un modèle **par régime météo** plutôt qu'un modèle global : payant ?
> 29. Étant donné que XGBoost, CatBoost et LightGBM tiennent en 0,3 point, **continuer à
>     comparer des architectures est-il un bon emploi de mon temps** ?
> 30. Si je n'ai qu'**une journée de calcul**, sur quoi la dépenses-tu ?
>
> ## Bloc 4 — Les extrêmes, qui décident du service (Q31-Q37)
>
> 31. Mon échec sur la queue vient-il de la **perte**, de la **cible résiduelle**, du
>     **déséquilibre**, ou de l'**écrêtage** ?
> 32. Prédire directement une **probabilité de dépassement** plutôt que seuiller une
>     concentration : gain réel ?
> 33. Existe-t-il une formulation qui **domine** mon compromis global/queue au lieu de s'y
>     déplacer ?
> 34. Pour une AASQA, une alerte manquée coûte combien de fausses alertes ?
> 35. Mon CSI de 0,317 sur le max 8 h à 120 µg/m³ : bon, moyen, mauvais ?
> 36. Un rappel de 0,47 sur les jours « Mauvais » peut-il être présenté sans être démonté ?
> 37. Pourquoi PM2.5 marche-t-il et pas O₃ ? Une phrase de mécanisme.
>
> ## Bloc 5 — Le récit et l'entretien (Q38-Q44)
>
> 38. Quelle est **la** phrase d'ouverture de ma candidature ?
> 39. Quelles **trois** questions techniques vais-je recevoir, auxquelles je n'ai pas de
>     réponse prête ?
> 40. Comment présenter un résultat **négatif** (queue, POD, généralisation temporelle) pour
>     qu'il serve au lieu de nuire ?
> 41. Faut-il montrer l'échelle complète (débiaisage +7,3 % → LightGBM +19,4 %) au risque de
>     relativiser mon travail, ou est-ce précisément ce qui le crédibilise ?
> 42. Dois-je parler de FAIRMODE et du MQI, ou est-ce un terrain où je me ferai reprendre ?
> 43. Quel est le plus grand risque de mon dossier : trop technique, pas assez opérationnel,
>     ou trop honnête ?
> 44. À la place du recruteur, quelle serait ma **première** question ?
>
> ## Bloc 6 — Actualité, ta force propre (Q45-Q48)
>
> 45. Épisodes de pollution en Occitanie en **juillet 2026** — lesquels, et lesquels furent
>     mal anticipés ? Distingue nettement **[vu]** de **[jugement]**.
> 46. Actualité ATMO Occitanie ou LCSQA de juillet 2026 que je devrais connaître ?
> 47. Un changement récent de CAMS, PREV'AIR ou CHIMERE que j'ignorerais ?
> 48. Une publication de moins de six mois sur le post-traitement ML de la qualité de l'air
>     qui changerait mon cadrage ?
>
> ## Bloc 7 — Trancher (Q49-Q50)
>
> 49. **Que couper** de mes trois semaines restantes, en un seul item, et pourquoi celui-là ?
> 50. Quelle question **essentielle** ai-je omise dans ces cinquante ?
>
> ---
>
> **Format.** Numérote, une à trois lignes par réponse, verdict d'abord et justification
> ensuite. Pas d'introduction. Si une de mes prémisses est fausse, dis-le à la question
> concernée plutôt qu'en préambule.
