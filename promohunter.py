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

    def init_promo_tab(self):
        layout = QVBoxLayout()
        self.promo_tab.setLayout(layout)

        search_panel = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(
            ["Все категории", "Доставка еды", "Стройматериалы", "Озон/Wildberries", "Одежда/Обувь", "Электроника",
             "Красота/Здоровье", "Путешествия", "Развлечения"])
        search_panel.addWidget(self.category_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите промокод или магазин...")
        search_panel.addWidget(self.search_input)

        self.search_btn = QPushButton("Поиск")
        self.search_btn.clicked.connect(self.search_promocodes)
        search_panel.addWidget(self.search_btn)

        self.expired_check = QCheckBox("Показать истекшие")
        self.expired_check.stateChanged.connect(self.toggle_expired)
        search_panel.addWidget(self.expired_check)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            ["Сортировка", "По дате (новые)", "По дате (старые)", "По категории", "Активные", "Истекшие"])
        self.sort_combo.currentIndexChanged.connect(self.sort_promocodes)
        search_panel.addWidget(self.sort_combo)

        layout.addLayout(search_panel)
        self.promocodes_list = QListWidget()
        self.promocodes_list.setIconSize(QSize(32, 32))
        layout.addWidget(self.promocodes_list)

        button_panel = QHBoxLayout()
        self.add_to_cart_btn = QPushButton("Добавить в корзину")
        self.add_to_cart_btn.clicked.connect(self.add_to_cart)
        button_panel.addWidget(self.add_to_cart_btn)

        self.add_to_fav_btn = QPushButton("В избранное")
        self.add_to_fav_btn.clicked.connect(self.toggle_favorite)
        button_panel.addWidget(self.add_to_fav_btn)

        self.view_cart_btn = QPushButton("Корзина")
        self.view_cart_btn.clicked.connect(self.view_cart)
        button_panel.addWidget(self.view_cart_btn)

        self.save_cart_btn = QPushButton("Сохранить корзину")
        self.save_cart_btn.clicked.connect(self.save_cart)
        button_panel.addWidget(self.save_cart_btn)

        self.history_btn = QPushButton("История поиска")
        self.history_btn.clicked.connect(self.show_history)
        button_panel.addWidget(self.history_btn)

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.refresh_promocodes)
        button_panel.addWidget(self.refresh_btn)

        layout.addLayout(button_panel)
    def init_fav_tab(self):
        layout = QVBoxLayout()
        self.fav_tab.setLayout(layout)
        self.fav_list = QListWidget()
        self.fav_list.setIconSize(QSize(32, 32))
        layout.addWidget(self.fav_list)

        button_panel = QHBoxLayout()
        self.remove_fav_btn = QPushButton("Удалить из избранного")
        self.remove_fav_btn.clicked.connect(self.remove_from_favorites)
        button_panel.addWidget(self.remove_fav_btn)

        self.recommend_btn = QPushButton("Рекомендации")
        self.recommend_btn.clicked.connect(self.show_recommendations)
        button_panel.addWidget(self.recommend_btn)

        layout.addLayout(button_panel)
        self.update_favorites_list()

    def init_stats_tab(self):
        layout = QVBoxLayout()
        self.stats_tab.setLayout(layout)
        stats_label = QLabel("Статистика будет здесь")
        layout.addWidget(stats_label)

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.theme_combo.setCurrentText(self.current_theme)
        if dialog.exec_() == QDialog.Accepted:
            self.current_theme = dialog.theme_combo.currentText()
            self.apply_theme(self.current_theme)

    def show_rating_dialog(self):
        dialog = RatingDialog(self)
        dialog.exec_()

    def apply_theme(self, theme):
        if theme == "Синяя":
            self.setStyleSheet("""
                QWidget {
                    background-color: #e6f3ff;
                    color: #000;
                }
                QListWidget {
                    background-color: #fff;
                    border: 1px solid #99c2ff;
                }
                QPushButton {
                    background-color: #4d94ff;
                    color: white;
                    border: none;
                    padding: 5px;
                }
            """)
        elif theme == "Темно-синяя":
            self.setStyleSheet("""
                QWidget {
                    background-color: #003366;
                    color: #fff;
                }
                QListWidget {
                    background-color: #002244;
                    border: 1px solid #0055a5;
                }
                QPushButton {
                    background-color: #0055a5;
                    color: white;
                    border: none;
                    padding: 5px;
                }
            """)
        elif theme == "Черная":
            self.setStyleSheet("""
                QWidget {
                    background-color: #1a1a1a;
                    color: #fff;
                }
                QListWidget {
                    background-color: #2d2d2d;
                    border: 1px solid #4d4d4d;
                }
                QPushButton {
                    background-color: #333;
                    color: white;
                    border: none;
                    padding: 5px;
                }
            """)
        elif theme == "Серая":
            self.setStyleSheet("""
                QWidget {
                    background-color: #d9d9d9;
                    color: #000;
                }
                QListWidget {
                    background-color: #f2f2f2;
                    border: 1px solid #bfbfbf;
                }
                QPushButton {
                    background-color: #a6a6a6;
                    color: white;
                    border: none;
                    padding: 5px;
                }
            """)
        elif theme == "Белая":
            self.setStyleSheet("""
                QWidget {
                    background-color: #fff;
                    color: #000;
                }
                QListWidget {
                    background-color: #fff;
                    border: 1px solid #ddd;
                }
                QPushButton {
                    background-color: #f2f2f2;
                    color: #000;
                    border: 1px solid #ddd;
                    padding: 5px;
                }
            """)
    def parse_promocodes_from_sites(self):
        try:
            new_promocodes = []

            url1 = "https://www.promokodabra.ru/"
            response = requests.get(url1)
            soup = BeautifulSoup(response.text, 'html.parser')

            return new_promocodes
        except Exception as e:
            print(f"Ошибка парсинга: {e}")
            return []