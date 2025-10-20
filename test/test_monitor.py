import socket
from unittest.mock import Mock, patch, call

import pytest

from thc_devops_toolkit.observability.monitor import (
    Monitor,
    Unit,
    NetworkInterface,
    NetworkInterfaceStatus,
    ProcessStatus,
    GPUStatus,
    SystemStatus,
)


# Tests for models.py
class TestUnit:
    """Test Unit enum functionality."""
    
    def test_unit_values(self):
        """Test unit enum values."""
        assert Unit.BYTES.value == "B"
        assert Unit.KILOBYTES.value == "KB" 
        assert Unit.MEGABYTES.value == "MB"
        assert Unit.GIGABYTES.value == "GB"
        assert Unit.MBPS.value == "MBps"
        assert Unit.GBPS.value == "GBps"
    
    def test_unit_factors(self):
        """Test unit conversion factors."""
        assert Unit.BYTES.factor == 1
        assert Unit.KILOBYTES.factor == 1024
        assert Unit.MEGABYTES.factor == 1024 * 1024
        assert Unit.GIGABYTES.factor == 1024 * 1024 * 1024
        assert Unit.MBPS.factor == 1024 * 1024
        assert Unit.GBPS.factor == 1024 * 1024 * 1024


class TestNetworkInterface:
    """Test NetworkInterface class functionality."""
    
    @patch("psutil.net_if_addrs")
    def test_from_network_interface_success(self, mock_net_if_addrs):
        """Test successful creation from network interface name."""
        mock_net_if_addrs.return_value = {"eth0": [], "lo": []}
        
        net_iface = NetworkInterface.from_network_interface("eth0")
        assert net_iface.name == "eth0"
    
    @patch("psutil.net_if_addrs")
    def test_from_network_interface_not_found(self, mock_net_if_addrs):
        """Test creation from non-existent network interface."""
        mock_net_if_addrs.return_value = {"eth0": []}
        
        with pytest.raises(ValueError, match="Network interface invalid not found"):
            NetworkInterface.from_network_interface("invalid")
    
    @patch("psutil.net_if_addrs")
    def test_from_ip_address_success(self, mock_net_if_addrs):
        """Test successful creation from IP address."""
        mock_addr = Mock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "192.168.1.1"
        
        mock_net_if_addrs.return_value = {
            "eth0": [mock_addr],
            "lo": []
        }
        
        net_iface = NetworkInterface.from_ip_address("192.168.1.1")
        assert net_iface.name == "eth0"
    
    @patch("psutil.net_if_addrs")
    def test_from_ip_address_with_zone_identifier(self, mock_net_if_addrs):
        """Test creation from IP address with zone identifier."""
        mock_addr = Mock()
        mock_addr.family = socket.AF_INET6
        mock_addr.address = "fe80::1%eth0"
        
        mock_net_if_addrs.return_value = {
            "eth0": [mock_addr]
        }
        
        net_iface = NetworkInterface.from_ip_address("fe80::1")
        assert net_iface.name == "eth0"
    
    @patch("psutil.net_if_addrs")
    def test_from_ip_address_not_found(self, mock_net_if_addrs):
        """Test creation from non-existent IP address."""
        mock_net_if_addrs.return_value = {"eth0": []}
        
        with pytest.raises(ValueError, match="No network interface found with IP address"):
            NetworkInterface.from_ip_address("192.168.1.99")


class TestDataClasses:
    """Test data class functionality."""
    
    def test_network_interface_status_defaults(self):
        """Test NetworkInterfaceStatus default values."""
        status = NetworkInterfaceStatus()
        assert status.inbound_rate == 0.0
        assert status.outbound_rate == 0.0
        assert status.unit == Unit.MBPS
        assert isinstance(status.timestamp, str)
    
    def test_network_interface_status_custom_values(self):
        """Test NetworkInterfaceStatus with custom values."""
        status = NetworkInterfaceStatus(
            inbound_rate=10.5,
            outbound_rate=5.2,
            unit=Unit.GBPS,
            timestamp="2023-01-01 12:00:00"
        )
        assert status.inbound_rate == 10.5
        assert status.outbound_rate == 5.2
        assert status.unit == Unit.GBPS
        assert status.timestamp == "2023-01-01 12:00:00"
    
    def test_gpu_status_defaults(self):
        """Test GPUStatus default values."""
        status = GPUStatus()
        assert status.model == ""
        assert status.index == -1
        assert status.uuid == ""
        assert status.utilization == 0.0
        assert status.memory_used == 0.0
        assert status.memory_total == 0.0
        assert status.memory_unit == Unit.MEGABYTES
        assert isinstance(status.timestamp, str)
    
    def test_process_status_defaults(self):
        """Test ProcessStatus default values."""
        status = ProcessStatus()
        assert status.cpu_usage == 0.0
        assert status.memory_used == 0.0
        assert status.memory_total == 0.0
        assert status.memory_unit == Unit.MEGABYTES
        assert isinstance(status.timestamp, str)
    
    def test_system_status_defaults(self):
        """Test SystemStatus default values."""
        status = SystemStatus()
        assert status.cpu_usage == 0.0
        assert status.memory_used == 0.0
        assert status.memory_total == 0.0
        assert status.memory_unit == Unit.MEGABYTES
        assert status.disk_used == 0.0
        assert status.disk_total == 0.0
        assert status.disk_unit == Unit.GIGABYTES
        assert isinstance(status.timestamp, str)


# Tests for monitor.py
class TestMonitor:
    """Test Monitor class functionality."""
    
    def test_monitor_init(self):
        """Test Monitor initialization."""
        monitor = Monitor()
        assert monitor.pids == []
        assert monitor.net_ifaces == []
        assert monitor.gpu_monitoring_enabled is False
        assert monitor.system_monitoring_enabled is False
        assert monitor.threads == []
        assert monitor.shutdown_event.is_set() is False
    
    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_net_iface_success(self, mock_thread_class):
        """Test successful network interface monitoring setup."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        monitor = Monitor()
        net_iface = NetworkInterface(name="eth0")
        
        monitor.monitor_net_iface(net_iface)
        
        # Verify that the interface name is tracked
        assert "eth0" in monitor.net_ifaces
        # Verify thread was created and started
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        assert mock_thread in monitor.threads

    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_net_iface_duplicate(self, mock_thread_class):
        """Test monitoring already monitored network interface."""
        monitor = Monitor()
        monitor.net_ifaces = ["eth0"]
        net_iface = NetworkInterface(name="eth0")
        
        monitor.monitor_net_iface(net_iface)
        
        # Verify interface is still in the list only once
        assert monitor.net_ifaces.count("eth0") == 1
        # Verify no thread was created for duplicate
        mock_thread_class.assert_not_called()

    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_net_iface_custom_params(self, mock_thread_class):
        """Test network interface monitoring with custom parameters."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        monitor = Monitor()
        net_iface = NetworkInterface(name="eth0")
        
        monitor.monitor_net_iface(net_iface, interval=5.0, unit=Unit.GBPS, precision=2, retry=5)
        
        # Verify thread was created with correct arguments
        mock_thread_class.assert_called_once_with(
            target=monitor._monitor_net_iface,
            args=(net_iface, 5.0, Unit.GBPS, 2, 5),
            daemon=True
        )

    @patch("psutil.net_io_counters")
    @patch("time.sleep")
    def test_monitor_net_iface_internal_success(self, mock_sleep, mock_net_io):
        """Test internal network interface monitoring success."""
        monitor = Monitor()
        net_iface = NetworkInterface(name="eth0")
        
        # Mock network statistics
        mock_stat_1 = Mock()
        mock_stat_1.bytes_recv = 1000
        mock_stat_1.bytes_sent = 500
        
        mock_stat_2 = Mock()
        mock_stat_2.bytes_recv = 2000
        mock_stat_2.bytes_sent = 1000
        
        mock_net_io.side_effect = [
            {"eth0": mock_stat_1},
            {"eth0": mock_stat_2}
        ]
        
        # Set shutdown after first iteration
        def set_shutdown(*args):
            monitor.shutdown_event.set()
        
        mock_sleep.side_effect = set_shutdown
        
        monitor._monitor_net_iface(net_iface, interval=1.0)

    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_process_success(self, mock_thread_class):
        """Test successful process monitoring setup."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        monitor = Monitor()
        pid = 1234
        
        monitor.monitor_process(pid)
        
        assert pid in monitor.pids
        # Verify thread was created and started
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        assert mock_thread in monitor.threads
    
    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_process_duplicate(self, mock_thread_class):
        """Test monitoring already monitored process."""
        monitor = Monitor()
        monitor.pids = [1234]
        
        monitor.monitor_process(1234)

        assert monitor.pids.count(1234) == 1
        # Verify no thread was created for duplicate
        mock_thread_class.assert_not_called()

    @patch("psutil.Process")
    @patch("psutil.virtual_memory")
    @patch("time.sleep")
    def test_monitor_process_internal_success(self, mock_sleep, mock_virtual_memory, mock_process_class):
        """Test internal process monitoring success."""
        monitor = Monitor()
        pid = 1234
        
        # Mock process and memory info
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 25.5
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process
        
        mock_vm = Mock()
        mock_vm.total = 1024 * 1024 * 1024 * 8  # 8GB
        mock_virtual_memory.return_value = mock_vm
        
        # Set shutdown after first iteration
        def set_shutdown(*args):
            monitor.shutdown_event.set()
        
        mock_sleep.side_effect = set_shutdown
        
        monitor._monitor_process(pid, interval=1.0)
        
        # Verify calls
        mock_process_class.assert_called_with(pid)

    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_system_success(self, mock_thread_class):
        """Test successful system monitoring setup."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        monitor = Monitor()
        
        monitor.monitor_system()
        
        assert monitor.system_monitoring_enabled is True
        # Verify thread was created and started
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        assert mock_thread in monitor.threads

    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_system_duplicate(self, mock_thread_class):
        """Test monitoring system when already enabled."""
        monitor = Monitor()
        monitor.system_monitoring_enabled = True
        
        monitor.monitor_system()
        
        # Verify no thread was created for duplicate
        mock_thread_class.assert_not_called()

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("time.sleep")
    def test_monitor_system_internal_success(self, mock_sleep, mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        """Test internal system monitoring success."""
        monitor = Monitor()
        
        # Mock system stats
        mock_cpu_percent.return_value = 45.2
        
        mock_memory = Mock()
        mock_memory.used = 1024 * 1024 * 1024 * 4  # 4GB
        mock_memory.total = 1024 * 1024 * 1024 * 8  # 8GB
        mock_virtual_memory.return_value = mock_memory
        
        mock_disk = Mock()
        mock_disk.used = 1024 * 1024 * 1024 * 100  # 100GB
        mock_disk.total = 1024 * 1024 * 1024 * 500  # 500GB
        mock_disk_usage.return_value = mock_disk
        
        # Set shutdown after first iteration
        def set_shutdown(*args):
            monitor.shutdown_event.set()
        
        mock_sleep.side_effect = set_shutdown
        
        monitor._monitor_system(interval=1.0)
        
        # Verify calls
        mock_cpu_percent.assert_called()
        mock_virtual_memory.assert_called()
        mock_disk_usage.assert_called_with("/")

    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_gpu_success(self, mock_thread_class):
        """Test successful GPU monitoring setup."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        monitor = Monitor()
        
        monitor.monitor_gpu()
        
        assert monitor.gpu_monitoring_enabled is True
        # Verify thread was created and started
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        assert mock_thread in monitor.threads

    @patch("thc_devops_toolkit.observability.monitor.monitor.Thread")
    def test_monitor_gpu_duplicate(self, mock_thread_class):
        """Test monitoring GPU when already enabled."""
        monitor = Monitor()
        monitor.gpu_monitoring_enabled = True
        
        monitor.monitor_gpu()
        
        # Verify no thread was created for duplicate
        mock_thread_class.assert_not_called()

    @patch("pynvml.nvmlInit")
    def test_monitor_gpu_internal_nvml_init_failure(self, mock_nvml_init):
        """Test GPU monitoring when NVML initialization fails."""
        monitor = Monitor()
        mock_nvml_init.side_effect = Exception("NVML init failed")
        
        monitor._monitor_gpu()

    @patch("pynvml.nvmlInit")
    @patch("pynvml.nvmlDeviceGetCount")
    @patch("pynvml.nvmlDeviceGetHandleByIndex")
    @patch("pynvml.nvmlDeviceGetMemoryInfo")
    @patch("pynvml.nvmlDeviceGetName")
    @patch("pynvml.nvmlDeviceGetUUID")
    @patch("pynvml.nvmlDeviceGetUtilizationRates")
    @patch("time.sleep")
    def test_monitor_gpu_internal_success(self, mock_sleep, mock_util_rates, mock_uuid, mock_name, 
                                        mock_memory_info, mock_handle, mock_device_count, mock_nvml_init):
        """Test internal GPU monitoring success."""
        monitor = Monitor()
        
        # Mock NVML functions
        mock_device_count.return_value = 1
        mock_handle_obj = Mock()
        mock_handle.return_value = mock_handle_obj
        
        mock_memory = Mock()
        mock_memory.used = 1024 * 1024 * 2048  # 2GB
        mock_memory.total = 1024 * 1024 * 8192  # 8GB
        mock_memory_info.return_value = mock_memory
        
        mock_name.return_value = b"GeForce RTX 3080"
        mock_uuid.return_value = b"GPU-12345678"
        
        mock_rates = Mock()
        mock_rates.gpu = 75.5
        mock_util_rates.return_value = mock_rates
        
        # Set shutdown after first iteration
        def set_shutdown(*args):
            monitor.shutdown_event.set()
        
        mock_sleep.side_effect = set_shutdown
        
        monitor._monitor_gpu(interval=1.0)
        
        # Verify calls
        mock_nvml_init.assert_called_once()
        mock_device_count.assert_called()
        mock_handle.assert_called_with(0)

    def test_monitor_net_iface_internal_exception_retry(self):
        """Test network interface monitoring exception handling and retry."""
        monitor = Monitor()
        net_iface = NetworkInterface(name="eth0")
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:  # Fail 3 times to trigger retry limit
                monitor.shutdown_event.set()
            raise Exception("Network error")
        
        with patch("psutil.net_io_counters", side_effect=side_effect):
            monitor._monitor_net_iface(net_iface, retry=3)

    @patch("psutil.Process")
    def test_monitor_process_internal_exception_retry(self, mock_process_class):
        """Test process monitoring exception handling and retry."""
        monitor = Monitor()
        pid = 1234
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                monitor.shutdown_event.set()
            raise Exception("Process error")
        
        mock_process_class.side_effect = side_effect
        
        monitor._monitor_process(pid, retry=3)

    @patch("psutil.cpu_percent")
    def test_monitor_system_internal_exception_retry(self, mock_cpu_percent):
        """Test system monitoring exception handling and retry."""
        monitor = Monitor()
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                monitor.shutdown_event.set()
            raise Exception("System error")
        
        mock_cpu_percent.side_effect = side_effect
        
        monitor._monitor_system(retry=3)

    @patch("pynvml.nvmlInit")
    @patch("pynvml.nvmlDeviceGetCount")
    def test_monitor_gpu_internal_exception_retry(self, mock_device_count, mock_nvml_init):
        """Test GPU monitoring exception handling and retry."""
        monitor = Monitor()
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                monitor.shutdown_event.set()
            raise Exception("GPU error")
        
        mock_device_count.side_effect = side_effect
        
        monitor._monitor_gpu(retry=3)
    
    def test_shutdown(self):
        """Test monitor shutdown functionality."""
        monitor = Monitor()
        
        # Mock threads
        mock_thread1 = Mock()
        mock_thread1.is_alive.return_value = False
        mock_thread1.name = "thread1"
        
        mock_thread2 = Mock()
        mock_thread2.is_alive.return_value = True
        mock_thread2.name = "thread2"
        
        monitor.threads = [mock_thread1, mock_thread2]

        monitor.shutdown()
        
        assert monitor.shutdown_event.is_set()
        mock_thread1.join.assert_called_with(timeout=15.0)
        mock_thread2.join.assert_called_with(timeout=15.0)

    def test_shutdown_with_hanging_thread(self):
        """Test shutdown with thread that doesn't stop within timeout."""
        monitor = Monitor()
        
        # Mock thread that doesn't stop
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        mock_thread.name = "hanging_thread"
        
        monitor.threads = [mock_thread]

        monitor.shutdown()
        
        assert monitor.shutdown_event.is_set()
        mock_thread.join.assert_called_with(timeout=15.0)
