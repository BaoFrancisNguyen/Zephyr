import os
import sys

# Essayer d'installer requests s'il n'est pas disponible
try:
    import requests
except ImportError:
    print("Module requests non trouvé, tentative d'installation...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print("Installation terminée, redémarrez le script.")
    sys.exit(1)

# Ajouter le répertoire courant au chemin pour s'assurer que app est trouvable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import create_app, db, bcrypt
    from app.models.user import User
except ImportError as e:
    print(f"Erreur lors de l'importation: {e}")
    print("Vérifiez la structure de votre projet et assurez-vous que tous les modules sont installés.")
    sys.exit(1)

def create_admin():
    try:
        app = create_app()
        with app.app_context():
            # Vérifier si l'admin existe déjà
            admin = User.query.filter_by(email='admin@zephyr-drones.fr').first()
            
            if not admin:
                # Créer un nouvel admin
                hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
                admin = User(
                    username='admin',
                    email='admin@zephyr-drones.fr',
                    password=hashed_password,
                    nom='Admin',
                    prenom='Admin',
                    role='administrateur',
                    est_verifie=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Administrateur créé avec succès!")
                print("Identifiants: admin@zephyr-drones.fr / admin123")
            else:
                print("Un administrateur avec cet email existe déjà.")
    except Exception as e:
        print(f"Erreur lors de la création de l'administrateur: {e}")

if __name__ == "__main__":
    create_admin()