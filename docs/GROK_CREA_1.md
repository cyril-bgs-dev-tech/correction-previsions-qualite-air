# GROK CREA 1 — La figure maîtresse (30 juillet 2026)

État dossier : en-tête `docs/TACHES_GROK_CREATIVITE.md`. Une image, page 1, 10 secondes, vidéoprojecteur médiocre.

---

## Trois candidates

### A — « Le jour où ça casse » (26/07/2026)

**On y voit :** trois barres côte à côte, une couleur chacune — CAMS **49,6** · obs **46,8** · correction **36,6** — et, à droite ou en surimpression grisée, la même scène **avec règle d'abstention** : correction désactivée → on reste sur CAMS (~erreur ÷3,6). Un seul mot sous le graphique : *alerte PM, Occitanie*.

**Prouve :** le travail n'est pas « +30 % moyen » — c'est un correctif qui peut **sous-alarmer un jour juste**, et une règle qui le rattrape. En dix secondes : risque + filet.

**Ne prouve pas :** que la règle généralise (0,28 % des cas) ; le +28–34 % réglementaire ; la leave-station ; O₃.

### B — « Deux nuages, un message » (dérive du forçage)

**On y voit :** nuage de points **mois × (RMSE CAMS saison-égale en abscisse, gain du correctif en ordonnée)**, ~17 points gros, une droite légère sans équation. Titre unique : *plus CAMS se dégrade, plus le correctif gagne*. Pas de sept séries.

**Prouve :** le gain n'est pas magique — il se concentre où le forçage dérive (ta thèse lisible sans paragraphe).

**Ne prouve pas :** causalité pure (régression vers la moyenne non tranchée visuellement) ; le service rendu un lundi ; l'abstention.

### C — « Avant / après au seuil » (POD)

**On y voit :** deux grands nombres seulement — POD **0,325 → 0,389** — sous-titre une ligne : *même modèle, règle d'abstention, 3,2 M de couples*. Eventuellement une pastille « RMSE +0,02 ». Rien d'autre.

**Prouve :** un levier ops minuscule en fréquence (0,28 %) qui **bouge la détection** sans casser le RMSE — langage service, pas Kaggle.

**Ne prouve pas :** le cas 26/07 concret ; le +30 % leave-station ; pourquoi la règle existe.

---

## Choix : **A**

**Pourquoi A gagne.** Un non-lecteur de la suite retient une **histoire de métier** (jour d'alerte, chiffre trop bas, filet) — pas un coefficient. C'est la seule des trois qui répond en silence à « qu'est-ce que ça me fait gagner / éviter lundi ? ». Sur vidéoprojecteur : trois barres > nuage > deux pourcentages abstraits.

**Pourquoi B perd en page 1.** Juste, mais « académique » : le recruteur entend une thèse avant d'entendre un usage. Garde-la page 3–4 (mécanisme). Risque : qu'on te réduise à « tu surfe sur les pannes CAMS » sans avoir vu le filet.

**Pourquoi C perd en page 1.** Trop propre, trop peu incarné. 0,325→0,389 sans le 36,6 ne fait pas mal au ventre — or c'est le mal au ventre qui ouvre le dossier. C en slide « règle » juste après A.

---

## Spec minimale si tu la produis

| Élément | Oui / non |
|--------|-----------|
| Légende longue, axes multiples, RMSE global | non |
| Unités µg/m³ visibles | oui |
| Seuil d'alerte en pointillé horizontal si pertinent PM | oui, une ligne max |
| Logo / 5 logos partenaires | non |
| Mention « stations exclues » | non sur cette figure (page suivante) |

---

## Retenu / écarté

| Idée | Statut | Raison |
|------|--------|--------|
| Figure A (26/07 + abstention) | **Retenue** page 1 | Seule à porter risque + filet en 10 s |
| Figure B (nuage dérive) | **Écartée** page 1 ; **gardée** corps | Thèse forte, mauvais ouvreur humain |
| Figure C (POD 0,325→0,389) | **Écartée** page 1 ; **gardée** slide règle | Chiffre service, pas d'incarnation |
| Courbe multi-séries / dashboard | **Écartée** | Contrainte brief |

**Avant livrable :** confronter les 49,6 / 46,8 / 36,6 et le « ÷3,6 » aux données du jour (station, polluant, horizon) — ne pas figer la figure sur des chiffres non gelés.
