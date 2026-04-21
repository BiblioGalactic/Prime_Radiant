# Prime_Radiant

## Que es este repo

`Prime_Radiant` es el sitio donde fui dejando los sistemas mas ambiciosos del workspace cuando ya no cabian en un script suelto. Aqui conviven asistentes locales, daemons con RAG, MCP, evaluacion cruzada, cluster y utilidades de memoria. No lo presento como un producto unico porque no lo es; es un repositorio de trabajo con varias lineas, algunas activas y otras historicas.

La ventaja de haberlo dejado asi es que las decisiones siguen visibles. El coste tambien: hay carpetas muy maduras al lado de otras que son claramente laboratorio.

## Lo que sigue vivo

- `local-AIDaemon-agentic-rag-adaptative/`
- `local-agentic-MCP/`
- `local-cross-eval-synth/`
- `local-agentic-assistant/`
- `local-AI-cluster/`

La rama mas pesada es `local-AIDaemon-agentic-rag-adaptative/`, donde deje cinco generaciones visibles: A1, B2, C3, D4 y E5. No las borre al deprecarlas porque en ese historial estan las decisiones que salieron caras.

## Estado verificable

- `VERSIONC3` mantiene 19 tests en verde.
- A1-D4 siguen presentes como referencia historica y para migracion.

## Por donde empezaria yo hoy

Si quieres un sistema mas "producto":

1. mira `local-AIDaemon-agentic-rag-adaptative/`,
2. usa E5 como rama activa,
3. consulta las versiones viejas solo para entender por que se cambio algo.

Si quieres algo mas pequeno y utilitario:

- `local-cross-eval-synth/` para comparar 2-4 modelos,
- `local-agentic-assistant/` para instalar un asistente local en una maquina nueva,
- `local-AI-cluster/` si tu problema es repartir carga en red local.

## Por que no lo limpie mas

Porque aqui la "limpieza" total borraria informacion util. Hay nombres raros, README repetidos por idioma y versiones deprecadas que no son bonitas. Prefiero dejar la cicatriz visible a fingir que todo salio lineal.

## Deuda honesta

- No todos los modulos comparten el mismo nivel de madurez.
- Algunos README nacieron como folleto tecnico y he ido corrigiendo eso solo en las puertas de entrada mas importantes.
- Varias piezas siguen asumiendo rutas locales de `llama.cpp` y modelos GGUF; esa dependencia es deliberada, no un olvido.
