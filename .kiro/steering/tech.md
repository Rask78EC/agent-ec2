# Stack
- Amazon Linux 2023 (arm64) en EC2 t4g.micro
- Python 3 + boto3, Bedrock Converse API, modelo amazon.nova-lite-v1:0, región us-east-1
- systemd para ciclo de vida, límites y endurecimiento
- CloudWatch Agent para logs; SSM Session Manager para acceso humano
- Infraestructura como código: CloudFormation (infra/template.yaml)

# Reglas
- Nunca abrir el puerto 22 ni usar claves SSH.
- IAM con mínimo privilegio (solo bedrock:InvokeModel sobre el modelo usado).
- IMDSv2 obligatorio.
- La seguridad real vive en usuario, permisos y systemd, no en listas negras de texto.