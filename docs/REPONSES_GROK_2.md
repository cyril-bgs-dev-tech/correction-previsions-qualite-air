# Réponses aux 30 questions — jury, usage, angles morts, 23 jours (29 juillet 2026)

Sources croisées le **29/07/2026**. **Publié** = documentable ; **Jugement** = opinion argumentée, non mesurable. Six à dix lignes. Priorité aux groupes **D** et **E** (21–25).

---

## A. Ce qu'un jury valorise (je ne peux pas le mesurer)

### 1. +28 % en moyenne vs +22 % en améliorant les pics

**Publié.** PREV’AIR corrige explicitement pour la **détection des seuils réglementaires** et les épisodes, pas pour la RMSE seule ([prevair.org, prévisions corrigées, consulté 29/07/2026](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)). Les bilans AASQA de performances de prévision (LCSQA, millésime 2022) rapportent des indicateurs orientés **seuils / classes**, pas un unique score global ([LCSQA, performances des prévisions](https://www.lcsqa.org/fr/performances-des-previsions)).  
**Jugement.** Un jury AASQA **devrait** préférer le modèle à +22 % qui sauve les pics — c’est le métier (alerte, indice, préfets). En entretien, le +28 % impressionne d’abord ; le candidat qui **montre l’arbitrage chiffré** (votre pondération : ~6–7 pts de gain global contre ~13 pts sur le décile haut) impressionne durablement.  
Ne pas opposer les deux : présenter la **frontière de Pareto** RMSE global / queue, et dire lequel vous choisiriez en production et pourquoi.

### 2. Exposer trois résultats négatifs : rigueur ou doute ?

**Publié.** La culture LCSQA/AASQA documente les limites (bilans de performance, incertitudes de modélisation, guides FAIRMODE). La décision (UE) 2026/1208 exige validation et critères de qualité des modèles ([EUR-Lex 32026D1208, 9/06/2026](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).  
**Jugement.** En France, dans ce milieu, **trois négatifs bien bornés = rigueur** ; trois négatifs sans suite = fragilité.  
La limite : (i) chaque échec a une **cause testable** (−19 % = été hors domaine) ; (ii) un **remède ou une limite d’usage** est proposé ; (iii) le ton reste factuel, pas confessional.  
Cacher le −19 % ou la dégradation des pics O₃ serait plus disqualifiant que les montrer.

### 3. Combien de temps le jury lit-il vraiment ?

**Publié.** Aucune norme publique de durée de lecture d’un dossier de candidature AASQA.  
**Jugement.** Ordre de grandeur réaliste : **5–15 minutes** de lecture préalable, plus l’oral.  
Priorité de lecture : **une page de résultats chiffrés** (tableau baseline / gain / limite) → protocole de validation (fuite ?) → lien métier (indice, seuil, Occitanie) → stack technique en dernier.  
Ce qui n’est pas dans les **deux premières pages** n’existe quasiment pas. Une annexe technique peut être profonde ; le corps doit être scannable.

### 4. Démo interactive : ouverte ou mentionnée ?

**Publié.** Les offres Atmo Occitanie (data junior, responsable IA, PDFs 2026) valorisent vulgarisation et prototypes, sans imposer de format d’entretien ([atmo-occitanie.org/recrutement](https://www.atmo-occitanie.org/recrutement)).  
**Jugement.** Par défaut : **mentionnée + URL/capture**, ouverte **si le jury le demande** ou si vous avez 2–3 minutes cadrées.  
Préparer un scénario de 90 secondes (station held-out, un épisode O₃, un cas « ne pas suivre la correction »). Ne jamais dépendre du Wi‑Fi de la salle : GIF ou vidéo locale de secours.

### 5. Ce qui fait échouer un bon dossier technique à l’oral

**Jugement** (pas d’étude publiée spécifique AASQA).  
- Incapacité à dire **à quoi sert** le chiffre pour un prévisionniste ou un PPA.  
- Vocabulaire hors métier (cf. Q20) ou mépris du CTM (« le ML remplace CHIMERE »).  
- Défense émotionnelle des résultats négatifs, ou au contraire déni.  
- Aucune réponse à « que faites-vous le jour où le modèle se trompe ? ».  
- Monologue architecture au lieu de dialogue sur la **décision**.  
Le dossier technique ouvre la porte ; l’oral tue sur **jugement opérationnel et humilité calibrée**.

---

## B. L'usage réel, que je ne fais que supposer

### 6. Page « aide à l’expertise du jour » — besoin ou projection ?

**Publié.** La chaîne PREV’AIR combine modèle, observations et correction ; les AASQA portent l’expertise régionale et le lien préfets ([prevair.org, système](https://www.prevair.org/le-systeme-prevair)). Les procédures d’épisode reposent sur prévision + mesures ([arrêté du 7 avril 2016](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
**Jugement.** Divergence modèle/mesure, régime, confiance conditionnelle = **besoin réel** du matin de prévision, pas une invention — *à condition* que l’outil s’insère en **2 minutes** dans un rituel existant (pas un dashboard de plus).  
Risque de projection : sur-détailler l’explicabilité ML au lieu du **« est-ce que j’alerte ? »**.  
Valider en demandant en entretien : « qu’ouvrez-vous entre 7 h et 9 h un jour d’ozone ? ».

### 7. Un outil qui dit « ne suis pas la correction aujourd’hui »

**Publié.** Rien d’équivalent documenté comme produit AASQA standard. Les ensembles multi-modèles (CAMS, 11 systèmes) et les bilans de performance formalisent déjà le **doute quantifié** ([CAMS AAR 2025, 29/06/2026](https://atmosphere.copernicus.eu/cams-releases-annual-assessment-report-european-air-quality-2025-0) ; [LCSQA performances](https://www.lcsqa.org/fr/performances-des-previsions)).  
**Jugement.** Un prévisionniste **accepte** un signal de défiance s’il est (i) rare, (ii) expliqué (hors domaine, drift, désaccord stations), (iii) actionnable (revenir à PREV’AIR brut / expertise).  
Mal reçu : ton paternaliste, clignotement permanent, boîte noire.  
Bien reçu : « confiance basse — été hors archive d’entraînement — privilégier CHIMERE/PREV’AIR ».

### 8. Forme d’incertitude utilisable en salle

**Publié.** Communication grand public : **indice ATMO en classes / couleurs** ([Atmo France, indice ATMO](https://www.atmo-france.org/article/lindice-atmo)). Expert : scores, biais, détection de seuils dans les bilans de prévision ([LCSQA](https://www.lcsqa.org/fr/performances-des-previsions)).  
**Jugement.** Hiérarchie d’usage :  
1. **Probabilité de dépassement de seuil** (ou POD/FAR attendu) — la plus actionnable.  
2. **Code couleur confiance** (vert/orange/rouge) sur la correction.  
3. Intervalle en µg/m³ — utile en revue, trop lent le matin.  
4. Variance brute du modèle — quasi inutilisable seule.  
« Rien du tout » est le défaut si l’incertitude n’est pas traduite en **décision**.

### 9. Retours d’expérience publiés — adoption d’outils stats par prévisionnistes QA

**Publié.** Peu de REX « adoption humaine » au sens UX. Ce qui existe : bilans réglementaires de plateformes de prévision par AASQA (ex. Atmo Occitanie, bilan modélisation 2022 sur LCSQA) ; description PREV’AIR de la correction ML ([prevair.org](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)) ; littérature scientifique sur post-processing, rarement sur le refus d’outil.  
**À vérifier.** Enquêtes internes Ineris/AASQA non publiques.  
**Jugement.** L’adoption réussie se voit quand l’outil devient la **référence du briefing**, pas quand un papier annonce +15 % de R².

### 10. Ce qui fait abandonner un outil en trois mois

**Jugement** (transversal outils métier, pas étude QA dédiée trouvée).  
- Faux positifs d’alerte ou silence sur un épisode réel.  
- Friction : login, latence, un écran de plus.  
- Sorties en désaccord avec l’intuition **sans explication courte**.  
- Maintenance morte (données cassées, personne ne regarde).  
- Pas de propriétaire métier.  
Votre page « expertise du jour » mourra si elle n’est pas branchée sur le flux déjà ouvert à 7 h 30.

---

## C. Technique — là où la littérature épargne des jours

### 11. Modèle à deux régimes (classifieur épisode + régresseur)

**Publié.** L’idée « régime / extrême » est classique en AQ et météo (classification d’épisode puis intensité ; modèles d’extrêmes spatiaux-temporels). Ex. récents : réseaux spatio-temporels ciblant les extrêmes (E-STGCN, arXiv 2024-11) ; post-processing orienté seuils PREV’AIR ([prevair.org](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
Gains typiques **non standardisés** : souvent meilleurs POD au seuil, parfois pire biais moyen — **pas de +X % universel**.  
**Pièges :** fuite si le label « épisode » utilise l’observation future ; déséquilibre de classes ; frontière de régime arbitraire ; deux modèles à maintenir.  
**Jugement.** Documenté comme **famille**, pas comme recette magique. Trois jours = test utile **seulement** si métrique = seuil O₃, pas RMSE globale.

### 12. Pondération pour préserver la queue — pratique de référence

**Publié.** Pas de norme AASQA unique. Pratiques établies en stats/ML :  
- **pinball / quantile** (Koenker) ;  
- **pondération par |y| ou y²** (insistance sur hauts niveaux) ;  
- **loss sur excès de seuil** / peaks-over-threshold ;  
- focal / asymmetric losses.  
Votre propre mesure (rapport projet) : MSE simple +28 % global mais **−4 %** sur décile haut O₃ ; pondération par concentration **+22 %** global et **+9 %** décile ; quantile q=0,9 sauve la queue mais **pire que CAMS** en global ([reports/PRESERVER_LA_QUEUE.md](../reports/PRESERVER_LA_QUEUE.md)).  
**Jugement.** La pratique de référence opérationnelle est **métrique au seuil + perte qui ne ruine pas le fond** — votre pondération par concentration est déjà le bon compromis publié *par vous* ; ne pas chercher une formule plus exotique sans gain prouvé.

### 13. Prédiction conforme en production QA

**Publié.** Conformal prediction : garanties sous **échangeabilité** (Vovk ; tutoriels Angelopoulos & Bates). Extension au **drift** : Barber et al., *Conformal prediction beyond exchangeability*, arXiv:2202.13415 (révision 2023).  
Applications AQ : travaux récents (ex. mapping PM2.5 conformal sous covariate shift, arXiv 2026-04 ; forecasting probabiliste régional, 2024) — **recherche**, pas chaîne AASQA/PREV’AIR documentée en production.  
Sous décalage de distribution (votre été caché), la couverture **n’est plus garantie** sans méthodes weighted/adaptive.  
**Jugement.** Utile comme **prototype d’intervalle** sur données quasi-stationnaires ; ne pas promettre une couverture 90 % en production estivale après entraînement hivernal.

### 14. Intervalle de confiance accepté sur séries spatio-temporelles corrélées

**Publié.** La communauté AQ/modélisation accepte plutôt :  
- **validation croisée spatiale / temporelle par blocs** (pas i.i.d.) ;  
- ensembles multi-modèles (CAMS) ;  
- objectifs de qualité de modélisation (MQO) FAIRMODE / annexe V dir. 2024/2881 ;  
- leave-one-station-out pour fusion modèle–mesure ([décision 2026/1208, annexe II](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).  
Les ±σ d’un GBM ignorants de la corrélation spatiale sont **mal vus** s’ils sont présentés comme probabilités vraies.  
**Jugement.** Faire accepter un intervalle = montrer une **couverture empirique** sur plis held-out spatiaux *et* temporels, pas une formule.

### 15. GNN sur 476 stations vs modèle par station + covariables — chiffres

**Publié.** Aucune étude trouvée au 29/07/2026 qui compare proprement un GNN à un tabulaire+covariables sur **le réseau français ~400–500 stations** avec leave-location-out + leave-time-out et residual CTM.  
Littérature GNN AQ (Chine, grilles denses, ST-GCN et variantes) rapporte souvent des baisses de RMSE de l’ordre de **quelques % à ~10–20 %** vs LSTM/GRU **sur leurs jeux**, pas vs LightGBM+LUR+CTM sur la France.  
E-STGCN et apparentés ciblent extrêmes spatio-temporels (arXiv 2024) — chiffres non transposables sans re-benchmark.  
**Jugement / verdict.** **Pas de chiffre publiable pour votre cas.** Baseline tabulaire+covariables d’abord ; GNN seulement si gain mesuré sur *votre* protocole.  
Affirmer « un GNN battra » serait une **spéculation**, pas un fait.

---

## D. Les angles morts que je ne vois pas ★

### 16. La question évidente non posée ★

**Jugement (prioritaire).**  
> **« Sur quelle décision du lundi matin mon score change-t-il quelque chose — et comment le mesurer en classes d’indice ATMO / déclenchement d’épisode, pas en RMSE de station ? »**

Vous avez déjà réorienté vers O₃ et l’EPCI (`LIVRABLE.md`, 28/07/2026) : c’est exactement cette question. Beaucoup de candidats ML s’arrêtent à la station.  
Autres évidences métier souvent oubliées :  
- **heure de cut-off** des entrées (prévision disponible à T vs réanalyse) ;  
- **statut de validation** des mesures (brute vs validée) ;  
- **qui signe** l’indice et l’alerte (responsabilité, pas accuracy).  
Si une seule question devait guider les 23 jours : *le gain survit-il jusqu’à la classe d’indice EPCI ?*

### 17. Ce qu’un ingénieur QA trouverait naïf dans vos formulations

**Jugement.**  
- Dire « on corrige CAMS » sans préciser **échéance, run, polluant, type de station**.  
- Parler de « vérité terrain » pour une mesure qui a une **incertitude et une représentativité**.  
- Présenter un gain national comme un gain **Occitanie opérationnel**.  
- Ignorer que l’indice est un **max sur zone et sur polluants**, pas une moyenne de stations (`LIVRABLE.md` : biais −0,72 classe point→surface).  
- Traiter O₃ comme NO₂ (primaires vs secondaire).  
- « Le modèle prédit la pollution » au lieu de « il réduit l’erreur de *cette* prévision sous *ce* protocole ».

### 18. Biais méthodologique encore probable

**Jugement + bonnes pratiques publiées (validation spatiale).**  
- **Fuite temporelle douce** : features dérivées avec fenêtre qui chevauche le test ; hyperparamètres tunés en regardant le test.  
- **Fuite spatiale** : normalisation ou krigeage utilisant des stations test.  
- **Sélection de stations** non i.i.d. (sur-représentation fond urbain).  
- **CAMS archive vs prévision émise** : évaluer sur un produit plus « savant » que le run du matin.  
- **Sur-interprétation des covariables** : corrélation avec un biais CTM déjà spatialement lisse, pas causalité terrain.  
- **Trois mois** : toute conclusion saisonnière reste fragile (vous le savez — le rappeler à chaque tableau).

### 19. Erreurs systématiques du profil ML sur la physique atmosphérique

**Jugement.**  
- Croire qu’un résidu stationnaire corrige un **régime photochimique** non linéaire (O₃).  
- Sous-estimer **transport** et conditions aux limites (panache, brise de mer, Sahara).  
- Confondre **émission** et **concentration**.  
- Ignorer la **couche limite** et la stabilité (vallées, inversions — enjeu occitan/pyrénéen, [CONTEXTE_ATMO](CONTEXTE_ATMO_OCCITANIE.md)).  
- Traiter les PM comme un scalaire unique (composition CARA, sources).  
- Attendre du ML qu’il invente de la chimie absente des entrées.

### 20. Erreurs de vocabulaire qui trahissent l’extérieur

**Publié / usage métier.**  
- Dire **« taux de pollution »** au lieu de **concentration** (µg/m³) ou **indice**.  
- Confondre **alerte / information / dépassement de valeur limite / indice ATMO**.  
- « Station de mesure » sans **type** (trafic, fond urbain, rural).  
- « Modèle » sans dire **CTM / statistique / inventaire**.  
- « Temps réel » pour de la donnée **horaire non validée**.  
- « Carte satellite » pour du **CAMS modèle**.  
- « Norme OMS » confondue avec **valeur limite UE**.  
Utiliser juste : *fond / proximité, échéance J0 (1-24 h), run, représentativité, épisode, procédure préfectorale*.

---

## E. Arbitrer les 23 jours restants ★

### 21. Archive à un an vs approfondir l’existant

**Jugement, critère extérieur.**  
| Critère jury AASQA | Archive 1 an | Approfondir 3 mois |
|---|---|---|
| Tue l’objection −19 % | **Oui** | Non |
| Crédibilise O₃ estival | **Oui** | Cosmétique |
| Améliore le récit EPCI/indice | Indirect | **Oui si métrique indice** |
| Risque de ne rien finir | Élevé si mal cadré | Faible |

**Verdict.** Si le téléchargement/traitement un an tient en **≤10–12 jours calendaires** (passe unitaire coût+résultat d’abord, règle projet CLAUDE.md) : **priorité archive**, quitte à geler GNN/régimes.  
Sinon : **approfondir O₃ + spatialisation EPCI + arbitrage queue** sur le corpus actuel, et présenter le −19 % comme limite **assumée** avec plan d’extension.  
Les deux à demi = pire option.

### 22. Deux régimes : trois jours utiles ou élégance ?

**Jugement.** **Élégance à bas rendement** tant que la métrique de slide n’est pas le seuil O₃ / classe d’indice.  
Trois jours justifiés **seulement si** : (1) labels épisode sans fuite, (2) comparaison à votre perte pondérée déjà mesurée, (3) gain POD/FAR visible.  
Sinon : investir ces trois jours dans **spatialisation point→EPCI** ou **un mois d’archive estivale supplémentaire**.  
La perte pondérée couvre déjà une partie de l’intention « régime haut ».

### 23. Ozone à fond vs cinq polluants superficiels

**Publié dans votre projet.** O₃ pilote l’indice à **87,8 %** en Occitanie dans votre analyse ; réorientation actée le 28/07 (`LIVRABLE.md`). Indice ATMO = max des sous-indices polluants ([Atmo France](https://www.atmo-france.org/article/lindice-atmo)).  
**Verdict.** **Ozone à fond.** NO₂/PM en une slide « même méthode, gains spatiaux, non optimisés queue ».  
Couvrir cinq polluants en surface dilue le message et contredit votre propre diagnostic.

### 24. Spatialisation EPCI — indispensable ou dispensable ?

**Publié.** L’indice est diffusé par territoire / commune-EPCI, pas par station ([Atmo France, indice ATMO](https://www.atmo-france.org/article/lindice-atmo) ; pratique Atmo Occitanie). Votre mesure : prédire des points donne **−0,72 classe** de biais structurel (`LIVRABLE.md`).  
**Verdict.** **Indispensable au récit**, même si le champ n’est pas parfait.  
Minimum viable en 23 jours : agrégation simple (max/percentile des stations ou grille interpolée) + **accord de classe d’indice** avant/après correction, sur quelques EPCI.  
Dispensable seulement si vous postulez purement « data junior scripts » sans lien prévision — ce n’est pas le positionnement IA/modélisation.

### 25. Que retirer pour rendre le projet plus lisible ?

**Jugement — coupe franche.**  
**Retirer / reléguer en annexe :** GNN, agents, RealMLP comme héros, cinq polluants à parité, long catalogue de sources, toute architecture non ablatée.  
**Garder le fil unique :**  
1. CAMS se trompe où / quand (O₃, pics, été).  
2. Correction apprise + covariables, validation leave-station.  
3. Arbitrage queue (perte pondérée).  
4. Limite temporelle honnête.  
5. Pont métier : **classe d’indice / EPCI** + aide à l’expertise du jour.  
Un lecteur doit pouvoir raconter le projet en **quatre phrases** après la page 1.

---

## F. Après

### 26. Si pris : compétences des premiers mois

**Jugement.**  
- Rituel de prévision et **qui décide quoi**.  
- Chaîne SI locale (bases, validation, horaires de gel des données).  
- Inventaires d’émissions et lien PPA/ZFE (cœur Atmo Occitanie, [CONTEXTE](CONTEXTE_ATMO_OCCITANIE.md)).  
- Lire un bilan de performances de prévision comme un natif ([LCSQA](https://www.lcsqa.org/fr/performances-des-previsions)).  
- Python de prod + git + reproductibilité, pas seulement notebooks.  
- Communication collectivités (sans overclaim).

### 27. Apprendre avant de commencer (ne s’improvise pas)

**Publié à étudier.** Arrêté dispositif national ; arrêté épisodes 7/04/2016 ; construction **indice ATMO** ; bases CHIMERE/PREV’AIR ; directive 2024/2881 (modélisation, 2030).  
**Jugement.** La photochimie O₃ méditerranéenne et la **représentativité des stations** ne s’inventent pas en une semaine sur place — les lire avant J0.

### 28. Outils internes qui rendront peut-être le travail caduc

**À vérifier sur place.** Chaîne régionale de prévision déjà corrigée ; scripts MOS internes ; couplage urbain (type SIRANE ailleurs) ; dashboards prévisionnistes ; accès PREV’AIR+ ; règles auto d’épisode.  
**Jugement.** Votre valeur ne sera pas « le » correcteur national, mais **l’adaptation locale, l’audit, l’indice EPCI, l’IA transverse** (fiche de poste responsable IA 2026).

### 29. Comment un nouvel arrivant gagne la confiance des pratiquants 15 ans

**Jugement.**  
- Arriver en **écoute** les deux premières semaines (shadow du briefing).  
- Livrer un **petit correctif pénible** (script, QA donnée, plot du lundi) avant la grande théorie.  
- Ne jamais contredire un épisode vécu sans données sous les yeux.  
- Créditer le CTM et l’historique.  
- Demander la critique tôt.  
La confiance suit la **fiabilité répétée**, pas le CV ML.

### 30. Sur quoi se taire le premier mois

**Jugement.**  
- « On devrait tout passer en deep learning / agents. »  
- Critiques de PREV’AIR ou des collègues sans mesure.  
- Promesses de gains % en réunion élargie.  
- Refonte du SI.  
- Comparaisons méprisantes autres AASQA.  
Parler tôt : questions de flux de données, définitions d’épisode, où ça fait mal l’été.

---

## Synthèse actionnable — 23 jours

| Rang | Action | Pourquoi (critère extérieur) |
|------|--------|------------------------------|
| 1 | **O₃ + métrique classe d’indice / EPCI** | C’est la décision publiée, pas la RMSE station |
| 2 | **Étendre l’archive autant que le calendrier le permet** | Seule réponse solide au −19 % |
| 3 | **Garder l’arbitrage queue (perte pondérée) en slide principale** | Aligne le jury sur les pics/seuils |
| 4 | **Page expertise du jour minimale** (divergence + confiance) | Usage matin, pas projection |
| 5 | **Couper GNN / multi-polluants / agents** | Lisibilité |

### Groupe D — une ligne

L’angle mort n’est plus une architecture : c’est **l’unité de décision métier** (indice, épisode, responsabilité). Tout score qui ne s’y rattache pas reste un exercice ML, même excellent.

---

*Document complémentaire à `REPONSES_GROK.md`. Re-vérifier l’état des offres et le temps réel de téléchargement archive avant de figer le plan à 23 jours.*
