from datetime import datetime
import uuid
from app import db

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False)  # Garde offer_id pour compatibilité
    quantite = db.Column(db.Integer, default=1)
    prix_unitaire = db.Column(db.Float, nullable=False)
    
    # Relations
    offer = db.relationship('Offer', back_populates='order_items')
    order = db.relationship('Order', back_populates='items')
    
    def __init__(self, order_id, offer_id, quantite, prix_unitaire):
        self.order_id = order_id
        self.offer_id = offer_id
        self.quantite = quantite
        self.prix_unitaire = prix_unitaire
    
    def sous_total(self):
        """Calcule le sous-total pour cet élément de la commande."""
        return self.quantite * self.prix_unitaire
    
    def __repr__(self):
        return f"OrderItem(order_id={self.order_id}, offer_id={self.offer_id}, quantite={self.quantite})"

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    total = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(20), default='en attente')  # 'en attente', 'payée', 'expédiée', 'livrée', 'annulée'
    date_commande = db.Column(db.DateTime, default=datetime.utcnow)
    date_paiement = db.Column(db.DateTime, nullable=True)
    date_expedition = db.Column(db.DateTime, nullable=True)
    date_livraison = db.Column(db.DateTime, nullable=True)
    numero_suivi = db.Column(db.String(100), nullable=True)  # Numéro de suivi du colis
    cle_achat = db.Column(db.String(255), unique=True, nullable=False)
    adresse_email = db.Column(db.String(120), nullable=False)
    adresse_livraison = db.Column(db.Text, nullable=True)  # Adresse de livraison
    
    # Relations
    items = db.relationship('OrderItem', back_populates='order', lazy=True, cascade="all, delete-orphan")
    user = db.relationship('User', back_populates='orders')
    
    def __init__(self, user_id, total, adresse_email, adresse_livraison=None):
        self.user_id = user_id
        self.total = total
        self.reference = self._generate_reference()
        self.cle_achat = self._generate_purchase_key()
        self.adresse_email = adresse_email
        self.adresse_livraison = adresse_livraison
    
    def _generate_reference(self):
        """Génère une référence unique pour la commande."""
        date_str = datetime.utcnow().strftime('%Y%m%d')
        random_str = str(uuid.uuid4())[:8]
        return f"ZD-{date_str}-{random_str}".upper()
    
    def _generate_purchase_key(self):
        """Génère une clé d'achat unique pour la commande."""
        from flask import current_app
        import hashlib
        
        key_material = f"{uuid.uuid4()}{self.user_id}{datetime.utcnow().timestamp()}{current_app.config['SALT_KEY']}"
        return hashlib.sha256(key_material.encode()).hexdigest()
    
    def add_item(self, offer, quantite, prix_unitaire):
        """Ajoute un élément à la commande."""
        item = OrderItem(
            order_id=self.id,
            offer_id=offer.id if hasattr(offer, 'id') else offer,
            quantite=quantite,
            prix_unitaire=prix_unitaire
        )
        db.session.add(item)
        db.session.commit()
        return item
    
    def set_paid(self):
        """Marque la commande comme payée."""
        self.statut = 'payée'
        self.date_paiement = datetime.utcnow()
        db.session.commit()
        return True
    
    def set_shipped(self, numero_suivi=None):
        """Marque la commande comme expédiée."""
        self.statut = 'expédiée'
        self.date_expedition = datetime.utcnow()
        if numero_suivi:
            self.numero_suivi = numero_suivi
        db.session.commit()
        return True
    
    def set_delivered(self):
        """Marque la commande comme livrée."""
        self.statut = 'livrée'
        self.date_livraison = datetime.utcnow()
        db.session.commit()
        return True
    
    def cancel(self):
        """Annule la commande."""
        if self.statut == 'en attente' or self.statut == 'payée':
            # Remettre les produits en stock
            from app.models.offer import Offer
            
            for item in self.items:
                offer = Offer.query.get(item.offer_id)
                if offer:
                    offer.increase_stock(item.quantite)
            
            self.statut = 'annulée'
            db.session.commit()
            return True
        return False
    
    # Méthode pour compatibilité avec l'ancien code (billets -> non applicable pour les drones)
    def generate_tickets(self, user):
        """Méthode de compatibilité pour l'ancien code, ne fait rien pour les drones."""
        return []
    
    def to_dict(self):
        """Convertit la commande en dictionnaire."""
        return {
            'id': self.id,
            'reference': self.reference,
            'total': self.total,
            'statut': self.statut,
            'date_commande': self.date_commande.isoformat(),
            'date_paiement': self.date_paiement.isoformat() if self.date_paiement else None,
            'date_expedition': self.date_expedition.isoformat() if self.date_expedition else None,
            'date_livraison': self.date_livraison.isoformat() if self.date_livraison else None,
            'numero_suivi': self.numero_suivi,
            'adresse_livraison': self.adresse_livraison,
            'items': [
                {
                    'id': item.id,
                    'drone_id': item.offer_id,
                    'titre': item.offer.titre,
                    'quantite': item.quantite,
                    'prix_unitaire': item.prix_unitaire,
                    'sous_total': item.sous_total()
                } for item in self.items
            ]
        }
    
    def __repr__(self):
        return f"Order(reference='{self.reference}', statut='{self.statut}', total={self.total}€)"