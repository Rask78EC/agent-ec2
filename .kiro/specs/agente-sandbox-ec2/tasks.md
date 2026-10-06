# Plan de implementación

- [ ] 1. Validar la infraestructura
  - Ejecutar `cfn-lint infra/template.yaml` y corregir hallazgos
  - Desplegar el stack con VpcId y SubnetId reales
  - _Requisitos: 1.3, 3.2, 5.1, 5.3_

- [ ] 2. Preparar la instancia
  - Conectar por SSM, clonar el repo y ejecutar `scripts/setup_instance.sh`
  - Verificar que `systemctl status ai-agent` esté activo
  - _Requisitos: 1.1, 1.2, 2.1, 2.3_

- [ ] 3. Pruebas del agente
  - Crear `tests/` con pytest para el parseo de JSON (con y sin bloques ```json) y el timeout de `ejecutar_comando`
  - _Requisitos: 3.3, 6.1, 6.2, 6.3_

- [ ] 4. Verificar el sandbox
  - Comprobar que el agente no puede escribir fuera de `/opt/agent_workspace` ni ejecutar `sudo`
  - Documentar los resultados en el README
  - _Requisitos: 1.2, 2.2_

- [ ] 5. Observabilidad
  - Confirmar que el log llega a `/ai-agent/agent` en CloudWatch
  - Añadir una alarma por errores repetidos en el log
  - _Requisitos: 4.1, 4.2_

- [ ] 6. Endurecimiento (opcional)
  - Separar el proceso que llama a Bedrock del que ejecuta comandos
  - Restringir la red del ejecutor (por ejemplo `IPAddressDeny=`)
  - _Requisitos: 1.1, 1.3_

- [ ] 7. Programación y aprobación humana (opcional)
  - Disparar el agente con EventBridge Scheduler + SSM Run Command
  - Añadir aprobación con Step Functions y task tokens para comandos sensibles
