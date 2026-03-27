## registration
POST /auth/register

пример json
{
  "username": "student",
  "password": "12345"
}

## login
POST /auth/login


Ответ в консоли:
{
  "access_token": "...",
  "token_type": "bearer"
}
Потом authorize и вставить токен

## пользователь
GET /users/me


## создать задачу
POST /tasks

{
  "title": "Подготовить отчет",
  "description": "Сдать отчет по Python",
  "status": "pending",
  "priority": 5
}

## список задач
GET /tasks

параметры задачи:
- sort_by=title|status|created_at|priority
- sort_order=asc|desc
- search=текст
- status=pending|in_progress|completed
- priority=1...5
- skip=0
- limit=20

## Получить задачу по ID
GET /tasks/{task_id}

## Обновить задачу
PATCH /tasks/{task_id}

## Удалить задачу
DELETE /tasks/{task_id}

## Топ-N приоритетных задач
GET /tasks/top?limit=3

