#!/usr/bin/env python3
"""Le contexte territorial des 84 départements, rendu pour les pages départementales.

Les pages de `pages_regions.py` disent **de combien** la correction améliore un territoire.
Elles ne disent jamais **pourquoi ce territoire se comporte comme il se comporte** — c'est
le manque que `docs/PROMPT_GPT_DEPARTEMENTS.md` a commandé et que `docs/departements/*.yaml`
comblent. Ce module est le pont entre les deux, et rien d'autre : il ne calcule aucune
mesure et n'en lit aucune.

Trois principes gouvernent ce rendu, et aucun n'est cosmétique
---------------------------------------------------------------
· **Le cité ne se confond jamais avec le mesuré.** Tout ce qui sort d'ici est écrit par des
  tiers — Atmo régionales, DREAL, Météo-France, préfectures — et le bloc le dit en toutes
  lettres, en tête. Un lecteur qui prendrait « 66 % des NOx » pour une de nos sorties nous
  attribuerait un chiffre que nous n'avons pas mesuré : c'est le nom faux qui se propage
  plus loin que le code (CLAUDE.md § 4 ter).
· **Chaque affirmation porte sa source, datée et ouvrable.** Les citations sont numérotées
  et rappelées en bas de bloc, plutôt que répétées en ligne où elles noieraient le propos.
· **Une hypothèse est marquée comme telle.** Les `pieges_modelisation` portent
  `speculatif: true` — ce sont des mécanismes plausibles, jamais des faits établis, et ils
  sont rendus sous ce titre-là.

Le contrôle de couverture suit § 4 : l'attendu vient de la **demande** — les 84 codes du
brief, lus par `valider_departements.codes_du_brief()`, jamais recopiés ici — et les
manquants sont **nommés** un par un, jamais résumés en « 82 sur 84 ». Et § 2 quater :
`rapport_couverture()` imprime le périmètre **effectif**, pas le périmètre demandé.

Usage :
    python3 scripts/contexte_departements.py          # contrôle de couverture seul
    python3 scripts/contexte_departements.py --html 30  # rend un bloc, pour l'œil
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from valider_departements import codes_du_brief  # noqa: E402

LOTS = RACINE / "docs" / "departements"

# Les énumérations du brief sont en ASCII sans accent — contrainte d'ingestion, pas
# d'affichage. Elles se traduisent donc ici, au seul moment où elles sont lues par un œil.
JOLI_POLLUANT = {"NO2": "NO₂", "O3": "O₃", "PM10": "PM10", "PM2.5": "PM2,5",
                 "SO2": "SO₂", "NH3": "NH₃", "COV": "COV", "benzene": "benzène"}
JOLIE_SAISON = {"hiver": "hiver", "printemps": "printemps", "ete": "été",
                "automne": "automne", "toute_annee": "toute l'année"}
JOLI_EFFET = {"dispersif": "dispersif", "piegeant": "piégeant", "mixte": "mixte"}


def charger(strict: bool = True) -> dict[str, dict]:
    """Les blocs de contexte, indexés par code de département.

    `strict` lève si un département du brief manque. Les pages n'en ont pas besoin — une
    page sans contexte reste une page valide — mais tout ce qui prétend publier le corpus
    complet doit échouer bruyamment plutôt que rendre un dossier troué.
    """
    if not LOTS.is_dir():
        raise SystemExit(f"absent : {LOTS.relative_to(RACINE)}")
    blocs: dict[str, dict] = {}
    for fichier in sorted(LOTS.glob("lot*.yaml")):
        contenu = yaml.safe_load(fichier.read_text(encoding="utf-8"))
        if not isinstance(contenu, list):
            raise SystemExit(f"{fichier.name} : attendu une liste de blocs")
        for bloc in contenu:
            code = bloc["code"]
            if code in blocs:
                raise SystemExit(f"{code} livré deux fois — {fichier.name}")
            blocs[code] = bloc
    manquants = [c for c in codes_du_brief() if c not in blocs]
    if manquants and strict:
        raise SystemExit(f"{len(manquants)} départements du brief sans contexte : "
                         f"{' '.join(manquants)}")
    return blocs


class Citations:
    """Les sources d'un bloc, numérotées une fois et rappelées en bas.

    Le champ `source` du brief est une chaîne libre qui peut porter **plusieurs** citations
    séparées par « ; », chacune terminée par son URL. Les répéter en ligne rendrait le bloc
    illisible ; les compter serait pire — deux affirmations appuyées sur le même document
    doivent pointer le même numéro, sinon le lecteur croit à deux sources.
    """

    def __init__(self) -> None:
        self.liste: list[str] = []

    def marquer(self, source: object) -> str:
        if not isinstance(source, str) or not source.strip():
            return ""
        numeros = []
        for citation in source.split(" ; "):
            citation = citation.strip(" ;")
            if not citation:
                continue
            if citation not in self.liste:
                self.liste.append(citation)
            numeros.append(self.liste.index(citation) + 1)
        if not numeros:
            return ""
        return ('<sup class="ctx-ref">'
                + "".join(f'<a href="#ctx-s{n}">{n}</a>' for n in numeros) + "</sup>")

    def rendre(self, reserves: list[str] | None = None) -> str:
        """La liste des sources, et les réserves qui les qualifient.

        Les `sans_source` d'un département qui **a** des sources ne disent pas « rien
        trouvé » : ils disent « voici ce que la source ne couvre pas » — un bilan de 2021
        au lieu de 2024, un inventaire de 2010. Leur place est donc contre les sources
        qu'ils qualifient, jamais en tête du bloc où ils se liraient comme une absence.
        """
        if not self.liste and not reserves:
            return ""
        items = []
        for n, citation in enumerate(self.liste, 1):
            urls = re.findall(r"https?://[^\s;]+", citation)
            texte = re.sub(r"https?://[^\s;]+", "", citation).strip(" -–—·,")
            liens = "".join(
                f'<a href="{html.escape(url, quote=True)}" rel="noopener" '
                f'target="_blank">{html.escape(urlparse(url).netloc.removeprefix("www."))}'
                f'</a>' for url in urls)
            items.append(f'<li id="ctx-s{n}">{html.escape(texte)} {liens}</li>')
        bloc_reserves = ""
        if reserves:
            bloc_reserves = ('<p class="ctx-note"><b>Réserves sur ces sources</b></p><ul>'
                             + "".join(f"<li>{_texte(r)}</li>" for r in reserves)
                             + "</ul>")
        titre = (f"Les {len(self.liste)} sources citées" if self.liste
                 else "Réserves sur les sources")
        return (f'<details class="ctx-plus"><summary>{titre}'
                + (" et leurs réserves" if reserves and self.liste else "")
                + f'</summary><ol class="ctx-src">{"".join(items)}</ol>'
                + f'{bloc_reserves}</details>')


def _confiance(item: dict) -> str:
    """La confiance n'est montrée que si elle n'est pas haute — sinon elle est du bruit.

    Le bloc annonce en tête que le défaut est « haute » : afficher l'étiquette partout
    la banaliserait au point qu'on ne verrait plus les deux qui comptent.
    """
    niveau = item.get("confiance")
    if niveau in (None, "haute"):
        return ""
    return f'<span class="ctx-conf ctx-{niveau}">confiance {niveau}</span>'


def _puces(polluants: object) -> str:
    if not isinstance(polluants, list):
        return ""
    return "".join(f'<i class="ctx-pol">{JOLI_POLLUANT.get(p, p)}</i>' for p in polluants)


# Le texte libre écrit les polluants en ASCII — `NO2`, `PM2.5` — là où le reste du dossier
# les compose. Les énumérations passent par JOLI_POLLUANT ; sans cette passe, la même page
# afficherait « NO₂ » dans une puce et « NO2 » deux lignes plus haut. Les bornes de mot
# protègent les identifiants : dans `FR03O3`, `O3` n'est pas précédé d'une frontière.
FORMULES = [(re.compile(r"\bNO2\b"), "NO₂"), (re.compile(r"\bO3\b"), "O₃"),
            (re.compile(r"\bSO2\b"), "SO₂"), (re.compile(r"\bNH3\b"), "NH₃"),
            (re.compile(r"\bPM2[.,]5\b"), "PM2,5"), (re.compile(r"\bCO2\b"), "CO₂")]


def _texte(valeur: object) -> str:
    """Les champs `>` du YAML arrivent repliés avec des sauts de ligne : on les rend plats."""
    plat = " ".join(str(valeur or "").split())
    for motif, joli in FORMULES:
        plat = motif.sub(joli, plat)
    return html.escape(plat)


def _carte(titre: str, corps: str) -> str:
    return f'<article class="ctx-carte"><h3>{titre}</h3>{corps}</article>' if corps else ""


def rendre(bloc: dict) -> str:
    """Le bloc de contexte d'un département, prêt à être inséré dans sa page."""
    src = Citations()
    cartes = []

    if bloc.get("sources_dominantes"):
        cartes.append(_carte("Ce qui est émis ici", "<ul>" + "".join(
            f'<li>{_puces(i.get("polluants"))}{_texte(i.get("libelle"))}'
            f'{src.marquer(i.get("source"))}{_confiance(i)}</li>'
            for i in bloc["sources_dominantes"]) + "</ul>"))

    topo = bloc.get("topographie_climat")
    if topo:
        vents = topo.get("vents_nommes") or []
        cartes.append(_carte("Relief et circulation", (
            f'<p><span class="ctx-effet ctx-{topo.get("effet", "mixte")}">'
            f'{JOLI_EFFET.get(topo.get("effet"), topo.get("effet"))}</span>'
            f'{_texte(topo.get("libelle"))}{src.marquer(topo.get("source"))}'
            f'{_confiance(topo)}</p>'
            + (f'<p class="ctx-vents">Vents nommés : '
               f'{", ".join(html.escape(str(v)) for v in vents)}</p>' if vents else ""))))

    if bloc.get("regime_episodes"):
        cartes.append(_carte("Quand les épisodes arrivent", "<ul>" + "".join(
            f'<li><b>{JOLIE_SAISON.get(i.get("saison"), i.get("saison"))} · '
            f'{JOLI_POLLUANT.get(i.get("polluant"), i.get("polluant"))}</b> — '
            f'{_texte(i.get("mecanisme"))}{src.marquer(i.get("source"))}'
            f'{_confiance(i)}</li>' for i in bloc["regime_episodes"]) + "</ul>"))

    if bloc.get("transport_longue_distance"):
        cartes.append(_carte("Ce qui arrive d'ailleurs", "<ul>" + "".join(
            f'<li><b>{_texte(i.get("origine"))} → '
            f'{JOLI_POLLUANT.get(i.get("polluant"), i.get("polluant"))}</b> — '
            f'{_texte(i.get("regime"))}{src.marquer(i.get("source"))}'
            f'{_confiance(i)}</li>' for i in bloc["transport_longue_distance"]) + "</ul>"))

    cadre = bloc.get("cadre_decision")
    if cadre:
        contentieux = cadre.get("contentieux_no2")
        cartes.append(_carte("Le cadre de décision", (
            f'<p><b>PPA</b> — {_texte(cadre.get("ppa")) or "non renseigné"}</p>'
            f'<p><b>ZFE</b> — {_texte(cadre.get("zfe")) or "non renseigné"}</p>'
            f'<p><b>Contentieux NO₂</b> — '
            f'{"département concerné" if contentieux else "non concerné"}'
            f'{src.marquer(cadre.get("source"))}{_confiance(cadre)}</p>')))

    pieges = ""
    if bloc.get("pieges_modelisation"):
        # Ces items portent `speculatif: true` : ce sont des mécanismes plausibles, pas des
        # résultats. Le titre et l'avertissement le disent avant que le lecteur ne lise la
        # première puce — l'inverse (une réserve après coup) vaudrait validation (§ 4 ter).
        pieges = (
            '<details class="ctx-plus"><summary>Ce qui peut piéger un modèle ici '
            '— hypothèses, non vérifiées sur nos données</summary>'
            '<p class="ctx-note">Ces mécanismes sont déduits du contexte ci-dessus par le '
            'rédacteur du brief. Aucun n\'a été testé contre nos résidus : ils orientent '
            'où chercher, ils ne concluent rien.</p><ul>' + "".join(
                f'<li>{_texte(i.get("libelle"))}{_confiance(i)}</li>'
                for i in bloc["pieges_modelisation"]) + "</ul></details>")

    # `sans_source` couvre DEUX situations que le rendu ne doit pas confondre — c'est le
    # défaut de nom faux (§ 4 ter), et il a failli être publié : sur 60, 78, 94 et 95 le
    # champ qualifie une source **utilisée** (« bilan de 2021 et non de 2024 »), alors que
    # sur 77 et 80 il constate qu'aucune n'existe. Écrire « aucune publication trouvée »
    # au-dessus de trois sources citées aurait été faux dans les deux sens.
    reserves = bloc.get("sans_source") or []
    vide = ""
    if reserves and not bloc.get("sources_dominantes"):
        # Nommer ce qui a été cherché et n'a rien rendu vaut mieux qu'une carte absente :
        # un blanc muet se lit comme un oubli, et l'oubli supposé se corrige à tort.
        # Le libellé dit ce qui a été CHERCHÉ, jamais « rien trouvé » : le `resume` porte
        # déjà le constat d'absence, et le répéter deux lignes plus bas se lirait comme
        # deux absences distinctes.
        vide = ('<p class="ctx-vide"><b>Ce qui a été cherché, et ce que ça a rendu.</b> '
                + " ".join(_texte(s) for s in reserves) + '</p>')
        reserves = []

    if not cartes and not vide:
        return ""

    return (
        '<section class="ctx" aria-labelledby="ctx-titre">'
        '<h2 id="ctx-titre">Ce que ce territoire a de particulier</h2>'
        '<p class="ctx-avert"><b>Contexte publié par des tiers</b> — Atmo régionales, '
        'DREAL, Météo-France, préfectures. <b>Aucun chiffre de cette section ne sort de '
        'notre modèle</b> : nos mesures sont dans les onglets, plus bas. Chaque '
        'affirmation renvoie à sa source ; sauf mention contraire, celle-ci est de '
        'confiance haute.</p>'
        f'<p class="ctx-resume">{_texte(bloc.get("resume"))}</p>'
        f'{vide}'
        f'<div class="ctx-grille">{"".join(cartes)}</div>'
        f'{pieges}{src.rendre(reserves)}'
        '</section>')


CSS = """
.ctx{margin:22px 0 6px;padding:16px 18px 6px;border:1px solid var(--trait);
 border-radius:12px;background:var(--sur)}
.ctx>h2{margin:0 0 8px;font-size:1.02rem}
.ctx-avert{margin:0 0 12px;font-size:.82rem;line-height:1.5;color:var(--doux);
 border-left:3px solid var(--or);padding-left:10px}
.ctx-resume{margin:0 0 14px;font-size:.98rem;line-height:1.55}
.ctx-grille{display:grid;grid-template-columns:repeat(auto-fit,minmax(285px,1fr));gap:12px}
.ctx-carte{border:1px solid var(--trait);border-radius:10px;background:var(--sur2);
 padding:11px 13px}
.ctx-carte h3{margin:0 0 7px;font-size:.79rem;text-transform:uppercase;
 letter-spacing:.055em;color:var(--azur)}
.ctx-carte ul{margin:0;padding-left:17px}
.ctx-carte li{margin:0 0 7px;font-size:.85rem;line-height:1.5}
.ctx-carte p{margin:0 0 7px;font-size:.85rem;line-height:1.5}
.ctx-pol{display:inline-block;font-style:normal;font-family:var(--mono);font-size:.68rem;
 padding:1px 5px;margin:0 5px 0 0;border-radius:4px;background:var(--fond);
 color:var(--doux);vertical-align:1px}
.ctx-effet{display:inline-block;font-size:.68rem;padding:1px 6px;margin-right:6px;
 border-radius:4px;background:var(--fond);color:var(--doux);text-transform:uppercase;
 letter-spacing:.04em}
.ctx-effet.ctx-piegeant{color:var(--brique)}
.ctx-effet.ctx-dispersif{color:var(--vert)}
.ctx-vents{color:var(--doux);font-size:.78rem}
.ctx-conf{display:inline-block;margin-left:6px;font-size:.68rem;padding:0 5px;
 border:1px solid var(--trait);border-radius:4px;color:var(--or)}
.ctx-conf.ctx-basse{color:var(--brique)}
.ctx-ref a{font-family:var(--mono);font-size:.62rem;color:var(--azur);
 text-decoration:none;padding:0 1px}
.ctx-ref a:hover{text-decoration:underline}
.ctx-ref a+a::before{content:","}
.ctx-vide{margin:0 0 12px;padding:9px 11px;border:1px dashed var(--trait);
 border-radius:9px;font-size:.83rem;line-height:1.5;color:var(--doux)}
.ctx-plus{margin-top:12px;border-top:1px solid var(--trait);padding-top:9px}
.ctx-plus>summary{cursor:pointer;font-size:.82rem;color:var(--azur);list-style:none}
.ctx-plus>summary::-webkit-details-marker{display:none}
.ctx-plus>summary::before{content:"▸ ";font-size:.75rem}
.ctx-plus[open]>summary::before{content:"▾ "}
.ctx-plus>summary:focus-visible{outline:2px solid var(--azur);outline-offset:2px}
.ctx-note{font-size:.8rem;color:var(--doux);line-height:1.5;margin:8px 0}
.ctx-plus ul{margin:6px 0 4px;padding-left:17px}
.ctx-plus li{margin:0 0 7px;font-size:.84rem;line-height:1.5}
.ctx-src{margin:8px 0 4px;padding-left:20px}
.ctx-src li{margin:0 0 6px;font-size:.76rem;line-height:1.45;color:var(--doux)}
.ctx-src a{color:var(--azur);font-family:var(--mono);font-size:.72rem}
"""


def rapport_couverture(blocs: dict[str, dict], codes_pages: list[str]) -> None:
    """Le périmètre EFFECTIF, pas le périmètre demandé (§ 2 quater).

    Les deux écarts sont nommés séparément parce qu'ils n'ont pas la même cause : une page
    sans contexte est un trou du corpus ; un contexte sans page est un département que nos
    données ne couvrent pas, ce qui est légitime et n'a rien à corriger.
    """
    sans_contexte = sorted(set(codes_pages) - set(blocs))
    sans_page = sorted(set(blocs) - set(codes_pages))
    creux = sorted(c for c, b in blocs.items() if not b.get("sources_dominantes"))
    print(f"  contexte injecté : {len(set(codes_pages) & set(blocs))} pages sur "
          f"{len(codes_pages)}")
    if sans_contexte:
        print(f"  ⚠️ page SANS contexte : {' '.join(sans_contexte)}")
    if sans_page:
        print(f"  contexte sans page (département hors de nos données) : "
              f"{' '.join(sans_page)}")
    if creux:
        print(f"  sans source dominante publiée, la réserve est affichée : "
              f"{' '.join(creux)}")


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--html", metavar="CODE", help="rendre le bloc d'un département")
    n = a.parse_args()
    blocs = charger(strict=False)
    if n.html:
        if n.html not in blocs:
            raise SystemExit(f"{n.html} : aucun contexte — connus : {' '.join(blocs)}")
        print(rendre(blocs[n.html]))
        return 0
    print(f"{len(blocs)} blocs chargés depuis {LOTS.relative_to(RACINE)}")
    rapport_couverture(blocs, codes_du_brief())
    rendus = {c: rendre(b) for c, b in blocs.items()}
    muets = [c for c, h in rendus.items() if not h]
    print(f"  rendus non vides : {sum(1 for h in rendus.values() if h)} · "
          f"octets médians : {sorted(len(h) for h in rendus.values())[len(rendus) // 2]:,}")
    if muets:
        print(f"  ⚠️ blocs rendus VIDES : {' '.join(muets)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
