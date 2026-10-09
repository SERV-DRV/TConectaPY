from app.config import settings


def get_payment_service():
    """Retorna la implementación de pago según entorno"""
    if settings.use_stripe:
        from app.services.transaction_service_Stp import StripePaymentService
        return StripePaymentService()
    else:
        from app.services.transaction_service import SimulationPaymentService
        return SimulationPaymentService()