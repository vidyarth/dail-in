# DOCUMENTATION

## SETUP
### Download and setup

- Download and install prometheus : https://prometheus.io/download/

- Download and install Grafana : https://grafana.com/grafana/download

- Download and install Loki : https://github.com/grafana/loki/releases/tag/v2.8.1

- Download the loki YAML file : https://raw.githubusercontent.com/grafana/loki/main/cmd/loki/loki-local-config.yaml

### configure prometheus
- Open the terminal or command prompt.
- Navigate to the directory where Prometheus is installed. This is typically the directory where the prometheus.exe file is located.
- Locate the `prometheus.yml` file. It is the main configuration file for Prometheus.
- append the following to the yml file
	```
 	- job_name: "telemetry"
	  static_configs:
	    - targets: ["localhost:9092"]
 	```

### running the code
- Run the Telemetry code in the system
	- If it gives error it will be due to the reason that TLS will not be enabled in the gRPC port of the router. Kindly make sure that TLS in enabled in the router.
	

### check if prometheus is set up correctly

	- go to localhost:9090 and check if prometheus is runnning
	- go to localhost:9090/targets and check if our telemetry metrics on port 9092 is up
	
	
### Grafana setup
	- Open localhost:3000 and go to datasources
	- Click prometheus and set the URL as http://localhost:9090
	- Create a Dashboard for the required visualisation

### Loki Setup
	- run the following command to start loki `.\loki-windows-amd64.exe --config.file=loki-local-config.yaml`
	- check in localhost:3100 if the loki server is running properly
	
## Visualise logs in loki
	- Open localhost:3000 and go to datasources
	- Click loki and set the URL as http://localhost:3100
	- go to explore section in grafana
	- configure the datasource as loki and start querying the logs.






## Telemetry Client for Cisco Device Metrics Collection

The code implements a telemetry client for collecting and monitoring metrics from a Cisco device using the gNMI (gRPC Network Management Interface) protocol. The collected metrics are then exposed as Prometheus metrics for further monitoring and analysis.

### Classes

#### 1. Metric

This class represents a metric that will be collected from the Cisco device and exposed as a Prometheus metric. It has the following attributes:

- `metric_name`: The name of the metric extracted from the XPath.
- `metric_xpath`: The XPath expression used to collect the metric from the device.
- `metric_time_period`: The time period (in seconds) at which the metric should be collected.
- `metric_prometheus_job_name`: The name of the Prometheus job associated with the metric.
- `metric_prometheus_job_description`: The description of the Prometheus job associated with the metric.
- `prometheus_metric`: The Prometheus Gauge metric object associated with the metric.

#### 2. Telemetry

This class represents the telemetry client for connecting to the Cisco device and collecting metrics. It has the following methods:

- `__init__(self, target, os, username, password)`: Initializes the telemetry client by setting up the gNMI client connection with the target Cisco device. It takes the following parameters:
  - `target`: The target address of the Cisco device in the format `hostname:port`.
  - `os`: The operating system of the Cisco device.
  - `username`: The username for authentication.
  - `password`: The password for authentication.

- `print_context(self, reply)`: A helper method to print the context of the CLI reply with the timestamp.

- `get_cli(self, command)`: Sends a CLI command to the Cisco device and prints the response.

- `create_subscription_list(self)`: Creates and returns an empty `SubscriptionList` object.

- `add_subscription_periodic(self, metric)`: Adds a periodic subscription for the given metric. It sets up the gNMI subscription and listens for updates periodically. The collected metric values are stored in the associated Prometheus metric object. It takes the following parameter:
  - `metric`: The `Metric` object to be subscribed and collected.

- `add_subscription_onchange(self, metric)`: Does the same thing as `add_subscription_periodic(self, metric)` but adds a onchange subscription.

- `collect_metrics(self)`: [Not used in the provided code]

### Usage

The provided code demonstrates the usage of the telemetry client. It sets up a Prometheus metrics server on port 9092 using `start_http_server(9092)`.

It defines a list of metrics (`metrics_desired`) that need to be collected from the Cisco device. Each metric is represented by a `Metric` object with relevant details.

A `Telemetry` object is created by providing the target Cisco device address, operating system, username, and password. The telemetry client is then connected to the device.

For each metric in the `metrics_desired` list, a separate thread is created to subscribe and collect the metric periodically using `telemetry_client.add_subscription_periodic(metric)`.

Finally, all the threads are started, and the telemetry client starts collecting metrics from the Cisco device in parallel.
