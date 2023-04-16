import esprima
from .extractor import LanguageMetadataExtractor
from typing import List

class JavascriptMetadataExtractor(LanguageMetadataExtractor):
    def extract_metadata(self, file_path: str) -> dict:
        """
        Extract metadata from a JavaScript code file.

        Args:
            file_path (str): The path to the JavaScript code file.

        Returns:
            dict: A dictionary containing the extracted metadata.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            code = file.read()

        # Initialize dictionaries to store extracted metadata
        function_signatures = {}
        constants = {}
        classes = {}


        try:
            tree = esprima.parseScript(code)

            def process_node(node):
                def process_function(node, func_name):
                    function_signatures[func_name] = [p.name for p in node.params]

                def process_expression(expression):
                    if isinstance(expression, esprima.nodes.CallExpression):
                        for arg in expression.arguments:
                            if isinstance(arg, esprima.nodes.ArrowFunctionExpression):
                                process_function(arg, "anon")

                if isinstance(node, esprima.nodes.FunctionDeclaration) or isinstance(node, esprima.nodes.AsyncFunctionDeclaration):
                    func_name = node.id.name
                    process_function(node, func_name)

                elif isinstance(node, esprima.nodes.ArrowFunctionExpression):
                    process_function(node, "anon")

                elif isinstance(node, esprima.nodes.ExpressionStatement):
                    process_expression(node.expression)

                elif isinstance(node, esprima.nodes.BlockStatement):
                    for child_node in node.body:
                        process_node(child_node)

                elif isinstance(node, esprima.nodes.CallExpression):
                    for arg in node.arguments:
                        if isinstance(arg, esprima.nodes.ArrowFunctionExpression):
                            process_function(arg, "anon")

                elif isinstance(node, esprima.nodes.FunctionExpression):
                    process_function(node, "anon")

                elif isinstance(node, esprima.nodes.VariableDeclaration):
                    for declaration in node.declarations:
                        if isinstance(declaration.init, esprima.nodes.Literal):
                            constant = {
                                "name": declaration.id.name,
                                "value": declaration.init.value,
                            }
                            constants[constant["name"]] = constant["value"]
                elif isinstance(node, esprima.nodes.ClassDeclaration):
                    methods = {}
                    for class_element in node.body.body:
                        if isinstance(class_element, esprima.nodes.MethodDefinition):
                            methods[class_element.key.name] = [p.name for p in class_element.value.params]
                    classes[node.id.name] = {
                        "methods": methods,
                        "fields": []
                    }

                if hasattr(node, "body"):
                    if isinstance(node.body, list):
                        for child_node in node.body:
                            process_node(child_node)
                    else:
                        process_node(node.body)

            for node in tree.body:
                process_node(node)

        except:
            pass

        metadata = {
            'function_signatures': function_signatures,
            'constants': constants,
            'classes': classes
        }
        return metadata
