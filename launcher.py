import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QFileDialog,
    QLineEdit,
    QMessageBox,
)

from PySide6.QtCore import Qt
from crabby_ide import Main as CrabbyMain
from esolang_ide import Main as EsolangMain


class IDELauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Coral IDE Launcher")
        self.resize(900, 550)

        self.open_project_window = None
        self.new_project_window = None

        # Store IDE windows so Python does not delete them
        self.ide_windows = []

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("sidebar")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(15)
        sidebar_layout.setAlignment(Qt.AlignTop)

        open_project_btn = QPushButton("Open Project")
        new_project_btn = QPushButton("New Project")

        open_project_btn.setFixedHeight(42)
        new_project_btn.setFixedHeight(42)

        open_project_btn.clicked.connect(self.open_project)
        new_project_btn.clicked.connect(self.new_project)

        sidebar_layout.addWidget(open_project_btn)
        sidebar_layout.addWidget(new_project_btn)

        content = QFrame()
        content.setObjectName("content")

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.setCentralWidget(main_widget)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }

            #sidebar {
                background-color: #252526;
                border-right: 1px solid #333333;
            }

            #content {
                background-color: #1e1e1e;
            }

            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                text-align: left;
                padding-left: 14px;
            }

            QPushButton:hover {
                background-color: #3f3f46;
            }

            QPushButton:pressed {
                background-color: #007acc;
            }
        """)

    def launch_ide(self, path, ide_type="crabby"):
        try:
            if ide_type == "esolang":
                ide = EsolangMain(path)
            else:
                ide = CrabbyMain(path)
            ide.show()
            self.ide_windows.append(ide)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open project:\n{e}")

    def open_project(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Open Project Folder"
        )

        if folder:
            self.launch_ide(folder)

    def new_project(self):
        self.new_project_window = QWidget()
        self.new_project_window.setWindowTitle("New Project")
        self.new_project_window.resize(560, 340)

        layout = QVBoxLayout(self.new_project_window)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(14)

        title = QLabel("Create New Project")
        title.setObjectName("title")

        subtitle = QLabel("Choose where the project folder should be created.")
        subtitle.setObjectName("subtitle")

        project_type_label = QLabel("Project Type")
        project_type_label.setObjectName("pathLabel")

        project_type_row = QHBoxLayout()
        project_type_row.setSpacing(10)

        crabby_btn = QPushButton("Crabby")
        esolang_btn = QPushButton("Esolang")
        crabby_btn.setFixedHeight(36)
        esolang_btn.setFixedHeight(36)

        selected_type = {"type": "crabby"}

        def select_crabby():
            selected_type["type"] = "crabby"
            crabby_btn.setStyleSheet("background-color: #007acc; border: none;")
            esolang_btn.setStyleSheet("background-color: #333333;")

        def select_esolang():
            selected_type["type"] = "esolang"
            esolang_btn.setStyleSheet("background-color: #007acc; border: none;")
            crabby_btn.setStyleSheet("background-color: #333333;")

        crabby_btn.clicked.connect(select_crabby)
        esolang_btn.clicked.connect(select_esolang)

        project_type_row.addWidget(crabby_btn)
        project_type_row.addWidget(esolang_btn)

        select_crabby()

        path_label = QLabel("Project Path")
        path_label.setObjectName("pathLabel")

        path_row = QHBoxLayout()
        path_row.setSpacing(10)

        path_input = QLineEdit()
        path_input.setPlaceholderText("Type or select a project path...")

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(100)

        def select_path():
            folder = QFileDialog.getExistingDirectory(
                self.new_project_window,
                "Select Project Folder"
            )

            if folder:
                path_input.setText(folder.replace("\\", "/"))

        def create_project():
            project_path_text = path_input.text().strip()

            if not project_path_text:
                QMessageBox.warning(
                    self.new_project_window,
                    "Missing Path",
                    "Please enter or select a project path."
                )
                return

            project_path = Path(project_path_text).expanduser()

            try:
                project_path.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                QMessageBox.critical(
                    self.new_project_window,
                    "Error",
                    f"Could not create project folder:\n{e}"
                )
                return

            self.launch_ide(str(project_path), selected_type["type"])
            self.new_project_window.close()

        browse_btn.clicked.connect(select_path)

        path_row.addWidget(path_input)
        path_row.addWidget(browse_btn)

        create_btn = QPushButton("Create Project")
        create_btn.setObjectName("primaryButton")
        create_btn.setFixedHeight(40)
        create_btn.clicked.connect(create_project)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(project_type_label)
        layout.addLayout(project_type_row)
        layout.addSpacing(10)
        layout.addWidget(path_label)
        layout.addLayout(path_row)
        layout.addStretch()
        layout.addWidget(create_btn)

        self.new_project_window.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
                font-family: Segoe UI;
                font-size: 14px;
            }

            QLabel#title {
                font-size: 22px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #a0a0a0;
                font-size: 13px;
            }

            QLabel#pathLabel {
                color: #d4d4d4;
                font-weight: bold;
            }

            QLineEdit {
                background-color: #2d2d30;
                color: white;
                border: 1px solid #3f3f46;
                border-radius: 7px;
                padding: 8px 10px;
                selection-background-color: #007acc;
            }

            QLineEdit:focus {
                border: 1px solid #007acc;
            }

            QPushButton {
                background-color: #333333;
                color: white;
                border: 1px solid #444444;
                border-radius: 7px;
                padding: 8px 12px;
                text-align: center;
            }

            QPushButton:hover {
                background-color: #3f3f46;
            }

            QPushButton:pressed {
                background-color: #007acc;
            }

            QPushButton#primaryButton {
                background-color: #007acc;
                border: none;
                font-weight: bold;
            }

            QPushButton#primaryButton:hover {
                background-color: #1688d9;
            }
        """)

        self.new_project_path_input = path_input
        self.new_project_window.show()


app = QApplication(sys.argv)

window = IDELauncher()
window.show()

sys.exit(app.exec())