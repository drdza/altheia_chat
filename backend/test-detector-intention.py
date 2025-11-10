#!/usr/bin/env python3
"""
Script de testing para el servicio de clasificación de intenciones
CON NUEVAS CATEGORÍAS DE ENRUTAMIENTO
"""

import requests
import json
import time
from typing import List, Tuple, Dict

class IntentTester:
    def __init__(self, base_url: str = "http://altheia:8002"):
        self.base_url = base_url
        
        # NUEVAS CATEGORÍAS DE ENRUTAMIENTO
        self.candidate_labels = [
            "el usuario quiere analizar un documento o archivo que ha subido",
            "el usuario reporta un problema técnico o necesita soporte", 
            "el usuario pregunta sobre la empresa o organización",
            "el usuario consulta sobre un proceso o procedimiento específico",
            "el usuario busca información actualizada en tiempo real",
            "el usuario necesita acceder a datos de sistemas o APIs",
            "el usuario pregunta sobre inteligencia artificial o cómo funciona el sistema",
            "el usuario está conversando de manera general o casual"
        ]
        
        # Mapeo a categorías simples
        self.intention_map = {
            "el usuario quiere analizar un documento o archivo que ha subido": 
                {"intention": "analizar_documento_usuario", "integration": "milvus_user_docs"},
            "el usuario reporta un problema técnico o necesita soporte": 
                {"intention": "soporte_tecnico", "integration": "knowledge_base + apis"},
            "el usuario pregunta sobre la empresa o organización": 
                {"intention": "informacion_empresa", "integration": "milvus_company"},
            "el usuario consulta sobre un proceso o procedimiento específico": 
                {"intention": "consultar_proceso", "integration": "milvus_processes"},
            "el usuario busca información actualizada en tiempo real": 
                {"intention": "consulta_tiempo_real", "integration": "duckduckgo + apis"},
            "el usuario necesita acceder a datos de sistemas o APIs": 
                {"intention": "acceso_api", "integration": "enterprise_apis"},
            "el usuario pregunta sobre inteligencia artificial o cómo funciona el sistema": 
                {"intention": "informacion_ia", "integration": "knowledge_base"},
            "el usuario está conversando de manera general o casual": 
                {"intention": "conversacion_general", "integration": "base_model"}
        }
    
    def test_health(self) -> bool:
        """Verifica que el servicio esté saludable"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Servicio saludable")
                return True
            else:
                print(f"❌ Servicio no saludable: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error conectando al servicio: {e}")
            return False
    
    def classify_intention(self, text: str) -> Dict:
        """Clasifica una frase y retorna el enrutamiento completo"""
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/classify",
                json={
                    "text": text,
                    "candidate_labels": self.candidate_labels
                },
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                top_label = result["labels"][0]
                top_score = result["scores"][0]
                
                # Mapear a categoría simple
                if top_label in self.intention_map:
                    route = self.intention_map[top_label]
                    return {
                        "success": True,
                        "text": text,
                        "response_time": response_time,
                        "detected_label": top_label,
                        "detected_intention": route["intention"],
                        "suggested_integration": route["integration"],
                        "confidence": top_score,
                        "all_predictions": list(zip(result["labels"], result["scores"]))
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Label no mapeado: {top_label}",
                        "response_time": response_time
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP Error: {response.status_code}",
                    "response_time": 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": 0
            }
    
    def test_single_intent(self, text: str, expected_intention: str = None):
        """Prueba una sola frase y muestra resultados detallados"""
        result = self.classify_intention(text)
        
        if not result["success"]:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"\n📝 Texto: '{text}'")
        print(f"⏱️  Tiempo: {result['response_time']:.2f}s")
        print(f"🏷️  Etiqueta detectada: {result['detected_label']}")
        print(f"🎯 Intención: {result['detected_intention']}")
        print(f"🔗 Integración sugerida: {result['suggested_integration']}")
        print(f"📊 Confianza: {result['confidence']:.2%}")
        
        if expected_intention:
            if result['detected_intention'] == expected_intention:
                print(f"✅ CORRECTO (esperado: {expected_intention})")
            else:
                print(f"❌ INCORRECTO (esperado: {expected_intention})")
        
        # Mostrar top 3 predicciones
        print("📈 Top 3 predicciones:")
        for i, (label, score) in enumerate(result['all_predictions'][:3]):
            simple_intention = self.intention_map.get(label, {}).get('intention', 'N/A')
            print(f"   {i+1}. {simple_intention}: {score:.2%}")
    
    def run_test_suite(self):
        """Ejecuta una suite completa de pruebas con las nuevas categorías"""
        test_cases = [
            # (texto, intención_esperada)
            ("Analiza este documento PDF que subí", "analizar_documento_usuario"),
            ("Revisa el archivo Excel que cargué", "analizar_documento_usuario"),
            ("No puedo iniciar sesión en la plataforma", "soporte_tecnico"),
            ("La aplicación se cierra inesperadamente", "soporte_tecnico"),
            ("¿Qué hace esta empresa?", "informacion_empresa"),
            ("Cuéntame sobre la historia de la compañía", "informacion_empresa"),
            ("¿Cómo solicito vacaciones?", "consultar_proceso"),
            ("Proceso para aprobación de gastos", "consultar_proceso"),
            ("¿Cuál es el precio del dólar hoy?", "consulta_tiempo_real"),
            ("Noticias recientes sobre tecnología", "consulta_tiempo_real"),
            ("¿Cuál es el estado de mi pedido?", "acceso_api"),
            ("Necesito mi saldo de cuenta", "acceso_api"),
            ("¿Cómo funciona tu inteligencia artificial?", "informacion_ia"),
            ("Qué modelos de IA utilizas", "informacion_ia"),
            ("Hola, ¿cómo estás?", "conversacion_general"),
            ("Cuéntame un chiste", "conversacion_general"),
            ("Buenos días", "conversacion_general"),
            ("Que es Grupo Reyes?", "informacion_empresa"),
            ("¿Quien eres?", "informacion_ia"),
        ]
        
        print("🚀 INICIANDO SUITE DE PRUEBAS - ENRUTAMIENTO AVANZADO")
        print("=" * 60)
        
        # Test de salud primero
        if not self.test_health():
            return
        
        # Ejecutar casos de prueba
        correct = 0
        total = len(test_cases)
        
        for text, expected in test_cases:
            self.test_single_intent(text, expected)
            print("-" * 50)
        
        print(f"\n📈 Resumen: {correct}/{total} correctos")
    
    def benchmark_performance(self, text: str = "Hola, ¿cómo estás?", iterations: int = 10):
        """Prueba de rendimiento con múltiples iteraciones"""
        print(f"\n⚡ PRUEBA DE RENDIMIENTO ({iterations} iteraciones)")
        print("=" * 50)
        
        times = []
        successes = 0
        
        for i in range(iterations):
            result = self.classify_intention(text)
            if result["success"]:
                times.append(result["response_time"])
                successes += 1
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            print(f"⏱️  Tiempo promedio: {avg_time:.3f}s")
            print(f"⏱️  Tiempo mínimo: {min_time:.3f}s")
            print(f"⏱️  Tiempo máximo: {max_time:.3f}s")
            print(f"📊 Iteraciones exitosas: {successes}/{iterations}")
            
            if successes > 0:
                result = self.classify_intention(text)
                print(f"🎯 Ejemplo de clasificación: {result['detected_intention']} ({result['confidence']:.2%})")

    def interactive_test(self):
        """Modo interactivo para probar frases personalizadas"""
        print("\n🔍 MODO INTERACTIVO - Prueba frases personalizadas")
        print("Escribe 'quit' para salir")
        
        while True:
            text = input("\n📝 Ingresa la frase a clasificar: ").strip()
            
            if text.lower() in ['quit', 'exit', 'salir']:
                break
                
            if not text:
                continue
                
            self.test_single_intent(text)

def main():
    tester = IntentTester()
    
    while True:
        print("\n🎯 MENU DE TESTING - SISTEMA DE ENRUTAMIENTO")
        print("1. Suite completa de pruebas")
        print("2. Probar frase específica")
        print("3. Prueba de rendimiento") 
        print("4. Modo interactivo")
        print("5. Salud del servicio")
        print("6. Salir")
        
        choice = input("\nSelecciona una opción (1-6): ").strip()
        
        if choice == "1":
            tester.run_test_suite()
        elif choice == "2":
            text = input("Ingresa la frase a probar: ").strip()
            expected = input("Intención esperada (opcional): ").strip() or None
            tester.test_single_intent(text, expected)
        elif choice == "3":
            text = input("Frase para benchmark (enter para default): ").strip()
            if not text:
                text = "Hola, ¿cómo estás?"
            tester.benchmark_performance(text)
        elif choice == "4":
            tester.interactive_test()
        elif choice == "5":
            tester.test_health()
        elif choice == "6":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()