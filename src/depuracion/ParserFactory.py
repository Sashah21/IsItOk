from abc import ABC

class DependencyParser(ABC):

    @staticmethod
    def parse_for_osv(file: str):
        pass

class PythonDependencyParser(DependencyParser):

    @staticmethod
    def parse_for_osv(file: str):
        dependencies = []
        individual = []
        for line in file.splitlines():
            line = line.strip()
            # Ignorar comentarios
            if not line or line.startswith("#"):
                continue
            for operador in ["==", ">=", "<=", "~=", "!=", ">", "<"]:
                if operador in line:
                    name, version = line.split(operador, 1)
                    dependencies.append({"nombre": name.strip(), "ecosistema": "PyPI", "version": version.strip()})
                    break
            # Si no especifica versión
            individual.append({"nombre": line.strip(), "version": version.strip()})
        result = {"conjunto": dependencies, "individuales": individual}
        return result

class ParserFactory:
    parser = {
        "python" : PythonDependencyParser
    }

    @staticmethod
    def crearParser(api : str) -> DependencyParser:
        result: DependencyParser = ParserFactory.parser.get(api.lower())
        if not result:
            raise ValueError(f'{result} no es soportado.')
        return result()
