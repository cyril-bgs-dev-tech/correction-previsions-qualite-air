# Audit de finition — tout ce qu'un recruteur verra sur GitLab

**Échéance : 22 août 2026.** Ce n'est pas une revue d'architecture ni une re-analyse des
résultats — trois audits l'ont déjà fait. C'est le **dernier passage avant envoi** : ce qu'un
lecteur voit, dans quel ordre, et ce qui le ferait tiquer.

Tout ce que tu signales doit être **corrigeable en quelques heures**. Une remarque juste mais
qui demande une semaine ne sert à rien aujourd'hui — mets-la dans la section « après
l'échéance ».

---

## 1. Ce qui change par rapport aux briefs précédents : **tu peux réellement ouvrir les pages**

Les audits précédents embarquaient le contenu en dur, parce que le compte GitHub rendait 404
aux visiteurs non connectés. **Ce n'est plus le cas ici** : les six dépôts ci-dessous sont
publics sur GitLab et servis **sans compte ni session**. Vérifié le 21/08 par requête anonyme.

| dépôt | ce que c'est |
|---|---|
| [correction-previsions-qualite-air](https://gitlab.com/cyril.bgs.dev/correction-previsions-qualite-air) | **le projet phare** — post-traitement appris des prévisions CAMS |
| [Portfolio](https://gitlab.com/cyril.bgs.dev/Portfolio) | la vitrine : une fiche par projet |
| [anomaly_tabular](https://gitlab.com/cyril.bgs.dev/anomaly_tabular) | recherche — composition de détecteurs, banc ADBench |
| [anomaly_tsad](https://gitlab.com/cyril.bgs.dev/anomaly_tsad) | le même sujet en séries temporelles, banc TSB-AD |
| [projets_Master_1](https://gitlab.com/cyril.bgs.dev/projets_Master_1) | 10 projets de formation, notebooks avec sorties |
| [projets_Master_2](https://gitlab.com/cyril.bgs.dev/projets_Master_2) | 7 projets de formation |

**Ouvre-les vraiment.** Chaque constat doit citer une **URL exacte** et une **ligne ou un
titre de section que je peux retrouver**.

> ⚠️ **Le piège des audits précédents, et il s'est produit deux fois.** Des défauts réels ont
> été signalés à des chemins **inventés** — `portfolio_project.qmd`,
> `assets/qa_gain_decomposition.svg`. Aucun des deux n'existe. Le constat était juste, la
> référence fausse, et j'ai perdu du temps à chercher. **Si tu n'as pas ouvert le fichier, dis
> que tu ne l'as pas ouvert.** Un « je n'ai pas pu vérifier » vaut mieux qu'une référence
> plausible.

---

## 2. Ce qui vient d'être corrigé — ne le re-signale pas

Contrôlé mécaniquement le 21/08, tout est vert :

- **liens** : 29 liens externes testés en anonyme — 20 vivants, 0 mort inattendu. Les 8 morts
  connus pointent vers un compte GitHub suspendu (recours en cours), c'est un état subi ;
- **liens relatifs et images** : 0 cassé, 14 images référencées, 0 manquante ;
- **plis `<details>`** : sept fiches repliaient 68 à 87 % d'elles-mêmes derrière « Détails
  techniques » — dépliés, un seul subsiste et il est légitime ;
- **diagrammes Mermaid** : les deux ont désormais un équivalent textuel ;
- **cohérence des chiffres** : 28 contrôles sur le dossier, 0 écart ; figures recalculées
  depuis leurs artefacts ;
- **métadonnées des dépôts** : les six ont une description ; un dépôt doublon a été retiré de
  la vue publique.

---

## 3. La question ouverte, et c'est la principale — **`docs/` expose 134 fichiers**

Dans le dépôt phare, `docs/` est public et contient :

| | |
|---|---|
| **53** | réponses d'autres IA (`GPT_R3` … `GPT_R17`, `REPONSES_GROK`, `réponse_KIMI_K3`…) |
| **48** | prompts que je leur ai envoyés (`PROMPT_GPT_*`, `BRIEF_*`, `MISSION_*`) |
| 14 | documentation de fond — celle-là est légitime |
| 5 | plans de travail internes (`TRENTE_ACTIONS`, `PLAN_10_ACTIONS_EXTREMES`) |
| 1 | `CRITIQUE_ADVERSE.md` — une critique adverse du projet |

Et à la racine, `CLAUDE.md` : **1 200 lignes qui consignent chaque erreur commise sur ce
projet**, avec son coût en heures.

**La question que je te pose, et je veux une position tranchée, pas une liste d'options :**

> Un recruteur d'AASQA qui ouvre `docs/` et y trouve 101 fichiers de dialogue avec GPT, Grok
> et Kimi — **est-ce que ça renforce ou ça dessert ?**

Argumente dans les deux sens puis **choisis**. Et distingue bien :

- les **prompts et réponses d'IA** — méthode de travail assistée, transparente ;
- `CLAUDE.md` — un registre d'erreurs et de garde-fous, qui peut se lire comme une rigueur
  d'ingénierie **ou** comme un aveu ;
- `CRITIQUE_ADVERSE.md` — une critique du projet, publiée par son auteur.

Si tu recommandes de retirer, dis **lesquels précisément** et **ce qu'on écrit à la place**
pour que la méthode reste visible sans que le dossier ressemble à un journal de bord.

---

## 4. Ce que je te demande de regarder, dans cet ordre

### ① Les trente premières secondes

Pour **chacun des six dépôts** : un lecteur qui arrive sur la page d'accueil et ne lit que le
premier écran — que comprend-il ? Peut-il dire **ce que fait le projet** et **pourquoi c'est
crédible** ? Si non, dis quelle phrase manque, et où.

### ② La cohérence entre dépôts

Six dépôts, un seul candidat. Est-ce qu'ils se ressemblent assez pour former un ensemble ?
Est-ce qu'ils se renvoient les uns aux autres quand il le faut ? Est-ce qu'un même fait y
porte deux valeurs ?

### ③ Les culs-de-sac

Un lien qui promet et ne livre pas, une section « à venir », un renvoi vers un endroit vide.
Les liens **morts** sont déjà contrôlés — je parle des liens **vivants qui déçoivent**.

### ④ Le français et le ton

Fautes, anglicismes, formulations qui sonnent faux. Et surtout : **une phrase qui promet plus
que ce que la mesure autorise**. Ce projet tient à ce que chaque chiffre porte son protocole ;
signale toute affirmation où le protocole manque.

### ⑤ Ce qui manque et qu'on ne voit pas

La question la plus utile : qu'est-ce qu'un recruteur **s'attendrait à trouver** et ne trouve
pas ? Licence, instructions d'installation, exemple d'exécution, capture d'écran, contact ?

---

## 5. Format de réponse imposé

```
## ① Ce que j'ai réellement ouvert
   - liste des URL visitées, et celles que je n'ai PAS pu ouvrir

## ② Défauts, par gravité
   🔴 bloquant  · à corriger avant envoi
   🟠 gênant    · corrigeable en moins d'une heure
   🟡 mineur    · si le temps le permet
   Pour chacun : URL exacte · citation du texte fautif · correction proposée, rédigée

## ③ La question de docs/ — ma position
   (tranchée, argumentée, avec la liste des fichiers concernés)

## ④ Ce que je n'ai pas pu vérifier
   (obligatoire, même si la liste est vide — dis-le alors explicitement)

## ⑤ Après l'échéance
   (les remarques justes mais trop coûteuses pour aujourd'hui)
```

**Ne reformule pas ce brief, n'écris pas de préambule.** Commence directement par ①.
