# Revue de design n° 2 — réponse au brief

> Réponse à `docs/BRIEF_2_DESIGN_KIMI.md`. Une section par numéro ; chaque
> recommandation porte : **la règle · ce qu'elle remplace · le code · le contrôle
> mécanique**. Tout ce qui est affirmé ici a été vérifié dans les artefacts actuels
> (`app.py` 746 lignes, `presentation_atmo.html`, `_p*_style.css`, `_p*_script.js`,
> `exporter_pdf.py`) le 17/08/2026.

---

## § 1 — Le registre : le problème n'est pas 36 blocs, c'est 5 actes de parole dans une même couleur

### La mesure qui manque au brief

J'ai relu les 36 blocs un par un. Le mélange n'est pas seulement visuel : **un même
habitat porte des actes de parole différents**. `st.info` porte aujourd'hui cinq choses
incompatibles — une absence de claim (PM10 non mesuré, l. 280), une couverture (ERA5,
l. 289), un cas d'usage vide (l. 634), **un verdict** (« X % des stations sont
améliorées », l. 429) et une interprétation dérivée (l. 687). `st.caption` porte des
réserves (plis non bloqués, l. 412) *et* de la narration (« Trier par écart absolu
désigne… », l. 299). Le lecteur ne peut pas apprendre le code, parce que le code ne
code rien.

### La règle — un seul critère : **que perd le lecteur qui saute ce bloc ?**

| réponse | acte | habitat autorisé |
|---|---|---|
| le chiffre devient **faux** | **réserve** | le composant `.reserve` (§ 3), jamais autre chose |
| le chiffre devient **introuvable** | provenance | `caption` nu, sans composant |
| **rien** | narration | candidat à suppression — pas parce qu'il est lourd, parce qu'il **dilue les réserves** |

Votre axe proposé (« error = ne pas citer · warning = périmètre · caption = provenance »)
est le bon — il classe par **ce que le lecteur doit faire**, pas par le ton de
l'auteur. Il ne garde que trois habitats, et c'est exactement ce qu'il faut : **deux
niveaux de réserve + la provenance**. `success` n'est pas un habitat de réserve, c'est
un verdict ; `info` cesse d'exister comme fourre-tout.

Réponse à la question 1 : **non, un jury ne lit pas une nuance** — donc une réserve qui
n'est pas *attachée* à son chiffre n'existe pas. C'est ce qui motive le composant du
§ 3 : la réserve doit être structurellement soudée au nombre qu'elle borne, pas posée
dans un bloc voisin.

Réponse à la question 3 : **oui, deux niveaux suffisent** — la règle de choix est au
§ 3.2.

### Les huit blocs, au cas par cas

Aucun n'est faux. Deux fusions sont légitimes au titre de « déplacé » — pas une seule
réserve ne disparaît :

| # | verdict | pourquoi |
|---|---|---|
| 1 bandes dérivées | **garder** | dérivée de la figure, elle ne peut plus la contredire |
| 2 plis non bloqués | **garder** | c'est la réserve « le score est-il optimiste ? » — le cœur du ④ |
| 3 régime descriptif | **fusionner avec 4** | même sujet, même page, deux blocs pour une seule réserve — la clause « description nationale » est le chapeau naturel du bloc 4 |
| 4 périmètre de l'étude | **garder** (absorbe 3) | porte les trois mots mesurés |
| 5 triple caption journalière | **réduire, sans rien perdre** : clause (a) « ignore le sélecteur » est **déplacée** — elle concerne le *geste*, pas la donnée → elle va dans le label du radio (« Classe d'indice journalière — multi-polluants, ignore le sélecteur »). Clauses (b)+(c) : un seul sujet (« cet indice n'est pas l'indice publié ») → une seule phrase | |
| 6 écart par seuil | **garder** | c'est le garde-fou du verdict, deux lignes |
| 7 écrêtage de la carte | **garder** | déjà conditionnel (`if hors:`) |
| 8 prototype + cinq mots | **garder** | c'est la signature (§ 2) — elle change de forme, pas de contenu |

Bilan : **36 → 35 blocs, zéro réserve supprimée** — une fusion (3+4), un déplacement
vers le contrôle qu'il concerne (5a → le label du radio), et la triple caption réduite à
sa seule clause non redondante.

### Le contrôle mécanique

Le test d'ignorance est lexical, donc scriptable : tout bloc contenant `⚠️`, « ne pas »,
« jamais », « mesuré sur », « périmètre » est une **réserve** → il doit passer par le
composant. Voir § 3.4.

---

## § 2 — La signature : cinq mots, un seul endroit

### La mesure qui simplifie tout

**Les cinq dimensions sont constantes sur toute la démo.** Les sélecteurs changent le
polluant et l'échelle, jamais le protocole : échéance J0, grain horaire, pile de base,
stations exclues, corpus 2023-08→2026-08 — partout, tout le temps. Le dossier avait
besoin de `.sig3` sur *chaque figure* parce que ses échéances varient d'une page à
l'autre (J0/J+1/J+2) ; la démo n'a pas ce problème. **Une signature constante se dit
une fois, dans le seul emplacement persistant : la barre latérale.** Toute répétition
sur six pages la transformerait en mobilier — votre crainte 2.3 est juste, et c'est
pourquoi la réponse est *un* endroit, pas six.

### La règle

> **Ce qui ne varie pas se signe une fois, au plus visible ; ce qui varie se signe au
> plus près du chiffre.** Dans la démo, tout est invariant → une signature unique. La
> clause variable (« cette page ignore le sélecteur ») n'est pas de la signature, c'est
> une réserve locale — elle reste sur la page.

### Le code

Remplacer la caption « Échéance J0 » actuelle (l. 169-172) par le passeport complet —
même grammaire visuelle que `.sig3` (label monospace majuscule + valeur), qui existe
déjà dans le dossier :

```python
st.sidebar.markdown(
    '<div class="sig">'
    '<span>échéance</span><b>J0 — le jour même</b>'
    '<span>grain</span><b>horaire</b>'
    '<span>pile</span><b>base — CAMS + terrain + calendrier</b>'
    '<span>épreuve</span><b>stations exclues, mois vus</b>'
    '<span>corpus</span><b>2023-08 → 2026-08</b>'
    '<span>≠ dossier</span><b>J+1/J+2 · pile complète · double aveugle</b>'
    '</div>',
    unsafe_allow_html=True,
)
```

```css
.sig { display: grid; grid-template-columns: auto 1fr; gap: 3px 10px;
       padding: 10px 12px; border: 1px solid rgba(154,102,5,.45);
       border-radius: 3px; font-size: 12px; line-height: 1.5; }
.sig span { font-family: ui-monospace, monospace; font-size: 9px;
            text-transform: uppercase; letter-spacing: .1em; opacity: .65;
            align-self: center; }
.sig b { font-weight: 600; }
```

La dernière ligne — `≠ dossier` — est celle qui répond à votre question 2.3 : la
signature dit **toujours la même chose, et c'est voulu** ; son rôle n'est pas d'informer
à chaque visite, c'est d'être **introuvable-à-rater** le jour où un juré compare. Le
corpus se dérive des données (`jours[0]`, `jours[-1]` déjà calculés page ① — le mettre
dans une variable partagée), jamais en dur.

### Que garder des cinq ? — votre intuition est mesurée juste

`pile` et `épreuve` sont bien les deux qui font le plus mal, et le dossier le chiffre :
⑤→③, la pile fait **+3,31 % → +18,19 %** sur O₃ ; spatial→double aveugle, l'épreuve
fait **+24,10 % → +3,31 %**. Les deux bascules les plus violentes du § 7 ter portent
ces deux mots-là. Mais comme la signature est *unique*, les cinq y tiennent — la
question du tri ne se pose que si l'on répète.

### Faut-il faire converger la démo vers le dossier ? — **Non, et c'est mesuré**

Votre propre table le décide : **sur PM2,5 la démo (+14,4 %) est au-dessus du dossier ③
(+12,49 %)**. La démo n'est donc pas une version affaiblie du dossier — c'est **un autre
produit**, et il n'y a aucune direction de convergence qui soit uniformément favorable.
Le coût, lui, est certain : la pile complète exige `tendance` (donc la veille → périmètre
AUX STATIONS), GEOS-CF (s'arrête au 01/08/2026), les membres PM10 (2025-01), les feux
(2025-06) — le corpus se rabat sur l'intersection, la page « Aide à l'expertise » perd
sa matière, et le pré-calcul du § 3.2 du brief précédent se refait. En 5 jours, c'est
une refonte déguisée.

La bonne frontière : **la démo montre un produit, le dossier prouve une méthode** — et
la ligne `≠ dossier` du passeport est ce qui empêche le jury de les confondre. Ne pas
afficher le chiffre du dossier dans la démo : deux chiffres côte à côte invitent la
comparaison terme à terme que vos cinq dimensions interdisent (règle D).

---

## § 3 — Le composant : `.reserve`

### 3.1 La règle de composition

> **Une réserve ne s'écrit qu'à travers le composant.** Deux niveaux, jamais trois ;
> la provenance n'est pas une réserve et n'entre pas dans le composant.

### 3.2 Ce qu'elle remplace — et la règle de choix entre les deux niveaux

Côté démo : les 14 blocs `st.warning` / `st.info` / `st.caption` porteurs de réserves.
Côté dossier : `.note` (6 occurrences) et `.reserve` (1) — **`.limites` reste** (c'est
une section, pas une réserve) et **`.garde` reste** pour les pieds de carte (provenance,
pas réserve). Le composant n'ajoute donc pas un sixième habitat : il en remplace deux
et borne les autres.

Le choix du niveau tient en une question :

> **Le lecteur qui cite le chiffre en oubliant ce bloc dit-il quelque chose de faux ?**
> — oui → `.reserve--stop` · non, il dit quelque chose de juste sur un périmètre qu'il
> faut nommer → `.reserve` (borne).

Exemples mesurés dans l'état actuel : *stop* — la bannière d'échec de détection, « les
deux modèles manquent la majorité des épisodes sévères », « PM10 non mesuré » ; *borne* —
plis non bloqués, CAMS ≠ PREV'AIR, régime descriptif, écrêtage de la carte, indice
journalier partiel.

### 3.3 Le code — une structure, deux feuilles de style

HTML unique (les deux artefacts) :

```html
<div class="reserve" data-niveau="borne">
  <b>À ce périmètre.</b> Texte de la réserve.
</div>
<div class="reserve reserve--stop" data-niveau="stop">
  <b>Ne pas citer tel quel.</b> Texte de la réserve.
</div>
```

CSS **commun** (autonome — aucun jeton externe, donc aucun jeton fantôme possible ;
les fonds en `rgba` s'adaptent aux thèmes clair *et* sombre des deux hôtes, vérifié sur
les jetons fournis) :

```css
.reserve {
  margin: 10px 0; padding: 9px 13px 9px 12px;
  border-left: 3px solid #9A6605;            /* ambre — borne */
  background: rgba(233, 163, 23, .075);
  border-radius: 3px; font-size: 13px; line-height: 1.55;
  break-inside: avoid;                        /* le § 4.2 l'exige */
}
.reserve--stop { border-left-color: #A8452F; background: rgba(168, 69, 47, .085); }
.reserve > b { display: block; font-family: ui-monospace, monospace;
  font-size: 9.5px; text-transform: uppercase; letter-spacing: .11em;
  margin-bottom: 2px; opacity: .75; }
```

Côté présentation, on *peut* substituer `var(--ambre)` / `var(--refute)` — mais la
version littérale ci-dessus est délibérée : **le composant ne dépend d'aucun jeton de
l'hôte**, donc il ne peut pas hériter du défaut `--bord`. Côté Streamlit :

```python
# src/aq/demo.py
def reserve(texte: str, niveau: str = "borne") -> None:
    """La SEULE porte d'écriture d'une réserve — deux niveaux, pas de troisième."""
    assert niveau in ("borne", "stop"), f"niveau inconnu : {niveau}"
    etiquette = "À ce périmètre." if niveau == "borne" else "Ne pas citer tel quel."
    st.markdown(
        f'<div class="reserve{" reserve--stop" if niveau == "stop" else ""}">'
        f"<b>{etiquette}</b>{texte}</div>",
        unsafe_allow_html=True,
    )
```

(le CSS injecté une fois en tête de `app.py` via `st.markdown(f"<style>{CSS}</style>")`.)

### 3.4 Le contrôle mécanique — comment une réserve hors du composant est détectée

`scripts/auditer_reserves.py`, branché à la suite d'`auditer_regles.py` (même porte) :

```python
MARQUEURS = ("⚠️", "ne pas citer", "jamais", "ne pas ", "mesuré sur", "périmètre")
# ① démo : une réserve ne passe que par aq.demo.reserve()
for n, ligne in enumerate(Path("app.py").read_text().splitlines(), 1):
    if re.search(r"st\.(warning|info|error|caption)\(", ligne):
        corps = ligne
        if any(m in corps for m in MARQUEURS):
            print(f"app.py:{n} — réserve hors du composant"); sys.exit(1)
# ② dossier : ⚠️ ne vit que dans .reserve
for f in Path("reports/figures").glob("_p*_section.html"):
    for frag in re.findall(r'<[^>]*class="([^"]*)"[^>]*>[^<]*⚠️', f.read_text()):
        if "reserve" not in frag:
            print(f"{f.name} — ⚠️ hors .reserve : {frag}"); sys.exit(1)
# ③ le composant est protégé à l'impression
css = Path("reports/figures/presentation_atmo.html").read_text()
assert ".reserve" in css and "break-inside: avoid" in css
```

① et ② sont lexicaux et attrapent la récidive au moment du commit ; ③ rattache le
composant au garde d'impression du § 4.2.

---

## § 4 — Le PDF

### 4.1 La pièce courte — **elle existe déjà, il lui manque un panneau**

Ne pas créer un second document : un texte court *réécrit* à côté du long est une
**seconde surface de citation**, et ce dépôt a déjà payé deux fois pour des chiffres
qui divergent entre pièces (règle J — une leçon vit à un endroit). Or le document a 9
sections et la posture est déjà séparable :

> **La lecture en six pages** = sommaire → `synthese` (l'affirmation et ses trois mots)
> → `resultats` (ce que les leviers ajoutent) → `prevair` (la barre réelle) →
> `degradees` (où ça échoue — la posture) → `decision` (ce qu'on en fait).

**La règle** : la pièce courte est une *vue* du long, jamais un texte. **Ce qu'elle
remplace** : l'idée d'un dossier bis. **Le code** : une ligne dans le sommaire —
« Lecture en six pages : synthèse · résultats · la barre réelle · la limite · la
décision » — et, si un PDF physique de six pages est exigé, un drapeau
`--sections synthese,resultats,prevair,degradees,decision` à `exporter_pdf.py` qui
masque les autres `<section class="page">` avant impression. **Le contrôle** : le même
exporteur, les mêmes gardes (largeur, écrêtage, disponibilité), plus le
`verifier_dossier_candidature.py` existant — puisque la pièce courte est le même HTML,
elle ne peut pas contenir un chiffre que le long n'a pas.

### 4.2 Le troisième mode de perte silencieuse — **mesuré : c'est le contenu rendu par script**

| candidat | mord ici ? | preuve |
|---|---|---|
| `position: sticky` | **non** | un seul (`.bandeau`), déjà neutralisé : `@media print { .bandeau { position: static } }` (l. 569) |
| `<details>` fermés | **non** | **0 occurrence** dans le document |
| `page-break` qui coupe une figure | **non, pour les figures** | les 9 `<figure>` sont toutes `figure.fig`, couvertes par `break-inside: avoid` (l. 571) |
| **contenu rendu par script** | **🔴 OUI** | voir ci-dessous |

**Ce qui est mesuré.** Six scripts peuplent le document : `_p4_script.js` fait **19
écritures `innerHTML`** et construit du SVG, `_p5` 11, `_p6` 3, `_p7` injecte les
compteurs (`p7-jours`…), `_p0` la signature, `_p8` la grille. Si la capture précède la
fin de ces scripts, le PDF emporte des **emplacements vides** — et le CSS les *cache* :
`.p4-fr:empty { display: none }` (l. 2516). Le défaut s'efface lui-même. La seule
protection actuelle est `pg.wait_for_timeout(1800)` — **un délai fixe, donc la règle A
violée** — et le contrôle de fin (nombre de pages) ne peut pas voir un texte absent :
61 pages vides de leurs chiffres restent 61 pages. Aucun script ne signale qu'il a
fini ; l'exporteur n'écoute que les *erreurs* de console, pas les *absences*.

**La règle** : *on attend une condition, jamais un délai* — et l'échec **nomme** la
page fautive.

**Le code.** Une ligne à la fin de chaque `_p*_script.js` :

```js
document.documentElement.dataset[document.currentScript.dataset.page] = "pret";
// avec, sur chaque <script src="…"> :  data-page="p4"  (etc.)
```

et dans `exporter_pdf.py`, à la place du `wait_for_timeout(1800)` :

```python
PAGES_SCRIPTEES = ["p0", "p4", "p5", "p6", "p7", "p8"]
try:
    pg.wait_for_function(
        """attendues => attendues.every(
               p => document.documentElement.dataset[p] === 'pret')""",
        arg=PAGES_SCRIPTEES, timeout=15_000)
except Exception:
    manquantes = pg.evaluate(
        """attendues => attendues.filter(
               p => document.documentElement.dataset[p] !== 'pret')""",
        arg=PAGES_SCRIPTEES)
    print(f"ÉCHEC : contenu scripté absent à la capture — pages : {manquantes}. "
          "Le PDF aurait contenu des emplacements VIDES sans aucune erreur.")
    return 1
```

**Ce qu'il remplace** : le délai de 1 800 ms (qui devient le *plafond* de l'attente,
plus sa mesure). **Le contrôle du contrôle** : un grep dans `auditer_reserves.py` —
chaque `_p*_script.js` doit poser son drapeau, et chaque `<script src>` doit porter son
`data-page` — sinon l'export échoue en nommant le fichier. Le coût total est de six
lignes côté pages, une dizaine côté exporteur ; le mode de perte, lui, n'a pas encore
frappé — mais la machine est connue pour geler, et le poste de démonstration est un
autre matériel : c'est exactement le défaut qui choisit le jour du jury pour exister.

Et deux ajouts d'une ligne, mesurés pendant l'inventaire : `.reserve` et `.limites`
**ne sont pas** dans la liste `break-inside: avoid` (l. 571) — tout composant nouveau
doit y entrer au moment de sa création, et le contrôle ③ du § 3.4 le vérifie.

---

## En une page

| # | règle | remplace | contrôle |
|---|---|---|---|
| § 1 | une réserve = ce qui rend le chiffre faux si on la saute | les 5 habitats Streamlit comme porteurs de réserve | grep des marqueurs hors composant |
| § 2 | ce qui ne varie pas se signe une fois ; la démo est un **autre produit**, pas un dossier affaibli (PM2,5 : +14,4 > +12,49) | la répétition sur six pages · l'idée de convergence | le passeport est dérivé des données |
| § 3 | `.reserve`, deux niveaux, une seule porte d'écriture | `.note`, `.reserve` ad hoc, 14 blocs Streamlit | `auditer_reserves.py` ①②③ |
| § 4 | la pièce courte est une vue du long ; on attend une condition, jamais un délai | un dossier bis · `wait_for_timeout(1800)` | `--sections` mêmes gardes · drapeaux `data-page` + échec qui nomme la page |
