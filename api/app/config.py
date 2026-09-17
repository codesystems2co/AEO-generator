from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    MOZ_ACCESS_ID: Optional[str] = None
    MOZ_SECRET_KEY: Optional[str] = None
    MOZ_API_TOKEN: Optional[str] = None
    SEMRUSH_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://172.17.0.1:11435"
    OLLAMA_MODEL: str = "llama3.2:3b"
    AIRLLM_BASE_URL: str = "http://142.132.230.226:8088"
    AIRLLM_ENABLED: bool = False
    AIRLLM_TIMEOUT_SEC: float = 180.0
    PACK_OLLAMA_TIMEOUT_SEC: float = 90.0
    CORE_BASE_URL: str = "http://172.17.0.1:18642"
    CORE_TIMEOUT_SEC: float = 25.0
    FRONTEND_PUBLIC_URL: str = "http://2.28.106.22:9012"
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "https://arkiphere.cloud/aeo/google/oauth/callback"
    GOOGLE_SA_JSON: Optional[str] = None
    GOOGLE_SA_FILE: Optional[str] = None
    GSC_SITE_URL: Optional[str] = None
    ODOO_URL: str = "https://arkiphere.cloud"
    ODOO_DB: str = "osh"
    ODOO_USERNAME: Optional[str] = None
    ODOO_API_KEY: Optional[str] = None
    ODOO_PASSWORD: Optional[str] = None
    ENTITLEMENT_STORE: str = "/app/data/entitlement.json"
    ENTITLEMENT_DEFAULT_LOGIN: str = "thedeployer777"
    ARKIPHERE_SHOP_URL: str = "https://arkiphere.cloud/shop"
    ARKIPHERE_LOGIN_URL: str = "https://arkiphere.cloud/web/login"
    ARKIPHERE_CONSUME_URL: str = "https://arkiphere.cloud"
    CONNECTION_STORE: str = "/app/data/connections.json"
    CONNECTION_FERNET_KEY: Optional[str] = None

    @property
    def cors_list(self) -> List[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if "*" in origins:
            return ["*"]
        extra = [
            "http://2.28.106.22:9012",
            "http://localhost:5173",
            "http://localhost:9012",
        ]
        for item in extra:
            if item not in origins:
                origins.append(item)
        return origins

    @property
    def moz_configured(self) -> bool:
        return bool(self.MOZ_API_TOKEN or (self.MOZ_ACCESS_ID and self.MOZ_SECRET_KEY))

    @property
    def semrush_configured(self) -> bool:
        return bool(self.SEMRUSH_API_KEY)

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def google_sa_configured(self) -> bool:
        return bool(self.GOOGLE_SA_JSON or self.GOOGLE_SA_FILE)


settings = Settings()
