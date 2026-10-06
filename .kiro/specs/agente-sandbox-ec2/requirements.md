# Requisitos: Agente en sandbox sobre EC2

## Introducción
Un agente de IA ejecuta comandos de consola en una instancia EC2 con aislamiento a nivel
de sistema operativo y de nube, observabilidad y acceso humano seguro.

## Requisito 1: Aislamiento de identidad
**Historia de usuario:** Como administrador, quiero que el agente corra con un usuario dedicado, para que no tenga privilegios de superusuario.
#### Criterios de aceptación
1. CUANDO se inicie el servicio, ENTONCES EL SISTEMA DEBERÁ ejecutarlo como `ai_agent_executor`.
2. MIENTRAS el servicio esté activo, EL SISTEMA DEBERÁ impedir la escalada de privilegios (`NoNewPrivileges=true`).
3. EL ROL DE IAM de la instancia DEBERÁ permitir únicamente `bedrock:InvokeModel` sobre el modelo configurado, además de las políticas gestionadas de SSM y CloudWatch Agent.

## Requisito 2: Sandbox del workspace
**Historia de usuario:** Como administrador, quiero limitar dónde puede escribir el agente.
#### Criterios de aceptación
1. EL SISTEMA DEBERÁ restringir `/opt/agent_workspace` con permisos `700` para el usuario del agente.
2. CUANDO el agente intente escribir fuera del workspace, ENTONCES EL SISTEMA DEBERÁ denegar la escritura (`ProtectSystem=strict`, `ReadWritePaths`).
3. EL SISTEMA DEBERÁ limitar el servicio a 512 MB de memoria y 50% de CPU.

## Requisito 3: Ejecución resiliente
**Historia de usuario:** Como operador, quiero que el agente se recupere de fallos.
#### Criterios de aceptación
1. CUANDO el proceso termine con error, ENTONCES systemd DEBERÁ reiniciarlo (`Restart=on-failure`) con un límite de reintentos.
2. CUANDO falle el chequeo de estado del sistema de la instancia, ENTONCES una alarma DEBERÁ activar EC2 Auto Recovery.
3. CUANDO un comando exceda 15 segundos, ENTONCES EL AGENTE DEBERÁ terminarlo y reportar el timeout al modelo.

## Requisito 4: Observabilidad
#### Criterios de aceptación
1. EL SISTEMA DEBERÁ escribir stdout y stderr del agente en `/var/log/ai-agent/agent.log`.
2. EL CLOUDWATCH AGENT DEBERÁ enviar ese archivo al log group `/ai-agent/agent` con retención de 7 días.

## Requisito 5: Acceso humano seguro
#### Criterios de aceptación
1. EL SECURITY GROUP NO DEBERÁ tener reglas de entrada.
2. CUANDO un humano necesite intervenir, ENTONCES DEBERÁ conectarse con SSM Session Manager autenticado por IAM.
3. EL SISTEMA DEBERÁ exigir IMDSv2.

## Requisito 6: Bucle del agente
#### Criterios de aceptación
1. EL AGENTE DEBERÁ ejecutar como máximo `MAX_PASOS` iteraciones de razonamiento y comando.
2. CUANDO el modelo devuelva JSON dentro de bloques de código, ENTONCES EL AGENTE DEBERÁ extraerlo correctamente.
3. CUANDO el modelo devuelva un comando vacío, ENTONCES EL AGENTE DEBERÁ terminar.