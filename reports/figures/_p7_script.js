(function(){
  var d = JSON.parse(document.getElementById("p7-data").textContent);
  var pr = d.produit, me = d.methode, rg = d.reglage;
  function pose(id, v){ var e = document.getElementById(id); if (e) e.textContent = v; }
  // Toutes les mentions de fenêtre et de compte DÉRIVENT de la donnée. Une seule écrite
  // en dur (« sur dix jours d'été ») contredisait déjà l'autre : PM10 en compte onze.
  ["p7-jours", "p7-jours2"].forEach(function(id){ pose(id, pr.jours_max); });
  pose("p7-leurgain", me.leur_gain_max);
  pose("p7-nousdevant", me.nous_devant);
  pose("p7-nbtot", me.n_total);

  function tableau(id, entetes, corps){
    var t = document.getElementById(id); if (!t) return;
    t.innerHTML = '<thead><tr>' + entetes + '</tr></thead><tbody>' + corps + '</tbody>';
  }
  function num(v, n){ return v.toFixed(n === undefined ? 2 : n); }
  function signe(v, n){ return (v > 0 ? '+' : '') + v.toFixed(n === undefined ? 2 : n) + ' %'; }

  // ── ① leur produit ──────────────────────────────────────────────────────────
  tableau("p7-tab",
    '<th>Polluant</th><th>Fenêtre</th><th>Lignes</th><th>CAMS brut</th>'
    + '<th>Nous</th><th>PREV\u2019AIR</th><th>Écart / nous</th>',
    pr.lignes.map(function(l){
      return '<tr><td>' + l.polluant + ' <span class="p7-fen">' + l.produit + '</span></td>'
        + '<td class="p7-fen">' + l.jours + ' j</td>'
        + '<td>' + l.n.toLocaleString("fr-FR") + '</td>'
        + '<td>' + num(l.cams) + '</td>'
        + '<td class="nous">' + num(l.nous) + '</td>'
        + '<td>' + num(l.prevair) + '</td>'
        + '<td class="ecart">+' + l.ecart.toFixed(1) + ' %</td></tr>';
    }).join(""));

  // ── ② leur méthode ──────────────────────────────────────────────────────────
  tableau("p7-tab2",
    '<th>Polluant</th><th>Lignes</th><th>CHIMERE brut</th>'
    + '<th>+ leur krigeage</th><th class="sep">CAMS médiane</th>'
    + '<th>+ krigeage</th><th>+ nous</th>',
    me.lignes.map(function(l){
      return '<tr><td>' + l.polluant + '</td>'
        + '<td class="p7-fen">' + l.n.toLocaleString("fr-FR") + '</td>'
        + '<td>' + num(l.chimere) + '</td>'
        + '<td>' + num(l.chim_krig) + '</td>'
        + '<td class="sep">' + num(l.cams) + '</td>'
        + '<td>' + num(l.cams_krig) + '</td>'
        + '<td class="nous">' + num(l.nous) + '</td></tr>';
    }).join(""));

  // La phrase clé est DÉRIVÉE : elle se périmerait en silence si on l'écrivait.
  var cle = document.getElementById("p7-cle");
  if (cle) cle.innerHTML =
    '<b>Le point de départ pèse autant que la méthode.</b> CHIMERE brut est plus mauvais '
    + 'que la <strong>médiane de l\u2019ensemble dont il est membre</strong> sur '
    + '<strong>' + me.n_depart_perdant + ' polluants sur ' + me.n_total + '</strong> — '
    + 'jusqu\u2019à <strong>' + Math.abs(me.pire_depart).toFixed(0) + ' %</strong>. '
    + 'Moyenner sept modèles vaut mieux que le meilleur d\u2019entre eux, et aucune '
    + 'comparaison de méthodes ne le montre si les deux partent du même endroit.';

  // ── ③ le réglage, des deux côtés ────────────────────────────────────────────
  tableau("p7-tab3",
    '<th>Polluant</th><th>Leur krigeage, au mieux</th><th>Leur krigeage, honnête</th>'
    + '<th class="sep">Notre réglage</th><th>Essais</th>',
    rg.lignes.map(function(l){
      var n = l.notre_gain === null
        ? '<td class="sep p7-attente">en cours</td><td class="p7-attente">—</td>'
        : '<td class="sep nous">' + signe(l.notre_gain) + '</td>'
          + '<td class="p7-fen">' + l.notre_essais + '</td>';
      return '<tr><td>' + l.polluant + '</td>'
        + '<td class="p7-fen">' + signe(l.leur_majorant) + '</td>'
        + '<td class="' + (l.leur_honnete < 0 ? 'perd' : '') + '">'
        + signe(l.leur_honnete) + '</td>' + n + '</tr>';
    }).join(""));

  var c3 = document.getElementById("p7-cle3");
  if (c3) {
    var t = '<b>Le figeage ne décide de rien.</b> Réglé par polluant sur son propre '
      + 'départ, leur krigeage gagne <strong>au plus ' + rg.leur_max.toFixed(2)
      + ' %</strong>, et il <strong>perd</strong> sur ' + rg.leur_negatifs + ' polluants '
      + 'sur ' + rg.lignes.length + ' — régler une interpolation sur le passé ne dit pas '
      + 'qu\u2019elle sera meilleure ensuite.';
    if (rg.mesures > 0) {
      t += ' Notre méthode, au même traitement, gagne <strong>'
        + rg.notre_min.toFixed(2) + ' à ' + rg.notre_max.toFixed(2) + ' %</strong>'
        + (rg.mesures < rg.attendus
            ? ' (mesuré sur ' + rg.mesures + ' polluants sur ' + rg.attendus + ')' : '')
        + '. <strong>La précaution jouait donc contre nous</strong> : les écarts du bloc ② '
        + 'sont des minorants de ce côté-là aussi.';
    } else {
      t += ' Notre côté est en cours de mesure.';
    }
    c3.innerHTML = t;
  }

  var s = document.getElementById("p7-sig");
  if (s) s.textContent = "RMSE en µg/m³ · ① " + pr.debut + " → " + pr.fin
      + " · ② trois ans, station cachée, mêmes lignes pour les six systèmes"
      + " · généré le " + d.genere.replace("T", " ");
})();
