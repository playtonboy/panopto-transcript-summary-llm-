import config
from fake_lmstudio import start_fake_server
from summarizer import llm_client


def test_loaded_models_lists_the_ids_from_lm_studio(monkeypatch):
    server, url = start_fake_server()
    monkeypatch.setattr(config, "LMSTUDIO_BASE_URL", url)
    try:
        assert llm_client.loaded_models() == ["local-model"]
        monkeypatch.setattr(config, "MODEL_NAME", "local-model")
        assert llm_client.model_warning() is None
    finally:
        server.shutdown()


def test_warning_names_the_loaded_model_when_the_id_is_wrong(monkeypatch):
    server, url = start_fake_server()
    monkeypatch.setattr(config, "LMSTUDIO_BASE_URL", url)
    monkeypatch.setattr(config, "MODEL_NAME", "qwen2.5-7b-instruct")
    try:
        warning = llm_client.model_warning()
    finally:
        server.shutdown()
    assert "qwen2.5-7b-instruct" in warning and "local-model" in warning


def test_warning_when_lm_studio_is_not_running(monkeypatch):
    monkeypatch.setattr(config, "LMSTUDIO_BASE_URL", "http://127.0.0.1:9/v1")  # nothing listens on port 9
    assert llm_client.loaded_models() == []
    assert "not reachable" in llm_client.model_warning()


def test_worker_takes_the_model_from_the_command_line():
    from worker.main import parse_args

    args = parse_args(["laptop-1", "--model", "meta-llama-3.1-8b-instruct"])
    assert args.name == "laptop-1"
    assert args.model == "meta-llama-3.1-8b-instruct"
    assert parse_args([]).model == config.MODEL_NAME