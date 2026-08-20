# Audit du portefeuille GitHub — brief de relecture externe

*Rédigé le 20/08/2026. Réponse attendue : **un fichier `.md`**, format imposé au § 7.*

---

## 0. En une phrase

**Trouve tout ce qui, dans ce portefeuille, nuit à une communication simple, efficace et propre — et dis-le avec l'emplacement exact et le remplacement exact.**

---

## 1. Ce que je te demande

Ce portefeuille est la vitrine publique d'un data scientist en recherche de poste. Son unique fonction est de convaincre en quelques minutes un lecteur qui, la plupart du temps, **n'est pas spécialiste** et ne lira pas tout.

Trois axes, dans cet ordre de priorité :

1. **Communication** — est-ce compréhensible sans connaître le sujet ? Y a-t-il du jargon non expliqué, des phrases trop longues, des paragraphes qu'on saute ?
2. **Présentation des résultats** — les chiffres sont-ils lisibles, comparables, correctement cadrés ? Un chiffre sans son point de comparaison ne dit rien.
3. **Propreté** — cohérence entre les pages, rendu correct, rien de cassé, rien d'inachevé, rien qui se contredise.

Sois **impitoyable et concret**. Je préfère trente défauts précis à trois conseils généraux.

---

## 2. 🔴 Ne navigue pas — le compte GitHub rend 404 aux anonymes

**C'est le point le plus important de ce brief.** Si tu essaies d'ouvrir `github.com/cyril-bgs-dev-tech`, tu obtiendras **404**, et tu conclurais à tort que rien n'existe.

Mesuré, quatre requêtes anonymes, quatre 404 : le profil, l'API `users/`, chaque dépôt, et le site `github.io`. Avec le jeton du propriétaire, tout existe et est marqué `public`. C'est un **blocage au niveau du compte** — vraisemblablement un signalement automatique de GitHub, en cours d'appel.

> **Conséquence pour toi : tout le contenu est reproduit intégralement au § 8 de ce document.** N'infère rien depuis le web, ne cite rien de mémoire. Une revue précédente sur ce projet a été juste 3 fois sur 3 sur ce qu'elle avait sous les yeux, et fausse sur ce qu'elle citait de mémoire. La différence n'était pas la compétence.

**Conséquence pour l'audit lui-même** : puisque le site Quarto (`github.io`) n'a **jamais** été construit, le rendu qui compte aujourd'hui est celui des **`README.md` par GitHub**. Pondère en conséquence : un défaut visible sur GitHub est grave, un défaut qui n'apparaîtrait que sur le site Quarto est secondaire.

---

## 3. Le contexte utile

| | |
|---|---|
| **Personne** | Cyril Bourgeois — reconversion armée → commerce → data science (2021-2024) |
| **Cible** | recruteurs et responsables techniques, premier passage souvent non spécialiste |
| **Échéance proche** | une candidature en cours, dossier à rendre le 22/08/2026 |
| **Structure** | 8 dépôts. `Portfolio` est la vitrine : une fiche par projet. 5 fiches ont un dépôt de code, 4 n'en ont pas |
| **Rendu** | GitHub Markdown (aujourd'hui) ; Quarto → GitHub Pages (prévu, jamais construit) |

Les cinq projets : correction de prévisions de qualité de l'air, plateforme MLOps temps réel (*vigilance*), agent LLM de diagnostic (*aegis-rca*), benchmarks de détection d'anomalies (*anomaly_tabular* / *anomaly_tsad*), compétitions Kaggle.

---

## 4. Ce qui compte comme un défaut — pré-enregistré

Classe chaque trouvaille dans **une** de ces familles. Si une trouvaille n'entre dans aucune, dis-le et propose la famille.

| # | famille | exemple de ce que je cherche |
|---|---|---|
| **A** | **Contradiction interne** | deux pages donnent deux valeurs du même fait ; un chiffre de l'accueil ne correspond pas à celui de la fiche |
| **B** | **Jargon non expliqué** | un sigle, une métrique ou une méthode employée sans que le lecteur non spécialiste puisse suivre |
| **C** | **Chiffre sans cadre** | un pourcentage sans base de comparaison, un rang sans dénominateur, une performance sans protocole |
| **D** | **Rendu cassé sur GitHub** | syntaxe non supportée affichée telle quelle, tableau qui déborde, badge muet, lien mort |
| **E** | **Inachevé ou creux** | section vide, promesse non tenue, page qui n'apporte rien, remplissage générique |
| **F** | **Longueur / structure** | paragraphe qu'on saute, information enterrée, ordre qui dessert, redondance entre pages |
| **G** | **Ton** | auto-dévalorisation, superlatif invérifiable, formule creuse, familiarité déplacée |
| **H** | **Cohérence de forme** | typographie, majuscules, décimales, unités, nommage, emoji incohérents d'une page à l'autre |

**Pour chaque défaut, la question à te poser** : *qu'est-ce qu'un recruteur pense en lisant ça, et est-ce ce qu'on voulait qu'il pense ?*

---

## 5. Ce qui ne m'intéresse pas

Pour ne pas gaspiller ton effort :

- ❌ **les conseils génériques** — « ajoutez des visuels », « soignez le SEO », « racontez une histoire ». Si tu le recommandes, dis **où**, **quoi exactement**, et **à la place de quoi** ;
- ❌ **les réécritures complètes** — je veux des correctifs ciblés que je peux appliquer un par un ;
- ❌ **les remarques sur le fond scientifique** des projets — c'est audité ailleurs, par d'autres, avec les données ;
- ❌ **ce qui découle du blocage du compte** — badges dynamiques muets, liens `github.io` en 404, absence du site. C'est connu, c'est traité, et ça se résoudra d'un coup ;
- ❌ **les suggestions qui ne font qu'ajouter** — le portefeuille doit rester court. Si tu proposes un ajout, dis ce qu'il **remplace**.

---

## 6. Ce qui vient d'être corrigé — ne le re-signale pas

Ces défauts ont été trouvés et corrigés entre le 18 et le 20/08/2026 :

- dates de « dernière mise à jour » périmées sur 11 pages ; « OpenClassRooms » → OpenClassrooms ; « Supelec » → Supélec ;
- nombre de projets du Master 2 : 8 annoncé, **7** mesuré depuis deux sources concordantes ;
- « algorithmes de fuzzy matching » et « score > 85 % » retirés (non employés, non sourcés) ;
- expérience DELTAMU sans impact ni retour, et absente de la page d'accueil du site ;
- deux badges dynamiques affichant « repo not found » ; un badge dont le tiret coupait le libellé en deux ;
- colonnes de « Faits Marquants » alignées sur leur milieu au lieu du haut ;
- volume du corpus qualité de l'air : « 213 M d'enregistrements » sans aucune source, corrigé à **28 M** ;
- carte du projet qualité de l'air réécrite pour un lecteur non spécialiste.

**Un défaut déjà connu, non encore corrigé** — inutile de le redécouvrir, mais dis-moi si tu vois pire que ce que j'en pense : **7 des 9 fiches projet contiennent de la syntaxe Quarto (`::: {.panel-tabset}` et `:::`) que GitHub affiche telle quelle**, en clair, au milieu de la page.

---

## 7. Le format de réponse attendu

**Un fichier `.md`**, structuré ainsi, trié par gravité décroissante :

```markdown
## Synthèse — les 5 choses à corriger en premier
(cinq lignes, pas plus)

## Défauts

### [gravité] famille — titre court
- **Où** : `fichier:ligne` (ou section nommée)
- **Ce qui est écrit** : citation exacte
- **Le problème** : une à trois phrases
- **Ce qu'un lecteur en conclut** : une phrase
- **Remplacement proposé** : le texte exact à mettre à la place
- **Ce que ça retire** : ce qu'on supprime en échange (ou « rien »)
```

Gravité : `🔴 bloquant` (nuit dès la première lecture) · `🟠 important` · `🟡 confort`.

**Trois exigences de méthode :**

1. **Cite exactement.** Un défaut sans citation littérale n'est pas actionnable.
2. **Ne rapporte que ce que tu as sous les yeux au § 8.** Si tu supposes, dis « hypothèse à vérifier ».
3. **Termine par une section « Ce qui est bien »** — trois à cinq points, sincères. J'ai besoin de savoir ce qu'il ne faut pas casser en corrigeant le reste.

---

## 8. Le contenu intégral

Ce qui suit est le contenu exact des fichiers, tel qu'il est publié. Les `index.qmd` des dossiers de projet ne contiennent qu'une ligne d'inclusion (`{{< include README.md >}}`) et sont omis.


---

### 📄 `README.md`

*349 lignes · 1476 mots*

````markdown
<div align="center">

# 🚀 Cyril BOURGEOIS

### Data Scientist | MLOps Engineer | Problem Solver

[![Portfolio](https://img.shields.io/badge/Portfolio-en%20ligne-2563eb?style=for-the-badge&logo=quarto)](https://cyril-bgs-dev-tech.github.io/Portfolio/)
![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/cyril-bourgeois/)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail)](mailto:cyril.bgs.dev.tech@gmail.com)
[![Kaggle](https://img.shields.io/badge/Kaggle-Top%201%25-20BEFF?style=for-the-badge&logo=kaggle)](https://www.kaggle.com/cyrilbourgeois)

---

</div>

## 🎯 À Propos

> *"Transformer des données complexes en décisions business impactantes"*

Data Scientist passionné avec **double compétence modélisation + production**, spécialisé en détection d'anomalies et systèmes MLOps temps réel. Mon parcours atypique (armée → commerce → data science) m'a apporté une perspective unique : **rigueur technique + sens du business + communication efficace**.

### 🏆 Faits Marquants

<table>
<tr>
<td width="33%" valign="top">
  
**🥇 Kaggle Top 1%**
- 35+ compétitions
- 3 top 1% mondial
- Meilleur rang : #14/3022

</td>
<td width="33%" valign="top">
  
**🔬 Benchmarks SOTA**
- ADBench : 47 datasets
- TSB-AD : 870 séries U + 200 M
- Reproductions exactes validées

</td>
<td width="33%" valign="top">
  
**⚙️ MLOps Temps Réel**
- DAG 9 workers, 4 réplicas
- Dashboard 40+ pages RASCI
- Observabilité Prometheus/Grafana

</td>
</tr>
</table>

---

## 💼 Expérience Professionnelle

<div align="center">

### 🏭 Data Scientist - MICHELIN (Alternance)
*Février 2023 - Février 2024 · 39h/semaine, 4 jours/5 en entreprise*

</div>

**POC Parsing/Matching de Données Complexes — Niveau Continental**

🎯 **Mission** : Réalisation d'un POC de parsing/matching de données complexes, niveau continental

✨ **Réalisations** :
- 🎯 Augmentation considérable du taux de détection des correspondances
- 🧹 Nettoyage et qualité des données, analyses spécifiques autour du pricing niveau mondial
- ✅ Tests de non régression

💡 **Impact** :
- Vitesse d'exécution et résultats jugés excellents d'après plusieurs Product Owners
- Accélération considérable des temps de traitement par rapport au processus manuel
- POC mené jusqu'au bout et préparé pour la mise en production, adapté et utilisé par les équipes par la suite

🗣️ **Feedback** :
> *"Implication et capacité constante à se challenger. Force de proposition, assidu dans les missions. POC parsing/mapping mené avec succès."*  
> — Antoine DANIEL LAMAZIERE (PO) + Architecte Data

---

<div align="center">

### 🧪 Data Scientist / ML Engineer - DELTAMU (CDD)
*Octobre 2024 - Octobre 2025*

</div>

**Recherche en Détection d'Anomalies — Capteurs Industriels (Pharma)**

🎯 **Contexte** : Industrie pharma, plusieurs centaines de capteurs

✨ **Missions** :
- 🔬 Tests de recherche en clustering et détection d'anomalies
- 📊 Analyse et interprétation d'insights et de cycliques
- 🧠 Création d'un algorithme de niveau recherche validé par le responsable scientifique

💡 **Impact** :
- 📈 Analyses statistiques avancées sur ensemble de bon fonctionnement
- ⚡ Cœur calculatoire haute vitesse optimisé en **Rust**
- 🔍 Augmentation colossale de la capacité de compréhension des données

🗣️ **Feedback** :
> *"Réelle passion pour la data science et les algorithmes d'IA. Investissement dans les missions. Contribution active au produit logiciel."*  
> — Nuno DOS REIS, Président, DELTAMU

---

## 🎓 Formation

<div align="center">

| Master 2 - Data Scientist | Master 1 - Data Analyst |
|:---:|:---:|
| **OpenClassrooms + Centrale Supélec** (2024) | **OpenClassrooms + ENSAE** (2022) |
| 7 projets validés | 10 projets validés |
| Alternance Michelin (12 mois) | — |
| Deep Learning, NLP, Time Series | ML classique, SQL, BI |

</div>

---

## 🛠️ Stack Technique

<div align="center">

### 🐍 Langages & Frameworks
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Rust](https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-4479A1?style=for-the-badge)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

### 📊 Machine Learning & IA
![XGBoost](https://img.shields.io/badge/XGBoost-FF6B6B?style=for-the-badge)
![LightGBM](https://img.shields.io/badge/LightGBM-007ACC?style=for-the-badge)
![RealMLP](https://img.shields.io/badge/RealMLP-6E56CF?style=for-the-badge)
![Modèles physiques](https://img.shields.io/badge/Mod%C3%A8les%20physiques-0EA5E9?style=for-the-badge)
![LLMs](https://img.shields.io/badge/LLMs-8B5CF6?style=for-the-badge)
![Modèles pré-entraînés](https://img.shields.io/badge/Mod%C3%A8les%20pr%C3%A9--entra%C3%AEn%C3%A9s-F59E0B?style=for-the-badge)
![CUDA](https://img.shields.io/badge/CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

### 🤖 LLMs utilisés
![Claude](https://img.shields.io/badge/Claude-D97757?style=for-the-badge&logo=claude&logoColor=white)
![ChatGPT](https://img.shields.io/badge/ChatGPT-10A37F?style=for-the-badge)
![Grok](https://img.shields.io/badge/Grok-000000?style=for-the-badge&logo=x&logoColor=white)
![Kimi K3](https://img.shields.io/badge/Kimi%20K3-1E293B?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white)
![Mistral](https://img.shields.io/badge/Mistral-FA520F?style=for-the-badge&logo=mistralai&logoColor=white)

### ⚡ Agentic
![Claude Code](https://img.shields.io/badge/Claude%20Code-D97757?style=for-the-badge&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-412991?style=for-the-badge)
![OpenCode](https://img.shields.io/badge/OpenCode-0F172A?style=for-the-badge)

### ⚙️ MLOps & Infrastructure
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)

### 📈 Visualisation & BI
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-E97627?style=for-the-badge&logo=tableau&logoColor=white)
![PowerBI](https://img.shields.io/badge/PowerBI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge)

</div>

---

## 🚀 Projets Phares

### 🌬️ [Correction apprise des prévisions de qualité de l'air](projets_Qualite_Air/)
**Apprendre l'erreur du modèle européen, et la retirer** — 36 mois, 28 M de mesures horaires, 4 polluants

<div align="center">

![Protocole](https://img.shields.io/badge/Protocole-Double%20aveugle-2563eb?style=for-the-badge)
![NO2](https://img.shields.io/badge/NO%E2%82%82-%E2%88%9239%2C6%20%25%20d'erreur-10B981?style=for-the-badge)
![Stations](https://img.shields.io/badge/Stations-438-8B5CF6?style=for-the-badge)
![Sources](https://img.shields.io/badge/Sources-CAMS%20%7C%20GEOS--CF%20%7C%20ERA5-F59E0B?style=for-the-badge)

</div>

✨ **Highlights** :
- 🎯 **Prévoir là où personne ne mesure** : aucune observation du lieu corrigé n'entre dans le modèle — et il est testé sur des stations *et* des mois qu'il n'a jamais vus
- 📉 **−39,6 % d'erreur sur le NO₂**, −20,2 % sur les PM10, −17,9 % sur l'ozone, −11,8 % sur les PM2,5, face à la prévision européenne brute
- 📅 **En 2030 l'Europe divise ses seuils par deux** : à pollution inchangée, les stations en dépassement passent de **6 à 109** — et 4 départements d'Occitanie n'ont aucune station pour le constater
- ✅ **Assez bon pour servir en réglementaire&nbsp;?** Le critère européen de qualité est atteint sur 41,4 % des stations NO₂ avec la prévision brute, **96,2 %** après correction
- 🔍 **Les limites sont publiées comme les résultats** : 3 épisodes de pollution réels détectés sur 33 — l'observation directe elle-même n'en attrape que 21, et le produit officiel 1
- 💻 **Code** : [github.com/cyril-bgs-dev-tech/correction-previsions-qualite-air](https://github.com/cyril-bgs-dev-tech/correction-previsions-qualite-air)

---

### 🔧 [Système MLOps Temps Réel](vigilance/)
**Détection d'anomalies industrielle** - 1 200+ heures

<div align="center">

![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-2563eb?style=for-the-badge)
![Workers](https://img.shields.io/badge/Workers-9%20%C3%97%204%20r%C3%A9plicas-10B981?style=for-the-badge)
![Dashboard](https://img.shields.io/badge/Dashboard-40%2B%20pages-8B5CF6?style=for-the-badge)
![Observabilité](https://img.shields.io/badge/Observabilit%C3%A9-Prometheus%20%7C%20Grafana-F59E0B?style=for-the-badge)

</div>

✨ **Highlights** :
- 🏗️ DAG event-driven : 9 workers, barrières Redis atomiques, DLQ, reprise après crash
- 🤖 3 canaux décorrélés (IsolationForest + Ridge temporel + PCA séquentiel) fusionnés par XGBoost + détection de nouveauté
- 🎫 Cycle de vie d'alarme en épisode unique : hystérésis, escalade, SLA par sévérité
- 📊 Dashboard Streamlit 40+ pages avec rôles RASCI
- 🔭 Observabilité par étape du DAG : Prometheus + Grafana + cAdvisor
- 💻 **Code** : [github.com/cyril-bgs-dev-tech/vigilance](https://github.com/cyril-bgs-dev-tech/vigilance)

---

### 🕵️ [Aegis-RCA — Agent de Diagnostic de Causes Racines](aegis-rca/)
**Prototype de recherche actif** — extension de vigilance, 3 jours de développement (juillet 2026)

✨ **Highlights** :
- 🤖 Agent LLM local (Qwen3.6:27B) qui investigue les incidents ouverts par vigilance : contexte métriques, RAG sur procédures, diagnostic + recommandation validés par un humain
- 🔬 Décisions d'architecture confrontées à des avis externes (Gemini, ChatGPT) **puis vérifiées par des bancs de mesure réels** — une erreur de méthodologie détectée et corrigée en cours de route, documentée telle quelle
- 🛡️ Sandbox d'auto-correction durci (Docker jetable, réseau isolé, cgroups) — 1 succès réel mesuré
- 💻 **Code** : [github.com/cyril-bgs-dev-tech/aegis-rca](https://github.com/cyril-bgs-dev-tech/aegis-rca)

---

### 🔬 [Recherche Compositionnelle - Anomaly Detection](anomaly_tabular/)
**Composer les SOTA et router par domaine — ADBench (tabulaire) + TSB-AD (séries temporelles)**

<div align="center">

![Corpus](https://img.shields.io/badge/Corpus-502%20datasets%20%C2%B7%2020%20domaines-2563eb?style=for-the-badge)
![PaAno](https://img.shields.io/badge/PaAno%20(ICLR'26)-%231%20des%202%20volets%20TSB--AD-10B981?style=for-the-badge)
![Repro](https://img.shields.io/badge/Reproductions-exactes%20valid%C3%A9es-8B5CF6?style=for-the-badge)
![Métrique](https://img.shields.io/badge/VUS--PR-point--adjust%20banni-F59E0B?style=for-the-badge)

</div>

✨ **Highlights** :
- 🎯 Démarche : reproduire l'ancre (égalités exactes : Sub-PCA 0.4234, Sub-KNN 0.3501) → monter les SOTA → **caractériser les domaines** → router
- 🥇 PaAno (ICLR 2026) intégré à TSB-AD et certifié : **#1 des volets U et M** (0.58 / 0.46 VUS-PR vs 0.42 / 0.31 pour les leaders publiés)
- 📈 Tabulaire : routage par domaine **72.5 AUROC** (préenregistré, p=5×10⁻⁷) vs 69.8 meilleur détecteur unique — oracle à 78.3
- 💡 Leçon : même avec un système SOTA, la composition par domaine ajoute jusqu'à +0.33 VUS-PR localement
- 🔬 Volets : [tabulaire](anomaly_tabular/) · [séries temporelles](anomaly_tsad/) — dépôts : [anomaly_tabular](https://github.com/cyril-bgs-dev-tech/anomaly_tabular) · [anomaly_tsad](https://github.com/cyril-bgs-dev-tech/anomaly_tsad)

---

### 🏆 [Compétitions Kaggle - Top 1% Mondial](projets_Competitions/)
**35+ compétitions** | **3 top 1%**

<div align="center">

| Compétition | Rang | Top % |
|:---|:---:|:---:|
| 🏎️ Prediction F1 Pit Stop | #14 / 3 022 | 0.5% |
| 🌾 Predicting Irrigation Need | #32 / 4 315 | 0.7% |
| 🎧 Predict Podcast Listening | #20 / 3 310 | 0.6% |
| 🏠 Regression California Housing | #14 / 689 | 2% |

</div>

✨ **Approche** :
- 🔧 Feature engineering intensif (centaines de features)
- 🤝 Ensembling/stacking de modèles diversifiés
- ⚡ Optimisation bayésienne (Optuna)
- 🔬 Veille active (TabM, TabICL2, RealMLP)
- 🤖 La stratégie gagnante se déplace vers l'**agentique** — des systèmes d'agents qui explorent et sélectionnent les pistes en autonomie
- 🏅 **Palmarès vérifiable** : [kaggle.com/cyrilbourgeois](https://www.kaggle.com/cyrilbourgeois/competitions)

---

## 📂 Structure du Portfolio

<div align="center">

```
📦 Portfolio
├── 🎓 projets_Master_1/  # 10 projets Data Analyst
├── 🎓 projets_Master_2/  # 7 projets Data Scientist + Michelin
├── 🏆 projets_Competitions/  # 35+ compétitions Kaggle
├── 🌬️ projets_Qualite_Air/  # Correction apprise des prévisions CAMS
├── 🔧 vigilance/  # Système MLOps temps réel
├── 🕵️ aegis-rca/  # Agent de diagnostic de causes racines
├── 🔬 anomaly_tabular/  # Recherche tabulaire
└── 🔬 anomaly_tsad/  # Recherche time series
```

</div>

---

## 🎯 Ce Que Je Recherche

<div align="center">

### 🚀 Opportunités

</div>

- **Data Scientist** : Projets ML/DL complexes, détection d'anomalies
- **MLOps Engineer** : Mise en production de modèles, systèmes temps réel
- **Research Engineer** : État de l'art, benchmark, nouvelles architectures

### 🌟 Environnement Idéal

- ✅ Équipe technique passionnée et collaborative
- ✅ Problématiques business à fort impact
- ✅ Stack moderne (Python, cloud, MLOps)
- ✅ Culture data-driven et innovation

---

## 📫 Contact

<div align="center">

**📧 Email** : [cyril.bgs.dev.tech@gmail.com](mailto:cyril.bgs.dev.tech@gmail.com)  
**💼 LinkedIn** : [linkedin.com/in/cyril-bourgeois](https://www.linkedin.com/in/cyril-bourgeois/)  
**🏆 Kaggle** : [kaggle.com/cyrilbourgeois](https://www.kaggle.com/cyrilbourgeois)  
**🐙 GitHub** : [github.com/cyril-bgs-dev-tech](https://github.com/cyril-bgs-dev-tech)

</div>

---

<div align="center">

### 🌟 *"Le code ne ment jamais, les commentaires oui"* - Linus Torvalds

*Portfolio construit avec passion | Quarto + GitHub Pages*

![Quarto](https://img.shields.io/badge/Built%20with-Quarto-2563eb?style=for-the-badge)
![GitHub Pages](https://img.shields.io/badge/Deployed%20on-GitHub%20Pages-2088FF?style=for-the-badge&logo=github)
![Open Source](https://img.shields.io/badge/Open%20Source-Yes-10B981?style=for-the-badge)

*Dernière mise à jour : Août 2026*

</div>

````

---

### 📄 `about.qmd`

*232 lignes · 1195 mots*

````markdown
---
title: "À Propos"
---

## 🎯 Mon Parcours

### De l'Armée à la Data Science

**Background atypique** : Reconversion professionnelle de l'armée vers le commerce, puis vers la data science (2021-2024).

Ce parcours m'a apporté :
- **Rigueur et discipline** (armée)
- **Sens du client et communication** (commerce)
- **Compétences techniques** (data science)

---

## 🎓 Formation

### Master 2 - Data Scientist (2023-2024)
**OpenClassrooms + Centrale Supélec**

- 7 projets validés
- Alternance **MICHELIN** (12 mois)
- POC parsing/matching de données complexes
- Deep Learning, NLP, Time Series, Détection d'anomalies

### Master 1 - Data Analyst (2021-2022)
**OpenClassrooms + ENSAE**

- 10 projets validés
- Analyse exploratoire, SQL, ML classique
- Outils : Python, SQL, KNIME, Tableau, Power BI

---

## 💼 Expérience Professionnelle

### Alternance Data Scientist - MICHELIN (Fév 2023 - Fév 2024)
*39h/semaine, 4 jours/5 en entreprise*

**POC Parsing/Matching de Données Complexes — Niveau Continental**

**Missions** :
- Réalisation d'un POC de parsing/matching de données complexes, niveau continental
- Algorithmes de fuzzy matching — augmentation considérable du taux de détection des correspondances
- Nettoyage et qualité des données, analyses spécifiques autour du pricing niveau mondial
- Tests de non régression

**Résultats** :
- Vitesse d'exécution et résultats jugés excellents d'après plusieurs Product Owners
- Accélération considérable des temps de traitement par rapport au processus manuel
- POC mené jusqu'au bout et préparé pour la mise en production, adapté et utilisé par les équipes par la suite

**Feedback** :
> *"Implication et capacité constante à se challenger. Force de proposition, assidu dans les missions. POC parsing/mapping mené avec succès."*
> 
> — Antoine DANIEL LAMAZIERE (PO) + Architecte Data, Michelin

---

### CDD Data Scientist / ML Engineer - DELTAMU (Oct 2024 - Oct 2025)

**Recherche en Détection d'Anomalies — Capteurs Industriels (Pharma)**

**Contexte** : Industrie pharma, plusieurs centaines de capteurs

**Missions** :
- Tests de recherche en clustering et détection d'anomalies
- Analyse et interprétation d'insights et de cycliques
- Création d'un algorithme de niveau recherche validé par le responsable scientifique

---

## 🏆 Réalisations Marquantes

### 1. Compétitions Kaggle - Top 1% Mondial

**35+ compétitions** avec des résultats exceptionnels :

| Compétition | Rang | Top % |
|-------------|------|-------|
| Prediction F1 Pit Stop | #14 / 3 022 | 0.5% |
| Predicting Irrigation Need | #32 / 4 315 | 0.7% |
| Predict Podcast Listening Time | #20 / 3 310 | 0.6% |
| Regression — California Housing | #14 / 689 | 2% |

**Approche** :
- Feature engineering intensif (centaines de features)
- Ensembling/stacking de modèles diversifiés
- Optimisation bayésienne (Optuna)
- Veille active (TabM, TabICL2, RealMLP)

### 2. Recherche - Benchmarks de Reproduction (ADBench & TSB-AD)

**Phase 1 — exploration** (~60 concepts testés depuis papiers 2024-2026, dont le modèle maison MVAD) : riche en leçons, mais méthodologiquement fragile — d'où la phase 2.

**Phase 2 — reproduction rigoureuse (en cours)** :

- **ADBench** : 5 détecteurs classiques reproduits sur 47 datasets, écarts diagnostiqués
- **TSB-AD** : reproductions exactes (Sub-PCA 0.4234, Sub-KNN 0.3501 en VUS-PR), SOTA récents montés sur RTX 5090
- **Rigueur** : VUS-PR primaire, point-adjust banni, validation LODO par source

**Leçons clés de la phase exploratoire** :
- La simplicité bat la complexité
- StandardScaler aussi bon que RobustScaler pour KNN
- L'autoencodeur dégrade les performances (lisse les anomalies)
- Seuil d/n > 0.1 → LOF, sinon → KNN multi-échelle

### 3. Système MLOps Temps Réel

**Projet personnel** - 1 200+ heures de développement

**Architecture** :
- DAG event-driven avec 9 workers (3 réplicas CPU + 1 GPU)
- Redis : queues, barrières de synchronisation atomiques, Dead Letter Queue
- Docker Compose : 14 services (workers, monitoring, jobs de fond)
- 3 canaux de détection décorrélés (IsolationForest + Ridge temporel + PCA séquentiel) + fusion XGBoost

**Dashboard** :
- 40+ pages Streamlit avec rôles RASCI
- Investigation temporelle avancée, replay, analyse contrastive
- Analyse SHAP par event pour interprétabilité

**Observabilité** :
- Prometheus : latence et erreurs par étape du DAG
- Grafana + cAdvisor : pipeline et infrastructure
- SLA opérationnel par sévérité d'alerte (countdown dans le cockpit)

**Points forts défendables** :
- Cycle de vie d'alarme en épisode unique (hystérésis, escalade, concurrence multi-réplicas sans verrou)
- Reprise exacte après redémarrage (état persisté Redis)
- Détecteurs temporels à 0.05-0.12 ms/event, historique partagé entre réplicas

### 4. Aegis-RCA — Agent de Diagnostic de Causes Racines

**Prototype de recherche actif** — extension de vigilance, 3 jours de développement (juillet 2026)

- Agent LLM local (Qwen3.6:27B) : investigue les incidents ouverts par vigilance, corrèle métriques et procédures (RAG), propose diagnostic + recommandation validés par un humain
- Décisions d'architecture confrontées à des avis externes (Gemini, ChatGPT) puis vérifiées par des bancs de mesure réels — une erreur méthodologique détectée et corrigée en cours de route, documentée telle quelle plutôt que masquée
- Sandbox d'auto-correction durci (Docker jetable, réseau isolé, cgroups) : 1 succès réel mesuré
- Statut assumé : prototype, pas un produit fini

---

## 🛠️ Compétences Techniques

### Langages
- **Python** (avancé) : Pandas, NumPy, Scikit-learn, PyTorch
- **SQL** : Requêtes complexes, optimisation

### Machine Learning
- **Classique** : Scikit-learn, XGBoost, LightGBM, CatBoost
- **Deep Learning** : PyTorch, TensorFlow, HuggingFace Transformers
- **Time Series** : Statsmodels, Prophet, LSTM, AnomalyTransformer, TimesNet
- **Anomalies** : Isolation Forest, LOF, Autoencoders, AnomalyTransformer

### MLOps & Infrastructure
- **Containerisation** : Docker, Docker Compose
- **Orchestration** : Redis, DAG event-driven, 9 workers
- **Monitoring** : Prometheus, Grafana, cAdvisor
- **Dashboard** : Streamlit (40+ pages)
- **Stockage** : Parquet, registries JSON versionnés

### Data Engineering
- **DataFrames** : Pandas, Polars, NumPy
- **Feature Engineering** : Temporel, textuel, géographique
- **Versioning** : Git, DVC, SCD2

### Visualisation & BI
- **Python** : Matplotlib, Seaborn, Plotly
- **BI** : Tableau, Power BI, Excel
- **No-Code** : KNIME Analytics Platform

---

## 🎓 Certifications et Diplômes

- **Master 2 Data Scientist** - OpenClassrooms + Centrale Supélec (2024)
- **Master 1 Data Analyst** - OpenClassrooms + ENSAE (2022)
- **Kaggle Competitions** : Top 1% mondial (3 compétitions)

---

## 📚 Centres d'Intérêt

### Veille Technologique
- Papiers de recherche (NeurIPS, ICML, ICLR)
- Nouvelles architectures (Transformers, GNN, Foundation Models)
- Compétitions Kaggle (feature engineering, ensembling)

### Domaines d'Application
- Détection d'anomalies (tabulaire, time series)
- Maintenance prédictive
- Pricing et prévision
- NLP et computer vision

### Open Source
- Contribution à des projets communautaires
- Partage de solutions et notebooks
- Documentation et tutoriels

---

## 📫 Contact

**Email** : [cyril.bgs.dev.tech@gmail.com](mailto:cyril.bgs.dev.tech@gmail.com)  
**GitHub** : [github.com/cyril-bgs-dev-tech](https://github.com/cyril-bgs-dev-tech)  
**LinkedIn** : [linkedin.com/in/cyril-bourgeois](https://www.linkedin.com/in/cyril-bourgeois/)

---

## 📄 Lettres de Recommandation

### Michelin (2023-2024)
**Antoine DANIEL LAMAZIERE** (Product Owner) + **Architecte Data**

> *"Implication et capacité constante à se challenger. Maîtrise des solutions de développement et mise en œuvre. Curiosité et motivation, intérêt pour problématiques Data Business. Force de proposition, assidu dans les missions."*

### OpenClassrooms (2022)
**Hamza Tajmouati** (Head of AI chez Iktos, Mentor OpenClassrooms)

> *"Grande autonomie, proactivité et motivation. Curiosité et recherche constante d'amélioration. Doué en programmation et en compréhension théorique."*

### Deltamu (2026)
**Nuno DOS REIS** (Président)

> *"Réelle passion pour la data science et les algorithmes d'IA. Investissement dans les missions, contribution active au produit logiciel."*

---

*Dernière mise à jour : Août 2026*

````

---

### 📄 `aegis-rca/README.md`

*73 lignes · 989 mots*

````markdown
# 🕵️ Aegis-RCA — Agent de Diagnostic de Causes Racines

**Vision** : une fois que [vigilance](../vigilance/) détecte une anomalie, Aegis-RCA l'investigue — corrèle le contexte, consulte les procédures, propose un diagnostic et une recommandation, toujours soumis à validation humaine avant toute action.

**Contexte** : projet personnel, extension directe de vigilance (2026)
**Durée** : prototype développé sur 3 jours (17-19 juillet 2026)

**Où en est ce projet** :
- ✅ Fait : consommation des tickets vigilance, corrélation métriques Prometheus, RAG sur base de connaissance (procédures/post-mortems), sandbox d'auto-correction fonctionnel (1 succès mesuré), méthodologie d'évaluation rigoureuse (bancs internes avec seuils fixés à l'avance)
- 🚧 Pas encore fait : mémoire long-terme des corrections opérateur, observabilité de production, déploiement cloud (décisions documentées, pas construites) — c'est un prototype de recherche de 3 jours, pas un produit fini

---

::: {.panel-tabset}

## 🧑‍💼 Vue d'ensemble

**Le problème** : un système de détection d'anomalies comme `vigilance` dit *qu'*une machine se comporte anormalement — mais pas toujours *pourquoi*. Un opérateur reçoit une alerte et doit encore chercher la cause, consulter les procédures pertinentes, et décider quoi faire. C'est ce travail d'investigation qu'Aegis-RCA prend en charge automatiquement.

**Comment ça marche, en clair** : dès qu'un incident est ouvert, un agent (basé sur un modèle de langage exécuté en local, pas dans le cloud) rassemble le contexte — les métriques autour de l'incident, l'historique de la machine, les procédures internes pertinentes — puis rédige un diagnostic avec sa recommandation. Rien n'est exécuté automatiquement : un humain valide toujours avant qu'une action ne soit prise.

**Ce qui distingue ce projet, ce n'est pas juste "il y a un agent IA"** — c'est la méthode : chaque choix d'architecture a été soumis à l'avis de plusieurs IA différentes (Gemini, ChatGPT) puis vérifié contre des mesures réelles avant d'être adopté. Un exemple concret : un premier test semblait montrer que la technique choisie pour fiabiliser l'agent fonctionnait parfaitement (100 % de réussite) — une vérification plus poussée a révélé que ce succès venait en fait d'un détail différent du prompt, pas de la technique testée. Cette erreur a été détectée et corrigée avant de tirer une conclusion, plutôt que d'afficher un chiffre flatteur mais faux.

**Ce que ça démontre** : la capacité à construire un système d'IA agentique avec la même rigueur qu'une démarche scientifique — mesurer plutôt que supposer, documenter les échecs autant que les réussites, et rester honnête sur ce qui n'est pas encore prouvé (le module d'auto-correction n'a qu'un seul succès mesuré à ce stade, pas un taux fiable).

## 🔧 Détails techniques

## Architecture

- `aegis/consumer.py` — consommateur Redis at-least-once, anti-poison (ACK systématique) sur le flux `aegis:incidents` de vigilance
- `aegis/agent/investigator.py` — agent d'investigation : LLM local (Qwen3.6:27B via Ollama), orchestré par une machine à états Python explicite (pas de framework agent type LangGraph — décision mesurée, voir plus bas)
- `aegis/rag/` — RAG hybride (Qdrant) sur une base de connaissance versionnée : procédures (SOPs), post-mortems, fiches de référence
- `aegis/sandbox/` — auto-correction : exécution de code généré dans un conteneur Docker jetable et durci (user non-root, rootfs read-only, `--network=none`, cgroups pids-limit anti fork-bomb)
- `aegis/tools/metrics.py` — tool typé Prometheus (requêtes curées, best-effort)
- API FastAPI : `/health`, `/incidents`, `/incidents/{ticket}`

## Méthode — pas de décision d'architecture sans confrontation au réel

Chaque choix structurant a été soumis à deux avis externes (Gemini, ChatGPT) **puis vérifié contre le code et des bancs de mesure réels** avant adoption. Deux exemples représentatifs :

- **Tool-calling** : un premier banc semblait valider un stack à 100 % de succès. Une bissection plus poussée a montré que le succès venait d'un exemple JSON littéral présent dans le prompt système, pas de la contrainte de décodage structuré qu'on pensait tester — le banc validait le mauvais mécanisme. Correction appliquée avant d'écrire la moindre conclusion.
- **Machine à états maison vs LangGraph** : décision de rester sur une machine à états explicite tant que le graphe reste sous ~15 nœuds et qu'aucune pause n'est nécessaire en milieu d'exécution — le seuil de bascule est documenté explicitement, pas choisi par défaut.
- **Évaluation sans vérité terrain** : rubrique de questions binaires plutôt qu'une note globale (qui récompense la longueur), "fidélité au contexte" comme métrique reine, juge ≠ générateur (Qwen génère, mistral-small juge), comparaisons A/B systématiquement permutées, stabilité du juge mesurée avant d'y faire confiance.

## Preuves (bancs internes, résultats bruts versionnés)

| Banc | Résultat |
|---|---|
| Tool-calling (qwen3.6:27B, 300 appels) | 100 % JSON valide / outil correct / arguments corrects, une fois le piège ci-dessus corrigé |
| Incidents à cause connue (gate Phase C, 14 cas dont cas ambigus à dessein) | 6 itérations avant un run conforme aux seuils fixés à l'avance — runs ratés conservés, pas masqués |
| Auto-correction (sandbox) | 1 succès mesuré : 1 itération, 9,6 s, modèle réel |
| Calibration du juge | Stabilité mesurée sur répétitions, juge différent du générateur |
| Retrieval RAG | hit@1 = 0,969 · hit@4 = 1,000 · MRR = 0,984 sur 32 requêtes |

## Limites honnêtes

- Prototype de 3 jours de développement, Phase A/B seulement
- L'auto-correction n'a qu'une seule preuve de succès mesurée — pas un taux statistiquement robuste
- Nécessite le réseau Docker externe de vigilance pour tourner
- Mémoire long-terme, observabilité de production et déploiement cloud : décisions documentées, pas encore construites

## Prochaine étape — boucle de feedback fermée avec vigilance

Les diagnostics validés (ou corrigés) par un opérateur constituent des labels de cause racine que [vigilance](../vigilance/) n'a pas aujourd'hui (sa couche supervisée ne distingue qu'anomalie/pas-anomalie). L'architecture mémoire déjà décidée (tickets résolus indexés dans Qdrant + corrections humaines structurées) est le prérequis naturel : une fois construite, elle alimente à la fois le réentraînement de vigilance et l'élargissement du banc d'évaluation d'Aegis au-delà des 14 cas actuels.

:::

---

**Code source** : [github.com/cyril-bgs-dev-tech/aegis-rca](https://github.com/cyril-bgs-dev-tech/aegis-rca)
**Projet frère** : [vigilance](../vigilance/) (le système qu'Aegis-RCA investigue)
**Dernière mise à jour** : Août 2026
**Contact** : cyril.bgs.dev.tech@gmail.com

````

---

### 📄 `anomaly_tabular/README.md`

*94 lignes · 1148 mots*

````markdown
# 🔬 Recherche Compositionnelle — Détection d'Anomalies Tabulaire

**Thèse** : aucun détecteur d'anomalies ne domine partout. Plutôt que de chercher un modèle miracle, on **compose** les meilleurs détecteurs (SOTA inclus) et on apprend **quand utiliser lequel** — en caractérisant les domaines de données. La performance vient de la sélection, pas d'un énième détecteur.

**Où en est ce projet** :
- ✅ Fait : 5 détecteurs de référence reproduits sur 47 datasets (ADBench), corpus étendu à 502 datasets / 20 domaines, système de sélection par domaine validé en LODO préenregistré (+3.0 pts vs meilleur détecteur unique) — résultats bruts par dataset publiés (502 lignes)
- 🚧 Pas encore fait : le harnais de calcul complet n'est pas encore extrait dans ce dépôt public sous une forme ré-exécutable par un tiers — la méthodologie, les résultats consolidés et les données brutes y sont, pas encore le code

**📊 [Présentation interactive](https://cyril-bgs-dev-tech.github.io/anomaly_tabular/)** — résultats par domaine, tous les constats (y compris les négatifs), enseignements.

---

::: {.panel-tabset}

## 🧑‍💼 Vue d'ensemble

**La question posée** : pour détecter des anomalies dans des données tabulaires (transactions, mesures, dossiers...), existe-t-il un détecteur qui marche mieux que tous les autres, quel que soit le domaine ? Beaucoup de projets s'arrêtent au premier modèle qui bat une baseline.

**Ce qu'on a trouvé** : le détecteur qui gagne change selon le domaine — un modèle par diffusion domine sur des données d'activité, un modèle causal sur des données agricoles, un autre sur de l'audio. Plutôt que de chercher LE détecteur universel, la solution est de **reconnaître le domaine** et d'y assigner le détecteur qui y excelle réellement.

**Pourquoi c'est rigoureux et pas juste une intuition** : avant de prétendre faire mieux que les résultats publiés dans la recherche académique (ADBench, la référence du domaine), la première étape a été de **reproduire exactement** ces résultats — c'est la garantie que les comparaisons qui suivent sont fiables et pas un artefact de mesure.

**Le résultat chiffré** : le système de sélection par domaine dépasse le meilleur détecteur unique de +3.0 points de précision (AUROC) — un gain confirmé statistiquement (pas un hasard de mesure) et vérifié sur des données jamais vues pendant la mise au point.

**Une découverte utile en soi** : sur environ un tiers des jeux de données (les cas "mal posés", où même les méthodes classiques peinent), ce sont les modèles de dernière génération ("foundation models") qui prennent le relais — alors qu'ils sont plutôt décevants en moyenne. Savoir *quand* changer d'outil est aussi précieux que l'outil lui-même.

**Ce que ça démontre** : la capacité à mener une recherche appliquée avec la même rigueur qu'une publication scientifique (hypothèses figées avant les résultats, vérification systématique), tout en restant honnête sur les limites (le gain est nul sur certains domaines, et c'est dit clairement).

## 🔧 Détails techniques

## 1️⃣ Le benchmark de base (l'ancre)

**ADBench** — la référence académique du domaine : 47 datasets tabulaires classiques, protocoles et hyperparamètres officiels (dépôts de référence clonés, pas réinventés).

## 2️⃣ Reproduction — le harnais doit être exact avant tout

Reproduction des détecteurs de référence avec un harnais maison (pool de processus ~28 workers, 1 thread BLAS/worker, cache reprenable — un crash ne perd aucun calcul) :

| Détecteur | Score reproduit (protocole ADBench, 47 datasets) |
|-----------|-----------------|
| IsolationForest | 0.762 |
| COPOD | 0.744 |
| ECOD | 0.742 |
| PCA | 0.740 |
| KNN | 0.699 |

Chaque écart au publié passe par une checklist : métrique, splits/seeds, hyperparamètres, préprocessing, version des données, variance, librairies.

## 3️⃣ Nos modèles sur le même banc d'essai

- **Champion maison (famille MRCD, covariance robuste)** — évalué en **préenregistrement** (hypothèses figées avant les runs) : **+1.5 pt d'AUROC médian vs IsolationForest** (p = 1.3×10⁻⁵ sur 92 datasets à anomalies natives), généralisation confirmée **hors échantillon** (+3.1 pts sur 74 datasets jamais vus). Lecture honnête, publiée telle quelle : effet réel mais modeste, nul face à KNN — ce filon seul ne suffit pas.
- **Pool de 18 « rails »** : détecteurs spécialisés par mécanisme (distance, densité, reconstruction, spectral, diffusion, covariance robuste…) + 2 **foundation models** tabulaires (TabICL, TabPFN), tous évalués au même protocole.

## 4️⃣ Spécialiser le benchmark : caractérisation des domaines

Extension du corpus à **502 datasets / 20 domaines applicatifs** (médical, vision, pharma, finance, réseau, génomique, industrie, audio…), avec méta-features label-free par dataset. Deux découvertes structurantes :

- **Le champion change selon le domaine** : diffusion #1 en activité, modèle causal non-linéaire #1 en agriculture, entropie spectrale #1 en audio… Le « meilleur détecteur global » n'est le meilleur presque nulle part.
- **Découverte des régimes** : 168/502 datasets sont « mal posés » (IF-AUC < 0.55). Sur ce régime, les **foundation models dominent** tous les détecteurs classiques — alors qu'ils sont médiocres en moyenne globale. Le signal de routage existe.

## 5️⃣ L'extension par domaines — et les scores

Système **tuned-domaine** : configuration du pool figée par domaine, validée en **LODO préenregistré** (leave-one-dataset-out) :

| Système | AUROC moyen | Lecture |
|---|---:|---|
| IsolationForest (baseline) | 63.8 | largement dépassée |
| KNN (meilleur détecteur unique) | 69.8 | le « SOTA single » |
| Ensemble 18 rails (fusion plate) | 71.3 | déjà mieux que tout single |
| **Routeur source-strict (préenregistré, LODO groupé par source)** | **72.8** | bat KNN de +3.0 pts — headline |
| Oracle du pool (sélection parfaite) | 78.7 | le plafond à capturer |

Gains par domaine du routage : **+5.1 pts environnement, +3.3 agriculture, +3.0 réseau** — et honnêtement 0.0 sur médical/finance (domaines où le signal de routage reste à trouver).

## 💡 Aparté — combien gagne-t-on au-dessus d'un système SOTA ?

Même en partant du **meilleur détecteur unique** (KNN, 69.8), la composition rapporte **+3.0 pts** aujourd'hui — et le plafond de sélection parfaite est à **+8.9 pts** (oracle 78.7). Autrement dit : ~70 % du gain accessible n'est **pas encore capturé**, et il se trouve dans la sélection, pas dans un 19ᵉ détecteur (démontré par screening systématique : les candidats supplémentaires n'élèvent plus l'oracle).

## 🧭 Prochaines actions intelligentes

1. **Méta-routeur par dataset** (au-delà du domaine) : kNN-sélecteur puis LightGBM en ranking des rails, méta-features label-free uniquement, validation LODO **nichée** — objectif : battre 72.8
2. **Proxy label-free du régime « mal posé »** (critère : corrélation > 0.5) → routage ciblé des foundation models
3. **Fusion pondérée par point** plutôt que sélection dure par dataset (la pondération douce bat déjà la fusion plate de +0.9)
4. **Corpus : grandir en natif** (~200 datasets à anomalies réelles) + lot de réplication séquestré
5. **Baseline concurrente MetaOD** re-run au même protocole + courbe de scaling du routeur (100 → 250 → 502 datasets) — les conditions de publiabilité

:::

---

**Dépôt dédié** : [github.com/cyril-bgs-dev-tech/anomaly_tabular](https://github.com/cyril-bgs-dev-tech/anomaly_tabular)  
**Projet frère** : [Recherche time series](../anomaly_tsad/) (TSB-AD, PaAno, routage par domaine)  
**Dernière mise à jour** : Août 2026  
**Contact** : cyril.bgs.dev.tech@gmail.com

````

---

### 📄 `anomaly_tsad/README.md`

*103 lignes · 1150 mots*

````markdown
# 🔬 Recherche Compositionnelle — Détection d'Anomalies Séries Temporelles

**Thèse** : même le meilleur modèle SOTA ne domine pas partout sur les séries temporelles. On reproduit le benchmark de référence, on y monte les SOTA les plus récents, puis on **caractérise les domaines** pour router le bon détecteur vers la bonne série — et on mesure ce que cette composition rapporte **au-dessus** du SOTA.

**Où en est ce projet** :
- ✅ Fait : benchmark de référence reproduit à l'exact, dernier état de l'art (PaAno, ICLR 2026) intégré et certifié #1, caractérisation des domaines et gains de routage mesurés en LODO préenregistré
- 🚧 Pas encore fait : le harnais de code n'est pas encore extrait dans ce dépôt public sous une forme reproductible par un tiers — seuls la méthodologie et les classements consolidés y sont aujourd'hui

**📊 [Présentation interactive](https://cyril-bgs-dev-tech.github.io/anomaly_tsad/)** — classements complets, tous les constats, enseignements.

---

::: {.panel-tabset}

## 🧑‍💼 Vue d'ensemble

**La question posée** : face à un signal (température, vibration, trafic réseau...) qui part en dérive, existe-t-il UN modèle qui détecte le mieux les anomalies, quel que soit le type de données ? Beaucoup de recherches cherchent "le" meilleur modèle universel.

**Ce qu'on a trouvé** : non, ce modèle universel n'existe pas. Le meilleur détecteur pour des données médicales n'est pas le même que pour des données de serveurs informatiques ou de capteurs industriels. Plutôt que de chercher LE modèle miracle, l'approche ici est de **reconnaître automatiquement le type de données** et d'assigner le bon outil au bon problème — comme un chef d'orchestre qui assigne le bon musicien à la bonne partition plutôt que de chercher un instrument qui joue tout parfaitement.

**Pourquoi c'est rigoureux et pas juste une intuition** : avant de prétendre faire mieux que les modèles publiés dans la recherche académique, la première étape a été de **reproduire exactement** leurs résultats publiés — sans ça, impossible de savoir si un gain mesuré ensuite est réel ou un artefact de mesure. Cette étape de vérification est ce qui distingue une démarche scientifique sérieuse d'un simple benchmark marketing.

**Le résultat chiffré** : en intégrant le modèle le plus récent de la recherche (2026) et en le combinant avec ce routage par domaine, le système obtient de meilleurs résultats que n'importe quel modèle utilisé seul — l'écart grandit avec la complexité des données (plusieurs capteurs corrélés plutôt qu'un seul).

**Ce que ça démontre** : la capacité à mener une recherche appliquée avec la même rigueur qu'une publication scientifique (protocoles figés à l'avance, vérifications anti-triche), tout en gardant un œil sur l'utilité pratique du résultat.

## 🔧 Détails techniques

## 1️⃣ Le benchmark de base (l'ancre)

**TSB-AD** — 870 séries univariées + 200 multivariées, issues de sources réelles (aérospatial, SCADA industriel, serveurs IT, médical, éolien…).

**Rigueur assumée** : **VUS-PR** en métrique primaire, le **point-adjust est banni** (il gonfle artificiellement les scores — biais documenté), endpoint d'évaluation natif du benchmark, validation LODO par **source** de données (jamais par série : pas de fuite).

## 2️⃣ Reproduction — des égalités exactes au publié

| Détecteur | Publié (VUS-PR moyen) | Reproduit | Statut |
|-----------|--------|-----------|--------|
| Sub-PCA (U, 350 séries) | 0.4234 | 0.4234 | ✅ **exact** |
| Sub-KNN (U) | 0.3501 | 0.3501 | ✅ **exact** |
| POLY (U) | 0.3898 | 0.3899 | ✅ |
| CNN (M, 180 séries) | 0.313 | 0.3171 | ✅ écart diagnostiqué |

SOTA récents montés et validés sur RTX 5090 : MOMENT (foundation, zero-shot), TranAD, AnomalyTransformer, FITS, Donut, OFA — plus les blocages documentés (Chronos/TimesFM : environnements isolés ; TimesNet : kernel CUDA incompatible Blackwell).

## 3️⃣ Le SOTA le plus récent sur le même banc : PaAno devient #1

**PaAno** (ICLR 2026, représentation par patchs) n'était pas classé sur TSB-AD. On l'a intégré au protocole officiel, **certifié en pleine résolution** (reproduction conforme au papier : 0.412 vs 0.426 publié sur Eva-M), puis classé contre tout le leaderboard :

| Volet | PaAno | Leader publié précédent | Rang |
|-------|-------|------------------------|------|
| Univarié (350 séries, 33 méthodes) | **0.58** VUS-PR moyen | Sub-PCA 0.42 | 🥇 #1 (rang moyen 7.8 vs 12.6 au suivant) |
| Multivarié (180 séries, 24 méthodes) | **0.46** VUS-PR moyen | CNN 0.31 | 🥇 #1 (rang moyen 7.3) |

Un écart pareil vs le publié impose la paranoïa méthodologique : mêmes splits Eva, protocole officiel, runs pleine longueur sur les séries > 250k points, vérification anti-fuite — d'où la certification avant tout claim.

## 4️⃣ Spécialiser le benchmark : caractérisation des domaines

Le corpus multivarié est caractérisé en **9 domaines applicatifs** (aérospatial, SCADA industriel, serveurs/ITops, éolien-solaire, médical cardiaque, médical neuro, robotique/drones, finance, wearables, eau/environnement) + méta-features par série (dimension, périodicité, non-stationnarité, corrélation inter-canaux…).

**Constat clé** : le champion varie par domaine — PaAno domine en robotique/finance/wearables, mais la **covariance robuste (Mahalanobis)** gagne en SCADA, le **spectral** en serveurs ITops et médical neuro, la **dynamique de corrélation** en eau/environnement.

## 5️⃣ L'extension par domaines — et les scores

Routage tuned-domaine validé en LODO, gains **au-dessus du meilleur global** par domaine :

| Domaine | Gain LODO (VUS-PR) | Rail gagnant |
|---------|-------------------:|--------------|
| Serveurs / ITops | **+0.33** | spectral |
| Médical cardiaque | **+0.27** | champion covariance |
| Médical neuro | **+0.11** | Mahalanobis |
| Éolien-solaire | +0.01 | Mahalanobis |

Et le signal le plus intéressant — **le gain du routage croît avec la dimensionnalité** :

| Strate | Gain routage | Plafond oracle |
|--------|-------------:|---------------:|
| Tout multivarié (d ≥ 2) | −0.01 | +0.16 |
| Multivarié réel (d ≥ 8) | **+0.03** | +0.18 |
| Haute dimension (d ≥ 20) | **+0.07** | +0.24 |

Les séries quasi-univariées (d = 2) diluent le signal : le routage compositionnel est une stratégie **du multivarié réel**.

## 💡 Aparté — combien gagne-t-on au-dessus d'un système SOTA ?

Même en déployant PaAno partout (le #1 absolu), la spécialisation par domaine ajoute jusqu'à **+0.33 de VUS-PR** localement, et l'oracle du pool laisse **+0.16 à +0.24** de marge selon la dimension. Le SOTA global est un excellent défaut — pas une stratégie optimale : sur les benchmarks hétérogènes, **la composition bat le champion**.

## 🧭 Prochaines actions intelligentes

1. **Benchmark & routeur « multivarié pur »** (d ≥ 8) — là où le signal de routage est démontré
2. **Proxy label-free de difficulté** par série (le routage ne doit dépendre d'aucun label)
3. **Warm-start par source** : les deltas warm vs cold montrent qu'un historique de la source vaut des points (jusqu'à +0.44 en médical neuro)
4. **Corpus qualité** : ≥ 800 séries / ≥ 12 domaines avec gates de qualité par série
5. **Préenregistrement + réplication séquestrée** des claims de routage (même discipline que le volet tabulaire)

:::

---

**Dépôt dédié** : [github.com/cyril-bgs-dev-tech/anomaly_tsad](https://github.com/cyril-bgs-dev-tech/anomaly_tsad) (classements complets inclus)  
**Projet frère** : [Recherche tabulaire](../anomaly_tabular/) (ADBench, 502 datasets, 20 domaines)  
**Dernière mise à jour** : Août 2026  
**Contact** : cyril.bgs.dev.tech@gmail.com

````

---

### 📄 `index.qmd`

*186 lignes · 1029 mots*

````markdown
---
title: "Cyril BOURGEOIS"
subtitle: "Data Scientist | MLOps Engineer"
about:
  template: jolla
  links:
    - icon: github
      text: GitHub
      href: https://github.com/cyril-bgs-dev-tech
    - icon: linkedin
      text: LinkedIn
      href: https://www.linkedin.com/in/cyril-bourgeois/
    - icon: envelope
      text: Email
      href: mailto:cyril.bgs.dev.tech@gmail.com
---

## 🎯 Profil

Data Scientist avec **double compétence modélisation + production**, spécialisé en détection d'anomalies et MLOps.

**Parcours atypique** : reconversion armée → commerce → data science (2021-2024)

---

## 🏆 Faits Marquants

### Compétitions Kaggle
- **35+ compétitions** complétées
- **3 compétitions top 1% mondial**
- **Meilleur classement** : #14 / 3 022 équipes (Top 0.5%)

### Recherche compositionnelle — détection d'anomalies
- **Ancres reproduites** : ADBench (47 datasets) et TSB-AD (égalités exactes au publié)
- **PaAno (ICLR 2026)** intégré et certifié sur TSB-AD : **#1 des volets U et M**
- **Routage par domaine** : 502 datasets / 20 domaines, +2.7 pts AUROC vs meilleur single (préenregistré)

### MLOps
- **Système temps réel** : DAG 9 workers, Redis, Docker
- **Dashboard** : 40+ pages Streamlit avec rôles RASCI
- **Observabilité** : Prometheus, Grafana, SLA tracking

---

## 🎓 Formation

### Master 2 - Data Scientist (2023-2024)
**OpenClassrooms + Centrale Supélec**  
7 projets validés · Alternance **MICHELIN** (12 mois)

### Master 1 - Data Analyst (2021-2022)
**OpenClassrooms + ENSAE**  
10 projets validés

---

## 🛠️ Stack Technique

### Langages
**Python** (avancé) · **SQL** · **Rust**

### Machine Learning
- **Classique** : Scikit-learn, XGBoost, LightGBM, CatBoost
- **Deep Learning** : PyTorch, TensorFlow, HuggingFace, **RealMLP**
- **Time Series** : Statsmodels, Prophet, LSTM, AnomalyTransformer
- **Modèles physiques** : chimie-transport (CAMS, CHIMERE, GEOS-CF) — post-traitement de sorties
- **LLMs** : évaluation, orchestration, revue croisée de résultats
- **Modèles pré-entraînés** : transfer learning, fine-tuning
- **Calcul GPU** : CUDA

### LLMs utilisés
Claude · ChatGPT · Grok · Kimi K3 · Gemini · Mistral

### Agentic
Claude Code · Codex · OpenCode

### MLOps & Infrastructure
- **Containerisation** : Docker, Docker Compose
- **Orchestration** : Redis, DAG event-driven
- **Monitoring** : Prometheus, Grafana
- **Dashboard** : Streamlit (40+ pages)

### Data Engineering
- **DataFrames** : Pandas, Polars, NumPy
- **Stockage** : Parquet, PostgreSQL, S3/MinIO
- **Versioning** : Git, DVC, MLflow

---

## 💼 Expérience

### Alternance Data Scientist - MICHELIN (2023-2024)
**POC Parsing/Matching de Données Complexes**

- Gestion de données pricing mondial (niveau continental)
- Augmentation considérable du taux de détection des correspondances
- Dashboards Power BI pour équipe pricing
- Tests automatisés (PyTest)

**Feedback** : *"Force de proposition, assidu dans les missions. POC parsing/mapping mené avec succès."*

### Data Scientist / ML Engineer - DELTAMU (2024-2025)
**Recherche en détection d'anomalies — capteurs industriels (pharma)**

- Tests de recherche en clustering et détection d'anomalies, plusieurs centaines de capteurs
- Algorithme de niveau recherche validé par le responsable scientifique
- Analyses statistiques avancées sur ensemble de bon fonctionnement
- Cœur calculatoire haute vitesse optimisé en **Rust**
- Augmentation colossale de la capacité de compréhension des données

**Feedback** : *"Réelle passion pour la data science et les algorithmes d'IA. Investissement dans les missions. Contribution active au produit logiciel."* — Nuno DOS REIS, Président, DELTAMU

---

## 📊 Projets Phares

### 🌬️ Correction Apprise des Prévisions de Qualité de l'Air
**Apprendre l'erreur du modèle européen, et la retirer** — 36 mois, 28 M de mesures horaires, 4 polluants

- **Prévoir là où personne ne mesure** : aucune observation du lieu corrigé n'entre dans le modèle, et il est testé sur des stations *et* des mois qu'il n'a jamais vus
- **−39,6 % d'erreur sur le NO₂**, −20,2 % sur les PM10, −17,9 % sur l'ozone, −11,8 % sur les PM2,5
- **En 2030 l'Europe divise ses seuils par deux** : à pollution inchangée, les stations en dépassement passent de **6 à 109**, et 4 départements d'Occitanie n'ont aucune station pour le constater
- **Assez bon pour servir en réglementaire ?** Le critère européen de qualité est atteint sur 41,4 % des stations NO₂ en brut, **96,2 %** après correction
- **Les limites sont publiées comme les résultats** : 3 épisodes réels détectés sur 33 — l'observation directe n'en attrape que 21, le produit officiel 1

→ [Voir le projet](projets_Qualite_Air/index.qmd)

### 🔧 Système de Détection d'Anomalies Temps Réel
**Projet MLOps complet** - 1 200+ heures

- Architecture event-driven : DAG 9 workers, 3 réplicas CPU + 1 GPU
- 3 canaux de détection décorrélés : IsolationForest + résidu Ridge temporel + reconstruction PCA séquentielle, fusion XGBoost
- Cycle de vie d'alarme en épisode unique (hystérésis, escalade, SLA)
- Dashboard Streamlit 40+ pages (rôles RASCI), observabilité Prometheus/Grafana

→ [Voir le projet](vigilance/index.qmd)

### 🕵️ Aegis-RCA — Agent de Diagnostic de Causes Racines
**Prototype de recherche actif** — extension de vigilance

- Agent LLM local qui investigue les incidents : contexte métriques, RAG sur procédures, diagnostic + recommandation validés par un humain
- Décisions d'architecture confrontées à des avis externes puis vérifiées par des bancs de mesure réels
- Sandbox d'auto-correction durci, 1 succès réel mesuré

→ [Voir le projet](aegis-rca/index.qmd)

### 🔬 Recherche Compositionnelle — Détection d'Anomalies (ADBench & TSB-AD)
**Composer les SOTA et router par domaine de données**

- Ancre reproduite à l'exact (Sub-PCA 0.4234, Sub-KNN 0.3501 en VUS-PR), point-adjust banni
- PaAno (ICLR 2026) monté sur TSB-AD et certifié : **#1 des deux volets** (0.58 U / 0.46 M)
- Corpus 502 datasets / 20 domaines : le routage par domaine bat le meilleur détecteur unique de +2.7 pts AUROC (préenregistré)
- Le gain du routage croît avec la dimensionnalité — la composition bat le champion global

→ [Voir le projet](anomaly_tabular/index.qmd)

### 🏆 Compétitions Kaggle - Top 1% Mondial
**35+ compétitions**

- Predict Podcast Listening Time : #20 / 3 310 (Top 0.6%)
- Prediction F1 Pit Stop : #14 / 3 022 (Top 0.5%)
- Feature engineering intensif, ensembling/stacking
- La stratégie gagnante se déplace vers l'**agentique** : des systèmes d'agents qui explorent et sélectionnent les pistes en autonomie
- **Palmarès vérifiable** : [kaggle.com/cyrilbourgeois](https://www.kaggle.com/cyrilbourgeois/competitions)

→ [Voir les compétitions](projets_Competitions/index.qmd)

---

## 🎓 Certifications

- **Master 2 Data Scientist** - OpenClassrooms + Centrale Supélec (2024)
- **Master 1 Data Analyst** - OpenClassrooms + ENSAE (2022)
- **Kaggle Competitions** : Top 1% mondial

---

## 📫 Contact

**Email** : [cyril.bgs.dev.tech@gmail.com](mailto:cyril.bgs.dev.tech@gmail.com)  
**GitHub** : [github.com/cyril-bgs-dev-tech](https://github.com/cyril-bgs-dev-tech)  
**LinkedIn** : [linkedin.com/in/cyril-bourgeois](https://www.linkedin.com/in/cyril-bourgeois/)

---

*Dernière mise à jour : Août 2026*

````

---

### 📄 `projets_Competitions/README.md`

*329 lignes · 1916 mots*

````markdown
# 🏆 Compétitions Kaggle & Machine Learning

<div align="center">

[![Profil Kaggle](https://img.shields.io/badge/Profil%20Kaggle-cyrilbourgeois-20BEFF?style=for-the-badge&logo=kaggle&logoColor=white)](https://www.kaggle.com/cyrilbourgeois/competitions)

**35+ compétitions** · **7 top 4 %** · **3 top 1 %** · meilleur rang **#14 / 3 022**

*Palmarès complet et vérifiable sur le profil.*

</div>

---

### 📖 Comment lire ce palmarès

**Toutes ces compétitions n'ont pas reçu le même investissement — autant le dire que le laisser deviner.**

La majorité ont été menées sérieusement, du début à la fin. D'autres ont été engagées puis
laissées de côté : une semaine de travail initial, puis le temps a manqué. Sur celles-là,
**moins de 25 % du temps disponible a été réellement exploité**, et le classement retenu est
celui d'une soumission arrêtée en fin de mois.

Le rang de ces compétitions-là ne mesure donc pas le plafond de la méthode : il mesure ce
qu'elle rend en une semaine. **La démarche qui mène au top 1 % est comprise et reproduite** —
trois fois, sur trois domaines sans rapport entre eux : course automobile, irrigation agricole,
écoute de podcasts.

**≈ 1 050 notebooks** : **499** dans l'espace de travail Kaggle, majoritairement privés, et
**551 en local**, comptés hors copies automatiques de Jupyter. Ce sont les brouillons, les
essais écartés et les itérations qui ne sont pas destinés à être publiés — l'ordre de grandeur
du travail réel derrière les sept rangs affichés.

### 🤖 Ce qui change en ce moment

La stratégie gagnante se déplace vers l'**agentique**. Là où l'on itérait à la main sur les
variables et les modèles, les compétiteurs déploient de plus en plus des **systèmes d'agents**
qui explorent, testent et sélectionnent les pistes en autonomie. C'est le même mouvement que
celui suivi par ailleurs sur mes projets — agent de diagnostic, orchestration de modèles — et
il est en train de redéfinir ce que veut dire « bien travailler » sur une compétition.

---

**Où en est ce projet** : activité continue — nouvelle compétition engagée régulièrement, en parallèle des autres projets.

---

::: {.panel-tabset}

## 🧑‍💼 Vue d'ensemble

**Le principe** : sur Kaggle, des milliers d'équipes dans le monde s'affrontent sur le même problème, avec les mêmes données, dans un délai fixé — un peu comme un concours d'algorithmes à l'échelle mondiale. Le classement final est objectif : même données pour tout le monde, un seul score qui compte.

**Pourquoi c'est une preuve utile** : contrairement à un projet personnel où on choisit son propre problème et ses propres critères de réussite, ici la difficulté et les règles sont imposées, et la comparaison se fait contre des milliers d'autres personnes, du débutant à l'expert. Finir dans le 1% mondial sur plusieurs compétitions différentes (course automobile, agriculture, écoute de podcasts...) montre une capacité à s'adapter vite à un nouveau domaine et à en extraire les bonnes informations, plutôt qu'une simple connaissance apprise par cœur sur un seul sujet.

**Ce que ça démontre concrètement** :
- Capacité d'apprentissage rapide sur des domaines très différents (35+ sujets distincts en 5 ans)
- Rigueur méthodologique (éviter de "tricher" en apprenant par cœur les données de test, une erreur fréquente chez les débutants)
- Veille technique active : intégration des toutes dernières techniques de recherche dès leur publication

## 🔧 Détails techniques

## 📊 Statistiques Globales

| Métrique | Valeur |
|----------|--------|
| Compétitions complétées | 35+ |
| Notebooks écrits | ≈ 1 050 — 499 sur Kaggle *(majorité privés)*, 551 en local |
| Top 4% mondial | 7 compétitions |
| Top 1% mondial | 3 compétitions |
| Meilleur rang | #14 / 3 022 (Top 0.5%) |
| Domaines couverts | Régression, classification, NLP, time series, vision, anomalies |

---

## 🥇 Compétitions Top 1% Mondial

### 1. Predicting Irrigation Need - #32 / 4 315 équipes (Top 0.7%)
**Type** : Classification binaire/multi-classes  
**Contexte** : Prédiction des besoins en irrigation agricole

**Approche Feature Engineering** :
- Features temporelles : cumul de précipitations, évapotranspiration
- Indices de végétation dérivés (NDVI, NDWI)
- Lag features sur données météo (J-7, J-14, J-30)
- Rolling statistics (moyennes, écarts-types sur fenêtres glissantes)
- Encodages cycliques : jour de l'année, heure

**Modélisation** :
- Modèles dominants : LightGBM, XGBoost, CatBoost
- Feature selection : importance des features, SHAP
- Validation : Time series split

**Technologies** : Python, LightGBM, XGBoost, Pandas, Polars

---

### 2. Prediction F1 Pit Stop - #14 / 3 022 équipes (Top 0.5%)
**Type** : Régression/Classification  
**Contexte** : Prédiction de la durée ou du moment des arrêts aux stands en F1

**Approche Feature Engineering** :
- Features course : position, écart avec concurrents, tours restants
- Features pilote : historique pit stops, style de conduite
- Features équipe : performance moyenne aux stands
- Features conditions : température piste, météo, safety car
- Lag features : performance derniers tours

**Modélisation** :
- Modèles : XGBoost, LightGBM, CatBoost, réseaux neuronaux
- Feature importance : SHAP values pour interprétation
- Validation : K-fold stratifié par course
- Ensembling : Stacking avec régression métique

**Technologies** : Python, XGBoost, LightGBM, SHAP, Optuna

---

### 3. Predict Podcast Listening Time - #20 / 3 310 équipes (Top 0.6%)
**Type** : Régression  
**Contexte** : Prédiction du temps d'écoute de podcasts

**Approche Feature Engineering** :
- Features utilisateur : historique d'écoute, préférences, engagement
- Features podcast : durée, catégorie, popularité, invité
- Features interaction : match utilisateur-podcast
- Features temporelles : jour de la semaine, heure, saison
- Text features : NLP sur titres et descriptions (TF-IDF, embeddings)

**Modélisation** :
- Modèles tabulaires : LightGBM, XGBoost, CatBoost
- NLP : Embeddings de texte + concaténation avec features tabulaires
- Validation : Group K-fold (par utilisateur)

**Technologies** : Python, LightGBM, HuggingFace Transformers, Scikit-learn

---

## 🥈 Autres Compétitions Notables

### 4. Regression — California Housing - #14 / 689 équipes (Top 2%)
**Type** : Régression  
**Contexte** : Prédiction de prix immobiliers en Californie

**Approche** :
- Feature engineering : interactions géographiques, ratios
- Modèles : XGBoost, LightGBM, CatBoost, réseaux neuronaux
- Validation : K-fold stratifié par région

---

### 5. Regression — Abalone Dataset - #61 / 2 606 équipes (Top 2%)
**Type** : Régression  
**Contexte** : Prédiction de l'âge d'ormeau à partir de caractéristiques physiques

**Approche** :
- Feature engineering : ratios de mesures, transformations non-linéaires
- Modèles : Gradient Boosting, SVR, réseaux neuronaux

---

### 6. Steel Plate Defect Prediction - #88 / 2 199 équipes (Top 4%)
**Type** : Classification multi-label  
**Contexte** : Détection de défauts sur des plaques d'acier (industrie)

**Approche** :
- Feature engineering : features géométriques, statistiques de capteurs
- Gestion déséquilibre : SMOTE, class weights
- Modèles : XGBoost, LightGBM, Random Forest

---

### 7. Multi-Label Classification — Enzyme Substrate - #44 / 1 047 équipes (Top 4%)
**Type** : Classification multi-label  
**Contexte** : Prédiction de substrats enzymatiques (biologie/chimie)

**Approche** :
- Feature engineering : descripteurs moléculaires, fingerprints
- Gestion multi-label : Binary Relevance, Label Powerset
- Modèles : One-vs-Rest XGBoost, Classifier Chains

---

## 🛠️ Méthodologie Générale

### 1. Analyse Exploratoire (EDA)
- Statistiques descriptives (moyenne, médiane, écart-type, quantiles)
- Visualisations : distributions, corrélations, pair plots
- Détection de valeurs manquantes et outliers
- Analyse de la variable cible (distribution, déséquilibre)

**Outils** : Pandas, NumPy, Matplotlib, Seaborn, Plotly

### 2. Feature Engineering

#### Features Tabulaires
- **Interactions** : Multiplication, division, ratio entre features
- **Transformations** : Log, sqrt, polynomial, binning
- **Agrégations** : Group by + mean/std/min/max/count
- **Encodages** : One-hot, target encoding, frequency encoding
- **Normalisation** : StandardScaler, RobustScaler, MinMaxScaler

#### Features Temporelles
- **Lag features** : Valeurs à J-1, J-7, J-30, etc.
- **Rolling statistics** : Moyenne, écart-type sur fenêtres glissantes
- **Encodages cycliques** : Sin/cos pour jour, mois, heure
- **Date features** : Jour de la semaine, mois, trimestre, année

#### Features Textuelles (NLP)
- **Bag of Words** : CountVectorizer, TfidfVectorizer
- **Embeddings** : Word2Vec, GloVe, FastText
- **Transformers** : BERT, CamemBERT (fine-tuning ou features extraites)

### 3. Modélisation

#### Algorithmes Utilisés
**Gradient Boosting** (dominants en tabulaire) :
- **XGBoost** : Robuste, rapide, bien supporté
- **LightGBM** : Plus rapide sur gros datasets, leaf-wise growth
- **CatBoost** : Excellent pour catégorielles, peu de preprocessing

**Réseaux Neuronaux** :
- **TabM** : Architecture récente, state-of-the-art tabulaire
- **TabICL2** : In-context learning pour tabulaire
- **RealMLP** : MLP avec améliorations récentes
- **LSTM/GRU** : Séquences temporelles
- **Transformers** : NLP, time series

#### Stratégies d'Ensembling
**Stacking** :
- Niveau 1 : Modèles de base (XGBoost, LightGBM, CatBoost, NN)
- Niveau 2 : Méta-modèle (régression linéaire, Ridge)
- Validation : Out-of-fold predictions pour éviter overfitting

### 4. Validation et Optimisation

#### Validation Croisée
- **K-Fold** : Standard, Stratifié, Group K-fold, Time Series Split

#### Optimisation Hyperparamètres
- **Optuna** : Optimisation bayésienne (TPE sampler), pruning, 100-500 trials
- **Grid Search** : Ajustements fins après Optuna

### 5. Interprétabilité

#### SHAP (SHapley Additive exPlanations)
- Feature importance globale
- Visualisation des impacts (summary plot, dependence plot)
- Explication de prédictions individuelles (force plot)

---

## 📊 Répartition par Type de Problème

| Type | Nombre | Meilleur Top % |
|------|--------|----------------|
| Régression | 10+ | 2% |
| Classification binaire | 12+ | 0.7% |
| Classification multi-classes | 6+ | 0.7% |
| Classification multi-label | 4+ | 4% |
| Time Series | 5+ | 0.5% |
| NLP | 3+ | 0.6% |

---

## 📈 Évolution des Performances

| Période | Performance | Approche |
|---------|-------------|----------|
| **2021-2022** | Top 20-30% | Modèles standards, peu de feature engineering |
| **2023-2024** | Top 5-10% | Feature engineering intensif, ensembling |
| **2025-2026** | Top 1-2% | Approche systématique, veille active (TabM, TabICL2) |

---

## 🛠️ Technologies Maîtrisées

| Catégorie | Technologies |
|-----------|-------------|
| **Langages** | Python (avancé), SQL |
| **ML/DL** | Scikit-learn, XGBoost, LightGBM, CatBoost, PyTorch, TensorFlow, HuggingFace |
| **Feature Engineering** | Pandas, NumPy, Polars, RAPIDS (GPU) |
| **Optimisation** | Optuna, Scikit-learn GridSearch |
| **Visualisation** | Matplotlib, Seaborn, Plotly |
| **Versioning** | Git, DVC |

---

## 🎯 Valeur Ajoutée pour l'Entreprise

### Compétences Démontrées
1. **Capacité d'apprentissage rapide** : Top 1% sur des domaines variés (agriculture, F1, podcasts)
2. **Feature engineering avancé** : Création de features pertinentes dans tous les domaines
3. **Maîtrise état de l'art** : Test et intégration des dernières avancées (TabM, TabICL2, RealMLP)
4. **Rigueur expérimentale** : Validation croisée, reproductibilité, interprétabilité
5. **Optimisation systématique** : Optimisation bayésienne, ensembling, stacking

### Applications Business
- **Pricing** : Prédiction de prix
- **Détection de fraude** : Classification binaire et détection d'anomalies
- **Segmentation clients** : Clustering et classification multi-classes
- **Prévision demande** : Time series et feature engineering temporel
- **NLP** : Analyse de sentiments, classification de textes
- **Recommandation** : Features d'interaction, modèles de ranking

---

## 🎓 Leçons Apprises

### Leçons Techniques
1. **Feature engineering > Modèle complexe** : De bonnes features battent souvent un modèle sophistiqué
2. **Validation rigoureuse** : Une bonne validation évite l'overfitting et les surprises
3. **Diversité des modèles** : L'ensembling de modèles diversifiés est puissant
4. **Domain knowledge** : Comprendre le domaine aide à créer de meilleures features
5. **Itération rapide** : Mieux vaut tester beaucoup d'idées simples que peu d'idées complexes

### Leçons Stratégiques
1. **Choisir ses batailles** : Se concentrer sur les compétitions où on a un avantage
2. **Collaboration** : Rejoindre des équipes pour combiner les forces
3. **Partage** : Partager ses approches apprend aux autres et renforce sa propre compréhension
4. **Veille** : Rester à jour sur les dernières avancées est crucial
5. **Patience** : Les améliorations marginales s'accumulent

:::

---

**Dernière mise à jour** : Août 2026  
**Contact** : cyril.bgs.dev.tech@gmail.com

````

---

### 📄 `projets_Master_1/README.md`

*280 lignes · 1333 mots*

````markdown
# 🎓 Projets Master 1 - Data Analyst (2021-2022)

**Formation** : OpenClassrooms + ENSAE  
**Durée** : 12 mois  
**Projets réalisés** : 10 projets validés

**Où en est ce projet** : les 10 projets sont validés et clos (2022). Les notebooks/livrables ne sont pas versionnés ici (pour garder le dépôt léger) — disponibles sur demande.

---

::: {.panel-tabset}

## 🧑‍💼 Vue d'ensemble

Cette première année de formation (2021-2022) pose les bases du métier de data analyst : passer de données brutes à des recommandations utilisables par une équipe métier, sur des cas concrets — ventes e-commerce, gestion de stock, indicateurs d'égalité professionnelle, qualité de l'eau potable, étude de marché...

Le fil conducteur des retours d'évaluateurs (5 formateurs différents sur 10 projets) : la technique était acquise dès le début, mais la **présentation des résultats à un public non-technique** était le point à travailler — et s'est nettement améliorée au fil des projets (voir le dernier, sur la détection de faux billets, où ce retour a été le plus explicite).

## 🔧 Détails techniques


## 📊 Vue d'Ensemble

### Compétences Acquises

- ✅ **Analyse exploratoire et dashboarding** (P2, P5, P6, P8)
- ✅ **Bases de données SQL** (P3)
- ✅ **Algorithmes fondamentaux de ML** (P9, P10)
- ✅ **Visualisation de données** (P2, P4, P6, P7, P8, P9)
- ✅ **Tests statistiques** (P6)
- ✅ **Séries temporelles** (P6)
- ✅ **Clustering et ACP** (P9)
- ✅ **Régression et classification** (P10)
- ✅ **Outils no-code** : KNIME (P7), Tableau (P8)
- ✅ **Conformité RGPD** (P7)

### Outils Maîtrisés

| Catégorie | Technologies |
|-----------|-------------|
| **Langages** | Python, SQL |
| **Data Analysis** | Pandas, NumPy, Scikit-learn |
| **Visualisation** | Matplotlib, Seaborn, Plotly |
| **BI & Dashboard** | Tableau, Power BI, Excel |
| **No-Code** | KNIME Analytics Platform |
| **Base de données** | PostgreSQL, MySQL |

---

## 📁 Liste des Projets

### 1. Plan d'Apprentissage Personnalisé
**Statut** : ✅ Validé | **Durée** : ~20 heures

**Objectifs** :
- Élaborer un plan d'apprentissage personnalisé sur 12 mois
- Identifier les ressources et outils nécessaires
- Planifier les 10 projets avec dates prévisionnelles

**Compétences validées** :
- Gestion de projet personnel
- Identification de ressources pertinentes
- Planification et organisation

---

### 2. Analyse des Ventes pour un E-commerce
**Statut** : ✅ Validé

**Contexte** : Analyse des données de ventes d'une entreprise e-commerce

**Réalisation** :
- Analyse exploratoire complète
- 12 graphiques principaux + 2 graphiques explicatifs
- Dashboard interactif avec filtres
- Présentation des insights

**Outils** : Excel, Dashboard interactif, PowerPoint

**Feedback** : *"Très beau travail autour de l'analyse des data. Beau rendu avec explications claires. Des softs skills déjà acquis autour de la présentation."*

---

### 3. Base de Données Immobilière avec SQL
**Statut** : ✅ Validé

**Contexte** : Conception et exploitation d'une base de données immobilière

**Réalisation** :
- Modélisation MCD/MLD avec normalisation (1FN, 2FN, 3FN)
- Création des tables et chargement des données
- 9 requêtes SQL complexes (jointures, agrégations, sous-requêtes)
- Bonus : Présentation d'une BI

**Outils** : PostgreSQL/MySQL, SQL avancé, BI tool

**Feedback** : *"Les données sont chargées dans une base de données. Le MCD et le MLD sont valides. Les requêtes SQL sont valides et permettent de répondre aux différentes questions."*

---

### 4. Étude de Santé Publique avec Python
**Statut** : ✅ Validé

**Contexte** : Analyse de données de santé publique

**Réalisation** :
- Configuration environnement Python (Anaconda, Jupyter)
- Manipulation de DataFrames (Pandas, NumPy)
- Analyses descriptives et visualisations
- Intégration d'analyses supplémentaires non demandées

**Outils** : Python (Pandas, NumPy, Matplotlib, Seaborn), Jupyter Notebook

**Feedback** : *"Conforme à la demande. Intégration d'analyses supplémentaires. Bonne présentation."*

---

### 5. Optimisation de la Gestion des Données d'une Boutique
**Statut** : ✅ Validé

**Contexte** : Analyse et optimisation de la gestion des stocks

**Réalisation** :
- Classification des données (produits, ventes, stocks, clients)
- Nettoyage des données (valeurs manquantes, doublons, incohérences)
- Analyse univariée détaillée
- Détection d'anomalies dans les stocks
- Recommandations pour optimisation

**Outils** : Python (Pandas, NumPy), Matplotlib, Seaborn

**Feedback** : *"Bonne présentation claire et précise. Analyse orientée métier et répond bien aux besoins exprimés."*

---

### 6. Analyse des Ventes d'une Librairie
**Statut** : ✅ Validé

**Contexte** : Analyse des ventes avec séries temporelles et tests statistiques

**Réalisation** :
- Tests statistiques (Shapiro-Wilk, Kolmogorov-Smirnov, t-test, Mann-Whitney)
- Analyse bivariée (corrélations, scatter plots)
- Séries temporelles (décomposition, saisonnalité, prévisions)
- Bonus Power BI : Dashboard interactif complet (7 min supplémentaires)

**Outils** : Python (Pandas, Statsmodels, Scipy), Power BI

**Feedback** : *"Livrable complet et conforme aux attentes. L'étudiant est allé au-delà de ce qui est demandé en proposant un ensemble de graphiques et tableau de bord sur PowerBI."*

---

### 7. Analyse des Indicateurs d'Égalité Femme/Homme avec KNIME
**Statut** : ✅ Validé

**Contexte** : Analyse des indicateurs d'égalité professionnelle

**Réalisation** :
- Collecte et conformité RGPD
- Préparation des données (nettoyage, normalisation)
- Workflow KNIME complet
- Analyse des écarts de rémunération
- Visualisations (barcharts empilés, indicateurs)

**Outils** : KNIME Analytics Platform, Workflow ETL

**Feedback** : *"Tous les livrables sont présents et conformes aux attentes. Bonne prise en main de KNIME. Graphiques intéressants."*

---

### 8. Étude sur l'Eau Potable avec Tableau
**Statut** : ✅ Validé

**Contexte** : Analyse de données sur la qualité de l'eau potable

**Réalisation** :
- Analyse du besoin client (questions analytiques)
- Dashboard Tableau avec plusieurs vues (globale, continentale, nationale)
- Filtres interactifs
- Graphiques adaptés aux types de données
- Publication sur Tableau Public

**Outils** : Tableau Desktop, Tableau Public

**Feedback** : *"Bonne soutenance dans l'ensemble, très claire apporte de bonne justification."*

---

### 9. Étude de Marché avec Clustering et ACP
**Statut** : ✅ Validé

**Contexte** : Analyse de marché avec réduction de dimension et segmentation

**Réalisation** :
- **ACP** : Éboulis des valeurs propres, cercle des corrélations, projection des individus
- **Clustering** : Dendrogramme CAH, K-Means, justification du nombre de classes
- **Caractérisation** : Centroïdes, heatmap, boxplots, radar plots
- Démarche respectée (contexte, méthodologie, résultats, recommandations)

**Outils** : Python (Scikit-learn, Scipy), Matplotlib, Seaborn

**Feedback** : *"Bonne présentation dans l'ensemble. Les graphiques sont un point fort."*

---

### 10. Détection de Faux Billets
**Statut** : ✅ Validé

**Contexte** : Classification de billets authentiques vs contrefaçons

**Réalisation** :
- Régression linéaire (feature engineering poussé)
- Régression logistique et classification (cross-validation, optimisation)
- Analyse prédictive (plusieurs modèles comparés)
- Clustering (CAH + matrice de confusion)

**Outils** : Python (Scikit-learn, Pandas, NumPy), Matplotlib, Seaborn

**Feedback** : *"Le projet est techniquement OK mais il faut faire un effort sur la présentation des résultats."*

**Leçon apprise** : Importance de la structuration des présentations et de la communication des résultats.

---

## 📊 Synthèse des Feedbacks

**Mots-clés dominants** :
- **Présentation** : Mentionnée dans 8/10 projets
- **Conforme/Complet** : Livrables de qualité
- **Bonus/Supplémentaire** : Proactivité (Power BI, analyses additionnelles)
- **Orienté métier** : Compréhension des besoins business
- **Graphiques** : Point fort récurrent

**Évolution constatée** :
- Présentations de plus en plus fluides et structurées
- Leçon P10 (soutenance confuse) intégrée pour la suite

---

## 🎯 Points Forts Développés

### Proactivité
- Allé au-delà des attentes dans la plupart des projets
- Bonus Power BI (P6), BI présentée (P3), analyses supplémentaires (P4)

### Compétences Techniques
- Maîtrise de Python, SQL, KNIME, Tableau, Power BI, Excel
- Capacité d'adaptation à différents outils et domaines

### Sens du Métier
- Analyse orientée métier (P5, P6, P9)
- Communication des résultats aux stakeholders

### Évolution
- Présentations de plus en plus fluides et structurées
- Leçon P10 intégrée pour la suite du parcours

---

## 📈 Transition vers Master 2

**Objectifs atteints** :
- Bases solides en analyse de données
- Premiers modèles de ML
- Capacité à réaliser des analyses complètes

**Ambitions pour M2** :
- Problèmes plus complexes
- Deep learning et NLP
- Données à plus grande échelle
- Alternance en entreprise

:::

---

**Dernière mise à jour** : Août 2026  
**Contact** : cyril.bgs.dev.tech@gmail.com

> 📦 **Livrables complets** (notebooks, rapports, soutenances) disponibles sur demande — non versionnés ici pour garder le dépôt léger.

````

---

### 📄 `projets_Master_2/README.md`

*219 lignes · 1111 mots*

````markdown
# 🎓 Projets Master 2 - Data Scientist (2023-2024)

**Formation** : OpenClassrooms + Centrale Supélec  
**Alternance** : MICHELIN (Fév 2023 - Fév 2024), 39h/semaine, 4 jours/5 en entreprise  
**Durée** : 12 mois  
**Projets réalisés** : 7 projets validés

**Où en est ce projet** : formation et alternance terminées et validées (2024). Le code Michelin est confidentiel (données pricing propriétaires) ; les notebooks des projets académiques ne sont pas versionnés ici — disponibles sur demande.

---

::: {.panel-tabset}

## 🧑‍💼 Vue d'ensemble

Cette deuxième année (2023-2024) associe une formation avancée (deep learning, NLP, séries temporelles) à une alternance d'un an chez Michelin.

**La mission Michelin en une phrase** : rapprocher automatiquement des données de pricing venant de sources multiples et hétérogènes, à l'échelle mondiale (niveau continental) — un travail de rapprochement fait manuellement jusque-là, avec des résultats jugés excellents par plusieurs Product Owners.

**L'impact** : accélération considérable des temps de traitement par rapport au processus manuel, amélioration de la qualité des données de pricing, et un POC mené jusqu'au bout, préparé pour la mise en production, puis adapté et utilisé par les équipes.

**Le reste de l'année** : projets académiques sur des cas variés (application santé publique, prévision de consommation énergétique, segmentation client e-commerce, classification automatique de texte, reconnaissance d'images).

## 🔧 Détails techniques

## 🏭 Alternance Michelin - POC Parsing/Matching de Données Complexes

**Statut** : ✅ Validé - Alternance réussie  
**Durée** : 12 mois (Fév 2023 - Fév 2024)  
**Contexte** : Données pricing mondial, niveau continental, hétérogénéité des sources

### Problématique
- Rapprocher des données de pricing provenant de sources multiples et hétérogènes, niveau continental
- Assurer la qualité des données pour des analyses pricing mondiales fiables

### Missions Réalisées
- Réalisation d'un POC de parsing/matching de données complexes, niveau continental
- Algorithmes de fuzzy matching — augmentation considérable du taux de détection des correspondances
- Nettoyage et qualité des données, analyses spécifiques autour du pricing niveau mondial
- Tests de non régression

### Résultats Globaux
- Vitesse d'exécution et résultats jugés excellents d'après plusieurs Product Owners
- Accélération considérable des temps de traitement par rapport au processus manuel
- POC mené jusqu'au bout et préparé pour la mise en production, adapté et utilisé par les équipes par la suite

### Synthèse des Feedbacks

**Mots-clés dominants** :
- **Implication/Challenger** : Engagement constant
- **Maîtrise/Développement** : Compétences techniques solides
- **Force proposition** : Autonomie et initiative
- **Qualité/Exécution** : Standards élevés
- **Industrialisation** : Vision produit

### Feedback Michelin
**Antoine DANIEL LAMAZIERE (PO) + Architecte Data** :
- *"Implication et capacité constante à se challenger"*
- *"Maîtrise des solutions de développement et mise en œuvre"*
- *"Force de proposition, assidu dans les missions"*
- *"POC parsing/mapping mené avec succès"*

---

## 🧠 Projets Académiques

### Projet 1 : Définissez Votre Stratégie d'Apprentissage
**Statut** : ✅ Validé

**Objectifs** :
- Définir une stratégie d'apprentissage personnalisée
- Planifier le parcours Master 2
- Identifier les ressources et outils

**Feedback** : *"Cadre de la formation bien défini, objectifs clairs. Très bonne soutenance."*

---

### Projet 2 : Concevez une Application au Service de la Santé Publique
**Statut** : ✅ Validé

**Contexte** : Application data science pour la santé publique

**Réalisation** :
- Analyse de données de santé
- Modélisation prédictive
- Visualisation et recommandations

**Feedback** : *"Livrables complets, répondent à la problématique. Analyse pertinente des données, traitements outliers et valeurs manquantes bien réalisés."*

---

### Projet 3 : Anticipez les Besoins en Consommation de Bâtiments
**Statut** : ✅ Validé

**Contexte** : Prédiction de consommation énergétique

**Réalisation** :
- Feature engineering temporel
- Modèles de régression
- Prévisions de consommation

**Feedback** : *"Valeurs manquantes très bien réalisées, beaucoup de recherches. Data leakage bien identifié et écarté. Très bon score de R². Félicitations."*

---

### Projet 4 : Segmentez des Clients d'un Site E-commerce
**Statut** : ✅ Validé

**Contexte** : Segmentation client pour e-commerce

**Réalisation** :
- Clustering (K-Means, CAH)
- Analyse comportementale
- Recommandations business

**Feedback** : *"Présentation claire et agréable, support de qualité professionnel. Bonne compréhension des approches de clustering, clusters bien interprétés."*

---

### Projet 5 : Catégorisez Automatiquement des Questions
**Statut** : ✅ Validé

**Contexte** : Classification automatique de textes (NLP)

**Réalisation** :
- Pipeline NLP (tokenization, vectorization)
- Modèles de classification de textes
- TF-IDF, embeddings, transformers

**Feedback** : *"Travail de grande qualité, répond parfaitement aux critères de validation. Bon niveau technique et solides compétences en communication."*

---

### Projet 6 : Classez des Images à l'Aide d'Algorithmes de Deep Learning
**Statut** : ✅ Validé

**Objectifs pédagogiques** :
- Maîtriser les architectures CNN (Convolutional Neural Networks)
- Transfer learning avec modèles pré-entraînés
- Data augmentation et régularisation

**Réalisation** :
- Architectures testées : CNN custom, ResNet, VGG, EfficientNet
- Framework : TensorFlow/Keras ou PyTorch
- Prétraitement d'images (normalisation, redimensionnement)
- Data augmentation (rotation, flip, zoom)
- Transfer learning et fine-tuning
- Gestion du surapprentissage (dropout, batch normalization)

**Technologies** : Python, TensorFlow/PyTorch, CNN, Transfer Learning

**Feedback** : *"Points forts : prétraitements, CNN from scratch, transfer learning, data augmentation, fine-tuning."*

---

### Projet 7 : Développez une Preuve de Concept (Option Stage)
**Statut** : ✅ Validé

**Contexte** : POC pour validation des acquis avant stage/alternance — classification sur données tabulaires, test d'une famille d'algorithmes récente (TabPFN) comparée aux approches ensemblistes (XGBoost, LightGBM, CatBoost)

**Réalisation** :
- Projet intégrateur combinant plusieurs compétences
- Démonstration de capacité à mener un projet de bout en bout
- Présentation et soutenance

**Feedback** : *"Sujet pertinent, sources sérieuses consultées et bien articulées. Présentation claire."*

---

## 🎯 Compétences Acquises en Master 2

### Deep Learning
- ✅ CNN, RNN, Transformers
- ✅ Transfer learning et fine-tuning
- ✅ Data augmentation avancée

### NLP
- ✅ Fine-tuning LLMs (BERT, CamemBERT)
- ✅ Word embeddings
- ✅ Pipeline NLP complet

### Time Series
- ✅ Feature engineering temporel avancé
- ✅ Modèles statistiques et deep learning
- ✅ Validation spécifique séries temporelles

### Détection d'Anomalies
- ✅ Approches statistiques et ML
- ✅ Autoencoders
- ✅ Gestion du déséquilibre

### Entreprise
- ✅ Gestion de projets data (Michelin, 12 mois)
- ✅ Collaboration avec Product Owners et Architectes Data
- ✅ Vision produit et industrialisation
- ✅ Communication avec stakeholders non-techniques

---

## 🛠️ Stack Technique Master 2

| Catégorie | Technologies |
|-----------|-------------|
| **Deep Learning** | PyTorch, TensorFlow, Keras |
| **NLP** | HuggingFace Transformers, SpaCy, NLTK |
| **Time Series** | Statsmodels, Prophet, LSTM |
| **Anomalies** | Scikit-learn, Isolation Forest, Autoencoders |
| **Entreprise** | Power BI, Streamlit, Plotly, Git |
| **Testing** | PyTest |

:::

---

**Dernière mise à jour** : Août 2026  
**Contact** : cyril.bgs.dev.tech@gmail.com

> 📦 **Livrables complets** (notebooks, rapports, soutenances) disponibles sur demande — non versionnés ici pour garder le dépôt léger.

````

---

### 📄 `projets_Qualite_Air/README.md`

*183 lignes · 1539 mots*

````markdown
# 🌬️ Correction apprise des prévisions de qualité de l'air

**Post-traitement des prévisions européennes CAMS aux stations françaises** — le modèle
apprend le **résidu** `observation − CAMS` et le retranche. Quatre polluants : NO₂, O₃,
PM10, PM2,5.

> **Ce que ce projet démontre n'est pas un score, c'est un protocole.** La méthode est
> publiée depuis 2023 ; ce qui a de la valeur ici est de l'avoir **mesurée honnêtement**, et
> d'avoir cherché où elle échoue.

📦 **Dépôt** : [correction-previsions-qualite-air](https://github.com/cyril-bgs-dev-tech/correction-previsions-qualite-air)

---

## 🎯 La contrainte qui définit le produit

Le modèle doit corriger **en un point où il n'y a aucune station**. Aucune observation
locale n'entre à l'inférence, pas même celle de la veille. C'est ce qui rend le problème
difficile — et ce qui élimine la moitié des méthodes publiées, qui supposent un réseau dense
disponible en temps réel.

L'évaluation est donc en **double aveugle** : le modèle est testé sur des stations
entièrement absentes de son apprentissage, pendant un mois également absent.

---

## 📊 Le résultat

**Pile complète, double aveugle station *et* mois cachés, J+1, 24 mois de support commun :**

| polluant | `PARTOUT` — aucune observation du point | aux stations — avec son historique |
|---|---|---|
| **NO₂** | **+39,6 %** | +45,7 % |
| **PM10** | **+20,2 %** | +26,3 % |
| **O₃** | **+17,9 %** | +24,1 % |
| **PM2,5** | **+11,8 %** | +19,6 % |

*Réduction de RMSE contre CAMS brut. **Citer deux chiffres, jamais un** : `PARTOUT` vaut là
où rien ne mesure — c'est le seul que CAMS ne sait pas faire.*

**Contre la chaîne opérationnelle**, mêmes stations et mêmes jours, à J+1 : le produit
archivé de PREV'AIR porte dans sa métadonnée `CHIMERE combined to surface real time
observations` — c'est **AS-CHI**, leur adaptation statistique. L'écart va de **+13,7 %**
(O₃) à **+66,9 %** (PM2,5) à notre avantage, **sur dix-sept jours seulement** : leur archive
n'expose que six jours glissants et ne peut pas remonter le temps.

---

## 🔬 Ce qui distingue ce travail

### Le mécanisme est établi, pas supposé

Le dernier levier trouvé — sept traceurs de **composition** du champ CAMS que le dépôt ne
téléchargeait pas — rend +1,5 à +6,0 %. Une **permutation conditionnelle** tranche son
mécanisme : permuter la composition *à l'intérieur* de chaque couple (station, mois)
conserve exactement l'histogramme par site et par saison, et ne détruit que l'appariement au
**jour**. Elle **efface la totalité du gain**, sur les quatre polluants.

Ce n'est donc ni un encodeur site×saison, ni un proxy de régime : le modèle exploite
l'**écart du jour** à la composition habituelle du lieu.

### Les seuils sont fixés avant de regarder

Chaque test porte son critère de décision **écrit dans l'en-tête du script**, avant la
première mesure — et la phrase à écrire si le test échoue. L'attribution par valeur de
Shapley a d'ailleurs **renoncé** à attribuer un gain à un groupe de traceurs sur PM2,5,
faute d'avoir franchi son propre seuil.

### Une affirmation du projet a été réfutée par sa propre mesure

Le dossier affirmait que ses leviers ne se dégradent pas avec l'échéance. Poussé jusqu'à
**J+3** — la dernière que CAMS Europe produise :

| | J0 | J+1 | J+2 | J+3 | plage | verdict |
|---|---|---|---|---|---|---|
| NO₂ | +37,1 % | +37,1 % | +36,9 % | +36,7 % | 0,38 pt | ✅ **stable** |
| O₃ | +9,3 % | +9,1 % | +8,5 % | **+7,0 %** | 2,25 pt | 🔴 **réfutée** |

Et le classement suit le mécanisme invoqué : l'apport de la typologie de station — qui mesure
à quel point le résidu est attaché au **lieu** — vaut **+9,0 pt sur NO₂** et **−0,2 sur O₃**.
Le polluant dont l'erreur est un effet de site résiste à l'échéance ; celui qui ne l'est pas
se dégrade. *L'affirmation était juste sur son mécanisme et trop large dans sa portée.*

---

## 🛡️ Les défauts trouvés dans nos propres résultats

Chaque ligne est un défaut **silencieux** — rien ne plantait, tout était plausible :

| ce qui était faux | comment on l'a su | ce qui l'empêche aujourd'hui |
|---|---|---|
| « J+1 » désignait en fait **J0** | lu dans les données, pas dans le nom | `libelle_echeance()` dérive le libellé |
| une colonne `rmse_realmlp` contenait du **LightGBM** | un relecteur externe a rouvert le CSV | un garde refuse d'écrire une étiquette qui affirme une identité |
| le PDF **ne contenait pas** le chiffre que le document désigne comme le seul citable | mesure de largeur en média impression | l'export **refuse** et nomme l'élément |
| un mois absent codait l'**année** | revue externe, puis recherche du jumeau | le garde **mesure** la couverture de chaque famille |
| l'échéance publiée était **J+2**, la mesure est **J+1** — une erreur qui **flattait** | premier jour couvert, horizon par horizon | mécanisé après être revenue une fois |

> **La règle du dépôt** : *une règle violée deux fois devient du code, ou elle disparaît.*
> Douze règles, dont dix exécutables.

---

## 📅 L'horizon réglementaire — pourquoi ce travail a un usage

La directive **(UE) 2024/2881** fait deux choses que l'on cite toujours séparément : elle
**divise par deux** les valeurs limites annuelles au 1ᵉʳ janvier 2030, et elle rend la
**modélisation obligatoire** dans toute zone où un seuil est dépassé. Multipliées, elles
donnent l'argument que ni l'une ni l'autre ne porte seule — abaisser le seuil **multiplie
mécaniquement** le nombre de zones où modéliser devient une obligation légale.

Compté sur le parc réel, moyennes annuelles 2025, à air constant : **6 stations en
dépassement aujourd'hui, 109 en 2030** — un facteur **×18,2** sur 408 évaluées. En
Occitanie, 2 → 5, et **4 des 13 départements n'ont aucune station retenue** : pour eux la
conformité 2030 ne peut pas être posée depuis la mesure. C'est le cas que la directive
confie explicitement à la modélisation.

**Et là où le modèle devient opposable, sa qualité devient un point de contrôle** — c'est le
critère FAIRMODE qui en décide. Part des stations satisfaisant `MQI_f ≤ 1` à J+1, critère
atteint à partir de **90 %** :

| polluant | CAMS brut | corrigé · `PARTOUT` | corrigé · aux stations |
|---|---|---|---|
| **NO₂** | **41,4 %** ✗ | 87,9 % ✗ | **96,2 %** ✓ |
| PM10 | 87,8 % ✗ | 98,4 % ✓ | **100 %** ✓ |
| O₃ | 93,6 % ✓ | 97,4 % ✓ | **99,2 %** ✓ |

Le NO₂ est le cas critique, et ce n'est pas une coïncidence : c'est à la fois le polluant où
le produit européen échoue le plus et celui dont la valeur limite est divisée par deux. Son
biais passe de −14,27 à −0,43 µg/m³.

🔴 **Le critère n'est pas franchi partout, et le dire fait partie du résultat** : sans aucune
observation du point, le NO₂ reste à 87,9 %, *sous* la barre. Il ne la franchit qu'aux
stations instrumentées.

---

## 🧰 Stack

**Python** · LightGBM · PyTorch *(RealMLP-TD porté)* · Optuna · xarray/netCDF4 · pandas ·
scikit-learn · Streamlit · Playwright

**Données** — CAMS Europe (Copernicus/ECMWF, 28 variables), NASA **GEOS-CF** *(modèle de
chimie indépendant)*, observations LCSQA/Geod'Air, ERA5 *(réanalyse : plafond, non
déployable)*, Copernicus DEM GLO-30, IGN Géoplateforme, PREV'AIR/INERIS.

**Volume** — corpus de **36 mois** (2023-08 → 2026-07), **28,0 M d'enregistrements horaires**. Prévisions extraites à **476 points** ; **438 stations effectivement évaluées**, de 236 (PM2,5) à 344 (NO₂) selon le polluant.

---

## 📐 Le protocole d'évaluation

Quatre cellules, selon ce qui est caché :

| épreuve | station | mois | ce qu'elle mesure |
|---|---|---|---|
| spatiale | **cachée** | vue | transfert vers un lieu non instrumenté |
| temporelle | vue | **caché** | tenue dans le temps |
| **double aveugle** | **cachée** | **caché** | **la condition de déploiement** |
| chronologique | **cachée** | **caché**, passé seul | extrapolation réelle |

Les masques d'entraînement sont donnés **explicitement**, jamais par complément — le
complément du test double aveugle contient encore le mois caché sur d'autres stations, ce
qui rendrait l'épreuve plus facile que chacune des deux prises séparément.

L'incertitude vient d'un **bootstrap circulaire par blocs de mois** sur les différences
appariées : les plis ne sont pas indépendants, les groupes de stations tournent et deux plis
partagent 93 % de leur apprentissage. La version à six mois est la sensibilité obligatoire.

---

## 🔴 Ce que ce projet ne démontre pas

- **La détection d'épisodes reste faible** : 3 des 33 épisodes PM10 réellement déclenchés par
  les préfectures. Même l'observation parfaite n'en attrape que 21 — la décision préfectorale
  intègre des critères que la concentration seule ne contient pas.
- **Dix-sept jours de duel ne concluent rien** contre la chaîne opérationnelle. C'est un
  ordre de grandeur.
- **Au seuil réglementaire ozone de 180 µg/m³**, 3 dépassements détectés sur 32.
- **Le flux GEOS-CF v1 est retiré depuis janvier 2026** et v2 n'est pas le même prédicteur
  (15,4 µg/m³ d'écart sur l'ozone au recouvrement). Un déploiement aujourd'hui exigerait de
  re-valider son apport.

*Ces limites sont publiées au même titre que les résultats favorables.*

````

---

### 📄 `projets_Tuning_Data_Augmentation_Vision/README.md`

*57 lignes · 213 mots*

````markdown
# 🎨 Projets Tuning & Data Augmentation - Vision

**Domaine** : Computer Vision  
**Focus** : Optimisation de modèles, data augmentation, transfer learning

---

## 📋 Vue d'Ensemble

### Objectifs
- Maîtriser les techniques de data augmentation pour la vision
- Optimisation d'hyperparamètres (tuning)
- Transfer learning avec modèles pré-entraînés
- Amélioration des performances sur datasets limités

---

## 🛠️ Techniques Maîtrisées

### Data Augmentation
- **Géométriques** : Rotation, flip, crop, zoom, shear
- **Colorimétriques** : Brightness, contrast, saturation, hue
- **Avancées** : MixUp, CutMix, RandAugment, AutoAugment
- **Adaptatives** : Techniques spécifiques au domaine

### Transfer Learning
- **Modèles pré-entraînés** : ResNet, VGG, EfficientNet, Vision Transformers
- **Fine-tuning** : Stratégies de gel/dégel de couches
- **Feature extraction** : Utilisation comme extracteur de features

### Tuning
- **Optimisation bayésienne** : Optuna, Hyperopt
- **Grid/Random Search** : Exploration systématique
- **Early stopping** : Prévention de l'overfitting
- **Learning rate scheduling** : Cosine annealing, warmup

---

## 📊 Projets

### [À compléter avec les fichiers du projet]

---

## 🛠️ Stack Technique

| Catégorie | Technologies |
|-----------|-------------|
| **Frameworks** | PyTorch, TensorFlow, Keras |
| **Vision** | torchvision, albumentations, timm |
| **Tuning** | Optuna, Ray Tune |
| **Visualisation** | Matplotlib, Seaborn, TensorBoard |

---

**Dernière mise à jour** : Août 2026  
**Contact** : cyril.bgs.dev.tech@gmail.com

````

---

### 📄 `vigilance/README.md`

*192 lignes · 1452 mots*

````markdown
# 🔧 Vigilance — Détection d'Anomalies Temps Réel (MLOps)

**Vision** : plateforme complète de détection d'anomalies en temps réel, démontrant une maîtrise bout-en-bout du MLOps — de la modélisation à la mise en production, avec observabilité et gestion du cycle de vie des alarmes.

**Contexte** : projet personnel, conçu comme un système (event model, workers découplés, registries versionnés) et non comme une suite de scripts  
**Durée** : 1 200+ heures de développement (2025-2026)  
**Périmètre** : 3 machines simulées (capteurs numériques, flux 1 event/s/machine), extensible par simple enregistrement de dataset

**Où en est ce projet** :
- ✅ Fait et fonctionnel : pipeline de détection (3 canaux + fusion), cycle de vie d'alarme, dashboard 40+ pages, observabilité Prometheus/Grafana, résilience (DLQ, backups, reprise après crash)
- 🚧 Prévu, pas encore construit : boucle de feedback opérateur (validation humaine → réentraînement automatique), score de santé agrégé par machine
- 🔭 Exploratoire : GATv2/Transformer sur graphes de capteurs (prototype existant, pas intégré au pipeline)

---

::: {.panel-tabset}

## 🧑‍💼 Vue d'ensemble

**En une phrase** : un système qui surveille en continu des capteurs industriels et prévient automatiquement quand quelque chose d'anormal se produit — avant que ça ne devienne une panne coûteuse.

**Le problème** : sur une ligne de production, un capteur qui dérive lentement (roulement qui s'use, capteur qui se désétalonne) passe souvent inaperçu jusqu'à la panne. Détecter ce genre de signal faible, en continu et sans intervention humaine, est la promesse du "monitoring intelligent" — le même principe que les outils de supervision utilisés par Netflix ou Uber pour surveiller leurs services, appliqué ici à des capteurs physiques.

**Ce que le système fait concrètement** :
- Il regarde chaque capteur en continu et compare son comportement à trois façons différentes de définir "anormal" (pour ne pas rater un type de dérive qu'une seule méthode manquerait)
- Quand une anomalie est confirmée, il ouvre un ticket unique (pas un spam d'alertes répétées pour le même problème) et lui donne un niveau de gravité
- Un tableau de bord affiche en direct l'état de toutes les machines, avec une explication de *pourquoi* chaque alerte a été levée — pas juste "anomalie détectée", mais "ce facteur précis est responsable"
- Le système sait aussi surveiller sa propre santé : temps de réponse, erreurs, charge — comme le ferait une équipe SRE pour un site web

**Pourquoi c'est difficile** : le vrai défi n'est pas de détecter une anomalie évidente, mais d'éviter à la fois les fausses alertes (qui usent la confiance des opérateurs) et les anomalies manquées — tout en restant utilisable en continu, sans surveillance humaine constante.

**Ce que ça démontre** : la capacité à concevoir un système complet — pas juste un modèle qui prédit, mais tout ce qu'il faut autour pour que ce modèle soit fiable, observable et utilisable en production.

## 🔧 Détails techniques

## 🏗️ Architecture Réelle du DAG (9 workers)

```
                        ┌──────────────────────────────────────┐
                        │   SIMULATEUR HAUTE RÉSILIENCE        │
                        │   3 machines · reprise après restart │
                        │   (index persisté Redis) · bruit 2%  │
                        └──────────────────┬───────────────────┘
                                           ▼
                                   worker_features
                                           │
            ┌──────────────┬───────────────┼────────────────┬──────────────┐
            ▼              ▼               ▼                ▼              │
      unsup_stat    unsup_temp_point  unsup_temp_seq   sensor_fault       │
   (IsolationForest) (résidu Ridge     (reconstruction  (règles capteur : │
                      sur 8 lags)       PCA fenêtres 16) STUCK, etc.)     │
            │              │               │                │             │
            └──────────────┴───────┬───────┘                │             │
                                   ▼  barrière à 3          │             │
                              worker_sup (XGBoost)          │             │
                                   │                        │             │
                                   └──────────┬─────────────┘             │
                                              ▼  barrière à 2             │
                                  worker_model_interpreter (SHAP)         │
                                              ▼                           │
                                  worker_correlation_drift                │
                                              ▼                           │
                              worker_novelty_rules_unsup_sup ─────────────┘
                                              │
                                              ▼
                        Dashboard (Redis list + Pub/Sub) + cycle de vie d'alarme
```

**Choix de topologie défendus** :
- `sensor_fault` (règles déterministes) ne bloque jamais le canal ML — il rejoint à la barrière SHAP
- Barrières de synchronisation **atomiques** dans Redis (HSET/HINCRBY + TTL 120 s) : un worker en panne n'immobilise pas le pipeline
- Détection de **nouveauté** par croisement : l'unsupervisé détecte ET le supervisé ne catalogue pas → anomalie hors des patterns connus

---

## ⚙️ Exécution distribuée

| Composant | Réalité technique |
|-----------|-------------------|
| **Pool CPU** | 3 réplicas de workers universels (consomment toutes les queues `queue:cpu:*`) |
| **Pool GPU** | 1 worker CUDA 12.8 (queues `queue:gpu:*`) |
| **Synchronisation** | Queues Redis par étape, barrières multi-parents, fusion des prédictions |
| **Résilience** | Dead Letter Queue rejouée (30 s), archiveur Parquet (300 s), backup des registries (1 h, 24 rétentions) |
| **Registries** | JSON versionnés (modèles, features, seuils, alertes, drift, data_versions) — écriture atomique write-tmp → `os.replace` |

### Détecteurs (3 canaux réellement décorrélés)

| Canal | Algorithme | Coût d'inférence |
|-------|-----------|------------------|
| Statique | IsolationForest | ~1 ms/event |
| Temporel ponctuel | Résidu de prévision Ridge sur 8 lags | 0.05 ms/event |
| Temporel séquentiel | Reconstruction PCA sur fenêtres de 16 pas | 0.12 ms/event |

Historique par machine **partagé entre réplicas** via Redis (1 aller-retour par event), calibration sigmoïde alignée (p97 train → proba 0.5), warm-up dégradé propre.

---

## 🎫 Cycle de vie d'alarme — un épisode = un ticket

Machine à états côté backend (pas dans l'UI) :

```
IDLE ──(N ticks anormaux consécutifs)──► OPEN (1 ticket)
OPEN ──(ticks anormaux)──► même ticket : occurrences++, pic, escalade de sévérité
OPEN ──(hystérésis : N ticks normaux consécutifs)──► AUTO_RESOLVED
```

- Un tick normal isolé ne fragmente pas l'épisode (anti-scintillement)
- Concurrence des 3 réplicas gérée **sans verrou** : `SET NX` à l'ouverture, `GETDEL` à la clôture → un seul écrivain par transition
- Clôture opérateur avec cooldown anti-réouverture ; champs opérateur (assignation, notes) jamais écrasés par le backend

---

## 📊 Dashboard Streamlit (40+ pages, 7 sections)

Navigation native `st.navigation`, matrice **RASCI par page** (opérateur / analyste / technicien / admin) :

| Section | Contenu |
|---------|---------|
| 📡 Monitoring | Global live, monitoring local, comparaison de flotte, pires instabilités, dérives |
| 🚨 Alertes | Alertes actives (SLA countdown), assignation, escalade, événements similaires passés |
| 🔍 Investigation | Étude d'anomalie, graphe causal, analyse contrastive, décisions modèles, replay |
| ✅ Feedback | Validation d'anomalies, corrections, qualité des labels |
| 📈 Reporting | Statistiques d'anomalies, historique maintenance, rapports planifiés |
| 🔧 Technicien | Contrôle bootstrap, gestion modèles/seuils, workers du DAG, feature sets |
| ⚙️ Admin | Règles d'alertes, santé système, audit log, gestion utilisateurs |

---

## 🔭 Observabilité

- **Prometheus** : latence et erreurs **par étape du DAG** (`worker_step_duration_seconds`, `worker_step_errors_total`), métriques Redis (exporter dédié)
- **Grafana** : dashboards pipeline + infrastructure, embarquables dans le cockpit
- **cAdvisor** : CPU/RAM par conteneur
- **SLA opérationnel** : countdown par sévérité d'alerte, suivi des dépassements dans le cockpit

---

## 🧠 Interprétabilité intégrée au flux

- SHAP calculé **par event** dans le pipeline (worker dédié), facteur principal remonté jusqu'à la carte d'alerte
- Profils de normalité par cluster (z-mean + SHAP) calculés au bootstrap et versionnés au registre
- Corrélations baseline par machine → détection de dérive de corrélation en ligne

---

## 🔄 Bootstrap « Cartographe »

- Entraînement complet d'une machine (5 modèles + profils d'interprétation) : **~1,5 s**
- Skip **par modèle** (fichier présent → chargé pour le vote, absent → ré-entraîné)
- Vote majoritaire 2/3 des canaux non supervisés → clusters → classifieur supervisé → règles de nouveauté

---

## 🛠️ Stack technique réelle

| Catégorie | Technologies |
|-----------|-------------|
| **Langages** | Python 3.11 |
| **Data** | Polars, Pandas, NumPy, Parquet |
| **ML** | Scikit-learn, XGBoost, PyTorch (CUDA 12.8) |
| **Interprétabilité** | SHAP |
| **Infrastructure** | Docker Compose (14 services), Redis 7 |
| **Monitoring** | Prometheus, Grafana, cAdvisor, redis-exporter |
| **Dashboard** | Streamlit ≥ 1.36 (st.navigation) |

---

## 🎯 Compétences démontrées

- **Architecture événementielle** : DAG distribué, barrières atomiques, workers découplés, fusion d'états
- **Fiabilité** : DLQ, archivage, backups, reprise exacte après redémarrage, dégradation propre (warm-up, TTL)
- **Gestion d'alarmes** : machine à états, hystérésis, escalade, déduplication en épisode unique — le cœur métier d'un système de monitoring industriel
- **MLOps** : registries versionnés, bootstrap conditionnel, compatibilité descendante des modèles picklés
- **Observabilité** : métriques par étape, SLA, monitoring infra
- **UX opérationnelle** : 40+ pages organisées par rôle RASCI, du cockpit temps réel à l'audit

---

## 🚀 Évolutions prévues

- **Court terme** : boucle de feedback fermée avec [Aegis-RCA](../aegis-rca/) — les diagnostics de cause racine validés (ou corrigés) par un opérateur deviennent des labels pour réentraîner la couche supervisée au-delà du binaire anomalie/pas-anomalie ; score de santé agrégé par machine, sparkline d'épisode sur les cartes d'alerte, Redis comme source de vérité unique des tickets
- **Moyen terme** : GATv2/Transformer sur graphes de capteurs (prototype existant), online learning, multi-sites
- **Long terme** : RUL (durée de vie restante), maintenance prescriptive

:::

---

**Code source** : [github.com/cyril-bgs-dev-tech/vigilance](https://github.com/cyril-bgs-dev-tech/vigilance)  
**Dernière mise à jour** : Août 2026  
**Contact** : cyril.bgs.dev.tech@gmail.com

````
