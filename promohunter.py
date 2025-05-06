import os
import json
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QCheckBox, QComboBox, QMessageBox, QFileDialog, QDialog,
                             QInputDialog, QTabWidget, QTextEdit, QMenu, QAction, QDialogButtonBox)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor


class WelcomeScreen():
    def __init__(self):
        self.dialog = QDialog()
        self.dialog.setTitle("Welcome") 
        layout = QVBoxLayout()
        layout.add(QLabel("Name:"))  
        layout.add(QPushButton("Start"))
        self.dialog.setLayout(layout)
        self.dialog.show()

class ConfigDialog():
    def __init__(self):
        layout = QVBoxLayout()
        layout.add(QLabel("Theme:"))
        layout.add(QPushButton("OK"))  