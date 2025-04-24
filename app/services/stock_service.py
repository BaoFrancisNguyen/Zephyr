from datetime import datetime, timedelta
from flask import flash, current_app
from app import db
from app.models.offer import Offer
from app.models.stock_model import StockMovement, StockAlert, SupplierOrder, SupplierOrderItem
import uuid
import logging

# Configuration du logger
logger = logging.getLogger('stock_service')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class StockService:
    """
    Service pour la gestion des stocks.
    Centralise toutes les opérations liées aux stocks.
    """
    
    @staticmethod
    def adjust_stock(offer_id, quantity, user_id, movement_type, reference=None, reason=None):
        """
        Ajuste le stock d'un produit et enregistre le mouvement
        
        Args:
            offer_id: ID du produit
            quantity: Quantité à ajouter (positive) ou retirer (négative)
            user_id: ID de l'utilisateur effectuant l'ajustement
            movement_type: Type de mouvement (manual, sale, return, etc.)
            reference: Référence associée au mouvement
            reason: Raison de l'ajustement
            
        Returns:
            bool: True si l'opération est réussie, False sinon
        """
        try:
            offer = Offer.query.get(offer_id)
            if not offer:
                logger.error(f"Produit {offer_id} non trouvé")
                return False
            
            return offer.adjust_stock(quantity, user_id, movement_type, reference, reason)
        except Exception as e:
            logger.error(f"Erreur lors de l'ajustement du stock: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def bulk_adjust_stock(offer_ids, quantity, user_id, movement_type, reference=None, reason=None):
        """
        Ajuste le stock de plusieurs produits
        
        Args:
            offer_ids: Liste des IDs de produits
            quantity: Quantité à ajouter (positive) ou retirer (négative)
            user_id: ID de l'utilisateur effectuant l'ajustement
            movement_type: Type de mouvement (manual, inventory, etc.)
            reference: Référence associée au mouvement
            reason: Raison de l'ajustement
            
        Returns:
            dict: Dictionnaire contenant les résultats de l'opération
        """
        results = {
            'success': [],
            'failed': []
        }
        
        for offer_id in offer_ids:
            success = StockService.adjust_stock(offer_id, quantity, user_id, movement_type, reference, reason)
            if success:
                results['success'].append(offer_id)
            else:
                results['failed'].append(offer_id)
        
        return results
    
    @staticmethod
    def bulk_update_stock(criteria, operation, value, user_id, reason=None):
        """
        Met à jour le stock de plusieurs produits selon des critères
        
        Args:
            criteria: Dictionnaire des critères de filtrage (niveau, type, etc.)
            operation: Type d'opération ('set', 'add', 'subtract', 'percent')
            value: Valeur à appliquer
            user_id: ID de l'utilisateur effectuant l'ajustement
            reason: Raison de l'ajustement
            
        Returns:
            dict: Dictionnaire contenant les résultats de l'opération
        """
        results = {
            'success': [],
            'failed': [],
            'total_updated': 0
        }
        
        # Construire la requête en fonction des critères
        query = Offer.query
        
        if 'niveau' in criteria and criteria['niveau']:
            query = query.filter(Offer.niveau == criteria['niveau'])
        
        if 'type' in criteria and criteria['type']:
            query = query.filter(Offer.type == criteria['type'])
        
        if 'stock_low' in criteria and criteria['stock_low']:
            # Récupérer les produits avec des stocks faibles
            products_with_alerts = db.session.query(Offer.id).join(
                StockAlert, Offer.id == StockAlert.offer_id
            ).filter(
                Offer.stock <= StockAlert.min_stock
            ).all()
            
            product_ids = [p[0] for p in products_with_alerts]
            query = query.filter(Offer.id.in_(product_ids))
        
        # Exécuter l'opération sur chaque produit
        products = query.all()
        reference = f"bulk-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        for product in products:
            try:
                previous_stock = product.stock
                
                # Appliquer l'opération
                if operation == 'set':
                    new_stock = int(value)
                elif operation == 'add':
                    new_stock = previous_stock + int(value)
                elif operation == 'subtract':
                    new_stock = max(0, previous_stock - int(value))
                elif operation == 'percent':
                    adjustment = int(previous_stock * float(value) / 100)
                    new_stock = previous_stock + adjustment
                else:
                    results['failed'].append(product.id)
                    continue
                
                # Vérifier que le stock ne devient pas négatif
                new_stock = max(0, new_stock)
                
                # Calculer la quantité à ajuster
                adjustment = new_stock - previous_stock
                
                # Si aucun changement, passer au produit suivant
                if adjustment == 0:
                    continue
                
                # Mettre à jour le stock
                success = StockService.adjust_stock(
                    product.id, 
                    adjustment, 
                    user_id, 
                    'bulk_update', 
                    reference, 
                    reason or f"Mise à jour en masse ({operation} {value})"
                )
                
                if success:
                    results['success'].append(product.id)
                    results['total_updated'] += 1
                else:
                    results['failed'].append(product.id)
            
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du stock pour le produit {product.id}: {str(e)}")
                results['failed'].append(product.id)
        
        return results
    
    @staticmethod
    def get_low_stock_products(limit=None):
        """
        Récupère les produits avec un stock faible
        
        Args:
            limit: Nombre maximum de produits à récupérer
            
        Returns:
            list: Liste des produits avec un stock faible
        """
        products_with_alerts = db.session.query(Offer).join(
            StockAlert, Offer.id == StockAlert.offer_id
        ).filter(
            Offer.stock <= StockAlert.min_stock,
            Offer.est_publie == True
        )
        
        if limit:
            products_with_alerts = products_with_alerts.limit(limit)
        
        return products_with_alerts.all()
    
    @staticmethod
    def get_out_of_stock_products(limit=None):
        """
        Récupère les produits en rupture de stock
        
        Args:
            limit: Nombre maximum de produits à récupérer
            
        Returns:
            list: Liste des produits en rupture de stock
        """
        query = Offer.query.filter_by(stock=0, est_publie=True)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_top_selling_products(days=30, limit=5):
        """
        Récupère les produits les plus vendus
        
        Args:
            days: Nombre de jours pour le calcul
            limit: Nombre maximum de produits à récupérer
            
        Returns:
            list: Liste des produits les plus vendus avec leur quantité
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer les mouvements de vente
        sales_movements = db.session.query(
            StockMovement.offer_id,
            db.func.sum(StockMovement.quantity.desc()).label('total_sold')
        ).filter(
            StockMovement.movement_type == 'sale',
            StockMovement.date_created >= start_date
        ).group_by(StockMovement.offer_id).order_by(
            db.func.sum(StockMovement.quantity.desc()).desc()
        ).limit(limit).all()
        
        # Récupérer les produits correspondants
        result = []
        for offer_id, total_sold in sales_movements:
            offer = Offer.query.get(offer_id)
            if offer:
                result.append((offer, abs(total_sold)))
        
        return result
    
    @staticmethod
    def create_supplier_order(supplier_name, user_id, items, expected_delivery_date=None, 
                             shipping_cost=0.0, notes=None):
        """
        Crée une commande fournisseur
        
        Args:
            supplier_name: Nom du fournisseur
            user_id: ID de l'utilisateur créant la commande
            items: Liste des articles à commander (dictionaires avec offer_id, quantity, unit_price)
            expected_delivery_date: Date de livraison prévue
            shipping_cost: Frais de livraison
            notes: Notes additionnelles
            
        Returns:
            SupplierOrder: La commande créée, ou None en cas d'erreur
        """
        try:
            # Générer une référence unique
            now = datetime.utcnow()
            reference = f"SO-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            
            # Créer la commande
            order = SupplierOrder(
                reference=reference,
                supplier_name=supplier_name,
                created_by=user_id,
                expected_delivery_date=expected_delivery_date,
                shipping_cost=shipping_cost,
                notes=notes
            )
            
            db.session.add(order)
            db.session.commit()
            
            # Ajouter les articles
            total_amount = 0
            for item in items:
                order_item = SupplierOrderItem(
                    order_id=order.id,
                    offer_id=item['offer_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price']
                )
                db.session.add(order_item)
                total_amount += item['quantity'] * item['unit_price']
            
            # Mettre à jour le montant total
            order.total_amount = total_amount + shipping_cost
            db.session.commit()
            
            return order
        
        except Exception as e:
            logger.error(f"Erreur lors de la création de la commande fournisseur: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_pending_supplier_orders():
        """
        Récupère les commandes fournisseurs en cours
        
        Returns:
            list: Liste des commandes fournisseurs en cours
        """
        return SupplierOrder.query.filter(
            SupplierOrder.status.in_(['created', 'ordered', 'partially_received'])
        ).order_by(SupplierOrder.order_date.desc()).all()
    
    @staticmethod
    def get_stock_movement_history(offer_id=None, days=30, movement_type=None, limit=100):
        """
        Récupère l'historique des mouvements de stock
        
        Args:
            offer_id: ID du produit (optionnel)
            days: Nombre de jours à prendre en compte
            movement_type: Type de mouvement (optionnel)
            limit: Nombre maximum de mouvements à récupérer
            
        Returns:
            list: Liste des mouvements de stock
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = StockMovement.query.filter(StockMovement.date_created >= start_date)
        
        if offer_id:
            query = query.filter_by(offer_id=offer_id)
        
        if movement_type:
            query = query.filter_by(movement_type=movement_type)
        
        return query.order_by(StockMovement.date_created.desc()).limit(limit).all()
    
    @staticmethod
    def process_alerts():
        """
        Traite les alertes de stock et génère des notifications
        
        Returns:
            dict: Dictionnaire contenant les résultats du traitement
        """
        results = {
            'low_stock': [],
            'reorder': []
        }
        
        # Récupérer tous les produits avec leurs alertes
        products_with_alerts = db.session.query(Offer, StockAlert).join(
            StockAlert, Offer.id == StockAlert.offer_id
        ).filter(
            Offer.est_publie == True
        ).all()
        
        for offer, alert in products_with_alerts:
            # Vérifier le stock faible
            if alert.should_notify(offer.stock):
                results['low_stock'].append({
                    'offer_id': offer.id,
                    'titre': offer.titre,
                    'stock': offer.stock,
                    'min_stock': alert.min_stock
                })
                
                # Mettre à jour la date de dernière notification
                alert.last_notified = datetime.utcnow()
                db.session.commit()
            
            # Vérifier si le produit doit être recommandé
            if alert.should_reorder(offer.stock):
                results['reorder'].append({
                    'offer_id': offer.id,
                    'titre': offer.titre,
                    'stock': offer.stock,
                    'reorder_point': alert.reorder_point,
                    'reorder_quantity': alert.reorder_quantity
                })
        
        return results
    
    @staticmethod
    def update_stock_alert(offer_id, min_stock, reorder_point, reorder_quantity, is_active=True):
        """
        Met à jour les paramètres d'alerte de stock
        
        Args:
            offer_id: ID du produit
            min_stock: Seuil d'alerte stock bas
            reorder_point: Seuil pour recommander
            reorder_quantity: Quantité à recommander
            is_active: Alerte activée ou non
            
        Returns:
            StockAlert: L'alerte mise à jour, ou None en cas d'erreur
        """
        try:
            alert = StockAlert.query.filter_by(offer_id=offer_id).first()
            
            if not alert:
                alert = StockAlert(
                    offer_id=offer_id,
                    min_stock=min_stock,
                    reorder_point=reorder_point,
                    reorder_quantity=reorder_quantity,
                    is_active=is_active
                )
                db.session.add(alert)
            else:
                alert.min_stock = min_stock
                alert.reorder_point = reorder_point
                alert.reorder_quantity = reorder_quantity
                alert.is_active = is_active
            
            db.session.commit()
            return alert
        
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'alerte de stock: {str(e)}")
            db.session.rollback()
            return None
