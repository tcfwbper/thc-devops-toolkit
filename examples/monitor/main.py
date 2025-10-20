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
from pathlib import Path

import psutil

from thc_devops_toolkit.observability import logger
from thc_devops_toolkit.observability.monitor import Monitor, NetworkInterface


def main() -> None:
    monitor = Monitor()
    net_iface = NetworkInterface.from_ip_address("127.0.0.1")
    pid = psutil.Process().pid

    logger.info("Start monitoring...")

    monitor.monitor_net_iface(net_iface=net_iface)
    monitor.monitor_process(pid=pid)
    monitor.monitor_system()
    monitor.monitor_gpu()

    time.sleep(60)
    monitor.shutdown()

    logger.info("Monitoring stopped.")


if __name__ == "__main__":
    main()
