"""
Validacion declarativa de parametros CLI con argparse.
Intercepta datos corruptos antes de que lleguen al event loop.

responsable: integrante 1

INSTRUCCIONES:
1. Crear 2 funciones validadoras para argparse
2. parse_timeout: valida que el valor sea float entre 0.1 y 5.0
3. parse_cluster_id: valida que siga el patron cluster-<region>-<numero>
4. Si falla, lanzar argparse.ArgumentTypeError

REGLAS:
- Ambas funciones reciben str y retornan str o float
- Si el valor es invalido, deben lanzar argparse.ArgumentTypeError
- El mensaje de error debe incluir el valor que fallo
- parse_timeout debe convertir a float primero
- parse_cluster_id debe usar expresion regular con modulo re
"""

# IMPORTS PERMITIDOS:
# import argparse
# import re

# FUNCION 1: parse_timeout
# - Recibe: value (str)
# - Retorna: float
# - Reglas:
#   - Convertir a float
#   - Si no es numerico -> argparse.ArgumentTypeError
#   - Si esta fuera de rango [0.1, 5.0] -> argparse.ArgumentTypeError
#   - El mensaje debe incluir el valor invalido

# TODO: Crear funcion parse_timeout(value: str) -> float

# FUNCION 2: parse_cluster_id
# - Recibe: value (str)
# - Retorna: str (el mismo valor si es valido)
# - Reglas:
#   - Usar expresion regular con re
#   - Patron: cluster-<region>-<numero_dos_digitos>
#   - Ejemplo valido: cluster-us-east-01
#   - Si no cumple -> argparse.ArgumentTypeError

# TODO: Crear funcion parse_cluster_id(value: str) -> str
