🤖 Configuration Assistant IA Local Amélioré

Description

Système d’installation automatisé pour un Assistant IA Local avec capacités agentiques avancées. Ce script configure un environnement de développement complet pour interagir avec des modèles LLaMA locaux, fournissant des fonctionnalités d’analyse de code, gestion de fichiers et exécution de commandes système.

Principales fonctionnalités

🧠 Mode agentique intelligent
	•	Planification automatique : décompose les tâches complexes en sous-tâches spécifiques
	•	Lecture automatique des fichiers : analyse automatiquement les fichiers pertinents du projet
	•	Synthèse sans redondances : combine plusieurs analyses en éliminant les informations répétées
	•	Vérification de la qualité : système automatique de contrôle qualité des réponses

🔧 Fonctionnalités avancées
	•	50+ commandes activées : Git, Docker, NPM, Python, et plus
	•	Protection contre commandes dangereuses : système de sécurité intégré
	•	Gestion intelligente des fichiers : lecture, écriture et analyse de code
	•	Configuration adaptative : s’ajuste automatiquement à l’environnement

🎯 Architecture modulaire
	•	Core : moteur principal de l’assistant
	•	LLM Client : communication avec les modèles llama.cpp
	•	File Manager : gestion sécurisée des fichiers
	•	Command Runner : exécution contrôlée des commandes
	•	Agentic Extension : capacités agentiques avancées

Prérequis système
	•	Python 3.11+
	•	llama.cpp compilé et fonctionnel
	•	Modèle GGUF compatible
	•	Bash 4.0+
	•	Système d’exploitation : macOS, Linux

Installation

1. Téléchargement et installation

# Télécharger le script
curl -O https://raw.githubusercontent.com/tu-usuario/setup-asistente/main/setup_asistente.sh

# Rendre exécutable
chmod +x setup_asistente.sh

# Exécuter l'installation
./setup_asistente.sh

2. Configuration interactive

Le script vous demandera :
	•	Répertoire d’installation : où le projet sera installé
	•	Chemin du modèle GGUF : votre modèle de langage local
	•	Chemin de llama-cli : binaire de llama.cpp

3. Structure générée

asistente-ia/
├── src/
│   ├── core/              # Moteur principal
│   ├── llm/               # Client LLM
│   ├── file_ops/          # Gestion des fichiers
│   └── commands/          # Exécution des commandes
├── config/                # Configuration
├── tools/                 # Outils additionnels
├── tests/                 # Tests système
├── logs/                  # Journaux d'exécution
└── examples/              # Exemples d'utilisation

Utilisation

Commandes de base

# Assistant normal
claudia "explique ce projet"

# Mode agentique
claudia-a "analyse complètement l'architecture"

# Mode verbose (voir le processus interne)
claudia-deep "investigation approfondie des erreurs"

# Aide complète
claudia-help

Exemples de commandes agentiques
	•	"analyse complètement la structure du code"
	•	"investigation approfondie sur la performance"
	•	"mode agentique : optimise tout le code"
	•	"examine en détail les erreurs"

Mode interactif

claudia
💬 > agentic on
💬 > analyse complètement ce projet
💬 > exit

Configuration avancée

Fichier de configuration

{
  "llm": {
    "model_path": "/chemin/vers/ton/modele.gguf",
    "llama_bin": "/chemin/vers/llama-cli",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": false,
    "backup_files": true,
    "supported_extensions": [".py", ".js", ".json", ".md"]
  }
}

Personnalisation
	•	Modèles : changez le chemin du modèle dans config/settings.json
	•	Commandes : modifiez la liste des commandes autorisées dans commands/runner.py
	•	Extensions : ajoutez de nouveaux types de fichiers supportés

Architecture du système

Composants principaux
	1.	LocalAssistant : classe principale qui coordonne tous les composants
	2.	AgenticAssistant : extension fournissant les capacités agentiques
	3.	LlamaClient : interface avec les modèles llama.cpp
	4.	FileManager : gestion sécurisée des fichiers du projet
	5.	CommandRunner : exécution contrôlée des commandes système

Flux agentique
	1.	Planification : décompose la tâche en sous-tâches spécifiques
	2.	Exécution : exécute chaque sous-tâche avec contexte enrichi
	3.	Synthèse : combine les résultats en éliminant les redondances
	4.	Vérification : valide la qualité de la réponse finale

Sécurité

Commandes prohibées
	•	rm, rmdir, dd, shred
	•	sudo, su, chmod, chown
	•	kill, reboot, shutdown

Commandes autorisées
	•	Outils de développement : git, npm, pip, docker
	•	Analyse de fichiers : cat, grep, find, head, tail
	•	Compilation : make, cmake, gradle, maven

Résolution de problèmes

Erreur : “llama-cli introuvable”

# Vérifier l'installation de llama.cpp
which llama-cli

# Mettre à jour le chemin dans la config
vim config/settings.json

Erreur : “Modèle introuvable”

# Vérifier le chemin du modèle
ls -la /chemin/vers/ton/modele.gguf

# Mettre à jour la configuration
claudia --config config/settings.json

Le mode agentique ne fonctionne pas

# Vérifier en mode verbose
claudia-deep "test simple"

# Consulter les logs
tail -f logs/assistant.log

Contribution
	1.	Forkez le dépôt
	2.	Créez une branche pour votre fonctionnalité : git checkout -b feature/nouvelle-fonctionnalite
	3.	Committez vos changements : git commit -am 'Ajouter nouvelle fonctionnalité'
	4.	Pushez la branche : git push origin feature/nouvelle-fonctionnalite
	5.	Ouvrez une Pull Request

Licence

MIT License - voir le fichier LICENSE pour les détails.

Auteur

Gustavo Silva da Costa (Eto Demerzel)

Version

2.0.0 - Système agentique amélioré avec planification intelligente et synthèse sans redondances.

⸻

Pour un support supplémentaire, créez un issue dans le dépôt du projet.
