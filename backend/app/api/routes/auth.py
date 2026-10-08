import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.workspace import Membership, Workspace
from backend.app.api.dependencies import get_current_user

router = APIRouter()

class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=100)
    workspace_name: Optional[str] = "Primary Workspace"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class WorkspaceInfo(BaseModel):
    id: str
    name: str
    slug: str
    role: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    workspace: WorkspaceInfo

@router.post("/register", response_model=AuthResponse)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # Create user
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    await db.flush()

    # Create workspace
    slug = payload.workspace_name.lower().replace(" ", "-") + f"-{uuid.uuid4().hex[:6]}"
    workspace = Workspace(
        name=payload.workspace_name or "Primary Workspace",
        slug=slug,
    )
    db.add(workspace)
    await db.flush()

    # Create admin membership
    membership = Membership(
        user_id=user.id,
        workspace_id=workspace.id,
        role="admin",
    )
    db.add(membership)
    await db.commit()

    # Generate token
    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.name},
        workspace=WorkspaceInfo(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            role="admin",
        ),
    )

@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Get primary workspace
    mem_stmt = (
        select(Membership, Workspace)
        .join(Workspace, Membership.workspace_id == Workspace.id)
        .where(Membership.user_id == user.id)
        .limit(1)
    )
    mem_res = await db.execute(mem_stmt)
    mem_row = mem_res.first()

    if mem_row:
        membership, workspace = mem_row
        ws_info = WorkspaceInfo(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            role=membership.role,
        )
    else:
        # Fallback create workspace
        ws = Workspace(name="Default Workspace", slug=f"ws-{user.id[:8]}")
        db.add(ws)
        await db.flush()
        mem = Membership(user_id=user.id, workspace_id=ws.id, role="admin")
        db.add(mem)
        await db.commit()
        ws_info = WorkspaceInfo(id=ws.id, name=ws.name, slug=ws.slug, role="admin")

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.name},
        workspace=ws_info,
    )

@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mem_stmt = (
        select(Membership, Workspace)
        .join(Workspace, Membership.workspace_id == Workspace.id)
        .where(Membership.user_id == current_user.id)
    )
    res = await db.execute(mem_stmt)
    workspaces = [
        {"id": ws.id, "name": ws.name, "slug": ws.slug, "role": mem.role}
        for mem, ws in res.all()
    ]
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "workspaces": workspaces,
    }
