# LinkedIn — matière prête à coller

> ⚠️ **Ce document n'est pas un audit.** LinkedIn rend **999** à toute requête automatique :
> je n'ai jamais vu ton profil et je ne peux pas dire ce qu'il faut en retirer. Tout ce qui
> suit est de la **matière à intégrer**. Pour l'audit, colle-moi le texte de tes sections
> « Titre », « Infos » et de ton expérience la plus récente — là je peux travailler.

**Règle qui gouverne tout ce fichier** : aucun pourcentage sans son protocole. Sur ce projet
l'ozone vaut +3,31 % ou +22,94 % selon l'épreuve, et **l'ordre des polluants change** avec
elle. Un chiffre nu est indéfendable en entretien — c'est la première question qu'on te
posera.

---

## 1. Titre (220 caractères)

> Data Scientist · Je corrige les prévisions de qualité de l'air par apprentissage — 39,6 %
> d'erreur en moins sur le NO₂, en double aveugle, sans aucune mesure du lieu prédit

Pourquoi celui-ci : il dit **ce que tu fais**, pas ce que tu sais faire, et il porte un
chiffre qui résiste à la question suivante. « Data Scientist | MLOps | Python » ne dit rien
que 400 000 profils ne disent déjà.

---

## 2. Infos (2 600 caractères)

> Je travaille sur un angle mort de la prévision de qualité de l'air : les modèles européens
> prévoient bien la **dynamique** — quand ça monte, quand ça descend — mais se trompent sur le
> **niveau**, station par station. J'apprends cette erreur et je la corrige.
>
> Le résultat, sur 36 mois et 28 millions de mesures horaires : **39,6 % d'erreur en moins sur
> le NO₂**, +20,2 % sur les PM10, +17,9 % sur l'ozone. À l'échéance J+1, en **double aveugle**
> — la station testée et le mois testé sont tous deux inconnus du modèle. Concrètement :
> **aucune mesure du lieu prédit n'entre dans le calcul**, ce qui est la seule condition
> honnête, puisqu'on veut prévoir là où personne ne mesure.
>
> Ce qui rend ça utile maintenant : la directive européenne 2024/2881 divise par deux les
> valeurs limites au 1ᵉʳ janvier 2030, et rend la modélisation **obligatoire** dans toute zone
> qui dépasse. À air constant, sur 408 stations françaises, on passe de **6 dépassements
> aujourd'hui à 109** — un facteur 18. Là où le modèle devient opposable, sa qualité devient
> un point de contrôle : c'est le critère FAIRMODE. Le produit européen brut ne le satisfait
> que sur **41,4 %** des stations NO₂ à J+1 ; corrigé, **96,2 %** — sur les stations
> instrumentées. Sans aucune observation du point, on plafonne à 87,9 %, donc **sous la
> barre** : je le dis parce que c'est la condition réelle de déploiement.
>
> Ce que j'ai appris à faire au passage compte autant que le résultat : un protocole
> d'évaluation qui ne se ment pas. Sur ce projet, un même gain vaut **+3,31 % ou +22,94 %**
> selon l'épreuve choisie, et l'ordre des polluants s'inverse. J'ai donc mécanisé les
> contrôles plutôt que de me fier à ma relecture — chaque chiffre publié est recalculé depuis
> son artefact par un script, et refuse de sortir s'il diverge.
>
> Avant : Data Scientist chez Michelin (alternance, parsing/matching de données complexes) et
> chez DELTAMU (métrologie). Kaggle : 35+ compétitions, 3 top 1 %, meilleur rang #14 / 3 022.
>
> Code, mesures et méthode : gitlab.com/cyril.bgs.dev

---

## 3. Sélection (« Featured ») — 3 éléments, dans cet ordre

1. **Le PDF de 63 pages** — `presentation_atmo.pdf`. C'est la pièce la plus convaincante et
   elle se lit sans cliquer ailleurs. LinkedIn accepte le PDF en natif et le rend feuilletable.
2. **gitlab.com/cyril.bgs.dev/correction-previsions-qualite-air** — vérifié lisible sans compte.
3. **kaggle.com/cyrilbourgeois**

⛔ **Pas de lien GitHub** tant que `github.com/cyril-bgs-dev-tech` ne s'ouvre pas en navigation
privée. Un lien mort en « Sélection » est pire qu'une section vide : il se voit.

---

## 4. Compétences à ajouter, et l'ordre compte

LinkedIn ne montre que les **3 premières** sur le profil. Mettre en tête ce qui te distingue,
pas ce qui te classe :

1. **Modélisation de la qualité de l'air** — presque personne ne l'a, et c'est le mot que les
   AASQA recherchent
2. **Post-traitement statistique de sorties de modèles** (MOS)
3. **Protocoles d'évaluation** / validation croisée spatiale

Puis : Python, LightGBM, RealMLP, séries temporelles, xarray/NetCDF, MLOps, Docker, SQL, CUDA.

---

## 5. Un post, si tu veux en publier un

L'angle 2030 est le plus fort : il est **daté**, **réglementaire**, et il concerne directement
les gens que tu veux atteindre.

> En 2030, les valeurs limites européennes de qualité de l'air sont divisées par deux.
>
> J'ai voulu savoir ce que ça change concrètement. J'ai pris les moyennes annuelles 2025 de
> 408 stations françaises et je les ai comparées aux futurs seuils, à air constant.
>
> Aujourd'hui : 6 stations en dépassement. En 2030 : **109**.
>
> Ce qui compte n'est pas le facteur 18 — c'est ce qu'il déclenche. La directive rend la
> modélisation **obligatoire** dans toute zone qui dépasse. Ces 109 stations, ce sont autant
> de territoires où il faudra produire une prévision qui tient devant un critère de qualité.
>
> Et 4 des 13 départements d'Occitanie n'ont aucune station de mesure exploitable. Pour eux,
> la conformité ne pourra pas être établie par la mesure — seulement par le modèle.
>
> C'est exactement le problème sur lequel je travaille depuis 36 mois de données.

**Ce qu'il ne faut PAS écrire dans ce post** : « les émissions de 2030 seront celles de 2025 ».
Elles ne le seront pas. Le calcul est *à air constant* et cette réserve doit rester visible —
elle est dans `VERITE_DOSSIER` § 5 bis, et un lecteur d'AASQA la verra manquer.

---

## 6. Les trois chiffres à ne jamais citer nus

| chiffre | sans quoi il est faux |
|---|---|
| **+39,6 % NO₂** | double aveugle · J+1 · **PARTOUT** (aucune observation du lieu) |
| **96,2 % FAIRMODE** | `MQI_f` de prévision · J+1 · **aux stations instrumentées** — et 87,9 % partout, donc sous la barre |
| **6 → 109 stations** | moyennes 2025 · **à air constant** · saisie ≥ 75 % |
