from pydantic import BaseSettings


class Settings(BaseSettings):
    queue: str
    scheduler: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        fields = {"queue": {"env": "queue"}}


settings = Settings()
