from app import db
from app.models.user import User
from app.models.offer import Offer
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, BaseView, expose
from flask_admin.base import AdminIndexView
from flask_login import current_user
from flask import redirect, url_for, flash, request
import datetime

# Vue personnalisée pour la page d'accueil admin
class AdminHomeView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'administrateur'
    
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('auth.login', next=request.url))

# Vue de base pour toutes les vues d'administration
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'administrateur'
    
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('auth.login', next=request.url))

# Vue personnalisée pour les utilisateurs
class UserModelView(SecureModelView):
    # Colonnes à afficher dans la liste
    column_list = ('id', 'username', 'email', 'nom', 'prenom', 'role', 'est_verifie', 'date_creation', 'derniere_connexion')
    
    # Colonnes pouvant être triées
    column_sortable_list = ('id', 'username', 'email', 'nom', 'prenom', 'role', 'date_creation', 'derniere_connexion')
    
    # Colonnes pouvant être filtrées
    column_filters = ('username', 'email', 'role', 'est_verifie', 'date_creation')
    
    # Colonnes pouvant être recherchées
    column_searchable_list = ('username', 'email', 'nom', 'prenom')
    
    # Empêcher la modification de certains champs sensibles
    form_excluded_columns = ('password', 'cle_securite', 'code_verification', 'code_2fa_secret')
    
    # Personnaliser les libellés des colonnes
    column_labels = {
        'username': 'Nom d\'utilisateur',
        'email': 'Email',
        'nom': 'Nom',
        'prenom': 'Prénom',
        'role': 'Rôle',
        'est_verifie': 'Vérifié',
        'est_2fa_active': '2FA Activé',
        'date_creation': 'Date d\'inscription',
        'derniere_connexion': 'Dernière connexion'
    }
    
    # Formater les dates
    column_formatters = {
        'date_creation': lambda v, c, m, p: m.date_creation.strftime('%d/%m/%Y %H:%M') if m.date_creation else '',
        'derniere_connexion': lambda v, c, m, p: m.derniere_connexion.strftime('%d/%m/%Y %H:%M') if m.derniere_connexion else 'Jamais'
    }
    
    # Configurations d'édition
    form_choices = {
        'role': [
            ('utilisateur', 'Utilisateur'),
            ('employe', 'Employé'),
            ('administrateur', 'Administrateur')
        ]
    }

# Vue personnalisée pour les offres (drones)
class OfferModelView(SecureModelView):
    column_list = ('id', 'titre', 'type', 'niveau', 'prix', 'stock', 'est_publie', 'date_creation')
    column_sortable_list = ('id', 'titre', 'type', 'niveau', 'prix', 'stock', 'date_creation')
    column_filters = ('titre', 'type', 'niveau', 'prix', 'est_publie')
    column_searchable_list = ('titre', 'description')
    
    column_labels = {
        'titre': 'Modèle',
        'description': 'Description',
        'type': 'Type',
        'niveau': 'Niveau',
        'prix': 'Prix (€)',
        'stock': 'Stock',
        'est_publie': 'Publié',
        'date_creation': 'Date de création',
        'autonomie': 'Autonomie (min)',
        'poids': 'Poids (g)',
        'dimensions': 'Dimensions',
        'camera': 'Caméra',
        'portee': 'Portée (m)',
        'vitesse': 'Vitesse max (km/h)'
    }
    
    form_choices = {
        'type': [
            ('debutant', 'Débutant'),
            ('intermediaire', 'Intermédiaire'),
            ('expert', 'Expert')
        ],
        'niveau': [
            ('debutant', 'Débutant'),
            ('intermediaire', 'Intermédiaire'),
            ('expert', 'Expert')
        ]
    }
    
    create_modal = False
    edit_modal = False

# Vue personnalisée pour les commandes
class OrderModelView(SecureModelView):
    column_list = ('id', 'reference', 'user.username', 'total', 'statut', 'date_commande', 'date_paiement', 'date_expedition')
    column_sortable_list = ('id', 'reference', 'total', 'statut', 'date_commande')
    column_filters = ('reference', 'statut', 'date_commande', 'date_paiement', 'date_expedition')
    column_searchable_list = ('reference', 'adresse_livraison')
    
    column_labels = {
        'reference': 'Référence',
        'user.username': 'Client',
        'total': 'Total (€)',
        'statut': 'Statut',
        'date_commande': 'Date de commande',
        'date_paiement': 'Date de paiement',
        'date_expedition': 'Date d\'expédition',
        'date_livraison': 'Date de livraison',
        'adresse_email': 'Email',
        'adresse_livraison': 'Adresse de livraison',
        'numero_suivi': 'N° de suivi'
    }
    
    form_choices = {
        'statut': [
            ('en attente', 'En attente'),
            ('payée', 'Payée'),
            ('expédiée', 'Expédiée'),
            ('livrée', 'Livrée'),
            ('annulée', 'Annulée')
        ]
    }
    
    # Empêcher la création manuelle de commandes
    can_create = False
    
    # Formater les dates
    column_formatters = {
        'date_commande': lambda v, c, m, p: m.date_commande.strftime('%d/%m/%Y %H:%M') if m.date_commande else '',
        'date_paiement': lambda v, c, m, p: m.date_paiement.strftime('%d/%m/%Y %H:%M') if m.date_paiement else '',
        'date_expedition': lambda v, c, m, p: m.date_expedition.strftime('%d/%m/%Y %H:%M') if m.date_expedition else '',
        'date_livraison': lambda v, c, m, p: m.date_livraison.strftime('%d/%m/%Y %H:%M') if m.date_livraison else ''
    }
    
# Vue personnalisée pour les items de commande
class OrderItemModelView(SecureModelView):
    column_list = ('id', 'order.reference', 'offer.titre', 'quantite', 'prix_unitaire', 'sous_total')
    column_sortable_list = ('id', 'quantite', 'prix_unitaire')
    column_filters = ('order_id', 'offer_id', 'quantite')
    
    column_labels = {
        'order.reference': 'Référence commande',
        'offer.titre': 'Produit',
        'quantite': 'Quantité',
        'prix_unitaire': 'Prix unitaire (€)',
        'sous_total': 'Sous-total (€)'
    }
    
    # Calculer le sous-total
    column_formatters = {
        'sous_total': lambda v, c, m, p: f"{m.quantite * m.prix_unitaire:.2f}"
    }
    
    # Empêcher la création manuelle d'items de commande
    can_create = False
    can_edit = False

# Vue personnalisée pour la gestion des stocks
class StockView(BaseView):
    @expose('/')
    def index(self):
        # Obtenir les produits avec stock faible
        low_stock_products = Offer.query.filter(Offer.stock <= 5, Offer.est_publie == True).all()
        
        # Obtenir les produits épuisés
        out_of_stock_products = Offer.query.filter(Offer.stock == 0, Offer.est_publie == True).all()
        
        # Obtenir les produits les plus vendus
        # Cette requête est simplifiée, dans un environnement réel elle serait plus complexe
        top_selling_products = db.session.query(
            Offer,
            db.func.sum(OrderItem.quantite).label('total_sold')
        ).join(OrderItem).group_by(Offer).order_by(db.desc('total_sold')).limit(5).all()
        
        return self.render('admin/stock.html', 
                          low_stock_products=low_stock_products,
                          out_of_stock_products=out_of_stock_products,
                          top_selling_products=top_selling_products)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'administrateur'
    
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('auth.login', next=request.url))

# Vue personnalisée pour les statistiques
class StatsView(BaseView):
    @expose('/')
    def index(self):
        # Statistiques générales
        total_users = User.query.count()
        total_offers = Offer.query.count()
        total_orders = Order.query.count()
        
        # Calcul du chiffre d'affaires total
        total_revenue = db.session.query(db.func.sum(Order.total)).filter(Order.statut == 'payée').scalar() or 0
        
        # Statistiques par mois (6 derniers mois)
        today = datetime.datetime.today()
        six_months_ago = today - datetime.timedelta(days=180)
        
        monthly_stats = []
        for i in range(6):
            month_start = today.replace(day=1) - datetime.timedelta(days=i*30)
            month_end = (month_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
            
            month_orders = Order.query.filter(
                Order.date_commande >= month_start,
                Order.date_commande <= month_end,
                Order.statut == 'payée'
            ).count()
            
            month_revenue = db.session.query(db.func.sum(Order.total)).filter(
                Order.date_commande >= month_start,
                Order.date_commande <= month_end,
                Order.statut == 'payée'
            ).scalar() or 0
            
            monthly_stats.append({
                'month': month_start.strftime('%B %Y'),
                'orders': month_orders,
                'revenue': month_revenue
            })
        
        # Statistiques par type de drone
        drone_stats = db.session.query(
            Offer.niveau,
            db.func.count(OrderItem.id).label('total_sold')
        ).join(OrderItem).group_by(Offer.niveau).all()
        
        # Statistiques par statut de commande
        order_status_stats = db.session.query(
            Order.statut,
            db.func.count(Order.id).label('count')
        ).group_by(Order.statut).all()
        
        return self.render('admin/stats.html', 
                          total_users=total_users,
                          total_offers=total_offers,
                          total_orders=total_orders,
                          total_revenue=total_revenue,
                          monthly_stats=monthly_stats,
                          drone_stats=drone_stats,
                          order_status_stats=order_status_stats)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'administrateur'
    
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('auth.login', next=request.url))

# Fonction pour initialiser l'administration
def init_admin(admin):
    # Ajouter les vues à l'administration
    admin.add_view(UserModelView(User, db.session, name="Utilisateurs", category="Gestion"))
    admin.add_view(OfferModelView(Offer, db.session, name="Drones", category="Gestion"))
    admin.add_view(OrderModelView(Order, db.session, name="Commandes", category="Gestion"))
    admin.add_view(OrderItemModelView(OrderItem, db.session, name="Détails commandes", category="Gestion"))
    admin.add_view(StockView(name="Gestion des stocks", endpoint="stock", category="Inventaire"))
    admin.add_view(StatsView(name="Statistiques", endpoint="stats"))