from abc import ABC, abstractmethod
from typing import List, TypedDict

class ClassMethodDict(TypedDict):
    methods: dict[str, List[str]]
    fields: List[str]


class MetadataDict(TypedDict):
    function_signatures: dict[str, List[str]]
    constants: dict[str, object]
    classes: dict[str, ClassMethodDict]


class LanguageMetadataExtractor(ABC):
    """Base class for language metadata extractors."""

    @abstractmethod
    def extract_metadata(self, file_path: str) -> MetadataDict:
        """Extract metadata from a file.

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary with metadata.
        """
        pass


def metadata_to_amalgamation(metadata: MetadataDict) -> str:
    """Convert metadata to a string that can be used as an amalgamation.

    Args:
        metadata: Dictionary with metadata.

    Returns:
        String with metadata.
    """
    function_signatures = metadata['function_signatures']
    constants = metadata['constants']
    classes = metadata['classes']

    # Convert function signatures to a string
    function_signatures_str = '###func sigs:\n'
    for function_name, arg_names in function_signatures.items():
        function_signatures_str += f'{function_name}({", ".join(arg_names)})\n'

    # Convert constants to a string
    constants_str = '###consts:\n'
    for constant_name, constant_value in constants.items():
        constants_str += f'{constant_name}={constant_value}\n'

    # Convert class information to a string
    classes_str = '###classes:\n'
    for class_name, class_data in classes.items():
        classes_str += f'{class_name}:\n'
        for method_name, method_signatures in class_data['methods'].items():
            classes_str += f'{class_name}::{method_name}({", ".join(method_signatures)})\n'
        for field in class_data['fields']:
            classes_str += f'{class_name}::{field}\n'
        classes_str += '\n'

    # Return the amalgamation
    return function_signatures_str + constants_str + classes_str

def get_metadata_extractor(language: str) -> LanguageMetadataExtractor:
    """Return an extractor for the given language.

    Args:
        language: Language name.

    Returns:
        LanguageMetadataExtractor instance.
    """
    if language == 'python' or language == 'py':
        from .python_extractor import PythonMetadataExtractor
        return PythonMetadataExtractor()
    elif language == 'javascript' or language == 'js':
        from .javascript_extractor import JavascriptMetadataExtractor
        return JavascriptMetadataExtractor()
    else:
        raise ValueError(f'Invalid language: {language}')

