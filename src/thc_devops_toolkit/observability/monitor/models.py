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
"""Data models for monitoring system and processes."""

import socket
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import psutil


class Unit(str, Enum):
    """Enumeration of measurement units for data size and transfer rates."""

    BYTES = "B"
    KILOBYTES = "KB"
    MEGABYTES = "MB"
    GIGABYTES = "GB"
    MBPS = "MBps"
    GBPS = "GBps"

    @property
    def factor(self) -> float:
        """Get the conversion factor for the unit."""
        if self in {Unit.MBPS, Unit.GBPS}:
            return {
                Unit.MBPS: 1024 * 1024,
                Unit.GBPS: 1024 * 1024 * 1024,
            }[self]

        return {
            Unit.BYTES: 1,
            Unit.KILOBYTES: 1024,
            Unit.MEGABYTES: 1024 * 1024,
            Unit.GIGABYTES: 1024 * 1024 * 1024,
        }[self]


@dataclass
class NetworkInterface:
    """Represents a network interface on the system.

    Attributes:
        name (str): The name of the network interface.
    """

    name: str

    @classmethod
    def from_network_interface(cls, net_iface: str) -> "NetworkInterface":
        """Create a NetworkInterface instance from a network interface name.

        Args:
            net_iface (str): The name of the network interface.

        Returns:
            NetworkInterface: An instance representing the specified network interface.

        Raises:
            ValueError: If the specified network interface does not exist.
        """
        if net_iface in psutil.net_if_addrs():
            return cls(name=net_iface)

        raise ValueError(f"Network interface {net_iface} not found.")

    @classmethod
    def from_ip_address(cls, ip_addr: str) -> "NetworkInterface":
        """Create a NetworkInterface instance from an IP address.

        Args:
            ip_addr (str): The IP address associated with the network interface.

        Returns:
            NetworkInterface: An instance representing the network interface with the specified IP address.

        Raises:
            ValueError: If no network interface is found with the specified IP address.
        """
        for net_iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family in (socket.AF_INET, socket.AF_INET6) and addr.address.split("%")[0] == ip_addr:
                    return cls(name=net_iface)

        raise ValueError(f"No network interface found with IP address {ip_addr}.")


@dataclass
class NetworkInterfaceStatus:
    """Represents the status of a network interface.

    Attributes:
        inbound_rate (float): The inbound data transfer rate.
        outbound_rate (float): The outbound data transfer rate.
        net_unit (Unit): The unit of measurement for the data transfer rates.
        timestamp (str): The timestamp of the status measurement.
    """

    inbound_rate: float = 0.0
    outbound_rate: float = 0.0
    unit: Unit = Unit.MBPS
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class GPUStatus:  # pylint: disable=too-many-instance-attributes
    """Represents the status of a GPU device.

    Attributes:
        model (str): The model name of the GPU.
        index (int): The index of the GPU device.
        uuid (str): The UUID of the GPU device.
        utilization (float): The GPU utilization percentage.
        memory_used (float): The amount of GPU memory used.
        memory_total (float): The total amount of GPU memory.
        memory_unit (Unit): The unit of measurement for the GPU memory.
        timestamp (str): The timestamp of the status measurement.
    """

    model: str = ""
    index: int = -1  # unassigned
    uuid: str = ""
    utilization: float = 0.0
    memory_used: float = 0.0
    memory_total: float = 0.0
    memory_unit: Unit = Unit.MEGABYTES
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class ProcessStatus:
    """Represents the status of a system process.

    Attributes:
        cpu_usage (float): The CPU usage percentage of the process.
        memory_used (float): The amount of memory used by the process.
        memory_total (float): The total amount of memory available to the process.
        memory_unit (Unit): The unit of measurement for the memory.
        timestamp (str): The timestamp of the status measurement.
    """

    cpu_usage: float = 0.0
    memory_used: float = 0.0
    memory_total: float = 0.0
    memory_unit: Unit = Unit.MEGABYTES
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class SystemStatus:  # pylint: disable=too-many-instance-attributes
    """Represents the overall status of the system.

    Attributes:
        cpu_usage (float): The overall CPU usage percentage of the system.
        memory_used (float): The amount of memory used by the system.
        memory_total (float): The total amount of memory available on the system.
        memory_unit (Unit): The unit of measurement for the memory.
        disk_used (float): The amount of disk space used on the system.
        disk_total (float): The total amount of disk space available on the system.
        disk_unit (Unit): The unit of measurement for the disk space.
        timestamp (str): The timestamp of the status measurement.
    """

    cpu_usage: float = 0.0
    memory_used: float = 0.0
    memory_total: float = 0.0
    memory_unit: Unit = Unit.MEGABYTES
    disk_used: float = 0.0
    disk_total: float = 0.0
    disk_unit: Unit = Unit.GIGABYTES
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
