# GROK R4 — Protocole 18 mois, piège d'échantillon, trafic statique (30 juillet 2026)

Salve courte (prompt `docs/PROMPTS_EXTERNES.md` §2). **Jugement** ≠ **publié**. Chiffres repris du prompt candidature — **à recoller** aux rapports une fois le recalcul 18 mois terminé.

**Contexte figé par le prompt (non revérifié ici) :** 18 mois d'obs appariées (corrigé fuite regex bi-mensuelle, +35 % de paires) ; archive CAMS 24 mois (2023-07 → 2026-06) ; 2025-02…2025-07 sans obs ; barre CAMS brut J+1 France ~4,0 M paires — NO₂ RMSE 12,87 / O₃ 16,97 / PM2.5 5,86 ; rappel « Mauvais » ~0,47 vs ~0,24 CAMS ; échéance candidature **22/08/2026** (23 j).

---

## 1. Découpage d'évaluation — verdict

| Option | Démontre | Coût effectif test |
|--------|----------|-------------------|
| **(a)** validation temporelle glissante multi-plis | Stabilité au fil des saisons | ~1/K de l'effectif par pli ; fragile si un pli capture seul un épisode extrême |
| **(b)** coupe inter-annuelle franche (train 2023-2024, test 2025) | Généralisation à une année non vue | ~6–8 mois de test ; trou d'obs 2025-02…07 → été partiellement amputé |
| **(c)** double aveugle spatial **et** temporel | Transfert station/territoire *et* temps | Produit des deux retenues — souvent trop peu de paires Occitanie×fenêtre pour les queues |

**Principal : (b).** Un ingénieur AASQA lit d'abord « année tenue hors entraînement ».

**Secondaire : (a) à 3–4 plis** sur la fenêtre complète — pour montrer que (b) n'est pas un coup de chance saisonnier.

**Pas de (c) en 23 jours.**

**Écart avec R3 :** R3 (29/07) recommandait train ~2023-07→2024-06 / test 2024-07→2025-06 sur archive annoncée jusqu'à 2025-06. Ici l'archive va à 2026-06 et les obs couvrent 18 mois jusqu'à mi-2026 : la coupe « test = 2025 calendaire » reste le récit le plus lisible, à condition d'**afficher explicitement** les mois 2025 sans obs (règle projet 4 bis).

---

## 2. Piège du changement d'échantillon (11 → 18 mois)

**Attendu en dégradation :** rappel / CSI des jours « Mauvais » (et souvent biais O₃ estival) — second cycle saisonnier + mois plus durs, fin de l'optimisme sur un sous-échantillon chanceux.

**Signe de fuite si amélioration suspecte :** RMSE (ou R²) qui **s'améliore nettement sur un jeu de test figé** sans changement de protocole → fuite temporelle (feature dérivée du futur, agrégats station calculés sur toute la période, split laissant des jours voisins des deux côtés).

---

## 3. Trafic statique — réponse opposable

**Réponse juste :** ce n'est pas une prévision du trafic horaire — c'est un **biais spatial conditionnel** (niveau moyen / régime local) que CAMS à ~8 km lisse. Le modèle apprend *où* corriger l'erreur systématique, pas *quand* le bouchon arrive.

**Preuve courte (à faire, pas à affirmer) :** même split temporel ; ablation avec vs sans `importance` BD TOPO ; métriques **par type de station** (trafic / fond / rurale) + carte des résidus moyens. Gain concentré trafic/fond urbain = signal utile.

**Seuil mémorisation :** dès qu'un ID station (ou proxy unique : coordonnées brutes + trafic collinéaires) bat un hold-out **spatial** (stations Occitanie jamais vues, ou leave-region-out).

---

## 4. Actualité juillet 2026

| Statut | Contenu |
|--------|---------|
| **Vu dans cette session** | Rien d'opposable — pas de consultation bulletins ATMO Occitanie / LCSQA juillet 2026 |
| **Supposé seulement** | Saison ozone typique + risque PM (saharien / feux) — **ne pas écrire comme fait** |

**Action avant rédaction candidature :** passe manuelle atmo-occitanie.org + lcsqa.org (épisodes, bilans). R3 listait déjà des épisodes O₃ caniculaires début juillet 2026 — **revérifier** plutôt que recopier.

---

## Seule chose à couper des 23 jours

Toute **reproduction de la spatialisation indice ATMO / comparaison EPCI**. Rester en station, assumer l'écart, livrer le protocole **(b)+(a)** et les ablations trafic.

---

## Points à coller au dépôt (avant livrable)

- [ ] Barre CAMS 18 mois (RMSE NO₂/O₃/PM2.5, n paires) = chiffres `reports/CAMS_BENCHMARK.md` après recalcul
- [ ] « 11 → 18 mois » et +35 % paires documentés dans le rapport qui annonce la couverture (cf. règle 4 bis)
- [ ] Split (b) : lister les mois test absents d'obs, ne pas les déduire du nom de fichier
- [ ] Ablation `importance` BD TOPO : pas encore dans cette note — à produire sous (b)
