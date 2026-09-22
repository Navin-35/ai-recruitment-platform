from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Skill
from app.schemas import SkillCreate, SkillResponse, SkillUpdate

router = APIRouter(
    prefix="/skills",
    tags=["Skills"],
)


@router.post(
    "/",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
):
    normalized_name = skill_data.name.strip()
    existing = (
        db.query(Skill)
        .filter(Skill.name.ilike(normalized_name))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill '{normalized_name}' already exists.",
        )

    skill = Skill(
        name=normalized_name,
        category=skill_data.category.strip() if skill_data.category else None,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get(
    "/",
    response_model=list[SkillResponse],
)
def get_skills(
    category: str | None = Query(default=None, description="Filter by skill category"),
    search: str | None = Query(default=None, description="Search skill name"),
    db: Session = Depends(get_db),
):
    query = db.query(Skill)
    if category:
        query = query.filter(Skill.category.ilike(category))
    if search:
        query = query.filter(Skill.name.ilike(f"%{search}%"))
    return query.order_by(Skill.name.asc()).all()


@router.get(
    "/{skill_id}",
    response_model=SkillResponse,
)
def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )
    return skill


@router.put(
    "/{skill_id}",
    response_model=SkillResponse,
)
def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    db: Session = Depends(get_db),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )

    update_data = skill_data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"]:
        normalized = update_data["name"].strip()
        existing = (
            db.query(Skill)
            .filter(Skill.name.ilike(normalized), Skill.id != skill_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Skill '{normalized}' already exists.",
            )
        update_data["name"] = normalized

    for field, value in update_data.items():
        setattr(skill, field, value)

    db.commit()
    db.refresh(skill)
    return skill


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )
    db.delete(skill)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
