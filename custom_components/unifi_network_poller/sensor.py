"""Example integration using DataUpdateCoordinator."""

import logging
import re
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfPower,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .models import MyOutletSensorEntityDescription, MySensorEntityDescription

_LOGGER = logging.getLogger(__name__)
OUTLET_NAME_REGEX = r"^.*-PS.$"


@callback
def async_client_device_info_fn(data: Any, mac: str) -> DeviceInfo:
    """Create device registry entry for client."""
    return DeviceInfo(
        identifiers={(DOMAIN, mac)},
        name=data["name"],
        manufacturer="Ubiquiti Networks",
        model=data["model"],
    )


@callback
def async_outlet_device_info_fn(udmpse_mac: str, name: str) -> DeviceInfo:
    """Create device registry entry for client."""
    identifier = f"{udmpse_mac}-Outlet-{name}"
    return DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name=name,
    )


@callback
def async_rx_rate_val_fn(data: Any, mac: str) -> float:
    """Calculate the asynchronous RX rate value based on the provided data and MAC address.

    Args:
        data (Any): The data containing the previous and current values.
        mac (str): The MAC address of the device.

    Returns:
        float: The calculated RX rate value.
    """
    if "prev_data" in data:
        prev_time = data["prev_data"]["time"]
        prev_rx = data["prev_data"][mac]["uplink"]["rx_bytes"]
        current_time = data["time"]
        current_rx = data[mac]["uplink"]["rx_bytes"]
        if current_rx < prev_rx:
            # counter reset
            prev_rx = 0
        return (current_rx - prev_rx) / (current_time - prev_time)
    else:
        return 0.0


@callback
def async_tx_rate_val_fn(data: Any, mac: str) -> float:
    """Calculate the asynchronous TX rate value based on the provided data and MAC address.

    Args:
        data (Any): The data containing the previous and current values.
        mac (str): The MAC address of the device.

    Returns:
        float: The calculated TX rate value.
    """
    if "prev_data" in data:
        prev_time = data["prev_data"]["time"]
        prev_tx = data["prev_data"][mac]["uplink"]["tx_bytes"]
        current_time = data["time"]
        current_tx = data[mac]["uplink"]["tx_bytes"]
        if current_tx < prev_tx:
            # counter reset
            prev_tx = 0
        return (current_tx - prev_tx) / (current_time - prev_time)
    else:
        return 0.0


GW_SENSORS: tuple[MySensorEntityDescription, ...] = (
    MySensorEntityDescription(
        key="Transfer sensor RX",
        device_class=SensorDeviceClass.DATA_SIZE,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfInformation.MEGABYTES,
        icon="mdi:upload",
        has_entity_name=True,
        device_info_fn=async_client_device_info_fn,
        name_fn=lambda: "RX",
        unique_id_fn=lambda mac: f"rx-{mac}",
        value_fn=lambda data, mac: data[mac]["uplink"]["rx_bytes"],
    ),
    MySensorEntityDescription(
        key="Transfer sensor TX",
        device_class=SensorDeviceClass.DATA_SIZE,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfInformation.MEGABYTES,
        icon="mdi:download",
        has_entity_name=True,
        device_info_fn=async_client_device_info_fn,
        name_fn=lambda: "TX",
        unique_id_fn=lambda mac: f"tx-{mac}",
        value_fn=lambda data, mac: data[mac]["uplink"]["tx_bytes"],
    ),
    MySensorEntityDescription(
        key="Transfer sensor RX Rate",
        device_class=SensorDeviceClass.DATA_RATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        icon="mdi:upload",
        has_entity_name=True,
        device_info_fn=async_client_device_info_fn,
        name_fn=lambda: "RX Rate",
        unique_id_fn=lambda mac: f"rx_rate-{mac}",
        value_fn=async_rx_rate_val_fn,
    ),
    MySensorEntityDescription(
        key="Transfer sensor TX Rate",
        device_class=SensorDeviceClass.DATA_RATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        icon="mdi:download",
        has_entity_name=True,
        device_info_fn=async_client_device_info_fn,
        name_fn=lambda: "TX Rate",
        unique_id_fn=lambda mac: f"tx_rate-{mac}",
        value_fn=async_tx_rate_val_fn,
    ),
)

PDU_SENSORS: tuple[MySensorEntityDescription, ...] = (
    MySensorEntityDescription(
        key="PDU Power Consumption",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=2,
        has_entity_name=True,
        device_info_fn=async_client_device_info_fn,
        name_fn=lambda: "AC Power Consumption",
        unique_id_fn=lambda mac: f"ac_power_consumption-{mac}",
        value_fn=lambda data, mac: data[mac]["outlet_ac_power_consumption"],
    ),
)

OUTLET_SENSORS: tuple[MyOutletSensorEntityDescription, ...] = (
    MyOutletSensorEntityDescription(
        key="Power Consumption",
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=2,
        has_entity_name=True,
        device_info_fn=async_outlet_device_info_fn,
        name_fn=lambda sensor: f"{sensor} AC Power Consumption",
        unique_id_fn=lambda mac,
        outlet_index: f"outlet_{outlet_index}_ac_power_consumption-{mac}",
        value_fn=lambda data: data.get("outlet_power", 0.0),
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Config entry example."""
    # assuming API object stored here by __init__.py
    unifiData = hass.data[DOMAIN][entry.entry_id]
    data = unifiData.coordinator.data
    udmpse_mac = next(
        mac for mac in unifiData.coordinator.macs if data[mac]["model"] == "UDMPROSE"
    )
    # lets get the gateway entities
    async_add_entities(
        MyEntity(unifiData.coordinator, mac, description)
        for mac in unifiData.coordinator.macs
        for description in GW_SENSORS
        if data[mac]["model"] in ["UDMPROSE"]
    )
    async_add_entities(
        MyEntity(unifiData.coordinator, mac, description)
        for mac in unifiData.coordinator.macs
        for description in PDU_SENSORS
        if data[mac]["model"] in ["USPPDUP"]
    )
    async_add_entities(
        MyOutletEntity(
            unifiData.coordinator, mac, udmpse_mac, outlet["index"], description
        )
        for mac in unifiData.coordinator.macs
        for outlet in unifiData.coordinator.data[mac]["outlet_table"]
        for description in OUTLET_SENSORS
        if unifiData.coordinator.data[mac]["model"] in ["USPPDUP"]
        and not outlet["name"].startswith("Outlet")
        and not outlet["name"].startswith("USB")
    )


class MyEntity(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity."""

    _attr_available = False
    _attr_has_entity_name = True

    def __init__(self, coordinator, mac, description):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=mac)
        data = coordinator.data[mac]
        self.mac = mac
        self.entity_description = description

        self._attr_available = False
        self._attr_device_info = description.device_info_fn(data, mac)
        self._attr_unique_id = description.unique_id_fn(mac)
        self._attr_name = description.name_fn()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        description = self.entity_description
        val = description.value_fn(self.coordinator.data, self.mac)
        if self._attr_available and self._attr_native_value == val:
            return
        self._attr_native_value = val
        self._attr_available = True
        self.async_write_ha_state()


class MyOutletEntity(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity."""

    _attr_available = False
    _attr_has_entity_name = True

    def __init__(self, coordinator, mac, udmpse_mac, outlet_index, description):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=mac)
        data = next(
            outlet
            for outlet in coordinator.data[mac]["outlet_table"]
            if outlet["index"] == outlet_index
        )
        if re.match(OUTLET_NAME_REGEX, data["name"]):
            self.name = data["name"].rsplit("-", 1)[0]
            self.port = data["name"].rsplit("-", 1)[1]
        else:
            self.name = data["name"]
            self.port = "PSU"

        self.mac = mac
        self.udmpse_mac = udmpse_mac
        self.outlet_index = outlet_index
        self.entity_description = description

        self._attr_available = False
        self._attr_device_info = description.device_info_fn(self.udmpse_mac, self.name)
        self._attr_unique_id = description.unique_id_fn(mac, self.outlet_index)
        self._attr_name = description.name_fn(self.port)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        description = self.entity_description
        data = next(
            outlet
            for outlet in self.coordinator.data[self.mac]["outlet_table"]
            if outlet["index"] == self.outlet_index
        )

        val = description.value_fn(data)
        if self._attr_available and self._attr_native_value == val:
            return
        self._attr_native_value = val
        self._attr_available = True
        self.async_write_ha_state()
