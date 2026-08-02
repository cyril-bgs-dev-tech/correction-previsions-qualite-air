# Programme de recherche — ce qui continue après l'envoi

*Arrêté au 30/07/2026. Les chiffres établis vivent dans `reports/VERITE_DOSSIER.md` ; ce
document ne porte que ce qui **reste ouvert**, avec pour chaque piste la mesure qui la
trancherait et le résultat qui l'enterrerait.*

Le dossier envoyé est un état, pas une fin. Trois pistes sont déjà instrumentées et leurs
scripts existent ; ce qui manque est du temps de mesure, pas de la conception.

---

## Pourquoi ce document existe

Un dossier de candidature qui se présente comme achevé invite à chercher ce qui manque. Un
dossier qui **nomme lui-même ce qui manque, avec le protocole pour le trancher**, déplace la
conversation : la question n'est plus « qu'avez-vous oublié ? » mais « que trouveriez-vous
ensuite ? ».

Chaque piste ci-dessous respecte la même discipline que le reste du projet : une hypothèse, une
mesure, et un résultat qui la réfuterait.

---

## Piste 1 — La météo, du plafond au déployable

**Ce qui est mesuré.** Ajouter les variables ERA5 aux prédicteurs rend, sur validation par
stations exclues :

| polluant | RMSE base | gain | relatif | IC95 | effet sur le décile haut |
|---|---|---|---|---|---|
| O₃ | 8,378 | +0,654 | **+7,8 %** | [+0,531 ; +0,783] | −0,42 *(meilleur)* |
| PM2,5 | 2,971 | +0,199 | **+6,7 %** | [+0,152 ; +0,254] | −0,55 *(meilleur)* |
| NO₂ | 15,036 | +0,400 | +2,7 % | [+0,210 ; +0,610] | −1,35 *(meilleur)* |

Les trois intervalles sont strictement positifs, et **la queue s'améliore partout** — il n'y a
pas d'arbitrage entre erreur moyenne et épisodes, ce qui est rare dans ce projet.

**Pourquoi ce n'est pas un résultat du modèle.** ERA5 est une **réanalyse** : elle n'existe pas
à l'heure où la prévision est émise. Le modèle évalué dans le dossier n'utilise, lui, aucune
météo — ses 53 prédicteurs sont tous disponibles à l'émission. Le tableau ci-dessus mesure donc
**ce qu'on se refuse**, pas ce qu'on obtient.

**Ce qui reste à faire — et l'archive existe.** Il faut refaire la mesure avec une météo
**prévue** plutôt que réanalysée. Une première rédaction de ce document affirmait cette piste
bloquée, sur la foi d'une relecture externe indiquant que l'open data ECMWF ne conserve que les
douze derniers runs. **C'est vrai du portail, faux de la réplique AWS**, vérifié le 30/07 par
interrogation directe du seau `ecmwf-forecasts` :

- profondeur d'archive depuis le **18/01/2023**, donc toute la fenêtre d'entraînement ;
- **deux flux** déterministes à 0,25° — **IFS** (physique) et **AIFS** (neuronal) ;
- licence **CC-BY**, accès anonyme ;
- surface : `10u 10v 100u 100v 2t 2d msl sp ssrd ssr strd str tp cape tcwv skt swvl1-4` ;
- **13 niveaux de pression** (1000 → 50 hPa) : `u v w t q r gh d vo` ;
- chaque pas est accompagné d'un **index de 31 Ko** portant `_offset` et `_length` par champ,
  donc lisible **par plage d'octets** : une vingtaine de champs utiles au lieu des 118 Mo du
  pas complet.

Le vent moyen dans la couche mélangée — celui qui manque à notre extraction ERA5, limitée au
vent à 10 m — devient calculable. La hauteur de mélange n'est pas fournie mais se dérive du
profil par le nombre de Richardson bulk.

**Ce que la piste gagne au passage.** Disposer des deux flux sur la même période permet une
question que le projet est équipé pour trancher et qu'il n'avait pas envisagée : *le
conditionnement par une prévision **neuronale** vaut-il celui d'une prévision **physique** ?*
Même protocole, deux produits, une réponse chiffrée.

> **Enterré si** le gain avec météo prévue tombe sous 0,3 µg/m³ sur O₃ avec un IC95 touchant
> zéro : le conditionnement météo ne survivrait pas au passage de la réanalyse à la prévision,
> et l'absence de météo cesserait d'être présentée comme une limite.

*Leçon de méthode, à retenir plus que le résultat : une source déclarée indisponible par un
relecteur compétent l'était sur le portail qu'il connaissait, pas sur la réplique. **Vérifier
soi-même l'accès avant de redimensionner un chantier** — c'est la règle 3 de ce projet, celle
qui avait déjà fait passer le modèle de terrain de « des dizaines de Go » à sept minutes et
zéro octet stocké.*

### Le coût, calculé avant tout lancement

Passe unitaire du 30/07 : l'accès par plage rend **HTTP 206** et des messages GRIB valides, et
les 22 champs utiles pèsent **16,6 Mo sur 118,2** — 14 % du pas. Mais le service renvoie
**503 Slow Down dès le troisième appel**, même espacé de 1,5 s. **Le goulot est le nombre de
requêtes, pas le volume.**

Le regroupement des plages contiguës se calcule alors, et l'arbitrage s'inverse :

| écart toléré entre champs | requêtes / pas | octets tirés | gaspillage |
|---|---|---|---|
| 0 — champs exacts | 14 | 16,6 Mo | 0 % |
| 5 Mo | **2** | 35,0 Mo | 53 % |
| 20 Mo | **1** | 41,9 Mo | 60 % |

Accepter **2,5 fois plus d'octets pour 14 fois moins de requêtes** est ici le bon choix — le
contraire de ce qu'on ferait si la bande passante était contrainte. Sur 8 pas par jour et
500 jours : **4 000 requêtes, ~168 Go transférés, 2 à 4 h** de temps mural, davantage avec les
reprises sur 503.

La sortie, elle, est minuscule : on interpole aux 476 stations à la volée et on jette le GRIB.
Quelques centaines de Mo conservés.

**Dépendance à prévoir** : aucun décodeur GRIB n'est installé (`cfgrib`/`eccodes` absents).
L'installation touche `numpy` et doit attendre qu'aucun ajustement ne tourne — c'est une
contrainte d'ordonnancement, pas un obstacle.

---

## Piste 2 — Le moniteur de dérive : quand faut-il réentraîner ?

**Ce qui est mesuré.** Un détecteur d'anomalies sur l'**état d'entrée** est aveugle aux ruptures
de la chaîne CAMS (55ᵉ et 48ᵉ percentile — le hasard), et c'est structurel : une mise à jour du
modèle amont change la *relation* entre prévision et observation, pas la *distribution* des
entrées. C'est une dérive de **concept**, pas de covariables.

Dans l'espace du **résidu**, la dérive est réelle et chiffrable :

| rupture | décalage du résidu | jours d'accumulation nécessaires | latence observée |
|---|---|---|---|
| 13/11/2024 | +4,76 µg/m³ | 10 j | **13 j** |
| 03/12/2024 | +2,87 µg/m³ | 28 j | non détectée (fenêtre 21 j) |

La théorie prédit l'observation : σ quotidien = 3,87 µg/m³, et il faut `(2×1,96×σ/saut)²` jours.

**Le verrou, et il n'est pas statistique.** Ces 3,87 µg/m³ portent déjà sur une moyenne de
259 stations. Ce qui reste est de la **variabilité synoptique en mode commun** — ajouter des
stations ne l'améliorera pas. Au seuil de 95 %, l'alarme se déclenche une fois tous les
20 jours : inutilisable comme déclencheur de réentraînement.

**Ce qui reste à faire.** Conditionner le résidu au régime météorologique avant de le
surveiller — c'est-à-dire retirer le mode commun. La piste 1 en fournit l'ingrédient.

> **Enterré si** le conditionnement ne réduit pas σ d'au moins un tiers : la latence resterait
> supérieure à trois semaines pour un décalage de 3 µg/m³, et un moniteur qui prévient un mois
> trop tard n'a pas d'usage.

---

## Piste 3 — L'exposition anisotrope au vent

**L'hypothèse, et pourquoi c'est la meilleure qui reste.** Les 28 variables de paysage et les 5
de trafic sont **isotropes** — des distances et des densités dans des cercles. Or une station
sous le vent d'une autoroute à 300 m n'est pas la même station quand le vent tourne. CAMS ne
peut pas le représenter : il a **une valeur par maille de 8 km**, et cette information est
strictement sous-maille. C'est donc le meilleur candidat au regard de la règle dégagée par les
ablations — une correction n'ajoute que là où le modèle amont est aveugle.

Le calcul est écrit et vérifié (`src/aq/features/exposure.py`, `exposition_au_vent`) :
décroissance exponentielle, secteur au vent en cosinus tronqué, vent nul traité. Il n'a jamais
servi.

**Ce qui bloque, mesuré le 30/07.** Les géométries sources — réseau routier, forêt — sont
obtenues en interrogeant un service WFS **à la volée** ; elles ne sont pas conservées, et les
variables gardées ne sont que des sommes, sans azimut.

Un criblage gratuit a été tenté en substituant aux sources leurs mandataires : les 93 stations
de typologie `traffic`. La passe unitaire l'a écarté avant le lot :

| échelle λ | part de valeurs nulles |
|---|---|
| **1 km** — l'échelle visée | **86,4 %** |
| 5 km | 54,5 % |
| 20 km | 7,3 % |

Le mandataire est vide là où l'hypothèse vit ; à 20 km, seule échelle avec du signal, on mesure
du transport régional que CAMS résout déjà. **Aucun mandataire fondé sur les stations ne peut
atteindre l'échelle du kilomètre** — la densité du réseau l'interdit.

**Ce qui reste à faire.** Réinterroger le WFS en conservant, par station, la **distance et
l'azimut de chaque source** plutôt que leur somme. Puis précalculer l'exposition par secteur de
vent et n'effectuer à l'heure qu'une lecture de table.

> **Enterré si** l'exposition anisotrope aux vraies géométries n'apporte rien au-delà du vent
> brut déjà présent dans le jeu météo : l'interaction vent × géographie locale serait alors
> soit absente, soit déjà captée par les variables isotropes et la direction du vent.

---

## Piste 4 — Le grain horaire, là où nous sommes faibles

**Ce qui est mesuré.** Sur le grain **réglementaire**, notre correction devance nettement le
produit officiel de Copernicus. Sur le grain **horaire**, le rapport s'inverse pour le NO₂ :

| polluant | grain horaire — officiel | grain horaire — nous |
|---|---|---|
| O₃ | +16,6 % | +21,7 % |
| **NO₂** | **+16,7 %** | **+2,7 %** |
| PM2,5 | +9,5 % | +20,5 % |

Nous avons optimisé le grain journalier ; nous payons le prix sur l'horaire, exactement comme
le produit officiel paie le sien sur le maximum 8 h. C'est la **même loi**, lue dans les deux
sens — et c'est ce qui rend la thèse falsifiable plutôt que commode.

**Ce qui reste à faire.** Un modèle à deux têtes, ou deux modèles, chacun entraîné sur son
grain. La question n'est pas de savoir si cela marche — le factoriel contrôlé le dit déjà —
mais si un service veut maintenir deux modèles pour un usage horaire qui ne déclenche aucune
procédure.

> **Enterré si** un prévisionniste répond qu'il ne regarde pas les séries horaires de NO₂ pour
> décider : la piste n'aurait alors aucune valeur opérationnelle, quel que soit son gain.
> **Cette question se pose à un humain, pas à une machine** — elle appartient à l'entretien.

---

## Une correction de protocole, à porter au dossier

Le critère d'arrêt du projet — « retenir seulement si le gain atteint **0,3 µg/m³** » — est
exprimé en **unités absolues** et s'applique à des polluants dont le RMSE varie d'un facteur 5.
Pour PM2,5 (RMSE ≈ 3), ce seuil vaut 10 % ; pour NO₂ (RMSE ≈ 15), il vaut 2 %.

Conséquence constatée sur la piste 1 : le critère **écarte** PM2,5 à +6,7 % relatifs tout en
**retenant** NO₂ à +2,7 %. Ce n'est pas un arbitrage scientifique, c'est un artefact d'unité.

Le critère doit devenir **relatif**, ou être fixé par polluant. Ce défaut n'a été vu que parce
qu'une mesure a été conduite sur les trois polluants à la fois — une seule aurait laissé
l'incohérence invisible.

---

## Ce que ce programme ne promet pas

- Aucune de ces pistes ne change la **nature** de ce qui est démontré : la généralisation
  spatiale reste le résultat solide, la généralisation temporelle reste non acquise.
- Aucune ne rend le projet **déployable** : cela dépend de décisions de service — quelles
  entrées sont garanties à l'heure d'émission, quel coût pour une fausse alerte — qui
  appartiennent à l'AASQA, pas au candidat.
- Aucune ne revendique de nouveauté méthodologique. L'effet du grain d'apprentissage est
  **publié** par les auteurs du produit officiel (Bertrand et al. 2023, ACP 23, 5317). Ce
  travail le réplique et caractérise le produit déployé ; il ne le découvre pas.
