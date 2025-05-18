import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QTabWidget, QHBoxLayout, QProgressBar, QDialog,
    QPushButton, QSizePolicy, QMessageBox, QListWidget, QListWidgetItem, QCheckBox
)
from PyQt6.QtCore import Qt, QDateTime, QTimer
from PyQt6.QtGui import QColor, QPalette, QFont, QBrush

class TaskTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EVA Procedures Tracker")
        self.setFixedSize(1000, 550)

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

        self.subtab_indices = {
            0: 0,  # Egress: default to first subtask group
            1: 0,  # Navigation & Sampling
            2: 0   # Ingress
        }

        self.task_groups = {
            "Egress": {
                "Connect UIA to DCU and Start Depress": [
                    "EV1 verify umbilical connection from UIA to DCU (UIA & DCU)",
                    "EV-1, EMU PWR - ON (UIA)",
                    "BATT - UMB (DCU)",
                    "DEPRESS PUMP PWR - ON (UIA)"
                ],
                "Prep O2 Tanks": [
                    "OXYGEN O2 VENT - OPEN (UIA)",
                    "Wait until both Primary and Secondary OXY tanks are < 10psi (TELEMETRY)",
                    "OXYGEN O2 VENT - CLOSE (UIA)",
                    "OXY - PRI (DCU)",
                    "OXYGEN EMU-1 - OPEN (UIA)",
                    "Wait until EV1 Primary O2 tank > 3000 psi (TELEMETRY)",
                    "OXYGEN EMU-1 - CLOSE (UIA)",
                    "OXY - SEC (DCU)",
                    "OXYGEN EMU-1 - OPEN (UIA)",
                    "Wait until EV1 Secondary O2 tank > 3000 psi (TELEMETRY)",
                    "OXYGEN EMU-1 - CLOSE (UIA)",
                    "OXY - PRI (DCU)"
                ],
                "END Depress, Check Switches and Disconnect": [
                    "Wait until SUIT PRESSURE and O2 Pressure = 4 psi(TELEMETRY)",
                    "DEPRESS PUMP PWR - OFF (UIA)",
                    "BATT - LOCAL (DCU)",
                    "EV-1 EMU PWR - OFF (UIA)",
                    "Verify OXY - PRI (DCU)",
                    "Verify COMMS - A (DCU)",
                    "Verify FAN - PRI (DCU)",
                    "Verify PUMP - CLOSE (DCU)",
                    "Verify CO2 - A (DCU)",
                    "EV1 disconnect UIA and DCU umbilical (UIA & DCU)",
                    "Verify Comms are working between DCU and PR (DCU)"
                ]
            },
            "Navigation & Sampling": {
                "Determine Navigation Path": [
                    "Drop pins and determine best path for each POI provided by LTV (Rock Yard Map)",
                    "Verify the path has been generated. Wait for go from PR (Rock Yard Map)",
                    "Exit airlock and begin navigation to worksite"
                ],
                "Navigation": [
                    "Start camera feed (Camera)",
                    "Navigate to first POI (Rock Yard Map)",
                    "Repeat process for other POIs"
                ],
                "Geological Sampling": [
                    "Announce arrival to worksite over comms",
                    "Perform Sampling Procedures below",
                    "Upon completion of sampling procedures at worksite, announce completion over comms",
                    "Proceed to next location if available and restart Geologic Sampling procedures"
                    "If sampling is complete at all locations or return is required:", 
                    "  • Announce completion over comms",
                    "  • Begin ingress procedures per protocol (PR)",
                    "  • Monitor EV locations and scientific data throughout the entire sampling process"
                ],
                "Sampling Procedure": [
                    "EV Open Sampling Procedure",
                    "If available, perform Field Notes on Rock (photo, voice, etc.)",
                    "Perform XRF Scan",
                    "Press and HOLD trigger",
                    "Aim close to sample until beep, then release trigger",
                    "Announce “Scan Complete, PR verify data received.”",
                    "If Rock Composition outside of nominal parameters (see legend), collect rock.",
                    "If able, drop and label a pin",
                    "Repeat until all samples in area are scanned."                    
                ]
            },
            "Ingress": {
                "Return to Pressurized Rover": [
                    "Verify path to rover.",
                    "Begin return to PR."
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
                ]
            }
        }

        self.current_task_index = [0] * len(self.task_groups)
        self.task_labels = []
        # self.proc_complete_buttons = []
        # self.undo_buttons = []

        self.current_task_indices = {}  # Track current index for each main tab

        self.task_step_indices = {}  # (tab_idx, subtask_idx): current step
        self.render_functions = {}

        self.step_history = {tab_idx: [] for tab_idx in range(len(self.task_groups))}
        
        for tab_idx, (tab_name, tasks) in enumerate(self.task_groups.items()):
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            self.current_task_indices[tab_idx] = 0
            self.task_step_indices[tab_idx] = 0  # Start with step 0

            task_display_layout = QVBoxLayout()
            tab_layout.addLayout(task_display_layout)

            def render_task(tab_idx, task_display_layout=task_display_layout):
                # Clear previous contents
                self.clear_layout(task_display_layout)


                group = list(self.task_groups.items())[tab_idx][1]
                task_names = list(group.keys())
                subtask_idx = self.current_task_indices[tab_idx]
                step_idx = self.task_step_indices.get((tab_idx, subtask_idx), 0)
                current_subtask_name = task_names[subtask_idx]
                current_steps = group[current_subtask_name]

                # Title
                title_label = QLabel(current_subtask_name)
                title_label.setStyleSheet("font-size: 20pt; color: white;")
                task_display_layout.addWidget(title_label)

                # Steps
                for i, step in enumerate(current_steps):
                    # label = QLabel(f"{i+1}. {step}")
                    label = QLabel(f"{step}")
                    label.setWordWrap(True)
                    if i == step_idx:
                        label.setStyleSheet("font-size: 14pt; color: #00FF00; font-weight: bold;")
                    else:
                        label.setStyleSheet("font-size: 14pt; color: white;")
                    task_display_layout.addWidget(label)

                # Buttons
                button_layout = QHBoxLayout()

                # No need to store this unless you're manipulating them elsewhere
                complete_button = QPushButton("Mark Step Complete")
                complete_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        font-size: 20pt;
                        padding: 10px 20px;
                        border-radius: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                    QPushButton:pressed {
                        background-color: #1e7e34;
                    }
                """)
                complete_button.setMinimumHeight(60)
                complete_button.clicked.connect(lambda: self.mark_step_complete(tab_idx))
                button_layout.addWidget(complete_button)

                undo_button = QPushButton("Undo Last Step")
                undo_button.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        font-size: 20pt;
                        padding: 10px 20px;
                        border-radius: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                    QPushButton:pressed {
                        background-color: #bd2130;
                    }
                """)
                undo_button.setMinimumHeight(60)
                undo_button.clicked.connect(lambda: self.undo_last_task(tab_idx))
                button_layout.addWidget(undo_button)

                task_display_layout.addLayout(button_layout)


            # Save reference
            self.render_functions[tab_idx] = render_task

            # Navigation buttons
            # nav_layout = QHBoxLayout()
            # prev_btn = QPushButton("Previous Task")
            # next_btn = QPushButton("Next Task")

            # def make_nav_func(delta, idx):
            #     def nav():
            #         self.current_task_indices[idx] += delta
            #         self.current_task_indices[idx] %= len(self.task_groups[list(self.task_groups.keys())[idx]])
            #         self.task_step_indices[(idx, self.current_task_indices[idx])] = 0  # Reset step
            #         self.render_functions[idx](idx)
            #     return nav

            # prev_btn.clicked.connect(make_nav_func(-1, tab_idx))
            # next_btn.clicked.connect(make_nav_func(1, tab_idx))
            # nav_layout.addWidget(prev_btn)
            # nav_layout.addWidget(next_btn)

            # tab_layout.addLayout(nav_layout)
            self.render_functions[tab_idx](tab_idx)
            self.tabs.addTab(tab_widget, tab_name)

        right_side = QVBoxLayout()
        main_layout.addLayout(right_side, 1)

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

        for tab_name in self.task_groups.keys():
            item = QListWidgetItem(f"  {tab_name}")
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

        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setFont(QFont("Courier", 20, QFont.Weight.Bold))
        self.clock_label.setStyleSheet("color: #00ffcc;")
        right_side.addWidget(self.clock_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

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

    def update_clock(self):
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss AP")
        self.clock_label.setText(current_time)

    def procedure_complete(self, tab_idx):
        tasks = list(self.task_groups.values())[tab_idx]
        idx = self.current_task_index[tab_idx]

        if idx >= len(tasks):
            return

        self.task_completion_states[tab_idx][idx] = True
        self.task_timestamps[tab_idx][idx] = QDateTime.currentDateTime()
        self.task_labels[tab_idx][idx].setStyleSheet("color: #00ff00; font-size: 16pt;")
        self.current_task_index[tab_idx] += 1

        if self.current_task_index[tab_idx] == len(tasks):
            self.tabs.tabBar().setTabTextColor(tab_idx, QColor("#00ff00"))
            self.proc_complete_buttons[tab_idx].setEnabled(False)
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("✅ Procedure Complete")
            msg_box.setText(f"Procedure {self.tabs.tabText(tab_idx)} complete! Moving to next tab.")
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #121212;
                    color: white;
                    font-size: 14pt;
                }
                QPushButton {
                    background-color: #333;
                    color: white;
                    padding: 10px;
                    font-size: 12pt;
                }
            """)
            msg_box.exec()
            if tab_idx + 1 < self.tabs.count():
                self.tabs.setCurrentIndex(tab_idx + 1)

    def go_prev_tab(self):
        idx = self.tabs.currentIndex()
        if idx > 0:
            self.tabs.setCurrentIndex(idx - 1)

    def go_next_tab(self):
        idx = self.tabs.currentIndex()
        if idx < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(idx + 1)

    def sync_tab_list_selection(self, index):
        self.tab_list_widget.setCurrentRow(index)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self.clear_layout(child_layout)


    # def open_sampling_popup(self, tab_idx):
    #     dialog = SamplingProcedureDialog(self)
    #     result = dialog.exec()

    #     if result == QMessageBox.DialogCode.Accepted:
    #         # Advance the step index after dialog is completed
    #         subtask_idx = self.current_task_indices[tab_idx]
    #         step_idx = self.task_step_indices.get((tab_idx, subtask_idx), 0)
    #         self.step_history[tab_idx].append((subtask_idx, step_idx))
    #         self.task_step_indices[(tab_idx, subtask_idx)] = step_idx + 1
    #         self.render_functions[tab_idx](tab_idx)
    
    def mark_step_complete(self, tab_idx):
        task_group = list(self.task_groups.items())[tab_idx][1]
        subtask_idx = self.current_task_indices[tab_idx]
        task_keys = list(task_group.keys())
        steps = task_group[task_keys[subtask_idx]]
        key = (tab_idx, subtask_idx)

        current_step = self.task_step_indices.get(key, 0)

        # ✅ Check if current step is the Sampling Procedure trigger
        current_task = task_keys[subtask_idx]
        if (current_task == "Geological Sampling" and
            "Perform Sampling Procedures below" in steps[current_step]):

            procedure_steps = self.task_groups["Navigation & Sampling"]["Sampling Procedure"]

            def resume_task():
                self.task_step_indices[key] = current_step + 1
                self.render_functions[tab_idx](tab_idx)

            popup = SamplingProcedurePopup(procedure_steps, resume_task)
            popup.exec()
            return

        # ✅ Log current step to step_history
        if tab_idx not in self.step_history:
            self.step_history[tab_idx] = []
        self.step_history[tab_idx].append((tab_idx, subtask_idx, current_step))

        if current_step + 1 < len(steps):
            self.task_step_indices[key] = current_step + 1
        else:
            # ✅ Highlight the completed subtask
            self.highlight_task_complete(tab_idx, subtask_idx)

            # Move to next subtask or next tab
            if subtask_idx + 1 < len(task_keys):
                self.current_task_indices[tab_idx] += 1
                self.task_step_indices[(tab_idx, self.current_task_indices[tab_idx])] = 0
            else:
                if tab_idx + 1 < self.tabs.count():
                    self.tabs.setCurrentIndex(tab_idx + 1)
                return

        self.render_functions[tab_idx](tab_idx)
    
    # def mark_step_complete(self, tab_idx):
    #     task_group = list(self.task_groups.items())[tab_idx][1]
    #     subtask_idx = self.current_task_indices[tab_idx]
    #     task_keys = list(task_group.keys())
    #     steps = task_group[task_keys[subtask_idx]]
    #     key = (tab_idx, subtask_idx)

    #     current_step = self.task_step_indices.get(key, 0)

    #     # ✅ Log current step to step_history
    #     if tab_idx not in self.step_history:
    #         self.step_history[tab_idx] = []
    #     self.step_history[tab_idx].append((tab_idx, subtask_idx, current_step))

    #     if current_step + 1 < len(steps):
    #         self.task_step_indices[key] = current_step + 1
    #     else:
    #         # ✅ Highlight the completed subtask
    #         self.highlight_task_complete(tab_idx, subtask_idx)

    #         # Move to next subtask or next tab
    #         if subtask_idx + 1 < len(task_keys):
    #             self.current_task_indices[tab_idx] += 1
    #             self.task_step_indices[(tab_idx, self.current_task_indices[tab_idx])] = 0
    #         else:
    #             if tab_idx + 1 < self.tabs.count():
    #                 self.tabs.setCurrentIndex(tab_idx + 1)
    #             return

    #     self.render_functions[tab_idx](tab_idx)


    def undo_last_task(self, tab_idx):
        if not self.step_history[tab_idx]:
            QMessageBox.information(self, "Undo", "No previous steps to undo.")
            return
    
        # Get the last recorded step
        last_tab_idx, last_subtask_idx, last_step_idx = self.step_history[tab_idx].pop()
    
        # Update current subtask and step
        self.current_task_indices[tab_idx] = last_subtask_idx
        self.task_step_indices[(tab_idx, last_subtask_idx)] = last_step_idx
    
        self.render_functions[tab_idx](tab_idx)
    
    def highlight_task_complete(self, tab_idx, subtask_idx):
        # Example: assume each tab has a QListWidget per subtask group
        tab_widget = self.tabs.widget(tab_idx)
        list_widget = tab_widget.findChild(QListWidget)  # Adjust as needed
        if list_widget:
            item = list_widget.item(subtask_idx)
            if item:
                item.setForeground(Qt.green)
                item.setFont(QFont(item.font().family(), item.font().pointSize(), QFont.Bold))

class SamplingProcedurePopup(QDialog):
    # Store checkbox state across instances (class-level cache)
    checkbox_states = {}

    def __init__(self, procedure_steps, on_complete_callback):
        super().__init__()
        self.setWindowTitle("Sampling Procedure") 
        self.setMinimumSize(900, 500)
        self.setStyleSheet("""
            QLabel { color: white; }
            QWidget { background-color: #2b2b2b; }
            QCheckBox { color: white; font-size: 20px; }
            QPushButton {
                color: white; font-weight: bold; padding: 8px;
                border-radius: 4px; min-width: 120px; min-height: 40px; 
                font-size: 24px;
            }
            QPushButton#complete {
                background-color: #28a745;
            }
            QPushButton#close {
                background-color: #dc3545;
            }
        """)

        self.on_complete_callback = on_complete_callback
        self.procedure_steps = procedure_steps

        self.checkboxes = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title label
        title = QLabel("Sampling Procedure Steps:")
        title_font = QFont("Arial", 20)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)

        # Step checkboxes
        for i, step in enumerate(self.procedure_steps):
            checkbox = QCheckBox(step)
            checkbox.setChecked(self.get_checkbox_state(i))
            checkbox.stateChanged.connect(lambda state, idx=i: self.save_checkbox_state(idx, state))
            layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        # Buttons layout
        button_layout = QHBoxLayout()

        complete_btn = QPushButton("Complete Sampling")
        complete_btn.setObjectName("complete")
        complete_btn.clicked.connect(self.complete_procedure)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("close")
        close_btn.clicked.connect(self.reject)

        button_layout.addWidget(complete_btn)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_checkbox_state(self, idx):
        return self.checkbox_states.get(idx, False)

    def save_checkbox_state(self, idx, state):
        self.checkbox_states[idx] = (state == Qt.CheckState.Checked)

    def complete_procedure(self):
        self.on_complete_callback()
        self.accept()
        # if all(cb.isChecked() for cb in self.checkboxes):
        #     self.on_complete_callback()
        #     self.accept()
        # else:
        #     QMessageBox.warning(self, "Incomplete", "Please check off all steps before completing.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TaskTracker()
    window.show()
    sys.exit(app.exec())
