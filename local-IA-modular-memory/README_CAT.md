Versió en Català

Memòria IA Modular Local és un script públic en Bash per generar i executar un prompt complet amb LLaMA a partir de les teves notes en Markdown. Concatena tots els fitxers .md d'un directori, els neteja i llança una sessió interactiva de LLaMA.

Funcionalitats

Funciona amb qualsevol directori de fitxers .md.

Neteja espais i línies buides mantenint UTF-8.

Sol·licita rutes del model i de l'executable llama-cli.

Actualització dinàmica opcional abans de generar el prompt.

Ús

./local_ia_modular_memory.sh

Segueix les indicacions:

Introdueix el directori amb els teus .md.

Introdueix la ruta al teu model LLaMA (.gguf).

Introdueix la ruta a l'executable llama-cli.

L'script generarà prompt_complet.txt i llançarà una sessió interactiva de LLaMA.

Requisits

Bash >=5

LLaMA CLI instal·lat

Model local .gguf

Llicència

Codi obert. Usa'l lliurement, modifica'l i comparteix-lo.

**Eto Demerzel** (Gustavo Silva Da Costa)
https://etodemerzel.gumroad.com  
https://github.com/BiblioGalactic