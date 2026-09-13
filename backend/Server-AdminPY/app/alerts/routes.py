from fastapi import APIRouter, Depends
from app.middlewares.validate_jwt import validate_jwt, require_admin_role
from app.middlewares.alerts_validators import AlertCreate, AlertStatusUpdate
from app.alerts.controller import create_alert, get_active_alerts, resolve_alert, delete_alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def list_alerts(_=Depends(validate_jwt)):
    return await get_active_alerts()


@router.post("", status_code=201)
async def add_alert(data: AlertCreate, _=Depends(require_admin_role)):
    return await create_alert(data.model_dump())


@router.put("/{alert_id}/status")
async def update_alert_status(alert_id: str, data: AlertStatusUpdate, _=Depends(require_admin_role)):
    return await resolve_alert(alert_id, data.status.value)


@router.delete("/{alert_id}")
async def remove_alert(alert_id: str, _=Depends(require_admin_role)):
    return await delete_alert(alert_id)
