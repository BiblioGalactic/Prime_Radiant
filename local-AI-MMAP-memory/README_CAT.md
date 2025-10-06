Local AI MMAP Memory és un llançador públic en Bash + C per executar LLaMA amb múltiples perfils modulars carregats directament a la memòria mitjançant mmap.
Cada perfil representa un context d’IA diferent (tècnic, filosòfic, seguretat, etc.), permetent gestionar prompts de manera eficient sense necessitat d’arxius temporals.

⸻

⚙️ Funcionalitats
	•	Carrega múltiples perfils .txt a la memòria.
	•	Selecció del perfil actiu en temps d’execució.
	•	Executa LLaMA de manera interactiva amb el context carregat via mmap.
	•	Portable i de codi obert: l’usuari introdueix les seves pròpies rutes.
	•	Gestió d’errors per a arxius, mmap i execució de LLaMA.

⸻

🚀 Ús

./local-AI-MMAP-memory.sh

Segueix els passos per a:
	1.	Introduir el teu arxiu prompt (.txt)
	2.	Introduir la ruta a l’executable llama-cli
	3.	Introduir la ruta del teu model .gguf
	4.	Introduir les rutes dels perfils separades per comes
	5.	Escollir l’índex del perfil actiu

⸻

🧩 Requisits
	•	Bash >=5
	•	GCC
	•	LLaMA CLI instal·lat
	•	Model local .gguf

⸻

📄 Llicència

Codi obert. Utilitza’l lliurement, modifica’l i comparteix-lo.