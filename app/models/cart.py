from datetime import datetime
from app import db

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False)  # Garde offer_id pour compatibilité
    quantite = db.Column(db.Integer, default=1)
    prix_unitaire = db.Column(db.Float, nullable=False)
    
    # Relations
    
    offer = db.relationship('Offer', back_populates='cart_items')
    cart = db.relationship('Cart', back_populates='items')
    
    def __init__(self, cart_id, offer_id, quantite, prix_unitaire):
        self.cart_id = cart_id
        self.offer_id = offer_id
        self.quantite = quantite
        self.prix_unitaire = prix_unitaire
    
    def sous_total(self):
        """Calcule le sous-total pour cet élément du panier."""
        return self.quantite * self.prix_unitaire
    
    def __repr__(self):
        return f"CartItem(cart_id={self.cart_id}, offer_id={self.offer_id}, quantite={self.quantite})"

class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    items = db.relationship('CartItem', back_populates='cart', lazy=True, cascade="all, delete-orphan")
    user = db.relationship('User', back_populates='carts')
    
    def __init__(self, user_id):
        self.user_id = user_id
    
    def add_item(self, offer, quantite=1):
        """Ajoute un drone au panier."""
        from app.models.offer import Offer
        
        # Vérifier si l'offre existe
        if isinstance(offer, int):
            offer = Offer.query.get(offer)
        
        if not offer:
            return False
        
        # Vérifier la disponibilité
        if not offer.is_available() or offer.stock < quantite:
            return False
        
        # Vérifier si l'élément existe déjà dans le panier
        item = CartItem.query.filter_by(cart_id=self.id, offer_id=offer.id).first()
        
        if item:
            # Mettre à jour la quantité
            item.quantite += quantite
        else:
            # Créer un nouvel élément
            item = CartItem(
                cart_id=self.id,
                offer_id=offer.id,
                quantite=quantite,
                prix_unitaire=offer.prix
            )
            db.session.add(item)
        
        db.session.commit()
        return True
    
    def update_item(self, item_id, quantite):
        """Met à jour la quantité d'un drone dans le panier."""
        item = CartItem.query.get(item_id)
        
        if not item or item.cart_id != self.id:
            return False
        
        # Vérifier la disponibilité
        if item.offer.stock < quantite:
            return False
        
        if quantite <= 0:
            db.session.delete(item)
        else:
            item.quantite = quantite
        
        db.session.commit()
        return True
    
    def remove_item(self, item_id):
        """Supprime un drone du panier."""
        item = CartItem.query.get(item_id)
        
        if not item or item.cart_id != self.id:
            return False
        
        db.session.delete(item)
        db.session.commit()
        return True
    
    def clear(self):
        """Vide le panier."""
        for item in self.items:
            db.session.delete(item)
        
        db.session.commit()
        return True
    
    def total(self):
        """Calcule le total du panier."""
        return sum(item.sous_total() for item in self.items)
    
    def count_items(self):
        """Compte le nombre total d'articles dans le panier."""
        return sum(item.quantite for item in self.items)
    
    def to_dict(self):
        """Convertit le panier en dictionnaire."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': [
                {
                    'id': item.id,
                    'drone_id': item.offer_id,
                    'titre': item.offer.titre,
                    'type': item.offer.type,
                    'niveau': item.offer.niveau,
                    'quantite': item.quantite,
                    'prix_unitaire': item.prix_unitaire,
                    'sous_total': item.sous_total()
                } for item in self.items
            ],
            'total': self.total(),
            'count': self.count_items()
        }
    
    def __repr__(self):
        return f"Cart(user_id={self.user_id}, items={len(self.items)})"