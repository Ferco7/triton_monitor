# Proyecto Triton - Telemetria Multicloud

## Grupo: Runtime Error 💀

## Integrantes

| Nombre                     |
| -------------------------- |
| Alegre, Facundo Sebastian  |
| Gaspar, Lautaro            |
| Herrera, Nancy Mariel      |
| Mamani, Hector Mauricio    |
| Rodriguez, Hector Fernando |
| Maldonado, Fernando        |

## Roles del Proyecto

| #   | Rol                                            | Archivo(s)                        | Integrante                 |
| --- | ---------------------------------------------- | --------------------------------- | -------------------------- |
| 1   | Robustez de Entradas y Excepciones             | `exceptions.py` + `sanitizer.py`  | Herrera, Nancy Mariel      |
| 2   | Concurrencia y Telemetria Asincrona            | `core.py`                         | Maldonado, Fernando        |
| 3   | Formateo Estructurado JSON                     | `logging_engine.py` (formatter)   | Mamani, Hector Mauricio    |
| 4   | Almacenamiento y Desacoplamiento No Bloqueante | `logging_engine.py` (pipeline)    | Alegre, Facundo Sebastian  |
| 5   | Integracion y Flujo CLI                        | `app_operator.py` + `__init__.py` | Rodriguez, Hector Fernando |
| 6   | Simulacion de Caos y Pruebas Forenses          | `tests/`                          | Gaspar, Lautaro            |

## Requisitos

- Python 3.11+
- httpx>=0.27.0

## Instalacion

```bash
git clone https://github.com/Ferco7/triton_monitor.git
cd triton_monitor
pip install -r requirements.txt
```

## Ejecucion

```bash
python3 src/app_operator.py AWS GCP -c cluster-us-east-01 -t 3.0
```

## Diagrama de Arquitectura

```mermaid
graph TD
    CLI["app_operator.py - CLI Entry"]
    SAN["sanitizer.py"]
    CORE["core.py - scan_all_providers"]
    AWS["httpx.AsyncClient - AWS"]
    AZURE["httpx.AsyncClient - Azure"]
    GCP["httpx.AsyncClient - GCP"]
    EXC["ExceptionGroup"]
    RES["results_list"]
    LOG_ENG["logging_engine.py - LogRecord"]
    QUEUE["queue.Queue - Thread-safe"]
    LISTENER["QueueListener - Hilo Secundario"]
    FMT["AsyncJSONFormatter"]
    HANDLER["RotatingFileHandler"]
    LOG_FILE["production_log.gz"]

    CLI -- "1. Sanitiza con argparse" --> SAN
    CLI -- "2. Inicia asyncio.run" --> CORE
    CORE -- "3. asyncio.gather" --> AWS
    CORE -- "3. asyncio.gather" --> AZURE
    CORE -- "3. asyncio.gather" --> GCP
    AWS -. "Falla / Timeout" .-> EXC
    AZURE -. "Falla / Red" .-> EXC
    GCP -. "Exito" .-> RES
    EXC -- "4. Propaga hacia" --> CLI
    CLI -- "5. Captura quirurgica except*" --> LOG_ENG
    LOG_ENG -- "6. Encola en microsegundos" --> QUEUE
    QUEUE -- "7. Consume desatendido" --> LISTENER
    LISTENER -- "8. Formatea a JSON recursivo" --> FMT
    LISTENER -- "9. Escribe y rota" --> HANDLER
    HANDLER -- "10. Rollover & Gzip" --> LOG_FILE
```

## Estructura del Proyecto

```
triton_monitor/
├── src/
│   ├── triton_telemetry/
│   │   ├── __init__.py          # API publica del paquete
│   │   ├── exceptions.py        # Excepciones semanticas custom
│   │   ├── sanitizer.py         # Validacion de argumentos CLI
│   │   ├── core.py              # Logica asincrona de red
│   │   └── logging_engine.py    # Formateador JSON y pipeline
│   └── app_operator.py          # Punto de entrada CLI
├── tests/
│   ├── README.md                # Instrucciones para tests
│   └── test_scenarios.py        # Escenarios de validacion
├── requirements.txt             # Dependencias del proyecto
├── .gitignore                   # Archivos ignorados por git
└── README.md                    # Este archivo
```
