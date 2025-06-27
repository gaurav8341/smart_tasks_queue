from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from pytz import all_timezones
from .. import schemas, crud, models
from ..database import get_db
from app.schemas.job_schemas import JobCreate, JobOut, JobLogOut
from app.services import api as job_api

router = APIRouter()

# Event routes

# @router.post(
#     "/events",
#     response_model=schemas.EventOut,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new event",
#     description="Creates a new event with name, location, start/end time, and max capacity. Times are stored in UTC.",
# )
# async def create_event(event: schemas.EventCreate, db: AsyncSession = Depends(get_db)):
#     if event.timezone not in all_timezones:
#         raise HTTPException(status_code=400, detail=f"Invalid timezone: {event.timezone}")
#     # Check for unique event name
#     from sqlalchemy.future import select
#     existing = await db.execute(select(models.Event).where(models.Event.name == event.name))
#     if existing.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail=f"Event with name '{event.name}' already exists.")
#     return await crud.create_event(db, event)

# @router.get(
#     "/events",
#     response_model=schemas.EventPagination,
#     summary="List all upcoming events",
#     description="Lists all upcoming events (end_time > now). Supports pagination and timezone conversion.",
# )
# async def list_events(
#     db: AsyncSession = Depends(get_db),
#     timezone: str = Query("Asia/Kolkata", description="Timezone, e.g. 'Asia/Kolkata'"),
#     skip: int = 0,
#     limit: int = 100,
# ):
#     if timezone not in all_timezones:
#         raise HTTPException(status_code=400, detail=f"Invalid timezone: {timezone}")
#     return await crud.get_upcoming_events(db, user_tz=timezone, skip=skip, limit=limit)

# @router.post(
#     "/events/{event_id}/register",
#     response_model=schemas.AttendeeOut,
#     summary="Register an attendee for an event",
#     description="Registers an attendee (name, email) for a specific event. Prevents overbooking and duplicate registration.",
# )
# async def register_attendee(event_id: int, attendee: schemas.AttendeeCreate, db: AsyncSession = Depends(get_db)):
#     result = await crud.register_attendee(db, event_id, attendee)
#     if result is None:
#         raise HTTPException(status_code=400, detail="Duplicate registration or event not found.")
#     if result is False:
#         raise HTTPException(status_code=400, detail="Event is full.")
#     return result

# @router.get(
#     "/events/{event_id}/attendees",
#     response_model=schemas.AttendeePagination,
#     summary="List all attendees for an event",
#     description="Returns all registered attendees for an event. Supports pagination and timezone conversion.",
# )
# async def get_attendees(
#     event_id: int,
#     skip: int = 0,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_db),
#     timezone: str = Query("UTC", description="Timezone, e.g. 'Asia/Kolkata'"),
# ):
#     if timezone not in all_timezones:
#         raise HTTPException(status_code=400, detail=f"Invalid timezone: {timezone}")
#     return await crud.get_attendees(db, event_id, skip=skip, limit=limit, user_tz=timezone)

# Job routes

@router.post(
    "/jobs",
    response_model=JobOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new job",
    description="Create and queue a new job."
)
def create_job(job: JobCreate, db=Depends(get_db)):
    return job_api.create_job(job, db)

@router.get(
    "/jobs/{job_id}",
    response_model=JobOut,
    summary="Get job status and details",
    description="Retrieve the status and details of a job by its job_id."
)
def get_job(job_id: UUID, db=Depends(get_db)):
    return job_api.get_job(job_id, db)

@router.get(
    "/jobs",
    response_model=List[JobOut],
    summary="List jobs with filtering",
    description="List all jobs, optionally filtered by status or priority."
)
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    priority: Optional[str] = Query(None, description="Filter by job priority"),
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    return job_api.list_jobs(status, priority, skip, limit, db)

@router.patch(
    "/jobs/{job_id}/cancel",
    response_model=JobOut,
    summary="Cancel a job",
    description="Cancel a job if it is not already completed or cancelled."
)
def cancel_job(job_id: UUID, db=Depends(get_db)):
    return job_api.cancel_job(job_id, db)

@router.get(
    "/jobs/{job_id}/logs",
    response_model=List[JobLogOut],
    summary="Get job execution logs",
    description="Retrieve execution logs for a specific job."
)
def get_job_logs(job_id: UUID, db=Depends(get_db)):
    return job_api.get_job_logs(job_id, db)

@router.websocket("/jobs/stream")
async def job_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time job updates.
    """
    await job_api.job_stream(websocket)
