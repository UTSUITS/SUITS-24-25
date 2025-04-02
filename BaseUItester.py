import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QTabWidget
from PyQt5.QtGui import QFont

class WMDUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wearable Mission Display (WMD)")
        self.setGeometry(100, 100, 800, 600)
        
        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.telemetry_tab = QWidget()
        self.mapping_tab = QWidget()
        self.navigation_tab = QWidget()
        self.warning_tab = QWidget()
        self.scientific_data_tab = QWidget()
        
        self.tabs.addTab(self.telemetry_tab, "Telemetry")
        self.tabs.addTab(self.mapping_tab, "Mapping")
        self.tabs.addTab(self.navigation_tab, "Navigation")
        self.tabs.addTab(self.warning_tab, "Caution/Warnings")
        self.tabs.addTab(self.scientific_data_tab, "Scientific Data")
        
        self.initTelemetryTab()
        self.initMappingTab()
        self.initNavigationTab()
        self.initWarningTab()
        self.initScientificDataTab()

    def initTelemetryTab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Real-time Biomedical and Environmental Data"))
        layout.addWidget(QTextEdit("Telemetry Data Here"))
        self.telemetry_tab.setLayout(layout)
    
    def initMappingTab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Mission Mapping and Positioning"))
        layout.addWidget(QTextEdit("Mapping Data Here"))
        self.mapping_tab.setLayout(layout)
    
    def initNavigationTab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Navigation and Path Guidance"))
        layout.addWidget(QTextEdit("Navigation Data Here"))
        self.navigation_tab.setLayout(layout)
    
    def initWarningTab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Caution and Warning Systems"))
        layout.addWidget(QTextEdit("Warnings and Alerts Here"))
        self.warning_tab.setLayout(layout)
    
    def initScientificDataTab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Scientific Data and Reports"))
        layout.addWidget(QTextEdit("Scientific Data Here"))
        self.scientific_data_tab.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = WMDUI()
    mainWin.show()
    sys.exit(app.exec_())
