from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.offer import Offer
from app.models.cart import Cart

offers_bp = Blueprint('offers', __name__, url_prefix='/offers')

@offers_bp.route('/')
def index():
    """
    Affiche tous les drones disponibles.
    """
    # Récupérer le niveau de drone sélectionné (filtre)
    drone_niveau = request.args.get('type')
    
    # Récupérer les drones en fonction du niveau sélectionné
    if drone_niveau and drone_niveau in ['debutant', 'intermediaire', 'expert']:
        drones = Offer.query.filter_by(est_publie=True, niveau=drone_niveau).all()
    else:
        drones = Offer.query.filter_by(est_publie=True).all()
    
    return render_template('offers/index.html', drones=drones, selected_type=drone_niveau)

@offers_bp.route('/<int:offer_id>')
def detail(offer_id):
    """
    Affiche les détails d'un drone spécifique.
    """
    drone = Offer.query.get_or_404(offer_id)
    
    # Vérifier si le drone est publié
    if not drone.est_publie:
        flash('Ce drone n\'est pas disponible.', 'warning')
        return redirect(url_for('offers.index'))
    
    # Préparer les caractéristiques pour l'affichage
    drone.features = []
    if drone.autonomie:
        drone.features.append(f"Autonomie: {drone.autonomie} minutes")
    if drone.poids:
        drone.features.append(f"Poids: {drone.poids} g")
    if drone.portee:
        drone.features.append(f"Portée: {drone.portee} m")
    if drone.vitesse:
        drone.features.append(f"Vitesse max: {drone.vitesse} km/h")
    
    # Récupérer des drones similaires (même niveau ou type)
    similar_drones = Offer.query.filter(
        Offer.id != drone.id,
        Offer.est_publie == True,
        (Offer.niveau == drone.niveau) | (Offer.type == drone.type)
    ).limit(4).all()
    
    return render_template('offers/detail.html', drone=drone, similar_drones=similar_drones)

@offers_bp.route('/add-to-cart/<int:offer_id>', methods=['POST'])
@login_required
def add_to_cart(offer_id):
    """
    Ajoute un drone au panier de l'utilisateur.
    """
    drone = Offer.query.get_or_404(offer_id)
    
    # Vérifier si le drone est publié et disponible
    if not drone.est_publie or not drone.is_available():
        flash('Ce drone n\'est pas disponible.', 'warning')
        return redirect(url_for('offers.detail', offer_id=offer_id))
    
    # Récupérer la quantité souhaitée
    quantity = int(request.form.get('quantity', 1))
    
    # Vérifier que la quantité est valide
    if quantity <= 0:
        flash('La quantité doit être positive.', 'danger')
        return redirect(url_for('offers.detail', offer_id=offer_id))
    
    # Vérifier la disponibilité
    if drone.stock < quantity:
        flash(f'Il ne reste que {drone.stock} unités disponibles pour ce drone.', 'warning')
        return redirect(url_for('offers.detail', offer_id=offer_id))
    
    # Récupérer le panier de l'utilisateur ou en créer un
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    # Ajouter le drone au panier
    if cart.add_item(drone, quantity):
        flash(f'{quantity} drone(s) {drone.titre} ajouté(s) au panier.', 'success')
    else:
        flash('Erreur lors de l\'ajout au panier.', 'danger')
    
    return redirect(url_for('cart.index'))

@offers_bp.route('/api/drones')
def api_drones():
    """
    API pour récupérer les drones (utilisé pour le filtrage dynamique).
    """
    # Récupérer le niveau de drone sélectionné (filtre)
    drone_niveau = request.args.get('type')
    
    # Récupérer les drones en fonction du niveau sélectionné
    if drone_niveau and drone_niveau in ['debutant', 'intermediaire', 'expert']:
        drones = Offer.query.filter_by(est_publie=True, niveau=drone_niveau).all()
    else:
        drones = Offer.query.filter_by(est_publie=True).all()
    
    # Convertir les drones en dictionnaires
    drones_data = [drone.to_dict() for drone in drones]
    
    return jsonify(drones_data)

@offers_bp.route('/categories/<category>')
def category(category):
    """
    Affiche les drones par catégorie.
    """
    if category not in ['debutant', 'intermediaire', 'expert', 'accessoires']:
        flash('Catégorie non valide.', 'warning')
        return redirect(url_for('offers.index'))
    
    if category == 'accessoires':
        # Logique pour les accessoires (à implémenter)
        accessories = []  # Remplacer par la logique pour récupérer les accessoires
        return render_template('offers/accessories.html', accessories=accessories)
    else:
        # Filtrer les drones par niveau
        drones = Offer.query.filter_by(est_publie=True, niveau=category).all()
        return render_template('offers/index.html', drones=drones, selected_type=category, 
                              category_title=category.capitalize())

@offers_bp.route('/search')
def search():
    """
    Recherche de drones.
    """
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('offers.index'))
    
    # Recherche dans les titres et descriptions
    drones = Offer.query.filter(
        Offer.est_publie == True,
        (Offer.titre.ilike(f'%{query}%') | Offer.description.ilike(f'%{query}%'))
    ).all()
    
    return render_template('offers/search_results.html', drones=drones, query=query)