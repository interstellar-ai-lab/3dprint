import asyncio

from manager import CadManager


async def main() -> None:
    query = input("What would you like to generate? ")
    print(query)
    await CadManager().run(query)


if __name__ == "__main__":
    asyncio.run(main())
