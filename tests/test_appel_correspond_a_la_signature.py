#!/usr/bin/env python3
"""Un point d'entrée doit passer à `main()` exactement ses paramètres — ni plus, ni moins.

Ce que ce test attrape, et ce qu'il a coûté de ne pas l'avoir
--------------------------------------------------------------
Deux fois sur ce dépôt, le désaccord entre le parseur d'arguments et la signature de `main()`
a produit un défaut MUET :

* une option `--lot` présente dans le parseur et **absente de l'appel positionnel** a fait
  tourner la chimie sous l'étiquette des précurseurs et **écraser leur fichier**. Rien n'a
  levé : le CSV existait, ses colonnes étaient les bonnes, ses valeurs venaient d'ailleurs ;
* et le 24/08, en convertissant l'appel en arguments nommés, j'ai écrit `plis_spatiaux=`
  quand le paramètre s'appelle `n_spa` — l'option, elle, s'appelle `--plis-spatiaux`. Ce
  décalage de nom est exactement ce qui rend un appel positionnel fragile.

Le second a été refusé en quatre minutes par le contrôle d'artefact. Le premier n'a été vu
que parce qu'un fichier a été relu par hasard.

> **Un appel positionnel est correct ou faux, et rien ne le dit. Un appel nommé est
> vérifiable — encore faut-il le vérifier.**
"""
import ast
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
# Les scripts dont le point d'entrée appelle `main(...)` avec des mots-clés.
CIBLES = ("scripts/methode_maximale.py",)


def _verifier(chemin: Path) -> None:
    arbre = ast.parse(chemin.read_text())
    fn = next((n for n in ast.walk(arbre)
               if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
    assert fn is not None, f"{chemin.name} : pas de fonction `main`"
    params = {a.arg for a in fn.args.args}
    appels = [n for n in ast.walk(arbre)
              if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "main"]
    assert appels, f"{chemin.name} : aucun appel à `main` trouvé"
    appel = appels[-1]
    assert not appel.args, (
        f"{chemin.name} : `main` est appelé avec {len(appel.args)} argument(s) POSITIONNELS. "
        f"Un argument positionnel arrive au bon endroit ou au mauvais, et rien ne le dit.")
    passes = {k.arg for k in appel.keywords}
    intrus = passes - params
    assert not intrus, (
        f"{chemin.name} : mot(s)-clé(s) inconnu(s) de la signature : {sorted(intrus)}. "
        f"Paramètres réels : {sorted(params)}")
    manque = params - passes
    assert not manque, (
        f"{chemin.name} : paramètre(s) jamais passé(s) par la ligne de commande : "
        f"{sorted(manque)}. Une option présente dans le parseur et absente de l'appel est "
        f"le défaut qui a écrasé un fichier de résultats.")


def test_les_points_d_entree_passent_exactement_leurs_parametres():
    for c in CIBLES:
        _verifier(RACINE / c)


if __name__ == "__main__":
    test_les_points_d_entree_passent_exactement_leurs_parametres()
    print("  ✅ chaque point d'entrée passe exactement les paramètres de sa `main`")
