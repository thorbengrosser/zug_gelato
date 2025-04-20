# GeLATO - Luxembourg FOIA Request Generator

GeLATO is a user-friendly web application that helps citizens generate Freedom of Information Act (FOIA) requests for Luxembourgish public administrations. It simplifies the process of requesting public information by guiding users through a step-by-step wizard and generating compliant request letters.

## Features

- 🚀 Easy-to-use step-by-step wizard interface
- 📝 Automatic generation of compliant FOIA request letters
- 🏛️ Comprehensive database of Luxembourgish public administrations
- 🤖 AI-powered request analysis and success likelihood estimation
- 📧 Optional email reminders for follow-up
- 📄 PDF export functionality
- 🔒 Secure admin interface for request management

## Technology Stack

- **Backend**: Python with Flask
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: MySQL
- **AI Analysis**: Mistral AI
- **PDF Generation**: Custom PDF generator
- **Analytics**: Matomo

## Installation with Docker

1. Clone the repository:
```bash
git clone https://github.com/yourusername/GeLATO.git
cd GeLATO
```

2. Create and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Build and start the containers:
```bash
docker-compose up --build -d
```

The application will be available at `http://localhost:5123`

## Manual Installation (Development)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/GeLATO.git
cd GeLATO
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Configuration

The application requires the following environment variables:

- `FLASK_APP`: Application entry point
- `FLASK_DEBUG`: Development or production environment (0 for production)
- `SECRET_KEY`: Flask secret key
- `MISTRAL_API_KEY`: API key for Mistral AI analysis
- `DB_ROOT_PASSWORD`: MySQL root password
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `ADMIN_PASSWORD`: Password for admin interface

## Usage

1. Visit the application in your web browser
2. Click "Start your request"
3. Follow the step-by-step wizard to create your FOIA request
4. Review and download your generated request letter
5. Submit the letter to the relevant administration

## Admin Interface

The admin interface allows you to:
- View all submitted requests
- Analyze request clarity and success likelihood
- Manage request status
- Export request data

Access the admin interface through the footer link and use the configured admin password.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Developed by [ZUG](https://www.zug.lu)

## Support

For support, please open an issue in the GitHub repository or contact the development team. 