# R17 — ce que la ronde change, vérifié sur pièces

*Traitement de `docs/GPT_R17.md` le 08/08/2026. Chaque verdict de GPT a été confronté au
dépôt : ce fichier ne recopie pas la réponse, il dit ce qu'elle change ici, ce qu'elle
confirme, et ce sur quoi elle se trompe.*

---

> ✅ **APPLIQUÉ le 09/08/2026.** Les **sept** lignes du tableau de la page 06 sont
> réécrites selon le § ② ci-dessous, `injecter_pages.py` a recollé (658 → 660 ko, 7 pages),
> `render_check` rend **0 anomalie** sur les deux thèmes et `verifier_dossier_candidature`
> **20 vérifiés / 0 en écart**. La contradiction du § ① est levée : la page dit désormais
> « non utilisable pour déclencher une procédure », ce que la fiche indicateur dit déjà.
>
> **Un huitième défaut trouvé en chemin, hors périmètre R17.** Le schéma « un tronc, deux
> têtes » (page 03) livrait « stations classées **par risque du jour** » — le vocabulaire
> exact que le § ② reproche à la ligne ARS, à un endroit que R17 n'avait pas regardé.
> Corrigé en « par **rang de dépassement** », qui est aussi ce que le modèle produit
> réellement. Les trois autres emplois de « risque » sont techniques (« classement des jours
> à risque ») et restent. C'est la règle 4 bis : *la correction d'un motif se termine par la
> recherche du même motif ailleurs.*

## ① Le défaut central : le dossier se contredit sur la préfecture

C'est la trouvaille de la ronde, et elle est vérifiable en deux `grep`.

| pièce | ce qu'elle promet à la préfecture |
|---|---|
| `docs/FICHE_INDICATEUR_EPISODES.md` l. 163 | « déclencher ou lever une procédure — ⚠️ **rien directement** — voir limite ① » |
| `reports/figures/_p6_section.html` (page 06) | « la mesure de cette page, et **un volume d'alertes choisi plutôt que subi** » |

**Les deux ne peuvent pas être vraies.** Et c'est la fiche qui a raison : la mesure du
dossier est **2 procédures PM10 retrouvées sur 33**, sur un endpoint *station-jour* quand
la procédure réelle est *zone-jour, prévisionnelle et préfectorale*. R17 le formule sans
ménagement — « naïve et juridiquement mal cadrée » — et arrive à la même conclusion que
notre propre fiche, sans l'avoir lue.

**Action** : aligner la ligne « Préfecture » de la page 06 sur la fiche. Reformulation
retenue, tirée de R17 § 6 :

> « Banc d'essai exploratoire de dépassements aux stations ; **non utilisable pour
> déclencher une procédure**. Je sais spécifier les données qui manquent pour reconstruire
> l'endpoint officiel. »

---

## ② Les sept promesses — verdict et reformulation

| ligne actuelle de la page 06 | verdict R17 | ce qu'il faut écrire |
|---|---|---|
| Préfecture — « la mesure de cette page, et un volume d'alertes choisi » | naïve, mal cadrée juridiquement | banc exploratoire aux stations, **pas** un déclencheur ; savoir spécifier ce qui manque |
| ARS — « l'indice par commune et la liste des stations classée par risque du jour » | trop médicalisant : un indice n'est ni une dose ni un risque | message **populationnel** par zone, polluant, durée et incertitude, relié aux recommandations officielles |
| Toulouse · Montpellier — « le champ spatialisé régional » pour les scénarios ZFE | inadapté : 0,1° ne résout ni rue, ni axe, ni population exposée | le champ documente le **fond régional** ; une évaluation ZFE exige modèle urbain, trafic, parc et contrefactuel |
| Région et collectivités — « 102 pages autonomes » | solution avant besoin ; duplique logique, versions et maintenance | **requalifier** en démonstration d'industrialisation hors ligne ; proposer un composant réutilisable et un contrat d'indicateur |
| LCSQA · Ineris — « une évaluation indépendante de leur chaîne » | promet trop : sans même cycle ni mêmes données, ce n'est pas indépendant, c'est non comparable | **protocole reproductible d'évaluation locale**, résultats **non officiels**, avec versions et limites |
| Atmo Nouvelle-Aquitaine — SIREQAETE | périmètre crédible ; réserve de R17 **réfutée**, voir ④ | garder la ligne ; ajouter « après accord sur cycles, frontières, chimie, QA et responsabilités » |
| Partenaires sanitaires et agricoles — « rien » | honnête mais **trop passif** | « je peux formaliser le besoin, la provenance et les limites ; je ne crée ni indice sanitaire ni seuil sans autorité compétente » |

⚠️ **Ces éditions relèvent de la lane présentation**, pas de celle-ci — la répartition est
consignée dans la mémoire du projet. Elles sont donc spécifiées ici, pas appliquées.

---

## ③ Ce que R17 signale et qui est **déjà satisfait** — audité, pas supposé

R17 § 9 donne une liste de formulations qui « trahissent immédiatement » un candidat.
Passée au `grep` sur les cinq pièces que le recruteur lit (`NOTE`, `SOUTENANCE`, `LETTRE`,
`FICHE_INDICATEUR_EPISODES`, `VERITE_DOSSIER`) :

| formulation proscrite | occurrences |
|---|---:|
| « indice de risque sanitaire » | 0 |
| « station réglementaire » sans précision | 0 |
| « carte précise » / « précision de la carte » | 0 |
| « conformité européenne » / « conforme à la directive » | 0 |
| « pollution produite par la commune » | 0 |
| ZFE (hors page 06) | 0 |
| « déclench… » | **13, toutes correctes** |

Les treize occurrences distinguent toutes la **procédure préfectorale** du dépassement à
la station — c'est précisément la distinction que R17 exige. **Le § 9 ne trouve rien à
reprendre dans le corps du dossier** ; le seul défaut est la ligne de tableau du ①.

---

## ④ Ce sur quoi R17 se trompe — SIREQAETE

R17 § 6 écrit : « le terme SIREQAETE ne l'est pas [sourcé] dans une source primaire
retrouvée ». **C'est un échec de sa recherche, pas une faiblesse du dossier.**

Vérifié le 08/08/2026 sur la page d'Atmo Occitanie consacrée aux incendies de Gironde et
des Landes, qui porte le terme **verbatim** :

> « SIREQAETE (Système InterRégional d'Évaluation de la Qualité de l'Air Et des Territoires
> Exposés) »

La page le décrit explicitement comme une **plateforme de modélisation** née de la
collaboration Atmo Occitanie × Atmo Nouvelle-Aquitaine, permettant de **partager une
prévision quotidienne** construite sur données et expertise régionales. C'est une source
primaire : le site de l'AASQA elle-même.

**La ligne du tableau tient.** Ce qui reste non sourcé — et que la mémoire du projet
interdit déjà d'affirmer — c'est la technique de la plateforme : modèle, résolution, état
de production, lien avec SIRANE ou PREV'AIR. Aucun n'a pu être retracé.

---

## ⑤ Ce qui reste, par ordre de valeur

1. ✅ **FAIT le 09/08** — les sept lignes du tableau page 06 sont alignées, plus le schéma
   de la page 03. Voir l'encadré en tête de fichier.
2. **Décider du livrable § 7** : R17 recommande une **note de cadrage partenaire de deux
   pages** sur *Grand Montauban — suivi PCAET*, adossée à un rapport public de juillet 2025,
   avec la fiche indicateur existante en annexe technique. Aucun modèle nouveau, aucune
   carte nouvelle. **Décision à prendre : le faire ou l'écarter explicitement.**
3. **Matière d'entretien à retenir** (R17 § 2) : transposition de la directive 2024/2881 au
   **11 décembre 2026**, feuilles de route 2026-2029, décision 2026/1208 sur la modélisation
   au **30 juin 2028**, valeurs limites au **1ᵉʳ janvier 2030**. Et l'obligation de l'arrêté
   du 16 avril 2021 art. 13 : **évaluation annuelle des prévisions transmise avant le
   30 juin** — ce n'est pas un souhait de partenaire, c'est une obligation de l'AASQA.
4. **La question que R17 pose et que le dossier n'aborde pas** (§ 10) : *qui porte la
   responsabilité du produit après la livraison — décision, validation, publication,
   maintenance, correction, retrait ?* C'est une question de poste, pas de méthode.
