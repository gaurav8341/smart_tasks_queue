from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.ext.declarative import declarative_base # Note: declarative_base is deprecated in SQLAlchemy 2.0, use `MappedAsDataclass` or `DeclarativeBase`
from sqlalchemy.schema import UniqueConstraint, CheckConstraint # Need to import this for JobDependency
from sqlalchemy.orm import relationship # Will need this if you want ORM relationships
import uuid
from datetime import datetime, timezone # Import timezone for timezone-aware datetimes

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    # __table_args__ = (
    #     Index(
    #         'uq_job_id_active_true', 
    #         'job_id',
    #         unique=True,
    #         postgresql_where=Column('active') == True
    #     ),
    # )

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(UUID(as_uuid=True), default=uuid.uuid4, index=True)
    job_name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    # active = Column(Boolean, default=True, nullable=False) # no versioning for now 
    payload = Column(JSON) 
    status = Column(String, index=True)
    cpu_units = Column(Integer)
    memory_mb = Column(Integer)

    max_attempts = Column(Integer, default=1)
    backoff_multiplier = Column(DECIMAL, default=1.0) 
    initial_delay = Column(DECIMAL, default=0.0)
    timeout = Column(Integer)

    created_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    modified_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # created_by = Column(String)
    # modified_by = Column(String)

    priority_enum = ENUM('Critical', 'High', 'Normal', 'Low', name='job_priority_enum', create_type=False)
    priority = Column(priority_enum, index=True)
    
    times_attempted = Column(Integer, default=0) 

    run_at = Column(DateTime(timezone=True), index=True) # When this job can next be considered for running.
    results = Column(JSON)

    logs = relationship("ExecutionLog", back_populates="job", cascade="all, delete-orphan", order_by="ExecutionLog.log_timestamp")
 
    # does this make sense as we are accessing job dependancy
    parent_jobdependancy = relationship("JobDependency", back_populates="dependent_job", cascade="all, delete-orphan")
    child_jobdependancy = relationship("JobDependency", back_populates="parent_job", cascade="all, delete-orphan")
        

    # def update(self, session, **kwargs):
    #     """
    #     Deactivate the current active record of this job_id and create a new one with updated fields.
    #     This implements the versioning strategy.
    #     """
    #     # 1. Deactivate the current active version of this specific job_id
    #     # Crucially, you need to query for the current ACTIVE version of the job_id,
    #     # not just reference `self`'s `id`, because `self` might not be the *current active* version
    #     # if the object was loaded from a prior state.
    #     current_active_job = session.query(Job).filter(Job.job_id == self.job_id, Job.active == True).first()

    #     if current_active_job:
    #         current_active_job.active = False
    #         # No need to session.add(self) here if current_active_job is already session-managed.
    #         # session.flush() ensures the update is sent to the DB before the insert is attempted.
    #         session.flush()

    #     # 2. Prepare data for the new version.
    #     # Copy relevant data from the original (or current active) job record.
    #     # Exclude 'id' as it's auto-incremented, and 'active' will be set to True.
    #     # Ensure 'job_id' (the logical ID) is carried over.
        
    #     # Collect existing data (from current_active_job if found, otherwise from self)
    #     source_job = current_active_job if current_active_job else self 
        
    #     new_data = {
    #         c.name: getattr(source_job, c.name)
    #         for c in source_job.__table__.columns
    #         if c.name not in ['id', 'active', 'created_time', 'modified_time']
    #     }
        
    #     # Override with new values from kwargs and set active to True
    #     new_data.update(kwargs)
    #     new_data['active'] = True
    #     new_data['created_time'] = datetime.now(timezone.utc) # New version's creation time
    #     new_data['modified_time'] = datetime.now(timezone.utc) # New version's modified time

    #     new_job_version = Job(**new_data)
    #     session.add(new_job_version)

    #     # IMPORTANT: Session management (commit/rollback) should typically be handled by the caller
    #     # (e.g., in your API endpoint or service layer).
    #     # Removing `session.commit()` from here makes the method reusable within larger transactions.
    #     # If you keep commit here, ensure you understand its implications for atomicity.
    #     # session.commit()
        
    #     # Refresh the new object to get its `id` if needed immediately
    #     # session.refresh(new_job_version)
        
    #     return new_job_version

class JobDependency(Base):
    __tablename__ = 'job_dependencies'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.job_id'), nullable=False)  # The job that depends
    # depends_on_id = Column(UUID(as_uuid=True), ForeignKey('jobs.job_id'), nullable=False) # The job it depends on
    id = Column(Integer, primary_key=True, autoincrement=True)
    dependant_id  = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    depends_on_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    
    # should be auto populated
    dependant_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4)
    depends_on_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4)
    
    __table_args__ = (
        UniqueConstraint('dependant_id', 'depends_on_id', name='uq_job_dependency_pair'),
        CheckConstraint('dependant_id != depends_on_id', name='chk_no_self_dependency') # Requires `from sqlalchemy import CheckConstraint`
    )
    
    parent_job = relationship("Job", foreign_keys=[depends_on_id], back_populates="child_jobdependancy")
    dependent_job = relationship("Job", foreign_keys=[dependant_id], back_populates="parent_jobdependancy")

class ExecutionLog(Base):
    __tablename__ = 'execution_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False) 
    
    # worker_id = Column(integer)Need worker id to know which worker did the task
    job_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4) # should be auto populated

    log_timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)

    message = Column(String, nullable=False)

    duration_seconds = Column(DECIMAL)
    
    is_successful = Column(Boolean)
    results = Column(JSON)
    
    cpu_units = Column(Integer)
    memory_mb = Column(Integer)

    execution_start_time = Column(DateTime(timezone=True))
    execution_end_time = Column(DateTime(timezone=True))

    attempt_number = Column(Integer, nullable=False, default=1) 
    
    job = relationship("Job", back_populates="logs")