# Palier A — rendre les chiffres réfutables avant d'en chercher de nouveaux

*23 août 2026. Ce document n'annonce aucun gain de score : il dit ce que les chiffres
déjà publiés valent réellement, et ce que le plan d'expérience sait ou ne sait pas
trancher. Trois d'entre eux ont changé de statut.*

---

## Ce que le palier a déplacé, en une page

| | avant | après | ce qui l'a fait bouger |
|---|---|---|---|
| **28 ratios d'échelle** | ✅ tient, p_PC = 0,0006 | 🔴 **réfuté** | le `p` était bilatéral : PM10 à **−0,66 %** comptait comme une confirmation |
| **précurseurs, moyennes ET maxima** | ✅ tient, p_PC = 0,0288 | 🔴 **non confirmé** (0,1185) | le bootstrap est asymptotique sur 9 blocs ; la permutation est exacte |
| **étalon ozone CCQM.O3.2019** | inconclusif, 1 mois | **non détecté**, 12 mois, ±2,70 pt | l'archive CAMS s'est remplie ; le blocage de 2026-08-02 n'existait plus |
| **apport des 9 familles** | 9 étages cumulés | **3 démontrées, 3 sans puissance, 3 vides** | l'apport se mesure en dernière position, pas dans l'ordre d'empilement |

---

## 1. Le défaut qui a tout déclenché — un `p` qui ne regardait pas le signe

La conjonction partielle de Benjamini-Heller teste *« l'effet est présent dans au moins
deux groupes »*. Alimentée par des `p` **bilatéraux**, elle ne distingue pas un groupe
qui confirme d'un groupe qui contredit :

```
③ + ratios des 5 familles (28)
  NO2   +1,212 %   p = 0,0002      ← aide
  PM10  −0,657 %   p = 0,0002      ← NUIT, avec la même force
  → « ✅ TIENT sur deux groupes »
```

Deux groupes significatifs, oui — **de signes opposés**. La configuration allait entrer
dans la pile. Les `p` sont devenus unilatéraux : `p⁺` alimente la conjonction, `p⁻`
réfute, et **la réfutation se teste avant la conjonction**.

Le seuil de réfutation n'est pas corrigé pour la multiplicité, délibérément : ne pas
promouvoir une famille utile se répare par une mesure de plus, publier une famille qui
nuit ne se répare pas.

---

## 2. L'instrument saturait — la permutation remplace le bootstrap

En calibrant le criblage, **cinq configurations sur dix rendaient exactement 0,0003**. Ce
n'est pas un accord : c'est le plancher du bootstrap, `3 × 1/(B+1)`. Avec 8 à 12 blocs et
un effet régulier, aucun rééchantillon ne traverse zéro.

Sous H₀, le signe de l'écart d'un bloc est **échangeable**. Le test exact est donc la
permutation par retournement de signe. Le `p` y passe ; **l'IC95 reste au bootstrap**, qui
est bon à cela et que la permutation ne sait pas produire.

Une seule conclusion bascule, et elle est actionnable : *« précurseurs, moyennes ET
maxima »* (8 colonnes) tombe, *« moyennes seules »* (4 colonnes) tient sur les deux axes.
**La pile en service porte la variante à 8 colonnes.**

---

## 3. Ce que chaque famille paie vraiment

La colonne `apport_marginal_pct` mesure un apport **dans l'ordre d'empilement** : la
famille placée tôt encaisse ce qu'elle partage avec les suivantes. Le seul apport
interprétable est celui de la **dernière position** — la pile complète moins la famille.

| | famille | apport | lecture |
|---|---|---|---|
| ✅ | **typologie** | +3,39 pt | démontrée |
| ✅ | **geoscf** | +0,48 pt | démontrée |
| ✅ | **fourier** | +0,28 pt | démontrée |
| 🟠 | **speciation** | +1,25 pt | p_PC = 0,065 · **les 4 polluants positifs** |
| 🟠 | **precurseurs** | +0,64 pt | p_PC = 0,095 · les 4 positifs |
| 🟠 | **membres** | +0,43 pt | les 4 positifs |
| 🔴 | **profil** | +0,01 pt | rien |
| 🔴 | **tendance** | −0,07 pt | **réfutée** — nuit au NO₂, −0,22 pt |
| 🔴 | **feux** | −0,17 pt | 3 polluants sur 4 négatifs |

**🟠 n'est pas 🔴, et les confondre coûterait cher.** Sur huit blocs, aucun `p_PC` de
permutation ne peut descendre sous **0,0117**, quel que soit l'effet. La spéciation à
+1,25 pt avec quatre polluants positifs n'est pas réfutée : elle est **hors de portée de
ce plan**. La réponse est de gagner des mois, pas de retirer la famille.

---

## 4. Ce que le protocole sait résoudre — et ce qu'il ne sait pas

| grandeur | valeur | conséquence |
|---|---|---|
| résolution de l'écart apparié | **±0,36 à ±0,48 %** | un gain sous ce seuil n'est pas un petit résultat, c'est un non-résultat |
| plancher de `p_PC` à 8 blocs | **0,0117** | un effet modeste ne PEUT pas y être significatif |
| taille réelle du test | **0,0015** | la conjonction partielle est **34× plus sévère** que son seuil nominal |
| seuil calibré après criblage de 10 | **0,0974** | le criblage **ne consomme pas** le budget — c'est la sévérité du test qui écarte |

Le dernier point renverse une réserve que le dépôt portait : entre 0,05 et 0,097, un
résultat n'est pas écarté par le criblage. Il est écarté par la sévérité du test, **ce qui
n'est pas la même réserve** — et le chiffre reste un minorant, les pistes abandonnées
avant d'écrire un CSV n'étant pas comptées.

---

## 5. Les garde-fous posés, et ce qu'ils attrapent

| mécanisme | ce qu'il rend impossible |
|---|---|
| `rendre_verdict` + 9 tests | un groupe en sens inverse compté comme une confirmation |
| `ablation_jointe.py` · garde de fenêtre | conclure d'un écart entre **deux fenêtres différentes** |
| `controle_pretraitement.py` + 6 tests | une dérive du corpus, **dans les deux sens** — un plancher ne voit pas un corpus qui gonfle, et le doublon d'appariement gonflait |
| `registre.py` | une prédiction reformulée après la mesure |
| `calibrer_criblage.py` | citer un biais de criblage venu d'une autre expérience |

---

## 6. Ce qui reste ouvert

1. **Trois prédictions scellées** attendent leurs mesures — ablations jointes
   `feux+tendance` et `membres+geoscf`, en file.
2. **`precurseurs` à 4 colonnes plutôt que 8** — à mesurer, pas à décider ici : choisir
   après avoir vu les résultats est du criblage, et le score d'une pile élaguée se
   re-mesure sur des plis qui n'ont pas servi à la choisir.
3. **Gagner des blocs.** Trois familles sont hors de portée par manque de mois, pas par
   absence d'effet. C'est le levier qui débloque le plus de questions à la fois.
