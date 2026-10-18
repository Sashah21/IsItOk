from typing import Optional
import json
import jmespath

class JsonExtractor:
    def __init__(self, data: json):
        self.data = data


    def search(self, expression: str):
        '''Busca {expression} en los datos almacenados en la clase y devuelve el valor de esa clave'''
        return jmespath.search(expression, self.data)

    def search_by_suffix(self,
                       array_key: str,
                       target_field: str,
                       suffix: str,
                       returned_field:Optional[str]):
        '''
        Busca en el arbol {array_key} el campo {target_field} que acabe en {suffix} y devuelve {returned_field}.\n
        Si no hay {returned_field} devuelve el arbol entero filtrado
        '''
        if returned_field is not None:
            returned_field = f".{returned_field}"  
        query = f"{array_key}[?ends_with({target_field}, '{suffix}')]" + returned_field
        return self.search(query)
