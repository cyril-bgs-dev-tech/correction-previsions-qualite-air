# Prompt ChatGPT R7 — 40 questions pour relever les notes faibles

**Intention.** Un bilan scoré a identifié où le projet est fort et où il ne l'est pas. Les
questions qui suivent ne visent **pas** à consolider ce qui va bien : elles ciblent les
quatre dimensions faibles, dans l'ordre du rendement — un point gagné sur une note à 3
vaut plus que sur une note à 9.

| Dimension | Note | Questions |
|---|---|---|
| Généralisation temporelle | **3/10** | Q1-Q11 |
| Ancrage opérationnel | **4/10** | Q12-Q22 |
| Détection d'épisodes | **6/10** | Q23-Q29 |
| Originalité | **6/10** | Q30-Q35 |
| Plafonds des dimensions fortes | 8-9/10 | Q36-Q40 |

À coller tel quel.

---

> Tu es un praticien de la data avec vingt ans de métier en prévision environnementale, et
> tu as déjà relu ce projet. Un bilan scoré vient d'identifier ses faiblesses. Je ne veux
> pas de consolidation de ce qui marche : je veux **relever les notes basses**.
>
> ## Règles de réponse
>
> 1. **Quatre colonnes obligatoires** dès qu'une action est proposée : gain attendu (chiffré
>    ou **Inconnu**), coût en heures, **test de falsification** — l'expérience la moins chère
>    qui la tue si elle est mauvaise — et **critère d'abandon**.
> 2. Étiquette **[publié]** (avec DOI) ou **[jugement]**. Un jugement assumé m'est utile ; un
>    jugement déguisé en fait me coûte cher.
> 3. **Rien au-delà d'une journée de calcul.** GPU RTX 5090 disponible, échéance 22 août 2026.
> 4. **Si une de mes prémisses est fausse, dis-le d'abord.** Je préfère perdre une question à
>    gagner une correction.
> 5. Sur les blocs marqués « créativité demandée », je veux des angles que je n'ai pas
>    envisagés — pas la liste standard.
>
> ## Le dispositif, à jour
>
> Correction apprise (LightGBM) des prévisions **CAMS Europe** (0,1°, ~8 km) **aux stations**,
> France, **17 mois** (août 2023 → décembre 2024), validation par **stations entièrement
> exclues**, cible = résidu, écrêtage à zéro. 52 variables : CAMS, météo **ERA5**, calendrier,
> 38 descripteurs de paysage, 9 de relief, trafic hiérarchisé, population.
>
> **Résultat principal** — sur la grandeur réglementaire de chaque polluant, hyperparamètres
> réglés en validation imbriquée :
>
> | Polluant | Grandeur | J+1 | J+2 | J+3 |
> |---|---|---|---|---|
> | NO₂ | max horaire | +33,2 % | +33,5 % | +34,2 % |
> | O₃ | max 8 h | +28,9 % | +29,4 % | +30,6 % |
> | PM2.5 | moyenne journalière | +30,0 % | +31,0 % | +31,9 % |
>
> Niveau comparable à Riccio & Chianese 2024 (27-30 %, stations exclues,
> doi:10.5194/acp-24-1673-2024). Deux leviers l'ont produit : apprendre la grandeur
> réglementaire **directement** (jusqu'à +6,5 points) et **augmenter la capacité** du modèle
> (jusqu'à +5,6 points).
>
> **Les faiblesses mesurées**, dans l'ordre où je veux les traiter :
>
> - **Généralisation temporelle** : gain moyen +14,4 % mais **pire pli −14,6 %**, et
>   **−24,9 %** en double aveugle (stations *et* mois cachés), sur 18 plis mensuels.
> - **Ancrage opérationnel** : aucune heure d'émission ni décision identifiée. Et surtout,
>   ma météo est **ERA5, une réanalyse** — donc indisponible en opérationnel. L'écart avec
>   une météo *prévue* n'est pas mesuré.
> - **Détection** : O₃ CSI 0,464 (au-dessus de la fourchette publiée 0,30-0,40) mais un tiers
>   des dépassements manqués ; **NO₂ inutilisable** (POD 0,084, Brier skill +0,017 sur
>   273 dépassements pour 165 990 jours-station).
> - **Originalité** : la correction apprise n'est pas nouvelle — PREV'AIR le fait déjà.
>
> **Autres mesures utiles** : corrélation **+0,913** entre dégradation de CAMS et hausse de
> mon gain à saison égale (deux ruptures documentées, 13/11 et 03/12/2024) · un débiaisage
> sans apprentissage plafonne à +7,3 % sur station inconnue · empiler covariables de terrain
> et interpolation du résidu **dégrade** (19,4 % → 16,4 %) · la typologie officielle de
> station n'apporte **rien** au-delà d'un biais global · aucune observation en 2025 · ozone
> temps réel EEA rompu en France depuis le 01/07/2025.
>
> ---
>
> ## Bloc A — Généralisation temporelle : la note la plus basse (Q1-Q11)
>
> **Q1.** *La question qui précède toutes les autres.* Mon score temporel a été mesuré sur
> l'**ancienne** configuration — cible horaire, hyperparamètres par défaut. La nouvelle
> (cible journalière, capacité triplée) n'a jamais été évaluée en double aveugle. Dans quel
> sens attends-tu que le score bouge, et pourquoi ? Une capacité plus grande devrait-elle
> aggraver l'échec temporel, ou l'agrégation journalière le réduire ?
>
> **Q2.** Comment distinguer proprement, avec mes données, la **non-stationnarité** du
> système, le **manque de données**, et le simple **effet du nombre de plis** — on voit plus
> de mauvais mois quand on en teste dix-huit que sept ?
>
> **Q3.** Un **réentraînement glissant** règle-t-il le problème ou le masque-t-il ? À quelle
> fréquence, et comment le démontrer sur 17 mois sans épuiser l'échantillon ?
>
> **Q4.** *Créativité demandée.* Et si je cessais de vouloir **empêcher** l'échec pour le
> **prédire** ? Peut-on construire un indicateur, calculable à l'émission, qui annonce que le
> modèle est hors de son domaine de validité ce jour-là — dérive de distribution des entrées,
> distance au domaine d'apprentissage, désaccord d'un ensemble ? Quelle méthode, et quel gain
> publié ?
>
> **Q5.** Dans le même esprit : un modèle qui **s'abstient** — rendant CAMS brut quand il ne
> sait pas — est-il défendable devant une AASQA, ou perçu comme un aveu ? Comment calibrer le
> taux d'abstention ?
>
> **Q6.** Les plis qui échouent ont-ils une **signature commune identifiable a priori** ?
> Comment le chercher sans tomber dans la sélection après coup, sachant que je n'ai que
> 18 mois ?
>
> **Q7.** Puis-je **borner** l'échec plutôt que l'éliminer — c'est-à-dire garantir un pire cas
> plutôt qu'un gain moyen ? Existe-t-il des approches de **prévision conforme** applicables à
> une correction de biais spatio-temporelle ?
>
> **Q8.** Mes 18 plis mensuels sont-ils le bon découpage ? Des blocs saisonniers, ou un
> découpage par **régime météo** plutôt que par calendrier, changeraient-ils le diagnostic ?
>
> **Q9.** Ma corrélation de **+0,913** entre dégradation de CAMS et hausse du gain
> contamine-t-elle aussi l'évaluation temporelle ? Autrement dit : mes plis « réussis »
> sont-ils simplement ceux où CAMS allait mal ?
>
> **Q10.** Comment **présenter** une généralisation temporelle non démontrée sans détruire le
> dossier, sachant que la spatiale, elle, est solide (σ 1,2) ? Y a-t-il un cadrage où cette
> asymétrie devient un résultat plutôt qu'un aveu ?
>
> **Q11.** Un usage **opérationnel** exige-t-il vraiment la généralisation temporelle, si le
> modèle est réentraîné chaque mois en production ? Ou est-ce que je m'impose une exigence
> académique qui ne correspond à aucun besoin réel ?
>
> ## Bloc B — Ancrage opérationnel : la faille la plus exploitable (Q12-Q22)
>
> **Q12.** *La plus urgente.* Ma météo est **ERA5**, une réanalyse. Quel écart de performance
> dois-je attendre en passant à une météo **prévue** ? Chiffre publié, si possible pour du
> post-traitement de qualité de l'air.
>
> **Q13.** Comment **mesurer** cet écart sans refaire toute la chaîne — existe-t-il un
> substitut bon marché, par exemple dégrader ERA5 en y injectant une erreur réaliste de
> prévision ?
>
> **Q14.** Quelles sources de **météo prévue** sont gratuites, couvrent la France, et sont
> disponibles à l'heure d'émission avec un historique de 17 mois exploitable ? Donne les noms,
> la latence et la profondeur d'archive.
>
> **Q15.** À quelle heure exacte les prévisions **CAMS Europe** sont-elles mises à disposition
> sur l'ADS, et cette heure est-elle garantie ou observée ?
>
> **Q16.** Quelle **décision** un prévisionniste d'AASQA prend-il réellement le matin, et à
> quelle heure ? Que regarde-t-il, dans quel ordre, et qu'est-ce qui déclenche une
> intervention humaine ?
>
> **Q17.** *Créativité demandée.* Sans accès à leur système, comment **démontrer**
> l'opérationnalité plutôt que de l'affirmer ? Quelle preuve un candidat peut-il produire
> seul — rejeu horodaté, simulation de panne, latence mesurée de bout en bout, autre ?
>
> **Q18.** Quel **contrat de service** minimal rend un tel produit crédible : latence, taux de
> disponibilité, comportement en panne d'entrée, traçabilité des versions ?
>
> **Q19.** Mon produit sort deux quantités — une concentration corrigée et une probabilité de
> dépassement. Est-ce un atout ou une complexité qui nuit à l'adoption ?
>
> **Q20.** L'ozone temps réel de l'EEA est **rompu en France depuis le 01/07/2025**. Que fait
> une AASQA dans ce cas, et cela renforce-t-il l'argument d'un modèle qui **n'utilise pas**
> d'observations récentes ?
>
> **Q21.** Comment rattacher la démonstration à un **épisode réel** ? J'en ai un : le
> **25 juillet 2026**, PM10 dans le Lot et l'Aveyron, **constaté *a posteriori*** et non
> prévu. Que puis-je en faire honnêtement sans données de ce jour-là ?
>
> **Q22.** Quelle est la **question opérationnelle** que je vais recevoir et à laquelle je n'ai
> pas de réponse préparée ?
>
> ## Bloc C — Détection d'épisodes (Q23-Q29)
>
> **Q23.** Comment monter le **POD sans faire exploser le FAR** ? Mon meilleur point donne
> POD 0,663 / FAR 0,393 sur l'ozone. Quelles approches publiées déplacent la courbe entière
> plutôt que le point de fonctionnement ?
>
> **Q24.** Le **NO₂ est-il récupérable** ? 273 dépassements du seuil horaire de 120 µg/m³ sur
> 165 990 jours-station, POD 0,084, Brier skill +0,017. Faut-il changer de seuil, de grandeur,
> agréger spatialement, ou renoncer explicitement ?
>
> **Q25.** *Créativité demandée.* Existe-t-il une formulation du problème d'épisode que je
> n'ai pas envisagée — prédire la **durée** plutôt que l'occurrence, le **rang** du jour dans
> le mois, l'**écart au seuil** plutôt que son franchissement, une survie ?
>
> **Q26.** Mon Brier skill vaut +0,460 sur O₃ et +0,017 sur NO₂. Quel seuil de Brier skill
> sépare, dans ta pratique, un modèle utilisable d'un modèle décoratif ?
>
> **Q27.** La classification et le tuning **se recouvrent** : le CSI de la régression réglée
> (0,437) approche celui de la classification (0,464). Comment mesurer l'apport **résiduel**
> de la classification sur le modèle réglé, et vaut-il encore la complexité d'un second
> modèle ?
>
> **Q28.** Sur événement rare, quel critère remplace avantageusement l'écart de CSI, que j'ai
> constaté trompeur — il déclarait concluant un NO₂ inutilisable ?
>
> **Q29.** Faut-il évaluer la détection **par station** plutôt que globalement ? Une AASQA
> alerte par zone, pas sur un agrégat national.
>
> ## Bloc D — Originalité : que reste-t-il de neuf ? (Q30-Q35)
>
> **Q30.** *Créativité demandée.* Parmi mes **résultats négatifs**, lesquels sont réellement
> nouveaux, c'est-à-dire non publiés à ma connaissance ? Je pense à trois : empiler
> covariables de terrain et krigeage du résidu **dégrade** ; la **typologie officielle** de
> station n'apporte rien au-delà d'un biais global ; apprendre directement la grandeur
> réglementaire gagne sur les **maxima** mais pas sur les **moyennes**.
>
> **Q31.** Ce dernier point — l'**asymétrie maxima/moyennes** — est-il documenté quelque part ?
> Il a une explication mécanique simple, et il conditionne le choix de cible de tout
> post-traitement réglementaire.
>
> **Q32.** Ma corrélation **+0,913** entre dégradation du forçage et gain apparent
> est-elle un phénomène **nommé** ? Elle remet en cause la lecture de tout gain de
> post-traitement mesuré sur une période où le modèle amont a changé.
>
> **Q33.** *Créativité demandée.* Quel angle **personne** ne prend dans ce domaine et qui
> serait à ma portée avec ces données ?
>
> **Q34.** Vaut-il mieux revendiquer une **contribution méthodologique** (protocole, résultats
> négatifs, honnêteté du périmètre) qu'une contribution de performance, sachant que je ne fais
> qu'atteindre l'état de l'art ?
>
> **Q35.** Y a-t-il matière à une **note courte publiable** dans ce travail ? Si oui, sur quoi,
> et dans quel format réaliste pour quelqu'un hors laboratoire ?
>
> ## Bloc E — Les plafonds des dimensions déjà fortes (Q36-Q40)
>
> **Q36.** Deux de mes seuils — la commutation Pareto à 70 µg/m³ et le point de fonctionnement
> à p ≥ 0,20 — sont **lus sur les données qui les évaluent**. Comment les choisir proprement
> sans jeu de validation supplémentaire, quand les données sont comptées ?
>
> **Q37.** Mon MQI FAIRMODE est calculé en **horaire** pour les trois polluants, alors que le
> document définit O₃ en max 8 h et PM2.5 en journalier. Le recalculer suffit-il, ou la
> mention de conformité doit-elle disparaître pour ces deux polluants ?
>
> **Q38.** Que manque-t-il à ma reproductibilité — j'ai un manifeste avec versions, empreintes
> et détection des rapports périmés — pour qu'un tiers puisse **refaire** mes chiffres sans
> moi ?
>
> **Q39.** J'**atteins** l'état de l'art sans le dépasser. Est-ce suffisant pour une
> candidature, ou faut-il un élément qui dépasse — et si oui, lequel est atteignable ?
>
> **Q40.** Si tu devais **réallouer** mes jours restants entre ces cinq blocs, quelle
> répartition, et quelle est la **seule** chose que tu ne ferais pas malgré son attrait ?
>
> ---
>
> **Format.** Un bloc par section, réponse d'abord, sources ensuite, quatre colonnes dès
> qu'une action est proposée. Termine par les points classés **Inconnu** — je les compte comme
> des réponses utiles.
