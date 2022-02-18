from interfaces import mongodb_requests
from interfaces import root_service_manager_requests
import copy


def service_resolution(service_name):
    """
    Resolves the service instance list by service name with the local DB,
    if no result found the query is propagated to the System Manager

    returns:
        instance_list: [{
                        instance_number: int
                        instance_ip: string
                        namespace_ip: string
                        host_ip: string
                        host_port: string
                        }]
        service_ip_list: [{
                            IpType: string
                            Address: string
                        }]
    """
    # resolve it locally
    job = mongodb_requests.mongo_find_job_by_name(service_name)
    instances = None
    siplist = None

    # if no results, ask the root orc
    if job is None:
        job = root_service_manager_requests.cloud_table_query_service_name(service_name)
        instances = job['instance_list']
        siplist = job['service_ip_list']
        mongodb_requests.mongo_insert_job(copy.deepcopy(job))
    else:
        instances = job['instance_list']
        siplist = job['service_ip_list']

    return instances, siplist


def service_resolution_ip(ip_string):
    """
    Resolves the service instance list by service ServiceIP with the local DB,
    if no result found the query is propagated to the System Manager

    returns:
        name: string #service name
        instance_list: [{
                        instance_number: int
                        namespace_ip: string
                        host_ip: string
                        host_port: string
                    }]
        service_ip_list: [{
                                IpType: string
                                Address: string
                    }]

    """
    # resolve it locally
    job = mongodb_requests.mongo_find_job_by_ip(ip_string)

    # if no results, ask the root orc
    if job is None:
        job = root_service_manager_requests.cloud_table_query_ip(ip_string)
        mongodb_requests.mongo_insert_job(copy.deepcopy(job))

    return job.get("job_name"), job.get('instance_list'), job.get('service_ip_list')


def format_instance_response(instance_list, sip_list):
    service_ip_list = sip_list
    for elem in instance_list:
        elem['service_ip'] = service_ip_list
        elem['service_ip'].append({
            "IpType": "instance_ip",
            "Address": elem['instance_ip']
        })
    return instance_list
