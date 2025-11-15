from mavsdk import System
import asyncio

class MAVSDKClient:
    def __init__(self):
        self.drone = System()

    async def connect(self):
        await self.drone.connect(system_address="udp://:14540")

    async def arm(self):
        await self.drone.action.arm()

    async def takeoff(self):
        await self.drone.action.takeoff()

    async def land(self):
        await self.drone.action.land()
