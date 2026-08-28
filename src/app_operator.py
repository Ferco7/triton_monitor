"""
Punto de entrada CLI oficial del TritonMonitor.
Configura argparse, inyecta logging y ejecutar el modulo asincrono
"""
import sys
import argparse
import asyncio
import logging
from triton_telemetry import(
    setup_triton_logging,
    scan_all_providers,
    parse_timeout,
    parse_cluster_id,
    ProviderTimeoutError,
    NetworkPeeringError,
    CorruptedPayloadError,
    TritonError
)

#Proveedores cloud soportados
VALID_PROVIDERS = ("AWS", "Azure", "GCP")

def build_cli_parser() -> argparse.ArgumentParser:
    """Configura y retorna el parser de argumetos CLI de TritomMonitor."""
    parser = argparse.ArgumentParser(
        prog="tritonmonitor",
        description="Consola de Telemetría Multicloud"
    )
    
    #argumentos posicionales y opciones
    parser.add_argument(
        "proveedores",
        nargs="+",
        choices=VALID_PROVIDERS,
        help=f"proveedores a monitorear ({', '.join(VALID_PROVIDERS)})"
    )
    parser.add_argument(
        "-c", "--cluster-id",
        type=parse_cluster_id,
        required=True,
        help="ID del cluster a monitorear"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=parse_timeout,
        default=2.5,
        help="Timeout por peticion HTTP en segundos (0.1 - 5.0)."
    )
    parser.add_argument(
        "--chaos",
        action="store_true",
        help="Activa el modo de inyeccion de fallos (chaos testing)"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["nominal", "debug", "emergency"],
        default="nominal",
        help="Modo de ejecucion del monitor"
    )
    
    return parser

async def async_main() -> None:
    """Flujo principal: parsea argumentos, configura logging, ejecuta el escaneo
    asincrono y captura quirurgicamente cada categoria de fallo con except*."""
    parser = build_cli_parser()
    args = parser.parse_args()
    
    #Logger configurado segun modo
    logger = setup_triton_logging()
    had_failures = False
    
    #Encabezado del monitoreo
    logger.info("=" * 64)
    logger.info("INICIANDO MONITOREO MULTICLOUD: PROYECTO TRITON")
    logger.info(f"Cluster objetivo: {args.cluster_id}")
    logger.info(f"Modo operativo: {args.mode.upper()}")
    logger.info(f"Provedores seleccionados: {', '.join(args.proveedores)}")
    logger.info(f"Timeout limite configurado: {args.timeout}s")
    if args.chaos:
        logger.warning("MODO CAOS ACTIVADO: se inyectaran fallas reales de red.")
    logger.info("=" * 64)
    
    try:
        #Escaneo concurrente de proveedores
        results = await scan_all_providers(
            args.proveedores, args.timeout, use_chaos=args.chaos
        )
        
        #Resultados exitoso
        logger.info("ESCANEO COMPLETADO SIN ANOMALIAS:")
        for r in results:
            logger.info(
                f"  * {r['provider']} -> latencia={r['latency_sec']:.3f}s "
                f" | id={r['payload_id']}  | estado={r['status']}"
            )
    
    #Captura de errores por categoria
    except* ProviderTimeoutError as group:
        had_failures = True
        logger.error(f"ANOMALIA: timeouts en proveedores cloud ({len(group.exceptions)} incidente/s): ")
        for exc in group.exceptions:
            logger.error(f" Fallo: {exc}")
            for note in getattr(exc, "__notes__", []):
                logger.error(f"   -> [FORENSE TRITON] {note}")
    
    except* NetworkPeeringError as group:
        had_failures = True
        logger.error(f"ANOMALIA: fallos de red/DNS/routing ({len(group.exceptions)} incidente/s): ")
        for exc in group.exceptions:
            logger.error(f" Fallo: {exc}")
            for note in getattr(exc, "__notes__", []):
                logger.error(f"   -> [FORENSE TRITON] {note}")
                    
    except* CorruptedPayloadError as group:
        had_failures = True
        logger.error(f"ADVERTENCIA: payloads o estatus HTTP corruptos ({len(group.exceptions)} incidente/s): ")
        for exc in group.exceptions:
            logger.error(f" Fallo: {exc}")
            for note in getattr(exc, "__notes__", []):
                logger.error(f"   -> [FORENSE TRITON] {note}")
    
    except* TritonError as group:
        had_failures = True
        logger.error(f"ERROR OPERACIONAL: fallo imprevisto en triton ({len(group.exceptions)} incidente/s): ")
        for exc in group.exceptions:
            logger.error(f" Fallo: {exc}")
    
    finally:
        # PEP 765 / Python 3.11+: solo liberacion de recursos, sin return/break/continue
        logger.info("=" * 64)
        logger.info("[FIN DE CICLO] Liberando recursos de la operacion Triton.")
        logger.info("=" * 64)
        listener = getattr(logger, "listener", None)
        if listener is not None:
            listener.stop()
    
    #Codigo de salida segun resultado
    if had_failures:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(async_main())