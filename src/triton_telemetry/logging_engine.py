# src/triton_telemetry/logging_engine.py

import json
import logging
import logging.config
import logging.handlers
import queue
import os
import gzip
import shutil
from datetime import datetime, timezone
from typing import Any, Dict

# --- Callbacks de Compresion GZIP (Facundo Alegre) ---
def gzip_namer(name: str) -> str:
    """Modifica el nombre del archivo de backup agregando la extension .gz."""
    return name + ".gz"

def gzip_rotator(source: str, dest: str):
    """Comprime el archivo rotado a .gz y elimina el original."""
    with open(source, 'rb') as f_in:
        with gzip.open(dest, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(source)


# --- Formateador JSON (Mauricio Mamani) ---
class AsyncJSONFormatter(logging.Formatter):
    """
    Formateador JSON de nivel productivo capaz de serializar tracebacks,
    estructuras complejas recursivas y metadatos dinámicos.
    """

    #Control de objetos no serializables 
    @staticmethod
    def _json_default(value: Any) -> str:
        """Convierte datetimes a ISO 8601 UTC estricto (con Z), y el resto a texto."""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                dt_utc = value.replace(tzinfo=timezone.utc)
            else:
                dt_utc = value.astimezone(timezone.utc)
            
            return dt_utc.isoformat().replace("+00:00", "Z")
            
        return str(value)

    def _serialize_exception(self, exc: BaseException) -> Dict[str, Any]:
        """Estructura recursivamente excepciones, notas y causas."""
        exc_data: Dict[str, Any] = {
            "class": exc.__class__.__name__,
            "message": str(exc),
            "notes": list(getattr(exc, "__notes__", []))
        }

        # Extracción de httpx envuelta en try/except para
        # evitar el RuntimeError al acceder a .request
        if exc.__class__.__module__.startswith("httpx"):
            try:
                request = getattr(exc, "request", None)
                if request:
                    exc_data["httpx_request"] = {
                        "method": getattr(request, "method", None),
                        "url": str(getattr(request, "url", ""))
                    }
                response = getattr(exc, "response", None)
                if response:
                    exc_data["httpx_response"] = {
                        "status_code": getattr(response, "status_code", None),
                        "reason_phrase": getattr(response, "reason_phrase", None),
                        "url": str(getattr(response, "url", ""))
                    }
            # Si httpx colapsa al leer la propiedad, simplemente la ignoramos
            except RuntimeError:
                pass  

        # Control para ExceptionGroup
        if isinstance(exc, BaseExceptionGroup):
            exc_data["nested_exceptions"] = [
                self._serialize_exception(nested_err)
                for nested_err in exc.exceptions
            ]
          
        # ExceptionGroup también puede tener una causa raíz (__cause__).
        if getattr(exc, "__cause__", None):
            exc_data["cause"] = self._serialize_exception(exc.__cause__)

        return exc_data

    def format(self, record: logging.LogRecord) -> str:
        dt_utc = datetime.fromtimestamp(record.created, tz=timezone.utc)

        log_payload: Dict[str, Any] = {
            "timestamp": dt_utc.isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "process": record.process,
            "threadName": record.threadName,
            "async_task": getattr(record, "taskName", None),
            "filename": record.filename,
            "line": record.lineno
        }

        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            if exc_value:
                log_payload["exception_tree"] = self._serialize_exception(
                    exc_value
                )
                log_payload["stack_trace"] = self.formatException(
                    record.exc_info
                )

        reserved_fields = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName"
        }

        for key, value in record.__dict__.items():
            if key not in reserved_fields and not key.startswith('_'):
                if key in log_payload:
                    log_payload.setdefault("extra", {})[key] = value
                else:
                    log_payload[key] = value

        return json.dumps(log_payload, ensure_ascii=False, default=self._json_default)

# --- Pipeline No Bloqueante (Facundo Alegre) ---
def setup_triton_logging(log_filename: str = "triton_services.log") -> logging.Logger:
    """Configura el logging con QueueHandler y QueueListener."""

    logging_schema = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json_structured": {"()": AsyncJSONFormatter},
            "console_clean": {
                "format": "%(asctime)s [%(levelname)s] (%(taskName)s) %(message)s",
                "datefmt": "%H:%M:%S"
            }
        },
        "handlers": {
            "stdout_console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "console_clean",
                "stream": "ext://sys.stdout"
            },
            "rotating_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "json_structured",
                "filename": log_filename,
                "maxBytes": 2 * 1024 * 1024,  # 2 MB
                "backupCount": 3,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "triton_monitor": {
                "level": "DEBUG",
                "handlers": ["stdout_console", "rotating_file"],
                "propagate": False
            }
        }
    }

    logging.config.dictConfig(logging_schema)
    app_logger = logging.getLogger("triton_monitor")

    # --- Inyección de callbacks de compresión GZIP ---
    for handler in app_logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.namer = gzip_namer
            handler.rotator = gzip_rotator

    # --- Desacoplamiento no bloqueante con Queue ---
    log_queue = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)

    # Tomamos los handlers síncronos y se los pasamos al listener
    real_handlers = app_logger.handlers
    listener = logging.handlers.QueueListener(log_queue, *real_handlers, respect_handler_level=True)

    # Reemplazamos los handlers del logger por el QueueHandler
    app_logger.handlers = [queue_handler]

    # Iniciamos el listener en un hilo secundario y lo guardamos como atributo
    listener.start()
    app_logger.listener = listener

    return app_logger
