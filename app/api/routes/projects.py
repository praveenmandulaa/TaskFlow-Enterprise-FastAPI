from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectPage, ProjectStatus

router = APIRouter(prefix='/projects', tags=['Projects'])

def accessible_team_ids(user_id: int):
    return select(Team.id).where(or_(Team.owner_id == user_id, Team.id.in_(select(TeamMember.team_id).where(TeamMember.user_id == user_id))))

def get_project(db: Session, project_id: int, user_id: int) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.team_id.in_(accessible_team_ids(user_id))))
    if project is None:
        raise HTTPException(404, 'Project not found')
    return project

def owner_only(db: Session, team_id: int, user_id: int):
    if db.scalar(select(Team.id).where(Team.id == team_id, Team.owner_id == user_id)) is None:
        raise HTTPException(403, 'Only the team owner can manage projects')

@router.post('', response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    owner_only(db, payload.team_id, current_user.id)
    project = Project(**payload.model_dump(mode='json'), created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get('', response_model=ProjectPage)
def list_projects(team_id: int | None = Query(None, gt=0), project_status: ProjectStatus | None = Query(None, alias='status'), search: str | None = Query(None, max_length=150), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conditions = [Project.team_id.in_(accessible_team_ids(current_user.id))]
    if team_id is not None: conditions.append(Project.team_id == team_id)
    if project_status is not None: conditions.append(Project.status == project_status.value)
    if search: conditions.append(Project.name.ilike(f'%{search}%'))
    total = db.scalar(select(func.count(Project.id)).where(*conditions)) or 0
    items = db.scalars(select(Project).where(*conditions).order_by(Project.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size, 'pages': (total + page_size - 1) // page_size}

@router.get('/{project_id}', response_model=ProjectResponse)
def read_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_project(db, project_id, current_user.id)

@router.patch('/{project_id}', response_model=ProjectResponse)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project(db, project_id, current_user.id)
    owner_only(db, project.team_id, current_user.id)
    changes = payload.model_dump(exclude_unset=True, mode='json')
    for key in ('name', 'status'):
        if key in changes and changes[key] is None:
            raise HTTPException(422, f'{key} cannot be null')
    start = changes.get('start_date', project.start_date)
    due = changes.get('due_date', project.due_date)
    if start and due and str(due) < str(start):
        raise HTTPException(422, 'due_date must be on or after start_date')
    for key, value in changes.items(): setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project

@router.delete('/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project(db, project_id, current_user.id)
    owner_only(db, project.team_id, current_user.id)
    db.delete(project)
    db.commit()
