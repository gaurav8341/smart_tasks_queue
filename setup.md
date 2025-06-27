# Setup Instructions (Rough)

## Create Python Virtual Environment at Custom Location

To create a virtual environment named `smart_queue` at `/opt/grv` using mkvirtualenv:

```bash
# export WORKON_HOME=/opt/grv
mkvirtualenv smart_queue
```

To activate the environment:

```bash
workon smart_queue
```

To install dependencies:

```bash
pip install -r /home/vast/repos/smart_tasks_queue/requirements.txt
```


