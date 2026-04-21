# WikiRAG - estado actual

## Antes de entrar

A fecha de febrero de 2026, A1, B2, C3 y D4 estan deprecadas. La linea activa es E5.

No elimine las versiones viejas porque cada una me dejo una leccion distinta: router de modelos, colas, mensajeria, memoria o empaquetado. El coste de mantenerlas visibles es el ruido. El beneficio es que no tengo que reexplicar por que tome ciertas decisiones.

## Que intenta resolver este sistema

Queria un stack local que no fuese solo "pregunta a un modelo y ya". Necesitaba:

- colas,
- criterios de seleccion de modelo,
- memoria,
- RAG,
- agentes,
- y la posibilidad de degradar el sistema sin apagarlo entero.

Por eso esta carpeta acabo creciendo mas de la cuenta.

## Como esta organizado

- `VERSIONE5/`: rama activa.
- `VERSIONA1` a `VERSIOND4/`: historial de arquitectura, migraciones y errores ya pagados.
- `MIGRATION_GUIDE.md`: puente entre generaciones.

## Numeros que si puedo afirmar

- cinco generaciones visibles: A1, B2, C3, D4 y E5,
- `VERSIONC3` conserva 19 tests en verde.

## Lo que aprendi y no quiero ocultar

- meter demasiadas capacidades en una sola version vuelve difusa la frontera entre producto y laboratorio,
- el router de modelos merece existir porque no todos los prompts justifican el mismo coste,
- mantener versiones deprecadas es feo, pero me ha ahorrado rehacer errores por segunda vez.

## Si quieres usarlo hoy

Empieza por E5.

Si algo de E5 te resulta incomprensible, entonces baja a C3 o D4 para entender la evolucion, no para desplegarlo.
