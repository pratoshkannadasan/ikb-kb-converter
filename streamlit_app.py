#!/usr/bin/env python3
"""
Frontend launcher for the Document Conversion Pipeline.
"""

import os
import subprocess
import sys
from pathlib import Path


SHORT_PIP_TEMP = Path("C:/temp/pip-build")
REQUIREMENTS_FILE = Path("requirements.txt")
REQUIRED_IMPORTS = {
    "streamlit": "streamlit>=1.42,<2",
    "watchdog": "watchdog>=6.0.0",
    "docx": "python-docx==0.8.11",
    "dotenv": "python-dotenv==1.0.0",
    "PyPDF2": "PyPDF2==3.0.1",
    "pdfplumber": "pdfplumber==0.11.4",
    "openai": "openai>=1.97.1",
    "yaml": "pyyaml==6.0.1",
    "tqdm": "tqdm==4.66.1",
    "colorama": "colorama==0.4.6",
    "markdown": "markdown==3.5.1",
}


def get_package_name(requirement):
    """Extract the importable package name from a pip requirement specifier."""
    for separator in ("==", ">=", "<=", "!=", "~=", "<", ">"):
        requirement = requirement.split(separator)[0]
    return requirement.strip()


def build_install_environment():
    """Use a short temp path to avoid Windows path length issues during pip builds."""
    env = os.environ.copy()
    SHORT_PIP_TEMP.mkdir(parents=True, exist_ok=True)
    short_temp = str(SHORT_PIP_TEMP)
    env["TMP"] = short_temp
    env["TEMP"] = short_temp
    env["PIP_NO_INPUT"] = "1"
    return env


def check_and_install_requirements():
    """Check if required packages are installed and install missing ones."""
    missing_packages = []

    print("Checking frontend dependencies...")

    for package_name, requirement in REQUIRED_IMPORTS.items():
        try:
            __import__(package_name)
            print(f"[ok] {package_name} is installed")
        except ImportError:
            missing_packages.append(requirement)
            print(f"[missing] {package_name} is missing")

    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        try:
            install_command = [sys.executable, "-m", "pip", "install", "--prefer-binary"]
            if REQUIREMENTS_FILE.exists():
                install_command += ["-r", str(REQUIREMENTS_FILE)]
            else:
                install_command += missing_packages

            subprocess.check_call(install_command, env=build_install_environment())
            print("[ok] All packages installed successfully")
        except subprocess.CalledProcessError as exc:
            print(f"[error] Failed to install packages: {exc}")
            print(
                'Please install manually using: '
                'pip install --prefer-binary -r requirements.txt'
            )
            return False

    return True


def check_main_pipeline():
    """Check if the main pipeline can be imported."""
    try:
        sys.path.insert(0, str(Path.cwd()))
        import main  # noqa: F401

        print("[ok] Main pipeline is available")
        return True
    except ImportError as exc:
        print(f"[warn] Could not import main pipeline: {exc}")
        print("Make sure you're running this from the project root directory")
        return False


def start_streamlit():
    """Start the Streamlit application."""
    frontend_path = Path("frontend/app.py")

    if not frontend_path.exists():
        print(f"[error] Frontend app not found at: {frontend_path}")
        return False

    print("\nStarting Document Conversion Pipeline Frontend...")
    print("=" * 60)
    print("The web interface will open in your browser at:")
    print("http://localhost:8501")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print()

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(frontend_path),
                "--server.headless=false",
            ],
            check=False,
        )
    except KeyboardInterrupt:
        print("\nFrontend stopped by user")
    except Exception as exc:
        print(f"[error] Error starting frontend: {exc}")
        return False

    return True


def main():
    """Main launcher function."""
    print("Document Conversion Pipeline - Frontend Launcher")
    print("=" * 55)

    if not Path("main.py").exists():
        print("[error] main.py not found in current directory")
        print("Please run this script from the project root directory")
        return False

    if not check_and_install_requirements():
        return False

    check_main_pipeline()
    return start_streamlit()


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nLauncher stopped by user")
        sys.exit(0)
    except Exception as exc:
        print(f"[error] Unexpected error: {exc}")
        sys.exit(1)
