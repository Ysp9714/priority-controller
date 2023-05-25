import kopf
import time
import logging
from kopf._cogs.structs.bodies import Body
from kubernetes import client
from config import settings


@kopf.on.create("jobs.v1alpha1.batch.volcano.sh")
def create_fn(body: Body, **kwargs):
    logging.info(f"A handler is called with body: {body.metadata.name}")

    scheduler_setting(body, settings.queue, settings.scheduler)


def scheduler_setting(body, queue_name, scheduler_name):
    jobs_patch(body, queue_name, scheduler_name)
    podgroup_patch(body, queue_name)


def jobs_patch(body: Body, queue: str, scheduler: str):
    job_patch = {
        "spec": {
            "schedulerName": scheduler,
            "queue": queue,
            "priorityClassName": body.metadata.namespace,
        },
        "metadata": {
            "annotation": {
                "scheduling.volcano.sh/queue-name": queue,
            }
        },
    }

    api = client.CustomObjectsApi()
    api.patch_namespaced_custom_object(
        group="batch.volcano.sh",
        version="v1alpha1",
        name=body.metadata.name,
        namespace=body.metadata.namespace,
        plural="jobs",
        body=job_patch,
    )


def podgroup_patch(body: Body, queue: str):
    api = client.CustomObjectsApi()
    podgroups_patch = {
        "spec": {
            "queue": queue,
            "priorityClassName": body.metadata.namespace,
        },
    }

    api.patch_namespaced_custom_object(
        group="scheduling.volcano.sh",
        version="v1beta1",
        name=f"{body.metadata.name}-{body.metadata.uid}",
        namespace=body.metadata.namespace,
        plural="podgroups",
        body=podgroups_patch,
    )
