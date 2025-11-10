#!/usr/bin/env python3
"""
TEST PROFESIONAL: LangGraph-style Agent con Llama 3.1 70B
Simula arquitectura de producción sin dependencias externas
"""

import requests
import json
import asyncio
import time
from typing import Dict, List, TypedDict, Literal, Annotated
from datetime import datetime
import re

# Simulamos los tipos de LangGraph para estructura profesional
class AgentState(TypedDict):
    messages: Annotated[List[Dict], lambda x, y: x + y]
    question: str
    reasoning: str
    tool_decision: str
    context: Dict[str, str]
    final_answer: str

class ProfessionalAgenticTester:
    def __init__(self, base_url: str = "http://altheia.gruporeyes.org:8001/v1"):
        self.base_url = base_url
        self.chat_endpoint = f"{base_url}/chat/completions"
        
        # Tools disponibles (simuladas para testing)
        self.tools = {
            "vector_search_company": "Buscar en base de conocimiento empresarial",
            "vector_search_user_docs": "Buscar en documentos del usuario", 
            "query_business_api": "Consultar APIs de datos empresariales",
            "web_search": "Búsqueda web en tiempo real",
            "direct_response": "Responder con conocimiento general"
        }
    
    async def llama_chat(self, messages: List[Dict], temperature: float = 0.1, max_tokens: int = 2048) -> str:
        """Llama al endpoint con manejo robusto de errores"""
        try:
            payload = {
                "model": "llama-3.1-70b-instruct",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = requests.post(self.chat_endpoint, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.Timeout:
            return "ERROR: Timeout llamando al modelo"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def simulate_tool_execution(self, tool_name: str, query: str) -> str:
        """Simula la ejecución de herramientas (en producción serían reales)"""
        time.sleep(0.5)  # Simula latencia
        
        tool_responses = {
            "vector_search_company": f"Resultados de búsqueda empresarial para: '{query}'. Se encontraron 5 documentos relevantes sobre políticas y procedimientos.",
            "vector_search_user_docs": f"Búsqueda en documentos del usuario: '{query}'. Se analizaron 3 documentos subidos recientemente.",
            "query_business_api": f"Consulta a API empresarial: '{query}'. Datos obtenidos: 15 tickets en proceso, 8 resueltos esta semana.",
            "web_search": f"Búsqueda web para: '{query}'. Información actualizada obtenida de fuentes confiables.",
            "direct_response": "Herramienta no necesitada - respuesta directa posible."
        }
        
        return tool_responses.get(tool_name, "Tool no encontrada")
    
    async def router_node(self, state: AgentState) -> Dict:
        """Nodo de routing - Decide qué herramienta usar"""
        print("🔄 [Router] Analizando pregunta...")
        
        routing_prompt = [
            {
                "role": "system",
                "content": f"""Eres un router inteligente. Analiza la pregunta y decide EXACTAMENTE UNA de estas herramientas:

HERRAMIENTAS DISPONIBLES:
1. vector_search_company - Para información de la empresa, políticas, procesos internos
2. vector_search_user_docs - Cuando el usuario menciona "documento", "archivo", "PDF" que haya subido  
3. query_business_api - Para datos numéricos, tickets, pedidos, estados, reportes en tiempo real
4. web_search - Para información actual, noticias, precios, eventos recientes
5. direct_response - Para conversación general, explicaciones, conocimiento general

Responde SOLO con el nombre exacto de la herramienta. No expliques."""
            },
            {
                "role": "user",
                "content": f"Pregunta a analizar: {state['question']}"
            }
        ]
        
        tool_decision = await self.llama_chat(routing_prompt, temperature=0.1, max_tokens=50)
        tool_decision = tool_decision.strip().lower()
        
        # Mapear a tool names válidos
        tool_mapping = {
            "empresa": "vector_search_company",
            "documento": "vector_search_user_docs", 
            "api": "query_business_api",
            "web": "web_search",
            "directo": "direct_response"
        }
        
        for key, tool in tool_mapping.items():
            if key in tool_decision:
                selected_tool = tool
                break
        else:
            selected_tool = "direct_response"  # Fallback
        
        print(f"   🎯 Tool seleccionada: {selected_tool}")
        return {"tool_decision": selected_tool}
    
    async def tool_node(self, state: AgentState) -> Dict:
        """Nodo de ejecución de herramientas"""
        print(f"🛠️  [Tool] Ejecutando: {state['tool_decision']}")
        
        tool_result = self.simulate_tool_execution(state['tool_decision'], state['question'])
        
        print(f"   📦 Resultado tool: {tool_result[:100]}...")
        return {"context": {state['tool_decision']: tool_result}}
    
    async def reasoning_node(self, state: AgentState) -> Dict:
        """Nodo de reasoning avanzado"""
        print("🤔 [Reasoning] Generando razonamiento...")
        
        reasoning_prompt = [
            {
                "role": "system", 
                "content": """Analiza la pregunta, la herramienta seleccionada y su resultado. Genera un razonamiento estructurado:

ANÁLISIS_DE_NECESIDAD: ¿Por qué se necesitó o no la herramienta?
EVALUACIÓN_DE_CONTEXTO: ¿El resultado es suficiente/satisfactorio?
ESTRATEGIA_RESPUESTA: ¿Cómo integrar la información en la respuesta?"""
            },
            {
                "role": "user",
                "content": f"""
PREGUNTA: {state['question']}
HERRAMIENTA_SELECCIONADA: {state['tool_decision']}  
RESULTADO_HERRAMIENTA: {state['context'].get(state['tool_decision'], 'N/A')}
"""
            }
        ]
        
        reasoning = await self.llama_chat(reasoning_prompt, temperature=0.2)
        print(f"   💡 Razonamiento: {reasoning[:150]}...")
        return {"reasoning": reasoning}
    
    async def generation_node(self, state: AgentState) -> Dict:
        """Nodo de generación de respuesta final"""
        print("✨ [Generation] Generando respuesta final...")
        
        generation_prompt = [
            {
                "role": "system",
                "content": """Eres un asistente profesional. Genera una respuesta útil y natural integrando el contexto obtenido.

Si usaste herramientas, menciona brevemente de dónde obtienes la información.
Sé transparente sobre limitaciones si la información no es completa.
Mantén un tono profesional pero amable."""
            },
            {
                "role": "user", 
                "content": f"""
PREGUNTA ORIGINAL: {state['question']}

CONTEXTO OBTENIDO:
- Herramienta usada: {state['tool_decision']}
- Resultado: {state['context'].get(state['tool_decision'], 'N/A')}

RAZONAMIENTO: {state['reasoning']}

RESPUESTA FINAL:
"""
            }
        ]
        
        final_answer = await self.llama_chat(generation_prompt, temperature=0.3)
        return {"final_answer": final_answer}
    
    async def run_agent_graph(self, question: str) -> Dict:
        """Ejecuta el grafo completo del agente"""
        print(f"\n🚀 INICIANDO AGENT GRAPH: '{question}'")
        print("=" * 70)
        
        start_time = time.time()
        
        # Estado inicial
        state = {
            "messages": [],
            "question": question,
            "reasoning": "",
            "tool_decision": "",
            "context": {},
            "final_answer": ""
        }
        
        # Ejecutar nodos en secuencia (en LangGraph sería conditional edges)
        try:
            # 1. Routing
            router_result = await self.router_node(state)
            state.update(router_result)
            
            # 2. Tool execution  
            tool_result = await self.tool_node(state)
            state.update(tool_result)
            
            # 3. Reasoning
            reasoning_result = await self.reasoning_node(state) 
            state.update(reasoning_result)
            
            # 4. Generation
            generation_result = await self.generation_node(state)
            state.update(generation_result)
            
            total_time = time.time() - start_time
            
            print(f"\n✅ AGENT COMPLETADO en {total_time:.2f}s")
            print("=" * 70)
            print(f"🎯 HERRAMIENTA: {state['tool_decision']}")
            print(f"💬 RESPUESTA: {state['final_answer']}")
            print("=" * 70)
            
            return {
                "success": True,
                "state": state,
                "metrics": {
                    "total_time": total_time,
                    "tool_used": state["tool_decision"],
                    "question_complexity": len(question.split())
                }
            }
            
        except Exception as e:
            print(f"❌ ERROR en agent graph: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_benchmark_suite(self):
        """Suite de benchmarking profesional"""
        benchmark_cases = [
            {"question": "¿cuantos tickets hay en proceso?", "expected_tool": "query_business_api"},
            {"question": "¿cuál es nuestra política de vacaciones?", "expected_tool": "vector_search_company"},
            {"question": "analiza el PDF que subí ayer", "expected_tool": "vector_search_user_docs"},
            {"question": "precio del dólar hoy", "expected_tool": "web_search"},
            {"question": "explícame qué es transformer en IA", "expected_tool": "direct_response"},
        ]
        
        print("📊 BENCHMARK SUITE - AGENT PROFESIONAL")
        print("=" * 70)
        
        results = []
        for i, case in enumerate(benchmark_cases, 1):
            print(f"\n🧪 Caso {i}/{len(benchmark_cases)}: {case['question']}")
            
            result = await self.run_agent_graph(case["question"])
            
            if result["success"]:
                tool_match = result["state"]["tool_decision"] == case["expected_tool"]
                results.append({
                    "case": case["question"],
                    "expected_tool": case["expected_tool"],
                    "actual_tool": result["state"]["tool_decision"], 
                    "match": tool_match,
                    "time": result["metrics"]["total_time"]
                })
                
                status = "✅" if tool_match else "❌"
                print(f"{status} Tool: {result['state']['tool_decision']} (esperado: {case['expected_tool']})")
        
        # Reporte de benchmark
        print("\n📈 REPORTE DE BENCHMARK:")
        print(f"Precisión: {sum(1 for r in results if r['match'])}/{len(results)}")
        print(f"Tiempo promedio: {sum(r['time'] for r in results)/len(results):.2f}s")
        
        return results

async def main():
    agent_tester = ProfessionalAgenticTester()
    
    print("🎯 AGENT TESTER PROFESIONAL")
    print("Simulando arquitectura LangGraph con Llama 3.1 70B")
    
    while True:
        print("\n1. Ejecutar Agent Graph (pregunta específica)")
        print("2. Run Benchmark Suite") 
        print("3. Salir")
        
        choice = input("\nSelecciona opción (1-3): ").strip()
        
        if choice == "1":
            question = input("Ingresa la pregunta: ").strip()
            if question:
                await agent_tester.run_agent_graph(question)
        elif choice == "2":
            await agent_tester.run_benchmark_suite()
        elif choice == "3":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    asyncio.run(main())