# Network Monitor

Background network connection logger that captures all network activity to a CSV file for security monitoring and analysis.

## Features

- Captures all TCP and UDP network connections
- Records full connection data: protocol, local/remote addresses and ports, status
- Process identification (PID and process name) for each connection
- DNS resolution with background caching
- Connection state tracking (ESTABLISHED, TIME_WAIT, etc.)
- Timestamp for each logged connection
- Background/daemon mode for continuous monitoring
- Configurable polling interval

## Requirements

- Python 3.8+
- psutil
- dnspython

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode

```bash
python network_logger.py
```

Press `Ctrl+C` to exit.

### Background/Daemon Mode

Run as a background process:

```bash
python network_logger.py -d -o /var/log/network_connections.csv -p /var/run/network_logger.pid
```

Stop a running daemon:

```bash
kill $(cat /var/run/network_logger.pid)
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output CSV file path | `network_connections.csv` |
| `-i, --interval` | Polling interval in seconds | `2` |
| `-d, --daemon` | Run as background daemon | - |
| `-p, --pidfile` | PID file path for daemon mode | - |

## Data Collected

Each connection logs the following fields:

- `timestamp` - ISO format timestamp of capture
- `protocol` - TCP or UDP
- `local_address` - Local IP address
- `local_port` - Local port number
- `remote_address` - Remote IP address
- `remote_port` - Remote port number
- `domain` - Resolved hostname (if available)
- `status` - Connection state (ESTABLISHED, TIME_WAIT, etc.)
- `process_name` - Name of the associated process
- `process_pid` - Process ID

## Security Note

This tool requires elevated privileges to access full network connection information. On Linux, you may need to run with `sudo`:

```bash
sudo python network_logger.py
```

## Project Structure

```
network-monitor/
├── network_logger.py      # Main application
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## License

MIT