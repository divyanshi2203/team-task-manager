"""SQLAlchemy models."""
from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="member")  # 'admin' | 'member'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    owned_projects = db.relationship(
        "Project", back_populates="owner", lazy="dynamic"
    )
    memberships = db.relationship(
        "Membership", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_tasks = db.relationship(
        "Task", back_populates="assignee", foreign_keys="Task.assignee_id"
    )

    # Helpers
    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def projects(self):
        """All projects this user can see (owned + member of)."""
        owned = self.owned_projects.all()
        member_of = [m.project for m in self.memberships]
        # Dedup preserving order
        seen, out = set(), []
        for p in owned + member_of:
            if p.id not in seen:
                seen.add(p.id)
                out.append(p)
        return out

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


# ---------------------------------------------------------------------------
# Projects + Membership
# ---------------------------------------------------------------------------

class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    owner = db.relationship("User", back_populates="owned_projects")
    memberships = db.relationship(
        "Membership", back_populates="project", cascade="all, delete-orphan"
    )
    tasks = db.relationship(
        "Task", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )

    def members(self):
        """Return all User objects with access (owner + memberships)."""
        users = {self.owner.id: self.owner}
        for m in self.memberships:
            users[m.user.id] = m.user
        return list(users.values())

    def has_access(self, user) -> bool:
        if user is None or not user.is_authenticated:
            return False
        if user.is_admin or user.id == self.owner_id:
            return True
        return any(m.user_id == user.id for m in self.memberships)

    def can_manage(self, user) -> bool:
        """Only owner or app-admin can edit project / add members."""
        if user is None or not user.is_authenticated:
            return False
        return user.is_admin or user.id == self.owner_id

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class Membership(db.Model):
    __tablename__ = "memberships"
    __table_args__ = (
        db.UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship("Project", back_populates="memberships")
    user = db.relationship("User", back_populates="memberships")


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

TASK_STATUSES = ("todo", "in_progress", "done")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), nullable=False, default="todo")
    due_date = db.Column(db.Date, nullable=True)

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    project = db.relationship("Project", back_populates="tasks")
    assignee = db.relationship(
        "User", back_populates="assigned_tasks", foreign_keys=[assignee_id]
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    @property
    def is_overdue(self) -> bool:
        return (
            self.status != "done"
            and self.due_date is not None
            and self.due_date < date.today()
        )

    @property
    def status_label(self) -> str:
        return {"todo": "To Do", "in_progress": "In Progress", "done": "Done"}.get(
            self.status, self.status
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "project_id": self.project_id,
            "assignee_id": self.assignee_id,
            "assignee": self.assignee.username if self.assignee else None,
            "is_overdue": self.is_overdue,
            "created_at": self.created_at.isoformat(),
        }
