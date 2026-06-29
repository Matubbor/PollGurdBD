"""CustomTkinter screens for the PollGuard BD desktop application."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

import customtkinter as ctk

from config import APP_NAME, APP_SUBTITLE
from services.auth_service import AuthenticationService
from services.election_service import DuplicateVoteError, ElectionService
from services.report_service import ReportService


COLORS = {
    "navy": "#102A43",
    "navy_hover": "#1D466B",
    "green": "#0F8B6D",
    "green_hover": "#0B7058",
    "red": "#C64747",
    "amber": "#D99000",
    "blue": "#2D6CDF",
    "muted": "#627D98",
    "panel": ("#FFFFFF", "#1D2733"),
    "surface": ("#F2F6FA", "#111820"),
    "border": ("#D8E2EC", "#344454"),
    "text": ("#102A43", "#F0F4F8"),
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
        super().__init__(master, fg_color=COLORS["surface"])
        self.auth_service = auth_service
        self.on_login = on_login
        self.pack(fill="both", expand=True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self,
            width=430,
            height=500,
            corner_radius=20,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=0, column=0, padx=30, pady=30)
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkLabel(
            card,
            text="✓",
            width=70,
            height=70,
            corner_radius=35,
            fg_color=COLORS["green"],
            text_color="white",
            font=ctk.CTkFont(size=34, weight="bold"),
        )
        badge.grid(row=0, column=0, pady=(42, 14))

        ctk.CTkLabel(
            card,
            text=APP_NAME,
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=1, column=0)
        ctk.CTkLabel(
            card,
            text=APP_SUBTITLE,
            font=ctk.CTkFont(size=14),
            text_color=COLORS["muted"],
        ).grid(row=2, column=0, pady=(5, 28))

        self.username_entry = ctk.CTkEntry(
            card, width=330, height=44, placeholder_text="Officer username"
        )
        self.username_entry.grid(row=3, column=0, pady=7)
        self.password_entry = ctk.CTkEntry(
            card,
            width=330,
            height=44,
            placeholder_text="Password",
            show="●",
        )
        self.password_entry.grid(row=4, column=0, pady=7)
        self.password_entry.bind("<Return>", lambda _event: self.attempt_login())

        self.feedback_label = ctk.CTkLabel(
            card,
            text="",
            width=330,
            height=30,
            text_color=COLORS["red"],
            wraplength=320,
        )
        self.feedback_label.grid(row=5, column=0, pady=(4, 0))

        ctk.CTkButton(
            card,
            text="Sign in securely",
            width=330,
            height=46,
            fg_color=COLORS["green"],
            hover_color=COLORS["green_hover"],
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.attempt_login,
        ).grid(row=6, column=0, pady=(6, 20))

        ctk.CTkLabel(
            card,
            text="Offline mode  •  Local database  •  Demo data only",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        ).grid(row=7, column=0)
        self.after(100, self.username_entry.focus)

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
        self.content.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages = {
            "Voter Logging": VoterLoggingPage(
                self.content, election_service, officer
            ),
            "Ballot Tracking": BallotTrackingPage(
                self.content, election_service, officer
            ),
            "Reports": ReportsPage(self.content, report_service, officer),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")
        self.show_page("Voter Logging")

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self,
            width=245,
            corner_radius=0,
            fg_color=COLORS["navy"],
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="✓  PollGuard BD",
            text_color="white",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(30, 4), sticky="ew")
        ctk.CTkLabel(
            sidebar,
            text="POLLING OFFICER CONSOLE",
            text_color="#9FB3C8",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).grid(row=1, column=0, padx=25, pady=(0, 30), sticky="ew")

        for row, (label, icon) in enumerate(
            (
                ("Voter Logging", "◉"),
                ("Ballot Tracking", "▤"),
                ("Reports", "▣"),
            ),
            start=2,
        ):
            button = ctk.CTkButton(
                sidebar,
                text=f"{icon}   {label}",
                width=205,
                height=46,
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["navy_hover"],
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda name=label: self.show_page(name),
            )
            button.grid(row=row, column=0, padx=20, pady=4)
            self.nav_buttons[label] = button

        ctk.CTkLabel(
            sidebar,
            text=f"Signed in as\n{self.officer['full_name']}",
            justify="left",
            anchor="w",
            text_color="#D9E2EC",
            font=ctk.CTkFont(size=12),
            wraplength=190,
        ).grid(row=8, column=0, padx=25, pady=(10, 12), sticky="ew")
        ctk.CTkButton(
            sidebar,
            text="Sign out",
            width=195,
            height=38,
            fg_color="#243B53",
            hover_color=COLORS["navy_hover"],
            command=self.on_logout,
        ).grid(row=9, column=0, padx=24, pady=(0, 24))

    def show_page(self, name: str) -> None:
        for button_name, button in self.nav_buttons.items():
            button.configure(
                fg_color=COLORS["green"] if button_name == name else "transparent"
            )
        page = self.pages[name]
        if hasattr(page, "refresh"):
            page.refresh()
        page.tkraise()


class PageHeader(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, title: str, subtitle: str):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text=title,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=27, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            self,
            text=subtitle,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(3, 0))


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
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, padx=26, pady=(24, 4), sticky="ew")
        ctk.CTkLabel(
            card,
            text="The identifier is hashed before it is compared or stored.",
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, padx=26, sticky="ew")

        self.voter_entry = ctk.CTkEntry(
            card,
            height=48,
            placeholder_text="10–17 digit fictional voter ID",
            font=ctk.CTkFont(size=15),
        )
        self.voter_entry.grid(row=2, column=0, padx=(26, 12), pady=22, sticky="ew")
        self.voter_entry.bind("<Return>", lambda _event: self.record_voter())
        ctk.CTkButton(
            card,
            text="Verify and issue ballot",
            width=205,
            height=48,
            fg_color=COLORS["green"],
            hover_color=COLORS["green_hover"],
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
            text_color=color,
            font=ctk.CTkFont(size=34),
        ).grid(row=0, column=0, rowspan=2, padx=(0, 16))
        ctk.CTkLabel(
            content,
            text=title,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            content,
            text=detail,
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
                text_color=color,
                font=ctk.CTkFont(size=28, weight="bold"),
            )
            label.pack(pady=(15, 0))
            ctk.CTkLabel(
                card,
                text=title,
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(pady=(0, 14))
            self.count_labels[key] = label

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(16, 10))
        ctk.CTkLabel(
            actions,
            text="Select a pending ballot below:",
            text_color=COLORS["muted"],
        ).pack(side="left")
        ctk.CTkButton(
            actions,
            text="Mark Cast",
            width=120,
            fg_color=COLORS["green"],
            hover_color=COLORS["green_hover"],
            command=lambda: self.change_status("Cast"),
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            actions,
            text="Mark Spoiled",
            width=125,
            fg_color=COLORS["red"],
            hover_color="#A83B3B",
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
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ctk.CTkLabel(
            tables,
            text="Recent activity",
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
        style.configure(
            "PollGuard.Treeview",
            rowheight=31,
            font=("TkDefaultFont", 11),
            borderwidth=0,
        )
        style.configure(
            "PollGuard.Treeview.Heading",
            font=("TkDefaultFont", 10, "bold"),
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
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(20, 2), sticky="ew")
        ctk.CTkLabel(
            toolbar,
            text="SHA-256 checks integrity; Fernet encrypts the secure .pgbd copy.",
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, padx=24, pady=(0, 20), sticky="ew")
        ctk.CTkButton(
            toolbar,
            text="Generate secure report",
            width=210,
            height=44,
            fg_color=COLORS["green"],
            hover_color=COLORS["green_hover"],
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
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        self.preview = ctk.CTkTextbox(
            preview_card,
            fg_color=("gray96", "#151E27"),
            border_width=0,
            font=ctk.CTkFont(family="Courier", size=13),
            activate_scrollbars=True,
        )
        self.preview.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="nsew")
        self.preview.configure(state="disabled")
        self.status_label = ctk.CTkLabel(
            preview_card,
            text="",
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
