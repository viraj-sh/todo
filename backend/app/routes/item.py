from fastapi import APIRouter, status, HTTPException
from beanie import PydanticObjectId
from datetime import datetime, UTC

from app.models import Item, Tag, List

from app.auth import currentUser
from app.schemas.item import ItemResponse, ItemCreate, ItemUpdatePartial

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/lists/{list_id}/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_todo_item",
)
async def create_list_item(
    workspace_id: PydanticObjectId,
    list_id: PydanticObjectId,
    item_data: ItemCreate,
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
    for id in item_data.tag_ids:
        tag = await Tag.find_one(Tag.id == id, Tag.workspace_id == workspace_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="tag not found"
            )

    new_item = Item(
        label=item_data.label,
        priority=item_data.priority,
        description=item_data.description,
        deadline=item_data.deadline,
        user_id=current_user.id,
        workspace_id=workspace_id,
        list_id=list_id,
        tag_ids=item_data.tag_ids,
        parent_id=item_data.parent_id,
    )
    await new_item.create()
    if new_item.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="failed to created the item"
        )
    return await Item.get(new_item.id)


@router.patch(
    "/workspaces/{workspace_id}/lists/{list_id}/items/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_todo_item",
)
async def update_item_state(
    workspace_id: PydanticObjectId,
    list_id: PydanticObjectId,
    item_id: PydanticObjectId,
    update: ItemUpdatePartial,
    current_user: currentUser,
):
    item = await Item.find_one(
        Item.id == item_id,
        Item.list_id == list_id,
        Item.workspace_id == workspace_id,
        Item.user_id == current_user.id,
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )
    item_update = update.model_dump(exclude_none=True)
    item_update["updated_at"] = datetime.now(UTC)
    await item.update({"$set": item_update})
    return await Item.get(item.id)


@router.delete(
    "/workspaces/{workspace_id}/lists/{list_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_todo_item",
)
async def delete_item(
    workspace_id: PydanticObjectId,
    list_id: PydanticObjectId,
    item_id: PydanticObjectId,
    current_user: currentUser,
):
    item = await Item.find_one(
        Item.id == item_id,
        Item.list_id == list_id,
        Item.workspace_id == workspace_id,
        Item.user_id == current_user.id,
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )
    await item.delete()
