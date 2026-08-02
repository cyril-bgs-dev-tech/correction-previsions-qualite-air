"""Audit de contraste sur le rendu réel, plutôt qu'à l'œil sur une capture."""
from playwright.sync_api import sync_playwright
import pathlib

SCR = pathlib.Path("/tmp/claude-1000/-mnt-d-Projet-Air-Quality/"
                   "f3bcaeaf-0254-40ba-8f44-127a50341efe/scratchpad")

JS = """
() => {
  const lum = c => {
    const [r,g,b] = c.match(/\\d+/g).map(Number).map(v => {
      v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
    });
    return 0.2126*r + 0.7152*g + 0.0722*b;
  };
  const ratio = (a,b) => { const L1 = Math.max(lum(a),lum(b)), L2 = Math.min(lum(a),lum(b));
    return (L1+0.05)/(L2+0.05); };
  const racine = document.querySelector('.doc') || document.querySelector('.viz-root');
  const fond = getComputedStyle(racine).backgroundColor;
  const out = [];
  const vus = new Set();
  document.querySelectorAll('td, th, p, li, .fsub, .kpi .val, .kpi .note, .kpi .lab, summary, .num, h2, h3')
    .forEach(e => {
      const cs = getComputedStyle(e);
      const cle = e.tagName + '|' + e.className + '|' + cs.color;
      if (vus.has(cle)) return; vus.add(cle);
      let bg = fond, p = e;
      while (p && p !== document.documentElement) {
        const c = getComputedStyle(p).backgroundColor;
        if (c && c !== 'rgba(0, 0, 0, 0)') { bg = c; break; }
        p = p.parentElement;
      }
      out.push({sel: e.tagName + (e.className ? '.' + e.className.split(' ')[0] : ''),
                couleur: cs.color, fond: bg, ratio: +ratio(cs.color, bg).toFixed(2),
                exemple: (e.textContent || '').trim().slice(0, 34)});
    });
  return out.sort((a,b) => a.ratio - b.ratio);
}
"""

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for src in ("figures.html", "presentation.html"):
        for mode in ("light", "dark"):
            pg = b.new_page(viewport={"width": 1120, "height": 900}, color_scheme=mode)
            pg.goto(f"file://{SCR/src}")
            pg.wait_for_timeout(600)
            res = pg.evaluate(JS)
            faibles = [r for r in res if r["ratio"] < 4.5]
            print(f"RESULTAT === {src} · {mode} · {len(res)} éléments · "
                  f"{len(faibles)} sous 4,5:1", flush=True)
            for r in faibles[:8]:
                print(f"RESULTAT   {r['ratio']:5.2f}  {r['sel']:22s} {r['couleur']:20s} "
                      f"sur {r['fond']:20s} « {r['exemple']} »", flush=True)
            pg.close()
    b.close()
