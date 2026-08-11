(function(){
  var d = JSON.parse(document.getElementById("p7-data").textContent);
  // Les DEUX mentions de la fenêtre dérivent de la donnée. Une seule écrite en dur
  // (« sur dix jours d'été ») contredisait déjà l'autre : PM10 en compte onze.
  ["p7-jours", "p7-jours2"].forEach(function(id){
    var e = document.getElementById(id); if (e) e.textContent = d.jours_max;
  });
  var t = document.getElementById("p7-tab"); if (!t) return;
  var h = '<thead><tr><th>Polluant</th><th>Fenêtre</th><th>Lignes</th>'
        + '<th>CAMS brut</th><th>Nous</th><th>PREV\u2019AIR</th>'
        + '<th>Écart / nous</th></tr></thead><tbody>';
  d.lignes.forEach(function(l){
    h += '<tr><td>' + l.polluant + ' <span class="p7-fen">' + l.produit + '</span></td>'
       + '<td class="p7-fen">' + l.jours + ' j</td>'
       + '<td>' + l.n.toLocaleString("fr-FR") + '</td>'
       + '<td>' + l.cams.toFixed(2) + '</td>'
       + '<td class="nous">' + l.nous.toFixed(2) + '</td>'
       + '<td>' + l.prevair.toFixed(2) + '</td>'
       + '<td class="ecart">+' + l.ecart.toFixed(1) + ' %</td></tr>';
  });
  t.innerHTML = h + '</tbody>';
  var s = document.getElementById("p7-sig");
  if (s) s.textContent = "RMSE en µg/m³ · " + d.debut + " → " + d.fin
      + " · les trois systèmes sur exactement les mêmes lignes · généré le "
      + d.genere.replace("T", " ");
})();
