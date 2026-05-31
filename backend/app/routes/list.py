from fastapi import APIRouter, status, HTTPException, Query
from app.schemas import (
    ListCreate,
    ListResponse,
    ListDetailedResponse,
    ListItemCreate,
    ListUpdate,
    ListItemResponse,
    ListItemBase,
    ListItemUpdatePartial,
)
from app.models import TodoList
from beanie import PydanticObjectId
from typing import Annotated

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
async def fetch_todo_lists():
    return await TodoList.list_summaries()


@router.post("", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_todo_list(list_data: ListCreate):
    new_list = TodoList(name=list_data.name)
    await new_list.create()
    return new_list


@router.get(
    "/{list_id}", response_model=ListDetailedResponse, status_code=status.HTTP_200_OK
)
async def fetch_todo_list_details(list_id: PydanticObjectId):
    list_details = await TodoList.get(list_id)
    if not list_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    return list_details


@router.patch(
    "/{list_id}", response_model=ListResponse, status_code=status.HTTP_202_ACCEPTED
)
async def update_todo_list(list_id: PydanticObjectId, list_data: ListUpdate):
    list = await TodoList.get(list_id)
    if not list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="list not found"
        )
    if list_data.name != None:
        await list.update({"$set": {"title": list_data.name}})
    return await TodoList.get(list_id)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo_list(list_id: PydanticObjectId):
    list = await TodoList.get(list_id)
    if not list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    await list.delete()


@router.post(
    "/{list_id}/items",
    response_model=ListDetailedResponse,
    status_code=status.HTTP_200_OK,
)
async def create_list_item(list_id: PydanticObjectId, item_data: ListItemCreate):
    todolist = await TodoList.get(list_id)
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    await todolist.update({"$push": {"items": item_data.model_dump()}})
    return await TodoList.get(list_id)


@router.patch(
    "/{list_id}/items",
    response_model=ListDetailedResponse,
    status_code=status.HTTP_200_OK,
)
async def update_item_state(list_id: PydanticObjectId, update: ListItemUpdatePartial):
    todolist = await TodoList.get(list_id)
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    for item in todolist.items:
        if item.id == update.item_id:
            if update.checked != None:
                item.checked = update.checked
                await todolist.save()
                return await TodoList.get(list_id)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="item not found")


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(list_id: PydanticObjectId, item_id: str):
    item_deleted = False
    todolist = await TodoList.get(list_id)
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="todo list not found"
        )
    for item in todolist.items:
        if item.id == item_id:
            todolist.items.remove(item)
            item_deleted = True
            await todolist.save()
            break
    if not item_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )
