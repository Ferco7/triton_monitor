"""
Excepciones semanticas del ecosistema TritonMonitor.

responsable: integrante 1
"""
class TritonError(Exception):
    """Excepción base para el sistema Triton (nunca heredar de BaseException)."""
    pass

class ProviderTimeoutError(TritonError):
    """Excepción para timeouts de red."""
    pass

class CorruptedPayloadError(TritonError):
    """Excepción para respuestas corruptas o estatus HTTP fallidos."""
    pass

class NetworkPeeringError(TritonError):
    """Excepción para fallos de DNS o resolución de hosts."""
    pass
