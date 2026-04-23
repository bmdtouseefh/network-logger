# Network Monitor

Real-time network monitoring dashboard that displays active connections, network interfaces, and traffic statistics in a terminal UI.

![Terminal UI preview](screenshot would go here)

## Features

- Real-time display of active network connections
- Process identification for each connection
- DNS resolution with background caching
- Network interface traffic statistics
- Connection state summary (ESTABLISHED, TIME_WAIT, etc.)
- Colorized terminal output

## Requirements

- Python 3.8+
- psutil
- colorama
- dnspython

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python network-mon.py
```

Press `Ctrl+C` to exit.

## Security Note

This tool requires elevated privileges to access full network connection information. On Linux, you may need to run with `sudo`:

```bash
sudo python network-mon.py
```

## Project Structure

```
network-monitor/
├── network-mon.py      # Main application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## License

MIT