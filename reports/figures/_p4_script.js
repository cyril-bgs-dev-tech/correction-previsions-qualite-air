/* ═══ Page 04 — tableau, cartes, bandes temporelles ═══════════════════════════
   Aucune couleur n'est calculée en JavaScript : tout passe par color-mix() sur les
   variables du thème. Une page qui calcule ses teintes doit les recalculer à chaque
   bascule clair/sombre, et c'est exactement ce qu'on oublie de faire. */
(function () {
  var noeud = document.getElementById('p4-data');
  if (!noeud) return;
  var D = JSON.parse(noeud.textContent);
  var POLS = Object.keys(D.polluants);
  var etat = { p: 'NO2', an: 'toutes', p2: 'NO2' };

  var nf = function (x, d) { return (x >= 0 ? '+' : '') + x.toFixed(d === undefined ? 1 : d); };
  var ent = function (n) { return n.toLocaleString('fr-FR'); };
  var el = function (n, a) {
    var e = document.createElementNS('http://www.w3.org/2000/svg', n);
    for (var k in a) e.setAttribute(k, a[k]);
    return e;
  };

  /* Teinte divergente : |gain| écrêté à 40 %, avec un plancher de 12 % pour qu'une
     station à +2 % ne soit pas indistinguable du fond neutre. */
  function teinte(g) {
    var t = Math.min(Math.abs(g) / 40, 1) * 0.88 + 0.12;
    var pole = g >= 0 ? 'var(--accent)' : 'var(--refute)';
    return 'color-mix(in oklab, ' + pole + ' ' + (t * 100).toFixed(0) +
           '%, var(--neutre-carte))';
  }
  function teinteSeq(t) {
    t = Math.max(0, Math.min(1, t));
    return t < 0.5
      ? 'color-mix(in oklab, var(--seq-1) ' + (t * 200).toFixed(0) + '%, var(--seq-0))'
      : 'color-mix(in oklab, var(--seq-2) ' + ((t - 0.5) * 200).toFixed(0) + '%, var(--seq-1))';
  }

  /* ── 1. Le tableau ───────────────────────────────────────────────────────── */
  function tableau() {
    var tb = document.querySelector('#p4-tab tbody');
    tb.innerHTML = '<tr><th>année</th><th>jours-station</th><th>RMSE CAMS</th>' +
      '<th>AASQA réglée</th><th>AASQA usuelle</th><th>nous</th></tr>';
    POLS.forEach(function (p) {
      var b = D.polluants[p];
      var tr = document.createElement('tr');
      tr.className = 'grp';
      tr.innerHTML = '<td colspan="6">' + b.nom +
        ' <span>· ' + b.grandeur + ' · ' + b.unite + '</span></td>';
      tb.appendChild(tr);
      b.annees.forEach(function (a) {
        var r = document.createElement('tr');
        r.className = a.an === 'toutes' ? 'tot' : 'an';
        var cl = function (v) { return v >= 0 ? 'pos' : 'neg'; };
        // Marquer les cases où leur méthode nous bat : ne pas le signaler serait le cacher.
        var bat = a.gain.aasqa > a.gain.nous ? ' bat' : '';
        r.innerHTML =
          '<td>' + (a.an === 'toutes' ? 'ensemble' : a.an) +
            (a.faible ? ' <span class="marq-faible" title="effectif faible">faible</span>' : '') + '</td>' +
          '<td class="v n">' + ent(a.n) + '<span class="n"> · ' + a.ns + ' st.</span></td>' +
          '<td class="v gris">' + a.rmse.cams.toFixed(2) + '</td>' +
          '<td class="v ' + cl(a.gain.aasqa) + bat + '">' + nf(a.gain.aasqa) + ' %</td>' +
          '<td class="v gris">' + nf(a.gain.usuel) + ' %</td>' +
          '<td class="v ' + cl(a.gain.nous) + '">' + nf(a.gain.nous) + ' %</td>';
        tb.appendChild(r);
      });
    });
  }

  /* ── 2. Les cartes ───────────────────────────────────────────────────────── */
  var W = 400, H = 380, M = 8, proj = null;
  function projection() {
    if (proj) return proj;
    var xs = [], ys = [];
    D.contours.forEach(function (poly) {
      poly.forEach(function (pt) { xs.push(pt[0]); ys.push(pt[1]); });
    });
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
    var y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    var k = Math.min((W - 2 * M) / (x1 - x0), (H - 2 * M) / (y1 - y0));
    var dx = (W - k * (x1 - x0)) / 2, dy = (H - k * (y1 - y0)) / 2;
    proj = function (x, y) { return [dx + k * (x - x0), H - dy - k * (y - y0)]; };
    return proj;
  }

  function carte(svg, cle) {
    var b = D.polluants[etat.p];
    var a = b.annees.filter(function (z) { return z.an === etat.an; })[0];
    var P = projection();
    svg.innerHTML = '';
    D.contours.forEach(function (poly) {
      var d = poly.map(function (pt, i) {
        var q = P(pt[0], pt[1]);
        return (i ? 'L' : 'M') + q[0].toFixed(1) + ' ' + q[1].toFixed(1);
      }).join('') + 'Z';
      svg.appendChild(el('path', { d: d, class: 'contour' }));
    });
    a.st.i.forEach(function (idx, k) {
      var q = P(b.stations.x[idx], b.stations.y[idx]);
      var g = cle === 'ga' ? a.st.ga[k] : a.st.gn[k];
      var c = el('circle', {
        cx: q[0].toFixed(1), cy: q[1].toFixed(1), r: 3.4, class: 'st',
        fill: teinte(g), tabindex: '0', role: 'img',
        'aria-label': b.stations.nom[idx] + ' : ' + nf(g) + ' %'
      });
      c.dataset.k = k;
      svg.appendChild(c);
    });
  }

  function part(a) {
    var n = a.st.i.length, ga = 0, gn = 0;
    a.st.ga.forEach(function (v) { if (v > 0) ga++; });
    a.st.gn.forEach(function (v) { if (v > 0) gn++; });
    return { n: n, ga: ga, gn: gn };
  }

  function dessinerCartes() {
    var b = D.polluants[etat.p];
    var a = b.annees.filter(function (z) { return z.an === etat.an; })[0];
    if (!a) { etat.an = 'toutes'; a = b.annees[b.annees.length - 1]; }
    carte(document.getElementById('p4-svg-a'), 'ga');
    carte(document.getElementById('p4-svg-n'), 'gn');
    document.getElementById('p4-t-a').innerHTML =
      b.aasqa + '<br><b class="' + (a.gain.aasqa >= 0 ? 'pos' : 'neg') + '">' +
      nf(a.gain.aasqa) + ' %</b> contre CAMS brut';
    document.getElementById('p4-t-n').innerHTML =
      'résidu appris · double aveugle<br><b class="pos">' + nf(a.gain.nous) +
      ' %</b> contre CAMS brut';
    var q = part(a);
    // Nommer la fenêtre réelle : « 2026 » quand l'année ne contient qu'un mois est un
    // nom qui ment. Et le tiers de réseau par mois est le protocole, pas une lacune.
    var fen = a.n_mois === 1 ? a.mois[0] : a.mois[0] + ' → ' + a.mois[1];
    document.getElementById('p4-eff').innerHTML =
      '<b>' + ent(a.n) + '</b> jours-station · <b>' + a.n_mois + '</b> mois (' + fen +
      ') · <b>' + a.ns + '</b> stations vues' +
      (a.faible ? ' · <span class="marq-faible">fenêtre courte</span>' : '');
    document.getElementById('p4-part').textContent =
      'stations améliorées : ' + q.ga + ' / ' + q.n + ' pour l\'AASQA · ' +
      q.gn + ' / ' + q.n + ' pour nous';
  }

  /* ── 3. Les bandes temporelles ───────────────────────────────────────────── */
  var BW = 1000, BH = 250, BX = 108, BY = 16, BHB = 42, BG = 6;
  var SERIES = [['obs', 'Observation', 1], ['cams', 'CAMS brut', 0],
                ['aasqa', 'Stratégie AASQA', 0], ['nous', 'Notre système', 0]];

  function bande() {
    var b = D.polluants[etat.p2], s = b.serie, svg = document.getElementById('p4-bande');
    svg.innerHTML = '';
    var n = s.j.length;
    // ⚠️ L'axe suit le CALENDRIER, pas le rang du jour dans la table. Placer les cases
    // par leur indice comprimerait les périodes manquantes sans que rien ne le signale —
    // un trou de trois semaines deviendrait invisible.
    var t0 = Date.parse(s.j[0]), t1 = Date.parse(s.j[n - 1]);
    var utile = BW - BX - 10, jour = 86400000;
    var xDe = function (i) { return BX + (Date.parse(s.j[i]) - t0) / (t1 - t0) * utile; };
    var larg = Math.max(utile / ((t1 - t0) / jour + 1), 0.9);
    // Une échelle commune aux quatre bandes, bornée aux 2e-98e centiles de l'observation :
    // un maximum brut écraserait tout le reste sur une seule journée d'épisode.
    var tri = s.obs.slice().sort(function (x, y) { return x - y; });
    var lo = tri[Math.floor(n * 0.02)], hi = tri[Math.floor(n * 0.98)];
    document.getElementById('p4-b-min').textContent = lo.toFixed(0) + ' ' + b.unite;
    document.getElementById('p4-b-max').textContent = hi.toFixed(0) + ' +';

    SERIES.forEach(function (se, r) {
      var y = BY + r * (BHB + BG);
      svg.appendChild(el('rect', { x: BX, y: y, width: BW - BX - 10, height: BHB,
                                   fill: 'var(--surface-2)' }));
      for (var i = 0; i < n; i++) {
        var t = (s[se[0]][i] - lo) / (hi - lo);
        svg.appendChild(el('rect', { x: xDe(i).toFixed(2), y: y,
                                     width: larg.toFixed(2), height: BHB,
                                     fill: teinteSeq(t) }));
      }
      var t2 = el('text', { x: BX - 8, y: y + BHB / 2 + 3, class: 'lab' + (se[2] ? ' fort' : ''),
                            'text-anchor': 'end' });
      t2.textContent = se[1];
      svg.appendChild(t2);
    });

    // Axe : un trait au 1er janvier, et l'année en clair
    var vus = {};
    s.j.forEach(function (d, i) {
      var an = d.slice(0, 4);
      if (vus[an]) return;
      vus[an] = 1;
      var x = xDe(i);
      svg.appendChild(el('line', { x1: x, x2: x, y1: BY - 3, y2: BY + 4 * (BHB + BG) - BG,
                                   stroke: 'var(--encre-3)', 'stroke-width': .6,
                                   'stroke-dasharray': '2 2' }));
      var t = el('text', { x: x + 3, y: BY + 4 * (BHB + BG) + 6, class: 'ax' });
      t.textContent = an;
      svg.appendChild(t);
    });
    var creux = Math.round((t1 - t0) / jour) + 1 - n;
    var f = el('text', { x: BX, y: BH - 6, class: 'ax' });
    f.textContent = s.j[0] + ' → ' + s.j[n - 1] + ' · ' + n + ' jours mesurés' +
      (creux > 0 ? ', ' + creux + ' journées absentes laissées en blanc' : '') +
      ' · de ' + Math.min.apply(null, s.ns) + ' à ' + Math.max.apply(null, s.ns) + ' stations';
    svg.appendChild(f);
    document.getElementById('p4-eff2').innerHTML =
      '<b>' + n + '</b> jours · échelle commune aux quatre bandes, bornée aux centiles 2 et 98';
    svg.dataset.t0 = t0; svg.dataset.t1 = t1; svg.dataset.utile = utile;
  }

  /* ── 4. Infobulles ───────────────────────────────────────────────────────── */
  function bulle(cadre, bul, cible, html) {
    bul.innerHTML = html;
    bul.setAttribute('data-on', '');
    var rc = cadre.getBoundingClientRect(), rb = cible.getBoundingClientRect();
    var x = rb.left - rc.left + rb.width / 2 - bul.offsetWidth / 2;
    x = Math.max(4, Math.min(x, rc.width - bul.offsetWidth - 4));
    var y = rb.top - rc.top - bul.offsetHeight - 9;
    if (y < 2) y = rb.top - rc.top + rb.height + 9;
    bul.style.left = x + 'px';
    bul.style.top = y + 'px';
  }

  function brancherCartes() {
    var cadre = document.getElementById('p4-cartes-fig');
    var bul = document.getElementById('p4-info');
    ['p4-svg-a', 'p4-svg-n'].forEach(function (id) {
      var svg = document.getElementById(id);
      svg.addEventListener('pointerover', function (e) {
        if (!e.target.classList.contains('st')) return;
        var b = D.polluants[etat.p];
        var a = b.annees.filter(function (z) { return z.an === etat.an; })[0];
        var k = +e.target.dataset.k, idx = a.st.i[k];
        bulle(cadre, bul, e.target,
          '<b>' + b.stations.nom[idx] + '</b>' +
          b.stations.typo[idx] + ' · ' + a.st.n[k] + ' jours<br>' +
          'AASQA <i>' + nf(a.st.ga[k]) + ' %</i> · nous <i>' + nf(a.st.gn[k]) + ' %</i>');
      });
      svg.addEventListener('pointerout', function () { bul.removeAttribute('data-on'); });
      svg.addEventListener('focusin', function (e) {
        if (e.target.classList.contains('st')) e.target.dispatchEvent(
          new PointerEvent('pointerover', { bubbles: true }));
      });
    });
  }

  function brancherBande() {
    var cadre = document.getElementById('p4-bande-fig');
    var bul = document.getElementById('p4-info2');
    var svg = document.getElementById('p4-bande');
    svg.addEventListener('pointermove', function (e) {
      var b = D.polluants[etat.p2], s = b.serie;
      var r = svg.getBoundingClientRect();
      var xs = (e.clientX - r.left) / r.width * BW;
      // L'axe étant calendaire, on remonte de l'abscisse à une DATE, puis à la journée
      // mesurée la plus proche — et on n'affiche rien si elle est à plus de 3 jours.
      var cible = +svg.dataset.t0 +
                  (xs - BX) / (+svg.dataset.utile) * (+svg.dataset.t1 - +svg.dataset.t0);
      var i = -1, ecart = Infinity;
      for (var k = 0; k < s.j.length; k++) {
        var dd = Math.abs(Date.parse(s.j[k]) - cible);
        if (dd < ecart) { ecart = dd; i = k; }
      }
      if (i < 0 || ecart > 3 * 86400000) { bul.removeAttribute('data-on'); return; }
      bul.innerHTML = '<b>' + s.j[i] + '</b>' +
        'observé <i>' + s.obs[i].toFixed(1) + '</i> ' + b.unite + '<br>' +
        'CAMS brut ' + s.cams[i].toFixed(1) + ' · AASQA ' + s.aasqa[i].toFixed(1) +
        ' · nous ' + s.nous[i].toFixed(1) +
        '<small>' + s.ns[i] + ' stations ce jour-là</small>';
      bul.setAttribute('data-on', '');
      var rc = cadre.getBoundingClientRect();
      var x = e.clientX - rc.left - bul.offsetWidth / 2;
      bul.style.left = Math.max(4, Math.min(x, rc.width - bul.offsetWidth - 4)) + 'px';
      bul.style.top = (svg.getBoundingClientRect().top - rc.top - bul.offsetHeight - 6) + 'px';
    });
    svg.addEventListener('pointerleave', function () { bul.removeAttribute('data-on'); });
  }

  /* ── 5. Les filtres ──────────────────────────────────────────────────────── */
  function boutons(hote, liste, actif, clic) {
    hote.innerHTML = '';
    liste.forEach(function (o) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-selected', o.v === actif ? 'true' : 'false');
      b.innerHTML = o.t;
      b.addEventListener('click', function () { clic(o.v); });
      hote.appendChild(b);
    });
  }

  /* Le corpus de l'artefact contre ce que les sources permettent. Un artefact périmé
     ne se distingue pas d'un artefact complet — sauf si la page le dit elle-même. */
  function fraicheur(p, hote) {
    var f = D.polluants[p].fraicheur, e = document.getElementById(hote);
    if (!e) return;
    if (!f || !f.manquants || !f.manquants.length) { e.innerHTML = ''; return; }
    var m = f.manquants;
    e.innerHTML = '<span class="p4-tronque">⚠ corpus tronqué</span> — <b>' + f.n_present +
      '</b> mois utilisés sur <b>' + f.n_dispo + '</b> disponibles· ' + m.length +
      ' mois absents de l\'artefact : ' + m.slice(0, 3).join(', ') +
      (m.length > 3 ? ' … ' + m[m.length - 1] : '') +
      '. Les chiffres ci-dessous portent sur le corpus réduit.';
  }

  function anneesDe(p) {
    return D.polluants[p].annees.map(function (a) {
      return { v: a.an,
               t: (a.an === 'toutes' ? 'ensemble' : a.an) +
                  (a.faible ? ' <span class="faible">' + a.n_mois + ' mois</span>' : '') };
    });
  }

  function filtres() {
    boutons(document.getElementById('p4-pol'),
      POLS.map(function (p) { return { v: p, t: D.polluants[p].nom }; }), etat.p,
      function (v) {
        etat.p = v;
        var dispo = anneesDe(v).map(function (a) { return a.v; });
        if (dispo.indexOf(etat.an) < 0) etat.an = 'toutes';
        filtres(); dessinerCartes(); fraicheur(v, 'p4-fr');
      });
    boutons(document.getElementById('p4-an'), anneesDe(etat.p), etat.an,
      function (v) { etat.an = v; filtres(); dessinerCartes(); });
    boutons(document.getElementById('p4-pol2'),
      POLS.map(function (p) { return { v: p, t: D.polluants[p].nom }; }), etat.p2,
      function (v) { etat.p2 = v; filtres(); bande(); fraicheur(v, 'p4-fr2'); });
  }

  tableau();
  filtres();
  dessinerCartes();
  bande();
  fraicheur(etat.p, 'p4-fr');
  fraicheur(etat.p2, 'p4-fr2');
  brancherCartes();
  brancherBande();
})();
