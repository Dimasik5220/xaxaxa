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

        self.last_login = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.last_update = "Никогда"
        self.current_theme = "Синяя"

        if not os.path.exists("data"): os.makedirs("data")
        if not os.path.exists("history"): os.makedirs("history")
        if not os.path.exists("user_data"): os.makedirs("user_data")

        self.search_history = self.load_json("history/search_history.json", [])
        self.favorites = self.load_json("user_data/favorites.json", [])
        self.promocodes = []
        self.cart = []

        self.init_ui()
        self.load_promocodes()
        self.apply_theme(self.current_theme)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_session_time)
        self.timer.start(60000)

    def update_session_time(self):
        minutes = int((time.time() - self.start_time) / 60)
        self.session_time_label.setText(f"Время в приложении: {minutes} мин")

    def load_json(self, path, default):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return default

    def save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        top_panel = QHBoxLayout()
        self.user_label = QLabel(f"Пользователь: {self.user_name}")
        self.last_login_label = QLabel(f"Последний вход: {self.last_login}")
        self.last_update_label = QLabel(f"Последнее обновление: {self.last_update}")
        self.session_time_label = QLabel("Время в приложении: 0 мин")

        top_panel.addWidget(self.user_label)
        top_panel.addWidget(self.last_login_label)
        top_panel.addWidget(self.last_update_label)
        top_panel.addWidget(self.session_time_label)

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon("icons/settings.png"))
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.clicked.connect(self.show_settings)
        top_panel.addWidget(self.settings_btn)

        self.rating_btn = QPushButton("Оценить")
        self.rating_btn.clicked.connect(self.show_rating_dialog)
        top_panel.addWidget(self.rating_btn)

        main_layout.addLayout(top_panel)

        self.tabs = QTabWidget()
        self.promo_tab = QWidget()
        self.fav_tab = QWidget()
        self.stats_tab = QWidget()

        self.init_promo_tab()
        self.init_fav_tab()
        self.init_stats_tab()

        self.tabs.addTab(self.promo_tab, "Промокоды")
        self.tabs.addTab(self.fav_tab, "Избранное")
        self.tabs.addTab(self.stats_tab, "Статистика")
        main_layout.addWidget(self.tabs)
