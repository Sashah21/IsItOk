import time
import random
import logging
from typing import Optional, Dict, Any
from abc import ABC
import requests

# Configuracion de registro de eventos (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class APIClient(ABC):
    '''Gestor de consumición de API's de terceros con protocolos de seguridad y manejo de excepciones'''
    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        requests_per_second: float = 1.0,
        max_retries: int = 3,
        timeout: int = 10
    ):
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        # Configuracion del intervalo #
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

        # Configuracion de sesion (cookies y cabecera) #
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "MiAplicacionPro/1.0"
        })

        if auth_token:
            self.set_authentication(auth_token)
        if headers:
            self.session.headers.update(headers)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def set_authentication(self, token: str):
        '''Añade la autenticacion en los headers, tanto automática como manualmente en caso de ser necesario'''
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _wait_for_rate_limit(self):
        """Asegura que respetamos el intervalo minimo entre peticiones."""
        tiempo = time.time() - self.last_request_time
        if tiempo < self.min_interval:
            time.sleep(self.min_interval - tiempo)
        self.last_request_time = time.time()

    def _generic_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        '''Metodo generico que centraliza la lógica de gestión de llamadas a API's'''
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        method = method.upper()
        for attempt in range(self.max_retries + 1):
            # Trigger de tiempo de espera #
            self._wait_for_rate_limit()
            # - - - - - - - - - - - - - - #
            try:
                logging.info(msg=f"Petición {method} a {url} (Intento {attempt + 1})")
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    timeout=self.timeout
                )
                # Inspeccion  de cabeceras de limite (dependen de la API)
                remaining = response.headers.get("X-RateLimit-Remaining")
                if remaining is not None:
                    logging.debug(msg=f"Peticiones restantes en cuota: {remaining}")
                # Exito
                if 200 <= response.status_code < 300:
                    if response.status_code == 204 or not response.text.strip():
                        return {}
                    return response.json()
                # Limite excedido (429) o error de Servidor (5xx) -> Esperar X tiempo
                if response.status_code in [429, 500, 502, 503, 504]:
                    # Maximo numero de intentos #
                    if attempt == self.max_retries:
                        logging.error(msg=f"Alcanzado el máximo de reintentos. Código final: {response.status_code}")
                        response.raise_for_status()
                    # Verificar si se indico un Retry-After
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_time = float(retry_after)
                        logging.warning(msg=f"HTTP {response.status_code}. Servidor solicitó esperar {wait_time}s via Retry-After.")
                    else:
                        # Calculo de Backoff Exponencial con Jitter
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logging.warning(msg=f"HTTP {response.status_code}. Aplicando Backoff Exponencial: esperando {wait_time:.2f}s...")
                    time.sleep(wait_time)
                # Otros errores 4xx (Quitando errores de limites)
                else:
                    logging.error(msg=f"Error cliente HTTP {response.status_code}: {response.text}")
                    response.raise_for_status()
            # Fallos al conectar con la API
            except requests.exceptions.Timeout:
                logging.warning(msg=f"Timeout al conectar con {url}.")
                if attempt == self.max_retries:
                    raise
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                logging.error(msg=f"Error de red o conexión: {e}")
                raise

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Realiza una peticion GET al cliente."""
        return self._generic_request(method="GET", endpoint=endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Realiza una petición POST."""
        return self._generic_request(method="POST", endpoint=endpoint, params=params, data=data, json=json)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Realiza una petición PUT."""
        return self._generic_request(method="PUT", endpoint=endpoint, params=params, data=data, json=json)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Realiza una petición DELETE."""
        return self._generic_request(method="DELETE", endpoint=endpoint, params=params)

    def close(self):
        ''' Cierra la sesion HTTPS. '''
        self.session.close()
