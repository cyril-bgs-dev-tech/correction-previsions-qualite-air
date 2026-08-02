"""Le moteur unique du projet — un seul modèle, un seul réglage, partout.

Le défaut que ce module existe pour supprimer
---------------------------------------------
Au 02/08/2026, **quatre objets différents** produisaient les chiffres du dossier :

===========================================  ==========================================
ce qui produit le chiffre                    le modèle réellement employé
===========================================  ==========================================
`+23,4 %` publié (`fit_mos` → `mos._modele`) LightGBM **par défaut**, 400 arbres
tous les `apport_*`, `validation_bloquee`    XGBoost avec `REGLE` **mal traduit**
l'expérience du 02/08 sur la capacité        LightGBM, 3 288 arbres
`shap_familles`                              LightGBM, 2 000 arbres
===========================================  ==========================================

La traduction LightGBM → XGBoost employée jetait `num_leaves=255` — **le paramètre de
capacité** — et le remplaçait par un `max_depth=10` écrit en dur. Croissance *leaf-wise* à
255 feuilles contre *depth-wise* autorisant 1 024 : ce ne sont pas les mêmes modèles.

**Conséquence** : les gains mesurés par les uns ne s'additionnent pas à ceux mesurés par les
autres, et aucun ne décrit le système présenté. L'audit externe R9 l'a nommé comme le
deuxième défaut structurel du projet.

Pourquoi LightGBM par défaut, et pas le réglage « optimisé »
--------------------------------------------------------------
Parce que c'est **mesuré**, sur l'axe qui correspond au déploiement. Double aveugle — station
*et* mois cachés ensemble — sur l'ozone, quatre configurations :

===============================  ==========  ==============  ==================
configuration                    capacité    spatial         **double aveugle**
===============================  ==========  ==============  ==================
**`DEFAUT`** (celle-ci)          400 × 63    +24,10 %        **+3,31 %**
`REGLE`                          900 × 255   +29,68 %        +0,46 %
`DEFAUT` + arbres                3 000 × 63  +28,22 %        **−1,07 %**
===============================  ==========  ==============  ==================

**Dégradation monotone avec la capacité.** Plus un réglage gagne en validation spatiale, plus
il perd en conditions de déploiement — au point de devenir négatif. Sur NO₂ l'effet est
quasi absent (+25,71 → +24,73 → +24,53), ce qui est cohérent : son résidu est **sous-maille
et attaché au site**, donc transportable d'un mois à l'autre, là où celui de l'ozone est
**photochimique et saisonnier**.

Une étude Optuna de 201 essais a été conduite le 02/08 : elle gagne +5,25 % sur la validation
interne **spatiale**, et se trouve donc suspecte par construction. Elle est conservée comme
**démonstration** que régler sur cet axe est contre-productif, jamais comme source de réglage.

Comment s'en servir
-------------------
    from aq.models.moteur import modele_mos

    m = modele_mos()                    # le réglage de production
    m = modele_mos(graine=7)            # une autre graine, pour un ensemble
    m = modele_mos(n_estimators=3000)   # une variante, en le DISANT

Toute variante passée en argument doit apparaître dans le rapport qui en découle : un chiffre
produit par un modèle non nommé n'est pas attribuable.
"""

from __future__ import annotations

# Le réglage de production, tel qu'il tourne dans `mos._modele` depuis l'origine et tel que
# le double aveugle le désigne comme le meilleur des quatre testés.
DEFAUT: dict = {
    "n_estimators": 400,
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_child_samples": 200,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
}

# Nombre de fils par ajustement. ⚠️ **Pas `-1`.** Mesuré le 02/08 : sur 90 000 lignes × 57
# variables, LightGBM plafonne à ~1,5 cœur quel que soit `n_jobs` — le jeu est trop petit
# pour que la synchronisation des fils soit rentable. Et trois ajustements en `n_jobs=-1`
# lancés ensemble sur 32 cœurs se sont effondrés d'un ordre de grandeur, la contention
# portant sur la bande passante mémoire. La parallélisation utile est **entre** les
# ajustements, pas dedans.
N_JOBS = 8


def modele_mos(graine: int = 0, n_jobs: int = N_JOBS, **variantes):
    """Le modèle du projet. Toute variante doit être nommée dans le rapport qui en découle."""
    from lightgbm import LGBMRegressor

    return LGBMRegressor(random_state=graine, n_jobs=n_jobs, verbose=-1,
                         **(DEFAUT | variantes))


def fabrique_mos(n_jobs: int = N_JOBS, **variantes):
    """Une fabrique compatible avec `mos.ajuster_par_stations_exclues(fabrique_modele=…)`."""
    def _f(graine: int = 0):
        return modele_mos(graine=graine, n_jobs=n_jobs, **variantes)
    return _f
