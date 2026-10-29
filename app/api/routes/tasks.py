from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskPage, TaskStatus, TaskPriority
from app.api.routes.projects import accessible_team_ids, get_project

router = APIRouter(prefix='/tasks', tags=['Tasks'])

def get_task(db: Session, task_id: int, user_id: int) -> Task:
    task = db.scalar(select(Task).join(Project, Task.project_id == Project.id).where(Task.id == task_id, Project.team_id.in_(accessible_team_ids(user_id))))
    if task is None: raise HTTPException(404, 'Task not found')
    return task

def require_member(db: Session, team_id: int, user_id: int):
    member = db.scalar(select(TeamMember.id).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))
    owner = db.scalar(select(Team.id).where(Team.id == team_id, Team.owner_id == user_id))
    if member is None and owner is None: raise HTTPException(403, 'User must belong to the project team')

def validate_assignee(db: Session, team_id: int, assignee_id: int | None):
    if assignee_id is None: return
    user = db.get(User, assignee_id)
    if user is None or not user.is_active: raise HTTPException(422, 'Assignee must be an active user')
    require_member(db, team_id, assignee_id)

def can_edit(db: Session, task: Task, user_id: int):
    project = db.get(Project, task.project_id)
    team = db.get(Team, project.team_id)
    if user_id not in (team.owner_id, task.created_by, task.assignee_id):
        raise HTTPException(403, 'Only owner, creator, or assignee can modify tasks')

@router.post('', response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project(db, payload.project_id, current_user.id)
    require_member(db, project.team_id, current_user.id)
    validate_assignee(db, project.team_id, payload.assignee_id)
    task = Task(**payload.model_dump(mode='json'), created_by=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get('', response_model=TaskPage)
def list_tasks(project_id: int | None = Query(None, gt=0), team_id: int | None = Query(None, gt=0), task_status: TaskStatus | None = Query(None, alias='status'), priority: TaskPriority | None = None, assignee_id: int | None = Query(None, gt=0), search: str | None = Query(None, max_length=200), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conditions = [Project.team_id.in_(accessible_team_ids(current_user.id))]
    if project_id is not None: conditions.append(Task.project_id == project_id)
    if team_id is not None: conditions.append(Project.team_id == team_id)
    if task_status is not None: conditions.append(Task.status == task_status.value)
    if priority is not None: conditions.append(Task.priority == priority.value)
    if assignee_id is not None: conditions.append(Task.assignee_id == assignee_id)
    if search: conditions.append(Task.title.ilike(f'%{search}%'))
    stmt = select(Task).join(Project, Task.project_id == Project.id).where(*conditions)
    total = db.scalar(select(func.count(Task.id)).join(Project, Task.project_id == Project.id).where(*conditions)) or 0
    items = db.scalars(stmt.order_by(Task.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size, 'pages': (total + page_size - 1) // page_size}

@router.get('/{task_id}', response_model=TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_task(db, task_id, current_user.id)

@router.patch('/{task_id}', response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = get_task(db, task_id, current_user.id)
    can_edit(db, task, current_user.id)
    changes = payload.model_dump(exclude_unset=True, mode='json')
    for key in ('title', 'status', 'priority'):
        if key in changes and changes[key] is None: raise HTTPException(422, f'{key} cannot be null')
    if 'assignee_id' in changes:
        project = db.get(Project, task.project_id)
        validate_assignee(db, project.team_id, changes['assignee_id'])
    for key, value in changes.items(): setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task

@router.delete('/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = get_task(db, task_id, current_user.id)
    project = db.get(Project, task.project_id)
    team = db.get(Team, project.team_id)
    if current_user.id not in (team.owner_id, task.created_by): raise HTTPException(403, 'Only owner or creator can delete tasks')
    db.delete(task)
    db.commit()
