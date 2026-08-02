#!/bin/bash
# Membres d'ensemble pour 2025 — les six premiers mois, seuls couverts par les prévisions CAMS.
cd /mnt/d/Projet_Air_Quality
/home/cyril/miniforge3/envs/llm-agent/bin/python3 - <<'PY'
import sys, time, zipfile
sys.path.insert(0,'src'); sys.path.insert(0,'scripts')
from pathlib import Path
from aq.ingest import copernicus as cop
from download_copernicus import SERVICES, lire_cle
D = Path('data/raw/cams_membres')
url, jeu = SERVICES['cams_prevision']
ident = cop.Identifiants(url=url, cle=lire_cle())
membres = cop.MEMBRES_DIVERSIFIES
for espece, court in (('ozone','o3'), ('nitrogen_dioxide','no2'),
                      ('particulate_matter_2.5um','pm25')):
    for mois in range(1, 7):
        cible = D / f'membres_{court}_2025{mois:02d}.nc'
        if cible.exists(): continue
        partiel = cible.with_suffix('.nc.partiel')
        r = cop.requete_cams_prevision(2025, mois, variables=[espece],
                                       echeances_h=range(1,25), modeles=membres)
        t0 = time.time()
        try:
            cop.executer(ident, jeu, r, str(partiel))
        except Exception as e:
            print(f'{cible.name} ÉCHEC {type(e).__name__}: {str(e)[:120]}', flush=True)
            partiel.unlink(missing_ok=True); continue
        # Contrôle de complétude avant renommage : six entrées pour six membres demandés.
        if not zipfile.is_zipfile(partiel):
            print(f'{cible.name} REJETÉ : pas une archive', flush=True)
            partiel.unlink(missing_ok=True); continue
        with zipfile.ZipFile(partiel) as z: n = len(z.namelist())
        if n != len(membres):
            print(f'{cible.name} REJETÉ : {n}/{len(membres)} membres', flush=True)
            partiel.unlink(missing_ok=True); continue
        partiel.rename(cible)
        print(f'{cible.name} · {cible.stat().st_size/1e6:.0f} Mo · {time.time()-t0:.0f}s',
              flush=True)
PY
