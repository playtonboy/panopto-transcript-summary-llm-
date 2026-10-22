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

    for encoding in ("utf-8-sig", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    return data.decode("latin-1")
