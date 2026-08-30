"""
Tests - Simulacion de Caos y Pruebas Forenses
==============================================
Ejecuta los 3 escenarios de validacion del CLI Triton.
Cada escenario verifica un comportamiento diferente del sistema.

responsable: integrante 6
"""

import subprocess
import sys
import os

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Raiz del proyecto (dos niveles arriba de este archivo: tests/ -> raiz)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_PATH = os.path.join(PROJECT_ROOT, "src", "app_operator.py")


def run_cli(args, timeout):
    """Ejecuta el CLI como proceso separado y devuelve el CompletedProcess."""
    cmd = [sys.executable, CLI_PATH] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=PROJECT_ROOT,
    )


# ============================================================
# ESCENARIO A: NOMINAL
# ============================================================
def test_scenario_nominal() -> bool:
    print("\n--- Escenario A: Nominal ---")
    args = ["AWS", "GCP", "-c", "cluster-us-east-01", "-t", "3.0"]

    try:
        result = run_cli(args, timeout=30)
    except subprocess.TimeoutExpired:
        print(f"{RED}FAIL{RESET}: el CLI no respondio dentro del timeout")
        return False

    ok = True

    if result.returncode != 0:
        print(f"{RED}FAIL{RESET}: exit code {result.returncode} (esperado 0)")
        print(f"  stderr: {result.stderr.strip()}")
        ok = False

    if "ESCANEO COMPLETADO SIN ANOMALIAS" not in result.stdout:
        print(f"{RED}FAIL{RESET}: stdout no contiene 'ESCANEO COMPLETADO SIN ANOMALIAS'")
        ok = False

    for provider in ("AWS", "GCP"):
        if provider not in result.stdout:
            print(f"{RED}FAIL{RESET}: stdout no menciona al proveedor {provider}")
            ok = False

    if ok:
        print(f"{GREEN}PASS{RESET}: exit 0 y escaneo completado sin anomalias.")
    return ok


# ============================================================
# ESCENARIO B: ARGUMENTOS INVALIDOS
# ============================================================
def test_scenario_invalid_args() -> bool:
    print("\n--- Escenario B: Argumentos invalidos ---")
    args = ["AWS", "GCP", "-c", "cluster-invalido-id", "-t", "9.5"]

    try:
        result = run_cli(args, timeout=10)
    except subprocess.TimeoutExpired:
        print(f"{RED}FAIL{RESET}: el CLI no respondio dentro del timeout")
        return False

    ok = True

    if result.returncode != 2:
        print(f"{RED}FAIL{RESET}: exit code {result.returncode} (esperado 2)")
        ok = False

    if "cluster-invalido-id" not in result.stderr:
        print(f"{RED}FAIL{RESET}: stderr no menciona 'cluster-invalido-id'")
        ok = False

    if result.stdout.strip() != "":
        print(f"{RED}FAIL{RESET}: stdout deberia estar vacio (no se llego a ejecutar asyncio)")
        ok = False

    if ok:
        print(f"{GREEN}PASS{RESET}: exit 2, error de argparse, sin tocar la red.")
    return ok


# ============================================================
# ESCENARIO C: CHAOS
# ============================================================
def test_scenario_chaos() -> bool:
    print("\n--- Escenario C: Chaos ---")
    args = ["AWS", "Azure", "GCP", "-c", "cluster-us-west-02", "-t", "1.5", "--chaos"]

    try:
        result = run_cli(args, timeout=30)
    except subprocess.TimeoutExpired:
        print(f"{RED}FAIL{RESET}: el CLI no respondio dentro del timeout")
        return False

    ok = True

    if result.returncode != 1:
        print(f"{RED}FAIL{RESET}: exit code {result.returncode} (esperado 1)")
        ok = False

    fallos = result.stdout.count("Fallo:")
    if fallos != 3:
        print(f"{RED}FAIL{RESET}: stdout tiene {fallos} lineas 'Fallo:' (esperado 3)")
        ok = False

    if result.stderr.strip() != "":
        print(f"{RED}FAIL{RESET}: stderr deberia estar vacio (except* captura el ExceptionGroup)")
        ok = False

    if ok:
        print(f"{GREEN}PASS{RESET}: exit 1 y las 3 anomalias (timeout, 504, payload corrupto) reportadas.")
    return ok


# ============================================================
# MAIN
# ============================================================
def main() -> int:
    tests = [
        ("Escenario A - Nominal", test_scenario_nominal),
        ("Escenario B - Argumentos invalidos", test_scenario_invalid_args),
        ("Escenario C - Chaos", test_scenario_chaos),
    ]

    resultados = []
    for nombre, funcion in tests:
        passed = funcion()
        resultados.append((nombre, passed))

    print("\n" + "=" * 50)
    print("RESUMEN DE ESCENARIOS")
    print("=" * 50)

    total_pass = 0
    for nombre, passed in resultados:
        estado = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {nombre}: {estado}")
        if passed:
            total_pass += 1

    print(f"\nTotal: {total_pass}/{len(resultados)} escenarios pasaron.")

    return 0 if total_pass == len(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())