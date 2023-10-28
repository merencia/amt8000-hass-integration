"""Defines the sensors for amt-8000."""
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .isec2.client import Client as ISecClient

LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the entries for amt-8000."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = AmtCoordinator(hass, data["host"], data["port"], data["password"])
    await coordinator.async_config_entry_first_refresh()
    sensors = [AmtStatusSensor(coordinator), AmtFiringSensor(coordinator)]
    async_add_entities(sensors)


class AmtCoordinator(DataUpdateCoordinator):
    """Coordinate the amt status update."""

    def __init__(self, hass, host, port, password):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name="AMT-8000 Data Polling",
            update_interval=timedelta(seconds=10),
        )
        self.host = host
        self.port = port
        self.password = password

    async def _async_update_data(self):
        """Retrieve the current status."""
        LOGGER.info(f"retrieving amt-800 updated status at host: {self.host}:{self.port}...")
        isec_client = ISecClient(self.host, self.port)
        isec_client.connect()
        isec_client.auth(self.password)
        status = isec_client.status()
        LOGGER.info(f"AMT-8000 new state: {status}")
        isec_client.close()

        return status


class AmtStatusSensor(CoordinatorEntity, Entity):
    """Define a Status Sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.status = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the stored value on coordinator updates."""
        self.status = self.coordinator.data
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "AMT-8000 Status"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return "amt8000.status"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.status is not None

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        if self.status is None:
            return "unknown"

        return self.status["status"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state."""
        return self.status


class AmtFiringSensor(CoordinatorEntity, Entity):
    """Define a Firing Sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.status = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the stored value on coordinator updates."""
        self.status = self.coordinator.data
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "AMT-8000 Firing"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return "amt8000.firing"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.status is not None

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        if self.status is None:
            return "unknown"

        return self.status["zonesFiring"]
