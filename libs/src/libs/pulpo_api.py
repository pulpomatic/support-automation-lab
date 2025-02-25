import json

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

    def get_all_vehicles(self, get_archived: bool = False):
        """
        Retorna todos los vehículos de la cuenta sin ser mapeados
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "skip": 0,
            "take": 0,
        }
        if get_archived:
            params.update(
                {
                    "q": json.dumps(
                        {"AND": [{"parent": "archived", "archived": {"is": True}}]}
                    )
                }
            )

        response = requests.get(
            f"{self.base_url}/vehicles", headers=headers, params=params
        )
        if response.status_code != 200:
            raise ValueError(
                f"Error al obtener vehículos, el estatus devuelto {response.status_code}"
            )
        response_json = response.json()
        vehicles = response_json["vehicles"]
        if len(vehicles) == 0:
            raise ValueError("No hay vehículos asociados a la cuenta")

        return vehicles

    def get_all_payment_methods(self, get_archived=False):
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "skip": 0,
            "take": 0,
        }
        if get_archived:
            params.update(
                {
                    "q": json.dumps(
                        {"AND": [{"parent": "archived", "archived": {"is": True}}]}
                    )
                }
            )

        response = requests.get(
            f"{self.base_url}/payment-methods", headers=headers, params=params
        )
        if response.status_code != 200:
            raise ValueError(
                f"Error al obtener medios de pago, el estatus devuelto {response.status_code}"
            )
        response_json = response.json()
        payment_methods = response_json["paymentMethods"]
        if len(payment_methods) == 0:
            raise ValueError("No hay medios de pago asociados a la cuenta")

        return payment_methods

    def get_all_drivers(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"skip": 0, "take": 0, "userType": 4}
        response = requests.get(
            f"{self.base_url}/users", headers=headers, params=params
        )
        if response.status_code != 200:
            raise ValueError(
                f"Error al obtener conductores, el estatus devuelto {response.status_code}"
            )
        response_json = response.json()
        drivers = response_json["list"]
        if len(drivers) == 0:
            raise ValueError("No hay conductores asociados a la cuenta")

        return drivers

    def get_all_catalogs(self, catalog_type):
        """
        Retorna todos los catálogos de un tipo mapeados a 3 campos importantes id, nombre y referenceCode.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/catalogs/{catalog_type}", headers=headers
        )

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

    def get_all_suppliers(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "collectionType": "supplier",
            "skip": 0,
            "take": 0,
        }
        response = requests.get(
            f"{self.base_url}/suppliers", headers=headers, params=params
        )
        if response.status_code != 200:
            raise ValueError(
                f"Error al obtener proveedores, el estatus devuelto {response.status_code}"
            )
        response_json = response.json()
        suppliers = response_json["suppliers"]
        if len(suppliers) == 0:
            raise ValueError("No hay proveedores asociados a la cuenta")

        return [
            {
                "id": supplier["id"],
                "name": supplier["name"],
            }
            for supplier in suppliers
        ]
