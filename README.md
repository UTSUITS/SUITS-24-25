# SUITS-24-25
This contains work involving NASA SUITS for the Aether-net team from UT


## Instructions 
Clone this repo: 
```bash
git clone git@github.com:UTSUITS/SUITS-24-25.git
```

Before running these scripts you need to clone the [TSS-2025](https://github.com/SUITS-Techteam/TSS-2025) repo and run the server. Please follow the instructions from the given link. 

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

Now open a new terminal and cd into the SUITS-24-25 repo you just cloned. 
```bash
cd SUITS-24-25
```

Now run the following: 
```bash 
chmod +x start_server.py

./start_server.py path/to/server

# Example 
./start_server.py "/Users/guarneros/Documents/NASA SUITS/TSS-2025/server" 

# Example Output
Data successfully written to server_info.json
```

A new file ```server_info.json``` should have been created. Now you are able to run ```send_to_server``` to communicate with the server and receive the desired data. 

```bash
chmod  +x send_to_server.py

# Example
./send_to_server.py 15 

# Example Output
Receiving from ('100.66.113.144', 14141)
Command: 15
Output: 1
```
This means we sent a command to get the oxygen error and received a boolean value of 1, which means the oxygen error is on. Please look into the [TSS-2025](https://github.com/SUITS-Techteam/TSS-2025) documentation for more information on what each command means. 
