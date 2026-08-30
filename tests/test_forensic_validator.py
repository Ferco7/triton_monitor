"""
Tests - Validador Forense JSON/Gzip
===================================
Script forense que abre el log estructurado de Triton (triton_services.log),
verifica que cada linea sea JSON valido con el esquema base, que la
serializacion del ExceptionGroup contenga los errores httpx dentro de
exception_tree, y que la descompresion gzip funcione (round-trip y
backups *.gz de la rotacion del RotatingFileHandler).

responsable: integrante 6
"""

import subprocess
import sys
import os
import json
import gzip
import glob

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_PATH = os.path.join(PROJECT_ROOT, "src", "app_operator.py")
LOG_FILE = "triton_services.log"
LOG_PATH = os.path.join(PROJECT_ROOT, LOG_FILE)
CHAOS_ARGS = ["AWS", "GCP", "Azure", "-c", "cluster-us-east-01", "-t", "2.0", "--chaos"]

REQUIRED_KEYS = {
    "timestamp", "level", "logger", "message",
    "process", "threadName", "async_task", "filename", "line",
}


# ============================================================
# 1) GENERAR LOG EN MODO CAOS
# ============================================================
def generar_log_chaos() -> str:
    """Elimina el log previo (y sus backups) y corre el CLI en modo caos
    para producir un triton_services.log fresco con exception_tree."""
    for path in glob.glob(LOG_PATH + "*"):
        try:
            os.remove(path)
        except OSError:
            pass

    subprocess.run(
        [sys.executable, CLI_PATH] + CHAOS_ARGS,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=PROJECT_ROOT,
    )

    if not os.path.exists(LOG_PATH):
        raise RuntimeError(
            f"No se genero '{LOG_FILE}'. Verifica que la corrida de caos haya ejecutado."
        )

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return f.read()


def parsear_lineas_json(contenido_log: str) -> list:
    """Parsea cada linea no vacia del log como JSON. Lanza si alguna es invalida."""
    records = []
    for i, linea in enumerate(contenido_log.splitlines(), start=1):
        linea = linea.strip()
        if not linea:
            continue
        try:
            records.append(json.loads(linea))
        except json.JSONDecodeError as err:
            raise ValueError(f"Linea {i} no es JSON valido: {err}") from err
    return records


# ============================================================
# 2) ESQUEMA BASE
# ============================================================
def validar_esquema_base(records: list) -> bool:
    if not records:
        print(f"{RED}FAIL{RESET}: no hay registros para validar el esquema base.")
        return False

    ok = True
    for i, record in enumerate(records):
        faltantes = REQUIRED_KEYS - record.keys()
        if faltantes:
            print(f"{RED}FAIL{RESET}: registro {i} sin claves {faltantes}")
            ok = False
            continue
        ts = record["timestamp"]
        if not isinstance(ts, str) or not ts.endswith("Z"):
            print(f"{RED}FAIL{RESET}: timestamp '{ts}' no termina en 'Z' (ISO 8601 UTC)")
            ok = False

    if ok:
        print(f"{GREEN}PASS{RESET}: {len(records)} registros cumplen el esquema base.")
    return ok


# ============================================================
# 3) EXCEPTION_TREE (Req 4 / Rol 3)
# ============================================================
def _flatten_tree(node: dict, acumulador: list) -> None:
    """Recorre recursivamente cause y nested_exceptions, juntando todos los nodos."""
    acumulador.append(node)
    causa = node.get("cause")
    if isinstance(causa, dict):
        _flatten_tree(causa, acumulador)
    for anidada in node.get("nested_exceptions", []):
        if isinstance(anidada, dict):
            _flatten_tree(anidada, acumulador)


def validar_exception_tree(records: list) -> bool:
    error_records = [
        r for r in records
        if r.get("level") == "ERROR" and "exception_tree" in r
    ]

    if not error_records:
        print(f"{RED}FAIL{RESET}: no se encontro ningun registro ERROR con 'exception_tree'.")
        return False

    ok = True
    nodos_totales = []

    for i, record in enumerate(error_records):
        if not record.get("stack_trace"):
            print(f"{RED}FAIL{RESET}: registro ERROR {i} sin 'stack_trace'.")
            ok = False

        nodos = []
        _flatten_tree(record["exception_tree"], nodos)
        nodos_totales.extend(nodos)

        for nodo in nodos:
            faltantes = {"class", "message", "notes"} - nodo.keys()
            if faltantes:
                print(f"{RED}FAIL{RESET}: nodo del arbol sin claves {faltantes}")
                ok = False

    tiene_504 = any(
        nodo.get("httpx_response", {}).get("status_code") == 504
        for nodo in nodos_totales
    )
    if not tiene_504:
        print(f"{RED}FAIL{RESET}: ningun nodo httpx_response con status_code 504.")
        ok = False

    tiene_nota_forense = any(
        any("[FORENSE" in nota for nota in nodo.get("notes", []))
        for nodo in nodos_totales
    )
    if not tiene_nota_forense:
        print(f"{RED}FAIL{RESET}: ninguna nota forense '[FORENSE ...]' encontrada.")
        ok = False

    if ok:
        print(
            f"{GREEN}PASS{RESET}: exception_tree valido en "
            f"{len(error_records)} registro/s ERROR "
            f"(504 y notas forenses presentes)."
        )
    return ok


# ============================================================
# 4) GZIP
# ============================================================
def validar_gzip(contenido_log: str) -> bool:
    ok = True

    # --- Round-trip: comprimir y descomprimir debe devolver lo mismo ---
    original_bytes = contenido_log.encode("utf-8")
    comprimido = gzip.compress(original_bytes, compresslevel=9)
    descomprimido = gzip.decompress(comprimido)

    if descomprimido != original_bytes:
        print(f"{RED}FAIL{RESET}: el round-trip de gzip no devolvio el contenido original.")
        ok = False
    else:
        print(f"{GREEN}PASS{RESET}: round-trip gzip correcto ({len(original_bytes)} bytes).")

    # --- Backups rotados, si existen ---
    backups = sorted(glob.glob(LOG_PATH + ".*.gz"))
    if not backups:
        print(f"{GREEN}PASS{RESET}: no hay backups rotados (.gz) en esta corrida; nada que validar.")
        return ok

    for backup in backups:
        try:
            with gzip.open(backup, "rt", encoding="utf-8") as f:
                contenido_backup = f.read()
            for linea in contenido_backup.splitlines():
                linea = linea.strip()
                if linea:
                    json.loads(linea)
        except (OSError, json.JSONDecodeError) as err:
            print(f"{RED}FAIL{RESET}: backup '{backup}' invalido: {err}")
            ok = False

    if ok:
        print(f"{GREEN}PASS{RESET}: {len(backups)} backup/s .gz descomprimidos y parseados como JSON.")
    return ok


# ============================================================
# MAIN
# ============================================================
def main() -> int:
    print("\n--- Generando log de caos ---")
    try:
        contenido_log = generar_log_chaos()
    except RuntimeError as err:
        print(f"{RED}FAIL{RESET}: {err}")
        return 1

    try:
        records = parsear_lineas_json(contenido_log)
    except ValueError as err:
        print(f"{RED}FAIL{RESET}: {err}")
        return 1

    print("\n--- 1) Esquema base ---")
    r1 = validar_esquema_base(records)

    print("\n--- 2) Exception tree forense ---")
    r2 = validar_exception_tree(records)

    print("\n--- 3) Gzip ---")
    r3 = validar_gzip(contenido_log)

    resultados = [
        ("Esquema base", r1),
        ("Exception tree forense", r2),
        ("Gzip (round-trip + backups)", r3),
    ]

    print("\n" + "=" * 50)
    print("RESUMEN VALIDADOR FORENSE")
    print("=" * 50)

    total_pass = 0
    for nombre, passed in resultados:
        estado = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {nombre}: {estado}")
        if passed:
            total_pass += 1

    print(f"\nTotal: {total_pass}/{len(resultados)} validaciones pasaron.")

    return 0 if total_pass == len(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())