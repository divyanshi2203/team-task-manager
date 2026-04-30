"""Landing + dashboard routes."""
from datetime import date

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models import Project, Task

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Visible projects depend on role
    if current_user.is_admin:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        tasks_query = Task.query
    else:
        projects = current_user.projects()
        project_ids = [p.id for p in projects]
        tasks_query = Task.query.filter(Task.project_id.in_(project_ids or [0]))

    all_tasks = tasks_query.all()
    my_tasks = [t for t in all_tasks if t.assignee_id == current_user.id]

    stats = {
        "projects": len(projects),
        "my_tasks": len(my_tasks),
        "todo": sum(1 for t in my_tasks if t.status == "todo"),
        "in_progress": sum(1 for t in my_tasks if t.status == "in_progress"),
        "done": sum(1 for t in my_tasks if t.status == "done"),
        "overdue": sum(1 for t in my_tasks if t.is_overdue),
    }

    overdue_tasks = sorted(
        [t for t in all_tasks if t.is_overdue],
        key=lambda t: t.due_date or date.max,
    )

    return render_template(
        "dashboard.html",
        stats=stats,
        my_tasks=sorted(my_tasks, key=lambda t: (t.status == "done", t.due_date or date.max)),
        overdue_tasks=overdue_tasks,
        recent_projects=projects[:5],
    )
