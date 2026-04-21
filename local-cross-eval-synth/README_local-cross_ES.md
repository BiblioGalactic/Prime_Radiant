# Local-CROS

Construyi Local-CROS cuando empece a desconfiar de la primera respuesta convincente de un modelo local. La idea es muy simple y por eso la deje en Bash: preguntar lo mismo a varios modelos, obligarlos a mirarse entre ellos y guardar todo en disco para poder revisar de donde salio la sintesis final.

## Que hace de verdad

- lanza el mismo prompt contra 2 a 4 modelos GGUF,
- guarda cada respuesta cruda,
- permite evaluacion cruzada entre modelos,
- genera una respuesta final combinada.

Lo limite a 4 modelos porque, a partir de ahi, el tiempo de espera me estaba creciendo mas rapido que el valor del contraste.

## Por que guarda tanto archivo

Preferi trazabilidad a limpieza visual. Si la sintesis final sale mal, quiero ver que modelo metio ruido y cual aporto la parte util. Una salida bonita por consola no me sirve para eso.

## Requisitos

- `llama.cpp`
- 2-4 modelos GGUF
- Bash
- utilidades basicas de shell

## Limites honestos

- la sintesis es heuristica; no garantiza verdad,
- con modelos lentos el ciclo entero pesa bastante,
- dos modelos flojos pueden ponerse de acuerdo en algo flojo.

## Uso

```bash
./local-cros.sh "Explica el coste real de una arquitectura multiagente"
```

Si solo vas a consultar un modelo, este repo no te aporta mucho. Su sentido empieza cuando hay friccion entre respuestas.
