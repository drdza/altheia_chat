# services/sql_agent.py
import httpx
import logging
from typing import Dict, Any
from core.config import settings

log = logging.getLogger(__name__)

API_ALTHEIA_SQL = settings.ALTHEIA_SQL

class SQLAgentService:
    def __init__(self, base_url: str = API_ALTHEIA_SQL):
        self.base_url = base_url
        self.timeout = 30.0
    
    async def generate_sql(self, question: str) -> Dict:
        """Genera SQL a partir de lenguaje natural"""
        try:
            payload = {
                "question": question,
                "domain": "tickets",
                "previous_question": ""
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate_sql",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            log.error(f"❌ Error en generate_sql: {e}")
            return {"error": str(e), "sql_query": None}
    
    async def execute_sql(self, sql_query: str) -> Dict:
        """Ejecuta la consulta SQL generada"""
        try:
            payload = {
                "sql": sql_query            
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/execute_sql", 
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            log.error(f"❌ Error en execute_sql: {e}")
            return {"error": str(e), "data": None}

# Instancia global
sql_agent = SQLAgentService()