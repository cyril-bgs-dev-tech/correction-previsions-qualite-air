# Prompt Grok 4.5 R7 — 50 verdicts sur un résultat qui change le dossier

**Pourquoi maintenant.** Le projet vient de trouver quelque chose : le produit officiel de
post-traitement de Copernicus n'apporte que **+2 %** sur la grandeur réglementaire de
l'ozone, et la **dégrade** en été. Ce n'est plus une question de performance, c'est une
question de **posture** — comment porte-t-on un tel constat quand on est un candidat
spontané face à une institution européenne ?

C'est exactement le registre où Grok est irremplaçable : le jugement humain, le risque social,
la formulation qui passe ou qui tue.

Réponses **une à trois lignes**, verdict d'abord, blocs par valeur décroissante.

À coller tel quel.

---

> Tu m'as relu sept fois, tu connais le dossier. **Ne répète rien.** Une à trois lignes par
> réponse, verdict d'abord, étiquette **[vu]** / **[publié]** / **[jugement]**.
>
> ## Ce qui vient de changer
>
> Copernicus publie un produit de correction de ses prévisions aux stations européennes
> (`optimised-at-observation-sites`), par apprentissage, au pas **horaire**. C'est le seul
> produit post-traité de leur catalogue.
>
> Mesuré sur la **France, année 2024 complète, ozone** :
>
> | Grain | CAMS brut | MOS officiel | Nous |
> |---|---|---|---|
> | horaire (1,6 M obs.) | 17,30 | 14,43 (+16,6 %) | 13,55 (+21,7 %) |
> | **max journalier 8 h** — la grandeur réglementaire | 12,08 | **11,85 (+2,0 %)** | **9,49 (+21,5 %)** |
>
> Et le défaut est **saisonnier** : sur le max 8 h, leur produit **dégrade** le brut d'avril à
> septembre (juillet : 14,05 contre 11,47), avec un POD qui tombe de 0,374 à **0,122**.
>
> **La cause est identifiée et simple** : ils corrigent l'**horaire**, ce qui écrase la
> variabilité — et le maximum d'une série écrasée s'effondre. Or toutes les grandeurs
> réglementaires sont des **maxima**. Nous avons mesuré séparément qu'apprendre directement
> la bonne grandeur rapporte +5,8 points.
>
> **Réserves** : notre modèle a vu 2024 (test hors échantillon 2025 en cours) · un seul
> polluant · un seul pays.
>
> Candidature spontanée à ATMO Occitanie, échéance **22 août 2026**.
>
> ---
>
> ## Bloc 1 — Toi, recruteur, devant ce résultat (Q1-Q10)
>
> 1. Ta réaction en une phrase.
> 2. Tu le crois, ou tu penses qu'il s'est trompé ?
> 3. Qu'est-ce qui te ferait le croire immédiatement ?
> 4. Ce résultat change-t-il ta décision d'embauche, ou c'est un détail technique ?
> 5. Un candidat qui trouve un défaut dans un produit de l'ECMWF : impressionnant, ou
>    prétentieux ?
> 6. Tu utilises ce produit dans ton service ? Si oui, qu'est-ce que ça te fait ?
> 7. Quelle est ta première question pour le mettre en défaut ?
> 8. Préfères-tu ce résultat, ou les +30 % de performance de son modèle ?
> 9. Est-ce que ça vaut un entretien à soi seul ?
> 10. Qu'est-ce qui te ferait dire « il a raison mais je m'en fiche » ?
>
> ## Bloc 2 — Porter une critique d'une institution (Q11-Q22)
>
> 11. Comment le formuler **sans accuser** ?
> 12. La phrase « leur MOS dégrade la grandeur réglementaire » : acceptable, ou à reformuler ?
> 13. Faut-il nommer Copernicus, ou parler de « post-traitement horaire » en général ?
> 14. Un candidat qui critique l'ECMWF prend-il un risque de carrière ?
> 15. Comment éviter de passer pour quelqu'un qui n'a pas compris leur cas d'usage ?
> 16. Faut-il ouvrir en disant « ils ont sans doute de bonnes raisons » ?
> 17. Que répondre si on te dit « vous comparez leur produit horaire à votre produit
>     journalier, c'est déloyal » ?
> 18. Faut-il **leur écrire** avant l'entretien ?
> 19. Si oui, quel ton, et qu'est-ce qui se passe mal si on se trompe ?
> 20. Vaut-il mieux présenter le constat comme une **découverte** ou comme une **vérification
>     de routine** ?
> 21. Quel mot employer : « défaut », « limite », « décalage », « inadéquation » ?
> 22. À quel moment de l'entretien sortir ce résultat ?
>
> ## Bloc 3 — Les risques (Q23-Q32)
>
> 23. Quel est le pire scénario si le résultat est faux ?
> 24. Et s'il est vrai mais déjà connu de tous dans le métier ?
> 25. Comment savoir si c'est un secret de polichinelle ?
> 26. Est-ce que ça peut vexer quelqu'un qui a travaillé sur ce produit ?
> 27. Un recruteur peut-il y voir « il critique au lieu de construire » ?
> 28. Comment éviter que tout le dossier soit réduit à cette découverte ?
> 29. Faut-il un plan B si le test hors échantillon 2025 l'invalide ?
> 30. Quel niveau de certitude faut-il avant de l'écrire noir sur blanc ?
> 31. Est-ce qu'un seul polluant suffit, ou faut-il les trois ?
> 32. Que faire si NO₂ et PM ne montrent pas le même effet ?
>
> ## Bloc 4 — Le dossier (Q33-Q42)
>
> 33. Ce résultat doit-il être en **première page** ?
> 34. Quelle est la nouvelle phrase d'accroche du dossier ?
> 35. Quelle figure le porte le mieux ?
> 36. Faut-il réorganiser les dix pages autour de lui ?
> 37. Qu'est-ce qui devient secondaire et peut être coupé ?
> 38. Le reste du travail — covariables, garde-fou, cible journalière — sert-il encore ?
> 39. Comment articuler « je trouve un défaut chez eux » et « je propose une solution » ?
> 40. Faut-il montrer qu'on a **essayé de se tromper** — les vérifications faites ?
> 41. Combien de place donner aux réserves ?
> 42. Quelle est la dernière phrase du dossier maintenant ?
>
> ## Bloc 5 — Ce que je ne vois pas (Q43-Q48)
>
> 43. Qu'est-ce que je surestime dans ce résultat ?
> 44. Qu'est-ce que je sous-estime ?
> 45. Quelle conséquence pratique m'échappe ?
> 46. À qui d'autre que les AASQA ce constat sert-il ?
> 47. Y a-t-il un usage commercial ou institutionnel auquel je ne pense pas ?
> 48. *Créativité demandée.* Quelle porte ce résultat ouvre-t-il, que je n'ai pas vue ?
>
> ## Bloc 6 — Trancher (Q49-Q50)
>
> 49. S'il ne me reste qu'une action après ce résultat, laquelle ?
> 50. Quelle question essentielle ai-je omise ?
>
> ---
>
> **Format.** Numérote, verdict d'abord. Si une prémisse est fausse, dis-le à la question
> concernée plutôt qu'en préambule.
