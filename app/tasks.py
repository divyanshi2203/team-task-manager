"""Task routes (server-rendered forms)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.decorators import project_access_required
from app.forms import TaskForm
from app.models import Project, Task

tasks_bp = Blueprint("tasks", __name__)


def _populate_form_choices(form: TaskForm, project: Project) -> None:
    """Fill the assignee + status dropdowns from this project's data."""
    project.ensure_statuses()
    members = project.members()
    form.assignee_id.choices = [(0, "— Unassigned —")] + [
        (u.id, u.username) for u in members
    ]
    form.status.choices = [(s.key, s.label) for s in project.statuses]


@tasks_bp.route("/project/<int:project_id>/new", methods=["GET", "POST"])
@login_required
@project_access_required
def new_task(project_id, project):
    # Members can create tasks within projects they belong to.
    form = TaskForm()
    _populate_form_choices(form, project)

    if form.validate_on_submit():
        assignee_id = form.assignee_id.data or None
        task = Task(
            title=form.title.data.strip(),
            description=(form.description.data or "").strip(),
            status=form.status.data,
            due_date=form.due_date.data,
            project_id=project.id,
            assignee_id=assignee_id if assignee_id else None,
            created_by_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        flash("Task created.", "success")
        return redirect(url_for("projects.detail", project_id=project.id))

    return render_template("tasks/form.html", form=form, project=project, mode="new")


@tasks_bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    if not project.has_access(current_user):
        abort(403)

    form = TaskForm(obj=task)
    _populate_form_choices(form, project)
    if request.method == "GET":
        form.assignee_id.data = task.assignee_id or 0

    if form.validate_on_submit():
        task.title = form.title.data.strip()
        task.description = (form.description.data or "").strip()
        task.status = form.status.data
        task.due_date = form.due_date.data
        assignee_id = form.assignee_id.data or None
        task.assignee_id = assignee_id if assignee_id else None
        db.session.commit()
        flash("Task updated.", "success")
        return redirect(url_for("projects.detail", project_id=project.id))

    return render_template(
        "tasks/form.html", form=form, project=project, mode="edit", task=task
    )


@tasks_bp.route("/<int:task_id>/status", methods=["POST"])
@login_required
def quick_status(task_id):
    """Quick status flip from the dashboard / project page."""
    task = Task.query.get_or_404(task_id)
    if not task.project.has_access(current_user):
        abort(403)

    new_status = request.form.get("status", "").strip()
    task.project.ensure_statuses()
    if new_status not in task.project.status_keys():
        flash("Invalid status.", "danger")
        return redirect(request.referrer or url_for("main.dashboard"))

    task.status = new_status
    db.session.commit()
    flash(f"Task moved to {task.status_label}.", "success")
    return redirect(request.referrer or url_for("main.dashboard"))


@tasks_bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    # Only project managers (owner / admin) or the task creator may delete.
    if not (project.can_manage(current_user) or task.created_by_id == current_user.id):
        abort(403)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("projects.detail", project_id=project.id))
