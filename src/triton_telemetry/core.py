"""
Logica asincrona de consulta paralela con httpx + asyncio.gather + ExceptionGroup.
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
            raise NetworkPeeringError(
                f"Fallo de red/DNS en '{provider}' (HTTP {err.response.status_code})."
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


async def scan_all_providers(
    providers: list, timeout: float, use_chaos: bool = False
) -> list:
    """Orquesta consultas paralelas a varios proveedores y agrupa errores."""
    tasks = [
        query_provider_telemetry(provider, timeout, use_chaos)
        for provider in providers
    ]

    # gather con return_exceptions=True NO cancela las demas tareas al fallar una,
    # de modo que se recolectan todas las excepciones (patron del Lab 3).
    results = await asyncio.gather(*tasks, return_exceptions=True)

    errors = [r for r in results if isinstance(r, Exception)]
    success = [r for r in results if not isinstance(r, Exception)]

    if errors:
        raise ExceptionGroup(
            "Anomalias criticas detectadas durante el escaneo multicloud.",
            errors,
        )

    return success
