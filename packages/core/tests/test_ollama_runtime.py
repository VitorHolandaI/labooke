from labooke_core.config import Settings
from labooke_core.llm import OpenAICompatibleClient
from labooke_core.services.ollama_runtime import OLLAMA_BASE_URL_KEY, OllamaRuntime
from labooke_core.store.db import open_db
from labooke_core.store.settings_repo import SettingsRepo


def test_runtime_uses_environment_endpoints_without_override():
    repo = SettingsRepo(open_db(":memory:", seed_tags=False))
    settings = Settings(
        embed_base_url="http://embed-env",
        llm_base_url="http://llm-env/v1",
        llm_model="chat-model",
    )
    runtime = OllamaRuntime(settings, repo)

    assert runtime.active_base_url() == "http://embed-env"
    assert runtime.override_base_url() is None
    client = runtime.chat_client()
    assert isinstance(client, OpenAICompatibleClient)
    assert client.base_url == "http://llm-env/v1"


def test_runtime_admin_override_changes_new_clients_immediately():
    repo = SettingsRepo(open_db(":memory:", seed_tags=False))
    settings = Settings(
        embed_base_url="http://embed-env",
        llm_base_url="http://llm-env/v1",
        llm_model="chat-model",
    )
    runtime = OllamaRuntime(settings, repo)
    repo.set(OLLAMA_BASE_URL_KEY, "http://gpu-host")

    assert runtime.active_base_url() == "http://gpu-host"
    client = runtime.chat_client()
    assert isinstance(client, OpenAICompatibleClient)
    assert client.base_url == "http://gpu-host/v1"

    repo.delete(OLLAMA_BASE_URL_KEY)
    assert runtime.active_base_url() == "http://embed-env"
