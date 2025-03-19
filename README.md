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
python3 connect_to_server.py --ip ip_address --port port_number

# Example 
python3 connect_to_server.py --ip 192.168.40.73 --port 14141 

```

A new file ```output_results.json``` should have been created which updates every one second. 

Please look into the [TSS-2025](https://github.com/SUITS-Techteam/TSS-2025) documentation for more information on what each command means. 
