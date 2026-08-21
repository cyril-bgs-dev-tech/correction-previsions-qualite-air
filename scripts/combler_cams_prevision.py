#!/usr/bin/env python3
"""Comble les derniers jours de prévision CAMS — la fenêtre que PREV'AIR a déjà, pas nous.

Pourquoi
---------
Le duel contre PREV'AIR est borné par NOTRE panel, pas par le leur : l'archive PREV'AIR va
au 21/08/2026, nos prévisions CAMS s'arrêtaient au 16. Cinq jours manquants réduisaient la
comparaison sans qu'aucune limite de service ne l'impose.

Coût, calculé avant d'envoyer (`CLAUDE.md` § 1)
-----------------------------------------------
5 jours × 73 échéances × 1 espèce = **365 champs** par requête, pour un plafond ADS de
121 000 — soit **0,3 %**. Ce n'est pas la taille qui coûte ici, c'est l'attente en file ;
la passe unitaire la mesure avant d'engager les trois autres espèces.

Usage : python3 scripts/combler_cams_prevision.py --espece no2 --debut 2026-08-17 --fin 2026-08-21
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from aq.ingest.copernicus import URL_ADS, EMPRISE_FRANCE, cout_champs  # noqa: E402

NOM_ADS = {"no2": "nitrogen_dioxide", "o3": "ozone",
           "pm10": "particulate_matter_10um", "pm25": "particulate_matter_2.5um"}
VAR_NC = {"no2": "no2_conc", "o3": "o3_conc", "pm10": "pm10_conc", "pm25": "pm2p5_conc"}


def cle() -> str:
    for l in (Path.home() / ".cdsapirc").read_text().splitlines():
        if l.strip().startswith("key:"):
            return l.split(":", 1)[1].strip()
    raise SystemExit("aucune ligne 'key:' dans ~/.cdsapirc")


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--espece", default="no2", choices=list(NOM_ADS))
    a.add_argument("--debut", default="2026-08-17")
    a.add_argument("--fin", default="2026-08-21")
    o = a.parse_args()

    import cdsapi
    import pandas as pd
    import xarray as xr

    ech = list(range(73))
    n_jours = (int(o.fin[-2:]) - int(o.debut[-2:])) + 1
    cout = cout_champs(1, len(ech), n_jours)
    print(f"═══ {o.espece} · {o.debut} → {o.fin} · {n_jours} jours ═══")
    print(f"  coût demandé : {cout} champs (plafond 121 000 — {100*cout/121_000:.1f} %)")

    dest = RACINE / f"data/raw/cams_prevision/cams_prevision_{o.espece}_{o.debut[:4]}{o.debut[5:7]}"
    dest.mkdir(parents=True, exist_ok=True)
    brut = dest / f"_comble_{o.debut}_{o.fin}.nc"

    c = cdsapi.Client(url=URL_ADS, key=cle(), quiet=True, progress=False)
    t0 = time.time()
    c.retrieve("cams-europe-air-quality-forecasts", {
        "variable": [NOM_ADS[o.espece]], "model": ["ensemble"], "level": ["0"],
        "type": ["forecast"], "date": [f"{o.debut}/{o.fin}"], "time": ["00:00"],
        "leadtime_hour": [str(h) for h in ech],
        "area": list(EMPRISE_FRANCE), "data_format": "netcdf",
    }, str(brut))
    dt = time.time() - t0
    mo = brut.stat().st_size / 1e6
    print(f"  reçu en {dt:.0f} s · {mo:.1f} Mo · {mo/dt:.2f} Mo/s")

    # Le service livre un **ZIP** sous une extension `.nc` — le tout premier piège de
    # `CLAUDE.md` § 1, et il contient déjà les journées au nom attendu. On ne découpe donc
    # rien : on extrait, puis on VÉRIFIE le contenu de chaque fichier (§ 2 bis, compter le
    # reçu contre le demandé — un code 200 n'est pas un résultat).
    import zipfile
    if not zipfile.is_zipfile(brut):
        raise SystemExit(f"❌ {brut.name} n'est ni un ZIP ni lisible — {open(brut,'rb').read(4)!r}")
    jours = pd.date_range(o.debut, o.fin, freq="D")
    attendus = {f"ENS_FORECAST_{j:%Y-%m-%d}.nc" for j in jours}
    with zipfile.ZipFile(brut) as z:
        recus = {i.filename for i in z.infolist()}
        manquants = attendus - recus
        if manquants:
            raise SystemExit(f"❌ journées absentes du ZIP : {sorted(manquants)}")
        z.extractall(dest)
    var = VAR_NC[o.espece]
    ecrits = 0
    for nom in sorted(attendus):
        f = dest / nom
        d = xr.open_dataset(f)
        if var not in d.data_vars:
            raise SystemExit(f"❌ {nom} : {var} absent — reçu {list(d.data_vars)}")
        if d.sizes.get("time", 0) != len(ech):
            raise SystemExit(f"❌ {nom} : {d.sizes.get('time')} pas de temps au lieu de {len(ech)}")
        v = d[var]
        if float(v.max() - v.min()) < 1e-6:
            raise SystemExit(f"❌ {nom} : champ constant — lecture suspecte")
        d.close()
        ecrits += 1
        print(f"    ✅ {nom} · {f.stat().st_size/1e6:.1f} Mo · {len(ech)} échéances")
    brut.unlink()
    print(f"  {ecrits} journée(s) écrite(s) · extrapolation 4 espèces : {4*dt/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
