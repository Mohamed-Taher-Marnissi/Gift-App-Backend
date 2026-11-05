from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    mail_username: str
    mail_password: str
    mail_from: str
    mail_server: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    frontend_host: str
    cloudinary_api_secret: str
    cloudinary_api_key: str
    cloud_name: str
    
    groq_api_key: str
    groq_api_url: str
    groq_ai_model: str

    openrouter_api_key: str
    openrouter_api_url: str
    openrouter_ai_model: str

        
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()