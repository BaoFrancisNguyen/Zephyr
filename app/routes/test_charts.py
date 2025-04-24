from flask import Blueprint, render_template, redirect, url_for, flash, send_file
import os

test_bp = Blueprint('test', __name__, url_prefix='/test')

@test_bp.route('/charts')
def test_charts():
    """
    Page de test pour vérifier si les graphiques fonctionnent correctement.
    Cette page utilise des données statiques et Chart.js directement.
    """
    return render_template('admin/simplified_stats.html')

@test_bp.route('/minimal')
def minimal_chart():
    """
    Page minimale avec un seul graphique pour tester Chart.js.
    """
    return render_template('admin/minimal_chart.html')

@test_bp.route('/standalone')
def standalone():
    """
    Renvoie un fichier HTML autonome pour tester les graphiques sans dépendances Flask.
    """
    return send_file('templates/admin/minimal_chart.html')