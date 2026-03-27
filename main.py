from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session
from .auth import create_access_token, hash_password, verify_password
from .cache import get_top_tasks_cached, invalidate_task_cache
from .database import Base, engine
from .dependencies import get_current_user, get_db
from .models import Task, TaskStatus, User
from .schemas import (
    SortField,
    SortOrder,
    TaskCreate,
    TaskListResponse,
    TaskRead,
    TaskUpdate,
    Token,
    UserCreate,
    UserRead,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title='Task Manager',
    version='1.0',
    lifespan=lifespan,
)

SORT_FIELD_TO_COLUMN = {
    "title": Task.title,
    "status": Task.status,
    "created_at": Task.created_at,
    "priority": Task.priority,
}


@app.get('/')
def root():
    return {
        "message": 'Task Manager is running',
        "docs": '/docs',
    }


@app.post('/auth/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Username already exists')
    user = User(username=user_data.username, password_hash=hash_password(user_data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post('/auth/login', response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid username or password')

    access_token = create_access_token({'sub': str(user.id)})
    return Token(access_token=access_token)


@app.get('/users/me', response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post('/tasks', response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
        task_data: TaskCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    task = Task(**task_data.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    invalidate_task_cache()
    return task


@app.get('/tasks', response_model=TaskListResponse)
def list_tasks(
        sort_by: SortField = Query(default='created_at'),
        sort_order: SortOrder = Query(default='desc'),
        search: str | None = Query(default=None, description='Поиск по title и description'),
        status_filter: TaskStatus | None = Query(default=None, alias='status'),
        priority: int | None = Query(default=None, ge=1, le=5),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    query = db.query(Task).filter(Task.owner_id == current_user.id)
    if search:
        pattern = f'%{search}%'
        query = query.filter(or_(Task.title.ilike(pattern), Task.description.ilike(pattern)))
    if status_filter is not None:
        query = query.filter(Task.status == status_filter)
    if priority is not None:
        query = query.filter(Task.priority == priority)

    total = query.with_entities(func.count(Task.id)).scalar() or 0
    order_column = SORT_FIELD_TO_COLUMN[sort_by]
    ordering = desc(order_column) if sort_order == 'desc' else asc(order_column)
    items = query.order_by(ordering, desc(Task.id)).offset(skip).limit(limit).all()
    return TaskListResponse(total=total, items=items)


@app.get('/tasks/top', response_model=list[TaskRead])
def get_top_tasks(
        limit: int = Query(default=5, ge=1, le=50),
        current_user: User = Depends(get_current_user),
):
    return get_top_tasks_cached(current_user.id, limit)


@app.get('/tasks/{task_id}', response_model=TaskRead)
def get_task(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    return task


@app.patch('/tasks/{task_id}', response_model=TaskRead)
def update_task(
        task_id: int,
        task_data: TaskUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    invalidate_task_cache()
    return task


@app.delete('/tasks/{task_id}')
def delete_task(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')

    db.delete(task)
    db.commit()
    invalidate_task_cache()
    return {"message": 'Task deleted successfully'}
