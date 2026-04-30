# Deployment Guide — Railway

This guide walks you through deploying the Team Task Manager to **Railway** end-to-end. You should be able to do it in 10–15 minutes. No paid plan required for a basic deploy.

---

## 0. Prerequisites

- A **GitHub** account
- A **Railway** account → sign up at <https://railway.com> (you can use “Login with GitHub”)
- Git installed locally (`git --version` to check)

---

## 1. Push the project to GitHub

If your project is already in a Git repo and on GitHub, skip to step 2.

```bash
cd /path/to/myproject

git init
git add .
git commit -m "Initial commit: Team Task Manager"

# Create an empty repo on GitHub first (e.g. team-task-manager). Then:
git branch -M main
git remote add origin https://github.com/<your-username>/team-task-manager.git
git push -u origin main
```

Make sure `.env` is **not** committed (it's already in `.gitignore`).

---

## 2. Create a new Railway project from the repo

1. Go to <https://railway.com/dashboard> and click **New Project**.
2. Choose **Deploy from GitHub repo**.
3. Authorize Railway to access your GitHub account if asked.
4. Pick the repo you just pushed (`team-task-manager`).

Railway will start an initial build. It will fail or run with SQLite — that's fine, we're about to add Postgres.

---

## 3. Add a PostgreSQL database

1. Inside the project, click **+ New** (top right) → **Database** → **Add PostgreSQL**.
2. Wait ~30 seconds for it to provision.
3. Open the Postgres service → **Variables** tab → you'll see `DATABASE_URL`, `PGHOST`, etc. You don't need to copy anything; we'll reference it from the app.

---

## 4. Wire `DATABASE_URL` into the web service

1. Open your **app service** (not the Postgres one) → **Variables** tab.
2. Click **+ New Variable** → **Add Reference**.
3. Pick the Postgres service and select `DATABASE_URL`.
   - Railway will save it as `DATABASE_URL` on the app service, with the value `${{Postgres.DATABASE_URL}}`. That's exactly what we want — `config.py` reads `os.environ["DATABASE_URL"]`.
4. While you're on the Variables tab, also add:
   - **`SECRET_KEY`** — a long random string. Generate one with:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```

The app code (`config.py`) automatically rewrites `postgres://` to `postgresql://` so SQLAlchemy 2.x is happy.

---

## 5. Confirm the start command

Railway auto-detects Python apps from `requirements.txt` and uses the **`Procfile`** for the start command. The Procfile in this repo is:

```
web: gunicorn wsgi:app
release: python -c "from app import create_app, db; app=create_app(); ctx=app.app_context(); ctx.push(); db.create_all(); ctx.pop(); print('DB ready')"
```

- `web` — the actual server process Railway runs.
- `release` — runs once per deploy, before the web process starts. It creates the DB tables on first deploy. (The app also calls `db.create_all()` at boot, so this is a belt-and-braces.)

You shouldn't have to touch anything in the Settings → Deploy section, but if Railway asks for a Start Command, set it to:

```
gunicorn wsgi:app
```

---

## 6. Generate a public URL

1. Open the app service → **Settings** → **Networking** → **Generate Domain**.
2. Railway gives you a URL like `team-task-manager-production.up.railway.app`.
3. Wait for the next deploy to finish (top right shows status). Click the URL.

You should land on the login page. Click **Create an account** — the first user you sign up becomes the **admin** automatically.

---

## 7. Smoke test (do this before submitting)

Once live, click through:

- [ ] Sign up as admin (your first account)
- [ ] Sign up a second user as a member (use a different browser / incognito)
- [ ] As admin: create a project, then add the member by username
- [ ] As admin: create a task, assign it to the member, give it a due date in the past
- [ ] As member: log in → confirm the task shows up in **My Tasks**
- [ ] As member: change the status from To Do → In Progress
- [ ] Confirm the dashboard counters and the **Overdue** card update correctly

If any step fails, check **Deployments → View Logs** in Railway.

---

## 8. Common issues & fixes

**“Application failed to respond” on first load**
The first request after a fresh deploy can be slow because Railway boots the container on demand. Refresh after 10s.

**`sqlalchemy.exc.OperationalError: could not connect to server`**
The `DATABASE_URL` variable isn't set, or you set it as a literal value instead of a reference. Go to Variables → make sure it shows `${{Postgres.DATABASE_URL}}`.

**`ModuleNotFoundError: No module named 'psycopg2'`**
Your `requirements.txt` is missing `psycopg2-binary`. The one in this repo includes it.

**`KeyError: 'SECRET_KEY'` or sessions don't persist**
Set the `SECRET_KEY` env var (step 4).

**Tables don't exist on first request**
The `release` command in the Procfile should have created them. Check the deploy logs for the line `DB ready`. If you don't see it, run `db.create_all()` manually via the Railway shell:

```
railway shell      # or use the in-browser shell
python -c "from app import create_app, db; a=create_app(); a.app_context().push(); db.create_all()"
```

---

## 9. Re-deploying after changes

```bash
git add .
git commit -m "Whatever you changed"
git push
```

Railway auto-deploys every push to `main`. Watch progress in the **Deployments** tab.

---

## 10. Submission checklist

Before sending the link to your placement cell:

- [ ] App opens at the Railway URL
- [ ] Signup → Login → Logout all work
- [ ] You can create a project and assign a task
- [ ] Status changes persist after refresh
- [ ] Overdue tasks show up in red on the dashboard
- [ ] README.md links to the live URL
- [ ] Repo is public (or you've shared access with the evaluator)

That's it. Good luck. 🚀
