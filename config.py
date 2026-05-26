import os


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:password@db:3306/captive_portal",
    )
    SQLALCHEMY_DATABASE_URI: str = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    UNIFI_HOST: str = os.environ.get("UNIFI_HOST", "https://192.168.1.1")
    UNIFI_API_KEY: str = os.environ.get("UNIFI_API_KEY", "")
    UNIFI_SITE_ID: str = os.environ.get("UNIFI_SITE_ID", "default")
    UNIFI_VERIFY_SSL: bool = (
        os.environ.get("UNIFI_VERIFY_SSL", "false").lower() == "true"
    )
    PORTAL_AUTHORIZED_MINUTES: int = int(
        os.environ.get("PORTAL_AUTHORIZED_MINUTES", "480")
    )
    UNIFI_MOCK: bool = os.environ.get("UNIFI_MOCK", "false").lower() == "true"


class TestConfig(Config):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    WTF_CSRF_ENABLED: bool = False
