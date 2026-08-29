#!/bin/bash
# Setup cron job for daily morning news digest
# Run this script once to install the cron job

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$PROJECT_DIR/morning_routine.py"
ENV_FILE="$PROJECT_DIR/.env"

# Make the script executable
chmod +x "$SCRIPT_PATH"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your Telegram credentials:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your bot token and chat ID"
    exit 1
fi

# Create a wrapper script that sets up the environment
WRAPPER_PATH="$PROJECT_DIR/morning_routine_cron.sh"
cat > "$WRAPPER_PATH" << 'WRAPPER'
#!/bin/bash
# This wrapper ensures environment variables are loaded before running the morning routine

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the morning routine
python3 morning_routine.py >> /tmp/morning_routine.log 2>&1
WRAPPER

chmod +x "$WRAPPER_PATH"

# Add cron job - runs every 6 hours
# Remove existing cron job if it exists
(crontab -l 2>/dev/null | grep -v "morning_routine_cron.sh") | crontab - 2>/dev/null || true

# Add the new cron job
(crontab -l 2>/dev/null; echo "0 */6 * * * $WRAPPER_PATH") | crontab -

echo "✅ Cron job installed successfully!"
echo ""
echo "📋 Cron Configuration:"
echo "   Time: Every 6 hours"
echo "   Script: $WRAPPER_PATH"
echo "   Log: /tmp/morning_routine.log"
echo ""
echo "To view installed cron jobs:"
echo "   crontab -l"
echo ""
echo "To remove the cron job:"
echo "   crontab -e  # then delete the morning_routine line"
echo ""
echo "To change the time, edit the cron schedule:"
echo "   crontab -e"
echo ""
echo "Common times:"
echo "   0 */6 * * *  = every 6 hours"
echo "   0 8 * * *    = 8:00 AM every day"
echo "   30 7 * * *   = 7:30 AM every day"
