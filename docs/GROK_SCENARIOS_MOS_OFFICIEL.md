# Scénarios A–E — Que conclure sur le MOS officiel CAMS ?

*Relecture Grok 4.5 · 30/07/2026. Jugement de cadrage, pas recalcul.*

---

## Rappel des faits (tels que déclarés — à geler avant tout claim)

| | CAMS brut | MOS officiel `optimised-at-observation-sites` | Nous |
|--|-----------|-----------------------------------------------|------|
| O₃ horaire, FR 2024 | 17,30 | 14,43 (**+16,6 %**) | 13,55 (**+21,7 %**) |
| O₃ **max 8 h** (réglementaire) | 12,08 | 11,85 (**+2,0 %**) | 9,49 (**+21,5 %**) |
| O₃ max 8 h **été** | — | **sous le brut** (ex. juil. 14,05 vs 11,47) ; POD 0,374 → **0,122** | — |
| NO₂, **janvier**, grandeur rég. = **max horaire** | — | **+30,8 %** sur *sa* grandeur | (indice contrariant) |

**Mécanisme candidat :** corriger l’horaire lisse la série → un **maximum** (ou max de moyenne glissante) de série lissée s’affaiblit. Apprendre directement la grandeur réglementaire récupère une partie du gain (+5,8 pts mesurés à part sur la cible).

**Réserves structurelles (tous scénarios) :** une année (2024) · un pays · modèle « nous » qui a vu 2024 · produit officiel dont le contrat d’usage n’est pas le tien.

---

## Grille de lecture avant les scénarios

Deux confusions tuent le dossier plus vite qu’un mauvais RMSE :

1. **Confondre grain et grandeur.** Un MOS *horaire* peut être excellent sur l’heure et médiocre sur le max 8 h sans « être faux ». Ce n’est une attaque que si *toi* ou *ton service* l’utilisez comme proxy réglementaire sans le re-scorer.
2. **Confondre mécanisme et universalité.** « Le lissage nuit aux maxima » peut être vrai **et** ne se voir clairement que quand le signal utile *est* un pic (O₃ été), pas quand la grandeur réglementaire *est déjà* un max horaire (NO₂).

Le NO₂ janvier n’est pas un détail gênant à glisser sous le tapis : c’est le **premier test de falsification** de la thèse A. Un max horaire est aligné sur le grain du correctif ; un max 8 h d’ozone est un **agrégat non linéaire** d’une bosse diurne. Si le MOS gagne fort sur le premier et s’effondre sur le second, tu n’as pas « un bug Copernicus » — tu as une **carte d’adéquation grain ↔ usage**.

---

## Scénario A — L’effet vaut pour les trois polluants

**Ce que ça signifierait.** Sur NO₂ et PM, le passage horaire → grandeur réglementaire (max horaire, max jour, percentile…) ferait aussi s’évaporer l’essentiel du gain horaire du MOS officiel — même famille d’écart qu’O₃ +16 % → +2 %.

### Tu peux conclure honnêtement
- Le post-traitement public **optimisé à l’heure** ne se comporte pas comme un correctif « prêt pour le réglementaire » : il faut **re-scorer chaque grandeur d’usage**.
- Propriété plausible d’une large classe de MOS horaires (régression vers la moyenne locale / lissage), pas seulement d’un run 2024 ozone.
- Légitime d’en faire un **principe d’acceptance** : tout produit « optimised at stations » est audité sur *tes* grandeurs, pas sur le grain vendeur.

### Tu dois te retenir d’écrire
- « Copernicus / l’ECMWF livre un produit défectueux. »
- « Le MOS officiel est inutile » (il peut rester excellent pour biais horaire, cartographie, usages non-max).
- « Tout post-traitement appris est condamné sur les maxima » (contredit par *ton* +21,5 % sur cible adaptée).
- Une généralisation Europe / tous les millésimes sans les avoir mesurés.

### Phrase de dossier (si A confirmé)
> Sur trois polluants, le gain du correctif public horaire ne se transporte pas aux grandeurs réglementaires que nous publions — d’où l’intérêt d’apprendre la grandeur d’usage, pas seulement l’heure.

### Ce qui doit être vrai avant d’oser A
NO₂ **et** PM, **même protocole** FR, année(s) figée(s), grandeurs réglementaires **nommées**, et idéalement un hold-out temporel. Le +30,8 % NO₂ janvier, s’il se maintient sur l’année et sur le max réglementaire réel, **tue A** — tu redescendrais en B/C.

---

## Scénario B — L’effet ne vaut que pour l’ozone (cas particulier)

**Ce que ça signifierait.** O₃ max 8 h : gain MOS officiel ~nul ou faible, été dégradant. NO₂/PM : le MOS officiel **garde** un gain substantiel sur *leurs* grandeurs réglementaires (comme le +30,8 % NO₂ le suggère déjà en janvier).

### Tu peux conclure honnêtement
- **Inadéquation spécifique** : correctif horaire × **max 8 h d’ozone** (pic photochimique, forte amplitude diurne).
- Le mécanisme « lisser l’heure → affaiblir le max de moyenne glissante » est **sélectif**, pas universel — et c’est plus crédible scientifiquement qu’un A forcé.
- Ton apport se lit : *pour l’ozone réglementaire, la cible compte autant que l’architecture*.

### Tu dois te retenir d’écrire
- Tout titre qui dit « le post-traitement CAMS » sans dire **ozone / max 8 h**.
- « Les grandeurs réglementaires » au pluriel fourre-tout.
- Cacher le NO₂ : le contre-exemple **renforce** B s’il est assumé (« là où la grandeur = max horaire, leur produit porte son gain »).

### Phrase de dossier (si B)
> Sur l’ozone, le correctif public horaire garde un gain à l’heure (+16 %) mais presque plus sur le max 8 h (+2 %), et passe sous le brut en été. Sur le NO₂, où la grandeur réglementaire est un max horaire, le même produit garde un gain élevé — l’enjeu n’est pas « le MOS », c’est l’alignement grain / grandeur.

### Piège B
Transformer B en A par paresse de slide. Ou l’inverse : minimiser O₃ parce que « ce n’est qu’un polluant » alors que c’est **le** polluant d’été en Occitanie.

---

## Scénario C — L’effet ne vaut que pour l’ozone **estival** (encore plus étroit)

**Ce que ça signifierait.** Le bilan annuel max 8 h du MOS officiel est mediocre **parce que** l’été tire tout vers le bas ; hors saison, le MOS peut rester neutre ou utile sur le max 8 h. Le scandale opérationnel est un **problème de saison de pic**, pas un bilan 12 mois homogène.

### Tu peux conclure honnêtement
- En période où l’on se sert vraiment du max 8 h pour l’**arbitrage d’épisode**, s’appuyer sur le MOS horaire agrégé peut **dégrader** le brut (POD qui s’écroule).
- C’est le scénario le plus **aligné service prévi** : moins de thèse générale, plus de « ne pas faire confiance à ce proxy en juillet ».
- Ton modèle / ta cible journalière se vendent comme **outil de saison sensible**, pas comme remplacement annuel du catalogue Copernicus.

### Tu dois te retenir d’écrire
- Le +2 % annuel comme si c’était une propriété plate (il masque une hétérogénéité pire).
- « Propriété du post-traitement horaire » (trop large — tu es en sous-cas de B).
- Une courbe d’apprentissage ou un claim leave-station portés uniquement par l’été sans le dire.

### Phrase de dossier (si C)
> Le correctif public horaire n’est pas « faible sur l’ozone » en abstrait : c’est en saison de pic que son max 8 h passe sous le brut et que le POD s’effondre. C’est exactement la fenêtre où un service publie.

### Piège C
Paradoxalement le plus **utile** pour un recruteur ATMO et le plus **facile à sous-vendre** (« ce n’est que l’été »). Ne pas laisser un relecteur académique te convaincre que C est trop petit : pour l’ops, C *est* le cœur.

---

## Scénario D — Le hold-out 2025 **réduit** l’effet sans l’annuler

**Ce que ça signifierait.** Même protocole en 2025 (modèle non entraîné sur 2025, MOS officiel selon ses règles ops) : l’écart MOS officiel vs brut sur max 8 h O₃ reste dans le même *sens* mais plus petit ; ton avance aussi peut maigrir.

### Tu peux conclure honnêtement
- Phénomène **reproductible en direction**, magnitude **année-dépendante**.
- 2024 reste une observation forte, plus un **titre absolu**.
- Le mécanisme reste admissible ; la communication doit **vieillir avec les chiffres**.

### Tu dois te retenir d’écrire
- Les pourcentages 2024 en accroche sans millésime ni « confirmé en signe en 2025, atténué en ampleur ».
- « Donc le message ne change pas » (si, le **corps du message** maigrit).
- Blâmer 2025 (« année facile pour CAMS ») sans le montrer.

### Phrase de dossier (si D)
> En 2024, le gain du MOS public s’effondre du pas horaire au max 8 h ; en 2025 hold-out, le même schéma apparaît, plus modéré. On publie les deux années.

### Piège D — le plus dangereux psychologiquement
Voir section « Rationalisations » : D est le scénario où l’honnêteté meurt par **note de bas de page**.

---

## Scénario E — Le hold-out 2025 **annule ou inverse** l’effet

**Ce que ça signifierait.** En 2025, le MOS officiel redevient compétitif ou supérieur sur max 8 h O₃ ; ou ton +21,5 % s’écroule ; ou l’été 2025 ne reproduit pas la dégradation.

### Tu peux conclure honnêtement
- Le contraste spectaculaire était **contingent** (année, version CAMS, entraînement, jointure).
- Le mécanisme lissage → max reste une **hypothèse de travail**, utile pour *designer* une cible, insuffisante pour *accuser* un produit.
- Le dossier solide redevient : leave-station, abstention (26/07), cible réglementaire, filet — **sans** pilier ECMWF.

### Tu dois te retenir d’écrire
- Toute accroche vs-MOS-officiel en noir dans la candidature du 22/08.
- « On a montré que le produit public échoue au réglementaire. »
- Les rationalisations E (ci-dessous) : année bizarre, setup déloyal, « le mécanisme suffit ».

### Phrase de dossier (si E)
> Une comparaison 2024 au produit public horaire suggérait une inadéquation au max 8 h ; non confirmée en hold-out 2025. On conserve l’exigence de scorer la grandeur d’usage ; on ne conserve pas le claim contre ce produit.

### Ce que E ne t’enlève pas
L’idée d’**apprendre la grandeur réglementaire** et la règle d’abstention peuvent rester valides **sur tes propres bases** — seulement, tu ne les accroches plus au scalp du MOS Copernicus.

---

## Question 1 — Scénario le plus probable

### Verdict : **B avec forte composante C** (probablement le duo dominant)

| Rang | Scénario | Pourquoi |
|------|----------|----------|
| 1 | **B + C** | Le NO₂ max horaire **aligne** grain et grandeur → un gros gain MOS n’y est pas paradoxal. L’O₃ max 8 h est un agrégat de bosse diurne → le lissage y fait le plus mal, **surtout en été**. |
| 2 | **D** | Une seule année + upgrades CAMS + météo : la magnitude bougera ; le signe peut tenir. |
| 3 | **A** | Exigerait que PM/NO₂ réglementaires se comportent comme l’O₃ max 8 h — le premier indice NO₂ va **contre**. |
| 4 | **E** | Possible (2024 vu par toi, ruptures, surinterprétation) mais le mécanisme n’est pas absurde au point de devoir s’inverser net. |

**Lecture fine :** tu n’auras probablement pas un A propre ni un C « hiver parfait / été seul catastrophe » au millimètre. Tu auras un **gradient** : effet maximal O₃ été max 8 h, effet faible ou nul sur grandeurs déjà horaires, magnitude sensible à l’année (D).

**Conséquence immédiate pour les trois semaines :** ne pas investir la com’ comme si A était vrai ; **mesurer** NO₂/PM réglementaires sur l’année (pas un mois) et l’été O₃ à part ; **hold-out 2025** avant tout titre.

---

## Question 2 — Où tu seras le plus tenté de te sur-vendre

### Verdict : **D**, avec une variante toxique en **E précoce**

Ce n’est pas A (trop gros, le NO₂ te retient). Ce n’est pas C (trop « petit », tu auras plutôt peur de sous-vendre). C’est **D** : les chiffres bougent un peu, le ego veut que le **récit** reste entier.

---

## Rationalisations à tuer *avant* qu’elles n’arrivent

Une fois écrites ici, elles doivent te paraître bêtes à relire le jour J.

### R1 — La favorite sous D (la plus dangereuse)
> « L’effet diminue en 2025, mais le *mécanisme* est toujours vrai — donc le message candidature ne change pas. Je garde le +2 % et l’été 2024 en gros ; 2025 va en note. »

**Pourquoi c’est faux.** Un mécanisme sans magnitude stable n’autorise pas la même phrase d’accroche. Le titre doit **maigrir avec le chiffre**. Le mécanisme guide le *design* (cible max, re-score) ; il ne sauve pas un claim chiffré 2024.

### R2 — Sous D, variante « moyenne »
> « Je moyenne 2024 et 2025 pour un chiffre unique plus presentable. »

**Pourquoi c’est faux.** Tu effaces la fragilité que le hold-out était censé révéler. Deux années, deux lignes.

### R3 — Sous E (ou D sévère)
> « 2025 est une année bizarre / CAMS a changé / mon modèle est désavantagé / le test est trop court — le vrai résultat reste 2024. »

**Pourquoi c’est faux.** Le hold-out n’existe que pour pouvoir te contredire. Le disqualifier parce qu’il te contredit, c’est inventer la réplication jusqu’à ce qu’elle applaudisse.

### R4 — Sous B, pour récupérer un A rhétorique
> « Le NO₂ +30 % c’est janvier seulement, ça ne compte pas — sur l’essentiel (l’esprit du truc) c’est général. »

**Pourquoi c’est faux.** Un contre-exemple sur la grandeur alignée est pile ce que la thèse du lissage **prédit**. L’ignorer c’est refuser la falsification.

### R5 — Sous C, pour gonfler
> « Si ça casse en été, ça casse pour l’ozone, donc pour la réglementation, donc le produit est inadapté au réglementaire *en général*. »

**Pourquoi c’est faux.** Tu empiles les généralisations (saison → polluant → catalogue). Un recruteur entend l’empilement.

### R6 — La sociale (tous scénarios)
> « Si j’adoucis le claim, le dossier redevient un ML parmi d’autres et je perds l’entretien. »

**Pourquoi c’est faux.** Ce qui t’ouvre l’entretien ATMO, ce n’est pas humilier un produit ECMWF — c’est montrer que tu **scores ce qu’ils publient** et que tu as un filet quand le correctif nuit. Un claim juste étroit bat un scoop large fragile.

---

## Matrice express : conclure / taire

| Si les mesures disent… | Claim max honnête | Claim interdit |
|------------------------|-------------------|----------------|
| **A** | Re-scorer tout MOS horaire sur grandeurs d’usage (3 polluants) | « Produit Copernicus défectueux » |
| **B** | Inadéquation O₃ max 8 h ; NO₂ comme contraste | « Les grandeurs réglementaires » sans dire O₃ |
| **C** | En saison de pic, MOS horaire agrégé peut battre le brut à l’envers | Propriété annuelle / tous polluants |
| **D** | Sens stable, ampleur année-dépendante ; deux millésimes affichés | Accroche 2024 seule comme vérité |
| **E** | Exigence de grandeur d’usage **sans** scalp du MOS officiel | Tout titre vs-produit public |

---

## Une seule discipline jusqu’au 22/08

1. **Mesurer** ce qui tranche A vs B vs C (NO₂/PM année + O₃ par saison) avant d’écrire le nom du scénario.  
2. **Hold-out 2025** avant le noir sur blanc.  
3. Le jour où D ou E arrive, relire **R1–R3** à voix haute — si la phrase que tu t’apprêtes à mettre en slide ressemble à R1, tu la rayes.

**Phrase à se coller au-dessus de l’écran :**  
> Le scénario le plus probable est étroit (B/C). Le scénario le plus tentant à tricher est D. Je ne laisserai pas un mécanisme vrai porter un chiffre qui a maigri.
