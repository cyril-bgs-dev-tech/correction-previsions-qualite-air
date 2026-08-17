/* ═══ Page 00 — les chiffres de tête ══════════════════════════════════════════
   Aucune valeur n'est écrite en dur : tout vient de p0_donnees.json, lui-même
   dérivé des JSON des pages 04 et 06. Deux pages qui affichent le même gain avec
   deux décimales différentes détruisent la confiance dans les deux. */
(function () {
  var n = document.getElementById('p0-data');
  if (!n) return;
  var D = JSON.parse(n.textContent);
  var ent = function (x) { return x.toLocaleString('fr-FR'); };

  var hote = document.getElementById('p0-tuiles');
  D.gains.forEach(function (g) {
    var d = document.createElement('div');
    d.className = 'p0-tuile';
    d.innerHTML =
      '<p class="pol">' + g.nom + '</p>' +
      '<p class="val">+' + g.gain.toFixed(2).replace('.', ',') + '<span style="font-size:19px"> %</span></p>' +
      '<p class="ctx"><b>' + g.n_mois + '</b> mois<br>' + g.fenetre.join(' → ') + '</p>';
    hote.appendChild(d);
  });

  /* La signature en trois mots, affichée avec les chiffres et non dans une note :
     cinq familles de gains portent des noms voisins dans ce dossier, et sur l'ozone
     elles valaient au 08/08/2026 +22,43 %, +22,47 %, +15,83 %, +9,24 % et +3,31 % —
     toutes justes, aucune interchangeable. Un pourcentage sans ses trois mots n'est pas
     citable. (Valeurs d'illustration, datées : la table de VERITE_DOSSIER § 7 ter est
     recalculée à chaque exécution et fait foi.) */
  var sg = D.signature;
  document.getElementById('p0-signature').innerHTML =
    '<span>périmètre</span><b>' + sg.perimetre + '</b>' +
    '<span>épreuve</span><b>' + sg.epreuve + '</b>' +
    '<span>échéance</span><b>' + sg.echeance + '</b>';

  var c = D.contrepoids;
  document.getElementById('p0-contre-chiffre').textContent =
    c.nous + ' sur ' + c.episodes;
  document.getElementById('p0-contre-txt').innerHTML =
    'épisodes PM10 <strong>réellement déclenchés</strong> par un préfet que nous aurions ' +
    'annoncés. La chaîne AASQA en attrape <strong>' + c.aasqa + '</strong>, et ' +
    'l’observation elle-même — le plafond de ce qui était atteignable — <strong>' +
    c.plafond + '</strong>. ' +
    '<strong>Tout le monde est aveugle ici</strong>, nous très légèrement moins. ' +
    'C’est la page 06, et elle est dans ce dossier parce qu’un jury la demanderait.';
})();
