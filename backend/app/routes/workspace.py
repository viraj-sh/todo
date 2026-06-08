from fastapi import APIRouter, status, HTTPException
from fastapi.responses import StreamingResponse
import json
from app.schemas.workspace import (
    WorkspaceResponse,
    WorkspaceCreate,
    WorkspaceUpdate,
    ExportFile,
)
from app.auth import currentUser
from app.models import Item, Workspace, List
from beanie import PydanticObjectId
from datetime import datetime, UTC

router = APIRouter()


@router.get(
    "",
    response_model=list[WorkspaceResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_workspaces",
)
async def fetch_workspaces(current_user: currentUser):
    return (
        await Workspace.find(Workspace.user_id == current_user.id)
        .sort("+created_at")
        .to_list()
    )


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_workspace",
)
async def create_workspace(current_user: currentUser, workspace_data: WorkspaceCreate):
    existing_workspace = await Workspace.find_one(
        Workspace.name == workspace_data.name,
        Workspace.user_id == current_user.id,
        fetch_links=True,
    )
    if existing_workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="workspace already present"
        )
    new_workspace = Workspace(name=workspace_data.name, user_id=current_user.id)
    await new_workspace.create()
    return new_workspace


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_workspace",
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
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_workspace",
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
    if update.name is not None:
        existing_workspace = await Workspace.find_one(Workspace.name == update.name)
        if existing_workspace:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="workspace already present",
            )
    workspace_data = update.model_dump(exclude_none=True)
    workspace_data["updated_at"] = datetime.now(UTC)
    await workspace.update({"$set": workspace_data})
    return await Workspace.get(workspace_id)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_workspace",
)
async def delete_workspace(workspace_id: PydanticObjectId, current_user: currentUser):
    workspace = await Workspace.find_one(
        Workspace.id == workspace_id, Workspace.user_id == current_user.id
    )
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    await Item.find_all(Item.workspace_id == workspace.id).delete()
    await List.find_all(List.workspace_id == workspace.id).delete()
    await workspace.delete()


@router.get(
    "/{workspace_id}/export",
    response_model=ExportFile,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def export_workspace(workspace_id: PydanticObjectId):
    workspace = await Workspace.get(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    workspace_data = await Workspace.get_export_data(workspace_id)
    if not workspace_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="cannot export this workspace"
        )
    export_file = ExportFile(
        version="1.0",
        exported_at=datetime.now(UTC),
        workspace=workspace_data,
    )

    json_bytes = export_file.model_dump_json(indent=2).encode("utf-8")

    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{workspace_data.name}.json"'
        },
    )
