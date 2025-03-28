from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from .config import (
    DEFAULT_OTEL_ENABLED,
    DEFAULT_OTEL_EXPORT_INTERVAL_MS,
    DEFAULT_OTEL_SERVICE_NAME,
    DEFAULT_OTEL_NAMESPACE,
    DEFAULT_OTEL_COLLECTOR_ENDPOINT,
    STATE_FILE,
)
from .utils import load_state, save_state


class TelemetryManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.enabled = self.config_manager.getboolean(
            "OpenTelemetry", "enabled", fallback=DEFAULT_OTEL_ENABLED
        )
        self.meter = None
        self.gauges = {}
        self.previous_values = {}

        # Define unit mappings
        self.metric_names = {
            "temperature": "netatmo.temperature",
            "humidity": "netatmo.humidity",
            "pressure": "netatmo.pressure",
            "co2": "netatmo.co2",
            "noise": "netatmo.noise",
        }

        # Define units
        self.metric_units = {
            "temperature": "Cel",  # Celsius (UCUM)
            "humidity": "%",  # Percent
            "pressure": "hPa",  # Hectopascal
            "co2": "ppm",  # Parts per million
            "noise": "dB",  # Decibels
        }

        # Define descriptions
        self.metric_descriptions = {
            "temperature": "Temperature in Celsius",
            "humidity": "Relative humidity percentage",
            "pressure": "Atmospheric pressure in hectopascals",
            "co2": "CO2 concentration in parts per million",
            "noise": "Noise level in decibels",
        }

        # Load previous states if available
        self.load_state()

        if self.enabled:
            self.setup_telemetry()

    def setup_telemetry(self):
        """Set up OpenTelemetry with OTLP gRPC exporter
            pointing to the collector"""
        try:
            # Get OpenTelemetry configuration
            collector_endpoint = self.config_manager.get(
                "OpenTelemetry",
                "collector_endpoint",
                fallback=DEFAULT_OTEL_COLLECTOR_ENDPOINT,
            )
            service_name = self.config_manager.get(
                "OpenTelemetry",
                "service_name",
                fallback=DEFAULT_OTEL_SERVICE_NAME,
            )
            namespace = self.config_manager.get(
                "OpenTelemetry", "namespace", fallback=DEFAULT_OTEL_NAMESPACE
            )

            # Set up OTLP gRPC exporter to send to collector
            # Note that the OTLPMetricExporter uses gRPC by default
            exporter = OTLPMetricExporter(
                endpoint=collector_endpoint,
                insecure=True,  # For development; set to False
                                # and use credentials in production
            )

            reader = PeriodicExportingMetricReader(
                exporter,
                export_interval_millis=DEFAULT_OTEL_EXPORT_INTERVAL_MS,
            )

            # Set up resource with service information
            resource = Resource.create(
                {"service.name": service_name, "service.namespace": namespace}
            )

            # Create meter provider
            provider = MeterProvider(
                metric_readers=[reader], resource=resource
            )
            metrics.set_meter_provider(provider)

            # Create meter
            self.meter = metrics.get_meter(namespace)

            # Initialize gauges for each metric type with "netatmo." prefix
            for metric_key, metric_name in self.metric_names.items():
                self.gauges[metric_key] = self.meter.create_gauge(
                    name=metric_name,  # Full metric name
                    description=self.metric_descriptions.get(
                        metric_key, f"{metric_key} measurement"
                    ),
                    unit=self.metric_units.get(metric_key, ""),
                )

            print(
                f"OpenTelemetry configured to send metrics via gRPC "
                f"to collector at: {collector_endpoint}"
            )
            return True
        except Exception as e:
            print(f"Error setting up OpenTelemetry: {e}")
            self.enabled = False
            return False

    def record_metrics(self, reading):
        """Record metrics from a weather reading using gauges"""
        if not self.enabled or not self.meter:
            return

        try:
            # Get sensor key
            sensor_key = reading.get_sensor_key()

            # Get common attributes
            common_attributes = reading.get_attributes()

            # Process each available metric
            for metric_key, value in reading.metrics.items():
                if metric_key in self.gauges:
                    # Create attributes with current value
                    attributes = common_attributes.copy()

                    # Set the gauge to the absolute value
                    gauge = self.gauges[metric_key]
                    gauge.set(value, attributes)

                    # Get prefixed name for logging
                    prefixed_name = self.metric_names[metric_key]

                    print(
                        f"Recorded {prefixed_name} "
                        f"value: {value} {self.metric_units[metric_key]} "
                        f"for {sensor_key}"
                    )

                    # For reporting purposes
                    state_key = f"{sensor_key}:{metric_key}"
                    previous_value = self.previous_values.get(state_key)
                    if previous_value is not None:
                        delta = value - previous_value
                        print(
                            f"  Change since last reading: {delta:+.2f} "
                            f"{self.metric_units[metric_key]}"
                        )

                    self.previous_values[state_key] = value

            # Save state for reporting purposes
            self.save_state()

        except Exception as e:
            print(f"Error recording telemetry: {e}")

    def load_state(self):
        """Load previous metric values from state file"""
        self.previous_values = load_state(STATE_FILE)
        if self.previous_values:
            print(
                f"Loaded previous states for {len(self.previous_values)} "
                "metrics"
            )
        else:
            print("No previous state found, this appears to be the first run")
            self.previous_values = {}

    def save_state(self):
        """Save current metric values to state file"""
        save_state(STATE_FILE, self.previous_values)
