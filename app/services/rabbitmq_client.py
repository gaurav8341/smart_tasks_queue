import pika
import os
import json

class RabbitMQClient:
    # Exchange Names
    JOB_DISPATCH_EXCHANGE = 'job_dispatch_exchange'
    JOB_LOGS_STREAM_EXCHANGE = 'job_logs_stream_exchange'
    JOB_LOGS_DB_EXCHANGE = 'job_logs_db_exchange'
    JOB_MONITORING_EXCHANGE = 'job_monitoring_exchange'

    # Queue Names
    JOB_DISPATCH_QUEUE = 'job_dispatch_queue'
    JOB_LOGS_DB_QUEUE = 'job_logs_db_queue'
    JOB_MONITORING_QUEUE = 'job_monitoring_queue'

    def __init__(self):
        self.connection = None
        self.channel = None
        self.RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
        self.RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
        self.RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
        self.RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

    def connect(self):
        try:
            credentials = pika.PlainCredentials(self.RABBITMQ_USER, self.RABBITMQ_PASS)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.RABBITMQ_HOST,
                    port=self.RABBITMQ_PORT,
                    credentials=credentials
                )
            )
            self.channel = self.connection.channel()
            print("Connected to RabbitMQ successfully!")
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("RabbitMQ connection closed.")

    def declare_exchange(self, exchange_name, exchange_type='topic', durable=True):
        if self.channel:
            self.channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=durable)
            print(f"Exchange '{exchange_name}' declared.")

    def declare_queue(self, queue_name, durable=True, arguments=None):
        if self.channel:
            self.channel.queue_declare(queue=queue_name, durable=durable, arguments=arguments)
            print(f"Queue '{queue_name}' declared.")

    def bind_queue(self, queue_name, exchange_name, routing_key):
        if self.channel:
            self.channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
            print(f"Queue '{queue_name}' bound to exchange '{exchange_name}' with routing key '{routing_key}'.")

    def publish_message(self, exchange_name, routing_key, message, priority=None):
        if not self.channel:
            print("Not connected to RabbitMQ. Cannot publish message.")
            return

        properties = pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
            priority=priority # Set message priority
        )
        try:
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=properties
            )
            print(f"Message published to exchange '{exchange_name}' with routing key '{routing_key}' and priority {priority}: {message}")
        except Exception as e:
            print(f"Error publishing message: {e}")

    def consume_messages(self, queue_name, callback):
        if not self.channel:
            print("Not connected to RabbitMQ. Cannot consume messages.")
            return

        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        print(f"Started consuming messages from '{queue_name}'. To exit press CTRL+C")
        self.channel.start_consuming()

    def ack_message(self, ch, method):
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def nack_message(self, ch, method):
        ch.basic_nack(delivery_tag=method.delivery_tag)

# Example Usage (for testing purposes, can be removed later)
if __name__ == "__main__":
    client = RabbitMQClient()
    client.connect()

    if client.connection and client.channel:
        # Declare exchanges
        client.declare_exchange(RabbitMQClient.JOB_DISPATCH_EXCHANGE)
        client.declare_exchange(RabbitMQClient.JOB_LOGS_STREAM_EXCHANGE)
        client.declare_exchange(RabbitMQClient.JOB_LOGS_DB_EXCHANGE)
        client.declare_exchange(RabbitMQClient.JOB_MONITORING_EXCHANGE)

        # Declare queues
        client.declare_queue(RabbitMQClient.JOB_DISPATCH_QUEUE, arguments={'x-max-priority': 10}) # Max priority 10
        client.declare_queue(RabbitMQClient.JOB_LOGS_DB_QUEUE)
        client.declare_queue(RabbitMQClient.JOB_MONITORING_QUEUE)

        # Bind queues to exchanges
        client.bind_queue(RabbitMQClient.JOB_DISPATCH_QUEUE, RabbitMQClient.JOB_DISPATCH_EXCHANGE, "job.dispatch.*") # for schduler to dispatcher
        client.bind_queue(RabbitMQClient.JOB_LOGS_DB_QUEUE, RabbitMQClient.JOB_LOGS_DB_EXCHANGE, "job.logs.db.#") # for all services to logger # from worker to stream 
        client.bind_queue(RabbitMQClient.JOB_MONITORING_QUEUE, RabbitMQClient.JOB_MONITORING_EXCHANGE, "job.monitoring.#") # for real time resource monitoring

        # Publish some messages with different priorities
        client.publish_message(RabbitMQClient.JOB_DISPATCH_EXCHANGE, "job.dispatch.123", {"task": "low_priority_task"}, priority=1)
        client.publish_message(RabbitMQClient.JOB_DISPATCH_EXCHANGE, "job.dispatch.456", {"task": "high_priority_task"}, priority=10)
        client.publish_message(RabbitMQClient.JOB_DISPATCH_EXCHANGE, "job.dispatch.789", {"task": "medium_priority_task"}, priority=5)

        def publisher_callback(ch, method, properties, body):
            print(f" [x] Received {body.decode()} from {method.routing_key} with priority {properties.priority}")
            client.ack_message(ch, method)

        # To consume, uncomment the line below and run this script
        # client.consume_messages(RabbitMQClient.JOB_DISPATCH_QUEUE, publisher_callback)

        print("\n--- Consumer Example ---")
        def consumer_callback(ch, method, properties, body):
            print(f" [x] Consumed {body.decode()} from {method.routing_key} with priority {properties.priority}")
            # Process the message here
            client.ack_message(ch, method)

        try:
            print(f"Starting to consume from {RabbitMQClient.JOB_DISPATCH_QUEUE}...")
            client.consume_messages(RabbitMQClient.JOB_DISPATCH_QUEUE, consumer_callback)
        except KeyboardInterrupt:
            print("Consumer stopped by user.")
        except Exception as e:
            print(f"An error occurred during consumption: {e}")
        finally:
            client.close()