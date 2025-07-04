# Smart Task Queue system

## Problem Statement

Design Task queue system.

Task will be queued based on below factors
- Priority
- Resources available, cpu memory
- Dependancy

Will handle Job Scheduling, Prioritization, execution



## Core Features**

**API Endpoints**:
```
POST   /jobs                  # Submit a new job
GET    /jobs/{job_id}         # Get job status and details
GET    /jobs                  # List jobs with filtering
PATCH  /jobs/{job_id}/cancel  # Cancel a job if possible
GET    /jobs/{job_id}/logs    # Get job execution logs
WS     /jobs/stream           # WebSocket for real-time updates
```


**Job Model**:

- should support multiple types of jobs
- Priority levels
- Resource required
- Dependancy on other jobs
- Retry Config
    - `max_attempts`: number of times job should be retried in case of failure.
    - `backoff_multiplier`: multiplier of initial_delay seconds. in case of failure we will wait `initial_delay_seconds x backoff_multiplier` before relaunching the task.
    - `initial_delay_seconds`: number of times to wait 
- Timeout Config

**Core Features**:
- make sure idempotency is maintained: Same job submitted twice doesn't execute twice -- can be handled in api
- Scheduling happens keeping in mind three factors
    - Priority
    - dependencies
    - Availability
- Jobs can be dependant on other jobs successful completion
- Track System resources.
- Failed jobs retry with exponential backoff

**Production Considerations**
- Concurrent job execution (simulate with asyncio.sleep)
- graceful shutdown
- Job timeout handling
- Proper error messages and status codes
- Basic monitoring metrics

All above things will be handled using decorator to task


## DB Design

Design efficient PostgreSQL tables considering: - Job metadata and status - Dependency relationships (graph structure) - Execution history and logs - Resource allocation tracking

Jobs table with all the data for incoming jobs.

Scheduler will either listen to this job or listn to job from incoming apis.
    - will only implement db part first

Execution History
- This will be the log, this should be handled by our worker parent process. 

Resource allocation 
- This will be like log only, can be saved along with Execution History.

For Dependancy Relation ships need one to many relation ship between the jobs.


We will have essentially two tables

Jobs -- This will have all the jobs related data coming from user and also 

Jobs Dependancy

Logs

Status of job 

Gemini generated

pending: The job has been submitted to the system but is not yet ready to run (e.g., waiting for resources, or its dependencies haven't been evaluated yet).

blocked: The job is waiting for its dependencies to complete successfully. This is a specific state within 'pending' that indicates why it's not running.

ready: The job's dependencies are met (if any), and it is eligible to be picked up by a worker when resources become available.

running: The job is currently being executed by a worker.

completed: The job has finished its execution successfully.

failed: The job has failed its execution (either due to an error, timeout, or exhausting all retries). This indicates a permanent failure after retries.

retrying: The job has failed an attempt but is scheduled for a retry after a backoff delay.

cancelled: The job has been explicitly cancelled by a user request (PATCH /jobs/{job_id}/cancel).

Should we have seperate Status table?


- Jobs table will grow to millions of rows
- Status queries need to be fast
- Queue operations should be O(log n) or better
- Consider indexes carefully

3 tables

1. Jobs

id pk
Job uuid, indexed column may be based on time instead of uuid   
job name,
type,
active
payload : json
status : string # indexed can we have hash index
cpu_units
memory_mb
max_attempts
backoff_multiplier
initial_delay
timeout
created_time
modified_time
created_by
modified_by
priority : string can we have selectlist kind of thing eg. Critical: 1, High: 2, Normal: 3, Low: 4 indexed
times_attempted : no of time this job was attempted but failed
run_at: Jobs will be considered for queue after this time. # will also help in case of failure and to schedule jobs indexed
results: Json # log of execution, results and all 




2. Jobs Dependancy

Job_id: foreign_key
depends_on_id: foreign key jobs


3. Execution Logs

job_id : foreign_key jobs
duration_seconds : decimal
is_successfull : boolean # execution status
results : json
Execution start time : datetime
execution end time : datetime
message: text

## Design Choices. 

This will be one scheduler ie manager process which will basically share jobs with the worker. Worker will be single process, multi thread.

During scheduling, we will check available resources, get the jobs that can be done within given resources. will check the one with highest priority whether it can be done given the dependancies.

tasks : will be seperate class which will have all necessary tasks code.
    - like celery need to register tasks
    - other tasks cannot be taken in.

    - We will create a decorator which will enclose the actual task.
        - here logging will happen
        - Need to see if timeout is possible may be it is.
            - we will create thread inside this decorator for that task.
            - we can then also set timeout for thread here then.
            - Will return if task was completed successfully or not.
            - exception handling can also happen here.
    

        - 

Postgres -- db

RabiitMQ -- for message passing from scheduler to worker. 

API service

Scheduler Service

Worker -- single process -- multiple thread

    # in future should multi process setup. scheduler will send to master process. Master Process will align one of the worker process.

Logger -- In future -- this will log data in log table, message passing through rabbitmq


## Question 

How to know where job is at. 

How can we have observability at queue level itself.

## work 

Docker compose file

test results
    - test codes.

apis
    -   
```
POST   /jobs                  # Submit a new job                   # High Priority
GET    /jobs/{job_id}         # Get job status and details         # High Priority
GET    /jobs                  # List jobs with filtering           # Normal Priority
PATCH  /jobs/{job_id}/cancel  # Cancel a job if possible           # High Priority
GET    /jobs/{job_id}/logs    # Get job execution logs             # High Priority
WS     /jobs/stream           # WebSocket for real-time updates    # High Priority -- dpennacy on Scheduler
```


scheduler

worker 

First Apis

1. post api, get api , get list, patch,  # First four apis are easy.

2. Scheduler Worker

3. apis, logs, websocket

4. test

5. docker

What is needed. 

1. model for tables.

## Plan



## message brokers 

where its needed



scheduler to worker

    job.dispatch.job_id

worker to api

    basically for websocket

        <!-- job.logs.stream.<job_id>.<log_level> -->

    job.logs.job_id


worker to logger

    log to database

        <!-- job.logs.stream.<job_id>.<log_level> -->

    job.logs.job_id

scheduler to api

    monitoring of queue

    job.monitoring.queue

    job.monitoring.resource




