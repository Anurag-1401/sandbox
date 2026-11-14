class DocumentValidationError(Exception):
    """Base exception for document validation errors."""


class UnsupportedFileTypeError(DocumentValidationError):
    pass


class FileSizeExceededError(DocumentValidationError):
    pass


class EmptyFileError(DocumentValidationError):
    pass


class InvalidFileSignatureError(DocumentValidationError):
    pass


class CorruptedDocumentError(DocumentValidationError):
    pass


class EncryptedDocumentError(DocumentValidationError):
    pass