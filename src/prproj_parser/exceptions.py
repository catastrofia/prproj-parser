"""Custom exceptions for prproj-parser."""


class PrprojError(Exception):
    """Base exception for all prproj-parser errors."""


class PrprojParseError(PrprojError):
    """Raised when the XML cannot be parsed — corrupt file, invalid gzip, etc."""


class PrprojVersionError(PrprojError):
    """Raised when the PremiereData version is unsupported."""
    def __init__(self, version: str):
        self.version = version
        super().__init__(f"Unsupported PremiereData version: {version!r}")


class ReferenceNotFoundError(PrprojError):
    """Raised when an ObjectRef/ObjectURef points to a non-existent element."""
    def __init__(self, ref_type: str, ref_value: str):
        self.ref_type = ref_type
        self.ref_value = ref_value
        super().__init__(f"{ref_type}={ref_value!r} not found in index")


class SequenceNotFoundError(PrprojError):
    """Raised when a requested sequence name does not exist."""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Sequence {name!r} not found in project")
