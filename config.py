from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"  
    POSTGRES_PASSWORD: str = ""     
    POSTGRES_HOST: str = ""          
    POSTGRES_PORT: str = "6543"      
    POSTGRES_DB: str = "postgres"    


    class Config:
        env_file = ".env"

settings = Settings()