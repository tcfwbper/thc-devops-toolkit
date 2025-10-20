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
"""Monitoring utilities for system and process metrics."""

import time
from datetime import datetime
from threading import Event, Thread

import psutil
import pynvml

from thc_devops_toolkit.observability.logger import LogLevel, logger
from thc_devops_toolkit.observability.monitor.models import (
    GPUStatus,
    NetworkInterface,
    NetworkInterfaceStatus,
    ProcessStatus,
    SystemStatus,
    Unit,
)


class Monitor:
    """A class to monitor system and process metrics."""

    def __init__(self) -> None:
        """Initializes the Monitor class."""
        self.pids: list[int] = []
        self.net_ifaces: list[str] = []
        self.gpu_monitoring_enabled: bool = False
        self.system_monitoring_enabled: bool = False
        self.threads: list[Thread] = []
        self.shutdown_event = Event()

    def monitor_net_iface(  # pylint: disable=too-many-arguments
        self,
        net_iface: NetworkInterface,
        interval: float = 10.0,
        unit: Unit = Unit.MBPS,
        precision: int = 3,
        retry: int = 3,
    ) -> None:
        """Monitors a specific network interface.

        Args:
            net_iface (NetworkInterface): The network interface to monitor.
            interval (float): The interval in seconds between measurements.
            unit (Unit): The unit for measuring data transfer rates.
            precision (int): The number of decimal places for the measurements.
            retry (int): The number of retries on failure before stopping monitoring.
        """
        if net_iface.name in self.net_ifaces:
            logger.warning("[Monitor] Network interface %s is already being monitored.", net_iface.name)
            return

        self.net_ifaces.append(net_iface.name)
        thread = Thread(target=self._monitor_net_iface, args=(net_iface, interval, unit, precision, retry), daemon=True)
        thread.start()
        self.threads.append(thread)

    def _monitor_net_iface(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        net_iface: NetworkInterface,
        interval: float = 10.0,
        unit: Unit = Unit.MBPS,
        precision: int = 3,
        retry: int = 3,
    ) -> None:
        """Monitors the specified network interface at regular intervals.

        Args:
            net_iface (NetworkInterface): The network interface to monitor.
            interval (float): The interval in seconds between measurements.
            unit (Unit): The unit for measuring data transfer rates.
            precision (int): The number of decimal places for the measurements.
            retry (int): The number of retries on failure before stopping monitoring.
        """
        failure_count = 0
        while not self.shutdown_event.is_set():
            try:
                logger.info("[Monitor] Measuring network interface %s statistics...", net_iface.name)
                start_time = datetime.now()

                net_stat = psutil.net_io_counters(pernic=True, nowrap=True)[net_iface.name]
                inbound_1 = net_stat.bytes_recv
                outbound_1 = net_stat.bytes_sent

                time.sleep(1)

                net_stat = psutil.net_io_counters(pernic=True, nowrap=True)[net_iface.name]
                inbound_2 = net_stat.bytes_recv
                outbound_2 = net_stat.bytes_sent

                end_time = datetime.now()
                logger.info("[Monitor] Successfully measured network interface %s statistics.", net_iface.name)

                net_status = NetworkInterfaceStatus(
                    inbound_rate=round((inbound_2 - inbound_1) / unit.factor, precision),
                    outbound_rate=round((outbound_2 - outbound_1) / unit.factor, precision),
                    unit=unit,
                    timestamp=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                )
                logger.highlight(level=LogLevel.INFO, message=f"[Monitor] Network Interface {net_iface.name} status: {net_status}")
                failure_count = 0
                time.sleep(interval - (end_time - start_time).total_seconds())
            except Exception as exception:  # pylint: disable=broad-except
                logger.highlight(
                    level=LogLevel.ERROR,
                    message=f"[Monitor] Error monitoring network interface {net_iface.name}: {exception}",
                )
                failure_count += 1
                if failure_count >= retry:
                    logger.highlight(
                        level=LogLevel.ERROR,
                        message=f"[Monitor] Stopping monitoring for network interface {net_iface.name} after multiple failures.",
                    )
                    break

    def monitor_process(  # pylint: disable=too-many-arguments
        self,
        pid: int,
        interval: float = 10.0,
        memory_unit: Unit = Unit.MEGABYTES,
        precision: int = 3,
        retry: int = 3,
    ) -> None:
        """Monitors a specific process.

        Args:
            pid (int): The process ID to monitor.
            interval (float): The interval in seconds between measurements.
            memory_unit (Unit): The unit for measuring memory usage.
            precision (int): The number of decimal places for the measurements.
            retry (int): The number of retries on failure before stopping monitoring.
        """
        if pid in self.pids:
            logger.warning("[Monitor] Process %d is already being monitored.", pid)
            return

        self.pids.append(pid)
        thread = Thread(target=self._monitor_process, args=(pid, interval, memory_unit, precision, retry), daemon=True)
        thread.start()
        self.threads.append(thread)

    def _monitor_process(  # pylint: disable=too-many-arguments
        self,
        pid: int,
        interval: float = 10.0,
        memory_unit: Unit = Unit.MEGABYTES,
        precision: int = 3,
        retry: int = 3,
    ) -> None:
        """Monitors the specified network interface at regular intervals.

        Args:
            pid (int): The process ID to monitor.
            interval (float): The interval in seconds between measurements.
            memory_unit (Unit): The unit for measuring memory usage.
            precision (int): The number of decimal places for the measurements.
            retry (int): The number of retries on failure before stopping monitoring.
        """
        failure_count = 0
        while not self.shutdown_event.is_set():
            try:
                logger.info("[Monitor] Measuring process %d statistics...", pid)
                start_time = datetime.now()

                process = psutil.Process(pid)
                memory_info = process.memory_info()

                process_status = ProcessStatus(
                    cpu_usage=round(process.cpu_percent(), precision),
                    memory_used=round(memory_info.rss / memory_unit.factor, precision),
                    memory_total=round(psutil.virtual_memory().total / memory_unit.factor, precision),
                    memory_unit=memory_unit,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                logger.highlight(level=LogLevel.INFO, message=f"[Monitor] Process {pid} status: {process_status}")

                end_time = datetime.now()
                logger.info("[Monitor] Successfully measured process %d statistics.", pid)

                failure_count = 0
                time.sleep(interval - (end_time - start_time).total_seconds())
            except Exception as exception:  # pylint: disable=broad-except
                logger.highlight(level=LogLevel.ERROR, message=f"[Monitor] Error monitoring process {pid}: {exception}")
                failure_count += 1
                if failure_count >= retry:
                    logger.highlight(
                        level=LogLevel.ERROR,
                        message=f"[Monitor] Stopping monitoring for process {pid} after multiple failures.",
                    )
                    break

    def monitor_system(  # pylint: disable=too-many-arguments
        self,
        interval: float = 10.0,
        memory_unit: Unit = Unit.MEGABYTES,
        disk_unit: Unit = Unit.GIGABYTES,
        precision: int = 3,
        retry: int = 3,
    ) -> None:
        """Monitors system metrics.

        Args:
            interval (float): The interval in seconds between measurements.
            memory_unit (Unit): The unit for measuring memory usage.
            disk_unit (Unit): The unit for measuring disk usage.
            precision (int): The number of decimal places for the measurements.
            retry (int): The number of retries on failure before stopping monitoring.
        """
        if self.system_monitoring_enabled:
            logger.warning("[Monitor] System monitoring is already enabled.")
            return

        self.system_monitoring_enabled = True
        thread = Thread(target=self._monitor_system, args=(interval, memory_unit, disk_unit, precision, retry), daemon=True)
        thread.start()
        self.threads.append(thread)

    def _monitor_system(  # pylint: disable=too-many-arguments
        self,
        interval: float = 10.0,
        memory_unit: Unit = Unit.MEGABYTES,
        disk_unit: Unit = Unit.GIGABYTES,
        precision: int = 3,
        retry: int = 3,
    ) -> None:
        """Monitors the system at regular intervals.

        Args:
            interval (float): The interval in seconds between measurements.
            memory_unit (Unit): The unit for measuring memory usage.
            disk_unit (Unit): The unit for measuring disk usage.
            precision (int): The number of decimal places for the measurements.
            retry (int): The number of retries on failure before stopping monitoring.
        """
        failure_count = 0
        while not self.shutdown_event.is_set():
            try:
                logger.info("[Monitor] Measuring system statistics...")
                start_time = datetime.now()

                memory_info = psutil.virtual_memory()
                disk_info = psutil.disk_usage("/")

                system_status = SystemStatus(
                    cpu_usage=round(psutil.cpu_percent(), precision),
                    memory_used=round(memory_info.used / memory_unit.factor, precision),
                    memory_total=round(memory_info.total / memory_unit.factor, precision),
                    memory_unit=memory_unit,
                    disk_used=round(disk_info.used / disk_unit.factor, precision),
                    disk_total=round(disk_info.total / disk_unit.factor, precision),
                    disk_unit=disk_unit,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                logger.highlight(level=LogLevel.INFO, message=f"[Monitor] System status: {system_status}")

                end_time = datetime.now()
                logger.info("[Monitor] Successfully measured system statistics.")

                failure_count = 0
                time.sleep(interval - (end_time - start_time).total_seconds())
            except Exception as exception:  # pylint: disable=broad-except
                logger.highlight(level=LogLevel.ERROR, message=f"[Monitor] Error monitoring system: {exception}")
                failure_count += 1
                if failure_count >= retry:
                    logger.highlight(level=LogLevel.ERROR, message="[Monitor] Stopping system monitoring after multiple failures")
                    break

    def monitor_gpu(
        self,
        interval: float = 10.0,
        memory_unit: Unit = Unit.MEGABYTES,
        precision: int = 3,
        retry: int = 3,
    ) -> None:
        """Monitors GPU metrics.

        Args:
            interval (float): The interval in seconds between measurements.
            memory_unit (Unit): The unit for measuring GPU memory usage.
            precision (int): The number of decimal places for the measurements.
            retry (int): The number of retries on failure before stopping monitoring.
        """
        if self.gpu_monitoring_enabled:
            logger.warning("[Monitor] GPU monitoring is already enabled.")
            return

        self.gpu_monitoring_enabled = True
        thread = Thread(target=self._monitor_gpu, args=(interval, memory_unit, precision, retry), daemon=True)
        thread.start()
        self.threads.append(thread)

    def _monitor_gpu(
        self,
        interval: float = 10.0,
        memory_unit: Unit = Unit.MEGABYTES,
        precision: int = 3,
        retry: int = 3,
    ) -> None:
        """Monitors the GPU at regular intervals.

        Args:
            interval (float): The interval in seconds between measurements.
            memory_unit (Unit): The unit for measuring GPU memory usage.
            precision (int): The number of decimal places for the measurements.
            retry (int): The number of retries on failure before stopping monitoring.
        """
        try:
            pynvml.nvmlInit()
        except Exception as exception:  # pylint: disable=broad-except
            logger.highlight(level=LogLevel.ERROR, message=f"[Monitor] Failed to initialize NVML for GPU monitoring: {exception}")
            return

        failure_count = 0
        while not self.shutdown_event.is_set():
            try:
                logger.info("[Monitor] Measuring GPU statistics...")
                start_time = datetime.now()

                for gpu_idx in range(pynvml.nvmlDeviceGetCount()):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_idx)
                    gpu_meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)

                    gpu_status = GPUStatus(
                        model=str(pynvml.nvmlDeviceGetName(handle)),
                        index=gpu_idx,
                        uuid=str(pynvml.nvmlDeviceGetUUID(handle)),
                        utilization=round(pynvml.nvmlDeviceGetUtilizationRates(handle).gpu, precision),
                        memory_used=round(gpu_meminfo.used / memory_unit.factor, precision),
                        memory_total=round(gpu_meminfo.total / memory_unit.factor, precision),
                        memory_unit=memory_unit,
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    logger.highlight(level=LogLevel.INFO, message=f"[Monitor] GPU status: {gpu_status}")

                end_time = datetime.now()
                logger.info("[Monitor] Successfully measured GPU statistics.")

                failure_count = 0
                time.sleep(interval - (end_time - start_time).total_seconds())
            except Exception as exception:  # pylint: disable=broad-except
                logger.highlight(level=LogLevel.ERROR, message=f"[Monitor] Error monitoring GPU: {exception}")
                failure_count += 1
                if failure_count >= retry:
                    logger.highlight(level=LogLevel.ERROR, message="[Monitor] Stopping GPU monitoring after multiple failures.")
                    break

    def shutdown(self) -> None:
        """Gracefully shuts down the Monitor and all threads."""
        logger.info("[Monitor] Graceful shutdown...")
        self.shutdown_event.set()

        # Wait for all threads to finish with a reasonable timeout
        for thread in self.threads:
            thread.join(timeout=15.0)
            if thread.is_alive():
                logger.highlight(
                    level=LogLevel.WARNING,
                    message=f"[Monitor] Thread {thread.name} did not stop within timeout",
                )

        logger.info("[Monitor] Graceful shutdown completed")
