# Le prétraitement partagé avait deux défauts — ce qu'ils coûtaient, ce que le correctif déplace

**22/08/2026.** Deux défauts trouvés dans les deux fonctions que **tous** les scripts
journaliers appellent — 69 scripts passent par `agreger_journalier`. Aucun des deux ne levait
d'exception : ils produisaient des nombres plausibles.

Ce document existe pour que le déplacement des chiffres soit **vérifiable**, pas seulement
annoncé. Les mesures sont régénérables : `python3 scripts/apport_ratios_echelle.py` avant et
après, puis `reports/impact_correctif_pretraitement.csv`.

---

## ① La clé d'appariement n'était pas unique

`fit_mos.paires_cams_observations` — que sa propre docstring appelle « point d'entrée unique
de l'appariement » — rendait **5 à 6 % de lignes en double** :

| polluant | copies exactes | part du corpus horaire |
|---|---|---|
| NO₂ | 467 326 | 5,22 % |
| O₃ | 375 294 | 5,23 % |
| PM10 | 418 039 | 5,83 % |
| PM2,5 | 302 815 | 4,97 % |

Copies **strictement identiques** — même échéance, même valeur CAMS, même observation — et
toutes confinées à **2024-01, 2024-02 et le 1er mars 2024**.

**La cause n'est pas le panel d'observations** : `panel_unifie_lcsqa.parquet` est propre,
29 669 240 lignes pour autant de clés. Ce sont les **fichiers de prévision CAMS** : janvier et
février 2024 ont été téléchargés deux fois, une fois seuls et une fois groupés.

```
cams_prevision_metropole_o3_202401.parquet          2024-01-01 → 2024-02-04
cams_prevision_metropole_o3_202401_202402.parquet   2024-01-01 → 2024-03-04   ← recouvre janvier
cams_prevision_metropole_o3_202402_202403.parquet   2024-02-01 → 2024-04-04   ← recouvre février
```

> ⚠️ **Le nettoyage évident était faux.** Supprimer le fichier groupé comme redondant aurait
> retiré **331 296 lignes qu'aucun autre fichier ne porte** — vérifié avant d'agir. Les trois
> se chevauchent partiellement et chacun porte de l'unique : c'est l'**union dédoublonnée**
> qui est juste. Le débordement de 4 jours en fin de chaque fichier, lui, ne duplique rien —
> ce sont d'autres échéances du même horodatage.

**Ce que ça faussait** : chaque ligne de ces deux mois pesait **double** à l'apprentissage et
au score ; `n_heures` doublait, donc le filtre des 75 % ne filtrait plus rien ; et la fenêtre
glissante ci-dessous s'en trouvait resserrée de moitié.

---

## ② La fenêtre « 8 h » comptait des LIGNES, pas des HEURES

`max_glissant_8h` faisait `rolling(8, min_periods=6)` sur une série non réindexée sur une
grille horaire continue. Un trou l'étalait au-delà de 8 heures ; **un doublon la resserrait à
4 heures réelles**. Les deux défauts se composaient donc exactement là où ① frappait.

La grandeur produite n'était alors plus celle du texte : la valeur cible européenne de
l'ozone, le MQI FAIRMODE et le sous-indice ATMO sont définis sur **8 heures d'horloge**.

**Mesuré sur l'ozone, à filtre de couverture identique** — 283 512 jours-station :

* **7,96 %** portaient une cible différente de la bonne ;
* sur ces jours-là : écart absolu médian **2,17 µg/m³**, p90 7,42, p99 15,30, max 46,20 ;
* biais moyen **+1,99 µg/m³** — la version en lignes **surestime** le maximum ;
* et la casse n'était pas diffuse :

| mois | jours-station à cible fausse |
|---|---|
| **2024-02** | **99,9 %** |
| **2024-01** | **98,6 %** |
| 2024-03 | 7,8 % |
| les 34 autres mois | 2,4 % en moyenne |

Deux mois entiers du corpus avaient une cible ozone qui n'était pas la grandeur réglementaire.

---

## Ce que le correctif déplace — mêmes plis, mêmes graines, mêmes colonnes

Configuration de base, double aveugle station **et** mois cachés, J+1. Seul le prétraitement
change.

| polluant | grandeur cible | gain avant | gain après | Δ |
|---|---|---|---|---|
| **NO₂** | max horaire | +27,895 % | +27,782 % | **−0,113 pt** |
| **O₃** | max 8 h | +5,719 % | **+6,117 %** | **+0,398 pt** |
| **PM10** | moyenne jour | +12,722 % | **+13,040 %** | **+0,317 pt** |
| **PM2,5** | moyenne jour | +4,489 % | **+5,581 %** | **+1,092 pt** |

**Les deux causes se séparent proprement.** PM10 et PM2,5 utilisent la moyenne journalière,
insensible à la fenêtre 8 h : leur gain vient **entièrement du dédoublonnage**, et ce sont
justement deux mois d'hiver — les plus chargés en particules — qui comptaient double. Le NO₂
est le seul à perdre : son maximum horaire ne bougeait pas, seul le poids des lignes changeait.

> 🔑 **Les chiffres publiés étaient sous-estimés sur trois polluants sur quatre**, et de près
> d'un quart en relatif sur PM2,5. Un correctif qui améliore son propre score demande plus de
> prudence qu'un correctif qui le dégrade : c'est pourquoi il est mesuré **apparié**, à plis
> et graines identiques, avec le prétraitement pour seule différence.

⚠️ **Portée** : ces chiffres sont ceux de la configuration **de base** sur le corpus complet
(37 mois), non ceux de la pile complète du dossier, qui tourne sur la fenêtre GEOS-CF. La
direction et l'ordre de grandeur transfèrent ; les valeurs publiées demandent de rejouer
`methode_maximale.py`.

---

## Les correctifs, et ce qui les rend durables

1. **Dédoublonnage au point d'entrée**, qui **lève** si deux copies divergent — un doublon
   exact se jette sans rien perdre, un conflit de source pose une question qu'aucun
   `drop_duplicates` ne doit trancher seul.
2. **`moyenne_glissante_8h(d, colonne)`** sur `rolling("8h")` à index temporel. Sur une grille
   propre et continue, elle rend **exactement** ce que rendait `rolling(8)` : le correctif ne
   déplace que ce qui était faux.
3. **`max_glissant_8h` lève** au lieu de disparaître — un appelant oublié doit échouer, pas
   retomber en silence sur la grandeur fausse.
4. **Les quatre jumeaux corrigés** (§ 4 bis) : `comparer_mos_officiel`,
   `test_hors_echantillon_2025`, `duel_chimere_krigeage`, `mqi_bon_grain`.
5. **Le filtre des 75 % compte et imprime** ce qu'il écarte — 4 249 jours-station sur NO₂,
   3 430 sur O₃, jusqu'à 5,6 % sur un mois de bord (§ 2 quater).
6. **La sentinelle `30 000`** ne s'applique plus qu'aux distances et **lève** sur toute autre
   colonne infinie. ⚠️ Elle ne remplaçait **rien** aujourd'hui — zéro valeur infinie sur les
   53 colonnes admises : mine dormante rendue bruyante, pas défaut réalisé.
7. **`tests/test_cible_journaliere.py`** fige six propriétés — identité sur grille propre,
   sensibilité au trou, insensibilité au doublon, étanchéité entre stations, refus d'une table
   non triée, et l'ancienne fonction qui lève. **296 tests passent.**

---

## Comment ils ont été trouvés

Non par relecture : en **mesurant un soupçon**. La question posée était « la fenêtre 8 h
compte-t-elle des lignes ou des heures ? », et la réponse a demandé de compter les sauts
horaires du corpus. La duplication est apparue ensuite, en vérifiant l'unicité de la clé avant
d'écrire le correctif — un contrôle qui n'existait nulle part.

C'est la règle 5 de `CLAUDE.md` appliquée au prétraitement : *si ce traitement produisait une
grandeur qui n'est pas celle que je crois, est-ce que je m'en apercevrais ?* Sans le compter,
la réponse était non.
