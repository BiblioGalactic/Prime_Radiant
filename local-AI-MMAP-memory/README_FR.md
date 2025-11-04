Mémoire MMAP IA Locale est un lanceur public en Bash + C conçu pour exécuter LLaMA avec plusieurs profils modulaires chargés directement en mémoire via mmap.
Chaque profil représente un contexte IA distinct (technique, philosophique, sécurité, etc.), permettant de gérer les prompts efficacement sans fichiers temporaires.

⸻

🧠 Fonctionnalités
	•	Charge plusieurs profils .txt en mémoire
	•	Sélection du profil actif à l’exécution
	•	Exécute LLaMA de façon interactive avec le contexte chargé via mmap
	•	Portable et open-source : l’utilisateur fournit ses propres chemins
	•	Gestion des erreurs pour les fichiers, mmap et le lancement de LLaMA

⸻

⚙️ Utilisation

./local-AI-MMAP-memory.sh

Suis les étapes pour :
	1.	Entrer ton fichier prompt (.txt)
	2.	Entrer le chemin de l’exécutable llama-cli
	3.	Entrer le chemin de ton modèle .gguf
	4.	Entrer les chemins des profils séparés par des virgules
	5.	Choisir l’indice du profil actif

⸻

🧩 Prérequis
	•	Bash ≥ 5
	•	GCC
	•	LLaMA CLI installé
	•	Modèle local .gguf

⸻

📜 Licence

Open-source — Utilise-le librement, modifie-le et partage-le.