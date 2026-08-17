"""Les calculs de la démo qui coûtent trop cher pour être faits devant un jury.

Pourquoi ce module existe — mesuré le 17/08/2026
--------------------------------------------------
`detection_journaliere` groupe **28,9 M de lignes trois fois**, avec un `iterrows` dans
`sous_indices_journaliers`. Chronométré deux fois, à des moments distincts : **> 120 s**
puis **90 s** — et la pire valeur fait foi (§ 1 ter). Le cache Streamlit portait
`show_spinner=False` : la page « Détection » gelait donc **une fois par session, sans aucun
retour visuel**, au premier clic.

Une démo opérée en direct n'a pas droit à quatre-vingt-dix secondes de page blanche. Le
résultat, lui, fait **huit lignes** : il se calcule une fois à la construction du jeu de
démo et se lit ensuite instantanément.

La fonction vit ici, et non dans `app.py`, pour que `build_demo_data.py` puisse l'appeler
sans importer une page Streamlit — importer l'application pour en extraire un calcul
exécuterait la page.
"""
from __future__ import annotations

import pandas as pd

# Le seuil de complétude de l'indice : un jour n'entre que s'il porte au moins ce nombre
# de sous-indices. ⚠️ Un indice calculé sur un sous-ensemble est **optimiste par
# construction** — le pire de quatre polluants ne peut qu'être supérieur ou égal au pire
# de trois. La démo l'affiche désormais ; le chiffre reste ce qu'il est.
N_REQUIS = 3

LIB = {2: "Moyen ou pire", 3: "Dégradé ou pire", 4: "Mauvais ou pire",
       5: "Très mauvais ou pire"}


def compter(reel: pd.Series, annonce: pd.Series) -> dict[str, float]:
    """Rappel, précision, manques et effectif réel — l'unité de tout tableau de détection."""
    vp = int((reel & annonce).sum())
    return {"rappel": vp / max(1, int(reel.sum())),
            "precision": vp / max(1, int(annonce.sum())),
            "manques": int((reel & ~annonce).sum()), "n": int(reel.sum())}


def detection_journaliere(pred: pd.DataFrame) -> pd.DataFrame:
    """Classe d'indice ATMO du jour, calculée STATION PAR STATION.

    ⚠️ Ce n'est pas « l'échelle de ce qui est publié au public » : l'indice publié est
    **spatialisé** sur une maille, pas calculé en un point (`aq.models.indice_atmo`). C'est
    la **même règle d'agrégation** appliquée à un autre objet.

    L'indice retient le **pire** des sous-indices, sur le maximum horaire du jour pour les
    gaz et la moyenne journalière pour les particules. Cette agrégation par le maximum est
    ce qui rattrape une part de l'amortissement que la correction introduit heure par heure.

    ⚠️ Cette table **ignore le polluant** : l'indice est multi-polluants par construction.
    """
    from aq.models import indice_atmo as idx  # noqa: PLC0415

    tables = {}
    for source, colonne in (("observe", "observe"), ("cams", "cams"), ("mos", "corrige")):
        jeu = pred.rename(columns={colonne: "valeur"})[
            ["station_id", "timestamp_utc", "polluant", "valeur"]].dropna()
        jeu["polluant"] = jeu["polluant"].astype(str)
        indices = idx.indice_par_station(idx.sous_indices_journaliers(jeu))
        tables[source] = idx.indice_complet_seulement(indices, n_requis=N_REQUIS)

    cles = [set(map(tuple, t[["station_id", "jour_local"]].to_numpy()))
            for t in tables.values()]
    communs = set.intersection(*cles)

    def aligner(t: pd.DataFrame) -> pd.DataFrame:
        garde = [tuple(x) in communs for x in t[["station_id", "jour_local"]].to_numpy()]
        return t[garde].sort_values(["station_id", "jour_local"]).reset_index(drop=True)

    ref = aligner(tables["observe"])
    lignes = []
    for seuil, nom in LIB.items():
        reel = ref["indice"] >= seuil
        if reel.sum() < 5:
            continue
        for modele, source in (("CAMS brut", "cams"), ("Corrigé", "mos")):
            lignes.append({"seuil": f"≥ {seuil} — {nom}", "seuil_val": float(seuil),
                           "modele": modele,
                           **compter(reel, aligner(tables[source])["indice"] >= seuil)})
    return pd.DataFrame(lignes)
