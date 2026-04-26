from __future__ import annotations

import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured


def _reload_settings_with_env(monkeypatch, env: dict[str, str | None]) -> None:
    """Reload backend.config.settings under a controlled os.environ snapshot."""

    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    import config.settings as settings_module

    importlib.reload(settings_module)


class TestProductionEnvValidation:
    def test_production_with_missing_postgres_password_raises(self, monkeypatch):
        with pytest.raises(ImproperlyConfigured) as excinfo:
            _reload_settings_with_env(
                monkeypatch,
                {
                    "ENV": "production",
                    "DJANGO_SECRET_KEY": "real-secret",
                    "DJANGO_ALLOWED_HOSTS": "example.com",
                    "POSTGRES_DB": "x",
                    "POSTGRES_USER": "x",
                    "POSTGRES_PASSWORD": None,
                    "POSTGRES_HOST": "db",
                },
            )
        assert "POSTGRES_PASSWORD" in str(excinfo.value)

    def test_production_with_dev_default_secret_raises(self, monkeypatch):
        with pytest.raises(ImproperlyConfigured) as excinfo:
            _reload_settings_with_env(
                monkeypatch,
                {
                    "ENV": "production",
                    "DJANGO_SECRET_KEY": "dev-insecure-key-change-in-production",
                    "DJANGO_ALLOWED_HOSTS": "example.com",
                    "POSTGRES_DB": "x",
                    "POSTGRES_USER": "x",
                    "POSTGRES_PASSWORD": "x",
                    "POSTGRES_HOST": "db",
                },
            )
        assert "DJANGO_SECRET_KEY" in str(excinfo.value)

    def test_development_does_not_validate(self, monkeypatch):
        # Should not raise even though required prod vars are unset.
        _reload_settings_with_env(
            monkeypatch,
            {
                "ENV": "development",
                "POSTGRES_PASSWORD": None,
                "POSTGRES_HOST": None,
            },
        )

    def test_production_with_all_vars_set_succeeds(self, monkeypatch):
        _reload_settings_with_env(
            monkeypatch,
            {
                "ENV": "production",
                "DJANGO_SECRET_KEY": "real-secret-please",
                "DJANGO_ALLOWED_HOSTS": "example.com",
                "POSTGRES_DB": "x",
                "POSTGRES_USER": "x",
                "POSTGRES_PASSWORD": "x",
                "POSTGRES_HOST": "db",
            },
        )

    @pytest.fixture(autouse=True)
    def _restore_settings_at_end(self, monkeypatch):
        # Ensure later tests run with the real (development) settings.
        yield
        for key in [
            "ENV",
            "DJANGO_SECRET_KEY",
            "DJANGO_ALLOWED_HOSTS",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_HOST",
        ]:
            monkeypatch.delenv(key, raising=False)
        import config.settings as settings_module

        importlib.reload(settings_module)
