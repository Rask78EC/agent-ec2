# Estructura
- agent/agent.py: bucle de razonamiento y ejecución
- systemd/ai-agent.service: unidad con usuario, límites y endurecimiento
- scripts/setup_instance.sh: prepara usuario, workspace, servicio y CloudWatch Agent
- cloudwatch/: configuración del agente de CloudWatch
- infra/template.yaml: EC2, IAM, Security Group, log group y alarma de auto recovery
- .kiro/specs/agente-sandbox-ec2/: requisitos, diseño y tareas