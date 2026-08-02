# GROK R5 — 50 verdicts courts (30 juillet 2026)

Prompt : `docs/PROMPT_GROK_R5.md`. **[vu]** / **[publié]** / **[jugement]**. Chiffres du prompt candidature — non recalculés ici.

**Correction R4 intégrée.** La coupe « train 2023-2024 / test 2025 calendaire » est **infaisable** : obs jusqu'au **31/12/2024** seulement ; couverture réelle **17 mois** (2023-08 → 2024-12). Protocole temporel opposable = **glissant / leave-month / train antérieur → test mois tenus hors**, jamais une année 2025 sans mesures.

---

## Bloc 1 — Ce que j'ai le droit d'affirmer (Q1–Q10)

**1.** **Non** en l'état. **[jugement]** CAMS Europe 0,1° ≠ chaîne ATMO (PREV'AIR/CHIMERE ~km + expertise). Dis : « correction apprise d'un forçage européen, utile en amont d'une chaîne locale » — pas « même nature ».

**2.** **Normal-bas, pas suspect.** **[jugement]** Riccio leave-station ~+30 % ; ton +19 % avec double aveugle fragile et queue négative est cohérent, pas un miracle à cacher.

**3.** **Oui pour « solide sur l'espace testé », non pour « démontrée universellement ».** **[jugement]** 3 plis + σ 1,2 suffisent à une phrase d'entretien si tu nommes le schéma de plis ; pas à « prouvé France entière ».

**4.** **Les deux chiffres ensemble, ou rien.** **[jugement]** Devant un ingénieur, +14,4 % sans le −14,6 % = mensonge par omission ; avec les deux = maturité. Le moyen seul s'annule ; le couple convainc.

**5.** **Présentable comme limite structurante, pas comme détail.** **[jugement]** Disqualifie l'usage « alerte ozone pure » ; ne disqualifie pas le post-traitement RMSE/FAR si tu recentres le service rendu.

**6.** **Le plus fort levier feature clairement isolé ; le résultat le plus fort du dossier est ailleurs.** **[jugement]** +13 % trafic sur NO₂ = meilleur *ablation*. Le plus fort *système* reste LightGBM O₃ +19,4 % leave-station + échelle des baselines.

**7.** **Créditibilise.** **[jugement]** +7,3 % sans ML = plancher honnête ; +19,4 % = surplus d'apprentissage réel, pas magie.

**8.** **Assumer en une ligne, pas mettre en avant comme trophée.** **[jugement]** « POD O₃ stable/↓, FAR↓ » = trade-off classique ; le cacher tue la confiance ; en faire le héros du pitch non plus.

**9.** **Non comme pivot unique ; oui comme preuve de service.** **[jugement]** L'Occitanie recrute encore beaucoup sur l'ozone estival. PM2.5 = meilleur POD/FAR ; O₃ = enjeu local. Récit bi-polluant hiérarchisé, pas recentrage total.

**10.** **Toute formulation « généralisation temporelle démontrée » (héritage 29/07 / R3).** **[jugement]** Contredite par pire pli −14,6 % et double aveugle −24,9 %. Retirer aussi l'équivalence opérationnelle ATMO si elle traîne.

---

## Bloc 2 — Angles morts (Q11–Q20)

**11.** **Optimisme de protocole + attribution du gain aux upgrades CAMS non séparée.** **[jugement]** Tu choisis encore en regardant la val ; et fin 2024 le gain « explose » pile sur les ruptures — tu risques de vendre un artefact d'usine comme talent du modèle.

**12.** **Ça détruit l'attribution causale du +19 %, pas forcément l'utilité locale.** **[jugement]** Si le surplus vient d'un CAMS devenu plus biaisé, tu montres « je corrige une régression du forçage », pas « j'ai appris la chimie ». La promesse leave-station reste ; le récit « gain structurel durable » tombe.

**13.** **Stratifier le gain mensuel leave-station : nov–déc 2024 vs nov–déc 2023, et fenêtres ±14 j autour du 13/11 et 03/12/2024.** **[jugement]** Une heure : tableau mois × gain, sans retune. Si l'anomalie est localisée aux ruptures, flaguer ces mois hors score « nominal ».

**14.** **~0,3–0,8 µg/m³ RMSE d'optimisme, rarement >1 si leave-station figé.** **[jugement]** Ordre de grandeur praticien après beaucoup de regards val ; pas une mesure. Au-delà de 1 point, ton protocole fuit.

**15.** **Bon pour le score, mauvais comme seule intelligence.** **[jugement]** Calendrier +9,1 % = saisonnalité/biais de régime captés — légitime. Mauvais signe seulement si c'est le *seul* levier et que leave-month s'effondre sans lui.

**16.** **Résultat réel plausible (colinéarité / double comptage du résidu spatial).** **[jugement]** Terrain et krigeage du résidu expliquent la même erreur spatiale ; les empiler sur-ajuste. Refaire une fois hors sample ; si ça se reproduit, c'est un vrai enseignement « ou l'un ou l'autre ».

**17.** **Variables nuisibles / redondantes, pas seulement bruit.** **[jugement]** +1 % en retirant la forêt de façon stable = signal d'ablation. Si ça oscille selon le pli → bruit.

**18.** **Oui, biais bas non nul probable, surtout NO₂/PM bas.** **[jugement]** Mesure manquante typique : erreur conditionnelle sur y_hat≈0, fraction écrêtée, impact sur biais et sur classes basses. Une heure de stats descriptives.

**19.** **Insuffisants seuls — bloquer le temps (ou clusters jour/épisode).** **[jugement]** Bootstrap station ignore la corrélation temporelle des erreurs → IC trop étroits. Block bootstrap temporel ou par épisode.

**20.** **Fuite (split, features futures, agrégats fit sur tout T) et reproductibilité du score.** **[jugement]** Ensuite : une commande qui régénère le tableau leave-station ; pas la beauté du notebook.

---

## Bloc 3 — Points restants (Q21–Q30)

**21.** **+1 à +3 points de % RMSE possibles, parfois plus sur biais court terme ; pas 10.** **[jugement]** Obs récentes = autoforçage / persistance d'erreur. Plafond bas si CAMS porte déjà l'essentiel de la dynamique.

**22.** **Oui si tu deviens « maintenantcasteur déguisé » ; non si J+1 reste évalué sans fuite d'obs du jour cible.** **[jugement]** Encadrer : features ≤ t0 de prévision, horizon respecté. Sinon la promesse candidature change.

**23.** **~2–5 % relatif typique, pas 15 %.** **[jugement]** Tes trois boosters tiennent en 0,3 pt : l'espace est plat. 15 % = rêve ou protocole cassé.

**24.** **`num_leaves` / profondeur effective et taux d'apprentissage (avec `n_estimators` en binôme).** **[jugement]** Puis régularisation (`min_child_samples`, `lambda`). Le reste est de second ordre ici.

**25.** **Oui comme feature d'incertitude / gating, pas comme monstre de RMSE moyen.** **[jugement]** Utile pour confiances et extrêmes ; gain RMSE global souvent faible.

**26.** **Utile en principe, circulaire si mal raconté.** **[jugement]** NO₂/PM CAMS portent précurseurs et régimes ; OK en leave-station. Interdit de prétendre « mesure » ; attention fuite si copolluant observé du même instant.

**27.** **Réel surtout pour PM/NO₂ asymétriques et queues ; cosmétique sur O₃ estival déjà quasi-symétrique.** **[jugement]** Tester pinball / Huber avant log systématique.

**28.** **Payant seulement si régimes ont assez d'effectif queue ; sinon fragmentation.** **[jugement]** Vu tes gains queue négatifs par régime, un modèle global + poids ou perte asymétrique bat souvent 4 petits modèles.

**29.** **Non — arrêter les courses d'architectures.** **[jugement]** 0,3 pt = bruit de protocole. Temps → protocole temporel honnête, queue, ruptures CAMS.

**30.** **Mesure « gain vs ruptures CAMS » + un leave-month strict sur 17 mois + une perte asymétrique figée.** **[jugement]** Pas d'archi, pas d'indice EPCI.

---

## Bloc 4 — Extrêmes (Q31–Q37)

**31.** **Déséquilibre + perte L2 sur résidu (régression vers la moyenne) en premier ; écrêtage secondaire.** **[jugement]** La cible résiduelle aggrave si CAMS sous-estime déjà les pics : tu apprends un correctif moyen. Diagnostiquer : résidu vs y_CAMS sur décile haut.

**32.** **Oui pour le service alerte ; pas pour le RMSE.** **[jugement]** POD/CSI/FAR se pilotent mieux en proba de dépassement (et calibration) qu'en seuil post-hoc sur µg/m³.

**33.** **Pas magique : multi-objectif (RMSE + pinball haut) ou deux têtes (espérance + queue) avec choix à l'usage.** **[jugement]** Tu déplaces encore le compromis, mais tu le rends **explicite** et domines le « un seul seuil de pondération caché ».

**34.** **Pas de ratio universel publié unique — ordre de grandeur opérationnel souvent plusieurs FA pour 1 miss, variable selon polluant et communication préfectorale.** **[jugement]** **[publié]** le guide LCSQA impose POD/FAR/SR/FB/CSI et règles de couples ; le coût relatif FA/miss est **politique locale**, pas une constante. Ne invente pas « 1 miss = 5 FA ».

**35.** **Moyen-faible pour un usage alerte, honnête pour un premier MOS.** **[jugement]** CSI 0,317 = mieux que le hasard bas-prévalence, loin d'un système d'alerte seul. Présenter vs CAMS brut sur la même cible, pas en absolu glorieux.

**36.** **Oui si collé à CAMS (~0,24) et aux limites queue ; non comme promesse terrain.** **[jugement]** « +près du double du brut, encore insuffisant pour remplacer l'expertise » = indémontable. « On détecte la moitié des mauvais jours » seul = démonté.

**37.** **PM2.5 : biais d'émission/transport plus stationnaire et seuils mieux alignés ; O₃ : non-linéaire, pics météo-dépendants, résidu moyen qui sous-corrige la queue.** **[jugement]**

---

## Bloc 5 — Récit et entretien (Q38–Q44)

**38.** **« Je corrige CAMS aux stations sur 17 mois, leave-station, en nommant où ça généralise (espace) et où ça casse (temps, queue ozone). »** **[jugement]**

**39.** **(a) Protocole temporel exact sans 2025 obs — quel test ? (b) Part du gain due aux upgrades CAMS nov–déc 2024 ? (c) Que faites-vous le jour où POD O₃ baisse et le préfet appelle ?** **[jugement]**

**40.** **Cadre : hypothèse → test → échec borné → décision d'usage.** **[jugement]** « La queue O₃ −3 % vs brut m'interdit l'alerte auto ; ça oriente le produit vers aide à l'expertise + FAR↓, pas remplacement. »

**41.** **Montrer l'échelle complète — c'est ce qui crédibilise.** **[jugement]** Sans débiaisage, +19 % sent le cherry-pick d'archi.

**42.** **Parler FAIRMODE/MQI seulement si chiffres collés au guide et tableaux v4 ; sinon te faire reprendre.** **[jugement]** Une slide « conforme aux indicateurs LCSQA POD/FAR/CSI » > dissertation MQI approximative.

**43.** **Pas assez opérationnel (le plus grand risque).** **[jugement]** Trop technique se pardonne si une phrase d'usage existe ; trop honnête est un atout ATMO ; l'absence de « le matin, sur quel écran, quelle décision » tue.

**44.** **« Sur une prévision de demain en Occitanie, qu'est-ce qui change concrètement à l'écran — et qu'est-ce que vous ne signeez pas ? »** **[jugement]**

---

## Bloc 6 — Actualité (Q45–Q48)

**45.** **[vu]** (atmo-occitanie.org/episodes-pollution, consulté 30/07/2026) :
- **O₃** : 08/07 information puis **09/07 alerte** — 30, 31, 34, 65.
- **PM10 feux 66** : 06–07/07 (information → alerte), incendie Pyrénées-Orientales.
- **PM10** 13–14/07 (66 alerte + plusieurs dép. information).
- **PM10** 25/07 : **constaté a posteriori** (46, 12) — signal fort de **sous-anticipation**.
- **PM10** 26–27/07 : multi-départements information/alerte (12, 30, 34, 46, 48, 81, 82…), communiqués évoquant incendies / maintien d'épisode.
- **[jugement]** « Mal anticipés » au sens strict documenté ici : surtout le **25/07 a posteriori** ; pour les autres, les pages disent surtout « prévoit » — pas de score officiel d'anticipation vérifié dans cette session. Juin : 24/06 PM10 saharien (09, 31, 65) hors juillet mais utile au récit.

**46.** **[vu]** LCSQA publications juillet 2026 : reco PMF/SoFi ACSM (27/07) ; CIL lévoglucosane (21/07) ; contrôle analyseurs PM vs référence (09/07). **[jugement]** Pour l'entretien ATMO : épisodes feux+O₃ ci-dessus + existence page performances prévisions LCSQA — pas les CIL labo sauf si poste mesures.

**47.** **[publié/vu]** CAMS global **IFS 50r1** déployé **12/05/2026** (O₃ dépôt sec, BVOC, émissions, assims) — [CAMS upgrade](https://atmosphere.copernicus.eu/cams-global-system-gets-upgrade). Assessment Report AQ Europe 2025 (29/06/2026). **[jugement]** Vérifier à part si le **régional ensemble** Europe a bougé sur ta fenêtre 2023–2024 (tes U7b/U8…) — le global 2026 ne change pas ton train historique mais change le récit « forçage vivant ».

**48.** **[jugement]** Rien de nouveau **vérifié** <6 mois dans cette session au-delà du papier Science (juin 2026) feux→O₃ (contexte mécanisme, pas MOS). **Ne pas inventer un DOI.** Garder Riccio 2024 / Bertrand 2023 comme ancres ; une veille Scholar la veille de l'envoi suffit.

---

## Bloc 7 — Trancher (Q49–Q50)

**49.** **Couper : spatialisation indice ATMO / comparaison EPCI / courses d'archi.** **[jugement]** Pourquoi celui-là : zéro obs 2025 + queue O₃ déjà disqualifiante pour l'indice « alerte » ; le temps doit aller au **protocole temporel vrai sur 17 mois** et à l'**audit ruptures CAMS**, seuls à protéger le droit d'affirmer.

**50.** **« Quel produit exact livres-tu le 22/08 — chiffre leave-month figé, ablation trafic NO₂, et phrase d'usage — avec quel split temporel opposable sans année 2025 ? »** **[jugement]** La question omise lie contrainte de données, livrable et récit ; les 49 autres tournent autour sans la figer.

---

## Recollement dépôt (avant livrable)

- [ ] Remplacer partout la reco R4 « test 2025 » par protocole 17 mois
- [ ] Afficher mois couverts min/max dans les données, pas via noms de fichiers
- [ ] Tableau gain × mois autour 13/11 et 03/12/2024
- [ ] Chiffres prompt (+19,4 %, queue −3,1 %, POD…) = rapports après gel du split
