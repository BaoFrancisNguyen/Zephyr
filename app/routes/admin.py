from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.offer import Offer
from app.models.order import Order, OrderItem
from app.models.ticket import Ticket
from app.models.stock_model import StockMovement, StockAlert, SupplierOrder, SupplierOrderItem
from app.services.stock_service import StockService
from app.forms.admin_forms import OfferForm, UserForm
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename
from flask import current_app

# Utiliser un préfixe d'URL différent pour éviter les conflits avec Flask-Admin
admin_bp = Blueprint('admin_custom', __name__, url_prefix='/admin-custom')

# Routes pour l'administration
@admin_bp.route('/')
@login_required
def index():
    """
    Tableau de bord administrateur amélioré.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Statistiques générales
    total_users = User.query.count()
    total_offers = Offer.query.count()
    total_orders = Order.query.count()
    total_tickets = Ticket.query.count()
    
    # Statistiques des offres
    offers_stats = db.session.query(
        Offer.type,
        db.func.count(Ticket.id).label('tickets_count')
    ).outerjoin(Ticket).group_by(Offer.type).all()
    
    offers_stats_dict = {
        'solo': 0,
        'duo': 0,
        'familiale': 0
    }
    
    for offer_type, count in offers_stats:
        offers_stats_dict[offer_type] = count
    
    # Commandes récentes
    recent_orders = Order.query.filter_by(statut='payée').order_by(Order.date_commande.desc()).limit(5).all()
    
    # Statistiques de ventes
    # Calculer le chiffre d'affaires des 30 derniers jours
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.statut == 'payée',
        Order.date_commande >= thirty_days_ago
    ).scalar() or 0
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_offers=total_offers,
        total_orders=total_orders,
        total_tickets=total_tickets,
        offers_stats=offers_stats_dict,
        recent_orders=recent_orders,
        recent_revenue=recent_revenue
    )

@admin_bp.route('/offers')
@login_required
def offers():
    """
    Gestion des offres.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    offers = Offer.query.all()
    return render_template('admin/offers.html', offers=offers)

@admin_bp.route('/offers/new', methods=['GET', 'POST'])
@login_required
def new_offer():
    """
    Création d'une nouvelle offre.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    form = OfferForm()
    
    if form.validate_on_submit():
        offer = Offer(
            titre=form.titre.data,
            description=form.description.data,
            type=form.type.data,
            niveau=form.niveau.data,
            prix=form.prix.data,
            stock=form.stock.data,
            est_publie=form.est_publie.data,
            autonomie=form.autonomie.data,
            poids=form.poids.data,
            dimensions=form.dimensions.data,
            camera=form.camera.data,
            portee=form.portee.data,
            vitesse=form.vitesse.data
        )
        
        # Traitement de l'image
        if form.image.data:
            # Code pour sauvegarder l'image
            filename = secure_filename(form.image.data.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(file_path)
            offer.image = filename
        
        db.session.add(offer)
        db.session.commit()
        
        # Créer une alerte de stock par défaut pour le nouveau produit
        StockService.update_stock_alert(
            offer_id=offer.id,
            min_stock=5,
            reorder_point=10,
            reorder_quantity=20,
            is_active=True
        )
        
        flash(f'Drone "{offer.titre}" créé avec succès.', 'success')
        return redirect(url_for('admin_custom.offers'))
    
    return render_template('admin/offer_form.html', form=form, title='Nouveau drone')

@admin_bp.route('/offers/<int:offer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_offer(offer_id):
    """
    Modification d'une offre existante.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    offer = Offer.query.get_or_404(offer_id)
    form = OfferForm(obj=offer)
    
    if form.validate_on_submit():
        # Enregistrer l'ancien stock pour le mouvement de stock si nécessaire
        old_stock = offer.stock
        
        offer.titre = form.titre.data
        offer.description = form.description.data
        offer.type = form.type.data
        offer.niveau = form.niveau.data
        offer.prix = form.prix.data
        offer.stock = form.stock.data
        offer.est_publie = form.est_publie.data
        offer.autonomie = form.autonomie.data
        offer.poids = form.poids.data
        offer.dimensions = form.dimensions.data
        offer.camera = form.camera.data
        offer.portee = form.portee.data
        offer.vitesse = form.vitesse.data
        
        # Traitement de l'image
        if form.image.data:
            # Code pour sauvegarder l'image
            filename = secure_filename(form.image.data.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(file_path)
            offer.image = filename
        
        # Enregistrer les modifications de base
        db.session.commit()
        
        # Si le stock a changé, enregistrer un mouvement
        if old_stock != form.stock.data:
            adjustment = form.stock.data - old_stock
            StockService.adjust_stock(
                offer_id=offer.id,
                quantity=adjustment,
                user_id=current_user.id,
                movement_type='admin_edit',
                reason=f"Modification administrative du stock"
            )
        
        flash(f'Drone "{offer.titre}" modifié avec succès.', 'success')
        return redirect(url_for('admin_custom.offers'))
    
    return render_template('admin/offer_form.html', form=form, offer=offer, title='Modifier le drone')

@admin_bp.route('/offers/<int:offer_id>/delete', methods=['POST'])
@login_required
def delete_offer(offer_id):
    """
    Suppression d'une offre.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    offer = Offer.query.get_or_404(offer_id)
    
    # Vérifier si l'offre a des billets associés
    if offer.tickets:
        flash(f'Impossible de supprimer le drone "{offer.titre}" car il a des billets associés.', 'danger')
        return redirect(url_for('admin_custom.offers'))
    
    # Vérifier s'il y a des commandes en cours contenant ce produit
    if OrderItem.query.filter_by(offer_id=offer_id).count() > 0:
        flash(f'Impossible de supprimer le drone "{offer.titre}" car il est présent dans des commandes.', 'danger')
        return redirect(url_for('admin_custom.offers'))
    
    db.session.delete(offer)
    db.session.commit()
    
    flash(f'Drone "{offer.titre}" supprimé avec succès.', 'success')
    return redirect(url_for('admin_custom.offers'))

@admin_bp.route('/users')
@login_required
def users():
    """
    Gestion des utilisateurs.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    """
    Création d'un nouvel utilisateur.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    from app import bcrypt
    form = UserForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            nom=form.nom.data,
            prenom=form.prenom.data,
            role=form.role.data,
            est_verifie=form.est_verifie.data
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Utilisateur "{user.username}" créé avec succès.', 'success')
        return redirect(url_for('admin_custom.users'))
    
    return render_template('admin/user_form.html', form=form, title='Nouvel utilisateur')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """
    Modification d'un utilisateur existant.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    from app import bcrypt
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    # Ne pas exiger le mot de passe en édition
    form.password.validators = []
    form.confirm_password.validators = []
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.nom = form.nom.data
        user.prenom = form.prenom.data
        user.role = form.role.data
        user.est_verifie = form.est_verifie.data
        
        # Changer le mot de passe uniquement s'il est fourni
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        db.session.commit()
        
        flash(f'Utilisateur "{user.username}" modifié avec succès.', 'success')
        return redirect(url_for('admin_custom.users'))
    
    # Vider les champs de mot de passe pour l'affichage
    form.password.data = ''
    form.confirm_password.data = ''
    
    return render_template('admin/user_form.html', form=form, user=user, title='Modifier l\'utilisateur')

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """
    Suppression d'un utilisateur.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Empêcher la suppression de son propre compte
    if user_id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin_custom.users'))
    
    user = User.query.get_or_404(user_id)
    
    # Vérifier si l'utilisateur a des commandes ou des billets associés
    if user.orders or user.tickets:
        flash(f'Impossible de supprimer l\'utilisateur "{user.username}" car il a des commandes ou des billets associés.', 'danger')
        return redirect(url_for('admin_custom.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Utilisateur "{user.username}" supprimé avec succès.', 'success')
    return redirect(url_for('admin_custom.users'))

@admin_bp.route('/orders')
@login_required
def orders():
    """
    Gestion des commandes.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    orders = Order.query.all()
    return render_template('admin/orders.html', orders=orders)

@admin_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """
    Détail d'une commande.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_order_status(order_id):
    """
    Mise à jour du statut d'une commande.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status not in ['en attente', 'payée', 'expédiée', 'livrée', 'annulée']:
        flash('Statut de commande invalide.', 'danger')
        return redirect(url_for('admin_custom.order_detail', order_id=order_id))
    
    # Si passage à annulé, remettre les produits en stock
    if new_status == 'annulée' and order.statut != 'annulée':
        for item in order.items:
            # Remettre en stock
            StockService.adjust_stock(
                item.offer_id,
                item.quantite,  # Ajouter au stock
                current_user.id,
                'order_cancelled',
                reference=order.reference,
                reason=f"Annulation de la commande {order.reference}"
            )
    
    # Si passage à expédiée, mettre à jour la date d'expédition
    if new_status == 'expédiée' and order.statut != 'expédiée':
        order.date_expedition = datetime.utcnow()
        
        # Ajouter le numéro de suivi si fourni
        tracking_number = request.form.get('tracking_number')
        if tracking_number:
            order.numero_suivi = tracking_number
    
    # Si passage à livrée, mettre à jour la date de livraison
    if new_status == 'livrée' and order.statut != 'livrée':
        order.date_livraison = datetime.utcnow()
    
    order.statut = new_status
    db.session.commit()
    
    flash(f'Statut de la commande mis à jour: {new_status}', 'success')
    return redirect(url_for('admin_custom.order_detail', order_id=order_id))

@admin_bp.route('/tickets')
@login_required
def tickets():
    """
    Gestion des billets.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    tickets = Ticket.query.all()
    return render_template('admin/tickets.html', tickets=tickets)

@admin_bp.route('/stats')
@login_required
def stats():
    """
    Statistiques avancées.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Statistiques générales
    total_users = User.query.count()
    total_offers = Offer.query.count()
    total_orders = Order.query.count()
    
    # Calcul du chiffre d'affaires total
    total_revenue = db.session.query(db.func.sum(Order.total)).filter(Order.statut == 'payée').scalar() or 0
    
    # Statistiques mensuelles (6 derniers mois)
    monthly_stats = []
    today = datetime.today()
    
    for i in range(6):
        month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        if i == 0:
            month_end = today
        else:
            next_month = month_start.replace(month=month_start.month+1) if month_start.month < 12 else month_start.replace(year=month_start.year+1, month=1)
            month_end = next_month - timedelta(days=1)
        
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
    
    # Inverser pour avoir l'ordre chronologique
    monthly_stats.reverse()
    
    # Statistiques par type de drone
    drone_stats = db.session.query(
        Offer.niveau,
        db.func.count(OrderItem.id).label('total_sold')
    ).join(OrderItem, Offer.id == OrderItem.offer_id).group_by(Offer.niveau).all()
    
    # Statistiques par statut de commande
    order_status_stats = db.session.query(
        Order.statut,
        db.func.count(Order.id).label('count')
    ).group_by(Order.statut).all()
    
    return render_template(
        'admin/stats.html',
        total_users=total_users,
        total_offers=total_offers,
        total_orders=total_orders,
        total_revenue=total_revenue,
        monthly_stats=monthly_stats,
        drone_stats=drone_stats,
        order_status_stats=order_status_stats
    )

@admin_bp.route('/stock')
@login_required
def stock():
    """
    Gestion des stocks.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Obtenir les produits avec stock faible
    low_stock_products = StockService.get_low_stock_products()
    
    # Obtenir les produits épuisés
    out_of_stock_products = StockService.get_out_of_stock_products()
    
    # Obtenir les produits les plus vendus
    top_selling_products = StockService.get_top_selling_products(days=30, limit=5)
    
    # Date actuelle pour l'affichage
    now = datetime.utcnow()
    
    return render_template(
        'admin/stock.html',
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products,
        top_selling_products=top_selling_products,
        now=now
    )

@admin_bp.route('/stock/history')
@login_required
def stock_history():
    """
    Historique des mouvements de stock.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Paramètres de filtrage
    offer_id = request.args.get('offer_id', type=int)
    movement_type = request.args.get('type')
    days = request.args.get('days', 30, type=int)
    
    # Récupérer l'historique
    movements = StockService.get_stock_movement_history(
        offer_id=offer_id,
        days=days, 
        movement_type=movement_type
    )
    
    # Liste des produits pour le filtre
    products = Offer.query.filter_by(est_publie=True).all()
    
    # Types de mouvements pour le filtre
    movement_types = [
        ('manual', 'Ajustement manuel'),
        ('sale', 'Vente'),
        ('return', 'Retour'),
        ('supplier_order', 'Commande fournisseur'),
        ('inventory', 'Inventaire'),
        ('bulk_update', 'Mise à jour en masse'),
        ('admin_edit', 'Modification administrative'),
        ('order_cancelled', 'Commande annulée')
    ]
    
    return render_template(
        'admin/stock_history.html',
        movements=movements,
        products=products,
        movement_types=movement_types,
        selected_product=offer_id,
        selected_type=movement_type,
        selected_days=days
    )

@admin_bp.route('/stock/supplier-orders')
@login_required
def supplier_orders():
    """
    Gestion des commandes fournisseurs.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Récupérer les commandes
    orders = SupplierOrder.query.order_by(SupplierOrder.order_date.desc()).all()
    
    return render_template('admin/supplier_orders.html', orders=orders)

@admin_bp.route('/stock/supplier-orders/new', methods=['GET', 'POST'])
@login_required
def new_supplier_order():
    """
    Création d'une commande fournisseur.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        data = request.form
        
        supplier_name = data.get('supplier_name')
        shipping_cost = float(data.get('shipping_cost', 0))
        expected_delivery_date = datetime.strptime(data.get('expected_delivery_date'), '%Y-%m-%d') if data.get('expected_delivery_date') else None
        notes = data.get('notes')
        
        # Récupérer les articles
        items = []
        item_count = int(data.get('item_count', 0))
        
        for i in range(item_count):
            offer_id = int(data.get(f'item[{i}][offer_id]'))
            quantity = int(data.get(f'item[{i}][quantity]'))
            unit_price = float(data.get(f'item[{i}][unit_price]'))
            
            items.append({
                'offer_id': offer_id,
                'quantity': quantity,
                'unit_price': unit_price
            })
        
        # Créer la commande
        order = StockService.create_supplier_order(
            supplier_name=supplier_name,
            user_id=current_user.id,
            items=items,
            expected_delivery_date=expected_delivery_date,
            shipping_cost=shipping_cost,
            notes=notes
        )
        
        if order:
            flash('Commande fournisseur créée avec succès.', 'success')
            return redirect(url_for('admin_custom.supplier_orders'))
        else:
            flash('Erreur lors de la création de la commande fournisseur.', 'danger')
    
    # Liste des produits pour le formulaire
    products = Offer.query.filter_by(est_publie=True).all()
    
    return render_template('admin/new_supplier_order.html', products=products)

@admin_bp.route('/api/stock/adjust', methods=['POST'])
@login_required
def api_adjust_stock():
    """
    API pour ajuster le stock d'un produit.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403
    
    data = request.get_json()
    
    offer_id = data.get('offer_id')
    quantity = data.get('quantity')
    reason = data.get('reason', 'Ajustement manuel')
    
    if not offer_id or quantity is None:
        return jsonify({'success': False, 'message': 'Paramètres manquants'}), 400
    
    # Calculer la quantité à ajuster (différence entre nouvelle et ancienne)
    offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
    
    adjustment = int(quantity) - offer.stock
    
    # Aucun changement
    if adjustment == 0:
        return jsonify({'success': True, 'message': 'Aucun changement nécessaire'})
    
    success = StockService.adjust_stock(
        offer_id=offer_id,
        quantity=adjustment,
        user_id=current_user.id,
        movement_type='manual',
        reason=reason
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Stock ajusté avec succès',
            'new_stock': offer.stock
        })
    else:
        return jsonify({'success': False, 'message': 'Erreur lors de l\'ajustement du stock'}), 500

@admin_bp.route('/api/stock/bulk-update', methods=['POST'])
@login_required
def api_bulk_update_stock():
    """
    API pour mettre à jour le stock de plusieurs produits.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403
    
    data = request.get_json()
    
    operation = data.get('operation')
    value = data.get('value')
    criteria = data.get('criteria', {})
    reason = data.get('reason', 'Mise à jour en masse')
    
    if not operation or value is None:
        return jsonify({'success': False, 'message': 'Paramètres manquants'}), 400
    
    results = StockService.bulk_update_stock(
        criteria=criteria,
        operation=operation,
        value=value,
        user_id=current_user.id,
        reason=reason
    )
    
    return jsonify({
        'success': True,
        'message': f"{results['total_updated']} produits mis à jour avec succès",
        'results': results
    })

@admin_bp.route('/stock/supplier-orders/<int:order_id>', methods=['GET'])
@login_required
def supplier_order_detail(order_id):
    """
    Détail d'une commande fournisseur.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    order = SupplierOrder.query.get_or_404(order_id)
    return render_template('admin/supplier_order_detail.html', order=order)

@admin_bp.route('/stock/supplier-orders/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_supplier_order_status(order_id):
    """
    Mise à jour du statut d'une commande fournisseur.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    order = SupplierOrder.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status not in ['en attente', 'confirmée', 'expédiée', 'reçue', 'annulée']:
        flash('Statut de commande invalide.', 'danger')
        return redirect(url_for('admin_custom.supplier_order_detail', order_id=order_id))
    
    # Si passage à reçue, mettre à jour le stock et la date de réception
    if new_status == 'reçue' and order.status != 'reçue':
        order.received_date = datetime.utcnow()
        
        # Mettre à jour le stock pour chaque article
        for item in order.items:
            StockService.adjust_stock(
                offer_id=item.offer_id,
                quantity=item.quantity,
                user_id=current_user.id,
                movement_type='supplier_order',
                reference=f"SO-{order.id}",
                reason=f"Réception de la commande fournisseur #{order.id}"
            )
    
    # Si passage à annulée et était confirmée, prévenir l'admin
    if new_status == 'annulée' and order.status == 'confirmée':
        flash('Attention: Une commande fournisseur confirmée a été annulée.', 'warning')
    
    order.status = new_status
    db.session.commit()
    
    flash(f'Statut de la commande fournisseur mis à jour: {new_status}', 'success')
    return redirect(url_for('admin_custom.supplier_order_detail', order_id=order_id))

@admin_bp.route('/stock/alerts')
@login_required
def stock_alerts():
    """
    Gestion des alertes de stock.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Récupérer toutes les alertes
    alerts = StockAlert.query.join(Offer).filter(Offer.est_publie == True).all()
    
    return render_template('admin/stock_alerts.html', alerts=alerts)

@admin_bp.route('/stock/alerts/<int:alert_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_stock_alert(alert_id):
    """
    Modification d'une alerte de stock.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    alert = StockAlert.query.get_or_404(alert_id)
    
    if request.method == 'POST':
        min_stock = int(request.form.get('min_stock', 0))
        reorder_point = int(request.form.get('reorder_point', 0))
        reorder_quantity = int(request.form.get('reorder_quantity', 0))
        is_active = bool(request.form.get('is_active', False))
        
        if min_stock < 0 or reorder_point < 0 or reorder_quantity <= 0:
            flash('Les valeurs doivent être positives.', 'danger')
        else:
            StockService.update_stock_alert(
                alert_id=alert.id,
                min_stock=min_stock,
                reorder_point=reorder_point,
                reorder_quantity=reorder_quantity,
                is_active=is_active
            )
            
            flash('Alerte de stock mise à jour avec succès.', 'success')
            return redirect(url_for('admin_custom.stock_alerts'))
    
    return render_template('admin/edit_stock_alert.html', alert=alert)

@admin_bp.route('/api/stock/alerts/<int:alert_id>', methods=['PUT'])
@login_required
def api_update_alert(alert_id):
    """
    API pour mettre à jour une alerte de stock.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403
    
    data = request.get_json()
    
    min_stock = data.get('min_stock')
    reorder_point = data.get('reorder_point')
    reorder_quantity = data.get('reorder_quantity')
    is_active = data.get('is_active')
    
    if min_stock is None or reorder_point is None or reorder_quantity is None or is_active is None:
        return jsonify({'success': False, 'message': 'Paramètres manquants'}), 400
    
    success = StockService.update_stock_alert(
        alert_id=alert_id,
        min_stock=min_stock,
        reorder_point=reorder_point,
        reorder_quantity=reorder_quantity,
        is_active=is_active
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Alerte de stock mise à jour'})
    else:
        return jsonify({'success': False, 'message': 'Erreur lors de la mise à jour'}), 500

@admin_bp.route('/reports')
@login_required
def reports():
    """
    Rapports administratifs.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('admin/reports.html')

@admin_bp.route('/reports/sales', methods=['GET'])
@login_required
def sales_report():
    """
    Rapport des ventes.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Paramètres de filtrage
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = datetime.today() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = datetime.today()
    
    # Requête pour les ventes par jour
    daily_sales = db.session.query(
        db.func.date(Order.date_commande).label('date'),
        db.func.count(Order.id).label('orders'),
        db.func.sum(Order.total).label('revenue')
    ).filter(
        Order.statut == 'payée',
        Order.date_commande >= start_date,
        Order.date_commande <= end_date
    ).group_by(db.func.date(Order.date_commande)).order_by(db.func.date(Order.date_commande)).all()
    
    # Requête pour les ventes par produit
    product_sales = db.session.query(
        Offer.id,
        Offer.titre,
        db.func.sum(OrderItem.quantite).label('quantity'),
        db.func.sum(OrderItem.prix_unitaire * OrderItem.quantite).label('revenue')
    ).join(OrderItem, Offer.id == OrderItem.offer_id
    ).join(Order, OrderItem.order_id == Order.id
    ).filter(
        Order.statut == 'payée',
        Order.date_commande >= start_date,
        Order.date_commande <= end_date
    ).group_by(Offer.id).order_by(db.func.sum(OrderItem.quantite).desc()).all()
    
    # Totaux
    total_orders = db.session.query(db.func.count(Order.id)).filter(
        Order.statut == 'payée',
        Order.date_commande >= start_date,
        Order.date_commande <= end_date
    ).scalar() or 0
    
    total_revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.statut == 'payée',
        Order.date_commande >= start_date,
        Order.date_commande <= end_date
    ).scalar() or 0
    
    return render_template(
        'admin/sales_report.html',
        daily_sales=daily_sales,
        product_sales=product_sales,
        total_orders=total_orders,
        total_revenue=total_revenue,
        start_date=start_date,
        end_date=end_date
    )

@admin_bp.route('/reports/stock', methods=['GET'])
@login_required
def stock_report():
    """
    Rapport de stock.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Valeur totale du stock
    total_stock_value = db.session.query(
        db.func.sum(Offer.prix * Offer.stock)
    ).filter(Offer.est_publie == True).scalar() or 0
    
    # Mouvement de stock (30 derniers jours)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    stock_movement = db.session.query(
        StockMovement.movement_type,
        db.func.sum(StockMovement.quantity).label('total_quantity')
    ).filter(StockMovement.movement_date >= thirty_days_ago
    ).group_by(StockMovement.movement_type).all()
    
    # Produits hors stock avec demande
    out_of_stock_demanded = db.session.query(
        Offer
    ).filter(
        Offer.stock == 0,
        Offer.est_publie == True,
        Offer.id.in_(
            db.session.query(OrderItem.offer_id).distinct()
            .join(Order)
            .filter(Order.date_commande >= thirty_days_ago)
        )
    ).all()
    
    # Stocks excédentaires (produits avec beaucoup de stock mais peu de ventes)
    excess_stock = db.session.query(
        Offer,
        db.func.coalesce(db.func.sum(OrderItem.quantite), 0).label('sales')
    ).outerjoin(
        OrderItem, Offer.id == OrderItem.offer_id
    ).outerjoin(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Offer.est_publie == True,
        Offer.stock > 20,
        db.or_(
            Order.date_commande >= thirty_days_ago,
            Order.date_commande == None
        )
    ).group_by(Offer.id
    ).having(db.func.coalesce(db.func.sum(OrderItem.quantite), 0) < 5
    ).all()
    
    return render_template(
        'admin/stock_report.html',
        total_stock_value=total_stock_value,
        stock_movement=stock_movement,
        out_of_stock_demanded=out_of_stock_demanded,
        excess_stock=excess_stock
    )

@admin_bp.route('/reports/customers', methods=['GET'])
@login_required
def customers_report():
    """
    Rapport sur les clients.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Clients les plus actifs (par nombre de commandes)
    top_customers_by_orders = db.session.query(
        User,
        db.func.count(Order.id).label('order_count'),
        db.func.sum(Order.total).label('total_spent')
    ).join(Order, User.id == Order.user_id
    ).filter(Order.statut == 'payée'
    ).group_by(User.id
    ).order_by(db.func.count(Order.id).desc()
    ).limit(10).all()
    
    # Clients les plus dépensiers
    top_customers_by_spend = db.session.query(
        User,
        db.func.count(Order.id).label('order_count'),
        db.func.sum(Order.total).label('total_spent')
    ).join(Order, User.id == Order.user_id
    ).filter(Order.statut == 'payée'
    ).group_by(User.id
    ).order_by(db.func.sum(Order.total).desc()
    ).limit(10).all()
    
    # Nouveaux clients (30 derniers jours)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_customers = User.query.filter(User.date_inscription >= thirty_days_ago).count()
    
    # Total des clients
    total_customers = User.query.filter(User.role == 'client').count()
    
    return render_template(
        'admin/customers_report.html',
        top_customers_by_orders=top_customers_by_orders,
        top_customers_by_spend=top_customers_by_spend,
        new_customers=new_customers,
        total_customers=total_customers
    )

@admin_bp.route('/export/sales-csv', methods=['GET'])
@login_required
def export_sales_csv():
    """
    Exporter les données de ventes au format CSV.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Paramètres de filtrage
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = datetime.today() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = datetime.today()
    
    # Requête pour les commandes
    orders = Order.query.filter(
        Order.statut == 'payée',
        Order.date_commande >= start_date,
        Order.date_commande <= end_date
    ).order_by(Order.date_commande).all()
    
    # Générer le CSV
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # En-tête
    writer.writerow([
        'ID', 'Référence', 'Date', 'Client', 'Email', 
        'Total', 'Statut', 'Produits', 'Quantité'
    ])
    
    # Lignes
    for order in orders:
        products = []
        quantities = []
        
        for item in order.items:
            offer = Offer.query.get(item.offer_id)
            products.append(offer.titre if offer else f"Produit {item.offer_id}")
            quantities.append(str(item.quantite))
        
        writer.writerow([
            order.id,
            order.reference,
            order.date_commande.strftime('%Y-%m-%d %H:%M'),
            f"{order.user.nom} {order.user.prenom}" if order.user else "Utilisateur inconnu",
            order.user.email if order.user else "",
            order.total,
            order.statut,
            ", ".join(products),
            ", ".join(quantities)
        ])
    
    # Renvoyer le fichier
    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=ventes_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
    }

@admin_bp.route('/settings')
@login_required
def settings():
    """
    Paramètres administratifs.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Obtenir les paramètres depuis la base de données ou un fichier de configuration
    # Exemple simple avec des valeurs codées en dur
    settings = {
        'site_name': 'Drone Store',
        'contact_email': 'contact@dronestore.com',
        'orders_email': 'orders@dronestore.com',
        'tax_rate': 20.0,
        'shipping_cost': 9.99,
        'free_shipping_threshold': 99.0,
        'allow_guest_checkout': True,
        'maintenance_mode': False
    }
    
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """
    Mise à jour des paramètres.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Récupérer les données du formulaire
    data = request.form
    
    # Mettre à jour les paramètres (exemple)
    # Dans une application réelle, vous utiliseriez un modèle de base de données
    # ou un fichier de configuration
    
    flash('Paramètres mis à jour avec succès.', 'success')
    return redirect(url_for('admin_custom.settings'))

# Enregistrer le blueprint dans l'application
# Cette ligne doit être dans app/__init__.py, pas ici
# from app.routes.admin_routes import admin_bp
# app.register_blueprint(admin_bp)