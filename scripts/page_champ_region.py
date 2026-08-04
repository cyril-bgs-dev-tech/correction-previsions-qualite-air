#!/usr/bin/env python3
"""La page du champ spatialisé d'une région — propagation, correction, navigation.

Ce qu'elle montre, et ce qu'elle ne montre pas
------------------------------------------------
Un champ **déjà calculé**, pas une interpolation de stations. `champ_occitanie.py` lit les
grilles CAMS conservées sur disque (9 035 fichiers à 0,1°) et leur ajoute le biais récent
krigé depuis les **stations de fond**. La page ne fait que l'afficher, jour par jour.

Trois couches commutables :

| couche | ce qu'elle donne à voir |
|---|---|
| **CAMS brut** | la propagation — advection, accumulation, panaches régionaux |
| **corrigé** | ce que la correction rend au niveau réellement mesuré |
| **écart** | l'ampleur spatiale de la correction, positive là où le modèle sous-estime |

⚠️ **Résolution 0,1° ≈ 8 × 11 km.** Un panache traverse la région ; une rue n'apparaît pas.
Les cartes fines d'Atmo viennent d'un modèle de dispersion nourri d'un inventaire
d'émissions routières — autre objet, autre métier, et la page le dit.

⚠️ **Ce n'est pas notre modèle appris**, qui exige des descripteurs de site à chaque maille.
C'est la chaîne de krigeage — famille PREV'AIR — appliquée à la grille.

Le krigeage porte sur les **stations de fond seulement**
----------------------------------------------------------
Mesuré le 04/08 : la typologie explique **57 % de la variance du biais entre stations sur
NO₂** — +10,24 µg/m³ en fond contre **+27,58 en trafic**. Interpoler géographiquement un
biais de station trafic étalerait une correction de bord de route sur la campagne. L'arrêté
du 10 juillet 2020 exclut d'ailleurs les mailles de proximité routière de l'indice.

La part de variance expliquée par la typologie est **affichée par polluant** : c'est la
mesure de fragilité du procédé, et elle doit rester sous les yeux du lecteur.

Le contrôle qui valide la page
--------------------------------
Le champ corrigé est comparé au niveau **réellement observé aux stations de fond
d'Occitanie**. Écart mesuré : 0,2 à 2,7 µg/m³, contre 17 µg/m³ pour CAMS brut sur NO₂.

Encodage
----------
Chaque couche devient un **atlas PNG** — les 577 journées tuilées en une image — décodé en
JavaScript sur un canevas. Un tableau brut pèserait trois fois plus.

Usage  : python3 scripts/page_champ_region.py --region 76
Sortie : reports/html/champ_<region>.html
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import sys
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from champ_region import emprise_region  # noqa: E402
from pages_soutenance import BANDES, CSS, COURT, JS, charger, enveloppe  # noqa: E402

CHAMPS = RACINE / "data/processed/champs"
POLLUANTS = ("O3", "NO2", "PM10", "PM25")
# Part de la variance du biais inter-stations expliquée par la typologie — mesurée le 04/08.
# C'est l'indicateur de fragilité du krigeage : plus il est haut, moins le biais est une
# propriété du LIEU, et plus l'interpolation géographique est discutable.
TYPOLOGIE_PCT = {"O3": 1, "PM25": 10, "PM10": 29, "NO2": 57}
def observe_fond(polluant: str, boite: dict) -> float | None:
    """Niveau médian **réellement observé** aux stations de fond de la région.

    ⚠️ Calculé, jamais codé en dur : la valeur dépend de la région, et une constante
    recopiée d'un territoire à l'autre validerait un champ contre le mauvais réel.
    """
    import pandas as pd  # noqa: PLC0415

    d = charger(polluant, 1)
    if d is None:
        return None
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "type_station", "lat_wgs84", "lon_wgs84"]
                         ).drop_duplicates("station_id")
    st = st[st["lat_wgs84"].between(*boite["lat"]) & st["lon_wgs84"].between(*boite["lon"])]
    d = d.merge(st, on="station_id", how="inner")
    d = d[d["type_station"].astype(str).str.lower() == "background"]
    return float(d["valeur"].median()) if len(d) >= 500 else None


def atlas(cube: np.ndarray, vmin: float, vmax: float) -> tuple[str, int, int]:
    """Tuile les journées en une seule image PNG, quantifiées sur 8 bits.

    La valeur 0 est réservée aux mailles manquantes : les données utiles occupent 1-255,
    sans quoi un trou et une valeur nulle seraient indiscernables — exactement le défaut
    que ce projet traque ailleurs.
    """
    from PIL import Image

    n, h, w = cube.shape
    cols = int(np.ceil(np.sqrt(n * h / w)))
    cols = max(1, min(n, cols))
    lignes = int(np.ceil(n / cols))
    grille = np.zeros((lignes * h, cols * w), dtype="uint8")
    q = np.clip((cube - vmin) / max(vmax - vmin, 1e-9), 0, 1)
    q = np.where(np.isfinite(cube), 1 + (q * 254).astype("uint8"), 0).astype("uint8")
    for k in range(n):
        r, c = divmod(k, cols)
        grille[r * h:(r + 1) * h, c * w:(c + 1) * w] = q[k]
    t = io.BytesIO()
    Image.fromarray(grille, mode="L").save(t, format="PNG", optimize=True)
    return base64.b64encode(t.getvalue()).decode(), cols, lignes


def contour_region(lat: np.ndarray, lon: np.ndarray, code: str) -> list:
    """Le contour régional, en coordonnées de maille — pour le superposer au canevas."""
    from pages_regions import SOURCE_REGIONS  # noqa: PLC0415

    brut = json.loads(SOURCE_REGIONS.read_text(encoding="utf-8"))
    if str(code).lower() in ("france", "fr", "0"):
        # Vue nationale : on trace TOUS les contours régionaux, pas un seul.
        anneaux_tous = []
        for x in brut["features"]:
            g = x["geometry"]
            anneaux_tous += (g["coordinates"] if g["type"] == "Polygon"
                             else [a for poly in g["coordinates"] for a in poly])
        return _vers_mailles(anneaux_tous, lat, lon)
    f = next((x for x in brut["features"] if x["properties"]["code"] == code), None)
    if f is None:
        return []
    g = f["geometry"]
    anneaux = (g["coordinates"] if g["type"] == "Polygon"
               else [a for poly in g["coordinates"] for a in poly])
    return _vers_mailles(anneaux, lat, lon)


def _vers_mailles(anneaux: list, lat: np.ndarray, lon: np.ndarray) -> list:
    out = []
    for a in anneaux:
        p = np.asarray(a, dtype="float64")
        if len(p) < 40:
            continue
        # de degrés vers l'indice de maille, en pixels du canevas
        x = (p[:, 0] - lon[0]) / (lon[1] - lon[0])
        y = (p[:, 1] - lat[0]) / (lat[1] - lat[0])
        pas = max(1, len(p) // 600)
        out.append(np.round(np.column_stack([x, y])[::pas], 2).tolist())
    return out


def main(region: str) -> int:
    boite, ardoise_reg = emprise_region(region)
    from pages_regions import SOURCE_REGIONS  # noqa: PLC0415
    if ardoise_reg == "france":
        nom_reg = "France métropolitaine"
    else:
        nom_reg = next(x["properties"]["nom"] for x in
                       json.loads(SOURCE_REGIONS.read_text(encoding="utf-8"))["features"]
                       if x["properties"]["code"] == region)
    jeux, onglets, vues = {}, [], []
    for i, p in enumerate(POLLUANTS):
        f = CHAMPS / f"champ_{ardoise_reg}_{p}.npz"
        if not f.exists():
            print(f"  {p} : champ absent — ignoré", flush=True)
            continue
        z = np.load(f, allow_pickle=True)
        jours = [str(x) for x in z["jours"]]
        lat, lon = z["lat"], z["lon"]
        cams, corr = z["cams"], z["corrige"]
        ecart = corr - cams
        # Échelle commune à CAMS et corrigé — sans quoi la comparaison visuelle est fausse.
        fini = np.isfinite(cams) | np.isfinite(corr)
        vmax = float(np.nanpercentile(np.concatenate([cams[fini], corr[fini]]), 99.5))
        emax = float(np.nanpercentile(np.abs(ecart[np.isfinite(ecart)]), 99.5))
        couches = {}
        for nom, cube, a, b in (("cams", cams, 0.0, vmax), ("corr", corr, 0.0, vmax),
                                ("ecart", ecart, -emax, emax)):
            b64, cols, lignes = atlas(cube, a, b)
            couches[nom] = {"png": b64, "cols": cols, "lignes": lignes,
                            "vmin": a, "vmax": b}
        jeux[p] = {
            "jours": jours, "h": int(cams.shape[1]), "w": int(cams.shape[2]),
            # ⚠️ L'échelle s'ancre sur la borne basse de la classe « mauvais », PAS sur
            # `SEUIL` : celui-ci vaut 200 µg/m³ pour le NO₂ — le seuil **horaire**
            # réglementaire — alors que le champ journalier médian est à 17,7. Ancrée
            # dessus, toute la région resterait bleue et la carte ne dirait rien. La borne
            # de classe 3 est celle qui déclenche une communication : c'est elle qui doit
            # colorer. NO₂ 90 · O₃ 120 · PM10 50 · PM2,5 25.
            "seuil": float(BANDES[p][3][0]), "couches": couches,
            "contour": contour_region(lat, lon, region),
            "typo": TYPOLOGIE_PCT[p], "observe": observe_fond(p, boite),
            "med_cams": float(np.nanmedian(cams)), "med_corr": float(np.nanmedian(corr))}
        onglets.append(f'<button role="tab" data-cle="{p}" '
                       f'aria-selected="{"true" if not vues else "false"}">'
                       f'{COURT[p]}</button>')
        vues.append(f'<div class="vue" data-cle="{p}"{"" if not vues else " hidden"}>'
                    f'{panneau(p, jeux[p])}</div>')
        print(f"  {p:5s} · {len(jours)} jours · {cams.shape[1]}×{cams.shape[2]} mailles · "
              f"{sum(len(c['png']) for c in couches.values()) / 1e6:.1f} Mo encodés",
              flush=True)

    if not jeux:
        raise SystemExit("aucun champ — lancer d'abord champ_occitanie.py")

    corps = (
        f'<p class="eyebrow">Champ spatialisé · {html.escape(nom_reg)} · maille CAMS 0,1°</p>'
        f'<h1>Voir la diffusion, pas seulement les stations</h1>'
        f'<p class="chapo">Ce champ n\'est <b>pas une interpolation de stations</b> : c\'est '
        f'la grille du modèle européen, conservée depuis le premier téléchargement et '
        f'jusqu\'ici inexploitée — <b>9 035 fichiers</b> dont on n\'extrayait que 476 '
        f'points. La correction y ajoute le biais récent des stations de <b>fond</b>, '
        f'interpolé spatialement. <a href="index.html">← retour au dossier</a></p>'
        f'<div class="avert"><b>Ce que cette résolution permet et interdit.</b> La maille '
        f'fait <b>8 × 11 km</b> : un panache traverse la région, une rue n\'apparaît pas. '
        f'Les cartes de rue d\'Atmo viennent d\'un modèle de dispersion nourri d\'un '
        f'inventaire d\'émissions routières — autre objet. Et ce champ porte la chaîne de '
        f'<b>krigeage</b>, pas notre modèle appris, qui exigerait des descripteurs de site '
        f'à chaque maille.</div>'
        f'<nav class="ong" role="tablist">{"".join(onglets)}</nav>{"".join(vues)}')
    page = enveloppe(f"Champ spatialisé — {nom_reg}", corps, "champ 0,1°")
    page = page.replace("</style>", CSS_SUP + "</style>").replace(
        "</script>", "\n" + JS_CARTE + "\nCHAMPS = " + json.dumps(jeux) + ";\ninit();\n</script>")
    sortie = f"reports/html/champ_{ardoise_reg}.html"
    f = RACINE / sortie
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(page, encoding="utf-8")
    print(f"\nÉcrit : {sortie} · {f.stat().st_size / 1e6:.1f} Mo")
    return 0


def panneau(p: str, d: dict) -> str:
    frag = "fragile" if d["typo"] >= 40 else ("prudent" if d["typo"] >= 20 else "solide")
    # ⚠️ Une région peut ne pas avoir assez de stations de fond pour ce polluant :
    # `observe_fond` rend alors `None`, et l'écart au réel n'existe pas. On le **dit**
    # plutôt que de laisser un formatage planter ou d'afficher un zéro trompeur.
    obs = d.get("observe")
    if obs is None:
        v_obs, e_cams, e_corr = "—", "non calculable", "non calculable"
    else:
        v_obs = f'{obs:.1f}'
        e_cams = f'écart au réel : {abs(d["med_cams"] - obs):.1f}'
        e_corr = f'écart au réel : {abs(d["med_corr"] - obs):.1f}'
    return (
        f'<div class="strip">'
        f'<div class="kpi"><span class="k">Niveau observé au fond, Occitanie</span>'
        f'<span class="v">{d["observe"]:.1f}</span><span class="s">µg/m³, médiane</span></div>'
        f'<div class="kpi"><span class="k">Champ CAMS brut</span>'
        f'<span class="v neg">{d["med_cams"]:.1f}</span>'
        f'<span class="s">écart au réel : {abs(d["med_cams"] - d["observe"]):.1f}</span></div>'
        f'<div class="kpi"><span class="k">Champ corrigé</span>'
        f'<span class="v pos">{d["med_corr"]:.1f}</span>'
        f'<span class="s">écart au réel : {abs(d["med_corr"] - d["observe"]):.1f}</span></div>'
        f'<div class="kpi"><span class="k">Biais expliqué par la typologie</span>'
        f'<span class="v {"neg" if d["typo"] >= 40 else ""}">{d["typo"]} %</span>'
        f'<span class="s">interpolation spatiale : {frag}</span></div>'
        f'</div>'
        f'<div class="bloc"><div class="cmd">'
        f'<button class="bt" data-act="play">▶ Lecture</button>'
        f'<input class="cur" type="range" min="0" max="{len(d["jours"]) - 1}" value="0">'
        f'<span class="jour"></span>'
        f'<span class="sel">'
        f'<button class="bt lay" data-lay="cams">CAMS brut</button>'
        f'<button class="bt lay actif" data-lay="corr">corrigé</button>'
        f'<button class="bt lay" data-lay="ecart">écart</button></span>'
        f'</div><canvas class="champ"></canvas><div class="rampe-l"></div></div>')


CSS_SUP = """
.cmd{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.cmd .cur{flex:1 1 260px;accent-color:var(--azur)}
.cmd .jour{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:.88rem;
 min-width:9ch;font-weight:620}
.bt{appearance:none;border:1px solid var(--trait);background:var(--sur2);color:var(--texte);
 font:inherit;font-size:.83rem;padding:6px 12px;border-radius:7px;cursor:pointer}
.bt:hover{border-color:var(--azur)} .bt.actif{background:var(--azur);color:#fff;
 border-color:var(--azur)}
.bt:focus-visible{outline:2px solid var(--azur);outline-offset:2px}
.sel{display:flex;gap:4px}
canvas.champ{width:100%;height:auto;display:block;border-radius:10px;background:var(--sur2)}
.rampe-l{display:flex;align-items:center;gap:8px;margin-top:10px;font-size:.76rem;
 color:var(--doux);font-family:var(--mono)}
.rampe-l .bar{flex:1;height:11px;border-radius:3px}
"""

JS_CARTE = r"""
var CHAMPS = null, etat = {};
// Rampe divergente ancrée au seuil réglementaire — la même sémantique que les cartes de
// chaleur du dossier : bleu sous la normale, rouge au seuil, bordeaux au-delà.
var ARRETS = [[0,[30,70,140]],[0.35,[60,145,205]],[0.55,[120,195,165]],
              [0.70,[185,215,110]],[0.85,[243,214,75]],[0.95,[240,150,45]],
              [1.00,[225,90,45]],[1.30,[150,20,25]],[1.80,[85,5,30]]];
function teinte(r){
  if(r<=ARRETS[0][0])return ARRETS[0][1];
  for(var i=1;i<ARRETS.length;i++){
    if(r<=ARRETS[i][0]){var a=ARRETS[i-1],b=ARRETS[i],t=(r-a[0])/(b[0]-a[0]);
      return [0,1,2].map(function(k){return a[1][k]+(b[1][k]-a[1][k])*t;});}}
  return ARRETS[ARRETS.length-1][1];
}
function divergente(t){            // pour la couche « écart » : rouge négatif, bleu positif
  var c=Math.max(-1,Math.min(1,t)), n=[214,216,212],
      d=c>=0?[26,92,148]:[160,58,38], p=Math.pow(Math.abs(c),0.7);
  return [0,1,2].map(function(k){return n[k]+(d[k]-n[k])*p;});
}
function init(){
  Object.keys(CHAMPS).forEach(function(p){
    var d=CHAMPS[p], vue=document.querySelector('.vue[data-cle="'+p+'"]');
    var cv=vue.querySelector('canvas.champ'), cur=vue.querySelector('.cur');
    var lbl=vue.querySelector('.jour'), ech=6;
    cv.width=d.w*ech; cv.height=d.h*ech;
    var ctx=cv.getContext('2d'); ctx.imageSmoothingEnabled=true;
    var tampon=document.createElement('canvas'); tampon.width=d.w; tampon.height=d.h;
    var tctx=tampon.getContext('2d');
    etat[p]={d:d,cv:cv,ctx:ctx,tampon:tampon,tctx:tctx,cur:cur,lbl:lbl,ech:ech,
             lay:'corr',jour:0,timer:null,img:{},pret:{}};
    ['cams','corr','ecart'].forEach(function(l){
      var im=new Image();
      im.onload=function(){etat[p].pret[l]=true; if(etat[p].lay===l)dessiner(p);};
      im.src='data:image/png;base64,'+d.couches[l].png;
      etat[p].img[l]=im;
    });
    cur.addEventListener('input',function(){etat[p].jour=+cur.value;dessiner(p);});
    vue.querySelectorAll('.lay').forEach(function(b){
      b.addEventListener('click',function(){
        vue.querySelectorAll('.lay').forEach(function(x){x.classList.remove('actif');});
        b.classList.add('actif'); etat[p].lay=b.dataset.lay; dessiner(p);});
    });
    vue.querySelector('[data-act="play"]').addEventListener('click',function(){
      var e=etat[p];
      if(e.timer){clearInterval(e.timer);e.timer=null;this.textContent='▶ Lecture';return;}
      this.textContent='❚❚ Pause';
      e.timer=setInterval(function(){
        e.jour=(e.jour+1)%e.d.jours.length; e.cur.value=e.jour; dessiner(p);},110);
    });
    dessiner(p);
  });
}
function dessiner(p){
  var e=etat[p], d=e.d, l=e.lay, c=d.couches[l];
  e.lbl.textContent=d.jours[e.jour]||'';
  if(!e.pret[l])return;
  var col=e.jour%c.cols, lig=Math.floor(e.jour/c.cols);
  e.tctx.clearRect(0,0,d.w,d.h);
  e.tctx.drawImage(e.img[l], col*d.w, lig*d.h, d.w, d.h, 0,0, d.w,d.h);
  var im=e.tctx.getImageData(0,0,d.w,d.h), a=im.data;
  for(var i=0;i<a.length;i+=4){
    var q=a[i];
    if(q===0){a[i+3]=0;continue;}                       // maille manquante : transparente
    var v=c.vmin+(q-1)/254*(c.vmax-c.vmin), rgb;
    rgb = (l==='ecart') ? divergente(v/Math.max(c.vmax,1e-9)) : teinte(v/d.seuil);
    a[i]=rgb[0];a[i+1]=rgb[1];a[i+2]=rgb[2];a[i+3]=235;
  }
  e.tctx.putImageData(im,0,0);
  e.ctx.clearRect(0,0,e.cv.width,e.cv.height);
  // ⚠️ AUCUN retournement. L'axe des latitudes de CAMS est **décroissant** — 51,95 → 41,05
  // — donc la ligne 0 du tableau est déjà le NORD, et un canevas la dessine en haut. Une
  // première version retournait le canevas « pour mettre le nord en haut » : la France
  // sortait à l'envers. La convention d'un axe se lit dans les données, jamais dans son nom.
  e.ctx.drawImage(e.tampon,0,0,e.cv.width,e.cv.height);
  if(d.contour&&d.contour.length){
    // Le contour est déjà exprimé en indices de maille par la même convention : y croît
    // vers le sud puisque `lat[1]-lat[0]` est négatif. Il se superpose donc tel quel.
    e.ctx.strokeStyle='rgba(255,255,255,.55)'; e.ctx.lineWidth=1.4; e.ctx.lineJoin='round';
    d.contour.forEach(function(an){
      e.ctx.beginPath();
      an.forEach(function(pt,k){var x=pt[0]*e.ech,y=pt[1]*e.ech;
        k?e.ctx.lineTo(x,y):e.ctx.moveTo(x,y);});
      e.ctx.stroke();});
  }
  var r=e.cv.parentElement.querySelector('.rampe-l');
  if(l==='ecart'){
    r.innerHTML='<span>'+(-c.vmax).toFixed(0)+'</span><span class="bar" style="background:'
      +'linear-gradient(90deg,#a03a26,#d6d8d4,#1a5c94)"></span><span>+'
      +c.vmax.toFixed(0)+' µg/m³ · correction apportée</span>';
  }else{
    r.innerHTML='<span>0</span><span class="bar" style="background:linear-gradient(90deg,'
      +'#1e468c,#3c91cd,#78c3a5,#b9d76e,#f3d64b,#f0962d,#e15a2d,#961419)"></span><span>'
      +c.vmax.toFixed(0)+' µg/m³ · seuil « mauvais » à '+d.seuil.toFixed(0)+'</span>';
  }
}
"""


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--region", default="76", help="76 Occitanie · 75 Nouvelle-Aquitaine")
    n = a.parse_args()
    raise SystemExit(main(n.region))
