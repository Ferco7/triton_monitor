class TritonError(Exception):
    """Excepción base para el sistema Triton (nunca heredar de BaseException)."""
    pass
class ProviderTimeoutError(TritonError):
    """Excepión para timeouts de red."""
    pass
class CorruptedPayloadError(TritonError):
    """Excepción para respuestas corruptas o estatus HTTP fallidos."""
    pass
class NetworkPeeringError(TritonError):
    """Excepción para fallos de DNS o resolucion de hosts."""
    pass
