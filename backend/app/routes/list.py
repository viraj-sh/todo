from fastapi import APIRouter, status, HTTPException
from app.schemas.list import (
    ListCreate,
    ListResponse,
    ListDetailedResponse,
    ListUpdate,
)
from app.models import List, Workspace, Item
from beanie import PydanticObjectId
from app.auth import currentUser
from datetime import datetime, UTC

router = APIRouter()


@router.get(
    "/workspaces/{workspace_id}/lists",
    status_code=status.HTTP_200_OK,
    operation_id="list_todo_lists",
)
async def fetch_lists(workspace_id: PydanticObjectId, current_user: currentUser):
    workspace = await Workspace.find_one(
        Workspace.id == workspace_id, Workspace.user_id == current_user.id
    )
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    return await List.get_workspace_lists_summary(workspace_id)


@router.post(
    "/workspaces/{workspace_id}/lists",
    response_model=ListResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_todo_list",
)
async def create_lists(
    workspace_id: PydanticObjectId, list_data: ListCreate, current_user: currentUser
):
    workspace = await Workspace.find_one(
        Workspace.id == workspace_id, Workspace.user_id == current_user.id
    )
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    new_list = List(
        name=list_data.name, user_id=current_user.id, workspace_id=workspace_id
    )
    await new_list.create()
    return new_list


@router.get(
    "/workspaces/{workspace_id}/lists/{list_id}",
    response_model=ListDetailedResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_todo_list",
)
async def fetch_lists_details(
    workspace_id: PydanticObjectId, list_id: PydanticObjectId, current_user: currentUser
):
    list_details = await List.find_one(
        List.id == list_id,
        List.workspace_id == workspace_id,
        List.user_id == current_user.id,
    )
    if not list_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="list not found"
        )
    return list_details


@router.patch(
    "/workspaces/{workspace_id}/lists/{list_id}",
    response_model=ListResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_todo_list",
)
async def update_lists(
    workspace_id: PydanticObjectId,
    list_id: PydanticObjectId,
    list_data: ListUpdate,
    current_user: currentUser,
):
    list = await List.find_one(
        List.id == list_id,
        List.workspace_id == workspace_id,
        List.user_id == current_user.id,
    )
    if not list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="list not found"
        )
    if list_data.name is not None:
        await list.update(
            {"$set": {"name": list_data.name, "updated_at": datetime.now(UTC)}}
        )
    return await List.find_one(
        List.id == list_id,
        List.workspace_id == workspace_id,
        List.user_id == current_user.id,
    )


@router.delete(
    "/workspaces/{workspace_id}/lists/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_todo_list",
)
async def delete_lists(
    workspace_id: PydanticObjectId, list_id: PydanticObjectId, current_user: currentUser
):
    list = await List.find_one(
        List.id == list_id,
        List.workspace_id == workspace_id,
        List.user_id == current_user.id,
    )
    if not list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="list not found"
        )
    await Item.find_all(Item.list_id == list.id).delete()
    await list.delete()
