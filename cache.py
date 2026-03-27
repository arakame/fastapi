from functools import lru_cache
from .database import SessionLocal
from .models import Task
from .schemas import TaskRead


@lru_cache(maxsize=256)
def get_top_tasks_cached(user_id: int, limit: int):
    db = SessionLocal()
    try:
        tasks = (
            db.query(Task)
            .filter(Task.owner_id == user_id)
            .order_by(Task.priority.desc(), Task.created_at.desc())
            .limit(limit)
            .all()
        )
        return [TaskRead.model_validate(task).model_dump(mode='json') for task in tasks]
    finally:
        db.close()


def invalidate_task_cache():
    get_top_tasks_cached.cache_clear()
