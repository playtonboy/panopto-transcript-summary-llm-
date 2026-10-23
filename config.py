# All settings in one place.
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
MODEL_NAME = "local-model"
TEMPERATURE = 0.2
ALLOWED_EXTENSIONS = (".txt",)
MAX_UPLOAD_MB = 5
DETAIL_LEVELS = {"Short": 5, "Medium": 10, "Detailed": 15}
DEFAULT_DETAIL_LEVEL = "Medium"
REQUEST_TIMEOUT_S = 300   # how long we wait for the model (seconds)
MAX_OUTPUT_TOKENS = 1500  # longest answer the model may give
MIN_TRANSCRIPT_WORDS = 20
CHARS_PER_TOKEN = 4
CHUNK_TOKENS = 12000
CHUNK_OVERLAP_TOKENS = 200
