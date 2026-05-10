from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["Payment Orders Create"])


class CreateOrderRequest(BaseModel):
    order_type: str
    amount: float
    title: str
    description: str | None = None
    related_id: int | str | None = None
    related_type: str | None = None


async def create_order(data, current_user=None, db=None):
    raise NotImplementedError


@router.post("/orders")
async def create_order_endpoint():
    raise NotImplementedError
