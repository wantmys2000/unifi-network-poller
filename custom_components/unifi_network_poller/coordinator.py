"""Example integration using DataUpdateCoordinator."""

from datetime import timedelta
import logging
import time

import async_timeout
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyunifi.controller import APIError, Controller

_LOGGER = logging.getLogger(__name__)


class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, my_api, macs):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Unifi Protect Data",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=60),
        )
        self.my_api = my_api
        self.macs = macs

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                # return await self.my_api.fetch_data(listening_idx)
                data_val = {}
                data_val["time"] = time.monotonic()
                for mac in self.macs:
                    data_val[mac] = await self.hass.async_add_executor_job(
                        self.my_api.get_device_stat, mac
                    )
                if self.data:
                    data_val["prev_data"] = {
                        k: v for k, v in self.data.items() if k not in {"prev_data"}
                    }
                return data_val
        except APIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except KeyError as err:
            try:
                await self.hass.async_add_executor_job(self.my_api._login)
            except APIError as inner_err:
                raise UpdateFailed(
                    f"Error communicating with API: {inner_err}"
                ) from inner_err
            else:
                raise UpdateFailed(f"Need to Relogin: {err}") from err
