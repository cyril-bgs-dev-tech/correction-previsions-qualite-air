# Prompts pour relecteurs externes — ronde du 30/07/2026

> **Ronde close pour Grok** — sa réponse est dans `GROK_R4.md`. Sa recommandation
> principale (« test = 2025 calendaire, ~6-8 mois de test ») repose sur une prémisse
> fausse : le panel d'observations s'arrête au **31/12/2024**, il n'y a **aucune**
> observation en 2025. Vérifié sur les données (2025-01 : 894 lignes contre ~665 000 pour
> un mois plein). Ne pas reprendre ce verdict tel quel.
>
> **Chiffres corrigés depuis la première rédaction** : couverture **17 mois** (août 2023 →
> décembre 2024), et non 18 ; archive CAMS jusqu'à **juin 2025**, et non juin 2026.

Deux prompts calibrés sur ce que chaque modèle peut réellement tenir :

- **ChatGPT → mission longue.** Un seul sujet, creusé : la **spatialisation de l'indice
  ATMO**. C'est le plus gros écart restant (−0,72 classe, 42,8 % d'accord) et le dernier
  maillon vers l'indice publié. Tâche documentaire, donc vérifiable ligne à ligne.
- **Grok 4.5 → une salve courte.** Sa session ne tiendra pas : les questions sont rangées
  **par valeur décroissante**, pour qu'une réponse tronquée reste utile. Une seule vraie
  question — le protocole de validation que 18 mois autorisent.

**Ne plus demander** — déjà sourcé, il ne reste que du code à écrire :

| Sujet | Où | Ce qu'il reste à faire, côté dépôt |
|---|---|---|
| Paramètres FAIRMODE par polluant | `GPT_R3.md` §11 — v4.0 tab. 6 p. 35 ; v3.2 DOI 10.2760/30226 tab. 6 p. 43 | vérifier `aq.eval.comparaison` contre le tableau |
| Référentiel de prévision opposable | `GPT_R3.md` §15 — guide LCSQA applicable au 01/01/2022 | raccorder au **POD/FAR/SR/FB/CSI**, 75 % de couples, O₃ en max journalier avril-sept., J0 et J1 |
| Ruptures opérationnelles CAMS | `GPT_R3.md` §1-6 | construire `cams_regional_upgrade` (U7b, U8, U8b, U9) |

---

## Prompt 1 — ChatGPT · mission longue

> Tu es ingénieur d'étude en qualité de l'air, familier des AASQA françaises, de la chaîne
> PREV'AIR et du référentiel technique national LCSQA. Je prépare une candidature
> spontanée à ATMO Occitanie (échéance 22 août 2026). J'ai besoin d'une **fiche source
> exploitable**, pas d'un avis : je vais écrire du code à partir de tes réponses.
>
> **Règles de réponse, strictes — elles comptent plus que l'exhaustivité.**
> 1. Classe chaque affirmation en **Établi** (lien + article ou page), **À vérifier**
>    (piste plausible, source incomplète) ou **Inconnu**.
> 2. **Aucun chiffre, aucun nom de méthode, aucune référence sans source vérifiable.** Un
>    « Inconnu » assumé m'est plus utile qu'une valeur plausible : une référence inventée
>    dans un livrable réglementaire est pire que son absence.
> 3. Quand un texte a été modifié, dis lequel fait foi **aujourd'hui**.
> 4. Ne me réponds pas sur les paramètres FAIRMODE ni sur le guide LCSQA d'évaluation des
>    prévisions : je les ai déjà sourcés. Reste sur la spatialisation.
>
> **Mon état, en trois phrases.** Je corrige par apprentissage (LightGBM, post-traitement
> type MOS) les prévisions CAMS Europe (0,1°, ~8 km, J+1 à J+3) **aux stations de mesure**,
> sur **17 mois** d'observations appariées (août 2023 → décembre 2024 ; mes prévisions vont
> jusqu'à juin 2025 mais je n'ai pas encore les observations de 2025), 476 stations
> métropolitaines. Je reconstitue ensuite un indice ATMO **en station** sur trois polluants
> (NO₂, O₃, PM2.5). Comparé à l'indice **publié** à l'EPCI, je n'obtiens que **42,8 %
> d'accord exact, avec un biais de −0,72 classe** — mon indice est donc plus **bas** que
> l'officiel.
>
> Mon hypothèse : l'écart vient de la **spatialisation** (station → commune → EPCI) et des
> **cinq** polluants officiels contre mes trois, pas de la qualité de mes prévisions. Je
> veux savoir si cette hypothèse tient et ce que je dois reproduire pour être comparable.
>
> **Un point de cadrage, à ne pas perdre de vue.** Un relecteur me conseille de **ne pas**
> reproduire cette spatialisation en 23 jours, et de rester en station en assumant l'écart.
> C'est peut-être le bon choix — mais je ne veux pas l'assumer par manque de temps, je veux
> l'assumer en sachant exactement ce que je renonce à mesurer. Réponds donc pour
> m'**équiper**, que je reproduise ou non : un « je ne le fais pas, et voici précisément
> pourquoi » sourcé vaut mieux qu'un travail bâclé.
>
> **Les huit questions. Traite-les toutes, dans l'ordre.**
>
> **1. Le texte qui fait foi.** Quel texte fixe aujourd'hui le calcul et la diffusion de
> l'indice ATMO (nature, date, version en vigueur, modifications éventuelles) ? Que dit-il
> exactement sur : (a) les polluants obligatoires, (b) les seuils de classes par polluant,
> (c) l'**échelle de restitution** imposée, (d) la règle d'agrégation entre sous-indices ?
> Cite l'article pour chacun.
>
> **2. L'ordre des opérations — le cœur de mon écart.** L'indice d'un EPCI est-il le
> **maximum** des sous-indices sur son emprise, une moyenne, la valeur d'une maille
> représentative, autre chose ? Et surtout : l'agrégation spatiale porte-t-elle sur les
> **concentrations** (puis on classe), ou sur les **classes** déjà calculées (puis on
> agrège) ? Les deux ordres ne donnent pas le même résultat, et je dois savoir lequel
> reproduire.
>
> **3. La méthode de production.** Comment une AASQA passe-t-elle d'un champ modèle et de
> stations ponctuelles à une carte communale : krigeage, fusion données-modèle,
> assimilation, descente d'échelle statistique ? Nomme les outils **réellement employés en
> France**, dis lesquels sont documentés publiquement, et lesquels relèvent d'un choix
> propre à chaque AASQA.
>
> **4. La résolution.** À quelle résolution le champ est-il produit avant agrégation
> communale ? Cette résolution est-elle imposée par un texte ou laissée à l'AASQA ?
>
> **5. Le sens de mon biais — teste mon hypothèse.** Un indice calculé **en station**
> devrait plutôt être plus **haut** qu'un indice spatialisé (les stations trafic tirent
> vers le haut, les mailles rurales vers le bas). Or je mesure **−0,72 classe**, donc plus
> **bas**. Qu'est-ce qui explique ce sens-là ? Passe en revue, en hiérarchisant par
> ampleur probable : les deux polluants que je n'ai pas (dis-moi lesquels et à quelle
> fréquence ils **pilotent** l'indice en Occitanie), les PM10 sahariennes, le rôle des
> stations trafic (sont-elles **exclues** du calcul de l'indice ?), le fait que je n'aie
> que des stations là où l'officiel couvre tout le territoire.
>
> **6. Prévu ou constaté.** L'indice publié « du jour » et celui « de demain » sortent-ils
> de la même chaîne ? Si celui du lendemain est un indice **prévu**, contre lequel des deux
> dois-je me comparer pour être honnête, moi qui produis une prévision à J+1 ?
>
> **7. La circularité de l'évaluation — la question méthodologique la plus importante.**
> Si le produit officiel interpole lui aussi depuis les **mêmes stations** que celles que
> j'utilise, alors comparer mon interpolation à la sienne n'est pas une validation
> indépendante : les deux savent la même chose. Comment une AASQA valide-t-elle sa propre
> spatialisation — validation croisée en retirant des stations, campagnes de mesure mobile,
> micro-capteurs, comparaison inter-modèles ? Puis dis-moi quel protocole serait
> **défendable pour moi**, avec des données ouvertes uniquement.
>
> **8. Les données, très concrètement.** Pour reproduire et pour évaluer, il me faut :
> (a) le contour des communes et des EPCI d'Occitanie, (b) la population par commune,
> (c) et surtout l'**historique de l'indice ATMO publié par EPCI** sur plusieurs mois, qui
> me sert de vérité terrain. Pour chacun : la source ouverte exacte, le format, la
> profondeur d'historique réellement disponible, la licence, et s'il existe une API. Si
> l'historique de l'indice n'est pas récupérable en masse, dis-le clairement — cela
> changerait ma stratégie d'évaluation.
>
> **Pour finir, une seule phrase de recommandation** : dois-je (a) reproduire la
> spatialisation, (b) abandonner la comparaison à l'indice publié et rester en station en
> l'assumant explicitement, ou (c) comparer autrement ? Justifie uniquement par ce que tu
> viens d'établir.
>
> **Format.** Une section par question, la réponse d'abord et les sources ensuite. Pas
> d'introduction, pas de résumé initial. Termine par la liste des points classés
> « Inconnu » : ce sont ceux que j'irai demander directement à l'AASQA, et les connaître
> a autant de valeur que le reste.

---

## Prompt 2 — Grok 4.5 · salve courte

> Tu m'as déjà relu deux fois : ne répète rien de général. Réponds en français, **bref et
> tranché** — une recommandation par point, pas de liste d'options. Traite les points dans
> l'ordre : si tu dois t'arrêter, arrête-toi après le 1.
>
> **Ce qui a changé depuis hier, et qui motive la question.** Un défaut d'analyse de nom de
> fichier me faisait perdre **35 % de mon jeu d'entraînement en silence** (expression
> ancrée à droite : sur des dossiers bi-mensuels, seul le second mois était capturé).
> Corrigé, je passe de **11 à 18 mois** d'observations appariées, sur une archive CAMS
> désormais de 24 mois (juillet 2023 → juin 2026 ; 2025-02 à 2025-07 sont sans
> observations). J'ajoute aussi deux familles de variables : **trafic hiérarchisé**
> (champ `importance` de la BD TOPO, au lieu de la seule longueur de voirie) et
> **population communale**. Tous mes chiffres de performance sont donc **en recalcul** —
> sauf la barre à battre, déjà refaite sur 18 mois : CAMS brut J+1, France, ~4,0 M de
> paires, NO₂ RMSE **12,87** (R² +0,125), O₃ **16,97**, PM2.5 **5,86**, avec une
> dégradation faible jusqu'à J+3.
>
> Le décor : correction apprise (LightGBM) des prévisions CAMS Europe aux stations,
> entraînement France entière, évaluation Occitanie, 476 stations, 38 variables de paysage
> et 9 de relief. Ce que je ne prétends pas : ce n'est pas le système d'ATMO (CAMS ≠
> PREV'AIR à 2 km), ce n'est pas l'indice officiel publié, et mon rappel des jours
> « Mauvais » (~0,47 contre ~0,24 pour CAMS brut) reste mauvais en absolu. Candidature à
> rendre le **22 août 2026**, soit 23 jours.
>
> **1. Le découpage d'évaluation — la seule question qui compte.** Avec 18 mois couvrant
> deux étés et deux hivers, quel protocole défend le mieux ce travail devant un ingénieur
> d'AASQA ? Tranche entre : (a) validation temporelle glissante à plusieurs plis, (b) coupe
> inter-annuelle franche — entraîner 2023-2024, tester 2025, (c) double aveugle spatial
> **et** temporel simultané. Pour chacun, dis en une ligne ce qu'il **démontre** et ce
> qu'il **coûte** en effectif de test. Puis choisis : **un** protocole principal, **un**
> secondaire, rien de plus — je ne peux pas tout faire en 23 jours.
>
> **2. Le piège du changement d'échantillon.** En passant de 11 à 18 mois, quelle métrique
> devrais-je m'attendre à voir **se dégrader** ? Et si l'une **s'améliore** au contraire,
> laquelle serait le signe d'une fuite d'information plutôt que d'un progrès ? Nomme la
> métrique et le mécanisme, deux phrases.
>
> **3. La question qu'on va me poser sur le trafic.** « Ces variables sont **statiques** :
> comment peuvent-elles améliorer une **prévision** ? » Donne la réponse juste, puis
> l'expérience courte qui la **prouve** au lieu de l'affirmer. Et le revers : à partir de
> quand est-ce de la mémorisation de station plutôt que de la généralisation ?
>
> **4. Si tu tiens encore — l'actualité.** Juillet 2026 vient de finir : des épisodes de
> pollution en Occitanie ce mois-ci (ozone, PM de feux ou d'intrusion saharienne), et
> lesquels ont été **mal anticipés** ? Une actualité ATMO Occitanie ou LCSQA de juillet
> 2026 à connaître avant que j'écrive ? Distingue nettement ce que tu as **vu** de ce que
> tu supposes.
>
> Termine par la **seule** chose que tu couperais de mes 23 jours restants.

---

## Micro-tests — pour toute session courte

Un modèle à fenêtre limitée est mal employé sur une question de jugement : il l'est bien
sur des **vérifications atomiques**. Chacun des tests ci-dessous est autoportant, se colle
seul, se répond en quelques lignes, et **je peux le vérifier**. À servir dans l'ordre : le
premier débloque une correction de code en attente.

En-tête à coller devant n'importe lequel :

> Réponds en français, en trois lignes maximum. Donne la source (document, version, page).
> Si tu n'as pas la source sous les yeux, réponds **Inconnu** — une valeur plausible me
> coûterait plus cher que ton silence, elle irait dans un livrable réglementaire.

**T1 — le paramètre que je crois faux.** Dans le *Guidance Document on Modelling Quality
Objectives and Benchmarking* du JRC (FAIRMODE), version **3.2** de 2020, DOI
10.2760/30226, tableau 6 : quelle est la valeur de **α pour PM2,5** ? Et celle pour
**PM10** ? Je soupçonne mon code d'avoir utilisé celle de PM10 (0,13) à la place de celle
de PM2,5.

**T2 — la formule.** Toujours dans ce document, l'incertitude de mesure servant au MQI
s'écrit-elle bien
`U(O) = U_r^RV · sqrt((1 − α²)·O² + α²·RV²)` ,
avec `O` l'observation ? Confirme la place du `(1 − α²)` et du `α²` — les inverser change
le résultat, et dis si l'expression porte sur `RMS_U` ou sur `U` point par point.

**T3 — le temps d'agrégation.** Les paramètres du tableau 6 sont-ils définis pour un
**temps d'agrégation précis par polluant** (NO₂ horaire, O₃ en maximum journalier 8 h,
PM2,5 en journalier) ? Autrement dit : calculer un MQI sur des concentrations **horaires**
d'O₃ et de PM2,5 sort-il du cadre du document ? Réponds oui ou non, puis cite.

**T4 — quelle version citer.** En juillet 2026, pour une candidature en France, cite-t-on
la v3.2 (2020, β = 2 global) ou la v4.0 (mai 2026, β par polluant) ? La v4.0 annonce-t-elle
elle-même une révision à venir, et la v3.2 est-elle formellement retirée ?

**T5 — mon estimateur d'intervalle.** Je compare deux modèles sur ~4 millions de couples
horaires issus de 343 stations, fortement autocorrélés. Je tire un bootstrap **par
station** (l'unité rééchantillonnée est la station, pas la ligne), 300 tirages, IC 95 %.
Deux questions : le groupement par station est-il le bon choix face à cette
autocorrélation, et **300 tirages suffisent-ils** pour un IC 95 %, ou faut-il monter ?

**T6 — le sens d'un biais.** Un indice de qualité de l'air calculé **aux stations** de
mesure est-il structurellement plus **haut** ou plus **bas** qu'un indice spatialisé sur un
EPCI entier, et pourquoi ? Une phrase, et dis si les stations trafic entrent dans le calcul
de l'indice ATMO français.

---

## Après leurs réponses

Les consigner dans `docs/` au format des rondes précédentes (`GPT_R3.md`, `GROK_R3.md`),
et **vérifier chaque chiffre** avant qu'il n'entre dans un livrable : la ronde 3 a livré
une référence exacte et une piste non concluante **sans que le ton les distingue**.
