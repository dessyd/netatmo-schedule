import os
import configparser
from dotenv import load_dotenv

# --------------------------------
# Constants
# --------------------------------

# File paths
DEFAULT_ENV_FILE = ".env"
DEFAULT_CONFIG_FILE = "netatmo_config.ini"
STATE_FILE = "netatmo_state.json"

# API endpoints
NETATMO_AUTH_URL = "https://api.netatmo.com/oauth2/token"
NETATMO_AUTH_AUTHORIZE_URL = "https://api.netatmo.com/oauth2/authorize"
NETATMO_STATION_DATA_URL = "https://api.netatmo.com/api/getstationsdata"

# Environment variable names
ENV_CLIENT_ID = "NETATMO_CLIENT_ID"
ENV_CLIENT_SECRET = "NETATMO_CLIENT_SECRET"
ENV_REFRESH_TOKEN = "NETATMO_REFRESH_TOKEN"
ENV_REDIRECT_URI = "NETATMO_REDIRECT_URI"

# Default settings
DEFAULT_POLL_INTERVAL = 300  # 5 minutes in seconds
DEFAULT_MAX_ERRORS = 5
DEFAULT_REDIRECT_URI = "http://localhost"

# OpenTelemetry defaults
DEFAULT_OTEL_ENABLED = True
DEFAULT_OTEL_EXPORT_INTERVAL_MS = 10000  # 10 seconds
DEFAULT_OTEL_SERVICE_NAME = "netatmo-monitor"
DEFAULT_OTEL_NAMESPACE = "netatmo"
DEFAULT_OTEL_COLLECTOR_ENDPOINT = (
    "localhost:4317"  # gRPC endpoint for Docker
)

# Load environment variables
load_dotenv(DEFAULT_ENV_FILE)


class ConfigManager:
    def __init__(self, config_file=DEFAULT_CONFIG_FILE):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Load configuration from INI file, create default if not exists"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            # Create default configuration
            self.config["General"] = {
                "poll_interval_seconds": str(DEFAULT_POLL_INTERVAL),
                "max_errors": str(DEFAULT_MAX_ERRORS),
            }
            self.config["OpenTelemetry"] = {
                "enabled": str(DEFAULT_OTEL_ENABLED).lower(),
                "service_name": DEFAULT_OTEL_SERVICE_NAME,
                "namespace": DEFAULT_OTEL_NAMESPACE,
                "collector_endpoint": DEFAULT_OTEL_COLLECTOR_ENDPOINT,
            }

            # Write default config
            with open(self.config_file, "w") as configfile:
                self.config.write(configfile)

            print(f"Created default configuration file: {self.config_file}")

    def get(self, section, option, fallback=None):
        """Get a configuration value"""
        return self.config.get(section, option, fallback=fallback)

    def getboolean(self, section, option, fallback=None):
        """Get a boolean configuration value"""
        return self.config.getboolean(section, option, fallback=fallback)

    def getint(self, section, option, fallback=None):
        """Get an integer configuration value"""
        return self.config.getint(section, option, fallback=fallback)
