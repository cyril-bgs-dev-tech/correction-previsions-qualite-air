# Réponse à la revue — trois défauts confirmés, un chiffre corrigé, et ce qu'il me manque

> **Format de réponse demandé : un fichier `.md`.** Pas de prose libre — un document
> structuré que je puisse lire et appliquer directement.

---

## 1. Ce que j'ai vérifié moi-même, et qui tient

### ① Le nitrate absent avant décembre 2024 — **confirmé sur fichier**

```
202401 : 5 vars · nitrate ABSENT
202406 : 5 vars · nitrate ABSENT
202411 : 5 vars · nitrate ABSENT
202412 : 6 vars · nitrate OUI
202501 : 6 vars · nitrate OUI
```

CAMS a **servi les cinq autres sans lever**, et mon contrôle par la seule taille
(≥ 200 000 octets) les a validés. C'est exactement la règle du dépôt — *« un service qui
ignore un nom invalide sert le reste sans lever »* — enfreinte dans un script dont la
docstring **cite cette règle**. Le contrôle de schéma existait une couche plus bas, à
l'extraction, mais il n'aurait sauvé que le temps déjà dépensé.

**Correctif en cours** : contrôle du schéma, des dimensions, de la fenêtre temporelle et du
taux de manquants **au téléchargement**, avant renommage définitif.

### ② Les 9 % de RealMLP — **votre chiffre est le bon, et mon nommage vous a induit**

`optuna_lgbm_PM10_temporel.csv` porte `rmse_lgbm = 6,2010` et `rmse_realmlp = 5,7943`. Mais
quand le script tourne avec `--modele lgbm`, la colonne `rmse_realmlp` contient en réalité
**le LightGBM réglé** — nommage faux de ma part, hérité d'une généralisation du script.

Donc, à budget égal (60 essais, même objectif temporel, même découpage) :

| polluant | LightGBM réglé | RealMLP réglé | avantage RealMLP |
|---|---:|---:|---:|
| O₃ | 12,3073 | 12,1320 | +1,42 % |
| NO₂ | 12,3882 | 12,3476 | +0,33 % |
| **PM10** | **5,7943** | **5,6405** | **+2,65 %** |
| PM2,5 | 3,8492 | 3,7911 | +1,51 % |

**Le « 9 % » est mort.** Reste +2,65 % sur PM10, à soumettre à l'ablation que vous proposez.

### ③ « Notre épreuve cache station ET mois » — **faux, confirmé**

`vue_aasqa.py` répartit par `i % 3` sur les stations et entraîne sur **toutes les dates**
des autres stations. Aucun mois n'est caché. La phrase était fausse dans mon brief et le
resterait dans le dossier : je la retire.

---

## 2. Ce que je corrige immédiatement dans le dossier

- Suppression de « on domine », « à égalité », « ils nous dépassent ». Formulation retenue :
  **les deux études ne permettent aucun classement direct** — dénominateurs, périodes,
  échéances et populations différents.
- Le tableau de § 10 bis sera étiqueté **« axe spatial, dates communes »**, pas
  « convention AASQA » tout court.
- Le « 2/33 » : je fige **une** règle avant calcul et publie **une** valeur reproductible.
  Vous avez raison que trois variantes coexistent ; quelle que soit celle retenue, le
  verdict reste que **la détection PM10 opérationnelle est un échec**, et je le présente
  ainsi.

---

## 3. Ce sur quoi je ne suis pas convaincu — et pourquoi

### Le Kalman

Votre argument : sans observation à l'inférence, un filtre de biais se réduit à une
climatologie. **Je l'accepte pour un Kalman par station.** Mais notre levier le plus fort
est déjà une moyenne glissante de l'erreur par station, qui **utilise donc l'observation
récente** et vit dans la variante `FULL` du produit (station instrumentée). Pour cette
variante-là, un Kalman n'enfreint aucune contrainte — il remplace une moyenne mobile à
fenêtre fixe par un état à variance apprise.

**Question : maintenez-vous la dépriorisation pour la variante `FULL` uniquement ?**

### La spéciation contre l'IFS

Vous priorisez l'IFS (P0) devant la spéciation (P1), preuve locale à l'appui
(+4,76 % sur PM2,5). J'accepte l'ordre. Mais la spéciation est **déjà téléchargée** (32
mois, 7,1 Go), donc son coût marginal est l'extraction et l'ablation, pas le
téléchargement.

**Question : cela change-t-il l'ordre, ou l'IFS reste-t-il P0 par sa valeur propre ?**

---

## 4. Ce dont j'ai besoin de vous, en `.md`

### ① Le contrat expérimental, spécifié

Vous écrivez « figer dates, stations, support, échéance, variables et versions CAMS ».
J'ai besoin de la **spécification exacte**, sous une forme que je puisse implémenter sans
l'interpréter :

- bornes de dates d'entraînement et de test, en absolu ;
- règle de découpage des stations ;
- que faire des versions CAMS U8/U8b/U9/U10 — exclure, repondérer, ou stratifier ?
- quelles métriques, avec quel intervalle de confiance et quel bootstrap
  (vous dites « par blocs de mois et de stations » — quelle taille de bloc ?).

### ② L'arbitrage sous contrainte réelle

Il reste **quatre jours**, une machine à dix-sept paniques noyau, et un dossier qui doit
être rendu complet. Votre plan en compte cinq.

**Si vous ne pouviez garder que DEUX lignes de votre tableau P0/P1/P2, lesquelles ?**
Et que faut-il **écrire comme limitation** plutôt que mesurer, pour ce qui saute ?

### ③ L'audit des ruptures CAMS

C'est votre P0 et je ne l'avais pas vu. Précisez :

- les dates de bascule exactes à utiliser comme frontières ;
- le test qui distingue une **rupture de version** d'une **saisonnalité** — nos versions
  changent en novembre, et novembre est aussi le début de la saison de chauffage ;
- ce qui se conclut si la rupture est confirmée : réentraîner sur la période récente
  seulement, repondérer, ou ajouter la version en variable ?

### ④ Une réponse à une objection que je vous fais

Vous écrivez que CAMS *« contient déjà de l'information d'émission »*, donc que la
spéciation n'est pas un inventaire manquant mais une sortie de CTM. **D'accord — mais c'est
précisément l'argument pour l'utiliser** : le modèle corrige un résidu, et connaître la
composition lui permet d'apprendre un biais **par source** au lieu d'un biais moyen. La
question n'est pas si l'information est nouvelle en amont, mais si elle est **nouvelle pour
le correcteur**.

**Réfutez ou accordez, avec le test qui trancherait.**

---

## 5. Contraintes inchangées

- **4 jours.** Toute suggestion doit être chiffrable.
- Machine instable — tout lot reprenable.
- **Aucune observation à l'inférence** pour la variante déployable ; la variante `FULL`
  aux stations instrumentées y a droit, et c'est un produit distinct.
- Réponse attendue **en `.md`**, structurée par vos numéros de section.
