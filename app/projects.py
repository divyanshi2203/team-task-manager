"""Project + team-membership routes."""
from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.decorators import (
    admin_required,
    project_access_required,
    project_manage_required,
)
from app.forms import AddMemberForm, ProjectForm
from app.models import Membership, Project, User

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
