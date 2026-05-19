from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

# Схемы для Пользователя
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Пароль от 6 символов")
    skill_level: int = Field(default=1, ge=1, le=5)

class UserOut(BaseModel):
    id: int
    email: EmailStr
    skill_level: int

    class Config:
        from_attributes = True

# Схемы для Токенов
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Схемы для Задач
class TaskBase(BaseModel):
    title: str = Field(..., min_length=2)
    description: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=3)
    estimated_hours: float = Field(default=1.0, gt=0)
    status: str = Field(default="Backlog")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    assigned_to_id: Optional[int] = None

class TaskOut(TaskBase):
    id: int
    project_id: int
    assigned_to_id: Optional[int] = None

    class Config:
        from_attributes = True

# Схемы для Проектов
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None

class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True