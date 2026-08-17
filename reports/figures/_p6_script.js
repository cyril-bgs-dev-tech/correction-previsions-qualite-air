/* ═══ Page 06 — les 52 épisodes réellement déclenchés ═════════════════════════ */
(function () {
  var n = document.getElementById('p6-data');
  if (!n) return;
  var D = JSON.parse(n.textContent);
  var ent = function (x) { return x.toLocaleString('fr-FR'); };

  /* La signature en trois mots. Celle de cette page ne partage AUCUN terme avec celle
     des pages 04 et 05 : Occitanie et non France, procédures préfectorales et non
     bandes ATMO, J0 et non J+1. Reporter le « 2 sur 33 » d'ici sur le tableau de la
     page 04 comparerait deux mesures sans terme commun — d'où la signature, écrite
     depuis le JSON et jamais recopiée à la main dans la prose. */
  var sg = D.signature, hs = document.getElementById('p6-sig');
  if (sg && hs) {
    hs.innerHTML = '<span>périmètre</span><b>' + sg.perimetre + '</b>' +
                   '<span>épreuve</span><b>' + sg.epreuve + '</b>' +
                   '<span>échéance</span><b>' + sg.echeance + '</b>';
  }

  var TITRE = {
    PM10: ['PM10 · seuil réglementaire',
           'seuil d’information <b>50 µg/m³</b> en moyenne journalière — <strong>exactement la grandeur que nous prédisons</strong>'],
    O3: ['O₃ · à titre indicatif',
         'borne de classe « mauvais », <b>120 µg/m³</b> — <strong>pas</strong> le seuil réglementaire de 180 µg/m³ en maximum horaire, que nous ne prédisons pas']
  };

  var hote = document.getElementById('p6-tables');
  ['PM10', 'O3'].forEach(function (p) {
    var b = D.polluants[p];
    if (!b) return;
    var t = TITRE[p] || [p, ''];
    var h = '<h4>' + t[0] + '</h4><p class="seuil">' + t[1] + '<br>' +
      '<b>' + b.episodes + '</b> épisodes évaluables · <b>' + ent(b.zones_jours) +
      '</b> zones-jours</p>' +
      '<table class="p6-tab"><tbody><tr><th>système</th><th>annoncés</th>' +
      '<th>ratés</th><th>fausses</th><th>rappel</th><th>précision</th></tr>';
    b.systemes.forEach(function (s) {
      var cl = s.nom === 'observation' ? ' class="plafond"'
             : (s.nom === 'notre modèle' ? ' class="nous"' : '');
      h += '<tr' + cl + '><td>' + s.nom + '</td>' +
        '<td class="att">' + s.attrapes + '</td><td>' + s.rates + '</td>' +
        '<td>' + s.fausses + '</td><td>' + s.rappel.toFixed(1).replace('.', ',') + '%</td>' +
        '<td>' + s.precision.toFixed(1).replace('.', ',') + '%</td></tr>';
    });
    h += '</tbody></table><p class="p6-plaf"><strong>La ligne « observation » est le ' +
      'plafond</strong>, pas un concurrent : c’est ce qu’un système parfait, ' +
      'connaissant la mesure, aurait annoncé avec ce seuil et ces stations.</p>';
    var c = document.createElement('div');
    c.className = 'p6-carte';
    c.innerHTML = h;
    hote.appendChild(c);
  });

  /* Les inévaluables — nommés un par un. Un épisode perdu en silence sort du
     dénominateur et flatte le rappel ; c'est la seule raison de les lister. */
  var inv = D.inevaluables, ul = document.getElementById('p6-inev');
  var grouper = function (liste) {
    var par = {};
    liste.forEach(function (x) { par[x.dep] = (par[x.dep] || 0) + x.n; });
    return Object.keys(par).sort().map(function (d) { return d + ' (' + par[d] + ')'; });
  };
  var a = grouper(inv.sans_station), b = grouper(inv.sans_prediction);
  var na = inv.sans_station.reduce(function (s, x) { return s + x.n; }, 0);
  var nb = inv.sans_prediction.reduce(function (s, x) { return s + x.n; }, 0);
  ul.innerHTML =
    '<li><strong>Aucune station dans le réseau national extrait</strong> — <b>' + na +
      '</b> épisode(s) : ' + a.join(', ') + '. Ni Carcassonne, ni Narbonne, ni Cahors : ' +
      'deux départements d’Occitanie sans aucun point de mesure dans l’extraction. ' +
      '<strong>C’est un résultat pour un pôle Partenariats</strong>, pas seulement une ' +
      'limite de notre évaluation.</li>' +
    '<li><strong>Une station, mais aucune prédiction pour ce polluant</strong> — <b>' + nb +
      '</b> épisode(s) : ' + b.join(', ') + '.</li>' +
    '<li><strong>' + inv.total_declares + ' déclarés → ' + (inv.total_declares - na - nb) +
      ' évaluables.</strong> Les sept écartés sont <em>nommés</em>, jamais comptés comme ' +
      'ratés : les compter nous accuserait d’un trou de données, les taire gonflerait ' +
      'notre rappel.</li>';
})();
