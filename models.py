from app import db
from datetime import datetime

class ImportBatch(db.Model):
    __tablename__ = 'import_batches'
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    wines= db.relationship('Wine', backref='import_batch',cascade="all, delete-orphan", lazy='dynamic')

class Wine(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    alcohol=db.Column(db.Float, nullable=False)
    malic_acid=db.Column(db.Float, nullable=False)
    color_intensity=db.Column(db.Float, nullable=False)
    target=db.Column(db.Integer, nullable=False)
    
    batch_id = db.Column(db.Integer, db.ForeignKey('import_batches.id'), nullable=True)

    