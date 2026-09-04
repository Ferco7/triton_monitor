"""
Logica asincrona de consulta paralela con httpx + asyncio.TaskGroup + ExceptionGroup.
Consume APIs reales en internet (jsonplaceholder, httpbin).

responsable: integrante 2
"""
import asyncio
import json
import time

import httpx

from .exceptions import (
    CorruptedPayloadError,
    NetworkPeeringError,
    ProviderTimeoutError,
    TritonError,
)

# Proveedores cloud soportados (nombres alineados con app_operator.py)
PROVIDER_ENDPOINTS: dict[str, str] = {
    "AWS": "https://jsonplaceholder.typicode.com/posts/1",
    "Azure": "https://jsonplaceholder.typicode.com/posts/2",
    "GCP": "https://jsonplaceholder.typicode.com/posts/3",
}

# Endpoints de caos para el escenario de chaos testing
CHAOS_ENDPOINTS: dict[str, str] = {
    "TIMEOUT_TRIGGER": "https://httpbin.org/delay/3",
    "BAD_GATEWAY_TRIGGER": "https://httpbin.org/status/504",
    "CORRUPTED_TRIGGER": "https://httpbin.org/xml",
}


async def query_provider_telemetry(
    provider: str, timeout: float, use_chaos: bool = False
) -> dict:
    """Consulta la telemetria de un unico proveedor cloud (normal o chaos)."""
    # Seleccion de endpoint segun modo
    if use_chaos:
        # En modo caos, el proveedor no importa: todos caen en endpoints de fallo
        endpoint_keys = {"AWS": "TIMEOUT_TRIGGER", "Azure": "BAD_GATEWAY_TRIGGER", "GCP": "CORRUPTED_TRIGGER"}
        url = CHAOS_ENDPOINTS[endpoint_keys[provider]]
    else:
        url = PROVIDER_ENDPOINTS[provider]

    start = time.perf_counter()

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
            # Estado HTTP 4xx/5xx se traduce a error de red/peering
            if response.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            payload = response.json()
        except httpx.TimeoutException as err:
            err.add_note(f"[FORENSE] Timeout en proveedor '{provider}'")
            raise ProviderTimeoutError(
                f"El proveedor '{provider}' tardo demasiado ({timeout}s)."
            ) from err
        except httpx.HTTPStatusError as err:
            err.add_note(f"[FORENSE] HTTP {err.response.status_code} desde '{provider}'")
            raise CorruptedPayloadError(
                f"Estatus HTTP no esperado recibido desde '{provider}' (HTTP {err.response.status_code})."
            ) from err
        except httpx.RequestError as err:
            err.add_note(f"[FORENSE] Error de red en '{provider}': {err}")
            raise NetworkPeeringError(
                f"Fallo de conexion con '{provider}'."
            ) from err
        except json.JSONDecodeError as err:
            err.add_note(f"[FORENSE] Payload corrupto desde '{provider}'")
            raise CorruptedPayloadError(
                f"Respuesta corrupta o JSON invalido desde '{provider}'."
            ) from err

    latency_sec = time.perf_counter() - start

    return {
        "provider": provider,
        "status": "OK",
        "latency_sec": latency_sec,
        "payload_id": payload.get("id"),
    }


async def _run_mission_with_capture(
    provider: str, timeout: float, use_chaos: bool
):
    """Aisla el fallo de cada proveedor para que no cancele a las tareas
    hermanas dentro del TaskGroup (evita el fail-fast nativo). Devuelve el
    dict nominal o la excepcion semantica como sentinela de incidente."""
    try:
        return await query_provider_telemetry(provider, timeout, use_chaos)
    except TritonError as semantic_error:
        return semantic_error


async def scan_all_providers(
    providers: list, timeout: float, use_chaos: bool = False
) -> list:
    """Orquesta consultas paralelas a varios proveedores y agrupa errores.

    Se usa asyncio.TaskGroup con un wrapper (_run_mission_with_capture) que
    captura cada fallo como valor para evitar que el fail-fast de TaskGroup
    cancele a las demas tareas y se pierdan categorias del arbol forense.
    Luego los incidentes se agrupan en un ExceptionGroup para la captura
    quirurgica con except*.
    """
    async with asyncio.TaskGroup() as task_group:
        tasks = [
            task_group.create_task(
                _run_mission_with_capture(provider, timeout, use_chaos)
            )
            for provider in providers
        ]

    outcomes = [task.result() for task in tasks]

    errors = [o for o in outcomes if isinstance(o, Exception)]
    success = [o for o in outcomes if not isinstance(o, Exception)]

    if errors:
        raise ExceptionGroup(
            "Anomalias criticas detectadas durante el escaneo multicloud.",
            errors,
        )

    return success
