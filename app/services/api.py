from fastapi import HTTPException, status, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import asyncio
from app.models.models import Job, ExecutionLog, JobDependency
from app.schemas.job_schemas import JobCreate, JobOut, JobLogOut, ExecutionLogOut
from app.database import get_db

# POST /jobs - Submit a new job
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    # Flatten resource_requirements and retry_config for DB model
    job_data = job.model_dump(exclude={"depends_on", "resource_requirements", "retry_config"})
    if job.resource_requirements:
        job_data["cpu_units"] = job.resource_requirements.cpu_units
        job_data["memory_mb"] = job.resource_requirements.memory_mb
    if job.retry_config:
        job_data["max_attempts"] = job.retry_config.max_attempts
        job_data["backoff_multiplier"] = job.retry_config.backoff_multiplier
        job_data["initial_delay"] = job.retry_config.initial_delay_seconds
    db_job = Job(**job_data)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    # Handle dependencies if any
    if job.depends_on:
        from app.models.models import JobDependency, Job
        for dep_uuid in job.depends_on:
            dep_job = db.query(Job).filter(Job.job_id == dep_uuid).first()
            if not dep_job:
                raise HTTPException(status_code=400, detail=f"Dependency job {dep_uuid} not found")
            dependency = JobDependency(dependant_id=db_job.id, depends_on_id=dep_job.id)
            db.add(dependency)
        db.commit()
    return job_out_from_db(db_job, db)

# GET /jobs/{job_id} - Get job status and details
def get_job(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_id == job_id,  True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_out_from_db(job, db)

# GET /jobs - List jobs with filtering
def list_jobs(status: Optional[str], priority: Optional[str], skip: int, limit: int, db: Session = Depends(get_db)):
    query = db.query(Job).all()
    if status:
        query = query.filter(Job.status == status)
    if priority:
        query = query.filter(Job.priority == priority)
    jobs = query.offset(skip).limit(limit).all()
    return [job_out_from_db(job, db) for job in jobs]

# PATCH /jobs/{job_id}/cancel - Cancel a job if possible
def cancel_job(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Check if any jobs depend on this job
    from app.models.models import JobDependency
    dependants = db.query(JobDependency).filter(JobDependency.depends_on_id == job.id).all()
    if dependants:
        raise HTTPException(status_code=400, detail="Cannot cancel: other jobs depend on this job.")
    if job.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    job.status = "cancelled"
    db.commit()
    db.refresh(job)
    return job

# GET /jobs/{job_id}/logs - Get job execution logs
def get_job_logs(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    logs = db.query(ExecutionLog).filter(ExecutionLog.job_id == job.id).all()
    job_resource_requirements = {"cpu_units": job.cpu_units, "memory_mb": job.memory_mb}
    job_logs = []
    for log in logs:
        log_out = JobLogOut.model_validate(log)
        log_out.status = job.status
        log_out.resource_requirements = job_resource_requirements
        job_logs.append(log_out)
    return job_logs

# WS /jobs/stream - WebSocket for real-time updates (basic example)
async def job_stream(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    last_log_id = None
    try:
        while True:
            # Fetch the latest execution logs
            query = db.query(ExecutionLog)
            if last_log_id is not None:
                query = query.filter(ExecutionLog.id > last_log_id)
            logs = query.order_by(ExecutionLog.id).all()
            if logs:
                for log in logs:
                    await websocket.send_json(ExecutionLogOut.model_validate(log).model_dump())
                last_log_id = logs[-1].id
            await asyncio.sleep(2)  # Poll every 2 seconds
    except WebSocketDisconnect:
        pass

def job_out_from_db(job, db):
    from app.models.models import JobDependency, Job
    dependencies = db.query(JobDependency).filter(JobDependency.dependant_id == job.id).all()
    depends_on_uuids = []
    for dep in dependencies:
        dep_job = db.query(Job).filter(Job.id == dep.depends_on_id).first()
        if dep_job:
            depends_on_uuids.append(dep_job.job_id)
    resource_requirements = {"cpu_units": job.cpu_units, "memory_mb": job.memory_mb}
    retry_config = {"max_attempts": job.max_attempts, "backoff_multiplier": job.backoff_multiplier, "initial_delay_seconds": job.initial_delay}
    job_out = JobOut.model_validate(job)
    job_out.depends_on = depends_on_uuids
    job_out.resource_requirements = resource_requirements
    job_out.retry_config = retry_config
    return job_out
