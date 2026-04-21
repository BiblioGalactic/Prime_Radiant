# Setup de Asistente IA Local

Escribi este instalador porque repetir a mano el mismo setup de asistente local en cada maquina era perder tiempo. Aqui no intento vender "capacidad agéntica avanzada" como eslogan. Intento dejar levantado un entorno util sobre `llama.cpp` sin volver a montar la misma estructura desde cero.

## Que monta

- cliente local para el modelo,
- ejecucion de comandos,
- lectura y escritura de archivos,
- configuracion base del proyecto,
- punto de partida para flujos de trabajo tipo agente.

## Por que sigue siendo un instalador

Necesitaba reproducibilidad mas que acabado de producto. Si puedo reconstruir el entorno rapido en otra maquina, el script ya ha cumplido.

## Lo que conviene vigilar

- si desactivas el modo seguro, asumes el riesgo de ejecutar comandos en host,
- las rutas a modelo y a `llama-cli` siguen siendo locales y explicitas,
- la calidad del asistente sigue dependiendo mas del modelo que del envoltorio.

## Deuda honesta

- acelera el arranque, pero no elimina la necesidad de revisar lo que el asistente hace,
- el entorno puede derivar con el tiempo: Python, utilidades de shell y rutas de modelos,
- "agéntico" no significa "autonomo sin supervision".

## Instalacion

```bash
chmod +x setup_asistente.sh
./setup_asistente.sh
```

Usalo cuando quieras bootstrap rapido en local, no cuando esperes un appliance cerrado.
