"""Initial migration

Revision ID: b378ae5c64bb
Revises: 
Create Date: 2025-04-17 17:27:18.876346

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b378ae5c64bb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('offers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('titre', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('nombre_personnes', sa.Integer(), nullable=False),
    sa.Column('prix', sa.Float(), nullable=False),
    sa.Column('disponibilite', sa.Integer(), nullable=False),
    sa.Column('date_evenement', sa.DateTime(), nullable=False),
    sa.Column('image', sa.String(length=255), nullable=True),
    sa.Column('est_publie', sa.Boolean(), nullable=True),
    sa.Column('date_creation', sa.DateTime(), nullable=True),
    sa.Column('date_modification', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('nom', sa.String(length=50), nullable=False),
    sa.Column('prenom', sa.String(length=50), nullable=False),
    sa.Column('password', sa.String(length=120), nullable=False),
    sa.Column('cle_securite', sa.String(length=255), nullable=False),
    sa.Column('date_creation', sa.DateTime(), nullable=True),
    sa.Column('derniere_connexion', sa.DateTime(), nullable=True),
    sa.Column('role', sa.String(length=20), nullable=True),
    sa.Column('est_verifie', sa.Boolean(), nullable=True),
    sa.Column('code_verification', sa.String(length=100), nullable=True),
    sa.Column('code_2fa_secret', sa.String(length=32), nullable=True),
    sa.Column('est_2fa_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('cle_securite'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('carts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('date_creation', sa.DateTime(), nullable=True),
    sa.Column('date_modification', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=50), nullable=False),
    sa.Column('total', sa.Float(), nullable=False),
    sa.Column('statut', sa.String(length=20), nullable=True),
    sa.Column('date_commande', sa.DateTime(), nullable=True),
    sa.Column('date_paiement', sa.DateTime(), nullable=True),
    sa.Column('cle_achat', sa.String(length=255), nullable=False),
    sa.Column('adresse_email', sa.String(length=120), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('cle_achat'),
    sa.UniqueConstraint('reference')
    )
    op.create_table('cart_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cart_id', sa.Integer(), nullable=False),
    sa.Column('offer_id', sa.Integer(), nullable=False),
    sa.Column('quantite', sa.Integer(), nullable=True),
    sa.Column('prix_unitaire', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ),
    sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('order_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('offer_id', sa.Integer(), nullable=False),
    sa.Column('quantite', sa.Integer(), nullable=True),
    sa.Column('prix_unitaire', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('offer_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('cle_utilisateur', sa.String(length=255), nullable=False),
    sa.Column('cle_achat', sa.String(length=255), nullable=False),
    sa.Column('cle_billet', sa.String(length=255), nullable=False),
    sa.Column('qr_code', sa.Text(), nullable=True),
    sa.Column('est_valide', sa.Boolean(), nullable=True),
    sa.Column('date_generation', sa.DateTime(), nullable=True),
    sa.Column('date_utilisation', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('cle_billet')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tickets')
    op.drop_table('order_items')
    op.drop_table('cart_items')
    op.drop_table('orders')
    op.drop_table('carts')
    op.drop_table('users')
    op.drop_table('offers')
    # ### end Alembic commands ###
