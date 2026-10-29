
from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.models.user import User


router = APIRouter(
    prefix="/roles",
    tags=["Role-Based Access Control"],
)


@router.get("/admin")
def admin_dashboard(
    user: User = Depends(require_roles("admin")),
):
    return {
        "message": "Welcome to Admin Dashboard",
        "role": user.role,
    }


@router.get("/manager")
def manager_dashboard(
    user: User = Depends(require_roles("admin", "manager")),
):
    return {
        "message": "Welcome to Manager Dashboard",
        "role": user.role,
    }


@router.get("/employee")
def employee_dashboard(
    user: User = Depends(
        require_roles("admin", "manager", "employee")
    ),
):
    return {
        "message": "Welcome to Employee Dashboard",
        "role": user.role,
    }
