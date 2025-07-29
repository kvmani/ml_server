from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from flask import current_app, request, render_template
from flask_admin import Admin, BaseView, expose, AdminIndexView

from ...config import Config
from ..services.metrics import visit_summary, active_user_count, metrics_response


class _SecureMixin:
    """Provide simple token based access control."""

    def is_accessible(self) -> bool:  # type: ignore[override]
        token = request.args.get("token")
        admin_token = current_app.config.get("ADMIN_TOKEN")
        return bool(admin_token and token == admin_token)

    def inaccessible_callback(self, name: str, **kwargs: Any):  # type: ignore[override]
        return "Unauthorized", 401


class DashboardView(_SecureMixin, AdminIndexView):
    @expose("/")
    def index(self):
        cfg = Config()
        feedback_file = cfg.feedback_settings.get("file_path", "src/ml_server/feedback.json")
        feedback: list[dict[str, Any]] = []
        if os.path.exists(feedback_file):
            with open(feedback_file) as f:
                feedback = json.load(f).get("feedback", [])

        health = {
            "super_resolution": cfg.ml_model_health_url and True,
            "ebsd_cleanup": cfg.ebsd_cleanup_settings.get("ml_model", {}).get("health_url"),
        }

        uptime = getattr(current_app, "start_time", None)
        uptime_str = "n/a"
        if uptime:
            delta = datetime.now() - datetime.fromtimestamp(uptime)
            days, seconds = delta.days, delta.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            uptime_str = f"{days}d {hours}h {minutes}m"

        logs_path = os.path.join(cfg.logging_settings.get("log_dir", "logs"), cfg.logging_settings.get("log_file", "app.log"))
        log_lines: list[str] = []
        if os.path.exists(logs_path):
            with open(logs_path) as lf:
                log_lines = lf.readlines()[-20:]

        metrics_text = metrics_response()[0].decode()

        return self.render(
            "admin_dashboard.html",
            feedback=feedback[:10],
            visits=visit_summary(),
            active_users=active_user_count(),
            health=health,
            uptime=uptime_str,
            logs="".join(log_lines),
            metrics=metrics_text,
        )


class FeedbackView(_SecureMixin, BaseView):
    @expose("/")
    def index(self):
        cfg = Config()
        feedback_file = cfg.feedback_settings.get("file_path", "src/ml_server/feedback.json")
        feedback: list[dict[str, Any]] = []
        if os.path.exists(feedback_file):
            with open(feedback_file) as f:
                feedback = json.load(f).get("feedback", [])
        return self.render("admin_feedback.html", feedback=feedback, page=1)


def init_admin(app) -> None:
    admin = Admin(app, name="Dashboard", index_view=DashboardView(url="/admin"), template_mode="bootstrap3")
    admin.add_view(FeedbackView(name="All Feedback", endpoint="feedback_admin"))

