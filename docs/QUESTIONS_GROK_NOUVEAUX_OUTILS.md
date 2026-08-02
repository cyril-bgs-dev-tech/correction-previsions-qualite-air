# Questions à Grok 4.5 — ce que ces nouvelles données valent en exploitation

> À coller tel quel. ChatGPT reçoit un jeu complémentaire sur la **rigueur méthodologique** —
> statistiques de dispersion, contrôles négatifs, fuites. **N'y va pas.**
>
> Ton angle : *un service pourrait-il en faire quelque chose un mardi matin, et à quel prix ?*
> Quand une question repose sur une prémisse fausse, dis-le au lieu d'y répondre.

---

## Ce qui vient de s'ouvrir

| source | ce qu'on en a | coût mesuré |
|---|---|---|
| **6 membres de l'ensemble CAMS** — CHIMERE, EMEP, MOCAGE, SILAM, LOTOS-EUROS, MATCH | O₃ horaire, 0,1°, **16 mois sur 17** (nov. 2023 perdu en HTTP 400) | 4,6 Go, 2 h |
| **GFAS** — puissance radiative des feux | 0,1°, quotidien, 2003 → **03/12/2025**, puis migration hors ADS | **0,1 Mo/mois, 15 min** le lot entier |
| **IFS et AIFS** via seau AWS | prévisions physique **et** neuronale, surface + 13 niveaux, depuis le 18/01/2023, lecture par plage d'octets | ~4 000 requêtes, 168 Go, 2-4 h |

Nous ne disposions jusqu'ici que de la **médiane** de l'ensemble, d'aucune donnée feu, et
d'aucune météo.

## Où en est le projet, pour situer

Correction du résidu `observation − CAMS` à la grandeur réglementaire, 270 stations, validation
par stations exclues. Le résultat qui compte : **à budget de fausses alertes égal, 3,6 fois plus
de dépassements d'ozone détectés** que CAMS brut — facteur reproduit hors fenêtre
d'apprentissage. Sur PM2,5, 0,485 de rappel à 30 % de fausses alertes. Sur **NO₂, rien** : 270
dépassements sur 161 637 jours-station, aucun budget atteignable.

Trois matinées d'astreinte rejouées en juillet 2026 ont montré le mode d'échec : sur une
sous-estimation brutale, aucun post-traitement ne rattrape. Le 25/07, sept stations dépassaient
réellement, aucun produit n'en annonçait une seule.

---

## A. La dispersion d'ensemble, côté salle (1-12)

1. Un prévisionniste d'AASQA **regarde-t-il** la dispersion des membres CAMS aujourd'hui, ou
   seulement la médiane ?
2. Si oui, sous quelle forme — carte, série, éventail, indicateur unique ?
3. Qu'est-ce qu'il en fait concrètement : il gradue, il attend, il appelle quelqu'un ?
4. Un fort désaccord entre modèles change-t-il sa décision, ou seulement sa confiance ?
5. Existe-t-il une pratique établie du type « si les modèles divergent de plus de X, ne pas
   publier automatiquement » ?
6. Certains membres ont-ils une **réputation** dans le métier — CHIMERE meilleur en hiver,
   MOCAGE sur les poussières, etc. ? Est-ce documenté ou du folklore ?
7. Le fait que CHIMERE soit le modèle de PREV'AIR change-t-il son statut aux yeux d'une AASQA
   française ?
8. Une AASQA aurait-elle un intérêt à voir un correcteur **pondérer** les membres plutôt que
   prendre la médiane, ou est-ce vu comme une boîte noire de plus ?
9. Quelle serait la réaction à « votre modèle utilise le désaccord entre modèles comme signal
   de méfiance » — utile ou trop subtil ?
10. Un indicateur d'incertitude non calibré est-il pire que pas d'indicateur du tout, dans ce
    métier ?
11. Que se passe-t-il en exploitation quand **un membre tombe** un matin ? La chaîne le
    supporte-t-elle ?
12. Six membres sur onze : est-ce défendable auprès d'un ingénieur, ou bancal ?

## B. Les feux, côté décision (13-24)

13. Comment une AASQA apprend-elle aujourd'hui qu'un feu affecte sa région — un flux, un
    téléphone, la préfecture, la fumée par la fenêtre ?
14. À quelle vitesse cette information arrive-t-elle, et par quel canal ?
15. Un prévisionniste **ajuste-t-il** sa prévision à la main quand il sait qu'un feu brûle en
    amont ?
16. Existe-t-il une procédure écrite pour les épisodes de fumée, distincte des épisodes
    ordinaires ?
17. Les feux comptent-ils comme épisode « naturel » exclu du décompte réglementaire, et cela
    change-t-il l'intérêt de les prévoir ?
18. Quelle échelle importe le plus en pratique : le feu local à 20 km, le feu ibérique à
    300 km, la fumée canadienne à 5 000 km ?
19. Un service utiliserait-il un modèle qui annonce « épisode probable, origine combustion » —
    ou l'origine est-elle hors de son mandat ?
20. Que ferait un prévisionniste d'un indicateur « exposition aux feux amont » sur son écran ?
21. Les épisodes de fumée sont rares. Un outil qui n'améliore que ces jours-là mérite-t-il d'être
    maintenu toute l'année ?
22. GFAS quitte l'ADS le 4 décembre pour le portail ECMWF. Un service accepterait-il une
    dépendance à une source qui vient de migrer ?
23. Existe-t-il, côté sécurité civile ou EFFIS, des flux que les AASQA utilisent déjà et que
    j'ignore ?
24. Un feu est aussi un **événement médiatique**. Cela change-t-il la tolérance à l'erreur ce
    jour-là — dans quel sens ?

## C. Le modèle « situation habituelle + feu » (25-33)

L'idée : deux modèles, un généraliste et un spécialiste des régimes de combustion, choisis par
un détecteur.

25. Un service accepterait-il **deux modèles** en exploitation, ou est-ce disqualifiant en soi ?
26. Qui répond quand le routeur se trompe — c'est-à-dire quand le mauvais modèle a parlé ?
27. Ce projet a déjà mesuré qu'un **modèle dédié aux journées anormales perd** (14,70 contre
    13,32). Un praticien s'attendrait-il au même échec sur les feux, et pourquoi ?
28. Vaut-il mieux un second modèle, ou un **garde-fou** qui suspend la correction en régime de
    feu et laisse passer le brut ?
29. Comment une AASQA gère-t-elle aujourd'hui les situations qu'elle sait mal modélisées —
    a-t-elle des modes dégradés explicites ?
30. Un système qui dit « je ne sais pas aujourd'hui » a-t-il de la valeur, ou est-ce perçu comme
    une dérobade ?
31. Quel **gain minimal** justifierait la complexité opérationnelle d'un système à deux modèles ?
32. Le spécialiste devrait-il porter sur les **feux** ou plus largement sur les **épisodes
    importés** — poussières, fumées, transport lointain ?
33. Si tu devais formuler cette idée en une phrase pour un directeur technique, laquelle ?

## D. Les modèles de fondation (34-42)

34. AIFS et Aurora sont-ils regardés dans le milieu de la qualité de l'air, ou restent-ils une
    curiosité météo ?
35. Une AASQA accepterait-elle une prévision **neuronale** comme entrée d'une chaîne
    réglementaire ?
36. Qu'est-ce qui bloque en pratique — la traçabilité, la validation, la responsabilité
    juridique, l'habitude ?
37. Le fait qu'AIFS soit **opérationnel à l'ECMWF** change-t-il son acceptabilité par rapport à
    un modèle académique ?
38. Aurora est annoncée égalant ou dépassant CAMS sur 74 % des cibles. Un ingénieur d'AASQA y
    croit-il, et que demanderait-il pour être convaincu ?
39. Si un modèle de fondation battait CAMS sur la grandeur réglementaire, qu'est-ce qui
    changerait — ou rien, faute de mandat pour en changer ?
40. Est-ce un sujet qui **intéresse** un recruteur d'AASQA, ou qui l'inquiète ?
41. Y a-t-il un risque à en parler en entretien — passer pour quelqu'un qui suit les modes ?
42. Comment le formuler pour que ce soit une compétence et non une lubie ?

## E. Priorités et pièges (43-50)

43. Au vu de ce que le projet a déjà mesuré, laquelle des trois pistes — ensemble, feux, météo
    prévue — a le plus de chances de **changer une décision** un mardi matin ?
44. Laquelle a le plus de chances d'impressionner un recruteur sans rien changer au service ?
    Et faut-il l'écarter pour autant ?
45. Le NO₂ est indétectable à ce grain — 270 dépassements sur 161 637 jours. Est-ce un constat
    qu'une AASQA connaît déjà, ou une information ?
46. Qu'est-ce qu'un praticien penserait de la comparaison **à budget de fausses alertes égal** ?
    Est-ce la bonne façon de lui présenter un gain de détection ?
47. Le budget de fausses alertes réel d'une AASQA, tu le situerais où — 10 %, 30 %, davantage ?
48. Trois matinées rejouées : est-ce assez pour convaincre, ou faut-il une saison entière ?
49. Qu'est-ce qui, dans tout ce que je viens de décrire, te paraît **du travail pour rien** ?
50. Quelle question aurais-je dû poser dans cette liste et que je n'ai pas posée ?
