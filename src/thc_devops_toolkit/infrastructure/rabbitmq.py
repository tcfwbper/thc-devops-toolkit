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
"""RabbitMQ manager for sending and receiving messages using RabbitMQ."""
import ssl
import time
from dataclasses import dataclass, field
from enum import Enum
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel

from thc_devops_toolkit.observability import THCLoggerHighlightLevel, thc_logger


class RabbitMQActions(Enum):
    """RabbitMQ actions."""

    SEND: str = "send"
    RECV: str = "receive"


@dataclass
class RabbitMQConfig:  # pylint: disable=too-many-instance-attributes
    """RabbitMQ configuration.

    Attributes:
        host (str): RabbitMQ host.
        port (int): RabbitMQ port.
        user (str): RabbitMQ user.
        password (str): RabbitMQ password.
        exchange_name (str): RabbitMQ exchange name.
        exchange_type (str): RabbitMQ exchange type.
        routing_key (str): RabbitMQ routing key.
        tls (bool): Whether to use TLS.
        message_queue (Queue): Queue for message passing or receiving.
        channel (BlockingChannel | None): RabbitMQ channel.
    """

    host: str
    port: int
    user: str
    password: str
    exchange_name: str
    exchange_type: str
    routing_key: str
    tls: bool
    message_queue: Queue[bytes] = field(default_factory=Queue, init=False, repr=False)
    channel: BlockingChannel | None = field(default=None, init=False, repr=False)


class RabbitMQManager:  # pylint: disable=too-many-instance-attributes
    """Manages sending and receiving messages using RabbitMQ."""

    def __init__(self) -> None:
        """Initializes the RabbitMQ manager."""
        self.senders: dict[str, RabbitMQConfig] = {}
        self.receivers: dict[str, RabbitMQConfig] = {}
        self.threads: list[Thread] = []
        self.shutdown_event = Event()

    def register(
        self,
        action: RabbitMQActions,
        config: RabbitMQConfig,
    ) -> bool:
        """Registers a sender or receiver.

        Args:
            action (RabbitMQActions): Action to perform (send or receive).
            config (RabbitMQConfig): RabbitMQ configuration.

        Returns:
            bool: True if registration is successful, False otherwise.
        """
        if config.message_queue is None or config.exchange_name == "" or config.routing_key == "":
            thc_logger.highlight(level=THCLoggerHighlightLevel.WARNING, message="[RabbitMQ] Invalid configuration for registration.")
            return False

        if action == RabbitMQActions.SEND:
            chan_dict = self.senders
        elif action == RabbitMQActions.RECV:
            chan_dict = self.receivers
        else:
            return False

        chan_id = "/".join([config.exchange_name, config.routing_key])
        if chan_id not in chan_dict:
            chan_dict[chan_id] = config
            thc_logger.info("[RabbitMQ] Channel %s registered.", chan_id)
            return True

        thc_logger.highlight(
            level=THCLoggerHighlightLevel.WARNING,
            message=f"[RabbitMQ] Channel {chan_id} already registered to {action}, ignored.",
        )
        return False

    def run(self) -> None:
        """Starts all registered sender and receiver threads."""
        for receiver_id, receiver_config in self.receivers.items():
            thc_logger.info("[RabbitMQ] starting receiver: %s", receiver_id)
            thread = Thread(
                target=self.recv,
                args=(receiver_config,),
                daemon=True,
            )
            thread.start()
            thc_logger.info("[RabbitMQ] receiver: %s started", receiver_id)
            self.threads.append(thread)
        for sender_id, sender_config in self.senders.items():
            thc_logger.info("[RabbitMQ] starting sender: %s", sender_id)
            thread = Thread(
                target=self.send,
                args=(sender_config,),
                daemon=True,
            )
            thread.start()
            thc_logger.info("[RabbitMQ] sender: %s started", sender_id)
            self.threads.append(thread)

    @staticmethod
    def _connect(host: str, port: int, user: str, password: str, tls: bool) -> pika.BlockingConnection:
        """Establish a connection to RabbitMQ server.

        Args:
            host (str): RabbitMQ server host.
            port (int): RabbitMQ server port.
            user (str): RabbitMQ server username.
            password (str): RabbitMQ server password.
            tls (bool): Whether to use TLS for the connection.
        """
        if tls:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # self-signed
            ssl_options = pika.SSLOptions(ssl_context)
            return pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host,
                    port=port,
                    credentials=pika.PlainCredentials(user, password),
                    ssl_options=ssl_options,
                ),
            )
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=pika.PlainCredentials(user, password),
            ),
        )

    def recv(self, config: RabbitMQConfig) -> None:
        """Receives messages from RabbitMQ and puts them in the queue.

        Args:
            config (RabbitMQConfig): RabbitMQ configuration.
        """

        def callback(
            ch: Any,  # pylint: disable=unused-argument,invalid-name
            method: Any,  # pylint: disable=unused-argument
            properties: Any,  # pylint: disable=unused-argument
            body: bytes,
        ) -> None:
            """Callback function for receiving messages.

            Args:
                ch (Any): Channel.
                method (Any): Method.
                properties (Any): Properties.
                body (bytes): Message body.
            """
            thc_logger.info("[RabbitMQ] data receive from %s/%s", config.exchange_name, config.routing_key)
            try:
                config.message_queue.put(body)
            except Exception as exception:  # pylint: disable=broad-except
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.ERROR,
                    message=f"[RabbitMQ] Failed to put data into queue {config.message_queue}: {exception}",
                )

        while not self.shutdown_event.is_set():
            try:
                thc_logger.info("[RabbitMQ] %s/%s starting...", config.exchange_name, config.routing_key)
                connection = self._connect(
                    host=config.host,
                    port=config.port,
                    user=config.user,
                    password=config.password,
                    tls=config.tls,
                )
                channel = connection.channel()
                config.channel = channel
                channel.exchange_declare(exchange=config.exchange_name, exchange_type=config.exchange_type)
                result = channel.queue_declare("", exclusive=True)
                queue_name = result.method.queue
                channel.queue_bind(exchange=config.exchange_name, queue=queue_name, routing_key=config.routing_key)
                channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
                channel.start_consuming()
            except Exception as exception:  # pylint: disable=broad-except
                if self.shutdown_event.is_set():
                    break
                thc_logger.info(
                    "[RabbitMQ] %s/%s restart...",
                    config.exchange_name,
                    config.routing_key,
                )
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.ERROR,
                    message=f"[RabbitMQ] Error occurred: {exception}",
                )
                time.sleep(10)

    def send(self, config: RabbitMQConfig) -> None:
        """Sends messages from the queue to RabbitMQ.

        Args:
            config (RabbitMQConfig): RabbitMQ configuration.
        """
        while not self.shutdown_event.is_set():
            try:
                # Add timeout to allow shutdown check
                data = config.message_queue.get(block=True, timeout=1)
                connection = self._connect(
                    host=config.host,
                    port=config.port,
                    user=config.user,
                    password=config.password,
                    tls=config.tls,
                )
                channel = connection.channel()
                channel.exchange_declare(exchange=config.exchange_name, exchange_type=config.exchange_type)
                channel.basic_publish(exchange=config.exchange_name, routing_key=config.routing_key, body=data)
                thc_logger.info(
                    "[RabbitMQ] data send to %s/%s",
                    config.exchange_name,
                    config.routing_key,
                )
                connection.close()
            except Empty:
                continue
            except Exception as exception:  # pylint: disable=broad-except
                if self.shutdown_event.is_set():
                    break
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.ERROR,
                    message=f"[RabbitMQ] Error occurred: {exception}",
                )
                # Brief pause before retry
                time.sleep(10)
                if "data" in locals():
                    config.message_queue.put(data)

    def shutdown(self) -> None:
        """Gracefully shuts down the RabbitMQ manager and all threads."""
        thc_logger.info("[RabbitMQ] Graceful shutdown...")
        self.shutdown_event.set()

        # Close all channels
        for receiver_config in self.receivers.values():
            if receiver_config.channel is not None:
                receiver_config.channel.stop_consuming()

        # Wait for all threads to finish with a reasonable timeout
        for thread in self.threads:
            thread.join(timeout=5.0)
            if thread.is_alive():
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.WARNING,
                    message=f"[RabbitMQ] Thread {thread.name} did not stop within timeout",
                )

        thc_logger.info("[RabbitMQ] Graceful shutdown completed")
