# GROK 70 — La qualité de l’air telle qu’on la pratique

*Réponses métier (prévision / AASQA). Pas de physico-chimie ni de métrologie de labo.  
Jugement de praticien sauf mention [publié]/[vu]. Premisses fausses signalées.*

**Contexte candidat (rappel) :** MOS CAMS Europe, grandeurs réglementaires, J−2 déployable, spatial OK / temporel non, MOS officiel fragile en saison O₃.

---

## A. La salle de prévision (1–12)

**1.** Tour des sorties de la nuit (PREV’AIR / CHIMERE / CAMS selon boîte), lecture des mesures temps réel et validations, météo du jour et J+1/J+2, cohérence spatiale des cartes, rédaction ou validation de la « météo de l’air » / indices, points mail ou points préfecture si seuil proche. Un jour ordinaire = **surveillance + publication**, pas de guerre.

**2.** Ordre inversé : d’abord **seuils et trajectoire 24–48 h**, puis confiance (mesures qui montent déjà ? vent qui tourne ?), puis **arbitrage alerte / info / rien**, puis com’ (préfecture, presse, collectivités). Le polish des cartes passe après la décision.

**3.** Les trois, dans cet ordre variable : **obs de la nuit et du matin** (le réel), **expérience des sites** (« ce capteur monte toujours avant l’agglo »), **modèle** comme scénario. Le coup de fil existe encore pour les cas limites (collègue, autre AASQA, parfois Météo-France).

**4.** En premier : **série temporelle stations + carte régionale du jour**. Ensuite modèle J+0/J+1. Les dashboards « jolis » passent après. S’il n’y a qu’un écran : mesures + un champ prévu superposé.

**5.** Écart brutal modèle/mesure sur plusieurs stations ; météo prévue déjà fausse à 8 h ; panache ou inversion que le modèle lisse ; sortie qui **contredit l’épisode en cours** ; upgrade modèle récent non digéré.

**6.** Quand le modèle est **systématiquement** haut/bas sur un régime connu, ou la veille d’un seuil pour « coller » à la tendance observée. Base : climatologie locale + obs récentes + parfois consigne d’équipe — rarement une formule écrite.

**7.** Large et **assumée** : la prévision publiée est une **expertise**, pas un dump modèle. Encadrement : procédures internes, double regard les jours sensibles, guides LCSQA/préfecture, traçabilité plus ou moins réelle selon boîte.

**8.** Outils qui **arrivent trop tard**, multiplient les onglets, ne disent pas *quoi faire*, changent de biais sans prévenir, ou exigent une vérité terrain que le prévi n’a pas le temps de recalculer.

**9.** Souvent **quelques matins d’épisode** ou deux semaines calmes max. S’il n’a pas changé une décision ou réduit un doute en 3–5 utilisations réelles → tiroir.

**10.** Il est **là à l’heure**, ne casse pas, a un **repli** (brut), un collègue le jure, et il parle le langage seuil/indice — pas seulement RMSE.

**11.** Surtout **la tête** + archives d’épisodes / communiqués / parfois un tableur perso. Peu de « knowledge base » industrielle. D’où la valeur d’un carnet d’épisodes rejouable.

**12.** Pardonné : se tromper de **quelques µg** loin des seuils, rater un micro-événement local. Impardonnable : **sous-alerter un pic large déjà visible dans les mesures**, ou contredire le terrain en public sans filet.

---

## B. La décision et ses coûts (13–24)

**13.** Usure de la **confiance préfectorale et médiatique**, fatigue des mairies (mesures impopulaires), sentiment « ils crient au loup ». Coût monétaire direct souvent faible ; coût **politique et attentionnel** réel.

**14.** Bien plus grave en image : « l’AASQA n’a pas vu venir ». Risque sanitaire perçu, questions parlementaires/locales, tension avec le ministère. Un miss cuisant se raconte des années.

**15.** **Implicite.** On optimise mentalement « plutôt une FA de trop qu’un miss » *jusqu’à* un seuil de ridicule — jamais un ratio écrit unique.

**16.** **Préfecture** (ou autorité de police) pour les mesures d’urgence ; l’AASQA **informe, recommande, qualifie** l’épisode. L’automatisme pur est rare sur l’alerte « dure ».

**17.** Négociation, notes, parfois déclenchement préfectoral **plus ferme ou plus mou** que le conseil technique. L’AASQA documente son avis ; la décision administrative prime.

**18.** Oui : **crédibilité**, questions « pourquoi avoir gêné pour rien », parfois coût économique des mesures. Rarement une ligne budgétaire « erreur de prévi ».

**19.** Seuils **réglementaires / nationaux** (info vs alerte), pas inventés localement chaque matin. Contestation plutôt sur **pertinence des mesures** et communication que sur le µg exact du seuil.

**20.** Acceptable si le prévi **garde la main** et comprend le curseur. Inacceptable quand les FA deviennent la **norme hebdomadaire** en hors-épisode — le public et la préfecture décrochent. Pas de taux magique : plutôt « est-ce encore crédible ce mois-ci ? ».

**21.** Effet souvent **modeste et disputé** (surtout O₃ estival). Ça rend certains décideurs **plus hésitants** ; d’autres déclenchent pour le signal politique/sanitaire même si le gain µg est mince.

**22.** De **quelques heures** (com’, vitesse) à **J+1** pour voir un effet trafic/mesures. Trop lent pour « corriger » un pic de l’après-midi déjà engagé.

**23.** Oui, en sourdine : vacances (moins de monde, autre mix trafic), rentrée, grands événements, parfois prudence accrue si le sujet est déjà médiatisé. Pas un algorithme — un **contexte**.

**24.** Par le **dossier** : mesures, sorties modèles horodatées, procédure suivie, comparaison aux guides. La défense est procédurale autant que scientifique.

---

## C. L’institution et son écosystème (25–36)

**25.** **AASQA** : surveillance locale, prévi/indices, appui préfets, open data régional. **LCSQA** : référentiel technique, métrologie, méthodes. **INERIS** (parmi d’autres) : expertise, modélisation nationale, appui LCSQA. **Météo-France** : météo et souvent chaînes liées. **Ministère** : politique, rapportage UE, tutelle. Schéma réel plus emmêlé que l’organigramme.

**26.** Méthodes, conformité d’appareils, guides, exercices, pas chaque prévision du mardi. Latence : **mois à années** pour un guide ; pas du temps réel opérationnel.

**27.** AASQA : **densité locale**, expertise terrain, relation préfecture/collectivités, réseaux et campagnes. PREV’AIR : **couverture nationale**, horizons, produit de référence visible. Réciproque : PREV’AIR ne remplace pas le jugement local ; l’AASQA ne tient pas seule l’Europe.

**28.** Mix **État / collectivités / fiscalité air / prestations**. Contrainte : peu de CDD data longs, priorisation du **réglementaire** sur la R&D, sous-traitance ou mutualisation pour le lourd.

**29.** Rapportages, bilans, indices, épisodes, données aux formats nationaux/UE. Le plus cher : souvent **qualité de donnée + inventaires/modélisation locale + campagnes**, pas la slide jolie.

**30.** De **quelques personnes** à quelques dizaines selon région. Profils : métrologie, exploitation réseau, études/modélisation, communication, admin. Peu de « ML engineer » dédiés.

**31.** Très majoritairement **exploitation et obligations**. Le dev est l’exception ou le projet fléché — d’où la méfiance envers tout outil qui crée de la maintenance.

**32.** Manque de **temps d’intégration**, peur de la boîte noire, besoin de traçabilité, validation LCSQA perçue ou réelle, et « on a déjà PREV’AIR / notre chaîne ».

**33.** Fédération Atmo France, groupes techniques, partages d’outils (plus ou moins), pas un unique SI national unique pour la prévi fine. Mutualisation **partielle**.

**34.** Intérêt croissant, usage **complémentaire** (cartographie, pédagogie), rare en **décision réglementaire pure** tant que QA non cadrée. Ni rejet total ni adoption aveugle.

**35.** Un porte-parole, messages alignés préfecture, factuels, éviter la sur-promesse. Le prévi fournit la substance ; la com’ tient le rythme médiatique.

**36.** Indices refondus, open data, pression UE/seuils futurs, ML qui entre dans PREV’AIR/CAMS, feux et importations plus visibles, attente de **réactivité** citoyenne.

---

## D. Ce que les données ne disent pas (37–46)

**37.** « Cette station ment par vent d’ouest », chantiers, panne en cours, voisinage industriel qui tourne la nuit, fiabilité d’un modèle *cette* semaine, humeur préfectorale.

**38.** Stations en **canyon**, trop près d’un feu tricolore, abri douteux, influence parking. On le sait en interne ; les bases publiques disent « trafic » ou « fond » sans le folklore.

**39.** Audit d’implantation, comparaison aux voisines, campagne mobile. On **déplace, reclasse, ou documente la limite** — on efface rarement l’historique d’un coup.

**40.** En Occitanie comme ailleurs : zones industrielles, axes, parfois ports/airports, carrières, agriculture (NH₃, brûlages). Le modèle 8 km ne les nomme pas ; le prévi oui.

**41.** Oui : configurations **vent + saison + axe** récurrentes, « soupes » estivales connues des équipes. Peu écrites hors bilans d’épisode.

**42.** Synoptique (vent de secteur, panache sat/CAMS, absence de source locale montante), cohérence multi-stations **amont**, parfois couleur du ciel / odeurs (PM feux).

**43.** Mal et en retard : info mairie/DIR ponctuelle, pas un flux propre. D’où des NO₂ « inexplicables » une semaine.

**44.** Brûlages, feux de forêt, grands rassemblements, parfois pratiques agricoles. Trace PM/O₃ selon cas — le calendrier national ne suffit pas.

**45.** Bascule sur stations voisines, statut maintenance, parfois retard de validation. La prévi continue avec **trous** ; le discours se prudentise.

**46.** Le **jugement du jour** (pourquoi on a tranché ainsi), versions de modèle exactes, correctifs manuels, conversations préfecture. Trois ans plus tard il reste l’indice publié — souvent écrasé s’il n’est pas archivé (tu as raison de cron l’indice).

---

## E. L’Occitanie en particulier (47–56)

**47.** **Ozone estival** marqué (sud, fort ensoleillement), contrastes mer/continent/relief, importations (saharien, panaches), moins « un seul grand bassin parisien » : **plusieurs climats dans une région**.

**48.** Été : O₃ / canicule. Printemps–été : parfois PM (saharien, feux). Hiver : PM plus locales/chaauffage selon zones, NO₂ urbain. Épisodes mixtes possibles.

**49.** Méditerranée = brises, stagnations côtières ; Pyrénées / Massif = freins, foehn, contrastes altitude ; Garonne = couloir ; plaines languedociennes = photochimie large.

**50.** **Toulouse** : agglomération large, NO₂ axes, O₃ plume urbaine. **Montpellier** : littoral, brises, densités différentes, influence maritime. Même polluant, **pas la même heure ni le même levier**.

**51.** Import **ibérique / saharien** pour PM ; Rhône / flux d’est ou nord selon configs ; mer comme modulateur (brise, fumées transportées). CAMS 8 km voit l’import grossier ; le détail côtier reste local.

**52.** Oui, l’O₃ de fond rural/périurbain du sud peut être **élevé** — ce n’est pas qu’un problème de centre-ville. D’où l’indice piloté O₃ souvent hors agglo pure.

**53.** Transport routier, résidentiel, agriculture, industrie localisée, photchimie estivale (pas un « secteur » mais le moteur O₃). Le poids exact = inventaires régionaux, pas un slogan.

**54.** Couverture hétérogène montagne/littoral, mix fond/trafic, dépendance aux choix historiques d’implantation. Comme partout : **pas un grillage régulier**.

**55.** [jugement] Tenir les **épisodes** (O₃, PM feux/sable), anticipation communication, données/services numériques, préparation **seuils 2030**, parfois agriculture/pesticides/odeurs selon actualité — au-delà du seul RMSE CAMS.

**56.** [jugement + vu partiel] Bilans d’épisodes publics, open data, outils type AtmoViz / datavis, campagnes. Apprentissages typiques : **com’ d’épisode**, limites du modèle en import, besoin de réactivité feux. Pour la liste exacte des projets 2024–2026 : site ATMO + rapports d’activité — à citer en entretien **après relecture**, pas d’invention de noms de projets.

---

## F. Ce que je n’ai pas vu (57–64)

**57.** Anormal / saillant pour le métier : (a) avoir **mesuré** que le MOS public horaire **casse le max 8 h en saison O₃** et le dire sans triomphalisme — rare et utile ; (b) exclure longtemps J−1/J−2 alors que c’est le réflexe salle ; (c) un double aveugle / temporel **avoué faible** — honnête, mais un prévi demandera aussitôt le **filet** ; (d) beaucoup de RMSE, encore peu de **matins rejoués** sur *leurs* épisodes.

**58.** **Évident** dès qu’on accepte la persistance d’erreur et le trafic quotidien. +21,9 % sur NO₂ avec la veille ne surprend pas un prévi ; ce qui surprend c’est de **ne pas** l’avoir mis d’emblée. Suspect seulement si la fuite temporelle n’est pas cadrée à l’émission.

**59.** Oui : méconnaissance **caractéristique du data scientist « batch »**, pas du métier prévi. Tu l’as corrigé : tant mieux — raconte-le comme apprentissage métier, pas comme detail technique.

**60.** « **À 10 h demain, sur mon écran, qu’est-ce qui change — et quand je désactive ?** » Second couteau : « Et si CAMS upgrade la semaine prochaine ? »

**61.** Tableaux de gains sans **heure d’arrivée des entrées** ; « on bat Copernicus » même adouci ; absence de **mode dégradé** ; validation qui parle mois/plis plus que **jours d’épisode locaux** ; livrable qui ressemble à un paper plus qu’à une consigne d’astreinte.

**62.** Le geste : **s’asseoir sur une vraie matinée d’astreinte** (même rejouée) et écrire la décision publier/graduer/attendre avec *leurs* contraintes — pas seulement entraîner un modèle.

**63.** Beaucoup sous-exploitent : bulletins/épisodes ATMO en série, open data indices (si non destructif / archivé), données trafic/chantiers hétérogènes, sorties PREV’AIR publiques, météo prévue (pas réanalyse) déjà dans l’écosystème CAMS/MF. Toi : l’**archive d’indice glissant** est exactement ce genre de gisement.

**64.** « Super les %, mais **je n’ai pas tes features à l’heure H**, ton temporel flippe en été, et le produit gratuit me donne déjà un signal — **montre-moi trois jours d’Occitanie où tu m’évites une bêtise**. »

---

## G. Où va le métier (65–70)

**65.** [publié cadre] Des **seuils plus stricts** et un rapportage plus exigeant → plus de jours « mauvais », plus de pression sur prévi/com’/plans d’action, besoin de mieux quantifier les **bas niveaux** et la population exposée. Concrètement : plus de travail d’explication, pas seulement plus de modèles.

**66.** Encore **périphériques** pour la majorité des prévisionnistes AASQA (PRIORITÉ = chaîne nationale + local). Regardés par quelques profils études/innovation ; pas le quotidien de l’astreinte 2026.

**67.** Le pont **données temps réel / décision** : ingénierie d’exploitation fiable + traduction décisionnelle — plus rare que « encore un chimiste » ou « encore un dev ».

**68.** Automatisé : ingest, contrôles de seuil, premières cartes, alertes internes, rapports types. **Pas** automatisé : arbitrage d’épisode ambigu, négociation préfectorale, récit public, cas monstrueux (feux, panne réseau, modèle fou).

**69.** Savoir **quand ne pas croire le modèle** (y compris le sien) avec une latence de heures, pas de semaines — gouvernance de dérive + incertitude actionnable.

**70.** Tu n’as pas assez posé : **« Qui paie la maintenance de mon outil dans 18 mois, et quel indicateur fait qu’on le débranche ? »** — la question de survie réelle en AASQA.

---

## Fil pour ta candidature (hors numéros)

| Message métier à coller | Anti-message |
|-------------------------|--------------|
| J−2 / obs récentes = évidence d’astreinte, maintenant mesurée | « Découverte ML » |
| MOS officiel fragile sur max 8 h O₃ été = vérification d’usage | « On humilie Copernicus » |
| Filet + rejeu d’épisode > +2 pts RMSE | Course d’architectures |
| Archive indice = compétence données publiques | Encore une figure d’ablation |

**Prémisse globale à ne pas glisser :** ce questionnaire n’implique pas qu’un spontané doive *devenir* prévisionniste en 70 réponses — mais qu’il doit **parler leur coût de décision**, pas seulement leur RMSE.
