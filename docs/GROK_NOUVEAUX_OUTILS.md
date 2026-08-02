# GROK — Nouveaux outils (ensemble, feux, IFS/AIFS) : valeur en exploitation

*Angle : service un mardi matin, pas stats de fuite. Jugement métier sauf [vu]/[publié].*

**Contexte :** 6 membres CAMS O₃ · GFAS · IFS/AIFS AWS · MOS déjà à ×3,6 dépassements O₃ à budget FA égal · PM2,5 POD utile · NO₂ indétectable · 25/07 raté par tous.

---

## A. Dispersion d’ensemble (1–12)

**1.** **Surtout la médiane / le produit agrégé** (PREV’AIR, CAMS ensemble). La dispersion membre à membre est **marginale** en routine AASQA — plus un regard études ou jour de doute qu’un rituel 8 h.

**2.** Quand elle existe : plutôt **éventail ou min–max sur un point / une zone**, parfois carte de spread. Rarement un indicateur unique bien calibré « confiance 0–100 ».

**3.** Il **gradue la confiance**, retarde un message trop sec, ou cherche une **obs** qui tranche. Il n’appelle pas la préfecture *parce que* l’écart-type a bougé — il appelle parce qu’un seuil se joue.

**4.** D’abord la **confiance** ; la décision (info/alerte) ne bascule que si on est **déjà sur le fil** du seuil. Divergence seule, loin des seuils → peu d’effet.

**5.** **Pas de X universel écrit** du type « σ > X ⇒ pas d’auto-publication ». Des pratiques d’équipe floues (« les modèles ne sont pas d’accord, on reste prudents »), pas une règle chiffrée nationale.

**6.** **Folklore + fond de vérité** : CHIMERE « maison » France ; réputations saison/processus circulent en ateliers. Peu de tableau de bord officiel « champion du mois » opposable en entretien.

**7.** **Oui** : CHIMERE/PREV’AIR a un **statut de référence nationale**. Le voir diverger des autres pèse plus qu’un désaccord entre deux membres « exotiques ».

**8.** Intérêt **études / recherche appliquée** oui ; en exploitation quotidienne, une pondération apprise = **encore une boîte** à maintenir et expliquer. Acceptable en mode *consultation*, pas en boîte noire qui publie.

**9.** **Utile** s’il tient en une pastille (« désaccord fort → ne pas durcir seuls ») ; **trop subtil** s’il faut un cours de 20 min. Formule : *méfiance*, pas *méta-modèle*.

**10.** **Oui, souvent pire** : une barre d’incertitude non calibrée **légitime des mauvaises audaces** ou paralyse sans raison. Mieux : pas d’indic, ou indic **avec mode d’emploi** (« non calibré, ordonner seulement »).

**11.** L’ensemble opérationnel est conçu pour **survivre** à un membre manquant (médiane sur restants). Un service qui dépend d’un membre nommé **casse** ; un service sur médiane/spread robuste **tient**.

**12.** **Défendable** si tu dis « sous-ensemble stable, 6/11, trou nov. 2023 documenté » et que tu ne prétends pas l’ensemble officiel complet. **Bancal** si tu vends « l’ensemble CAMS » sans le dire incomplet.

---

## B. Feux (13–24)

**13.** Mélange : **préfecture / SDIS / sécurité civile**, médias, fumée visible, collègues, parfois sat/CAMS/EFFIS côté études. Pas un unique API « feu → prévi » dans toutes les boîtes.

**14.** De **quasi immédiat** (odeur, appel) à **heures** (canal officiel). Le canal le plus fiable pour l’action reste souvent **institutionnel**, pas GFAS seul.

**15.** **Oui**, fréquemment : hausse PM, élargissement zone, ton plus prudent. Ajustement **qualitatif** plus que recalage µg précis.

**16.** Souvent des **réflexes / retours d’expérience**, parfois fiches épisode ; rarement un code aussi cadré que l’ozone estival classique. Variable selon AASQA.

**17.** [publié cadre] Certains épisodes « naturels » (sable, parfois feux selon règles) ont un **traitement réglementaire/com’ distinct**. Ça **change le récit** plus que l’intérêt de prévoir la **concentration** : le public respire pareil.

**18.** En pratique : **local et régional (20–300 km)** d’abord — décision et com’ du jour. Canadien à 5 000 km : contexte / rare, sauf panache exceptionnel.

**19.** « Épisode probable » **oui** ; « origine combustion » **utile en com’ et diagnostic**, pas toujours dans le mandat de **seuil** (le seuil se joue en µg). Ne pas sur-promettre l’attribution légale.

**20.** Couche **contexte** : « attention PM amont », pas bouton alerte auto. Sert à **ne pas sous-interpréter** une hausse et à préparer la com’.

**21.** **Seulement s’il ne coûte presque rien** le reste de l’année (GFAS à 0,1 Mo/mois = candidat). Un usine à gaz pour 5 jours/an = non.

**22.** **Oui si le nouveau portail est stable et scriptable** ; non si la chaîne casse à chaque migration. Documenter bascule + plan B (sans feux). Migration ≠ interdit, = **risque d’exploitation à chiffrer**.

**23.** **Oui** : EFFIS / Copernicus EMS, canaux sécurité civile, produits sat fumée, parfois outils nationaux. Tu n’es pas le seul radar — positionne GFAS comme **complément quantitatif**, pas découverte du feu.

**24.** **Tolérance à l’erreur plus basse sur le miss** (on « aurait dû voir la fumée »), un peu plus haute sur une **FA prudente** le jour J. Le médiatique **durcit le miss**, pas la FA modérée.

---

## C. Deux modèles « habituel + feu » (25–33)

**25.** **Deux modèles acceptables** si un seul **responsable** d’écran, un routeur **lisible**, et un repli unique. Disqualifiant si double publication contradictoire ou double maintenance sans propriétaire.

**26.** **L’équipe prévi / le service**, jamais « le routeur ». Le système doit journaliser *quel modèle a parlé* pour le debrief.

**27.** **Oui, s’y attendre** : peu de jours feu → spécialiste **sous-appris** ou sur-spécialisé ; le généraliste + contexte feu gagne souvent. Ton 14,70 vs 13,32 est un **signal d’alarme design**, pas une surprise métier.

**28.** **Garde-fou / mode dégradé** d’abord (brut, expertise, pas de correctif agressif). Second modèle seulement si le garde-fou ne suffit pas **et** que les jours feu sont assez nombreux pour apprendre.

**29.** Oui, de façon **plus ou moins explicite** : « on ne sur-corrige pas », expertise renforcée, parfois ignore un produit. Peu formalisé en API — formaliser serait déjà un apport.

**30.** **Haute valeur** s’il est rare et **daté** (« incertitude élevée, on s’en tient au brut + mesures »). Dérobade s’il s’excuse tous les lundis.

**31.** Pas un +0,3 µg : un changement sur **décisions d’épisode** (quelques jours/an bien pris) ou une baisse claire des **miss médiatiques**. Sinon complexité injustifiable.

**32.** Plus large : **importé / non local** (feux, sable, panache) — une famille de modes dégradés. « Feu only » trop étroit pour le coût d’un second modèle.

**33.** « Un correctif pour le régime habituel, et un **mode prudence** quand l’import ou le feu domine — plutôt que deux cerveaux qui se battent. »

---

## D. Modèles de fondation (34–42)

**34.** Encore **curiosité / veille** pour la plupart des prévi AASQA ; un peu plus chez profils études. Pas l’outil du matin.

**35.** **Pas demain en sortie réglementaire pure.** En entrée **expérimentale** ou feature météo : peut-être, sous contrôle.

**36.** Les quatre : **traçabilité, validation multi-années, responsabilité, habitude** — dans cet ordre selon interlocuteur. La com’ « black box » bloque autant que le RMSE.

**37.** **Oui, ça aide** (support ECMWF, continuité) mais ne suffit pas : il faut la perf **sur *leurs* grandeurs et stations**.

**38.** Il ne « croit » pas un communiqué 74 %. Il demande : **max 8 h O₃ / PM jour, mon territoire, mon réseau, hors période train, vs PREV’AIR/CAMS, jours d’épisode.**

**39.** Ça changerait la **veille nationale** avant le **mandat local**. Une AASQA ne swap pas CAMS seule ; elle peut **exploiter un meilleur forçage** si la chaîne amont l’adopte.

**40.** Les deux : **intéresse** (culture technique à jour) si cadré ; **inquiète** si tu sembles vouloir reconstruire PREV’AIR tout seul.

**41.** Oui si c’est le **pitch central**. Non si c’est une **piste instrumentée** (AWS, plages, plafond mesurable) après le solide ops.

**42.** « Je sais **ingérer et évaluer** des forçages météo/composition modernes au même protocole que CAMS — pas “j’ai remplacé l’ECMWF”. »

---

## E. Priorités et pièges (43–50)

**43.** **Météo prévue (IFS)** — le levier le plus transverse pour l’erreur de régime et le lien au plafond ERA5 déjà chiffré.  
Ensuite **ensemble comme méfiance** (pas comme super-MOS).  
**Feux** : fort les jours J, faible le reste — prioritaire seulement en couche légère (GFAS).

**44.** **Fondations / AIFS-Aurora** impressionnent le recruteur tech ; changent peu le mardi sans chaîne. **Ne pas écarter** : une slide « capacité d’évaluation », pas le cœur du dossier.

**45.** **Déjà largement connu** : dépassements NO₂ horaires réglementaires sont **rares** hors trafic/canyon ; un prévi ne s’attend pas à un POD miracle au 8 km. Ton chiffrage 270/161k est une **confirmation utile**, pas une révélation.

**46.** **Oui, c’est la bonne langue** — mieux que le seul RMSE. Dis « à budget de FA fixé, ×3,6 rappels » : ça parle arbitrage. Ajoute **quel budget tu as calé** et sur quelle fenêtre.

**47.** [jugement] Ordre de grandeur mental souvent **plus près de 20–40 %** sur les jours où on « joue » le seuil en internal, pas 10 % puriste ; en com’ publique on vise **beaucoup moins**. 30 % comme point de courbe est **audible** ; le vrai budget est **politique et saisonnier**, pas un hyperparamètre unique.

**48.** **Assez pour ouvrir la porte**, pas pour clore. Trois matinées = preuve de **méthode** ; une saison = preuve de **service**. Annonce les trois + le protocole d’extension.

**49.** **Travail pour rien (ou presque) si mal cadré :**  
- second modèle « spécialiste anormales/feux » sans assez de jours ;  
- collection d’ensemble pour **repondérer en silence** sans pastille méfiance ;  
- 168 Go d’IFS/AIFS sans **un** tableau leave-station sur grandeur réglementaire ;  
- tout NO₂ « détection de dépassement » au grain actuel comme promesse de service.

**50.** Tu n’as pas assez posé : **« Qui opère la bascule de source (GFAS, membre manquant, AIFS) à 03 h du matin, et quel est le mode si la source est absente ? »** — c’est le prix réel de chaque nouvelle donnée.

---

## Synthèse décisionnelle

| Piste | Mardi matin | Coût ops | Verdict |
|-------|-------------|----------|---------|
| Ensemble (6 membres) | Pastille **désaccord → prudence** | Moyen (trou nov., 6/11) | Oui en **méfiance**, non en usine à pondération |
| GFAS feux | Contexte PM / mode prudence | Faible si flux stable post-migration | Oui **couche légère** |
| IFS météo prévue | Correctif / régimes | Élevé à digérer, fort levier | **Priorité mesure** |
| AIFS/Aurora | Veille | Élevé | Compétence d’**évaluation**, pas cœur produit |
| Dual modèle feu | Risqué | Élevé | **Non** en premier — garde-fou d’abord |

**Une ligne pour le directeur technique :**  
*On n’achète pas trois nouvelles usines ; on achète une météo d’émission, une pastille d’accord d’ensemble, et un drapeau feu — le reste reste en labo jusqu’à ce qu’un mardi soit meilleur.*
