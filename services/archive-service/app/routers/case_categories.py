"""案例分类管理API"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.archive import CaseCategory

router = APIRouter(prefix="/api/v1/archive/case-categories", tags=["案例分类管理"])


class CaseCategoryCreateRequest(BaseModel):
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0


class CaseCategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CaseCategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    description: Optional[str]
    icon: Optional[str]
    sort_order: int
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=CaseCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_case_category(
    request: CaseCategoryCreateRequest,
    db: Session = Depends(get_db)
):
    """创建案例分类"""
    existing = db.query(CaseCategory).filter(
        CaseCategory.name == request.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类名称已存在")

    category = CaseCategory(
        name=request.name,
        parent_id=request.parent_id,
        description=request.description,
        icon=request.icon,
        sort_order=request.sort_order
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("")
async def list_case_categories(
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取案例分类列表"""
    query = db.query(CaseCategory)

    if parent_id is not None:
        query = query.filter(CaseCategory.parent_id == parent_id)
    if is_active is not None:
        query = query.filter(CaseCategory.is_active == is_active)

    categories = query.order_by(CaseCategory.sort_order).all()
    return {"categories": categories}


@router.get("/{category_id}", response_model=CaseCategoryResponse)
async def get_case_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """获取案例分类详情"""
    category = db.query(CaseCategory).filter(
        CaseCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category


@router.put("/{category_id}", response_model=CaseCategoryResponse)
async def update_case_category(
    category_id: int,
    request: CaseCategoryUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新案例分类"""
    category = db.query(CaseCategory).filter(
        CaseCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """删除案例分类"""
    category = db.query(CaseCategory).filter(
        CaseCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    category.is_active = False
    db.commit()
