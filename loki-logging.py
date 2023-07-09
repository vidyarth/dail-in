from cisco_gnmi import ClientBuilder,proto
import threading
import logging
import logging
import logging_loki

logging_loki.emitter.LokiEmitter.level_tag = "level"

class Metric:
    def __init__(self,xpath,prometheus_job_name,prometheus_job_description,time_period):
        self.metric_name = xpath.split("/")[0].split(":")[-1]
        self.metric_xpath = xpath
        self.metric_time_period = time_period
        self.metric_prometheus_job_name = prometheus_job_name
        self.metric_prometheus_job_description = prometheus_job_description
        handler = logging_loki.LokiHandler(
          url="http://localhost:3100/loki/api/v1/push",   version="1",
        )
        self.logger = logging.getLogger("my-logger")
        self.logger.addHandler(handler)

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
        subscription_list = proto.gnmi_pb2.SubscriptionList()
        subscription_list.mode = proto.gnmi_pb2.SubscriptionList.Mode.Value("STREAM")
        subscription_list.encoding = proto.gnmi_pb2.Encoding.Value("PROTO")
        return  subscription_list

    def add_subscription_periodic(self,metric):
        subscription_list = self.create_subscription_list()
        #self.metric_name_object_map[metric.metric_name] = metric
        sampled_subscription = proto.gnmi_pb2.Subscription()
        sampled_subscription.path.CopyFrom(
            self.client.parse_xpath_to_gnmi_path(metric.metric_xpath)
        )
        sampled_subscription.mode = proto.gnmi_pb2.SubscriptionMode.Value("SAMPLE")
        sampled_subscription.sample_interval = metric.metric_time_period  * int(1e9)
        subscription_list.subscription.extend([sampled_subscription])
        i = 0
        for subscribe_response in self.client.subscribe([subscription_list]):
            print(i)
            i += 1
            try:
                metric_recieved_name = subscribe_response.update.prefix.elem[0].name
                print(metric_recieved_name)
                log_tags = {}
                log_text = ""
                log_severity = ""
                for update in subscribe_response.update.update:
                    for path_elem in update.path.elem:
                        element_name = path_elem.name
                        unit_val = update.val.uint_val
                        str_val = update.val.string_val
                        if element_name == "text":
                            log_text = str_val
                        elif element_name == "severity":
                            log_severity = str_val
                        elif str_val == "":
                            log_tags[element_name] = unit_val
                            print("Unit Value:", unit_val)
                        else:
                            log_tags[element_name] = str_val
                            print("Stri Value:", str_val)
                if "info" in log_severity:
                    metric.logger.info(
                      log_text,
                      extra={"tags": log_tags},
                    )
                elif "warning" in log_severity:
                    metric.logger.warning(
                      log_text,
                      extra={"tags": log_tags},
                    )
                elif "error" in log_severity:
                    metric.logger.error(
                      log_text,
                      extra={"tags": log_tags},
                    )
                                          
            except:
                print(subscribe_response)


    def add_subscription_onchange(self,metric):
        self.metric_name_object_map[metric.metric_name] = metric
        onchange_subscription = proto.gnmi_pb2.Subscription()
        onchange_subscription.path.CopyFrom(
            self.client.parse_xpath_to_gnmi_path(
                self.client.parse_xpath_to_gnmi_path(metric.metric_xpath)
            )
        )
        onchange_subscription.mode = proto.gnmi_pb2.SubscriptionMode.Value("ON_CHANGE")
        self.subscription_list.subscription.extend([onchange_subscription])

metrics_desired = [
            Metric("Cisco-IOS-XR-infra-syslog-oper:syslog/messages/message","Cisco_XR_syslog","Syslog messages",2),
]
telemetry_client = Telemetry("sandbox-iosxr-1.cisco.com:57777","IOS XR","admin","C1sco12345")
threads = []
for metric in metrics_desired:
    telemetry_client.add_subscription_periodic(metric)
