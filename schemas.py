from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .models import TaskStatus


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=5000)
    status: TaskStatus = TaskStatus.pending
    priority: int = Field(default=3, ge=1, le=5)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    owner_id: int
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    total: int
    items: list[TaskRead]


SortField = Literal['title', 'status', 'created_at', 'priority']
SortOrder = Literal['asc', 'desc']
