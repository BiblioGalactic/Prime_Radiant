🤖 AI Cluster – Système Distribué d’Intelligence Artificielle

Traite des requêtes d’IA en parallèle à l’aide de plusieurs machines de ton réseau local (intranet).

Sans cloud • Privé • Évolutif • Open Source

⸻

📋 Description

AI Cluster est un système permettant d’exploiter les ordinateurs inactifs d’un réseau local pour exécuter des modèles d’IA de manière distribuée.
Idéal pour les entreprises souhaitant :
	•	✅ Confidentialité totale – Les données ne quittent jamais ton réseau
	•	✅ Aucun coût cloud – Utilise le matériel existant
	•	✅ Conformité RGPD – Tout reste dans ton infrastructure
	•	✅ Évolutivité – Ajoute facilement de nouvelles machines
	•	✅ Traitement parallèle – Les requêtes sont exécutées simultanément

⸻

🚀 Cas d’Utilisation

Pour les Entreprises
	•	Traiter plusieurs requêtes IA via les ordinateurs du bureau
	•	Analyse distribuée de documents
	•	Génération de contenu en parallèle
	•	Automatisation de tâches répétitives

Pour les Développeurs
	•	Expérimenter avec les systèmes distribués
	•	Apprendre la parallélisation
	•	Tester les performances des modèles
	•	Prototyper rapidement des solutions

⸻

🎯 Caractéristiques
	•	✨ Assistant interactif – Configuration guidée pas à pas
	•	🔐 Configuration SSH automatique – Connexions sans mot de passe
	•	🌐 Multi-machines – Supporte N ordinateurs du réseau
	•	⚖️ Répartition round-robin – Charge équilibrée entre hôtes
	•	📊 Statistiques détaillées – Suivi du traitement
	•	🛡️ Gestion d’erreurs robuste – Continue même en cas d’échec d’une machine

⸻

📦 Prérequis

Sur TOUTES les machines :
	1.	llama.cpp compilé

git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make


	2.	Modèle GGUF téléchargé
	•	Mistral, Llama, Qwen, etc.
	•	Placé au même chemin sur chaque machine
	3.	SSH activé (uniquement sur les machines distantes)

# macOS
sudo systemsetup -setremotelogin on

# Linux
sudo systemctl enable ssh
sudo systemctl start ssh



⸻

⚙️ Installation

1. Télécharger le script

# Cloner le dépôt
git clone https://github.com/BiblioGalactic/ai-cluster
cd ai-cluster

# Ou télécharger directement
curl -O https://raw.githubusercontent.com/BiblioGalactic/ai-cluster/main/ai-cluster.sh
chmod +x ai-cluster.sh

2. Première configuration

./ai-cluster.sh setup

L’assistant te guidera pour :
	•	✅ Détecter llama.cpp et les modèles locaux
	•	✅ Configurer les IPs des machines distantes
	•	✅ Configurer SSH sans mot de passe
	•	✅ Vérifier la connectivité et les fichiers

⸻

📖 Utilisation

Commande de base

./ai-cluster.sh run queries.txt

Fichier de requêtes

Crée un fichier queries.txt avec tes questions (une par ligne) :

Explique ce qu’est un réseau neuronal  
Résume la théorie de la relativité  
Quelle est la capitale du Japon ?  
Écris un haïku sur la technologie  

Autres commandes

# Voir la configuration actuelle
./ai-cluster.sh config

# Tester la connectivité
./ai-cluster.sh test

# Reconfigurer
./ai-cluster.sh setup

# Aide
./ai-cluster.sh help


⸻

🏗️ Architecture

┌─────────────────────────────────────────────────┐
│           ai-cluster.sh (Orchestrateur)         │
└─────────────┬───────────────────────────────────┘
              │
      ┌───────┴────────┬──────────────┬──────────┐
      │                │              │          │
  ┌───▼────┐      ┌───▼────┐    ┌───▼────┐ ┌───▼────┐
  │ Local  │      │ PC 1   │    │ PC 2   │ │ PC N   │
  │ (Mac)  │      │ (SSH)  │    │ (SSH)  │ │ (SSH)  │
  └────────┘      └────────┘    └────────┘ └────────┘
  Query 1,5,9     Query 2,6,10  Query 3,7  Query 4,8

Répartition round-robin :
	•	Requête #1 → Machine locale
	•	Requête #2 → Machine distante 1
	•	Requête #3 → Machine distante 2
	•	Requête #4 → Machine distante 3
	•	Requête #5 → Retour à la machine locale

⸻

🔧 Configuration Avancée

Fichier .ai_cluster_config

Après la configuration, ce fichier est créé :

# Machine locale
LOCAL_LLAMA="/Users/user/modelo/llama.cpp/build/bin/llama-cli"
LOCAL_MODEL="/Users/user/modelo/mistral-7b.gguf"

# Machines distantes (séparées par des virgules)
REMOTE_IPS="192.168.1.82,192.168.1.83"
REMOTE_USER="username"
REMOTE_LLAMA="/home/user/llama.cpp/build/bin/llama-cli"
REMOTE_MODEL="/home/user/mistral-7b.gguf"

# Délai entre connexions SSH (en secondes)
REMOTE_DELAY=10

Tu peux le modifier manuellement si nécessaire.

⸻

📊 Exemple de Sortie

╔═══════════════════════════════════════════════════════════╗
║     🤖 AI CLUSTER – Système Distribué d’IA 🤖             ║
║   Traite des requêtes en parallèle sur ton réseau local   ║
╚═══════════════════════════════════════════════════════════╝

[17:30:00] 🎯 Total de requêtes : 20  
[i] Machines disponibles : 3 (1 locale + 2 distantes)

[17:30:00] 💻 [Locale] Requête #1 : Explique ce qu’est un réseau neuronal…  
[17:30:00] 🌐 [192.168.1.82] Requête #2 : Résume la théorie…  
[17:30:00] 🌐 [192.168.1.83] Requête #3 : Quelle est la capitale…  
[17:30:02] ✓ [Locale] Requête #1 terminée  
[17:30:15] ✓ [192.168.1.82] Requête #2 terminée  
[17:30:18] ✓ [192.168.1.83] Requête #3 terminée  

...

[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
[17:35:00] ✓ ✨ TERMINÉ  
[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
[i] Total traité : 20 requêtes  
[i] Résultats dans : results_cluster/  


⸻

🐛 Dépannage

SSH demande un mot de passe à chaque fois

# Relance le setup pour configurer ssh-copy-id
./ai-cluster.sh setup

“llama-cli introuvable” sur machine distante

Vérifie le chemin dans .ai_cluster_config :

# Sur la machine distante
which llama-cli
# Ou cherche
find ~ -name "llama-cli" 2>/dev/null

Les requêtes ne se traitent pas

# Tester la connectivité
./ai-cluster.sh test

# Vérifier les journaux individuels
cat results_cluster/result_2_*.txt

Script lent sur Mac Mini

Les scripts automatiques dans .zshrc peuvent ralentir SSH.
Ajoute au début du .zshrc des machines distantes :

# Désactiver pour SSH non interactif
[[ -n "$SSH_CONNECTION" ]] && [[ ! -t 0 ]] && return


⸻

🤝 Contribuer

Les contributions sont les bienvenues !
	1.	Fork le projet
	2.	Crée une branche (git checkout -b feature/AmazingFeature)
	3.	Commit tes modifications (git commit -m 'Ajout de AmazingFeature')
	4.	Push la branche (git push origin feature/AmazingFeature)
	5.	Ouvre une Pull Request

⸻

📝 Feuille de Route
	•	Tableau de bord web en temps réel
	•	Support Docker containers
	•	Détection automatique des machines du réseau
	•	Cache des résultats
	•	Système de priorités
	•	Métriques de performance
	•	Intégration Kubernetes

⸻

📄 Licence

Licence MIT – voir le fichier LICENSE

⸻

👨‍💻 Auteur

Gustavo Silva da Costa (BiblioGalactic)
	•	GitHub : @BiblioGalactic
	•	Projet : Réalisme cybernétique appliqué à l’infrastructure d’entreprise

⸻

🙏 Remerciements
	•	llama.cpp – Moteur d’inférence
	•	Anthropic Claude – Assistance au développement
	•	Communauté open-source de l’IA locale

⸻

⚠️ Avertissement

Ce logiciel est fourni “tel quel”, sans aucune garantie.
Son utilisation se fait à tes propres risques.
Les auteurs ne sont pas responsables de pertes de données,
de dysfonctionnements matériels ou de tout dommage lié à son usage.

⸻

📚 Ressources
	•	Documentation de llama.cpp
	•	Modèles GGUF disponibles
	•	Configuration SSH sans mot de passe

⸻

Si ce projet t’est utile, laisse-lui une ⭐ sur GitHub !
