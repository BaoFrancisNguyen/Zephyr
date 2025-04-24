# cleanup_drones.py
from app import db, create_app
from app.models.offer import Offer

app = create_app()
with app.app_context():
    try:
        # Option 1 : Supprimer tous les drones existants
        deleted_count = Offer.query.delete()
        db.session.commit()
        print(f"Tous les drones ont été supprimés ({deleted_count} entrées).")
        
        # Option 2 (alternative) : Conserver uniquement un exemplaire de chaque modèle
        # titles = ["Zephir X100", "Zephir Pro 720", "Zephir Elite 4K"]
        # for title in titles:
        #     # Récupérer toutes les entrées pour ce titre
        #     drones = Offer.query.filter_by(titre=title).all()
        #     # Garder le premier, supprimer les autres
        #     if len(drones) > 1:
        #         for drone in drones[1:]:
        #             db.session.delete(drone)
        #     print(f"Conservé 1 drone {title}, supprimé {len(drones)-1 if len(drones)>0 else 0} doublons.")
        # db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors du nettoyage de la base de données: {str(e)}")