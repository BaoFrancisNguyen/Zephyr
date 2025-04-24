# Dans un script Python ou via une session Flask shell
from app import db, create_app
from app.models.offer import Offer
import sys

app = create_app()
with app.app_context():
    try:
        # Vérifier si des drones existent déjà
        existing_drones = Offer.query.filter(Offer.titre.in_(["Zephir X100", "Zephir Pro 720", "Zephir Elite 4K"])).all()
        existing_titles = [drone.titre for drone in existing_drones]
        
        if existing_drones:
            print(f"Attention: {len(existing_drones)} drones existent déjà: {', '.join(existing_titles)}")
            response = input("Voulez-vous continuer et potentiellement créer des doublons? (o/n): ")
            if response.lower() != 'o':
                print("Opération annulée.")
                sys.exit(0)
        
        # Créer quelques drones
        drones = [
            Offer(
                titre="Zephir X100", 
                description="Drone d'entrée de gamme parfait pour les débutants. Facile à piloter avec une autonomie de 20 minutes.",
                type="debutant",
                niveau="debutant",
                prix=89.99,
                image="drone1.jpg",
                autonomie=20,
                est_publie=True
            ),
            Offer(
                titre="Zephir Pro 720", 
                description="Équipé d'une caméra HD et stabilisation avancée pour des prises de vue fluides.",
                type="intermediaire",
                niveau="intermediaire",
                prix=119.99,
                image="drone2.jpg",
                autonomie=25,
                est_publie=True
            ),
            Offer(
                titre="Zephir Elite 4K", 
                description="Notre modèle premium avec caméra 4K et suivi automatique pour des vidéos professionnelles.",
                type="expert",
                niveau="expert",
                prix=139.99,
                image="drone3.jpg",
                autonomie=35,
                est_publie=True
            )
        ]
        
        added_count = 0
        for drone in drones:
            db.session.add(drone)
            added_count += 1
        
        db.session.commit()
        print(f"Succès! {added_count} drones ont été ajoutés à la base de données.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'ajout des drones: {str(e)}")