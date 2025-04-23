from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, flash, request
from app import bcrypt
from app.models.user import User
from wtforms import PasswordField, StringField, BooleanField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, Length, NumberRange

class AdminBaseView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'administrateur'
    
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('auth.login', next=request.url))

class UserAdminView(AdminBaseView):
    # Définir les colonnes à afficher dans la liste
    column_list = ('id', 'username', 'email', 'nom', 'prenom', 'role', 'est_verifie')
    
    # Définir les colonnes qui peuvent être triées
    column_sortable_list = ('id', 'username', 'email', 'nom', 'prenom', 'role')
    
    # Définir les colonnes qui peuvent être filtrées
    column_filters = ('username', 'email', 'role', 'est_verifie')
    
    # Définir les colonnes qui peuvent être recherchées
    column_searchable_list = ('username', 'email', 'nom', 'prenom')
    
    # Masquer les colonnes sensibles
    column_exclude_list = ('password', 'cle_securite', 'code_verification', 'code_2fa_secret')
    
    # Ajout de champs personnalisés
    form_args = {
        'username': {
            'label': 'Nom d\'utilisateur',
            'validators': [DataRequired(), Length(min=3, max=20)]
        },
        'email': {
            'label': 'Adresse email',
            'validators': [DataRequired(), Email()]
        },
        'nom': {
            'label': 'Nom',
            'validators': [DataRequired(), Length(min=2, max=50)]
        },
        'prenom': {
            'label': 'Prénom',
            'validators': [DataRequired(), Length(min=2, max=50)]
        },
        'role': {
            'label': 'Rôle'
        },
        'est_verifie': {
            'label': 'Compte vérifié'
        }
    }
    
    # Définir les champs supplémentaires pour le formulaire
    form_extra_fields = {
        'password': PasswordField('Mot de passe')
    }
    
    # Désactiver les modaux pour éviter les problèmes
    create_modal = False
    edit_modal = False
    
    def on_model_change(self, form, model, is_created):
        """Appelé lorsqu'un modèle est créé ou modifié."""
        # Si un mot de passe est fourni, le hacher
        if form.password and form.password.data:
            model.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Si c'est une création, générer la clé de sécurité
        if is_created:
            model.cle_securite = model._generate_security_key()

class OfferAdminView(AdminBaseView):
    # Configurer les colonnes et les options pour les drones
    column_list = ('id', 'titre', 'type', 'niveau', 'prix', 'stock', 'est_publie')
    column_sortable_list = ('id', 'titre', 'type', 'niveau', 'prix', 'stock')
    column_filters = ('type', 'niveau', 'est_publie')
    column_searchable_list = ('titre', 'description')
    
    # Personnaliser les noms des colonnes pour l'interface admin
    column_labels = {
        'titre': 'Modèle',
        'type': 'Type',
        'niveau': 'Niveau',
        'prix': 'Prix (€)',
        'stock': 'Stock',
        'est_publie': 'Publié',
        'autonomie': 'Autonomie (min)',
        'poids': 'Poids (g)',
        'dimensions': 'Dimensions',
        'camera': 'Caméra',
        'portee': 'Portée (m)',
        'vitesse': 'Vitesse max (km/h)'
    }
    
    # Définir les champs du formulaire
    form_columns = (
        'titre', 'description', 'type', 'niveau', 'prix', 'stock', 
        'autonomie', 'poids', 'dimensions', 'camera', 'portee', 'vitesse',
        'image', 'est_publie'
    )
    
    # Champs supplémentaires et validateurs
    form_args = {
        'type': {
            'choices': [
                ('debutant', 'Débutant'),
                ('intermediaire', 'Intermédiaire'),
                ('expert', 'Expert')
            ]
        },
        'niveau': {
            'choices': [
                ('debutant', 'Débutant'),
                ('intermediaire', 'Intermédiaire'),
                ('expert', 'Expert')
            ]
        },
        'prix': {
            'validators': [DataRequired(), NumberRange(min=0)]
        },
        'stock': {
            'validators': [DataRequired(), NumberRange(min=0)]
        },
        'autonomie': {
            'validators': [NumberRange(min=0)]
        },
        'poids': {
            'validators': [NumberRange(min=0)]
        },
        'portee': {
            'validators': [NumberRange(min=0)]
        },
        'vitesse': {
            'validators': [NumberRange(min=0)]
        }
    }
    
    # Désactiver les modaux pour éviter les problèmes
    create_modal = False
    edit_modal = False

class OrderAdminView(AdminBaseView):
    # Configurer les colonnes et les options pour les commandes
    column_list = ('id', 'reference', 'user.username', 'total', 'statut', 'date_commande', 'date_expedition', 'date_livraison')
    column_sortable_list = ('id', 'reference', 'total', 'date_commande')
    column_filters = ('statut',)
    column_searchable_list = ('reference', 'adresse_livraison')
    
    # Les commandes ne peuvent pas être créées manuellement
    can_create = False
    
    # Désactiver les modaux pour éviter les problèmes
    create_modal = False
    edit_modal = False

class OrderItemAdminView(AdminBaseView):
    def titre_formatter(view, context, model, name):
        """Formatter pour afficher le titre de l'offre."""
        return model.offer.titre if model.offer else ""
    
    def reference_formatter(view, context, model, name):
        """Formatter pour afficher la référence de la commande."""
        return model.order.reference if model.order else ""
    
    column_formatters = {
        'titre': titre_formatter,
        'reference': reference_formatter
    }
    
    column_list = ('id', 'reference', 'titre', 'quantite', 'prix_unitaire')
    column_sortable_list = ('id', 'quantite', 'prix_unitaire')
    column_filters = ('order_id', 'offer_id')
    
    # Les items de commande ne peuvent pas être créés manuellement
    can_create = False
    
    # Désactiver les modaux pour éviter les problèmes
    create_modal = False
    edit_modal = False

def init_admin(admin):
    """Initialise l'interface d'administration Flask-Admin"""
    # Importer les modèles
    from app.models.user import User
    from app.models.offer import Offer
    from app.models.order import Order, OrderItem
    from app import db
    
    # Ajouter les vues à l'admin
    admin.add_view(UserAdminView(User, db.session, name="Utilisateurs"))
    admin.add_view(OfferAdminView(Offer, db.session, name="Drones"))
    admin.add_view(OrderAdminView(Order, db.session, name="Commandes"))
    admin.add_view(OrderItemAdminView(OrderItem, db.session, name="Détails commandes"))