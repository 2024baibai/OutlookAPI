from datetime import datetime
from extensions import db

class OutlookEmail(db.Model):
    __tablename__ = 'outlook_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    email_password = db.Column(db.String(255), nullable=False)
    client_id = db.Column(db.String(255), nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    access_token = db.Column(db.Text, nullable=True)
    expire_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OutlookEmail {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'client_id': self.client_id,
            'expire_time': self.expire_time.isoformat() if self.expire_time else None,
            'created_at': self.created_at.isoformat()
        }

class EmailRecord(db.Model):
    __tablename__ = 'email_records'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    sender = db.Column(db.String(255), nullable=True)
    received_time = db.Column(db.DateTime, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('email', 'subject', 'sender', 'received_time', name='unique_email_record'),
    )
    
    def __repr__(self):
        return f'<EmailRecord {self.email} - {self.subject}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'subject': self.subject,
            'sender': self.sender,
            'received_time': self.received_time.isoformat()
        }
