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

NOM = {"O3": "Ozone (O₃)", "NO2": "Dioxyde d'azote (NO₂)", "PM25": "Particules PM2.5"}

# Bornes des classes de l'indice ATMO (arrêté du 10/07/2020), en µg/m³.
BORNES = {"O3": [50, 100, 130, 240, 380], "NO2": [40, 90, 120, 230, 340],
          "PM25": [10, 20, 25, 50, 75]}

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


def _detection(reel: pd.Series, annonce: pd.Series) -> dict[str, float]:
    vp = int((reel & annonce).sum())
    return {"rappel": vp / max(1, int(reel.sum())),
            "precision": vp / max(1, int(annonce.sum())),
            "manques": int((reel & ~annonce).sum()), "n": int(reel.sum())}


def detection_horaire(p: pd.DataFrame, polluant: str) -> pd.DataFrame:
    """Franchissement d'un seuil, heure par heure — l'échelle du déclenchement d'alerte."""
    etiquettes = ["Moyen", "Dégradé", "Mauvais", "Très mauvais", "Extrêmement mauvais"]
    lignes = []
    for seuil, nom in zip(BORNES[polluant], etiquettes):
        reel = p["observe"] >= seuil
        if reel.sum() < 5:
            continue
        for modele, colonne in (("CAMS brut", "cams"), ("Corrigé", "corrige")):
            lignes.append({"seuil": f"≥ {seuil:.0f} — {nom}", "modele": modele,
                           **_detection(reel, p[colonne] >= seuil)})
    return pd.DataFrame(lignes)


@st.cache_data(show_spinner=False)
def detection_journaliere(pred: pd.DataFrame) -> pd.DataFrame:
    """Classe d'indice ATMO du jour — l'échelle de ce qui est publié au public.

    L'indice retient le **pire** des sous-indices, sur le maximum horaire du jour pour
    les gaz et la moyenne journalière pour les particules. Cette agrégation par le
    maximum est ce qui rattrape l'amortissement que la correction introduit heure par
    heure : les deux échelles ne rendent pas le même verdict, et il faut les deux.
    """
    from aq.models import indice_atmo as idx

    tables = {}
    for source, colonne in (("observe", "observe"), ("cams", "cams"),
                            ("mos", "corrige")):
        jeu = pred.rename(columns={colonne: "valeur"})[
            ["station_id", "timestamp_utc", "polluant", "valeur"]].dropna()
        jeu["polluant"] = jeu["polluant"].astype(str)
        indices = idx.indice_par_station(idx.sous_indices_journaliers(jeu))
        tables[source] = idx.indice_complet_seulement(indices, n_requis=3)

    cles = [set(map(tuple, t[["station_id", "jour_local"]].to_numpy()))
            for t in tables.values()]
    communs = set.intersection(*cles)

    def aligner(t: pd.DataFrame) -> pd.DataFrame:
        garde = [tuple(x) in communs
                 for x in t[["station_id", "jour_local"]].to_numpy()]
        return (t[garde].sort_values(["station_id", "jour_local"])
                .reset_index(drop=True))

    ref = aligner(tables["observe"])
    LIB = {2: "Moyen ou pire", 3: "Dégradé ou pire", 4: "Mauvais ou pire",
           5: "Très mauvais ou pire"}
    lignes = []
    for seuil, nom in LIB.items():
        reel = ref["indice"] >= seuil
        if reel.sum() < 5:
            continue
        for modele, source in (("CAMS brut", "cams"), ("Corrigé", "mos")):
            lignes.append({"seuil": f"≥ {seuil} — {nom}", "modele": modele,
                           **_detection(reel, aligner(tables[source])["indice"] >= seuil)})
    return pd.DataFrame(lignes)


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

polluant = st.sidebar.selectbox("Polluant", list(NOM), format_func=NOM.get)
st.sidebar.divider()
st.sidebar.caption(
    "Sources — mesures : EEA · prévisions et modèle de terrain : Copernicus "
    "(CAMS, DEM GLO-30) · paysage : IGN Géoplateforme · stations : LCSQA."
)

resume_tout = charger("resume_stations")
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

    # ── Régime météo, qui conditionne la confiance ──
    st.subheader("Régime du jour, et confiance associée")
    mois = pd.Timestamp(jour).strftime("%Y%m")
    chemin_meteo = DEMO.parent / "processed" / "meteo" / f"era5_metropole_{mois}.parquet"
    if chemin_meteo.exists():
        meteo = pd.read_parquet(chemin_meteo)
        meteo["jour"] = meteo["timestamp_utc"].dt.tz_convert("Europe/Paris").dt.date
        m = meteo[meteo["jour"] == jour]
        if not m.empty:
            couche = m["couche_limite_m"].mean()
            vent = m["vent_vitesse_m_s"].mean()
            rayon = m["rayonnement_w_m2"].mean()
            if couche < 300 and vent < 2:
                regime, fiable = "stagnation", polluant != "O3"
            elif rayon > 150:
                regime, fiable = "photochimique", True
            else:
                regime, fiable = "ventilé", polluant != "O3"

            g1, g2, g3 = st.columns(3)
            g1.metric("Couche limite", f"{couche:.0f} m")
            g2.metric("Vent moyen", f"{vent:.1f} m/s")
            g3.metric("Rayonnement", f"{rayon:.0f} W/m²")

            if fiable:
                st.success(
                    f"**Régime {regime}.** Dans ce régime, la correction améliore aussi "
                    "les fortes valeurs — elle peut être suivie sur les pics.")
            else:
                st.error(
                    f"**Régime {regime} — prudence sur les pics.** Mesuré sur l'ozone : "
                    "la correction dégrade de 17 % le décile supérieur dans ce régime. "
                    "Elle reste fiable sur le fond, pas sur les maxima.")
        else:
            st.info("Météo indisponible pour ce jour.")
    else:
        st.info(f"Météo non extraite pour {mois}.")

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

    st.caption(
        "⚠️ Cette page est un **prototype d'aide à la décision**, pas un outil validé. "
        "Elle repose sur trois mois de 2024 et sur une correction dont la généralisation "
        "temporelle n'est pas démontrée. Sa valeur est de montrer la forme qu'un tel "
        "outil pourrait prendre, pas de se substituer à l'expertise."
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
        st.caption(
            "Le gain n'est pas uniforme : il se concentre sur les valeurs basses, et la "
            "correction fait **jeu égal** dans la queue. C'est voulu — une version "
            "antérieure gagnait 13 % de RMSE global en écrasant complètement les épisodes."
        )
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
        st.caption(f"Sur {len(resume)} stations, en validation par **station exclue** — "
                   "chacune est prédite par un modèle qui ne l'a jamais vue.")
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
    fig = go.Figure(go.Scattergeo(
        lon=vue["lon_wgs84"], lat=vue["lat_wgs84"], mode="markers",
        marker=dict(
            size=8, color=vue["gain_pct"], colorscale=[[0, "#d03b3b"], [0.5, "#f0efec"],
                                                       [1, BLEU]],
            cmin=-50, cmax=50, line=dict(width=0.6, color="rgba(255,255,255,0.85)"),
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
    detection = (detection_journaliere(pred) if echelle.startswith("Classe")
                 else detection_horaire(pred[pred["polluant"] == polluant], polluant))

    if detection.empty:
        st.warning("Trop peu de dépassements pour conclure.")
        st.stop()

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

    pivot = detection.pivot(index="seuil", columns="modele", values="manques")
    ecart = int((pivot["CAMS brut"] - pivot["Corrigé"]).sum())
    if ecart > 0:
        st.success(f"**{ecart} épisodes manqués en moins.** C'est la même mesure qu'un "
                   "gain de RMSE, exprimée dans l'unité qui engage une AASQA.")
    else:
        st.error(f"**{abs(ecart)} épisodes manqués de plus.** À cette échelle, la "
                 "correction échange du rappel contre de la précision — et pour un "
                 "usage d'alerte, c'est le mauvais côté de l'échange.")

    st.dataframe(
        detection.assign(rappel=lambda d: (100 * d["rappel"]).round(1),
                         precision=lambda d: (100 * d["precision"]).round(1))
        .rename(columns={"seuil": "Seuil", "modele": "Modèle", "rappel": "Rappel (%)",
                         "precision": "Précision (%)", "manques": "Épisodes manqués",
                         "n": "Épisodes réels"}),
        hide_index=True, use_container_width=True)

    st.info(
        "**Pourquoi les deux échelles divergent.** À l'échelle **horaire**, la correction "
        "amortit les valeurs extrêmes : elle gagne en précision et **perd en rappel**. "
        "À l'échelle **journalière** — celle de l'indice publié — l'agrégation par le "
        "maximum des 24 heures rattrape cet amortissement, et le rappel progresse. "
        "C'est l'indice qui est publié, mais un déclenchement d'alerte se décide sur "
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
