from datetime import datetime
import uuid
import hashlib
from flask import current_app
from flask_login import UserMixin
from app import db, login_manager, bcrypt

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    cle_securite = db.Column(db.String(255), unique=True, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    derniere_connexion = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(20), default='utilisateur')
    est_verifie = db.Column(db.Boolean, default=False)
    code_verification = db.Column(db.String(100), nullable=True)
    code_2fa_secret = db.Column(db.String(32), nullable=True)
    est_2fa_active = db.Column(db.Boolean, default=False)
    
    # Relations
    carts = db.relationship('Cart', back_populates='user', lazy=True)
    orders = db.relationship('Order', back_populates='user', lazy=True)
    tickets = db.relationship('Ticket', back_populates='user', lazy=True)
    
    def __init__(self, username, email, password, nom, prenom, role='utilisateur', est_verifie=False):
        self.username = username
        self.email = email
        self.nom = nom
        self.prenom = prenom
        self.password = password
        self.role = role
        self.est_verifie = est_verifie
        self.cle_securite = self._generate_security_key()
        
    def _generate_security_key(self):
        """Génère une clé de sécurité unique pour l'utilisateur."""
        key_material = f"{uuid.uuid4()}{self.email}{datetime.utcnow().timestamp()}{current_app.config['SALT_KEY']}"
        return hashlib.sha256(key_material.encode()).hexdigest()
    
    def check_password(self, password):
        """Vérifie si le mot de passe fourni correspond au mot de passe haché stocké."""
        return bcrypt.check_password_hash(self.password, password)
    
    def update_last_login(self):
        """Met à jour la date de dernière connexion."""
        self.derniere_connexion = datetime.utcnow()
        db.session.commit()
    
    def is_admin(self):
        """Vérifie si l'utilisateur est un administrateur."""
        return self.role == 'administrateur'
    
    def generate_verification_code(self):
        """Génère un code de vérification pour l'activation du compte."""
        code = str(uuid.uuid4())
        self.code_verification = code
        db.session.commit()
        return code
    
    def verify_account(self):
        """Active le compte de l'utilisateur."""
        self.est_verifie = True
        self.code_verification = None
        db.session.commit()
    
    def generate_2fa_secret(self):
        """Génère un secret pour l'authentification à deux facteurs."""
        import pyotp
        self.code_2fa_secret = pyotp.random_base32()
        db.session.commit()
        return self.code_2fa_secret
    
    def verify_2fa_code(self, code):
        """Vérifie un code d'authentification à deux facteurs."""
        import pyotp
        if not self.code_2fa_secret:
            return False
        totp = pyotp.TOTP(self.code_2fa_secret)
        return totp.verify(code)
    
    def enable_2fa(self):
        """Active l'authentification à deux facteurs."""
        self.est_2fa_active = True
        db.session.commit()
    
    def disable_2fa(self):
        """Désactive l'authentification à deux facteurs."""
        self.est_2fa_active = False
        db.session.commit()
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"
