import argparse
import re

def parse_timeout(value: str) -> float:
    """Valida y restringe el parametro --timeout de 0.1 a 5.0 segundos."""
    try:
        val = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("El valor del timeout debe ser numerico.")
    
    if not (0.1 <= val <= 5.0):
        raise argparse.ArgumentTypeError("El parámetro --timeout debe estar estrictamente entre 0.1 y 5.0 segundos.")
    
    return val

def parse_cluster_id(cluster_id: str) -> str:
    """Valida mediante expresiones regulares el formato cluster-<region>-<numero>."""
    patron = r"^cluster-[a-z-]+-\d{2}$"
    if not re.match(patron, cluster_id):
        raise argparse.ArgumentTypeError(f"El identificador de cluster '{cluster_id}' no cumple con el patrón requerido 'cluster-<region>-<numero>'.")
    return cluster_id
