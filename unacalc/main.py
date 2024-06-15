import sys
import pint
import numpy as np
from pyparsing import Word, alphas, nums, oneOf, infixNotation, opAssoc, Group, ParserElement, Combine, Optional
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QGridLayout, QLabel, QMenuBar, QAction, QMessageBox
from PyQt5.QtGui import QFont, QPalette, QColor, QKeySequence
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, QVariantAnimation, QPointF

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

integer = Word(nums).setParseAction(lambda t: int(t[0]))
float_number = Combine(
    (Optional(Word(nums)) + '.' + Word(nums)) | 
    (Word(nums) + '.')
).setParseAction(lambda t: float(t[0]))
scientific_number = Combine(Word(nums) + Optional('.') + Optional(Word(nums)) + oneOf("e E") + Word(nums + "+-")).setParseAction(lambda t: float(t[0]))
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
        (oneOf('-'), 1, opAssoc.RIGHT),
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
        self.setGeometry(100, 100, 700, 400)

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

        self.result_field = QLineEdit()
        self.result_field.setReadOnly(True)
        self.layout.addWidget(self.result_field)

        font = QFont()
        font.setPointSize(14)

        self.input_field.setFont(font)
        self.result_field.setFont(font)

        self.layout.addSpacing(10)
        
        self.create_buttons()
        
        self.setLayout(self.layout)

        self.input_field.textChanged.connect(self.auto_calculate)
        self.input_field.returnPressed.connect(self.auto_calculate)

        exit_shortcut = QAction(self)
        exit_shortcut.setShortcut(QKeySequence("Ctrl+W"))
        exit_shortcut.triggered.connect(self.close)
        self.addAction(exit_shortcut)

        self.show()

    def create_menu(self):
        self.menu_bar = QMenuBar(self)

        file_menu = self.menu_bar.addMenu('File')
        help_menu = self.menu_bar.addMenu('Help')

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        help_action = QAction('Help', self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        self.layout.setMenuBar(self.menu_bar)

    def show_about(self):
        about_msg = QMessageBox(self)
        about_msg.setWindowTitle("About Unacalc")
        about_msg.setTextFormat(Qt.RichText)
        about_msg.setText(
            f"""
            Unacalc: A Unit-Aware Calculator<br/>
            Version {VERSION}<br/>
            <a href='https://github.com/tovam/unacalc'>https://github.com/tovam/unacalc</a>"""
        )
        about_msg.exec_()

    def show_help(self):
        QMessageBox.information(self, "Help", "Enter expressions using standard mathematical notation.\n"
                                              "Example: '3 * 5 m/s^2 in km/h^2'")

    SPECIAL_BUTTONS = {
        '÷': '/',
        '×': '*',
        '–': '-',
    }
    REV_SPECIAL_BUTTONS = {v: k for k, v in SPECIAL_BUTTONS.items()}

    def create_buttons(self):
        self.buttons = {}
        buttons_layout = QGridLayout()
        
        buttons = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), (self.REV_SPECIAL_BUTTONS['/'], 0, 3),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), (self.REV_SPECIAL_BUTTONS['*'], 1, 3),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), (self.REV_SPECIAL_BUTTONS['-'], 2, 3),
            ('0', 3, 0), ('.', 3, 1), ('+', 3, 2), ('=', 3, 3),
        ]

        button_style = """
            QPushButton {
                background-color: #e1e1e1; 
                color: #333333; 
                font-size: 18px; 
                padding: 10px; 
                margin: 5px; 
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #a6a6a6;
            }
        """

        for text, row, col in buttons:
            button = CustomButton(text)
            button.setStyleSheet(button_style)
            button.clicked.connect(self.on_button_clicked)
            buttons_layout.addWidget(button, row, col)
            self.buttons[text] = button
            if text in self.SPECIAL_BUTTONS:
                self.buttons[self.SPECIAL_BUTTONS[text]] = button

        self.layout.addLayout(buttons_layout)

    def on_button_clicked(self):
        button = self.sender()
        text = button.text()
        if text == '=':
            self.auto_calculate()
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
            self.result_field.setText(str(result))
            self.input_field.setStyleSheet("background-color: None;")
        except Exception as e:
            self.result_field.setText("Error")
            self.input_field.setStyleSheet("background-color: #550000;")
            print(f"Error: {e}", file=sys.stderr)

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
            self.input_field.setText(self.input_field.text()[:-1])
        elif key in '0123456789+-*/.':
            self.input_field.setText(self.input_field.text() + key)

    def mousePressEvent(self, event):
        widget = self.childAt(event.pos())
        if widget not in [self.input_field, self.result_field] + list(self.buttons.values()):
            self.input_field.clearFocus()
            self.result_field.clearFocus()
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
