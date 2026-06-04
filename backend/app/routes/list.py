from fastapi import APIRouter, status, HTTPException
from app.schemas.list import (
    ListCreate,
    ListResponse,
    ListDetailedResponse,
    ItemCreate,
    ListUpdate,
    ItemUpdatePartial,
)
from app.models import List, Workspace
from beanie import PydanticObjectId
from app.utils import normalize_tags
from app.auth import currentUser
from datetime import datetime, UTC
import uuid

router = APIRouter()


@router.get("/workspaces/{workspace_id}/lists", status_code=status.HTTP_200_OK)
async def fetch_lists(workspace_id: PydanticObjectId, current_user: currentUser):
    workspace = await Workspace.find_one(
        Workspace.id == workspace_id, Workspace.user_id == current_user.id
    ).sort("+created_at")
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    return await List.list_summaries(workspace_id)


@router.post(
    "/workspaces/{workspace_id}/lists",
    response_model=ListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lists(
    workspace_id: PydanticObjectId, list_data: ListCreate, current_user: currentUser
):
    workspace = await Workspace.find_one(Workspace.id == workspace_id)
    if not workspace or not workspace.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    new_list = List(name=list_data.name, workspace_id=workspace_id)
    await new_list.create()
    return new_list


@router.get(
    "/workspaces/{workspace_id}/lists/{list_id}",
    response_model=ListDetailedResponse,
    status_code=status.HTTP_200_OK,
)
async def fetch_lists_details(
    workspace_id: PydanticObjectId, list_id: PydanticObjectId, current_user: currentUser
):
    workspace = await Workspace.find_one(Workspace.id == workspace_id)
    if not workspace or not workspace.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    list_details = await List.find_one(
        List.workspace_id == workspace_id, List.id == list_id
    )
    if not list_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    return list_details


@router.patch(
    "/workspaces/{workspace_id}/lists/{list_id}",
    response_model=ListResponse,
    status_code=status.HTTP_200_OK,
)
async def update_lists(
    workspace_id: PydanticObjectId,
    list_id: PydanticObjectId,
    list_data: ListUpdate,
    current_user: currentUser,
):
    workspace = await Workspace.find_one(Workspace.id == workspace_id)
    if not workspace or not workspace.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    list = await List.find_one(List.workspace_id == workspace_id, List.id == list_id)
    if not list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="list not found"
        )
    if list_data.name is not None:
        await list.update({"$set": {"name": list_data.name}})
    await list.update({"$set": {"updated_at": datetime.now(UTC)}})
    return await List.find_one(List.workspace_id == workspace_id, List.id == list_id)


@router.delete(
    "/workspaces/{workspace_id}/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_lists(
    workspace_id: PydanticObjectId, list_id: PydanticObjectId, current_user: currentUser
):
    workspace = await Workspace.find_one(Workspace.id == workspace_id)
    if not workspace or not workspace.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    list = await List.find_one(List.workspace_id == workspace_id, List.id == list_id)
    if not list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    await list.delete()


@router.post(
    "/workspaces/{workspace_id}/lists/{list_id}/items",
    response_model=ListDetailedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_list_item(
    workspace_id: PydanticObjectId,
    list_id: PydanticObjectId,
    item_data: ItemCreate,
    current_user: currentUser,
):
    workspace = await Workspace.find_one(Workspace.id == workspace_id)
    if not workspace or not workspace.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    todolist = await List.find_one(
        List.workspace_id == workspace_id, List.id == list_id
    )
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    item_dict = item_data.model_dump()
    item_dict["item_id"] = uuid.uuid4().hex
    if "tags" in item_dict:
        item_dict["tags"] = normalize_tags(item_dict["tags"])
    else:
        item_dict["tags"] = []
    item_dict["created_at"] = datetime.now(UTC)
    item_dict["updated_at"] = datetime.now(UTC)
    await todolist.update(
        {"$push": {"items": item_dict}, "$set": {"updated_at": datetime.now(UTC)}}
    )
    return await List.find_one(List.workspace_id == workspace_id, List.id == list_id)


@router.patch(
    "/workspaces/{workspace_id}/lists/{list_id}/items",
    response_model=ListDetailedResponse,
    status_code=status.HTTP_200_OK,
)
async def update_item_state(
    workspace_id: PydanticObjectId,
    list_id: PydanticObjectId,
    update: ItemUpdatePartial,
    current_user: currentUser,
):
    workspace = await Workspace.find_one(Workspace.id == workspace_id)
    if not workspace or not workspace.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    todolist = await List.find_one(
        List.workspace_id == workspace_id, List.id == list_id
    )
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    for item in todolist.items:
        if item.item_id == update.item_id:
            if update.checked is not None:
                item.checked = update.checked
                # await todolist.save()
            if update.label is not None:
                item.label = update.label
                # await todolist.save()
            if update.priority is not None:
                item.priority = update.priority
                # await todolist.save()
            if update.description is not None:
                item.description = update.description
            if update.tags is not None:
                item.tags = update.tags
                # await todolist.save()
            item.updated_at = datetime.now(UTC)
            await todolist.save()
            await todolist.update({"$set": {"updated_at": datetime.now(UTC)}})
            return await List.find_one(
                List.workspace_id == workspace_id, List.id == list_id
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="item not found")


@router.delete(
    "/workspaces/{workspace_id}/lists/{list_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_item(
    workspace_id: PydanticObjectId,
    list_id: PydanticObjectId,
    item_id: str,
    current_user: currentUser,
):
    workspace = await Workspace.find_one(Workspace.id == workspace_id)
    if not workspace or not workspace.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found"
        )
    item_deleted = False
    todolist = await List.find_one(
        List.workspace_id == workspace_id, List.id == list_id
    )
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    for item in todolist.items:
        if item.item_id == item_id:
            todolist.items.remove(item)
            item_deleted = True
            await todolist.save()
            await todolist.update({"$set": {"updated_at": datetime.now(UTC)}})
            break
    if not item_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )
