# Audit de falsification du résultat CAMS-MOS

## 1. Antériorité du phénomène

**[publié]** Oui, et plus directement que Huang et al. : Bertrand et al. ont testé le MOS CAMS et constaté qu’un maximum journalier extrait des sorties horaires réduisait la RMSE de 20,5 %, contre 32,8 % pour le même algorithme entraîné directement sur le maximum. Ils recommandent explicitement une cible journalière lorsque le maximum est l’usage visé. Leur maximum est toutefois un maximum horaire, pas la MDA8 réglementaire, et l’étude précède le produit ADS opérationnel actuel.  
**[jugement]** Le mécanisme et la recommandation ne sont donc pas nouveaux. Restent potentiellement nouveaux : la réplication sur le produit opérationnel, la MDA8, l’ampleur estivale et le POD.

**Sources :** Bertrand et al. (2023), *Atmospheric Chemistry and Physics*, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023), tableau 3 et §5 ; Petetin et al. (2022), MDA8 CAMS et compromis scores continus/catégoriels, [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022) ; Huang et al. (2017), [doi:10.1175/WAF-D-16-0118.1](https://doi.org/10.1175/WAF-D-16-0118.1).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Recentrer la revendication sur « produit opérationnel + MDA8 + saison » | Évite une revendication d’antériorité fausse | 1 h | Bertrand ou Petetin documente déjà exactement ces trois éléments | Abandonner toute revendication de nouveauté si une telle source est trouvée |

## 2. Équité de la comparaison

**[publié]** Comparer le MOS horaire agrégé à un modèle directement entraîné sur la MDA8 répond à une question d’usage, mais ne permet pas d’attribuer l’écart à la seule cible : algorithme, variables, historique et information disponible diffèrent. Bertrand et al. isolent mieux l’effet en gardant le même algorithme et en changeant la cible.  
**[jugement]** La comparaison CAMS brut–MOS officiel sur les mêmes lignes est équitable pour évaluer le produit. La comparaison MOS officiel–« notre modèle » ne l’est pas encore comme duel opérationnel, surtout si le vôtre utilise ERA5 ou des observations d’autres stations aux mêmes dates valides.

**Sources :** Bertrand et al. (2023), expérience cible horaire/cible journalière, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; documentation CAMS-MOS, entrées IFS prévues et observations de la veille, [ECMWF](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Faire un 2×2 : même LightGBM, cible horaire ou MDA8, mêmes données et mêmes plis temporels | Attribution causale de l’écart à la cible | 6–8 h | L’écart disparaît à données et modèle constants | Ne plus attribuer le résultat à la cible si ΔRMSE < 1 point ou IC recouvre largement 0 |

## 3. Pourquoi optimiser l’horaire

**[publié]** Le produit vise des séries de stations de 0 à 96 h, et ses usages comprennent les profils horaires, le biais, la corrélation et les seuils horaires ; NO₂ possède en outre une norme horaire. Un seul produit horaire permet ensuite de calculer plusieurs résumés. CAMS a aussi retenu une architecture globale réentraînée chaque jour sur trois jours pour absorber rapidement les changements opérationnels.  
**[jugement]** C’est une raison légitime d’optimiser l’horaire, pas une preuve que l’agrégation MDA8 est optimale.

**Sources :** [documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; Bertrand et al. (2023), compromis opérationnel, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Présenter le résultat comme une incompatibilité d’objectifs, non comme une erreur de CAMS | Crédibilité institutionnelle | 1 h | CAMS déclare la MDA8 comme objectif principal de ce produit | Retirer cette lecture si le cahier des charges impose explicitement d’optimiser la MDA8 |

## 4. Évaluation publique du MOS

**[publié]** Oui. Le serveur EQC compare le MOS aux observations et à l’ENSEMBLE, par saison et échéance ; il propose explicitement l’espèce « ozone MDA8 » et des scores horaires, journaliers ou mensuels. Le rapport méthodologique 2025 dit aussi que l’évaluation cherche les variations saisonnières et les paramètres pour lesquels l’optimisation échoue.  
**[jugement]** Le constat n’est donc pas inédit par son objet. **Inconnu** : les pages publiques affichent-elles déjà exactement vos RMSE françaises mensuelles et votre seuil de POD, avec le même échantillon ?

**Sources :** CAMS EQC, rapport méthodologique 2025, pp. 22–33, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf) ; [page EQC CAMS](https://confluence.ecmwf.int/spaces/CKB/pages/601307378/Evaluation%2Band%2BQuality%2BControl%2BEQC%2Bof%2BCAMS%2BEuropean%2Bproducts).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Exporter/capturer le panneau EQC France–O₃ MDA8–2024 et réconcilier ses filtres | Détermine la redondance réelle | 2 h | Les chiffres et la conclusion saisonnière y sont déjà publiés | Abandonner l’angle « découverte » si la reproduction est exacte |

## 5. Conformité de la MDA8

**[publié]** La MDA8 est le maximum des moyennes glissantes de huit heures, recalculées chaque heure ; chaque fenêtre appartient au jour où elle se termine. La première va de 17 h la veille à 1 h et la dernière de 16 h à 24 h. Une moyenne 8 h exige 6 valeurs horaires sur 8 et une MDA8 journalière 18 fenêtres valides sur 24.  
**[jugement]** Il faut travailler en heure civile réglementaire, gérer CET/CEST explicitement et charger les sept heures du jour précédent. Un calcul limité aux 24 pas du jour est non conforme.

**Sources :** directive 2008/50/CE, annexes I.A et VII, [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32008L0050) ; version consolidée, règles de complétude, [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02008L0050-20150918).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Ajouter un test unitaire avec changement d’heure, 31 h consécutives et fenêtres 6/8–18/24 | Élimine un artefact potentiellement fatal | 3 h | Les résultats mensuels changent fortement après correction | Abandonner les chiffres actuels si ΔRMSE > 0,2 µg/m³ ou signe mensuel inversé |

## 6. Le modèle a vu 2024

**[jugement]** Oui, cela peut expliquer 2,4 µg/m³, mais aucune amplitude publiée transférable ne permet de la quantifier : **Inconnu**. Exclure des stations n’empêche pas une fuite temporelle si l’entraînement utilise les observations d’autres stations aux mêmes dates — voire des dates futures — ni une avance d’information si ERA5 remplace la météo disponible à l’émission.  
**[publié]** Petetin et al. distinguent explicitement météo prévue et ERA5 et emploient une validation à origine glissante ; CAMS-MOS n’utilise que prévisions IFS et observations antérieures.

**Sources :** Petetin et al. (2022), protocole et sensibilité HRES/ERA5, [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022) ; [documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Geler au 31-12-2024, tester 2025 et remplacer toute variable indisponible à l’émission | Mesure l’optimisme opérationnel | 4–8 h hors téléchargement | L’avantage sur MOS tombe à zéro | Ne plus publier « notre modèle > MOS » si IC de ΔRMSE inclut 0 |

## 7. Taille et test apparié

**[publié]** 73 108 lignes ne sont pas 73 108 réplications indépendantes. Les pertes sont corrélées par station et par date ; l’inférence multi-clusters traite précisément ces deux dimensions non emboîtées. Le test de Diebold–Mariano compare des pertes appariées avec autocorrélation temporelle, mais ne résout pas seul la dépendance spatiale.  
**[jugement]** L’effectif paraît largement suffisant pour estimer une RMSE ; la largeur de l’IC, non le nombre brut, tranche.

**Sources :** Cameron, Gelbach & Miller (2011), [doi:10.1198/jbes.2010.07136](https://doi.org/10.1198/jbes.2010.07136) ; Diebold & Mariano (1995), [doi:10.1080/07350015.1995.10524599](https://doi.org/10.1080/07350015.1995.10524599).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Bootstrap apparié à deux voies station × blocs de dates, en recalculant les deux RMSE | IC défendable | 3–5 h | IC95 % du gain MOS–brut contient 0 | Abandonner « améliore/dégrade » et écrire « indiscernable » |

## 8. Différence d’échantillon

**[publié]** Le MOS n’est produit que pour les stations de fond satisfaisant 75 % de disponibilité sur ses trois jours d’apprentissage ; la liste varie selon date et espèce. L’EQC limite donc aussi l’ENSEMBLE aux sites où le MOS existe et avertit que son score brut diffère d’autres évaluations.  
**[jugement]** Sur l’intersection exacte observation–brut–MOS, le contraste brut/MOS est apparié et valide pour ce sous-échantillon. Il ne prouve pas la performance nationale ni la disponibilité du service.

**Sources :** [documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; CAMS EQC 2025, §4.6, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Publier un diagramme de flux et comparer stations-jours incluses/exclues par mois, pays et niveau observé | Écarte la sélection favorable | 2–3 h | Les absences se concentrent sur les pics ou certains types de stations | Restreindre strictement la conclusion à l’échantillon complet si déséquilibre > 10 points |

## 9. Piège d’échéance

**[publié]** CAMS-MOS fournit les pas 0–96 h et est calculé vers 06:30 UTC. « 24–47 h » décrit un intervalle UTC relatif au run, pas nécessairement le jour civil local J+1. La MDA8 du jour D requiert aussi sept heures de D−1.  
**[jugement]** C’est un risque fatal : il faut indexer par heure valide, convertir Europe/Paris avec CET/CEST, puis construire le jour réglementaire. Le « décalage 0 h optimal » ne prouve pas cette équivalence.

**Sources :** [documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; directive 2008/50/CE, annexe VII, [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32008L0050).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Refaire l’appariement par `valid_time` local et fenêtres traversant minuit | Vérifie l’échéance réelle | 3–5 h | Le signe avril–septembre disparaît | Abandonner le résultat actuel si plus de 1 % des heures changent de jour à tort |

## 10. Pari avant vérification

**[jugement]** Je parie que le constat qualitatif « un MOS horaire est moins efficace sur les maxima qu’à l’heure » survivra : il est déjà publié par l’équipe CAMS. Je parie aussi que les chiffres exacts seront révisés, car « année 2024 complète » est faux pour un jeu disponible seulement depuis le 17 janvier, et les pièges MDA8/J+1 sont substantiels. La supériorité de votre modèle est la partie la plus fragile à cause de l’information temporelle non comparable.

**Sources :** catalogue ADS, couverture à partir du 17 janvier 2024 et DOI du jeu [10.24381/2cce4067](https://doi.org/10.24381/2cce4067) ; Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Geler toute valorisation jusqu’aux audits date–heure–échantillon–2025 | Évite une affirmation publiquement fausse | 0,5 h | Les quatre audits passent sans correction matérielle | Abandonner l’axe central si deux audits changent le signe saisonnier ou l’avantage propre |

## 11. Test minimal incontestable

**[jugement]** Le minimum n’est pas une nouvelle architecture : (i) intersection identique brut/MOS/observations, (ii) MDA8 réglementaire en heure locale, (iii) France 17 janvier–31 décembre 2024, (iv) reproduction indépendante sur 2025 gelé ou sur l’Espagne, (v) IC multi-clusters. Il établit le produit et le phénomène, pas la cause.  
**[publié]** L’Espagne est déjà un domaine CAMS-MOS/MDA8 étudié, ce qui offre un comparateur publié.

**Sources :** Petetin et al. (2022), péninsule Ibérique, [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022) ; Cameron et al. (2011), [doi:10.1198/jbes.2010.07136](https://doi.org/10.1198/jbes.2010.07136).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Exécuter ce paquet minimal reproductible | Passe de constat exploratoire à résultat robuste | 8 h | Pas de dégradation estivale hors France-2024 | Abandonner la généralisation ; conserver seulement « France 2024 » |

## 12. Pays voisin

**[jugement]** Oui : l’Espagne est le meilleur test adverse, car elle augmente le nombre de situations estivales à ozone élevé et prolonge directement le domaine de Petetin et al. La Belgique ou l’Allemagne donneraient plus de contraste climatique, mais répondraient moins directement au mécanisme estival.  
**[publié]** Petetin et al. ont évalué CAMS sur Espagne–Portugal, de l’heure à la MDA8 et de J+1 à J+4.

**Sources :** Petetin et al. (2022), [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Répliquer 2024 en Espagne avec le code inchangé | Forte validité externe pour faible effort | 4–6 h hors acquisition | MOS ne dégrade aucun mois chaud et conserve son POD | Abandonner le mécanisme général si l’effet français n’est pas reproduit |

## 13. Isoler cible et modèle

**[publié]** Bertrand et al. fournissent le dessin approprié : même famille de modèle, mêmes prédicteurs, mêmes périodes, mais cibles horaire et maximum distinctes ; ils comparent ensuite le maximum agrégé du premier au maximum prévu par le second.  
**[jugement]** Ajoutez un contrôle « horaire direct sans variables de terrain » : le 2×2 cible × covariables sépare contribution de la cible et richesse spatiale.

**Sources :** Bertrand et al. (2023), tableaux 2–3, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Factoriel cible horaire/MDA8 × variables CAMS seules/toutes variables | Quantifie les deux contributions | 6–8 h | Interaction instable entre plis ou saisons | Ne pas annoncer un effet propre si IC de l’effet principal recouvre 0 |

## 14. Intervalle de confiance

**[jugement]** Publiez l’IC95 % de la **différence appariée de RMSE**, en recalculant les RMSE à chaque réplication ; ne soustrayez pas deux IC séparés. Utilisez un bootstrap multiway station × blocs calendaires de 7 jours, puis une sensibilité 3/14 jours. Un DM sur la série quotidienne de perte nationale peut servir de contrôle, pas de résultat unique.  
**[publié]** L’inférence multi-clusters est conçue pour deux dépendances non emboîtées.

**Sources :** Cameron et al. (2011), [doi:10.1198/jbes.2010.07136](https://doi.org/10.1198/jbes.2010.07136) ; Diebold & Mariano (1995), [doi:10.1080/07350015.1995.10524599](https://doi.org/10.1080/07350015.1995.10524599).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Produire 2 000 réplications appariées multiway et trois longueurs de bloc | Incertitude robuste | 3–6 h | Conclusions changent avec la longueur de bloc | Écrire « non concluant » si un IC95 % raisonnable inclut 0 |

## 15. Mois ou année

**[jugement]** L’agrégat annuel masque précisément le résultat : publiez les mois avec IC et effectifs, plus deux saisons définies a priori (avril–septembre, octobre–février). Évitez douze tests isolés non corrigés ; l’objet principal doit être une interaction produit × saison.  
**[publié]** CAMS EQC évalue lui-même le MOS par saison et demande si les performances varient saisonnièrement.

**Sources :** CAMS EQC 2025, §4.6, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Estimer l’interaction saison × produit, mois en graphique secondaire | Rend l’inversion testable sans p-hacking | 2 h | Interaction non significative et instable en 2025 | Abandonner « saisonnier » si signe non reproduit |

## 16. Stations sans MOS

**[publié]** L’absence fait partie de la conception : fond seulement, 75 % de données récentes, sites variables. On ne peut pas imputer honnêtement une prévision MOS inexistante pour comparer les erreurs.  
**[jugement]** Il faut séparer deux estimands : performance conditionnelle quand le MOS existe et couverture opérationnelle. Pour généraliser, comparez les caractéristiques et erreurs CAMS brut des cas inclus/exclus ; une pondération de sensibilité est possible, mais pas une « RMSE MOS nationale » observée.

**Sources :** [documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; CAMS EQC 2025, §4.6, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Rapporter couverture et modèle logistique de présence sans imputer MOS | Délimite la population cible | 2–4 h | Présence fortement prédite par pollution ou saison | Interdire toute formulation « France entière » si AUC de présence > 0,70 |

## 17. Métrique complémentaire

**[jugement]** La plus décisive pour le mécanisme est le ratio d’écart-type temporel MOS/observation, accompagné du biais de MDA8. Pour l’usage, ajoutez CSI et FAR au POD, car un POD seul s’augmente trivialement en alertant toujours. Une courbe quantile–quantile des MDA8 montre directement la compression de la queue.  
**[publié]** Petetin et al. insistent sur le compromis entre scores continus et catégoriels ; CAMS EQC publie RMSE, biais et corrélations.

**Sources :** Petetin et al. (2022), [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022) ; CAMS EQC 2025, §2, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Ajouter ratio de variance, QQ-plot et CSI/FAR avec IC | Relie mécanisme et conséquence | 2–3 h | Variance non réduite ou POD compensé par FAR bien meilleur | Abandonner « écrasement » si σMOS/σobs ≥ σbrut/σobs |

## 18. Autres échéances

**[publié]** Oui : le produit couvre 0–96 h et l’EQC pose explicitement la question de l’efficacité selon l’horizon. Petetin et al. ont étudié J+1 à J+4.  
**[jugement]** Tester 48–71 et 72–95 h coûte peu et distingue un effet structurel d’un accident J+1. Il faut toutefois construire les jours par heure valide locale, pas copier des tranches UTC.

**Sources :** [documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; Petetin et al. (2022), [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Calculer J+2/J+3 avec la même chaîne réglementaire | Généralité par horizon | 2–4 h | Effet sans ordre ni reproduction saisonnière | Limiter la conclusion à J+1 si deux horizons contredisent |

## 19. Vers une recommandation AASQA

**[publié]** PREV’AIR entraîne déjà directement des indicateurs de maximum et moyenne journaliers, puis les spatialise ; son rapport évalue RMSE, biais, corrélation et tables de contingence par échéance.  
**[jugement]** La recommandation utile est donc : « vérifier chaque cible décisionnelle à son échelle et maintenir un post-traitement dédié si le MOS horaire échoue », avec déclenchement fondé sur POD/FAR/CSI et disponibilité. Une seule année O₃ ne suffit pas à imposer une méthode.

**Sources :** rapport LCSQA *Performances PREV’AIR 2023*, annexe 1 et chap. 2, [PDF](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf) ; [PREV’AIR, prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Produire une fiche décisionnelle O₃ : cible, horizon, coût des ratés, scores et couverture | Traduction opérationnelle | 3 h | L’AASQA n’utilise pas cette cible/horizon pour ses décisions | Abandonner la recommandation si aucun processus métier correspondant n’est identifié |

## 20. Expérience mécanistique minimale

**[jugement]** Sur un jeu d’apprentissage séparé, appliquez au MOS horaire une transformation affine mensuelle qui conserve sa moyenne mais restaure son écart-type observé, puis recalculez la MDA8. Si la MDA8 estivale et le POD remontent sans changement des rangs horaires, la compression est causalement impliquée ; si seul le recentrage du biais agit, l’explication doit devenir « biais + variance ».  
**[publié]** L’inflation pure peut fabriquer de la variabilité non prévisible et n’est pas une solution générale.

**Sources :** von Storch (1999), critique de l’inflation, [doi:10.1175/1520-0442(1999)012%3C3505:OTUOII%3E2.0.CO;2](https://doi.org/10.1175/1520-0442(1999)012%3C3505:OTUOII%3E2.0.CO;2).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Décomposition 2×2 : recentrage oui/non × remise à l’échelle oui/non | Identifie biais versus variance | 3–4 h | La variance restaurée n’améliore pas MDA8/POD | Abandonner « écrasement de variabilité » si effet < 10 % de l’écart MOS–brut |

## 21. Prédictions avant test

**[jugement]** O₃ MDA8 : dégradation probable en été, déjà observée. NO₂ maximum horaire : compression probable, mais le biais local et la persistance peuvent dominer ; je prédis un dommage plus hétérogène, urbain et hivernal — confiance faible. PM10/PM2.5 moyenne journalière : amélioration plus probable, car la moyenne est linéaire et bénéficie de la réduction du bruit.  
**[publié]** Bertrand et al. trouvent justement les moyennes agrégées depuis l’horaire comparables aux modèles dédiés, mais les maxima significativement moins bons.

**Sources :** Bertrand et al. (2023), tableau 3, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Horodater ces prédictions puis tester trois polluants sans retouche | Test réellement prédictif du mécanisme | 4–6 h | PM moyennes dégradées et NO₂ maximum amélioré uniformément | Abandonner l’explication universelle si deux prédictions sur trois échouent |

## 22. Moyenne contre maximum

**[publié]** Oui. L’espérance et la moyenne temporelle commutent, alors que le maximum est convexe et non linéaire. Empiriquement, Bertrand et al. trouvent que les moyennes journalières tirées du MOS horaire restent comparables aux modèles entraînés directement, contrairement aux maxima.  
**[jugement]** La phrase « toutes les grandeurs réglementaires sont des maxima » est fausse : PM10 et PM2.5 utilisent notamment des moyennes journalières ou annuelles.

**Sources :** Bertrand et al. (2023), tableau 3, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; directive (UE) 2024/2881, annexe I, [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2024/2881/oj).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Corriger cette phrase et montrer moyenne/max sur les mêmes séries | Évite une erreur réglementaire nette | 1–2 h | Moyenne et maximum réagissent identiquement | Ne plus invoquer la non-linéarité si leurs écarts sont indiscernables |

## 23. Effet de l’échéance

**[jugement]** Je prédis un écart d’agrégation croissant avec l’horizon : la persistance de l’observation de la veille perd de l’information et le point forecast régresse davantage vers une valeur centrale. Mais la RMSE brute augmente aussi ; le gain relatif MOS peut donc augmenter même si les extrêmes se tassent. **Inconnu** : aucune loi quantitative publiée ne permet de fixer la pente pour ce produit.

**Sources :** CAMS-MOS utilise les observations de la veille et couvre 0–96 h, [documentation](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; Petetin et al. (2022), J+1–J+4, [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Régression interaction horizon × saison sur pertes appariées | Quantifie la tendance | 2–3 h | Pente incohérente et IC recouvrant 0 | Ne pas annoncer d’aggravation si non monotone sur J+1–J+3 |

## 24. Autres produits opérationnels

**[publié]** PREV’AIR est un cas français directement testable ; en Amérique du Nord, Huang et al. ont documenté une correction analogique opérationnelle du NAQFC et sa réduction de variabilité. Petetin et al. offrent un autre banc CAMS sur la péninsule Ibérique, mais pas un produit distinct.  
**[jugement]** Pour l’échéance du dossier, PREV’AIR est le meilleur prolongement : pertinent pour l’AASQA et documenté, sous réserve d’accès aux séries corrigées/brutes appariées.

**Sources :** Huang et al. (2017), [doi:10.1175/WAF-D-16-0118.1](https://doi.org/10.1175/WAF-D-16-0118.1) ; [PREV’AIR](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees) ; rapport LCSQA [PDF](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Vérifier la disponibilité de séries PREV’AIR brutes/corrigées aux stations | Extension institutionnellement forte | 1–2 h | Pas d’archive appariable accessible | Abandonner l’extension si acquisition > 4 h ou nécessite une convention |

## 25. Pas de temps de PREV’AIR

**[publié]** Le rapport LCSQA 2023 indique que l’adaptation statistique historique entraîne directement seulement le maximum et la moyenne journaliers, par régression multilinéaire, puis krigeage avec CHIMERE en dérive externe. Le site PREV’AIR indique aujourd’hui que des cartes corrigées peuvent être journalières ou horaires, sans documenter sur cette page l’algorithme horaire.  
**[jugement]** Pour le mécanisme qui vous intéresse, PREV’AIR a donc déjà adopté la cible journalière. La nature exacte du produit horaire actuel est **Inconnu** sans documentation de version plus précise.

**Sources :** LCSQA, *Performances PREV’AIR 2023*, annexe 1 pp. 57–58, [PDF](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf) ; [PREV’AIR, prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Poser au LCSQA une question fermée : cible et agrégation du produit horaire en production 2026 | Ferme une ambiguïté importante | 0,5 h | Documentation publique répond déjà précisément | Classer Inconnu si aucune réponse avant le dossier |

## 26. Effet sur les cartes

**[publié]** CAMS-MOS n’est pas une carte : ce sont des séries à des stations sélectionnées, et l’EQC désactive donc la fonction cartographique pour ce produit. PREV’AIR, à l’inverse, spatialise ses estimations aux stations par krigeage avec CHIMERE en dérive externe.  
**[jugement]** Le défaut n’affecte pas les cartes CAMS brutes tant que le MOS n’y est pas réinjecté. Il se transmettrait à toute carte construite par interpolation de maxima sous-estimés, sans que le krigeage puisse recréer les pics temporels perdus.

**Sources :** CAMS EQC 2025, §4.6, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf) ; LCSQA, annexe PREV’AIR, [PDF](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Tracer une carte de différence MDA8 uniquement sur les stations, sans surface interpolée | Montre la structure spatiale sans fausse précision | 2 h | Aucun motif spatial stable | Ne pas conclure aux cartes si variogramme ou regroupement spatial absent |

## 27. Autres statistiques d’ordre

**[jugement]** Sont exposés : maximum 1 h, MDA8, quantiles élevés, rang du jour, nombre et durée des dépassements, maximum saisonnier et AOT40, qui contient un seuillage positif. Les moyennes et sommes linéaires sans seuil sont beaucoup moins sensibles à la compression, hors biais.  
**[publié]** Petetin et al. évaluent heure, moyenne, maximum 1 h, MDA8 et dépassements, précisément parce que les classements changent selon la statistique.

**Sources :** Petetin et al. (2022), [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022) ; directive 2008/50/CE, définitions AOT40 et MDA8, [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32008L0050).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Calculer quantiles 90/95/99 et nombres de dépassements avant toute nouvelle cible | Cartographie rapide de la non-linéarité | 2–3 h | Aucun tassement relatif au-dessus de P90 | Limiter le constat à la seule MDA8 si les autres statistiques sont stables |

## 28. AOT40 et végétation

**[publié]** L’AOT40 somme, durant une plage et une saison définies, les excès horaires d’O₃ au-dessus de 40 ppb ; le seuillage rend l’indicateur non linéaire. La directive 2008/50 utilise 8:00–20:00 CET et mai–juillet pour la protection de la végétation.  
**[jugement]** Une compression près du seuil peut donc supprimer de nombreuses contributions et produire une erreur cumulée importante. « Encore plus touché » reste **Inconnu** : le signe dépend aussi du biais moyen et du nombre d’heures proches du seuil.

**Sources :** directive 2008/50/CE, annexes I et VII, [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32008L0050).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Calculer AOT40 CAMS brut/MOS/observé sur les stations rurales admissibles | Extension réglementaire forte | 3–4 h | MOS améliore l’AOT40 malgré la compression | Abandonner « plus touché » si erreur absolue MOS ≤ brute |

## 29. Classes d’indice

**[publié]** L’indice ATMO agrège des sous-indices construits à partir de concentrations journalières : maximum journalier des moyennes glissantes 8 h pour O₃, maximum horaire pour NO₂ et moyennes journalières pour PM10/PM2.5.  
**[jugement]** La compression peut faire franchir vers le bas une frontière de classe, surtout pour O₃/NO₂. L’effet réel doit être mesuré par matrice de confusion et rappel des classes élevées, pas déduit de la seule RMSE.

**Sources :** arrêté du 10 juillet 2020 relatif à l’indice de la qualité de l’air ambiant, annexes, [Légifrance](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042119934).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Recalculer les sous-indices et l’indice final sur les cas appariés | Lien direct avec le projet candidat | 3–5 h | Taux de classe et rappel « Mauvais+ » inchangés | Abandonner l’impact public si Δrappel < 0,02 et kappa inchangé |

## 30. Usage où le coût est maximal

**[publié]** Pour l’ozone, le seuil d’information européen est défini sur une heure ; la MDA8 sert à la valeur cible de santé et l’AOT40 à la végétation. Les dispositifs français d’épisode combinent concentrations prévues et critères territoriaux.  
**[jugement]** À court terme, le coût décisionnel le plus grave est un épisode élevé manqué : le coût d’un faux négatif est asymétrique. Pour votre résultat MDA8, l’impact le plus directement démontré est cependant la mauvaise classe/évaluation journalière, pas encore le déclenchement réglementaire français complet.

**Sources :** directive 2008/50/CE, annexe XII, [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32008L0050) ; arrêté du 7 avril 2016, [Légifrance](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376954).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Évaluer les décisions avec seuils exacts et une fonction de coût faux négatif/faux positif | Passe du score au risque métier | 3–4 h | Aucun jour décisionnel ne change | Ne pas invoquer l’alerte si zéro décision est affectée |

## 31. Formalisation correcte

**[jugement]** L’inégalité proposée est inversée. Pour un vecteur aléatoire \(Y\) conditionné par \(X\), le maximum est convexe :
\[
\mathbb E[\max_t Y_t\mid X]\ \ge\ \max_t\mathbb E[Y_t\mid X].
\]
Un prédicteur horaire MSE approche chaque moyenne conditionnelle \(\mathbb E[Y_t\mid X]\). Prendre ensuite son maximum donne le membre de droite, inférieur à l’espérance du véritable maximum lorsque subsiste une variabilité conditionnelle. Ce « Jensen gap » explique le tassement ; \(\mathbb E[\max f(X)]<\max \mathbb E[f(X)]\) n’est pas la bonne écriture.

**Sources :** le constat empirique correspondant chez CAMS est publié par Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023). La première inégalité est une conséquence directe de Jensen.

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Remplacer l’inégalité dans tous les documents et ajouter une simulation gaussienne de 24 heures | Évite une erreur mathématique fatale | 1–2 h | La simulation ne reproduit pas le gap avec variance résiduelle | Abandonner cette formalisation si la cible du modèle n’est pas une moyenne conditionnelle |

## 32. Perte quadratique ou cible horaire

**[jugement]** La MSE fixe la statistique apprise — la moyenne conditionnelle — et favorise donc la régression vers le centre. Mais le défaut structurel vient de l’incompatibilité entre une cible heure par heure et la fonction maximum. Une MAE horaire apprendrait des médianes et ne résoudrait pas le maximum ; une autre perte peut atténuer les pics sans rendre l’agrégation cohérente.  
**[publié]** Bertrand et al. améliorent le maximum en changeant directement la cible, à algorithme comparable.

**Sources :** Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Comparer MSE/MAE/pondérée sur cible horaire, puis cible MDA8 à MSE | Sépare perte et cible | 5–8 h | La perte horaire récupère tout le gain de la cible directe | Attribuer à la perte si elle explique > 80 % de l’écart |

## 33. Post-traitement quantile horaire

**[publié]** Des quantiles horaires calibrent les marginales, pas le maximum de la trajectoire : celui-ci dépend de la dépendance entre heures. Les méthodes multivariées de type ensemble copula coupling restaurent une structure temporelle après calibration marginale.  
**[jugement]** Choisir arbitrairement un quantile élevé par heure pourrait relever les pics, mais ne produirait ni une MDA8 calibrée ni une trajectoire cohérente. Une prévision probabiliste de trajectoires, ou un modèle direct de MDA8, est nécessaire.

**Sources :** Schefzik, Thorarinsdottir & Gneiting (2013), [doi:10.1214/13-STS443](https://doi.org/10.1214/13-STS443) ; Wilks (2017), calibration multivariée, [doi:10.1002/qj.2906](https://doi.org/10.1002/qj.2906).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Tester trois quantiles horaires avec réordonnancement par rang CAMS brut | Vérifie une solution légère | 6–8 h | MDA8 non calibrée ou RMSE horaire nettement dégradée | Abandonner si gain MDA8 < 2 points ou perte horaire > 1 point |

## 34. Inversion hivernale

**[jugement]** Le rapport biais/variance est l’hypothèse la plus parcimonieuse : en hiver, une forte correction du biais brut peut dominer la perte d’amplitude ; en été, un biais MOS négatif et la compression s’additionnent. Ce n’est pas démontré par les RMSE seules.  
**[publié]** Bertrand et al. montrent que la baisse de RMSE du MOS s’accompagne d’une forte correction du biais, et CAMS EQC demande explicitement une analyse saisonnière.

**Sources :** Bertrand et al. (2023), §4, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; CAMS EQC 2025, §4.6, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Décomposer mensuellement MSE = biais² + variance + covariance d’erreur | Explique l’inversion | 2–3 h | Le changement vient uniquement de corrélation/timing | Abandonner « biais/variance » si ces termes n’expliquent pas la bascule |

## 35. Chute du POD

**[jugement]** Une compression peut produire une forte chute si beaucoup de prévisions brutes se trouvent juste au-dessus du seuil. Mais un biais MDA8 estival de −6,76 µg/m³ suffit aussi à déplacer massivement les cas proches : le POD ne permet pas d’isoler les deux. Il faut vérifier seuil, effectifs de hits et distribution des marges au seuil.  
**[publié]** Petetin et al. montrent que le meilleur RMSE peut coexister avec une mauvaise détection des pics.

**Sources :** Petetin et al. (2022), [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022) ; Bertrand et al. (2023), §4–5, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Recalculer POD après correction du seul biais, puis de la seule variance | Attribution du raté catégoriel | 2 h | POD reste ≈ 0,122 après les deux | Chercher erreur de timing/seuil si récupération < 20 % |

## 36. Correction de variance a posteriori

**[publié]** Des transformations de distribution et réordonnancements existent : correction affine, quantile mapping et copules empiriques. Les méthodes de copule réinjectent une dépendance temporelle provenant d’un gabarit brut ou historique.  
**[jugement]** Une correction affine mensuelle peut restaurer moyenne et variance, mais pas l’heure correcte du pic. Un quantile mapping station–mois–horizon, appris hors test, est plus flexible ; aucun ne garantit la MDA8 sans validation dédiée.

**Sources :** Schefzik et al. (2013), [doi:10.1214/13-STS443](https://doi.org/10.1214/13-STS443) ; Lakatos et al. (2023), post-traitement temporel multivarié, [doi:10.1002/qj.4436](https://doi.org/10.1002/qj.4436).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Comparer affine et quantile mapping appris sur saison précédente | Correctif sans réentraînement CAMS | 4–6 h | Gain hors échantillon nul ou POD/FAR empire | Abandonner si gain MDA8 < 2 points |

## 37. Inflation de variance

**[publié]** Non, ce n’est pas une réponse standard sûre. Von Storch montre que l’inflation suppose à tort que toute variabilité locale est prédictible depuis le signal de grande échelle et recommande plutôt une composante aléatoire lorsque cette hypothèse échoue.  
**[jugement]** Pour CAMS-MOS déterministe, gonfler les anomalies peut améliorer les maxima mais dégrader l’heure, le biais et les faux positifs. Gains publiés transférables à l’O₃ CAMS-MOS actuel : **Inconnu**.

**Sources :** von Storch (1999), *Journal of Climate*, [doi:10.1175/1520-0442(1999)012%3C3505:OTUOII%3E2.0.CO;2](https://doi.org/10.1175/1520-0442(1999)012%3C3505:OTUOII%3E2.0.CO;2).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Tester l’inflation seulement comme expérience mécanistique, jamais comme solution annoncée | Confirme ou infirme la causalité | 2–3 h | POD monte uniquement avec explosion du FAR | Abandonner comme correction si CSI ne progresse pas |

## 38. Prédire l’ampleur

**[jugement]** Sous une approximation gaussienne, l’écart du maximum dépend du biais, de l’écart-type résiduel et du nombre effectif d’heures indépendantes, lui-même lié à l’autocorrélation. Une approximation utile est \(\Delta\max \approx \Delta\mu + k(n_{\rm eff})\Delta\sigma\), à ajuster par station-mois. Elle est diagnostique, non réglementaire.  
**[publié]** Une procédure publiée compare les distributions de MDA8 et utilise le bootstrap pour l’incertitude des percentiles.

**Sources :** Hogrefe et al. (2008), [doi:10.1016/j.atmosenv.2008.02.046](https://doi.org/10.1016/j.atmosenv.2008.02.046).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Régresser la perte de MDA8 mensuelle sur Δbiais, Δécart-type et \(n_{\rm eff}\) | Modèle explicatif compact | 3–4 h | R² hors mois < 0,3 ou signes instables | Abandonner toute prétention prédictive si validation leave-one-month-out échoue |

## 39. Calibration probabiliste

**[publié]** Oui. Des prévisions horaires marginalement calibrées peuvent être mal calibrées comme trajectoire si leur dépendance temporelle est fausse ; les maxima et cumuls dépendent de cette loi jointe. Les copules empiriques/ECC ont été développées pour conserver ou restaurer ces dépendances.  
**[jugement]** Votre problème déterministe est la projection ponctuelle du même défaut : calibrer chaque heure ne garantit pas une grandeur non linéaire du jour.

**Sources :** Schefzik et al. (2013), [doi:10.1214/13-STS443](https://doi.org/10.1214/13-STS443) ; Wilks (2017), [doi:10.1002/qj.2906](https://doi.org/10.1002/qj.2906).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Ajouter un schéma conceptuel marginales horaires → dépendance → MDA8 | Clarifie le mécanisme | 1 h | Aucun résultat probabiliste n’est présenté ou envisagé | Retirer ce détour s’il surcharge la candidature |

## 40. Nom météorologique

**[jugement]** Les termes les plus justes sont « damping of variability », « regression toward the mean/climatology », « loss of temporal dependence » et « temporal aggregation inconsistency ». « Underdispersion » convient mieux à une distribution ou un ensemble qu’à une unique série déterministe ; « double penalty » désigne un autre problème spatial.  
**[publié]** Huang et al. parlent de réduction de variabilité ; la littérature probabiliste parle de dépendance multivariée/temporale.

**Sources :** Huang et al. (2017), [doi:10.1175/WAF-D-16-0118.1](https://doi.org/10.1175/WAF-D-16-0118.1) ; Schefzik et al. (2013), [doi:10.1214/13-STS443](https://doi.org/10.1214/13-STS443).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Employer « amortissement de la variabilité et incohérence d’agrégation temporelle » | Vocabulaire précis | 0,5 h | Un relecteur CAMS fournit un terme officiel différent | Adopter le terme institutionnel s’il est documenté |

## 41. Valeur publiable

**[jugement]** En l’état : note de réplication, pas article original, car Bertrand a déjà publié le mécanisme et CAMS évalue déjà la MDA8. Après audit, reproduction Espagne/2025 et protocole figé, une courte *Technical note* dans *Atmospheric Chemistry and Physics* ou un article d’application dans *Atmospheric Environment* devient défendable. **Inconnu** : un éditeur jugerait-il la seule inversion saisonnière suffisamment nouvelle ?

**Sources :** précédent de format : Bertrand et al. (2023), *Technical note*, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; étude CAMS-MDA8 : Petetin et al. (2022), [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Rédiger un abstract de 250 mots seulement après validation 2025/Espagne | Teste la contribution sans gros coût | 2 h | L’abstract ne contient aucun apport absent de Bertrand/EQC | Abandonner l’article et garder une note de candidature |

## 42. Signalement à Copernicus

**[publié]** Le catalogue fournit un lien « Get help » vers le support ECMWF/Jira ; la documentation donne aussi le serveur EQC public.  
**[jugement]** Signalez d’abord en privé, avec script minimal, identifiants de station, dates, fuseau, définition MDA8, intersection exacte et résultats sans adjectif. Demandez confirmation de l’interprétation avant toute communication publique.

**Sources :** jeu ADS et support, [doi:10.24381/2cce4067](https://doi.org/10.24381/2cce4067) ; [catalogue ADS](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts-optimised-at-observation-sites).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Ouvrir un ticket privé avec paquet reproductible | Validation par le producteur | 2–3 h | CAMS identifie une erreur de variable, heure ou usage | Suspendre toute conclusion jusqu’à correction |

## 43. Risque de se tromper publiquement

**[jugement]** Il est élevé sur les détails et faible sur le mécanisme général. Les risques principaux sont déjà visibles : « année complète » malgré un début au 17 janvier, calcul MDA8/J+1, échantillon variable, comparaison à un modèle ayant vu les dates, et antériorité Bertrand. L’enjeu n’est pas l’autorité de l’organisme mais la reproductibilité.  
**[publié]** Le catalogue date explicitement le début au 17 janvier 2024 et l’EQC documente l’échantillon spécifique au MOS.

**Sources :** [catalogue ADS](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts-optimised-at-observation-sites) ; CAMS EQC 2025, §4.6, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Faire relire protocole et une dizaine de lignes brutes par un tiers | Réduit le risque réputationnel | 2 h | Le tiers ne reproduit pas les jours-station | Ne rien publier tant que la réplication exacte échoue |

## 44. Formulation non accusatoire

**[jugement]** Écrire : « Dans notre évaluation appariée, le produit optimisé pour les concentrations horaires conserve l’essentiel de son gain à l’heure, mais ce gain se réduit après transformation en MDA8 et change de signe certains mois chauds. Ce résultat décrit une inadéquation possible entre cible d’apprentissage et cible d’usage ; il ne remet pas en cause l’usage horaire prévu du produit. »

**Sources :** la cible horaire et les objectifs du produit sont documentés par [ECMWF](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; l’écart horaire/max est publié par Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Utiliser cette formulation après audit | Ton factuel et défendable | 0,5 h | L’évaluation corrigée ne montre plus le changement de signe | Retirer la proposition causale si mécanisme non testé |

## 45. Phrase résistante à un relecteur hostile

**[jugement]** « Sur les couples station–date français où observation, ENSEMBLE brut et CAMS-MOS sont conjointement disponibles entre le 17 janvier et le 31 décembre 2024, et après calcul de la MDA8 selon les règles européennes en heure civile, le gain de RMSE du MOS par rapport au brut est de X % [IC95 % : a ; b], contre Y % à l’heure ; d’avril à septembre, la différence appariée de RMSE est Z [IC95 % : c ; d]. »  
Cette phrase ne doit recevoir les nombres qu’après reprise du calcul.

**Sources :** couverture ADS, [doi:10.24381/2cce4067](https://doi.org/10.24381/2cce4067) ; définition MDA8, directive 2008/50/CE, [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32008L0050).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Remplir uniquement X–d depuis une table générée automatiquement | Traçabilité totale | 1 h | Table et texte divergent | Bloquer le document si une valeur est copiée manuellement |

## 46. Réponse à « ils ont de bonnes raisons »

**[jugement]** « Oui : le produit sert des séries horaires, plusieurs polluants et 0–96 h, doit être réentraîné quotidiennement et absorber vite les changements. Notre résultat ne conteste pas ce choix ; il montre qu’un objectif horaire ne garantit pas une cible non linéaire journalière. L’équipe CAMS l’avait d’ailleurs déjà signalé pour les maxima. »

**Sources :** [documentation CAMS-MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Préparer cette réponse en deux phrases pour l’entretien | Montre nuance et maîtrise | 0,5 h | Le jury ne s’intéresse pas au produit CAMS-MOS | Ne pas développer au-delà de 30 secondes sans relance |

## 47. Première page du dossier

**[jugement]** Pas encore. Un résultat qui contient trois réserves potentiellement fatales — date de début, calendrier réglementaire, test non prospectif — ne doit pas devenir l’accroche. Après validation 2025/Espagne, il peut devenir un encadré de première page : « optimiser la bonne cible opérationnelle ». Aujourd’hui, la première page doit rester sur la correction aux stations exclues et l’évaluation des épisodes, avec réserves explicites.

**Sources :** l’antériorité du compromis est Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; couverture ADS, [doi:10.24381/2cce4067](https://doi.org/10.24381/2cce4067).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Garder le constat en page méthodologique jusqu’au test gelé | Évite de sur-vendre | 0,5 h | 2025 et Espagne reproduisent signe et IC | Promouvoir seulement si les deux validations passent |

## 48. Axe principal ou second rang

**[jugement]** Second rang maintenant. S’il survit, l’axe principal ne doit pas être « Copernicus se trompe », mais « aligner le post-traitement sur la décision : heure, MDA8, classe et épisode ». Cette formulation englobe votre modèle, le test direct-target et le constat CAMS tout en restant utile à ATMO Occitanie.

**Sources :** PREV’AIR entraîne déjà maximum et moyenne comme indicateurs dédiés, rapport LCSQA [PDF](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf) ; Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Réécrire le fil narratif autour de l’alignement cible–décision | Axe plus général et moins fragile | 2 h | Les tests direct-target ne se reproduisent pas hors échantillon | Revenir à un simple portfolio technique si gain < 3 points |

## 49. Contre-argument le plus fort

**[jugement]** Contre le constat CAMS : « vous avez mal construit le jour MDA8 ou J+1, et l’effet est un artefact de fuseau/fenêtre ». Contre la supériorité de votre modèle : « ce n’est pas une prévision opérationnelle, car il a appris sur 2024, peut contenir les observations d’autres stations aux mêmes dates et éventuellement ERA5, tandis que CAMS n’utilise que l’information disponible à l’émission ». Le second est actuellement décisif.

**Sources :** MDA8, directive 2008/50/CE, [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32008L0050) ; entrées opérationnelles CAMS, [documentation](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation) ; sensibilité prévision/ERA5, Petetin et al. (2022), [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Répondre par un test prospectif strict, non par un argument verbal | Ferme l’objection principale | 4–8 h | Avantage propre disparaît en 2025 | Retirer toute comparaison de niveau si ΔRMSE non significatif |

## 50. Prochaine question

**[jugement]** Si le résultat tient : « comment construire un post-traitement cohérent entre l’heure et les décisions journalières, sans sacrifier ni RMSE horaire ni détection des épisodes ? » Le dessin utile compare trois voies sous information strictement opérationnelle : modèle MDA8 direct, apprentissage multi-tâche heure+MDA8, et trajectoires probabilistes avec dépendance temporelle. Le critère final doit être un front Pareto heure–MDA8–CSI, pas une RMSE unique.

**Sources :** cibles dédiées, Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; dépendance temporelle, Lakatos et al. (2023), [doi:10.1002/qj.4436](https://doi.org/10.1002/qj.4436).

| Action | Gain attendu | Coût | Test qui la tue | Critère d’abandon |
|---|---:|---:|---|---|
| Prototyper d’abord un LightGBM multi-cible ou deux têtes avec mêmes variables | Peut conserver heure et gagner ≥ 3 points MDA8 | 6–8 h | Aucun point ne domine le MOS horaire et le direct-target | Abandonner l’architecture si elle est dominée sur RMSE heure, MDA8 et CSI |

# Verdict

## Le résultat est affaibli

**[jugement]** Le noyau qualitatif survit probablement, mais il n’est pas nouveau : l’équipe CAMS a déjà publié qu’un maximum tiré du MOS horaire est moins performant qu’une cible maximum directe. La réplication sur le produit opérationnel, la MDA8 réglementaire et l’inversion estivale peut avoir de la valeur. Elle n’est pas encore « blindée » : le jeu commence le **17 janvier 2024**, l’inégalité proposée est inversée, l’EQC public évalue déjà l’**ozone MDA8**, et la supériorité de votre modèle n’est pas comparable opérationnellement tant que 2025 n’est pas strictement gelé.

Priorité avant toute valorisation : recalcul par `valid_time` local avec les sept heures antérieures, intersection exacte des trois flux, IC station × blocs de jours, puis France-2025 et Espagne. Si le signe avril–septembre disparaît après le premier audit, le résultat central est faux ; s’il disparaît seulement hors France-2024, il devient un cas d’étude local.

# Points classés Inconnu

- Existence d’une publication antérieure portant exactement sur **le produit ADS opérationnel actuel**, la **MDA8 réglementaire française** et son **inversion saisonnière**.
- Présence publique, sur le serveur EQC, de vos valeurs françaises mensuelles exactes et du même seuil de POD.
- Amplitude quantitative de l’optimisme causé par l’apprentissage sur 2024 dans votre protocole précis.
- Loi quantitative de l’aggravation du tassement avec l’échéance pour CAMS-MOS.
- Algorithme et cible exacts du produit **horaire** PREV’AIR en production 2026.
- Sens et amplitude de l’effet sur l’AOT40 avant calcul.
- Gains transférables d’une inflation de variance appliquée à l’O₃ CAMS-MOS actuel.
- Seuil de nouveauté éditoriale : l’inversion saisonnière seule suffirait-elle à une publication ?
