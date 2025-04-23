#!/usr/bin/env python
"""
Script pour créer des offres de drones dans la base de données.
À exécuter depuis le répertoire racine du projet avec Flask shell:

$ flask shell < create_offers.py

ou directement avec Python:
$ python create_offers.py
"""

from app import create_app, db
from app.models.offer import Offer

# Créer l'application Flask
app = create_app()

# Liste des drones à créer
drones = [
    {
        "titre": "Zephir X100",
        "description": "Notre drone d'entrée de gamme parfait pour les débutants. Facile à piloter avec une stabilisation automatique et une autonomie de 20 minutes, le X100 est idéal pour s'initier au pilotage de drone. Sa construction robuste lui permet de résister aux chocs légers, ce qui le rend parfait pour les premiers apprentissages.",
        "type": "debutant",
        "niveau": "debutant",
        "prix": 89.99,
        "stock": 25,
        "image": "drone1.jpg",
        "autonomie": 20,
        "poids": 250,
        "dimensions": "25cm x 25cm x 7cm",
        "camera": "HD 720p",
        "portee": 100,
        "vitesse": 30
    },
    {
        "titre": "Zephir Pro 720",
        "description": "Le modèle intermédiaire pour les pilotes qui souhaitent aller plus loin. Équipé d'une caméra HD 720p avec stabilisation gyroscopique, le Pro 720 offre des images nettes et fluides. Avec une autonomie de 25 minutes et une portée de 300 mètres, ce drone vous permettra d'explorer davantage et de capturer de belles images aériennes.",
        "type": "intermediaire",
        "niveau": "intermediaire",
        "prix": 119.99,
        "stock": 18,
        "image": "drone2.jpg",
        "autonomie": 25,
        "poids": 350,
        "dimensions": "30cm x 30cm x 8cm",
        "camera": "HD 720p stabilisée",
        "portee": 300,
        "vitesse": 40
    },
    {
        "titre": "Zephir Elite 4K",
        "description": "Notre modèle haut de gamme pour les pilotes expérimentés et les professionnels. Avec sa caméra 4K stabilisée sur 3 axes, le Elite 4K capture des images de qualité professionnelle. Son autonomie de 35 minutes, sa portée de 500 mètres et ses fonctionnalités avancées comme le suivi de sujet et les trajectoires automatisées en font l'outil idéal pour la photographie et la vidéographie aérienne.",
        "type": "expert",
        "niveau": "expert",
        "prix": 139.99,
        "stock": 12,
        "image": "drone3.jpg",
        "autonomie": 35,
        "poids": 450,
        "dimensions": "35cm x 35cm x 9cm",
        "camera": "4K stabilisée 3 axes",
        "portee": 500,
        "vitesse": 50
    },
    {
        "titre": "Zephir Mini",
        "description": "Un drone compact et léger, idéal pour une utilisation en intérieur ou lors de vos déplacements. Malgré sa petite taille, le Zephir Mini est équipé d'une caméra HD et offre une stabilité surprenante. Facile à transporter, il se glisse dans n'importe quel sac et est prêt à voler en quelques secondes.",
        "type": "debutant",
        "niveau": "debutant",
        "prix": 79.99,
        "stock": 30,
        "image": "drone4.jpg",
        "autonomie": 15,
        "poids": 150,
        "dimensions": "15cm x 15cm x 5cm",
        "camera": "HD 720p",
        "portee": 80,
        "vitesse": 25
    },
    {
        "titre": "Zephir Explorer",
        "description": "Conçu pour l'exploration et l'aventure, le Zephir Explorer offre une autonomie prolongée de 30 minutes et une résistance accrue aux conditions extérieures. Sa caméra HD orientable vous permet de capturer des images sous différents angles sans avoir à repositionner le drone. Idéal pour les randonnées et les voyages.",
        "type": "intermediaire",
        "niveau": "intermediaire",
        "prix": 129.99,
        "stock": 15,
        "image": "drone5.jpg",
        "autonomie": 30,
        "poids": 380,
        "dimensions": "32cm x 32cm x 8cm",
        "camera": "HD 1080p orientable",
        "portee": 350,
        "vitesse": 45
    },
    {
        "titre": "Zephir Pro Racing",
        "description": "Un drone haute performance conçu pour la vitesse et l'agilité. Avec sa structure légère et ses moteurs puissants, le Pro Racing peut atteindre 60 km/h et exécuter des manœuvres complexes avec précision. Destiné aux pilotes expérimentés qui recherchent des sensations fortes et des performances exceptionnelles.",
        "type": "expert",
        "niveau": "expert",
        "prix": 149.99,
        "stock": 10,
        "image": "drone6.jpg",
        "autonomie": 20,
        "poids": 300,
        "dimensions": "28cm x 28cm x 7cm",
        "camera": "HD 1080p",
        "portee": 400,
        "vitesse": 60
    },
    {
        "titre": "Zephir Nano",
        "description": "Le plus petit de nos drones, parfait pour s'amuser en intérieur. Extrêmement léger et maniable, le Nano est idéal pour apprendre les bases du pilotage dans un espace restreint. Sa petite taille lui permet de naviguer facilement entre les obstacles, et sa construction résistante supporte bien les chocs.",
        "type": "debutant",
        "niveau": "debutant",
        "prix": 59.99,
        "stock": 40,
        "image": "drone7.jpg",
        "autonomie": 10,
        "poids": 50,
        "dimensions": "10cm x 10cm x 3cm",
        "camera": "SD 480p",
        "portee": 50,
        "vitesse": 20
    },
    {
        "titre": "Zephir Photographer",
        "description": "Spécialement conçu pour la photographie aérienne, ce drone est équipé d'une caméra haute résolution avec un grand capteur pour des images détaillées même en faible luminosité. Il dispose de modes de vol automatiques dédiés à la photographie, comme le panorama 360° et le time-lapse aérien.",
        "type": "intermediaire",
        "niveau": "intermediaire",
        "prix": 134.99,
        "stock": 20,
        "image": "drone8.jpg",
        "autonomie": 28,
        "poids": 400,
        "dimensions": "33cm x 33cm x 9cm",
        "camera": "12MP grand capteur",
        "portee": 300,
        "vitesse": 40
    },
    {
        "titre": "Batterie supplémentaire Zephir",
        "description": "Prolongez votre temps de vol avec cette batterie supplémentaire compatible avec les modèles X100, Pro 720 et Elite 4K. Capacité identique à la batterie d'origine, avec indicateur LED de niveau de charge.",
        "type": "accessoire",
        "niveau": "tous",
        "prix": 29.99,
        "stock": 50,
        "image": "accessory1.jpg",
        "autonomie": None,
        "poids": 80,
        "dimensions": "5cm x 3cm x 2cm",
        "camera": None,
        "portee": None,
        "vitesse": None
    },
    {
        "titre": "Hélices de rechange (lot de 8)",
        "description": "Lot de 8 hélices de rechange (4 paires) compatibles avec tous nos modèles de drones. Faciles à installer, ces hélices sont fabriquées dans un matériau durable pour garantir stabilité et performances optimales.",
        "type": "accessoire",
        "niveau": "tous",
        "prix": 14.99,
        "stock": 100,
        "image": "accessory2.jpg",
        "autonomie": None,
        "poids": 20,
        "dimensions": "12cm de diamètre",
        "camera": None,
        "portee": None,
        "vitesse": None
    },
    {
        "titre": "Sac de transport Zephir",
        "description": "Sac de transport robuste et étanche, spécialement conçu pour protéger votre drone et ses accessoires. Dispose de compartiments rembourrés sur mesure pour le drone, la télécommande, les batteries et les pièces de rechange.",
        "type": "accessoire",
        "niveau": "tous",
        "prix": 24.99,
        "stock": 35,
        "image": "accessory3.jpg",
        "autonomie": None,
        "poids": 500,
        "dimensions": "40cm x 30cm x 20cm",
        "camera": None,
        "portee": None,
        "vitesse": None
    },
    {
        "titre": "Chargeur rapide Zephir",
        "description": "Rechargez votre batterie en moitié moins de temps avec ce chargeur rapide. Compatible avec toutes les batteries Zephir, il dispose d'une protection contre la surchauffe et d'un affichage LED qui indique l'état de charge.",
        "type": "accessoire",
        "niveau": "tous",
        "prix": 19.99,
        "stock": 45,
        "image": "accessory4.jpg",
        "autonomie": None,
        "poids": 150,
        "dimensions": "10cm x 6cm x 3cm",
        "camera": None,
        "portee": None,
        "vitesse": None
    }
]

def create_offers():
    """Crée des offres de drones dans la base de données."""
    
    with app.app_context():
        # Vérifier si des offres existent déjà pour éviter les duplications
        existing_count = Offer.query.count()
        if existing_count > 0:
            print(f"Il y a déjà {existing_count} offres dans la base de données.")
            user_input = input("Voulez-vous ajouter d'autres offres ? (o/n): ")
            if user_input.lower() != 'o':
                print("Opération annulée.")
                return
        
        # Créer les offres
        created_count = 0
        for drone_data in drones:
            # Vérifier si l'offre existe déjà (par titre)
            existing_offer = Offer.query.filter_by(titre=drone_data["titre"]).first()
            if existing_offer:
                print(f"L'offre '{drone_data['titre']}' existe déjà.")
                continue
            
            # Créer la nouvelle offre
            offer = Offer(
                titre=drone_data["titre"],
                description=drone_data["description"],
                type=drone_data["type"],
                niveau=drone_data["niveau"],
                prix=drone_data["prix"],
                stock=drone_data["stock"],
                image=drone_data["image"],
                autonomie=drone_data["autonomie"],
                poids=drone_data["poids"],
                dimensions=drone_data["dimensions"],
                camera=drone_data["camera"],
                portee=drone_data["portee"],
                vitesse=drone_data["vitesse"]
            )
            db.session.add(offer)
            created_count += 1
        
        # Sauvegarder les changements
        db.session.commit()
        print(f"{created_count} nouvelles offres ont été créées avec succès!")

if __name__ == "__main__":
    create_offers()