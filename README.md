# Team Task Manager

Placement assignment. A small full stack web app where users can create projects, build small teams, assign tasks and track progress. Two roles: admin and member.

Live URL: add your railway url here once you deploy

Repo: add your github link here


## What the app does

Basically a small task tracker. You sign up, you log in, and based on your role you either create projects (admin) or work on tasks inside projects you were added to (member).

Each project has a kanban style board. By default the board has three columns: To Do, In Progress, Done. Admins can add their own columns too if a project needs something like Review or Blocked.

There is also a dashboard that shows how many tasks you have, how they are split across statuses, and a list of anything that is overdue.

Three main pieces:

- auth (signup, login, logout)
- projects with members
- tasks with title, description, status, assignee and due date


## How it works

1. First user to sign up becomes admin automatically. This is just so you can bootstrap the app without seed scripts.
2. Admin creates a project. The project gets the three default board columns.
3. Admin opens the project and adds members by username.
4. Anyone with access to the project can create tasks inside it.
5. Tasks can be assigned to any member of the project and given a due date.
6. Status can be changed from the small dropdown on each task card. The board updates live.
7. Members only ever see projects they were added to. Admins see everything.
8. If a task is past its due date and not done, it shows up in the Overdue list on the dashboard.


## Tech stack

- Python 3.11
- Flask 3
- Flask-SQLAlchemy for the ORM
- Flask-Login for sessions
- Flask-WTF for forms and CSRF
- PostgreSQL on Railway, SQLite when running locally
- Jinja2 templates with Bootstrap 5 for the UI
- Gunicorn as the production server

I did not use React. The whole thing renders server side so it can ship as one Railway service. Less moving parts, faster to deploy, easier to grade.


## Project structure

```
app/
  __init__.py       flask app factory, blueprints, csrf, db init
  models.py         user, project, membership, projectstatus, task
  forms.py          wtforms classes (validation lives here)
  decorators.py     admin_required, project_access_required
  auth.py           signup, login, logout
  main.py           landing page and dashboard
  projects.py       project crud, members, kanban columns
  tasks.py          task crud, status changes
  api.py            json rest api
templates/
  base.html
  auth/             login.html, signup.html
  projects/         list.html, new.html, detail.html
  tasks/            form.html
  dashboard.html
static/
  style.css
config.py           reads SECRET_KEY and DATABASE_URL
wsgi.py             gunicorn entry point (wsgi:app)
requirements.txt
Procfile            web + release commands for railway
runtime.txt         python version pin
.env.example        copy this to .env for local dev
README.md
DEPLOYMENT.md       step by step railway guide
walkthrough.txt     short usage walkthrough
```


## Running locally

You need Python 3.11.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python wsgi.py
```

Then open http://127.0.0.1:5000

A `app.db` sqlite file gets created on first run. The first account you sign up becomes admin.


## Roles

Admin can:

- create new projects
- add and remove members in any project
- delete a project
- add or remove custom kanban columns
- everything a member can do

Member can:

- see only projects they belong to
- create tasks inside those projects
- edit any task in their projects
- change task status
- delete tasks they created themselves

Members cannot create projects, cannot add or remove other members, and cannot delete a project.


## REST API

There is a small json api under `/api/`. It uses the same session cookie that the web ui uses, so the easiest way to call it is to log in through the browser first and then call the endpoints from the same browser or with `curl --cookie`.

- `GET /api/me`  current user
- `GET /api/projects`  projects you can see
- `POST /api/projects`  create a project (admin only)
- `GET /api/projects/<id>/tasks`  list tasks in a project
- `POST /api/projects/<id>/tasks`  create a task in that project
- `PATCH /api/tasks/<id>`  update task fields
- `DELETE /api/tasks/<id>`  delete a task

Example body for creating a task:

```
{
  "title": "fix the login button",
  "description": "broken on mobile",
  "status": "in_progress",
  "assignee_id": 2
}
```

Status values are the keys of the project's columns. The three defaults are `todo`, `in_progress` and `done`. If an admin added a custom column, its key becomes a slug of the label (for example `Review` becomes `review`).

## Notes

- The first signup becoming admin is intentional. Otherwise nobody could create anything on a fresh database.
- All forms have csrf protection.
- Passwords are hashed with werkzeug.
- The api blueprint is exempted from csrf because it expects token-less json calls from the same session.
- Default kanban columns cannot be deleted. Custom ones can only be deleted when no task is using them.
