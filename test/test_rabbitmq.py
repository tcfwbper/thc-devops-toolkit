from unittest.mock import MagicMock, patch
from queue import Queue
from thc_devops_toolkit.infrastructure.rabbitmq import RabbitMQManager, RabbitMQActions

def test_rabbitmq_manager_init():
    mgr = RabbitMQManager(
        host="localhost",
        port=5672,
        user="u",
        password="p",
        exchange_type="direct"
    )
    assert mgr.host == "localhost"
    assert mgr.port == 5672
    assert mgr.exchange_type == "direct"
    assert isinstance(mgr.senders, dict)
    assert isinstance(mgr.receivers, dict)
    assert isinstance(mgr.threads, list)
    assert mgr.shutdown_event.is_set() is False

def test_register_sender_receiver():
    mgr = RabbitMQManager("h", 1, "u", "p", "fanout")
    q = Queue()
    # sender
    assert mgr.register(RabbitMQActions.SEND, "ex", "rk", q) is True
    assert mgr.register(RabbitMQActions.SEND, "ex", "rk", q) is False  # duplicate
    # receiver
    q2 = Queue()
    assert mgr.register(RabbitMQActions.RECV, "ex2", "rk2", q2) is True
    # invalid
    assert mgr.register(RabbitMQActions.SEND, "", "rk", q) is False
    assert mgr.register(RabbitMQActions.SEND, "ex", "", q) is False
    assert mgr.register(RabbitMQActions.SEND, "ex", "rk", None) is False
    assert mgr.register(None, "ex", "rk", q) is False

def test_register_invalid_action():
    mgr = RabbitMQManager("h", 1, "u", "p", "fanout")
    q = Queue()
    class DummyAction:
        pass
    assert mgr.register(DummyAction(), "ex", "rk", q) is False

def test_run_starts_threads():
    mgr = RabbitMQManager("h", 1, "u", "p", "fanout")
    q1 = Queue()
    q2 = Queue()
    mgr.register(RabbitMQActions.SEND, "ex", "rk", q1)
    mgr.register(RabbitMQActions.RECV, "ex2", "rk2", q2)
    with patch.object(
        mgr, "send"
    ) as send_mock, patch.object(
        mgr, "recv"
    ) as recv_mock:
        mgr.run()
        assert len(mgr.threads) == 2
        # Threads should be started (daemon)
        for t in mgr.threads:
            assert t.daemon

def test_send_and_recv_logic():
    mgr = RabbitMQManager("h", 1, "u", "p", "fanout")
    q = Queue()
    # Patch pika.BlockingConnection and related methods
    with patch("pika.BlockingConnection") as conn_mock:
        conn = MagicMock()
        conn_mock.return_value = conn
        channel = MagicMock()
        conn.channel.return_value = channel
        channel.exchange_declare.return_value = None
        channel.basic_publish.return_value = None
        # Put a message in queue
        q.put(b"msg")
        # Set shutdown after one send
        def shutdown_after_send(*args, **kwargs):
            mgr.shutdown_event.set()
        channel.basic_publish.side_effect = shutdown_after_send
        mgr.send(q, "ex", "rk")
        channel.exchange_declare.assert_called()
        channel.basic_publish.assert_called()
        conn.close.assert_called()
        # Test recv: simulate callback and consuming
        conn_mock.reset_mock()
        conn.reset_mock()
        channel.reset_mock()
        mgr.shutdown_event.clear()
        conn_mock.return_value = conn
        conn.channel.return_value = channel
        channel.exchange_declare.return_value = None
        channel.queue_declare.return_value.method.queue = "qname"
        channel.queue_bind.return_value = None
        channel.basic_consume.return_value = None
        def start_consuming_side_effect():
            mgr.shutdown_event.set()
        channel.start_consuming.side_effect = start_consuming_side_effect
        mgr.recv(q, "ex", "rk")
        channel.exchange_declare.assert_called()
        channel.queue_declare.assert_called()
        channel.queue_bind.assert_called()
        channel.basic_consume.assert_called()
        channel.start_consuming.assert_called()

def test_shutdown_joins_threads():
    mgr = RabbitMQManager("h", 1, "u", "p", "fanout")
    t1 = MagicMock()
    t1.is_alive.return_value = False
    t2 = MagicMock()
    t2.is_alive.return_value = True
    t2.name = "t2"
    mgr.threads = [t1, t2]
    mgr.shutdown()
    t1.join.assert_called_once()
    t2.join.assert_called_once()

def test_send_exception_and_retry(monkeypatch):
    mgr = RabbitMQManager("h", 1, "u", "p", "fanout")
    q = Queue()
    q.put(b"msg")
    # Simulate connection error, then success
    call_count = {"count": 0}
    monkeypatch.setattr("time.sleep", lambda x: None)
    def conn_side_effect(*args, **kwargs):
        if call_count["count"] == 0:
            call_count["count"] += 1
            raise Exception("fail")
        class DummyConn:
            def channel(self):
                class DummyChan:
                    def exchange_declare(self, *a, **k): pass
                    def basic_publish(self, *a, **k): pass
                return DummyChan()
            def close(self):
                mgr.shutdown_event.set()  # trigger exit after success
        return DummyConn()
    monkeypatch.setattr("pika.BlockingConnection", conn_side_effect)
    mgr.send(q, "ex", "rk")
    assert q.empty()

def test_recv_exception_and_retry(monkeypatch):
    mgr = RabbitMQManager("h", 1, "u", "p", "fanout")
    q = Queue()
    # Simulate connection error, then success
    call_count = {"count": 0}
    monkeypatch.setattr("time.sleep", lambda x: None)
    def conn_side_effect(*args, **kwargs):
        if call_count["count"] == 0:
            call_count["count"] += 1
            raise Exception("fail")
        class DummyConn:
            def channel(self):
                class DummyChan:
                    def exchange_declare(self, *a, **k): pass
                    def queue_declare(self, *a, **k):
                        class DummyRes:
                            class method:
                                queue = "qname"
                        return DummyRes()
                    def queue_bind(self, *a, **k): pass
                    def basic_consume(self, *a, **k): pass
                    def start_consuming(self):
                        mgr.shutdown_event.set()
                return DummyChan()
            def close(self): pass
        return DummyConn()
    monkeypatch.setattr("pika.BlockingConnection", conn_side_effect)
    mgr.recv(q, "ex", "rk")

def test_callback_put_exception(monkeypatch):
    mgr = RabbitMQManager("h", 1, "u", "p", "fanout")
    q = MagicMock()
    def raise_exc(*args, **kwargs):
        raise Exception("put fail")
    q.put.side_effect = raise_exc
    # Patch pika.BlockingConnection to call callback directly
    class DummyChan:
        def exchange_declare(self, *a, **k): pass
        def queue_declare(self, *a, **k):
            class DummyRes:
                class method:
                    queue = "qname"
            return DummyRes()
        def queue_bind(self, *a, **k): pass
        def basic_consume(self, queue, on_message_callback, auto_ack):
            on_message_callback(None, None, None, b"msg")
        def start_consuming(self):
            mgr.shutdown_event.set()
    class DummyConn:
        def channel(self): return DummyChan()
        def close(self): pass
    monkeypatch.setattr("pika.BlockingConnection", lambda *a, **k: DummyConn())
    mgr.recv(q, "ex", "rk")
