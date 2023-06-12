from ncclient import manager
from lxml.etree import fromstring
import xmltodict
import datetime
import requests
from prometheus_client import start_http_server, Gauge
import json
import time

class Metric:
    def __init__(self,name,xpath,prometheus_job_name,prometheus_job_description):
        self.metric_name = name
        self.metric_xpath = xpath
        self.metric_prometheus_job_name = prometheus_job_name
        self.metric_prometheus_job_description = prometheus_job_description
        self.prometheus_metric = Gauge(self.metric_prometheus_job_name, self.metric_prometheus_job_description)
    
    def getMetrics(self,msg_json):
        if self.metric_name == "cpu-util":
            return msg_json["notification"]["push-update"]["datastore-contents-xml"]["cpu-usage"]["cpu-utilization"]["five-seconds"]
        if self.metric_name == "memory-stats":
            return msg_json["notification"]["push-update"]["datastore-contents-xml"]["memory-statistics"]["memory-statistic"][0]["used-memory"]
        if self.metric_name == "gigabit1":
            return msg_json["notification"]["push-update"]["datastore-contents-xml"]["interfaces"]["interface"]["statistics"]["in-unicast-pkts"]
        

def telemetry_subscribe(conn, xpath, period=100):
    xmlns = "urn:ietf:params:xml:ns:yang:ietf-event-notifications"
    xmlns_yp = "urn:ietf:params:xml:ns:yang:ietf-yang-push"

    subscribe_rpc = f"""
        <establish-subscription xmlns="{xmlns}" xmlns:yp="{xmlns_yp}">
            <stream>yp:yang-push</stream>
            <yp:xpath-filter>{xpath}</yp:xpath-filter>
            <yp:period>{period}</yp:period>
        </establish-subscription>
    """
    subscribe_response = conn.dispatch(fromstring(subscribe_rpc))
    return subscribe_response


def str_to_int(path, key, value):
    try:
        return (key, int(value))
    except (ValueError, TypeError):
        return (key, value)


def solve():
    netconf_params = {
        "host": "sandbox-iosxe-latest-1.cisco.com",
        "port": 830,
        "username": "admin",
        "password": "C1sco12345",
        "hostkey_verify": False,
        "allow_agent": False,
        "look_for_keys": False,
        "device_params": {"name": "csr"},
    }

    with manager.connect(**netconf_params) as conn:
        metrics_desired = [
            Metric("cpu-util","/process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/five-seconds","cpu_util_cisco_xe","CPU data connected from cisco telemetry"),
            Metric("memory-stats","/memory-ios-xe-oper:memory-statistics/memory-statistic","memory_util_cisco_xe","Memory stats data connected from cisco telemetry"),
            Metric("gigabit1","/interfaces-ios-xe-oper:interfaces/interface[name=\"GigabitEthernet1\"]","gigabit_util_cisco_xe","interface stats data connected from cisco telemetry"),
        ]

        sub_ids = {}
        for metrics in metrics_desired:
            sub_resp = telemetry_subscribe(conn, metrics.metric_xpath)
            sub_json = xmltodict.parse(sub_resp.xml)
            sub_result = sub_json["rpc-reply"]["subscription-result"]["#text"]

            if "ok" in sub_result.lower():
                sub_id = sub_json["rpc-reply"]["subscription-id"]["#text"]
                print(f"Subscribed to {metrics.metric_name} via ID : {sub_id}")
                sub_ids[int(sub_id)] = metrics
            else:
                print(f"{metrics.metric_name} : Not subscribed")
        print(sub_ids)
        i = 0
        start_http_server(9092)
        while i < 50000:
            msg_xml = conn.take_notification()
            msg_json = xmltodict.parse(
                msg_xml.notification_xml, postprocessor=str_to_int
            )
            recieved_sub_id = msg_json["notification"]["push-update"]["subscription-id"]
            recieved_metric = sub_ids[recieved_sub_id]
            recieved_metric.prometheus_metric.set(recieved_metric.getMetrics(msg_json))
            i += 1


if __name__ == "__main__":
    solve()
