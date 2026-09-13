from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="UNLOOP_",
        extra="ignore",
    )

    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8787
    discovery_level: int = 70
    database_path: str = "data/unloop.db"
    spotify_client_id: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8787/v1/connections/spotify/callback"
    musicbrainz_contact: str = ""
    listenbrainz_username: str = ""
    listenbrainz_token: str = ""
