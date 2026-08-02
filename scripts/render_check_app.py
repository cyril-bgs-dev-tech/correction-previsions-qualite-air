from playwright.sync_api import sync_playwright
import pathlib, time
SCR = pathlib.Path("/tmp/claude-1000/-mnt-d-Projet-Air-Quality/f3bcaeaf-0254-40ba-8f44-127a50341efe/scratchpad")
PAGES = ["Vue d'ensemble", "Où la correction agit", "Station par station",
         "Détection des épisodes", "Variables du paysage"]
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(("pageerror", str(e)[:200])))
    pg.on("console", lambda m: errs.append(("console", m.text[:200])) if m.type == "error" else None)
    pg.goto("http://localhost:8503", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(6000)
    for i, nom in enumerate(PAGES):
        if i:
            try:
                pg.get_by_text(nom, exact=True).first.click(timeout=15000)
            except Exception as e:
                print("RESULTAT clic échoué", nom, str(e)[:90], flush=True); continue
            pg.wait_for_timeout(7000)
        # Une exception Streamlit s'affiche dans un bloc dédié : on la lit.
        txt = pg.inner_text("body")
        alerte = "Traceback" in txt or "Error" in txt.split("Sources")[0]
        pg.screenshot(path=str(SCR / f"app{i}.png"), full_page=True)
        print(f"RESULTAT page{i} « {nom} » · exception affichée : {alerte}", flush=True)
    print("RESULTAT erreurs js :", errs[:4], flush=True)
    b.close()
