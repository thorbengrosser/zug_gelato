# GeLATO - Luxembourg FOIA Request Generator

GeLATO (Generator for "Loi du 14 septembre 2018 relative à une administration transparente et ouverte") is a modern, easy-to-use web application that helps citizens and journalists generate legally compliant FOIA requests to Luxembourgish public administrations.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://www.docker.com/)

## Features

- 🧙‍♂️ User-friendly wizard interface
- 🤖 AI-powered request analysis and refinement using Mistral AI
- 📄 Professional PDF generation in French
- 🏛️ Administration autocomplete
- 📊 Request success likelihood estimation
- 🔒 Anonymous request storage for statistics
- 🐳 Docker support for easy deployment

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- Mistral API key for LLM functionality
- Docker (optional, for containerized deployment)

## Installation

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/thorbengrosser/zug_gelato.git
cd zug_gelato
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

### Option 2: Docker Installation

1. Clone the repository:
```bash
git clone https://github.com/thorbengrosser/zug_gelato.git
cd zug_gelato
```

2. Build and run the Docker container:
```bash
docker build -t zug_gelato .
docker run -p 5000:5000 --env-file .env zug_gelato
```

## Running the Application

### Local Development

1. Activate the virtual environment (if not already activated):
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the Flask development server:
```bash
flask run
```

The application will be available at `http://localhost:5000`

### Docker

If using Docker, the application will be available at `http://localhost:5000` after running the container.

## Project Structure

```
zug_gelato/
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── data/
│       └── admin-lux.json
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── admin/
│   │   ├── login.html
│   │   ├── requests.html
│   │   └── request_detail.html
│   └── wizard/
│       ├── step1_admin.html
│       ├── step2_type.html
│       ├── step3_input.html
│       ├── step4_review.html
│       ├── step5_format.html
│       ├── step6_contact.html
│       └── step7_preview.html
├── models/
│   ├── request.py
│   └── administration.py
├── utils/
│   ├── mistral.py
│   └── pdf_generator.py
├── migrations/
├── instance/
├── app.py
├── forms.py
├── routes.py
├── requirements.txt
├── Dockerfile
└── run_app.sh
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
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask and Mistral AI
- UI components from Tailwind CSS
- PDF generation using ReportLab
- Docker support for easy deployment

## Contact

Thorben Grosser - [@thorbengrosser](https://github.com/thorbengrosser)

Project Link: [https://github.com/thorbengrosser/zug_gelato](https://github.com/thorbengrosser/zug_gelato) 