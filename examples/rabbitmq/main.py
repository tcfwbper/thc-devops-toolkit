# Copyright 2025 Tsung-Han Chang. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from thc_devops_toolkit.containerization.docker import docker_pull, docker_run_daemon, docker_stop
from thc_devops_toolkit.infrastructure.rabbitmq import RabbitMQActions, RabbitMQConfig, RabbitMQManager
from thc_devops_toolkit.observability import LogLevel, logger

rabbitmq_example_dir = Path(__file__).resolve().parent
rabbitmq_full_image_name = "rabbitmq:4.1.4-alpine"
rabbitmq_container_name = "test-rabbitmq-server"
rabbitmq_host = "0.0.0.0"
rabbitmq_port = 5672
rabbitmq_user = "user"
rabbitmq_password = "password"


@contextmanager
def run_rabbitmq_server(
    user: str,
    password: str,
) -> Iterator[None]:
    docker_pull(full_image_name=rabbitmq_full_image_name)
    docker_run_daemon(
        full_image_name=rabbitmq_full_image_name,
        remove=True,
        container_name=rabbitmq_container_name,
        env_vars=[
            f"RABBITMQ_DEFAULT_USER={user}",
            f"RABBITMQ_DEFAULT_PASS={password}",
        ],
        port_mappings=[f"{rabbitmq_port}:{rabbitmq_port}"],
    )
    time.sleep(10)

    yield

    docker_stop(obj=rabbitmq_container_name)


def rabbitmq_example() -> None:
    """Example demonstrating RabbitMQ manager usage."""
    # Initialize RabbitMQ manager
    manager = RabbitMQManager()

    # Create RabbitMQConfig for sending and receiving messages
    sender = RabbitMQConfig(
        host=rabbitmq_host,
        port=rabbitmq_port,
        user=rabbitmq_user,
        password=rabbitmq_password,
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_routing_key",
        tls=False,
    )
    receiver = RabbitMQConfig(
        host=rabbitmq_host,
        port=rabbitmq_port,
        user=rabbitmq_user,
        password=rabbitmq_password,
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_routing_key",
        tls=False,
    )

    # 1. Register receiver and sender
    logger.info("[RabbitMQ] Registering receiver and sender...")
    sender_registered = manager.register(action=RabbitMQActions.SEND, config=sender)
    receiver_registered = manager.register(action=RabbitMQActions.RECV, config=receiver)

    if not receiver_registered or not sender_registered:
        logger.highlight(
            LogLevel.ERROR,
            "Failed to register receiver or sender",
        )
        return

    # 2. Run RabbitMQ manager
    logger.info("Starting RabbitMQ manager...")

    manager.run()

    # Give some time for connections to establish
    time.sleep(2)

    # 3. Put messages to sender and receive from receiver
    logger.info("Sending messages...")
    test_messages = [b"Hello, RabbitMQ!", b"This is message 2", b"Message number 3", b"Final test message"]

    # Send messages
    for i, message in enumerate(test_messages, 1):
        logger.highlight(
            LogLevel.INFO,
            f"Putting message {i} into send queue: {message}",
        )
        sender.message_queue.put(message)

    # Receive messages
    logger.info("Waiting for messages to be received...")
    received_messages = []

    # Wait up to 10 seconds for messages to be received
    for i in range(len(test_messages)):
        try:
            # Wait for message with timeout
            message = receiver.message_queue.get(timeout=5)
            received_messages.append(message)
        except Exception as exception:
            logger.highlight(
                LogLevel.ERROR,
                f"Error occurred while waiting for message {i+1}: {exception}",
            )
            break

    for i, message in enumerate(received_messages):
        logger.highlight(
            LogLevel.INFO,
            f"Received message {i+1}: {message}",
        )

    # Verify all messages were received
    if len(received_messages) == len(test_messages):
        logger.info("All messages successfully sent and received!")
        for sent, received in zip(test_messages, received_messages):
            if sent == received:
                logger.info("✓ Message verified: %s", sent)
            else:
                logger.error(
                    "✗ Message mismatch: sent %s, received %s",
                    sent,
                    received,
                )
    else:
        logger.highlight(
            LogLevel.WARNING,
            f"Only {len(received_messages)} out of {len(test_messages)} messages received",
        )

    # Wait a bit more to ensure all operations complete
    time.sleep(2)

    # 4. Stop RabbitMQ manager
    logger.info("Stopping RabbitMQ manager...")
    manager.shutdown()
    logger.info("RabbitMQ manager stopped successfully")


def main() -> None:
    with run_rabbitmq_server(user=rabbitmq_user, password=rabbitmq_password):
        logger.info("[RabbitMQ] RabbitMQ server is running.")

        # Run the RabbitMQ example
        rabbitmq_example()

    logger.info("[RabbitMQ] RabbitMQ server is stopped.")


if __name__ == "__main__":
    main()
