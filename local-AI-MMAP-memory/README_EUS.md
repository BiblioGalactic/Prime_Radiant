Local AI MMAP Memory 

Local AI MMAP Memory Bash + C-n egindako abiarazle publikoa da, LLaMA exekutatzeko profil modular anitzak zuzenean memorian kargatuz mmap bidez.
Profil bakoitzak adimen artifizialaren testuinguru desberdin bat ordezkatzen du (teknikoa, filosofikoa, segurtasuna, etab.), eta horri esker prompt-ak eraginkortasunez kudea daitezke, aldi baterako fitxategirik sortu gabe.

⸻
Funtzionaltasunak
	•	Hainbat .txt profil memorian kargatzen ditu.
	•	Profil aktiboa exekuzio-denboran aukeratu daiteke.
	•	LLaMA interaktiboki exekutatzen du mmap bidez kargatutako testuinguruarekin.
	•	Erabat eramangarria eta kode irekikoa: erabiltzaileak bere bideak zehazten ditu.
	•	Fitxategien, mmap eta LLaMA-ren abiarazpenaren errore-kudeaketa integratua dauka.

⸻
 Erabilera

./local-AI-MMAP-memory.sh

Jarraitu urrats hauek:
	1.	Sartu zure prompt fitxategia (.txt).
	2.	Adierazi llama-cli exekutagarrirako bidea.
	3.	Sartu zure .gguf modeloaren bidea.
	4.	Gehitu profilen bideak koma bidez bereizita.
	5.	Aukeratu profil aktiboaren indizea.

⸻
 Baldintzak
	•	Bash ≥ 5
	•	GCC
	•	LLaMA CLI instalatuta
	•	.gguf formatuan modeloa lokalki

⸻

Lizentzia

Kode irekikoa.
Erabili libreki, aldatu eta partekatu nahi duzun bezala.