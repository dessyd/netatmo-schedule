import os
import sys
from .config import (
    ConfigManager,
    ENV_CLIENT_ID,
    ENV_CLIENT_SECRET,
    ENV_REFRESH_TOKEN,
    DEFAULT_REDIRECT_URI,
)
from .models import Credentials
from .api import NetatmoAPI
from .telemetry import TelemetryManager


def display_readings(readings):
    """Display readings in the console"""
    if not readings:
        print("No weather readings available.")
        return

    print(f"\nNetatmo Weather Report - {readings[0].timestamp}\n")

    current_station = None
    for reading in readings:
        if current_station != reading.station_name:
            current_station = reading.station_name
            print(f"Station: {current_station}")

        print(f"  Module: {reading.module_name} ({reading.module_type})")
        print(f"  Last updated: {reading.last_updated}")

        for metric_name, value in reading.metrics.items():
            if metric_name == "temperature":
                print(f"    Temperature: {value} Cel")
            elif metric_name == "humidity":
                print(f"    Humidity: {value} %")
            elif metric_name == "pressure":
                print(f"    Pressure: {value} hPa")
            elif metric_name == "co2":
                print(f"    CO2: {value} ppm")
            elif metric_name == "noise":
                print(f"    Noise: {value} dB")

        print("")  # Add a blank line


def get_and_send_weather_data(api, telemetry):
    """Get weather data from Netatmo API and send to OpenTelemetry"""
    try:
        # Get access token
        access_token = api.refresh_access_token()
        if not access_token:
            return False

        # Get station data
        station_data = api.get_station_data(access_token)
        if not station_data:
            return False

        # Parse weather readings
        readings = api.parse_weather_readings(station_data)

        # Display readings
        display_readings(readings)

        # Send metrics to OpenTelemetry
        if readings:
            for reading in readings:
                telemetry.record_metrics(reading)

        return True

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    """Main function to get and send weather data once"""

    # Load configuration
    config_manager = ConfigManager()
    print(f"Configuration loaded from: {config_manager.config_file}")

    # Setup credentials from environment variables
    credentials = Credentials(
        client_id=os.getenv(ENV_CLIENT_ID),
        client_secret=os.getenv(ENV_CLIENT_SECRET),
        refresh_token=os.getenv(ENV_REFRESH_TOKEN),
        redirect_uri=os.getenv("NETATMO_REDIRECT_URI", DEFAULT_REDIRECT_URI),
    )

    # Check if credentials are valid
    if not credentials.validate():
        print(
            "Error: Missing client ID or client secret "
            "in environment variables"
        )
        return False

    # Setup API
    api = NetatmoAPI(credentials)

    # Check if refresh token exists, if not, initiate auth flow
    if not credentials.has_refresh_token():
        print("No refresh token found. Setting up initial authorization...")
        if not api.setup_initial_auth():
            print("Failed to set up initial authorization. Exiting.")
            return False

    # Setup telemetry
    telemetry = TelemetryManager(config_manager)

    # Get and send weather data just once
    success = get_and_send_weather_data(api, telemetry)
    return success


if __name__ == "__main__":
    # Execute one weather data collection cycle
    result = main()
    sys.exit(0 if result else 1)
