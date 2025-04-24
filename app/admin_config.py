from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, flash, request
from app import bcrypt
from app.models.user import User
from app.models.offer import Offer
from app.models.order import Order, OrderItem
from wtforms import PasswordField, StringField, BooleanField, SelectField, IntegerField, FloatField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from flask_wtf.file import FileAllowed

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
    
    # Définir les champs de formulaire
    form_columns = ('username', 'email', 'nom', 'prenom', 'role', 'est_verifie')
    
    # Désactiver les modaux pour éviter les problèmes
    create_modal = False
    edit_modal = False
    
    # Définir les champs supplémentaires pour le formulaire
    form_extra_fields = {
        'password': PasswordField('Mot de passe')
    }
    
    # Options de formulaire
    form_choices = {
        'role': [
            ('utilisateur', 'Utilisateur'),
            ('employe', 'Employé'),
            ('administrateur', 'Administrateur')
        ]
    }
    
    def on_model_change(self, form, model, is_created):
        """Appelé lorsqu'un modèle est créé ou modifié."""
        # Si un mot de passe est fourni, le hacher
        if form.password and form.password.data:
            model.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Si c'est une création, générer la clé de sécurité
        if is_created and not hasattr(model, 'cle_securite') or not model.cle_securite:
            model.cle_securite = model._generate_security_key()

class OfferAdminView(AdminBaseView):
    # Activer explicitement la création
    can_create = True
    can_edit = True
    can_delete = True
    
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
        'vitesse': 'Vitesse max (km/h)',
        'description': 'Description'
    }
    
    # Définir les champs du formulaire
    form_columns = (
        'titre', 'description', 'type', 'niveau', 'prix', 'stock', 
        'autonomie', 'poids', 'dimensions', 'camera', 'portee', 'vitesse',
        'est_publie'
    )
    
    # Ajout d'un champ d'image au formulaire
    form_extra_fields = {
        'image_upload': FileField('Image du drone', validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement!')
        ])
    }
    
    # Création de champs personnalisés avec des types adaptés
    form_overrides = {
        'description': TextAreaField,
        'dimensions': StringField,
        'camera': StringField
    }
    
    # Valeurs par défaut et options pour les champs à choix
    form_args = {
        'description': {
            'validators': [DataRequired()],
            'render_kw': {'rows': 5}
        },
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
        }
    }
    
    # Désactiver les modaux pour éviter les problèmes
    create_modal = False
    edit_modal = False
    
    def on_model_change(self, form, model, is_created):
        """Gestion des champs supplémentaires comme l'image upload"""
        if form.image_upload.data:
            # Gérer l'upload d'image
            from werkzeug.utils import secure_filename
            import os
            from flask import current_app
            
            filename = secure_filename(form.image_upload.data.filename)
            if filename:
                # Créer le dossier d'upload s'il n'existe pas
                upload_folder = os.path.join(current_app.static_folder, 'images')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                # Sauvegarder l'image
                filepath = os.path.join(upload_folder, filename)
                form.image_upload.data.save(filepath)
                
                # Mettre à jour le chemin de l'image dans le modèle
                model.image = filename

class OrderAdminView(AdminBaseView):
    # Configurer les colonnes et les options pour les commandes
    column_list = ('id', 'reference', 'user.username', 'total', 'statut', 'date_commande', 'date_paiement')
    column_sortable_list = ('id', 'reference', 'total', 'statut', 'date_commande')
    column_filters = ('statut',)
    column_searchable_list = ('reference',)
    
    # Les commandes ne peuvent pas être créées manuellement
    can_create = False
    
    # Désactiver les modaux pour éviter les problèmes
    create_modal = False
    edit_modal = False
    
    # Personnaliser les libellés des colonnes
    column_labels = {
        'id': 'ID',
        'reference': 'Référence',
        'user.username': 'Utilisateur',
        'total': 'Total (€)',
        'statut': 'Statut',
        'date_commande': 'Date de commande',
        'date_paiement': 'Date de paiement',
        'date_expedition': 'Date d\'expédition',
        'adresse_livraison': 'Adresse de livraison'
    }
    
    # Définir les champs du formulaire d'édition
    form_columns = (
        'statut', 'numero_suivi'
    )
    
    form_choices = {
        'statut': [
            ('en attente', 'En attente'),
            ('payée', 'Payée'),
            ('expédiée', 'Expédiée'),
            ('livrée', 'Livrée'),
            ('annulée', 'Annulée')
        ]
    }

class OrderItemAdminView(AdminBaseView):
    # Ne pas permettre l'édition directe des éléments de commande
    can_create = False
    can_edit = False
    can_delete = False
    
    column_list = ('id', 'order.reference', 'offer.titre', 'quantite', 'prix_unitaire', 'sous_total')
    column_labels = {
        'id': 'ID',
        'order.reference': 'Référence commande',
        'offer.titre': 'Produit',
        'quantite': 'Quantité',
        'prix_unitaire': 'Prix unitaire (€)',
        'sous_total': 'Sous-total (€)'
    }
    
    column_formatters = {
        'sous_total': lambda v, c, m, p: f"{m.quantite * m.prix_unitaire:.2f} €"
    }
    
    column_sortable_list = ('id', 'quantite', 'prix_unitaire')
    column_filters = ('order.id', 'offer.id')

def init_admin(admin):
    """Initialise l'interface d'administration Flask-Admin"""
    # Importer les modèles
    from app.models.user import User
    from app.models.offer import Offer
    from app.models.order import Order, OrderItem
    from app.models.cart import Cart, CartItem
    from app import db
    
    # Ajouter les vues à l'admin
    admin.add_view(UserAdminView(User, db.session, name="Utilisateurs"))
    
    # Modifié pour correspondre exactement à l'URL que vous recevez
    admin.add_view(OfferAdminView(Offer, db.session, name="Drones", endpoint="offer", url="/admin/offer"))
    
    admin.add_view(OrderAdminView(Order, db.session, name="Commandes"))
    admin.add_view(OrderItemAdminView(OrderItem, db.session, name="Détails commandes"))