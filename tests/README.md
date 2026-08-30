# Tests - Simulacion de Caos y Pruebas Forenses

responsable: integrante 6

## Que es esta carpeta

Contiene los dos scripts de validacion del proyecto Triton:

- `test_scenarios.py`: suite de los 3 escenarios del CLI (exit codes y salida).
- `test_forensic_validator.py`: validador forense del log JSON + gzip.

## Escenario A: Nominal

- Que hace: Ejecuta el CLI con args validos y 2 proveedores (comando oficial de la consigna)
- Resultado esperado: Exit code 0 y stdout con el escaneo completo
- Aserciones sugeridas:
  - exit code == 0
  - stdout contiene "ESCANEO COMPLETADO SIN ANOMALIAS"
  - stdout lista los proveedores con estado OK
- Comando:
  ```
  python3 src/app_operator.py AWS GCP -c cluster-us-east-01 -t 3.0
  ```

## Escenario B: Argumentos invalidos

- Que hace: Ejecuta el CLI con cluster malformado y timeout fuera de rango (9.5)
- Resultado esperado: Exit code 2, error de argparse, NO se ejecuta asyncio
- Aserciones sugeridas:
  - exit code == 2
  - stderr menciona "cluster-invalido-id" (mensaje del sanitizer, sin tocar red)
- Comando:
  ```
  python3 src/app_operator.py AWS GCP -c cluster-invalido-id -t 9.5
  ```

## Escenario C: Chaos

- Que hace: Ejecuta el CLI con los 3 proveedores en modo caos
- Resultado esperado: Exit code 1, ExceptionGroup con 3 excepciones
  (timeout, 504, payload corrupto)
- Aserciones sugeridas:
  - exit code == 1
  - stdout contiene 3 lineas "Fallo:" (una por excepcion del arbol)
  - stderr vacio
- Comando:
  ```
  python3 src/app_operator.py AWS Azure GCP -c cluster-us-west-02 -t 1.5 --chaos
  ```

IMPORTANTE (correccion respecto a la plantilla original):

- Los logs del monitoreo salen por STDOUT (handler de consola). El STDOUT
  debe validarse para el escenario C; stderr queda vacio porque el
  ExceptionGroup se captura con except* y no propaga a la salida de error.
- Usar `-t 1.5` en caos: contra `httpbin.org/delay/3` (tarda ~3 segundos)
  el timeout se dispara de forma garantizada y `asyncio.gather` no cancela
  las demas tareas, asi se materializan las 3 categorias (timeout, 504 y
  payload corrupto). Con `-t 3.0` exactos es una carrera contra el endpoint.
- Las notas forenses (`[FORENSE ...]`) viajan dentro del nodo
  `exception_tree` del log; en consola aparecen como anotaciones del
  traceback (Python 3.11+). El check robusto de stdout es contar las
  lineas "Fallo:"; las notas se asertan en el arbol del registro
  (validador forense).

## Validador forense (test_forensic_validator.py)

Debe verificar sobre `triton_services.log` (generado por una corrida de caos):

0. IMPORTANTE: el RotatingFileHandler abre en modo append, por lo que
   `triton_services.log` acumula corridas. Antes de validar, eliminar el
   archivo previo (o regenerarlo) y asertar "al menos N" arboles, no un
   conteo exacto.

1. Esquema base por linea JSON: timestamp (ISO 8601 UTC terminado en Z),
   level, logger, message, process, threadName, async_task, filename, line.
2. `exception_tree` en los registros ERROR de caos: nodo recursivo con
   class, message, notes (add_note), cause (`__cause__`) con
   httpx_request/httpx_response (p.ej. `status_code: 504`),
   nested_exceptions para ExceptionGroup, y stack_trace en el registro.
3. Gzip: descompresion round-trip del log (comprimir y descomprimir debe
   devolver el contenido original) y, si existen backups rotados
   (`triton_services.log.N.gz`), abrirlos, descomprimirlos y parsearlos
   como JSON por linea.

## Como ejecutar (desde la raiz del proyecto)

```bash
python3 tests/test_scenarios.py
python3 tests/test_forensic_validator.py
```

## Reglas

- NO modificar archivos en src/
- NO instalar dependencias nuevas
- Python 3.11+ (requerido para ExceptionGroup y except*)
- Windows y Linux compatibles
- Usar subprocess.run() con capture_output=True y text=True para ejecutar el CLI como proceso separado
- Usar sys.executable para obtener la ruta del interprete Python
- El test es externo al paquete (NO importar nada de src/)
- No hardcodear rutas absolutas: usar os.path.join
- Colores: GREEN="\033[92m", RED="\033[91m", RESET="\033[0m"
- Timeout de 30 segundos para escenarios con red, 10 para invalid args