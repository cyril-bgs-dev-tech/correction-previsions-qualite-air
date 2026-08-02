# Tâches créatives pour Grok 4.5 — une par session, dans l'ordre de valeur

**Pourquoi ce format.** Les rondes précédentes ont montré où Grok est irremplaçable : le
**retournement de cadre** (« ce que tu notes 3/10 est le début du produit »), la **lecture
humaine** (« l'auto-notation sans contrepartie agace plus que le défaut »), et le **flair
pour la bonne condition** — il a posé le test de la régression vers la moyenne sans faire un
seul calcul. Il ne source pas et ne calcule pas : ne rien lui demander de tel.

Chaque tâche est **autoportante** : on colle l'en-tête commun, puis une seule tâche. Sa
fenêtre étant courte, mieux vaut une tâche traitée à fond que six survolées.

---

## En-tête commun — à coller avant n'importe quelle tâche

> Tu m'as déjà relu six fois sur ce projet et tu connais le dossier. Rappel de l'état, en
> quatre lignes :
>
> Correction apprise (LightGBM) des prévisions **CAMS Europe** aux stations, France, 17 mois,
> validation par **stations exclues**. Sur les grandeurs réglementaires : **NO₂ +33,2 %**,
> **O₃ +28,9 %**, **PM2.5 +30,0 %** — niveau de l'état de l'art publié. Détection d'ozone :
> POD 0,663, CSI 0,464.
>
> **Les faiblesses, mesurées et assumées** : généralisation temporelle non démontrée (pire
> pli −35,5 %) ; météo **ERA5**, une réanalyse indisponible en opérationnel ; NO₂ horaire
> indétectable ; et une part du gain qui revient à une **dégradation du forçage** plutôt qu'au
> modèle (r = +0,953 entre dérive de CAMS et bénéfice absolu).
>
> **Ce qui a été construit depuis** : une **règle d'abstention** — ne pas corriger à la baisse
> quand CAMS annonce déjà un dépassement. Testée sur 3,2 M de couples : s'applique à 0,28 %
> des cas, coûte +0,02 µg/m³ de RMSE, relève le **POD de 0,325 à 0,389**. Sur le cas qui l'a
> fait naître — 26/07/2026, CAMS 49,6, observation 46,8, correction 36,6 — elle divise
> l'erreur du jour par 3,6.
>
> Candidature spontanée à ATMO Occitanie, échéance **22 août 2026**. Livrables actuels :
> présentation de dix pages, bibliothèque de figures, démo Streamlit, fiche opérationnelle.
>
> **Réponds court et tranché.** Pas de sourcing, pas de calcul — je ne te demande que ce que
> tu fais mieux que les autres : retourner un cadre, lire ce qu'un humain ressentira, et
> trouver l'angle que personne ne prend.

---

## Tâche 1 — La figure maîtresse

> Je peux mettre **une seule image** en première page. Elle doit faire comprendre en dix
> secondes ce que ce travail apporte, à quelqu'un qui ne lira pas la suite.
>
> Propose **trois** figures candidates. Pour chacune : ce qu'on y voit, ce qu'elle prouve, et
> ce qu'elle ne prouve pas. Puis choisis-en une et dis pourquoi les deux autres perdent.
>
> Contrainte : elle doit survivre à un vidéoprojecteur médiocre et à un regard de trente
> secondes. Une courbe à sept séries est disqualifiée d'office.

## Tâche 2 — Les autres retournements

> Ton meilleur apport a été de retourner une faiblesse en fonctionnalité : « ce que tu
> sous-scores en temporel, c'est le début du produit ».
>
> **Fais-le encore, sur les quatre autres faiblesses** : (a) la météo ERA5 indisponible en
> opérationnel ; (b) le NO₂ indétectable ; (c) une part du gain qui vient de la dégradation du
> forçage ; (d) le fait de ne pas utiliser d'observations récentes.
>
> Pour chacune : y a-t-il un cadrage où ce défaut devient un **argument** ? Si non, dis-le —
> un retournement forcé se voit et coûte plus qu'il ne rapporte.

## Tâche 3 — L'écran du lundi matin

> Décris **l'écran** que voit le prévisionniste à 13 h. Pas l'architecture, pas les métriques :
> ce qu'il voit, dans quel ordre, et le geste qu'il fait ensuite.
>
> Contraintes : il a **quatre minutes**, il regarde vingt zones, et il doit décider
> *publier / graduer / attendre*. Il ne lira aucune documentation.
>
> Dis aussi ce qu'il **ne doit pas** voir — un tableau de RMSE, par exemple, ou une
> probabilité sans échelle interprétable.

## Tâche 4 — Nommer

> Trois choses n'ont pas de nom, et un nom décide de la façon dont on en parle :
>
> 1. la **règle d'abstention** (ne pas corriger à la baisse quand le forçage alerte déjà) ;
> 2. le **produit** dans son ensemble ;
> 3. le **phénomène** — le gain qui se concentre là où le forçage dérive.
>
> Propose deux ou trois noms pour chacun. Écarte le jargon anglais et les acronymes. Un bon
> nom se retient après l'avoir entendu une fois et ne promet pas plus que ce qui est mesuré.

## Tâche 5 — L'analogie qui tient

> Je dois expliquer à une direction non technique — voire à un élu — pourquoi une correction
> automatique **gagne moins quand le modèle d'origine va bien**, et pourquoi il faut parfois
> la désactiver.
>
> Trouve **deux analogies**. Puis attaque-les : où chacune ment-elle ? Une analogie qui ne
> ment nulle part n'existe pas ; celle qu'on garde est celle dont le mensonge est **inoffensif
> dans le contexte où on l'emploie**.

## Tâche 6 — L'angle que personne ne prend

> Dans la correction statistique des prévisions de qualité de l'air, tout le monde fait à peu
> près la même chose. **Quel angle personne ne prend**, et qui serait à ma portée avec
> 17 mois de données, 476 stations, un GPU et trois semaines ?
>
> Donne trois pistes, de la plus sage à la plus risquée. Pour chacune, dis ce qui la rend
> négligée — si c'est parce qu'elle est mauvaise, dis-le, c'est une réponse utile.

## Tâche 7 — Les six questions pièges

> Écris les **six questions** qu'un ingénieur d'AASQA posera pour me mettre en difficulté, en
> connaissant mes faiblesses. Classe-les par difficulté.
>
> Pour chacune, donne aussi la **mauvaise réponse instinctive** — celle que je vais donner si
> je ne me suis pas préparé. C'est elle qui m'intéresse le plus.

## Tâche 8 — Ce que je jetterais à tort

> Il reste trois semaines. Je vais devoir couper. **Qu'est-ce que je risque de jeter alors
> que ça a de la valeur pour un recruteur**, et que je sous-estime parce que ça ne ressemble
> pas à du résultat ?
>
> Tu l'as déjà fait une fois avec la gouvernance du modèle. Cherche-en deux autres.

## Tâche 9 — Le livrable à six mois

> Ta propre question restée sans réponse : *« à six mois, quel livrable de service te rend non
> optionnel ? »*
>
> Réponds-y **à ma place**, en trois scénarios selon le poste : prévision, données, ou études.
> Pour chacun : le livrable, à qui il sert, et ce qui se passerait s'il disparaissait. Le
> critère est celui-là — ce dont l'absence se remarquerait.

## Tâche 10 — La dernière page

> Quelle doit être la **dernière page** de la présentation ? Pas un résumé, pas des
> remerciements : la chose qu'on veut laisser dans la tête de quelqu'un qui referme le
> document.
>
> Propose trois versions : une qui mise sur le chiffre, une sur la limite assumée, une sur
> l'ouverture. Dis laquelle tu gardes et ce que les deux autres laissent passer.

---

## Après chaque tâche

Consigner la réponse dans `docs/GROK_CREA_<n>.md`, et **noter ce qui a été retenu ou écarté,
avec la raison**. Les rondes précédentes ont montré que ses meilleures idées sont des
retournements de cadre, qui ne se jugent pas à la première lecture — mais aussi qu'il peut
bâtir sur une prémisse fausse sans la vérifier. Chaque idée retenue doit être confrontée aux
mesures avant d'entrer dans un livrable.
