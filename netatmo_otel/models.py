class Credentials:
    def __init__(
        self, client_id, client_secret, refresh_token=None, redirect_uri=None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.redirect_uri = redirect_uri

    def validate(self):
        """Check if required credentials are available"""
        return all([self.client_id, self.client_secret])

    def has_refresh_token(self):
        """Check if refresh token is available"""
        return bool(self.refresh_token)


class WeatherReading:
    def __init__(
        self,
        timestamp,
        station_name,
        module_name,
        module_type,
        metrics,
        last_updated,
    ):
        self.timestamp = timestamp
        self.station_name = station_name
        self.module_name = module_name
        self.module_type = module_type
        self.metrics = metrics  # Dictionary with temperature, humidity, etc.
        self.last_updated = last_updated

    def get_sensor_key(self):
        """Create a unique key for this sensor"""
        return f"{self.station_name}:{self.module_name}:{self.module_type}"

    def get_attributes(self):
        """Get common attributes for all metrics for this sensor"""
        return {
            "station_name": self.station_name,
            "module_name": self.module_name,
            "module_type": self.module_type,
        }
