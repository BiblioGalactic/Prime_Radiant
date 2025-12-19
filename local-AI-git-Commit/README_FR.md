🧠 Git Commit IA Locale

Script Git interactif avec IA
Version publique et portable pour améliorer tes commits grâce à l’assistance d’une intelligence artificielle.

⸻

🧑‍💻 Auteur

Gustavo Silva
Date de création : $(date +%F)

⸻

📌 Description

local-Commit.sh est un script Git interactif avec IA qui te permet de :
	•	Sélectionner les fichiers à ajouter (tous ou individuellement via fzf).
	•	Saisir ton message de commit et le corriger automatiquement à l’aide d’un modèle IA.
	•	Vérifier que le commit corrigé ne change pas le sens original grâce à un second modèle IA.
	•	Modifier manuellement le commit corrigé avant de l’envoyer.
	•	Détecter automatiquement la branche principale et effectuer un push sécurisé.
	•	Rester portable : le script te demandera les chemins vers llama-cli et les modèles .gguf.

⸻

⚙️ Prérequis
	•	Bash 5+
	•	Git
	•	timeout
	•	nl
	•	fzf
	•	llama-cli et modèles .gguf (correction et vérification)

⸻

📂 Installation
	1.	Clone ce dépôt ou télécharge le script.
	2.	Assure-toi que les dépendances (git, timeout, nl, fzf) sont installées.
	3.	Prépare tes modèles .gguf et ton llama-cli compilé.
	4.	Exécute :

chmod +x local-Commit.sh
./local-Commit.sh
