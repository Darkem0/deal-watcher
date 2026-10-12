from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, model_validator


class ConfigLoadError(ValueError):
    """A configuration file could not be parsed or validated."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Thresholds(StrictModel):
    normal_drop_percent: float = Field(gt=0, le=100)
    high_drop_percent: float = Field(gt=0, le=100)
    urgent_drop_percent: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def ordered(self) -> Thresholds:
        if not self.normal_drop_percent < self.high_drop_percent < self.urgent_drop_percent:
            raise ValueError("thresholds must satisfy normal < high < urgent")
        return self


class ProductDefaults(StrictModel):
    poll_interval_minutes: int = Field(gt=0)
    target_price_try: int | None = Field(default=None, ge=0)
    thresholds: Thresholds


class CategoryPolicy(StrictModel):
    minimum_models: int = Field(gt=0)
    include_exact: str = Field(min_length=1)
    exclude_terms: list[str] = Field(min_length=1)


class ProductConfig(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    source: Literal["akakce"]
    source_type: Literal["product_page", "category_page"]
    name: str = Field(min_length=1)
    url: HttpUrl
    target_price_try: int | None = Field(default=None, ge=0)
    category_policy: CategoryPolicy | None = None

    @model_validator(mode="after")
    def category_requirements(self) -> ProductConfig:
        if self.source_type == "category_page" and self.category_policy is None:
            raise ValueError("category_page requires category_policy")
        if self.source_type == "product_page" and self.category_policy is not None:
            raise ValueError("category_policy is only valid for category_page")
        return self


class ProductsConfig(StrictModel):
    version: Literal[1]
    defaults: ProductDefaults
    products: list[ProductConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> ProductsConfig:
        ids = [product.id for product in self.products]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise ValueError(f"duplicate product id(s): {', '.join(duplicates)}")
        return self


class ForumSourceConfig(StrictModel):
    name: str = Field(min_length=1)
    url: HttpUrl


class ForumPollingConfig(StrictModel):
    first_page_minutes: int = Field(gt=0)
    second_page_minutes: int = Field(gt=0)
    jitter_seconds: tuple[int, int]

    @model_validator(mode="after")
    def valid_jitter(self) -> ForumPollingConfig:
        low, high = self.jitter_seconds
        if low < 0 or high < low:
            raise ValueError("jitter_seconds must be non-negative and ordered")
        return self


class ForumPrioritiesConfig(StrictModel):
    urgent_categories: list[str]
    normal_categories: list[str]
    digest_categories: list[str]


class ForumConfig(StrictModel):
    version: Literal[1]
    source: ForumSourceConfig
    polling: ForumPollingConfig
    baseline_on_first_success: bool
    notify_reply_count_only: bool
    priorities: ForumPrioritiesConfig
    urgent_signals: list[str]
    categories: list[str]
    re_notification_events: list[str]
    ignore_or_classify: list[str]

    @model_validator(mode="after")
    def validate_categories(self) -> ForumConfig:
        if len(self.categories) != len(set(self.categories)):
            raise ValueError("forum categories must be unique")
        configured = set(self.categories)
        groups = (
            self.priorities.urgent_categories
            + self.priorities.normal_categories
            + self.priorities.digest_categories
        )
        unknown = sorted(set(groups) - configured)
        if unknown:
            raise ValueError(f"priority categories are not declared: {', '.join(unknown)}")
        overlap = len(groups) != len(set(groups))
        if overlap:
            raise ValueError("a forum category may belong to only one priority group")
        unassigned = sorted(configured - set(groups))
        if unassigned:
            raise ValueError(f"forum categories lack a priority: {', '.join(unassigned)}")
        return self


class ApplicationConfig(StrictModel):
    timezone: str = Field(min_length=1)
    platform: Literal["windows", "linux", "macos", "auto"]


class NetworkConfig(StrictModel):
    timeout_seconds: int = Field(gt=0)
    connect_timeout_seconds: int = Field(default=10, gt=0)
    read_timeout_seconds: int = Field(default=20, gt=0)
    write_timeout_seconds: int = Field(default=20, gt=0)
    pool_timeout_seconds: int = Field(default=10, gt=0)
    max_retries: int = Field(ge=0)
    backoff_seconds: list[int]
    min_request_interval_seconds: float = Field(default=3.0, ge=0)
    max_response_bytes: int = Field(default=5_000_000, gt=0)
    user_agent: str = Field(default="deal-watcher/0.2 (+offline-first monitor)", min_length=1)
    respect_rate_limits: Literal[True]
    playwright_fallback: Literal["controlled_only"]


class AkakceFetchConfig(StrictModel):
    enabled: bool = False
    status: Literal["experimental"] = "experimental"
    fetch_mode: Literal["http", "browser", "auto"] = "http"
    browser_fallback_enabled: bool = False
    browser_headless: bool = True
    minimum_request_interval_seconds: int = Field(default=300, ge=0)


class StorageConfig(StrictModel):
    database_path: Path
    log_directory: Path
    instance_lock_path: Path


class NotificationsConfig(StrictModel):
    channels: list[Literal["telegram", "windows_toast", "dry_run", "logging"]]
    digest_interval_minutes: int = Field(gt=0)
    send_runtime_started: bool = True
    send_first_successful_scan: bool = True


class RulesConfig(StrictModel):
    captcha_bypass: Literal["forbidden"]
    automatic_purchase: Literal["forbidden"]
    suspicious_price_action: Literal["flag_anomaly"]


class SettingsConfig(StrictModel):
    version: Literal[1]
    application: ApplicationConfig
    network: NetworkConfig
    akakce: AkakceFetchConfig = Field(default_factory=AkakceFetchConfig)
    storage: StorageConfig
    notifications: NotificationsConfig
    rules: RulesConfig


class AppConfig(StrictModel):
    products: ProductsConfig
    forum: ForumConfig
    settings: SettingsConfig


def _load_yaml(path: Path, model: type[BaseModel]) -> BaseModel:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigLoadError(f"Cannot read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigLoadError(f"YAML root must be a mapping: {path}")
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise ConfigLoadError(f"Invalid configuration {path}: {details}") from exc


def load_config(config_dir: Path) -> AppConfig:
    return AppConfig(
        products=_load_yaml(config_dir / "products.yaml", ProductsConfig),
        forum=_load_yaml(config_dir / "forum.yaml", ForumConfig),
        settings=_load_yaml(config_dir / "settings.yaml", SettingsConfig),
    )
