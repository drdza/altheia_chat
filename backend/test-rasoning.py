#!/usr/bin/env python3
"""
Test simple de Agentic Reasoning con Llama 3.1 70B
Usando tu endpoint: http://altheia.gruporeyes.org:8001/v1/chat/completions
"""

import requests
import json
import asyncio
import time
from typing import Dict, List

class AgenticTester:
    def __init__(self, base_url: str = "http://altheia.gruporeyes.org:8001/v1"):
        self.base_url = base_url
        self.chat_endpoint = f"{base_url}/chat/completions"
    
    async def llama_chat(self, messages: List[Dict], temperature: float = 0.1) -> str:
        """Llama al endpoint de chat completions"""
        try:
            payload = {
                "model": "llama-3.1-70b-instruct",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2048,
                "stream": True
            }
            
            response = requests.post(self.chat_endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            return f"Error llamando al modelo: {str(e)}"
    
    async def test_reasoning_capability(self, question: str):
        """Testea si el modelo puede razonar sobre qué herramientas usar"""
        print(f"\n🧠 TEST DE REASONING: '{question}'")
        print("=" * 60)
        
        # Paso 1: Razonamiento sobre herramientas necesarias
        reasoning_prompt = [
            {
                "role": "system",
                "content": """Eres un asistente inteligente que analiza preguntas y decide si necesitas usar herramientas especializadas o puedes responder directamente.

HERRAMIENTAS DISPONIBLES:
1. BASE_CONOCIMIENTO_EMPRESARIAL - Información general de la empresa, procesos, políticas
2. DOCUMENTOS_USUARIO - Archivos PDF, Word, Excel que el usuario ha subido  
3. APIS_DATOS - Sistemas empresariales para datos en tiempo real (tickets, pedidos, etc.)
4. CONOCIMIENTO_GENERAL - Tu conocimiento interno como IA

Analiza la pregunta y responde con este formato:

RAZONAMIENTO: [Explica brevemente por qué sí o no necesitas herramientas]
HERRAMIENTA_RECOMENDADA: [BASE_CONOCIMIENTO_EMPRESARIAL | DOCUMENTOS_USUARIO | APIS_DATOS | CONOCIMIENTO_GENERAL | COMBINACION]
JUSTIFICACION: [Explica por qué esa herramienta es la adecuada]"""
            },
            {
                "role": "user", 
                "content": question
            }
        ]
        
        start_time = time.time()
        reasoning_result = await self.llama_chat(reasoning_prompt, temperature=0.1)
        reasoning_time = time.time() - start_time
        
        print(f"⏱️  Tiempo reasoning: {reasoning_time:.2f}s")
        print(f"🤔 Razonamiento:\n{reasoning_result}")
        
        # Paso 2: Generar respuesta basada en el razonamiento
        response_prompt = [
            {
                "role": "system",
                "content": f"""Basado en tu análisis anterior, responde al usuario de manera natural y útil.

CONTEXTO DEL ANÁLISIS:
{reasoning_result}

Si recomendaste herramientas específicas, sugiérele al usuario cómo podrías ayudarlo con esas herramientas.
Si es algo que puedes responder directamente, hazlo de manera completa y útil."""
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        start_time = time.time()
        final_response = await self.llama_chat(response_prompt, temperature=0.3)
        response_time = time.time() - start_time
        
        print(f"⏱️  Tiempo respuesta: {response_time:.2f}s")
        print(f"💬 Respuesta final:\n{final_response}")
        print("=" * 60)
    
    async def run_test_suite(self):
        """Ejecuta una suite de pruebas con diferentes tipos de preguntas"""
        test_cases = [
            # Consultas que necesitan APIs/datos
            "¿cuantos tickets hay en proceso actualmente?",
            "muéstrame el estado de mis pedidos pendientes",
            "necesito el reporte de ventas del último mes",
            
            # Consultas que necesitan base de conocimiento  
            "¿cuál es nuestra política de vacaciones?",
            "cómo funciona el proceso de reembolsos",
            "qué beneficios tiene la empresa para empleados",
            
            # Consultas sobre documentos del usuario
            "analiza el documento que subí sobre el proyecto",
            "qué información importante hay en el PDF que cargué",
            
            # Consultas de conocimiento general
            "explícame qué es machine learning",
            "cuáles son las mejores prácticas para code review",
            "hola, ¿cómo estás?",
        ]
        
        print("🚀 INICIANDO TEST SUITE - AGENTIC REASONING")
        print("Endpoint:", self.chat_endpoint)
        print("=" * 70)
        
        for i, question in enumerate(test_cases, 1):
            print(f"\n📋 Caso {i}/{len(test_cases)}")
            await self.test_reasoning_capability(question)
            if i < len(test_cases):
                input("\n⏎ Presiona Enter para el siguiente caso...")

async def main():
    tester = AgenticTester()
    
    print("🎯 TESTER DE AGENTIC REASONING")
    print("Este test valida si Llama 3.1 70B puede razonar sobre herramientas")
    
    while True:
        print("\n1. Ejecutar suite completa de pruebas")
        print("2. Probar pregunta específica") 
        print("3. Salir")
        
        choice = input("\nSelecciona opción (1-3): ").strip()
        
        if choice == "1":
            await tester.run_test_suite()
        elif choice == "2":
            question = input("Ingresa la pregunta a analizar: ").strip()
            if question:
                await tester.test_reasoning_capability(question)
        elif choice == "3":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    asyncio.run(main())