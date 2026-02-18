# Riot API Project Setup

## Prerequisites

1.  **Python 3.11+**: Ensure Python is installed.
2.  **MySQL Server**: This project requires a running MySQL server.
    *   Default configuration:
        *   Host: `localhost`
        *   User: `root`
        *   Password: `""` (empty string)
        *   Database: `riot_data` (will be created automatically)
    *   If your configuration differs, update the `.env` file.

## Setup

1.  **Install Dependencies**:
    Dependencies are already installed in the `.venv` virtual environment.

2.  **Configuration (.env)**:
    Open `.env` and verify:
    *   `RIOT_API_KEY`: Your RGAPI key from [developer.riotgames.com](https://developer.riotgames.com/).
    *   `TARGET_GAME_NAME` / `TARGET_TAG_LINE`: The account you want to look up.
    *   Database settings (`DB_HOST`, `DB_USER`, `DB_PASSWORD`) if needed.

3.  **Initialize Database**:
    Run the setup script to create the database and table:
    ```bash
    python setup_db.py
    ```

## Usage

Run the main script to fetch data:
```bash
python main.py
```
