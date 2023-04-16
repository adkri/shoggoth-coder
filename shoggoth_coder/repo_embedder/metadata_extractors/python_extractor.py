import ast
from .extractor import LanguageMetadataExtractor, metadata_to_amalgamation
from collections import defaultdict


class PythonMetadataExtractor(LanguageMetadataExtractor):
    def extract_metadata(self, file_path: str) -> dict:
        def _process_classes_data(classes):
            # classes_data = defaultdict(lambda: {"methods": [], "fields": []})
            classes_data = {}
            for class_name, class_data in classes.items():
                classes_data[class_name] = {}
                classes_data[class_name]["methods"] = {}
                classes_data[class_name]["fields"] = []
                for method_name, signature in class_data["methods"].items():
                    classes_data[class_name]["methods"][method_name] = signature
                for field_name, _ in class_data["fields"].items():
                    classes_data[class_name]["fields"].append(f"{field_name}")
            return classes_data

        with open(file_path, "r") as source:
            tree = ast.parse(source.read())
            function_signature_extractor = FunctionSignatureExtractor()
            function_signature_extractor.visit(tree)
            constants_extractor = ConstantsExtractor()
            constants_extractor.visit(tree)
            class_extractor = ClassExtractor()
            class_extractor.visit(tree)

            final_classes = _process_classes_data(class_extractor.classes)

            return {
                "function_signatures": function_signature_extractor.function_signatures,
                "constants": constants_extractor.constants,
                "classes": final_classes
            }


class FunctionSignatureExtractor(ast.NodeVisitor):
    def __init__(self):
        self.function_signatures = {}

    def visit_FunctionDef(self, node):
        arg_names = [arg.arg for arg in node.args.args]
        self.function_signatures[node.name] = arg_names

    def visit_ClassDef(self, node):
        # dont traverse into classes
        pass


class ConstantsExtractor(ast.NodeVisitor):
    def __init__(self):
        self.constants = {}

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                value = self.get_constant_value(node.value)
                self.constants[target.id] = value

    def get_constant_value(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func
            if attr.attr == 'get' and isinstance(attr.value, ast.Attribute) and attr.value.attr == 'environ':
                default_value = node.args[1].value if len(node.args) > 1 else None
                return f"default: {default_value}"
        return "<unparsed expression>"


class ClassExtractor(ast.NodeVisitor):
    def __init__(self):
        self.classes = defaultdict(lambda: {"methods": {}, "fields": {}})
        self.current_class = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.generic_visit(node)
        # self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class:
            arg_names = [arg.arg for arg in node.args.args if arg.arg != 'self']
            self.classes[self.current_class]["methods"][node.name] = arg_names

    def visit_Assign(self, node):
        if self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                    self.classes[self.current_class]["fields"][target.attr] = None


