from setuptools import setup, find_packages

setup(
    name='tnh-scholar',
    version='0.1',
    packages=find_packages(include=['data_processing', 'data_processing.*']),
    install_requires=[],  # Add any dependencies here
    entry_points={
        "console_scripts": [
            "audio-transcribe=CLI_tools.audio_transcribe.audio_transcribe:main",
        ],
    },
)