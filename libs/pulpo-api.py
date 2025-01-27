import requests


class PulpoApi:
    """
    En Pulpo API se define un token y una base_url que sirven para poder definir la cuenta y el entorno
    donde se van a ejecutar las peticiones.
    Es importante entender que los datos devueltos por las API estarán asociados a la cuenta del token.
    """
    token: str
    base_url: str

    def __init__(self, token, base_url):
        self.token = token
        self.base_url = base_url

    def get_all_vehicles(self):
        """
        Retorna todos los vehículos de la cuenta sin ser mapeados
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "skip": 0,
            "take": 0,
        }
        response = requests.get(f"{self.base_url}/vehicles", headers=headers, params=params)
        if response.status_code != 200:
            raise ValueError(
                f"Error al obtener vehículos, el estatus devuelto {response.status_code}"
            )
        response_json = response.json()
        vehicles = response_json["vehicles"]
        if len(vehicles) == 0:
            raise ValueError("No hay vehículos asociados a la cuenta")

        return vehicles

    def get_all_catalogs(self, catalog_type):
        """
        Retorna todos los catálogos de un tipo mapeados a 3 campos importantes id, nombre y referenceCode.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/catalogs/{catalog_type}", headers=headers)

        if response.status_code != 200:
            raise ValueError(
                f"Error al obtener catálogos, el estatus devuelto {response.status_code}"
            )
        catalogs = response.json()

        if len(catalogs) == 0:
            raise ValueError(f"No hay catálogos {catalog_type} asociados a la cuenta")

        return [
            {
                "id": catalog["id"],
                "name": catalog["name"],
                "referenceCode": catalog["referenceCode"],
            }
            for catalog in catalogs
        ]