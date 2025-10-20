from unittest.mock import MagicMock, patch
from queue import Queue
from thc_devops_toolkit.infrastructure.rabbitmq import RabbitMQManager, RabbitMQActions, RabbitMQConfig

def test_rabbitmq_manager_init():
    mgr = RabbitMQManager()
    assert isinstance(mgr.senders, dict)
    assert isinstance(mgr.receivers, dict)
    assert isinstance(mgr.threads, list)
    assert mgr.shutdown_event.is_set() is False

def test_register_sender_receiver():
    mgr = RabbitMQManager()
    config = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_key",
        tls=False
    )
    
    # sender
    assert mgr.register(RabbitMQActions.SEND, config) is True
    assert mgr.register(RabbitMQActions.SEND, config) is False  # duplicate
    
    # receiver
    config2 = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user", 
        password="pass",
        exchange_name="test_exchange2",
        exchange_type="direct",
        routing_key="test_key2",
        tls=False
    )
    assert mgr.register(RabbitMQActions.RECV, config2) is True
    
    # invalid - empty exchange name
    config_invalid = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass", 
        exchange_name="",
        exchange_type="direct",
        routing_key="test_key",
        tls=False
    )
    assert mgr.register(RabbitMQActions.SEND, config_invalid) is False
    
    # invalid - empty routing key
    config_invalid2 = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct", 
        routing_key="",
        tls=False
    )
    assert mgr.register(RabbitMQActions.SEND, config_invalid2) is False
    
    # invalid - None message_queue
    config_invalid3 = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_key", 
        tls=False
    )
    config_invalid3.message_queue = None
    assert mgr.register(RabbitMQActions.SEND, config_invalid3) is False

def test_register_invalid_action():
    mgr = RabbitMQManager()
    config = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_key",
        tls=False
    )
    
    class DummyAction:
        pass
    assert mgr.register(DummyAction(), config) is False

def test_run_starts_threads():
    mgr = RabbitMQManager()
    config1 = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass", 
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_key",
        tls=False
    )
    config2 = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange2", 
        exchange_type="direct",
        routing_key="test_key2",
        tls=False
    )
    
    mgr.register(RabbitMQActions.SEND, config1)
    mgr.register(RabbitMQActions.RECV, config2)
    
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
    mgr = RabbitMQManager()
    config = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_key",
        tls=False
    )
    
    # Patch pika.BlockingConnection and related methods
    with patch("thc_devops_toolkit.infrastructure.rabbitmq.pika.BlockingConnection") as conn_mock:
        conn = MagicMock()
        conn_mock.return_value = conn
        channel = MagicMock()
        conn.channel.return_value = channel
        channel.exchange_declare.return_value = None
        channel.basic_publish.return_value = None
        
        # Put a message in queue
        config.message_queue.put(b"msg")
        
        # Set shutdown after one send
        def shutdown_after_send(*args, **kwargs):
            mgr.shutdown_event.set()
        channel.basic_publish.side_effect = shutdown_after_send
        
        mgr.send(config)
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
        
        mgr.recv(config)
        channel.exchange_declare.assert_called()
        channel.queue_declare.assert_called()
        channel.queue_bind.assert_called()
        channel.basic_consume.assert_called()
        channel.start_consuming.assert_called()

def test_shutdown_joins_threads():
    mgr = RabbitMQManager()
    t1 = MagicMock()
    t1.is_alive.return_value = False
    t2 = MagicMock()
    t2.is_alive.return_value = True
    t2.name = "t2"
    mgr.threads = [t1, t2]
    
    # Mock receiver configs with channels
    config1 = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_key",
        tls=False
    )
    config1.channel = MagicMock()
    mgr.receivers = {"test": config1}
    
    mgr.shutdown()
    t1.join.assert_called_once()
    t2.join.assert_called_once()
    config1.channel.stop_consuming.assert_called_once()

def test_send_exception_and_retry(monkeypatch):
    mgr = RabbitMQManager()
    config = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user", 
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_key",
        tls=False
    )
    config.message_queue.put(b"msg")
    
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
    
    monkeypatch.setattr("thc_devops_toolkit.infrastructure.rabbitmq.pika.BlockingConnection", conn_side_effect)
    mgr.send(config)
    assert config.message_queue.empty()

def test_recv_exception_and_retry(monkeypatch):
    mgr = RabbitMQManager()
    config = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct",
        routing_key="test_key",
        tls=False
    )
    
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
    
    monkeypatch.setattr("thc_devops_toolkit.infrastructure.rabbitmq.pika.BlockingConnection", conn_side_effect)
    mgr.recv(config)

def test_callback_put_exception(monkeypatch):
    mgr = RabbitMQManager()
    config = RabbitMQConfig(
        host="localhost",
        port=5672,
        user="user",
        password="pass",
        exchange_name="test_exchange",
        exchange_type="direct", 
        routing_key="test_key",
        tls=False
    )
    
    # Mock the message_queue to raise exception on put
    config.message_queue = MagicMock()
    def raise_exc(*args, **kwargs):
        raise Exception("put fail")
    config.message_queue.put.side_effect = raise_exc
    
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
    
    monkeypatch.setattr("thc_devops_toolkit.infrastructure.rabbitmq.pika.BlockingConnection", lambda *a, **k: DummyConn())
    mgr.recv(config)
