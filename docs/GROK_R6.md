# GROK R6 — 40 verdicts, point de vue recruteur ATMO (30 juillet 2026)

Prompt : `docs/PROMPT_GROK_R6.md`. Posture : **responsable qui recrute**, pas relecteur académique. **[vu]** / **[publié]** / **[jugement]**.

---

## Bloc 1 — Devant ce dossier (Q1–Q10)

**1.** **Une phrase d'usage + un chiffre réglementaire tenu hors stations vues.** **[jugement]** Sans « lundi matin, sur quoi j'agis », je tourne la page même à +30 %. Avec les deux en 30 s, j'ouvre la suite.

**2.** **Oui, je le reçois.** **[jugement]** Parce qu'il mesure ce qui casse (temps, ERA5, CAMS qui se dégrade) au lieu de vendre une boîte noire — rare en spontané, et le niveau RMSE leave-station est au niveau publié.

**3.** **L'ancrage ops à 4/10 auto-noté sans contrepartie produit.** **[jugement]** Tu me dis que ça ne s'accroche pas au service, puis tu me livres dix pages et un Streamlit : l'écart m'agace plus que le −24,9 %.

**4.** **Maturité si tu proposes le contournement ; cadeau empoisonné si tu t'arrêtes au mea culpa.** **[jugement]** En entretien je retournerai 3/10 et 4/10 : « alors pourquoi je t'embauche ? » — aie la phrase prête.

**5.** **+15 % avec usage clair.** **[jugement]** J'embauche quelqu'un qui réduit mon risque de décision, pas un champion RMSE orphelin.

**6.** **Une seconde lecture chiffrée des prévisions stations O₃/PM avant arbitrage d'épisode — pas une chaîne de remplacement.** **[jugement]** Lundi : « CAMS dit X, correctif leave-station dit Y, écart et confiance » — aide à l'expertise, gain de temps de doute, pas bouton magique.

**7.** **Intégration forçage ops (plus ERA5), monitoring de dérive, réentraînement, dette Python/ML.** **[jugement]** Coût réel = un demi-poste les premiers mois si on industrialise ; en mode « outil analyste » = quelques jours + vigilance données.

**8.** **Il parle POD/CSI/FAR, refuse le NO₂, refuse l'indice qu'il ne peut pas défendre, documente les trous.** **[jugement]** C'est le langage salle de prévision, pas seulement Kaggle. Manque encore le rythme quotidien et la contrainte préfectorale vécue.

**9.** **Démontre : protocole d'évaluation et honnêteté de périmètre. En doute : mise en production et météo temps réel.** **[jugement]**

**10.** **O₃ J+1 : +28,9 % RMSE leave-station, CSI dépassement 0,464.** **[jugement]** Un couple performance + service — pas le +33 % NO₂ (indétectable en épisode).

---

## Bloc 2 — Ancrage opérationnel 4/10 (Q11–Q20)

**11.** **Grave pour la prod, pas disqualifiant pour un recrutement si c'est borné.** **[jugement]** **Annoncer d'emblée** (slide 1 ou 2) : sinon je découvre la bombe en fin et je jette le reste. ERA5 = preuve de concept ; ops = IFS/PREV'AIR/AROME ou équivalent prévu.

**12.** **Ça sauve — à condition du plan B en une phrase.** **[jugement]** « Réanalyse pour l'étude ; bascule prévue sur champs prévisionnels, même protocole » = adulte. « ERA5 point final » = enfonce.

**13.** **Arbitrage épisode / communication / confiance dans la carte du lendemain — typiquement fin de matinée après les sorties modèles et le tour de table.** **[jugement]** L'heure exacte varie ; la décision n'est pas « le RMSE », c'est **publier, graduer, ou attendre**.

**14.** **Cohérence modèles/mesures, situation météo, persistence de la veille, bulletins voisins, signaux atypiques (feux, saharien).** **[jugement]** Ensuite seulement un correctif ML s'il est calibré et expliquable ce jour-là.

**15.** **Plus utile qu'une concentration seule pour l'arbitrage d'épisode — si calibrée.** **[jugement]** Pas un gadget si elle parle POD/FAR au seuil réglementaire ; gadget si elle remplace le µg/m³ sans calibration.

**16.** **Bonne idée **encadrée** ; mauvaise si tu me balances deux points sans recommandation.** **[jugement]** Donne le levier **et** ta reco par usage (com grand public vs vigilance interne). Refiler le curseur nu = lâcheté technique.

**17.** **Pas de quota universel — ordre de grandeur : quelques fausses pour un vrai manqué évité, variable selon O₃ été vs PM hiver et pression com.** **[jugement]** **[publié]** les guides imposent de **mesurer** POD/FAR, pas un ratio d'embauche. En entretien, refuse un chiffre inventé ; propose de le caler avec le service.

**18.** **Boîte noire sans repli, météo non disponible le jour J, score qui s'écroule hors saison sans drapeau, maintenance mono-personne.** **[jugement]** Aussi : correctif qui **empire les pics** sans le dire.

**19.** **Pèse si elle rejoue un jour d'épisode réel en 90 s ; décoratif si tableau de RMSE interactif.** **[jugement]**

**20.** **Carnet de bord « 5 matins » : à heure fixe, entrée modèle brute → correctif → proba seuil → ce que j'aurais recommandé — sur épisodes juil. 2026 déjà publics, sans mon SI.** **[jugement]** Ou : même score recalculé en remplaçant ERA5 par un champ **prévisionnel** ouvert sur un mois. Ça, ça m'impressionne.

---

## Bloc 3 — Généralisation temporelle 3/10 (Q21–Q27)

**21.** **Normal si récurrent et monitoré ; rédhibitoire si tu le caches ou si c'est aléatoire.** **[jugement]** −24,9 % sur un pli double aveugle = « il faut un filet », pas « poubelle » — surtout si réentraînement / abstention existent.

**22.** **[jugement]** En AASQA réelle : souvent **pas** de retrain ML quotidien façon big-tech ; plutôt versions saisonnières, après rupture modèle, ou pas de ML du tout. **[publié]** je n'ai pas ton runbook ATMO Occitanie sous les yeux — ne pas inventer une fréquence. Pose la question en entretien comme candidat curieux.

**23.** **En partie oui — le double aveugle −24,9 % est une exigence de thèse plus dure que mon besoin « utile la plupart des jours d'été ».** **[jugement]** Garde-la comme stress test, pas comme unique porte d'entrée du dossier.

**24.** **S'abstenir / rendre le brut avec drapeau.** **[jugement]** Échouer en silence me coûte une crise ; le brut + « hors domaine » me laisse mon métier.

**25.** **Utile — c'est même le pont vers le 4/10 ops.** **[jugement]** Complexité inutile seulement s'il est illisible. Un feu vert/orange/rouge battant le −24 % vaut mieux qu'un 11ᵉ tableau d'ablation.

**26.** **« Il sait corriger l'espace (stations nouvelles) ; il ne tient pas encore le calendrier ni les régimes nouveaux. »** **[jugement]** Profil junior ML solide spatialement, pas encore calé saison/ops — embauchable avec tutorat métier.

**27.** **Chiffre du pire pli + condition de survenue + règle de bascule (brut / autre modèle / expertise seule).** **[jugement]** Pas d'excuse longue. « Voici quand je me tais. »

---

## Bloc 4 — Valeur / non-valeur (Q28–Q34)

**28.** **Respect immédiat — puis audit : hors fenêtres de dégradation CAMS, que reste-t-il ?** **[jugement]** Spontané = confiance. Si le gain « noble » s'effondre hors ruptures, on recentre le récit ensemble, on ne jette pas la personne.

**29.** **Ça me rassure sur l'honnêteté ; ça m'inquiète si le pitch ouvrait sur le NO₂.** **[jugement]** Déclare-le tôt, pivote O₃/PM. Cacher un POD 0,084 serait pire.

**30.** **« Apprendre le maximum gagne, pas la moyenne » — aligné décision d'épisode.** **[jugement]** Professionnellement plus actionnable que l'ablation krigeage pour mon matin.

**31.** **Oui, beaucoup — c'est un vrai sujet qualité/audit du dispositif public.** **[jugement]** Moins prioritaire qu'un outil de prévision pour un recrutement prévi, mais excellente accroche transversale données/SI si le poste touche au reporting.

**32.** **[vu]** épisode ATMO 25/07/2026 PM10 info **constaté a posteriori** (46, 12). **[jugement]** En faire **la** vignette ops : timeline ce qui était dispo la veille vs le constat ; où un correctif/proba aurait (ou non) changé l'appel. Sans prétendre l'avoir prédit en live si tu ne l'as pas fait.

**33.** **Ingénieur : baselines, leave-station, POD/FAR, limites déclarées, figures actionnables. Chercheur : double aveugle extrême, littérature, originalité 6/10.** **[jugement]** Je recrute l'**ingénieur** qui sait parler au chercheur — pas l'inverse pour ce poste de service.

**34.** **Le travail de *repli et de gouvernance du modèle* (quand se taire, quand réentraîner, comment journaliser).** **[jugement]** Tu le sous-scores en « temporel 3/10 » ; pour moi c'est le début du produit. Aussi : la bascule météo prévisionnelle, même partielle.

---

## Bloc 5 — Forme (Q35–Q38)

**35.** **Bon calibre si un fil ; trop si dix pages = dix rapports.** **[jugement]**

**36.** **Un manque opérationnel + ce que tu apportes le lendemain matin — pas la méthode d'abord.** **[jugement]** Épisode > chiffre > méthode > annexes.

**37.** **« Voici ce qui aurait changé (ou non) dans l'arbitrage d'un épisode réel — et ce que je ne signe pas encore. »** **[jugement]**

**38.** **Note de 2 pages + lien dépôt reproductible > vidéo ; Streamlit seulement en appui d'épisode.** **[jugement]** La com' interne lit court ; le tech creuse le repo.

---

## Bloc 6 — Trancher (Q39–Q40)

**39.** **Une preuve d'opérationnalité sans mon SI : rejeu d'épisode (25/07 PM10 a posteriori + un O₃ 08–09/07) avec drapeau hors-domaine et sans promesse ERA5 en prod.** **[jugement]** Une seule chose — pas un 11ᵉ point de RMSE.

**40.** **« Sous quel contrat t'embauche-t-on — et à 6 mois, quel livrable de service te rend non optionnel ? »** **[jugement]** Stage, CDD prévi, data : le dossier ne dit pas le **rôle** ni le **critère de réussite employeur**.

---

## Synthèse recruteur (hors questions)

| Signal | Lecture |
|--------|---------|
| Recevoir | Oui |
| Risque principal | Outil de labo posé sur mon bureau sans météo ops ni filet temporel |
| Condition d'embauche mentale | Phrase d'usage + plan ERA5→prévi + règle d'abstention |
| Chiffre à remonter direction | O₃ leave-station + CSI épisode, pas le baromètre d'auto-notes |
