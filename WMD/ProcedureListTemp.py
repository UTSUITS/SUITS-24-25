import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QTabWidget, QHBoxLayout, QProgressBar,
    QPushButton, QSizePolicy, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDateTime, QTimer
from PyQt6.QtGui import QColor, QPalette, QFont, QBrush

class TaskTracker(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EVA Procedures Tracker")
        self.setFixedSize(1100, 600) 

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor("#121212"))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        self.setPalette(dark_palette)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        left_side = QVBoxLayout()
        main_layout.addLayout(left_side, 3)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #1E1E1E;
                color: white;
                padding: 14px 10px;
                font-weight: bold;
                font-size: 14pt;
            }
            QTabBar::tab:selected {
                background: #3A3A3A;
            }
            QTabBar::tab:disabled {
                color: grey;
            }
        """)
        left_side.addWidget(self.tabs)

        self.task_groups = {
            "Connect UIA to DCU and start Depress": [
                "EV1 verify umbilical connection from UIA to DCU",
                "EV-1, EMU PWR – ON",
                "BATT – UMB",
                "DEPRESS PUMP PWR – ON"
            ],
            "Prep O2 Tanks": [
                "OXYGEN O2 VENT – OPEN",
                "Wait until both Primary and Secondary OXY tanks are < 10psi",
                "OXYGEN O2 VENT – CLOSE",
                "OXY – PRI",
                "OXYGEN EMU-1 – OPEN",
                "Wait until EV1 Primary O2 tank > 3000 psi",
                "OXYGEN EMU-1 – CLOSE",
                "OXY – SEC",
                "OXYGEN EMU-1 – OPEN",
                "Wait until EV1 Secondary O2 tank > 3000 psi",
                "OXYGEN EMU-1 – CLOSE",
                "OXY – PRI"
            ],
            "END Depress, Check Switches and Disconnect": [
                "Wait until SUIT PRESSURE and O2 Pressure = 4",
                "DEPRESS PUMP PWR – OFF",
                "BATT – LOCAL",
                "EV-1 EMU PWR - OFF",
                "Verify OXY – PRI",
                "Verify COMMS – A",
                "Verify FAN – PRI",
                "Verify PUMP – CLOSE",
                "Verify CO2 – A",
                "EV1 disconnect UIA and DCU umbilical"
            ],
            "EVA Ingress": [
                "EV1 connect UIA and DCU umbilical",
                "EV-1 EMU PWR – ON",
                "BATT – UMB"
            ],
            "Vent O2 Tanks": [
                "OXYGEN O2 VENT – OPEN",
                "Wait until both Primary and Secondary OXY tanks are < 10psi",
                "OXYGEN O2 VENT – CLOSE"
            ],
            "Empty Water Tanks": [
                "PUMP – OPEN",
                "EV-1 WASTE WATER – OPEN",
                "Wait until water EV1 Coolant tank is < 5%",
                "EV-1, WASTE WATER – CLOSE"
            ],
            "Disconnect UIA from DCU": [
                "EV-1 EMU PWR – OFF",
                "EV1 disconnect umbilical"
            ],
        }

        self.current_task_index = [0] * len(self.task_groups)
        self.task_labels = []
        self.proc_complete_buttons = []
        self.undo_buttons = []

        for tab_idx, (tab_name, tasks) in enumerate(self.task_groups.items()):
            tab_widget = QWidget()
            tab_widget.setStyleSheet("background-color: #121212; color: white;")
            tab_layout = QVBoxLayout(tab_widget)

            labels_for_tab = []
            for i, task in enumerate(tasks, start=1):
                label = QLabel(f"{i}. {task}")
                label.setStyleSheet("color: white; font-size: 16pt;")
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                tab_layout.addWidget(label)
                labels_for_tab.append(label)
            self.task_labels.append(labels_for_tab)

            tab_layout.addStretch()

            btn_layout = QHBoxLayout()

            proc_btn = QPushButton("Procedure Complete")
            proc_btn.setStyleSheet("font-size: 14pt; padding: 12px; background-color: #444; color: white;")
            proc_btn.clicked.connect(lambda checked, idx=tab_idx: self.procedure_complete(idx))
            self.proc_complete_buttons.append(proc_btn)
            btn_layout.addWidget(proc_btn)

            undo_btn = QPushButton("Undo Last Task")
            undo_btn.setStyleSheet("font-size: 14pt; padding: 12px; background-color: #cc4444; color: white;")
            undo_btn.clicked.connect(lambda checked, idx=tab_idx: self.undo_last_task(idx))
            self.undo_buttons.append(undo_btn)
            btn_layout.addWidget(undo_btn)

            tab_layout.addLayout(btn_layout)
            self.tabs.addTab(tab_widget, tab_name)

        right_side = QVBoxLayout()
        main_layout.addLayout(right_side, 1)

        # Add persistent tab checklist list widget at the top right side
        self.tab_list_widget = QListWidget()
        self.tab_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                color: white;
                font-size: 14pt;
                font-weight: bold;
            }
            QListWidget::item:selected {
                background-color: #3A3A3A;
                color: #ffaa00;
            }
        """)
        self.tab_list_widget.setFixedHeight(250)
        right_side.addWidget(self.tab_list_widget)

        # Populate the tab checklist with tabs and unchecked initially
        for tab_name in self.task_groups.keys():
            item = QListWidgetItem(f"  {tab_name}")  # space for checkmark
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.tab_list_widget.addItem(item)
        self.tab_list_widget.currentRowChanged.connect(self.tabs.setCurrentIndex)
        self.tabs.currentChanged.connect(self.sync_tab_list_selection)

        nav_buttons_layout = QHBoxLayout()

        self.prev_button = QPushButton("Previous Tab")
        self.prev_button.setStyleSheet("background-color: #333; color: white; font-size: 12pt; padding: 8px;")
        self.prev_button.clicked.connect(self.go_prev_tab)
        nav_buttons_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next Tab")
        self.next_button.setStyleSheet("background-color: #333; color: white; font-size: 12pt; padding: 8px;")
        self.next_button.clicked.connect(self.go_next_tab)
        nav_buttons_layout.addWidget(self.next_button)

        right_side.addLayout(nav_buttons_layout)

        # Clock at the top
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setFont(QFont("Courier", 20, QFont.Weight.Bold))
        self.clock_label.setStyleSheet("color: #00ffcc;")
        right_side.addWidget(self.clock_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        # Progress bar below clock
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Overall Progress: %p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 10px;
                text-align: center;
                color: white;
                font-weight: bold;
                font-size: 14pt;
                background-color: #222;
            }
            QProgressBar::chunk {
                background-color: #00cc66;
                border-radius: 10px;
            }
        """)
        right_side.addWidget(self.progress_bar)

        self.task_completion_states = [
            [False] * len(tasks) for tasks in self.task_groups.values()
        ]
        self.task_timestamps = [
            [None] * len(tasks) for tasks in self.task_groups.values()
        ]

        self.update_progress()
        self.update_nav_buttons()
        self.update_tab_checklist()

    def update_clock(self):
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss AP")
        self.clock_label.setText(current_time)

    def log_task_event(self, message):
        print(message)  # For debugging purposes

    def procedure_complete(self, tab_idx):
        tasks = list(self.task_groups.values())[tab_idx]
        idx = self.current_task_index[tab_idx]

        if idx >= len(tasks):
            return

        self.task_completion_states[tab_idx][idx] = True
        self.task_timestamps[tab_idx][idx] = QDateTime.currentDateTime()
        self.task_labels[tab_idx][idx].setStyleSheet("color: #00ff00; font-size: 16pt;")
        self.log_task_event(f"✓ Completed: {tasks[idx]}")
        self.current_task_index[tab_idx] += 1

        if self.current_task_index[tab_idx] == len(tasks):
            self.tabs.tabBar().setTabTextColor(tab_idx, QColor("#00ff00"))
            self.proc_complete_buttons[tab_idx].setEnabled(False)
            QMessageBox.information(self, "Completed", f"Procedure '{self.tabs.tabText(tab_idx)}' completed!")

            next_tab = next(
                (i for i in range(tab_idx + 1, self.tabs.count())
                 if self.current_task_index[i] < len(self.task_groups[list(self.task_groups.keys())[i]])),
                next((i for i in range(tab_idx)
                      if self.current_task_index[i] < len(self.task_groups[list(self.task_groups.keys())[i]])), None)
            )
            if next_tab is not None:
                self.tabs.setCurrentIndex(next_tab)

        self.update_progress()
        self.update_nav_buttons()
        self.update_tab_checklist()

    def undo_last_task(self, tab_idx):
        idx = self.current_task_index[tab_idx] - 1
        if idx < 0:
            return

        self.task_completion_states[tab_idx][idx] = False
        self.task_timestamps[tab_idx][idx] = None
        self.task_labels[tab_idx][idx].setStyleSheet("color: white; font-size: 16pt;")
        self.log_task_event(f"Undo: {self.task_groups[list(self.task_groups.keys())[tab_idx]][idx]}")

        self.current_task_index[tab_idx] = idx
        self.proc_complete_buttons[tab_idx].setEnabled(True)
        self.tabs.tabBar().setTabTextColor(tab_idx, QColor("white"))

        self.update_progress()
        self.update_nav_buttons()
        self.update_tab_checklist()

    def update_progress(self):
        total_tasks = sum(len(tasks) for tasks in self.task_groups.values())
        total_completed = sum(sum(1 for done in states if done) for states in self.task_completion_states)
        percent = int(total_completed / total_tasks * 100) if total_tasks else 0
        self.progress_bar.setValue(percent)

    def update_nav_buttons(self):
        current = self.tabs.currentIndex()
        self.prev_button.setEnabled(current > 0)
        self.next_button.setEnabled(current < self.tabs.count() - 1)

    def go_prev_tab(self):
        current = self.tabs.currentIndex()
        if current > 0:
            self.tabs.setCurrentIndex(current - 1)

    def go_next_tab(self):
        current = self.tabs.currentIndex()
        if current < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(current + 1)

    def sync_tab_list_selection(self, index):
        if 0 <= index < self.tab_list_widget.count():
            self.tab_list_widget.setCurrentRow(index)

    def update_tab_checklist(self):
        current_index = self.tabs.currentIndex()
        for i in range(self.tab_list_widget.count()):
            full_text = self.tab_list_widget.item(i).text()
            tab_name = full_text[2:].strip()  # Remove the prefix symbol + space
            
            total_tasks = len(self.task_groups[tab_name])
            completed = sum(1 for done in self.task_completion_states[i] if done)

            if completed == total_tasks and total_tasks > 0:
                # Done - green checkmark
                checkmark = "✔"
                color = QColor("#00ff00")  # green
            elif completed > 0:
                # In progress - yellow bullet
                checkmark = "●"
                color = QColor("#ffaa00")  # yellow
            else:
                # Not started - no mark, white color
                checkmark = " "
                color = QColor("white")

            # If this is the current tab, override color to blue
            if i == current_index:
                color = QColor("#3399ff")  # blue

            self.tab_list_widget.item(i).setText(f"{checkmark} {tab_name}")
            self.tab_list_widget.item(i).setForeground(QBrush(color))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskTracker()
    window.show()
    sys.exit(app.exec())
