# Unacalc, the Unit-Aware Calculator

This project is a unit-aware calculator application developed using PyQt5 for the graphical user interface and Pint for handling units of measurement. It allows users to input and evaluate mathematical expressions that include units, providing accurate results with unit conversions.

## Features

- **Unit Management**: Supports unit conversions and arithmetic using the Pint library.
- **Expression Parsing**: Parses mathematical expressions, recognizing numbers, units, and operations using the Pyparsing library.
- **Arithmetic Operations**: Supports addition, subtraction, multiplication, division, and exponentiation.
- **Auto Calculation**: Automatically calculates and displays the result as the user types.
- **Unit Conversion**: Enables unit conversion within expressions using the "in" keyword (e.g., "100 m in cm").
- **Intuitive GUI**: Features an easy-to-use interface with an input field, result display, and a grid of buttons for input.
- **Error Handling**: Displays error messages for invalid expressions.
- **Keyboard Input**: Supports keyboard input for digits, operators, and backspace.
- **Date and Time Calculations**: Supports date and time arithmetic and conversion (e.g., "2024-11-13 + 2d", "now - 2 weeks").

## Getting Started

### Prerequisites

- Python 3.x
- PyQt5
- Pint
- NumPy
- Pyparsing

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/tovam/unacalc
    ```
2. Change to the project directory:
    ```sh
    cd unacalc
    ```
3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

### Running the Calculator

To start the calculator application, run:
```sh
python unacalc.py
```

## Usage

- Enter mathematical expressions directly into the input field.
- Use the buttons to input numbers and operators.
- The result is automatically calculated and displayed in the result field.
- Use the "in" keyword to convert units (e.g., `100 m in cm`).

## Example Expressions

- `5 m + 3 m`
- `10 kg * 9.81 m/s^2`
- `100 W * 2 h in Wh`
- `100 m in cm`
- `1e3 kg * 9.81 m/s^2 in N`
- `2024-06-08T19:45:10 + 5 month`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
