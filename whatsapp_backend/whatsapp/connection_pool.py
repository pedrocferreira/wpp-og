import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager
from typing import Optional, Dict, Any
import threading
from django.conf import settings

logger = logging.getLogger(__name__)


class OptimizedHTTPSession:
    """
    Session HTTP otimizada com pool de conexões e retry automático
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern para reutilizar sessão"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.session = requests.Session()
        self._setup_session()
        self._initialized = True
        
        logger.info("[POOL] Pool de conexões HTTP inicializado")
    
    def _setup_session(self):
        """Configura sessão com pool de conexões e retry"""
        
        # Configuração de retry
        retry_strategy = Retry(
            total=3,  # Total de tentativas
            status_forcelist=[429, 500, 502, 503, 504],  # Status codes para retry
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            backoff_factor=1,  # Delay: 1s, 2s, 4s
            raise_on_redirect=False,
            raise_on_status=False
        )
        
        # Adapter customizado
        adapter = HTTPAdapter(
            pool_connections=10,  # Número de pools de conexão
            pool_maxsize=20,      # Máximo de conexões por pool
            max_retries=retry_strategy,
            pool_block=False
        )
        
        # Aplica adapter para HTTP e HTTPS
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers padrão
        self.session.headers.update({
            'User-Agent': 'WhatsApp-Bot/1.0 (Production)',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        # Configurações de timeout padrão
        self.default_timeout = (10, 30)  # (connect_timeout, read_timeout)
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Faz requisição com configurações otimizadas
        """
        try:
            # Define timeout se não fornecido
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.default_timeout
            
            # Log da requisição
            logger.debug(f"[POOL] {method.upper()} {url}")
            
            response = self.session.request(method, url, **kwargs)
            
            # Log da resposta
            logger.debug(f"[POOL] Response: {response.status_code} in {response.elapsed.total_seconds():.2f}s")
            
            return response
            
        except requests.exceptions.Timeout as e:
            logger.error(f"[POOL] Timeout na requisição {method} {url}: {str(e)}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[POOL] Erro de conexão {method} {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[POOL] Erro inesperado na requisição {method} {url}: {str(e)}")
            raise
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET otimizado"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST otimizado"""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """PUT otimizado"""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """DELETE otimizado"""
        return self.request('DELETE', url, **kwargs)
    
    def close(self):
        """Fecha sessão e libera recursos"""
        if hasattr(self, 'session'):
            self.session.close()
            logger.info("[POOL] Pool de conexões fechado")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da sessão"""
        try:
            # Acessa statistics dos adapters
            http_adapter = self.session.get_adapter('http://')
            https_adapter = self.session.get_adapter('https://')
            
            stats = {
                'initialized': self._initialized,
                'adapters': {
                    'http': {
                        'pool_connections': http_adapter.config.get('pool_connections', 'N/A'),
                        'pool_maxsize': http_adapter.config.get('pool_maxsize', 'N/A'),
                    },
                    'https': {
                        'pool_connections': https_adapter.config.get('pool_connections', 'N/A'),
                        'pool_maxsize': https_adapter.config.get('pool_maxsize', 'N/A'),
                    }
                },
                'default_timeout': self.default_timeout
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"[POOL] Erro ao obter estatísticas: {str(e)}")
            return {'error': str(e)}


class EvolutionAPIClient:
    """
    Cliente otimizado para Evolution API usando pool de conexões
    """
    
    def __init__(self):
        self.http_session = OptimizedHTTPSession()
        self.base_url = settings.EVOLUTION_API_URL
        self._setup_headers()
    
    def _setup_headers(self):
        """Configura headers específicos da Evolution API"""
        from .models import EvolutionConfig
        
        try:
            config = EvolutionConfig.objects.filter(is_active=True).first()
            if config:
                self.headers = {
                    "Content-Type": "application/json",
                    "apikey": config.api_key,
                    "token": config.api_key
                }
                self.instance_id = config.instance_id
            else:
                logger.warning("[POOL] Nenhuma configuração Evolution ativa encontrada")
                self.headers = {}
                self.instance_id = settings.EVOLUTION_INSTANCE_ID
                
        except Exception as e:
            logger.error(f"[POOL] Erro ao configurar headers: {str(e)}")
            self.headers = {}
            self.instance_id = settings.EVOLUTION_INSTANCE_ID
    
    def send_message(self, phone: str, message: str, media_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Envia mensagem usando pool de conexões otimizado
        """
        try:
            url = f"{self.base_url}/message/sendText/{self.instance_id}"
            
            data = {
                "number": phone,
                "text": message,
                "linkPreview": True
            }
            
            if media_url:
                data["mediaUrl"] = media_url
            
            logger.info(f"[POOL] Enviando mensagem para {phone} via pool otimizado")
            
            response = self.http_session.post(
                url,
                headers=self.headers,
                json=data
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[POOL] Mensagem enviada com sucesso para {phone}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[POOL] Erro ao enviar mensagem via pool: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"[POOL] Resposta de erro: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"[POOL] Erro inesperado no envio via pool: {str(e)}")
            raise
    
    def get_connection_state(self) -> Optional[Dict[str, Any]]:
        """
        Verifica estado da conexão usando pool otimizado
        """
        try:
            url = f"{self.base_url}/instance/connectionState/{self.instance_id}"
            
            response = self.http_session.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"[POOL] Erro ao verificar connection state: {str(e)}")
            raise
    
    def get_instance_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações da instância usando pool otimizado
        """
        try:
            url = f"{self.base_url}/instance/info/{self.instance_id}"
            
            response = self.http_session.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"[POOL] Erro ao obter info da instância: {str(e)}")
            raise
    
    def send_media(self, phone: str, media_url: str, caption: str = None) -> Optional[Dict[str, Any]]:
        """
        Envia mídia usando pool otimizado
        """
        try:
            url = f"{self.base_url}/message/sendMedia/{self.instance_id}"
            
            data = {
                "number": phone,
                "mediaUrl": media_url
            }
            
            if caption:
                data["caption"] = caption
            
            logger.info(f"[POOL] Enviando mídia para {phone}")
            
            response = self.http_session.post(
                url,
                headers=self.headers,
                json=data
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[POOL] Mídia enviada com sucesso para {phone}")
            return result
            
        except Exception as e:
            logger.error(f"[POOL] Erro ao enviar mídia: {str(e)}")
            raise
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do pool de conexões
        """
        return self.http_session.get_stats()


# Pool global para reutilização
_global_evolution_client = None
_client_lock = threading.Lock()


def get_evolution_client() -> EvolutionAPIClient:
    """
    Retorna cliente Evolution otimizado (singleton)
    """
    global _global_evolution_client
    
    if _global_evolution_client is None:
        with _client_lock:
            if _global_evolution_client is None:
                _global_evolution_client = EvolutionAPIClient()
                logger.info("[POOL] Cliente Evolution global inicializado")
    
    return _global_evolution_client


def close_all_connections():
    """
    Fecha todas as conexões do pool (útil para shutdown graceful)
    """
    global _global_evolution_client
    
    if _global_evolution_client:
        _global_evolution_client.http_session.close()
        _global_evolution_client = None
        logger.info("[POOL] Todas as conexões fechadas") 