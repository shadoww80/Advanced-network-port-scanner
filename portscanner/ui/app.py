"""Main CustomTkinter application window."""

from __future__ import annotations

import csv
from datetime import datetime
from tkinter import filedialog, ttk
import tkinter as tk
from typing import Any, Callable

import customtkinter as ctk

from portscanner.config import (
    APP_TITLE,
    CSV_DEFAULT_EXTENSION,
    CSV_DIALOG_TITLE,
    CSV_ENCODING,
    CSV_FILE_TYPES,
    CSV_HEADERS,
    CSV_INITIAL_FILENAME_PREFIX,
    CSV_SUMMARY_TITLE,
    CSV_TIMESTAMP_FORMAT,
    DEFAULT_END_PORT,
    DEFAULT_START_PORT,
    SUMMARY_PLACEHOLDER,
    TABLE_COLUMNS,
    WINDOW_GEOMETRY,
    WINDOW_MIN_SIZE,
)
from portscanner.core.scanner import PortScanner
from portscanner.logging_config import get_logger, setup_logging
from portscanner.models import ScanSummary
from portscanner.ui.theme import COLORS
from portscanner.validation import ValidationError, validate_scan_form

ScanRow = tuple[int, str, str, str, str]
logger = get_logger("ui.app")


class PortScannerApp(ctk.CTk):
    """Desktop UI for configuring scans and displaying open-port results."""

    def __init__(self) -> None:
        super().__init__()
        self._configure_window()
        self._initialize_state()
        self._scanner = self._create_scanner()
        self._build_layout()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _configure_window(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(APP_TITLE)
        self.geometry(WINDOW_GEOMETRY)
        self.minsize(*WINDOW_MIN_SIZE)
        self.configure(fg_color=COLORS["bg"])

    def _initialize_state(self) -> None:
        setup_logging()
        self._open_port_count = 0
        self._results: list[ScanRow] = []
        self._results_epoch = 0
        self._scan_summary = ScanSummary.empty()
        self._summary_value_labels: dict[str, ctk.CTkLabel] = {}

    def _create_scanner(self) -> PortScanner:
        return PortScanner(
            on_progress=self._schedule_progress_update,
            on_result=self._schedule_result_insert,
            on_status=self._schedule_status_update,
            on_complete=self._schedule_scan_complete,
            on_scan_started=self._schedule_scan_started,
        )

    @property
    def scanner(self) -> PortScanner:
        """Backward-compatible access to the scanner instance."""
        return self._scanner

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self._build_header()
        self._build_input_panel()
        self._build_action_bar()
        self._build_progress_section()
        self._build_scan_summary_panel()
        self._build_results_table()
        self._build_status_bar()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            header,
            text="⬡ ADVANCED NETWORK PORT SCANNER",
            font=ctk.CTkFont(family="Consolas", size=26, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="TCP · Multi-threaded · Service Detection",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"],
        ).pack(side="right", padx=4)

    def _build_input_panel(self) -> None:
        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.pack(fill="x", padx=24, pady=8)
        panel.columnconfigure(1, weight=1)

        fields = (
            ("Target", "target_entry", "IP address or domain (e.g. 192.168.1.1)", 280),
            ("Start Port", "start_entry", None, 100),
            ("End Port", "end_entry", None, 100),
        )

        for column_index, (label, attribute_name, placeholder, width) in enumerate(fields):
            ctk.CTkLabel(
                panel,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=COLORS["text"],
            ).grid(
                row=0,
                column=column_index * 2,
                padx=(16, 6),
                pady=16,
                sticky="w",
            )

            entry = ctk.CTkEntry(
                panel,
                width=width,
                placeholder_text=placeholder or "",
                fg_color=COLORS["surface_alt"],
                border_color=COLORS["border"],
                font=ctk.CTkFont(family="Consolas", size=13),
            )
            entry.grid(
                row=0,
                column=column_index * 2 + 1,
                padx=(0, 16),
                pady=16,
                sticky="ew" if column_index == 0 else "w",
            )
            setattr(self, attribute_name, entry)

        self.start_entry.insert(0, str(DEFAULT_START_PORT))
        self.end_entry.insert(0, str(DEFAULT_END_PORT))

    def _build_action_bar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=4)

        self.scan_btn = ctk.CTkButton(
            bar,
            text="▶  Start Scan",
            width=140,
            height=36,
            fg_color=COLORS["accent_dim"],
            hover_color=COLORS["accent_hover"],
            text_color="#000000",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._handle_start_scan,
        )
        self.scan_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            bar,
            text="■  Stop",
            width=110,
            height=36,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._handle_stop_scan,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.export_btn = self._create_outline_button(
            bar, text="⬇  Export CSV", width=130, command=self._handle_export_csv
        )
        self.export_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = self._create_outline_button(
            bar, text="✕  Clear", width=110, command=self._clear_results
        )
        self.clear_btn.pack(side="left")

    def _build_progress_section(self) -> None:
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=24, pady=(8, 4))

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progress: 0%",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["text_muted"],
        )
        self.progress_label.pack(anchor="w", pady=(0, 4))

        self.progress = ctk.CTkProgressBar(
            progress_frame,
            height=10,
            fg_color=COLORS["surface_alt"],
            progress_color=COLORS["accent"],
            corner_radius=5,
        )
        self.progress.pack(fill="x")
        self.progress.set(0)

    def _build_scan_summary_panel(self) -> None:
        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.pack(fill="x", padx=24, pady=(4, 8))

        ctk.CTkLabel(
            panel,
            text="Scan Summary",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=(12, 8), sticky="w")

        summary_fields = (
            ("Target", "target"),
            ("Resolved IP", "resolved_ip"),
            ("Scan Start Time", "start_time"),
            ("Scan End Time", "end_time"),
            ("Scan Duration", "duration"),
            ("Total Ports Scanned", "ports_scanned"),
            ("Open Ports Found", "open_ports"),
        )

        for index, (title, key) in enumerate(summary_fields):
            row = 1 + (index // 4)
            column = index % 4

            field_frame = ctk.CTkFrame(panel, fg_color="transparent")
            field_frame.grid(
                row=row,
                column=column,
                padx=12,
                pady=(0, 12),
                sticky="nsew",
            )

            ctk.CTkLabel(
                field_frame,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLORS["text_muted"],
            ).pack(anchor="w")

            value_label = ctk.CTkLabel(
                field_frame,
                text=SUMMARY_PLACEHOLDER,
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color=COLORS["accent"],
                wraplength=250,
                justify="left",
            )
            value_label.pack(anchor="w", pady=(2, 0))
            self._summary_value_labels[key] = value_label

        for column in range(4):
            panel.columnconfigure(column, weight=1)

        self._apply_scan_summary(self._scan_summary)

    def _build_results_table(self) -> None:
        container = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        container.pack(fill="both", expand=True, padx=24, pady=8)

        ctk.CTkLabel(
            container,
            text="Scan Results",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=16, pady=(12, 6))

        table_wrapper = ctk.CTkFrame(container, fg_color="transparent")
        table_wrapper.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._configure_treeview_style()
        self.table = ttk.Treeview(
            table_wrapper,
            columns=tuple(TABLE_COLUMNS),
            show="headings",
            style="Cyber.Treeview",
            selectmode="browse",
        )

        for column_id, (heading, width) in TABLE_COLUMNS.items():
            self.table.heading(column_id, text=heading)
            self.table.column(column_id, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_wrapper, orient="vertical", command=self.table.yview
        )
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.table.tag_configure("open", foreground=COLORS["accent"])

    def _build_status_bar(self) -> None:
        bar = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        bar.pack(fill="x", padx=24, pady=(0, 16))

        self.status_label = ctk.CTkLabel(
            bar,
            text="Status: Ready",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack(side="left", padx=16, pady=10)

        self.open_ports_label = ctk.CTkLabel(
            bar,
            text="Open Ports: 0",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=COLORS["accent"],
        )
        self.open_ports_label.pack(side="right", padx=16, pady=10)

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

    def _configure_treeview_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Cyber.Treeview",
            background=COLORS["table_bg"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["table_bg"],
            rowheight=32,
            font=("Consolas", 11),
            borderwidth=0,
        )
        style.configure(
            "Cyber.Treeview.Heading",
            background=COLORS["heading"],
            foreground="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Cyber.Treeview",
            background=[("selected", COLORS["accent_dim"])],
            foreground=[("selected", "#FFFFFF")],
        )

    def _create_outline_button(
        self,
        parent: ctk.CTkFrame,
        *,
        text: str,
        width: int,
        command: Callable[[], None],
    ) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=36,
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=command,
        )

    # ------------------------------------------------------------------
    # User actions
    # ------------------------------------------------------------------

    def _set_scan_controls_enabled(self, scanning: bool) -> None:
        self.scan_btn.configure(state="disabled" if scanning else "normal")
        self.stop_btn.configure(state="normal" if scanning else "disabled")
        self.target_entry.configure(state="disabled" if scanning else "normal")
        self.start_entry.configure(state="disabled" if scanning else "normal")
        self.end_entry.configure(state="disabled" if scanning else "normal")

    def _handle_start_scan(self) -> None:
        try:
            scan_input = validate_scan_form(
                self.target_entry.get(),
                self.start_entry.get(),
                self.end_entry.get(),
            )
        except ValidationError as exc:
            self._schedule_status_update(exc.user_message)
            return
        except (tk.TclError, RuntimeError):
            logger.exception("Unexpected error while reading scan input fields")
            self._schedule_status_update(
                "Unable to start scan — check your input and try again."
            )
            return

        try:
            self._clear_results()
            self._set_scan_controls_enabled(True)
            self._scanner.start(
                scan_input.target,
                scan_input.start_port,
                scan_input.end_port,
            )
        except (tk.TclError, RuntimeError):
            logger.exception("Unexpected error while starting scan")
            self._set_scan_controls_enabled(False)
            self._schedule_status_update(
                "Unable to start scan — see logs for details."
            )

    def _handle_stop_scan(self) -> None:
        self._scanner.stop()

    def _handle_export_csv(self) -> None:
        if not self._results:
            self._set_status_text("No results to export.")
            return

        filepath = filedialog.asksaveasfilename(
            title=CSV_DIALOG_TITLE,
            defaultextension=CSV_DEFAULT_EXTENSION,
            filetypes=list(CSV_FILE_TYPES),
            initialfile=(
                f"{CSV_INITIAL_FILENAME_PREFIX}"
                f"{datetime.now():{CSV_TIMESTAMP_FORMAT}}"
                f"{CSV_DEFAULT_EXTENSION}"
            ),
        )
        if not filepath:
            return

        snapshot = list(self._results)
        summary = self._scan_summary
        try:
            with open(filepath, "w", newline="", encoding=CSV_ENCODING) as handle:
                writer = csv.writer(handle)
                writer.writerow([CSV_SUMMARY_TITLE])
                for label, value in summary.csv_metadata_rows():
                    writer.writerow([label, value])
                writer.writerow([])
                writer.writerow(CSV_HEADERS)
                writer.writerows(snapshot)
            self._set_status_text(f"Exported {len(snapshot)} row(s) to {filepath}")
            logger.info(
                "CSV export succeeded | path=%s | rows=%d | target=%s",
                filepath,
                len(snapshot),
                summary.target,
            )
        except PermissionError as exc:
            self._set_status_text(f"Export failed: permission denied.")
            logger.error("CSV export failed | path=%s | error=%s", filepath, exc)
        except OSError as exc:
            self._set_status_text(f"Export failed: {exc}")
            logger.error("CSV export failed | path=%s | error=%s", filepath, exc)
        except csv.Error as exc:
            self._set_status_text("Export failed: invalid CSV data.")
            logger.error("CSV export failed while writing rows | path=%s | error=%s", filepath, exc)
        except (tk.TclError, RuntimeError):
            logger.exception("Unexpected error during CSV export | path=%s", filepath)
            self._set_status_text("Export failed due to an unexpected error.")

    def _clear_results(self) -> None:
        """Reset the results table and invalidate pending async inserts."""
        self._results_epoch += 1

        for row_id in self.table.get_children():
            self.table.delete(row_id)

        self._results.clear()
        self._open_port_count = 0
        self._scan_summary = ScanSummary.empty()
        self._apply_scan_summary(self._scan_summary)
        self.progress.set(0)
        self.progress_label.configure(text="Progress: 0%")
        self.open_ports_label.configure(text="Open Ports: 0")

    # ------------------------------------------------------------------
    # Thread-safe UI bridge
    # ------------------------------------------------------------------

    def _run_on_main_thread(self, callback: Callable[[], None]) -> None:
        """Schedule *callback* on the Tk main loop when the window is alive."""
        try:
            if self.winfo_exists():
                self.after(0, callback)
        except (tk.TclError, RuntimeError):
            logger.exception("Failed to schedule callback on main thread")

    def _schedule_progress_update(self, value: float) -> None:
        self._run_on_main_thread(lambda value=value: self._apply_progress_update(value))

    def _apply_progress_update(self, value: float) -> None:
        try:
            self.progress.set(value)
            self.progress_label.configure(text=f"Progress: {int(value * 100)}%")
        except tk.TclError:
            logger.exception("Failed to update progress bar")

    def _schedule_result_insert(
        self,
        port: int,
        status: str,
        service: str,
        response: str,
        banner: str,
    ) -> None:
        epoch = self._results_epoch
        self._run_on_main_thread(
            lambda: self._insert_scan_result(
                port, status, service, response, banner, epoch
            )
        )

    def _insert_scan_result(
        self,
        port: int,
        status: str,
        service: str,
        response: str,
        banner: str,
        epoch: int,
    ) -> None:
        if epoch != self._results_epoch:
            return

        try:
            row: ScanRow = (port, status, service, response, banner)
            self._results.append(row)
            self._open_port_count += 1
            self.table.insert("", "end", values=row, tags=("open",))
            self.open_ports_label.configure(text=f"Open Ports: {self._open_port_count}")
            self.table.yview_moveto(1.0)
        except tk.TclError:
            logger.exception("Failed to insert scan result for port %s", port)

    def _schedule_status_update(self, message: str) -> None:
        self._run_on_main_thread(lambda message=message: self._set_status_text(message))

    def _set_status_text(self, message: str) -> None:
        try:
            self.status_label.configure(text=f"Status: {message}")
        except tk.TclError:
            logger.exception("Failed to update status label")

    def _schedule_scan_started(self, summary: ScanSummary) -> None:
        self._run_on_main_thread(lambda: self._apply_scan_started(summary))

    def _apply_scan_started(self, summary: ScanSummary) -> None:
        try:
            self._scan_summary = summary
            self._apply_scan_summary(summary)
        except tk.TclError:
            logger.exception("Failed to apply scan-started summary")

    def _apply_scan_summary(self, summary: ScanSummary) -> None:
        idle = summary.target == SUMMARY_PLACEHOLDER
        values = {
            "target": summary.target,
            "resolved_ip": summary.resolved_ip,
            "start_time": (
                SUMMARY_PLACEHOLDER if idle else summary.format_start_time()
            ),
            "end_time": summary.format_end_time(),
            "duration": summary.format_duration(),
            "ports_scanned": str(summary.total_ports_scanned),
            "open_ports": str(summary.open_ports_found),
        }
        for key, text in values.items():
            label = self._summary_value_labels.get(key)
            if label is not None:
                label.configure(text=text)

    def _schedule_scan_complete(self, summary: ScanSummary) -> None:
        self._run_on_main_thread(lambda: self._apply_scan_complete(summary))

    def _apply_scan_complete(self, summary: ScanSummary) -> None:
        try:
            self._scan_summary = summary
            self._apply_scan_summary(summary)
            self._set_scan_controls_enabled(False)
            self.open_ports_label.configure(
                text=f"Open Ports: {summary.open_ports_found}"
            )
            if not summary.stopped:
                self.progress.set(1.0)
                self.progress_label.configure(text="Progress: 100%")
        except tk.TclError:
            logger.exception("Failed to apply scan completion state")
