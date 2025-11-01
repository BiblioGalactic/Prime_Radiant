# 🚀 Inicio Rápido - AI Cluster

## En 5 Minutos

### Paso 1: Descarga

```bash
curl -O https://raw.githubusercontent.com/BiblioGalactic/ai-cluster/main/ai-cluster.sh
chmod +x ai-cluster.sh
```

### Paso 2: Configura

```bash
./ai-cluster.sh setup
```

Responde las preguntas del wizard:

```
📍 PASO 1/4: Configuración Local
  ✓ llama-cli detectado
  ✓ Modelo detectado
  
🌐 PASO 2/4: Máquinas Remotas
  IPs remotas: 192.168.1.82
  Usuario SSH: tuusuario
  
🔐 PASO 3/4: Configuración SSH
  ✓ Acceso configurado
  
✅ PASO 4/4: Verificación
  ✓ Cluster configurado: 1 local + 1 remota
```

### Paso 3: Crea Queries

```bash
cat > queries.txt << 'EOF'
Explica qué es una red neuronal
Resume la teoría de la relatividad
¿Cuál es la capital de Japón?
Escribe un haiku sobre la tecnología
EOF
```

### Paso 4: ¡Ejecuta!

```bash
./ai-cluster.sh run queries.txt
```

---

## Escenarios Comunes

### Solo Tienes 1 Ordenador

Usa la versión local (sin SSH):

```bash
# Edita el script y comenta las líneas de SSH
# O usa local_distributor.sh del repo
```

### Tienes 2 Macs en Casa

```bash
# Activa SSH en el segundo Mac
sudo systemsetup -setremotelogin on

# Configura con el wizard
./ai-cluster.sh setup
```

### Tienes 10+ PCs en la Oficina

```bash
# Configura todas las IPs separadas por comas
IPs remotas: 192.168.1.10,192.168.1.11,192.168.1.12...

# El script distribuirá automáticamente
```

---

## Verificación Rápida

```bash
# ¿SSH funciona?
ssh tuusuario@192.168.1.82 "echo ok"

# ¿llama-cli existe remotamente?
ssh tuusuario@192.168.1.82 "ls ~/llama.cpp/build/bin/llama-cli"

# ¿Modelo existe remotamente?
ssh tuusuario@192.168.1.82 "ls ~/modelo/*.gguf"
```

---

## Problemas Comunes

| Problema | Solución |
|---|---|
| SSH pide password | `./ai-cluster.sh setup` (reconfigura SSH) |
| llama-cli no encontrado | Verifica ruta en `.ai_cluster_config` |
| Queries lentas | Reduce modelo o aumenta threads |
| Script se cuelga | Verifica `.zshrc` en remotas (ver README) |

---

## Próximos Pasos

- 📖 Lee el [README completo](README.md)
- 🐛 Reporta bugs en [GitHub Issues](https://github.com/BiblioGalactic/ai-cluster/issues)
- ⭐ Dale estrella al proyecto si te gusta

---

**¿Dudas? Abre un Issue en GitHub**
