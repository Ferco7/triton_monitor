# Tests - Simulacion de Caos y Pruebas Forenses

responsable: integrante 6

## Que es esta carpeta

Esta carpeta contiene los scripts de validacion del proyecto Triton.
Cada escenario prueba un comportamiento diferente del CLI.

## Escenarios

### Escenario A: Nominal
- Que hace: Ejecuta el CLI con args validos y 3 proveedores
- Resultado esperado: Exit code 0, resultados impressos en stdout
- Comando:
  ```
  python3 src/app_operator.py AWS GCP Azure -c cluster-us-east-01 -t 3.0
  ```

### Escenario B: Argumentos invalidos
- Que hace: Ejecuta el CLI sin argumentos
- Resultado esperado: Exit code 2, error de argparse, NO se ejecuta asyncio
- Comando:
  ```
  python3 src/app_operator.py
  ```

### Escenario C: Chaos
- Que hace: Ejecuta el CLI con los 3 proveedores en modo caos
- Resultado esperado: Exit code 1, ExceptionGroup con 3 excepciones (timeout, 504, corrupted)
- Comando:
  ```
  python3 src/app_operator.py AWS GCP Azure -c cluster-us-east-01 -t 3.0 --chaos
  ```

## Como ejecutar

```bash
python3 tests/test_scenarios.py
```

## Reglas

- NO modificar archivos en src/
- NO instalar dependencias nuevas
- Python 3.11+ (requerido para ExceptionGroup y except*)
- Windows y Linux compatibles
- Usar subprocess.run() para ejecutar el CLI como proceso separado
- El test es externo al paquete (no importa de src/)
