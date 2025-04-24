from flask import Blueprint, render_template
from flask_login import login_required, current_user

admin_links_bp = Blueprint('admin_links', __name__, url_prefix='/admin-links')

@admin_links_bp.route('/')
@login_required
def index():
    """
    Page d'accès rapide à toutes les sections d'administration.
    """
    # Vérifier que l'utilisateur est administrateur
    if current_user.role != 'administrateur':
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('admin/links.html')
