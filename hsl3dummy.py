import json

class DebugSection:
    def log(self, text):
        print(text)
    
class Hsl3Framework:
    def __init__(self, configfile):
        with open(configfile) as f:
            self.config = json.load(f)["module"]
        self.debug = DebugSection()
        self.inputs = self.interfaces_to_dict(self.config["inputs"])
        self.outputs = self.interfaces_to_dict(self.config["outputs"])
        self.is_mock = True

    def interfaces_to_dict(self, interface_list):
        return {item["identifier"]: item for item in interface_list}
        
    def create_debug_section(self):
        return self.debug

    def get_module_id(self):
        return self.config["id"]

    def run_in_context(self, func, *args):
        func(*args[0])

    def set_output(self, key, value):
        assert key in self.outputs
        if self.outputs[key]["type"] == "string":
            assert type(value) == bytes
        else:
            assert type(value) == float or type(value) == int
        print("Setting output {} to {}".format(key, value))

class Hsl3Slot:
    def __init__(self, value):
        self.value = value
        self.changed = False

class Hsl3Slots:
    def __init__(self, elements):
        self.elements = {key: Hsl3Slot(value) for key, value in elements.items()}

    def __getitem__(self, key):
        return self.elements[key]
        

