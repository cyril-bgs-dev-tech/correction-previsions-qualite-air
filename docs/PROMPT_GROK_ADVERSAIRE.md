# Prompt Grok — jouer l'adversaire, pas le relecteur bienveillant

*À coller tel quel. Rédigé le 01/08/2026. Objectif : trouver ce qui ferait rejeter cette
candidature, pas ce qui la valide.*

---

## Ton rôle

Tu es **prévisionniste senior dans une AASQA** — association agréée de surveillance de la
qualité de l'air, l'équivalent français d'un service régional de qualité de l'air. Quinze ans
de métier. Tu reçois une candidature spontanée avec ce dossier technique. Tu n'as ni le temps
ni l'envie d'être gentil : tu cherches **la faille qui te fait passer au CV suivant**.

Trois consignes qui prévalent sur toute autre :

1. **Ne valide rien.** Si tu es d'accord avec un point, dis-le en une ligne et passe. Ton
   utilité est dans les désaccords.
2. **Cherche l'objection que le candidat n'a pas anticipée.** Il en a anticipé beaucoup — la
   liste est plus bas. Celles-là ne m'intéressent plus.
3. **Distingue « faux » de « mal présenté ».** Ce sont deux verdicts différents et le second
   se répare.

---

## Le contexte factuel

Les prévisions européennes **CAMS** de qualité de l'air sont produites sur une maille de 0,1°
(≈ 8 km), à J+1 à J+3. Le candidat a construit un post-traitement statistique : un modèle à
gradient boosté apprend l'**erreur** de CAMS (`observation − CAMS`) station par station, à
partir de variables disponibles à l'heure d'émission — calendrier, relief, réseau routier
hiérarchisé, paysage, membres d'ensemble, exposition aux feux, observation de l'avant-veille.

Validation : **stations entièrement exclues** de l'apprentissage, intervalles par bootstrap
de stations, plus un test hors fenêtre temporelle sur 2025.

### Les chiffres, après recalcul

Au grain réglementaire de chaque polluant, France 2024, contre le post-traitement officiel
que Copernicus publie (`cams-europe-air-quality-forecasts-optimised-at-observation-sites`) :

| polluant | grain | CAMS brut | MOS officiel | ce dossier |
|---|---|---|---|---|
| O₃ | max glissant 8 h | 12,45 | 11,93 (+4,1 %) | **9,53 (+23,4 %)** |
| NO₂ | max horaire | 15,47 | 12,16 (+21,4 %) | **10,44 (+32,5 %)** |
| PM2,5 | moyenne journalière | 4,17 | 3,43 (+17,6 %) | **2,91 (+30,1 %)** |

Aux conventions d'un rapport AASQA — stations de **fond** seules, disponibilité > 75 %, score
**par station puis moyenne non pondérée**, ozone limité à avril–septembre, échéance J0 (1-24 h) :

| polluant | n stations | CAMS brut | corrigé | gain |
|---|---|---|---|---|
| O₃ | 254 | 10,06 | 7,88 | +21,7 % |
| NO₂ | 217 | 15,46 | 10,10 | **+34,7 %** |
| PM2,5 | 156 | 3,94 | 2,77 | +29,6 % |

Sur les **150 stations urbaines de fond**, CAMS sous-estime le NO₂ de **−11,6 µg/m³** en biais
moyen ; la correction ramène ce biais à −0,5 et la corrélation de 0,59 à 0,75.

### L'affirmation la plus exposée

> Le post-traitement officiel de Copernicus **dégrade** la prévision brute d'ozone au grain
> réglementaire **huit mois sur douze**, et de **−19,6 %** sur la saison avril–septembre.
> Sa moyenne annuelle positive (+4,1 %) est la somme de −19,6 % en saison et +20,4 % hors
> saison.

L'explication avancée : le produit officiel apprend sur les **valeurs horaires**, alors que le
seuil réglementaire porte sur un **maximum**. Toute réduction de variabilité dégrade une
statistique d'ordre. Le candidat cite Bertrand et al. 2023 (ACP 23, 5317), qui sont les
auteurs du produit officiel et recommandent eux-mêmes la cible journalière.

---

## Ce que le candidat a DÉJÀ anticipé — inutile d'y revenir

Ne me redonne pas ces objections, elles sont dans le dossier avec leur mesure :

- **la méthode n'est pas nouvelle** — Bertrand et al. 2023 et PREV'AIR corrigent déjà par
  apprentissage ; le dossier cite et ne revendique pas ;
- **au seuil de procédure française (180 µg/m³ en max horaire), la méthode ne détecte rien** —
  32 dépassements sur 60 400 jours-station, 3 détectés par CAMS, 2 par la correction, zéro à
  J+3 ; un modèle entraîné directement sur ce grain fait pareil ;
- **les PM10 ne sont pas traités** — or 40 des 52 vigilances réellement déclarées par ATMO
  Occitanie entre 01/2025 et 03/2026 portent sur les PM10 ;
- **la validation était optimiste** — les plis de validation n'étaient pas bloqués
  spatialement (79 % des stations ont une voisine à moins de 10 km) ; en imposant 50 km de
  séparation, le gain ozone tombe de 28,6 % à **18,5 %** ;
- **23 % des stations NO₂ sont dégradées** par la correction, malgré un gain médian de +32 % ;
- **le meilleur levier (observation à J−2, +8,9 à +21,9 %) n'existe qu'aux stations
  instrumentées** et scinde le produit en deux périmètres ;
- **aucune comparaison contre PREV'AIR ni contre le modèle régional d'ATMO Occitanie** — le
  candidat compare à CAMS brut, que l'AASQA ne consomme pas telle quelle.

---

## Ce que je te demande

### 1. L'objection non anticipée

Quelle est la **première question** que tu poserais en entretien et à laquelle ce dossier
n'a pas de réponse ? Une seule, la plus dure. Dis pourquoi elle est fatale ou pas.

### 2. L'affirmation contre le produit officiel

Accuser un produit officiel de dégrader une prévision est risqué. Cherche une **explication
innocente** que le candidat aurait manquée :

- une différence de version, de cycle ou d'heure d'émission entre les deux sources comparées ;
- une différence de population de stations ou de règle de complétude ;
- un choix de conception documenté qui rendrait le comportement attendu plutôt que fautif ;
- un problème d'appariement temporel — fuseau, jour civil, décalage d'échéance.

Si tu n'en trouves pas, dis-le : c'est une information.

### 3. Le cadrage

Le candidat hésite entre deux présentations du **même travail** :

- **A** — « j'ai construit une correction qui gagne 23 à 35 % sur les prévisions CAMS » ;
- **B** — « j'ai évalué le post-traitement officiel dans les conventions du référentiel, montré
  qu'il dégrade la prévision huit mois sur douze en saison ozone, et mesuré ce qu'une
  correction peut et ne peut pas faire ».

L'argument pour **B** : l'article 13 de l'arrêté du 16 avril 2021 impose à chaque AASQA
d'évaluer annuellement ses outils de modélisation *et son expertise*. Le dossier démontrerait
donc le métier d'**évaluateur**, plus rare que celui de constructeur.

Lequel te ferait décrocher le téléphone ? Et si aucun, quel est le C ?

### 4. Le point mort du recrutement

Question la plus utile et la moins confortable : **une AASQA a-t-elle réellement besoin de
ça ?** Elle reçoit PREV'AIR, fait tourner son propre modèle régional, et son quotidien est
largement fait de mesure, de rapportage et d'expertise humaine. Si le vrai besoin est
ailleurs — spatialisation, capteurs bas coût, inventaire d'émissions, indice communal,
automatisation du rapportage — dis-le franchement, avec ce qui te le fait penser.

Utilise ta recherche en temps réel : offres d'emploi AASQA récentes, appels d'offres, rapports
d'activité, communications du LCSQA ou d'Atmo France sur leurs chantiers 2025-2026.

### 5. Ce qui manque et qui serait bon marché

Trois choses au maximum, réalisables en **moins de trois jours de calcul**, qui changeraient
le plus la valeur du dossier. Pas de « il faudrait plus de données ».

---

## Format de réponse

Six sections, dans cet ordre, sans préambule :

1. **L'objection fatale** — une, argumentée, avec un verdict : rédhibitoire / réparable /
   surmontable en entretien.
2. **Explication innocente du −19,6 %** — trouvée ou non trouvée, avec les sources.
3. **Cadrage** — A, B ou C, en trois lignes de justification maximum.
4. **Besoin réel d'une AASQA** — avec sources datées.
5. **Trois actions bon marché**, classées par rapport valeur/effort.
6. **Ce sur quoi tu n'as pas d'avis fiable** — sois explicite plutôt que d'inventer.

Sois direct. Les formules de politesse et les résumés de ce que je viens d'écrire coûtent de
la place et n'apportent rien.
