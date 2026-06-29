from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "clinical_trials_doc"
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/clinical_trials_sql"


settings = Settings()
