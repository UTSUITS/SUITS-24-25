from threading import Lock

# Shared dictionary for data
shared_results = {}

# Thread-safe lock
results_lock = Lock()
