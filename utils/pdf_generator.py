from weasyprint import HTML, CSS
from io import BytesIO
import os
from jinja2 import Template

def generate_foia_pdf(letter_data):
    """
    Generate a PDF document for the FOIA request using WeasyPrint.
    
    Args:
        letter_data (dict): Dictionary with all data for the letter
            
    Returns:
        BytesIO: Buffer containing the PDF document
    """
    # Create a BytesIO buffer
    buffer = BytesIO()
    
    # Get the template path
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'letter.html')
    
    # Read the template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Prepare the data for the template
    template_data = {
        'user_info': letter_data.get('user_info', {}),
        'administration': letter_data.get('administration', {}),
        'current_date': letter_data.get('current_date', ''),
        'requested_documents': letter_data.get('requested_documents', []),
        'requested_explanations': letter_data.get('requested_explanations', []),
        'response_format': letter_data.get('response_format', 'email')
    }
    
    # Render the template with the data
    html = Template(template).render(**template_data)
    
    # Create CSS for A4 page size
    css = CSS(string='''
        @page {
            size: A4;
            margin: 2.5cm;
        }
        body {
            width: 100%;
            height: 100%;
            font-family: 'Times New Roman', Times, serif;
            line-height: 1.5;
        }
        .letter-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .sender-info {
            text-align: right;
            margin-bottom: 40px;
        }
        .recipient-info {
            margin-bottom: 40px;
        }
        .date {
            text-align: right;
            margin-bottom: 40px;
        }
        .subject {
            font-weight: bold;
            margin-bottom: 20px;
        }
    ''')
    
    # Convert HTML to PDF with CSS
    HTML(string=html).write_pdf(buffer, stylesheets=[css])
    
    # Reset buffer position
    buffer.seek(0)
    
    return buffer 