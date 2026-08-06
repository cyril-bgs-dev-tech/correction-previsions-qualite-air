/* ═══ Page 05 — profils d'erreur de bande ═════════════════════════════════════ */
(function () {
  var n = document.getElementById('p5-data');
  if (!n) return;
  var D = JSON.parse(n.textContent);
  var POLS = Object.keys(D.polluants);
  var etat = { p: 'NO2' };
  var ent = function (x) { return x.toLocaleString('fr-FR'); };

  /* Cinq segments, pas neuf : au-delà de deux bandes d'écart, l'agrégat suffit et
     les parts deviennent trop fines pour être vues. Les valeurs exactes restent
     dans l'infobulle. */
  var SEG = [
    ['≤ −2', 'd-neg2', function (q) { return q['-4'] + q['-3'] + q['-2']; }, 'sous-classé de 2 bandes ou plus'],
    ['−1', 'd-neg1', function (q) { return q['-1']; }, 'sous-classé d’une bande'],
    ['exact', 'd-zero', function (q) { return q['0']; }, 'bande exacte'],
    ['+1', 'd-pos1', function (q) { return q['1']; }, 'sur-classé d’une bande'],
    ['≥ +2', 'd-pos2', function (q) { return q['2'] + q['3'] + q['4']; }, 'sur-classé de 2 bandes ou plus']
  ];

  function bulle(cadre, bul, cible, html) {
    bul.innerHTML = html;
    bul.setAttribute('data-on', '');
    var rc = cadre.getBoundingClientRect(), rb = cible.getBoundingClientRect();
    var x = rb.left - rc.left + rb.width / 2 - bul.offsetWidth / 2;
    bul.style.left = Math.max(4, Math.min(x, rc.width - bul.offsetWidth - 4)) + 'px';
    var y = rb.top - rc.top - bul.offsetHeight - 8;
    bul.style.top = (y < 2 ? rb.top - rc.top + rb.height + 8 : y) + 'px';
  }

  function entete(a) {
    // « 2026 » quand l'année ne porte qu'un mois est un nom qui ment : la fenêtre
    // réelle est écrite à côté. Et le nombre de stations est celui du TIERS de réseau
    // évalué chaque mois — le protocole cache un tiers des stations à la fois.
    var fen = a.n_mois === 1 ? a.mois[0] : a.n_mois + ' mois · ' + a.mois[0] + ' → ' + a.mois[1];
    return '<h5>' + (a.an === 'toutes' ? 'Ensemble de la période' : a.an) +
      (a.faible ? ' <span class="p5-faible">' + fen + '</span>'
                : ' <span class="p5-faible">' + a.n_mois + ' mois</span>') + '</h5>' +
      '<p class="meta"><b>' + ent(a.n) + '</b> jours-station · <b>' + a.ns +
      '</b> stations vues · <b>' + ent(a.n_crit) +
      '</b> journées observées en bande mauvaise ou pire</p>';
  }

  /* ── Bloc 1 : les profils ────────────────────────────────────────────────── */
  function profils() {
    var b = D.polluants[etat.p], hote = document.getElementById('p5-grille');
    var cadre = document.getElementById('p5-fig'), bul = document.getElementById('p5-info');
    hote.innerHTML = '';
    b.annees.forEach(function (a) {
      var c = document.createElement('div');
      c.className = 'p5-carte';
      var h = entete(a);
      D.systemes.forEach(function (sy) {
        var q = a.sys[sy.c].part, nous = sy.c.indexOf('tete') === 0;
        h += '<div class="p5-lig' + (nous ? ' nous' : '') + '">' +
             '<span class="nm">' + sy.n + '</span>' +
             '<span class="p5-barre" tabindex="0" data-s="' + sy.c + '" data-a="' + a.an + '">' +
             SEG.map(function (s) {
               var v = s[2](q);
               return '<span class="' + s[1] + '" style="width:' + v.toFixed(2) + '%"></span>';
             }).join('') + '</span>' +
             '<span class="val">' + a.sys[sy.c].exact.toFixed(1) + '%</span></div>';
      });
      c.innerHTML = h;
      hote.appendChild(c);
    });
    hote.querySelectorAll('.p5-barre').forEach(function (e) {
      var montre = function () {
        var a = b.annees.filter(function (z) { return z.an === e.dataset.a; })[0];
        var s = a.sys[e.dataset.s];
        var nom = D.systemes.filter(function (z) { return z.c === e.dataset.s; })[0];
        bulle(cadre, bul, e, '<b>' + nom.n + ' · ' + (a.an === 'toutes' ? 'ensemble' : a.an) + '</b>' +
          nom.d + '<br>' +
          SEG.map(function (g) { return g[3] + ' : <i>' + g[2](s.part).toFixed(1) + ' %</i>'; })
             .join('<br>') +
          '<small>distance moyenne ' + s.dist_moy.toFixed(3) + ' bande · ' +
          ent(a.n) + ' jours-station</small>');
      };
      e.addEventListener('pointerenter', montre);
      e.addEventListener('focus', montre);
      e.addEventListener('pointerleave', function () { bul.removeAttribute('data-on'); });
      e.addEventListener('blur', function () { bul.removeAttribute('data-on'); });
    });
  }

  /* ── Bloc 2 : les journées critiques manquées ────────────────────────────── */
  function critiques() {
    var b = D.polluants[etat.p], hote = document.getElementById('p5-crit');
    var cadre = document.getElementById('p5-crit-fig'), bul = document.getElementById('p5-info2');
    hote.innerHTML = '';
    b.annees.forEach(function (a) {
      var vals = D.systemes.map(function (sy) { return a.sys[sy.c].crit_manquees; });
      var dispo = vals.filter(function (v) { return v !== null; });
      var c = document.createElement('div');
      c.className = 'p5-carte';
      var h = entete(a);
      if (!dispo.length) {
        h += '<p class="meta">Aucune journée observée en bande mauvaise ou pire cette ' +
             'année-là — la mesure n’a pas d’objet.</p>';
      } else {
        var mini = Math.min.apply(null, dispo);
        D.systemes.forEach(function (sy, i) {
          var v = vals[i];
          h += '<div class="p5-lig' + (v === mini ? ' best' : '') + '">' +
               '<span class="nm">' + sy.n + '</span>' +
               '<span class="mq" tabindex="0" data-s="' + sy.c + '" data-a="' + a.an + '">' +
               (v === null ? '' : '<i style="width:' + v.toFixed(1) + '%"></i>') + '</span>' +
               '<span class="val">' + (v === null ? '—' : v.toFixed(1) + '%') + '</span></div>';
        });
      }
      c.innerHTML = h;
      hote.appendChild(c);
    });
    hote.querySelectorAll('.mq').forEach(function (e) {
      var montre = function () {
        var a = b.annees.filter(function (z) { return z.an === e.dataset.a; })[0];
        var s = a.sys[e.dataset.s];
        var nom = D.systemes.filter(function (z) { return z.c === e.dataset.s; })[0];
        var manq = Math.round(s.crit_manquees / 100 * a.n_crit);
        bulle(cadre, bul, e, '<b>' + nom.n + ' · ' + (a.an === 'toutes' ? 'ensemble' : a.an) + '</b>' +
          '<i>' + manq + '</i> journées annoncées plus bénignes qu’elles ne le sont, ' +
          'sur <i>' + ent(a.n_crit) + '</i> observées en bande mauvaise ou pire.' +
          '<small>bande exacte tous jours confondus : ' + s.exact.toFixed(1) + ' %</small>');
      };
      e.addEventListener('pointerenter', montre);
      e.addEventListener('focus', montre);
      e.addEventListener('pointerleave', function () { bul.removeAttribute('data-on'); });
      e.addEventListener('blur', function () { bul.removeAttribute('data-on'); });
    });
  }

  function bandes() {
    var b = D.polluants[etat.p];
    document.getElementById('p5-bandes').innerHTML = 'bandes ' + b.nom + ' : ' +
      b.bandes.map(function (z) {
        return z.max === null ? '≥ <b>' + z.min + '</b>' : '<b>' + z.max + '</b>';
      }).join(' · ') + ' µg/m³';
  }

  function filtres() {
    var h = document.getElementById('p5-pol');
    h.innerHTML = '';
    POLS.forEach(function (p) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-selected', p === etat.p ? 'true' : 'false');
      b.textContent = D.polluants[p].nom;
      b.addEventListener('click', function () {
        etat.p = p; filtres(); bandes(); profils(); critiques();
      });
      h.appendChild(b);
    });
  }

  /* La signature en trois mots. Deux signatures cohabitent sur cette page, et c'est le
     fond du sujet : le § 15 ne porte ni le même périmètre (Occitanie, pas la France), ni
     la même épreuve (épisodes préfectoraux, pas bandes ATMO), ni la même échéance (J0,
     pas J+1) que les deux figures qui le précèdent. Une signature unique mentirait. */
  function poser(cible, s) {
    if (!cible || !s) return;
    cible.innerHTML = '<span>périmètre</span><b>' + s.perimetre + '</b>' +
                      '<span>épreuve</span><b>' + s.epreuve + '</b>' +
                      '<span>échéance</span><b>' + s.echeance + '</b>';
  }
  function signer() {
    var t = document.querySelectorAll('#seuils .sig3');
    for (var i = 0; i < t.length; i++) {
      if (t[i].id !== 'p5-persist-sig') poser(t[i], D.signature);
    }
    poser(document.getElementById('p5-persist-sig'),
          (D.persistance || {}).signature);
  }

  /* ── § 15 · la persistance ─────────────────────────────────────────────────
     Les quatre systèmes, toujours. Le tableau existe pour montrer que le −34 % de
     notre ligne n'a rien d'une propriété du modèle : l'observation elle-même fait
     mieux. N'afficher que notre ligne serait un chiffre juste et une phrase fausse. */
  function persistance() {
    var P = D.persistance;
    if (!P) return;
    var tb = document.querySelector('#p5-persist tbody');
    tb.innerHTML =
      '<tr><th>système</th><th>épisodes attrapés</th>' +
      '<th>fausses alertes<span>règle instantanée</span></th>' +
      '<th>fausses alertes<span>2 jours de suite</span></th>' +
      '<th>écart</th><th>rappel</th></tr>';
    P.systemes.forEach(function (s) {
      var r = document.createElement('tr');
      r.className = s.nom === 'notre modèle' ? 'nous' : (s.gratuite ? '' : 'coute');
      var ep = s.avec.attrapes + ' / ' + s.episodes;
      r.innerHTML =
        '<td>' + s.nom + (s.gratuite ? '' :
          ' <span class="marq-faible" title="la persistance lui coûte un épisode">'
          + 'coûte un épisode</span>') + '</td>' +
        '<td class="v">' + ep + '</td>' +
        '<td class="v gris">' + ent(s.sans.fausses) + '</td>' +
        '<td class="v">' + ent(s.avec.fausses) + '</td>' +
        '<td class="v pos">' + s.delta_fausses_pct.toFixed(1) + ' %</td>' +
        '<td class="v ' + (s.gratuite ? 'gris' : 'neg') + '">' +
          s.sans.rappel.toFixed(1) + ' → ' + s.avec.rappel.toFixed(1) + ' %</td>';
      tb.appendChild(r);
    });
    var n = P.systemes[0];
    document.getElementById('p5-persist-conf').innerHTML =
      'Configuration, en toutes lettres&#8239;: <b>' + P.conf.polluant + '</b> · seuil <b>' +
      P.conf.seuil + ' µg/m³</b> — valeur cible européenne, <em>pas</em> le seuil de ' +
      'procédure française à 180 · règle d\'agrégation <b>' + P.conf.regle + '</b> · ' +
      '<b>' + ent(n.zones_jours) + '</b> zones-jours, <b>' + n.episodes +
      '</b> épisodes déclarés · au moins <b>' + P.conf.min_stations +
      '</b> station par département.';
  }

  filtres(); bandes(); profils(); critiques(); persistance(); signer();
})();
