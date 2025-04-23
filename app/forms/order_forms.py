from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Regexp
from flask_login import current_user
from datetime import datetime

class ShippingAddressForm(FlaskForm):
    """
    Formulaire pour l'adresse de livraison
    """
    nom = StringField('Nom', validators=[
        DataRequired(message="Le nom est requis"),
        Length(min=2, max=50, message="Le nom doit contenir entre 2 et 50 caractères")
    ])
    
    prenom = StringField('Prénom', validators=[
        DataRequired(message="Le prénom est requis"),
        Length(min=2, max=50, message="Le prénom doit contenir entre 2 et 50 caractères")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message="L'email est requis"),
        Email(message="Veuillez entrer une adresse email valide")
    ])
    
    telephone = StringField('Téléphone', validators=[
        DataRequired(message="Le numéro de téléphone est requis"),
        Regexp(r'^\+?[0-9]{10,15}$', message="Veuillez entrer un numéro de téléphone valide")
    ])
    
    adresse = TextAreaField('Adresse', validators=[
        DataRequired(message="L'adresse est requise"),
        Length(min=5, max=200, message="L'adresse doit contenir entre 5 et 200 caractères")
    ])
    
    code_postal = StringField('Code postal', validators=[
        DataRequired(message="Le code postal est requis"),
        Regexp(r'^[0-9]{5}$', message="Le code postal doit contenir 5 chiffres")
    ])
    
    ville = StringField('Ville', validators=[
        DataRequired(message="La ville est requise"),
        Length(min=2, max=50, message="La ville doit contenir entre 2 et 50 caractères")
    ])
    
    pays = SelectField('Pays', choices=[
        ('FR', 'France'),
        ('BE', 'Belgique'),
        ('CH', 'Suisse'),
        ('LU', 'Luxembourg'),
        ('DE', 'Allemagne'),
        ('ES', 'Espagne'),
        ('IT', 'Italie'),
        ('GB', 'Royaume-Uni'),
    ], validators=[DataRequired(message="Le pays est requis")])
    
    commentaire = TextAreaField('Commentaires pour la livraison (optionnel)', validators=[
        Length(max=500, message="Le commentaire ne doit pas dépasser 500 caractères")
    ])
    
    submit = SubmitField('Continuer vers le paiement')
    
    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm, self).__init__(*args, **kwargs)
        # Pré-remplir les champs avec les informations de l'utilisateur connecté si disponibles
        if current_user.is_authenticated and not self.is_submitted():
            self.nom.data = current_user.nom
            self.prenom.data = current_user.prenom
            self.email.data = current_user.email

class PaymentForm(FlaskForm):
    """
    Formulaire pour les informations de paiement
    """
    card_holder = StringField('Nom du titulaire', validators=[
        DataRequired(message="Le nom du titulaire est requis"),
        Length(min=2, max=100, message="Le nom doit contenir entre 2 et 100 caractères")
    ])
    
    card_number = StringField('Numéro de carte', validators=[
        DataRequired(message="Le numéro de carte est requis"),
        Regexp(r'^[0-9]{16}$', message="Le numéro de carte doit contenir 16 chiffres")
    ])
    
    expiry_month = SelectField('Mois d\'expiration', choices=[
        ('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'),
        ('05', '05'), ('06', '06'), ('07', '07'), ('08', '08'),
        ('09', '09'), ('10', '10'), ('11', '11'), ('12', '12')
    ], validators=[DataRequired(message="Le mois d'expiration est requis")])
    
    expiry_year = SelectField('Année d\'expiration', choices=[
        ('2025', '2025'), ('2026', '2026'), ('2027', '2027'), ('2028', '2028'),
        ('2029', '2029'), ('2030', '2030'), ('2031', '2031'), ('2032', '2032')
    ], validators=[DataRequired(message="L'année d'expiration est requise")])
    
    cvv = StringField('Code de sécurité (CVV)', validators=[
        DataRequired(message="Le code de sécurité est requis"),
        Regexp(r'^[0-9]{3,4}$', message="Le code de sécurité doit contenir 3 ou 4 chiffres")
    ])
    
    save_card = SelectField('Enregistrer cette carte pour mes prochains achats', choices=[
        ('0', 'Non'),
        ('1', 'Oui')
    ], default='0')
    
    submit = SubmitField('Payer maintenant')
    
    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        # Générer dynamiquement les années d'expiration à partir de l'année courante
        current_year = datetime.utcnow().year
        years = [(str(current_year + i), str(current_year + i)) for i in range(8)]  # 8 ans à partir de l'année courante
        self.expiry_year.choices = years
    
    def validate_expiry_date(self, form, field):
        """
        Vérifie que la date d'expiration n'est pas passée.
        Cette méthode est appelée après la validation de chaque champ.
        """
        try:
            month = int(self.expiry_month.data)
            year = int(self.expiry_year.data)
            
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            if year < current_year or (year == current_year and month < current_month):
                raise ValidationError('La date d\'expiration est dépassée.')
        except ValueError:
            pass  # Les autres validateurs s'occuperont de ce cas
