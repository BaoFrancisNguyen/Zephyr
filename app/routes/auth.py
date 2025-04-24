from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models.user import User
from app.services.auth_service import (
    register_user, verify_account, login_user as auth_login_user,
    setup_2fa, verify_2fa_code, change_password,
    reset_password_request, reset_password
)
from app.forms.auth_forms import (
    RegistrationForm, LoginForm, TwoFactorForm,
    ChangePasswordForm, RequestResetForm, ResetPasswordForm
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription."""
    print("⭐ Route register appelée")
    if current_user.is_authenticated:
        print("⭐ Utilisateur déjà authentifié, redirection vers l'accueil")
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    print(f"⭐ Méthode : {request.method}")
    
    if request.method == 'POST':
        print(f"⭐ Données du formulaire : {request.form}")
    
    if form.validate_on_submit():
        print("⭐ Formulaire validé")
        try:
            success, result = register_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                nom=form.nom.data,
                prenom=form.prenom.data
            )
            print(f"⭐ Résultat de register_user : success={success}, result={result}")
            
            if success:
                flash('Votre compte a été créé avec succès. Veuillez vérifier votre email pour activer votre compte.', 'success')
                print("⭐ Redirection vers login")
                return redirect(url_for('auth.login'))
            else:
                flash(result, 'danger')
                print(f"⭐ Erreur : {result}")
        except Exception as e:
            print(f"⭐ Exception : {str(e)}")
            import traceback
            print(traceback.format_exc())
            flash(f"Une erreur s'est produite : {str(e)}", 'danger')
    else:
        print(f"⭐ Erreurs de validation : {form.errors}")
    
    print("⭐ Rendu du template register.html")
    return render_template('auth/register.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    """Page de réinitialisation de mot de passe."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        success, message = reset_password(token, form.password.data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')
            return redirect(url_for('auth.request_reset'))
    
    return render_template('auth/reset_token.html', form=form)


@auth_bp.route('/verify/<code>')
def verify_account_route(code):
    """Route de vérification de compte."""
    success, message = verify_account(code)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('auth.login'))
    else:
        flash(message, 'danger')
        return redirect(url_for('main.index'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        success, result = auth_login_user(
            email=form.email.data,
            password=form.password.data
        )
        
        if success:
            user = result
            
            # Vérifier si l'authentification à deux facteurs est activée
            if user.est_2fa_active:
                # Stocker l'ID utilisateur en session pour la vérification 2FA
                session['user_id_for_2fa'] = user.id
                return redirect(url_for('auth.two_factor'))
            
            remember = form.remember.data
            login_user(user, remember=remember)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash(result, 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/two-factor', methods=['GET', 'POST'])
def two_factor():
    """Page d'authentification à deux facteurs."""
    if current_user.is_authenticated or 'user_id_for_2fa' not in session:
        return redirect(url_for('main.index'))
    
    form = TwoFactorForm()
    
    if form.validate_on_submit():
        user_id = session['user_id_for_2fa']
        user = User.query.get(user_id)
        
        if not user:
            flash('Utilisateur non trouvé.', 'danger')
            return redirect(url_for('auth.login'))
        
        success, message = verify_2fa_code(user, form.code.data)
        
        if success:
            # Supprimer l'ID utilisateur de la session
            session.pop('user_id_for_2fa', None)
            
            # Connecter l'utilisateur
            login_user(user, remember=False)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/two_factor.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion."""
    # Déconnexion de l'utilisateur via Flask-Login
    logout_user()
    
    # Vider complètement la session
    session.clear()
    
    # Supprimer également le cookie de session
    response = redirect(url_for('main.index'))
    response.delete_cookie('remember_token')  # Supprimer le cookie "Se souvenir de moi"
    response.delete_cookie('session')  # Supprimer le cookie de session
    
    flash('Vous avez été déconnecté.', 'info')
    return response

@auth_bp.route('/profile')
@login_required
def profile():
    """Page de profil."""
    return render_template('auth/profile.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password_route():
    """Page de changement de mot de passe."""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        success, message = change_password(
            user=current_user,
            current_password=form.current_password.data,
            new_password=form.new_password.data
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa_route():
    """Page de configuration de l'authentification à deux facteurs."""
    if current_user.est_2fa_active:
        flash('L\'authentification à deux facteurs est déjà activée.', 'info')
        return redirect(url_for('auth.profile'))
    
    success, result = setup_2fa(current_user)
    
    if not success:
        flash(result, 'danger')
        return redirect(url_for('auth.profile'))
    
    # Stocker le secret en session pour la vérification
    session['setup_2fa_secret'] = result['secret']
    
    # Passer à la fois le secret et l'URI du QR code au template
    return render_template('auth/setup_2fa.html', 
                           uri=result['uri'], 
                           secret=result['secret'])

@auth_bp.route('/verify-2fa', methods=['POST'])
@login_required
def verify_2fa_setup():
    """Vérification de la configuration de l'authentification à deux facteurs."""
    if 'setup_2fa_secret' not in session:
        flash('Session expirée. Veuillez recommencer la configuration.', 'danger')
        return redirect(url_for('auth.setup_2fa_route'))
    
    code = request.form.get('code')
    
    if not code:
        flash('Veuillez fournir un code.', 'danger')
        return redirect(url_for('auth.setup_2fa_route'))
    
    # Vérifier le code
    import pyotp
    totp = pyotp.TOTP(session['setup_2fa_secret'])
    
    if totp.verify(code):
        # Activer l'authentification à deux facteurs
        current_user.code_2fa_secret = session['setup_2fa_secret']
        current_user.enable_2fa()
        
        # Supprimer le secret de la session
        session.pop('setup_2fa_secret', None)
        
        flash('L\'authentification à deux facteurs a été activée avec succès.', 'success')
        return redirect(url_for('auth.profile'))
    else:
        flash('Code incorrect. Veuillez réessayer.', 'danger')
        return redirect(url_for('auth.setup_2fa_route'))

@auth_bp.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    """Désactivation de l'authentification à deux facteurs."""
    if not current_user.est_2fa_active:
        flash('L\'authentification à deux facteurs n\'est pas activée.', 'info')
        return redirect(url_for('auth.profile'))
    
    current_user.disable_2fa()
    current_user.code_2fa_secret = None
    db.session.commit()
    
    flash('L\'authentification à deux facteurs a été désactivée avec succès.', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def request_reset():
    """Page de demande de réinitialisation de mot de passe."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestResetForm()
    
    if form.validate_on_submit():
        success, message = reset_password_request(form.email.data)
        flash(message, 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/request_reset.html', form=form)