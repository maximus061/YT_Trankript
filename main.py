import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
    QLabel, QFrame, QSizePolicy, QTabWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QTextCursor


# ── Worker thread ────────────────────────────────────────────────────────────

class TranscriptWorker(QThread):
    output_line = pyqtSignal(str)
    finished    = pyqtSignal(bool)

    def __init__(self, cmd: list[str]):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            success = True
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    self.output_line.emit(line)
                if line.startswith("❌"):
                    success = False
            proc.wait()
            if proc.returncode != 0:
                success = False
            self.finished.emit(success)
        except Exception as e:
            self.output_line.emit(f"❌ Greška u GUI-ju: {e}")
            self.finished.emit(False)


# ── Shared helpers ───────────────────────────────────────────────────────────

def make_field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("field_label")
    return lbl

def make_divider() -> QFrame:
    div = QFrame()
    div.setFrameShape(QFrame.Shape.HLine)
    div.setObjectName("divider")
    return div


# ── Single video tab ─────────────────────────────────────────────────────────

class SingleVideoTab(QWidget):
    request_run = pyqtSignal(list)

    def __init__(self, api_key_getter):
        super().__init__()
        self._translate_on   = False
        self._keypoints_on   = False
        self._api_key_getter = api_key_getter
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 20, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(make_field_label("VIDEO URL ILI ID"))
        outer.addSpacing(5)
        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        self.url_input = QLineEdit()
        self.url_input.setObjectName("url_input")
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=…  ili  dQw4w9WgXcQ")
        self.url_input.returnPressed.connect(self._on_fetch)
        url_row.addWidget(self.url_input)
        self.fetch_btn = QPushButton("PREUZMI")
        self.fetch_btn.setObjectName("fetch_btn")
        self.fetch_btn.setFixedWidth(110)
        self.fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fetch_btn.clicked.connect(self._on_fetch)
        url_row.addWidget(self.fetch_btn)
        outer.addLayout(url_row)
        outer.addSpacing(20)

        outer.addWidget(make_divider())
        outer.addSpacing(16)

        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(12)

        self.btn_translate = QPushButton("PREVOD: ISKLJUČEN")
        self.btn_translate.setObjectName("toggle_btn_off")
        self.btn_translate.setCheckable(True)
        self.btn_translate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_translate.clicked.connect(self._toggle_translate)
        toggle_row.addWidget(self.btn_translate)

        self.btn_keypoints = QPushButton("KLJUČNE TAČKE: ISKLJUČENO")
        self.btn_keypoints.setObjectName("toggle_btn_off")
        self.btn_keypoints.setCheckable(True)
        self.btn_keypoints.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_keypoints.clicked.connect(self._toggle_keypoints)
        toggle_row.addWidget(self.btn_keypoints)
        outer.addLayout(toggle_row)
        outer.addStretch()

    def _toggle_translate(self):
        self._translate_on = not self._translate_on
        if self._translate_on:
            self.btn_translate.setText("PREVOD: UKLJUČEN")
            self.btn_translate.setObjectName("toggle_btn_on")
        else:
            self.btn_translate.setText("PREVOD: ISKLJUČEN")
            self.btn_translate.setObjectName("toggle_btn_off")
        self.btn_translate.setStyle(self.btn_translate.style())

    def _toggle_keypoints(self):
        self._keypoints_on = not self._keypoints_on
        if self._keypoints_on:
            self.btn_keypoints.setText("KLJUČNE TAČKE: UKLJUČENO")
            self.btn_keypoints.setObjectName("toggle_btn_on")
        else:
            self.btn_keypoints.setText("KLJUČNE TAČKE: ISKLJUČENO")
            self.btn_keypoints.setObjectName("toggle_btn_off")
        self.btn_keypoints.setStyle(self.btn_keypoints.style())

    def set_running(self, running: bool):
        self.fetch_btn.setEnabled(not running)
        self.fetch_btn.setText("…" if running else "PREUZMI")

    def _on_fetch(self):
        url          = self.url_input.text().strip()
        api_key      = self._api_key_getter()
        needs_gemini = self._translate_on or self._keypoints_on

        if not url:
            self.request_run.emit([])
            return

        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "script.py")
        cmd = [sys.executable, script_path, url]
        if needs_gemini:
            cmd.append(api_key)
        if self._translate_on:
            cmd.append("--prevod")
        if self._keypoints_on:
            cmd.append("--kljucne")

        self.request_run.emit(cmd)


# ── Playlist tab ─────────────────────────────────────────────────────────────

class PlaylistTab(QWidget):
    request_run = pyqtSignal(list)

    def __init__(self, api_key_getter):
        super().__init__()
        self._translate_on   = True
        self._keypoints_on   = True
        self._api_key_getter = api_key_getter
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 20, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(make_field_label("PLAYLIST URL"))
        outer.addSpacing(5)
        pl_row = QHBoxLayout()
        pl_row.setSpacing(10)
        self.pl_input = QLineEdit()
        self.pl_input.setObjectName("url_input")
        self.pl_input.setPlaceholderText("https://www.youtube.com/playlist?list=…")
        self.pl_input.returnPressed.connect(self._on_fetch)
        pl_row.addWidget(self.pl_input)
        self.fetch_btn = QPushButton("POKRENI")
        self.fetch_btn.setObjectName("fetch_btn")
        self.fetch_btn.setFixedWidth(110)
        self.fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fetch_btn.clicked.connect(self._on_fetch)
        pl_row.addWidget(self.fetch_btn)
        outer.addLayout(pl_row)
        outer.addSpacing(20)

        outer.addWidget(make_divider())
        outer.addSpacing(16)

        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(12)

        self.btn_translate = QPushButton("PREVOD: UKLJUČEN")
        self.btn_translate.setObjectName("toggle_btn_on")
        self.btn_translate.setCheckable(True)
        self.btn_translate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_translate.clicked.connect(self._toggle_translate)
        toggle_row.addWidget(self.btn_translate)

        self.btn_keypoints = QPushButton("KLJUČNE TAČKE: UKLJUČENO")
        self.btn_keypoints.setObjectName("toggle_btn_on")
        self.btn_keypoints.setCheckable(True)
        self.btn_keypoints.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_keypoints.clicked.connect(self._toggle_keypoints)
        toggle_row.addWidget(self.btn_keypoints)
        outer.addLayout(toggle_row)

        outer.addSpacing(14)
        self.info_label = QLabel(
            "Svaki video u playlisti će biti obrađen redom.\n"
            "Fajlovi se čuvaju u:  transcripts/playlist_DATUM/"
        )
        self.info_label.setObjectName("info_label")
        outer.addWidget(self.info_label)
        outer.addStretch()

    def _toggle_translate(self):
        self._translate_on = not self._translate_on
        if self._translate_on:
            self.btn_translate.setText("PREVOD: UKLJUČEN")
            self.btn_translate.setObjectName("toggle_btn_on")
        else:
            self.btn_translate.setText("PREVOD: ISKLJUČEN")
            self.btn_translate.setObjectName("toggle_btn_off")
        self.btn_translate.setStyle(self.btn_translate.style())

    def _toggle_keypoints(self):
        self._keypoints_on = not self._keypoints_on
        if self._keypoints_on:
            self.btn_keypoints.setText("KLJUČNE TAČKE: UKLJUČENO")
            self.btn_keypoints.setObjectName("toggle_btn_on")
        else:
            self.btn_keypoints.setText("KLJUČNE TAČKE: ISKLJUČENO")
            self.btn_keypoints.setObjectName("toggle_btn_off")
        self.btn_keypoints.setStyle(self.btn_keypoints.style())

    def set_running(self, running: bool):
        self.fetch_btn.setEnabled(not running)
        self.fetch_btn.setText("…" if running else "POKRENI")

    def _on_fetch(self):
        url     = self.pl_input.text().strip()
        api_key = self._api_key_getter()

        if not url:
            self.request_run.emit([])
            return

        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlist.py")
        cmd = [sys.executable, script_path, url, api_key]
        if self._translate_on:
            cmd.append("--prevod")
        if self._keypoints_on:
            cmd.append("--kljucne")

        self.request_run.emit(cmd)


# ── Main window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self._setup_window()
        self._build_ui()
        self._apply_styles()

    def _setup_window(self):
        self.setWindowTitle("YT Transkript")
        self.setMinimumSize(700, 640)
        self.resize(760, 720)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(32, 26, 32, 26)
        outer.setSpacing(0)

        header = QLabel("YT\nTRANSKRIPT")
        header.setObjectName("header")
        outer.addWidget(header)
        outer.addSpacing(22)

        outer.addWidget(make_divider())
        outer.addSpacing(20)

        # Shared API key (above tabs)
        outer.addWidget(make_field_label("GEMINI API KLJUČ"))
        outer.addSpacing(5)
        self.api_key_input = QLineEdit()
        self.api_key_input.setObjectName("api_key_input")
        self.api_key_input.setPlaceholderText("AIza…  (potreban za prevod i ključne tačke)")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        outer.addWidget(self.api_key_input)
        outer.addSpacing(20)

        outer.addWidget(make_divider())
        outer.addSpacing(16)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("main_tabs")

        self.tab_single   = SingleVideoTab(self._get_api_key)
        self.tab_playlist = PlaylistTab(self._get_api_key)

        self.tabs.addTab(self.tab_single,   "JEDAN VIDEO")
        self.tabs.addTab(self.tab_playlist, "PLAYLISTA")

        self.tab_single.request_run.connect(self._on_run)
        self.tab_playlist.request_run.connect(self._on_run)

        outer.addWidget(self.tabs)
        outer.addSpacing(18)

        outer.addWidget(make_divider())
        outer.addSpacing(14)

        outer.addWidget(make_field_label("IZLAZ"))
        outer.addSpacing(5)
        self.log = QTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outer.addWidget(self.log)
        outer.addSpacing(10)

        self.status_label = QLabel("Spreman.")
        self.status_label.setObjectName("status")
        outer.addWidget(self.status_label)

    def _get_api_key(self) -> str:
        return self.api_key_input.text().strip()

    def _on_run(self, cmd: list):
        if not cmd:
            self._set_status("⚠  Unesite URL.", error=True)
            return

        needs_gemini = "--prevod" in cmd or "--kljucne" in cmd
        if needs_gemini and not self._get_api_key():
            self._set_status("⚠  Gemini API ključ je potreban za prevod / ključne tačke.", error=True)
            return

        script_file = cmd[1]
        if not os.path.isfile(script_file):
            name = os.path.basename(script_file)
            self._set_status(f"⚠  {name} nije pronađen u istom direktorijumu.", error=True)
            return

        self.log.clear()
        self._set_running(True)
        self._set_status("Obrađujem…", error=False)

        self.worker = TranscriptWorker(cmd)
        self.worker.output_line.connect(self._append_log)
        self.worker.finished.connect(self._on_done)
        self.worker.start()

    def _set_running(self, running: bool):
        self.tab_single.set_running(running)
        self.tab_playlist.set_running(running)

    def _append_log(self, line: str):
        if line.startswith("✅"):
            colour = "#7ec87e"
        elif line.startswith("❌") or line.startswith("⚠"):
            colour = "#c87e7e"
        elif line.startswith("🎬"):
            colour = "#c8a96e"
        elif line.startswith("🌐"):
            colour = "#7eaec8"
        elif line.startswith("🔑"):
            colour = "#b07ec8"
        elif line.startswith("📋") or line.startswith("📁") or line.startswith("🏁"):
            colour = "#c8a96e"
        elif line.startswith("──"):
            colour = "#2a2520"
        else:
            colour = "#a09080"

        self.log.append(
            f'<span style="color:{colour}; font-family:\'Courier New\';">{line}</span>'
        )
        self.log.moveCursor(QTextCursor.MoveOperation.End)

    def _on_done(self, success: bool):
        self._set_running(False)
        if success:
            self._set_status("✅  Gotovo.", error=False)
        else:
            self._set_status("❌  Došlo je do greške — pogledajte izlaz iznad.", error=True)

    def _set_status(self, msg: str, error: bool):
        colour = "#c87e7e" if error else "#7e9e7e"
        self.status_label.setStyleSheet(
            f"font-family:'Courier New',monospace; font-size:11px; "
            f"letter-spacing:1px; color:{colour};"
        )
        self.status_label.setText(msg)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0d0d0d;
                color: #e8e0d4;
            }
            QLabel#header {
                font-family: "Courier New", Courier, monospace;
                font-size: 32px;
                font-weight: 900;
                letter-spacing: 6px;
                color: #e8e0d4;
            }
            QFrame#divider {
                border: none;
                border-top: 1px solid #2a2520;
            }
            QLabel#field_label {
                font-family: "Courier New", Courier, monospace;
                font-size: 10px;
                letter-spacing: 3px;
                color: #6b6058;
            }
            QLabel#info_label {
                font-family: "Courier New", Courier, monospace;
                font-size: 11px;
                color: #4a4038;
                margin-top: 4px;
            }
            QTabWidget#main_tabs::pane {
                border: 1px solid #2a2520;
                border-radius: 2px;
                background: #0d0d0d;
                padding: 16px;
            }
            QTabWidget#main_tabs > QTabBar::tab {
                font-family: "Courier New", Courier, monospace;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 3px;
                color: #4a4038;
                background: #0d0d0d;
                border: 1px solid #2a2520;
                border-bottom: none;
                padding: 8px 20px;
                margin-right: 4px;
            }
            QTabWidget#main_tabs > QTabBar::tab:selected {
                color: #c8a96e;
                border-color: #c8a96e;
                background: #0d0d0d;
            }
            QTabWidget#main_tabs > QTabBar::tab:hover:!selected {
                color: #8a8078;
                border-color: #3a3530;
            }
            QLineEdit#url_input, QLineEdit#api_key_input {
                background-color: #151210;
                border: 1px solid #2e2822;
                border-radius: 2px;
                color: #e8e0d4;
                font-family: "Courier New", Courier, monospace;
                font-size: 13px;
                padding: 9px 12px;
                selection-background-color: #c8a96e;
                selection-color: #0d0d0d;
            }
            QLineEdit#url_input:focus, QLineEdit#api_key_input:focus {
                border: 1px solid #c8a96e;
            }
            QPushButton#fetch_btn {
                background-color: #c8a96e;
                border: none;
                border-radius: 2px;
                color: #0d0d0d;
                font-family: "Courier New", Courier, monospace;
                font-size: 12px;
                font-weight: 900;
                letter-spacing: 2px;
                padding: 9px 0;
            }
            QPushButton#fetch_btn:hover  { background-color: #ddbf84; }
            QPushButton#fetch_btn:pressed { background-color: #a88a52; }
            QPushButton#fetch_btn:disabled {
                background-color: #2e2822;
                color: #5a5248;
            }
            QPushButton#toggle_btn_off {
                background-color: #1a1612;
                border: 1px solid #2e2822;
                border-radius: 2px;
                color: #5a5248;
                font-family: "Courier New", Courier, monospace;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 2px;
                padding: 10px 0;
            }
            QPushButton#toggle_btn_off:hover {
                background-color: #201c18;
                border-color: #4a4038;
                color: #8a8078;
            }
            QPushButton#toggle_btn_on {
                background-color: #1e2a1a;
                border: 1px solid #4a7a3a;
                border-radius: 2px;
                color: #7ec87e;
                font-family: "Courier New", Courier, monospace;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 2px;
                padding: 10px 0;
            }
            QPushButton#toggle_btn_on:hover {
                background-color: #243020;
                border-color: #6a9a5a;
            }
            QTextEdit#log {
                background-color: #080706;
                border: 1px solid #1e1a16;
                border-radius: 2px;
                color: #a09080;
                font-family: "Courier New", Courier, monospace;
                font-size: 12px;
                padding: 10px;
            }
            QScrollBar:vertical {
                background: #0d0d0d;
                width: 8px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #2e2822;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QLabel#status {
                font-family: "Courier New", Courier, monospace;
                font-size: 11px;
                letter-spacing: 1px;
                color: #4a4038;
            }
        """)


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#0d0d0d"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#e8e0d4"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#151210"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#1a1612"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#e8e0d4"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#1a1612"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#e8e0d4"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#c8a96e"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0d0d0d"))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
