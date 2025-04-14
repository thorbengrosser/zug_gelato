from flask import render_template, jsonify, redirect, url_for, session, request, flash, send_file, abort
import json
import os
from app import app, db
from forms import (
    AdminSelectionForm, RequestTypeForm, DocumentRequestForm,
    ExplanationRequestForm, ResponseFormatForm, ContactInfoForm,
    ReviewForm, DocumentItemForm, ExplanationItemForm, NextStepForm,
    AdminLoginForm
)
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.units import inch
from io import BytesIO
import html2text
from utils.pdf_generator import generate_foia_pdf
from models.request import Request
from models.administration import Administration
from utils.mistral import MistralAnalyzer

def load_administrations():
    """Load administrations from JSON file."""
    json_path = os.path.join(app.static_folder, 'data', 'admin-lux.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Store full admin data in a dictionary for later use
    app.admin_data = {admin['Name']: admin for admin in data if admin['Name']}
    # Return only names for the select box
    return [(name, name) for name in app.admin_data.keys()]

@app.route('/')
def index():
    """Landing page route."""
    return render_template('index.html')

@app.route('/wizard/step1', methods=['GET', 'POST'])
def step1_admin():
    """Administration selection step."""
    form = AdminSelectionForm()
    form.administration.choices = load_administrations()
    
    if form.validate_on_submit():
        if form.selection_type.data == 'select':
            # Get the full administration data from the stored dictionary
            selected_admin = app.admin_data.get(form.administration.data)
            if selected_admin:
                session['administration'] = selected_admin['Name']
                session['admin_name'] = selected_admin['Name']
                session['admin_street'] = selected_admin['Address']
                session['admin_postal_code'] = selected_admin['Postal Code']
                session['admin_city'] = selected_admin['City']
                session['admin_address'] = f"{selected_admin['Address']}\n{selected_admin['Postal Code']} {selected_admin['City']}"
        else:
            session['administration'] = 'manual'
            session['admin_name'] = form.admin_name.data
            session['admin_street'] = form.admin_street.data
            session['admin_postal_code'] = form.admin_postal_code.data
            session['admin_city'] = form.admin_city.data
            # Construct full address
            address_parts = []
            if form.admin_street.data:
                address_parts.append(form.admin_street.data)
            if form.admin_postal_code.data and form.admin_city.data:
                address_parts.append(f"{form.admin_postal_code.data} {form.admin_city.data}")
            session['admin_address'] = "\n".join(address_parts)
        
        return redirect(url_for('step2_type'))
    
    return render_template('wizard/step1_admin.html', form=form)

@app.route('/wizard/step2', methods=['GET', 'POST'])
def step2_type():
    """Request type selection step."""
    form = RequestTypeForm()
    
    if form.validate_on_submit():
        session['document_request'] = form.document_request.data
        session['explanation_request'] = form.explanation_request.data
        return redirect(url_for('step3_input'))
    
    return render_template('wizard/step2_type.html', form=form)

@app.route('/wizard/step3', methods=['GET', 'POST'])
def step3_input():
    """Guided input wizard step."""
    document_form = DocumentRequestForm()
    explanation_form = ExplanationRequestForm()
    
    if request.method == 'POST':
        # Process documents and explanations in a single form submission
        if 'submit' in request.form:
            has_valid_data = False
            
            # Process document requests if that option was selected
            if session.get('document_request'):
                # Extract all document items
                document_data = []
                index = 0
                while f'documents-{index}-description' in request.form:
                    description = request.form.get(f'documents-{index}-description', '').strip()
                    date = request.form.get(f'documents-{index}-date', '').strip()
                    
                    # Only add non-empty documents
                    if description:
                        document_data.append({
                            'description': description,
                            'date': date
                        })
                    
                    index += 1
                
                if document_data:
                    session['documents'] = document_data
                    session.pop('temp_documents', None)  # Clean up temporary data
                    has_valid_data = True
            
            # Process explanation requests if that option was selected
            if session.get('explanation_request'):
                # Extract all explanation
                explanation_data = []
                index = 0
                while f'explanations-{index}-description' in request.form:
                    description = request.form.get(f'explanations-{index}-description', '').strip()
                    date = request.form.get(f'explanations-{index}-date', '').strip()
                    
                    # Only add non-empty explanations
                    if description:
                        explanation_data.append({
                            'description': description,
                            'date': date
                        })
                    
                    index += 1
                
                if explanation_data:
                    session['explanations'] = explanation_data
                    session.pop('temp_explanations', None)  # Clean up temporary data
                    has_valid_data = True
            
            # Proceed if at least one valid item was submitted in either category
            if has_valid_data:
                return redirect(url_for('step4_review'))
            
            # If no valid data was submitted, show error
            if session.get('document_request') and session.get('explanation_request'):
                flash('Please add at least one document or explanation request.', 'error')
            elif session.get('document_request'):
                flash('Please add at least one document request.', 'error')
            else:
                flash('Please add at least one explanation request.', 'error')
                
            # Render the template again with the validation error
            return render_template('wizard/step3_input.html',
                                 document_form=document_form,
                                 explanation_form=explanation_form)
    
    # Initialize forms for GET request
    return render_template('wizard/step3_input.html',
                         document_form=document_form,
                         explanation_form=explanation_form)

@app.route('/wizard/step4', methods=['GET', 'POST'])
def step4_review():
    """Request review step."""
    # Check if we have the necessary data from step 3
    if not session.get('documents') and not session.get('explanations'):
        return redirect(url_for('step3_input'))
        
    form = NextStepForm()
    
    # Combine document and explanation requests
    all_items = []
    if session.get('document_request') and session.get('documents'):
        all_items.extend(session.get('documents', []))
    if session.get('explanation_request') and session.get('explanations'):
        all_items.extend(session.get('explanations', []))
    
    # Set for the template
    session['all_items'] = all_items
    
    # Debug logging
    print("Debug: Step 4 - Checking session state")
    print(f"Debug: refined_text exists in session: {'refined_text' in session}")
    if 'refined_text' in session:
        print(f"Debug: Current refined_text type: {type(session['refined_text'])}")
        print(f"Debug: Current refined_text content: {session['refined_text']}")
    
    # Continue with next step on form submission
    if request.method == 'POST':
        print("Debug: POST request received for step4_review")
        
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        print(f"Debug: Is AJAX request: {is_ajax}")
        
        # Print all form data for debugging
        print("Debug: Form data received:")
        for key, value in request.form.items():
            print(f"Debug: {key} = {value}")
        
        # First check for the direct refined text input
        direct_refined_text = request.form.get('direct_refined_text')
        if direct_refined_text:
            print(f"Debug: Found direct_refined_text in form: {direct_refined_text}")
            session['refined_text'] = direct_refined_text
            print(f"Debug: Set refined_text in session to direct value")
            session['step4_complete'] = True
            
            if is_ajax:
                return jsonify({'success': True, 'message': 'Refined text saved successfully (direct)'})
            else:
                return redirect(url_for('step5_format'))
            
        # Get refined text directly from request data since it's a hidden input
        refined_text = request.form.get('refined_text')
        if refined_text:
            print(f"Debug: Storing new refined text from request.form: {refined_text}")
            print(f"Debug: New refined text type: {type(refined_text)}")
            session['refined_text'] = refined_text
            session['step4_complete'] = True
            
            if is_ajax:
                return jsonify({'success': True, 'message': 'Refined text saved successfully'})
            else:
                return redirect(url_for('step5_format'))
        else:
            print("Debug: No refined_text found in form data")
            error_msg = "No refined text found in form data"
            
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('wizard/step4_review.html', form=form)
        
    return render_template('wizard/step4_review.html', form=form)

@app.route('/wizard/step5', methods=['GET', 'POST'])
def step5_format():
    """Response format selection step."""
    form = ResponseFormatForm()
    
    if form.validate_on_submit():
        session['response_format'] = form.response_format.data
        return redirect(url_for('step6_contact'))
    
    return render_template('wizard/step5_format.html', form=form)

@app.route('/wizard/step6', methods=['GET', 'POST'])
def step6_contact():
    """Contact information step."""
    form = ContactInfoForm()
    
    if form.validate_on_submit():
        session['full_name'] = form.full_name.data
        session['email'] = form.email.data
        session['phone'] = form.phone.data
        session['street_address'] = form.street_address.data
        session['postal_code'] = form.postal_code.data
        session['city'] = form.city.data
        # Construct full address
        address_parts = []
        if form.street_address.data:
            address_parts.append(form.street_address.data)
        if form.postal_code.data and form.city.data:
            address_parts.append(f"{form.postal_code.data} {form.city.data}")
        session['address'] = "\n".join(address_parts)
        return redirect(url_for('step7_preview'))
    
    return render_template('wizard/step6_contact.html', form=form)

@app.route('/wizard/step7', methods=['GET', 'POST'])
def step7_preview():
    """Step 7: Preview and generate the final document."""
    # Check if we have the required contact information
    required_fields = ['full_name', 'email', 'street_address', 'postal_code', 'city']
    missing_fields = [field for field in required_fields if not session.get(field)]
    
    if missing_fields:
        return redirect(url_for('step6_contact'))
    
    # Get letter data for preview
    letter_data = get_letter_data()
    
    # Check if reminder was requested
    reminder_requested = session.get('reminder_requested', False)
    
    return render_template(
        'wizard/step7_preview.html',
        letter_data=letter_data,
        reminder_requested=reminder_requested
    )

def get_letter_data():
    """Prepare data for letter generation."""
    # Get user information
    user_info = {
        'name': session.get('full_name', ''),
        'street_address': session.get('street_address', ''),
        'postal_code': session.get('postal_code', ''),
        'city': session.get('city', ''),
        'email': session.get('email', ''),
        'phone': session.get('phone', ''),
        'address': f"{session.get('street_address', '')}\n{session.get('postal_code', '')} {session.get('city', '')}"
    }
    
    # Get administration
    admin_name = session.get('admin_name', '')
    
    # Format administration address
    admin_address = ''
    if session.get('admin_street'):
        admin_address = session.get('admin_street')
    if session.get('admin_postal_code') and session.get('admin_city'):
        if admin_address:  # Add newline if we already have street info
            admin_address += '\n'
        admin_address += f"{session.get('admin_postal_code')} {session.get('admin_city')}"
    
    # Current date
    current_date = datetime.now().strftime('%d/%m/%Y')
    
    # Get request items - use the refined text if available
    requested_documents = []
    requested_explanations = []
    
    # Debug logging
    print("Debug: Checking refined text in session")
    print(f"Debug: refined_text exists in session: {'refined_text' in session}")
    if 'refined_text' in session:
        print(f"Debug: refined_text type: {type(session['refined_text'])}")
        print(f"Debug: refined_text content: {session['refined_text']}")
    
    if session.get('refined_text'):
        # Use the AI-refined text
        refined_text = session.get('refined_text')
        print(f"Debug: Processing refined text: {refined_text}")
        
        # Store the raw refined text for debugging
        raw_text = refined_text
        
        # Try to force the refined text to be JSON compatible
        if isinstance(refined_text, str):
            # Direct string replacement for common JSON issues
            refined_text = refined_text.replace("'", '"')
            refined_text = refined_text.strip()
            print(f"Debug: Cleaned refined text (quotes): {refined_text}")
            
            # Ensure it starts and ends with curly braces
            if not refined_text.startswith('{'):
                refined_text = '{' + refined_text
            if not refined_text.endswith('}'):
                refined_text = refined_text + '}'
            print(f"Debug: Cleaned refined text (braces): {refined_text}")
        
        # Handle different formats of refined text
        if isinstance(refined_text, dict):
            # If it's already a dictionary, use it directly
            items_dict = refined_text
            print("Debug: Using refined text as dictionary")
        else:
            try:
                # Try to parse as JSON if it's a string
                items_dict = json.loads(refined_text)
                print("Debug: Parsed refined text as JSON")
            except (json.JSONDecodeError, TypeError) as e:
                # If parsing fails, try different approaches
                print(f"Debug: JSON parsing failed: {e}")
                
                try:
                    # Try a different JSON parsing approach
                    # First eliminate any non-JSON characters
                    import re
                    clean_text = re.sub(r'[^\{\}:"0-9a-zA-Z,\.\-_\s]', '', refined_text)
                    print(f"Debug: Regex cleaned text: {clean_text}")
                    
                    items_dict = json.loads(clean_text)
                    print("Debug: Parsed cleaned refined text (regex) as JSON")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Debug: Second JSON parsing attempt failed: {e}")
                    # If all parsing fails, treat as a simple string
                    items_dict = {'Item 1': raw_text}
                    print("Debug: Using raw refined text as simple string")
        
        # Extract items in order
        items = []
        i = 1
        while True:
            key = f'Item {i}:'
            alt_key = f'Item {i}'
            if key in items_dict:
                items.append(items_dict[key])
                print(f"Debug: Found item with key {key}")
            elif alt_key in items_dict:
                items.append(items_dict[alt_key])
                print(f"Debug: Found item with key {alt_key}")
            else:
                break
            i += 1
        
        print(f"Debug: Extracted items: {items}")
        
        # If we have document requests and explanation requests, split the items
        if session.get('document_request') and session.get('explanation_request'):
            doc_count = len(session.get('documents', []))
            exp_count = len(session.get('explanations', []))
            print(f"Debug: Document count: {doc_count}, Explanation count: {exp_count}")
            
            if len(items) >= (doc_count + exp_count):
                # We have enough items to distribute to both categories
                requested_documents = items[:doc_count]
                requested_explanations = items[doc_count:doc_count + exp_count]
                print("Debug: Split items between documents and explanations")
            else:
                # Not enough items, use the refined text for both categories
                requested_documents = items
                requested_explanations = items
                print("Debug: Using same items for both documents and explanations")
        elif session.get('document_request'):
            # Only document requests
            requested_documents = items
            print("Debug: Using items for documents only")
        else:
            # Only explanation requests
            requested_explanations = items
            print("Debug: Using items for explanations only")
    else:
        # Use the original request items
        print("Debug: Using original request items")
        if session.get('document_request') and session.get('documents'):
            requested_documents = [doc['description'] for doc in session.get('documents', [])]
        if session.get('explanation_request') and session.get('explanations'):
            requested_explanations = [exp['description'] for exp in session.get('explanations', [])]
    
    print(f"Debug: Final requested_documents: {requested_documents}")
    print(f"Debug: Final requested_explanations: {requested_explanations}")
    
    # Get response format
    response_format = session.get('response_format', 'email')
    
    return {
        'user_info': user_info,
        'administration': {
            'name_fr': admin_name,
            'address': admin_address
        },
        'current_date': current_date,
        'requested_documents': requested_documents,
        'requested_explanations': requested_explanations,
        'response_format': response_format
    }

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """Generate and download PDF version of the request letter."""
    # Get the letter data
    letter_data = get_letter_data()
    
    # Store user's intention and reminder preference
    send_request = request.form.get('send_request') == 'true'
    reminder_requested = request.form.get('reminder_requested') == 'true'
    
    # Create a new Request object
    from datetime import datetime
    
    # Determine request type
    request_type = 'both' if letter_data.get('requested_documents') and letter_data.get('requested_explanations') else \
                  'document' if letter_data.get('requested_documents') else 'explanation'
    
    # Format request description
    request_description = []
    if letter_data.get('requested_documents'):
        request_description.append("Documents requested:")
        request_description.extend([f"- {doc}" for doc in letter_data['requested_documents']])
    if letter_data.get('requested_explanations'):
        request_description.append("\nExplanations requested:")
        request_description.extend([f"- {exp}" for exp in letter_data['requested_explanations']])
    
    # Create and save the request
    new_request = Request(
        administration=letter_data['administration']['name_fr'],
        request_type=request_type,
        request_description='\n'.join(request_description),
        preferred_response_format=letter_data['response_format'],
        reminder_requested=reminder_requested,
        reminder_date=datetime.now() + timedelta(days=60) if reminder_requested else None
    )
    
    # Save contact information if reminder is requested
    if reminder_requested:
        new_request.requester_name = letter_data['user_info']['name']
        new_request.requester_email = letter_data['user_info']['email']
        new_request.requester_address = letter_data['user_info']['address']
    
    db.session.add(new_request)
    db.session.commit()
    
    if send_request and reminder_requested:
        # Store reminder request in session
        session['reminder_requested'] = True
        session['reminder_date'] = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    
    # Generate PDF
    buffer = generate_foia_pdf(letter_data)
    
    # Store the letter data in session for later use
    session['letter_data'] = letter_data
    
    # Flash success message
    flash('Your FOIA request letter has been generated successfully!', 'success')
    
    # Redirect to confirmation page
    return redirect(url_for('confirmation'))

@app.route('/confirmation')
def confirmation():
    """Show confirmation page after PDF generation."""
    if 'letter_data' not in session:
        return redirect(url_for('index'))
    
    return render_template('confirmation.html')

@app.route('/download-confirmed-pdf')
def download_confirmed_pdf():
    """Download the PDF after confirmation."""
    if 'letter_data' not in session:
        return redirect(url_for('index'))
    
    # Get the letter data from session
    letter_data = session['letter_data']
    
    # Generate PDF
    buffer = generate_foia_pdf(letter_data)
    
    # Return PDF as download
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='foia_request.pdf'
    )

@app.route('/api/analyze-request', methods=['POST'])
def analyze_request():
    """API endpoint for analyzing FOIA requests."""
    try:
        request_data = request.get_json()
        analyzer = MistralAnalyzer()
        analysis = analyzer.analyze_request(request_data)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/store-refined-text', methods=['POST'])
def store_refined_text():
    """API endpoint for storing refined text in the session."""
    try:
        data = request.get_json()
        refined_text = data.get('refined_text')
        
        if not refined_text:
            return jsonify({'success': False, 'message': 'No refined text provided'}), 400
        
        print(f"Debug: Storing refined text via API: {refined_text}")
        
        # If this is the first item, initialize the session variable
        if 'refined_text' not in session:
            session['refined_text'] = {}
            print("Debug: Initialized refined_text in session")
        
        # If the session variable is a string (from previous versions), convert to dict
        if isinstance(session['refined_text'], str):
            try:
                session['refined_text'] = json.loads(session['refined_text'])
                print("Debug: Converted refined_text from string to dict")
            except (json.JSONDecodeError, TypeError):
                session['refined_text'] = {}
                print("Debug: Reset refined_text due to parsing error")
        
        # Update the session with the new refined text
        if isinstance(session['refined_text'], dict):
            session['refined_text'].update(refined_text)
            print(f"Debug: Updated refined_text in session: {session['refined_text']}")
        else:
            session['refined_text'] = refined_text
            print(f"Debug: Set refined_text in session: {refined_text}")
        
        # Mark as complete
        session['step4_complete'] = True
        
        return jsonify({'success': True, 'message': 'Refined text stored successfully'})
    except Exception as e:
        print(f"Debug: Error storing refined text: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """API endpoint for PDF generation."""
    # TODO: Implement PDF generation
    return jsonify({'status': 'success'})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    form = AdminLoginForm()
    if form.validate_on_submit():
        password = form.password.data
        if password == os.getenv('ADMIN_PASSWORD', 'admin123'):  # Default password for development
            session['admin_logged_in'] = True
            return redirect(url_for('admin_requests'))
        flash('Invalid password', 'error')
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/requests')
def admin_requests():
    """Admin page to view all requests."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    requests = Request.query.order_by(Request.created_at.desc()).all()
    return render_template('admin/requests.html', requests=requests)

@app.route('/admin/request/<int:request_id>')
def view_request(request_id):
    """View detailed request information."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    req = Request.query.get_or_404(request_id)
    return render_template('admin/request_detail.html', request=req)

@app.route('/api/confirm-refined-text', methods=['POST'])
def confirm_refined_text():
    """API endpoint to confirm refined text and proceed to next step."""
    try:
        data = request.get_json()
        confirmed = data.get('confirmed', False)
        
        if confirmed:
            # Check if we have refined text in the session
            if 'refined_text' in session:
                print(f"Debug: Confirmed refined text in session: {session['refined_text']}")
                
                # Make sure it's a proper format
                if isinstance(session['refined_text'], str):
                    try:
                        # Try to parse it if it's a JSON string
                        session['refined_text'] = json.loads(session['refined_text'])
                    except json.JSONDecodeError:
                        pass  # Keep it as a string if parsing fails
                
                # Set the step as complete
                session['step4_complete'] = True
                
                return jsonify({
                    'success': True, 
                    'message': 'Refined text confirmed', 
                    'refined_text': session['refined_text']
                })
            else:
                print("Debug: No refined text found in session during confirmation")
                return jsonify({
                    'success': False, 
                    'message': 'No refined text found in session'
                }), 400
        else:
            return jsonify({'success': False, 'message': 'Confirmation required'}), 400
    except Exception as e:
        print(f"Debug: Error confirming refined text: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500 