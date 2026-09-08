from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models.role import Permission, Role
from app.models.user import User
from app.schemas.role import (
    MODULES,
    SUB_MODULES,
    ModulesResponse,
    PermissionItem,
    PermissionsBulkUpdate,
    PermissionsMatrixRow,
    RoleCreate,
    RoleDetail,
    RoleOut,
    RoleUpdate,
)

router = APIRouter(prefix="/api/roles", tags=["roles"])


def _all_keys() -> list[tuple[str, str | None]]:
    """Every (module, sub_module) slot the matrix should show."""
    keys: list[tuple[str, str | None]] = []
    for module in MODULES:
        keys.append((module, None))
        for sub in SUB_MODULES.get(module, ()):
            keys.append((module, sub))
    return keys


def _permissions_for(db: Session, role_id: int) -> list[PermissionItem]:
    rows = db.scalars(select(Permission).where(Permission.role_id == role_id)).all()
    by_key = {(r.module, r.sub_module): r for r in rows}
    out: list[PermissionItem] = []
    for module, sub in _all_keys():
        p = by_key.get((module, sub))
        out.append(PermissionItem(
            module=module,
            sub_module=sub,
            can_view=p.can_view if p else False,
            can_create=p.can_create if p else False,
            can_edit=p.can_edit if p else False,
            can_delete=p.can_delete if p else False,
            can_export=p.can_export if p else False,
        ))
    return out


def _user_count(db: Session, role_name: str) -> int:
    return db.scalar(
        select(func.count(User.id)).where(User.role == role_name, User.deleted_at.is_(None))
    ) or 0


@router.get("/modules", response_model=ModulesResponse)
def list_modules(_: User = Depends(get_current_user)):
    return ModulesResponse(
        modules=list(MODULES),
        sub_modules={k: list(v) for k, v in SUB_MODULES.items()},
    )


@router.get("/matrix", response_model=list[PermissionsMatrixRow])
def matrix(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    out: list[PermissionsMatrixRow] = []
    for role in db.scalars(select(Role).order_by(Role.id)).all():
        out.append(PermissionsMatrixRow(
            role=role.name,
            role_id=role.id,
            permissions=_permissions_for(db, role.id),
        ))
    return out


@router.get("", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.scalars(select(Role).order_by(Role.id)).all()


@router.get("/{role_id}", response_model=RoleDetail)
def get_role(role_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    return RoleDetail(
        id=role.id,
        name=role.name,
        description=role.description,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=_permissions_for(db, role.id),
        user_count=_user_count(db, role.name),
    )


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    body: RoleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    if db.scalar(select(Role).where(Role.name == body.name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Role name already exists")
    role = Role(name=body.name, description=body.description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != role.name:
        if db.scalar(select(Role).where(Role.name == data["name"], Role.id != role.id)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Role name already in use")
    for field, value in data.items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    if _user_count(db, role.name) > 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Role is in use by one or more users")
    db.delete(role)
    db.commit()


@router.put("/{role_id}/permissions", response_model=list[PermissionItem])
def set_permissions(
    role_id: int,
    body: PermissionsBulkUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")

    valid_keys = set(_all_keys())
    incoming: dict[tuple[str, str | None], PermissionItem] = {}
    for p in body.permissions:
        key = (p.module, p.sub_module)
        if key not in valid_keys:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Unknown module/sub-module: {p.module}/{p.sub_module}",
            )
        incoming[key] = p

    existing = {
        (p.module, p.sub_module): p
        for p in db.scalars(select(Permission).where(Permission.role_id == role.id)).all()
    }

    for key, new in incoming.items():
        module, sub = key
        row = existing.get(key)
        if row is None:
            db.add(Permission(
                role_id=role.id,
                module=module,
                sub_module=sub,
                can_view=new.can_view,
                can_create=new.can_create,
                can_edit=new.can_edit,
                can_delete=new.can_delete,
                can_export=new.can_export,
            ))
        else:
            row.can_view = new.can_view
            row.can_create = new.can_create
            row.can_edit = new.can_edit
            row.can_delete = new.can_delete
            row.can_export = new.can_export

    for key, row in existing.items():
        if key not in incoming:
            db.delete(row)

    db.commit()
    return _permissions_for(db, role.id)
