[![Python](https://img.shields.io/badge/Python-3.12.2-3776AB?style=flat&logo=Python&logoColor=yellow)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.3-336791?style=flat&logo=PostgreSQL&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.10.0-3776AB?style=flat&logo=telegram&logoColor=white")](https://aiogram.dev/)
[![Flake8](https://img.shields.io/badge/flake8-checked-blueviolet?style=flat)](https://flake8.pycqa.org/en/latest/)

# Hamster-code-generator

![Hamster code](./img/image.png)

## Table of Contents

- [Project Description](#project-description)
- [Features](#features)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Running with Docker](#running-with-docker)
- [Continuous Integration/Continuous Deployment (CI/CD)](#continuous-integrationcontinuous-deployment-cicd)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)


## Project Description
[Hamster-Code-Generator](https://t.me/hamster_keys_xbot) is a bot designed to automatically farm promo codes for various games. 
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

## Environment Configuration
Create a `.env` file in the project root directory based on the provided `.env.example` file. 
Fill it with the following parameters:
```plaintext
DATABASE_NAME=your_database_name
DATABASE_USER=your_database_user
DATABASE_PASSWORD=your_database_password
DATABASE_HOST=your_database_host
DATABASE_PORT=your_database_port

BOT_TOKEN=your_telegram_bot_token

GROUP_CHAT_ID=your_group_chat_id
```

## Running with Docker
1. Build and start the containers using Docker Compose:
```sh
docker-compose up -d postgres
```
2. Apply migrations and set up the database:
```sh
alembic upgrade head
```

### Running the Bot
After setting up the database and configuration, you can start the bot with Python:
```sh
python bot/main.py
```

### Running the Farmer
The farmer can be started as a separate process:
```sh
python app/main.py
```

### Logging
Logs are saved in the `logs` directory. 
Log files are rotated when they reach 10 MB, with up to 5 backup copies retained.

## Continuous Integration/Continuous Deployment (CI/CD)
The project includes **CI/CD** setup using **GitHub Actions**. 
The pipeline performs the following tasks:

- ***Linting:*** Ensures code quality by running Flake8 on each push.
- ***Build and Deploy:*** Deploys the application to a remote server when changes are pushed to the main branch.
- ***Release:*** Automatically creates a GitHub Release when a new version is tagged.

### Configuration
Make sure to configure the following ***GitHub Secrets*** for deployment:

- ***HOST:*** The remote server host.
- ***USERNAME:*** The SSH username.
- ***PORT:*** The SSH port.
- ***SSHKEY:*** The private SSH key for connecting to the remote server.


## Project Structure
```commandline
.
├── .env.example
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