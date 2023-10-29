from datetime import timedelta

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .isec2.client import Client as ISecClient

import logging

LOGGER = logging.getLogger(__name__)

class AmtCoordinator(DataUpdateCoordinator):
    """Coordinate the amt status update."""

    def __init__(self, hass, isec_client: ISecClient, password):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name="AMT-8000 Data Polling",
            update_interval=timedelta(seconds=10),
        )
        self.isec_client = isec_client
        self.password = password

    async def _async_update_data(self):
        """Retrieve the current status."""
        LOGGER.info("retrieving amt-8000 updated status...")
        self.isec_client.connect()
        self.isec_client.auth(self.password)
        status = self.isec_client.status()
        LOGGER.info(f"AMT-8000 new state: {status}")
        self.isec_client.close()

        return status