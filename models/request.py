from datetime import datetime
from app import db

class Request(db.Model):
    """Model for storing FOIA requests without PII."""
    
    id = db.Column(db.Integer, primary_key=True)
    # Request metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    administration = db.Column(db.String(255), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # 'document' or 'explanation' or 'both'
    
    # Request details (anonymized)
    request_description = db.Column(db.Text, nullable=False)
    preferred_response_format = db.Column(db.String(50), nullable=False)
    
    # Contact information (stored only if reminder requested)
    requester_name = db.Column(db.String(255))
    requester_email = db.Column(db.String(255))
    requester_address = db.Column(db.Text)
    
    # LLM Analysis results
    clarity_score = db.Column(db.Float)
    success_likelihood = db.Column(db.String(50))
    llm_suggestions = db.Column(db.Text)
    
    # Status tracking
    reminder_requested = db.Column(db.Boolean, default=False)
    reminder_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Request {self.id}: {self.administration}>' 