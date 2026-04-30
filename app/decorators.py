"""Reusable view decorators for role / project access."""
from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def project_access_required(f):
    """Expects a `project_id` kwarg on the route. Loads project and checks access."""
    from app.models import Project

    @wraps(f)
    def wrapper(*args, **kwargs):
        project_id = kwargs.get("project_id")
        project = Project.query.get_or_404(project_id)
        if not project.has_access(current_user):
            abort(403)
        kwargs["project"] = project
        return f(*args, **kwargs)
    return wrapper


def project_manage_required(f):
    from app.models import Project

    @wraps(f)
    def wrapper(*args, **kwargs):
        project_id = kwargs.get("project_id")
        project = Project.query.get_or_404(project_id)
        if not project.can_manage(current_user):
            abort(403)
        kwargs["project"] = project
        return f(*args, **kwargs)
    return wrapper
