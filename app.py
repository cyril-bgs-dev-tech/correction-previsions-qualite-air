"""Démo interactive — correction apprise des prévisions de qualité de l'air.

Lancement : streamlit run app.py

Les données viennent de `data/demo/`, préparées par `scripts/build_demo_data.py`.
Streamlit relit ses sources à chaque interaction : les charger en Parquet plutôt qu'en
CSV et les mettre en cache fait la différence entre une démo fluide et une démo poussive
(mesuré : 22× sur le temps de lecture).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RACINE = Path(__file__).resolve().parent
DEMO = RACINE / "data/demo"
sys.path.insert(0, str(RACINE / "src"))

# Palette validée pour la daltonie et le contraste, identique à celle de la
# présentation : bleu pour la référence, orange pour le modèle corrigé.
BLEU, ORANGE, VERT = "#2a78d6", "#eb6834", "#1baf7a"
GRIS, ENCRE = "#898781", "#0b0b0b"

NOM = {"O3": "Ozone (O₃)", "NO2": "Dioxyde d'azote (NO₂)",
       "PM25": "Particules PM2.5", "PM10": "Particules PM10"}

# Bornes des classes de l'indice ATMO (arrêté du 10/07/2020), en µg/m³.
# **Importées, jamais recopiées.** La démo en tenait une copie littérale de trois polluants ;
# elle coïncidait avec la source, ce qui est la façon dont une copie se fait oublier jusqu'au
# jour où elle diverge. PM10 y manquait — comme partout ailleurs dans la chaîne horaire.
from aq.models.indice_atmo import BORNES  # noqa: E402

st.set_page_config(page_title="Qualité de l'air — démo", page_icon="🌬️",
                   layout="wide", initial_sidebar_state="expanded")


@st.cache_data(show_spinner=False)
def charger(nom: str) -> pd.DataFrame:
    chemin = DEMO / f"{nom}.parquet"
    if not chemin.exists():
        st.error(f"`{chemin.relative_to(RACINE)}` absent — lancer d'abord "
                 "`python scripts/build_demo_data.py`.")
        st.stop()
    return pd.read_parquet(chemin)


def metriques(observe: pd.Series, predit: pd.Series) -> dict[str, float]:
    err = predit - observe
    var = float(observe.var())
    return {"rmse": float(np.sqrt((err ** 2).mean())), "biais": float(err.mean()),
            "r2": float(1 - (err ** 2).mean() / var) if var > 0 else np.nan}


from aq.demo import compter as _detection  # noqa: E402
from aq.demo import detection_journaliere as _detection_journaliere  # noqa: E402


@st.cache_data(show_spinner=False)
def _index_meteo(chemins: tuple[str, ...]) -> dict:
    """Fichier ERA5 → (premier jour, dernier jour), lus DANS les données.

    § 4 bis : le nom ne dit pas la fenêtre. `era5_metropole_202501_04.parquet` en porte
    quatre mois, `..._202505_06.parquet` deux, et un chemin construit depuis `%Y%m` n'en
    trouve aucun — ce qui faisait afficher « Météo non extraite » sur des mois présents.
    On lit la seule colonne temporelle, une fois, et le résultat est mis en cache.
    """
    index = {}
    for c in chemins:
        try:
            t = pd.read_parquet(c, columns=["timestamp_utc"])
        except Exception as e:                       # jamais silencieux (§ 2 bis)
            st.warning(f"ERA5 illisible : {pathlib.Path(c).name} — {type(e).__name__}")
            continue
        j = t["timestamp_utc"].dt.tz_convert("Europe/Paris").dt.date
        index[c] = (j.min(), j.max())
    return index


def detection_horaire(p: pd.DataFrame, polluant: str) -> pd.DataFrame:
    """Franchissement d'un seuil, heure par heure — l'échelle du déclenchement d'alerte."""
    # ⚠️ `BORNES` porte les bornes **hautes** de chaque classe, borne supérieure INCLUSE :
    # une valeur d'exactement 50 µg/m³ d'ozone est encore « Bon ». Compter `>= 50` et
    # étiqueter « Moyen » promettait donc une classe que la donnée ne tient pas, d'un cran.
    # On compte `>` et l'on étiquette « ou pire » — la même forme que l'échelle journalière
    # juste en dessous, qui l'avait déjà juste.
    etiquettes = ["Moyen", "Dégradé", "Mauvais", "Très mauvais", "Extrêmement mauvais"]
    lignes = []
    for seuil, nom in zip(BORNES[polluant], etiquettes):
        reel = p["observe"] > seuil
        if reel.sum() < 5:
            continue
        for modele, colonne in (("CAMS brut", "cams"), ("Corrigé", "corrige")):
            lignes.append({"seuil": f"> {seuil:.0f} — {nom} ou pire", "seuil_val": float(seuil),
                           "modele": modele,
                           **_detection(reel, p[colonne] > seuil)})
    return pd.DataFrame(lignes)


@st.cache_data(show_spinner="Calcul de l\'indice ATMO sur 28,9 M de lignes…")
def detection_journaliere(pred: pd.DataFrame) -> pd.DataFrame:
    """Lit la table précalculée par `build_demo_data.py` ; la recalcule si elle manque.

    🔴 Mesuré le 17/08 : le calcul prend **90 s au mieux, plus de 120 s au pire**, une fois
    par session, et le cache portait `show_spinner=False` — donc quatre-vingt-dix secondes
    de page blanche au premier clic, devant un jury. La table fait huit lignes ; elle est
    désormais matérialisée à la construction du jeu de démo.

    Le repli qui recalcule reste, mais il est **bruyant** : un spinner nommé, et un
    avertissement qui dit pourquoi c'est lent et comment l'éviter. Un repli silencieux
    rendrait le défaut invisible jusqu'au jour où il compte.
    """
    fichier = DEMO / "detection_journaliere.parquet"
    if fichier.exists():
        return pd.read_parquet(fichier)
    st.warning(
        "Table de détection journalière **non précalculée** — elle est reconstruite ici, "
        "ce qui prend une à deux minutes. Lancer `python3 scripts/build_demo_data.py` "
        "avant une démonstration."
    )
    return _detection_journaliere(pred)


def mise_en_forme(fig: go.Figure, hauteur: int = 380) -> go.Figure:
    """Chrome discret : la donnée est la seule chose autorisée à être visible."""
    fig.update_layout(
        height=hauteur, margin=dict(l=8, r=8, t=28, b=8),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRIS)
    fig.update_yaxes(gridcolor="rgba(137,135,129,0.22)", zeroline=False)
    return fig


# ─────────────────────────── barre latérale ───────────────────────────
st.sidebar.title("🌬️ Qualité de l'air")
st.sidebar.caption("Correction apprise des prévisions CAMS · 476 stations")

PAGES = ["Aide à l'expertise du jour", "Vue d'ensemble", "Où la correction agit",
         "Station par station", "Détection des épisodes", "Variables du paysage"]
page = st.sidebar.radio("Page", PAGES, label_visibility="collapsed")

resume_tout = charger("resume_stations")

# Le sélecteur est piloté par CE QUI EST DANS LA DONNÉE, pas par une liste écrite à la main.
# Une liste en dur peut proposer un polluant absent — page vide sans un mot — ou taire un
# polluant présent. Les deux sont arrivés : PM10 manquait de `NOM`, et il manquait aussi des
# données, si bien qu'aucun des deux défauts n'était visible tant que l'autre durait.
DISPONIBLES = [p for p in NOM if p in set(resume_tout["polluant"].astype(str))]
if not DISPONIBLES:
    st.error("Aucun polluant dans `data/demo/` — lancer `python scripts/build_demo_data.py`.")
    st.stop()
if absents := [p for p in NOM if p not in DISPONIBLES]:
    st.sidebar.caption(f"⚠️ Absent des données : {', '.join(NOM[p] for p in absents)}")

polluant = st.sidebar.selectbox("Polluant", DISPONIBLES, format_func=NOM.get)
st.sidebar.divider()
# L'échéance n'était affirmée NULLE PART dans cette démo. Ce n'était pas faux — c'était muet,
# et un chiffre sans son échéance ne se cite pas (§ 4 ter : `TRANCHES[1] = (1, 24)`, ce sont
# les 24 premières heures de la sortie 00 UTC, donc le JOUR MÊME, pas le lendemain).
st.sidebar.caption(
    "**Échéance J0** — les 24 premières heures de la sortie CAMS de 00 UTC, "
    "c'est-à-dire le jour même. C'est l'échéance du produit officiel de référence."
)
st.sidebar.caption(
    "Sources — mesures : EEA · prévisions et modèle de terrain : Copernicus "
    "(CAMS, DEM GLO-30) · paysage : IGN Géoplateforme · stations : LCSQA."
)

stations = charger("stations")
resume = (resume_tout[resume_tout["polluant"] == polluant]
          .merge(stations, on="station_id", how="inner"))



# ─────────────────────────── 0. Aide à l'expertise ───────────────────────────
if page == "Aide à l'expertise du jour":
    st.title("Aide à l'expertise du jour")
    st.caption(
        "Un prévisionniste d'AASQA lit chaque matin les sorties de modèle, les confronte "
        "aux stations, puis décide. Cette page ne remplace pas ce jugement : elle "
        "rassemble ce qui l'oriente — **où le modèle diverge des mesures**, **dans quel "
        "régime météo on se trouve**, et **quelle confiance accorder à la correction "
        "dans ce régime**."
    )

    pred = charger("predictions")
    p = pred[pred["polluant"] == polluant].copy()
    p["jour"] = p["timestamp_utc"].dt.tz_convert("Europe/Paris").dt.date
    jours = sorted(p["jour"].unique())
    jour = st.select_slider("Jour analysé", jours, value=jours[len(jours) // 2])
    du_jour = p[p["jour"] == jour]

    if du_jour.empty:
        st.warning("Aucune donnée ce jour."); st.stop()

    # ── Divergence modèle / mesure : le premier réflexe du prévisionniste ──
    ecart = du_jour["cams"] - du_jour["observe"]
    ecart_corrige = du_jour["corrige"] - du_jour["observe"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stations mesurées", f"{du_jour['station_id'].nunique()}")
    c2.metric("Maximum observé", f"{du_jour['observe'].max():.0f} µg/m³")
    c3.metric("Écart CAMS", f"{ecart.mean():+.1f} µg/m³")
    c4.metric("Écart corrigé", f"{ecart_corrige.mean():+.1f} µg/m³",
              f"{abs(ecart_corrige.mean()) - abs(ecart.mean()):+.1f}",
              delta_color="inverse")

    # ── Régime météo, DESCRIPTIF — et pourquoi il ne conditionne plus la confiance ──
    #
    # 🔴 Trois défauts de périmètre, mesurés par une revue externe le 17/08 :
    #
    # ① `REGIMES_METEO.md` classe chaque **station × heure** ; cette page classait la
    #    **moyenne nationale des 24 h** en lui appliquant les mêmes seuils. Rejouée sur le
    #    corpus, cette classification donne stagnation **3,4 %** — le régime qui portait le
    #    message de prudence ne se déclenchait presque jamais, et une journée ventilée à
    #    Brest et stagnante à Lyon recevait une seule étiquette.
    # ② Le « −17 % » cité est mesuré à **J+1, par station-heure, sur trois mois de 2024,
    #    pour l'ozone seul**. Sans ces trois mots, il était affiché sur un autre objet.
    # ③ **PM10 n'a jamais été mesuré dans ce rapport** (O₃, NO₂, PM2,5 seulement) — et la
    #    page lui servait quand même le verdict vert « suivable sur les pics ».
    #
    # Le verdict est donc retiré : le régime reste affiché comme **description du jour**,
    # et la réserve de confiance ne s'énonce que sur le périmètre où elle a été mesurée.
    # C'est § 4 ter — signaler un défaut n'est pas le corriger, mais ici corriger voulait
    # dire cesser d'affirmer.
    MESURE_REGIME = ("O3", "NO2", "PM25")     # le périmètre réel de REGIMES_METEO.md
    st.subheader("Régime météo du jour — description nationale")
    # 🔴 § 4 bis — un nom de fichier n'est pas une source de vérité. La météo de 2025 est
    # stockée en fichiers GROUPÉS (`era5_metropole_202501_04.parquet`), et construire le
    # chemin depuis `%Y%m` ne les trouve pas : la page annonçait « Météo non extraite »
    # pour des mois **présents sur le disque** — y compris sur le jour affiché par défaut,
    # donc sur le premier écran. On liste les candidats, puis on tranche sur le CONTENU.
    candidats = sorted((DEMO.parent / "processed" / "meteo").glob("era5_metropole_*.parquet"))
    couverture = _index_meteo(tuple(str(c) for c in candidats))
    porteur = next((c for c, (d0, d1) in couverture.items() if d0 <= jour <= d1), None)
    m = pd.DataFrame()
    if porteur:
        meteo = pd.read_parquet(porteur)
        meteo["jour"] = meteo["timestamp_utc"].dt.tz_convert("Europe/Paris").dt.date
        m = meteo[meteo["jour"] == jour]
    if candidats:
        if not m.empty:
            couche = m["couche_limite_m"].mean()
            vent = m["vent_vitesse_m_s"].mean()
            rayon = m["rayonnement_w_m2"].mean()
            if couche < 300 and vent < 2:
                regime = "stagnation"
            elif rayon > 150:
                regime = "photochimique"
            else:
                regime = "ventilé"

            g1, g2, g3 = st.columns(3)
            g1.metric("Couche limite", f"{couche:.0f} m")
            g2.metric("Vent moyen", f"{vent:.1f} m/s")
            g3.metric("Rayonnement", f"{rayon:.0f} W/m²")

            st.caption(
                f"**Régime {regime}** — classé sur la **moyenne nationale des 24 heures**, "
                "pas station par station. Une journée ventilée à Brest et stagnante à Lyon "
                "reçoit ici une seule étiquette : c'est une **description du jour**, pas "
                "l'objet de l'étude des régimes.")
            if polluant in MESURE_REGIME:
                st.warning(
                    "**Ce que l'étude des régimes dit, et sur quoi exactement.** Sur "
                    "l'**ozone seul**, à **J+1**, par **station-heure**, sur **trois mois "
                    "de 2024**, la correction dégrade le décile supérieur de **17 %** en "
                    "régime ventilé comme en régime de stagnation. Ces trois mots — "
                    "polluant, échéance, objet — ne se retirent pas du chiffre, et rien "
                    "ici ne transpose ce résultat à la classification ci-dessus.")
            else:
                st.info(
                    f"**Le PM10 n'a pas été mesuré dans l'étude des régimes** "
                    f"(elle porte sur {', '.join(MESURE_REGIME)}). Aucune réserve de "
                    "confiance par régime n'est donc publiable pour ce polluant — ni "
                    "dans un sens ni dans l'autre.")
        else:
            # Dire la couverture RÉELLE, pas « ce mois manque » : la couverture est
            # partielle par construction (ERA5 s'arrête avant la fin du corpus), et un
            # message qui ne la nomme pas laisse croire à une panne.
            jours = sorted(d for bornes in couverture.values() for d in bornes)
            st.info(f"Météo indisponible pour ce jour. Couverture ERA5 réelle : "
                    f"{jours[0]:%Y-%m-%d} → {jours[-1]:%Y-%m-%d} "
                    f"({len(couverture)} fichier·s) — le bloc « régime » n'existe que là."
                    if jours else "Météo indisponible pour ce jour.")
    else:
        st.info("Aucun fichier ERA5 dans `data/processed/meteo` — bloc « régime » désactivé.")

    # ── Les stations qui divergent le plus : où porter l'attention ──
    st.subheader("Stations où le modèle diverge le plus")
    st.caption("Trier par écart absolu désigne où une vérification humaine est utile.")
    par_station = (du_jour.groupby("station_id")
                   .agg(observe=("observe", "max"), cams=("cams", "max"),
                        corrige=("corrige", "max")).reset_index()
                   .merge(stations[["station_id", "nom", "commune", "type_station"]],
                          on="station_id", how="left"))
    par_station["ecart_cams"] = par_station["cams"] - par_station["observe"]
    par_station["ecart_corrige"] = par_station["corrige"] - par_station["observe"]
    st.dataframe(
        par_station.reindex(
            par_station["ecart_cams"].abs().sort_values(ascending=False).index
        ).head(12)[["nom", "commune", "type_station", "observe", "cams", "corrige",
                    "ecart_cams", "ecart_corrige"]]
        .round(1)
        .rename(columns={"nom": "Station", "commune": "Commune",
                         "type_station": "Typologie", "observe": "Mesuré",
                         "cams": "CAMS", "corrige": "Corrigé",
                         "ecart_cams": "Écart CAMS", "ecart_corrige": "Écart corrigé"}),
        hide_index=True, use_container_width=True)

    # ⚠️ La fenêtre se DÉRIVE des données (règle A du dépôt, appliquée à une phrase). Elle
    # était écrite en dur — « trois mois de 2024 » — et l'est restée après l'extension du
    # corpus à ~36 mois : une réserve périmée qui sous-déclarait notre propre travail, et
    # que n'importe qui réfutait en ouvrant le sélecteur de date juste au-dessus.
    n_mois = len({pd.Timestamp(j).strftime("%Y-%m") for j in jours})
    st.caption(
        f"⚠️ Cette page est un **prototype d'aide à la décision**, pas un outil validé. "
        f"Elle porte sur {jours[0]:%Y-%m-%d} → {jours[-1]:%Y-%m-%d} ({n_mois} mois) à "
        f"l'échéance **J0**, au pas **horaire**, avec la pile de base seule — ce n'est ni "
        f"l'échéance, ni le grain, ni la pile des chiffres du dossier. Sa valeur est de "
        f"montrer la forme qu'un tel outil pourrait prendre, pas de se substituer à "
        f"l'expertise."
    )

# ─────────────────────────── 1. Vue d'ensemble ───────────────────────────
if page == "Vue d'ensemble":
    st.title("Ce que la correction apporte")
    st.caption(
        "Prévisions CAMS Europe corrigées par apprentissage, à partir des seules "
        "informations disponibles **à l'heure où la prévision est publiée** : la sortie "
        "CAMS, le paysage, le relief et le calendrier. Aucune météo réanalysée — elle "
        "donnerait au modèle un futur que CAMS n'avait pas."
    )

    pred = charger("predictions")
    p = pred[pred["polluant"] == polluant]
    mc, mm = metriques(p["observe"], p["cams"]), metriques(p["observe"], p["corrige"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RMSE — CAMS brut", f"{mc['rmse']:.2f} µg/m³")
    c2.metric("RMSE — corrigé", f"{mm['rmse']:.2f} µg/m³",
              f"{100 * (mm['rmse'] / mc['rmse'] - 1):+.1f} %", delta_color="inverse")
    c3.metric("R²", f"{mm['r2']:.3f}", f"{mm['r2'] - mc['r2']:+.3f}")
    c4.metric("Biais", f"{mm['biais']:+.2f} µg/m³",
              f"{abs(mm['biais']) - abs(mc['biais']):+.2f}", delta_color="inverse")

    st.divider()
    gauche, droite = st.columns([3, 2])

    with gauche:
        st.subheader("Où le gain se produit")
        bornes = [0] + BORNES[polluant][:4] + [float("inf")]
        lignes = []
        for bas, haut in zip(bornes[:-1], bornes[1:]):
            b = p[p["observe"].between(bas, haut, inclusive="left")]
            if len(b) < 30:
                continue
            lignes.append({
                "bande": f"{bas:.0f}–{haut:.0f}" if np.isfinite(haut) else f"≥ {bas:.0f}",
                "n": len(b),
                "CAMS brut": metriques(b["observe"], b["cams"])["rmse"],
                "Corrigé": metriques(b["observe"], b["corrige"])["rmse"],
            })
        bandes = pd.DataFrame(lignes)

        # 🔴 La légende se CALCULE depuis les bandes affichées, elle ne se rédige pas.
        # La version précédente affirmait « le gain se concentre sur les valeurs basses, et
        # la correction fait jeu égal dans la queue » — un récit vrai d'une version
        # antérieure du modèle, et démenti par le graphique auquel il était accolé : sur
        # PM10 le gain est le plus FAIBLE en bas (+2,7 %) et le plus fort en queue (+17,6 %),
        # et sur O₃ la bande 50-100 est DÉGRADÉE de 12,7 %. Un juré voyait la barre orange
        # au-dessus de la bleue pendant que la légende disait « jeu égal ».
        # Une légende dérivée des mêmes nombres que la figure ne peut plus la contredire.
        if not bandes.empty:
            bandes["gain_pct"] = 100 * (1 - bandes["Corrigé"] / bandes["CAMS brut"])
            bas, queue = bandes.iloc[0], bandes.iloc[-1]
            pire = bandes.loc[bandes["gain_pct"].idxmin()]
            phrase = (f"Le gain n'est pas uniforme : **{bas['gain_pct']:+.1f} %** sur la "
                      f"bande basse ({bas['bande']}), **{queue['gain_pct']:+.1f} %** dans la "
                      f"queue ({queue['bande']}).")
            if pire["gain_pct"] < 0:
                phrase += (f" ⚠️ La correction **dégrade** la bande {pire['bande']} de "
                           f"{abs(pire['gain_pct']):.1f} % — c'est visible sur la figure, "
                           f"et c'est dit.")
            phrase += (" Aucune bande n'est écrasée au profit du RMSE global : une version "
                       "antérieure gagnait 13 % en aplatissant les épisodes.")
            st.caption(phrase)

        fig = go.Figure()
        for nom, couleur in (("CAMS brut", BLEU), ("Corrigé", ORANGE)):
            fig.add_bar(x=bandes["bande"], y=bandes[nom], name=nom,
                        marker_color=couleur, marker_line_width=0)
        fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.08,
                          yaxis_title="RMSE (µg/m³)",
                          xaxis_title="Concentration observée (µg/m³)")
        st.plotly_chart(mise_en_forme(fig), use_container_width=True)

    with droite:
        st.subheader("Répartition du gain")
        # La réserve du § 11 du dossier n'avait pas traversé jusqu'ici. L'affirmation
        # « un modèle qui ne l'a jamais vue » est exacte et **incomplète** : les plis
        # tirent des stations entières, pas des zones. Le modèle n'a pas vu la station,
        # il a vu ses voisines — et le dossier chiffre ce que cela flatte.
        st.caption(f"Sur {len(resume)} stations, en validation par **station exclue** — "
                   "chacune est prédite par un modèle qui ne l'a jamais vue. "
                   "⚠️ Les plis ne sont **pas bloqués spatialement** : le modèle n'a pas vu "
                   "la station, mais il a vu ses voisines. Le § 11 du dossier mesure "
                   "l'optimisme résiduel — jusqu'à **−10 points sur l'ozone** avec un fossé "
                   "de 50 km.")
        fig = go.Figure()
        fig.add_histogram(x=resume["gain_pct"], nbinsx=34, marker_color=BLEU,
                          marker_line_width=0, name="stations")
        fig.add_vline(x=0, line_color=GRIS, line_width=1)
        fig.add_vline(x=float(resume["gain_pct"].median()), line_color=ORANGE,
                      line_width=2, line_dash="dot",
                      annotation_text=f"médiane {resume['gain_pct'].median():.0f} %")
        fig.update_layout(xaxis_title="Gain de RMSE (%)", yaxis_title="Stations",
                          showlegend=False)
        st.plotly_chart(mise_en_forme(fig), use_container_width=True)
        part = 100 * float((resume["gain_pct"] > 0).mean())
        st.info(f"**{part:.0f} %** des stations sont améliorées. Les autres sont "
                "montrées telles quelles — voir la page suivante.")

    st.divider()
    st.caption(
        "⚠️ CAMS Europe (0,1°, soit ~8 km en longitude × 11 en latitude) n'est "
        "**pas** PREV'AIR (~2 km), la chaîne "
        "réellement employée par les AASQA. Ce qui est démontré vaut pour une chaîne "
        "opérationnelle de même nature, pas pour celle d'ATMO."
    )

# ─────────────────────────── 2. Carte ───────────────────────────
elif page == "Où la correction agit":
    st.title("Où la correction agit")
    st.caption("Chaque point est une station, prédite par un modèle qui ne l'a jamais "
               "vue. Le rouge signale les stations que la correction **dégrade** — "
               "elles sont montrées plutôt que masquées.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Stations", f"{len(resume)}")
    c2.metric("Améliorées", f"{100 * (resume['gain_pct'] > 0).mean():.0f} %")
    c3.metric("Gain médian", f"{resume['gain_pct'].median():.1f} %")

    typologies = st.multiselect(
        "Typologies affichées", sorted(resume["type_station"].dropna().unique()),
        default=sorted(resume["type_station"].dropna().unique()))
    vue = resume[resume["type_station"].isin(typologies)]

    # Échelle divergente : deux pôles opposés, neutre au milieu. Le zéro sépare
    # « la correction aide » de « la correction nuit » — c'est la seule lecture utile.
    #
    # ⚠️ Les bornes étaient écrites en dur à ±50 %. Mesuré : 15 stations sortent de cette
    # plage, dont une à **−396,9 %**, peinte du même rouge qu'une station à −50 %. La
    # couleur mentait par saturation, alors que le survol donnait le vrai chiffre. La borne
    # se dérive donc de la donnée affichée (règle A, appliquée à une échelle graphique) :
    # un quantile plutôt que le maximum, sinon une seule station écrase tout le contraste.
    borne = max(10.0, float(np.nanquantile(np.abs(vue["gain_pct"]), 0.98)))
    hors = int((np.abs(vue["gain_pct"]) > borne).sum())
    fig = go.Figure(go.Scattergeo(
        lon=vue["lon_wgs84"], lat=vue["lat_wgs84"], mode="markers",
        marker=dict(
            size=8, color=vue["gain_pct"], colorscale=[[0, "#d03b3b"], [0.5, "#f0efec"],
                                                       [1, BLEU]],
            cmin=-borne, cmax=borne, line=dict(width=0.6, color="rgba(255,255,255,0.85)"),
            colorbar=dict(title="Gain<br>(%)", thickness=12, len=0.75)),
        text=[f"{n}<br>{c}<br>RMSE {a:.1f} → {b:.1f} µg/m³<br>{g:+.1f} %"
              for n, c, a, b, g in zip(vue["nom"], vue["commune"], vue["rmse_cams"],
                                       vue["rmse_mos"], vue["gain_pct"])],
        hoverinfo="text"))
    fig.update_geos(scope="europe", resolution=50, showcountries=True,
                    countrycolor="rgba(137,135,129,0.5)", showland=True,
                    landcolor="rgba(137,135,129,0.10)", showlakes=False,
                    lonaxis_range=[-5.5, 10], lataxis_range=[41, 51.5])
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=10, b=0),
                      paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    if hors:
        pire = float(vue["gain_pct"].min())
        st.caption(f"Échelle bornée à **±{borne:.0f} %**, dérivée du 98ᵉ centile des gains "
                   f"affichés. **{hors} station·s** sortent de la plage et sont peintes à la "
                   f"couleur de la borne — la plus dégradée est à **{pire:+.1f} %**. Le "
                   f"survol donne toujours la valeur réelle.")

    st.subheader("Les stations les moins bien traitées")
    st.caption("Comprendre pourquoi la correction échoue sur ces stations est un "
               "prolongement identifié du projet.")
    st.dataframe(
        vue.nsmallest(10, "gain_pct")[
            ["nom", "commune", "type_station", "altitude", "rmse_cams", "rmse_mos",
             "gain_pct"]
        ].rename(columns={"nom": "Station", "commune": "Commune",
                          "type_station": "Typologie", "altitude": "Altitude (m)",
                          "rmse_cams": "RMSE CAMS", "rmse_mos": "RMSE corrigé",
                          "gain_pct": "Gain (%)"}),
        hide_index=True, use_container_width=True)

# ─────────────────────────── 3. Station ───────────────────────────
elif page == "Station par station":
    st.title("Station par station")

    dispo = resume.sort_values("nom")
    choix = st.selectbox(
        "Station", dispo["station_id"],
        format_func=lambda s: f"{dispo.loc[dispo.station_id == s, 'nom'].iloc[0]} "
                              f"({dispo.loc[dispo.station_id == s, 'commune'].iloc[0]})")

    pred = charger("predictions")
    serie = (pred[(pred["polluant"] == polluant) & (pred["station_id"] == choix)]
             .sort_values("timestamp_utc"))
    if serie.empty:
        st.warning("Aucune prévision pour cette station et ce polluant.")
        st.stop()

    info = dispo[dispo["station_id"] == choix].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Typologie", str(info["type_station"]))
    c2.metric("Altitude", f"{info['altitude']:.0f} m")
    c3.metric("RMSE CAMS", f"{info['rmse_cams']:.2f}")
    c4.metric("RMSE corrigé", f"{info['rmse_mos']:.2f}",
              f"{info['gain_pct']:+.1f} %", delta_color="normal")

    mois = sorted(serie["timestamp_utc"].dt.strftime("%Y-%m").unique())
    choisi = st.select_slider("Mois affiché", mois, value=mois[0])
    fenetre = serie[serie["timestamp_utc"].dt.strftime("%Y-%m") == choisi]

    fig = go.Figure()
    fig.add_scatter(x=fenetre["timestamp_utc"], y=fenetre["observe"], name="Mesuré",
                    line=dict(color=ENCRE, width=2))
    fig.add_scatter(x=fenetre["timestamp_utc"], y=fenetre["cams"], name="CAMS brut",
                    line=dict(color=BLEU, width=2))
    fig.add_scatter(x=fenetre["timestamp_utc"], y=fenetre["corrige"], name="Corrigé",
                    line=dict(color=ORANGE, width=2))
    for seuil, etiquette in zip(BORNES[polluant][:3], ["Moyen", "Dégradé", "Mauvais"]):
        fig.add_hline(y=seuil, line_color=GRIS, line_width=1, line_dash="dot",
                      annotation_text=etiquette, annotation_position="right",
                      annotation_font_size=10)
    fig.update_layout(yaxis_title=f"{NOM[polluant]} (µg/m³)")
    st.plotly_chart(mise_en_forme(fig, 420), use_container_width=True)
    st.caption("Les traits pointillés marquent les bornes des classes de l'indice ATMO. "
               "Une erreur ne change ce qui est publié que si elle fait franchir l'une "
               "d'elles — c'est pourquoi un gain en µg/m³ n'est pas un gain de service.")

    st.subheader("Erreur au fil de la journée")
    st.caption("Un profil horaire d'erreur révèle ce que le modèle rate de façon "
               "systématique — cycle du trafic, rupture de la couche limite au lever "
               "du jour.")
    horaire = serie.assign(heure=serie["timestamp_utc"].dt.hour).groupby("heure").agg(
        cams=("cams", "mean"), corrige=("corrige", "mean"), observe=("observe", "mean"))
    fig = go.Figure()
    fig.add_scatter(x=horaire.index, y=horaire["cams"] - horaire["observe"],
                    name="CAMS brut", line=dict(color=BLEU, width=2))
    fig.add_scatter(x=horaire.index, y=horaire["corrige"] - horaire["observe"],
                    name="Corrigé", line=dict(color=ORANGE, width=2))
    fig.add_hline(y=0, line_color=GRIS, line_width=1)
    fig.update_layout(xaxis_title="Heure (UTC)", yaxis_title="Biais moyen (µg/m³)")
    st.plotly_chart(mise_en_forme(fig, 300), use_container_width=True)

# ─────────────────────────── 4. Épisodes ───────────────────────────
elif page == "Détection des épisodes":
    st.title("Détection des épisodes")
    st.caption(
        "Un taux d'accord traite les erreurs symétriquement ; le métier ne l'est pas. "
        "Ne pas annoncer un épisode qui survient expose la population — l'arrêté du "
        "7 avril 2016 autorise d'ailleurs le déclenchement **sur prévision**. Le rappel "
        "est donc le critère décisif."
    )

    echelle = st.radio(
        "Échelle de détection",
        ["Classe d'indice journalière", "Dépassement horaire"],
        horizontal=True,
        help="L'indice ATMO publié est journalier. Les deux échelles ne donnent pas le "
             "même verdict — c'est le point central de cette page.")

    pred = charger("predictions")
    journaliere = echelle.startswith("Classe")
    detection = (detection_journaliere(pred) if journaliere
                 else detection_horaire(pred[pred["polluant"] == polluant], polluant))

    if detection.empty:
        st.warning("Trop peu de dépassements pour conclure.")
        st.stop()

    # Deux non-dits que la vue journalière portait en silence — le second est une réserve
    # que le module lui-même énonce (`indice_atmo.py`) et que cette page n'affichait pas.
    if journaliere:
        st.caption(
            f"⚠️ Cette échelle **ignore le sélecteur de polluant** — vous avez choisi "
            f"{NOM[polluant]}, mais l'indice ATMO est **multi-polluants** par construction : "
            "il prend le pire des quatre sous-indices. C'est volontaire, et il faut le "
            "savoir avant de lire la table. · ⚠️ Un jour n'entre ici que s'il a **au moins "
            "trois polluants sur quatre** ; la moitié des jours retenus n'en a que trois, "
            "et un indice calculé sur un sous-ensemble est **optimiste par construction** "
            "— le pire des quatre ne peut qu'être supérieur ou égal au pire des trois. · "
            "⚠️ L'indice réellement publié au public est **spatialisé** ; on applique ici "
            "la même règle d'agrégation, station par station. Même règle, autre objet.")

    fig = go.Figure()
    for modele, couleur in (("CAMS brut", BLEU), ("Corrigé", ORANGE)):
        sous = detection[detection["modele"] == modele]
        fig.add_bar(x=sous["seuil"], y=sous["rappel"], name=modele,
                    marker_color=couleur, marker_line_width=0,
                    text=[f"{v:.0%}" for v in sous["rappel"]], textposition="outside")
    fig.update_layout(barmode="group", bargap=0.4, bargroupgap=0.08,
                      yaxis_title="Rappel — part des épisodes annoncés",
                      yaxis_tickformat=".0%", yaxis_range=[0, 1.08])
    st.plotly_chart(mise_en_forme(fig, 400), use_container_width=True)

    # 🔴 Les seuils sont EMBOÎTÉS : une heure à 140 µg/m³ d'ozone compte dans « ≥ 50 »,
    # « ≥ 100 » ET « ≥ 130 ». Sommer les manques compte donc le même épisode plusieurs fois,
    # et le total est dominé par le seuil le plus bas — sur O₃ celui-ci couvre 60 % du
    # corpus : ce n'est pas un épisode, c'est le régime courant. La version précédente de
    # cette bannière sommait, et annonçait « 282 224 épisodes manqués de plus » sur l'ozone
    # alors que le corrigé en manque MOINS aux deux seuils sévères (rappel 0,489 → 0,584 à
    # 100 µg/m³, 0,179 → 0,286 à 130). Le verdict affiché était l'inverse du verdict réel.
    #
    # La bannière porte donc sur UN seuil — le plus sévère qui ait assez d'occurrences pour
    # être mesurable — et le détail par seuil est publié à côté, sans total.
    MIN_EPISODES = 30
    par_seuil = (detection.pivot_table(index=["seuil_val", "seuil"], columns="modele",
                                       values="manques")
                 .join(detection.groupby(["seuil_val", "seuil"])["n"].max())
                 .sort_index())
    mesurables = par_seuil[par_seuil["n"] >= MIN_EPISODES]
    if mesurables.empty:
        st.info(f"Aucun seuil n'atteint {MIN_EPISODES} épisodes observés sur ce périmètre : "
                "pas de verdict de détection publiable ici.")
    else:
        val, lib = mesurables.index[-1]           # le PLUS SÉVÈRE, par valeur numérique
        r = mesurables.iloc[-1]
        ecart = int(r["CAMS brut"] - r["Corrigé"])
        detail = " · ".join(
            f"{l.split('—')[0].strip()} : {int(x['CAMS brut'] - x['Corrigé']):+d}"
            for (_, l), x in par_seuil.iterrows())
        if ecart > 0:
            st.success(f"**{ecart} épisodes manqués en moins** au seuil le plus sévère "
                       f"mesurable — {lib}, {int(r['n'])} épisodes observés. C'est la même "
                       "mesure qu'un gain de RMSE, dans l'unité qui engage une AASQA.")
        elif ecart < 0:
            st.error(f"**{abs(ecart)} épisodes manqués de plus** au seuil le plus sévère "
                     f"mesurable — {lib}, {int(r['n'])} épisodes observés. À ce seuil, la "
                     "correction échange du rappel contre de la précision.")
        else:
            st.info(f"**Aucun écart** au seuil le plus sévère mesurable — {lib}.")
        st.caption(f"Écart par seuil, jamais sommé — les seuils sont **emboîtés**, un même "
                   f"épisode compte dans tous ceux qu'il dépasse : {detail}")

    st.dataframe(
        detection.assign(rappel=lambda d: (100 * d["rappel"]).round(1),
                         precision=lambda d: (100 * d["precision"]).round(1))
        .rename(columns={"seuil": "Seuil", "modele": "Modèle", "rappel": "Rappel (%)",
                         "precision": "Précision (%)", "manques": "Épisodes manqués",
                         "n": "Épisodes réels"}),
        hide_index=True, use_container_width=True)

    # 🔴 Cette phrase disait « à l'échelle horaire la correction perd en rappel », sans
    # seuil. C'est vrai au seuil trivial et **faux aux seuils sévères** — sur l'ozone le
    # rappel passe de 0,489 à 0,584 à 100 µg/m³ et de 0,179 à 0,286 à 130. Une affirmation
    # vraie sur un sous-ensemble, publiée comme une loi (règle E). Elle se dérive maintenant
    # de la table affichée, seuil par seuil, et ne dit que ce que la table montre.
    if not detection.empty:
        p = detection.pivot_table(index=["seuil_val", "seuil"], columns="modele",
                                  values="rappel").sort_index()
        gagne = [l for (_, l), r in p.iterrows() if r["Corrigé"] > r["CAMS brut"]]
        perd = [l for (_, l), r in p.iterrows() if r["Corrigé"] <= r["CAMS brut"]]
        court = lambda ls: ", ".join(l.split("—")[0].strip() for l in ls)   # noqa: E731
        if gagne and perd:
            phrase = (f"**Le sens dépend du seuil, et il faut le dire ainsi.** Le rappel "
                      f"**progresse** à {court(gagne)} et **recule** à {court(perd)}. "
                      f"L'amortissement des extrêmes coûte du rappel là où le seuil est "
                      f"bas et fréquent ; il n'en coûte pas là où l'épisode est franc.")
        elif gagne:
            phrase = (f"**Le rappel progresse à tous les seuils mesurés** "
                      f"({court(gagne)}) — la correction n'échange pas ici du rappel "
                      f"contre de la précision.")
        else:
            phrase = (f"**Le rappel recule à tous les seuils mesurés** ({court(perd)}) : "
                      f"la correction amortit les extrêmes.")
        st.info(
            phrase + " À l'échelle **journalière** — celle de l'indice publié — l'agrégation "
            "par le maximum des 24 heures rattrape une part de l'amortissement. C'est "
            "l'indice qui est publié, mais un déclenchement d'alerte se décide sur "
            "l'horaire : **les deux comptent, et il faut annoncer les deux.**"
        )

    st.warning(
        "**À dire avant qu'on le demande.** En valeur absolue, la détection reste "
        "insuffisante : les deux modèles manquent la majorité des épisodes sévères. Ce "
        "qui est démontré, c'est qu'une part de cette insuffisance est **apprenable** — "
        "pas que le problème est résolu."
    )

# ─────────────────────────── 5. Paysage ───────────────────────────
else:
    st.title("Variables du paysage et du relief")
    st.caption(
        "47 variables construites autour de chaque station. Les **chênes** émettent "
        "l'isoprène, précurseur d'ozone ; les conifères des monoterpènes, au potentiel "
        "bien moindre. Les agréger sous « forêt » dilue le signal jusqu'à le rendre "
        "indétectable."
    )

    candidates = [c for c in stations.columns
                  if c.startswith(("tpi_", "rugosite_", "chene_", "conifere_",
                                   "feuillu_", "route_", "foret_"))
                  or c in ("altitude_mnt_m", "profondeur_vallee_m", "pente_deg")]
    defaut = "tpi_10000m" if "tpi_10000m" in candidates else candidates[0]

    c1, c2 = st.columns(2)
    variable = c1.selectbox("Variable", sorted(candidates),
                            index=sorted(candidates).index(defaut))
    axe_y = c2.selectbox("Comparer à", ["Concentration moyenne observée",
                                        "Gain de la correction (%)",
                                        "RMSE de CAMS brut"])

    jeu = resume.dropna(subset=[variable])
    y = {"Concentration moyenne observée": jeu["obs_moy"],
         "Gain de la correction (%)": jeu["gain_pct"],
         "RMSE de CAMS brut": jeu["rmse_cams"]}[axe_y]

    fig = go.Figure(go.Scatter(
        x=jeu[variable], y=y, mode="markers",
        marker=dict(size=8, color=BLEU, opacity=0.55,
                    line=dict(width=1, color="rgba(255,255,255,0.8)")),
        text=[f"{n}<br>{t}" for n, t in zip(jeu["nom"], jeu["type_station"])],
        hoverinfo="text+x+y", name="stations"))
    fig.update_layout(xaxis_title=variable, yaxis_title=axe_y, showlegend=False)
    fig.update_layout(hovermode="closest")
    st.plotly_chart(mise_en_forme(fig, 460), use_container_width=True)

    correlation = float(np.corrcoef(jeu[variable], y)[0, 1])
    st.metric(f"Corrélation — {variable} contre {axe_y.lower()}", f"{correlation:+.3f}")
    st.caption(
        "⚠️ Une corrélation ne vaut pas un apport au modèle : les variables de relief "
        "sont fortement corrélées entre elles (jusqu'à −0,90), si bien que leurs "
        "coefficients individuels ne sont pas interprétables. Le gain global, lui, est "
        "mesuré hors échantillon."
    )
