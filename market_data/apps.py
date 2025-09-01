from django.apps import AppConfig


class MarketDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'market_data'
    verbose_name = 'Market Data'
    
    def ready(self):
        """Code executed when app is ready"""
        try:
            import market_data.signals  # noqa
        except ImportError:
            pass
