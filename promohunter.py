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


class WelcomeWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добро пожаловать")
        self.setFixedSize(400, 200)
        layout = QVBoxLayout()
        self.name_label = QLabel("Введите ваше имя:")
        self.name_input = QLineEdit()
        self.lang_label = QLabel("Выберите язык:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Русский", "English", "Беларуская", "Қазақша"])
        self.start_btn = QPushButton("Начать")
        self.start_btn.clicked.connect(self.accept)
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.lang_label)
        layout.addWidget(self.lang_combo)
        layout.addWidget(self.start_btn)
        self.setLayout(layout)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setFixedSize(300, 200)
        layout = QVBoxLayout()
        self.theme_label = QLabel("Выберите тему:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Синяя", "Темно-синяя", "Черная", "Серая", "Белая"])
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(self.theme_label)
        layout.addWidget(self.theme_combo)
        layout.addWidget(buttons)
        self.setLayout(layout)


class RatingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Оцените приложение")
        self.setFixedSize(300, 150)
        layout = QVBoxLayout()
        self.rating_label = QLabel("Выберите оценку:")
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["1 звезда", "2 звезды", "3 звезды", "4 звезды", "5 звезд"])
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_rating)
        buttons.rejected.connect(self.reject)
        layout.addWidget(self.rating_label)
        layout.addWidget(self.rating_combo)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def accept_rating(self):
        QMessageBox.information(self, "Спасибо", "Спасибо за ваш отзыв, наша компания очень благодарна вам!")
        self.accept()


class PromoHunter(QMainWindow):
    def __init__(self, user_name="Пользователь", lang="Русский"):
        super().__init__()
        self.user_name = user_name
        self.lang = lang
        self.start_time = time.time()
        self.setWindowTitle("PROMO HUNTER")
        self.setWindowIcon(QIcon("icon.png"))
        self.setFixedSize(1200, 800)
