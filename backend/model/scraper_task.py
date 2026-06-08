from extensions import db
from datetime import datetime

class ScraperTask(db.Model):
    __tablename__ = 'scraper_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50))
    
    # Mapped to the actual 'query' column in MySQL DB
    search_query = db.Column('query', db.String(255)) 
    
    location = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default="PENDING")
    progress = db.Column(db.Integer, default=0)
    
    # Mapped to the actual 'total_leads' column in MySQL DB
    total_found = db.Column('total_leads', db.Integer, default=0)
    
    last_index = db.Column(db.Integer, default=0)
    should_stop = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        # We keep the keys as 'query' and 'total_leads' so the Frontend remains happy
        return {
            "id": self.id,
            "platform": self.platform,
            "query": self.search_query, 
            "location": self.location,
            "status": self.status,
            "progress": self.progress,
            "total_leads": self.total_found,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }