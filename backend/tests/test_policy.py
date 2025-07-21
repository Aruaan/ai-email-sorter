import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("Set event loop policy to WindowsSelectorEventLoopPolicy")
    loop = asyncio.get_event_loop()
    print("Event loop type:", type(loop))
    asyncio.set_event_loop(loop)
else:
    print("Not on Windows")

import subprocess
print("Trying to launch subprocess...")
subprocess.run(["python", "--version"])
