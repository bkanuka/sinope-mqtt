from setuptools import setup
from sinope_mqtt import __version__,\
    __author__,\
    __email__,\
    __license__,\
    __description__

setup(
    name="sinope_mqtt",
    version=__version__,
    url='',
    license=__license__,
    author=__author__,
    author_email=__email__,
    description=__description__,
    install_requires=['sinopey', 'paho-mqtt', 'requests'],
    scripts=['sinope_mqtt.py'],
    entry_points={
        'console_scripts': ['sinope_mqtt = sinope_mqtt:main']
    }
)