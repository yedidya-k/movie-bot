# Movie Bot

A Telegram-based CLI tool for searching and downloading movies through bridge bots.

## How It Works

1. You send a movie name to configured Telegram groups
2. Bridge bots in those groups respond with available options
3. You select an option and the bot sends you the file
4. Movie Bot downloads it to your machine

## Requirements

- Python 3.11+
- Telegram API credentials ([my.telegram.org](https://my.telegram.org))
- Access to a Telegram group with a bridge bot

## Setup

### Linux / macOS

```bash
# Clone and enter the directory
git clone https://github.com/yedidya-k/movie-bot
cd movie-bot

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run setup (creates .env with your credentials)
chmod +x setup.sh
./setup.sh
```

### Windows

```powershell
# Clone and enter the directory
git clone https://github.com/yedidya-k/movie-bot
cd movie-bot

# Create virtual environment and install dependencies
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Copy and edit the .env file manually
copy .env.example .env
notepad .env
```

Or manually create a `.env` file:

```
DOWNLOAD_PATH=./downloads/
GROUP_IDS=-1001111111111,-1002222222222
BRIDGE_GROUP_ID=-1003333333333
BRIDGE_BOTS=@ExampleBot

API_ID=12345
API_HASH=your_api_hash
PHONE_NUMBER=+1234567890
```

## Usage

### Linux / macOS

```bash
source venv/bin/activate
python main.py
```

### Windows

```powershell
.\venv\Scripts\activate
python main.py
```

Enter a movie name when prompted, select an option, and the file will be downloaded.

The session is saved so you only need to authenticate via Telegram once. The first run will prompt for a verification code sent to your Telegram account.

## Configuration

| Variable | Description |
|---|---|
| `DOWNLOAD_PATH` | Where downloaded files are saved (default: `./downloads/`) |
| `GROUP_IDS` | Comma-separated group IDs to send search queries to |
| `BRIDGE_GROUP_ID` | Optional — additional group for bridge bot responses |
| `BRIDGE_BOTS` | Comma-separated bot usernames (with @) that provide movie links |
| `API_ID` | Telegram API ID from my.telegram.org |
| `API_HASH` | Telegram API hash from my.telegram.org |
| `PHONE_NUMBER` | Your phone number (international format) |

## License

MIT
