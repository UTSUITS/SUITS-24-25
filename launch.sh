
#!/bin/bash

sudo tailscale up 

export DISPLAY=:0
export QT_QPA_PLATFORM=xcb 
export XAUTHORITY=/home/utsuits/.Xauthority

# Prompt for IP address if not already saved
IP_FILE="/home/utsuits/ip_address.txt"

# Only prompt in interactive shells (so it doesn't break scripts or systemd)
if [[ -t 0 ]]; then
    if [ ! -f "$IP_FILE" ] || [ "$(wc -l < "$IP_FILE")" -lt 2 ]; then
        echo ""
        echo "No IP address and team number set for this session."

        # Prompt for IP address
        while true; do
            read -p "Enter IP address for the session: " ip_address
            if [[ "$ip_address" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                break
            else
                echo "❌ Invalid IP format. Try again (e.g., 192.168.0.101)"
            fi
        done

	# Prompt for team number
        while true; do
            read -p "Enter your team number: " team_number
            if [[ "$team_number" =~ ^[0-9]+$ ]]; then
                break
            else
                echo "❌ Invalid team number. Must be numeric."
            fi
        done

        echo -e "$ip_address\n$team_number" > "$IP_FILE"
        echo "✅ Saved IP address: $ip_address"
        echo "✅ Saved team number: $team_number"
    else
        ip_address=$(sed -n '1p' "$IP_FILE")
        team_number=$(sed -n '2p' "$IP_FILE")
        echo "✅ IP address already set: $ip_address"
        echo "✅ Team number already set: $team_number"
    fi
fi

# Remove all existing Docker containers (if any)
containers=$(docker ps -a -q)
if [ -n "$containers" ]; then
    docker rm -f $containers
fi

# Check if anything is using port 6379
PORT_IN_USE=$(sudo lsof -i :6379 -t)

if [ -n "$PORT_IN_USE" ]; then
    echo "⚠️ Port 6379 is currently in use by process ID(s): $PORT_IN_USE"

    # Check if it's the system redis-server
    if ps -p $PORT_IN_USE -o cmd= | grep -q redis-server; then
        echo "🛑 Stopping native Redis server..."
        sudo systemctl stop redis || sudo service redis-server stop
    else
        echo "❌ Unknown process using port 6379. Attempting to kill it..."
        sudo kill -9 $PORT_IN_USE
    fi

    # Wait a bit for port to free up
    sleep 2
else
    echo "✅ Port 6379 is free to use."
fi

# Start Redis container if not already running
if ! docker ps | grep -q redis:7; then
    echo "Starting Redis container..."
    cd /home/utsuits/Documents/SUITS-24-25/api
    docker compose down
    docker compose up -d 
fi

# Wait until Redis is ready
echo "Waiting for Redis to be ready..."
until nc -z localhost 6379; do
    sleep 1 
done
echo "Redis is up!"


# Flask-Redis tmux session 
echo "Flask and Redis session starting!"
tmux new-session -d -s api "cd /home/utsuits/Documents/SUITS-24-25/api && python commands_api.py" 
echo "Flask and Redis are up and running!"

# WMD tmux session 
echo "Launching WMD"
tmux new-session -d -s WMD "export DISPLAY=:0 && export QT_QPA_PLATFORM=xcb && export XAUTHORITY=/home/utsuits/.Xauthority && cd /home/utsuits/Documents/SUITS-24-25/WMD && python display.py"
echo "WMD successfully launched."
echo "And we got liftoff!"
