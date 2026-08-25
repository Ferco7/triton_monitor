"""
Logica asincrona de consulta paralela con httpx + asyncio.gather + ExceptionGroup.
Consume APIs reales en internet (jsonplaceholder, httpbin).

responsable: integrante 2

INSTRUCCIONES:
1. Crear 2 funciones asincronas
2. query_provider_telemetry: consulta la API de un proveedor
3. scan_all_providers: orquesta las 3 consultas en paralelo
4. Capturar errores httpx y relanzar como excepciones de Triton
5. Usar asyncio.gather + ExceptionGroup manual para ejecucion paralela

REGLAS:
- Usar httpx.AsyncClient para las peticiones HTTP
- Usar asyncio.gather con return_exceptions=True para ejecucion paralela
- Recolectar todas las excepciones en una lista
- Si hay errores, crear ExceptionGroup manualmente con raise ExceptionGroup(..., errors)
- NO usar asyncio.TaskGroup (cancela las demas tareas al fallar una, perdiendo excepciones)
- Capturar httpx.TimeoutException -> ProviderTimeoutError
- Capturar httpx.HTTPStatusError -> NetworkPeeringError
- Capturar httpx.RequestError -> NetworkPeeringError
- Capturar json.JSONDecodeError -> CorruptedPayloadError
- Usar add_note() para agregar contexto forense
- Usar raise ... from para encadenar excepciones
"""

# IMPORTS PERMITIDOS:
# import asyncio
# import logging
# import json
# import httpx
# from typing import Any, Dict
# from .exceptions import ProviderTimeoutError, CorruptedPayloadError, NetworkPeeringError

# VARIABLES GLOBALES:
# PROVIDER_ENDPOINTS = {
#     "AWS": "https://jsonplaceholder.typicode.com/posts/1",
#     "Azure": "https://jsonplaceholder.typicode.com/posts/2",
#     "GCP": "https://jsonplaceholder.typicode.com/posts/3"
# }
# CHAOS_ENDPOINTS = {
#     "TIMEOUT_TRIGGER": "https://httpbin.org/delay/3",
#     "BAD_GATEWAY_TRIGGER": "https://httpbin.org/status/504",
#     "CORRUPTED_TRIGGER": "https://httpbin.org/xml"
# }

# FUNCION 1: query_provider_telemetry
# - Recibe: provider (str), timeout (float), use_chaos (bool)
# - Retorna: dict con keys: provider, status, latency_sec, payload_id
# - Lanza: ProviderTimeoutError, CorruptedPayloadError, NetworkPeeringError
# - Reglas:
#   - Si use_chaos es True, usar CHAOS_ENDPOINTS
#   - Si use_chaos es False, usar PROVIDER_ENDPOINTS
#   - Usar httpx.AsyncClient con timeout
#   - Capturar errores y relanzar como excepciones de Triton
#   - Agregar notas con add_note()

# TODO: Crear funcion async query_provider_telemetry(provider: str, timeout: float, use_chaos: bool = False) -> dict

# FUNCION 2: scan_all_providers
# - Recibe: providers (list), timeout (float), use_chaos (bool)
# - Retorna: list de dicts (resultados de cada proveedor)
# - Lanza: ExceptionGroup (si multiples fallas)
# - Reglas:
#   - Usar asyncio.gather(*tasks, return_exceptions=True)
#   - Recolectar excepciones en una lista
#   - Crear ExceptionGroup manual: raise ExceptionGroup("msg", errors)
#   - Retornar lista de resultados exitosos

# TODO: Crear funcion async scan_all_providers(providers: list, timeout: float, use_chaos: bool = False) -> list
