from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models.order import Order, OrderItem
from app.models.cart import Cart
from app.models.offer import Offer
from app.services.payment_service import process_payment
from datetime import datetime
from app.forms.order_forms import ShippingAddressForm

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/')
@login_required
def index():
    """
    Affiche les commandes de l'utilisateur.
    """
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_commande.desc()).all()
    return render_template('orders/index.html', orders=orders)

@orders_bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    """
    Affiche les détails d'une commande spécifique.
    """
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que l'utilisateur est bien le propriétaire de la commande
    if order.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à accéder à cette commande.', 'danger')
        return redirect(url_for('orders.index'))
    
    return render_template('orders/detail.html', order=order)

@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    Page de finalisation de commande avec formulaire d'adresse.
    """
    # Récupérer le panier de l'utilisateur
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart or not cart.items:
        flash('Votre panier est vide.', 'warning')
        return redirect(url_for('cart.index'))
    
    # Vérifier la disponibilité des articles
    for item in cart.items:
        if not item.offer.is_available() or item.offer.stock < item.quantite:
            flash(f'Le produit "{item.offer.titre}" n\'est plus disponible en quantité suffisante.', 'danger')
            return redirect(url_for('cart.index'))
    
    # Créer le formulaire d'adresse de livraison
    form = ShippingAddressForm()
    
    if form.validate_on_submit():
        # Formater l'adresse de livraison
        shipping_address = f"{form.nom.data} {form.prenom.data}\n{form.adresse.data}\n{form.code_postal.data} {form.ville.data}\n{form.pays.data}\nTél: {form.telephone.data}"
        
        # Créer la commande
        order = Order(
            user_id=current_user.id,
            total=cart.total() + (0 if cart.total() >= 100 else 5.99),  # Ajouter frais de livraison si nécessaire
            adresse_email=form.email.data,
            adresse_livraison=shipping_address
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Ajouter les articles à la commande
        for item in cart.items:
            order.add_item(item.offer, item.quantite, item.prix_unitaire)
            
            # Réduire le stock du produit
            item.offer.decrease_stock(item.quantite)
        
        # Vider le panier
        cart.clear()
        
        # Stocker l'ID de la commande en session pour la page de paiement
        session['order_id_for_payment'] = order.id
        
        # Rediriger vers la page de paiement
        return redirect(url_for('orders.payment'))
    
    return render_template('orders/checkout.html', cart=cart, form=form)

@orders_bp.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    """
    Page de paiement pour une commande.
    """
    # Récupérer l'ID de la commande depuis la session
    order_id = session.get('order_id_for_payment')
    
    if not order_id:
        flash('Aucune commande en attente de paiement.', 'warning')
        return redirect(url_for('orders.index'))
    
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que l'utilisateur est bien le propriétaire de la commande
    if order.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à accéder à cette commande.', 'danger')
        return redirect(url_for('orders.index'))
    
    # Vérifier que la commande n'est pas déjà payée
    if order.statut != 'en attente':
        flash('Cette commande a déjà été traitée.', 'info')
        return redirect(url_for('orders.detail', order_id=order.id))
    
    if request.method == 'POST':
        # Pour la démonstration, nous simulons simplement un paiement réussi
        # Dans une application réelle, vous intégreriez un service de paiement ici
        
        # Marquer la commande comme payée
        order.set_paid()
        
        # Supprimer l'ID de la commande de la session
        session.pop('order_id_for_payment', None)
        
        # Envoyer un email de confirmation (simulé ici)
        # send_confirmation_email(order)
        
        return redirect(url_for('orders.confirmation', order_id=order.id))
    
    return render_template('orders/payment.html', order=order)

@orders_bp.route('/<int:order_id>/confirmation')
@login_required
def confirmation(order_id):
    """
    Page de confirmation après un paiement réussi.
    """
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que l'utilisateur est bien le propriétaire de la commande
    if order.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à accéder à cette commande.', 'danger')
        return redirect(url_for('orders.index'))
    
    # Vérifier que la commande est bien payée
    if order.statut != 'payée':
        flash('Cette commande n\'a pas encore été payée.', 'warning')
        return redirect(url_for('orders.payment'))
    
    return render_template('orders/confirmation.html', order=order)

@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel(order_id):
    """
    Annule une commande (si possible).
    """
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que l'utilisateur est bien le propriétaire de la commande
    if order.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à accéder à cette commande.', 'danger')
        return redirect(url_for('orders.index'))
    
    # Vérifier que la commande peut être annulée (en attente ou payée mais pas expédiée)
    if order.statut not in ['en attente', 'payée']:
        flash('Cette commande ne peut pas être annulée car elle a déjà été expédiée.', 'warning')
        return redirect(url_for('orders.detail', order_id=order.id))
    
    # Annuler la commande
    if order.cancel():
        flash('Commande annulée avec succès. Les produits ont été remis en stock.', 'success')
    else:
        flash('Erreur lors de l\'annulation de la commande.', 'danger')
    
    return redirect(url_for('orders.index'))

@orders_bp.route('/<int:order_id>/track')
@login_required
def track(order_id):
    """
    Page de suivi de commande.
    """
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que l'utilisateur est bien le propriétaire de la commande
    if order.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à accéder à cette commande.', 'danger')
        return redirect(url_for('orders.index'))
    
    # Vérifier que la commande est expédiée
    if order.statut not in ['expédiée', 'livrée']:
        flash('Cette commande n\'est pas encore expédiée.', 'info')
        return redirect(url_for('orders.detail', order_id=order.id))
    
    # Dans une application réelle, vous récupéreriez des informations de suivi 
    # auprès du transporteur avec le numéro de suivi
    tracking_info = {
        'status': order.statut,
        'carrier': 'Transporteur Express',
        'tracking_number': order.numero_suivi or '123456789',
        'estimated_delivery': 'Sous 2-3 jours ouvrés',
        'history': [
            {
                'date': order.date_expedition.strftime('%d/%m/%Y %H:%M'),
                'status': 'Colis expédié',
                'location': 'Centre logistique Paris'
            }
        ]
    }
    
    if order.statut == 'livrée':
        tracking_info['history'].append({
            'date': order.date_livraison.strftime('%d/%m/%Y %H:%M'),
            'status': 'Colis livré',
            'location': 'Adresse de livraison'
        })
    
    return render_template('orders/tracking.html', order=order, tracking_info=tracking_info)