# Audit de la démo `app.py` — la seule pièce qui sera **opérée en direct** devant le jury

> ## 📄 Réponse attendue : **un fichier `.md`**
>
> Structuré par sections, et pour chaque constat : **ce qui est affirmé**, **ce que le code
> fait réellement**, **la ligne**, et **la correction** — en règle, pas en retouche.
> Hiérarchisez à la fin : si je n'ai le temps que d'un seul correctif, lequel.

---

## Pourquoi vous, et pourquoi celle-là

Votre revue du dossier HTML n'a pas trouvé un problème de goût : elle a trouvé que **le PDF
ne contenait pas le chiffre que le document désigne lui-même comme le seul citable**. Vous
l'avez trouvé en régénérant l'artefact et en comptant son texte, pas en le regardant.

C'est exactement ce dont cette pièce a besoin. `app.py` (587 lignes, Streamlit) sera
**manipulée en direct** : un écart entre ce qu'elle annonce et ce qu'elle calcule ne se
rattrape pas par une note de bas de page.

Le correctif de votre point ① est en place — `exporter_pdf.py` détecte désormais
l'écrêtage interne (`scrollWidth > clientWidth`) et **refuse d'exporter** : six conteneurs
signalés, dont vos 805 px et 833 px pour 615 px visibles, au pixel près. Les points ② à ④
sont en file.

---

## 1. Ce que la démo prétend être

Quatre vues, d'après ses propres titres :

| vue | titre affiché |
|---|---|
| ① | « Aide à l'expertise du jour » — régime du jour, confiance, stations où le modèle diverge |
| ② | « Ce que la correction apporte » — où le gain se produit, répartition |
| ③ | « Où la correction agit » |
| ④ | *(à identifier)* |

---

## 2. 🔴 Le piège connu, à vérifier en premier

La mémoire du projet porte un avertissement explicite, jamais audité depuis :

> **La démo montre le MOS horaire — J0, et non J+1. `tendance` et GEOS-CF appartiennent à
> une AUTRE pile que celle des chiffres publiés.**

Autrement dit : **la démo et le dossier pourraient ne pas parler du même système.** Le
dossier publie du J+1 (tranche 25-48 h d'une sortie 00 UTC) ; la démo afficherait du J0.

**Questions :**

1. Quelle échéance la démo calcule-t-elle **réellement** ? Le dit-elle à l'écran, ou
   faut-il le savoir ?
2. Quelles familles de variables la pile de la démo utilise-t-elle, comparées à celles des
   chiffres publiés ? Un écart de pile change le **produit**, pas seulement le score.
3. Si un juré compare un chiffre de l'écran à un chiffre du dossier, **tombera-t-il sur le
   même** ? Sinon, lequel des deux est faux, et que faut-il écrire à l'écran ?

---

## 3. Ce que je vous demande de vérifier — dans cet ordre

### ① Concordance des chiffres écran ↔ dossier

Pour chaque nombre affiché, la question est la même que celle qui a fait tomber le PDF :
**le chiffre affiché est-il celui que le code calcule, et est-ce celui que le dossier
publie ?** Le dépôt a déjà payé ce défaut deux fois — un rapport publié sans les six
mesures qui décidaient de tout, et une colonne affichée qui n'entrait dans aucun fichier.

### ② Étiquettes et périmètres

Ce dépôt vient d'adopter une règle : *une étiquette porte un rôle, jamais une identité* —
après qu'une colonne nommée `rmse_realmlp` eut contenu du LightGBM et produit un chiffre
faux envoyé à un relecteur. **Cherchez les étiquettes qui affirment plus que ce que la
donnée dit** : une légende qui nomme un polluant, une échéance, un protocole ou un
périmètre que le calcul sous-jacent ne garantit pas.

En particulier : quand un texte dit « validation par station exclue », est-ce **le
protocole réellement exécuté** à cet endroit ?

### ③ Ce qui casse en direct

Un jury manipule sans précaution. Que se passe-t-il si l'on choisit une station sans
donnée, une date hors fenêtre, un polluant sans modèle, un filtre qui vide la sélection ?
**Une démo qui affiche une erreur Python devant un jury coûte plus qu'un chiffre médiocre.**
Distinguez : ce qui plante · ce qui affiche un vide silencieux · ce qui affiche une valeur
plausible et fausse. **Le troisième cas est le seul vraiment dangereux.**

### ④ Ce que la démo ne dit pas et devrait dire

Le dossier assume ses limites — c'est sa posture. La démo les porte-t-elle ? Notamment :
les stations affichées sont-elles **connues du modèle** (donc le score est optimiste), et
est-ce écrit ?

---

## 4. Ce qu'il ne faut pas me proposer

- Une refonte d'interface : **4 jours**.
- Du cache ou de la performance, sauf si un temps de réponse casse la démonstration.
- Des dépendances nouvelles.
- Enjoliver au prix d'une réserve retirée : les réserves sont le produit.

---

## 5. Contexte utile

- Les données vivent en Parquet dans `data/processed/` et `data/interim/oof/`.
- Le dossier publie du **J+1**, en **double aveugle** (station **et** mois cachés), et
  distingue trois périmètres : `PARTOUT` (aucune observation passée), `AUX STATIONS`
  (mémoire locale disponible), `RAW` (repli).
- Convention du dépôt, contre-intuitive et source d'un défaut passé :
  **`horizon=1` désigne J0, `horizon=2` désigne J+1.**
- Un chiffre du dossier ne se cite jamais sans trois mots : **périmètre · épreuve ·
  échéance**. Le même polluant vaut de +3,31 % à +22,94 % selon l'épreuve.
