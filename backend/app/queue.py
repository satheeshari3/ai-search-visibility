from redis import Redis
from rq import Queue

redis_connection = Redis(
    host="localhost",
    port=6379,
    db=0,
)

analysis_queue = Queue(
    "analysis",
    connection=redis_connection,
    default_timeout=1800,
)