import requests
import webbrowser
from datetime import datetime
from .models import WeatherReading
from .config import (
    NETATMO_AUTH_URL,
    NETATMO_AUTH_AUTHORIZE_URL,
    NETATMO_STATION_DATA_URL,
    ENV_REFRESH_TOKEN,
)
from .utils import update_env_file


class NetatmoAPI:
    def __init__(self, credentials):
        self.credentials = credentials

    def refresh_access_token(self):
        """Get a new access token using the refresh token"""
        try:
            token_data = {
                "grant_type": "refresh_token",
                "refresh_token": self.credentials.refresh_token,
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
            }

            response = requests.post(NETATMO_AUTH_URL, data=token_data)
            response.raise_for_status()

            tokens = response.json()
            access_token = tokens["access_token"]
            new_refresh_token = tokens["refresh_token"]

            # Update refresh token
            self.credentials.refresh_token = new_refresh_token
            update_env_file(ENV_REFRESH_TOKEN, new_refresh_token)

            return access_token
        except Exception as e:
            print(f"Error refreshing access token: {e}")
            return None

    def get_station_data(self, access_token):
        """Get data from all weather stations"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(NETATMO_STATION_DATA_URL, headers=headers)
            response.raise_for_status()

            return response.json()["body"]
        except Exception as e:
            print(f"Error retrieving station data: {e}")
            return None

    def setup_initial_auth(self):
        """Set up initial authorization to get the first refresh token"""
        if not self.credentials.validate():
            print("Error: Missing client_id or client_secret in environment")
            return False

        # Step 1: Redirect user to authorization page
        auth_params = {
            "client_id": self.credentials.client_id,
            "redirect_uri": self.credentials.redirect_uri,
            "scope": "read_station",
            "state": "state",  # Replace with a random state for security
            "response_type": "code",
        }

        auth_request_url = f"{NETATMO_AUTH_AUTHORIZE_URL}?" + "&".join(
            [f"{key}={value}" for key, value in auth_params.items()]
        )

        print(
            "Opening browser for authorization. "
            "Please authorize the app and copy the authorization code."
        )
        print(
            f"If the browser doesn't open, go to this URL: {auth_request_url}"
        )

        webbrowser.open(auth_request_url)

        # Step 2: Get authorization code from user
        auth_code = input(
            "Enter the authorization code from the redirect URL: "
        )

        # Step 3: Exchange authorization code for access and refresh tokens
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "code": auth_code,
            "redirect_uri": self.credentials.redirect_uri,
        }

        try:
            response = requests.post(NETATMO_AUTH_URL, data=token_data)
            response.raise_for_status()

            tokens = response.json()
            refresh_token = tokens["refresh_token"]

            # Update refresh token
            self.credentials.refresh_token = refresh_token
            update_env_file(ENV_REFRESH_TOKEN, refresh_token)

            print(
                "Successfully obtained refresh token and updated environment"
            )
            return True
        except Exception as e:
            print(f"Error obtaining tokens: {e}")
            return False

    def parse_weather_readings(self, station_data):
        """Extract weather readings from station data"""
        readings = []
        current_time = datetime.now()
        timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Process each device (station)
        for device in station_data["devices"]:
            station_name = device.get("station_name", "Main Weather Station")

            # Process main module
            if "dashboard_data" in device:
                metrics = {}

                # Extract available metrics
                data = device["dashboard_data"]
                if "Temperature" in data:
                    metrics["temperature"] = data["Temperature"]
                if "Humidity" in data:
                    metrics["humidity"] = data["Humidity"]
                if "Pressure" in data:
                    metrics["pressure"] = data["Pressure"]
                if "CO2" in data:
                    metrics["co2"] = data["CO2"]
                if "Noise" in data:
                    metrics["noise"] = data["Noise"]

                if metrics:
                    last_updated = datetime.fromtimestamp(
                        data["time_utc"]
                    ).strftime("%Y-%m-%d %H:%M:%S")

                    readings.append(
                        WeatherReading(
                            timestamp=timestamp,
                            station_name=station_name,
                            module_name="Main Module",
                            module_type="MAIN",
                            metrics=metrics,
                            last_updated=last_updated,
                        )
                    )

            # Process additional modules
            if "modules" in device:
                for module in device["modules"]:
                    module_name = module.get("module_name", "Unnamed Module")
                    module_type = module.get("type", "Unknown")

                    if "dashboard_data" in module:
                        metrics = {}

                        # Extract available metrics
                        data = module["dashboard_data"]
                        if "Temperature" in data:
                            metrics["temperature"] = data["Temperature"]
                        if "Humidity" in data:
                            metrics["humidity"] = data["Humidity"]
                        if "Pressure" in data:
                            metrics["pressure"] = data["Pressure"]
                        if "CO2" in data:
                            metrics["co2"] = data["CO2"]
                        if "Noise" in data:
                            metrics["noise"] = data["Noise"]

                        if metrics:
                            last_updated = datetime.fromtimestamp(
                                data["time_utc"]
                            ).strftime("%Y-%m-%d %H:%M:%S")

                            readings.append(
                                WeatherReading(
                                    timestamp=timestamp,
                                    station_name=station_name,
                                    module_name=module_name,
                                    module_type=module_type,
                                    metrics=metrics,
                                    last_updated=last_updated,
                                )
                            )

        return readings
