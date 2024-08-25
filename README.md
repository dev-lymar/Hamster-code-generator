# Hamster-code-generator

### Table of Contents
- [Project Description](#project-description)
- [Features](#Features)
- [Installation](#Installation)
- [Contributing](#contributing)
- [License](#license)


## Project Description
Hamster-Code-Generator is a bot designed to automatically farm promo codes for various games. 
The bot uses proxy servers to send requests to game APIs, saves the generated codes in a database, and provides them to users through a Telegram bot interface. 
The project utilizes aiogram for working with the Telegram API, asyncpg for PostgreSQL database interactions, and aiohttp for performing asynchronous HTTP requests.

## Features

### Farmer
- ***Promo Code Generation:*** The farmer automatically generates promo codes for games specified in the configuration.
- ***Error Handling:*** In case of errors during promo code generation, the farmer automatically restarts the process.
- ***Logging:*** All information about the generation process and errors is logged to a file.
- ***Database Interaction:*** Generated promo codes are stored in PostgreSQL.

### Bot
- ***Promo Code Distribution:*** Users can request promo codes through the Telegram bot.
- ***Language Switching:*** The bot supports multiple languages and allows users to change the interface language.
- ***Admin Notifications:*** The bot sends notifications to administrators, including error messages if there’s a failure in sending messages to the group.
- ***Limits and Waiting:*** The bot implements daily limits on promo code distribution and a mechanism for waiting between requests.

## Installation

### Requirements
- Python 3.10+
- PostgreSQL 16.3+
- Docker (for deployment using Docker Compose)

### Installing Dependencies
Install the required dependencies with:
```sh
pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file in the project root directory and fill it with the following parameters:
```sh
DATABASE_NAME=your_database_name
DATABASE_USER=your_database_user
DATABASE_PASSWORD=your_database_password
DATABASE_HOST=your_database_host
DATABASE_PORT=your_database_port

BOT_TOKEN=your_telegram_bot_token

GROUP_CHAT_ID=your_group_chat_id
```

### Running with Docker
1. Build and start the containers using Docker Compose:
```sh
docker-compose up -d
```
2. Apply migrations and set up the database:
```sh
docker-compose exec postgres psql -U $DATABASE_USER -d $DATABASE_NAME -f /path/to/migration.sql
```

### Running the Bot
After setting up the database and configuration, you can start the bot with Python:
```sh
python bot/main.py
```

### Running the Farmer
The farmer can be started as a separate process:
```sh
python bot/main.py
```

### Logging
Logs are saved in the `logs` directory. 
Log files are rotated when they reach 10 MB, with up to 5 backup copies retained.

## Project Structure
```commandline
.
├── LICENSE
├── README.md
├── alembic
├── app
│   ├── __init__.py
│   ├── game_promo_manager.py
│   ├── games.py
│   ├── logs
│   │  └── game_promo.log
│   ├── main.py
│   └── proxies.txt
├── bot
│   ├── config.py
│   ├── handlers.py
│   ├── main.py
│   └── utils
├── docker-compose.yml
└── requirements.txt
```
## Contributing
We welcome contributions to Hamster-code-generator. To contribute:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and commit them to your branch.
4. Update your branch from the main repository:
    ```sh
    git fetch upstream
    git merge upstream/main
    ```
5. Submit a pull request.

We will review your pull request and provide feedback as needed.

## License
This project is licensed under the MIT License. 
See the LICENSE file for more information.