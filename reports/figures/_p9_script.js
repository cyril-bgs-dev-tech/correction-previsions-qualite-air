(function(){
  var d = JSON.parse(document.getElementById("p9-data").textContent);
  var vf = function(x, n){ return x.toFixed(n === undefined ? 1 : n).replace('.', ','); };
  var pose = function(id, txt){ var e = document.getElementById(id); if (e) e.textContent = txt; };

  // ── La thèse DÉRIVE du comptage. Écrite en dur, elle se périmerait à la première
  // re-mesure sans que rien ne le signale — c'est le défaut que ce dossier traque.
  var s = d.seuils;
  pose("p9-avant", String(s.union_actuel));
  pose("p9-apres", String(s.union_2030));
  pose("p9-facteur", "×" + vf(s.union_2030 / Math.max(s.union_actuel, 1)));
  pose("p9-sous-seuils",
       "moyennes annuelles " + d.annee + ", taux de saisie ≥ " + vf(d.saisie_min * 100, 0)
       + " % · " + s.parc + " stations évaluées · l'ozone est exclu : il n'a pas de valeur "
       + "limite annuelle mais une valeur cible sur le maximum 8 h");

  var h = "<thead><tr><th>Polluant</th><th>VL en vigueur</th><th>VL 2030</th>"
        + "<th>Évaluées</th><th>&gt; en vigueur</th><th>&gt; 2030</th><th>Basculent</th>"
        + "</tr></thead><tbody>";
  s.lignes.forEach(function(l){
    h += "<tr><td>" + l.polluant + "</td>"
       + "<td>" + l.vl_actuelle + " µg/m³</td>"
       + "<td class=\"p9-fort\">" + l.vl_2030 + " µg/m³</td>"
       + "<td>" + l.evaluees + "</td>"
       + "<td>" + l.depasse_actuel + "</td>"
       + "<td class=\"p9-fort\">" + l.depasse_2030 + "</td>"
       + "<td class=\"p9-fort\">+" + l.bascule + "</td></tr>";
  });
  document.getElementById("p9-tab-seuils").innerHTML = h + "</tbody>";

  // ── Le territoire : publié seulement s'il existe dans les données.
  var t = s.territoire, bloc = document.getElementById("p9-territoire-bloc");
  if (!t) { if (bloc) bloc.style.display = "none"; }
  else {
    pose("p9-territoire",
         "En Occitanie, " + t.actuel + " station(s) en dépassement aujourd'hui, " + t.en_2030
         + " en 2030, sur " + t.evaluees + " évaluées. Et " + t.depts_sans + " des "
         + t.depts_total + " départements n'ont aucune station retenue (" + t.sans.join(", ")
         + ") : pour eux, la conformité 2030 ne peut pas être posée depuis la mesure. "
         + "C'est exactement le cas que la directive confie à la modélisation.");
  }

  // ── Le critère de qualité, un régime par colonne.
  var f = d.fairmode;
  pose("p9-seuil", vf(f.seuil, 0));
  pose("p9-sous-fairmode",
       "part des stations satisfaisant MQI_f ≤ 1, échéance " + f.echeance
       + " · le critère est atteint à partir de " + vf(f.seuil, 0) + " %"
       + (f.absents.length ? " · non mesuré sur : " + f.absents.join(", ") : ""));

  var g = "<thead><tr><th>Polluant</th><th>Stations</th>";
  f.modes.forEach(function(m){
    g += "<th>" + m.libelle + "<span class=\"p9-sousmode\">" + m.sous + "</span></th>";
  });
  g += "</tr></thead><tbody>";
  f.lignes.forEach(function(l){
    g += "<tr><td>" + l.polluant + "</td><td>" + l.stations + "</td>";
    f.modes.forEach(function(m){
      var c = l[m.cle], ok = c.part >= f.seuil;
      g += "<td class=\"" + (ok ? "p9-ok" : "p9-non") + "\">"
         + vf(c.part) + " %&#8239;" + (ok ? "✓" : "✗") + "</td>";
    });
    g += "</tr>";
  });
  document.getElementById("p9-tab-fairmode").innerHTML = g + "</tbody>";

  // ── Le biais NO₂ cité dans la réserve vient de la table, pas d'une saisie.
  var no2 = f.lignes.filter(function(l){ return l.polluant === "NO₂"; })[0];
  if (no2) {
    pose("p9-biais-raw", vf(no2.RAW.biais, 2));
    pose("p9-biais-full", vf(no2.FULL.biais, 2));
  }

  pose("p9-sig", "Seuils : directive (UE) 2024/2881, annexe I · comptage sur "
       + d.annee + " · critère de qualité : MQI_f à l'échéance " + f.echeance
       + " · généré le " + d.genere.replace("T", " "));
})();
