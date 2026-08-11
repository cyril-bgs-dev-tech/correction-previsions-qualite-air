(function(){
  var d = JSON.parse(document.getElementById("p8-data").textContent);
  // Les bornes de la thèse DÉRIVENT de la table : écrites en dur, elles se périmeraient
  // à la première re-mesure sans que rien ne le signale.
  var parts = [];
  d.blocs.forEach(function(b){ b.lignes.forEach(function(l){ parts.push(l.part); }); });
  var mn = Math.min.apply(null, parts), mx = Math.max.apply(null, parts);
  var e;
  if ((e = document.getElementById("p8-min"))) e.textContent = mn.toFixed(1) + " %";
  if ((e = document.getElementById("p8-max"))) e.textContent = mx.toFixed(1) + " %";

  var g = document.getElementById("p8-grille"); if (!g) return;
  var h = "";
  d.blocs.forEach(function(b){
    // Le tableau vit dans `.fig-scroll` — six colonnes de chiffres débordent sur un écran
    // étroit, et c'est LA PAGE qui se mettrait à défiler latéralement sans ce conteneur.
    // Même idiome que la page 07 : on n'invente pas un mécanisme, on réemploie le sien.
    h += '<div class="p8-bloc"><h3>' + b.titre + '</h3>'
       + '<p class="p8-sous">' + b.sous + '</p><div class="fig-scroll">'
       + '<table class="p8-tab"><thead><tr><th>Polluant</th><th>Stations</th>'
       + '<th>Dégradées</th><th>Part</th><th>Gain médian</th><th>Pire station</th>'
       + '</tr></thead><tbody>';
    b.lignes.forEach(function(l){
      h += '<tr><td>' + l.polluant + '</td>'
         + '<td>' + l.stations + '</td>'
         + '<td>' + l.degradees + '</td>'
         + '<td class="p8-part">' + l.part.toFixed(1) + ' %</td>'
         + '<td>' + (l.median >= 0 ? "+" : "") + l.median.toFixed(1) + ' %</td>'
         + '<td>' + l.pire.toFixed(1) + ' %</td></tr>';
    });
    h += '</tbody></table></div></div>';
  });
  g.innerHTML = h;

  var s = document.getElementById("p8-sig");
  if (s) s.textContent = "Échéance J+1 · variante « " + d.variante + " » · au moins "
      + d.n_min + " jours par station (" + d.ecartees
      + " écartée(s) au plus, compte publié) · généré le " + d.genere.replace("T", " ");
})();
