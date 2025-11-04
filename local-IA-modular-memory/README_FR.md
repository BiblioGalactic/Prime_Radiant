Version en Français

Mémoire IA Modulaire Locale est un script public en Bash permettant de générer et d’exécuter un prompt complet avec LLaMA à partir de vos notes en Markdown.
Il concatène tous les fichiers .md d’un répertoire, les nettoie et lance une session interactive de LLaMA.

⸻

🧠 Fonctionnalités
	•	Fonctionne avec n’importe quel répertoire contenant des fichiers .md.
	•	Nettoie les espaces et lignes vides tout en conservant l’encodage UTF-8.
	•	Demande les chemins du modèle et de l’exécutable llama-cli.
	•	Mise à jour dynamique optionnelle avant la génération du prompt.

⸻

⚙️ Utilisation

./local_ia_modular_memory.sh

Suivez les instructions :
	1.	Indiquez le répertoire contenant vos fichiers .md.
	2.	Indiquez le chemin vers votre modèle LLaMA (.gguf).
	3.	Indiquez le chemin vers l’exécutable llama-cli.

Le script générera un fichier prompt_completo.txt et lancera une session interactive de LLaMA.

⸻

🧩 Prérequis
	•	Bash >= 5
	•	LLaMA CLI installé
	•	Modèle local .gguf

⸻

📄 Licence

Open-source. Vous pouvez l’utiliser librement, le modifier et le partager.

⸻

Eto Demerzel (Gustavo Silva Da Costa)
🔗 etodemerzel.gumroad.com
🔗 github.com/BiblioGalactic