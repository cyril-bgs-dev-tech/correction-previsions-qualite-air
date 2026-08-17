# Troisième revue — la spéciation marche, et je ne sais pas pourquoi

> ## 📄 Réponse attendue : **un fichier `.md`**
>
> Une section par numéro ci-dessous. Pour chaque recommandation : **le test exact**, **le
> seuil de décision**, **le coût en heures**, **ce qu'on écrit si le test échoue**.
> Il reste **3,5 jours**.

Vos corrections précédentes ont toutes été vérifiées et appliquées : l'erreur de
transcription O₃ (je citais le LightGBM par défaut comme « réglé » et le LightGBM réglé
comme « RealMLP »), le mot « honnête » abandonné pour `poids_developpement`, et la
comparaison appariée plutôt qu'à la barre absolue de ±2,02 pt.

⚠️ **Un avertissement sur votre clé d'API.** Vous recommandiez
`pm2.5_anthropogenic_total_carbon` : ce nom **n'existe pas** au catalogue ADS (vérifié sur
`form.json`). La clé réelle est `total_elementary_carbon`. Lancée telle quelle, la commande
aurait produit exactement le défaut que vous m'aviez signalé une heure plus tôt sur le
nitrate — le service sert le reste sans lever. Le complément est en cours avec les bonnes
clés (`pm10_sea_salt_dry` + `total_elementary_carbon`).

---

## 1. 🔴 Le résultat — et pourquoi il me met mal à l'aise

Ablation de la spéciation, axe **temporel**, mêmes lignes pour les deux configurations,
LightGBM aux hyperparamètres de production :

| polluant | base (58 var.) | + spéciation (68 var.) | apport | lignes conservées |
|---|---:|---:|---:|---:|
| **PM10** | 5,8752 | **5,1954** | **+11,57 %** | 100 % |
| O₃ | 12,7682 | 11,9222 | **+6,63 %** | 86 % |
| NO₂ | 11,9049 | 11,1855 | **+6,04 %** | 86 % |
| PM2,5 | 3,4472 | 3,2784 | **+4,90 %** | 87 % |

Les cinq variables : `dust`, `ecres_conc` (carbone résidentiel), `pm2p5_total_om_conc`,
`pmwf_conc` (feux), `sia_conc` (aérosol inorganique secondaire).

**+11,57 % en ajoutant dix colonnes à un modèle qui en a 58 me paraît trop beau.** J'ai
donc vérifié la fuite la plus probable — une spéciation plus fraîche que le CAMS corrigé :

| contrôle | valeur | lecture |
|---|---:|---|
| corrélation somme des composantes ↔ CAMS total | **0,911** | même sortie, même échéance — **pas de fuite de fraîcheur** |
| ratio somme / total | **0,546** | décomposition partielle cohérente (sel marin, nitrate, sulfate, fraction grossière absents) |
| meilleure corrélation d'une composante avec l'obs | `pm2p5_total_om_conc` **+0,466** | |
| corrélation du **total** avec l'obs | **+0,639** | **aucune composante ne bat le total** |

Donc ce n'est ni un décalage temporel, ni une composante secrètement plus prédictive.

**Ma question : quel mécanisme produit +11,57 %, et quel test distingue « le modèle apprend
un biais dépendant de la source » d'« une des composantes sert de proxy à une variable
latente absente de la base » ?** Je pense à la saison, à la position géographique, ou au
régime météorologique — que la spéciation encoderait indirectement.

---

## 2. Le paradoxe de l'ablation — et le doute que j'ai sur ma propre méthode

Retirer une variable à la fois **ne dégrade presque jamais**, et parfois **améliore** :

| retrait | PM10 | PM2,5 | NO₂ | O₃ |
|---|---:|---:|---:|---:|
| sans `ecres_conc` | **5,1789 ✓** | **3,2690 ✓** | **11,1679 ✓** | 11,9534 |
| sans `dust` | 5,3012 | **3,2606 ✓** | **11,1684 ✓** | 11,9770 |
| sans `sia_conc` | 5,3088 | 3,2810 | 11,4491 | **11,8723 ✓** |
| sans `pm2p5_total_om_conc` | 5,2738 | 3,3457 | 11,3695 | **11,8722 ✓** |
| sans `pmwf_conc` | 5,3099 | 3,3034 | 11,1974 | 12,0906 |
| *(tout)* | 5,1954 | 3,2784 | 11,1855 | 11,9222 |

**`ecres_conc` — le traceur du chauffage au bois, sur lequel reposait toute mon hypothèse —
est celui dont le retrait aide le plus, sur 3 polluants sur 4.**

Aucun retrait ne coûte plus de ~2 % : les cinq variables semblent **fortement redondantes**.

**Questions :**

1. **L'ablation un-à-un est-elle seulement le bon outil ici ?** Avec cinq variables
   colinéaires, retirer l'une laisse les autres compenser — l'exercice ne peut, me
   semble-t-il, rien mesurer. Faut-il une **ablation par groupe**, une importance par
   permutation **groupée**, ou autre chose ?
2. Un retrait qui **améliore** est-il du bruit d'ajustement, ou dit-il quelque chose ?
3. Comment formuler honnêtement le résultat ? Aujourd'hui je ne peux écrire que
   « **le bloc** apporte », jamais « **le chauffage au bois** apporte » — et c'est
   nettement plus modeste que l'hypothèse annoncée.

---

## 3. Un problème de comparabilité que je ne sais pas résoudre

Le corpus de cette ablation **n'est pas celui du dossier** : la jointure sur la
disponibilité de la spéciation conserve 100 % des lignes sur PM10 mais **86-87 %** sur les
trois autres — la spéciation commence en 2024-01.

Conséquence : la **base** y a un RMSE différent de celui publié. Sur NO₂, base = 11,9049
ici contre 12,3476 dans le banc temporel de référence.

**Comment publier un apport mesuré sur un corpus plus court, sans laisser croire qu'il
s'additionne aux gains du dossier ?** Faut-il republier toute la chaîne sur la fenêtre
2024-01 → 2026-08, ou présenter l'apport comme un écart isolé, avec sa fenêtre ?

---

## 4. L'arbitrage final, avec les chiffres réels

Il reste **3,5 jours**. Deux chantiers ont produit :

| chantier | effet | état |
|---|---|---|
| **spéciation CAMS** | **+4,9 à +11,6 %**, 4/4 au-dessus du seuil de criblage | mesuré, non bootstrappé |
| RealMLP contre LightGBM | +2,65 % (PM10), −0,89 % (NO₂) | mesuré, non bootstrappé |
| complément sel marin + carbone total | — | téléchargement en cours |

Le bootstrap apparié que vous avez spécifié est écrit (blocs de mois × 20 groupes
`KMeans`, tirages sur le produit cartésien).

**Questions :**

1. **Sur lequel des deux le passer d'abord**, si je n'ai le temps que d'un ?
2. Avec un effet de 5 à 12 %, vos seuils de décision (borne basse > 0 après Holm, gain
   ≥ 2 points) sont-ils toujours les bons, ou faut-il les resserrer quand l'effet est
   grand — le risque n'étant plus le bruit mais un **artefact de protocole** ?
3. Faut-il **abandonner RealMLP** pour concentrer le temps restant sur la spéciation, qui
   rend 4× plus ? Et si oui, que faut-il écrire du travail neuronal plutôt que le taire ?

---

## 5. Contraintes

- **3,5 jours**, machine à 17 paniques noyau, tout lot reprenable.
- Aucune observation à l'inférence pour le produit `PARTOUT`.
- Réponse en **`.md`**, une section par numéro.
