from datetime import timedelta, datetime

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
        self.next_update = datetime.now()
        self.stored_status = None
        self.attemt = 0

    async def _async_update_data(self):
        """Retrieve the current status."""
        self.attemt += 1

        if(datetime.now() < self.next_update):
           return self.stored_status

        try:
          LOGGER.info("retrieving amt-8000 updated status...")
          self.isec_client.connect()
          self.isec_client.auth(self.password)
          status = self.isec_client.status()
          LOGGER.info(f"AMT-8000 new state: {status}")
          self.isec_client.close()

          self.stored_status = status
          self.attemt = 0
          self.next_update = datetime.now()

          return status
        except Exception as e:
          print(f"Coordinator update error: {e}")
          seconds = 2 ** self.attemt
          time_difference = timedelta(seconds=seconds)
          self.next_update = datetime.now() + time_difference
          print(f"Next retry after {self.next_update}")

        finally:
           self.isec_client.close()