from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.cart import Cart, CartItem
from app.models.offer import Offer

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/')
@login_required
def index():
    """
    Affiche le contenu du panier de l'utilisateur.
    """
    # Récupérer le panier de l'utilisateur
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    # Récupérer des accessoires recommandés
    recommended_accessories = Offer.query.filter(
        Offer.est_publie == True,
        # Supposons que les accessoires ont un prix inférieur à 50€
        Offer.prix < 50
    ).order_by(Offer.date_creation.desc()).limit(3).all()
    
    return render_template('cart/index.html', cart=cart, recommended_accessories=recommended_accessories)

@cart_bp.route('/add/<int:offer_id>', methods=['POST'])
@login_required
def add_to_cart(offer_id):
    """
    Ajoute un article au panier.
    """
    # Récupérer l'offre (drone ou accessoire)
    offer = Offer.query.get_or_404(offer_id)
    
    if not offer.est_publie or not offer.is_available():
        flash('Ce produit n\'est pas disponible.', 'warning')
        return redirect(url_for('offers.index'))
    
    # Récupérer la quantité souhaitée
    quantity = int(request.form.get('quantity', 1))
    
    # Vérifier la validité de la quantité
    if quantity <= 0:
        flash('La quantité doit être positive.', 'danger')
        return redirect(url_for('offers.detail', offer_id=offer_id))
    
    # Vérifier le stock disponible
    if offer.stock < quantity:
        flash(f'Il ne reste que {offer.stock} exemplaires disponibles pour ce produit.', 'warning')
        return redirect(url_for('offers.detail', offer_id=offer_id))
    
    # Récupérer ou créer le panier
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    # Ajouter l'article au panier
    if cart.add_item(offer, quantity):
        flash(f'{quantity} {offer.titre} ajouté(s) au panier.', 'success')
    else:
        flash('Erreur lors de l\'ajout au panier.', 'danger')
    
    # Rediriger vers le panier ou rester sur la page actuelle selon le paramètre
    redirect_param = request.args.get('redirect', 'cart')
    if redirect_param == 'stay':
        return redirect(request.referrer or url_for('offers.index'))
    else:
        return redirect(url_for('cart.index'))

@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_item(item_id):
    """
    Met à jour la quantité d'un article dans le panier.
    """
    # Récupérer le panier de l'utilisateur
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        flash('Votre panier est vide.', 'warning')
        return redirect(url_for('cart.index'))
    
    # Récupérer la nouvelle quantité
    try:
        quantity = int(request.form.get('quantity', 0))
    except ValueError:
        flash('Quantité invalide.', 'danger')
        return redirect(url_for('cart.index'))
    
    # Récupérer l'article du panier
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Vérifier que l'article appartient bien au panier de l'utilisateur
    if cart_item.cart_id != cart.id:
        flash('Cet article n\'appartient pas à votre panier.', 'danger')
        return redirect(url_for('cart.index'))
    
    # Vérifier le stock disponible
    if quantity > cart_item.offer.stock:
        flash(f'Il ne reste que {cart_item.offer.stock} exemplaires disponibles pour ce produit.', 'warning')
        quantity = cart_item.offer.stock
    
    # Mettre à jour l'article
    if cart.update_item(item_id, quantity):
        flash('Panier mis à jour.', 'success')
    else:
        flash('Erreur lors de la mise à jour du panier.', 'danger')
    
    return redirect(url_for('cart.index'))

@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_item(item_id):
    """
    Supprime un article du panier.
    """
    # Récupérer le panier de l'utilisateur
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        flash('Votre panier est vide.', 'warning')
        return redirect(url_for('cart.index'))
    
    # Récupérer l'article du panier
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Vérifier que l'article appartient bien au panier de l'utilisateur
    if cart_item.cart_id != cart.id:
        flash('Cet article n\'appartient pas à votre panier.', 'danger')
        return redirect(url_for('cart.index'))
    
    # Supprimer l'article
    if cart.remove_item(item_id):
        flash('Article supprimé du panier.', 'success')
    else:
        flash('Erreur lors de la suppression de l\'article.', 'danger')
    
    return redirect(url_for('cart.index'))

@cart_bp.route('/clear', methods=['POST'])
@login_required
def clear():
    """
    Vide le panier de l'utilisateur.
    """
    # Récupérer le panier de l'utilisateur
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        flash('Votre panier est déjà vide.', 'info')
        return redirect(url_for('cart.index'))
    
    # Vider le panier
    if cart.clear():
        flash('Votre panier a été vidé.', 'success')
    else:
        flash('Erreur lors de la suppression des articles.', 'danger')
    
    return redirect(url_for('cart.index'))

@cart_bp.route('/api/count')
@login_required
def api_count():
    """
    API pour récupérer le nombre d'articles dans le panier (utilisé pour l'affichage dynamique).
    """
    # Récupérer le panier de l'utilisateur
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    count = 0
    if cart:
        count = cart.count_items()
    
    return jsonify({'count': count})

@cart_bp.route('/api/total')
@login_required
def api_total():
    """
    API pour récupérer le total du panier.
    """
    # Récupérer le panier de l'utilisateur
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    total = 0
    if cart:
        total = cart.total()
    
    # Calculer les frais de livraison
    shipping = 5.99 if total < 100 else 0
    
    return jsonify({
        'subtotal': total,
        'shipping': shipping,
        'total': total + shipping,
        'free_shipping_eligible': total >= 100
    })