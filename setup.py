"""
CyberSentinel - Ethical Keystroke Monitoring Suite
Setup configuration for package installation.
"""

from setuptools import setup, find_packages

setup(
    name="cybersentinel",
    version="1.0.0",
    author="CyberSecurity Research Team",
    description="Ethical keystroke monitoring suite for cybersecurity research",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pynput>=1.7.7",
        "cryptography>=42.0.0",
        "rich>=13.9.0",
        "pyperclip>=1.9.0",
        "Pillow>=10.4.0",
        "psutil>=6.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cybersentinel=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Topic :: Security",
        "Programming Language :: Python :: 3.9",
    ],
)
