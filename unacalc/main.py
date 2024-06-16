import sys
import pint
import numpy as np
from pyparsing import Word, alphas, nums, oneOf, infixNotation, opAssoc, Group, ParserElement, Combine, Optional
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QGridLayout, QLabel, QMenuBar, QAction, QMessageBox, QComboBox, QRadioButton, QButtonGroup, QSlider
from PyQt5.QtGui import QFont, QPalette, QColor, QKeySequence
from PyQt5.QtCore import Qt, QPropertyAnimation, QVariantAnimation, QTimer

VERSION = "1.0.1"

ureg = pint.UnitRegistry()
ureg.default_preferred_units = [ureg.s, ureg.m, ureg.kg, ureg.W, ureg.Wh]
ureg.default_format = '~'
ureg.default_format = '.3f~'

ParserElement.enablePackrat()

class CustomButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_color = QColor("#e1e1e1")
        self.hover_color = QColor("#d1d1d1")
        self.pressed_color = QColor("#a6a6a6")
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)
        self.set_color(self.default_color)

    def set_color(self, color):
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color.name()};
                color: #333333;
                font-size: 18px;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
            }}
            QPushButton:pressed {{
                background-color: #a6a6a6;
            }}
            """
        )

    def animate_color(self, start_color, end_color, duration):
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(duration)
        self.animation.setStartValue(start_color)
        self.animation.setEndValue(end_color)
        self.animation.valueChanged.connect(lambda value: self.set_color(value))
        self.animation.start()

    def enterEvent(self, event):
        self.animate_color(self.default_color, self.hover_color, 50)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_color(self.hover_color, self.default_color, 50)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.animate_color(self.hover_color, self.pressed_color, 100)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.animate_color(self.pressed_color, self.hover_color, 100)
        self.clearFocus()

class ExpressionConstant:
    def __init__(self, name):
        self.name = name
    def pint(self):
        if hasattr(self, 'obj'):
            return self.obj
        if self.name == 'c':
            self.obj = ureg.Quantity("speed_of_light")
        self.obj = ureg.Quantity(self.name)
        return self.pint()
    def __repr__(self):
        return f"ExpressionConstant({self.name})"

class ExpressionElement:
    def __init__(self, value, unit):
        self.value = value
        if isinstance(value, str):
            if '.' in self.value:
                self.value = float(self.value)
            else:
                self.value = int(self.value)
        self.unit = unit and unit.replace('µ', 'u')
        self.obj = ureg.Quantity(self.value, self.unit)
    def set_unit(self, unit):
        return ExpressionElement(self.value, unit)
    def __repr__(self):
        unitstr = " "+self.unit if self.unit else ''
        return f"EE({self.value}{unitstr})"

integer = Combine(Optional(oneOf('+ -')) + Word(nums)).setParseAction(lambda t: int(t[0]))
float_number = Combine(
    Optional(oneOf('+ -')) + ((Optional(Word(nums)) + '.' + Word(nums)) | (Word(nums) + '.'))
).setParseAction(lambda t: float(t[0]))
scientific_number = Combine(Optional(oneOf('+ -')) + Word(nums) + Optional('.') + Optional(Word(nums)) + oneOf("e E") + Optional(oneOf('+ -')) + Word(nums)).setParseAction(lambda t: float(t[0]))
number = scientific_number | float_number | integer

unit = Word(alphas)
value_without_unit = number.setParseAction(lambda t: ExpressionElement(t[0], None))
value_with_unit = Group(number + unit).setParseAction(lambda t: t[0][0].set_unit(t[0][1]))

constant = Word(alphas + "_").setParseAction(lambda t: [ExpressionConstant(t[0])])

operand = value_with_unit | value_without_unit | constant

plus = oneOf('+ -')
mult = oneOf('* /')
exp = oneOf('^ **')

expr = infixNotation(
    operand,
    [
        (exp, 2, opAssoc.RIGHT),
        (mult, 2, opAssoc.LEFT),
        (plus, 2, opAssoc.LEFT),
    ]
)

def parse_expression(expression):
    return expr.parseString(expression, parseAll=True).asList()

class Expression:
    def __init__(self, expr):
        self.parsed_expression = parse_expression(expr)[0]
        self.parsed_expression = self.parsed_expression
    
    def evaluate(self):
        result = self._evaluate_expression(self.parsed_expression)
        return result.to_preferred(ureg.default_preferred_units)
    
    def _evaluate_expression(self, expr):
        if isinstance(expr, ExpressionConstant):
            return expr.pint()
        if isinstance(expr, ExpressionElement):
            return expr.obj
        if isinstance(expr, pint.Quantity):
            return expr
        if isinstance(expr, list):
            if len(expr) == 3:
                left = self._evaluate_expression(expr[0])
                op = expr[1]
                right = self._evaluate_expression(expr[2])

                if op == '*':
                    result = left * right
                elif op == '+':
                    result = left + right
                elif op == '/':
                    result = left / right
                elif op == '-':
                    result = left - right
                elif op in ['^', '**']:
                    assert right.dimensionless, "A power can only be dimensionless"
                    result = np.power(left, right)
                else:
                    raise ValueError(f"Unsupported operation:\nL: {repr(left)}\nO: {repr(op)}\nR: {repr(right)}")
                
                return result
            if len(expr) % 2 == 1:
                tmp = self._evaluate_expression([expr[0], expr[1], expr[2]])
                for i in range(3, len(expr), 2):
                    tmp = self._evaluate_expression([tmp, expr[i], expr[i+1]])
                return tmp
            elif len(expr) == 2:
                value = float(expr[0])
                unit = expr[1]
                return ureg.Quantity(value, unit)
            else:
                raise ValueError(f"Unsupported expression:\n{repr(expr)}")
        elif isinstance(expr, ExpressionElement):
            return expr.obj
        else:
            value = float(expr)
            return ureg.Quantity(value)

class Unacalc(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f'Unacalc {VERSION}')
        self.setGeometry(100, 100, 500, 500)
        
        self.layout = QVBoxLayout()

        self.create_menu()

        self.input_field_label = QLabel("Input Expression:")
        self.input_field_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.layout.addWidget(self.input_field_label)
        
        self.input_field = QLineEdit()
        self.layout.addWidget(self.input_field)

        self.layout.addSpacing(10)
        
        self.result_field_label = QLabel("Result:")
        self.result_field_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.layout.addWidget(self.result_field_label)

        result_layout = QHBoxLayout()
        self.result_value_field = QLineEdit()
        self.result_value_field.setReadOnly(True)
        self.result_value_field.setFocusPolicy(Qt.NoFocus)
        self.result_unit_field = QLineEdit()
        self.result_unit_field.setReadOnly(True)
        self.result_unit_field.setFocusPolicy(Qt.NoFocus)
        result_layout.addWidget(self.result_value_field)
        result_layout.addWidget(self.result_unit_field)
        self.layout.addLayout(result_layout)

        controls_layout = QHBoxLayout()

        self.precision_label = QLabel("Precision:")
        self.precision_label.setFont(QFont('Arial', 12))
        controls_layout.addWidget(self.precision_label)

        self.precision_slider = QSlider(Qt.Horizontal)
        self.precision_slider.setRange(1, 10)
        self.precision_slider.setValue(3)
        self.precision_slider.setTickPosition(QSlider.TicksBelow)
        self.precision_slider.setTickInterval(1)
        self.precision_slider.valueChanged.connect(self.update_display_format)
        self.precision_slider.setStyleSheet("""
            QSlider {
                height: 28px;
                padding: 20px 0;
            }
            QSlider::groove:horizontal {
                border: 1px solid;
                height: 5px;
                margin: 0 12px;
            }
            QSlider::handle:horizontal {
                background: initial;
                border: 1px solid;
                margin: -14px -8px;
            }
        """)
        controls_layout.addWidget(self.precision_slider)

        self.format_label = QLabel("Display Format:")
        self.format_label.setFont(QFont('Arial', 12))
        controls_layout.addWidget(self.format_label)

        self.normal_radio = QRadioButton("Normal")
        self.scientific_radio = QRadioButton("Scientific")
        self.normal_radio.setChecked(True)
        self.display_format_group = QButtonGroup()
        self.display_format_group.addButton(self.normal_radio)
        self.display_format_group.addButton(self.scientific_radio)
        self.normal_radio.toggled.connect(self.update_display_format)
        controls_layout.addWidget(self.normal_radio)
        controls_layout.addWidget(self.scientific_radio)

        self.layout.addLayout(controls_layout)

        font = QFont()
        font.setPointSize(14)

        self.input_field.setFont(font)
        self.result_value_field.setFont(font)
        self.result_unit_field.setFont(font)

        self.layout.addSpacing(10)
        
        self.create_buttons()
        
        self.setLayout(self.layout)

        self.input_field.textChanged.connect(self.auto_calculate)
        self.input_field.returnPressed.connect(self.auto_calculate)

        exit_shortcut = QAction(self)
        exit_shortcut.setShortcut(QKeySequence("Ctrl+W"))
        exit_shortcut.triggered.connect(self.close)
        self.addAction(exit_shortcut)

        QTimer.singleShot(0, self.center_window)
        self.show()

    def center_window(self):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def create_menu(self):
        self.menu_bar = QMenuBar(self)

        file_menu = self.menu_bar.addMenu('File')
        help_menu = self.menu_bar.addMenu('Help')

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        user_guide_action = QAction('User Guide', self)
        user_guide_action.triggered.connect(self.show_help)
        help_menu.addAction(user_guide_action)

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        self.layout.setMenuBar(self.menu_bar)

    def show_about(self):
        about_msg = QMessageBox(self)
        about_msg.setWindowTitle("About Unacalc")
        about_msg.setTextFormat(Qt.RichText)
        about_msg.setText(
            f"""
            <h2>Unacalc</h2>
            <p><b>Version:</b> {VERSION}</p>
            <p>Unacalc is a unit-aware calculator that allows you to perform complex calculations 
            with units seamlessly.</p>
            <p>For more information, visit our 
            <a href='https://github.com/tovam/unacalc'>GitHub page</a>.</p>
            <p>Developed by <a href='https://github.com/tovam'>tovam</a>.</p>
            """
        )
        about_msg.exec_()


    def show_help(self):
        QMessageBox.information(self, "Help", 
            "<h2>Welcome to Unacalc!</h2>"
            "<p>Unacalc is a unit-aware calculator that allows you to perform complex calculations "
            "with units seamlessly.</p>"
            "<h3>Examples of valid expressions:</h3>"
            "<ul>"
            "  <li><b>Basic arithmetic with units:</b><br>"
            "    <code>3 * 5 m/s^2 in km/h^2</code></li>"
            "  <li><b>Converting units:</b><br>"
            "    <code>1000 g in kg</code><br>"
            "    <code>2 hours in minutes</code></li>"
            "  <li><b>Scientific notation:</b><br>"
            "    <code>4.5e3 J / 1.2e2 s</code></li>"
            "  <li><b>Negative and positive numbers:</b><br>"
            "    <code>-1 + 2</code></li>"
            "</ul>"
            "<p>You can type expressions directly into the input field.</p>"
            "<p>Many units and constants are supported.</p>"
        )

    SPECIAL_BUTTONS = {
        '÷': '/',
        '×': '*',
        '–': '-',
    }
    REV_SPECIAL_BUTTONS = {v: k for k, v in SPECIAL_BUTTONS.items()}

    def create_buttons(self):
        self.buttons = {}
        button_layouts = [
            (QHBoxLayout(), ['(', ')', '⌫', 'Clear']),
            (QGridLayout(), [
                ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), (self.REV_SPECIAL_BUTTONS['/'], 0, 3),
                ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), (self.REV_SPECIAL_BUTTONS['*'], 1, 3),
                ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), (self.REV_SPECIAL_BUTTONS['-'], 2, 3),
                ('0', 3, 0), ('.', 3, 1), ('^', 3, 2), ('+', 3, 3),
            ])
        ]

        for layout, button_defs in button_layouts:
            for button_def in button_defs:
                if isinstance(button_def, tuple):
                    text, row, col = button_def
                    button = CustomButton(text)
                    layout.addWidget(button, row, col)
                else:
                    text = button_def
                    button = CustomButton(text)
                    layout.addWidget(button)
                button.clicked.connect(self.on_button_clicked)
                self.buttons[text] = button
                if text in self.SPECIAL_BUTTONS:
                    self.buttons[self.SPECIAL_BUTTONS[text]] = button

            self.layout.addLayout(layout)

    def on_button_clicked(self):
        button = self.sender()
        text = button.text()
        if text == '⌫':
            self.input_field.setText(self.input_field.text()[:-1])
        elif text == 'Clear':
            self.input_field.clear()
        else:
            if text in self.SPECIAL_BUTTONS:
                text = self.SPECIAL_BUTTONS[text]
            self.input_field.setText(self.input_field.text() + text)

    def auto_calculate(self):
        expr = self.input_field.text()
        expr = expr.replace('µ', 'u')
        try:
            dest_unit = None
            if ' in ' in expr:
                [expr, dest_unit] = expr.split(' in ')
            result = Expression(expr).evaluate()
            if dest_unit:
                result = ureg.Quantity(result.m_as(dest_unit), dest_unit)
            self.display_result(result)
            self.input_field.setStyleSheet("background-color: None;")
        except Exception as e:
            self.result_value_field.setText("Error")
            self.result_unit_field.setText("")
            self.input_field.setStyleSheet("background-color: #550000;")
            print(f"Error: {e}", file=sys.stderr)

    def display_result(self, result):
        precision = self.precision_slider.value()
        if self.scientific_radio.isChecked():
            self.result_value_field.setText(f"{result.magnitude:.{precision}e}")
        else:
            self.result_value_field.setText(f"{result.magnitude:.{precision}f}")
        self.result_unit_field.setText(str(result.units))

    def update_display_format(self):
        expr = self.input_field.text()
        if expr:
            self.auto_calculate()

    def keyPressEvent(self, event):
        key = event.text()
        if event.key() in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]:
            return
        elif key in self.buttons:
            button = self.buttons[key]
            button.animate_color(button.default_color, button.pressed_color, 100)
            button.animate_color(button.pressed_color, button.default_color, 100)
            button.click()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.auto_calculate()
        elif event.key() == Qt.Key_Backspace:
            self.buttons['⌫'].click()
        elif key in '0123456789+-*/.()^' or key.isalpha():
            self.input_field.setText(self.input_field.text() + key)

    def mousePressEvent(self, event):
        widget = self.childAt(event.pos())
        if widget not in [self.input_field, self.result_value_field, self.result_unit_field] + list(self.buttons.values()):
            self.input_field.clearFocus()
            self.result_value_field.clearFocus()
            self.result_unit_field.clearFocus()
        super().mousePressEvent(event)

def main():
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(15, 15, 15))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    calc = Unacalc()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
