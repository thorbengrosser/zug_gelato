from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, BooleanField, TextAreaField, EmailField, TelField, FieldList, FormField, RadioField, PasswordField
from wtforms.validators import DataRequired, Email, Optional, Length

class AdminSelectionForm(FlaskForm):
    """Form for selecting the administration."""
    selection_type = RadioField('Select or Enter Administration', 
                              choices=[('select', 'Select from list'), ('manual', 'Enter manually')],
                              default='select',
                              validators=[DataRequired()])
    
    administration = SelectField('Administration', 
                               choices=[],  # Will be populated dynamically
                               validators=[Optional()])
    
    # Manual entry fields
    admin_name = StringField('Administration Name', validators=[Optional()])
    admin_street = StringField('Street Address', validators=[Optional()])
    admin_postal_code = StringField('Postal Code', validators=[Optional()])
    admin_city = StringField('City', validators=[Optional()])
    
    submit = SubmitField('Continue')

class RequestTypeForm(FlaskForm):
    """Form for selecting the type of FOIA request."""
    request_types = [
        ('documents', 'Request access to existing administrative documents'),
        ('explanations', 'Request explanations or justifications about specific administrative decisions or actions')
    ]
    
    document_request = BooleanField('Request access to existing administrative documents')
    explanation_request = BooleanField('Request explanations or justifications about specific administrative decisions or actions')
    submit = SubmitField('Continue')

class DocumentItemForm(FlaskForm):
    """Form for a single document request item."""
    description = TextAreaField('Document Description',
                              validators=[DataRequired()],
                              render_kw={"placeholder": "Describe the document you are requesting..."})
    date = StringField('Document Date (Optional)',
                      validators=[Optional()],
                      render_kw={"placeholder": "YYYY-MM-DD or time period"})

class ExplanationItemForm(FlaskForm):
    """Form for a single explanation request item."""
    description = TextAreaField('Decision Description',
                              validators=[DataRequired()],
                              render_kw={"placeholder": "Describe the administrative decision or action you need explanations about..."})
    date = StringField('Decision Date (Optional)',
                      validators=[Optional()],
                      render_kw={"placeholder": "YYYY-MM-DD"})

class DocumentRequestForm(FlaskForm):
    """Form for document request details."""
    documents = FieldList(FormField(DocumentItemForm), min_entries=1)
    add_document = SubmitField('Add Another Document')
    submit = SubmitField('Continue')

class ExplanationRequestForm(FlaskForm):
    """Form for explanation request details."""
    explanations = FieldList(FormField(ExplanationItemForm), min_entries=1)
    add_explanation = SubmitField('Add Another Explanation')
    submit = SubmitField('Continue')

class ResponseFormatForm(FlaskForm):
    """Form for selecting response format."""
    response_format = SelectField('Preferred Response Format',
                                choices=[
                                    ('email', 'Email'),
                                    ('postal', 'Postal Mail'),
                                    ('onsite', 'On-site Consultation')
                                ],
                                validators=[DataRequired()])
    submit = SubmitField('Continue')

class ContactInfoForm(FlaskForm):
    """Form for contact information."""
    full_name = StringField('Full Name', validators=[DataRequired()])
    street_address = StringField('Street Address', validators=[DataRequired()])
    postal_code = StringField('Postal Code', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    phone = TelField('Phone Number (Optional)', validators=[Optional()])
    submit = SubmitField('Continue')

class ReviewForm(FlaskForm):
    """Form for reviewing and refining the request."""
    refined_text = TextAreaField('Refined Request Text', validators=[Optional()])
    submit = SubmitField('Continue')

class NextStepForm(FlaskForm):
    """Form for moving to the next step with refined text."""
    refined_text = TextAreaField('Refined Request Text', validators=[Optional()], render_kw={"hidden": True})
    submit = SubmitField('Continue')

class AdminLoginForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login') 