from fastapi import APIRouter, status, HTTPException
from app.schemas.workspace import WorkspaceResponse, WorkspaceCreate, WorkspaceUpdate
from app.auth import currentUser
from app.models import Workspace, User, List
from beanie import PydanticObjectId
from datetime import datetime, UTC

router = APIRouter()


@router.get("", response_model=list[WorkspaceResponse], status_code=status.HTTP_200_OK)
async def fetch_workspaces(current_user: currentUser):
    return await Workspace.find(Workspace.user_id == current_user.id).sort("+created_at").to_list()


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(current_user: currentUser, workspace_data: WorkspaceCreate):
    existing_workspace = await Workspace.find_one(
        Workspace.name == workspace_data.name,
        Workspace.user_id == current_user.id,
    )
    if existing_workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="workspace already present"
        )
    new_workspace = Workspace(name=workspace_data.name, user_id=current_user.id)
    await new_workspace.create()
    return new_workspace


@router.get(
    "/{workspace_id}", response_model=WorkspaceResponse, status_code=status.HTTP_200_OK
)
async def fetch_workspace_details(
    workspace_id: PydanticObjectId, current_user: currentUser
):
    workspace = await Workspace.find_one(
        Workspace.id == workspace_id, Workspace.user_id == current_user.id
    )
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    return workspace


@router.patch(
    "/{workspace_id}", response_model=WorkspaceResponse, status_code=status.HTTP_200_OK
)
async def update_workspace_partial(
    workspace_id: PydanticObjectId, update: WorkspaceUpdate, current_user: currentUser
):
    workspace = await Workspace.find_one(
        Workspace.id == workspace_id, Workspace.user_id == current_user.id
    )
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    if update.user_id != None:
        user = await User.find_one(User.id == update.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="updated user not found"
            )
        await workspace.update({"$set": {"user_id": user.id}})
    if update.name != None:
        existing_workspace = await Workspace.find_one(Workspace.name == update.name)
        if existing_workspace:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="workspace already present",
            )
        await workspace.update({"$set": {"name": update.name}})
    await workspace.update({"$set": {"updated_at": datetime.now(UTC)}})
    return await Workspace.get(workspace_id)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: PydanticObjectId, current_user: currentUser):
    workspace = await Workspace.find_one(
        Workspace.id == workspace_id, Workspace.user_id == current_user.id
    )
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    workspace_list = await List.find(List.workspace_id == workspace.id).to_list()
    for ws in workspace_list:
        await ws.delete()
    await workspace.delete()
