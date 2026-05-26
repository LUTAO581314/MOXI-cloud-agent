from celery import shared_task


@shared_task
def provision_assistant(assistant_id):
    return {"assistant_id": assistant_id, "status": "queued"}
