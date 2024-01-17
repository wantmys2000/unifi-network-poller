"""Module-level docstring describing the purpose of the module."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pyunifi.controller import Controller

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


@dataclass
class BetterUnifiData:
    """Data for the Unifi Network Poller integration."""

    coordinator: DataUpdateCoordinator
    api: Controller


@dataclass(frozen=True)
class MyDescriptions:
    device_info_fn: Callable[[Any, str], DeviceInfo | None]
    name_fn: Callable[[], str | None]
    value_fn: Callable[[Any, str], float | str | None]
    unique_id_fn: Callable[[str], str]


@dataclass(frozen=True)
class MyOutletDescriptions:
    device_info_fn: Callable[[str, str], DeviceInfo | None]
    name_fn: Callable[[str], str | None]
    value_fn: Callable[[Any], float | str | None]
    unique_id_fn: Callable[[str, int], str]


@dataclass(frozen=True)
class MySensorEntityDescription(SensorEntityDescription, MyDescriptions):
    """Class describing UniFi sensor entity."""


@dataclass(frozen=True)
class MyOutletSensorEntityDescription(SensorEntityDescription, MyOutletDescriptions):
    """Class describing UniFi sensor entity."""
