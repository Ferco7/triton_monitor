"""
Formateador JSON estructurado y pipeline de logging no bloqueante.
Cola segura en memoria + RotatingFileHandler + compresion Gzip.

responsable: integrante 3 (formatter)
responsable: integrante 4 (pipeline)

INSTRUCCIONES:
PARTE 1 (Integrante 3) - Formatter:
1. Crear clase AsyncJSONFormatter que herede de logging.Formatter
2. Implementar _serialize_exception para serializar ExceptionGroups recursivamente
3. Implementar format para convertir LogRecord a JSON

PARTE 2 (Integrante 4) - Pipeline:
1. Crear callbacks gzip_namer y gzip_rotator para compresion
2. Crear setup_triton_logging con dictConfig
3. Configurar RotatingFileHandler (2MB, 3 backups)
4. Configurar QueueHandler + QueueListener

REGLAS:
- AsyncJSONFormatter debe heredar de logging.Formatter
- _serialize_exception debe ser recursivo (ExceptionGroup anidados)
- format debe retornar un string JSON
- gzip_namer agrega extension .gz
- gzip_rotator comprime con gzip y elimina original
- setup_triton_logging configura dictConfig con ambos handlers
- RotatingFileHandler: maxBytes=2MB, backupCount=3
- QueueHandler + QueueListener para desacoplamiento no bloqueante
"""

# IMPORTS PERMITIDOS:
# import json
# import logging
# import logging.config
# import logging.handlers
# import queue
# import os
# import gzip
# import shutil
# from datetime import datetime, timezone
# from typing import Any, Dict

# CLASE: AsyncJSONFormatter(logging.Formatter)
# Metodos:
#   _serialize_exception(exc: BaseException) -> dict
#     - Serializa recursivamente excepciones
#     - Soporta ExceptionGroup (nested_exceptions)
#     - Soporta encadenamiento (__cause__)
#     - Captura __notes__
#
#   format(record: logging.LogRecord) -> str
#     - Convierte LogRecord a JSON
#     - Incluye: timestamp ISO 8601 UTC, level, logger, message
#     - Incluye: async_task, thread_name, filename, line
#     - Incluye: exception_tree, stack_trace (si hay excepcion)
#     - Incluye: metadatos dinamicos via extra

# FUNCION 1: gzip_namer(name: str) -> str
# - Agrega extension .gz al nombre del archivo

# FUNCION 2: gzip_rotator(source: str, dest: str) -> None
# - Comprime source a dest usando gzip
# - Elimina source despues de comprimir

# FUNCION 3: setup_triton_logging(log_filename: str = "triton_services.log") -> logging.Logger
# - Configura dictConfig con:
#   - formatter json_structured (AsyncJSONFormatter)
#   - formatter console_clean (formato legible)
#   - handler stdout_console (StreamHandler)
#   - handler rotating_file (RotatingFileHandler)
#   - logger triton_monitor con ambos handlers
# - Inyecta callbacks gzip_namer y gzip_rotator
# - Configura QueueHandler + QueueListener
# - Retorna el logger configurado
