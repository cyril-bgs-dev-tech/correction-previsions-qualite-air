# Bloc « contact » du CV — liens vérifiés en anonyme le 21/08/2026

Le CV du 16/06 ne porte **aucun lien** : email, téléphone, adresse. Tout ce qui suit a été
demandé **sans session et sans compte**, c'est-à-dire dans les conditions du recruteur.

## Ce qui est vivant, ce qui ne l'est pas

| lien | code | à mettre sur le CV ? |
|---|---:|---|
| `gitlab.com/cyril.bgs.dev` | **200** | ✅ **oui** — c'est là que vit le travail récent |
| `kaggle.com/cyrilbourgeois` | **200** | ✅ oui |
| `github.com/InProgress63` | **200** | 🟠 à toi, vivant, mais **dernier push mars 2024** |
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

**Pourquoi GitLab et pas GitHub.** Le compte qui porte le travail récent — correction des
prévisions de qualité de l'air, aegis-rca, vigilance, recherche anomalies — est
`cyril-bgs-dev-tech`, et il rend **404** aux visiteurs non connectés. `InProgress63` est bien
à toi et répond, mais ses 4 dépôts publics datent de mars 2024 et ne montrent que les projets
de formation : y renvoyer donnerait de ton niveau actuel une image nettement en dessous du
vrai. **Ajouter GitHub le jour du rétablissement**, pas avant.

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
