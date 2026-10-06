# AI Agent (Amazon Nova + EC2 Sandbox)

Un agente de IA que ejecuta comandos en una instancia EC2 basándose en decisiones del modelo Amazon Nova Lite (vía Bedrock), todo dentro de un entorno sandbox limitado para seguridad.

## Visión General

El agente funciona como un bucle iterativo donde:
1. Recibe un objetivo en texto
2. Envía el objetivo + historial a Nova Lite
3. Nova Lite decide el siguiente comando y devuelve JSON
4. El agente ejecuta el comando en sandbox
5. El resultado se agrega al historial y se repite
6. Termina cuando el modelo indica fin o se alcanza el límite de pasos

### Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    EC2 Instance                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Agent Loop (agent.py)                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │   Objective  │  │  Nova Lite   │  │  Execute     │    │  │
│  │  │   Input      │->│  (Bedrock)   │->│  Command     │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  │              │            │           │                   │  │
│  │              ▼            ▼           ▼                   │  │
│  │      ┌──────────────────────────────────────┐            │  │
│  │      │   /opt/agent_workspace (sandbox)     │            │  │
│  │      │   - Limited user (ai_agent_executor)│             │  │
│  │      │   - Restricted systemd profile       │            │  │
│  │      │   - Resource limits (50% CPU, 512MB) │            │  │
│  │      └──────────────────────────────────────┘            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                        │                                         │
│            ┌───────────▼───────────┐                            │
│            │  CloudWatch Logs      │                            │
│            │  /var/log/ai-agent/   │                            │
│            └───────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### Flujos de Trabajo

#### Ciclo de Ejecución (Paso a Paso)

1. **Recibe objetivo**: Por defecto: *"Crear un reporte con el espacio libre en disco y el conteo de archivos en el workspace"*. Se puede cambiar con `AGENT_TASK`.

2. **Envía a Nova Lite**: El prompt incluye:
   - El objetivo actual
   - Historial de comandos anteriores
   - Instrucción explícita: responder solo con JSON `{"pensamiento": "...", "comando": "..."}`

3. **Extrae JSON**: Aunque la respuesta venga en bloque markdown ```json, el agente extrae el JSON válido.

4. **Verifica comando**: 
   - Si `comando` está vacío → termina
   - Si no → ejecuta con `bash -c` en `/opt/agent_workspace`

5. **Ejecución con sandbox**:
   - Timeout: 15 segundos
   - Salida capturada: máximo 4000 caracteres
   - Entorno: usuario sin privilegios, filesystem mostly read-only

6. **Actualiza historial**: Agrega el resultado y vuelve al paso 2.

7. **Termina cuando**:
   - Nova Lite decide que no hay más comandos (comando vacío)
   - O se alcanza `MAX_PASOS` (por defecto 5)

#### Ejemplo de Ejecución

| Paso | Objetivo | Comando Propuesto | Acción | Resultado |
|------|----------|-------------------|--------|-----------|
| 1 | Generar reporte de disco | `df -h` | Ejecutar | Espacio en disco |
| 2 | Contar archivos | `ls \| wc -l` | Ejecutar | Número de archivos |
| 3 | Guardar reporte | `echo "..." > reporte.txt` | Ejecutar | Archivo creado |
| 4 | Finalizar | (vacío) | Terminar | ✅ Done |

### Registro y Monitoreo

- **Logs locales**: `/var/log/ai-agent/agent.log`
- **Logs en CloudWatch**: `/ai-agent/agent` (log group)
- **Formato**: Plain text (el service lo captura desde stdout/stderr)

### Ejecución Periódica

El agente corre una sola vez y termina. Para ejecuciones recurrentes:

- **Option A**: systemd timer
- **Option B**: EventBridge Scheduler (recomendado para entornos AWS)

## Configuración

### Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `AGENT_TASK` | "Crear un reporte con el espacio libre en disco y el conteo de archivos en el workspace." | Objetivo inicial |
| `AWS_REGION` | "us-east-1" | Región de Bedrock |
| `MODEL_ID` | "amazon.nova-lite-v1:0" | ID del modelo Nova Lite |
| `AGENT_WORKSPACE` | "/opt/agent_workspace" | Directorio de trabajo del sandbox |
| `MAX_PASOS` | 5 | Máximo de iteraciones del bucle |

### Archivos de Configuración

- **Service**: `/etc/systemd/system/ai-agent.service`
- **CloudWatch**: `/opt/agent/amazon-cloudwatch-agent.json`

### Estructura de Archivos

```
agent-ec2/
├── agent/
│   └── agent.py                # Bucle principal y ejecución
├── systemd/
│   └── ai-agent.service        # Service definition
├── scripts/
│   └── setup_instance.sh       # Script de instalación
├── cloudwatch/
│   └── amazon-cloudwatch-agent.json
├── infra/
│   └── template.yaml           # CloudFormation
├── requirements.txt
└── README.md
```

## Requisitos

- EC2 con Amazon Linux 2023 (ARM64) o Ubuntu 22.04+
- IAM role con permisos:
  - `bedrock:InvokeModel` para Amazon Nova Lite
  - CloudWatch Logs: `PutLogEvents`, `CreateLogStream`
  - SSM: `ssm:StartSession` (para acceso interactivo)
- Python 3.11+
- Sistema con `bash`, `systemd`, `timeout`
- CloudWatch Agent instalado (`amazon-cloudwatch-agent`)

## Instalación

### Quick Start (desde la EC2)

```bash
# Instalar dependencias y configurar servicio
sudo bash scripts/setup_instance.sh

# Verificar estado del servicio
systemctl status ai-agent

# Ver logs en tiempo real
sudo tail -f /var/log/ai-agent/agent.log
```

El script `setup_instance.sh` realiza:
1. Instala dependencias (Python pip, CloudWatch Agent)
2. Crea usuario `ai_agent_executor`
3. Copia agent.py y configura servicio systemd
4. Configura CloudWatch Agent
5. Habilita y arranca el servicio

### Manual

1. Copiar archivos a `/opt/agent`
2. Crear usuario: `useradd -r -s /bin/bash ai_agent_executor`
3. Configurar CloudWatch agent
4. Iniciar servicio: `systemctl start ai-agent`

## Uso

### Ejecutar una vez

```bash
AGENT_TASK="Analiza los logs del sistema y reporta errores críticos" \
python3 agent/agent.py
```

### Con systemd

```bash
systemctl start ai-agent
# Ver logs: sudo tail -f /var/log/ai-agent/agent.log
```

## Seguridad

### Sandbox Implementation
- Usuario `ai_agent_executor` sin privilegios de sudo
- `NoNewPrivileges=true` en el service
- `ProtectSystem=strict` (filesystem read-only except /opt, /run, /tmp)
- `ProtectHome=true`
- Límites de recursos: 50% CPU, 512MB memoria
- Timeout por comando: 15s en subprocess
- Salida truncada a 4000 caracteres

### Advertencias
- El agente ejecuta lo que el modelo decide
- El sandbox reduce el daño pero no lo elimina
- Probar primero con tareas inocuas
- No dar acceso a datos sensibles

### Prácticas Recomendadas
1. Probar en instancias dedicadas primero
2. Usar objetivos simples al inicio
3. Monitorear CloudWatch Logs en tiempo real
4. Implementar revisiones humanas en production (ver task 7 en `.kiro/specs/agente-sandbox-ec2/`)

## Lo que NO hace

- ❌ No tiene herramientas externas (solo bash)
- ❌ No navega por web ni llama APIs
- ❌ No guarda memoria entre ejecuciones
- ❌ No pide aprobación humana (ese es un feature opcional)

## Logs y Troubleshooting

```bash
# Ver logs locales
sudo tail -f /var/log/ai-agent/agent.log

# Ver logs en CloudWatch
aws cloudwatch logs tail /ai-agent/agent --follow

# Ver servicio systemd
journalctl -u ai-agent -f
```

### Debug común

| Problema | Solución |
|----------|----------|
| Timeout en comandos | Aumentar `MAX_PASOS` o verificar comando |
| Salida truncada | Aumentar buffer en `agent.py` |
| Nova Lite no responde | Verificar IAM permissions (bedrock:InvokeModel) |
| Permission denied | Verificar usuario `ai_agent_executor` y permisos en workspace |
| Service no arranca | `journalctl -u ai-agent -xe` para diagnóstico |

## Despliegue

### CloudFormation

```bash
aws cloudformation deploy \
    --template-file infra/template.yaml \
    --stack-name agente-ec2 \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        VpcId=vpc-xxxx \
        SubnetId=subnet-xxxx
```

### Ingresar a la instancia y verificar

```bash
# Iniciar sesión en la instancia
aws ssm start-session --target <instance-id>

# Dentro de la instancia:
sudo dnf install -y git && git clone <tu-repo> && cd <repo>
sudo bash scripts/setup_instance.sh

# Ver logs en tiempo real
sudo tail -f /var/log/ai-agent/agent.log
```

### Terraform (próxima versión)

## Desarrollo

```bash
# Verificar syntax
python3 -m py_compile agent/agent.py

# Test local (sin sandbox)
AGENT_TASK="Escribe 'hello world' en /tmp/test.txt" \
python3 agent/agent.py
```

## Licencia

MIT License - Ver archivo LICENSE para detalles.