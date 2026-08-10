# Brief de recherche — les particularités départementales qui gouvernent la qualité de l'air

**Destinataire : un assistant de recherche avec accès au web (ChatGPT).**
**Commanditaire : une AASQA** — association agréée de surveillance de la qualité de l'air.

Ce document est un **cahier des charges**, pas une conversation. Lis-le en entier avant de
produire quoi que ce soit. Le format de sortie est imposé et sera **analysé par programme** :
un écart de structure rend la réponse inutilisable.

---

## 1. Le contexte, en trois phrases

Nous corrigeons par apprentissage les prévisions du modèle européen CAMS aux stations de
mesure françaises, puis nous publions le résultat sous forme de tableaux de bord : un
niveau national, un niveau régional, et **un niveau départemental — 84 départements**.

Le niveau départemental affiche aujourd'hui **nos mesures** : nombre de stations, erreur du
modèle brut, erreur après correction, gain, épisodes détectés et manqués. Ces chiffres sont
justes mais **muets** : ils disent *de combien* on s'améliore, jamais *pourquoi ce
territoire se comporte comme il se comporte*.

**Ta mission est de fournir exactement ce qui manque : le contexte physique, économique et
réglementaire qui explique la singularité de chaque département.**

---

## 2. Ce que nous avons déjà — et que tu ne dois donc PAS produire

> 🔴 **Interdiction absolue de produire un chiffre décrivant nos données ou nos
> performances.** Nous les avons mesurés ; toute valeur que tu inventerais entrerait en
> conflit avec la mesure et devrait être retirée.

Ne produis **jamais** :

- des concentrations moyennes de NO₂/O₃/PM10/PM2,5 par département « de mémoire » ;
- un nombre de stations, un nombre de dépassements, un gain de modèle ;
- un classement des départements « les plus pollués » fondé sur ton intuition ;
- des moyennes nationales chiffrées non sourcées.

Un chiffre n'est admis que s'il est **cité d'une source nommée, datée et vérifiable** — et
il est alors accompagné de son URL. Sinon, écris la particularité en clair **sans chiffre**.
Une phrase juste sans nombre vaut infiniment mieux qu'un nombre plausible et faux.

---

## 3. La question, précisément

Pour chaque département : **qu'est-ce qui fait que sa qualité de l'air ne ressemble pas à la
moyenne française, et que doit savoir quelqu'un qui prévoit ses concentrations ?**

Cinq angles, dans cet ordre de valeur :

### ① Les sources dominantes — ce qui est émis ici et pas ailleurs
Industrie lourde et son type (sidérurgie, pétrochimie, cimenterie, incinération), port de
commerce et trafic maritime, aéroport, autoroute de transit, chauffage résidentiel au bois,
agriculture — en distinguant **élevage** (ammoniac → nitrate d'ammonium particulaire) et
**grandes cultures** (épandages, travail du sol, brûlage), viticulture, écobuage.
Ce qui compte est ce qui **s'écarte** du profil national, pas l'inventaire exhaustif.

### ② La topographie et le climat — ce qui disperse ou ce qui piège
Vallée encaissée et inversions thermiques hivernales, cuvette, plaine ouverte, littoral et
brises de mer, altitude, vents dominants **nommés** (mistral, tramontane, autan, foehn),
ensoleillement. C'est souvent l'explication la plus forte et la plus oubliée : deux
départements aux émissions comparables n'ont pas la même qualité de l'air si l'un est
ventilé et l'autre non.

### ③ Le régime d'épisodes — quand, quel polluant, par quel mécanisme
Exemples de mécanismes attendus : PM10 hivernales par inversion + chauffage au bois ; nitrate
d'ammonium au printemps par épandages ; ozone estival photochimique ; poussières sahariennes ;
panache industriel par vent de secteur donné ; feux de biomasse et écobuage.
**Nomme la saison et le mécanisme**, pas seulement le polluant.

### ④ Le transport longue distance — ce qui arrive de l'extérieur
Import transfrontalier (Benelux et Ruhr, plaine du Pô, péninsule ibérique), poussières
sahariennes, panaches de feux. Précise le **régime de vent** qui l'amène quand tu le sais.

### ⑤ Le cadre de décision — ce qui est déjà en place
PPA (plan de protection de l'atmosphère) et son périmètre, ZFE-m effective ou annoncée,
contentieux européen sur le NO₂, zone sensible. Donne l'**état à jour** et sa date.

### Et le champ qui nous sert le plus : ⑥ les pièges de modélisation
**Qu'est-ce qui, ici, ferait qu'un modèle de qualité de l'air se trompe ?**
Une station de fond en vallée que le maillage à 10 km ne voit pas · un panache industriel
ponctuel invisible à un modèle d'émissions moyennées · une brise de mer qui inverse le
gradient en après-midi · une station urbaine dominée par une rue-canyon · un relief sous la
résolution du modèle. C'est le champ que personne n'écrit jamais et celui qui a le plus de
valeur pour nous : écris-le même quand il est spéculatif, **en le marquant comme tel**.

---

## 4. Les règles de rigueur — non négociables

1. **Chaque affirmation porte une source.** Nom de l'organisme, titre du document, année,
   URL. Une affirmation sans source est écrite dans `sans_source`, jamais mélangée aux
   autres.
2. **Distingue le mesuré de l'affirmé.** « Atmo X mesure un dépassement récurrent à la
   station Y » et « le département est réputé exposé » ne sont pas la même chose.
3. **`confiance` obligatoire** sur chaque bloc : `haute` (source institutionnelle explicite),
   `moyenne` (déduit de plusieurs sources concordantes), `basse` (plausible, non vérifié).
4. **Le vide est une réponse acceptable et souhaitable.** Si un département n'a pas de
   particularité documentée sur un angle, écris `null`. **Ne comble jamais un blanc par une
   généralité vraie partout** — « le trafic routier contribue aux émissions de NO₂ » n'apporte
   rien et pollue la base.
5. **Pas de recopie d'une fiche Wikipédia de géographie générale.** Nous voulons ce qui
   touche l'air, pas la superficie ni la démographie — sauf quand la démographie EST le
   facteur (densité francilienne, désert rural).
6. **Une particularité doit être différenciante.** Test à s'appliquer : *cette phrase
   serait-elle vraie pour 60 des 84 départements ?* Si oui, elle ne sert à rien — supprime-la.

---

## 5. Sources à privilégier — commence par elles

| source | ce qu'on y trouve |
|---|---|
| **Rapports annuels et bilans des AASQA** (Atmo Occitanie, Atmo Sud, Atmo AURA, Atmo Grand Est, Atmo Hauts-de-France, Airparif…) | le bilan par territoire, les épisodes de l'année, les sources locales — **la meilleure source de loin** |
| **PPA départementaux ou d'agglomération** (DREAL / préfectures) | diagnostic des sources, secteurs contributeurs, mesures |
| **CITEPA** et inventaires régionaux d'émissions | répartition sectorielle des émissions |
| **LCSQA / Géod'Air** | typologie des stations, méthodologie, épisodes nationaux |
| **Préfectures** — arrêtés d'épisode | mécanismes réellement invoqués lors des déclenchements |
| **Météo-France** | régimes de vent, climatologie locale |

Évite les sites d'actualité généralistes et les agrégateurs de « villes les plus polluées ».

---

## 6. Format de sortie — imposé

Un bloc **YAML** par département, dans un seul bloc de code. Rien d'autre : pas
d'introduction, pas de conclusion, pas de commentaire hors YAML. Les clés sont en français,
sans accent, exactement comme ci-dessous.

```yaml
- code: "31"
  nom: "Haute-Garonne"
  region: "Occitanie"
  resume: >
    Une phrase de 25 mots maximum : ce qui singularise ce departement pour la
    qualite de l'air. C'est le texte qui s'affichera en tete de la page.
  sources_dominantes:
    - libelle: "Trafic de transit et periurbain de l'agglomeration toulousaine"
      polluants: ["NO2", "PM2.5"]
      confiance: "haute"
      source: "Atmo Occitanie, Bilan annuel 2023, p. 12 — https://…"
    - libelle: "Agriculture de grandes cultures — epandages de printemps"
      polluants: ["PM10"]
      confiance: "moyenne"
      source: "PPA de l'agglomeration toulousaine, DREAL Occitanie, 2019 — https://…"
  topographie_climat:
    libelle: >
      Plaine de la Garonne ouverte au vent d'autan de sud-est, qui ventile
      fortement mais peut aussi rabattre le panache urbain vers le nord-ouest.
    effet: "dispersif"        # dispersif | piegeant | mixte
    vents_nommes: ["autan"]
    confiance: "moyenne"
    source: "…"
  regime_episodes:
    - saison: "hiver"          # hiver | printemps | ete | automne | toute_annee
      polluant: "PM10"
      mecanisme: "Inversion thermique nocturne et chauffage residentiel au bois"
      confiance: "haute"
      source: "…"
  transport_longue_distance:
    - origine: "Sahara"
      polluant: "PM10"
      regime: "flux de sud en fin d'hiver et au printemps"
      confiance: "haute"
      source: "…"
  cadre_decision:
    ppa: "PPA de l'agglomeration toulousaine, revise en 2019"
    zfe: "ZFE-m de Toulouse Metropole, en vigueur depuis 2022"
    contentieux_no2: false
    confiance: "haute"
    source: "…"
  pieges_modelisation:
    - libelle: >
        Les stations de proximite trafic du centre toulousain sont en rue-canyon :
        un modele a maille kilometrique ne peut pas reproduire leur niveau.
      confiance: "moyenne"
      speculatif: false
  sans_source:
    - "Affirmation retenue mais qu'aucune source n'a pu etayer."
```

**Contraintes de forme :**

- `code` est une **chaîne** — `"01"`, `"2A"`, `"2B"` gardent leur forme exacte.
- `polluants` n'utilise que : `NO2`, `O3`, `PM10`, `PM2.5`, `SO2`, `NH3`, `COV`, `benzene`.
- `effet` ∈ {`dispersif`, `piegeant`, `mixte`} · `saison` ∈ {`hiver`, `printemps`, `ete`,
  `automne`, `toute_annee`} · `confiance` ∈ {`haute`, `moyenne`, `basse`}.
- Toute liste vide s'écrit `null`, jamais `[]` ni une phrase d'excuse.
- Pas d'accent dans les **valeurs** des champs courts (`libelle` et `resume` peuvent en
  porter, le reste non) — cela évite les surprises d'encodage à l'ingestion.
- `resume` ≤ 25 mots. C'est un affichage, pas un paragraphe.

---

## 7. Ordre de travail — et il compte

**Commence par l'Occitanie**, c'est notre région de référence et elle sera relue en premier :

> **30** Gard · **31** Haute-Garonne · **32** Gers · **34** Hérault · **65** Hautes-Pyrénées ·
> **66** Pyrénées-Orientales · **81** Tarn

Puis, par ordre de valeur — les départements aux régimes les plus marqués, où le contexte
explique le plus :

> **13** Bouches-du-Rhône · **59** Nord · **62** Pas-de-Calais · **69** Rhône · **74** Haute-Savoie ·
> **73** Savoie · **38** Isère · **75** Paris · **92** Hauts-de-Seine · **93** Seine-Saint-Denis ·
> **06** Alpes-Maritimes · **83** Var · **84** Vaucluse · **76** Seine-Maritime · **57** Moselle ·
> **67** Bas-Rhin · **68** Haut-Rhin · **33** Gironde · **44** Loire-Atlantique · **63** Puy-de-Dôme

**Puis les 57 restants**, dans l'ordre numérique :

> 01 Ain · 02 Aisne · 03 Allier · 05 Hautes-Alpes · 08 Ardennes · 10 Aube · 14 Calvados ·
> 15 Cantal · 16 Charente · 17 Charente-Maritime · 18 Cher · 19 Corrèze · 21 Côte-d'Or ·
> 22 Côtes-d'Armor · 23 Creuse · 25 Doubs · 26 Drôme · 27 Eure · 28 Eure-et-Loir · 29 Finistère ·
> 2A Corse-du-Sud · 2B Haute-Corse · 35 Ille-et-Vilaine · 36 Indre · 37 Indre-et-Loire ·
> 39 Jura · 40 Landes · 41 Loir-et-Cher · 42 Loire · 43 Haute-Loire · 45 Loiret ·
> 49 Maine-et-Loire · 50 Manche · 51 Marne · 53 Mayenne · 54 Meurthe-et-Moselle · 55 Meuse ·
> 56 Morbihan · 58 Nièvre · 60 Oise · 61 Orne · 64 Pyrénées-Atlantiques · 71 Saône-et-Loire ·
> 72 Sarthe · 77 Seine-et-Marne · 78 Yvelines · 79 Deux-Sèvres · 80 Somme · 85 Vendée ·
> 86 Vienne · 87 Haute-Vienne · 88 Vosges · 89 Yonne · 90 Territoire de Belfort · 91 Essonne ·
> 94 Val-de-Marne · 95 Val-d'Oise

**Ces 84 sont la liste exacte**, et elle a été comptée, pas estimée : 84 des 96 départements
métropolitains. N'en ajoute aucun. Les **douze absents** — `04` `07` `09` `11` `12` `24` `46`
`47` `48` `52` `70` `82` — n'ont pas assez de stations dans notre panel pour porter une page ;
un bloc écrit pour eux est du travail perdu. *(Six d'entre eux sont occitans — Ariège, Aude,
Aveyron, Lot, Lozère, Tarn-et-Garonne : l'Occitanie compte 13 départements et n'en présente
donc que 7. C'est une densité de réseau, pas un oubli.)*

**Livre par lots** : d'abord les 7 de l'Occitanie, et **arrête-toi** pour validation. Nous te
dirons de continuer. Cela évite de produire 84 blocs dans un format que nous aurions voulu
corriger au premier.

---

## 8. Le test de qualité, à t'appliquer avant de rendre

Relis ta sortie et supprime tout ce qui échoue à l'un de ces trois tests :

1. **Le test du différenciant** — cette ligne serait-elle vraie pour la majorité des
   départements ? Alors elle ne dit rien.
2. **Le test de la source** — puis-je ouvrir l'URL et y retrouver l'affirmation ? Sinon,
   elle descend dans `sans_source` ou disparaît.
3. **Le test de l'utilité** — un prévisionniste qui lit cette ligne fait-il quelque chose de
   différent ? Si la réponse est non, elle est décorative.

Le meilleur rendu possible n'est pas le plus long : c'est celui où **chaque ligne survit aux
trois tests**.
