🤖 Configuration de l’Assistant IA Local - Installateur de Base

Description

Script d’installation automatisée pour configurer un assistant IA local utilisant les modèles llama.cpp. Cet installateur est conçu pour être simple, direct et facile à utiliser, fournissant une base solide pour interagir avec des modèles de langage locaux.

Caractéristiques principales

🔧 Configuration simple et intuitive
	•	Installation guidée : configuration interactive étape par étape
	•	Validation automatique : vérifie les prérequis et les chemins
	•	Configuration adaptative : s’ajuste à différents environnements
	•	Structure modulaire : architecture organisée et extensible

🎯 Fonctionnalités principales
	•	Client LLM : communication directe avec llama.cpp
	•	Gestionnaire de fichiers : opérations sûres de lecture/écriture
	•	Exécuteur de commandes : exécution contrôlée du système
	•	Configuration flexible : JSON configurable

📁 Architecture modulaire

src/
├── core/           # Moteur principal de l’assistant
├── llm/            # Client pour llama.cpp
├── file_ops/       # Gestion des fichiers
└── commands/       # Exécution des commandes

Prérequis système
	•	Python 3.11+
	•	llama.cpp compilé
	•	Modèle GGUF compatible
	•	pip3 pour les dépendances Python
	•	Système d’exploitation : macOS, Linux

Installation rapide

1. Téléchargement et exécution

# Télécharger le script
curl -O https://raw.githubusercontent.com/ton-utilisateur/asistente-basico/main/setup_asistente_basico.sh

# Rendre exécutable
chmod +x setup_asistente_basico.sh

# Lancer l’installation
./setup_asistente_basico.sh

2. Configuration interactive

Le script vous demandera :

Répertoire du projet :

Répertoire du projet [/Users/ton-utilisateur/assistant-ia]: 

Chemin du modèle GGUF :

Chemin du modèle GGUF [/Users/ton-utilisateur/modele/modele.gguf]: 

Chemin de llama-cli :

Chemin de llama.cpp [/Users/ton-utilisateur/llama.cpp/build/bin/llama-cli]: 

3. Confirmation

Configuration sélectionnée :
Répertoire du projet : /Users/ton-utilisateur/assistant-ia
Modèle : /Users/ton-utilisateur/modele/modele.gguf
Llama.cpp : /Users/ton-utilisateur/llama.cpp/build/bin/llama-cli

Continuer avec cette configuration ? (y/N)

Structure générée

assistant-ia/
├── src/
│   ├── main.py                 # Point d’entrée principal
│   ├── core/
│   │   ├── assistant.py        # Classe principale de l’assistant
│   │   └── config.py           # Gestion de la configuration
│   ├── llm/
│   │   └── client.py           # Client llama.cpp
│   ├── file_ops/
│   │   └── manager.py          # Gestion des fichiers
│   └── commands/
│       └── runner.py           # Exécution des commandes
├── config/
│   └── settings.json           # Configuration principale
├── tools/                      # Outils additionnels
├── tests/                      # Tests système
├── logs/                       # Fichiers journaux
└── examples/                   # Exemples d’utilisation

Utilisation basique

Commande principale

cd /chemin/vers/ton/assistant-ia
python3 src/main.py "Quels fichiers Python se trouvent dans ce projet ?"

Mode interactif

python3 src/main.py
🤖 Assistant IA Local - Mode interactif
Tapez 'exit' pour quitter, 'help' pour l’aide

💬 > explique le fichier main.py
🤖 Le fichier main.py est le point d’entrée...

💬 > exit
À bientôt ! 👋

Paramètres en ligne de commande

# Utiliser une configuration spécifique
python3 src/main.py --config config/custom.json "analyse ce projet"

# Mode verbeux
python3 src/main.py --verbose "liste les fichiers Python"

# Aide
python3 src/main.py --help

Configuration

Fichier de configuration (config/settings.json)

{
  "llm": {
    "model_path": "/chemin/vers/ton/modele.gguf",
    "llama_bin": "/chemin/vers/llama-cli",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": true,
    "backup_files": true,
    "max_file_size": 1048576,
    "supported_extensions": [".py", ".js", ".ts", ".json", ".md", ".txt", ".sh"]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/assistant.log"
  }
}