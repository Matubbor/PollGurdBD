"""CustomTkinter screens for the PollGuard BD desktop application."""

from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Callable

import customtkinter as ctk

from config import APP_NAME, APP_SUBTITLE
from services.auth_service import AuthenticationService
from services.election_service import DuplicateVoteError, ElectionService
from services.report_service import ReportService


COLORS = {
    "navy": "#13131D",
    "navy_hover": "#252532",
    "navy_soft": "#1B1B27",
    "gold": "#C9A84C",
    "gold_hover": "#D7B75A",
    "gold_soft": "#2B281F",
    "green": "#2E7D52",
    "green_hover": "#256643",
    "red": "#B54040",
    "red_hover": "#963535",
    "amber": "#C9941C",
    "blue": "#5A5868",
    "muted": "#777481",
    "muted_dark": "#8C8994",
    "panel": "#FFFFFF",
    "surface": "#F5F1EA",
    "border": "#E4DED4",
    "text": "#1A1A24",
    "entry": "#20202C",
}


def clear_frame(frame: ctk.CTkFrame) -> None:
    for widget in frame.winfo_children():
        widget.destroy()


class LoginView(ctk.CTkFrame):
    """Local officer sign-in screen."""

    def __init__(
        self,
        master: ctk.CTk,
        auth_service: AuthenticationService,
        on_login: Callable[[dict[str, Any]], None],
    ):
        super().__init__(master, fg_color=COLORS["navy"])
        self.auth_service = auth_service
        self.on_login = on_login
        self.pack(fill="both", expand=True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self,
            width=390,
            height=485,
            corner_radius=16,
            fg_color=COLORS["navy_soft"],
            border_width=1,
            border_color="#4A412A",
        )
        card.grid(row=0, column=0, padx=30, pady=(28, 16))
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkLabel(
            card,
            text="✓",
            width=56,
            height=56,
            corner_radius=13,
            fg_color=COLORS["gold"],
            text_color=COLORS["navy"],
            font=ctk.CTkFont(size=27, weight="bold"),
        )
        badge.grid(row=0, column=0, pady=(28, 12))

        ctk.CTkLabel(
            card,
            text=APP_NAME,
            fg_color="transparent",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLORS["gold"],
        ).grid(row=1, column=0)
        ctk.CTkLabel(
            card,
            text=APP_SUBTITLE,
            fg_color="transparent",
            font=ctk.CTkFont(size=14),
            text_color="#C2BFC8",
        ).grid(row=2, column=0, pady=(4, 20))

        self.username_entry = ctk.CTkEntry(
            card,
            width=310,
            height=44,
            corner_radius=9,
            placeholder_text="Enter officer username",
            fg_color=COLORS["entry"],
            border_color="#5A4D2D",
            text_color="#F1EFEA",
            placeholder_text_color="#706D78",
        )
        self.username_entry.grid(row=3, column=0, pady=5)
        self.password_entry = ctk.CTkEntry(
            card,
            width=310,
            height=44,
            corner_radius=9,
            placeholder_text="Enter password",
            show="●",
            fg_color=COLORS["entry"],
            border_color="#5A4D2D",
            text_color="#F1EFEA",
            placeholder_text_color="#706D78",
        )
        self.password_entry.grid(row=4, column=0, pady=5)
        self.password_entry.bind("<Return>", lambda _event: self.attempt_login())

        self.feedback_label = ctk.CTkLabel(
            card,
            text="",
            width=310,
            height=24,
            fg_color="transparent",
            text_color=COLORS["red"],
            wraplength=320,
        )
        self.feedback_label.grid(row=5, column=0, pady=(2, 0))

        ctk.CTkButton(
            card,
            text="Sign in securely",
            width=310,
            height=44,
            corner_radius=9,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["navy"],
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.attempt_login,
        ).grid(row=6, column=0, pady=(5, 14))

        badges = ctk.CTkFrame(card, fg_color="transparent")
        badges.grid(row=7, column=0)
        for column, text in enumerate(
            ("Offline mode", "Local database", "Demo data only")
        ):
            ctk.CTkLabel(
                badges,
                text=text,
                height=22,
                corner_radius=11,
                fg_color=COLORS["gold_soft"],
                text_color="#A88E48",
                font=ctk.CTkFont(size=10),
            ).grid(row=0, column=column, padx=3)

        ctk.CTkLabel(
            self,
            text="PollGuard BD v1.0 · COM668 AT3 Demonstration Build",
            fg_color="transparent",
            text_color="#77737D",
            font=ctk.CTkFont(size=11),
        ).grid(row=1, column=0, padx=24, pady=(0, 16))

    def attempt_login(self) -> None:
        try:
            officer = self.auth_service.login(
                self.username_entry.get(), self.password_entry.get()
            )
        except (ValueError, PermissionError) as exc:
            self.feedback_label.configure(text=str(exc), text_color=COLORS["red"])
            self.password_entry.delete(0, "end")
            return
        except Exception as exc:
            messagebox.showerror("Login error", f"Could not access the database.\n{exc}")
            return
        self.on_login(officer)


class DashboardView(ctk.CTkFrame):
    """Authenticated shell with sidebar navigation and feature pages."""

    def __init__(
        self,
        master: ctk.CTk,
        officer: dict[str, Any],
        election_service: ElectionService,
        report_service: ReportService,
        on_logout: Callable[[], None],
    ):
        super().__init__(master, fg_color=COLORS["surface"])
        self.officer = officer
        self.election_service = election_service
        self.report_service = report_service
        self.on_logout = on_logout
        self.pages: dict[str, ctk.CTkFrame] = {}
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.pack(fill="both", expand=True)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=28, pady=24)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages = {
            "Dashboard": HomeDashboardPage(
                self.content, report_service, officer
            ),
            "Voter Logging": VoterLoggingPage(
                self.content, election_service, officer
            ),
            "Ballot Tracking": BallotTrackingPage(
                self.content, election_service, officer
            ),
            "Reports": ReportsPage(self.content, report_service, officer),
            "Audit Log": AuditLogPage(self.content, election_service),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")
        self.show_page("Dashboard")

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self,
            width=238,
            corner_radius=0,
            fg_color=COLORS["navy"],
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(7, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, padx=20, pady=(28, 4), sticky="ew")
        ctk.CTkLabel(
            brand,
            text="✓",
            width=35,
            height=35,
            corner_radius=8,
            fg_color=COLORS["gold"],
            text_color=COLORS["navy"],
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0)
        ctk.CTkLabel(
            brand,
            text="PollGuard BD",
            fg_color="transparent",
            text_color=COLORS["gold"],
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, padx=(10, 0))
        ctk.CTkLabel(
            sidebar,
            text="OFFICER CONSOLE",
            fg_color="transparent",
            text_color="#746B50",
            font=ctk.CTkFont(size=10, weight="bold"),
            anchor="w",
        ).grid(row=1, column=0, padx=66, pady=(0, 28), sticky="ew")

        for row, (label, icon) in enumerate(
            (
                ("Dashboard", "⌂"),
                ("Voter Logging", "◉"),
                ("Ballot Tracking", "▤"),
                ("Reports", "▣"),
                ("Audit Log", "≡"),
            ),
            start=2,
        ):
            button = ctk.CTkButton(
                sidebar,
                text=f"{icon}   {label}",
                width=205,
                height=46,
                corner_radius=9,
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["navy_hover"],
                text_color=COLORS["muted_dark"],
                font=ctk.CTkFont(size=14),
                command=lambda name=label: self.show_page(name),
            )
            button.grid(row=row, column=0, padx=16, pady=4)
            self.nav_buttons[label] = button

        officer_panel = ctk.CTkFrame(
            sidebar,
            fg_color=COLORS["navy_soft"],
            border_width=1,
            border_color="#2C2C39",
            corner_radius=10,
        )
        officer_panel.grid(row=8, column=0, padx=16, pady=(10, 12), sticky="ew")
        ctk.CTkLabel(
            officer_panel,
            text=f"Signed in as\n{self.officer['full_name']}",
            fg_color="transparent",
            justify="left",
            anchor="w",
            text_color="#B4B1BA",
            font=ctk.CTkFont(size=12),
            wraplength=175,
        ).grid(row=0, column=0, padx=14, pady=12, sticky="ew")
        ctk.CTkButton(
            sidebar,
            text="Sign out",
            width=206,
            height=38,
            fg_color="transparent",
            hover_color=COLORS["navy_hover"],
            border_width=1,
            border_color="#3A3A47",
            text_color=COLORS["muted_dark"],
            command=self.on_logout,
        ).grid(row=9, column=0, padx=16, pady=(0, 22))

    def show_page(self, name: str) -> None:
        for button_name, button in self.nav_buttons.items():
            button.configure(
                fg_color=(
                    COLORS["gold_soft"] if button_name == name else "transparent"
                ),
                text_color=(
                    COLORS["gold"]
                    if button_name == name
                    else COLORS["muted_dark"]
                ),
            )
        page = self.pages[name]
        if hasattr(page, "refresh"):
            page.refresh()
        page.tkraise()


class HomeDashboardPage(ctk.CTkFrame):
    """At-a-glance local election overview for the signed-in officer."""

    METRICS = (
        ("total_registered_voters", "Registered voters", "Local voter register", "gold"),
        ("issued_ballots", "Issued ballots", "All ballots issued", "navy"),
        ("cast_ballots", "Cast ballots", "Recorded as cast", "green"),
        ("spoiled_ballots", "Spoiled ballots", "Recorded as spoiled", "red"),
        ("pending_ballots", "Pending ballots", "Awaiting final status", "amber"),
        ("turnout_percentage", "Turnout", "Issued ÷ registered", "gold"),
    )

    def __init__(
        self,
        master: ctk.CTkFrame,
        report_service: ReportService,
        officer: dict[str, Any],
    ):
        super().__init__(master, fg_color="transparent")
        self.report_service = report_service
        self.officer = officer
        self.metric_labels: dict[str, ctk.CTkLabel] = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        PageHeader(
            self,
            "Dashboard",
            "A live overview of this polling station from the local SQLite database.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 18))

        welcome_card = ctk.CTkFrame(
            self,
            height=108,
            fg_color=COLORS["navy"],
            border_width=1,
            border_color="#3A3424",
            corner_radius=13,
        )
        welcome_card.grid(row=1, column=0, sticky="ew")
        welcome_card.grid_propagate(False)
        welcome_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            welcome_card,
            text=f"Welcome, {self.officer['full_name']}",
            fg_color="transparent",
            text_color=COLORS["gold"],
            font=ctk.CTkFont(size=21, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(20, 2), sticky="ew")
        ctk.CTkLabel(
            welcome_card,
            text="Role: Polling Officer  •  Session status: Active",
            fg_color="transparent",
            text_color=COLORS["muted_dark"],
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).grid(row=1, column=0, padx=24, sticky="ew")

        status_panel = ctk.CTkFrame(
            welcome_card,
            fg_color=COLORS["gold_soft"],
            border_width=1,
            border_color="#5A4D2D",
            corner_radius=10,
        )
        status_panel.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=22,
            pady=16,
            sticky="e",
        )
        ctk.CTkLabel(
            status_panel,
            text="●  OFFLINE MODE ACTIVE",
            fg_color="transparent",
            text_color=COLORS["gold"],
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(11, 2))
        self.clock_label = ctk.CTkLabel(
            status_panel,
            text="",
            fg_color="transparent",
            text_color="#B4B1BA",
            font=ctk.CTkFont(size=12),
        )
        self.clock_label.grid(row=1, column=0, padx=18, pady=(0, 11))

        summary_bar = ctk.CTkFrame(self, fg_color="transparent")
        summary_bar.grid(row=2, column=0, sticky="ew", pady=(18, 9))
        summary_bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            summary_bar,
            text="ELECTION AT A GLANCE",
            fg_color="transparent",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        self.refresh_status_label = ctk.CTkLabel(
            summary_bar,
            text="",
            fg_color="transparent",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11),
        )
        self.refresh_status_label.grid(row=0, column=1, padx=(12, 10))
        ctk.CTkButton(
            summary_bar,
            text="Refresh data",
            width=110,
            height=30,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["navy"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.refresh,
        ).grid(row=0, column=2)

        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.grid(row=3, column=0, sticky="nsew")
        for column in range(3):
            metrics_frame.grid_columnconfigure(column, weight=1, uniform="metrics")

        for index, (key, title, detail, color_key) in enumerate(self.METRICS):
            row, column = divmod(index, 3)
            card = ctk.CTkFrame(
                metrics_frame,
                fg_color=COLORS["panel"],
                border_width=1,
                border_color=COLORS["border"],
                corner_radius=13,
            )
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 6, 0 if column == 2 else 6),
                pady=(0 if row == 0 else 6, 6 if row == 0 else 0),
            )
            card.grid_columnconfigure(1, weight=1)

            accent = ctk.CTkFrame(
                card,
                width=5,
                height=82,
                fg_color=COLORS[color_key],
                corner_radius=2,
            )
            accent.grid(row=0, column=0, rowspan=3, padx=(15, 13), pady=17, sticky="ns")

            value_label = ctk.CTkLabel(
                card,
                text="—",
                fg_color="transparent",
                text_color=COLORS[color_key],
                font=ctk.CTkFont(size=29, weight="bold"),
                anchor="w",
            )
            value_label.grid(
                row=0,
                column=1,
                padx=(0, 15),
                pady=(16, 0),
                sticky="ew",
            )
            ctk.CTkLabel(
                card,
                text=title,
                fg_color="transparent",
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            ).grid(row=1, column=1, padx=(0, 15), sticky="ew")
            ctk.CTkLabel(
                card,
                text=detail,
                fg_color="transparent",
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=11),
                anchor="w",
            ).grid(
                row=2,
                column=1,
                padx=(0, 15),
                pady=(1, 15),
                sticky="ew",
            )
            self.metric_labels[key] = value_label

        self._update_clock()

    def _update_clock(self) -> None:
        if not self.winfo_exists():
            return
        self.clock_label.configure(
            text=datetime.now().astimezone().strftime("%a, %d %b %Y  •  %H:%M:%S")
        )
        self.after(1000, self._update_clock)

    def refresh(self) -> None:
        try:
            summary = self.report_service.build_summary()
        except Exception:
            self.refresh_status_label.configure(
                text="Unable to refresh local data",
                text_color=COLORS["red"],
            )
            for label in self.metric_labels.values():
                label.configure(text="—")
            return

        for key, label in self.metric_labels.items():
            value = summary[key]
            label.configure(
                text=f"{value:.2f}%" if key == "turnout_percentage" else str(value)
            )
        self.refresh_status_label.configure(
            text=f"Updated {datetime.now().strftime('%H:%M:%S')}",
            text_color=COLORS["muted"],
        )


class PageHeader(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, title: str, subtitle: str):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkFrame(
            self,
            width=4,
            height=48,
            fg_color=COLORS["gold"],
            corner_radius=2,
        ).grid(row=0, column=0, rowspan=2, padx=(0, 12), pady=2, sticky="ns")
        ctk.CTkLabel(
            self,
            text=title,
            fg_color="transparent",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=27, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(
            self,
            text=subtitle,
            fg_color="transparent",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", pady=(3, 0))


class VoterLoggingPage(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        election_service: ElectionService,
        officer: dict[str, Any],
    ):
        super().__init__(master, fg_color="transparent")
        self.election_service = election_service
        self.officer = officer
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        PageHeader(
            self,
            "Voter Logging",
            "Verify a voter against the local register and issue one paper ballot.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 22))

        card = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=14,
        )
        card.grid(row=1, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Enter voter identifier",
            fg_color="transparent",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, padx=26, pady=(24, 4), sticky="ew")
        ctk.CTkLabel(
            card,
            text="The identifier is hashed before it is compared or stored.",
            fg_color="transparent",
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, padx=26, sticky="ew")

        self.voter_entry = ctk.CTkEntry(
            card,
            height=48,
            corner_radius=9,
            placeholder_text="10–17 digit fictional voter ID",
            fg_color="#FAF8F4",
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text_color="#9A96A0",
            font=ctk.CTkFont(size=15),
        )
        self.voter_entry.grid(row=2, column=0, padx=(26, 12), pady=22, sticky="ew")
        self.voter_entry.bind("<Return>", lambda _event: self.record_voter())
        ctk.CTkButton(
            card,
            text="Verify and issue ballot",
            width=205,
            height=48,
            corner_radius=9,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["navy"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.record_voter,
        ).grid(row=2, column=1, padx=(0, 26), pady=22)

        self.result_panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=14,
        )
        self.result_panel.grid(row=2, column=0, sticky="nsew", pady=(18, 0))
        self.result_panel.grid_columnconfigure(0, weight=1)
        self.result_panel.grid_rowconfigure(0, weight=1)
        self._show_result(
            "Ready for the next voter",
            "No voter has been logged in this session yet.",
            COLORS["muted"],
        )

    def _show_result(self, title: str, detail: str, color: str) -> None:
        clear_frame(self.result_panel)
        content = ctk.CTkFrame(self.result_panel, fg_color="transparent")
        content.grid(row=0, column=0)
        ctk.CTkLabel(
            content,
            text="●",
            fg_color="transparent",
            text_color=color,
            font=ctk.CTkFont(size=34),
        ).grid(row=0, column=0, rowspan=2, padx=(0, 16))
        ctk.CTkLabel(
            content,
            text=title,
            fg_color="transparent",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            content,
            text=detail,
            fg_color="transparent",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=14),
            anchor="w",
            justify="left",
            wraplength=620,
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))

    def record_voter(self) -> None:
        try:
            ballot = self.election_service.log_voter(
                self.voter_entry.get(), self.officer["id"]
            )
        except (ValueError, LookupError, DuplicateVoteError) as exc:
            self._show_result("Voter not logged", str(exc), COLORS["red"])
            return
        except Exception as exc:
            self._show_result(
                "Database error",
                f"The transaction was cancelled safely. {exc}",
                COLORS["red"],
            )
            return

        self._show_result(
            "Ballot issued successfully",
            (
                f"{ballot['voter_reference']} is recorded as voted.\n"
                f"Ballot code: {ballot['ballot_code']}  •  Status: Pending"
            ),
            COLORS["green"],
        )
        self.voter_entry.delete(0, "end")
        self.voter_entry.focus()


class BallotTrackingPage(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        election_service: ElectionService,
        officer: dict[str, Any],
    ):
        super().__init__(master, fg_color="transparent")
        self.election_service = election_service
        self.officer = officer
        self.ballot_lookup: dict[str, int] = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        PageHeader(
            self,
            "Ballot Tracking",
            "Review issued ballots and record their final paper-ballot status.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 16))

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, sticky="ew")
        for column in range(4):
            self.cards_frame.grid_columnconfigure(column, weight=1)
        self.count_labels: dict[str, ctk.CTkLabel] = {}
        for column, (key, title, color) in enumerate(
            (
                ("issued", "Total issued", COLORS["blue"]),
                ("cast", "Cast", COLORS["green"]),
                ("spoiled", "Spoiled", COLORS["red"]),
                ("pending", "Pending", COLORS["amber"]),
            )
        ):
            card = ctk.CTkFrame(
                self.cards_frame,
                fg_color=COLORS["panel"],
                border_width=1,
                border_color=COLORS["border"],
                corner_radius=12,
            )
            card.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(0 if column == 0 else 6, 0 if column == 3 else 6),
            )
            label = ctk.CTkLabel(
                card,
                text="0",
                fg_color="transparent",
                text_color=color,
                font=ctk.CTkFont(size=28, weight="bold"),
            )
            label.pack(pady=(15, 0))
            ctk.CTkLabel(
                card,
                text=title,
                fg_color="transparent",
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(pady=(0, 14))
            self.count_labels[key] = label

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(16, 10))
        ctk.CTkLabel(
            actions,
            text="Select a pending ballot below:",
            fg_color="transparent",
            text_color=COLORS["muted"],
        ).pack(side="left")
        ctk.CTkButton(
            actions,
            text="Mark Cast",
            width=120,
            height=36,
            corner_radius=8,
            fg_color=COLORS["green"],
            hover_color=COLORS["green_hover"],
            command=lambda: self.change_status("Cast"),
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            actions,
            text="Mark Spoiled",
            width=125,
            height=36,
            corner_radius=8,
            fg_color=COLORS["red"],
            hover_color=COLORS["red_hover"],
            command=lambda: self.change_status("Spoiled"),
        ).pack(side="right")

        tables = ctk.CTkFrame(self, fg_color="transparent")
        tables.grid(row=3, column=0, sticky="nsew")
        tables.grid_columnconfigure(0, weight=3)
        tables.grid_columnconfigure(1, weight=2)
        tables.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            tables,
            text="Ballots",
            fg_color="transparent",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ctk.CTkLabel(
            tables,
            text="Recent activity",
            fg_color="transparent",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, padx=(14, 0), sticky="ew", pady=(0, 6))

        self.ballot_tree = self._create_tree(
            tables, ("code", "status", "time"), (200, 90, 145)
        )
        self.ballot_tree.heading("code", text="Ballot code")
        self.ballot_tree.heading("status", text="Status")
        self.ballot_tree.heading("time", text="Issued")
        self.ballot_tree.grid(row=1, column=0, sticky="nsew")

        self.activity_tree = self._create_tree(
            tables, ("code", "change", "time"), (145, 120, 125)
        )
        self.activity_tree.heading("code", text="Ballot")
        self.activity_tree.heading("change", text="Activity")
        self.activity_tree.heading("time", text="Time")
        self.activity_tree.grid(row=1, column=1, padx=(14, 0), sticky="nsew")

    @staticmethod
    def _create_tree(
        master: ctk.CTkFrame,
        columns: tuple[str, ...],
        widths: tuple[int, ...],
    ) -> ttk.Treeview:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(
            "PollGuard.Treeview",
            rowheight=31,
            font=("TkDefaultFont", 11),
            background=COLORS["panel"],
            fieldbackground=COLORS["panel"],
            foreground=COLORS["text"],
            borderwidth=1,
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
        )
        style.map(
            "PollGuard.Treeview",
            background=[("selected", COLORS["gold"])],
            foreground=[("selected", COLORS["navy"])],
        )
        style.configure(
            "PollGuard.Treeview.Heading",
            font=("TkDefaultFont", 10, "bold"),
            background="#EDE7DD",
            foreground=COLORS["text"],
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "PollGuard.Treeview.Heading",
            background=[("active", "#E3DACB")],
        )
        tree = ttk.Treeview(
            master,
            columns=columns,
            show="headings",
            style="PollGuard.Treeview",
            selectmode="browse",
        )
        for column, width in zip(columns, widths):
            tree.column(column, width=width, minwidth=70, stretch=True)
        return tree

    def refresh(self) -> None:
        try:
            counts = self.election_service.ballot_summary()
            ballots = self.election_service.list_ballots()
            activity = self.election_service.recent_activity()
        except Exception as exc:
            messagebox.showerror("Refresh error", str(exc))
            return

        for key, label in self.count_labels.items():
            label.configure(text=str(counts[key]))

        self.ballot_lookup.clear()
        for item in self.ballot_tree.get_children():
            self.ballot_tree.delete(item)
        for ballot in ballots:
            item = self.ballot_tree.insert(
                "",
                "end",
                values=(
                    ballot["ballot_code"],
                    "Pending" if ballot["status"] == "Issued" else ballot["status"],
                    ballot["issued_at"],
                ),
            )
            self.ballot_lookup[item] = ballot["id"]

        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
        for log in activity:
            change = (
                "Issued"
                if log["old_status"] is None
                else f"{log['old_status']} → {log['new_status']}"
            )
            self.activity_tree.insert(
                "",
                "end",
                values=(log["ballot_code"], change, log["created_at"]),
            )

    def change_status(self, new_status: str) -> None:
        selection = self.ballot_tree.selection()
        if not selection:
            messagebox.showwarning("No ballot selected", "Select a ballot first.")
            return
        ballot_id = self.ballot_lookup[selection[0]]
        try:
            self.election_service.update_ballot_status(
                ballot_id, new_status, self.officer["id"]
            )
        except (ValueError, LookupError) as exc:
            messagebox.showwarning("Status not changed", str(exc))
            self.refresh()
            return
        except Exception as exc:
            messagebox.showerror("Database error", str(exc))
            return
        self.refresh()


class AuditLogPage(ctk.CTkFrame):
    """Read-only view of ballot and report activity stored in SQLite."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        election_service: ElectionService,
    ):
        super().__init__(master, fg_color="transparent")
        self.election_service = election_service
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        PageHeader(
            self,
            "Audit Log",
            "Review ballot and report events recorded in the local database.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 20))

        toolbar = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=14,
        )
        toolbar.grid(row=1, column=0, sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            toolbar,
            text="Local activity history",
            fg_color="transparent",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(18, 2), sticky="ew")
        ctk.CTkLabel(
            toolbar,
            text="Read-only events from ballot_logs and generated report records.",
            fg_color="transparent",
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, padx=24, pady=(0, 18), sticky="ew")
        ctk.CTkButton(
            toolbar,
            text="Refresh activity",
            width=145,
            height=40,
            corner_radius=9,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["navy"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.refresh,
        ).grid(row=0, column=1, rowspan=2, padx=24)

        table_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=14,
        )
        table_card.grid(row=2, column=0, sticky="nsew", pady=(18, 0))
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            table_card,
            text="RECORDED EVENTS",
            fg_color="transparent",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=22, pady=(18, 8), sticky="ew")

        columns = ("timestamp", "event", "reference", "officer", "details")
        self.audit_tree = BallotTrackingPage._create_tree(
            table_card,
            columns,
            (170, 145, 225, 90, 250),
        )
        for column, title in zip(
            columns,
            ("Timestamp", "Event type", "Reference", "Officer", "Details"),
        ):
            self.audit_tree.heading(column, text=title, anchor="w")
            self.audit_tree.column(column, anchor="w")
        self.audit_tree.tag_configure("cast", foreground=COLORS["green"])
        self.audit_tree.tag_configure("spoiled", foreground=COLORS["red"])
        self.audit_tree.tag_configure("report", foreground="#8A6C12")
        self.audit_tree.grid(
            row=1,
            column=0,
            padx=20,
            pady=(0, 10),
            sticky="nsew",
        )

        self.status_label = ctk.CTkLabel(
            table_card,
            text="",
            fg_color="transparent",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        self.status_label.grid(
            row=2,
            column=0,
            padx=22,
            pady=(0, 14),
            sticky="ew",
        )

    def refresh(self) -> None:
        try:
            events = self.election_service.audit_activity()
        except Exception as exc:
            self.status_label.configure(
                text=f"Unable to load local audit activity: {exc}",
                text_color=COLORS["red"],
            )
            return

        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        for event in events:
            details = event["details"]
            tag = ""
            if event["event_type"] == "Report generated":
                tag = "report"
            elif details.endswith("Cast"):
                tag = "cast"
            elif details.endswith("Spoiled"):
                tag = "spoiled"
            self.audit_tree.insert(
                "",
                "end",
                values=(
                    str(event["event_time"]).replace("T", " ")[:19],
                    event["event_type"],
                    event["reference"],
                    event["username"] or "Unavailable",
                    details,
                ),
                tags=(tag,) if tag else (),
            )

        if events:
            noun = "event" if len(events) == 1 else "events"
            status = (
                f"{len(events)} {noun} shown  •  "
                f"Updated {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            status = "No ballot or report activity has been recorded yet."
        self.status_label.configure(text=status, text_color=COLORS["muted"])


class ReportsPage(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        report_service: ReportService,
        officer: dict[str, Any],
    ):
        super().__init__(master, fg_color="transparent")
        self.report_service = report_service
        self.officer = officer
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        PageHeader(
            self,
            "Election Reports",
            "Create readable and encrypted local reports with separate protections.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 20))

        toolbar = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=14,
        )
        toolbar.grid(row=1, column=0, sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            toolbar,
            text="Current election summary",
            fg_color="transparent",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(20, 2), sticky="ew")
        ctk.CTkLabel(
            toolbar,
            text="SHA-256 checks integrity; Fernet encrypts the secure .pgbd copy.",
            fg_color="transparent",
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, padx=24, pady=(0, 20), sticky="ew")
        ctk.CTkButton(
            toolbar,
            text="Generate secure report",
            width=210,
            height=44,
            corner_radius=9,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["navy"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.generate,
        ).grid(row=0, column=1, rowspan=2, padx=24)

        preview_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=14,
        )
        preview_card.grid(row=2, column=0, sticky="nsew", pady=(18, 0))
        preview_card.grid_rowconfigure(1, weight=1)
        preview_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            preview_card,
            text="REPORT PREVIEW",
            fg_color="transparent",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        self.preview = ctk.CTkTextbox(
            preview_card,
            fg_color="#FAF8F4",
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=9,
            font=ctk.CTkFont(family="Courier", size=13),
            activate_scrollbars=True,
        )
        self.preview.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="nsew")
        self.preview.configure(state="disabled")
        self.status_label = ctk.CTkLabel(
            preview_card,
            text="",
            fg_color="transparent",
            text_color=COLORS["green"],
            anchor="w",
            wraplength=760,
        )
        self.status_label.grid(row=2, column=0, padx=24, pady=(0, 17), sticky="ew")

    def refresh(self) -> None:
        try:
            summary = self.report_service.build_summary()
        except Exception as exc:
            self._set_preview(f"Could not load report data:\n{exc}")
            return
        lines = [
            "POLLGuard BD — Election Summary",
            "=" * 40,
            f"Registered voters : {summary['total_registered_voters']}",
            f"Issued ballots    : {summary['issued_ballots']}",
            f"Cast ballots      : {summary['cast_ballots']}",
            f"Spoiled ballots   : {summary['spoiled_ballots']}",
            f"Pending ballots   : {summary['pending_ballots']}",
            f"Turnout           : {summary['turnout_percentage']:.2f}%",
            "",
            "The SHA-256 integrity hash is added when the report is generated.",
        ]
        self._set_preview("\n".join(lines))

    def _set_preview(self, text: str) -> None:
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def generate(self) -> None:
        try:
            artifacts = self.report_service.generate_report(self.officer["id"])
        except Exception as exc:
            messagebox.showerror("Report not generated", str(exc))
            return
        self.refresh()
        self.status_label.configure(
            text=(
                f"Readable JSON: {artifacts.readable_path}\n"
                f"Encrypted report: {artifacts.encrypted_path}\n"
                f"SHA-256: {artifacts.report['report_hash_sha256']}"
            ),
            text_color=COLORS["green"],
        )
