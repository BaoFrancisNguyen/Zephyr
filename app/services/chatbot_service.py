import requests
import json
import logging

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chatbot_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("chatbot_service")

class ChatbotService:
    """
    Service pour interagir avec Ollama en local
    """
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "mistral:latest"
        logger.info(f"Initialisation du service ChatbotService avec URL: {base_url} et modèle: {self.model}")
        
    def generate_response(self, prompt, system_prompt=None, history=None):
        """
        Génère une réponse à partir du modèle Mistral via Ollama.
        Essaie plusieurs méthodes d'API pour maximiser les chances de succès.
        
        Args:
            prompt (str): Question ou message de l'utilisateur
            system_prompt (str, optional): Message système pour guider le comportement du modèle
            history (list, optional): Historique de conversation précédent
            
        Returns:
            str: Réponse générée par le modèle
        """
        logger.debug(f"Requête de génération reçue. Prompt: '{prompt[:50]}...'")
        
        # Tentative avec l'API chat (format messages)
        try:
            response = self._try_chat_api(prompt, system_prompt, history)
            if "Erreur" not in response:
                return response
            logger.warning("Échec de l'API chat, essai avec l'API de complétion...")
        except Exception as e:
            logger.error(f"Exception dans l'API chat: {str(e)}")
            
        # Si l'API chat échoue, tentative avec l'API de complétion
        try:
            response = self._try_completion_api(prompt, system_prompt, history)
            return response
        except Exception as e:
            logger.error(f"Exception dans l'API de complétion: {str(e)}")
            return f"Je n'ai pas pu générer de réponse. Erreur: {str(e)}"
        
    def _try_chat_api(self, prompt, system_prompt=None, history=None):
        """Tentative avec l'API chat utilisant le format messages"""
        if system_prompt is None:
            system_prompt = """Tu es un assistant virtuel pour Zephir Drones, une entreprise spécialisée dans la vente de drones 
            destinés au grand public, des débutants aux experts. Tu dois répondre aux questions des clients 
            concernant les drones disponibles, leurs fonctionnalités, les prix, et le support technique. 
            Sois poli, serviable et enthousiaste à propos de nos produits. Nos gammes principales sont:
            - Zephir X100: Drone d'entrée de gamme à 89,99€, idéal pour les débutants avec 20 min d'autonomie
            - Zephir Pro 720: Drone intermédiaire à 119,99€ avec caméra HD et 25 min d'autonomie
            - Zephir Elite 4K: Drone expert à 139,99€ avec caméra 4K et 35 min d'autonomie
            
            Si tu ne connais pas la réponse à une question spécifique, propose de les rediriger vers notre service client par email ou téléphone."""
        
        # URL endpoint pour l'API Ollama chat
        url = f"{self.base_url}/api/chat"
        
        # Compilation du prompt complet avec historique si fourni
        messages = []
        if history:
            for msg in history:
                if "user" in msg:
                    messages.append({"role": "user", "content": msg["user"]})
                if "assistant" in msg:
                    messages.append({"role": "assistant", "content": msg["assistant"]})
        
        # Ajout du système prompt et de la question actuelle
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)
        full_messages.append({"role": "user", "content": prompt})
        
        # Paramètres de la requête
        data = {
            "model": self.model,
            "messages": full_messages,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        logger.debug(f"Envoi à l'API chat. URL: {url}")
        logger.debug(f"Données: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data)
        logger.debug(f"Réponse de l'API chat - Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            logger.debug(f"Réponse complète: {json.dumps(response_data, indent=2)}")
            
            # Essai de différents formats de réponse possibles
            if "message" in response_data and "content" in response_data["message"]:
                return response_data["message"]["content"]
            elif "response" in response_data:
                return response_data["response"]
            else:
                logger.warning(f"Format de réponse inattendu: {response_data}")
                return "Je n'ai pas pu générer de réponse (format inattendu)."
        else:
            error_msg = f"Erreur lors de la communication avec l'API chat: {response.status_code}"
            logger.error(f"{error_msg}. Détails: {response.text}")
            return error_msg
    
    def _try_completion_api(self, prompt, system_prompt=None, history=None):
        """Tentative avec l'API de complétion (format prompt)"""
        if system_prompt is None:
            system_prompt = """Tu es un assistant virtuel pour Zephir Drones, une entreprise spécialisée dans la vente de drones."""
        
        # URL endpoint pour l'API Ollama generate
        url = f"{self.base_url}/api/generate"
        
        # Préparer l'historique au format texte si disponible
        history_text = ""
        if history:
            for msg in history:
                if "user" in msg:
                    history_text += f"Utilisateur: {msg['user']}\n"
                if "assistant" in msg:
                    history_text += f"Assistant: {msg['assistant']}\n"
        
        # Construire le prompt complet
        full_prompt = f"{system_prompt}\n\n{history_text}Utilisateur: {prompt}\nAssistant:"
        
        # Paramètres de la requête
        data = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        logger.debug(f"Envoi à l'API generate. URL: {url}")
        logger.debug(f"Prompt: {full_prompt[:200]}...")
        
        response = requests.post(url, json=data)
        logger.debug(f"Réponse de l'API generate - Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            logger.debug(f"Réponse partielle: {json.dumps(response_data)[:200]}...")
            
            # Essai de différents formats de réponse possibles
            if "response" in response_data:
                return response_data["response"]
            else:
                logger.warning(f"Format de réponse inattendu: {response_data}")
                return "Je n'ai pas pu générer de réponse (format inattendu)."
        else:
            error_msg = f"Erreur lors de la communication avec l'API generate: {response.status_code}"
            logger.error(f"{error_msg}. Détails: {response.text}")
            return error_msg
    
    def check_availability(self):
        """
        Vérifie si Ollama est disponible et si le modèle Mistral est chargé
        
        Returns:
            bool: True si disponible, False sinon
        """
        logger.debug("Vérification de la disponibilité d'Ollama...")
        try:
            # Vérifier d'abord si le serveur est en fonctionnement
            health_url = f"{self.base_url}/api/tags"
            logger.debug(f"Requête vers: {health_url}")
            
            response = requests.get(health_url)
            logger.debug(f"Réponse du serveur: {response.status_code}")
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                logger.debug(f"Modèles disponibles: {models}")
                
                mistral_available = any(model.get("name", "").startswith("mistral") for model in models)
                logger.info(f"Modèle Mistral disponible: {mistral_available}")
                
                if not mistral_available:
                    logger.warning("Le modèle Mistral n'est pas chargé dans Ollama!")
                
                return mistral_available
            
            logger.error(f"Erreur de statut HTTP: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Exception lors de la vérification d'Ollama: {str(e)}")
            return False
    
    def test_api(self):
        """
        Teste l'API Ollama avec une requête simple pour diagnostiquer les problèmes
        
        Returns:
            dict: Résultats des tests
        """
        results = {
            "server_available": False,
            "model_loaded": False,
            "generate_api": False,
            "chat_api": False,
            "error": None
        }
        
        logger.info("Exécution des tests diagnostiques d'Ollama...")
        
        try:
            # 1. Test de disponibilité du serveur
            health_url = f"{self.base_url}/api/tags"
            health_response = requests.get(health_url, timeout=5)
            results["server_available"] = health_response.status_code == 200
            
            if not results["server_available"]:
                results["error"] = f"Serveur Ollama inaccessible (HTTP {health_response.status_code})"
                return results
            
            # 2. Vérification du modèle chargé
            models = health_response.json().get("models", [])
            results["model_loaded"] = any(model.get("name", "").startswith("mistral") for model in models)
            
            if not results["model_loaded"]:
                results["error"] = "Le modèle Mistral n'est pas chargé"
                return results
            
            # 3. Test de l'API generate
            generate_url = f"{self.base_url}/api/generate"
            generate_data = {
                "model": self.model,
                "prompt": "Dis bonjour",
                "stream": False
            }
            
            generate_response = requests.post(generate_url, json=generate_data, timeout=10)
            results["generate_api"] = generate_response.status_code == 200
            
            if not results["generate_api"]:
                results["error"] = f"API generate inaccessible (HTTP {generate_response.status_code})"
                logger.error(f"Erreur API generate: {generate_response.text}")
            
            # 4. Test de l'API chat (si elle existe)
            try:
                chat_url = f"{self.base_url}/api/chat"
                chat_data = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": "Dis bonjour"}],
                    "stream": False
                }
                
                chat_response = requests.post(chat_url, json=chat_data, timeout=10)
                results["chat_api"] = chat_response.status_code == 200
                
                if not results["chat_api"]:
                    logger.warning(f"API chat inaccessible (HTTP {chat_response.status_code}): {chat_response.text}")
            except Exception as chat_e:
                logger.warning(f"Erreur lors du test de l'API chat: {str(chat_e)}")
                results["chat_api"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Exception lors des tests diagnostiques: {str(e)}")
            results["error"] = str(e)
            return results