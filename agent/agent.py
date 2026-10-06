#!/usr/bin/env python3
"""
Agent Core - Main entry point for the EC2 monitoring agent.

This agent provides intelligent monitoring, logging analysis, and
automated operations for EC2 instances.
"""
import json
import os
import re
import subprocess

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-lite-v1:0")
WORKSPACE = os.environ.get("AGENT_WORKSPACE", "/opt/agent_workspace")
MAX_PASOS = int(os.environ.get("MAX_PASOS", "5"))
TAREA = os.environ.get(
    "AGENT_TASK",
    "Crear un reporte con el espacio libre en disco y el conteo de archivos en el workspace.",
)

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

SYSTEM_PROMPT = (
    "Eres un agente técnico de operaciones en Linux. Resuelve la tarea con comandos "
    f"de consola estándar dentro de {WORKSPACE}. Responde SOLO con JSON: "
    '{"pensamiento": "...", "comando": "..."}. '
    'Cuando termines, responde con "comando": "".'
)


def ejecutar_comando(comando: str) -> str:
    """Ejecuta un comando como el usuario del servicio (sin privilegios).
    La seguridad real la dan el usuario, los permisos y systemd; no este código."""
    try:
        r = subprocess.run(
            ["/bin/bash", "-c", comando],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=15,
        )
        salida = r.stdout if r.returncode == 0 else r.stderr
        return salida[:4000]
    except subprocess.TimeoutExpired:
        return "Error: tiempo de ejecución excedido (15 segundos)."


def parsear_json(texto: str) -> dict:
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.MULTILINE).strip()
    return json.loads(texto)


def pedir_decision(objetivo: str, historial: str) -> dict:
    contenido = f"Objetivo: {objetivo}\nHistorial de ejecución:\n{historial}"
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": contenido}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"temperature": 0.1, "maxTokens": 400},
    )
    return parsear_json(response["output"]["message"]["content"][0]["text"])


def main() -> None:
    historial = ""
    for _ in range(MAX_PASOS):
        decision = pedir_decision(TAREA, historial)
        print(f"[Pensamiento]: {decision.get('pensamiento', '')}")
        comando = decision.get("comando", "")
        if not comando:
            print("[Fin]")
            break
        print(f"[Comando]: {comando}")
        salida = ejecutar_comando(comando)
        print(f"[Salida]:\n{salida}")
        historial += f"\n$ {comando}\n{salida}"


if __name__ == "__main__":
    main()