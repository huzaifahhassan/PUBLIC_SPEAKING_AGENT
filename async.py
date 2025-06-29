import asyncio
import time

async def boil():
    print("Start boil")
    await asyncio.sleep(10)
    print("boiled")

async def chop_veggies():
    print("Start chop")
    await asyncio.sleep(10)
    print("chopped")

async def garnish():
    print("Start garnish")
    await asyncio.sleep(10)
    print("done")

# main async function
async def main():

    ### TRADITIONAL APPROACH (SLOWER)
    # cooking a recipe
    # await boil()
    # await chop_veggies()
    # await garnish()

    ### CONCURRENT RUN FASTER
    #await asyncio.gather(boil(), chop_veggies(), garnish())

    ### ALSO CONCURRENT RUN FASTER
    boiling = asyncio.create_task(boil())
    chopping = asyncio.create_task(chop_veggies())
    garnishing = asyncio.create_task(garnish())

    await boiling
    await chopping
    await garnishing


asyncio.run(main())