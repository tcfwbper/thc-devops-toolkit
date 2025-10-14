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
import time
from dataclasses import dataclass
from enum import Enum
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any

import pika

from thc_devops_toolkit.observability import THCLoggerHighlightLevel, thc_logger


class RabbitMQActions(Enum):
    """RabbitMQ actions."""

    SEND: str = "send"
    RECV: str = "receive"


@dataclass
class RabbitMQChannel:
    """Represents a RabbitMQ channel configuration.

    Attributes:
        chan_id (str): Unique identifier for the channel.
        queue (Queue[bytes]): Queue for message passing.
        routing_key (str): RabbitMQ routing key.
        exchange_name (str): RabbitMQ exchange name.
    """

    chan_id: str
    queue: Queue[bytes]
    routing_key: str
    exchange_name: str


class RabbitMQManager:  # pylint: disable=too-many-instance-attributes
    """Manages sending and receiving messages using RabbitMQ."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        exchange_type: str,
    ) -> None:
        """Initializes the RabbitMQ manager.

        Args:
            host (str): RabbitMQ host.
            port (int): RabbitMQ port.
            user (str): RabbitMQ user.
            password (str): RabbitMQ password.
            exchange_type (str): RabbitMQ exchange type.
        """
        self.host = host
        self.port = port
        self.exchange_type = exchange_type
        self.credentials = pika.PlainCredentials(user, password)
        self.senders: dict[str, RabbitMQChannel] = {}
        self.receivers: dict[str, RabbitMQChannel] = {}
        self.threads: list[Thread] = []
        self.shutdown_event = Event()

    def register(
        self,
        action: RabbitMQActions,
        exchange_name: str,
        routing_key: str,
        chan: Queue[bytes] | None = None,
    ) -> bool:
        """Registers a sender or receiver.

        Args:
            action (RabbitMQActions): Action to perform (send or receive).
            exchange_name (str): RabbitMQ exchange name.
            routing_key (str): RabbitMQ routing key.
            chan (Queue[bytes] | None): Queue for sending or receiving messages.

        Returns:
            bool: True if registration is successful, False otherwise.
        """
        chan_id = "/".join([exchange_name, routing_key])
        if chan is None or exchange_name == "" or routing_key == "":
            return False

        if action == RabbitMQActions.SEND:
            chan_dict = self.senders
        elif action == RabbitMQActions.RECV:
            chan_dict = self.receivers
        else:
            return False

        if chan_id not in chan_dict:
            chan_dict[chan_id] = RabbitMQChannel(
                chan_id=chan_id,
                queue=chan,
                exchange_name=exchange_name,
                routing_key=routing_key,
            )
            return True
        return False

    def run(self) -> None:
        """Starts all registered sender and receiver threads."""
        for receiver in self.receivers.values():
            thc_logger.highlight(
                level=THCLoggerHighlightLevel.INFO,
                message=f"[RabbitMQ] start receiver: {receiver}",
            )
            thread = Thread(
                target=self.recv,
                args=(
                    receiver.queue,
                    receiver.exchange_name,
                    receiver.routing_key,
                ),
                daemon=True,
            )
            thread.start()
            self.threads.append(thread)
        for sender in self.senders.values():
            thc_logger.highlight(
                level=THCLoggerHighlightLevel.INFO,
                message=f"[RabbitMQ] start sender: {sender}",
            )
            thread = Thread(
                target=self.send,
                args=(
                    sender.queue,
                    sender.exchange_name,
                    sender.routing_key,
                ),
                daemon=True,
            )
            thread.start()
            self.threads.append(thread)

    def recv(self, chan: Queue[bytes], exchange_name: str, routing_key: str) -> None:
        """Receives messages from RabbitMQ and puts them in the queue.

        Args:
            chan (Queue[bytes]): Queue to put received messages.
            exchange_name (str): RabbitMQ exchange name.
            routing_key (str): RabbitMQ routing key.
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
            thc_logger.highlight(
                level=THCLoggerHighlightLevel.INFO,
                message=f"[RabbitMQ] data receive from {exchange_name}/{routing_key}",
            )
            try:
                chan.put(body)
            except Exception as exception:  # pylint: disable=broad-except
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.ERROR,
                    message=f"[RabbitMQ] Failed to put data into queue {chan}: {exception}",
                )

        while not self.shutdown_event.is_set():
            try:
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.INFO,
                    message=f"[RabbitMQ] {exchange_name}/{routing_key} starting...",
                )
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host, port=self.port, credentials=self.credentials),
                )
                channel = connection.channel()
                channel.exchange_declare(exchange=exchange_name, exchange_type=self.exchange_type)
                result = channel.queue_declare("", exclusive=True)
                queue_name = result.method.queue
                channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
                channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
                channel.start_consuming()
            except Exception as exception:  # pylint: disable=broad-except
                if self.shutdown_event.is_set():
                    break
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.INFO,
                    message=f"[RabbitMQ] {exchange_name}/{routing_key} restart...",
                )
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.ERROR,
                    message=f"[RabbitMQ] Error occurred: {exception}",
                )
                time.sleep(10)

    def send(self, chan: Queue[bytes], exchange_name: str, routing_key: str) -> None:
        """Sends messages from the queue to RabbitMQ.

        Args:
            chan (Queue[bytes]): Queue to get messages to send.
            exchange_name (str): RabbitMQ exchange name.
            routing_key (str): RabbitMQ routing key.
        """
        while not self.shutdown_event.is_set():
            try:
                # Add timeout to allow shutdown check
                data = chan.get(block=True, timeout=1)
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host, port=self.port, credentials=self.credentials),
                )
                channel = connection.channel()
                channel.exchange_declare(exchange=exchange_name, exchange_type=self.exchange_type)
                channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=data)
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.INFO,
                    message=f"[RabbitMQ] data send to {exchange_name}/{routing_key}",
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
                    chan.put(data)

    def shutdown(self) -> None:
        """Gracefully shuts down the RabbitMQ manager and all threads."""
        thc_logger.highlight(
            level=THCLoggerHighlightLevel.INFO,
            message="[RabbitMQ] Initiating graceful shutdown...",
        )
        self.shutdown_event.set()

        # Wait for all threads to finish with a reasonable timeout
        for thread in self.threads:
            thread.join(timeout=5.0)
            if thread.is_alive():
                thc_logger.highlight(
                    level=THCLoggerHighlightLevel.WARNING,
                    message=f"[RabbitMQ] Thread {thread.name} did not stop within timeout",
                )

        thc_logger.highlight(
            level=THCLoggerHighlightLevel.INFO,
            message="[RabbitMQ] Graceful shutdown completed",
        )
