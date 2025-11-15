# connect_test.py
import asyncio
from mavsdk import System

async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")

    print("Arming...")
    await drone.action.arm()

    print("Taking off...")
    await drone.action.takeoff()

    await asyncio.sleep(5)

    print("Landing...")
    await drone.action.land()

asyncio.run(run())
