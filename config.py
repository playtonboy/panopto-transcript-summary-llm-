"""Central configuration.

Every tunable parameter lives here so it can be changed in a single place
(see "maintainability" in the requirements document).
"""

# LM Studio exposes an OpenAI-compatible server on localhost (Developer tab -> Start Server).
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
# Name of the model loaded in LM Studio. "local-model" works when only one model is loaded.
MODEL_NAME = "local-model"
REQUEST_TIMEOUT_S = 300

# Low temperature keeps repeated summaries of the same transcript consistent (FR12).
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 1024

# Context handling (FR11 / UR3). Rough rule of thumb: 1 token ~ 4 characters of English text.
CHARS_PER_TOKEN = 4
MODEL_CONTEXT_TOKENS = 8192
# Leave room for the prompt and the model's answer inside the context window.
CHUNK_TOKENS = 5000
CHUNK_OVERLAP_TOKENS = 200

# Input validation (FR5 / UR11).
ALLOWED_EXTENSIONS = (".txt",)
MIN_TRANSCRIPT_WORDS = 50
MAX_UPLOAD_MB = 5

# Summary length presets (FR14 / UR6). Values are the target number of bullet points.
DETAIL_LEVELS = {
    "Short": 5,
    "Medium": 10,
    "Detailed": 15,
}
DEFAULT_DETAIL_LEVEL = "Medium"  # FR15

# Output languages offered in the UI (FR10).
OUTPUT_LANGUAGES = ["English", "Dutch", "German", "French", "Spanish", "Lithuanian"]
DEFAULT_OUTPUT_LANGUAGE = "English"

# NFR12
AI_DISCLAIMER = (
    "This summary was generated with the help of a locally running AI model. "
    "It may contain mistakes; check important details against the original lecture."
)
