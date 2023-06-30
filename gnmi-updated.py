from cisco_gnmi import ClientBuilder,proto
from prometheus_client import start_http_server, Gauge


class Metric:
    def __init__(self,xpath,prometheus_job_name,prometheus_job_description):
        self.metric_name = xpath.split("/")[0].split(":")[-1]
        self.metric_xpath = xpath
        self.metric_prometheus_job_name = prometheus_job_name
        self.metric_prometheus_job_description = prometheus_job_description
        self.prometheus_metric = Gauge(
            self.metric_prometheus_job_name, 
            self.metric_prometheus_job_description,
            ["Metric_name"]
        )

class Telemetry:
    def __init__(self,target,os,username,password):
        try:
            self.builder = ClientBuilder(target)
            self.builder.set_os(os)
            self.builder.set_secure_from_target()
            self.builder.set_ssl_target_override()
            self.builder.set_call_authentication(username,password)
            self.client = self.builder.construct()
            self.client_capabilities = self.client.capabilities()
            self.metric_name_object_map = {}
            print(f"Connected to {target} successfully!")
        except:
            print("Error Occured !")

    def print_context(self,reply):
        print("timestamp : ", reply.notification[0].timestamp)
        print("path : ",reply.notification[0].update[0].path.elem[0].name)

    def get_cli(self,command):
        get_reply = self.client.get_cli(command)
        self.print_context(get_reply)
        print(get_reply.notification[0].update[0].val.ascii_val)

    def create_subscription_list(self):
        self.subscription_list = proto.gnmi_pb2.SubscriptionList()
        self.subscription_list.mode = proto.gnmi_pb2.SubscriptionList.Mode.Value("STREAM")
        self.subscription_list.encoding = proto.gnmi_pb2.Encoding.Value("PROTO")

    def add_subscription_periodic(self,metric,time=1):
        self.metric_name_object_map[metric.metric_name] = metric
        sampled_subscription = proto.gnmi_pb2.Subscription()
        sampled_subscription.path.CopyFrom(
            self.client.parse_xpath_to_gnmi_path(metric.metric_xpath)
        )
        sampled_subscription.mode = proto.gnmi_pb2.SubscriptionMode.Value("SAMPLE")
        sampled_subscription.sample_interval = time * 10 * int(1e9)
        self.subscription_list.subscription.extend([sampled_subscription])

    def add_subscription_onchange(self,metric):
        self.metric_name_object_map[metric.metric_name] = metric
        onchange_subscription = proto.gnmi_pb2.Subscription()
        onchange_subscription.path.CopyFrom(
            client.parse_xpath_to_gnmi_path(
                client.parse_xpath_to_gnmi_path(metric.metric_xpath)
            )
        )
        onchange_subscription.mode = proto.gnmi_pb2.SubscriptionMode.Value("ON_CHANGE")
        self.subscription_list.subscription.extend([onchange_subscription])

    def collect_metrics(self):
        for subscribe_response in self.client.subscribe([self.subscription_list]):
            try:
                metric_recieved_name = subscribe_response.update.prefix.elem[0].name
                metric_recieved_object = self.metric_name_object_map[metric_recieved_name]
                for update in subscribe_response.update.update:
                    for path_elem in update.path.elem:
                        element_name = path_elem.name
                        unit_val = update.val.uint_val
                        metric_recieved_object.prometheus_metric.labels(Metric_name = element_name).set(unit_val)
                        print("Element Name:", element_name)
                        print("Unit Value:", unit_val)
            except:
                pass

metrics_desired = [
            #Metric("Cisco-IOS-XR-shellutil-oper:system-time/uptime/uptime","Cisco_XR_uptime","uptime data connected from cisco telemetry"),
            Metric("Cisco-IOS-XR-nto-misc-oper:memory-summary","Cisco_XR_Memory_summary2","Physical Memory stats data connected from cisco telemetry"),
]
telemetry_client = Telemetry("sandbox-iosxr-1.cisco.com:57777","IOS XR","admin","C1sco12345")
telemetry_client.create_subscription_list()
for metric in metrics_desired:
    telemetry_client.add_subscription_periodic(metric,5)
telemetry_client.collect_metrics()
