# Muscler la méthode — pistes ML / Deep Learning

*Note de cadrage · 31/07/2026. Pas une roadmap de paper : ce qui peut encore bouger un **mardi matin** AASQA, vu l’état mesuré du projet.*

---

## 0. Ce qu’il ne faut plus re-découvrir

Le projet a déjà tranché une grande partie de l’espace « ML classique » :

| Déjà mesuré | Conséquence pour le DL |
|-------------|------------------------|
| LightGBM ≫ Ridge / RF ; XGB≈CatBoost≈LGBM (±0,3 pt) | **Arrêter les courses d’architectures tabulaires** |
| Cible = grandeur réglementaire (+5–6 pts sur max) | Toute nouvelle tête doit apprendre **le grain d’usage**, pas l’heure par défaut |
| Spatial solide, temporel fragile, rolling-origin +6 % moy. / été ~0 | Le DL qui mémorise la saison **aggravera** le temporel s’il n’est pas contraint |
| J−2 obs : +8,9 % O₃ / +21,9 % NO₂ | Le plus gros levier ML **simple** restant est **séquentiel court**, pas un transformer 100 M |
| ERA5 +7–8 % (plafond) ; IFS non encore en score dossier | Avant d’inventer un réseau, **brancher la météo d’émission** |
| Ensemble 6 membres dispo ; capteur d’anomalies statique/dyn. peu utile en coupe-circuit | L’ensemble sert la **méfiance**, pas un 2ᵉ MOS magique |
| Dual « jours anormaux » a **perdu** | Méfiance envers experts mal peuplés |
| NO₂ dépassements quasi absents au grain 8 km | Ne pas vendre un détecteur NO₂ réglementaire |
| ×3,6 dépassements O₃ à budget FA égal | Le produit est déjà un **classifieur de seuil** déguisé en régresseur — le muscler là |

**Principe directeur :**  
> On ne cherche pas un modèle plus savant. On cherche à **mieux poser le problème d’apprentissage** (cible, coût, quand se taire, quelles entrées à t₀) avec le minimum de paramètres nouveaux.

Le deep learning n’est légitime ici que s’il apporte une **inductive bias** que le boosting n’a pas : séquence courte, multi-tâches liées à l’indice, calibration d’incertitude, ou lecture d’un champ spatial — pas « parce que c’est deep ».

---

## 1. Carte des pistes (re-brainstorm)

### Légende d’impact

- **Décision** : change publier / graduer / attendre  
- **Score** : RMSE / CSI / courbe FA  
- **Dossier** : recruteur / crédibilité  
- **Risque** : fuite, maintenance, non-reproductibilité, arrogance

### Tableau unique

| # | Piste | Famille | Impact principal | Effort | Risque | Priorité |
|---|-------|---------|------------------|--------|--------|----------|
| **P1** | Tête **proba de dépassement** calibrée (même features, loss focale / BCE sur seuil) | ML classique | Décision + score queue | Faible | Faible | **1 — faire** |
| **P2** | **Multi-horizon / multi-grain** (J+1…J+3 ou max+horaire) à têtes partagées | ML / petit DL | Score + ops | Moyen | Moyen | **2** |
| **P3** | **Séquence courte** obs J−1…J−k + CAMS (TCN / tiny GRU / même LGBM sur lags) | Séquentiel | Score NO₂/O₃ | Moyen | Fuite t₀ | **2** |
| **P4** | Météo **IFS** (puis éventuellement AIFS) comme features | Features + ML inchangé | Score (plafond→réel) | Moyen–élevé | Données | **1 — mesurer** |
| **P5** | **Incertitude** : spread membres CAMS + quantile regression / ensemble de boosting | UQ | Décision (méfiance) | Moyen | Indic non calibré | **3** |
| **P6** | **Conformal** ou isotonic sur scores de dépassement | Calibration | Décision | Faible | Faible | **2** |
| **P7** | Loss **asymétrique / multi-objectif** (RMSE + pinball haut + FA) déjà entamée | ML | Queue | Faible | Trade-off | **2** (prolonger) |
| **P8** | **Mode prudence** (routeur simple feux/import/spread) sans 2ᵉ réseau | Règles + ML | Décision | Faible | Faible | **1** |
| **P9** | GFAS / feu en feature binaire ou densités amont | Features | PM épisodes | Faible | Rare | **3** |
| **P10** | GNN / CNN sur grille CAMS | Deep spatial | Score spatial | Élevé | Surdimensionné | **4 — plus tard** |
| **P11** | Transformer / foundation fine-tune (Aurora…) | Deep fondation | Dossier veille | Très élevé | Mode + mandat | **5 — veille** |
| **P12** | Physics-informed / contraintes stœchio O₃–NO₂ | Hybride | Cohérence | Élevé | Gains incertains | **4** |
| **P13** | Domain adaptation temporelle (reweight mois, adversarial saison) | ML robustesse | Temporel | Moyen | Complexe | **3** |
| **P14** | Residual learning **hiérarchique** : débiaisage → MOS → proba | Pipeline | Lisibilité | Faible | Faible | **2** |

---

## 2. Les pistes vraiment prometteuses (développement)

### 2.1 P1 — Arrêter de seuiller une concentration : apprendre la décision

**Pourquoi c’est le #1.**  
Le service ne paie pas le RMSE : il paie les **seuils**. Vous avez déjà prouvé qu’à budget de FA égal le rappel O₃ explose. Le régresseur + seuil post-hoc est un détour. Un classifieur (ou une tête de proba) optimise **directement** la courbe que le prévi comprend.

**Design minimal (pas deep obligatoire) :**
- Entrées = celles du MOS actuel (+ J−2 si validé à l’émission)
- Cible = `1{y_réglementaire ≥ seuil}` (O₃ 120 max 8 h, etc.)
- Loss = BCE / focal ; **calibration** (isotonic ou temperature scaling) sur plis temporels
- Sortie écran = proba + FA attendue au seuil de décision choisi par le service

**Deep seulement si** un petit MLP sur embeddings de station améliore la calibration leave-station — à A/B contre LGBMClassifier. Pari : **LGBM gagne encore** ; le gain vient du **problème**, pas du réseau.

**Muscles gagnés :** langage métier, POD/FAR natifs, lien direct avec ×3,6 déjà mesuré.

---

### 2.2 P4 puis P3 — Donner au modèle le temps court qu’un prévi utilise déjà

**Chaîne de valeur :**
1. **IFS (prévu)** remplace le fantasme ERA5 → mesure la part récupérable du +7–8 %.
2. **Lags d’obs** J−1…J−2 (déjà +21 % NO₂) structurés proprement (features à t₀ garanties).
3. Si et seulement si les lags tabulaires plafonnent : **TCN/GRU très petit** sur la fenêtre 48–72 h (obs + CAMS + météo prévue).

**Pourquoi pas un transformer d’emblée :**  
n stations × 17 mois ne justifie pas un modèle de fondation ; le risque de fuite et de maintenance tue le dossier ops.

**Test de tuer P3 deep :**  
LGBM sur `{lags 1..48 h agrégés, CAMS, calendrier, IFS}` vs GRU. Si Δ < 0,3 µg ou < 2 pts CSI → **rester tabulaire**.

---

### 2.3 P5 + P8 — Incertitude actionnable, pas décorative

L’échec du 25/07 (tout le monde à zéro) et les plis d’été négatifs disent la même chose : **il faut savoir se taire**.

**Stack réaliste :**
- Features d’état : spread inter-membres CAMS, drift récent du résidu, drapeau GFAS/import, proba de la tête P1
- Règle ou **petit** modèle de *gating* : corriger / brut / « expertise seule »
- Calibration des intervalles sur rolling-origin (conformal time-series si vous voulez un badge moderne **utile**)

**Deep inutile** pour le gate si une régression logistique sur 5 signaux suffit — et un prévi **lira** la logistique.

---

### 2.4 P2 + P14 — Une famille de sorties, un seul entraînement

Aujourd’hui : un grain gagne, l’autre paie (NO₂ horaire +2,7 % vs max +31 %).  

**Piste ML propre :**  
multi-task gradient boosting ou petit hard-sharing MLP :
- tête A : grandeur réglementaire (prioritaire, loss × w_reg)
- tête B : horaire (diagnostic)
- tête C : proba dépassement (P1)

Ce n’est pas du « deep washing » : c’est **aligner le produit** sur les deux usages salle (seuil + série).

---

### 2.5 P13 — Muscler le point faible : le temps

Sans nouvel algorithme exotique :
- **reweight** des mois d’été / des jours proches seuil
- **time-series CV** stricte (vous avez le rolling-origin) comme **seul** critère de sélection de modèle
- option : modèle **par saison** seulement si effectif queue suffisant (sinon weight, pas split)

Le deep adversarial domain-invariant est séduisant et souvent **fragile** ici ; ne le toucher qu’après reweight simple échoué.

---

## 3. Ce qui brille et qu’il ne faut pas faire maintenant

| Idée séduisante | Pourquoi la monétiser plus tard |
|-----------------|--------------------------------|
| Fine-tune Aurora / foundation AQ | Mandat amont, pas AASQA ; coût ; aucun gain décision avant proto IFS |
| CNN/GNN sur grille Europe | Votre produit est **station-first** ; leave-station marche déjà sans graphe |
| LSTM profond sur 27 ans de panneau | Cible MOS = appariement CAMS 17 mois ; le long panneau sert la **climatologie**, pas un monstre séquentiel |
| Deux réseaux expert feu / normal | Déjà contredit en petit ; jours feu trop rares |
| AutoML / NAS | Contredit la discipline anti-course d’archi |
| Generative downscaling 100 m | Autre projet (spatialisation EPCI), hors gel candidature |

---

## 4. « Deep Learning » : quand le mot a un sens ici

Utiliser le label DL seulement pour :

1. **Séquence** (si tabulaire lags saturés)  
2. **Calibration / réseaux d’incertitude** légers  
3. **Plus tard** : encodeur de champ (membres × espace) pour un score de méfiance spatial  

Ne pas l’utiliser pour :
- remplacer LightGBM sur table plate 53 features  
- impressionner un jury sans protocole rolling-origin  

**Phrase honnête candidature :**  
> « Le cœur est un MOS boosting sur grandeur réglementaire et proba de seuil ; le deep n’entre que si la structure séquentielle ou l’incertitude le justifie après un témoin tabulaire. »

---

## 5. Plan de musculation en 3 couches

```
Couche A — sans nouveau paradigme (1–2 semaines de mesure)
  A1. Tête / modèle proba dépassement O₃ (+ calibration)
  A2. Brancher J−2 proprement à l’émission (déjà gagnant)
  A3. IFS features + re-score leave-station / rolling
  A4. Gate prudence : spread membres + GFAS + proba basse
  A5. Sélection de modèle = CSI@FA fixé + rolling-origin, plus le RMSE spatial seul

Couche B — ML structuré (si A plafonne)
  B1. Multi-têtes grain × horizon
  B2. Loss multi-objectif (pinball + FA) avec front explicite
  B3. Conformal / quantiles pour bandes de confiance
  B4. Lags riches + témoin “petit séquentiel” (TCN)

Couche C — recherche (après le 22/08 ou si poste)
  C1. Encodeur d’ensemble / méfiance spatiale
  C2. Adaptation de domaine temporelle
  C3. Veille foundations (évaluation, pas remplacement)
```

---

## 6. Critères d’arrêt (anti-folie ML)

Abandonner une piste ML/DL si :

1. Gain < **0,3 µg/m³** **et** < **2 pts** de CSI@FA sur rolling-origin  
2. Elle exige une entrée **absente à t₀**  
3. Elle empire le **pire mois d’été** sans filet  
4. Personne en salle ne peut dire en une phrase **quand elle a tort**  
5. Elle n’a pas de **témoin plus bête** (débiaisage, lags LGBM, règle d’abstention)

---

## 7. Réponse courte à la question posée

**Les pistes les plus prometteuses ne sont pas « plus deep », elles sont « plus décisionnelles » :**

1. **Proba de dépassement calibrée** (même stack boosting)  
2. **Entrées d’astreinte** : obs récentes + météo **prévue** + (léger) signal feux/ensemble  
3. **Gating / incertitude** pour les matins type 25/07  
4. **Multi-objectifs grain/horizon** pour ne plus sacrifier un usage à l’autre  
5. Deep **séquence courte** seulement en challenger du tabulaire  

**Muscler la méthode**, concrètement :  
changer la **fonction de coût et la sortie** (décision + silence), enrichir le **contexte à l’émission**, imposer le **rolling-origin** comme juge — et traiter le deep learning comme un **outil d’inductive bias**, pas comme une promotion.

---

## 8. Lien avec les documents déjà produits

| Doc | Apport |
|-----|--------|
| `VERITE_DOSSIER.md` | Chiffres gelés à ne pas noyer sous un nouveau modèle |
| `GROK_NOUVEAUX_OUTILS.md` | Ensemble/feux/IFS côté exploitation — aligne P4, P5, P8, P9 |
| `GROK_70.md` | Ce que la salle accepte comme outil |
| `RAPPORT_AGENT.md` | Rolling-origin et échec du capteur d’anomalies → P8/P13 |
| `PROGRAMME_RECHERCHE.md` | IFS déjà piste 1 — à fusionner avec couche A3 |

---

*Fin. Toute piste DL ajoutée au dossier candidature doit citer le témoin tabulaire battu et le pli temporel du jugé.*
