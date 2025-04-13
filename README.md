# GeLATO - Luxembourg FOIA Request Generator

GeLATO (Generator for "Loi du 14 septembre 2018 relative à une administration transparente et ouverte") is a modern, easy-to-use web application that helps citizens and journalists generate legally compliant FOIA requests to Luxembourgish public administrations.

## Features

- User-friendly wizard interface
- AI-powered request analysis and refinement
- Professional PDF generation in French
- Administration autocomplete
- Request success likelihood estimation
- Anonymous request storage for statistics

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- Mistral API key for LLM functionality

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd gelato
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```bash
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
MISTRAL_API_KEY=your-mistral-api-key
DATABASE_URL=sqlite:///gelato.db
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Activate the virtual environment (if not already activated):
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the Flask development server:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Project Structure

```
gelato/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── base.html
│   ├── index.html
│   └── wizard/
│       └── ...
├── models/
│   ├── request.py
│   └── administration.py
├── utils/
│   ├── mistral.py
│   └── pdf_generator.py
├── app.py
├── config.py
└── requirements.txt
```

## Development

### Adding New Administrations

To add new administrations to the database, you can:

1. Modify the seed data in `models/administration.py`
2. Run the seeding command:
```bash
flask seed-administrations
```

### Customizing Templates

French letter templates can be customized in the `utils/mistral.py` file by modifying the prompt templates.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[License Type] - See LICENSE file for details

## Acknowledgments

- Built with Flask and Mistral AI
- UI components from Tailwind CSS
- PDF generation using ReportLab 