from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    MOZ_ACCESS_ID: Optional[str] = None
    MOZ_SECRET_KEY: Optional[str] = None
    MOZ_API_TOKEN: Optional[str] = None
    SEMRUSH_API_KEY: Optional[str] = None
    
    @property
    def cors_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]
    
    @property
    def moz_configured(self) -> bool:
        return bool(self.MOZ_API_TOKEN or (self.MOZ_ACCESS_ID and self.MOZ_SECRET_KEY))
    
    @property
    def semrush_configured(self) -> bool:
        return bool(self.SEMRUSH_API_KEY)


settings = Settings()
