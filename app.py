"""PollGuard BD desktop application entry point."""

from __future__ import annotations

import customtkinter as ctk

from config import APP_NAME, DATABASE_PATH, REPORTS_DIR
from database.repository import ElectionRepository
from database.schema import initialize_database
from services.auth_service import AuthenticationService
from services.election_service import ElectionService
from services.report_service import ReportService
from ui.views import DashboardView, LoginView


class PollGuardApp(ctk.CTk):
    """Own the application services and switch between login/dashboard views."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Offline Election Assistant")
        self.geometry("1180x760")
        self.minsize(1000, 680)

        # Startup is idempotent: it creates missing tables/demo records but does
        # not reset or overwrite election activity.
        initialize_database(DATABASE_PATH)
        repository = ElectionRepository(DATABASE_PATH)
        self.auth_service = AuthenticationService(repository)
        self.election_service = ElectionService(repository)
        self.report_service = ReportService(repository, REPORTS_DIR)
        self.current_view: ctk.CTkFrame | None = None
        self.show_login()

    def _replace_view(self) -> None:
        if self.current_view is not None:
            self.current_view.destroy()

    def show_login(self) -> None:
        self._replace_view()
        self.current_view = LoginView(self, self.auth_service, self.show_dashboard)

    def show_dashboard(self, officer: dict) -> None:
        self._replace_view()
        self.current_view = DashboardView(
            self,
            officer,
            self.election_service,
            self.report_service,
            self.show_login,
        )


def main() -> None:
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = PollGuardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
