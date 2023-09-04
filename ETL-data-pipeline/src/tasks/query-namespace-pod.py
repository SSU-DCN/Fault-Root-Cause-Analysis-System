import requests
import json
import time, datetime
import sys
import csv
import os
from minio import Minio

def warehouse_connection():
    client = Minio("192.168.24.20:30256",
                    access_key="XwMptXNrhYWMHj99",
                    secret_key="Uatsl7MkYaJVrABZAXRTXfQzbzJ9IwlW",
                    secure=False,
    )
    
    return client

def cluster_instance_pod_query(URL, cluster_name, namespace):
    """
    query metrics for each compute host by each host
    compute_host_cluster_URL: http://192.168.40.232:31270/api/v1/query
    """
    headers = {'X-Scope-OrgID': cluster_name}
    name =  namespace
    cluster_namespace_pod_metrics = {
            'cluster_ns_pod_status_scheduled': 'sum(kube_pod_status_scheduled{namespace=~"' + name + '", container="kube-state-metrics", condition="true"}) by (pod)',
            'cluster_ns_pod_status_unscheduled': 'sum(kube_pod_status_scheduled{namespace=~"' + name + '", container="kube-state-metrics", condition="false",}) by (pod)', #1 is oke and 0 is not scheduled
            'cluster_ns_pod_status_unknown': 'sum(kube_pod_status_scheduled{namespace=~"' + name + '", container="kube-state-metrics", condition="unknown",}) by (pod)',
            'cluster_ns_pod_status_ready_true': 'sum(kube_pod_status_ready{namespace=~"' + name + '", container="kube-state-metrics", condition="true",}) by (pod)', #1 is oke and 0 is not scheduled
            'cluster_ns_pod_status_ready_false': 'sum(kube_pod_status_ready{namespace=~"' + name + '", container="kube-state-metrics", condition="false"}) by (pod)', 
            'cluster_ns_pod_status_phase_pending': 'sum(kube_pod_status_phase{namespace=~"' + name + '", job=~"kube-state-metrics", pod=~".+", phase=~"Pending"}) by (pod)',
            'cluster_ns_pod_status_phase_failed': 'sum(kube_pod_status_phase{namespace=~"' + name + '", job=~"kube-state-metrics", pod=~".+", phase=~"Failed"}) by (pod)',
            'cluster_ns_pod_status_phase_running': 'sum(kube_pod_status_phase{namespace=~"' + name + '", job=~"kube-state-metrics", pod=~".+", phase=~"Running"}) by (pod)',
            'cluster_ns_pod_status_phase_succeeded': 'sum(kube_pod_status_phase{namespace=~"' + name + '", job=~"kube-state-metrics", pod=~".+", phase=~"Succeeded"}) by (pod)',
            'cluster_ns_pod_status_phase_unknown': 'sum(kube_pod_status_phase{namespace=~"' + name + '", job=~"kube-state-metrics", pod=~".+", phase=~"Unknown"}) by (pod)',
            'cluster_ns_pod_status_reason_evicted': 'sum(kube_pod_status_reason{namespace=~"' + name + '", job=~"kube-state-metrics", reason="Evicted"}) by (pod)',
            'cluster_ns_pod_status_reason_nodeaffinity': 'sum(kube_pod_status_reason{namespace=~"' + name + '", job=~"kube-state-metrics", reason="NodeAffinity"}) by (pod)',
            'cluster_ns_pod_status_reason_nodelost': 'sum(kube_pod_status_reason{namespace=~"' + name + '", job=~"kube-state-metrics", reason="NodeLost"}) by (pod)',
            'cluster_ns_pod_status_reason_shutdown': 'sum(kube_pod_status_reason{namespace=~"' + name + '", job=~"kube-state-metrics", reason="Shutdown"}) by (pod)',
            'cluster_ns_pod_status_reason_unexpectedadmissionerror': 'sum(kube_pod_status_reason{namespace=~"' + name + '", job=~"kube-state-metrics", reason="UnexpectedAdmissionError"}) by (pod)'
            }
    
    rows = []
    r0 = requests.get(url = URL, headers = headers, params = {'query': cluster_namespace_pod_metrics['cluster_ns_pod_status_scheduled']})
    r0_json = r0.json()['data']['result']
    # print(r0_json)
    for result in r0_json:
        l = []
        l.append(result['metric'].get('pod', ''))
        rows.append(l)

    for metric_name, metric_value in cluster_namespace_pod_metrics.items():
        r1 = requests.get(url = URL, headers = headers, params = {'query': metric_value})
        r1_json = r1.json()['data']['result']
        row = 0
        for result in r1_json:
                l = []
                l.append(result['value'][1])
                rows[row].append(l[0])
                # rows.append(l[0])
                ts = []
                ts.append(time.time())
                rows[row].append(ts[0])
                row = row + 1     
    return rows


URL = "http://192.168.24.20:31179/prometheus/api/v1/query"
metrics_name = ['pod', 'cluster_ns_pod_status_scheduled', 'cluster_ns_pod_status_unscheduled', 'cluster_ns_pod_status_unknown', 'cluster_ns_pod_status_ready_true', 'cluster_ns_pod_status_ready_false', 'cluster_ns_pod_status_phase_pending', 'cluster_ns_pod_status_phase_failed' \
                , 'cluster_ns_pod_status_phase_running', 'cluster_ns_pod_status_phase_succeeded', 'cluster_ns_pod_status_phase_unknown', 'cluster_ns_pod_status_reason_evicted', 'cluster_ns_pod_status_reason_nodeaffinity', 'cluster_ns_pod_status_reason_nodelost', 'cluster_ns_pod_status_reason_shutdown', 'cluster_ns_pod_status_reason_unexpectedadmissionerror', 'timestamp' ]


cluster_name = "central-cluster"
name_space = "kube-system"

file_name = cluster_name + '_' + name_space + '_pod' + '_data.csv'

with open(file_name, 'w') as f:
         write = csv.writer(f)
         write.writerow(metrics_name)

         for seq in range (0, 2):
            data = cluster_instance_pod_query(URL, cluster_name, name_space)
            # print(data)
            write.writerows(data)
            sys.stdout.flush()
            time.sleep(15)
        
minioClient = warehouse_connection()

date = datetime.datetime.now()

path = "cluster-namespace-pod/" + str(date.strftime("%Y")) + date.strftime("%m") + date.strftime("%d")
minioClient.fput_object(cluster_name, path, file_name, content_type='application/csv')
os.remove(file_name)

         
