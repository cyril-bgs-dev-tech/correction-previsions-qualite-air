# GROK — 30 prochaines actions (valeur & usage AASQA)

*Prompt : `docs/PROMPT_GROK_30_ACTIONS.md` · 30/07/2026. Angle destinataire, pas protocole stats.*

---

## Cadrage — avant le tableau

**Le cadrage n’est pas mauvais ; il est encore à moitié academicien.**  
Tu as le bon objet métier (grain réglementaire, filet, vs produit public) et encore trop de livrables qui parlent comme un paper (RMSE leave-station, 9 figures à chiffres morts, Streamlit à 6 pages). Un recruteur ATMO n’embauche pas un +21 % : il embauche quelqu’un qui **réduit une mauvaise décision un mardi à 13 h**.

**Prémisse « ce projet vaut la peine » :** oui **pour un entretien et un CDD/stage exigeant**, pas encore comme preuve autonome d’un poste de prévisionniste titulaire. Ce qui manque n’est pas un polluant de plus — c’est une **trace d’usage** (rejeu d’astreinte, fiche validée, chiffres gelés sur la fenêtre réelle).

**Ne pas rouvrir** (déjà tranché dans le prompt) : archis, EPCI, drop des stations dures, grid search exhaustif. Les actions ci-dessous respectent ça.

---

## Les 30 actions (valeur décroissante)

| # | Action | Pour qui | Coût (h) | Ce qu’elle rend possible qui ne l’est pas aujourd’hui |
|---|--------|----------|----------|------------------------------------------------------|
| 1 | **Geler une « vérité dossier »** : un unique tableau (brut / MOS officiel / nous) sur O₃·NO₂·PM2,5 × grain horaire × grain réglementaire, FR 2024 + hold-out Occitanie 2025 S1 avec **seuils recalibrés** — et **interdire** toute slide d’utiliser un autre millésime. | Recruteur, jury, toi | 4–6 | Fin des chiffres 11 mois / 17 mois / 2024 qui se contredisent d’une page à l’autre ; dossier opposable en entretien. |
| 2 | **Réécrire les pages 1–3 de la présentation** autour d’un seul fil : *le grain décide* — trois barres max 8 h O₃ (brut / officiel / nous) + une phrase sur le NO₂ horaire +2,7 % comme **preuve**, pas honte. Zéro « je bats Copernicus » ; ouvrir par « j’ignore leurs contraintes ops ». | Recruteur, direction | 6–8 | Un non-spécialiste comprend en 30 s pourquoi ce travail existe ; aligné registre imposé. |
| 3 | **Figure maîtresse unique (page 1)** : jour d’alerte réel (ex. 26/07/2026 PM ou O₃ 08–09/07) — CAMS / obs / correctif / correctif+filet d’abstention. Une image, vidéoprojecteur-proof. | Prévisionniste, recruteur | 3–5 | Passage de « ML candidat » à « risque de sous-alarme + filet » sans lire la suite. |
| 4 | **Vignette d’astreinte 4 minutes** (PDF 1 page ou slide) : à T+0, que regarde-t-on, que décide-t-on (publier / graduer / attendre), avec **tes** sorties vs brut vs MOS officiel sur un épisode Occitanie déjà public. Aucun RMSE sur cette page. | Prévisionniste, recruteur | 5–8 | Preuve d’ancrage ops (ta note 4/10) sans accès au SI ATMO. |
| 5 | **Recaler toute la bibliothèque de 9 figures** sur la vérité gelée (#1) ou **en supprimer** jusqu’à ≤5 figures vivantes ; archiver le reste hors envoi. | Recruteur, jury | 6–10 | L’envoi n’est plus un mensonge involontaire par chiffres périmés. |
| 6 | **Transformer la faiblesse « pas d’obs métro 2025 »** en encadré assumé : carte des 21 stations, n dépassements (163), ce que ça prouve / ne prouve pas ; titre du type *validation inter-annulaire bornée au réseau occitan*. | Jury, recruteur | 2–3 | L’objection arrive de ton fait, pas en embuscade ; crédibilité ↑. |
| 7 | **Phrase standard « station inconnue »** (faiblesse 4.3) : remplacer partout par *station du réseau jamais vue en entraînement, pas un lieu quelconque* + une ligne sur le plancher intra-maille 3,61 µg/m³ (26 % du RMSE). | Jury, recruteur | 1–2 | Fin de la sur-revendication spatiale ; tu as l’air de connaître ton objet. |
| 8 | **Slide « ce que je ne livre pas »** : EPCI/spatialisation (−0,72 classe), MQI hors grain FAIRMODE, équivalence PREV’AIR non revendiquée — trois puces, ton neutre. | Recruteur, direction | 1–2 | L’honnêteté de périmètre devient un *produit*, pas une confession en Q&A. |
| 9 | **Corriger ou retirer le MQI** (faiblesse 4.5) : soit recalcul max 8 h / jour selon référentiel, soit bandeau *hors cadre FAIRMODE — ne pas citer en conformité*. | Jury, LCSQA-minded | 3–8 | Évite un suicide en une question (« votre MQI est faux »). |
| 10 | **Fiche opérationnelle : validation *sur le papier* des entrées à l’heure d’émission** — tableau variable × source × heure UTC dispo × substitut si manquante ; faire relire par un tiers si possible, sinon auto-checklist datée. | Prévisionniste, toi | 4–6 | Débloque le discours « observations récentes » et montre que tu penses *émission*, pas batch de recherche. |
| 11 | **Règle d’abstention en une slide chiffrée** : 0,28 % des cas, +0,02 RMSE, POD ↑, cas 26/07 erreur ÷3,6 — puis *limite* : ne couvre pas CAMS juste sous le seuil. | Prévisionniste, direction | 2–3 | Filet racontable ; pont vers gouvernance de modèle. |
| 12 | **Tableau de décision POD/FAR** (hold-out 2025 recalibré) : trois lignes brut / officiel / nous avec **une reco d’usage** par ligne (ex. officiel = filet détection avide ; nous = CSI/FAR ; brut = baseline). | Prévisionniste, direction | 2–4 | Tu arrêtes de laisser le recruteur croire que le plus haut POD gagne toujours. |
| 13 | **Nommer le phénomène grain** sans jargon : 5 lignes + Huang 2017 en bas de slide (« déjà publié ; ici quantifié sur CAMS FR »). | Jury, recruteur | 1–2 | Tu n’as pas l’air de « découvrir » l’eau chaude ; tu as l’air de **mesurer l’usage**. |
| 14 | **Mettre le NO₂ horaire +2,7 % en avant** à côté du NO₂ max +31,6 % / MOS officiel horaire +16,7 % — même slide, titre : *optimiser un grain, c’est en sacrifier un autre*. | Jury, prévisionniste | 2 | Ta thèse devient falsifiable et mémorable ; le +2,7 % cesse d’être une honte. |
| 15 | **Rejeu écrit de 3 matins d’épisode** (O₃ 08–09/07 + PM 25/07 a posteriori + un jour calme) : une demi-page chacun, horodatage, « j’aurais dit X ». Données : site ATMO épisodes + tes sorties archives si dispo ; sinon CAMS public + obs des 21 stations. | Prévisionniste, recruteur | 8–12 | Ancrage ops sans SI ; matériau oral d’entretien. |
| 16 | **Streamlit : tuer 3 pages sur 6**, garder *un* parcours « jour J → trois produits → décision » ; retirer tout écran RMSE-only. | Recruteur | 4–6 | La démo cesse d’être décorative / diluée. |
| 17 | **Encadré ruptures CAMS 13/11 & 03/12/2024** : r=+0,913, ce que ça **détruit** (attribution du gain) et ce que ça **laisse** (utilité leave-station, besoin de filet post-upgrade). | Jury, recruteur | 2–3 | Faiblesse 4.6 / gain-sur-régression du forçage → maturité, pas scandale. |
| 18 | **Une phrase direction (non technique)** pour l’analogie filet / désactivation quand le modèle amont va bien — testée à voix haute sur un non-QA. | Direction | 1–2 | Tu peux parler à autre chose qu’à un ingénieur modèle. |
| 19 | **Checklist anti-arrogance** (10 interdits de formulation) collée au repo + relecture finale des 10 pages contre cette liste. | Toi, recruteur | 2 | Réduit le risque social « il critique l’ECMWF » / « il se croit PREV’AIR ». |
| 20 | **Manifeste de reproductibilité : une commande / un script** qui régénère le tableau #1 et écrit la date des empreintes ; si ça casse, le dire dans le manifeste. | Jury, recruteur tech | 4–8 | « Reproductible » devient vérifiable en 10 min, pas une intention. |
| 21 | **Page ou annexe « station ≠ maille »** (faiblesse 4.4) : ordre de grandeur 5–30 µg/m³, conséquence pour l’interprétation du RMSE et du plancher 3,61. | Jury | 2–3 | Évite l’objection « vous comparez des objets incomparables » sans solution spatiale EPCI. |
| 22 | **Classifier vs régresser** en une slide service : POD 0,345→0,663, *quand* tu activerais le mode proba en salle (épisode) vs concentration (carte). | Prévisionniste | 2 | Produit dual au lieu d’un monstre unique. |
| 23 | **Trafic hiérarchisé BD TOPO** : 3 phrases pour l’objection « variable statique » + renvoi ablation +13 % NO₂ par type de station (figure déjà mesurable dans tes sorties). | Jury, recruteur | 2–3 | Réponse d’entretien prête, pas improvisée. |
| 24 | **Indexer l’archive cron indice ATMO** : 1 graphique de couverture (jours capturés, trous) + une phrase *pourquoi ce flux est destructif* — sans prétendre comparer l’indice encore. | Recruteur data, jury | 3–5 | Montre une compétence **données publiques fragiles** rare chez les candidats ML. |
| 25 | **Préparer l’oral : 6 questions pièges** (ERA5, temporel −14,6 %, 21 stations, MQI, « pourquoi pas PREV’AIR », POD officiel plus haut) avec réponse en 40 s chacune, enregistrées une fois pour toi. | Recruteur (entretien) | 3–4 | Tu ne grilles pas sur la première question humaine. |
| 26 | **Couper du pitch** tout ce qui ressemble à une course d’architectures / ablation forêt / population nulle — une ligne max en annexe « déjà mesuré, écarté ». | Recruteur | 1–2 | Attention libérée pour le grain et le hold-out. |
| 27 | **Mail ou note interne type** (non envoyé) : 8 lignes à un prévisionniste fictif « voici comment brancher ce correctif en consultation seule, sans publication auto ». | Prévisionniste, direction | 1–2 | Montre que tu acceptes le mode *aide*, pas le remplacement. |
| 28 | **Inventaire des dépendances ops** (ERA5 vs prévi, GPU non requis en inférence?, latence) en demi-page — ce qui bloque la prod vs ce qui est déjà OK. | Direction, prévisionniste | 2–3 | Transforme ERA5 (faiblesse) en *plan de bascule* énonçable. |
| 29 | **Choisir 1 chiffre unique pour la direction** (reco : CSI hold-out recalibré 0,495 ou gain max 8 h O₃ vs officiel) et l’écrire sur la slide de clôture — un seul. | Direction | 0,5–1 | Évite le mitraillage de % en comité. |
| 30 | **Arrêt calcul J-10** : freeze tag git + PDF final + liste « non inclus » datée ; tout run après = hors dossier. | Toi | 1 | Discipline de livraison ; le projet cesse de bouger sous les pieds du recruteur. |

**Dont sans calcul (constatation) :** #2,3,4,6,7,8,11,12,13,14,18,19,22,23,25,26,27,29,30 et une grande part de #15–16 (mise en forme / coupe) — largement ≥10.

**Dont retournement explicite des faiblesses §4 :** #6 (obs 2025), #7 (station inconnue), #8 (EPCI abandonnée), #9 (MQI), #17 (méthode déjà industrialisée + gain forçage), #21 (station≠maille), #28 (ERA5/ops) — ≥5.

---

## Hors tableau

### A. Prévisionniste d’astreinte, 4 minutes

**Il retient :**  
(1) sur le **max 8 h O₃**, le correctif public horaire n’apporte presque rien et peut **nuires en été** ;  
(2) toi tu optimises le **grain réglementaire**, au prix de l’horaire NO₂ ;  
(3) avec seuil recalibré en 2025 tu es **meilleur CSI / FAR**, l’officiel **détecte plus** avec beaucoup de fausses ;  
(4) tu as un **filet** pour ne pas casser un dépassement déjà annoncé.

**Ça l’agace :**  
les RMSE leave-station France en ouverture ; l’absence d’écran « demain chez moi » ; ERA5 non tranché ; le Streamlit à tiroirs ; tout vocabulaire qui sonne *je remplace PREV’AIR* ; les chiffres qui ne matchent pas d’une figure à l’autre.

### B. NO₂ horaire +2,7 % — faiblesse ou preuve ?

| | Argument |
|--|----------|
| **Faiblesse à corriger** | En ops on regarde encore des séries horaires ; un correctif « sourd » à l’heure NO₂ gêne le diagnostic et la com’ fine. Un dual-head (horaire + max) serait plus vendable. |
| **Preuve de thèse** | Le MOS officiel fait +16,7 % *horaire* et moins relatif sur certains agrégats selon polluant ; toi l’inverse sur NO₂. C’est la **même loi de conservation du grain** lue dans l’autre sens. Huang et al. 2017 : tu quantifies. |

**Verdict : preuve à mettre en avant**, pas bug à patcher avant le 22/08 (et le prompt interdit de rouvrir l’optim multi-grain exhaustive). Une phrase suffit : *je n’ai pas « raté » le NO₂ horaire — j’ai payé le prix du max, comme eux paient le prix du max 8 h O₃*. Si un jour tu dualises, ce sera un *produit 2*, pas un aveu.

### C. « Je vois mais je n’observe pas » — trois gisements

1. **Le couple POD/FAR officiels vs toi sous le même protocole de seuil 2025** — tu as déjà le tableau ; tu ne l’as pas transformé en **politique d’usage** (qui active quoi selon le coût d’une FA). Ça vaut plus que +0,3 µg/m³.
2. **Les jours où CAMS est déjà excellent** (résidu faible) et où tu **dégrades** — fréquence, saison, type de station, lien avec l’abstention. Le 26/07 est une anecdote ; la carte de ces jours est un produit de confiance.
3. **L’archive cron de l’indice ATMO** — tu captres un flux destructif et tu ne montres ni couverture ni un seul appariement méthodologique (même sans spatialisation EPCI : ex. cohérence temporelle des millésimes, jours manquants). Signal *ingénieur données publiques*.

### D. Question de jury la plus probable sans réponse solide aujourd’hui

> **« En 2025 sur l’Occitanie, le MOS Copernicus a un meilleur POD que vous (0,72 vs 0,57). Pourquoi vous embaucher plutôt que de brancher le produit gratuit ? »**

Aujourd’hui tu as les chiffres mais pas la **réponse de service** en 40 s (FAR, CSI, été O₃, grain, filet, mode consultation, limites 21 stations). C’est *la* question. La collatérale close seconde : **« Votre MQI est-il conforme FAIRMODE ? »** si une slide non corrigée traîne.

### E. Supprimer 5 choses pour rendre le projet meilleur

1. **La moitié du Streamlit** (pages métriques orphelines).  
2. **Figures / passages encore en fenêtre 11 mois.**  
3. **Toute conformité MQI** tant que le grain est faux — mieux rien que faux.  
4. **Le récit « découverte du lissage »** présenté comme nouveauté (garder *quantification CAMS FR*).  
5. **La spatialisation EPCI comme promesse implicite** (écart −0,72 classe) — la tuer explicitement pour ne plus la porter comme dette invisible.

(Bonus si besoin d’une 6ᵉ : courses d’archi et ablations non actionnables en pitch.)

### F. Poste ou entretien ?

**Aujourd’hui : un entretien — clairement. Un poste : pas encore sur ce dossier seul.**

| Manque pour passer entretien → poste | |
|--------------------------------------|--|
| Chiffres gelés cohérents (#1–5) | non négociable |
| Trace d’usage (vignette astreinte + rejeux) | non négociable |
| Réponse orale à « pourquoi pas le MOS gratuit ? » | non négociable |
| MQI / périmètre sans mensonge | non négociable |
| ERA5 → chemin prévi énoncé | attendu |
| 6 mois de valeur service (fiche émission, monitoring post-upgrade CAMS) | ce qui transforme le CDD en besoin |

**Franchement :** le fond technique est déjà au-dessus de beaucoup de spontanéés. Le trou est **traduction salle de prévision + hygiène de claim**. Sans ça, tu restes un excellent dossier qu’on lit le soir et qu’on n’ouvre pas en staffing. Avec ça, tu deviens quelqu’un qu’on **essaye sur un été**.

---

## Ordre de bataille suggéré (3 semaines)

```
Semaine 1  #1 vérité gelée → #9 MQI → #5 figures → #2–3–4 pages & vignette
Semaine 2  #6–8–11–12–14 slides thèses/faiblesses → #15 rejeux → #10 fiche
Semaine 3  #16 Streamlit → #19–25 oral → #20 manifeste → #30 freeze
```

Tout ce qui est « encore un run pour +0,5 % RMSE » après le freeze est une **régression de candidature**, pas un progrès.
