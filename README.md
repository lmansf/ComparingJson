# Goals
To show the difference between storing data as json (string) vs broken out into string, int, and boolean.

# Performance Outcomes
- a 24% reduction from 0.22mb to 0.06mb in database size

## MySQL Script to Check Database size:
```
SELECT 
    table_schema AS riot_data3,
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'riot_data3';
```
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
