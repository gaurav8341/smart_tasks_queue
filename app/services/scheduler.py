from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from app.models.models import Job, JobDependency
from app.database import get_db
from fastapi import Depends

import time
from app.services.rabbitmq_client import RabbitMQClient

# Initialize RabbitMQ client
rabbitmq_client = RabbitMQClient()
rabbitmq_client.connect()

# Declare exchanges and queues on startup
if rabbitmq_client.connection and rabbitmq_client.channel:
    rabbitmq_client.declare_exchange(RabbitMQClient.JOB_DISPATCH_EXCHANGE)
    rabbitmq_client.declare_queue(RabbitMQClient.JOB_DISPATCH_QUEUE, arguments={'x-max-priority': 10})
    rabbitmq_client.bind_queue(RabbitMQClient.JOB_DISPATCH_QUEUE, RabbitMQClient.JOB_DISPATCH_EXCHANGE, "job.dispatch.*")

# in this file we will rread db and get all uncompleted jobs 
# whose run time is less than equal to current time.

# Read the db. if all dpendancy are fulfilled. then add in the queue. 

# so there are 2 modules here. one will add in queue other will dispatch

# 1. read the db and get all uncompleted jobs
def get_uncompleted_jobs(db: Session = Depends(get_db)) -> List[Job]:
    current_time = datetime.now(timezone.utc)
    jobs = db.query(Job).filter(
        Job.status != "completed",
        Job.run_at <= current_time
    ).all()
    
    # Filter jobs that have all dependencies fulfilled
    uncompleted_jobs = []
    for job in jobs:
        dependencies = db.query(JobDependency).filter(JobDependency.dependant_id == job.id).all()
        if not dependencies or all(dep.depends_on.status == "completed" for dep in dependencies):
            uncompleted_jobs.append(job)
    
    return uncompleted_jobs

# now main function which will continue to run and check for uncompleted jobs
def schedule_jobs(db: Session = Depends(get_db)):
    while True:
        uncompleted_jobs = get_uncompleted_jobs(db)
        for job in uncompleted_jobs:
            # Here you would add the job to the queue for processing
            # For example, using a message broker or a task queue
            print(f"Scheduling job: {job.job_name} with ID: {job.job_id}")
            
            # Map job priority to RabbitMQ message priority (1-10, 10 being highest)
            priority_map = {
                "Critical": 10,
                "High": 7,
                "Normal": 4,
                "Low": 1
            }
            message_priority = priority_map.get(job.priority, 4) # Default to Normal (4)
            
            # Publish job to RabbitMQ
            rabbitmq_client.publish_message(
                exchange_name=RabbitMQClient.JOB_DISPATCH_EXCHANGE,
                routing_key=f"job.dispatch.{job.job_id}",
                message=job.to_dict(), # Assuming job object can be converted to a dictionary
                priority=message_priority
            )
            
            # Update job status to "queued"
            job.status = "queued"
            db.add(job)
            db.commit()
            db.refresh(job)
            
            
        # Sleep for a while before checking again
        time.sleep(10)  # Adjust the sleep time as needed
