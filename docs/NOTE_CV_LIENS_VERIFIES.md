# Bloc « contact » du CV — liens vérifiés en anonyme le 21/08/2026

Le CV du 16/06 ne porte **aucun lien** : email, téléphone, adresse. Tout ce qui suit a été
demandé **sans session et sans compte**, c'est-à-dire dans les conditions du recruteur.

## Ce qui est vivant, ce qui ne l'est pas

| lien | code | à mettre sur le CV ? |
|---|---:|---|
| `gitlab.com/cyril.bgs.dev` | **200** | ✅ **oui** — c'est là que vit le travail récent |
| `kaggle.com/cyrilbourgeois` | **200** | ✅ oui |
| `github.com/InProgress63` | **200** | 🟠 à toi et vivant, mais ce n'est **pas le compte à mettre en avant** |
| `github.com/cyril-bgs-dev-tech` | **404** | ⛔ **non** — compte suspendu, recours en cours |
| `github.com/cyril-bourgeois` | 200 | ⛔ **non** — aucun nom, un dépôt « MHE » : probablement pas toi |
| `github.com/cyrbourgeois` | **404** | ⛔ non — n'existe pas |
| `linkedin.com/in/…` | **999** | ⚠️ **à vérifier au navigateur** — voir plus bas |

> ⛔ **Le piège à ne pas commettre : un 404 sur un CV.** Une lettre vit le temps d'une
> candidature ; un CV circule pendant des mois, chez des gens qu'on ne connaît pas. Un lien
> mort y est bien plus coûteux qu'ailleurs, et personne ne te préviendra.

## Le bloc proposé

```
cyril.bgs.dev@gmail.com · 06 89 44 81 36
42 bd côte blatin, 63000 Clermont-Ferrand
gitlab.com/cyril.bgs.dev · kaggle.com/cyrilbourgeois · linkedin.com/in/<à confirmer>
```

**Pourquoi GitLab, et GitHub seulement après rétablissement.** Le compte qui porte le travail
récent — qualité de l'air, aegis-rca, vigilance, recherche anomalies — est
`cyril-bgs-dev-tech`, et il rend **404** aux visiteurs non connectés. `InProgress63` répond et
t'appartient, mais ses 4 dépôts datent de mars 2024 et ne montrent que la formation : ce n'est
pas l'identité que le CV doit porter, décision prise le 21/08.

Donc **GitLab sur le CV aujourd'hui**, et GitHub ajouté le jour où
`github.com/cyril-bgs-dev-tech` s'ouvre en navigation privée — pas sur la promesse du recours,
sur la vérification. `scripts/miroir_github.sh` republiera dessus ce jour-là : il prend son
compte du jeton, donc il vise le compte rétabli sans être modifié, et il **refuse d'annoncer
un succès si l'anonyme n'obtient pas le contenu**.

## Les deux liens à trancher toi-même

1. **LinkedIn.** `in/cyrbourgeois` (dans la lettre) contre `in/cyril-bourgeois` (40 fois dans
   le portefeuille). LinkedIn rend **999 aux deux**, page identique de 1 530 octets, quel que
   soit l'agent — testé 3 fois chacun. **Aucune mesure ne peut trancher d'ici** : ouvrir les
   deux dans un navigateur.
2. **Faut-il citer GitHub malgré tout ?** Certains recruteurs filtrent sur le mot. Si oui,
   `InProgress63` — jamais `cyril-bgs-dev-tech` tant qu'il rend 404.

## Comment revérifier, en une commande

```bash
for u in gitlab.com/cyril.bgs.dev kaggle.com/cyrilbourgeois github.com/InProgress63; do
  printf '%s %s\n' "$(curl -s -o /dev/null -w '%{http_code}' -L "https://$u")" "$u"
done
```

Et `scripts/verifier_portefeuille.py` contrôle ⑤ fait la même chose sur les 27 liens publiés.
