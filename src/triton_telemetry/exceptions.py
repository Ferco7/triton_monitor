"""
Excepciones semanticas del ecosistema TritonMonitor.

responsable: integrante 1

INSTRUCCIONES:
1. Crear 4 clases que hereden de Exception (NUNCA de BaseException)
2. TritonError es la clase base
3. Las otras 3 heredan de TritonError
4. Cada clase debe tener un docstring que explique cuando se lanza

REGLAS:
- NUNCA heredar de BaseException (para no capturar Ctrl+C)
- Cada excepcion representa un tipo de error del sistema
- Las excepciones se usan en core.py y app_operator.py
"""

# TODO: Crear las siguientes excepciones heredando de Exception

# TritonError -> Exception
# ProviderTimeoutError -> TritonError (cuando un proveedor tarda demasiado)
# CorruptedPayloadError -> TritonError (cuando la respuesta esta corrupta o es HTTP error)
# NetworkPeeringError -> TritonError (cuando falla DNS o la conexion de red)
