from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError, Email
from datetime import datetime

# admin_forms.py (extrait)
class OfferForm(FlaskForm):
    """
    Formulaire de création/modification d'un drone.
    """
    titre = StringField('Titre', validators=[
        DataRequired(),
        Length(min=5, max=100)
    ])
    
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    
    type = SelectField('Type', choices=[
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('expert', 'Expert')
    ], validators=[DataRequired()])
    
    prix = FloatField('Prix (€)', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    
    stock = IntegerField('Stock disponible', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images uniquement')
    ])
    
    autonomie = IntegerField('Autonomie (minutes)', validators=[NumberRange(min=0)])
    poids = IntegerField('Poids (grammes)', validators=[NumberRange(min=0)])
    dimensions = StringField('Dimensions')
    camera = StringField('Caméra')
    portee = IntegerField('Portée (mètres)', validators=[NumberRange(min=0)])
    vitesse = IntegerField('Vitesse max (km/h)', validators=[NumberRange(min=0)])
    niveau = SelectField('Niveau', choices=[
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('expert', 'Expert')
    ])
    
    est_publie = BooleanField('Publier le drone')
    
    submit = SubmitField('Enregistrer')

class UserForm(FlaskForm):
    """
    Formulaire de modification d'un utilisateur.
    """
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(),
        Length(min=3, max=20)
    ])
    
    email = StringField('Adresse email', validators=[
        DataRequired(),
        Email()
    ])
    
    nom = StringField('Nom', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    
    prenom = StringField('Prénom', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    
    role = SelectField('Rôle', choices=[
        ('utilisateur', 'Utilisateur'),
        ('employe', 'Employé'),
        ('administrateur', 'Administrateur')
    ])
    
    est_verifie = BooleanField('Compte vérifié')
    
    submit = SubmitField('Enregistrer')
