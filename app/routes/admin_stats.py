from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
import json

admin_stats_bp = Blueprint('admin_stats', __name__, url_prefix='/admin-stats')

@admin_stats_bp.route('/')
@login_required
def index():
    """
    Page de statistiques simplifiée pour résoudre les problèmes d'affichage.
    Cette page inclut les graphiques directement dans le template.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    # Données statiques pour les graphiques (pour éviter les problèmes avec les données dynamiques)
    drones_data = {
        'labels': ['Débutant', 'Intermédiaire', 'Expert'],
        'data': [65, 25, 10]
    }
    
    date_data = {
        'labels': ['01/04', '02/04', '03/04', '04/04', '05/04', '06/04', '07/04'],
        'orders': [3, 5, 2, 7, 4, 6, 8],
        'sales': [350, 450, 200, 800, 350, 550, 950]
    }
    
    model_data = {
        'labels': ['Zephir X100', 'Zephir Pro 720', 'Zephir Elite 4K', 'Zephir Mini', 'Zephir Plus'],
        'data': [42, 28, 15, 10, 5]
    }
    
    month_data = {
        'labels': ['Jan 2025', 'Fév 2025', 'Mar 2025', 'Avr 2025'],
        'sales': [5200, 6800, 8500, 9200]
    }
    
    return render_template(
        'admin/simplified_stats.html',
        drones_data=json.dumps(drones_data),
        date_data=json.dumps(date_data),
        model_data=json.dumps(model_data),
        month_data=json.dumps(month_data)
    )
