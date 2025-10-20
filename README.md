# thc-devops-toolkit

[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](#)
[![Python](https://img.shields.io/badge/Python-3670A0?logo=python&logoColor=ffdd54)](#)
[![DevOps](https://img.shields.io/badge/DevOps-009999)](#)
[![DevOps](https://img.shields.io/badge/MLOps-fc411c)](#)
[![GitHub](https://img.shields.io/badge/GitHub-%23121011.svg?logo=github&logoColor=white)](https://github.com/tcfwbper?tab=repositories)
[![LinkedIn](https://custom-icon-badges.demolab.com/badge/LinkedIn-0A66C2?logo=linkedin-white&logoColor=fff)](https://www.linkedin.com/in/tsung-han-chang-31748b318/)

thc-devops-toolkit is a toolkit designed to simplify DevOps workflows, providing automation scripts and utilities to help developers and operations teams improve efficiency.

## Features
- Includes various built-in tools
- Easily extensible and customizable

## Installation
```bash
git clone https://github.com/tcfwbper/thc-devops-toolkit.git
cd thc-devops-toolkit
bash dev/venv-create.sh <your_venv version>
source .venv/bin/activate
bash dev/bootstrap.sh
```

## Usage
Refer to `examples` for each tool.

## Project Structure
```
thc-devops-toolkit/
├── dev/           # Scripts for development
├── examples/      # Demonstrate how to use this toolkit
├── src/           # Main code and utility scripts
│   ├── ...        # Sub-tools and modules
├── test/          # Test files
├── pyproject.toml # Project configuration
├── README.md      # Project documentation
```

## Contributing
Feel free to submit issues or pull requests to help improve this toolkit.

Please pass all the tests before submit your contribution.
```bash
bash dev/format-and-test.sh
```
