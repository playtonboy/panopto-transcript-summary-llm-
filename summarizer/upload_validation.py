import config
from summarizer.transcript import TranscriptError

def validate_upload(filename: str, size_bytes: int) -> None:
    """Check whether an uploaded transcript file is valid."""

    if not filename.lower().endswith(config.ALLOWED_EXTENSIONS):
        raise TranscriptError(
            "Unsupported file type. Please upload a .txt transcript."
        )

    #reject empty files
    if size_bytes == 0:
        raise TranscriptError(
            "The uploaded file is empty."
        )

    #reject files larger than the allowed limit
    if size_bytes > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise TranscriptError(
            f"The file is larger than {config.MAX_UPLOAD_MB} MB."
        )

def decode(data: bytes) -> str:
    """Convert uploaded file bytes into readable text."""

    if data.startswith(b"%PDF-"):
        raise TranscriptError(
            "This file appears to be a PDF. Please upload a .txt transcript."
        )

    # UTF-16 files have a BOM at the beginning
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            raise TranscriptError(
                "Could not decode the UTF-16 transcript."
            )

    # Try UTF-8 first
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass

    # Fall back to Latin-1 for older text files
    return data.decode("latin-1")
