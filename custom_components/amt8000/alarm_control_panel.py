"""Defines the sensors for amt-8000."""
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)


from .const import DOMAIN
from .coordinator import AmtCoordinator
from .isec2.client import Client as ISecClient


LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the entries for amt-8000."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    isec_client = ISecClient(data["host"], data["port"])
    coordinator = AmtCoordinator(hass, isec_client, data["password"])
    await coordinator.async_config_entry_first_refresh()
    sensors = [AmtAlarmPanel(coordinator, isec_client, data['password'])]
    async_add_entities(sensors)


class AmtAlarmPanel(CoordinatorEntity, AlarmControlPanelEntity):
    """Define a Amt Alarm Panel."""

    _attr_supported_features = (
          AlarmControlPanelEntityFeature.ARM_AWAY
        # | AlarmControlPanelEntityFeature.ARM_NIGHT
        # | AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.TRIGGER
    )

    def __init__(self, coordinator, isec_client: ISecClient, password):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.status = None
        self.isec_client = isec_client
        self.password = password

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the stored value on coordinator updates."""
        self.status = self.coordinator.data
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "AMT-8000"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return "amt8000.control_panel"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.status is not None

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        if self.status is None:
            return "unknown"

        if self.status['siren'] == True:
            return "triggered"

        return self.status["status"]

    def _arm_away(self):
        """Arm AMT in away mode"""
        self.isec_client.connect()
        self.isec_client.auth(self.password)
        result = self.isec_client.arm_system(0)
        self.isec_client.close()
        if result == "armed":
            return 'armed_away'

    def _disarm(self):
        """Arm AMT in away mode"""
        self.isec_client.connect()
        self.isec_client.auth(self.password)
        result = self.isec_client.disarm_system(0)
        self.isec_client.close()
        if result == "disarmed":
            return 'disarmed'


    def _trigger_alarm(self):
        """Trigger Alarm"""
        self.isec_client.connect()
        self.isec_client.auth(self.password)
        result = self.isec_client.panic(1)
        self.isec_client.close()
        if result == "triggered":
            return "triggered"


    def alarm_disarm(self, code=None) -> None:
        """Send disarm command."""
        self._disarm()

    async def async_alarm_disarm(self, code=None) -> None:
        """Send disarm command."""
        self._disarm()

    def alarm_arm_away(self, code=None) -> None:
        """Send arm away command."""
        self._arm_away()

    async def async_alarm_arm_away(self, code=None) -> None:
        """Send arm away command."""
        self._arm_away()

    def alarm_trigger(self, code=None) -> None:
        """Send alarm trigger command."""
        self._trigger_alarm()

    async def async_alarm_trigger(self, code=None) -> None:
        """Send alarm trigger command."""
        self._trigger_alarm()

