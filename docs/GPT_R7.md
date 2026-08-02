# Bloc A — Généralisation temporelle

## Q1 — Nouvelle configuration et double aveugle

**Réponse.** La direction nette est **Inconnue**. [jugement] L’agrégation journalière devrait réduire le bruit et l’écart entre mois, mais la capacité triplée augmente la possibilité d’apprendre des relations propres à la période. Le gain de +6,5 points observé sur la cible réglementaire ne mesure pas le transfert temporel. Il faut donc éviter de reporter le +14,4 % de l’ancienne configuration sur la nouvelle.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Inconnu ; hypothèse de travail : pire pli relevé de 5–10 points [jugement] | 6 h | Rejouer d’abord trois mois cachés : ancien pire pli, mois médian, meilleur pli, avec stations également cachées | Si le pire pli reste ≤ −15 %, ou si deux plis sur trois se dégradent, ne pas lancer les 18 plis avant d’avoir un garde-fou |

## Q2 — Non-stationnarité, taille d’échantillon et minimum sur 18 plis

**Réponse.** Il faut séparer trois objets : la moyenne des pertes, leur dispersion entre mois et le minimum, qui baisse mécaniquement quand le nombre de plis augmente. [jugement] Compare les configurations sur les **mêmes mois** et estime par bootstrap de mois la distribution du minimum pour 7 puis 18 plis. Une dérive est plus crédible si la perte suit le temps ou une rupture CAMS, pas seulement si un minimum est mauvais. Avec 17 mois, l’attribution causale restera fragile.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Diagnostic, pas gain RMSE ; séparation partielle des trois causes [jugement] | 3 h | Bootstrap des 18 pertes mensuelles, puis régression robuste de `ΔMSE` sur date, saison et indicateur de cycle CAMS | Si les intervalles sont trop larges pour distinguer une tendance de zéro, conclure « puissance insuffisante » |

## Q3 — Réentraînement glissant

**Réponse.** Il réduit l’âge des données mais ne « règle » pas une rupture : il expose encore le système pendant le délai d’observation et le premier intervalle avant réentraînement. [jugement] La bonne démonstration est préquentielle : à chaque mois, entraîner uniquement sur le passé, avec fenêtres glissantes de 3, 6, 12 mois et fenêtre croissante. Une fréquence mensuelle est un scénario à tester, pas une norme publiée universelle.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Inconnu | 7 h | Sur 6 dates d’origine réparties dans l’archive, comparer fenêtre 3/6/12 mois et croissante, mêmes stations cachées | Abandonner la fenêtre courte si son gain médian n’excède pas la fenêtre croissante et si sa variance augmente |

## Q4 — Prédire la sortie du domaine

**Réponse.** À l’émission, on peut détecter une **dérive de covariables**, pas une dérive du lien concentration–variables sans observations. La piste la plus falsifiable combine : distance au voisin d’apprentissage, score d’un classifieur « entraînement contre lot courant », désaccord d’un petit ensemble et taux de valeurs manquantes. La littérature documente la détection de dérive, mais un gain chiffré pour ce dispositif CAMS–AASQA est **Inconnu** [S-A1].

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Inconnu [publié : aucun gain AQ comparable trouvé] | 6 h | Produire ces quatre scores hors pli, puis mesurer leur AP pour identifier les jours où `MSE_corrigé > MSE_CAMS` | Abandonner comme garde-fou si l’AP n’excède pas la prévalence de 20 % relatif, ou si le signe n’est pas stable entre polluants |

## Q5 — Abstention ou retour à CAMS

**Réponse.** Il ne faut pas présenter cela comme une absence de prévision : le système **revient à CAMS brut**. C’est un mécanisme de sûreté explicable. [jugement] Calibre le seuil sur une courbe risque–couverture hors pli : perte moyenne de la correction en fonction de la fraction de cas acceptés. Le taux n’a pas de valeur universelle ; il doit résulter d’un coût asymétrique défini avec le métier.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Inconnu ; gain maximal borné par les erreurs évitées dans la queue [jugement] | 4 h | Tester des couvertures préfixées de 80, 90 et 95 %, seuil choisi dans les plis internes | Abandonner si aucun seuil ne réduit le 95e percentile de perte sans supprimer plus de 20 % des corrections utiles |

## Q6 — Signature commune des plis qui échouent

**Réponse.** Préenregistre au plus six signatures calculables avant vérité terrain : distance aux données, score de dérive, désaccord d’ensemble, proportion manquante, cycle CAMS et régime météo. Ensuite, chaque mois est prédit par un modèle ajusté sur les 17 autres mois ; aucune variable ne doit être inventée après inspection des échecs. [jugement] Dix-huit unités mensuelles interdisent une recherche multivariée ambitieuse.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Diagnostic ; Inconnu pour le score | 4 h | Corrélations leave-one-month-out et test de permutation au niveau mois | Si aucun signal n’a le même signe dans au moins 14/18 omissions, conserver seulement une analyse descriptive |

## Q7 — Borner l’échec et prévision conforme

**Réponse.** La prévision conforme peut fournir des intervalles à couverture marginale ou adaptative, y compris à plusieurs horizons [S-A2]. Elle ne garantit pas que la correction ponctuelle battra CAMS, ni un pire cas sous dérive arbitraire. [jugement] Le produit utile est plutôt : intervalle de concentration + retour à CAMS lorsque l’intervalle de **différence de perte** ne soutient pas la correction.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Couverture visée 90 % ; gain RMSE Inconnu [publié] | 7 h | Conformalisation par blocs de date sur prédictions hors pli ; vérifier couverture par mois et largeur | Abandonner toute formulation de « garantie » si un mois tombe sous 80 % de couverture pour une cible de 90 % |

## Q8 — Plis mensuels, saisonniers ou régimes météo

**Réponse.** Les plis mensuels répondent le mieux au déploiement « mois nouveau ». Les blocs saisonniers sont presque non identifiables avec seulement 1,5 cycle annuel. Les régimes météo testent une autre question — l’extrapolation physique — et doivent compléter, non remplacer, le calendrier. [jugement] Le diagnostic principal reste mensuel et chronologique.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Diagnostic ; Inconnu | 5 h | Regrouper les jours en 6–8 régimes par variables météo seulement, puis cacher chaque régime sans retuner | Abandonner les conclusions par régime si un groupe contient <5 % des jours ou une seule saison |

## Q9 — Corrélation avec la dégradation de CAMS

**Réponse.** Oui, le pourcentage de gain partage son dénominateur avec l’erreur CAMS : plus le brut est mauvais, plus il offre mécaniquement de marge. La corrélation +0,913 ne démontre donc ni robustesse ni causalité. [jugement] Il faut montrer simultanément `RMSE_corrigé`, `RMSE_CAMS` et leur différence absolue, puis comparer des mois de même saison avant/après rupture.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Correction d’interprétation, pas gain modèle | 2 h | Régression de `MSE_CAMS − MSE_corrigé` et de `MSE_corrigé` sur l’erreur CAMS, avec saison fixe | Retirer la corrélation du dossier si elle disparaît sur la différence absolue ou après contrôle saisonnier |

## Q10 — Présenter l’asymétrie spatial/temporal

**Réponse.** Formulation défendable : « interpolation spatiale démontrée sur stations exclues ; transport temporel non démontré et parfois négatif ». Ce n’est pas une validation opérationnelle, mais un résultat de périmètre : les covariables statiques transfèrent entre lieux, tandis que la relation dynamique dépend de la période et du modèle amont. [jugement] Donne les deux distributions, jamais seulement leur moyenne.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Gain de crédibilité ; non quantifiable [jugement] | 2 h | Faire relire une figure « deux axes : station inconnue / mois inconnu » sans texte explicatif | Si le lecteur conclut « modèle opérationnel validé », renommer explicitement le résultat « preuve de concept rétrospective » |

## Q11 — Besoin réel de généralisation temporelle

**Réponse.** Oui, au moins sur la durée entre deux mises à jour et pendant le délai de disponibilité des observations. Le réentraînement mensuel ne protège ni le premier jour après une rupture amont, ni une dérive progressive, ni une panne du flux d’observations. [jugement] L’exigence réaliste n’est pas « transférer un an », mais « ne pas nuire pendant un cycle de maintenance avec un repli sûr ».

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Inconnu | 5 h | Simulation préquentielle mensuelle avec délai d’observation de 2, 7 et 30 jours | Si le gain devient négatif dès 7 jours de délai, ne pas revendiquer une mise à jour mensuelle comme solution |

### Sources du bloc A

- **[S-A1] [publié]** Dehghan, M., Raahemi, B., Akbari, A. et Nassersharif, B. (2016), méthode de détection de dérive de concepts, *Intelligent Data Analysis*, DOI : [10.3233/IDA-150207](https://doi.org/10.3233/IDA-150207).
- **[S-A2] [publié]** Xu et al. (2024), prévision conforme adaptative à plusieurs pas, *Neurocomputing*, DOI : [10.1016/j.neucom.2024.128434](https://doi.org/10.1016/j.neucom.2024.128434).
- **[S-A3] [publié]** Riccio et Chianese (2024), correction statistique avec stations exclues, *Atmospheric Chemistry and Physics*, DOI : [10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024). Cette publication situe la performance spatiale, pas la robustesse mensuelle du présent projet.

# Bloc B — Ancrage opérationnel

## Q12 — Passage d’ERA5 à une météo prévue

**Prémisse à corriger.** ERA5 rend l’expérience rétrospective de type *perfect prognosis* ; elle ne mesure pas une chaîne disponible à l’émission. Un chiffre publié isolant, sur un même post-traitement de qualité de l’air, la seule substitution « réanalyse → prévision météo » n’a pas été trouvé : **Inconnu**. Bertrand et al. emploient des prévisions ECMWF opérationnelles, mais ne publient pas cette ablation appariée [S-B1].

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Perte de performance : Inconnu ; hypothèse 0–5 points de gain relatif, davantage aux extrêmes [jugement] | 8 h | Remplacer seulement les champs ERA5 par une semaine de prévisions archivées, mêmes dates et modèle gelé | Si la perte dépasse 5 points ou double sur les dépassements, retirer toute qualification opérationnelle fondée sur ERA5 |

## Q13 — Mesure bon marché de l’écart météo

**Réponse.** Ajouter un bruit gaussien à ERA5 n’est pas un substitut valide : les erreurs météo dépendent du régime, de l’horizon, de la variable et sont corrélées dans l’espace. [jugement] À défaut d’une archive complète, apparie une courte période de prévisions réelles à ERA5, conserve les champs d’erreur journaliers entiers, puis rééchantillonne ces champs par horizon. Cela mesure une sensibilité, pas la performance opérationnelle annuelle.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Estimation grossière ; biais annuel Inconnu | 5 h | 14 jours ARPEGE–ERA5, injection par blocs jour et comparaison à un bruit indépendant de même variance | Si les deux perturbations donnent des conclusions opposées, déclarer le substitut non informatif et passer à une archive réelle |

## Q14 — Sources gratuites de prévisions météo

**Réponse.** Aucune source française gratuite identifiée ne combine à la fois disponibilité opérationnelle documentée et archive en ligne immédiate de 17 mois. ARPEGE/AROME ont une rétention publique de 14 jours [S-B2] ; ECMWF Open Data conserve les 12 derniers runs, environ 2–3 jours [S-B3]. Le GFS 0,25° est archivé par le NCEI depuis 2014 et couvre donc la période en principe [S-B4], mais la latence exacte et la complétude des variables doivent être vérifiées sur un échantillon avant de bâtir la chaîne.

| Source | Latence publique | Archive exploitable | Verdict |
|---|---|---|---|
| ARPEGE 0,1° / AROME | **Inconnu** sur la page de données | 14 jours | Opérationnel futur, pas backfill 17 mois |
| ECMWF IFS Open Data 0,25° | Calendrier de diffusion publié, SLA **Inconnu** | 12 runs | Pas backfill |
| NOAA GFS 0,25° / NCEI | **Inconnu** pour ce besoin | Depuis 2014 en principe | Candidat au backfill, à vérifier |

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Suppression de la fuite ERA5 ; variation de score Inconnue | 6 h | Télécharger 10 dates GFS, trois horizons et les seules variables réellement utilisées | Abandonner GFS si >5 % des fichiers/champs manquent ou si la correspondance temporelle est ambiguë |

## Q15 — Heure de disponibilité CAMS Europe

**Réponse.** Le catalogue officiel annonce, chaque jour, les échéances 0–48 h vers **06:45 UTC** et 49–96 h vers **08:30 UTC** [S-B5]. Ce sont des horaires de disponibilité annoncés, pas un SLA de disponibilité observée ; la garantie contractuelle publique est **Inconnue**. Le catalogue décrit d’ailleurs 0,1° comme environ 10 km, pas 8 km partout.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Preuve de latence ; pas gain modèle | 4 h réparties | Journaliser pendant 10 jours l’heure du premier fichier complet 0–48 h | Si le 95e percentile dépasse l’heure produit visée, décaler le produit ou prévoir la veille comme repli |

## Q16 — Décision matinale d’une AASQA

**Réponse.** Le détail « heure, ordre des écrans, seuil d’intervention humaine » n’est pas normalisé publiquement : **Inconnu**. Le dispositif national indique que les AASQA alimentent quotidiennement une prévision J/J+1 **avant midi**, afin que le représentant de l’État puisse engager la procédure [S-B6]. Il est raisonnable de supposer que la décision utile en amont est la qualification du risque d’épisode et la validation du bulletin, mais l’ordre de travail d’Atmo Occitanie doit être vérifié en entretien.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Ancrage métier ; Inconnu | 1 h | Préparer une carte J/J+1, probabilité, incertitude et motif de repli ; la faire tester par un prévisionniste si accessible | Si aucune décision identifiable n’utilise le produit avant publication, ne pas le qualifier d’outil opérationnel |

## Q17 — Prouver l’opérationnalité sans accès AASQA

**Réponse.** La preuve la plus forte à portée est un **shadow run prospectif** : chaque matin, récupérer les entrées réellement disponibles, horodater chaque étape, produire sans vérité future, puis ne scorer qu’après arrivée des observations. Ajoute deux pannes injectées — météo absente et version de schéma inconnue. C’est plus probant qu’un rejeu dont les dates de publication des archives seraient reconstruites.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Gain de crédibilité élevé, performance Inconnue [jugement] | 8 h de montage + 10 min/jour | Trois shadow runs avant d’automatiser davantage, dont un avec entrée supprimée | Si une exécution exige une correction manuelle silencieuse ou dépasse 30 min après CAMS, la chaîne n’est pas opérationnelle |

## Q18 — Contrat de service minimal

**Réponse.** Aucun SLA AASQA public uniforme n’a été identifié. [jugement] Contrat candidat minimal : résultat ≤30 min après disponibilité du lot CAMS requis ; succès sur ≥95 % des shadow runs ; repli explicite vers CAMS brut ; aucune prédiction avec entrée partielle non signalée ; version, empreinte des entrées, modèle et heure conservés. Ces valeurs sont des objectifs de démonstrateur, pas des normes.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Crédibilité ; Inconnu | 4 h | Dix exécutions chronométrées et deux simulations de panne | Abandonner la promesse si <95 % terminent dans la fenêtre ou si un repli n’est pas visible dans la sortie |

## Q19 — Concentration et probabilité

**Réponse.** C’est un atout si elles proviennent d’une même distribution prédictive : médiane/espérance pour la carte, probabilité pour la décision. C’est une complexité si deux modèles indépendants se contredisent. [jugement] L’interface doit montrer d’abord le risque de dépassement, puis la concentration et l’incertitude comme explication.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Adoption : Inconnu | 3 h | Sur 30 cas hors pli, compter les contradictions « probabilité élevée / concentration sous seuil » | Si >5 % sont incohérents sans intervalle qui l’explique, ne livrer qu’un produit probabiliste dérivé d’une distribution unique |

## Q20 — Rupture du flux ozone EEA

**Prémisse à corriger.** La rupture nationale exacte « depuis le 01/07/2025 » n’a pas été confirmée par une source publique retrouvée : **Inconnu**. Surtout, l’EEA est un diffuseur aval ; une AASQA peut disposer de ses propres mesures même si le flux européen est incomplet. L’incident soutient un **mode dégradé portable**, pas l’idée que l’AASQA serait privée de ses observations locales.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Résilience de pipeline ; score Inconnu | 2 h | Simuler 1, 7 et 30 jours sans observations récentes, avec signalement visible | Abandonner l’argument EEA si l’AASQA confirme que son flux interne est indépendant ; conserver seulement le test générique de panne |

## Q21 — Épisode fumées des 25–26 juillet 2026

**Prémisse à corriger.** Atmo Occitanie indique que des fumées d’incendies ont atteint le nord de la région dès le 25 juillet et publie une prévision/alerte pour le **26 juillet** dans sept départements [S-B7]. Cela ne prouve ni que le 25 n’a pas été prévu, ni un échec du modèle. Sans entrées et observations horodatées, ce cas peut illustrer une classe de risque — transport de fumées — mais ne peut pas scorer le projet.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Narratif opérationnel ; gain quantitatif Inconnu | 3 h | Constituer une fiche chronologique sourcée : bulletins disponibles avant chaque échéance, CAMS disponible, observations ultérieures | Si l’heure d’émission du bulletin initial reste inconnue, bannir les termes « non prévu » et « échec » |

## Q22 — Question opérationnelle manquante

**Réponse.** « Que fait le système demain matin si une entrée manque, arrive en retard ou change de version, et comment le sais-je **avant** publication ? » [jugement] Une réponse crédible nomme le contrôle, le repli, l’indicateur visible, le responsable et la trace conservée. Le gain moyen n’y répond pas.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Gain d’entretien élevé ; non quantifiable [jugement] | 2 h | Démonstration filmée de 3 minutes avec un champ météo supprimé et un schéma CAMS modifié | Si une sortie plausible est produite sans alerte bloquante, suspendre toute revendication d’opérationnalité |

### Sources du bloc B

- **[S-B1] [publié]** Bertrand et al. (2023), prévisions de qualité de l’air par forêts aléatoires utilisant notamment les prévisions ECMWF, *Atmospheric Chemistry and Physics*, DOI : [10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).
- **[S-B2] [source institutionnelle]** Météo-France/data.gouv.fr, [API Modèle ARPEGE](https://dev.data.gouv.fr/dataservices/api-modele-arpege), accès ouvert avec compte, taux de disponibilité non communiqué et jeu associé à rétention de 14 jours, consulté le 30 juillet 2026.
- **[S-B3] [source institutionnelle]** ECMWF, [Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), douze derniers runs, consulté le 30 juillet 2026.
- **[S-B4] [source institutionnelle]** NOAA/NCEI, [catalogue historique GFS](https://www.ncei.noaa.gov/thredds/catalog/model/gfs.html) et demande d’archivage du GFS 0,25° à partir du 17 décembre 2014, consultés le 30 juillet 2026.
- **[S-B5] [publié]** Copernicus Atmosphere Monitoring Service, [CAMS European air-quality forecasts](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview), calendrier 06:45/08:30 UTC, archive glissante de trois ans et mises à niveau occasionnelles, DOI : [10.24381/a4005cee](https://doi.org/10.24381/a4005cee), consulté le 30 juillet 2026.
- **[S-B6] [source institutionnelle]** LCSQA, [Vigilance atmosphérique](https://www.lcsqa.org/fr/vigilance-atmospherique), prévisions AASQA J/J+1, consulté le 30 juillet 2026.
- **[S-B7] [source institutionnelle]** Atmo Occitanie, [épisode de particules lié aux fumées d’incendies des 25–26 juillet 2026](https://www.atmo-occitanie.org/episodes-pollution/2026-07-27%7C82), consulté le 30 juillet 2026.

# Bloc C — Détection d’épisodes

## Q23 — Monter le POD sans faire exploser le FAR

**Réponse.** Déplacer seulement le seuil ne déplace pas la courbe. Une calibration monotone améliore les probabilités, mais conserve le classement et donc les courbes ROC/PR. Il faut améliorer le signal : cible réglementaire directe, variables disponibles à l’émission qui expliquent les extrêmes, perte pondérée ou modèle de régime. La littérature avertit aussi que sélectionner les cas à évaluer parce qu’ils sont extrêmes observés produit le « dilemme du prévisionniste » [S-C1].

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Inconnu pour POD/FAR ; +6,5 points déjà observés sur RMSE de cible directe [résultat projet] | 7 h | Même validation imbriquée, comparer perte standard, pondérée et quantile sur la courbe PR entière | Abandonner la variante si l’AP et le Brier skill n’augmentent pas toutes deux, ou si le gain disparaît par saison |

## Q24 — NO₂ récupérable ?

**Réponse.** La prévalence est de **0,164 %** (273/165 990, calcul du projet). Changer le seuil réglementaire pour sauver la métrique serait incorrect. [jugement] Il faut d’abord vérifier si la décision AASQA est réellement station–jour ; si elle est zone–jour, agréger selon une règle fixée avant calcul. Si le besoin reste le dépassement station–jour à 120 µg/m³, le résultat actuel doit être qualifié d’inutilisable et la possibilité de récupération est **Inconnue**.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Inconnu | 5 h | Comparer trois cibles préfixées : marge continue au seuil, station–jour, zone–jour ; mêmes plis et seuil inchangé | Renoncer à la classification station–jour si l’AP n’excède pas deux fois la prévalence ou si l’IC du BSS contient 0 |

## Q25 — Reformulation créative de l’épisode

**Réponse.** La formulation la plus prometteuse est le **maximum de marge normalisée au seuil dans une zone et une journée**, puis le rang des jours à risque sous un budget d’alertes. Elle conserve l’information de distance au seuil, répond à une décision zonale et évite d’apprendre directement 0,164 % de « 1 ». Une seconde option, plus ambitieuse, est un modèle de temps jusqu’au début et jusqu’à la fin de l’épisode ; 273 cas sont probablement trop peu nombreux.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Inconnu [jugement] | 6 h | Sans réentraîner : classer les jours par marge prédite existante et calculer rappel parmi les 5/10 % de jours les plus risqués | Abandonner si le lift du top 5 % est <3 par rapport à la prévalence zonale ou instable entre zones |

## Q26 — Seuil de Brier skill utilisable

**Réponse.** Il n’existe pas de seuil universel publié. Un BSS >0 signifie seulement « meilleur que la référence choisie » ; son utilité dépend de la calibration, de la résolution, de l’incertitude et du coût métier. [jugement] +0,460 est substantiel si calculé hors pli face à une climatologie légitime ; +0,017 est à peine positif et ne doit pas être qualifié d’utile sans intervalle de confiance. La référence du BSS doit être nommée.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Décision, pas gain modèle | 3 h | Bootstrap hiérarchique par épisode et zone du BSS, avec diagramme fiabilité–résolution | Si l’IC95 % inclut 0 ou si la fiabilité se dégrade dans les probabilités hautes, abandonner « utilisable » |

## Q27 — Apport résiduel de la classification

**Réponse.** Compare les deux sorties sur les **mêmes observations hors pli**, après calibration apprise uniquement dans les plis internes. La classification n’est justifiée que si elle améliore une règle de score propre (Brier ou logarithmique), l’AP et une utilité opérationnelle préspécifiée. Un CSI de 0,464 contre 0,437, seul, ne paie pas un second modèle. [jugement]

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Résiduel observé en CSI : +0,027 ; gain propre Inconnu | 4 h | Test apparié par bootstrap d’épisodes sur Brier, log-loss et AP des prédictions OOF | Supprimer le classifieur si aucun des trois gains n’est positif avec IC95 %, ou si la calibration exige un entretien séparé |

## Q28 — Remplacer le CSI sur événement rare

**Réponse.** Utilise en primaire l’aire sous la courbe précision–rappel, rapportée à sa base — la prévalence — puis Brier skill, score logarithmique et courbe de calibration. Les courbes PR sont plus informatives que ROC sous fort déséquilibre [S-C2]. Le CSI reste une mesure secondaire à un seuil de décision fixé hors échantillon. Aucun score unique ne remplace la définition du coût des fausses alertes et des ratés.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Évite un faux positif méthodologique ; pas gain prédictif | 2 h | Recalculer AP/prévalence et BSS sur les sorties existantes, bootstrap par épisode | Si le classement des modèles change selon chaque métrique, ne pas annoncer un « meilleur » modèle sans fonction de coût |

## Q29 — Station, zone ou agrégat national

**Réponse.** Évalue les deux niveaux : station–jour pour diagnostiquer le modèle, zone–jour/événement pour la décision. L’agrégat national masque les zones et sous-estime la dépendance. [jugement] La règle zonale — maximum, proportion de surface/population ou nombre de stations — doit être définie d’après la procédure métier avant de voir les scores. Le bootstrap doit porter sur épisodes/zones, pas sur lignes station indépendantes.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Pertinence métier ; gain numérique Inconnu | 5 h | Une région test, règles zonales fixées à l’avance, comparaison avec score global | Abandonner toute agrégation qui change qualitativement quand une seule station est retirée |

### Sources du bloc C

- **[S-C1] [publié]** Lerch, S., Thorarinsdottir, T. L., Ravazzolo, F. et Gneiting, T. (2017), « Forecaster’s Dilemma », *Statistical Science*, DOI : [10.1214/16-STS588](https://doi.org/10.1214/16-STS588).
- **[S-C2] [publié]** Saito, T. et Rehmsmeier, M. (2015), courbes précision–rappel pour classes déséquilibrées, *PLOS ONE*, DOI : [10.1371/journal.pone.0118432](https://doi.org/10.1371/journal.pone.0118432).
- Les gains publiés spécifiques capables de déplacer toute la courbe POD–FAR pour CAMS Europe, avec stations et dates exclues, sont **Inconnus** dans la recherche effectuée.

# Bloc D — Originalité

## Q30 — Nouveauté des résultats négatifs

**Réponse.** Le troisième n’est pas entièrement nouveau : Bertrand et al. montrent déjà qu’un apprentissage direct du maximum journalier peut se comporter différemment d’un maximum dérivé de prévisions horaires [S-D1]. Pour « terrain + krigeage du résidu dégrade » et « typologie officielle n’ajoute rien au biais global », une démonstration strictement comparable n’a pas été trouvée : **Inconnu**, pas « nouveau ». Ces deux résultats deviennent publiables seulement s’ils survivent à plusieurs polluants, rayons et schémas de validation.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Originalité : Inconnu | 7 h | Répéter chaque résultat sur 3 graines, 2 polluants et mêmes plis ; aucun nouveau tuning | Abandonner la revendication si le signe change ou si l’écart est inférieur à l’incertitude inter-pli |

## Q31 — Asymétrie maxima/moyennes

**Réponse.** Oui, au moins un résultat publié la documente. Dans Bertrand et al. (2023), pour leur configuration globale par forêt aléatoire, le maximum journalier obtenu depuis les prévisions horaires a une RMSE de 20,5 contre 32,8 pour l’apprentissage direct du maximum ; la moyenne journalière est beaucoup moins asymétrique [S-D1]. Ce résultat n’établit pas une loi générale et son sens est opposé au tien : c’est précisément pourquoi la comparaison de cibles est une contribution de protocole, pas une règle mécanique.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Gain déjà mesuré jusqu’à +6,5 points [résultat projet] | 2 h | Tableau apparié direct/agrégé pour maxima et moyennes, mêmes plis et capacité | Abandonner l’explication universelle si l’interaction cible×agrégation n’est pas stable par polluant/horizon |

## Q32 — Nom de la corrélation +0,913

**Réponse.** Il n’existe pas de nom spécifique établi retrouvé en post-traitement de l’air. Deux mécanismes sont connus : **dépendance au modèle de référence / marge de progression** et **couplage mathématique** lorsqu’un gain relatif partage l’erreur du brut. S’y ajoute ici une possible dérive de concept après changement du modèle amont. [jugement] La valeur +0,913 ne doit pas être interprétée comme la preuve que la correction « s’adapte » aux ruptures.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Clarification causale ; pas gain modèle | 3 h | Analyse en différence absolue de MSE et série interrompue aux 13/11 et 03/12/2024 | Abandonner l’expression « phénomène robuste » si l’effet n’est pas présent sur les erreurs absolues corrigées |

## Q33 — Angle à portée et peu traité

**Réponse.** Angle proposé : **correction sûre sous changement du modèle amont**. Le système ne cherche pas seulement le meilleur RMSE ; il estime, à l’émission, si la correction a une espérance de perte inférieure à CAMS, revient au brut sinon, et publie une courbe risque–couverture autour des ruptures de cycle. [jugement] L’originalité exacte dans la littérature AQ est **Inconnue**, mais cet angle unifie tes échecs temporels, la corrélation +0,913 et le besoin opérationnel.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Réduction du pire pli : Inconnu ; originalité : Inconnu | 8 h | Méta-modèle très simple sur prédictions OOF, 4 indicateurs préenregistrés, évaluation leave-one-month-out | Abandonner si le pire pli ne gagne pas ≥5 points ou si le gain moyen baisse de >2 points |

## Q34 — Contribution méthodologique ou performance

**Réponse.** Revendiquer la méthode est plus solide : cible alignée sur la grandeur réglementaire, stations exclues, double aveugle espace–temps, résultats négatifs et périmètre explicite. La performance comparable à Riccio et Chianese est une validation de niveau, pas une nouveauté [S-D2]. [jugement] La contribution est « comment évaluer honnêtement et sécuriser », non « LightGBM bat CAMS ».

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Gain de dossier ; non quantifiable [jugement] | 3 h | Résumer la contribution sans aucun pourcentage en 150 mots et vérifier qu’elle reste précise | Si le résumé devient générique sans les scores, conserver la performance comme résultat principal et la méthode comme limite |

## Q35 — Note courte publiable

**Réponse.** Oui, potentiellement : une note reproductible sur « transfert spatial réussi, transfert temporel fragile et garde-fou sous changement CAMS ». Format réaliste : prépublication technique courte, 4–6 figures, code et splits archivés ; l’acceptation dans une revue est **Inconnue**. Il manque avant soumission une météo réellement prévue et un test temporel indépendant ou prospectif.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Valeur de candidature élevée ; publication Inconnue [jugement] | 6 h pour plan + figures existantes | Produire un résumé structuré et une figure maîtresse ; demander une lecture adverse | Abandonner le mot « publiable » si la conclusion repose encore sur ERA5 ou sur les mêmes mois ayant choisi les règles |

### Sources du bloc D

- **[S-D1] [publié]** Bertrand et al. (2023), comparaison d’apprentissages horaires et journaliers, notamment tableau 3, *Atmospheric Chemistry and Physics*, DOI : [10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).
- **[S-D2] [publié]** Riccio et Chianese (2024), correction statistique évaluée sur stations exclues, *Atmospheric Chemistry and Physics*, DOI : [10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024).
- La priorité d’antériorité des deux résultats négatifs et de l’angle de « correction sûre sous changement amont » reste **Inconnue** sans revue systématique.

# Bloc E — Plafonds des dimensions fortes

## Q36 — Seuils lus sur les données d’évaluation

**Réponse.** Les seuils de 70 µg/m³ et `p ≥ 0,20` sont actuellement optimistes. Choisis-les uniquement dans la boucle interne, puis applique-les au pli externe intact. Quand les données sont rares, fais du *cross-fitting* : chaque prédiction externe reçoit le seuil choisi sans elle ; rapporte médiane et dispersion des seuils, plus la performance OOF agrégée. Aucun jeu supplémentaire n’est requis.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Score apparent probablement en baisse ; biais supprimé [jugement] | 5 h | Recalculer les seuils à partir des prédictions OOF déjà stockées, sans réentraîner LightGBM | Abandonner un seuil fixe si son IQR entre plis dépasse 20 µg/m³ ou 0,10 de probabilité |

## Q37 — MQI FAIRMODE à la mauvaise agrégation

**Réponse.** Il faut recalculer avec l’agrégation définie pour chaque polluant et retirer entre-temps toute mention de conformité pour O₃ et PM2.5. FAIRMODE traite les objectifs par polluant et grandeur ; un MQI horaire exploratoire ne devient pas conforme parce que la formule est correcte [S-E1]. Si le recalcul respecte exactement données, couverture, incertitude et indicateurs demandés, la mention peut revenir, en citant la version du guide.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Conformité documentaire ; score Inconnu | 4 h | Recalcul sur un polluant avec script indépendant et contrôle manuel de 10 jours | Si l’agrégation, l’incertitude d’observation ou la couverture requise n’est pas reproduite, écrire « diagnostic inspiré de FAIRMODE » |

## Q38 — Reproductibilité par un tiers

**Réponse.** Le manifeste est nécessaire mais insuffisant. Il faut : requêtes d’acquisition figées, snapshot ou empreintes des données brutes, règles de sélection/QC des stations, identifiants exacts des plis, graines, environnement verrouillé, commande unique de bout en bout, artefacts intermédiaires, tolérances attendues et licences. [jugement] Un tiers doit aussi savoir reconstruire un résultat si une API change.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Reproductibilité ; non quantifiable | 6 h | Clone propre dans un nouveau dossier, exécution d’un polluant/pli depuis zéro avec seulement le README | Si une décision orale, un cache non déclaré ou un chemin local est requis, la reproduction autonome échoue |

## Q39 — Atteindre l’état de l’art suffit-il ?

**Réponse.** Oui pour une candidature : atteindre un résultat publié avec un protocole plus exigeant sur stations exclues démontre déjà la maîtrise. [jugement] L’élément différenciant atteignable n’est pas un point de RMSE supplémentaire, mais le garde-fou temporel et la preuve opérationnelle horodatée. Cela répond directement aux notes 3/10 et 4/10.

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Différenciation ; Inconnu | 8 h | Prototype du garde-fou + trois shadow runs, sans nouvelle architecture | Abandonner si aucune réduction du pire mois et aucune exécution autonome ne sont démontrées |

## Q40 — Réallocation jusqu’au 22 août 2026

**Réponse.** Au 30 juillet, il reste 23 jours calendaires. [jugement] Priorité : mesurer la nouvelle double aveugle, remplacer ou borner ERA5, puis produire une preuve opérationnelle. La seule chose à ne pas faire est tester des réseaux neuronaux/transformeurs : ils attirent, mais ne répondent à aucune des deux faiblesses principales.

| Bloc | Allocation | Livrable d’arrêt |
|---|---:|---|
| A — temporel | 6 jours | Double aveugle nouvelle configuration + garde-fou falsifié ou retenu |
| B — opérationnel | 5 jours | Source météo prévue testée + ≥3 shadow runs et 2 pannes |
| C — épisodes | 3 jours | PR/Brier/IC, cible NO₂ déclarée viable ou abandonnée |
| D — originalité et récit | 4 jours | Une figure maîtresse et un claim borné |
| E — seuils, MQI, reproduction | 3 jours | Seuils cross-fittés, agrégations corrigées, clone propre |
| Marge | 2 jours | Régressions, rédaction finale |

| Gain attendu | Coût | Test de falsification le moins cher | Critère d’abandon |
|---|---:|---|---|
| Hausse des notes faibles : Inconnu [jugement] | Enveloppe maximale 184 h sur 23 jours calendaires ; chaque calcul <8 h | Revue à J+7 : au moins un double aveugle et un run météo prévue terminés | Si l’un manque, couper immédiatement originalité et épisode pour finir A+B |

### Sources du bloc E

- **[S-E1] [publié]** FAIRMODE, *Modelling quality objectives and benchmarking — Version 3.2*, DOI : [10.2760/30226](https://doi.org/10.2760/30226). La version effectivement opposable ou recommandée en 2026 est **à vérifier** avant d’employer « conforme ».
- Les seuils de service, d’abstention, de Brier skill et de stabilité inter-plis proposés ici sont **[jugement]**, non des normes AASQA ou FAIRMODE.

# Points classés Inconnu

1. Sens et amplitude du changement de score double aveugle avec cible journalière et capacité triplée.
2. Part attribuable séparément à la non-stationnarité et au manque de données avec seulement 17 mois.
3. Fréquence optimale et gain du réentraînement glissant pour ce dispositif.
4. Gain AQ publié d’un détecteur de sortie du domaine ou d’un retour sélectif à CAMS.
5. Garantie de pire cas sous dérive : la couverture conforme ne garantit pas que la correction bat CAMS.
6. Dégradation chiffrée causée uniquement par le remplacement d’ERA5 par une météo prévue.
7. Source gratuite française réunissant SLA public et archive immédiate de 17 mois ; latence et complétude GFS à vérifier.
8. Caractère garanti des horaires ADS 06:45/08:30 UTC.
9. Heure, ordre des contrôles et critères d’intervention propres aux prévisionnistes d’Atmo Occitanie.
10. Réalité et portée de la rupture EEA ozone exactement depuis le 1er juillet 2025.
11. Affirmation que l’épisode du 25 juillet 2026 n’avait pas été prévu.
12. Gain publié déplaçant toute la courbe POD–FAR dans un protocole CAMS comparable.
13. Seuil universel de Brier skill « utilisable » : il n’existe pas dans les sources trouvées.
14. Récupérabilité du NO₂ à 120 µg/m³ au niveau station–jour.
15. Antériorité exacte des résultats négatifs terrain+krigeage et typologie+biais.
16. Nouveauté bibliographique de l’angle « correction sûre sous changement du modèle amont ».
17. Acceptation d’une note courte sans météo prévue ni test temporel indépendant.
18. Version FAIRMODE à citer comme effectivement en vigueur en 2026 et portée exacte de « conformité » dans ce contexte.
