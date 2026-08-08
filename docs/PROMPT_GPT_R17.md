# Prompt GPT — R17 · La cartographie des partenaires d'Atmo Occitanie

> À coller tel quel. Rédigé le **08/08/2026**. R16 cherchait mes angles morts **techniques** ;
> celui-ci porte sur le **métier du poste visé**, et sur lui seul.
>
> Je candidate au **pôle Partenariats d'Atmo Occitanie**, clôture le **22 août 2026**. Les
> quatre missions du poste ne parlent pas de modélisation : produire des indicateurs et des
> livrables pour des partenaires · formaliser un besoin métier en données · valoriser la
> donnée d'un partenaire dans des projets collaboratifs · diffuser les bonnes pratiques data.
>
> **Je ne cherche pas un résultat de plus.** Je cherche à savoir **avec qui ce poste
> travaille réellement** — nommément, et avec ce que chacun est *obligé* de faire, ce qu'il
> *veut* faire, et ce qui l'*empêche*. Mon dossier atteste sept partenaires ; je suis
> incapable de dire si c'est la moitié ou les neuf dixièmes du paysage réel.

---

## Ce que je vous demande de produire, en une phrase

**Une fiche par partenaire**, avec exactement six rubriques : **obligations** (le texte qui
les impose) · **missions** · **besoins** en donnée qualité de l'air · **points forts** ·
**faiblesses** · **envies** (ce qu'ils cherchent à obtenir et qui n'est pas encore une
obligation). Plus la liste de ceux que **j'ai oubliés**.

---

## Le contexte technique, en cinq lignes — pour situer ce que je peux offrir

Post-traitement statistique des prévisions **CAMS Europe** (maille ≈ 8 × 11 km) sur
**476 stations françaises**, quatre polluants — O₃, NO₂, PM10, PM2,5. Un modèle apprend le
résidu `observation − prévision` et le corrige. Le système produit **des points corrigés**,
**un champ spatialisé au pas de 0,1°** (France, Occitanie, Nouvelle-Aquitaine), et
**102 pages HTML autonomes** — une par territoire, sans serveur ni compte.

Deux chiffres pour calibrer ce que je peux promettre, et un pour calibrer ce que je ne peux
pas : le NO₂ brut de CAMS est **4 à 6 fois trop bas** en moyenne régionale et notre
correction le ramène à moins de 4 µg/m³ du niveau observé ; mais contre les **épisodes
réellement déclenchés par procédure préfectorale**, nous n'en attrapons que **2 sur 33** —
la chaîne officielle en attrape 1. Le domaine entier est aveugle sur cet objet-là.

---

## L'état actuel de ma cartographie — c'est ce qu'il faut attaquer

Voici **l'intégralité** de ce que mon dossier atteste aujourd'hui. Chaque ligne est sourcée
dans le dépôt ; aucune n'a été écrite d'après une intuition du paysage institutionnel.

| partenaire | la décision qu'il prend | ce que mon travail lui fournit |
|---|---|---|
| **Préfecture de département** | déclencher ou lever une procédure — 52 zones-jours en 14 mois | la mesure des épisodes, et un volume d'alertes **choisi** plutôt que subi |
| **ARS** | informer les publics sensibles, au moins quotidiennement en épisode | l'indice par commune, et les stations classées par risque du jour |
| **Toulouse Métropole · Montpellier Méditerranée Métropole** | maintenir, modifier ou réévaluer les scénarios **ZFE** | le champ spatialisé régional |
| **Région et collectivités — PPA, PCAET** | bâtir et suivre les plans à l'échelle de leur territoire | 102 pages autonomes, une par territoire |
| **LCSQA · Ineris** | produire PREV'AIR et le flux national | une évaluation indépendante de leur chaîne, dans leurs propres conventions |
| **Atmo Nouvelle-Aquitaine — coopération SIREQAETE** | partager une prévision quotidienne sur le Grand Sud-Ouest | des champs couvrant déjà les deux régions, et une chimie globale indépendante de CAMS |
| **Partenaires sanitaires et agricoles** | surveiller les pesticides dans l'air ambiant | **rien** — hors périmètre, et sans valeur réglementaire dans l'air ambiant |

**Et voici la réserve que ce tableau porte lui-même**, parce que je refuse d'inventer une
liste que je n'ai pas :

> « Ce tableau recense les partenaires que ce dossier atteste. Il ne prétend **pas** lister
> les adhérents des quatre collèges statutaires (État · collectivités · émetteurs ·
> associations et personnalités qualifiées) : cette liste appartient à Atmo Occitanie, et
> l'écrire sans source serait exactement le défaut que le reste du dossier traque. »

**C'est précisément ce trou que je veux combler — avec des sources, pas avec de la
vraisemblance.** Une liste plausible mais fausse me coûterait l'entretien ; une liste courte
et sourcée, complétée par un « je ne sais pas » explicite, ne me coûte rien.

---

## Question 1 — Les quatre collèges, nommément

Une AASQA est une association loi 1901 agréée, gouvernée par quatre collèges. Je veux la
composition **réelle d'Atmo Occitanie**, pas le principe général.

1. Quels textes fixent la structure en quatre collèges et l'agrément — **article par
   article** (code de l'environnement, arrêté d'agrément, statuts types) ? Que dit
   exactement le texte sur l'**équilibre** entre collèges et sur le **droit de vote** ?
2. Pour Atmo Occitanie précisément : quels membres composent chaque collège aujourd'hui ?
   Nommez-les, avec la source (statuts, rapport d'activité, liste d'adhérents publiée,
   composition du conseil d'administration) et son **millésime**.
3. Combien d'adhérents au total, et quelle est la part de chaque collège dans le
   **financement** ? Le financement est-il la bonne clé de lecture de l'influence, ou
   une fausse piste ?
4. **Qu'est-ce qui distingue Atmo Occitanie des autres AASQA** dans sa gouvernance ou son
   périmètre ? Fusion de deux structures antérieures, taille du territoire, nombre de
   départements, particularités statutaires.

## Question 2 — L'obligation, partenaire par partenaire

Un besoin qui n'est pas adossé à une obligation se négocie ; un besoin adossé à un texte
s'impose. Je veux savoir lequel est lequel.

1. Pour **chaque** catégorie de partenaire, quel texte crée l'obligation, et **quelle
   obligation exactement** ? Je cherche les articles, pas les principes : surveillance et
   information (code de l'environnement, livre II titre II), évaluation annuelle des
   modèles (arrêté du 16/04/2021, article 13), **PPA**, **PCAET**, **ZFE**, **PREPA**,
   directive **(UE) 2024/2881** et son calendrier de transposition.
2. Lesquelles de ces obligations sont **échues, en cours, ou à venir** d'ici 2030 ? Une
   obligation qui entre en vigueur dans dix-huit mois est le meilleur terrain d'un pôle
   Partenariats — c'est là qu'un partenaire ne sait pas encore comment il fera.
3. Quelles obligations pèsent sur l'**AASQA elle-même** vis-à-vis de ses partenaires
   (délais de publication, format, gratuité, réutilisation, données ouvertes) ?
4. Où l'obligation est-elle **de moyens** et où est-elle **de résultat** ? La distinction
   change entièrement ce qu'un indicateur doit prouver.

## Question 3 — La fiche des six rubriques, pour chaque partenaire

C'est le cœur de la demande. Pour **chacun** des partenaires que vous aurez identifiés —
les sept de mon tableau **et** ceux que j'ai oubliés — remplissez :

| rubrique | ce que j'attends |
|---|---|
| **obligations** | le texte, l'article, l'échéance |
| **missions** | ce que la structure fait, au-delà de l'air |
| **besoins** en donnée d'air | grandeur, grain spatial, grain temporel, latence, format |
| **points forts** | ce qu'elle apporte à une AASQA — donnée, réseau, financement, légitimité |
| **faiblesses** | ce qui lui manque et qu'une AASQA peut combler |
| **envies** | ce qu'elle cherche sans y être obligée — et pourquoi maintenant |

1. Remplissez la grille. **Étiquetez chaque case** : sourcé / pratique courante non écrite /
   extrapolation.
2. Pour la rubrique **besoins**, soyez concret sur le **grain** : une préfecture, une ARS et
   une métropole ne veulent ni la même maille, ni la même latence, ni le même objet. Qui
   veut une **station**, qui veut une **commune**, qui veut une **zone administrative**, qui
   veut un **champ** ?
3. Pour la rubrique **envies** : qu'est-ce qui, en 2026, est en train de devenir une demande
   forte et ne l'était pas il y a trois ans ? Microcapteurs, air intérieur, pollens,
   pesticides, odeurs, bruit, GES et air en une seule chaîne, exposition individuelle,
   justice environnementale, IA.

## Question 4 — Qui manque à mon tableau

1. Quels partenaires **structurants** sont absents de mes sept lignes ? Je pense n'avoir
   couvert ni les **émetteurs industriels** (troisième collège, qui financent), ni les
   **associations agréées de protection de l'environnement**, ni les **acteurs de santé**
   au-delà de l'ARS, ni le monde **académique**, ni les **gestionnaires d'infrastructure**
   (ports, aéroports, autoroutes, SNCF), ni l'**ADEME**, ni **Météo-France**, ni les
   **parcs naturels**, ni le monde **agricole** au-delà des pesticides.
2. Pour chacun des manquants : est-il un partenaire **d'Atmo Occitanie en particulier**, ou
   du réseau AASQA en général ? La distinction m'importe.
3. Y a-t-il des partenariats **spécifiques au territoire occitan** que je ne peux pas
   deviner ? Je pense à l'ozone méditerranéen, aux **poussières sahariennes**, à la vallée
   de l'Ariège, à l'étang de Berre voisin, aux ports de Sète et Port-la-Nouvelle, à
   l'aéronautique toulousaine, à la viticulture, aux incendies.
4. **Fédération Atmo France** : que mutualise-t-elle, et qu'est-ce qui reste à la main de
   chaque association ? Un pôle Partenariats travaille-t-il avec elle, ou à côté ?

## Question 5 — Ce qu'un partenaire reproche à une AASQA

C'est la question dont la réponse m'est la plus utile en entretien, et la plus difficile à
trouver écrite.

1. Quelles **insatisfactions récurrentes** les partenaires expriment-ils ? Latence,
   granularité, incertitude non communiquée, jargon, formats fermés, discontinuité entre
   régions, indice mal compris du public, écart entre prévision et ressenti.
2. Où une AASQA **dit non**, et pourquoi ? Un pôle Partenariats passe autant de temps à
   refuser qu'à livrer ; je veux connaître les refus légitimes.
3. Quels sont les **échecs connus** de projets collaboratifs dans ce domaine, et leur cause ?
   Un projet qui a échoué m'apprend plus qu'un projet réussi.
4. **Sur ma propre offre** : parmi les sept lignes de mon tableau, lesquelles un praticien
   jugerait-il **naïves** ? Je soupçonne la ligne ZFE — un champ à 0,1° est bien trop
   grossier pour un périmètre urbain, et je le dis, mais peut-être pas assez fort.

## Question 6 — Le geste utile avant le 22 août

1. Sachant qu'il reste **quatorze jours** et que le dépôt prime sur toute amélioration :
   quel est le **plus petit livrable** qui prouverait la compétence « partenariats » mieux
   que ce que j'ai ? J'ai déjà une **fiche indicateur** (définition, formule, périmètre,
   fréquence, destinataire, cinq limites écrites par moi dont une qui interdit son emploi
   pour une procédure préfectorale).
2. Une **fiche indicateur** est-elle le bon format, ou le métier en attend-il un autre —
   convention, cahier des charges, note de cadrage, catalogue de données, fiche de
   réutilisation ?
3. Quelles **questions un jury de pôle Partenariats** pose-t-il, et lesquelles ne portent
   pas du tout sur la technique ?
4. Quel **vocabulaire** trahirait immédiatement quelqu'un qui n'a jamais travaillé en
   AASQA ? Le projet a déjà commis ce genre de faute : avoir appelé « J+1 » pendant des
   semaines des prévisions qui étaient du **J0**. J'en cherche les jumelles côté métier.

## Question 7 — Ce que je n'ai pas demandé

1. Quelle question aurais-tu posée **à ma place** sur ce sujet, et que je n'ai pas posée ?
2. Qu'est-ce qui, dans ma façon de présenter les partenaires, révèle que je les vois **en
   destinataires d'un produit** plutôt qu'en **co-constructeurs** — si c'est le cas ?
3. Y a-t-il un partenaire pour lequel mon travail a une valeur que **je n'ai pas vue** ?

---

## Contraintes de réponse

- **Cite tes sources**, systématiquement : texte réglementaire avec l'article, rapport avec
  sa page et son année, page web avec sa date de consultation. La règle de ce projet est que
  tout élément du dossier doit remonter à une source ou à un artefact.
- **Distingue trois registres et étiquette-les** : ① établi et sourcé · ② pratique courante
  non écrite · ③ extrapolation de ta part. Le registre ③ m'est utile — mais seulement s'il
  est nommé comme tel.
- **N'invente aucune liste d'adhérents.** Si tu ne trouves pas la composition d'un collège,
  écris-le. Une liste plausible et fausse me coûterait un entretien ; un trou nommé
  m'indique juste où chercher.
- **Sépare ce qui vaut pour Atmo Occitanie de ce qui vaut pour le réseau AASQA.**
- **Hiérarchise.** Si une seule fiche partenaire devait être parfaite avant le 22 août,
  laquelle, et pourquoi ?
- Réponds en **français**, avec la terminologie du métier.

*Réponses attendues dans `docs/GPT_R17.md`.*
