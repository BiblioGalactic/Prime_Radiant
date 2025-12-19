⚡ Prime Radiant — Collection d’assistants d’IA locaux

🧠 J’automatise des idées complexes avec de l’IA locale. Depuis Bash, pour les humains.

⸻

🌟 Qu’est-ce que Prime Radiant

Prime Radiant est une collection d’outils et de configurations pour travailler avec de l’IA locale. Ce dépôt contient des scripts et des systèmes pour automatiser des tâches en utilisant des modèles de langage locaux via llama.cpp.

🎯 Philosophie du projet
	•	Local First : Toute l’IA s’exécute sur votre machine
	•	Bash Centered : Scripts puissants et transparents
	•	Itératif : Amélioration continue à chaque expérimentation

⸻

📦 Outils inclus

🤖 Local AI Assistant

Configureur avancé avec capacités agentiques
	•	Installation automatisée de l’assistant IA local
	•	Mode agentique avec planification intelligente
	•	Gestion sécurisée des fichiers et du code

./setup_asistente.sh

⚔️ Local-CROS (Cross-Referential Optimization)

Système d’évaluation croisée entre modèles
	•	Compare les réponses de plusieurs modèles LLaMA
	•	Évaluation croisée automatique
	•	Synthèse intelligente des réponses

./local-cros.sh "Votre question ici"


⸻

🚀 Démarrage rapide

Prérequis
	•	llama.cpp compilé et fonctionnel
	•	Modèles GGUF (Mistral, LLaMA, etc.)
	•	Bash 4.0+ sur macOS/Linux

Installation de base

git clone https://github.com/BiblioGalactic/Prime_Radiant.git
cd Prime_Radiant

# Explorer les outils disponibles
ls -la

Configuration
	1.	Installer llama.cpp :

git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make

	2.	Télécharger des modèles GGUF :

wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q6_K.gguf


⸻

🛠️ Catalogue des outils

Outil	Objectif	État
Local AI Assistant	Assistant agentique complet	✅ Stable
Local-CROS	Comparateur de modèles	✅ Stable


⸻

🎭 Philosophie de conception

Pourquoi Bash
	•	Transparence : Vous pouvez lire chaque commande
	•	Portabilité : Fonctionne sur systèmes Unix
	•	Simplicité : Sans dépendances complexes

Pourquoi local
	•	Confidentialité : Vos données ne quittent pas votre machine
	•	Contrôle : Vous décidez quels modèles utiliser
	•	Coût : Pas de limites d’API

⸻

📄 Licence

Licence MIT — Usage libre avec attribution.

Auteur

Gustavo Silva da Costa (Eto Demerzel)
🔗 BiblioGalactic

⸻

« La connaissance la plus précieuse est celle que vous pouvez contrôler, améliorer et partager librement. »
— Eto Demerzel, Prime Radiant