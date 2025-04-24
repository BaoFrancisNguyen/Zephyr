from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app.models.offer import Offer

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Page d'accueil."""
    # Récupérer quelques offres en vedette
    featured_offers = Offer.query.filter_by(est_publie=True).order_by(Offer.date_creation.desc()).limit(3).all()
    return render_template('home.html', featured_offers=featured_offers)

@main_bp.route('/about')
def about():
    """Page À propos."""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Page de contact."""
    return render_template('contact.html')

@main_bp.route('/faq')
def faq():
    """Page FAQ."""
    return render_template('faq.html')

@main_bp.route('/terms')
def terms():
    """Page Conditions d'utilisation."""
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """Page Politique de confidentialité."""
    return render_template('privacy.html')

@main_bp.route('/test-image')
def test_image():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test d'image</title>
    </head>
    <body>
        <h1>Test d'image</h1>
        <p>Voici l'image par défaut :</p>
        <img src="/static/images/default-offer.jpg" alt="Image par défaut">
        <hr>
        <p>Voici une autre image du dossier :</p>
        <img src="/static/images/swimming.jpg" alt="Image de natation">
    </body>
    </html>
    """


@main_bp.route('/support')
def support():
    """Page de support technique."""
    return render_template('support.html')

@main_bp.route('/tutorials')
def tutorials():
    """Page de tutoriels et guides."""
    return render_template('tutorials.html')

@main_bp.route('/faq')
def faq():
    """Page FAQ."""
    return render_template('faq.html')