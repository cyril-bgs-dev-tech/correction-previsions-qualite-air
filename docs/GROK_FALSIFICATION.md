# GROK — Falsification thèse « gain quand CAMS dérive » (30 juillet 2026)

Prompt 2 de `docs/PROMPT_FALSIFICATION.md`. Posture : **recruteur ATMO Occitanie**. Verdict d'abord, 1–3 lignes.

**Thèse candidate :** la correction a appris la signature des défaillances CAMS → gagne quand CAMS dérive, nuit quand CAMS est juste ; règle : ne pas corriger à la baisse si CAMS annonce déjà un dépassement. Preuves : r=+0,913 ; pire mois stable (nov. 2023) ; 26/07/2026 (CAMS 49,6 / obs 46,8 / correctif 36,6).

---

**1. Plus fort.**  
Un dossier +30 % sans mécanisme est un benchmark ; avec une limite mesurée et une règle de bascule, c'est un début de **gouvernance de modèle** — ce que j'achète vraiment.

**2. Lucidité — si les trois preuves tiennent un audit de 20 minutes.**  
Habillage seulement s'il n'a pas testé l'artefact « plus l'erreur CAMS est grande, plus tout correctif gagne » (régression vers la moyenne). Tant qu'il n'a pas tranché ça devant moi, je garde un doute, pas un rejet.

**3. Je retiens la lucidité, j'encaisse le « nuit ».**  
« Nuit » sans filet = alerte rouge embauche. « Nuit *ici*, donc je me tais *comme ça* » = exactement le profil que je peux mettre près d'une publication quotidienne.

**4. Utilisable comme **garde-fou v0**, trop grossière comme doctrine.**  
Chez moi : OK en filet d'épisode (ne pas casser un signal de dépassement déjà là). Insuffisant seul — il me faut aussi le cas « CAMS juste *sous* le seuil » et le cas « CAMS faux haut ». Une règle mono-sens ne couvre pas mon matin.

**5. Celui **avec** la thèse.**  
Les +30 % sans elle, je les classe « stagiaire ML brillant ». Avec elle, je vois quelqu'un qui comprend qu'un post-traitement est un **risque opérationnel**, pas un trophée.

**6. Les deux : peur sur le fond, confiance sur la personne.**  
Peur = ce correctif en prod aveugle le 26/07 m'aurait **sous-alarmé** un jour d'alerte PM. Confiance = il l'a trouvé sur un épisode réel public et l'écrit en gros : rare, et non négociable pour travailler avec moi.

**7. En faire une **politique d'abstention versionnée**, pas une slide de thèse.**  
Journal : jour × CAMS × correctif × obs × décision (corriger / brut / expertise). Réévaluer après chaque upgrade CAMS. La thèse devient une **procédure**, pas un papier.

**8. « Hors des mois où CAMS se dégrade et hors du 26/07, sur les jours où |biais CAMS| est petit, ton correctif améliore-t-il encore le CSI / le biais de pic — oui ou non, chiffre ? »**  
Si le gain s'évapore quand CAMS est déjà bon, la thèse tient et le produit est un *filet de dérive*. Si le gain reste, sa thèse est trop belle et il sur-raconte. Bonus : « montre-moi la même règle sur O₃ estival, pas seulement PM. »

---

## Verdict recruteur (hors questions)

| | |
|--|--|
| Thèse dans le dossier | **À garder**, en première moitié, pas en annexe honteuse |
| Condition | Une réfutation tentée de la régression vers la moyenne + règle d'abstention **testée** (avant/après sur 26/07 et un épisode O₃) |
| Risque si mal joué | Transformer un bon ingénieur en essayiste ; la direction retient « son modèle nuit » |
| Ce que je veux entendre en clôture | « Voici quand je rends le brut — et le 26/07, avec la règle, je ne passe plus à 36,6 » |
