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
{
  "closest_epoch": "2025-04-24 13:48:09",
  "data": {
    "1": 0,
    "10": 0,
    "100": 0.0,
    "101": 0.0,
    "102": 0.0,
    "103": 0,
    "104": 0,
    "105": 42,
    "106": 0.0,
    "107": 0,
    "108": 0,
    "109": 9.011358060502888e-40,
    "11": 0,
    "110": 0,
    "111": 0,
    "112": 0.0,
    "113": 0,
    "114": 0,
    "115": 0.0,
    "116": 0,
    "117": 0,
    "118": 0.0,
    "12": 0,
    "13": 0,
    "14": 0,
    "15": 0,
    "16": 0,
    "17": 0.0,
    "18": 0.0,
    "19": 0.0,
    "2": 0,
    "20": 0.0,
    "21": 0.0,
    "22": 0.0,
    "23": 0,
    "24": 0,
    "25": 0,
    "26": 0,
    "27": 0.0,
    "28": 0.0,
    "29": 0.0,
    "3": 0,
    "30": 0.0,
    "31": 0.0,
    "32": 1.0,
    "33": 1.0,
    "34": 1.0,
    "35": 1.0,
    "36": 1.0,
    "37": 0,
    "38": 1.0,
    "39": 1.0,
    "4": 0,
    "40": 1.0,
    "41": 91.0,
    "42": 0.0,
    "43": 1.0,
    "44": 1.0,
    "45": 1.0,
    "46": 1.0,
    "47": 1.0,
    "48": 0,
    "49": 0,
    "5": 0,
    "50": 0,
    "51": 0,
    "52": 0,
    "53": 0,
    "54": 0,
    "55": 0,
    "56": 0,
    "57": 0,
    "58": 0.0,
    "59": 0.0,
    "6": 0,
    "60": 0.0,
    "61": 0.0,
    "62": 0.0,
    "63": 0.0,
    "64": 5077.14892578125,
    "65": 23.755802154541016,
    "66": 15.48952865600586,
    "67": 0.0,
    "68": 0.0,
    "69": 4238.0,
    "7": 0,
    "70": 90.0,
    "71": 0.0,
    "72": 0.0,
    "73": 3.0722999572753906,
    "74": 0.005900000222027302,
    "75": 11.554200172424316,
    "76": 14.632401466369629,
    "77": 0.0,
    "78": 0.0,
    "79": 0.0,
    "8": 0,
    "80": 0.0,
    "81": 0.0,
    "82": 70.0,
    "83": 20.508068084716797,
    "84": 0.0,
    "85": 0.0,
    "86": 3384.893798828125,
    "87": 24.231962203979492,
    "88": 19.41913604736328,
    "89": 0.0,
    "9": 0,
    "90": 0.0,
    "91": 4714.0,
    "92": 90.0,
    "93": 0.0,
    "94": 0.0,
    "95": 3.0722999572753906,
    "96": 0.005900000222027302,
    "97": 11.554200172424316,
    "98": 14.632401466369629,
    "99": 0.0
  },
  "waited_seconds": 0.515
}
```

The output should include the epoch, the dictionary with all the commands and their outputs, and the time it took to retrieve that data from the Redis database. 

#### _/logs_ route 
To get the past logs, you are able to query as many past commands as you'd like. You ask for the number of seconds in the past from the now time that you want to get. This should get the range of data from the current time to the number of seconds you indicated back in time. 
```bash 
curl ip_address_of_pi:5000/logs/number_of_seconds_in_past

# Example 
curl 100.64.66.81:5000/logs/4

# Example Output
[
  {
    "data": {
      "1": 0,
      "10": 0,
      "100": 0.0,
      "101": 0.0,
      "102": 0.0,
      "103": 0,
      "104": 0,
      "105": 42,
      "106": 0.0,
      "107": 0,
      "108": 0,
      "109": 0.0,
      "11": 0,
      "110": 0,
      "111": 0,
      "112": 0.0,
      "113": 0,
      "114": 0,
      "115": 0.0,
      "116": 0,
      "117": 0,
      "118": 0.0,
      "12": 0,
      "13": 0,
      "14": 0,
      "15": 0,
      "16": 0,
      "17": 0.0,
      "18": 0.0,
      "19": 0.0,
      "2": 0,
      "20": 0.0,
      "21": 0.0,
      "22": 0.0,
      "23": 0,
      "24": 0,
      "25": 0,
      "26": 0,
      "27": 0.0,
      "28": 0.0,
      "29": 0.0,
      "3": 0,
      "30": 0.0,
      "31": 0.0,
      "32": 1.0,
      "33": 1.0,
      "34": 1.0,
      "35": 1.0,
      "36": 1.0,
      "37": 0,
      "38": 1.0,
      "39": 1.0,
      "4": 0,
      "40": 1.0,
      "41": 91.0,
      "42": 0.0,
      "43": 1.0,
      "44": 1.0,
      "45": 1.0,
      "46": 1.0,
      "47": 1.0,
      "48": 0,
      "49": 0,
      "5": 0,
      "50": 0,
      "51": 0,
      "52": 0,
      "53": 0,
      "54": 0,
      "55": 0,
      "56": 0,
      "57": 0,
      "58": 0.0,
      "59": 0.0,
      "6": 0,
      "60": 0.0,
      "61": 0.0,
      "62": 0.0,
      "63": 0.0,
      "64": 5077.14892578125,
      "65": 23.755802154541016,
      "66": 15.48952865600586,
      "67": 0.0,
      "68": 0.0,
      "69": 4238.0,
      "7": 0,
      "70": 90.0,
      "71": 0.0,
      "72": 0.0,
      "73": 3.0722999572753906,
      "74": 0.005900000222027302,
      "75": 11.554200172424316,
      "76": 14.632401466369629,
      "77": 0.0,
      "78": 0.0,
      "79": 0.0,
      "8": 0,
      "80": 0.0,
      "81": 0.0,
      "82": 70.0,
      "83": 20.508068084716797,
      "84": 0.0,
      "85": 0.0,
      "86": 3384.893798828125,
      "87": 24.231962203979492,
      "88": 19.41913604736328,
      "89": 0.0,
      "9": 0,
      "90": 0.0,
      "91": 4714.0,
      "92": 90.0,
      "93": 0.0,
      "94": 0.0,
      "95": 3.0722999572753906,
      "96": 0.005900000222027302,
      "97": 11.554200172424316,
      "98": 14.632401466369629,
      "99": 0.0
    },
    "epoch": "2025-04-24 13:49:46"
  },
...
]
```

You should have received a list of dictionaries pertaining to the number of epochs asked for. 

A different functionality includes asking for a specific command and its logs. You can do this with query parameters. 

```bash 
curl ip_address_of_pi:5000/logs/number_of_seconds_in_past?command=int

# Example 
curl 100.64.66.81:5000/logs/4?command=14 

# Example Output 
[
  {
    "data": {
      "14": 0
    },
    "epoch": "2025-04-24 13:53:17"
  },
  {
    "data": {
      "14": 0
    },
    "epoch": "2025-04-24 13:53:18"
  },
  {
    "data": {
      "14": 0
    },
    "epoch": "2025-04-24 13:53:19"
  },
  {
    "data": {
      "14": 0
    },
    "epoch": "2025-04-24 13:53:20"
  }
]
```

You will see that you receive a list of dictionaries including the command and its value as well as the epoch value. If you input a number greater than 118 or less than 1, you will receive an error. If you also input a letter instead of a number, the route will throw an error. Here are examples for the errors: 

```bash
# Example
curl 100.64.66.80:5000/logs/4?command=a

# Example Output 
Invalid command parameter; command must be an integer 
```

```bash
# Example
curl 100.64.66.80:5000/logs/4?command=200

# Example Output 
Command must be between 1 and 118
```

Please look into the [TSS-2025](https://github.com/SUITS-Techteam/TSS-2025) documentation for more information on what each command means. 
