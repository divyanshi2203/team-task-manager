# Team Task Manager

A minimal full-stack web app where users create projects, build small teams, assign tasks, and track progress — with role-based access (**Admin** / **Member**). Built as a placement assignment.

**Live:** _add your Railway URL after deploying_

---

## Features

- **Authentication** — signup, login, logout, password hashing
- **Roles** — `admin` (can create projects, manage members) and `member` (can work in projects they are added to). The first user to sign up is automatically promoted to admin.
- **Projects & Teams** — admins create projects, add/remove members by username
- **Tasks** — title, description, status (`To Do` / `In Progress` / `Done`), assignee, due date
- **Dashboard** — counts of your tasks by status, list of overdue tasks, recent projects
- **Kanban-style project view** — three columns by status, quick status change inline
- **REST API** — JSON endpoints under `/api/` (uses the same session login)

---

## Tech stack

| Layer    | Choice                                |
|----------|---------------------------------------|
| Backend  | Python 3.11 + Flask 3                 |
| ORM      | SQLAlchemy (Flask-SQLAlchemy)         |
| Auth     | Flask-Login + Werkzeug password hash  |
| Forms    | Flask-WTF + WTForms (CSRF, validation)|
| DB       | PostgreSQL on Railway, SQLite locally |
| Frontend | Jinja2 templates + Bootstrap 5        |
| Server   | Gunicorn                              |
| Hosting  | Railway                               |

A single Flask app serves both the HTML pages and the JSON API → one Railway service, no separate frontend deploy needed.

---

## Project layout

```
.
├── app/
│   ├── __init__.py        # Flask app factory, blueprints, db init
│   ├── models.py          # User, Project, Membership, Task
│   ├── forms.py           # WTForms (validation lives here)
│   ├── decorators.py      # @admin_required, @project_access_required
│   ├── auth.py            # signup / login / logout
│   ├── main.py            # landing + dashboard
│   ├── projects.py        # project + membership routes
│   ├── tasks.py           # task routes
│   └── api.py             # JSON REST API
├── templates/
│   ├── base.html
│   ├── auth/{login,signup}.html
│   ├── dashboard.html
│   ├── projects/{list,new,detail}.html
│   └── tasks/form.html
├── static/style.css
├── config.py              # reads SECRET_KEY, DATABASE_URL
├── wsgi.py                # gunicorn entrypoint (`wsgi:app`)
├── requirements.txt
├── Procfile               # web + release commands for Railway
├── runtime.txt            # python-3.11.9
├── .env.example
├── README.md              # this file
└── DEPLOYMENT.md          # step-by-step Railway guide
```

---

## Run locally

You need Python 3.11+.

```bash
# 1. clone and enter the project
cd myproject

# 2. create a virtualenv (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. install deps
pip install -r requirements.txt

# 4. configure env
cp .env.example .env        # edit SECRET_KEY if you like

# 5. run
python wsgi.py
# → http://127.0.0.1:5000
```

The first time you run it, an `app.db` SQLite file is created automatically. The first user you sign up becomes admin.

---

## Roles & access rules

| Action                        | Admin | Project Owner | Member |
|-------------------------------|:-----:|:-------------:|:------:|
| Create a project              | ✅    | —             | ❌     |
| See all projects              | ✅    | (own only)    | (member of) |
| Add / remove project members  | ✅    | ✅            | ❌     |
| Delete a project              | ✅    | ✅            | ❌     |
| Create a task in a project    | ✅    | ✅            | ✅ (if member) |
| Edit / change task status     | ✅    | ✅            | ✅ (if member) |
| Delete a task                 | ✅    | ✅            | ✅ (if creator) |

Project owner = the admin who created the project. Admins can also manage any project.

---

## REST API

All endpoints expect a logged-in session (cookie-based). Easiest way to test: log in via the browser, then call the API from the same browser, or with `curl --cookie cookies.txt`.

| Method | Path                                  | Description                       |
|--------|---------------------------------------|-----------------------------------|
| GET    | `/api/me`                             | Current user                      |
| GET    | `/api/projects`                       | Projects you can see              |
| POST   | `/api/projects`                       | Create project (admin only)       |
| GET    | `/api/projects/<id>/tasks`            | List tasks in a project           |
| POST   | `/api/projects/<id>/tasks`            | Create a task in that project     |
| PATCH  | `/api/tasks/<id>`                     | Update task fields                |
| DELETE | `/api/tasks/<id>`                     | Delete a task                     |

Example body for creating a task:

```json
{
  "title": "Write the README",
  "description": "Cover features, setup, deploy",
  "status": "in_progress",
  "assignee_id": 2
}
```

Status values: `todo`, `in_progress`, `done`.

---

## Deployment

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for the full step-by-step Railway walkthrough.

Short version: push to GitHub → New Project on Railway → add PostgreSQL → set `SECRET_KEY` → deploy.

---

## License

MIT — do whatever you want, no warranty.
