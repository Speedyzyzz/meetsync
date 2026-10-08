from typing import Optional
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.auth import decode_access_token
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.workspace import Membership, Workspace

security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extracts and authenticates user from JWT Bearer token.
    Falls back to dev user in development if unauthenticated for local zero-config runs.
    """
    if credentials and credentials.credentials:
        token = credentials.credentials
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload["sub"]
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

    # Development fallback
    if settings.ENVIRONMENT == "development" or settings.DEBUG:
        stmt = select(User).where(User.id == settings.DEFAULT_USER_ID)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                id=settings.DEFAULT_USER_ID,
                email="developer@meetsync.ai",
                name="Lead Engineer",
            )
            db.add(user)
            await db.flush()
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_workspace(
    request: Request,
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """
    Resolves active workspace and strictly enforces tenant membership authorization.
    Rejects with 403 Forbidden if user is not an active member.
    """
    target_ws_id = x_workspace_id or settings.DEFAULT_WORKSPACE_ID

    # 1. Fetch workspace
    stmt = select(Workspace).where(Workspace.id == target_ws_id)
    res = await db.execute(stmt)
    workspace = res.scalar_one_or_none()
    if not workspace:
        # Check if user has any workspace membership
        mem_stmt = select(Membership).where(Membership.user_id == current_user.id).limit(1)
        mem_res = await db.execute(mem_stmt)
        first_mem = mem_res.scalar_one_or_none()
        if first_mem:
            ws_stmt = select(Workspace).where(Workspace.id == first_mem.workspace_id)
            ws_res = await db.execute(ws_stmt)
            workspace = ws_res.scalar_one_or_none()
        
        if not workspace:
            # Create default workspace if none exists
            workspace = Workspace(
                id=target_ws_id,
                name="Engineering & Product",
                slug=f"workspace-{target_ws_id[:8]}",
            )
            db.add(workspace)
            await db.flush()

    # 2. STRICT AUTHORIZATION CHECK: User must be a member of this workspace!
    mem_check_stmt = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.workspace_id == workspace.id,
    )
    mem_check_res = await db.execute(mem_check_stmt)
    membership = mem_check_res.scalar_one_or_none()

    if not membership:
        # In dev mode, auto-bind dev user to default workspace
        if (
            (settings.ENVIRONMENT == "development" or settings.DEBUG)
            and current_user.id == settings.DEFAULT_USER_ID
            and workspace.id == settings.DEFAULT_WORKSPACE_ID
        ):
            dev_membership = Membership(
                user_id=current_user.id,
                workspace_id=workspace.id,
                role="admin",
            )
            db.add(dev_membership)
            await db.flush()
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not a member of this workspace.",
            )

    return workspace
