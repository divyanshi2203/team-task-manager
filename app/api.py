"""Lightweight JSON REST API.

These endpoints mirror the server-side functionality. They use Flask-Login's
session cookie for auth, so once you log in via the web UI, you can call them
from the same browser / from `curl --cookie`.
"""
from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.models import Project, Task

api_bp = Blueprint("api", __name__)


def _project_or_403(project_id: int) -> Project:
    project = Project.query.get_or_404(project_id)
    if not project.has_access(current_user):
        abort(403)
    return project


@api_bp.route("/projects", methods=["GET"])
@login_required
def list_projects():
    if current_user.is_admin:
        projects = Project.query.all()
    else:
        projects = current_user.projects()
    return jsonify(
        [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "owner": p.owner.username,
                "member_count": len(p.members()),
                "task_count": p.tasks.count(),
            }
            for p in projects
        ]
    )


@api_bp.route("/projects", methods=["POST"])
@login_required
def create_project():
    if not current_user.is_admin:
        abort(403)
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    project = Project(
        name=name,
        description=(data.get("description") or "").strip(),
        owner=current_user,
    )
    db.session.add(project)
    db.session.commit()
    return jsonify({"id": project.id, "name": project.name}), 201


@api_bp.route("/projects/<int:project_id>/tasks", methods=["GET"])
@login_required
def list_tasks(project_id):
    project = _project_or_403(project_id)
    return jsonify([t.to_dict() for t in project.tasks.all()])


@api_bp.route("/projects/<int:project_id>/tasks", methods=["POST"])
@login_required
def create_task(project_id):
    project = _project_or_403(project_id)
    project.ensure_statuses()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    status = data.get("status", "todo")
    valid = project.status_keys()
    if status not in valid:
        return jsonify({"error": f"status must be one of {valid}"}), 400

    task = Task(
        title=title,
        description=(data.get("description") or "").strip(),
        status=status,
        project_id=project.id,
        assignee_id=data.get("assignee_id") or None,
        created_by_id=current_user.id,
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@api_bp.route("/tasks/<int:task_id>", methods=["PATCH"])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not task.project.has_access(current_user):
        abort(403)
    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        task.title = title
    if "description" in data:
        task.description = (data["description"] or "").strip()
    if "status" in data:
        task.project.ensure_statuses()
        if data["status"] not in task.project.status_keys():
            return jsonify({"error": "invalid status"}), 400
        task.status = data["status"]
    if "assignee_id" in data:
        task.assignee_id = data["assignee_id"] or None

    db.session.commit()
    return jsonify(task.to_dict())


@api_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    if not (project.can_manage(current_user) or task.created_by_id == current_user.id):
        abort(403)
    db.session.delete(task)
    db.session.commit()
    return "", 204


@api_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify(
        {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
        }
    )
