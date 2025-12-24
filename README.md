I'll update the README.md to reflect the new modular structure and provide complete setup instructions. Here's the updated README.md:

README.md:

```markdown
<h2 align="center">
    ──「 SEQUENCE BOT 」──
</h2>

<p align="center">
  <img src="https://i.rj1.dev/aNWlA.png">
</p>

<p align="center">
<a href="https://github.com/RioShin2025/SequenceBot/stargazers"><img src="https://img.shields.io/github/stars/RioShin2025/SequenceBot?color=black&logo=github&logoColor=black&style=for-the-badge" alt="Stars" /></a>
<a href="https://github.com/RioShin2025/SequenceBot/network/members"> <img src="https://img.shields.io/github/forks/RioShin2025/SequenceBot?color=black&logo=github&logoColor=black&style=for-the-badge" /></a>
<a href="https://github.com/RioShin2025/SequenceBot/blob/RioShin/LICENSE"> <img src="https://img.shields.io/badge/License-MIT-blueviolet?style=for-the-badge" alt="License" /> </a>
<a href="https://www.python.org/"> <img src="https://img.shields.io/badge/Written%20in-Python-orange?style=for-the-badge&logo=python" alt="Python" /> </a>
<a href="https://github.com/RioShin2025/SequenceBot/commits/RioShin2025"> <img src="https://img.shields.io/github/last-commit/RioShin2025/SequenceBot?color=blue&logo=github&logoColor=green&style=for-the-badge" /></a>
</p>

<p align="center">
<b>📦 MODULAR ARCHITECTURE</b>
</p>

<h3 align="center">
    ──「 NEW FOLDER STRUCTURE 」──
</h3>

```

sequence-bot/
├──main.py                 # Main bot entry point
├──config.py               # Configuration settings
├──webserver.py           # Flask web server for hosting
├──database.py            # MongoDB database operations
├──requirements.txt       # Python dependencies
├──app.json              # Deployment configuration
├──README.md             # This documentation
│
├──handlers/              # Command handlers
│├── init.py
│├── start_handler.py      # /start, /fileseq commands
│├── sequence_handler.py   # /sequence, file processing
│├── ls_handler.py         # /ls command for channel sequencing
│└── admin_handler.py      # /broadcast, /status commands
│
├──callbacks/             # Callback query handlers
│├── init.py
│├── main_callbacks.py     # Main button callbacks
│└── ls_callbacks.py       # LS mode callbacks
│
└──utils/                 # Utility functions
├── init.py
├── fsub_checker.py       # Force subscribe checker
├── file_parser.py        # File name parser
├── link_extractor.py     # Telegram link extractor
└── admin_checker.py      # Admin permission checker

```

## ✨ FEATURES

### 📁 File Sequencing
- **Automatic Numbering**: Numbers files sequentially (001, 002, 003...)
- **Multiple Modes**: Episode flow & Quality flow sequencing
- **Smart Parsing**: Extracts season, episode, quality from filenames
- **Channel Support**: Sequence files directly from Telegram channels

### 👥 User Management
- **Leaderboard**: Track top users by files sequenced
- **User Stats**: Count files processed per user
- **Broadcast System**: Send messages to all users
- **Force Subscribe**: Require users to join channels

### 🔗 Channel Sequencing (New!)
- **/ls Command**: Sequence files between two message links
- **Direct to Chat**: Send sequenced files to your chat
- **Back to Channel**: Send sequenced files back to original channel
- **Admin Check**: Automatically verifies bot permissions

### ⚙️ Admin Tools
- **Broadcast Messages**: Send to all users instantly
- **Bot Status**: Check uptime, ping, and user count
- **Force Subscribe**: Multiple channel support
- **Modular Design**: Easy to extend and customize

## 🚀 DEPLOYMENT METHODS

<h3 align="center">
    ──「 DEPLOY ON RENDER/KOYEB/RAILWAY 」──
</h3>

### Method 1: Direct Deployment
1. Fork this repository
2. Go to your chosen hosting platform (Render/Koyeb/Railway)
3. Create a new web service
4. Connect your GitHub repository
5. Set environment variables (see below)
6. Deploy!

### Method 2: Manual Setup
```bash
# Clone the repository
git clone https://github.com/RioShin2025/SequenceBot.git
cd SequenceBot

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp config.py.example config.py
# Edit config.py with your credentials

# Run the bot
python3 main.py
# OR run with web server
python3 webserver.py
```

<h3 align="center">
    ──「 DEPLOY ON HEROKU 」──
</h3>

<p align="center"><a href="https://dashboard.heroku.com/new?template=https://github.com/RioShin/SequenceBot"> <img src="https://img.shields.io/badge/Deploy%20On%20Heroku-black?style=for-the-badge&logo=heroku" width="220" height="38.45"/></a></p>

<h3 align="center">
    ──「 DEPLOY ON VPS/LOCAL 」──
</h3>

Step-by-Step VPS Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Git
sudo apt install python3 python3-pip git -y

# Clone repository
git clone https://github.com/RioShin2025/SequenceBot.git
cd SequenceBot

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure the bot
nano config.py
# Add your API credentials

# Run the bot
python3 main.py
# OR run with PM2 for persistence
pm2 start main.py --name sequence-bot
pm2 save
pm2 startup
```

⚙️ CONFIGURATION

1. Get API Credentials

1. Go to my.telegram.org
2. Create a new application
3. Get API_ID and API_HASH

2. Get Bot Token

1. Message @BotFather on Telegram
2. Create a new bot with /newbot
3. Get your BOT_TOKEN

3. Get MongoDB URI

1. Go to MongoDB Atlas
2. Create a free cluster
3. Get your connection string
4. Replace password and database name

4. Edit config.py

```python
API_ID = 12345678                    # From my.telegram.org
API_HASH = "your_api_hash_here"     # From my.telegram.org
BOT_TOKEN = "your_bot_token_here"   # From @BotFather
MONGO_URI = "mongodb+srv://..."     # From MongoDB Atlas
START_PIC = "https://..."           # Bot start image URL
OWNER_ID = 1234567890               # Your Telegram ID

# Force Subscribe Channels (set to 0 to disable)
FSUB_CHANNEL = -1001234567890
FSUB_CHANNEL_2 = -1009876543210
FSUB_CHANNEL_3 = 0

# Custom Messages
START_MSG = """Your custom start message here"""
HELP_TXT = """Your custom help message here"""
COMMAND_TXT = """Your commands list here"""
```

📋 COMMANDS

User Commands

```
/start - Start the bot
/fileseq - Choose file ordering mode
/sequence - Start file sequencing mode
/ls - Sequence files from channel links (range selection)
/leaderboard - View top users
```

Admin Commands (Owner Only)

```
/broadcast - Send message to all users (reply to message)
/status - Check bot status and statistics
```

🔧 CUSTOMIZATION

Adding New Commands

1. Create a new file in handlers/ folder
2. Import necessary modules
3. Define your command handler
4. Register it in handlers/__init__.py

Example: Adding /help Command

```python
# handlers/help_handler.py
from pyrogram import filters

def register_help_handlers(app):
    @app.on_message(filters.command("help"))
    async def help_command(client, message):
        await message.reply_text("Help message here")

# handlers/__init__.py
from .help_handler import register_help_handlers

def register_handlers(app):
    # ... existing imports
    register_help_handlers(app)
```

Modifying File Parsing

Edit utils/file_parser.py to change how filenames are parsed:

```python
def parse_file_info(filename):
    # Add your custom parsing logic here
    pass
```

🐛 TROUBLESHOOTING

Common Issues

1. Bot not starting

```
# Check if all dependencies are installed
pip install -r requirements.txt

# Check if config.py is properly configured
python3 -c "import config; print('Config loaded')"

# Check if MongoDB is accessible
python3 -c "from pymongo import MongoClient; client = MongoClient('YOUR_URI'); print(client.server_info())"
```

2. /ls command not working

· Ensure bot is admin in the target channel
· Check if message links are valid
· Verify both links are from the same chat
· Check bot has permission to send messages

3. Broadcast not working

· Verify you're using the owner account
· Check if you replied to a message
· Ensure MongoDB connection is active

4. Force subscribe issues

· Check channel IDs are correct
· Verify bot is admin in force subscribe channels
· Check if channel is public or has invite link

Logging

Enable debug logging by adding to main.py:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

🔄 UPDATING

Update to Latest Version

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Restart the bot
pm2 restart sequence-bot
# OR
python3 main.py
```

🤝 CONTRIBUTING

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch (git checkout -b feature/AmazingFeature)
3. Commit your changes (git commit -m 'Add some AmazingFeature')
4. Push to the branch (git push origin feature/AmazingFeature)
5. Open a Pull Request

Guidelines

· Follow PEP 8 style guide
· Add comments for complex logic
· Update documentation when adding features
· Test your changes before submitting

📞 SUPPORT

Get Help

· Support Group: @BOTSKINGDOMSGROUP
· Updates Channel: @BOTSKINGDOMS
· Developer: @RioShin

Report Issues

1. Check existing issues first
2. Use the issue template
3. Include error logs and steps to reproduce

👥 CREDITS

· Developer: Rio Shin
· Organization: Bots Kingdoms
· Contributors: All Contributors

Special Thanks

· Pyrogram Team
· MongoDB for free database hosting
· All beta testers and users

📄 LICENSE

This project is licensed under the MIT License - see the LICENSE file for details.

Terms

· You can freely use, modify, and distribute this bot
· Attribution to the original authors is required
· No warranty provided
· Not responsible for misuse

🌟 STAR HISTORY

https://api.star-history.com/svg?repos=RioShin2025/SequenceBot&type=Date

---

<p align="center">
  Made with ❤️ by <a href="https://t.me/RioShin">Rio Shin</a>
</p>
<p align="center">
  Powered by <a href="https://t.me/BOTSKINGDOMS">Bots Kingdoms</a>
</p>
```

Additional Files You Need to Create:

1. config.py.example (Template for configuration):

```python
# Copy this file to config.py and fill in your credentials
API_ID = 12345678  # Get from https://my.telegram.org
API_HASH = "your_api_hash_here"  # Get from https://my.telegram.org
BOT_TOKEN = "your_bot_token_here"  # Get from @BotFather
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority"
START_PIC = "https://i.rj1.dev/aNWlA.png"
OWNER_ID = 1234567890  # Your Telegram ID

# Force Subscribe Channels (set to 0 to disable)
FSUB_CHANNEL = -1001234567890
FSUB_CHANNEL_2 = -1009876543210
FSUB_CHANNEL_3 = 0

START_MSG = """<blockquote><b>✨ Hey there!</b></blockquote>
<blockquote>Need your files sent in the right sequence?</blockquote>
<blockquote>Send them here, pick a mode, and let me do the work for you.</blockquote>
<blockquote>[ᴘᴏᴡᴇʀᴇᴅ ʙʏ ɴ4 sᴏᴄɪᴇᴛʏ](https://t.me/BOTSKINGDOMS)</blockquote>"""

HELP_TXT = """<blockquote><b>🤖 ᴍʏ ɴᴀᴍᴇ: ғɪʟᴇ sᴇǫᴜᴇɴᴄᴇ ʙᴏᴛ</b>
<b>◈ ᴏᴡɴᴇʀ:</b> <a href="https://t.me/Rioshin"><b>Cʟɪᴄᴋ ʜᴇʀᴇ</b></a><br>
<b>◈ ʙᴏᴛs ᴄʜᴀɴɴᴇʟ:</b> <a href="https://t.me/botskingdoms"><b>Cʟɪᴄᴋ ʜᴇʀᴇ</b></a><br>
<b>◈ ᴍᴀɴɢᴀ ᴄʜᴀɴɴᴇʟ:</b> <a href="https://t.me/astroMangas"><b>Cʟɪᴄᴋ ʜᴇʀᴇ</b></a><br>
<b>◈ ᴅᴇᴠᴇʟᴏᴘᴇʀ:</b> <a href="https://t.me/Rioshin"><b>Cʟɪᴄᴋ ʜᴇʀᴇ</b></a>"</blockquote>"""

COMMAND_TXT = """<b>🛠️ Bot Commands List</b>

<blockquote>• /start - Start the bot
• /sequence - Start file sequencing mode
• /fileseq - Choose file ordering mode
• /leaderboard - View top users
• /ls - Sequence files from channel links (range selection)</blockquote>"""
```

2. .gitignore (Git ignore file):

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Config files
config.py
.env
secrets.ini

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Temporary files
temp/
tmp/
```

3. setup.sh (Setup script for easy installation):

```bash
#!/bin/bash

echo "┌─────────────────────────┐"
echo "│  SEQUENCE BOT SETUP     │"
echo "└─────────────────────────┘"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python3 is installed: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create config file if it doesn't exist
if [ ! -f config.py ]; then
    echo "⚙️  Creating config file..."
    cp config.py.example config.py
    echo "📝 Please edit config.py with your credentials"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.py with your credentials"
echo "2. Run the bot: python3 main.py"
echo "3. Or run with web server: python3 webserver.py"
echo ""
echo "For help, visit: https://github.com/RioShin2025/SequenceBot"
```

4. run.sh (Run script):

```bash
#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if config exists
if [ ! -f "config.py" ]; then
    echo "❌ config.py not found!"
    echo "ℹ️  Copy config.py.example to config.py and edit it"
    exit 1
fi

# Run the bot
echo "🤖 Starting Sequence Bot..."
python3 main.py
```

5. update.sh (Update script):

```bash
#!/bin/bash

echo "🔄 Updating Sequence Bot..."

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Update dependencies
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "📦 Updating dependencies..."
    pip install -r requirements.txt --upgrade
fi

echo "✅ Update complete!"
echo "ℹ️  Restart the bot to apply changes"
```

6. Create a simple deployment guide PDF (Optional but helpful):

Create a file DEPLOYMENT_GUIDE.md with quick deployment steps for different platforms.

Summary of Changes:

1. Updated README.md with:
   · Complete modular structure explanation
   · Detailed setup instructions for all platforms
   · Step-by-step configuration guide
   · Troubleshooting section
   · Contribution guidelines
   · Maintenance instructions
2. Added helper files:
   · config.py.example - Configuration template
   · .gitignore - Proper Git ignore file
   · setup.sh - Automated setup script
   · run.sh - Easy run script
   · update.sh - Update script
3. Improved organization:
   · Clear folder structure documentation
   · Better command documentation
   · Visual hierarchy in README
   · Platform-specific instructions

The README is now comprehensive, covering everything from basic setup to advanced customization, making it easy for both beginners and experienced developers to deploy and use the bot.
