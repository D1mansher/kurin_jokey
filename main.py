import sys
import os
import re  # ← Добавлено для валидации email/телефона
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QMessageBox,
                             QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QListWidgetItem,
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
                             QScrollArea, QSizePolicy, QSpacerItem, QDialog, QGridLayout,
                             QFileDialog, QLineEdit, QTextEdit, QRadioButton, QGroupBox,
                             QSpinBox, QComboBox, QAbstractItemView, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QRegularExpression  # ← QRegularExpression добавлен
from PyQt6.QtGui import QPixmap, QIcon, QFont, QPainter, QPalette, QColor, QKeyEvent, QRegularExpressionValidator
from datetime import datetime
import shutil

try:
    from converted_ui.ui_auth import Ui_AuthWindow
    from converted_ui.ui_admin import Ui_AdminWindow
    from converted_ui.ui_user import Ui_UserWindow
    from converted_ui.ui_chef import Ui_ChefWindow
    from converted_ui.ui_waiter import Ui_WaiterWindow
    from converted_ui.ui_payment import Ui_PaymentWindow
except ImportError as e:
    print(f"❌ Ошибка импорта UI модулей: {e}")
    sys.exit(1)

from database import Database


def center_window(window):
    """Центрирует окно посередине основного экрана."""
    screen = QApplication.primaryScreen().availableGeometry()
    x = (screen.width() - window.width()) // 2
    y = (screen.height() - window.height()) // 2
    window.move(x, y)


class DishDescriptionDialog(QDialog):
    """Диалоговое окно с подробным описанием блюда: описание, состав, БЖУ, вес."""
    def __init__(self, dish_name, description, grams, calories, proteins, fats, carbs, composition, parent=None):
        super().__init__(parent)
        self.setWindowTitle(dish_name)
        self.setFixedSize(500, 400)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        title_label = QLabel(dish_name)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #ff6600;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
                border-radius: 8px;
                background: #333;
            }
            QTabBar::tab {
                background: #444;
                color: white;
                padding: 8px 16px;
                border: 1px solid #555;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #ff6600;
                color: white;
            }
        """)
        description_tab = QWidget()
        description_layout = QVBoxLayout(description_tab)
        description_layout.setContentsMargins(10, 10, 10, 10)
        if grams > 0:
            weight_label = QLabel(f"{grams}г")
            weight_label.setStyleSheet("color: #ff6600; font-size: 14pt; font-weight: bold;")
            weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            description_layout.addWidget(weight_label)
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11pt; color: white; line-height: 1.4;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        description_layout.addWidget(desc_label)
        description_layout.addStretch()
        self.tab_widget.addTab(description_tab, "Описание")
        composition_tab = QWidget()
        composition_layout = QVBoxLayout(composition_tab)
        composition_layout.setContentsMargins(10, 10, 10, 10)
        if calories > 0:
            nutrition_frame = QFrame()
            nutrition_frame.setStyleSheet("""
                background: #444; 
                border-radius: 8px; 
                padding: 10px; 
                margin-bottom: 10px;
                border: 1px solid #555;
            """)
            nutrition_layout = QHBoxLayout(nutrition_frame)
            if grams > 0:
                c100 = (calories / grams) * 100
                p100 = (proteins / grams) * 100
                f100 = (fats / grams) * 100
                carb100 = (carbs / grams) * 100
                nutrition_text = (
                    f"<b>Ккал:</b> {c100:.1f} | "
                    f"<b>Б:</b> {p100:.1f}г | "
                    f"<b>Ж:</b> {f100:.1f}г | "
                    f"<b>У:</b> {carb100:.1f}г"
                )
            else:
                nutrition_text = (
                    f"<b>Ккал:</b> {calories} | "
                    f"<b>Б:</b> {proteins}г | "
                    f"<b>Ж:</b> {fats}г | "
                    f"<b>У:</b> {carbs}г"
                )
            nutrition_label = QLabel(nutrition_text)
            nutrition_label.setStyleSheet("color: white; font-size: 10pt;")
            nutrition_layout.addWidget(nutrition_label)
            composition_layout.addWidget(nutrition_frame)
        if composition:
            comp_label = QLabel("Состав:")
            comp_label.setStyleSheet("color: #ff6600; font-weight: bold; font-size: 12pt;")
            composition_layout.addWidget(comp_label)
            comp_text = QLabel(composition)
            comp_text.setStyleSheet("font-size: 11pt; color: white; line-height: 1.4;")
            comp_text.setWordWrap(True)
            composition_layout.addWidget(comp_text)
        else:
            no_comp_label = QLabel("Состав не указан")
            no_comp_label.setStyleSheet("font-size: 11pt; color: #888; font-style: italic;")
            no_comp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            composition_layout.addWidget(no_comp_label)
        composition_layout.addStretch()
        self.tab_widget.addTab(composition_tab, "Состав")
        layout.addWidget(self.tab_widget)
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover { 
                background: #e55a00; 
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.setLayout(layout)
        self.setStyleSheet("background: #2d2d2d;")


class OrderTrackingDialog(QDialog):
    """Диалог отслеживания статуса заказа с визуальной шкалой прогресса."""
    def __init__(self, order_number, status, order_items, total_amount, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Трекинг заказа #{order_number}")
        self.setFixedSize(500, 600)
        layout = QVBoxLayout()
        order_label = QLabel(f"Заказ #{order_number}")
        order_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #ff6600;")
        order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(order_label)
        status_label = QLabel(self.get_status_text(status))
        status_label.setStyleSheet("font-size: 16pt; color: #28a745; font-weight: bold;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        layout.addWidget(self.create_status_progress(status))
        items_label = QLabel("Состав заказа")
        items_label.setStyleSheet("font-size: 14pt; color: white; font-weight: bold;")
        layout.addWidget(items_label)
        for item in order_items:
            item_layout = QHBoxLayout()
            name_label = QLabel(f"{item[0]} x{item[1]}")
            name_label.setStyleSheet("color: white; font-size: 12pt;")
            price_label = QLabel(f"{item[3]:.2f} ₽")
            price_label.setStyleSheet("color: #ff6600; font-size: 12pt;")
            item_layout.addWidget(name_label)
            item_layout.addStretch()
            item_layout.addWidget(price_label)
            layout.addLayout(item_layout)
        total_layout = QHBoxLayout()
        total_label = QLabel("Итого:")
        total_label.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")
        total_amount_label = QLabel(f"{total_amount:.2f} ₽")
        total_amount_label.setStyleSheet("color: #ff6600; font-size: 14pt; font-weight: bold;")
        total_layout.addWidget(total_label)
        total_layout.addStretch()
        total_layout.addWidget(total_amount_label)
        layout.addLayout(total_layout)
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover { background: #e55a00; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.setLayout(layout)
        self.setStyleSheet("background: #2d2d2d;")

    def get_status_text(self, status):
        """Возвращает человекочитаемое название статуса заказа."""
        return {
            'sent_to_kitchen': 'Принят',
            'preparing': 'Готовится',
            'ready_for_serving': 'Готов к подаче',
            'completed': 'Выполнен'
        }.get(status, status)

    def create_status_progress(self, current_status):
        """Создаёт визуальную индикацию прогресса выполнения заказа."""
        frame = QFrame()
        layout = QVBoxLayout()
        statuses = [
            ('sent_to_kitchen', 'Принят'),
            ('preparing', 'Готовится'),
            ('ready_for_serving', 'Готов к подаче'),
            ('completed', 'Выполнен')
        ]
        for status, text in statuses:
            status_layout = QHBoxLayout()
            indicator = QLabel("●")
            indicator.setStyleSheet(
                f"color: {'#28a745' if status == current_status else '#6c757d'}; font-size: 16pt;")
            status_label = QLabel(text)
            status_label.setStyleSheet(
                f"color: {'#28a745' if status == current_status else 'white'}; font-size: 12pt; font-weight: {'bold' if status == current_status else 'normal'};")
            status_layout.addWidget(indicator)
            status_layout.addWidget(status_label)
            status_layout.addStretch()
            layout.addLayout(status_layout)
        frame.setLayout(layout)
        return frame


class DishWidget(QFrame):
    """Виджет карточки блюда: изображение, название, цена, кнопки «Подробнее» и «В корзину»."""
    add_to_cart = pyqtSignal(int, int)

    def __init__(self, dish_id, name, description, price, image_data=None, grams=0, calories=0, proteins=0, fats=0,
                 carbs=0, composition="", parent=None):
        super().__init__(parent)
        self.dish_id = dish_id
        self.name = name
        self.description = description
        self.price = price
        self.image_path = image_data
        self.grams = grams
        self.calories = calories
        self.proteins = proteins
        self.fats = fats
        self.carbs = carbs
        self.composition = composition
        self.setup_ui()

    def setup_ui(self):
        """Инициализирует UI-элементы виджета блюда."""
        self.setStyleSheet("""
            DishWidget {
                background: #333;
                border: 2px solid #555;
                border-radius: 12px;
                padding: 12px;
            }
            DishWidget:hover {
                border-color: #ff6600;
            }
        """)
        self.setFixedSize(220, 320)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        image_label = QLabel()
        image_label.setFixedSize(180, 120)
        image_label.setStyleSheet("background: transparent; border: none; border-radius: 8px;")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.image_path and os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(170, 110, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setText("🍗")
                image_label.setStyleSheet("background: transparent; border: none; font-size: 28pt; color: white;")
        else:
            image_label.setText("🍗")
            image_label.setStyleSheet("background: transparent; border: none; font-size: 28pt; color: white;")
        layout.addWidget(image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        name_label = QLabel(self.name)
        name_label.setStyleSheet("color: white; font-size: 11pt; font-weight: bold;")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        if self.calories > 0:
            nutrition_label = QLabel(f"🔥 {self.calories} ккал")
            nutrition_label.setStyleSheet("color: #ccc; font-size: 9pt;")
            nutrition_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(nutrition_label)
        price_label = QLabel(f"{self.price:.2f} ₽")
        price_label.setStyleSheet("color: #ff6600; font-size: 14pt; font-weight: bold;")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(price_label)
        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Кол-во:")
        quantity_label.setStyleSheet("color: white; font-size: 9pt;")
        quantity_layout.addWidget(quantity_label)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(10)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setFixedWidth(50)
        self.quantity_spin.setStyleSheet("""
            QSpinBox {
                background: #333;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
                color: white;
                font-size: 9pt;
            }
        """)
        quantity_layout.addWidget(self.quantity_spin)
        quantity_layout.addStretch()
        layout.addLayout(quantity_layout)
        buttons_layout = QHBoxLayout()
        desc_btn = QPushButton("Подробнее")
        desc_btn.setFixedHeight(28)
        desc_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff6600;
                border: 2px solid #ff6600;
                border-radius: 6px;
                padding: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background: rgba(255, 102, 0, 0.1);
            }
        """)
        desc_btn.clicked.connect(self.show_description)
        buttons_layout.addWidget(desc_btn)
        cart_btn = QPushButton("В корзину")
        cart_btn.setFixedHeight(28)
        cart_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        cart_btn.clicked.connect(self.add_to_cart_clicked)
        buttons_layout.addWidget(cart_btn)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def show_description(self):
        """Открывает диалог подробного описания блюда."""
        dialog = DishDescriptionDialog(
            self.name,
            self.description,
            self.grams,
            self.calories,
            self.proteins,
            self.fats,
            self.carbs,
            self.composition,
            self
        )
        dialog.exec()

    def add_to_cart_clicked(self):
        """Эмитирует сигнал добавления блюда в корзину с указанным количеством."""
        quantity = self.quantity_spin.value()
        self.add_to_cart.emit(self.dish_id, quantity)


class OrderHistoryWidget(QFrame):
    """Виджет отображения заказа в истории: номер, статус, краткий состав, итоговая сумма."""
    def __init__(self, order_number, status, total_amount, order_date, order_items, parent=None):
        super().__init__(parent)
        self.order_number = order_number
        self.status = status
        self.order_items = order_items
        self.total_amount = total_amount
        self.setup_ui(order_date)

    def setup_ui(self, order_date):
        """Инициализирует UI-элементы виджета истории заказа."""
        self.setStyleSheet("""
            OrderHistoryWidget {
                background: #333;
                border: 2px solid #555;
                border-radius: 12px;
                padding: 15px;
                margin: 5px;
            }
        """)
        self.setFixedWidth(300)
        layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        order_label = QLabel(f"№ {self.order_number}")
        order_label.setStyleSheet("color: #ff6600; font-size: 16pt; font-weight: bold;")
        date_label = QLabel(order_date.split()[0])
        date_label.setStyleSheet("color: #888; font-size: 10pt;")
        header_layout.addWidget(order_label)
        header_layout.addStretch()
        header_layout.addWidget(date_label)
        layout.addLayout(header_layout)
        status_label = QLabel(self.get_status_text(self.status))
        status_label.setStyleSheet("color: #28a745; font-size: 14pt; font-weight: bold;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        items_text = ""
        for i, item in enumerate(self.order_items[:2]):
            items_text += f"{item[0]} x{item[1]}\n"
        if len(self.order_items) > 2:
            items_text += f"... и ещё {len(self.order_items) - 2} позиций"
        items_label = QLabel(items_text)
        items_label.setStyleSheet("color: white; font-size: 10pt;")
        layout.addWidget(items_label)
        amount_label = QLabel(f"{self.total_amount:.2f} ₽")
        amount_label.setStyleSheet("color: #ff6600; font-size: 12pt; font-weight: bold;")
        amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(amount_label)
        view_btn = QPushButton("Просмотреть статус")
        view_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #e55a00;
            }
        """)
        view_btn.clicked.connect(self.show_tracking)
        layout.addWidget(view_btn)
        self.setLayout(layout)

    def get_status_text(self, status):
        """Возвращает человекочитаемое название статуса заказа."""
        return {
            'sent_to_kitchen': 'Принят',
            'preparing': 'Готовится',
            'ready_for_serving': 'Готов к подаче',
            'completed': 'Выполнен'
        }.get(status, status)

    def show_tracking(self):
        """Открывает диалог отслеживания заказа."""
        dialog = OrderTrackingDialog(self.order_number, self.status, self.order_items, self.total_amount, self)
        dialog.exec()


class OrderChefWidget(QFrame):
    """Виджет заказа для повара: выбор цвета, множественный выбор, визуальная индикация."""
    order_toggled = pyqtSignal(int, bool)
    color_changed = pyqtSignal(int, str)

    def __init__(self, order_id, order_number, table_number, customer_name, order_items, total_amount, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.order_number = order_number
        self.is_selected = False
        self.current_color = "default"
        self.setup_ui(table_number, customer_name, order_items, total_amount)
        self.update_appearance()

    def setup_ui(self, table_number, customer_name, order_items, total_amount):
        """Создаёт UI: заголовок, данные клиента, состав, итог, кнопки цвета, статус выбора."""
        self.setFixedSize(320, 450)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        order_label = QLabel(f"ЗАКАЗ #{self.order_number}")
        order_label.setStyleSheet("color: #ff6600; font-size: 16pt; font-weight: bold;")
        order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(order_label)
        info_layout = QVBoxLayout()
        table_layout = QHBoxLayout()
        table_icon = QLabel("🍽️")
        table_icon.setStyleSheet("font-size: 12pt;")
        table_label = QLabel(f"Стол: {table_number}")
        table_label.setStyleSheet("color: white; font-size: 12pt; font-weight: bold;")
        table_layout.addWidget(table_icon)
        table_layout.addWidget(table_label)
        table_layout.addStretch()
        info_layout.addLayout(table_layout)
        customer_layout = QHBoxLayout()
        customer_icon = QLabel("👤")
        customer_icon.setStyleSheet("font-size: 12pt;")
        customer_label = QLabel(f"Клиент: {customer_name}")
        customer_label.setStyleSheet("color: #aaa; font-size: 11pt;")
        customer_layout.addWidget(customer_icon)
        customer_layout.addWidget(customer_label)
        customer_layout.addStretch()
        info_layout.addLayout(customer_layout)
        layout.addLayout(info_layout)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #555;")
        separator.setFixedHeight(2)
        layout.addWidget(separator)
        items_label = QLabel("СОСТАВ ЗАКАЗА:")
        items_label.setStyleSheet("color: white; font-size: 12pt; font-weight: bold;")
        layout.addWidget(items_label)
        scroll_area = QScrollArea()
        scroll_area.setFixedHeight(150)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #555;
                border-radius: 6px;
                background: #2a2a2a;
            }
            QScrollArea QWidget {
                background: #2a2a2a;
            }
        """)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(5)
        for item in order_items:
            item_widget = self.create_dish_item(item[0], item[1], item[2])
            scroll_layout.addWidget(item_widget)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        total_layout = QHBoxLayout()
        total_text = QLabel("ИТОГО:")
        total_text.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")
        total_amount_label = QLabel(f"{total_amount:.2f} ₽")
        total_amount_label.setStyleSheet("color: #ff6600; font-size: 16pt; font-weight: bold;")
        total_layout.addWidget(total_text)
        total_layout.addStretch()
        total_layout.addWidget(total_amount_label)
        layout.addLayout(total_layout)
        color_buttons_layout = QHBoxLayout()
        for color, emoji in [("red", "🔴"), ("yellow", "🟡"), ("blue", "🔵"), ("green", "🟢"), ("purple", "🟣")]:
            btn = QPushButton(emoji)
            btn.setFixedSize(30, 30)
            btn.setToolTip(color.capitalize())
            btn.clicked.connect(lambda _, c=color: self.set_color(c))
            color_buttons_layout.addWidget(btn)
        color_buttons_layout.addStretch()
        layout.addLayout(color_buttons_layout)
        self.status_label = QLabel("⬜ НЕ ВЫБРАН")
        self.status_label.setStyleSheet("color: #888; font-size: 10pt; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def create_dish_item(self, name, quantity, price):
        """Создаёт строку позиции блюда в составе заказа."""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(8, 4, 8, 4)
        name_label = QLabel(f"• {name} x{quantity}")
        name_label.setStyleSheet("color: white; font-size: 10pt;")
        name_label.setWordWrap(True)
        price_label = QLabel(f"{price * quantity:.2f} ₽")
        price_label.setStyleSheet("color: #ff6600; font-size: 10pt; font-weight: bold;")
        item_layout.addWidget(name_label, 4)
        item_layout.addWidget(price_label, 1)
        return item_widget

    def set_color(self, color):
        """Устанавливает цветовую метку заказа и обновляет внешний вид."""
        self.current_color = color
        self.update_appearance()
        self.color_changed.emit(self.order_id, color)

    def mousePressEvent(self, event):
        """Обрабатывает клик — переключает выбор заказа."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_selection()
        super().mousePressEvent(event)

    def toggle_selection(self):
        """Переключает флаг `is_selected` и обновляет внешний вид и сигналы."""
        self.is_selected = not self.is_selected
        self.update_appearance()
        self.order_toggled.emit(self.order_id, self.is_selected)

    def update_appearance(self):
        """Обновляет внешний вид виджета в зависимости от состояния и цвета."""
        color_styles = {
            "default": {"background": "#333", "border": "#555", "status_color": "#888"},
            "red": {"background": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5a1a1a, stop:1 #7a2a2a)",
                    "border": "#dc3545", "status_color": "#dc3545"},
            "yellow": {"background": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5a4a1a, stop:1 #7a6a2a)",
                       "border": "#ffc107", "status_color": "#ffc107"},
            "blue": {"background": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a3a5a, stop:1 #2a4a7a)",
                     "border": "#007bff", "status_color": "#007bff"},
            "green": {"background": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a5a3a, stop:1 #2a7a4a)",
                      "border": "#28a745", "status_color": "#28a745"},
            "purple": {"background": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4a1a5a, stop:1 #6a2a7a)",
                       "border": "#6f42c1", "status_color": "#6f42c1"}
        }
        style = color_styles.get(self.current_color, color_styles["default"])
        if self.is_selected:
            self.setStyleSheet(f"""
                OrderChefWidget {{
                    background: {style['background']};
                    border: 3px solid {style['border']};
                    border-radius: 12px;
                }}
            """)
            self.status_label.setText("✅ ВЫБРАН")
            self.status_label.setStyleSheet(f"color: {style['status_color']}; font-size: 10pt; font-weight: bold;")
        else:
            self.setStyleSheet(f"""
                OrderChefWidget {{
                    background: #333;
                    border: 2px solid #555;
                    border-radius: 12px;
                }}
                OrderChefWidget:hover {{
                    border-color: {style['border']};
                    background: #3a3a3a;
                }}
            """)
            self.status_label.setText("⬜ НЕ ВЫБРАН")
            self.status_label.setStyleSheet("color: #888; font-size: 10pt; font-weight: bold;")


class OrderWaiterWidget(QFrame):
    """Виджет готового заказа для официанта: данные, кнопки деталей и подачи."""
    order_served = pyqtSignal(int)

    def __init__(self, order_id, order_number, table_number, customer_name, order_items, total_amount, address,
                 parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.order_number = order_number
        self.table_number = table_number
        self.customer_name = customer_name
        self.order_items = order_items
        self.total_amount = total_amount
        self.address = address
        self.setup_ui()

    def setup_ui(self):
        """Создаёт UI: заголовок, статус, адрес/стол/клиент, кратко о блюдах, сумма, кнопки."""
        self.setFixedSize(280, 320)
        self.setStyleSheet("""
            OrderWaiterWidget {
                background: #333;
                border: 3px solid #28a745;
                border-radius: 12px;
                padding: 12px;
                margin: 8px;
            }
            OrderWaiterWidget:hover {
                border-color: #ff6600;
                background: #3a3a3a;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        order_label = QLabel(f"ЗАКАЗ #{self.order_number}")
        order_label.setStyleSheet("color: #ff6600; font-size: 14pt; font-weight: bold;")
        order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(order_label)
        status_label = QLabel("✅ ГОТОВ")
        status_label.setStyleSheet("color: #28a745; font-size: 12pt; font-weight: bold;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("background: #555;")
        separator1.setFixedHeight(1)
        layout.addWidget(separator1)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        short_address = self.address[:15] + "..." if len(self.address) > 15 else self.address
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel("🏠"))
        address_label = QLabel(short_address)
        address_label.setToolTip(self.address)
        address_label.setStyleSheet("color: white; font-size: 10pt;")
        address_layout.addWidget(address_label)
        address_layout.addStretch()
        info_layout.addLayout(address_layout)
        table_layout = QHBoxLayout()
        table_layout.addWidget(QLabel("🍽️"))
        table_label = QLabel(f"Стол: {self.table_number}")
        table_label.setStyleSheet("color: white; font-size: 10pt; font-weight: bold;")
        table_layout.addWidget(table_label)
        table_layout.addStretch()
        info_layout.addLayout(table_layout)
        short_customer = self.customer_name[:12] + "..." if len(self.customer_name) > 12 else self.customer_name
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("👤"))
        customer_label = QLabel(short_customer)
        customer_label.setToolTip(self.customer_name)
        customer_label.setStyleSheet("color: #aaa; font-size: 9pt;")
        customer_layout.addWidget(customer_label)
        customer_layout.addStretch()
        info_layout.addLayout(customer_layout)
        layout.addLayout(info_layout)
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background: #555;")
        separator2.setFixedHeight(1)
        layout.addWidget(separator2)
        items_preview = QLabel(f"Блюд: {len(self.order_items)}")
        items_preview.setStyleSheet("color: #ccc; font-size: 10pt;")
        items_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(items_preview)
        total_layout = QHBoxLayout()
        total_text = QLabel("Сумма:")
        total_text.setStyleSheet("color: white; font-size: 11pt; font-weight: bold;")
        total_amount_label = QLabel(f"{self.total_amount:.0f} ₽")
        total_amount_label.setStyleSheet("color: #ff6600; font-size: 12pt; font-weight: bold;")
        total_layout.addWidget(total_text)
        total_layout.addStretch()
        total_layout.addWidget(total_amount_label)
        layout.addLayout(total_layout)
        buttons_layout = QHBoxLayout()
        details_btn = QPushButton("📋 Детали")
        details_btn.setFixedHeight(30)
        details_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        details_btn.clicked.connect(self.show_order_details)
        buttons_layout.addWidget(details_btn)
        serve_btn = QPushButton("✅ Подать")
        serve_btn.setFixedHeight(30)
        serve_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        serve_btn.clicked.connect(self.serve_order)
        buttons_layout.addWidget(serve_btn)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def show_order_details(self):
        """Открывает модальное окно с полной информацией о заказе."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Детали заказа #{self.order_number}")
        dialog.setFixedSize(500, 600)
        dialog.setStyleSheet("QDialog { background: #2d2d2d; color: white; }")
        layout = QVBoxLayout()
        title_label = QLabel(f"ЗАКАЗ #{self.order_number}")
        title_label.setStyleSheet("color: #ff6600; font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        info_text = f"<p><b>Стол:</b> {self.table_number}</p><p><b>Клиент:</b> {self.customer_name}</p><p><b>Количество блюд:</b> {len(self.order_items)}</p>"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: white; font-size: 11pt;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        items_label = QLabel("СОСТАВ ЗАКАЗА:")
        items_label.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")
        layout.addWidget(items_label)
        scroll_area = QScrollArea()
        scroll_area.setFixedHeight(300)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #555;
                border-radius: 6px;
                background: #2a2a2a;
            }
            QScrollArea QWidget {
                background: #2a2a2a;
            }
        """)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        for item in self.order_items:
            item_widget = self.create_detailed_dish_item(item[0], item[1], item[2], item[3])
            scroll_layout.addWidget(item_widget)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        total_layout = QHBoxLayout()
        total_text = QLabel("ИТОГО:")
        total_text.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")
        total_amount_label = QLabel(f"{self.total_amount:.2f} ₽")
        total_amount_label.setStyleSheet("color: #ff6600; font-size: 16pt; font-weight: bold;")
        total_layout.addWidget(total_text)
        total_layout.addStretch()
        total_layout.addWidget(total_amount_label)
        layout.addLayout(total_layout)
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: #545b62;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.setLayout(layout)
        dialog.exec()

    def create_detailed_dish_item(self, name, quantity, price, total):
        """Создаёт строку детального отображения блюда в диалоге."""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(10, 6, 10, 6)
        name_label = QLabel(f"{name} x{quantity}")
        name_label.setStyleSheet("color: white; font-size: 11pt;")
        name_label.setWordWrap(True)
        price_layout = QVBoxLayout()
        price_per_item = QLabel(f"{price:.2f} ₽/шт")
        price_per_item.setStyleSheet("color: #ccc; font-size: 9pt;")
        price_per_item.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_price = QLabel(f"{total:.2f} ₽")
        total_price.setStyleSheet("color: #ff6600; font-size: 11pt; font-weight: bold;")
        total_price.setAlignment(Qt.AlignmentFlag.AlignRight)
        price_layout.addWidget(price_per_item)
        price_layout.addWidget(total_price)
        item_layout.addWidget(name_label, 4)
        item_layout.addLayout(price_layout, 1)
        return item_widget

    def serve_order(self):
        """Запрашивает подтверждение и эмитирует сигнал подачи заказа."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что подали заказ #{self.order_number}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.order_served.emit(self.order_id)


class AdminWindow(QMainWindow):
    """Главное окно администратора: управление блюдами и пользователями."""
    def __init__(self, user_id, user_name):
        super().__init__()
        self.ui = Ui_AdminWindow()
        self.ui.setupUi(self)
        self.user_id = user_id
        self.user_name = user_name
        self.db = Database()
        self.setWindowTitle(f"Панель администратора - {user_name}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        center_window(self)
        self.current_image_path = None
        self.setup_admin_ui()
        self.load_menu()
        self.load_users()
        self.ui.add_dish_btn.clicked.connect(self.add_dish)
        self.ui.update_role_btn.clicked.connect(self.update_user_role)
        self.ui.upload_image_btn.clicked.connect(self.upload_image)
        self.ui.clear_image_btn.clicked.connect(self.clear_image)
        if hasattr(self.ui, 'logout_btn'):
            self.ui.logout_btn.clicked.connect(self.logout)

    def setup_admin_ui(self):
        """Настройка внешнего вида таблиц (растягивание, поведение выделения)."""
        if hasattr(self.ui, 'menu_table'):
            h = self.ui.menu_table.horizontalHeader()
            h.setStretchLastSection(True)
            self.ui.menu_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        if hasattr(self.ui, 'users_table'):
            h = self.ui.users_table.horizontalHeader()
            h.setStretchLastSection(True)
            self.ui.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

    def upload_image(self):
        """Открывает диалог выбора изображения, копирует его в папку `images`, сохраняет путь."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение блюда", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif);;Все файлы (*)"
        )
        if not file_path:
            return
        try:
            os.makedirs("images", exist_ok=True)
            ext = os.path.splitext(file_path)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            new_filename = f"dish_{timestamp}{ext}"
            target_path = os.path.join("images", new_filename)
            shutil.copy2(file_path, target_path)
            self.current_image_path = target_path
            pixmap = QPixmap(target_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(240, 190, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                self.ui.image_preview_label.setPixmap(scaled)
                self.ui.image_preview_label.setText("")
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            self.current_image_path = None
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение")

    def clear_image(self):
        """Очищает превью изображения и сбрасывает путь к файлу."""
        self.current_image_path = None
        self.ui.image_preview_label.clear()
        self.ui.image_preview_label.setText("Превью изображения\n(250x200)")

    def load_menu(self):
        """Загружает список блюд из БД и отображает в таблице."""
        menu_items = self.db.get_menu_items()
        if not hasattr(self.ui, 'menu_table'):
            return
        table = self.ui.menu_table
        table.setSortingEnabled(True)
        table.setRowCount(len(menu_items))
        table.setHorizontalHeaderLabels(['ID', 'Название', 'Описание', 'Цена', 'Изображение', 'Действия'])
        for row, item in enumerate(menu_items):
            table.setItem(row, 0, QTableWidgetItem(str(item[0])))
            table.setItem(row, 1, QTableWidgetItem(item[1]))
            desc = (item[2][:100] + "...") if len(item[2]) > 100 else item[2]
            table.setItem(row, 2, QTableWidgetItem(desc))
            table.setItem(row, 3, QTableWidgetItem(f"{item[3]:.2f} руб."))
            table.setItem(row, 4, QTableWidgetItem("✅" if item[4] else "❌"))
            btn = QPushButton("Удалить")
            btn.setFixedSize(175, 30)
            btn.setStyleSheet("""
                QPushButton {
                    background: #dc3545; color: white; border: none;
                    border-radius: 8px; padding: 8px 12px; font-size: 10pt; font-weight: bold;
                }
                QPushButton:hover { background: #c82333; }
                QPushButton:pressed { background: #bd2130; }
            """)
            btn.clicked.connect(lambda _, id=item[0]: self.delete_dish(id))
            table.setCellWidget(row, 5, btn)
        widths = [50, 180, 280, 100, 100, 120]
        for i, w in enumerate(widths):
            table.setColumnWidth(i, w)
        table.verticalHeader().setDefaultSectionSize(45)
        table.viewport().update()

    def load_users(self):
        """Загружает список пользователей из БД и отображает в таблице."""
        users = self.db.get_all_users()
        if not hasattr(self.ui, 'users_table'):
            return
        table = self.ui.users_table
        table.setSortingEnabled(True)
        table.setRowCount(len(users))
        table.setHorizontalHeaderLabels(['ID', 'Имя', 'Email', 'Роль'])
        for row, user in enumerate(users):
            table.setItem(row, 0, QTableWidgetItem(str(user[0])))
            table.setItem(row, 1, QTableWidgetItem(user[1]))
            table.setItem(row, 2, QTableWidgetItem(user[2]))
            role_item = QTableWidgetItem(user[5])
            color_map = {'admin': '#ff6600', 'chef': '#28a745', 'waiter': '#007bff'}
            role_item.setForeground(QColor(color_map.get(user[5], '#6c757d')))
            table.setItem(row, 3, role_item)
        for i, w in enumerate([50, 200, 250, 150]):
            table.setColumnWidth(i, w)

    def add_dish(self):
        """Добавляет новое блюдо в базу данных с валидацией полей."""
        name = self.ui.dish_name_input.text().strip()
        desc = self.ui.dish_desc_input.toPlainText().strip()
        price_text = self.ui.dish_price_input.text().replace(',', '.').strip()
        if not name or not desc:
            QMessageBox.warning(self, "Ошибка", "Заполните название и описание")
            return
        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректная цена")
            return
        fields = [self.ui.grams_input, self.ui.calories_input, self.ui.proteins_input,
                  self.ui.fats_input, self.ui.carbs_input]
        try:
            nums = [float(f.text().strip() or 0) for f in fields]
            nums[0] = int(nums[0])
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Проверьте числовые поля")
            return
        composition = self.ui.composition_input.toPlainText().strip()
        success = self.db.add_menu_item(
            name, desc, price, self.current_image_path, *nums, composition
        )
        if success:
            self.ui.dish_name_input.clear()
            self.ui.dish_desc_input.clear()
            self.ui.dish_price_input.clear()
            self.clear_nutrition_fields()
            self.clear_image()
            self.load_menu()
            QMessageBox.information(self, "Успех", "Блюдо добавлено!")
        else:
            QMessageBox.warning(self, "Ошибка", "Блюдо с таким названием уже существует.")

    def clear_nutrition_fields(self):
        """Очищает поля ввода БЖУ и состава."""
        for f in [self.ui.grams_input, self.ui.calories_input, self.ui.proteins_input,
                  self.ui.fats_input, self.ui.carbs_input, self.ui.composition_input]:
            f.clear()

    def delete_dish(self, dish_id):
        """Удаляет блюдо из базы данных после подтверждения."""
        dish_name = next((item[1] for item in self.db.get_menu_items() if item[0] == dish_id), "")
        if QMessageBox.question(self, "Подтверждение",
                                f"Удалить блюдо '{dish_name}'?") == QMessageBox.StandardButton.Yes:
            if self.db.delete_menu_item(dish_id):
                self.load_menu()
                QMessageBox.information(self, "Успех", f"'{dish_name}' удалено!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить блюдо")

    def update_user_role(self):
        """Обновляет роль выбранного пользователя."""
        row = self.ui.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
        user_id = int(self.ui.users_table.item(row, 0).text())
        user_name = self.ui.users_table.item(row, 1).text()
        roles = {self.ui.admin_radio: 'admin', self.ui.chef_radio: 'chef',
                 self.ui.waiter_radio: 'waiter'}
        new_role = next((r for btn, r in roles.items() if btn.isChecked()), 'customer')
        if QMessageBox.question(self, "Подтверждение",
                                f"Изменить роль {user_name} на '{new_role}'?") == QMessageBox.StandardButton.Yes:
            if self.db.update_user_role(user_id, new_role):
                self.load_users()
                QMessageBox.information(self, "Успех", f"Роль обновлена!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить роль")

    def logout(self):
        """Закрывает окно администратора и открывает окно авторизации."""
        self.close()
        self.auth_window = AuthWindow()
        self.auth_window.show()

    def keyPressEvent(self, event):
        """Обрабатывает нажатие F11 для переключения полноэкранного режима."""
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)


class UserWindow(QMainWindow):
    """Главное окно клиента: меню, корзина, история заказов."""
    def __init__(self, user_id, user_name):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name
        self.db = Database()
        self.setWindowTitle(f"Куриный Жокей - {user_name}")
        self.setMinimumSize(900, 500)
        self.resize(1200, 600)
        center_window(self)
        self.setup_custom_ui()
        self.checkout_btn.clicked.connect(self.checkout)
        self.remove_from_cart_btn.clicked.connect(self.remove_from_cart)
        self.order_history_btn.clicked.connect(self.show_order_history)
        self.back_to_menu_btn.clicked.connect(self.show_main_view)
        self.logout_btn.clicked.connect(self.logout)
        self.load_menu()
        self.load_cart()

    def setup_custom_ui(self):
        """Создаёт кастомный интерфейс: меню слева, корзина справа, стек виджетов."""
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)
        left_layout.addWidget(QLabel("МЕНЮ"))
        menu_scroll = QScrollArea()
        menu_scroll.setWidgetResizable(True)
        self.menu_container = QWidget()
        self.menu_grid_layout = QGridLayout(self.menu_container)
        self.menu_grid_layout.setSpacing(12)
        self.menu_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        menu_scroll.setWidget(self.menu_container)
        left_layout.addWidget(menu_scroll)
        self.order_history_btn = QPushButton("История заказов")
        self.order_history_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff6600;
                border: 2px solid #ff6600;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 102, 0, 0.1);
            }
        """)
        left_layout.addWidget(self.order_history_btn)
        main_layout.addWidget(left_widget, 2)
        right_widget = QWidget()
        right_widget.setMinimumWidth(300)
        right_widget.setMaximumWidth(520)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(12)
        right_layout.addWidget(QLabel("КОРЗИНА"))
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(3)
        self.cart_table.setHorizontalHeaderLabels(['Название', 'Кол-во', 'Сумма'])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cart_table.setColumnWidth(0, 100)
        self.cart_table.setColumnWidth(1, 80)
        self.cart_table.setColumnWidth(2, 50)
        self.cart_table.setStyleSheet("""
            QTableWidget {
                background: #333;
                border: 1px solid #555;
                border-radius: 6px;
                gridline-color: #555;
                color: white;
                font-size: 11pt;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #555;
                font-size: 11pt;
            }
            QHeaderView::section {
                background: #ff6600;
                color: white;
                padding: 10px;
                border: none;
                font-size: 11pt;
                font-weight: bold;
            }
        """)
        right_layout.addWidget(self.cart_table)
        self.total_label = QLabel("Итого: 0.00 руб.")
        self.total_label.setStyleSheet("""
            color: #ff6600; 
            font-size: 16pt; 
            font-weight: bold;
            text-align: center;
            padding: 12px;
            border: 2px solid #ff6600;
            border-radius: 6px;
            background: rgba(255, 102, 0, 0.1);
        """)
        right_layout.addWidget(self.total_label)
        cart_buttons_layout = QHBoxLayout()
        self.remove_from_cart_btn = QPushButton("Удалить")
        self.remove_from_cart_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        self.checkout_btn = QPushButton("Оплатить")
        self.checkout_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        cart_buttons_layout.addWidget(self.remove_from_cart_btn)
        cart_buttons_layout.addWidget(self.checkout_btn)
        right_layout.addLayout(cart_buttons_layout)
        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: #545b62;
            }
        """)
        right_layout.addWidget(self.logout_btn)
        main_layout.addWidget(right_widget, 1)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(central_widget)
        self.stacked_widget.addWidget(self.create_history_page())
        self.setCentralWidget(self.stacked_widget)

    def create_history_page(self):
        """Создаёт страницу истории заказов с кнопкой возврата."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        layout.addWidget(QLabel("ИСТОРИЯ ЗАКАЗОВ"))
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setSpacing(10)
        scroll_area.setWidget(self.history_container)
        layout.addWidget(scroll_area)
        self.back_to_menu_btn = QPushButton("Вернуться к меню")
        self.back_to_menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff6600;
                border: 2px solid #ff6600;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 102, 0, 0.1);
            }
        """)
        layout.addWidget(self.back_to_menu_btn)
        return page

    def load_menu(self):
        """Загружает блюда из БД и отображает их карточками в сетке 3×N."""
        for i in reversed(range(self.menu_grid_layout.count())):
            widget = self.menu_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        menu_items = self.db.get_menu_items()
        columns = 3
        self.menu_grid_layout.setHorizontalSpacing(15)
        self.menu_grid_layout.setVerticalSpacing(20)
        self.menu_grid_layout.setContentsMargins(20, 10, 20, 10)
        row = col = 0
        for item in menu_items:
            widget = DishWidget(
                item[0], item[1], item[2], item[3], item[4],
                item[5] if len(item) > 5 else 0,
                item[6] if len(item) > 6 else 0,
                item[7] if len(item) > 7 else 0,
                item[8] if len(item) > 8 else 0,
                item[9] if len(item) > 9 else 0,
                item[10] if len(item) > 10 else ""
            )
            widget.add_to_cart.connect(self.add_dish_to_cart)
            self.menu_grid_layout.addWidget(widget, row, col, alignment=Qt.AlignmentFlag.AlignCenter)
            col += 1
            if col >= columns:
                col = 0
                row += 1
        for i in range(columns):
            self.menu_grid_layout.setColumnStretch(i, 1)
        self.menu_grid_layout.setRowStretch(row + 1, 1)

    def add_dish_to_cart(self, dish_id, quantity):
        """Добавляет блюдо в корзину и показывает уведомление."""
        if self.db.add_to_cart(self.user_id, dish_id, quantity):
            self.load_cart()
            self.show_cart_notification("Блюдо добавлено в корзину!")
        else:
            self.show_cart_notification("Не удалось добавить блюдо", error=True)

    def show_cart_notification(self, message, error=False):
        """Показывает временное уведомление в `total_label` (зелёное/красное)."""
        color = "#dc3545" if error else "#28a745"
        self.total_label.setStyleSheet(f"""
            color: {color}; 
            font-size: 16pt; 
            font-weight: bold;
            text-align: center;
            padding: 12px;
            border: 2px solid {color};
            border-radius: 6px;
            background: rgba(40, 167, 69, 0.1);
        """)
        self.total_label.setText(message)
        QTimer.singleShot(2000, self.update_total_display)

    def load_cart(self):
        """Загружает содержимое корзины из БД и отображает в таблице."""
        cart_items = self.db.get_cart(self.user_id)
        self.cart_table.setRowCount(len(cart_items))
        total = 0
        for row, item in enumerate(cart_items):
            self.cart_table.setItem(row, 0, QTableWidgetItem(item[2]))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(item[4])))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"{item[5]:.2f} ₽"))
            total += item[5]
        self.update_total_display(total)

    def update_total_display(self, total=None):
        """Обновляет метку итоговой суммы корзины."""
        if total is None:
            cart_items = self.db.get_cart(self.user_id)
            total = sum(item[5] for item in cart_items)
        self.total_label.setStyleSheet("""
            color: #ff6600; 
            font-size: 16pt; 
            font-weight: bold;
            text-align: center;
            padding: 12px;
            border: 2px solid #ff6600;
            border-radius: 6px;
            background: rgba(255, 102, 0, 0.1);
        """)
        self.total_label.setText(f"Итого: {total:.2f} ₽")

    def remove_from_cart(self):
        """Удаляет выбранную строку из корзины после подтверждения."""
        row = self.cart_table.currentRow()
        if row >= 0:
            dish_name = self.cart_table.item(row, 0).text()
            if QMessageBox.question(self, "Подтверждение",
                                    f"Удалить '{dish_name}' из корзины?") == QMessageBox.StandardButton.Yes:
                cart_items = self.db.get_cart(self.user_id)
                if row < len(cart_items):
                    self.db.remove_from_cart(cart_items[row][0])
                    self.load_cart()
                    self.show_cart_notification("Товар удален из корзины!")

    def show_main_view(self):
        """Переключает стек на основное меню."""
        self.stacked_widget.setCurrentIndex(0)

    def show_order_history(self):
        """Загружает и отображает историю заказов на отдельной странице."""
        for i in reversed(range(self.history_layout.count())):
            widget = self.history_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        orders = self.db.get_user_orders(self.user_id)
        if not orders:
            label = QLabel("У вас пока нет заказов")
            label.setStyleSheet("color: white; font-size: 12pt; text-align: center;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_layout.addWidget(label)
        else:
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(15)
            grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row = col = 0
            for order in orders:
                items = self.db.get_order_items(order[0])
                widget = OrderHistoryWidget(order[7], order[4], order[6], order[8], items)
                grid_layout.addWidget(widget, row, col, alignment=Qt.AlignmentFlag.AlignCenter)
                col = (col + 1) % 3
                if col == 0:
                    row += 1
            self.history_layout.addWidget(grid_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.setCurrentIndex(1)

    def checkout(self):
        """Открывает окно оплаты, если корзина не пуста."""
        if not self.db.get_cart(self.user_id):
            self.show_cart_notification("Корзина пуста", error=True)
            return
        self.payment_window = PaymentWindow(self.user_id, self.db)
        self.payment_window.order_placed.connect(self.on_order_placed)
        self.payment_window.show()

    def on_order_placed(self, order_number, order_id):
        """Обрабатывает успешное оформление заказа: обновляет корзину и показывает трекинг."""
        self.show_cart_notification(f"Заказ #{order_number} оформлен!")
        self.load_cart()
        orders = self.db.get_user_orders(self.user_id)
        if orders:
            order_items = self.db.get_order_items(order_id)
            dialog = OrderTrackingDialog(order_number, orders[0][4], order_items, orders[0][6], self)
            dialog.exec()

    def logout(self):
        """Закрывает окно клиента и открывает окно авторизации."""
        self.close()
        self.auth_window = AuthWindow()
        self.auth_window.show()

    def keyPressEvent(self, event):
        """Обрабатывает нажатие F11 для переключения полноэкранного режима."""
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)


class ChefWindow(QMainWindow):
    """Окно повара: отображение и выбор заказов, раскраска, передача официанту."""
    def __init__(self, user_id, user_name):
        super().__init__()
        self.ui = Ui_ChefWindow()
        self.ui.setupUi(self)
        self.user_id = user_id
        self.user_name = user_name
        self.db = Database()
        self.setWindowTitle(f"Панель повара - {user_name}")
        center_window(self)
        self.selected_orders = set()
        self.order_colors = {}
        self.setup_chef_ui()
        self.load_addresses()
        self.load_orders()
        if hasattr(self.ui, 'restaurant_combo'):
            self.ui.restaurant_combo.currentIndexChanged.connect(self.load_orders)
        if hasattr(self.ui, 'mark_prepared_btn'):
            self.ui.mark_prepared_btn.clicked.connect(self.mark_selected_as_prepared)
        if hasattr(self.ui, 'logout_btn'):
            self.ui.logout_btn.clicked.connect(self.logout)

    def setup_chef_ui(self):
        """Инициализирует прокручиваемую сетку для отображения заказов."""
        self.orders_grid_layout = QGridLayout()
        self.orders_grid_layout.setSpacing(20)
        self.orders_grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orders_container = QWidget()
        orders_container.setLayout(self.orders_grid_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(orders_container)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea QWidget {
                background: transparent;
            }
        """)
        if hasattr(self.ui, 'orders_layout'):
            for i in reversed(range(self.ui.orders_layout.count())):
                widget = self.ui.orders_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            self.ui.orders_layout.addWidget(scroll_area)

    def load_addresses(self):
        """Загружает список точек (адресов) в выпадающий список."""
        addresses = self.db.get_addresses()
        if hasattr(self.ui, 'restaurant_combo'):
            self.ui.restaurant_combo.clear()
            for addr in addresses:
                self.ui.restaurant_combo.addItem(addr[1], addr[0])

    def load_orders(self):
        """Загружает активные заказы (со статусом 'sent_to_kitchen') и отображает их."""
        self.clear_orders_layout()
        self.selected_orders.clear()
        address_id = self.ui.restaurant_combo.currentData() if hasattr(self.ui,
                                                                       'restaurant_combo') and self.ui.restaurant_combo.currentData() else None
        orders = self.db.get_orders_by_status('sent_to_kitchen', address_id)
        if not orders:
            self.show_no_orders_message()
            return
        row = col = 0
        for order in orders:
            order_items = self.db.get_order_items(order[0])
            widget = OrderChefWidget(order[0], order[7], order[3], order[9], order_items, order[6])
            widget.order_toggled.connect(self.on_order_toggled)
            widget.color_changed.connect(self.on_order_color_changed)
            if order[0] in self.order_colors:
                widget.set_color(self.order_colors[order[0]])
            self.orders_grid_layout.addWidget(widget, row, col)
            col = (col + 1) % 3
            if col == 0:
                row += 1
        self.update_prepare_button()

    def on_order_color_changed(self, order_id, color):
        """Обновляет словарь цветов заказов при изменении цвета в виджете."""
        self.order_colors[order_id] = color

    def clear_orders_layout(self):
        """Очищает сетку заказов."""
        for i in reversed(range(self.orders_grid_layout.count())):
            widget = self.orders_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def show_no_orders_message(self):
        """Отображает сообщение об отсутствии заказов."""
        label = QLabel("НЕТ ЗАКАЗОВ ДЛЯ ПРИГОТОВЛЕНИЯ")
        label.setStyleSheet("color: #28a745; font-size: 18pt; font-weight: bold; text-align: center; padding: 50px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orders_grid_layout.addWidget(label, 0, 0, 1, 3)

    def show_error_message(self):
        """Отображает сообщение об ошибке загрузки (в текущем коде не используется)."""
        label = QLabel("❌ ОШИБКА ЗАГРУЗКИ ЗАКАЗОВ")
        label.setStyleSheet("color: #dc3545; font-size: 16pt; font-weight: bold; text-align: center; padding: 50px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orders_grid_layout.addWidget(label, 0, 0, 1, 3)

    def on_order_toggled(self, order_id, is_selected):
        """Обновляет множество выбранных заказов и кнопку передачи."""
        (self.selected_orders.add if is_selected else self.selected_orders.discard)(order_id)
        self.update_prepare_button()

    def update_prepare_button(self):
        """Обновляет текст и состояние кнопки «передать официанту»."""
        if not hasattr(self.ui, 'mark_prepared_btn'):
            return
        if self.selected_orders:
            self.ui.mark_prepared_btn.setText(f"ПЕРЕДАТЬ ОФИЦИАНТУ ({len(self.selected_orders)})")
            self.ui.mark_prepared_btn.setEnabled(True)
        else:
            self.ui.mark_prepared_btn.setText("ПЕРЕДАТЬ ОФИЦИАНТУ")
            self.ui.mark_prepared_btn.setEnabled(False)

    def mark_selected_as_prepared(self):
        """Меняет статус выбранных заказов на 'ready_for_serving'."""
        if not self.selected_orders:
            return
        for order_id in list(self.selected_orders):
            if self.db.update_order_status(order_id, 'ready_for_serving'):
                self.order_colors.pop(order_id, None)
        self.load_orders()

    def logout(self):
        """Закрывает окно повара и открывает окно авторизации."""
        self.close()
        self.auth_window = AuthWindow()
        self.auth_window.show()


class WaiterWindow(QMainWindow):
    """Окно официанта: отображение готовых заказов, подтверждение подачи."""
    def __init__(self, user_id, user_name):
        super().__init__()
        self.ui = Ui_WaiterWindow()
        self.ui.setupUi(self)
        self.user_id = user_id
        self.user_name = user_name
        self.db = Database()
        self.setWindowTitle(f"Панель официанта - {user_name}")
        center_window(self)
        self.setup_waiter_ui()
        self.load_addresses()
        self.load_orders()
        if hasattr(self.ui, 'restaurant_combo'):
            self.ui.restaurant_combo.currentIndexChanged.connect(self.load_orders)
        if hasattr(self.ui, 'logout_btn'):
            self.ui.logout_btn.clicked.connect(self.logout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_orders)
        self.timer.start(10000)

    def setup_waiter_ui(self):
        """Подготавливает UI: заменяет таблицу на прокручиваемую сетку."""
        if hasattr(self.ui, 'orders_table'):
            self.ui.orders_table.setVisible(False)
        if hasattr(self.ui, 'mark_served_btn'):
            self.ui.mark_served_btn.setVisible(False)
        self.orders_grid_layout = QGridLayout()
        self.orders_grid_layout.setSpacing(10)
        self.orders_grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orders_container = QWidget()
        orders_container.setLayout(self.orders_grid_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(orders_container)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea QWidget {
                background: transparent;
            }
        """)
        if hasattr(self.ui, 'verticalLayout'):
            layout = self.ui.verticalLayout
            for i in range(layout.count()):
                if layout.itemAt(i).widget() == self.ui.orders_table:
                    layout.removeItem(layout.itemAt(i))
                    layout.insertWidget(i, scroll_area)
                    break

    def load_addresses(self):
        """Загружает список точек (включая «Все заведения») в выпадающий список."""
        addresses = self.db.get_addresses()
        if hasattr(self.ui, 'restaurant_combo'):
            self.ui.restaurant_combo.clear()
            self.ui.restaurant_combo.addItem("Все заведения", None)
            for addr in addresses:
                self.ui.restaurant_combo.addItem(addr[1], addr[0])

    def load_orders(self):
        """Загружает заказы со статусом 'ready_for_serving' и отображает их."""
        self.clear_orders_layout()
        address_id = self.ui.restaurant_combo.currentData() if hasattr(self.ui,
                                                                       'restaurant_combo') and self.ui.restaurant_combo.currentData() else None
        orders = self.db.get_orders_by_status('ready_for_serving', address_id)
        if not orders:
            self.show_no_orders_message()
            return
        row = col = 0
        for order in orders:
            items = self.db.get_order_items(order[0])
            address = order[10] if len(order) > 10 else "Основной зал"
            widget = OrderWaiterWidget(order[0], order[7], order[3], order[9], items, order[6], address)
            widget.order_served.connect(self.mark_as_completed)
            self.orders_grid_layout.addWidget(widget, row, col)
            col = (col + 1) % 3
            if col == 0:
                row += 1

    def clear_orders_layout(self):
        """Очищает сетку заказов."""
        for i in reversed(range(self.orders_grid_layout.count())):
            widget = self.orders_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def show_no_orders_message(self):
        """Показывает сообщение об отсутствии готовых к подаче заказов."""
        label = QLabel("НЕТ ЗАКАЗОВ ДЛЯ ПОДАЧИ")
        label.setStyleSheet("color: #28a745; font-size: 18pt; font-weight: bold; text-align: center; padding: 50px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orders_grid_layout.addWidget(label, 0, 0, 1, 3)

    def show_error_message(self):
        """Показывает сообщение об ошибке (в текущем коде не используется)."""
        label = QLabel("❌ ОШИБКА ЗАГРУЗКИ ЗАКАЗОВ")
        label.setStyleSheet("color: #dc3545; font-size: 16pt; font-weight: bold; text-align: center; padding: 50px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orders_grid_layout.addWidget(label, 0, 0, 1, 3)

    def mark_as_completed(self, order_id):
        """Меняет статус заказа на 'completed' после подачи."""
        if self.db.update_order_status(order_id, 'completed'):
            self.load_orders()

    def logout(self):
        """Останавливает автообновление, закрывает окно и открывает авторизацию."""
        self.timer.stop()
        self.close()
        self.auth_window = AuthWindow()
        self.auth_window.show()


class PaymentWindow(QMainWindow):
    """Окно оплаты: выбор точки, стола, способа оплаты и подтверждение."""
    order_placed = pyqtSignal(str, int)

    def __init__(self, user_id, db):
        super().__init__()
        self.ui = Ui_PaymentWindow()
        self.ui.setupUi(self)
        self.user_id = user_id
        self.db = db
        self.setWindowTitle("Оплата заказа")
        self.load_addresses()
        self.load_order_summary()
        self.ui.pay_btn.clicked.connect(self.process_payment)
        self.ui.cancel_btn.clicked.connect(self.close)
        self.add_address_info()

    def add_address_info(self):
        """Добавляет список адресов под способами оплаты для информативности."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Наши адреса:"))
        for addr in self.db.get_addresses():
            layout.addWidget(QLabel(f"🏠 {addr[1]}"))
        if hasattr(self.ui, 'verticalLayout'):
            self.ui.verticalLayout.insertWidget(2, widget)

    def load_addresses(self):
        """Заполняет выпадающий список точек (адресов)."""
        if hasattr(self.ui, 'restaurant_combo'):
            self.ui.restaurant_combo.clear()
            for addr in self.db.get_addresses():
                self.ui.restaurant_combo.addItem(addr[1], addr[0])

    def load_order_summary(self):
        """Отображает итоговую сумму заказа в метке."""
        cart = self.db.get_cart(self.user_id)
        total = sum(item[5] for item in cart)
        if hasattr(self.ui, 'total_amount_label'):
            self.ui.total_amount_label.setText(f"{total:.2f} руб.")

    def process_payment(self):
        """Создаёт заказ в БД и эмитирует сигнал `order_placed` при успехе."""
        try:
            cart_items = self.db.get_cart(self.user_id)
            if not cart_items:
                return
            total = sum(item[5] for item in cart_items)
            address_id = self.ui.restaurant_combo.currentData() if hasattr(self.ui,
                                                                           'restaurant_combo') and self.ui.restaurant_combo.currentData() else 1
            table = self.ui.table_spin.value() if hasattr(self.ui, 'table_spin') else 1
            method = self.ui.payment_method_combo.currentText() if hasattr(self.ui,
                                                                           'payment_method_combo') else "Наличные"
            order_id, order_number = self.db.create_order(self.user_id, address_id, table, method, total)
            if order_id and order_number:
                self.order_placed.emit(order_number, order_id)
                self.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать заказ")
        except Exception as e:
            print(f"Ошибка в process_payment: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось оформить заказ:\n{str(e)}")


class AuthWindow(QMainWindow):
    """Окно авторизации и регистрации: вход по email+пароль, регистрация нового пользователя."""
    def __init__(self):
        super().__init__()
        self.ui = Ui_AuthWindow()
        self.ui.setupUi(self)
        self.db = Database()
        self.setMinimumSize(400, 600)
        self.resize(400, 600)
        self._setup_centered_layout()
        self._center_page_contents()

        # ✅ Добавляем маску ТОЛЬКО на телефон (в регистрации)
        self.ui.register_phone_input.setInputMask("+7 (999) 999-99-99;_")

        # ✅ Опционально: подсказка в email-поле (не маска!)
        self.ui.register_email_input.setPlaceholderText("user@domain.com или .ru")

        self.ui.login_btn.clicked.connect(self.login)
        self.ui.register_btn.clicked.connect(self.show_register)
        self.ui.back_to_login_btn.clicked.connect(self.show_login)
        self.ui.register_submit_btn.clicked.connect(self.register)
        self.show_login()

    def _setup_centered_layout(self):
        """Центрирует основной layout окна вертикально и горизонтально."""
        central = self.centralWidget()
        layout = central.layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if isinstance(item, QSpacerItem):
                layout.removeItem(item)
        top_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.insertItem(0, top_spacer)
        layout.addItem(bottom_spacer)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    def _center_page_contents(self):
        """Центрирует содержимое страниц «вход» и «регистрация» по центру окна."""
        for page_name, page in [("login", self.ui.login_page), ("register", self.ui.register_page)]:
            current_layout = page.layout()
            if not current_layout:
                continue
            wrapper_layout = QVBoxLayout()
            wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            wrapper_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
            horizontal_wrapper = QHBoxLayout()
            horizontal_wrapper.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            content_widget = QWidget()
            content_widget.setLayout(current_layout)
            content_widget.setFixedWidth(300)
            horizontal_wrapper.addWidget(content_widget)
            horizontal_wrapper.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            horizontal_container = QWidget()
            horizontal_container.setLayout(horizontal_wrapper)
            wrapper_layout.addWidget(horizontal_container)
            wrapper_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
            page.setLayout(wrapper_layout)

    def show_login(self):
        """Переключает стек на страницу входа."""
        self.ui.stackedWidget.setCurrentIndex(0)

    def show_register(self):
        """Переключает стек на страницу регистрации."""
        self.ui.stackedWidget.setCurrentIndex(1)

    def login(self):
        """Вход без каких-либо проверок — только чтобы поля не были пустыми."""
        email = self.ui.email_input.text().strip()
        password = self.ui.password_input.text()
        if not email or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        user = self.db.get_user_by_email(email)
        if user and user[4] == password:
            self.user_id = user[0]
            self.user_name = user[1]
            self.user_role = user[5]
            print(f"Успешный вход: {self.user_name} ({self.user_role})")
            if self.user_role == 'admin':
                self.main_window = AdminWindow(self.user_id, self.user_name)
            elif self.user_role == 'chef':
                self.main_window = ChefWindow(self.user_id, self.user_name)
            elif self.user_role == 'waiter':
                self.main_window = WaiterWindow(self.user_id, self.user_name)
            else:
                self.main_window = UserWindow(self.user_id, self.user_name)
            self.main_window.show()
            self.hide()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный email или пароль")

    def register(self):
        """Регистрация с проверкой пароля (≥6), телефона (через маску) и email (.ru/.com)."""
        name = self.ui.register_name_input.text().strip()
        email = self.ui.register_email_input.text().strip()
        phone = self.ui.register_phone_input.text().strip()
        password = self.ui.register_password_input.text()
        confirm = self.ui.register_confirm_input.text()

        if not all([name, email, phone, password, confirm]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        # ✅ Пароль ≥6 символов — ТОЛЬКО при регистрации
        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать не менее 6 символов")
            return

        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return

        # ✅ Валидация email: должен содержать @ и оканчиваться на .ru или .com (регистронезависимо)
        if "@" not in email:
            QMessageBox.warning(self, "Ошибка", "Email должен содержать символ '@'")
            return
        if not (email.lower().endswith(".ru") or email.lower().endswith(".com")):
            QMessageBox.warning(self, "Ошибка", "Email должен оканчиваться на '.ru' или '.com'")
            return

        # ✅ Валидация телефона из маски
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 11 or not digits.startswith('7'):
            QMessageBox.warning(self, "Ошибка", "Некорректный номер телефона. Используйте формат +7 (999) 999-99-99")
            return

        if self.db.create_user(name, email, phone, password):
            QMessageBox.information(self, "Успех", "Регистрация прошла успешно!")
            self.show_login()
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким email уже существует")

    def keyPressEvent(self, event: QKeyEvent):
        """Поддержка F11 (полноэкранный режим) и Esc для выхода из него."""
        key = event.key()
        if key == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif key == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(event)


class MainApp:
    """Класс запуска приложения: инициализация QApplication и AuthWindow."""
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.auth_window = AuthWindow()

    def run(self):
        """Показывает окно авторизации и запускает цикл событий."""
        self.auth_window.show()
        return self.app.exec()


if __name__ == "__main__":
    try:
        sys.exit(MainApp().run())
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        QMessageBox.critical(None, "Ошибка", f"Не удалось запустить приложение: {e}")