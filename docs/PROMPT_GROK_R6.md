# Prompt Grok 4.5 R6 — 40 verdicts, du point de vue de celui qui recrute

**Pourquoi ce cadrage.** Le bilan scoré donne 9/10 à la rigueur et **4/10 à l'ancrage
opérationnel**. Or ce n'est pas un jury académique qui lira ce dossier : c'est un service
qui doit décider s'il embauche. Les questions ci-dessous inversent donc le point de vue —
non « ce travail est-il bon ? » mais **« qu'est-ce que ce travail me fait gagner lundi
matin ? »**

`PROMPT_GPT_R7.md` couvre l'angle analytique (40 questions, quatre colonnes). Celui-ci
couvre l'angle humain et opérationnel. Réponses courtes, blocs par valeur décroissante.

À coller tel quel.

---

> Tu m'as déjà relu quatre fois. **Ne répète rien.** Réponses de **une à trois lignes**,
> verdict d'abord. Étiquette **[vu]** / **[publié]** / **[jugement]**. Les blocs sont classés
> par valeur : si tu dois t'arrêter, arrête-toi à la fin d'un bloc.
>
> **Change de posture.** Tu n'es plus le relecteur du travail : tu es **le responsable qui
> recrute** à ATMO Occitanie. Tu as un service à faire tourner, des prévisions à publier
> chaque jour, et un candidat qui t'envoie un dossier spontané. Juge en ces termes.
>
> ## Ce que le candidat présente
>
> Correction apprise des prévisions **CAMS Europe** (8 km) **aux stations**, France, 17 mois,
> validation par **stations entièrement exclues**. Sur les grandeurs réglementaires :
> **NO₂ +33,2 %**, **O₃ +28,9 %**, **PM2.5 +30,0 %** à J+1, et le gain **croît** jusqu'à J+3.
> Niveau de l'état de l'art publié (Riccio & Chianese 2024 : 27-30 %, stations exclues).
>
> Détection d'épisodes : O₃ **POD 0,663 · CSI 0,464** (fourchette publiée 0,30-0,40),
> PM2.5 POD 0,417, **NO₂ inutilisable** (POD 0,084).
>
> **Un bilan scoré, fait par le candidat lui-même** :
>
> | Dimension | Note |
> |---|---|
> | Rigueur méthodologique | 9/10 |
> | Honnêteté du périmètre | 9/10 |
> | Généralisation **spatiale** | 9/10 |
> | Performance | 8/10 |
> | Pertinence réglementaire | 8/10 |
> | Reproductibilité | 8/10 |
> | Détection d'épisodes | 6/10 |
> | Originalité | 6/10 |
> | **Ancrage opérationnel** | **4/10** |
> | **Généralisation temporelle** | **3/10** |
>
> **Ce que le candidat déclare lui-même comme non acquis** : la généralisation temporelle
> (pire pli **−24,9 %** en double aveugle) ; une part du gain qui revient à une **dégradation
> de CAMS** et non au modèle (corrélation **+0,913** à saison égale) ; le NO₂ indétectable ;
> et surtout sa météo qui est **ERA5, une réanalyse — donc indisponible en opérationnel**.
>
> Livrables : une présentation de dix pages, une bibliothèque de figures, une démo Streamlit,
> un manifeste de reproductibilité. Échéance d'envoi : **22 août 2026**.
>
> ---
>
> ## Bloc 1 — Toi, recruteur, devant ce dossier (Q1-Q10)
>
> 1. Tu ouvres le dossier. **Qu'est-ce qui décide en trente secondes** que tu continues ou
>    que tu passes au suivant ?
> 2. Ce candidat, tu le reçois ou pas ? Une phrase, et **pourquoi**.
> 3. Qu'est-ce qui t'agace le plus dans ce dossier ?
> 4. Un candidat qui note lui-même ses faiblesses 3/10 et 4/10 : maturité, ou **cadeau
>    empoisonné** que tu retourneras contre lui ?
> 5. Entre un dossier à **+30 % de RMSE mal raconté** et un dossier à **+15 % avec un usage
>    clair**, lequel embauches-tu ?
> 6. Qu'est-ce que ce travail te fait **gagner concrètement** dans ton service, lundi matin ?
> 7. Et qu'est-ce qu'il te **coûte** — temps d'intégration, dépendances, maintenance ?
> 8. Le candidat n'a jamais travaillé en AASQA. **Qu'est-ce qui, dans ce dossier, prouve
>    malgré tout qu'il saurait y travailler ?**
> 9. Quelle **compétence** ce dossier démontre le mieux, et laquelle laisse-t-il en doute ?
> 10. Si tu ne devais retenir qu'**un seul chiffre** de tout ce travail pour le citer à ta
>     direction, lequel ?
>
> ## Bloc 2 — L'ancrage opérationnel, la note à 4/10 (Q11-Q20)
>
> 11. **ERA5 est une réanalyse.** À quel point est-ce disqualifiant à tes yeux ? Le candidat
>     doit-il l'annoncer d'emblée ou attendre la question ?
> 12. S'il l'annonce lui-même, ça sauve ou ça enfonce ?
> 13. Quelle **décision** prends-tu réellement le matin, et à quelle heure ?
> 14. Qu'est-ce que tu regardes **avant** de publier l'indice du lendemain ?
> 15. Une **probabilité de dépassement** t'est-elle plus utile qu'une concentration corrigée,
>     ou est-ce un gadget de data scientist ?
> 16. Le candidat te propose de choisir toi-même le point de fonctionnement (POD 0,737 /
>     FAR 0,466, ou POD 0,493 / FAR 0,264). Bonne idée, ou **façon de te refiler la
>     décision** ?
> 17. Combien de **fausses alertes** par an es-tu prêt à accepter pour un épisode détecté de
>     plus ?
> 18. Qu'est-ce qui, dans un outil de prévision, te fait dire « **je ne le mettrai jamais en
>     production** » ?
> 19. Une **démo Streamlit** : ça pèse dans ta décision, ou c'est décoratif ?
> 20. *Créativité demandée.* Sans accès à ton système, **quelle preuve d'opérationnalité** le
>     candidat pourrait-il produire seul et qui t'impressionnerait vraiment ?
>
> ## Bloc 3 — La généralisation temporelle, la note à 3/10 (Q21-Q27)
>
> 21. Un modèle dont le **pire mois fait −24,9 %** : rédhibitoire, ou normal et acceptable si
>     on le réentraîne ?
> 22. **Réentraînez-vous** vos modèles en production, et à quelle fréquence ?
> 23. Le candidat s'impose-t-il une exigence **académique** qui ne correspond à aucun de tes
>     besoins réels ?
> 24. Préfères-tu un modèle qui **échoue parfois** ou un modèle qui **s'abstient** en rendant
>     la prévision brute quand il ne sait pas ?
> 25. Un indicateur qui **prévient** que le modèle est hors de son domaine ce jour-là : utile,
>     ou complexité inutile ?
> 26. Le candidat a la généralisation **spatiale** solide (σ 1,2) et la temporelle faible.
>     Cette asymétrie, tu l'entends comment ?
> 27. Comment veux-tu qu'il te **présente** cet échec sans que tu perdes confiance ?
>
> ## Bloc 4 — Ce qui a de la valeur, et ce qui n'en a pas (Q28-Q34)
>
> 28. La **corrélation +0,913** entre dégradation de CAMS et gain du candidat : il te la dit
>     spontanément. Réaction ?
> 29. Le fait que **le NO₂ soit indétectable** — il le déclare. Ça te rassure ou ça t'inquiète ?
> 30. Parmi ses résultats **négatifs** (empiler krigeage et covariables dégrade ; la typologie
>     de station n'apporte rien ; apprendre le maximum gagne mais pas la moyenne), lequel
>     t'intéresse le plus **professionnellement** ?
> 31. Le candidat a découvert que **le flux public d'indice écrase ses propres millésimes** —
>     donc personne ne peut auditer a posteriori la performance publiée. Ça t'intéresse ?
> 32. Il a un épisode réel : **PM10 du 25 juillet 2026**, Lot et Aveyron, **constaté après
>     coup**. Que doit-il en faire ?
> 33. Qu'est-ce qui, dans ce dossier, est du **travail d'ingénieur** et qu'est-ce qui est du
>     **travail de chercheur** ? Lequel cherches-tu ?
> 34. *Créativité demandée.* Quelle **partie du travail** le candidat sous-estime alors
>     qu'elle a de la valeur pour toi ?
>
> ## Bloc 5 — La forme du dossier (Q35-Q38)
>
> 35. Dix pages de présentation : trop, trop peu, bon calibre ?
> 36. Par quoi doit-il **commencer** — un chiffre, un épisode, une méthode, un manque ?
> 37. Quelle est **la** phrase d'accroche que tu voudrais lire en premier ?
> 38. Y a-t-il un **format** que tu préférerais à une présentation — une note de deux pages,
>     un dépôt de code, une vidéo de trois minutes ?
>
> ## Bloc 6 — Trancher (Q39-Q40)
>
> 39. Il reste trois semaines. **Une seule chose** à faire, laquelle ?
> 40. Quelle question **essentielle** ai-je omise dans ces quarante ?
>
> ---
>
> **Format.** Numérote, une à trois lignes par réponse, verdict d'abord. Pas d'introduction.
> Si une prémisse est fausse, dis-le à la question concernée.
