# MoModbus: Modbus RTU/TCP CLI Tool

This is a Python-based CLI tool for implementing Modbus RTU and TCP communication, acting as both a master (client) and slave (server). It uses the `pymodbus` and `click` libraries and supports testing with Node-RED, Python scripts, and `socat` for serial port simulation. Below is a complete guide to set up and test the tool.

## Supported Function Codes
The `momodbus` tool supports the following Modbus function codes:

- **Read Operations**:
  - **FC 1**: Read Coils
  - **FC 2**: Read Discrete Inputs
  - **FC 3**: Read Holding Registers
  - **FC 4**: Read Input Registers

- **Write Operations**:
  - **FC 5**: Write Single Coil
  - **FC 6**: Write Single Register
  - **FC 15**: Write Multiple Coils
  - **FC 16**: Write Multiple Registers

## Prerequisites
- **Python 3.13+**
- **pip** (Python package manager)
- **Node.js** and **npm** (for Node-RED)
- **socat** (for serial port simulation)
- **pyseria**
- **pymodbus**
- **click**
- A Unix-like system (e.g., macOS, Linux) or WSL on Windows

## 1. Installation

### Set Up a Virtual Environment for Python
A virtual environment isolates project dependencies. Follow these steps:
- Create a virtual environment:
  ```bash
  python3 -m venv path/to/venv
  ```
- Activate the virtual environment:
  - On macOS/Linux:
    ```bash
    source path/to/venv/bin/activate
    ```
  - On Windows (WSL or cmd):
    ```bash
    venv\Scripts\activate
    ```

### Install Required Libraries
After activating the virtual environment, install the necessary Python libraries:
- Install `click` and `pymodbus`:
  ```bash
  pip install click pymodbus pyserial
  ```
- Make the script executable:
  ```bash
  chmod +x momodbus.py
  ```

### Install Node-RED
Node-RED is a flow-based programming tool for integrating Modbus devices.
- Install Node.js and npm (if not already installed):
  - On macOS/Linux, use a package manager like `brew` or `apt`:
    ```bash
    brew install node
    ```
    or
    ```bash
    sudo apt update && sudo apt install nodejs npm
    ```
- Install Node-RED globally:
  ```bash
  npm install -g node-red
  ```
- Start Node-RED to verify installation:
  ```bash
  node-red
  ```
  - Access it at `http://localhost:1880` in your browser.

### Install `socat` for Serial Port Simulation
`socat` creates virtual serial ports for testing RTU communication.
- Install `socat`:
  - On macOS:
    ```bash
    brew install socat
    ```
  - On Ubuntu/Debian:
    ```bash
    sudo apt install socat
    ```
  - On other systems, check your package manager or download from [socat.net](http://www.dest-unreach.org/socat/).

### Verify Dependencies
Ensure all tools are installed:
- Check Python: `python3 --version`
- Check `click`: `pip show click`
- Check `pymodbus`: `pip show pymodbus`
- Check Node-RED: `node-red --version`
- Check `socat`: `socat -V`

## 2. Testing MoModbus

### Start the Modbus Slave
The slave can run as an RTU or TCP server. Use a virtual serial port with `socat` for RTU testing.

- **Start a TCP Slave (Port 10502):**
  ```bash
  ./momodbus.py slave --protocol tcp --tcp-port 10502 --random-init --random-update --max-register-value 1000
  ```
  - This starts a TCP server on `0.0.0.0:10502` with random initial values and periodic updates. Make sure adjust the host IP Address as needed.

- **Start an RTU Slave with `socat`:**
  - Create virtual serial ports:
    ```bash
    socat -d -d pty,raw,echo=0 pty,raw,echo=0
    ```
    - This outputs two device paths (e.g., `/dev/ttys001` and `/dev/ttys002`). Note these paths.
  - Start the slave on one port (e.g., `/dev/ttys001`):
    ```bash
    ./momodbus.py slave --protocol rtu --port /dev/ttys001 --baudrate 9600 --random-init --random-update --max-register-value 1000
    ```
  - `socat` simulates a serial connection between the slave and master.

### Test as Modbus Master (Client)
Use the `read` and `write` commands to interact with the slave.

- **Read Holding Registers via TCP:**
  ```bash
  ./momodbus.py read --protocol tcp --host localhost --tcp-port 10502 --unit-id 1 --function-code 3 --address 1 --count 5
  ```
  - Reads 5 holding registers starting at address 1.

- **Write Random Registers via RTU:**
  - Use the second `socat` port (e.g., `/dev/ttys002`) as the master port:
    ```bash
    ./momodbus.py write --protocol rtu --port /dev/ttys002 --baudrate 9600 --unit-id 1 --function-code 16 --address 1 --count 3 --random-values
    ```
  - Writes 3 random values to registers starting at address 1.

- **Continuous Reading (2 Hz):**
  ```bash
  ./momodbus.py read --protocol tcp --host localhost --tcp-port 10502 --unit-id 1 --function-code 3 --address 1 --count 3 --sampling-rate 2
  ```
  - Press Ctrl+C to stop.

## 3. Integrate with Node-RED
Node-RED can act as a Modbus client to communicate with the `momodbus` slave.

- **Install Modbus Nodes:**
  - Open Node-RED (`http://localhost:1880`).
  - Go to Menu > Manage Palette > Install tab.
  - Search for `node-red-contrib-modbus` and click Install.

- **Node-RED JSON Flows for All Scenarios:**
  Import the following JSON configurations into Node-RED (Menu > Import) to test all combinations:

  - **TCP Master (Read Holding Registers):**
    ```json
    [
      {
        "id": "1",
        "type": "tab",
        "label": "TCP Master"
      },
      {
        "id": "2",
        "type": "modbus-read",
        "z": "1",
        "name": "Read Holding Registers",
        "topic": "",
        "showStatusActivities": false,
        "showErrors": false,
        "showWarnings": true,
        "unitid": 1,
        "dataType": "HoldingRegister",
        "adr": 1,
        "quantity": 5,
        "rate": "5000",
        "rateUnit": "ms",
        "delayOnStart": false,
        "startDelayTime": "",
        "server": "3",
        "useIOFile": false,
        "ioFileName": "",
        "keepAlive": false,
        "x": 300,
        "y": 140,
        "wires": [["4"]]
      },
      {
        "id": "3",
        "type": "modbus-client",
        "z": "1",
        "name": "TCP Server",
        "clienttype": "tcp",
        "bufferCommands": true,
        "stateLogEnabled": false,
        "queueLogEnabled": false,
        "failureLogEnabled": false,
        "tcpHost": "localhost",
        "tcpPort": "10502",
        "tcpType": "DEFAULT",
        "serialPort": "/dev/ttys001",
        "serialBaudrate": "9600",
        "serialDatabits": "8",
        "serialStopbits": "1",
        "serialParity": "none",
        "serialType": "RTU",
        "serialTimeOut": "1000",
        "serialProtocol": "RTU",
        "x": 120,
        "y": 140
      },
      {
        "id": "4",
        "type": "debug",
        "z": "1",
        "name": "Debug Output",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 480,
        "y": 140
      }
    ]
    ```
    - Start the TCP slave (`./momodbus.py slave --protocol tcp --tcp-port 10502 ...`) and deploy this flow. Make sure both host being used is the same (IP) host. 

  - **RTU Master (Read Holding Registers):**
    ```json
    [
    {
        "id": "5",
        "type": "tab",
        "label": "RTU Master"
    },
    {
        "id": "6",
        "type": "modbus-read",
        "z": "5",
        "name": "Read Holding Registers",
        "topic": "",
        "showStatusActivities": false,
        "showErrors": false,
        "showWarnings": true,
        "unitid": 1,
        "dataType": "HoldingRegister",
        "adr": 1,
        "quantity": 5,
        "rate": "5000",
        "rateUnit": "ms",
        "delayOnStart": false,
        "startDelayTime": "",
        "server": "7",
        "useIOFile": false,
        "ioFileName": "",
        "keepAlive": false,
        "x": 300,
        "y": 140,
        "wires": [["8"]]
    },
    {
        "id": "7",
        "type": "modbus-client",
        "z": "5",
        "name": "RTU Server",
        "clienttype": "serial",
        "bufferCommands": true,
        "stateLogEnabled": false,
        "queueLogEnabled": false,
        "failureLogEnabled": false,
        "tcpHost": "localhost",
        "tcpPort": "10502",
        "tcpType": "DEFAULT",
        "serialPort": "/dev/ttys002",
        "serialBaudrate": "9600",
        "serialDatabits": "8",
        "serialStopbits": "1",
        "serialParity": "none",
        "serialType": "RTU",
        "serialTimeOut": "1000",
        "serialProtocol": "RTU",
        "x": 120,
        "y": 140
    },
    {
        "id": "8",
        "type": "debug",
        "z": "5",
        "name": "Debug Output",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 480,
        "y": 140
    }
    ]
    ```
    - Start the RTU slave with `socat` and deploy this flow (adjust `/dev/ttys002` to match your socat output).

  - **TCP Client (Write Registers):**
    ```json
    [
      {
        "id": "9",
        "type": "tab",
        "label": "TCP Client"
      },
      {
        "id": "10",
        "type": "inject",
        "z": "9",
        "name": "Trigger Write",
        "props": [
          { "p": "payload" },
          { "p": "topic", "vt": "str" }
        ],
        "repeat": "",
        "crontab": "",
        "once": false,
        "onceDelay": 0.1,
        "topic": "",
        "payload": "[10, 20, 30, 40, 50]",
        "payloadType": "json",
        "x": 140,
        "y": 140,
        "wires": [["11"]]
      },
      {
        "id": "11",
        "type": "modbus-write",
        "z": "9",
        "name": "Write Registers",
        "showStatusActivities": false,
        "showErrors": false,
        "showWarnings": true,
        "unitid": 1,
        "dataType": "HoldingRegister",
        "adr": 1,
        "quantity": 5,
        "server": "12",
        "emptyMsgOnFail": false,
        "keepAlive": false,
        "x": 300,
        "y": 140,
        "wires": [["13"]]
      },
      {
        "id": "12",
        "type": "modbus-client",
        "z": "9",
        "name": "TCP Server",
        "clienttype": "tcp",
        "bufferCommands": true,
        "stateLogEnabled": false,
        "queueLogEnabled": false,
        "failureLogEnabled": false,
        "tcpHost": "0.0.0.0",
        "tcpPort": "10502",
        "tcpType": "DEFAULT",
        "serialPort": "/dev/ttys001",
        "serialBaudrate": "9600",
        "serialDatabits": "8",
        "serialStopbits": "1",
        "serialParity": "none",
        "serialType": "RTU",
        "serialTimeOut": "1000",
        "serialProtocol": "RTU",
        "x": 140,
        "y": 60
      },
      {
        "id": "13",
        "type": "debug",
        "z": "9",
        "name": "TCP Client Debug Output",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 460,
        "y": 140
      }
    ]
    ```
    - Start the TCP slave and deploy this flow to write `[10, 20, 30, 40, 50]` to registers.

  - **RTU Client (Write Registers):**
    ```json
    [
      {
        "id": "14",
        "type": "tab",
        "label": "RTU Client"
      },
      {
        "id": "15",
        "type": "inject",
        "z": "14",
        "name": "Trigger Write",
        "props": [
          { "p": "payload" },
          { "p": "topic", "vt": "str" }
        ],
        "repeat": "",
        "crontab": "",
        "once": false,
        "onceDelay": 0.1,
        "topic": "",
        "payload": "[10, 20, 30, 40, 50]",
        "payloadType": "json",
        "x": 140,
        "y": 140,
        "wires": [["16"]]
      },
      {
        "id": "16",
        "type": "modbus-write",
        "z": "14",
        "name": "Write Registers",
        "showStatusActivities": false,
        "showErrors": false,
        "showWarnings": true,
        "unitid": 1,
        "dataType": "HoldingRegister",
        "adr": 1,
        "quantity": 5,
        "server": "17",
        "emptyMsgOnFail": false,
        "keepAlive": false,
        "x": 300,
        "y": 140,
        "wires": [["18"]]
      },
      {
        "id": "17",
        "type": "modbus-client",
        "z": "14",
        "name": "RTU Server",
        "clienttype": "serial",
        "bufferCommands": true,
        "stateLogEnabled": false,
        "queueLogEnabled": false,
        "failureLogEnabled": false,
        "tcpHost": "localhost",
        "tcpPort": "10502",
        "tcpType": "DEFAULT",
        "serialPort": "/dev/ttys002",  
        "serialBaudrate": "9600",
        "serialDatabits": "8",
        "serialStopbits": "1",
        "serialParity": "none",
        "serialType": "RTU",
        "serialTimeOut": "1000",
        "serialProtocol": "RTU",
        "x": 140,
        "y": 60
      },
      {
        "id": "18",
        "type": "debug",
        "z": "14",
        "name": "Debug Output",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 460,
        "y": 140
      }
    ]
    ```
    - Start the RTU slave with `socat` and deploy this flow (adjust `/dev/ttys002` to match your socat output).

## 4. Test with Python `pymodbus`
Write a Python script to act as a master using `pymodbus`.

- Create `modbus_master.py`:
  ```python
  from pymodbus.client import ModbusTcpClient

  client = ModbusTcpClient('localhost', port=10502)
  client.connect()

  # Read 5 holding registers
  result = client.read_holding_registers(address=1, count=5, slave=1)
  print(f"Read registers: {result.registers}")

  # Write random values
  values = [10, 20, 30, 40, 50]
  client.write_registers(address=1, values=values, slave=1)
  print(f"Wrote values: {values}")

  client.close()
  ```
- Run it in the virtual environment:
  ```bash
  python modbus_master.py
  ```

## 5. Troubleshooting
- **Serial Port Issues**: Ensure `socat` ports are active and permissions are correct (e.g., `sudo chmod 666 /dev/ttys*`).
- **Connection Errors**: Verify the slave is running and ports match.
- **Node-RED Errors**: Check the Node-RED log (Menu > View Log) for issues.

## Notes
- The script logs at the INFO level by default.
- Adjust `max-register-value` and other parameters as needed.
- For advanced setups, explore Node-RED dashboards or Python threading for concurrent operations.
