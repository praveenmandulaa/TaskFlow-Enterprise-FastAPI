
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse

from sqlalchemy import func
from app.schemas.team_member import TeamMemberAdd, TeamMemberResponse

# Adjust this import if your existing auth dependency uses
# a different module or function name.
from app.api.deps import get_current_user


router = APIRouter(prefix="/teams", tags=["Teams"])


def get_accessible_team(
    team_id: int,
    db: Session,
    current_user: User,
) -> Team:
    team = db.scalar(
        select(Team)
        .outerjoin(
            TeamMember,
            TeamMember.team_id == Team.id,
        )
        .where(
            Team.id == team_id,
            (Team.owner_id == current_user.id)
            | (TeamMember.user_id == current_user.id),
        )
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found",
        )

    return team


@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = Team(
        name=payload.name,
        description=payload.description,
        owner_id=current_user.id,
    )

    db.add(team)
    db.flush()

    db.add(
        TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role="owner",
        )
    )

    db.commit()
    db.refresh(team)

    return team


@router.get("", response_model=list[TeamResponse])
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Team)
        .outerjoin(
            TeamMember,
            TeamMember.team_id == Team.id,
        )
        .where(
            (Team.owner_id == current_user.id)
            | (TeamMember.user_id == current_user.id)
        )
        .distinct()
        .order_by(Team.id.desc())
    )

    return db.scalars(statement).all()


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_accessible_team(team_id, db, current_user)


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = get_accessible_team(team_id, db, current_user)

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the team owner can update this team",
        )

    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)

    return team


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = get_accessible_team(team_id, db, current_user)

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the team owner can delete this team",
        )

    db.delete(team)
    db.commit()

    
@router.get(
    "/{team_id}/members",
    response_model=list[TeamMemberResponse],
)
def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_team(team_id, db, current_user)

    return db.scalars(
        select(TeamMember)
        .where(TeamMember.team_id == team_id)
        .order_by(TeamMember.id)
    ).all()


@router.post(
    "/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_team_member(
    team_id: int,
    payload: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = get_accessible_team(team_id, db, current_user)

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the team owner can add members",
        )

    user = db.get(User, payload.user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=404,
            detail="Active user not found",
        )

    existing = db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == payload.user_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="User is already a team member",
        )

    member = TeamMember(
        team_id=team_id,
        user_id=payload.user_id,
        role="member",
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return member


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = get_accessible_team(team_id, db, current_user)

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the team owner can remove members",
        )

    if user_id == team.owner_id:
        raise HTTPException(
            status_code=400,
            detail="The team owner cannot be removed",
        )

    member = db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )

    if member is None:
        raise HTTPException(
            status_code=404,
            detail="Team member not found",
        )

    db.delete(member)
    db.commit()

