"""Project + team-membership routes."""
import re

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.decorators import (
    admin_required,
    project_access_required,
    project_manage_required,
)
from app.forms import AddMemberForm, ProjectForm
from app.models import Membership, Project, ProjectStatus, User

ALLOWED_STATUS_COLORS = {
    "primary", "secondary", "success", "danger", "warning", "info", "dark",
}

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/")
@login_required
def list_projects():
    if current_user.is_admin:
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        projects = current_user.projects()
    return render_template("projects/list.html", projects=projects)


@projects_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            name=form.name.data.strip(),
            description=(form.description.data or "").strip(),
            owner=current_user,
        )
        db.session.add(project)
        db.session.commit()
        flash(f"Project '{project.name}' created.", "success")
        return redirect(url_for("projects.detail", project_id=project.id))
    return render_template("projects/new.html", form=form)


@projects_bp.route("/<int:project_id>")
@login_required
@project_access_required
def detail(project_id, project):
    project.ensure_statuses()  # backfill defaults for old projects
    member_form = AddMemberForm()
    return render_template(
        "projects/detail.html",
        project=project,
        member_form=member_form,
    )


@projects_bp.route("/<int:project_id>/members/add", methods=["POST"])
@login_required
@project_manage_required
def add_member(project_id, project):
    form = AddMemberForm()
    if not form.validate_on_submit():
        flash("Username is required.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    user = User.query.filter_by(username=form.username.data.strip()).first()
    if user is None:
        flash("No user with that username.", "danger")
    elif user.id == project.owner_id:
        flash("Owner is already a member.", "info")
    elif any(m.user_id == user.id for m in project.memberships):
        flash(f"{user.username} is already a member.", "info")
    else:
        db.session.add(Membership(project_id=project.id, user_id=user.id))
        db.session.commit()
        flash(f"Added {user.username} to project.", "success")

    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.route("/<int:project_id>/members/<int:user_id>/remove", methods=["POST"])
@login_required
@project_manage_required
def remove_member(project_id, project, user_id):
    if user_id == project.owner_id:
        flash("Cannot remove the project owner.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))
    membership = Membership.query.filter_by(
        project_id=project.id, user_id=user_id
    ).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash("Member removed.", "info")
    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.route("/<int:project_id>/delete", methods=["POST"])
@login_required
@project_manage_required
def delete_project(project_id, project):
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "info")
    return redirect(url_for("projects.list_projects"))


# ---------------------------------------------------------------------------
# Custom kanban columns (statuses)
# ---------------------------------------------------------------------------

@projects_bp.route("/<int:project_id>/statuses/add", methods=["POST"])
@login_required
@project_manage_required
def add_status(project_id, project):
    project.ensure_statuses()
    label = (request.form.get("label") or "").strip()
    color = (request.form.get("color") or "info").strip()

    if not label:
        flash("Column name is required.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))
    if len(label) > 60:
        flash("Column name is too long (max 60 chars).", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    # Slugify the label into a stable machine key.
    key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    if not key:
        flash("Column name must contain letters or numbers.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    if ProjectStatus.query.filter_by(project_id=project.id, key=key).first():
        flash(f"A column called '{label}' already exists.", "warning")
        return redirect(url_for("projects.detail", project_id=project.id))

    next_pos = (max((s.position for s in project.statuses), default=-1)) + 1
    db.session.add(
        ProjectStatus(
            project_id=project.id,
            key=key,
            label=label,
            color=color if color in ALLOWED_STATUS_COLORS else "info",
            position=next_pos,
            is_default=False,
        )
    )
    db.session.commit()
    flash(f"Column '{label}' added.", "success")
    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.route(
    "/<int:project_id>/statuses/<int:status_id>/delete", methods=["POST"]
)
@login_required
@project_manage_required
def delete_status(project_id, project, status_id):
    status = ProjectStatus.query.get_or_404(status_id)
    if status.project_id != project.id:
        abort(403)
    if status.is_default:
        flash("Default columns can't be removed.", "warning")
        return redirect(url_for("projects.detail", project_id=project.id))
    if status.task_count > 0:
        flash(
            f"Move tasks out of '{status.label}' before removing the column.",
            "warning",
        )
        return redirect(url_for("projects.detail", project_id=project.id))
    db.session.delete(status)
    db.session.commit()
    flash(f"Column '{status.label}' removed.", "info")
    return redirect(url_for("projects.detail", project_id=project.id))
