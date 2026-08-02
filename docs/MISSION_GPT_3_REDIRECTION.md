# Correction à ta mission en cours — le livrable 2 est résolu, redirige-toi

> À coller **avant** que tu ne rendes ta réponse à `MISSION_GPT_2_METEO_ACCESSIBLE.md`.
> Deux de ses trois livrables changent de nature. Ne dépense rien sur le livrable 2.

---

## Ce qui a été vérifié entre-temps

Ta réponse précédente indiquait que l'open data ECMWF ne conserve que les douze derniers runs
et que l'archive historique était dans MARS, sous droit d'accès. **C'est vrai du portail
ECMWF ; c'est faux de la réplique AWS**, interrogée directement le 30/07 :

`https://ecmwf-forecasts.s3.amazonaws.com/` — accès anonyme, licence CC-BY.

- **Profondeur depuis le 18/01/2023**, donc toute la fenêtre d'entraînement (août 2023 →
  décembre 2024).
- Arborescence `AAAAMMJJ/HHz/{ifs,aifs}/0p25/oper/…grib2` — **deux flux déterministes** à
  0,25°, l'un physique (IFS), l'autre neuronal (AIFS).
- Surface : `10u 10v 100u 100v 2t 2d msl sp ssrd ssr strd str tp cape tcwv skt lsm st stl2-4
  swvl1-4 ro asn ttr`.
- **13 niveaux de pression** (1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100,
  50 hPa) : `u v w t q r gh d vo`.
- Chaque pas porte un `.index` de 31 Ko avec `_offset` et `_length` par champ → lecture **par
  plage d'octets**, confirmée en HTTP 206 avec messages GRIB valides.

**Le vent aux niveaux de pression est donc disponible** : `ū_PBL` de ton coefficient de
ventilation est calculable, et la hauteur de mélange — absente en direct — se dérive du profil
par le Richardson bulk que tu avais déjà spécifié au §3.2. Ta spécification tenait sans le
savoir.

**Coût mesuré.** 22 champs utiles = 16,6 Mo sur 118,2 (14 %). Mais le service renvoie
**503 Slow Down dès le troisième appel** espacé de 1,5 s : le goulot est le **nombre de
requêtes**. Le regroupement des plages contiguës donne 1 à 2 requêtes par pas contre 14, au
prix de 2,5× d'octets. Total estimé : ~4 000 requêtes, ~168 Go, 2 à 4 h.

---

## Ce qui devient ta mission

### ⛔ Livrable 2 — annulé

« Trouver une archive de prévision ouverte » est résolu. N'y consacre rien.

### ✅ Livrable 1 — maintenu, mais son statut change

L'expérience d'encadrement par dégradation d'ERA5 reste utile comme **contrôle bon marché**, et
surtout comme **prédiction falsifiable** : si tu spécifies aujourd'hui la dégradation censée
imiter une prévision à J+1, et que la vraie prévision IFS donne ensuite un résultat très
différent, on apprend quelque chose sur la nature de l'erreur de prévision. Garde-le, mais
formule-le comme une prédiction à vérifier, pas comme un substitut.

### 🆕 Livrable 5 — le plan d'extraction, précis

C'est désormais le plus utile. Spécifie :

1. **Quels pas d'échéance** extraire pour reconstituer une journée de prévision J+1 au grain
   réglementaire. Le run de 00z de la veille couvre la journée cible par les pas 24 h à 47 h ;
   l'open data est tri-horaire. Faut-il les huit pas, ou moins suffit-il pour un maximum
   journalier de température et un minimum de couche limite ? Chaque pas économisé vaut 500
   requêtes.
2. **Quels champs exactement**, par ordre de priorité, sachant que le regroupement des plages
   fait que tirer un champ voisin est presque gratuit alors qu'un champ isolé coûte une requête
   entière. Ta liste doit tenir compte de cette économie : elle n'est pas la même que si chaque
   champ coûtait son volume.
3. **La méthode d'interpolation** aux 476 stations depuis une grille 0,25° — plus proche
   voisin, bilinéaire, ou pondérée par la distance ? Et surtout : **cela change-t-il quelque
   chose** pour des variables aussi lisses que la température et le vent synoptique ? Si non,
   dis-le, je prendrai la plus simple.
4. **Le contrôle de complétude** : qu'est-ce qui, dans les données extraites, prouverait qu'un
   pas est arrivé complet ? Ce projet a déjà écrit sous nom définitif un mois amputé de la
   moitié de ses variables, sauté à jamais par la reprise. Je veux un test sur le **contenu**,
   pas sur l'existence du fichier.

### 🆕 Livrable 6 — IFS contre AIFS

Disposer des deux flux sur la même période permet une question que je n'avais pas envisagée :
**le conditionnement d'une correction par une prévision neuronale vaut-il celui d'une prévision
physique ?**

- Qu'est-ce que la littérature établit déjà sur les **différences de structure d'erreur** entre
  IFS et AIFS — biais, dispersion, comportement dans les extrêmes, lissage ?
- Y a-t-il une raison **a priori** pour qu'un modèle neuronal, connu pour lisser, soit un
  moins bon conditionneur d'une correction visant des **maxima** ? Ce projet a mesuré que
  l'écrasement de la variabilité coûte cher sur les statistiques d'ordre.
- Quel protocole compare les deux **à armes égales**, et quel écart serait concluant ?

---

## Rappel de contexte

- Plafond mesuré avec ERA5 : O₃ **+7,8 %**, PM2,5 +6,7 %, NO₂ +2,7 %, IC95 tous positifs,
  décile haut meilleur partout.
- 17 mois appariés, 270 stations, 134 423 jours-station sur O₃.
- Cible : résidu `observation − CAMS` à la grandeur réglementaire.
- Le dossier part sous 48 h ; tout ceci est un programme de recherche présenté à l'entretien,
  pas un résultat annoncé.
