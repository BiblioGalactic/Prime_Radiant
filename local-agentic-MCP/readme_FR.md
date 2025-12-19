🤖 MCP Local - Chat IA avec Outils Système

Système complet Model Context Protocol avec 11 outils et mode agentique pour votre IA locale

╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       Transformez votre LLM local en un assistant puissant ║
║       avec accès à votre système d'exploitation            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝


⸻

📋 Table des matières
	•	Qu’est-ce que c’est ?
	•	Caractéristiques
	•	Prérequis
	•	Installation
	•	Utilisation de base
	•	Mode agentique
	•	Les 11 outils
	•	Exemples pratiques
	•	Configuration avancée
	•	Dépannage
	•	Architecture
	•	Crédits

⸻

🎯 Qu’est-ce que c’est ?

MCP Local est un système qui connecte votre modèle de langage local (comme Mistral, Llama, etc.) à de véritables outils de votre système d’exploitation.

Sans MCP :

👤 Utilisateur : "Liste mes fichiers Python"
🤖 IA : "Désolé, je ne peux pas accéder à votre système de fichiers"

Avec MCP :

👤 Utilisateur : "Liste mes fichiers Python"
🤖 IA : [RECHERCHER] ✓
       J'ai trouvé 12 fichiers : main.py, utils.py, config.py...

C’est comme donner des mains à votre IA pour qu’elle interagisse avec votre ordinateur 🦾

⸻

✨ Caractéristiques

🔧 11 outils complets
	•	✅ Lire et écrire des fichiers
	•	✅ Exécuter des commandes bash
	•	✅ Parcourir les répertoires
	•	✅ Rechercher des fichiers et du contenu
	•	✅ Interroger des API HTTP
	•	✅ Télécharger des fichiers depuis des URL
	•	✅ Compresser/décompresser (zip, tar, tar.gz)
	•	✅ Opérations Git (status, log, diff, branch)
	•	✅ Surveillance système (RAM, CPU, disque)
	•	✅ Recherche de contenu (grep)

🧠 Mode agentique

La fonctionnalité phare ! L’IA peut enchaîner plusieurs actions automatiquement :

👤 : "télécharge le README de GitHub et compresse tous les markdown"

🤖 [MODE AGENTIQUE]
   📋 Plan : 3 étapes
   🔄 Téléchargement... ✅
   🔄 Recherche *.md... ✅  
   🔄 Compression... ✅
   
   ✅ J'ai téléchargé le README (3.4KB), trouvé 5 markdown
      et les ai compressés en docs.zip (45KB)

🔒 Sécurité intégrée
	•	❌ Commandes dangereuses bloquées (rm, dd, sudo, etc.)
	•	🛡️ Écriture limitée à $HOME ou /tmp
	•	⏱️ Timeouts automatiques
	•	📦 Limites de taille de fichier (10MB)

🎨 Interface conviviale
	•	💬 Chat interactif
	•	📊 Mode verbose pour débogage
	•	🎯 Détection automatique du mode agentique
	•	⚡ Réponses rapides et claires

⸻

📦 Prérequis

Avant d’installer, assurez-vous d’avoir :

Obligatoire

✅ Python 3.8 ou supérieur
✅ pip3
✅ Un modèle GGUF (Mistral, Llama, etc.)
✅ llama.cpp compilé avec llama-cli

Optionnel

🔧 git (pour l'outil Git)
🔧 curl/wget (inclus sur macOS/Linux)

Systèmes supportés
	•	✅ macOS (testé)
	•	✅ Linux (testé)
	•	⚠️ Windows (via WSL)

⸻

🚀 Installation

Étape 1 : Télécharger l’installateur

# Option A : Cloner le dépôt
git clone https://github.com/tu-repo/mcp-local.git
cd mcp-local

# Option B : Télécharger le script directement
curl -O https://tu-url/mcp_setup.sh
chmod +x mcp_setup.sh

Étape 2 : Exécuter l’installateur

./mcp_setup.sh

Étape 3 : Configurer les chemins

L’installateur vous demandera deux chemins :

🎯 CONFIGURATION INITIALE
==========================================

📍 Étape 1/2 : Chemin de l'exécutable llama-cli
   Exemple : /usr/local/bin/llama-cli
   ou : /Users/ton-utilisateur/llama.cpp/build/bin/llama-cli
   Chemin complet : _

📍 Étape 2/2 : Chemin du modèle GGUF
   Exemple : /Users/ton-utilisateur/modeles/mistral-7b-instruct.gguf
   Chemin complet : _

Étape 4 : Installation automatique

Le script effectuera automatiquement :
	1.	✅ Création d’un environnement virtuel Python
	2.	✅ Installation des dépendances (flask, psutil, requests)
	3.	✅ Génération d’un serveur MCP (11 outils)
	4.	✅ Génération d’un client avec mode agentique
	5.	✅ Sauvegarde de la configuration

✅ INSTALLATION TERMINÉE

╔════════════════════════════════════════╗
║     MCP LOCAL - MENU PRINCIPAL         ║
║     💪 11 Outils + Mode agentique       ║
╚════════════════════════════════════════╝

  1) 💬 Démarrer le chat (avec mode agentique)
  2) 🔧 Voir les outils MCP (11)
  3) ⚙️  Reconfigurer les chemins
  4) 🚪 Quitter


⸻

💬 Utilisation de base

Démarrer le chat

./mcp_setup.sh
# Choisir l'option 1) Démarrer le chat

Commandes du chat

👤 Vous : _

Commandes disponibles :
  agentico on/off  → Activer/désactiver le mode agentique
  verbose on/off   → Afficher les logs détaillés
  herramientas     → Lister les 11 outils
  salir            → Fermer le chat

Exemple de conversation normale

👤 Vous : liste les fichiers sur mon bureau

🤖 IA: [LISTER] ✓
   Vous avez 23 éléments sur votre bureau : Documents/, Downloads/,
   image.png, notes.txt...

👤 Vous : combien de RAM libre ai-je ?

🤖 IA: [MEMOIRE] ✓
   Vous avez 8.5GB de RAM libre sur 16GB (53% libre)


⸻

🧠 Mode agentique

Le mode agentique permet à l’IA d’enchaîner plusieurs actions automatiquement sans que vous donniez chaque commande séparément.

Comment l’activer ?

Option 1 : Manuelle

👤 Vous : agentico on
🤖 Mode agentique : ACTIVÉ

Option 2 : Automatique (détection par mots-clé)
	•	et puis
	•	ensuite
	•	et compresse
	•	et recherche
	•	faites tout
	•	automatique

Exemple complet

Sans mode agentique (3 commandes séparées) :

👤: télécharge le README
🤖: ✓

👤: recherche tous les markdown
🤖: ✓

👤: compresse les fichiers
🤖: ✓

Avec mode agentique (1 seule commande) :

👤: télécharge le README de GitHub et ensuite compresse tous les markdown

🤖 [MODE AGENTIQUE ACTIVÉ]
📋 Plan : 3 étapes

🔄 Étape 1/3 : TÉLÉCHARGER:https://raw.githubusercontent.com/...
   ✅ TÉLÉCHARGÉ

🔄 Étape 2/3 : RECHERCHER:~/Desktop:*.md
   ✅ TROUVÉ

🔄 Étape 3/3 : COMPRESSER:~/Desktop → ~/Desktop/docs.zip
   ✅ COMPRESSÉ

🔄 Synthèse des résultats...

✅ Tâche complétée

🤖 J'ai téléchargé le README (3456 octets), trouvé 5 fichiers 
   markdown sur votre bureau et les ai compressés en docs.zip 
   (45KB). Tout est prêt !

Mode verbose (debug)

Pour visualiser le processus interne :

👤 Vous : verbose on
📊 Mode verbose : ACTIVÉ

👤 Vous : télécharge X et compresse Y

🧠 Planification des étapes...
📋 Étapes planifiées : ["TÉLÉCHARGER:...", "RECHERCHER:...", "COMPRESSER:..."]
🔍 Exécution : TÉLÉCHARGER:...
   ✅ TÉLÉCHARGÉ
🔍 Exécution : RECHERCHER:...
   ✅ TROUVÉ
...


⸻

🛠️ Les 11 outils

1. 📖 Lire un fichier

👤: lis le fichier README.md
🤖: [LIRE] ✓
   Le fichier contient la documentation sur...

	•	📦 Max : 64KB
	•	🔒 Texte seulement

2. ✍️ Écrire un fichier

👤: crée test.txt avec "Bonjour le monde"
🤖: [ÉCRIRE] ✓ (11 octets)
   Fichier créé dans ~/test.txt

	•	📦 Max : 10MB
	•	🔒 Uniquement $HOME ou /tmp
	•	🔀 Modes : w (écraser) ou a (ajouter)

3. 📁 Lister un répertoire

👤: que contient mon dossier Downloads ?
🤖: [LISTER] ✓
   45 éléments : documents/, images/, video.mp4...

	•	📊 Affiche : nom, type, taille, date
	•	📦 Limite : 100 items

4. 🔍 Rechercher des fichiers

👤: trouve tous mes fichiers Python
🤖: [RECHERCHER] ✓
   12 fichiers trouvés : main.py, utils.py...

	•	🌲 Recherche récursive
	•	🎯 Patterns glob : *.py, test*.txt, etc.
	•	📦 Limite : 50 fichiers

5. 🔎 Rechercher dans le contenu (Grep)

👤: cherche "TODO" dans les fichiers Python
🤖: [GREP] ✓ (8 correspondances)
   main.py:42: # TODO: Implémenter validation
   utils.py:15: # TODO: Optimiser l'algorithme

	•	📄 Uniquement fichiers <1MB
	•	🎯 Regex insensible à la casse
	•	📦 Limite : 50 correspondances

6. ⚡ Exécuter une commande

👤: exécute ls -la
🤖: [COMMANDE] ✓
   total 256
   drwxr-xr-x  15 user  staff   480 Oct 10 10:30 .
   ...

	•	❌ Bloqué : rm, dd, sudo, su, mkfs
	•	⏱️ Timeout : 10 secondes
	•	📦 Sortie : max 4KB

7. 💾 Consulter la mémoire / ressources

👤: quelles ressources ai-je de dispo ?
🤖: [MEMOIRE] ✓
   RAM : 8.5GB libre sur 16GB
   CPU : 35% d'utilisation (8 cœurs)
   Disque : 245GB libres sur 500GB

8. 📥 Télécharger un fichier

👤: télécharge https://example.com/file.pdf
🤖: [TÉLÉCHARGER] ✓ (2.5MB)
   Fichier enregistré dans ~/Downloads/file.pdf

	•	🌐 Protocoles : http:// et https://
	•	📦 Limite : 10MB
	•	⏱️ Timeout : 30 secondes

9. 🗜️ Compresser / Décompresser

👤: compresse mon dossier documents
🤖: [COMPRESSER] ✓
   Dossier compressé en documents.zip (12MB)

	•	📦 Formats : zip, tar, tar.gz
	•	🔄 Opérations : compresser, décompresser

10. 🔧 Opérations Git

👤: montre le status git
🤖: [GIT] ✓
   On branch main
   Changes not staged for commit:
     modified: src/main.py

	•	✅ Autorisé : status, log, diff, branch, remote
	•	❌ Bloqué : commit, push, pull (lecture seule)

11. 🌐 Interroger une API

👤: interroge l'API example.com
🤖: [API] ✓ (200)
   Status: OK
   Réponse: {"data": "exemple"}

	•	📡 Méthodes : GET, POST, PUT, DELETE, PATCH
	•	⏱️ Timeout : 10 secondes
	•	📦 Réponse : max 4KB

⸻

💡 Exemples pratiques

Exemple 1 : Analyse de projet

👤: agentico on

👤: liste tous les fichiers Python et cherche les TODOs

🤖 [MODE AGENTIQUE]
   Étape 1 : Recherche *.py... ✅
   Étape 2 : Recherche 'TODO'... ✅
   
   J'ai trouvé 12 fichiers Python avec 8 TODOs :
   - main.py : 3 TODOs
   - utils.py : 2 TODOs
   - config.py : 3 TODOs

Exemple 2 : Sauvegarde automatisée

👤: trouve tous les fichiers importants et compresse en backup

🤖 [MODE AGENTIQUE]
   Étape 1 : Recherche des fichiers... ✅
   Étape 2 : Compression... ✅
   
   J'ai créé backup.zip avec 45 fichiers (234MB)

Exemple 3 : Surveillance système

👤: affiche le git status et les ressources système

🤖 [MODE AGENTIQUE]
   Étape 1 : Git status... ✅
   Étape 2 : Consultation ressources... ✅
   
   Git : 3 fichiers modifiés sur la branche main
   Système : RAM 45% libre, CPU 25%, Disque 50% libre

Exemple 4 : Workflow complet

👤: télécharge le README GitHub, cherche sur mon bureau 
    et compresse tous les markdown trouvés

🤖 [MODE AGENTIQUE]
   📋 Plan : 3 étapes
   
   Étape 1 : Téléchargement depuis GitHub... ✅ (3.4KB)
   Étape 2 : Recherche *.md sur Desktop... ✅ (5 fichiers)
   Étape 3 : Compression... ✅ (45KB)
   
   ✅ J'ai téléchargé le README, trouvé 5 markdown et 
      les ai compressés en docs.zip. Tout est sur votre bureau.


⸻

⚙️ Configuration avancée

Changer le modèle ou le chemin de llama-cli

./mcp_setup.sh
# Choisir l'option 3) Reconfigurer les chemins

Éditer la configuration manuellement

nano ~/.mcp_local/config.env

# Configuration MCP Local
LLAMA_CLI="/chemin/vers/ton/llama-cli"
MODELE_GGUF="/chemin/vers/ton/modele.gguf"

Variables d’environnement

# Activer le debug du serveur MCP
export MCP_DEBUG=1

# Lancer
./mcp_setup.sh

Structure des fichiers

~/.mcp_local/
├── config.env           # Ta configuration
├── venv/                # Environnement Python
├── mcp_server.py        # Serveur avec 11 outils
└── chat_mcp.py          # Client avec mode agentique


⸻

🔧 Dépannage

Problème : “llama-cli introuvable”

Solution :

# Vérifier que llama.cpp est compilé
cd ~/llama.cpp
cmake -B build
cmake --build build

# Vérifier le chemin
ls ~/llama.cpp/build/bin/llama-cli

# Reconfigurer MCP
./mcp_setup.sh
# Option 3) Reconfigurer les chemins

Problème : “Modèle introuvable”

Solution :

# Vérifier que le modèle existe
ls ~/chemin/vers/ton/modele.gguf

# Si vous n'avez pas de modèle, téléchargez-en un
# Exemple : Mistral 7B
wget https://huggingface.co/...modele.gguf

# Reconfigurer
./mcp_setup.sh
# Option 3) Reconfigurer les chemins

Problème : “Erreur lors de l’installation des dépendances Python”

Solution :

# Vérifier Python
python3 --version  # Doit être >= 3.8

# Supprimer l'environnement virtuel corrompu
rm -rf ~/.mcp_local/venv

# Réinstaller
./mcp_setup.sh

Problème : “Le mode agentique ne fonctionne pas correctement”

Solution :

# Activer le mode verbose pour diagnostiquer
👤: verbose on
👤: ta commande problématique

# Le mode agentique dépend de la qualité du modèle
# Modèles recommandés :
# - Mistral 7B Instruct (minimum)
# - Llama 3 8B Instruct (mieux)
# - Mixtral 8x7B (optimal)

Problème : “Timeout sur les requêtes”

Solution :

# Si le modèle est lent, augmenter le timeout
# Éditer ~/.mcp_local/chat_mcp.py

# Ligne ~40 :
IA_CMD = [
    config.get('LLAMA_CLI', 'llama-cli'),
    "--model", config.get('MODELE_GGUF', ''),
    "--n-predict", "512",
    "--temp", "0.7",
    "--ctx-size", "4096"
]

# Ajouter GPU si disponible :
# "--n-gpu-layers", "35"

Problème : “Commande bloquée pour sécurité”

Solution :
Ceci est volontaire. Les commandes dangereuses sont bloquées :
	•	❌ rm -rf
	•	❌ dd
	•	❌ sudo
	•	❌ su

Si vous avez vraiment besoin d’exécuter des commandes privilégiées, faites-le manuellement en dehors du MCP.

⸻

🏗️ Architecture

┌─────────────────────────────────────────────┐
│           👤 Utilisateur (VOUS)             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      💬 Client Chat (chat_mcp.py)           │
│  ┌────────────────────────────────────┐     │
│  │  🧠 Mode agentique                  │     │
│  │  - Planification des étapes        │     │
│  │  - Exécution séquentielle          │     │
│  │  - Synthèse des résultats          │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│        🤖 Modèle LLM Local                  │
│     (Mistral, Llama, Mixtral, etc.)         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│   🔧 Serveur MCP (mcp_server.py)            │
│  ┌────────────────────────────────────┐     │
│  │  11 Outils :                        │     │
│  │  ✓ Fichiers (lire/écrire)          │     │
│  │  ✓ Système (mémoire/commandes)     │     │
│  │  ✓ Réseau (API/téléchargements)    │     │
│  │  ✓ Recherche (fichiers/contenu)    │     │
│  │  ✓ Utilitaires (git/compression)   │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     💻 Votre Système d'Exploitation         │
│  (Fichiers, Commandes, Ressources)         │
└─────────────────────────────────────────────┘

Flux d’une requête normale

1. Utilisateur envoie une commande
   👤 "liste les fichiers Python"
   
2. Le client interroge le LLM
   💬 → 🤖 "Quelle outil utiliser ?"
   
3. Le LLM choisit l'outil
   🤖 → 💬 "[UTILISER_OUTIL:RECHERCHER:.:*.py]"
   
4. Le client appelle le serveur MCP
   💬 → 🔧 {"method": "rechercher_fichiers", ...}
   
5. Le serveur exécute l'outil
   🔧 → 💻 Recherche réelle sur le système
   
6. Le serveur renvoie les résultats
   🔧 → 💬 {"result": ["main.py", ...]}
   
7. Le client renvoie les résultats au LLM
   💬 → 🤖 "Fichiers trouvés : ..."
   
8. Le LLM génère une réponse naturelle
   🤖 → 💬 "J'ai trouvé 12 fichiers Python : ..."
   
9. L'utilisateur voit la réponse
   💬 → 👤 "J'ai trouvé 12 fichiers Python : ..."

Flux du mode agentique

1. L'utilisateur donne une commande complexe
   👤 "télécharge X puis compresse Y"
   
2. Le client détecte le mode agentique
   💬 [Détecte mots-clé "puis", "ensuite"]
   
3. Le LLM planifie les étapes
   💬 → 🤖 "Décomposer en étapes"
   🤖 → 💬 ["TÉLÉCHARGER:...", "RECHERCHER:...", "COMPRESSER:..."]
   
4. Le client exécute les étapes séquentiellement
   💬 → 🔧 Étape 1 : TÉLÉCHARGER ✅
   💬 → 🔧 Étape 2 : RECHERCHER ✅
   💬 → 🔧 Étape 3 : COMPRESSER ✅
   
5. Le LLM synthétise les résultats
   💬 → 🤖 "Résume tout ce qui a été fait"
   🤖 → 💬 "J'ai téléchargé, recherché et compressé..."
   
6. L'utilisateur reçoit le résumé final
   💬 → 👤 "✅ Tâche complétée : ..."


⸻

📚 Ressources additionnelles

Model Context Protocol (MCP)
	•	📖 Spécification MCP
	•	🔗 GitHub Anthropic MCP

Modèles recommandés
	•	🦙 Llama 3 8B Instruct
	•	🌟 Mistral 7B Instruct
	•	🚀 Mixtral 8x7B

llama.cpp
	•	🔗 GitHub llama.cpp
	•	📖 Documentation

⸻

🎓 Cas d’utilisation

Pour les développeurs
	•	✅ Automatiser les tâches répétitives
	•	✅ Analyser le code et trouver les TODOs
	•	✅ Gérer des dépôts Git
	•	✅ Générer de la documentation
	•	✅ Surveiller les ressources système

Pour les administrateurs système
	•	✅ Automatiser les backups
	•	✅ Surveiller les logs
	•	✅ Gérer les fichiers de configuration
	•	✅ Rechercher dans les logs
	•	✅ Compresser/décompresser les fichiers

Pour les utilisateurs avancés
	•	✅ Organiser automatiquement les fichiers
	•	✅ Télécharger et traiter du contenu web
	•	✅ Rechercher de l’information dans des documents
	•	✅ Automatiser des workflows complexes
	•	✅ Intégrer des APIs externes

⸻

🤝 Contribuer

Vous avez des idées pour améliorer MCP Local ? Contribuez !

Idées d’outils supplémentaires
	•	📧 Client mail
	•	📅 Intégration calendrier
	•	🗄️ Opérations base de données
	•	🐳 Intégration Docker
	•	📊 Génération de rapports

Comment contribuer
	1.	Forkez le projet
	2.	Créez une branche (git checkout -b feature/nouvel-outil)
	3.	Committez vos modifications (git commit -am 'Ajout de l'outil X')
	4.	Pushez la branche (git push origin feature/nouvel-outil)
	5.	Ouvrez une Pull Request

⸻

📄 Licence

Ce projet est sous licence MIT. Utilisez-le librement, modifiez-le et partagez-le.

MIT License

Copyright (c) 2025 Gustavo Silva da Costa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


⸻

🙏 Remerciements
	•	Anthropic pour le concept de Model Context Protocol
	•	La communauté llama.cpp pour rendre l’exécution locale de LLM possible
	•	Tous ceux qui contribuent à l’écosystème IA open source

⸻

📞 Support

Des problèmes ? Des questions ? Des suggestions ?
	•	📧 Email : gsilvadacosta0@gmail.com
	•	🆇 Anciennement Twitter 😂 : https://x.com/bibliogalactic

⸻


<div align="center">


⭐ Si ce projet vous plaît, mettez-lui une étoile sur GitHub ⭐

╔════════════════════════════════════════════════════════╗
║                                                        ║
║   Fait avec ❤️ pour la communauté IA locale           ║
║                                                        ║
║   "Donner des mains aux IAs, un outil à la fois"      ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

👨‍💻 Créé par

Gustavo Silva Da Costa (Eto Demerzel) 🤫

🚀 Transformer les IAs locales en assistants puissants

</div>



⸻

Version : 1.0.0
Dernière mise à jour : Octobre 2025
État : ✅ Production

⸻

