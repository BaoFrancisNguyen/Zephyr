#!/usr/bin/env python
"""
Script pour gérer les stocks des drones et accessoires dans la base de données.
À exécuter depuis le répertoire racine du projet:

$ python manage_stock.py

Ce script permet de :
- Afficher les stocks actuels
- Augmenter/diminuer le stock d'un produit
- Définir un stock précis pour un produit
- Mettre à jour les stocks en masse
"""

from app import create_app, db
from app.models.offer import Offer
import sys
import os

# Créer l'application Flask
app = create_app()

def clear_screen():
    """Nettoie l'écran pour une meilleure lisibilité."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Affiche l'en-tête du programme."""
    print("=" * 80)
    print("                  GESTION DES STOCKS - ZEPHIR DRONES")
    print("=" * 80)
    print()

def display_stock():
    """Affiche le stock actuel de tous les produits."""
    with app.app_context():
        # Récupérer tous les drones et accessoires
        drones = Offer.query.filter(Offer.type != 'accessoire').order_by(Offer.titre).all()
        accessories = Offer.query.filter_by(type='accessoire').order_by(Offer.titre).all()
        
        print("\n=== DRONES ===")
        print(f"{'ID':<4} {'TITRE':<25} {'NIVEAU':<15} {'PRIX':<10} {'STOCK':<10}")
        print("-" * 70)
        for drone in drones:
            stock_status = "\033[92m✓\033[0m" if drone.stock > 0 else "\033[91m✗\033[0m"  # Vert si en stock, rouge sinon
            print(f"{drone.id:<4} {drone.titre[:25]:<25} {drone.niveau:<15} {drone.prix:>8.2f}€ {drone.stock:>5} {stock_status}")
        
        print("\n=== ACCESSOIRES ===")
        print(f"{'ID':<4} {'TITRE':<25} {'PRIX':<10} {'STOCK':<10}")
        print("-" * 70)
        for acc in accessories:
            stock_status = "\033[92m✓\033[0m" if acc.stock > 0 else "\033[91m✗\033[0m"
            print(f"{acc.id:<4} {acc.titre[:25]:<25} {acc.prix:>8.2f}€ {acc.stock:>5} {stock_status}")
        
        print("\n")

def update_single_stock():
    """Mettre à jour le stock d'un seul produit."""
    display_stock()
    
    with app.app_context():
        try:
            product_id = int(input("\nEntrez l'ID du produit à mettre à jour (0 pour annuler): "))
            if product_id == 0:
                return
            
            product = Offer.query.get(product_id)
            if not product:
                print("\033[91mErreur: Produit non trouvé.\033[0m")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            print(f"\nProduit sélectionné: {product.titre}")
            print(f"Stock actuel: {product.stock}")
            
            print("\nOptions:")
            print("1. Ajouter au stock")
            print("2. Retirer du stock")
            print("3. Définir une valeur spécifique")
            print("0. Annuler")
            
            choice = input("\nVotre choix: ")
            
            if choice == '1':
                try:
                    quantity = int(input("Quantité à ajouter: "))
                    if quantity < 0:
                        print("\033[91mErreur: La quantité doit être positive.\033[0m")
                        return
                    
                    old_stock = product.stock
                    product.increase_stock(quantity)
                    db.session.commit()
                    print(f"\033[92mStock mis à jour avec succès: {old_stock} → {product.stock}\033[0m")
                except ValueError:
                    print("\033[91mErreur: Veuillez entrer un nombre valide.\033[0m")
            
            elif choice == '2':
                try:
                    quantity = int(input("Quantité à retirer: "))
                    if quantity < 0:
                        print("\033[91mErreur: La quantité doit être positive.\033[0m")
                        return
                    
                    old_stock = product.stock
                    result = product.decrease_stock(quantity)
                    
                    if result:
                        print(f"\033[92mStock mis à jour avec succès: {old_stock} → {product.stock}\033[0m")
                    else:
                        print(f"\033[91mErreur: Stock insuffisant ({old_stock} disponible, {quantity} demandé)\033[0m")
                except ValueError:
                    print("\033[91mErreur: Veuillez entrer un nombre valide.\033[0m")
            
            elif choice == '3':
                try:
                    new_stock = int(input("Nouvelle valeur du stock: "))
                    if new_stock < 0:
                        print("\033[91mErreur: Le stock ne peut pas être négatif.\033[0m")
                        return
                    
                    old_stock = product.stock
                    product.stock = new_stock
                    db.session.commit()
                    print(f"\033[92mStock mis à jour avec succès: {old_stock} → {product.stock}\033[0m")
                except ValueError:
                    print("\033[91mErreur: Veuillez entrer un nombre valide.\033[0m")
            
            input("\nAppuyez sur Entrée pour continuer...")
        
        except Exception as e:
            print(f"\033[91mErreur: {str(e)}\033[0m")
            db.session.rollback()
            input("\nAppuyez sur Entrée pour continuer...")

def update_bulk_stock():
    """Mettre à jour le stock de plusieurs produits en même temps."""
    with app.app_context():
        try:
            print("\n=== MISE À JOUR EN MASSE ===")
            print("1. Augmenter tous les stocks d'un pourcentage")
            print("2. Diminuer tous les stocks d'un pourcentage")
            print("3. Réapprovisionner tous les produits sous un seuil")
            print("4. Définir un stock minimum pour tous les produits")
            print("0. Annuler")
            
            choice = input("\nVotre choix: ")
            
            if choice == '1':
                percentage = float(input("Pourcentage d'augmentation (ex: 10 pour 10%): "))
                if percentage <= 0:
                    print("\033[91mErreur: Le pourcentage doit être positif.\033[0m")
                    return
                
                products = Offer.query.all()
                count = 0
                for product in products:
                    old_stock = product.stock
                    increase = int(old_stock * percentage / 100)
                    if increase < 1:  # Au moins 1 d'augmentation
                        increase = 1
                    product.stock += increase
                    count += 1
                
                db.session.commit()
                print(f"\033[92mStocks augmentés de {percentage}% pour {count} produits.\033[0m")
            
            elif choice == '2':
                percentage = float(input("Pourcentage de diminution (ex: 10 pour 10%): "))
                if percentage <= 0:
                    print("\033[91mErreur: Le pourcentage doit être positif.\033[0m")
                    return
                
                products = Offer.query.all()
                count = 0
                for product in products:
                    old_stock = product.stock
                    decrease = int(old_stock * percentage / 100)
                    if old_stock - decrease < 0:
                        product.stock = 0
                    else:
                        product.stock -= decrease
                    count += 1
                
                db.session.commit()
                print(f"\033[92mStocks diminués de {percentage}% pour {count} produits.\033[0m")
            
            elif choice == '3':
                threshold = int(input("Seuil critique (réapprovisionner les produits avec un stock inférieur à): "))
                restock_value = int(input("Quantité à réapprovisionner: "))
                
                if threshold < 0 or restock_value <= 0:
                    print("\033[91mErreur: Les valeurs doivent être positives.\033[0m")
                    return
                
                products = Offer.query.filter(Offer.stock < threshold).all()
                count = 0
                for product in products:
                    old_stock = product.stock
                    product.stock += restock_value
                    print(f"- {product.titre}: {old_stock} → {product.stock}")
                    count += 1
                
                db.session.commit()
                print(f"\033[92m{count} produits réapprovisionnés avec succès.\033[0m")
            
            elif choice == '4':
                min_stock = int(input("Stock minimum pour tous les produits: "))
                
                if min_stock < 0:
                    print("\033[91mErreur: Le stock minimum ne peut pas être négatif.\033[0m")
                    return
                
                products = Offer.query.filter(Offer.stock < min_stock).all()
                count = 0
                for product in products:
                    old_stock = product.stock
                    product.stock = min_stock
                    print(f"- {product.titre}: {old_stock} → {product.stock}")
                    count += 1
                
                db.session.commit()
                print(f"\033[92m{count} produits mis à jour avec un stock minimum de {min_stock}.\033[0m")
            
            input("\nAppuyez sur Entrée pour continuer...")
        
        except Exception as e:
            print(f"\033[91mErreur: {str(e)}\033[0m")
            db.session.rollback()
            input("\nAppuyez sur Entrée pour continuer...")

def export_stock_report():
    """Exporte un rapport de stock au format CSV."""
    with app.app_context():
        try:
            filename = "stock_report.csv"
            with open(filename, 'w', encoding='utf-8') as f:
                # Écrire l'en-tête
                f.write("ID,Titre,Type,Niveau,Prix,Stock,Disponible\n")
                
                # Récupérer et écrire les données
                products = Offer.query.order_by(Offer.type, Offer.titre).all()
                for product in products:
                    f.write(f"{product.id},\"{product.titre}\",{product.type},{product.niveau},{product.prix},{product.stock},{product.stock > 0}\n")
            
            print(f"\033[92mRapport exporté avec succès dans {filename}\033[0m")
            input("\nAppuyez sur Entrée pour continuer...")
        
        except Exception as e:
            print(f"\033[91mErreur lors de l'exportation: {str(e)}\033[0m")
            input("\nAppuyez sur Entrée pour continuer...")

def main_menu():
    """Affiche le menu principal et gère les interactions utilisateur."""
    while True:
        clear_screen()
        print_header()
        
        print("MENU PRINCIPAL:")
        print("1. Afficher les stocks actuels")
        print("2. Mettre à jour le stock d'un produit")
        print("3. Mise à jour en masse des stocks")
        print("4. Exporter un rapport de stock (CSV)")
        print("0. Quitter")
        
        choice = input("\nVotre choix: ")
        
        if choice == '1':
            clear_screen()
            print_header()
            display_stock()
            input("\nAppuyez sur Entrée pour revenir au menu principal...")
        
        elif choice == '2':
            clear_screen()
            print_header()
            update_single_stock()
        
        elif choice == '3':
            clear_screen()
            print_header()
            update_bulk_stock()
        
        elif choice == '4':
            clear_screen()
            print_header()
            export_stock_report()
        
        elif choice == '0':
            clear_screen()
            print("Au revoir!")
            sys.exit(0)
        
        else:
            print("\033[91mOption invalide. Veuillez réessayer.\033[0m")
            input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main_menu()
