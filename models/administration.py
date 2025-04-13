from app import db

class Administration(db.Model):
    """Model for storing Luxembourg public administrations."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    name_fr = db.Column(db.String(255), nullable=False)  # French name
    address = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    category = db.Column(db.String(100))  # For grouping/filtering
    
    def __repr__(self):
        return f'<Administration {self.name}>'
    
    @staticmethod
    def seed_initial_data():
        """Seed initial administration data."""
        initial_data = [
            {
                'name': 'Ministry of State',
                'name_fr': 'Ministère d\'État',
                'address': '4, rue de la Congrégation, L-1352 Luxembourg',
                'category': 'Ministry'
            },
            {
                'name': 'Ministry of Justice',
                'name_fr': 'Ministère de la Justice',
                'address': '13, rue Erasme, L-1468 Luxembourg',
                'category': 'Ministry'
            },
            # Add more administrations as needed
        ]
        
        for data in initial_data:
            admin = Administration.query.filter_by(name=data['name']).first()
            if not admin:
                admin = Administration(**data)
                db.session.add(admin)
        
        db.session.commit() 