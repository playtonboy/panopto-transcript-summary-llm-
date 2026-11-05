# All settings in one place.
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
MODEL_NAME = "local-model"
TEMPERATURE = 0.2
ALLOWED_EXTENSIONS = (".txt",)
MAX_UPLOAD_MB = 5
DETAIL_LEVELS = {"Short": 5, "Medium": 10, "Detailed": 15}
DEFAULT_DETAIL_LEVEL = "Medium"
OUTPUT_LANGUAGES = ["English", "Dutch", "German"]  # SCRUM-43: languages the summary can be written in
DEFAULT_OUTPUT_LANGUAGE = "English"
REQUEST_TIMEOUT_S = 300   # how long we wait for the model (seconds)
MAX_OUTPUT_TOKENS = 1500  # longest answer the model may give
MIN_TRANSCRIPT_WORDS = 20
CHARS_PER_TOKEN = 4
CHUNK_TOKENS = 12000
CHUNK_OVERLAP_TOKENS = 200

AI_DISCLAIMER = (
    "AI-generated summary: created by a local language model from the lecture transcript. "
    "It may contain mistakes or miss details, so check important points against the original lecture."
)

ORCHESTRATOR_URL = "http://localhost:8000"
WORKER_POLL_S = 1.0   # how often an idle worker asks for a new job (seconds)
WORKER_SEEN_S = 10    # a worker counts as running if it asked for work this recently (seconds)
