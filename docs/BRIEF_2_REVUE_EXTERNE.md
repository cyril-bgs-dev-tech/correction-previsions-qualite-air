# Seconde revue — ce qui est tombé depuis, et une question qui décide de tout un chantier

> ## 📄 Réponse attendue : **un fichier `.md`**
>
> Structuré par mes numéros de section. Pour chaque recommandation : **le test exact**,
> **le seuil de décision**, **le coût en heures**, et **ce qu'on écrit si le test échoue**.
> Un conseil que je ne peux pas traduire en commande est inapplicable à quatre jours.

Vos trois constats de la première revue ont été **vérifiés sur artefact et acceptés** :
nitrate absent avant 2024-12 (confirmé fichier par fichier), le 9 % qui devient 2,65 %
(mon nommage de colonne mentait), `vue_aasqa` qui ne cache pas les mois (confirmé,
`i % 3` sur les stations). Corrigés dans le code, pas seulement notés.

---

## 1. 🔴 LA question — tous nos effets sont-ils sous la barre de bruit ?

Ce dépôt a mesuré sa propre barre de bruit, en décomposant la variance des écarts publiés :

| source | écart-type |
|---|---|
| graine d'algorithme | 0,399 pt |
| **composition des plis** | **1,368 pt** |
| **barre retenue (O₃)** | **±2,02 pt** |

Or voici **tous** les effets du chantier « booster neuronal », mesurés aujourd'hui sur un
partage temporel, budget de réglage égal (60 essais Optuna chacun, même objectif, même
découpage) :

| polluant | LightGBM réglé | RealMLP réglé | écart | mélange au poids honnête |
|---|---:|---:|---:|---:|
| O₃ | 12,3073 | **12,1320** | +1,42 % | +0,00 % *(w=0 : le mélange est refusé)* |
| NO₂ | **12,3476** | 12,4578 | −0,89 % | **−0,89 %** *(pire que le meilleur seul)* |
| PM10 | 5,7943 | **5,6405** | **+2,65 %** | **+0,85 %** |
| PM2,5 | 3,7911 | **3,7908** | +0,01 % | +0,84 % |

**Question directe : lesquels de ces effets sont distinguables du bruit, et par quel test ?**

Et si la réponse est « aucun » — ce que je crains —, **que faut-il écrire dans le dossier
plutôt que de les taire** ? Un chantier qui ne produit rien est un résultat, à condition
d'être présenté comme tel.

### Ce qui me trouble le plus, et que je ne sais pas interpréter

Sur **NO₂**, le poids choisi honnêtement sur la validation vaut **w = 0** (RealMLP seul),
et il rend **−0,89 % de moins que LightGBM seul**. *Choisir sur un hors-échantillon coûte
donc plus cher que ne pas choisir du tout.*

Le biais de criblage du combineur, mesuré comme l'écart entre le poids choisi sur la
validation et le poids choisi sur le test, vaut **1,34 % sur NO₂, 0,82 % sur PM2,5, mais
seulement 0,05 % sur PM10**.

**Comment lire ça ?** Est-ce (a) que le bloc de validation ne prédit pas le test — donc
tout choix guidé par lui est illusoire ; (b) que la courbe est trop plate pour qu'un
optimum existe ; (c) autre chose ? Et **quelle conséquence pratique** : renoncer à
sélectionner, moyenner sans choisir, ou abandonner l'ensemble ?

---

## 2. La spéciation est extraite — spécifiez l'ablation

Vous aviez raison sur la sélection. État réel après contrôle de schéma :

- **socle de 5 variables sur 32 mois** — `dust`, `ecres_conc` (carbone résidentiel),
  `pm2p5_total_om_conc`, `pmwf_conc` (feux), `sia_conc` ;
- **nitrate : tardif**, présent seulement depuis 2024-12, traité comme tel et **compté**,
  pas silencieusement à moitié vide ;
- `pm10_sea_salt_dry` et `total_elementary_carbon` — que vous recommandiez — **ne sont pas
  téléchargés**. Un mois coûte ~400 s ; 32 mois ≈ 1 h à 3 requêtes parallèles.

**Questions :**

1. **Faut-il télécharger le sel marin et le carbone élémentaire total avant l'ablation**,
   ou l'ablation sur les 5 existantes suffit-elle à décider ?
2. L'**ablation conditionnelle par époque CAMS** que vous proposez : quelles bornes exactes
   pour U8 / U8b / U9 / U10, et quel test sépare une rupture de version d'une saisonnalité ?
   Nos versions basculent en **novembre** — qui est aussi le début de la saison de
   chauffage, donc du signal `ecres_conc`. Les deux effets sont confondus par construction.
3. Le **bootstrap par blocs** : quelle taille de bloc en mois, quelle en stations, et
   combien de tirages pour un intervalle utilisable à quatre jours ?

---

## 3. Ce qu'une autre revue vient de trouver, et qui change la priorité

Un second relecteur a audité le dossier HTML et son PDF. Il a établi que **le document
imprimé ne contient pas le chiffre qu'il désigne lui-même comme le seul citable** : un
tableau de 805 px dans un conteneur de 615 px, donc défilant à l'écran et **absent du
papier**. Notre contrôle mesurait la largeur du *document* — 718 ≤ 718, vert — sans voir
l'écrêtage *interne*. Corrigé : l'export refuse désormais de produire un PDF écrêté.

**Cela consomme du temps sur les quatre jours restants.** D'où la question qui suit.

---

## 4. L'arbitrage, cette fois avec les coûts réels

Votre plan comptait cinq jours ; il en reste **quatre**, dont une partie ira à la
réparation ci-dessus.

Votre tableau P0/P1/P2 proposait : audit des ruptures CAMS · IFS (couche limite, vent,
pluie) · ablation de spéciation · modèle à régimes · prévision probabiliste · multi-tâches.

**Deux questions :**

1. **Quelles DEUX lignes garder**, sachant que l'IFS n'est extrait que sur **11 mois
   (2024-02 → 2024-12)** et ne contient **pas** la hauteur de couche limite — l'étendre
   coûte un téléchargement en plus ?
2. Pour chaque ligne écartée, **quelle phrase écrire dans le dossier** ? Une limite
   nommée vaut mieux qu'un silence, et je préfère écrire « non mesuré, voici pourquoi »
   que laisser croire que la question ne s'est pas posée.

---

## 5. Une objection que je maintiens

Vous dépriorisez le filtre de Kalman : *sans observation à l'inférence, un filtre de biais
se réduit à une climatologie.* **J'accepte pour le produit `PARTOUT`.**

Mais notre levier le plus fort — la moyenne glissante de l'erreur par station, **+43,1 %
sur NO₂ sans aucun apprentissage** — vit dans la variante `AUX STATIONS`, qui **utilise
déjà l'observation récente**. Pour celle-là, un Kalman n'enfreint rien : il remplace une
fenêtre fixe par un état à variance apprise, ce qui est précisément le cas d'usage
classique du MOS opérationnel.

**Maintenez-vous la dépriorisation pour cette variante-là ?** Si oui, sur quel argument
autre que la contrainte d'observation, qui n'y tient pas.

---

## 6. Contraintes

- **4 jours**, machine à 17 paniques noyau — tout lot reprenable.
- Aucune observation à l'inférence pour `PARTOUT` ; `AUX STATIONS` y a droit et c'est un
  produit distinct, pas une entorse.
- Réponse en **`.md`**, une section par numéro ci-dessus.
