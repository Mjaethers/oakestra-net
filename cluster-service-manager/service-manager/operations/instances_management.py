from threading import Thread

from interfaces import mongodb_requests
from network.tablequery import resolution
from network.tablequery import interests
from interfaces import mqtt_client, root_service_manager_requests
import logging


def instance_deployment(job_name, job):
    if job_name is None:
        return "Invalid argument", 400

    # table query the root to get the instances
    try:
        instances, siplist = resolution.service_resolution(job_name)
    except Exception as e:
        logging.error('Incoming Request /api/net/deployment failed service_resolution')
        return "Service resolution failed", 500

    return "job stored succesfully", 200


def instance_updates(job_name, instancenum, type):
    if job_name is None or instancenum is None:
        return "Invalid Parameters", 400

    if int(instancenum) < 0:
        return "Invalid instancenum", 400

    if type == "DEPLOYMENT" or type == "UNDEPLOYMENT":
        thread = Thread(target=_update_cache_and_workers,
                        kwargs={'job_name': job_name, 'instancenum': instancenum, 'type': type})
        thread.start()
        return "update notification received", 200
    else:
        return "Invalid type", 400


def _update_cache_and_workers(job_name, instancenum, type):
    if type == "DEPLOYMENT":
        query_result = root_service_manager_requests.cloud_table_query_service_name(job_name)
        instances = query_result['instance_list']
        updated_instance = None
        for instance in instances:
            if instance["instance_number"] == instancenum:
                updated_instance = instance
        if updated_instance is not None:
            mongodb_requests.mongo_update_job_instance(job_name=job_name, instance=updated_instance)
        else:
            logging.error("Invalid instancenum given")
    else:
        mongodb_requests.mongo_remove_job_instance(job_name=job_name, instancenum=instancenum)

    mqtt_client.mqtt_notify_service_change(job_name=job_name, type=type)