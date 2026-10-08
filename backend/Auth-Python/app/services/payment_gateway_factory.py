"""
Factory Pattern para seleccionar la implementación de pasarela de pago según entorno.

En production con Stripe configurado → StripePaymentService
En development o sin Stripe → SimulationPaymentService (Luhn actual)
"""

from app.config import settings


def get_payment_service():
    """
    Retorna la implementación de pago según configuración de entorno.
    
    Returns:
        Instancia del servicio de pago correspondiente
    """
    if settings.use_stripe:
        # Import lazy para evitar dependencias circulares
        from app.services.transaction_service_Stp import StripePaymentService
        return StripePaymentService()
    else:
        from app.services.transaction_service import SimulationPaymentService
        return SimulationPaymentService()


def get_payment_service_for_testing(force_stripe: bool = False):
    """
    Versión para testing que permite forzar Stripe.
    
    Args:
        force_stripe: Si True, usa Stripe independientemente del entorno
        
    Returns:
        Instancia del servicio de pago
    """
    if force_stripe or settings.use_stripe:
        from app.services.transaction_service_Stp import StripePaymentService
        return StripePaymentService()
    else:
        from app.services.transaction_service import SimulationPaymentService
        return SimulationPaymentService()