# BetterCourtFinder
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)

An easier way to find badminton courts.
## Features
- Periodic fetching of badminton court availability using Better's official API
- Local storage and caching of court data to minimise API requests and reduce server load
- Telegram bot integration to deliver real-time court availability updates
- Hosting of an `.ics` calendar file through FastAPI for calendar app integration

## How to run
1. Clone the repository.
2. Copy .env.example to .env and add your Telegram API key from BotFather.
3. Run the setup and start script:
  ```
  ./run.sh
  ```
  This will create a Python virtual environment and install dependencies using uv if available (or fallback to pip).


4. The Telegram bot will start running and monitoring court availability. Use the Telegram client to interact with it.
5. (_Optional_) Add the `.ics` calendar URL served by the FastAPI server to your calendar app.
