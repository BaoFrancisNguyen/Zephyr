from datetime import datetime
from app import db

class StockMovement(db.Model):
    """
    Modèle pour enregistrer les mouvements de stock.
    Utile pour le suivi et l'historique des modifications de stock.
    """
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Qui a effectué le mouvement
    quantity = db.Column(db.Integer, nullable=False)  # Positif pour ajout, négatif pour retrait
    previous_stock = db.Column(db.Integer, nullable=False)  # Stock avant mouvement
    new_stock = db.Column(db.Integer, nullable=False)  # Stock après mouvement
    movement_type = db.Column(db.String(50), nullable=False)  # 'manual', 'sale', 'return', 'inventory', etc.
    reference = db.Column(db.String(100), nullable=True)  # Référence de commande, etc.
    reason = db.Column(db.String(255), nullable=True)  # Raison du mouvement
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    offer = db.relationship('Offer', backref=db.backref('stock_movements', lazy=True))
    user = db.relationship('User', backref=db.backref('stock_movements', lazy=True))
    
    def __init__(self, offer_id, user_id, quantity, previous_stock, new_stock, movement_type, reference=None, reason=None):
        self.offer_id = offer_id
        self.user_id = user_id
        self.quantity = quantity
        self.previous_stock = previous_stock
        self.new_stock = new_stock
        self.movement_type = movement_type
        self.reference = reference
        self.reason = reason
    
    def __repr__(self):
        return f"StockMovement(offer_id={self.offer_id}, quantity={self.quantity}, type={self.movement_type})"

class StockAlert(db.Model):
    """
    Modèle pour configurer des alertes de stock.
    Permet de définir des seuils d'alerte pour chaque produit.
    """
    __tablename__ = 'stock_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False, unique=True)
    min_stock = db.Column(db.Integer, nullable=False, default=5)  # Seuil d'alerte stock bas
    reorder_point = db.Column(db.Integer, nullable=False, default=10)  # Seuil pour recommander
    reorder_quantity = db.Column(db.Integer, nullable=False, default=20)  # Quantité à recommander
    is_active = db.Column(db.Boolean, default=True)  # Alerte activée ou non
    last_notified = db.Column(db.DateTime, nullable=True)  # Dernière notification envoyée
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    offer = db.relationship('Offer', backref=db.backref('stock_alert', uselist=False, lazy=True))
    
    def __init__(self, offer_id, min_stock=5, reorder_point=10, reorder_quantity=20, is_active=True):
        self.offer_id = offer_id
        self.min_stock = min_stock
        self.reorder_point = reorder_point
        self.reorder_quantity = reorder_quantity
        self.is_active = is_active
    
    def should_notify(self, current_stock):
        """
        Détermine si une notification doit être envoyée pour ce produit
        """
        # Si l'alerte n'est pas active, ne pas notifier
        if not self.is_active:
            return False
        
        # Si le stock est inférieur au seuil minimum
        if current_stock <= self.min_stock:
            # Si aucune notification n'a été envoyée ou si la dernière date de plus de 24h
            if self.last_notified is None or \
               (datetime.utcnow() - self.last_notified).total_seconds() > 86400:
                return True
        
        return False
    
    def should_reorder(self, current_stock):
        """
        Détermine si le produit doit être recommandé
        """
        # Si l'alerte n'est pas active, ne pas recommander
        if not self.is_active:
            return False
        
        # Si le stock est inférieur au point de recommande
        return current_stock <= self.reorder_point
    
    def __repr__(self):
        return f"StockAlert(offer_id={self.offer_id}, min_stock={self.min_stock}, reorder_point={self.reorder_point})"

class SupplierOrder(db.Model):
    """
    Modèle pour gérer les commandes fournisseurs.
    """
    __tablename__ = 'supplier_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), nullable=False, unique=True)
    supplier_name = db.Column(db.String(100), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.DateTime, nullable=True)
    delivery_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='created')  # 'created', 'ordered', 'partially_received', 'received', 'cancelled'
    total_amount = db.Column(db.Float, nullable=True)
    shipping_cost = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    items = db.relationship('SupplierOrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    user = db.relationship('User', backref=db.backref('supplier_orders', lazy=True))
    
    def __init__(self, reference, supplier_name, created_by, expected_delivery_date=None, 
                 total_amount=None, shipping_cost=0.0, notes=None):
        self.reference = reference
        self.supplier_name = supplier_name
        self.created_by = created_by
        self.expected_delivery_date = expected_delivery_date
        self.total_amount = total_amount
        self.shipping_cost = shipping_cost
        self.notes = notes
    
    def add_item(self, offer_id, quantity, price):
        """Ajoute un article à la commande fournisseur"""
        item = SupplierOrderItem(
            order_id=self.id,
            offer_id=offer_id,
            quantity=quantity,
            unit_price=price
        )
        db.session.add(item)
        db.session.commit()
        
        # Recalculer le montant total
        self.total_amount = sum(item.quantity * item.unit_price for item in self.items) + self.shipping_cost
        db.session.commit()
        
        return item
    
    def remove_item(self, item_id):
        """Supprime un article de la commande fournisseur"""
        item = SupplierOrderItem.query.get(item_id)
        if not item or item.order_id != self.id:
            return False
        
        db.session.delete(item)
        db.session.commit()
        
        # Recalculer le montant total
        self.total_amount = sum(item.quantity * item.unit_price for item in self.items) + self.shipping_cost
        db.session.commit()
        
        return True
    
    def place_order(self):
        """Place la commande chez le fournisseur"""
        if self.status != 'created':
            return False
        
        self.status = 'ordered'
        self.order_date = datetime.utcnow()
        db.session.commit()
        return True
    
    def receive_order(self, complete=True):
        """Réceptionne la commande"""
        if self.status not in ['ordered', 'partially_received']:
            return False
        
        # Si réception complète
        if complete:
            self.status = 'received'
            self.delivery_date = datetime.utcnow()
            
            # Mettre à jour le stock pour chaque article
            for item in self.items:
                from app.models.offer import Offer
                offer = Offer.query.get(item.offer_id)
                if offer:
                    previous_stock = offer.stock
                    offer.stock += item.quantity
                    
                    # Enregistrer le mouvement de stock
                    movement = StockMovement(
                        offer_id=offer.id,
                        user_id=self.created_by,
                        quantity=item.quantity,
                        previous_stock=previous_stock,
                        new_stock=offer.stock,
                        movement_type='supplier_order',
                        reference=self.reference,
                        reason='Réception commande fournisseur'
                    )
                    db.session.add(movement)
            
            db.session.commit()
            return True
        # Si réception partielle
        else:
            self.status = 'partially_received'
            db.session.commit()
            return True
    
    def cancel_order(self):
        """Annule la commande"""
        if self.status in ['received', 'cancelled']:
            return False
        
        self.status = 'cancelled'
        db.session.commit()
        return True
    
    def __repr__(self):
        return f"SupplierOrder(reference='{self.reference}', status='{self.status}', total_amount={self.total_amount})"

class SupplierOrderItem(db.Model):
    """
    Modèle pour les articles dans une commande fournisseur.
    """
    __tablename__ = 'supplier_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('supplier_orders.id'), nullable=False)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    received_quantity = db.Column(db.Integer, default=0)
    
    # Relations
    offer = db.relationship('Offer', backref=db.backref('supplier_order_items', lazy=True))
    
    def __init__(self, order_id, offer_id, quantity, unit_price):
        self.order_id = order_id
        self.offer_id = offer_id
        self.quantity = quantity
        self.unit_price = unit_price
    
    def receive(self, quantity):
        """Réceptionne une quantité de cet article"""
        if quantity <= 0 or self.received_quantity + quantity > self.quantity:
            return False
        
        from app.models.offer import Offer
        offer = Offer.query.get(self.offer_id)
        order = SupplierOrder.query.get(self.order_id)
        
        if offer and order:
            previous_stock = offer.stock
            offer.stock += quantity
            
            # Enregistrer le mouvement de stock
            movement = StockMovement(
                offer_id=offer.id,
                user_id=order.created_by,
                quantity=quantity,
                previous_stock=previous_stock,
                new_stock=offer.stock,
                movement_type='supplier_order',
                reference=order.reference,
                reason='Réception partielle commande fournisseur'
            )
            db.session.add(movement)
            
            # Mettre à jour la quantité reçue
            self.received_quantity += quantity
            
            # Mettre à jour le statut de la commande si tous les articles sont reçus
            all_received = True
            for item in order.items:
                if item.received_quantity < item.quantity:
                    all_received = False
                    break
            
            if all_received:
                order.status = 'received'
                order.delivery_date = datetime.utcnow()
            else:
                order.status = 'partially_received'
            
            db.session.commit()
            return True
        
        return False
    
    def total_price(self):
        """Calcule le prix total de cet article"""
        return self.quantity * self.unit_price
    
    def __repr__(self):
        return f"SupplierOrderItem(order_id={self.order_id}, offer_id={self.offer_id}, quantity={self.quantity})"

# Extension du modèle Offer pour inclure les fonctionnalités de gestion de stock
def extend_offer_model():
    """
    Ajoute des méthodes à la classe Offer pour gérer le stock
    """
    from app.models.offer import Offer
    
    def adjust_stock(self, quantity, user_id, movement_type, reference=None, reason=None):
        """
        Ajuste le stock d'un produit et enregistre le mouvement
        
        Args:
            quantity: Quantité à ajouter (positive) ou retirer (négative)
            user_id: ID de l'utilisateur effectuant l'ajustement
            movement_type: Type de mouvement (manual, sale, return, etc.)
            reference: Référence associée au mouvement
            reason: Raison de l'ajustement
            
        Returns:
            bool: True si l'opération est réussie, False sinon
        """
        previous_stock = self.stock
        
        # Vérifier que le stock ne devient pas négatif
        if previous_stock + quantity < 0:
            return False
        
        self.stock += quantity
        
        # Enregistrer le mouvement de stock
        movement = StockMovement(
            offer_id=self.id,
            user_id=user_id,
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=self.stock,
            movement_type=movement_type,
            reference=reference,
            reason=reason
        )
        db.session.add(movement)
        db.session.commit()
        
        return True
    
    def get_stock_alert(self):
        """
        Récupère ou crée une alerte de stock pour ce produit
        
        Returns:
            StockAlert: L'alerte de stock associée à ce produit
        """
        alert = StockAlert.query.filter_by(offer_id=self.id).first()
        
        if not alert:
            alert = StockAlert(offer_id=self.id)
            db.session.add(alert)
            db.session.commit()
        
        return alert
    
    def is_low_stock(self):
        """
        Vérifie si le produit est en stock faible
        
        Returns:
            bool: True si le stock est faible, False sinon
        """
        alert = self.get_stock_alert()
        return self.stock <= alert.min_stock
    
    def needs_reorder(self):
        """
        Vérifie si le produit doit être recommandé
        
        Returns:
            bool: True si le produit doit être recommandé, False sinon
        """
        alert = self.get_stock_alert()
        return alert.should_reorder(self.stock)
    
    def get_stock_movements(self, limit=10):
        """
        Récupère les derniers mouvements de stock
        
        Args:
            limit: Nombre maximum de mouvements à récupérer
            
        Returns:
            list: Liste des mouvements de stock
        """
        return StockMovement.query.filter_by(offer_id=self.id).order_by(StockMovement.date_created.desc()).limit(limit).all()
    
    # Ajout des méthodes à la classe Offer
    Offer.adjust_stock = adjust_stock
    Offer.get_stock_alert = get_stock_alert
    Offer.is_low_stock = is_low_stock
    Offer.needs_reorder = needs_reorder
    Offer.get_stock_movements = get_stock_movements