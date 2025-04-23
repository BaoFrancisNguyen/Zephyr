from datetime import datetime
from app import db

class Offer(db.Model):
    """
    Modèle représentant un drone dans la boutique Zephir.
    Le nom de classe reste 'Offer' pour compatibilité avec l'existant.
    """
    __tablename__ = 'offers'
    
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'debutant', 'intermediaire', 'expert'
    niveau = db.Column(db.String(20), nullable=True)  # Niveau de difficulté
    prix = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=10)  # Stock disponible
    image = db.Column(db.String(255), nullable=True)  # URL de l'image
    est_publie = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Caractéristiques spécifiques aux drones
    autonomie = db.Column(db.Integer, nullable=True)  # Autonomie en minutes
    poids = db.Column(db.Integer, nullable=True)  # Poids en grammes
    dimensions = db.Column(db.String(50), nullable=True)  # Dimensions
    camera = db.Column(db.String(50), nullable=True)  # Type de caméra
    portee = db.Column(db.Integer, nullable=True)  # Portée en mètres
    vitesse = db.Column(db.Integer, nullable=True)  # Vitesse max en km/h
    
    # Relations
    
    cart_items = db.relationship('CartItem', back_populates='offer', lazy=True)
    order_items = db.relationship('OrderItem', back_populates='offer', lazy=True)
    
    # Propriété pour assurer la compatibilité avec l'ancien code
    @property
    def disponibilite(self):
        return self.stock
    
    @disponibilite.setter
    def disponibilite(self, value):
        self.stock = value
    
    # Propriété pour assurer la compatibilité avec l'ancien code
    @property
    def date_evenement(self):
        # Retourne la date actuelle + 30 jours comme valeur par défaut
        return datetime.utcnow() + datetime.timedelta(days=30)
    
    @date_evenement.setter
    def date_evenement(self, value):
        # Cette propriété est ignorée pour les drones
        pass
    
    # Propriété pour assurer la compatibilité avec l'ancien code
    @property
    def nombre_personnes(self):
        return 1
    
    @nombre_personnes.setter
    def nombre_personnes(self, value):
        # Cette propriété est ignorée pour les drones
        pass
    
    def __init__(self, titre, description, type, prix, stock=10, image=None, est_publie=True, 
                 autonomie=None, poids=None, dimensions=None, camera=None, portee=None, 
                 vitesse=None, niveau=None):
        self.titre = titre
        self.description = description
        self.type = type
        self.prix = prix
        self.stock = stock
        self.image = image
        self.est_publie = est_publie
        self.autonomie = autonomie
        self.poids = poids
        self.dimensions = dimensions
        self.camera = camera
        self.portee = portee
        self.vitesse = vitesse
        self.niveau = niveau
    
    def is_available(self):
        """Vérifie si le drone est disponible."""
        return self.est_publie and self.stock > 0
    
    def decrease_stock(self, quantity=1):
        """Diminue le stock du drone."""
        if self.stock >= quantity:
            self.stock -= quantity
            db.session.commit()
            return True
        return False
    
    def increase_stock(self, quantity=1):
        """Augmente le stock du drone."""
        self.stock += quantity
        db.session.commit()
        return True
    
    # Méthode pour compatibilité avec l'ancien code
    def decrease_availability(self, quantity=1):
        """Alias de decrease_stock pour compatibilité."""
        return self.decrease_stock(quantity)
    
    # Méthode pour compatibilité avec l'ancien code
    def increase_availability(self, quantity=1):
        """Alias de increase_stock pour compatibilité."""
        return self.increase_stock(quantity)
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire."""
        return {
            'id': self.id,
            'titre': self.titre,
            'description': self.description,
            'type': self.type,
            'niveau': self.niveau,
            'prix': self.prix,
            'stock': self.stock,
            'image': self.image,
            'est_publie': self.est_publie,
            'autonomie': self.autonomie,
            'poids': self.poids,
            'dimensions': self.dimensions,
            'camera': self.camera,
            'portee': self.portee,
            'vitesse': self.vitesse
        }
    
    def __repr__(self):
        return f"Drone('{self.titre}', '{self.type}', '{self.prix}€')"