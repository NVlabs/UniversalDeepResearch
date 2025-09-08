# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#!/usr/bin/env python3
"""
Setup script for the Universal Deep Research Backend (UDR-B).

This script helps users configure the backend by:
1. Creating necessary directories
2. Setting up environment configuration
3. Validating API key files
4. Installing dependencies
"""

import os
import subprocess
import sys
from pathlib import Path


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_step(step: str):
    """Print a step message."""
    print(f"\n→ {step}")


def check_python_version():
    """Check if Python version is compatible."""
    print_step("Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def create_directories():
    """Create necessary directories."""
    print_step("Creating directories...")
    directories = ["logs", "instances", "mock_instances"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_env_file():
    """Set up environment configuration file."""
    print_step("Setting up environment configuration...")

    env_file = Path(".env")
    env_example = Path("env.example")

    if env_file.exists():
        print("✅ .env file already exists")
        return

    if env_example.exists():
        # Copy example file
        with open(env_example, "r") as f:
            content = f.read()

        with open(env_file, "w") as f:
            f.write(content)

        print("✅ Created .env file from env.example")
        print("⚠️  Please edit .env file with your configuration")
    else:
        print("❌ env.example file not found")
        print("Creating basic .env file...")

        basic_env = """# Universal Deep Research Backend (UDR-B) - Environment Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
FRONTEND_URL=http://localhost:3000
DEFAULT_MODEL=moonshotai/kimi-k2-instruct-0905
LLM_API_KEY_FILE=groq_api.txt
TAVILY_API_KEY_FILE=tavily_api.txt
MAX_TOPICS=1
MAX_SEARCH_PHRASES=1
LOG_DIR=logs
"""
        with open(env_file, "w") as f:
            f.write(basic_env)

        print("✅ Created basic .env file")
        print("⚠️  Please edit .env file with your configuration")


def check_api_keys():
    """Check for required API key files."""
    print_step("Checking API key files...")

    required_files = ["groq_api.txt", "tavily_api.txt"]

    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)

    if missing_files:
        print(f"\n⚠️  Missing API key files: {', '.join(missing_files)}")
        print("Please create these files with your API keys:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nExample:")
        print("  echo 'your-api-key-here' > nvdev_api.txt")
        print("  echo 'your-tavily-key-here' > tavily_api.txt")


def install_dependencies():
    """Install Python dependencies."""
    print_step("Installing dependencies...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True,
        )
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please run: pip install -r requirements.txt")


def validate_setup():
    """Validate the setup."""
    print_step("Validating setup...")

    # Check if main modules can be imported
    try:
        import clients
        import config
        import main
        import scan_research

        print("✅ All modules can be imported")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Check if directories exist
    required_dirs = ["logs", "instances"]
    for directory in required_dirs:
        if not Path(directory).exists():
            print(f"❌ Directory missing: {directory}")
            return False

    print("✅ Setup validation passed")
    return True


def main():
    """Main setup function."""
    print_header("Universal Deep Research Backend (UDR-B) Setup")

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    check_python_version()
    create_directories()
    setup_env_file()
    check_api_keys()
    install_dependencies()

    if validate_setup():
        print_header("Setup Complete!")
        print("🎉 Your Universal Deep Research Backend (UDR-B) is ready!")
        print("\nNext steps:")
        print("1. Edit .env file with your configuration")
        print("2. Create API key files (nvdev_api.txt, tavily_api.txt)")
        print("3. Run: ./launch_server.sh")
        print("4. Or run: uvicorn main:app --reload")
        print("\nFor more information, see README.md")
    else:
        print_header("Setup Failed")
        print("❌ Please fix the issues above and run setup again")


if __name__ == "__main__":
    main()
