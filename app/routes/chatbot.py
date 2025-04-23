from flask import Blueprint, request, jsonify, render_template, session
from flask_login import login_required, current_user
from app.services.chatbot_service import ChatbotService

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')
chatbot_service = ChatbotService()

@chatbot_bp.route('/ask', methods=['POST'])
def ask():
    """
    Endpoint pour recevoir les questions et renvoyer les réponses du chatbot.
    """
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'La question est requise'}), 400
        
        # Récupérer l'historique de conversation de la session si disponible
        session_id = f"chat_{request.remote_addr}"
        history = session.get(session_id, [])
        
        # Générer la réponse
        answer = chatbot_service.generate_response(question, history=history)
        
        # Mettre à jour l'historique de la conversation
        history.append({"user": question})
        history.append({"assistant": answer})
        
        # Limiter l'historique aux 10 derniers messages pour éviter une session trop volumineuse
        if len(history) > 20:
            history = history[-20:]
        
        # Enregistrer l'historique mis à jour dans la session
        session[session_id] = history
        
        return jsonify({
            'answer': answer,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@chatbot_bp.route('/status', methods=['GET'])
def status():
    """
    Vérifie si le service de chatbot est disponible
    """
    try:
        available = chatbot_service.check_availability()
        return jsonify({
            'available': available,
            'model': chatbot_service.model if available else None
        })
    except Exception as e:
        return jsonify({'error': str(e), 'available': False}), 500

@chatbot_bp.route('/reset', methods=['POST'])
def reset_chat():
    """
    Réinitialise l'historique de la conversation
    """
    session_id = f"chat_{request.remote_addr}"
    session[session_id] = []
    return jsonify({'success': True, 'message': 'Conversation réinitialisée'})