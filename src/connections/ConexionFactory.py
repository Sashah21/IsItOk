from typing import Optional
import json
from .ApiClient import APIClient

class GithubClient(APIClient):
    def __init__(self, token: Optional[str] = None):
        github_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        super().__init__(
            base_url="https://api.github.com",
            auth_token=token,
            headers=github_headers,
            requests_per_second=1.0,  # restriccion de 60 peticiones por minuto
            max_retries=3
        )

class OsvClient(APIClient):
    def __init__(self, token: Optional[str] = None):
        github_headers = {
            "Accept": "application/json",
        }
        super().__init__(
            base_url="https://api.osv.dev",
            auth_token=token,
            headers=github_headers,
            requests_per_second=1.0,
            max_retries=3
        )

    def consultar_vulnerabilidades_lote(self,dependencias: list) -> json:
        payload = {
            "queries": [
                {
                    "package": {
                        "name": dep["nombre"],
                        "ecosystem": dep["ecosistema"]
                    },
                    "version": dep["version"]
                }
                for dep in dependencias
            ]
        }
        response = self.post(endpoint="v1/querybatch",json=payload)
        return response

    def consultar_vulnerabilidad(self, dependencia: dict) -> json:
        query_url = {
            "PyPI" : f"https://pypi.org/pypi/{dependencia.get("nombre")}/json"
        }
        for entorno, url in query_url.items():
            if dependencia.get("ecosistema") == entorno:
                request : APIClient = APIClient(base_url= url)
                break
        respuesta = request.get(endpoint="")



class ConexionFactory:
    conexiones = {
        "osv" : OsvClient,
        "github" : GithubClient,
    }

    def crearConexion(self, api : str):
        conn : APIClient = self.conexiones.get(api.lower())
        if not conn:
            raise ValueError(f'{conn} no es soportado.')
        return conn()
