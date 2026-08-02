# Reprise — état au 1ᵉʳ août 2026, 22 h

*Relais destiné à une session neuve. Lire `CLAUDE.md` d'abord — ce sont les règles ; ce
fichier-ci est l'**état**. Le détail chiffré vit dans `reports/VERITE_DOSSIER.md`, source
unique du dossier, régénérable par `python3 scripts/verite_dossier.py`.*

**Échéance de travail : mercredi 5 août, 12 h.** La candidature elle-même est au 22 août.
Objectif : candidature spontanée à **Atmo Occitanie**.

---

## 1. Ce que le projet est, en trois phrases

Post-traitement statistique des prévisions **CAMS Europe** (maille 0,1°, soit **≈ 8 km en
longitude × 11 km en latitude** aux latitudes françaises — la fiche officielle arrondit à
~10 km ; « 8 km » seul décrivait la largeur et taisait la hauteur, J+1 à J+3).
Un modèle à gradient boosté apprend le **résidu** `observation − CAMS` à partir de variables
disponibles à l'heure d'émission, station par station.

Le cadrage retenu pour la candidature n'est **pas** « j'ai construit un modèle » — la méthode
est publiée (Bertrand et al. 2023, et PREV'AIR corrige déjà par apprentissage). C'est
« j'ai **évalué** des produits officiels dans les conventions du référentiel, trouvé où ils
échouent, et mesuré ce qu'une correction peut et ne peut pas faire ». L'article 13 de l'arrêté
du 16/04/2021 impose précisément cette évaluation annuelle à chaque AASQA.

---

## 2. Les résultats qui portent le dossier

### ⚠️ À lire avant le tableau — le double aveugle, mesuré le 02/08/2026

Tous les chiffres ci-dessous portent sur l'axe **spatial** : stations exclues, dates connues.
En **double aveugle** — station *et* mois cachés ensemble, la condition de déploiement — les
deux polluants ne se comportent **pas du tout pareil** :

| épreuve | O₃ | **NO₂** |
|---|---|---|
| spatiale | +24,10 % | +31,57 % |
| temporelle | +9,38 % | **+45,94 %** |
| **double aveugle** | **+3,31 %** · **7-8 plis négatifs sur 17**, pire −41,4 | **+25,71 %** · σ 5,0 · **aucun pli négatif** |

**L'effondrement est spécifique à l'ozone.** Le NO₂ généralise même **mieux dans le temps que
dans l'espace**. Ne jamais citer un chiffre sans nommer son axe, ni « +1,48 % » sans dire
« sur l'ozone ».

Mécanisme cohérent avec la découverte du 02/08 : le résidu du NO₂ est **sous-maille et
attaché au site** — d'où +16,5 % pour quatre colonnes de typologie — donc transportable d'un
mois à l'autre. Celui de l'ozone est **photochimique et saisonnier**, et cacher un mois
retire un régime entier. Source : `reports/double_aveugle_journalier_O3.csv` et `_NO2.csv`.

Sur l'ozone, le réglage **dégrade** cet axe : défaut +4,02 % → réglé **+1,48 %**.

### Le tableau, axe spatial

| résultat | valeur | où |
|---|---|---|
| gain O₃ au grain réglementaire, France 2024 | **+23,4 %** | `VERITE_DOSSIER` § 1 |
| le même, à **indépendance spatiale réelle** | **≈ +13,5 %** | § 11, décomposé |
| gain NO₂, conventions AASQA | **+34,7 %** | § 10 bis |
| gain **PM10**, conventions AASQA | **+33,3 %** | § 10 bis |
| biais NO₂ urbain de fond | **−11,6 → −0,5 µg/m³** | § 10 bis |
| notre correction contre l'adaptation statistique **PREV'AIR** | **+20,2 % contre +4,3 %** | § 10 ter |
| le MOS officiel de Copernicus **dégrade** l'ozone | 8 mois sur 12, **−19,6 %** en saison | § 2 |

**Le résultat le plus solide** : deux post-traitements officiels — celui de Copernicus et
l'AS-CHI de PREV'AIR — **dégradent leur modèle brut** aux échéances lointaines. Le rapport
LCSQA le dit lui-même page 22. Ce n'est plus l'anomalie d'un produit, c'est un motif de la
famille de méthodes.

### Les limites, à énoncer soi-même

* **Au seuil de procédure français** (180 µg/m³ en max horaire), rien : 32 dépassements sur
  60 400 jours-station, 3 détectés par CAMS, 2 par la correction, zéro à J+3. Un modèle
  entraîné directement sur ce grain fait pareil. Le « 3,5× » porte sur la **valeur cible
  européenne** (120 µg/m³, max 8 h) — toujours nommer l'endpoint.
* **23 % des stations NO₂ sont dégradées** malgré un gain médian de +33 %.
* **Aucune comparaison au modèle régional d'Atmo Occitanie** : aucun bilan chiffré public
  n'existe (recherche documentaire du 01/08, résultat de recherche et non preuve d'absence).

---

## 3. Ce qui a été fait les 31/07 et 01/08 — et pourquoi ça compte

**Quatre chiffres publiés étaient faux ou mal cadrés.** Tous corrigés, tous propagés aux
artefacts en ligne :

1. **RMSE agrégée linéairement** au lieu de quadratiquement (audit externe) → +21,5 % devient
   **+23,4 %**. L'erreur nous **sous-estimait** : rien n'alertait.
2. **Plis de validation non bloqués spatialement** → l'optimisme vaut **18 points**, décomposé
   en 9,4 de fuite et 3 de famine de données grâce à un témoin à retrait aléatoire.
3. **Endpoint mal nommé** — « épisodes » pour une valeur cible.
4. **Deux périmètres confondus** sur une page en ligne (avec/sans observation de la veille).

**Deux explications que le dossier affirmait sont fausses**, retirées :

* « un post-traitement resserre la variance » — pente de calibration mesurée à **1,007** ;
* « le NO₂ résiste au blocage car son signal est local » — il a les stations **les plus
  serrées** et résiste le mieux. La vraie cause est la **portée des résidus** (O₃ 150 km,
  NO₂ 75 km), et la perte au blocage est monotone dans la corrélation à courte distance.

**Trois lacunes levées** : PM10 ingérées et mesurées ; ozone post-juillet 2025 retrouvé ; le
flux national LCSQA remplace Geod'Air sans authentification.

---

## 4. Où en sont les données

| jeu | état | chemin |
|---|---|---|
| observations O₃/NO₂/PM2,5 (EEA) | 94 M lignes, 2013-2025 | `data/processed/panel_metropole_ds2.parquet` |
| observations **PM10** (LCSQA) | 6,72 M, 336 st., 2024-01 → 2026-08 | `data/processed/panel_pm10_lcsqa.parquet` |
| flux LCSQA brut ingéré | 24,2 M lignes, 31 mois | `data/interim/lcsqa/` |
| prévisions CAMS, 4 espèces | extraites aux 476 stations | `data/processed/meteo/cams_prevision_metropole_*.parquet` |
| météo IFS prévue | 10 mois de 2024 | `data/processed/meteo/ifs_metropole_*.parquet` |

**Trous connus et déclarés** : membres d'ensemble de novembre 2023 (HTTP 400 deux fois) ·
GFAS s'arrête au 03/12/2025 · prévisions CAMS de janvier à juin 2025 puis juillet 2026 ·
ozone LCSQA en validité 4 après le 01/07/2025 (voir § 6).

---

## 5. Les pièges de données, vérifiés — ne pas les redécouvrir

1. **Le flux LCSQA étiquette l'heure par son DÉBUT**, notre chaîne par sa FIN. Les deux en
   UTC. Vérifié sur le NO₂, commun aux deux sources : concordance à **0,0001** à +1 h contre
   2,99 sans décalage. Lire la colonne **« Date de fin »**.
2. **Un `.nc` de l'ADS est une archive ZIP** de fichiers journaliers.
3. **Les noms groupés portent plusieurs mois** — `..._pm10_202401_202402`. Toute expression
   ancrée à droite en perd un. Corrigé dans `scripts/download_copernicus.py`, jumeaux cherchés.
4. **PM10 : valeurs horaires jusqu'à 3 784 µg/m³** sur une station urbaine de fond dont le
   p99,9 vaut 125. Plafond à 500 documenté dans `scripts/panel_pm10.py`, choisi sur le p99,99
   du réseau (228) et non par intuition.
5. **Ne jamais lancer `download_copernicus.py --service cams_prevision`** pour une seule
   espèce : il replanifie les quatre et redemande 18 fichiers déjà extraits. Utiliser
   `scripts/lot_cams_pm10.py` comme modèle.

---

## 6. Les prochaines actions, dans l'ordre

### À ma main

1. **Lire la note explicative du LCSQA sur le code de validité 4.** Tout l'ozone après le
   01/07/2025 y bascule ; les mesures continuent (277 à 279 sites), seule la validation s'est
   arrêtée. **13 mois de données en dépendent.** Note : `https://www.data.gouv.fr/datasets/
   donnees-temps-reel-de-mesure-des-concentrations-de-polluants-atmospheriques-reglementes-1`
   → ressource « Note explicative sur les données mises à disposition ».
2. ~~**Rayon de fossé fixé a priori**~~ — **fait le 02/08, et l'expression était fausse.**
   Ce n'est **pas un variogramme** : `scripts/portee_residus.py` calcule un **corrélogramme
   par tranches** et retient la première tranche dont la corrélation moyenne passe sous un
   seuil de 0,10, choisi. 150 km est donc une **borne de tranche**, pas une portée estimée
   avec incertitude. Et « a priori » n'est vrai qu'à moitié : le corrélogramme est estimé sur
   le même corpus, et 25 puis 50 km avaient déjà été essayés. Le rayon sert à concevoir la
   **prochaine** étude, pas à requalifier celle-ci rétroactivement. Résultats au rayon retenu :
   O₃ +10,46 %, NO₂ +29,95 %, PM2,5 **−9,04 %** — et le fossé écarte **~111 stations par pli**
   sur PM2,5, jamais 333 (ce nombre additionne les trois plis).
3. **PM10 sur les autres livrables** : la carte et le dossier les portent, pas les calendriers
   de signalements ni la page Anatomie.
4. Si le temps le permet : **graines sur l'axe temporel** — l'écart entre réglages est
   aujourd'hui à 2× une barre de bruit mesurée sur le mauvais axe.

### Décisions qui reviennent à Cyril

* **S'approprier la lettre** — `docs/LETTRE_ATMO_OCCITANIE.md`. Il y manque ce qu'aucune IA ne
  peut écrire : pourquoi ce poste, maintenant.
* **La marge d'utilité** qui remplace le critère à 2 % : *à partir de quel gain une AASQA
  change-t-elle quelque chose à sa pratique ?* Le critère actuel confond effet minimal
  pertinent et puissance statistique (audit GPT, bloc C3).
* **Trois décisions FAIRMODE** : α PM2,5 = 0,30 par défaut ; v3.2 ou v4.0 ; grain d'agrégation
  du MQI.
* **La fiche opérationnelle** `docs/FICHE_OPERATIONNELLE.md` — notamment : qui opère la
  bascule de source à 3 h du matin, et quel mode dégradé si une source manque.

### Écarté délibérément — ne pas y revenir sans raison neuve

* **Les jeux Kaggle** (`kaggle/`) — aucun banc public ne permet de dire qu'une architecture
  bat PREV'AIR, et aucun gain de Pékin ou Téhéran ne se transfère. Son seul apport a été
  retourné vers nous : audit de fuite de prétraitement dans notre chaîne, **trois points
  vérifiés, tous propres**.
* **La sélection d'hyperparamètres imbriquée spatialement** — juste sur le fond, 1 à 2 jours.
* **Les microcapteurs (CAPTOR)** — vrai besoin d'AASQA, mais **second projet**.
* **Le sol et la géologie** — mesurés, gains 11× sous le critère d'arrêt, et le témoin ozone
  réfute le mécanisme.
* **Une tête de classification ou de quantile** — battues par la régression sur son propre
  terrain ; c'est le **rang** du régresseur qui décide.

---

## 7. Artefacts publiés — URL stables

| page | URL | source |
|---|---|---|
| Dossier AASQA (carte 4 polluants) | `claude.ai/code/artifact/2154b834-aec9-420f-8114-fdd427109e3f` | `scripts/dossier_aasqa.py` |
| Présentation | `…/25cf3ec0-3061-48ca-b819-8636feee8952` | HTML à la main |
| Anatomie de la méthode | `…/08964c95-7db6-4296-a657-66746a62e9b1` | `scripts/anatomie_methode.py` |
| Note de cadrage | `…/198c248e-62db-4fb4-878f-0ad14a147791` | `reports/figures/note_cadrage_occitanie.html` |
| 9 calendriers de signalements | voir la mémoire de session, ou `grep -l 'claude.ai/code/artifact' reports/figures/*.html` | `scripts/calendrier_signalements.py`, `scripts/calendrier_annee.py` |

**Republier avec l'URL existante**, sinon une nouvelle est créée. Toujours passer
`scripts/render_check.py` avant : il teste les deux thèmes, les erreurs de console et le
débordement horizontal.

⚠️ **`reports/figures/presentation.html` et `note_cadrage_occitanie.html` sont écrits à la
main** — pas de générateur. Les éditer directement, et vérifier l'équilibre des balises après.

---

## 8. La leçon de méthode de ces deux jours

Le projet a trouvé, en deux jours, **quatre défauts dans ses propres chiffres publiés et deux
explications fausses qu'il affirmait**. Aucun n'avait levé d'erreur. Trois jouaient en sa
faveur — et c'est exactement pour cela qu'ils avaient survécu.

> **Un défaut qui vous avantage ne déclenche aucune alerte.** Et répondre « c'est prêt » de
> mémoire est un défaut en soi : l'état d'un projet se vérifie sur le disque — horodatage des
> artefacts contre celui de leurs sources, présence effective des chiffres dans les livrables,
> et non dans le souvenir de les avoir calculés.

C'est ce contrôle-là, appliqué le 01/08 au soir, qui a révélé qu'un panel PM10 périmé aurait
faussé toute la mesure du polluant central.
