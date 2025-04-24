from flask_admin import AdminIndexView, expose
from flask_login import current_user
from flask import redirect, url_for, flash, request

class AdminHomeView(AdminIndexView):
    """Vue personnalisée pour la page d'accueil de l'admin."""
    
    # Ajout de la méthode avec un décorateur @expose pour définir la vue par défaut
    @expose('/')
    def index(self):
        # Rediriger vers le dashboard personnalisé au lieu de la page d'accueil par défaut
        if current_user.is_authenticated and current_user.role == 'administrateur':
            return redirect(url_for('admin_custom.index'))
        return super(AdminHomeView, self).index()
    
    def is_accessible(self):
        """Vérifie si l'utilisateur a accès à la vue admin."""
        return current_user.is_authenticated and current_user.role == 'administrateur'
    
    def inaccessible_callback(self, name, **kwargs):
        """Callback appelé lorsque l'utilisateur n'a pas accès."""
        flash('Accès refusé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('auth.login', next=request.url))