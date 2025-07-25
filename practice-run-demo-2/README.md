# Hello PyOhio Flask App

A modern Flask web application that displays "Hello PyOhio" with a clean, responsive design.

## Features

- Modern UI with gradient background
- Responsive design that works on all devices
- Animated Python logo
- Current date display

## Installation

1. Clone this repository or download the files
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

To run the application locally:

```bash
python app.py
```

The app will be available at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Project Structure

```
.
├── app.py              # Main Flask application
├── requirements.txt    # Project dependencies
├── static/             # Static files
│   └── css/
│       └── style.css   # Custom CSS styles
├── templates/          # HTML templates
│   └── index.html      # Main page template
└── README.md           # This file
```

## Technologies Used

- Flask
- HTML5
- CSS3
- Bootstrap 5
- Google Fonts (Poppins)
