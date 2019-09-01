class Parameter:
    def __init__(self, name: str, type: str, min=-999999.0, max=999999.0, default=0.0):
        if type not in ["float", "str", "string", "int", "bool"]:
            raise AttributeError("Zły typ, nie ma takiego typu")

        if type == "default":
            default = False

        if type in ["float", "int"]:
            self.parametersDict = {
                "name": name,
                "type": type,
                "min": min,
                "max": max,
                "default": default,
            }
        else:
            self.parametersDict = {
                "name": name,
                "type": type,
                "default": default,
            }

    def dict(self):
        return self.parametersDict
