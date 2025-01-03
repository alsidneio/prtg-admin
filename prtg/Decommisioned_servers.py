import local_base
import csv



def Get_hostnames_from_csv(filename:str):
    with open(filename,encoding='utf-8-sig') as csv_file:
        hir_servers = csv.DictReader(csv_file)
        return [server["Hostname"] for server in hir_servers]

def Get_Decommissioned_Servers_in_PRTG(filename:str):
    PRTG_hosts = set(local_base.Get_All_PRTG_Hostnames())
    HIR_hosts = set(Get_hostnames_from_csv(filename))
    print(PRTG_hosts.intersection(HIR_hosts))


def Get_Decommissioned_Servers_in_Splunk(splunkCsv:str, *args):
    splunk_hosts = set(local_base.Get_Core_Hostnames(splunkCsv))
    HIR_hosts ={}
    for file in args: 
       HIR_hosts = {*HIR_hosts, *Get_hostnames_from_csv(file)}
    for host in splunk_hosts.intersection(HIR_hosts):
        print(host)
