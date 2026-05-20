from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(tags=["Tasks"])

@router.post("/projects/{project_id}/tasks/", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(project_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Проект не найден")
    new_task = models.Task(**task.model_dump(), project_id=project_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/projects/{project_id}/tasks/", response_model=List[schemas.TaskOut])
def list_tasks(project_id: int, status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Task).filter(models.Task.project_id == project_id)
    if status_filter:
        query = query.filter(models.Task.status == status_filter)
    return query.all()

@router.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, task_data: schemas.TaskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    for key, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    db.delete(task)
    db.commit()
    return None

@router.post("/projects/{project_id}/optimize-assignments", status_code=status.HTTP_200_OK)
def optimize_assignments(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    unassigned_tasks = db.query(models.Task).filter(
        models.Task.project_id == project_id,
        models.Task.assigned_to_id == None
    ).order_by(models.Task.priority.desc()).all() # Сначала сложные задачи

    if not unassigned_tasks:
        return {"message": "Нет нераспределенных задач в этом проекте"}

    users = db.query(models.User).all()
    if not users:
        raise HTTPException(status_code=400, detail="В системе нет пользователей для распределения")

    # Считаем текущую нагрузку каждого пользователя (сумма часов по незавершенным задачам)
    user_workload = {}
    for u in users:
        active_hours = sum(t.estimated_hours for t in u.tasks if t.status != "Done")
        user_workload[u.id] = active_hours

    assigned_count = 0

    # Распределение задач по стратегии балансировки
    for task in unassigned_tasks:
        best_user_id = None
        min_load = float('inf')

        for u in users:
            # Условие: квалификация пользователя должна подходить под приоритет задачи
            if u.skill_level >= task.priority:
                if user_workload[u.id] < min_load:
                    min_load = user_workload[u.id]
                    best_user_id = u.id

        # Если не нашли идеального по квалификации
        if best_user_id is None:
            best_user_id = min(user_workload, key=user_workload.get)

        task.assigned_to_id = best_user_id
        user_workload[best_user_id] += task.estimated_hours
        assigned_count += 1

    db.commit()
    return {"message": f"Успешно оптимизировано. Распределено задач: {assigned_count}"}
