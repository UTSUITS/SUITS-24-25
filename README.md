# SUITS-24-25
This contains work involving NASA SUITS for the AETHER-NET team from UT Austin. 

## Getting Started
Clone this repo and cd into it: 
```bash
git clone git@github.com:UTSUITS/SUITS-24-25.git
cd SUITS-24-25 
```

## Development Instructions 
Before running these scripts you need to clone the [TSS-2025](https://github.com/SUITS-Techteam/TSS-2025) repo and host the server in a separate computer. Please follow the instructions from the given link. 

Once the server is running you should be seeing the following message: 
```bash
# Example Output 
Hello World

Launching Server at IP: 100.66.113.144:14141
Configuring Local Address...
Creating HTTP Socket...
Binding HTTP Socket...
Listening to HTTP Socket...
Creating UDP Socket...
Binding UDP Socket...
Listening to UDP Socket...
```

Now you are able to run the display and host the flask app on your Pi! 

### Running the app and display 
You might have noticed that you have a ```launch.sh``` script. Running this script should allow you to automatically start all the services. 

First, make sure you have this script: 
```bash 
ls

# Output
api  commands  HoloLens_2_UI  launch.sh  README.md  WMD
```

Now you should make it an executable and run it: 
```bash 
chmod +x launch.sh
./launch.sh 

# Example Output
No IP address and team number set for this session.
Enter IP address for the session: 100.66.113.144
Enter your team number: 2
✅ Saved IP address: 100.66.113.144
✅ Saved team number: 2
b148ccb33487
⚠️ Port 6379 is currently in use by process ID(s): 677
🛑 Stopping native Redis server...
Starting Redis container...
[+] Running 1/1
 ✔ Network api_default  Removed                                                                                              0.4s 
[+] Running 2/2
 ✔ Network api_default       Created                                                                                         0.1s 
 ✔ Container api-redis-db-1  Started                                                                                         1.6s 
Waiting for Redis to be ready...
Redis is up!
Flask and Redis session starting!
Flask and Redis are up and running!
Launching WMD
WMD successfully launched.
And we got liftoff! 
```

This will prompt you for the ip address of the TSS server you started up earlier. It will also ask you for your team number and all of the services should start shortly after that. You should see the PyQt display took the whole screen. Now the app should expose a curl route where you can query the most up to date data as well as a determined number of past logs and the responses. 

### Interacting with Flask API
As mentioned above, you are able to post GET requests to the Flask API and get data formatted as a JSON file. You are able to do so from any computer that is connected to a public ip address. 

#### _/now_ route 
To get the most up to date data, please do the following in a terminal: 
```bash 
curl ip_address_of_pi:5000/now

# Example 
curl 100.64.66.81:5000/now

# Example Output


```

The output should include the epoch, the dictionary with all the commands and their outputs, and the time it took to retrieve that data from the Redis database. 

#### _/logs_ route 
To get the past logs, you are able to query as many past commands as you'd like. You ask for the number of seconds in the past from the now time that you want to get. This should be equal to the number of dictionaries you get. 
```bash 
curl ip_address_of_pi:5000/logs/number_of_seconds_in_past

# Example 
curl 100.64.66.81:5000/logs/60

# Example Output


```



Please look into the [TSS-2025](https://github.com/SUITS-Techteam/TSS-2025) documentation for more information on what each command means. 
