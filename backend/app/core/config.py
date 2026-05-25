"""全局配置：基于 pydantic-settings，从环境变量 / .env 加载。"""

from typing import List, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 应用元数据
    PROJECT_NAME: str = "quant-platform"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "quant_user"
    MYSQL_PASSWORD: str = "quant_password"
    MYSQL_DATABASE: str = "quant_platform"
    MYSQL_POOL_SIZE: int = 10
    MYSQL_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # 数据源（akshare 默认，tushare 后期启用）
    DATA_SOURCE: Literal["akshare", "tushare"] = "akshare"
    AKSHARE_TIMEOUT: int = 30
    # 默认不读 macOS/Shell 系统代理，避免 Clash 等未启动时出现 ProxyError
    AKSHARE_USE_SYSTEM_PROXY: bool = False
    # 若必须走代理访问东方财富，在此填写，例如 http://127.0.0.1:7890
    AKSHARE_HTTP_PROXY: str = ""
    TUSHARE_TOKEN: str = ""

    # 调度器（APScheduler）
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    SCHEDULER_DAILY_SYNC_HOUR: int = 16
    SCHEDULER_DAILY_SYNC_MINUTE: int = 30

    # 默认监控股票池（CSV，不带前缀，例如 "600519,000001,300750"）
    WATCH_STOCKS: str = "600519,000001,300750"

    # CORS（前端地址）
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # JWT 认证
    JWT_SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # QQ 邮箱 SMTP（验证码）
    QQ_SMTP_HOST: str = "smtp.qq.com"
    QQ_SMTP_PORT: int = 465
    QQ_EMAIL: str = ""
    QQ_EMAIL_AUTH_CODE: str = ""
    EMAIL_CODE_EXPIRE_SECONDS: int = 300
    EMAIL_CODE_RESEND_COOLDOWN: int = 60

    # 开发环境默认超级管理员
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""
    ADMIN_EMAIL: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def watch_stocks_list(self) -> list[str]:
        """``WATCH_STOCKS`` 解析为去空格、去空项的列表。"""
        return [s.strip() for s in self.WATCH_STOCKS.split(",") if s.strip()]


settings = Settings()
