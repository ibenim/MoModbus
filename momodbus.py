#!/usr/bin/env python3

import click
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.server import StartTcpServer, StartSerialServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.exceptions import ModbusException
import random
import time
import logging
import threading

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("momodbus")

# Helper function to initialize Modbus client (master)
def initialize_client(protocol, port, baudrate=None, host=None, tcp_port=None):
    if protocol == "rtu":
        if not port or not baudrate:
            raise click.UsageError("Port and baudrate are required for RTU")
        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            timeout=1,
            parity="N",
            stopbits=1,
            bytesize=8
        )
        logger.info(f"Initialized RTU client: port={port}, baudrate={baudrate}")
    elif protocol == "tcp":
        if not host or not tcp_port:
            raise click.UsageError("Host and TCP port are required for TCP")
        client = ModbusTcpClient(host=host, port=tcp_port or 502)
        logger.info(f"Initialized TCP client: host={host}, port={tcp_port}")
    else:
        raise click.UsageError("Invalid protocol. Use 'rtu' or 'tcp'")
    return client

# Helper function to update random values in the datastore
def update_random_values(context, unit_id, coils_count, holding_registers_count, max_register_value, update_interval=1.0):
    while True:
        try:
            # Update coils with random True/False starting at address 1
            coils = [random.choice([True, False]) for _ in range(coils_count)]
            context[unit_id].setValues(1, 1, coils)  # FC 1, address 1
            logger.debug(f"Updated {coils_count} coils with random values starting at 1: {coils[:5]}...")

            # Update holding registers with random values (0 to max_register_value) starting at address 1
            registers = [random.randint(0, max_register_value) for _ in range(holding_registers_count)]
            context[unit_id].setValues(3, 1, registers)  # FC 3, address 1
            # Log the first value explicitly to verify
            first_register = context[unit_id].getValues(3, 1, 1)[0]  # Read back the first register
            logger.debug(f"Verified first holding register at address 1: {first_register} (should match {registers[0]})")
            logger.debug(f"Updated {holding_registers_count} holding registers with random values (max={max_register_value}) starting at 1: {registers[:5]}...")
            
            time.sleep(update_interval)
        except Exception as e:
            logger.error(f"Error updating random values: {e}")
            time.sleep(update_interval)

# Helper function to initialize Modbus server (slave) context
def initialize_server_context(coils=1000, discrete_inputs=1000, holding_registers=1000, input_registers=1000, random_init=False, max_register_value=65535):
    # Initialize data blocks (1-based addressing)
    coils_block = ModbusSequentialDataBlock(1, [random.choice([True, False]) for _ in range(coils)] if random_init else [False] * coils)
    di_block = ModbusSequentialDataBlock(1, [random.choice([True, False]) for _ in range(discrete_inputs)] if random_init else [False] * discrete_inputs)
    hr_block = ModbusSequentialDataBlock(1, [random.randint(0, max_register_value) for _ in range(holding_registers)] if random_init else [0] * holding_registers)
    ir_block = ModbusSequentialDataBlock(1, [random.randint(0, max_register_value) for _ in range(input_registers)] if random_init else [0] * input_registers)
    
    # Create slave context
    store = ModbusSlaveContext(
        di=di_block,
        co=coils_block,
        hr=hr_block,
        ir=ir_block
    )
    
    # Create server context with unit ID 1
    context = ModbusServerContext(slaves={1: store}, single=False)
    logger.info(f"Initialized server context: {coils} coils, {discrete_inputs} discrete inputs, {holding_registers} holding registers, {input_registers} input registers")
    return context

# Function to read Modbus data (master)
def read_data(client, unit_id, function_code, address, count):
    try:
        if function_code == 1:
            logger.debug(f"Sending read_coils: unit_id={unit_id}, address={address}, count={count}")
            result = client.read_coils(address, count, slave=unit_id)
        elif function_code == 2:
            logger.debug(f"Sending read_discrete_inputs: unit_id={unit_id}, address={address}, count={count}")
            result = client.read_discrete_inputs(address, count, slave=unit_id)
        elif function_code == 3:
            logger.debug(f"Sending read_holding_registers: unit_id={unit_id}, address={address}, count={count}")
            result = client.read_holding_registers(address, count, slave=unit_id)
        elif function_code == 4:
            logger.debug(f"Sending read_input_registers: unit_id={unit_id}, address={address}, count={count}")
            result = client.read_input_registers(address, count, slave=unit_id)
        else:
            raise click.UsageError("Invalid function code for read. Use 1, 2, 3, or 4")
        
        if result.isError():
            logger.error(f"Error reading data: {result}")
            click.echo(f"Error reading data: {result}")
            return None
        values = result.bits if function_code in (1, 2) else result.registers
        logger.debug(f"Received response: {values}")
        return values
    except ModbusException as e:
        logger.error(f"Modbus error: {e}")
        click.echo(f"Modbus error: {e}")
        return None

# Function to write Modbus data (master)
def write_data(client, unit_id, function_code, address, count, random_values):
    try:
        if function_code in (5, 15):  # Coils
            if random_values:
                values = [random.choice([True, False]) for _ in range(count)]
                click.echo(f"Generated random coil values: {values}")
            else:
                values = []
                for i in range(count):
                    value = click.prompt(f"Enter value for coil {address + i} (0/1 or True/False)", type=str)
                    values.append(value.lower() in ("1", "true", "t"))
            
            if function_code == 5:
                if count != 1:
                    raise click.UsageError("Function code 5 requires count=1")
                logger.debug(f"Sending write_coil: unit_id={unit_id}, address={address}, value={values[0]}")
                result = client.write_coil(address, values[0], slave=unit_id)
            else:  # function_code == 15
                logger.debug(f"Sending write_coils: unit_id={unit_id}, address={address}, values={values}")
                result = client.write_coils(address, values, slave=unit_id)
        
        elif function_code in (6, 16):  # Registers
            if random_values:
                values = [random.randint(0, 65535) for _ in range(count)]
                click.echo(f"Generated random register values: {values}")
            else:
                values = [int(click.prompt(f"Enter value for register {address + i}", type=int)) for i in range(count)]
            
            if function_code == 6:
                if count != 1:
                    raise click.UsageError("Function code 6 requires count=1")
                logger.debug(f"Sending write_register: unit_id={unit_id}, address={address}, value={values[0]}")
                click.echo(f"Sending FC6 (Write Single Register): unit_id={unit_id}, address={address}, value={values[0]}")
                result = client.write_register(address, values[0], slave=unit_id)
                if not result.isError():
                    click.echo(f"FC6 Response: Successfully wrote value={values[0]} to register {address} for unit_id={unit_id}")
            else:  # function_code == 16
                logger.debug(f"Sending write_registers: unit_id={unit_id}, address={address}, values={values}")
                result = client.write_registers(address, values, slave=unit_id)
        
        else:
            raise click.UsageError("Invalid function code for write. Use 5, 6, 15, or 16")
        
        if result.isError():
            logger.error(f"Error writing data: {result}")
            click.echo(f"Error writing data: {result}")
        else:
            if function_code != 6:  # Avoid duplicate message for FC6
                logger.debug(f"Write successful: values={values}")
                click.echo(f"Successfully wrote {values} to {'coils' if function_code in (5, 15) else 'registers'} starting at {address}")
    except ModbusException as e:
        logger.error(f"Modbus error: {e}")
        click.echo(f"Modbus error: {e}")

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def momodbus():
    """MoModbus: Modbus RTU/TCP CLI tool for master or slave modes.

    Acts as a Modbus master (client) or slave (server) over RTU or TCP/IP.
    - Master: Read (FC 1-4) or write (FC 5, 6, 15, 16) with random values/sampling.
    - Slave: Server with configurable coils/registers.
    - Logs all communication to the terminal.

    Use 'read', 'write', or 'slave' commands with -h for details.
    Example: ./momodbus.py read -h
    """
    pass

@momodbus.command()
@click.option("--protocol", type=click.Choice(["rtu", "tcp"], case_sensitive=False), default="rtu", help="Protocol: 'rtu' (serial) or 'tcp' (network).")
@click.option("--port", default=None, help="Serial port for RTU (e.g., /dev/ttys001).")
@click.option("--baudrate", type=int, default=9600, help="Baudrate for RTU (e.g., 9600).")
@click.option("--host", default="localhost", help="IP address for TCP (e.g., 127.0.0.1).")
@click.option("--tcp-port", type=int, default=502, help="TCP port (default: 502).")
@click.option("--unit-id", type=int, default=1, help="Slave unit ID (default: 1).")
@click.option("--function-code", type=int, default=3, help="Function code: 1 (coils), 2 (discrete inputs), 3 (holding registers), 4 (input registers).")
@click.option("--address", type=int, required=True, help="Starting coil/register address.")
@click.option("--count", type=int, default=1, help="Number of coils/registers to read (default: 1).")
@click.option("--sampling-rate", type=float, default=0, help="Samples per second (0 for single read).")
def read(protocol, port, baudrate, host, tcp_port, unit_id, function_code, address, count, sampling_rate):
    """Read coils/registers from a Modbus slave as a master.

    Examples:
        Read 5 holding registers via TCP:
            ./momodbus.py read --protocol tcp --host 127.0.0.1 --tcp-port 10502 --unit-id 1 --function-code 3 --address 1 --count 5
        Continuous read (2 Hz) via RTU:
            ./momodbus.py read --protocol rtu --port /dev/ttys001 --baudrate 9600 --unit-id 1 --function-code 3 --address 1 --count 3 --sampling-rate 2
    """
    client = initialize_client(protocol, port, baudrate, host, tcp_port)
    if not client.connect():
        logger.error("Failed to connect to Modbus server")
        click.echo("Failed to connect to Modbus server")
        return

    try:
        if sampling_rate <= 0:
            result = read_data(client, unit_id, function_code, address, count)
            if result:
                data_type = "coils" if function_code in (1, 2) else "registers"
                click.echo(f"Read {data_type} {address} to {address + count - 1}: {result}")
        else:
            interval = 1.0 / sampling_rate
            click.echo(f"Reading periodically at {sampling_rate} Hz (Ctrl+C to stop)")
            while True:
                result = read_data(client, unit_id, function_code, address, count)
                if result:
                    data_type = "coils" if function_code in (1, 2) else "registers"
                    click.echo(f"Read {data_type} {address} to {address + count - 1}: {result}")
                time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Stopped continuous reading")
        click.echo("Stopped periodic reading")
    finally:
        client.close()

@momodbus.command()
@click.option("--protocol", type=click.Choice(["rtu", "tcp"], case_sensitive=False), default="rtu", help="Protocol: 'rtu' (serial) or 'tcp' (network).")
@click.option("--port", type=str, default=None, help="Serial port for RTU (e.g., /dev/ttys001).")
@click.option("--baudrate", type=int, default=9600, help="Baudrate for RTU (e.g., 9600).")
@click.option("--host", type=str, default="localhost", help="IP address for TCP (e.g., 127.0.0.1).")
@click.option("--tcp-port", type=int, default=502, help="TCP port (default: 502).")
@click.option("--unit-id", type=int, default=1, help="Slave unit ID (default: 1).")
@click.option("--function-code", type=int, default=16, help="Function code: 5 (single coil), 6 (single register), 15 (multiple coils), 16 (multiple registers).")
@click.option("--address", type=int, required=True, help="Starting coil/register address.")
@click.option("--count", type=int, default=1, help="Number of coils/registers to write (default: 1).")
@click.option("--random-values", is_flag=True, help="Use random values (coils: True/False; registers: 0-65535).")
@click.option("--sampling-rate", type=float, default=0, help="Samples per second (0 for single write).")
def write(protocol, port, baudrate, host, tcp_port, unit_id, function_code, address, count, random_values, sampling_rate):
    """Write coils/registers to a Modbus slave as a master.

    Examples:
        Write 3 random registers via TCP:
            ./momodbus.py write --protocol tcp --host 127.0.0.1 --tcp-port 10502 --unit-id 1 --function-code 16 --address 1 --count 3 --random-values
        Continuous write (1 Hz) via RTU:
            ./momodbus.py write --protocol rtu --port /dev/ttys001 --baudrate 9600 --unit-id 1 --function-code 16 --address 1 --count 3 --random-values --sampling-rate 1
    """
    client = initialize_client(protocol, port, baudrate, host, tcp_port)
    if not client.connect():
        logger.error("Failed to connect to Modbus server")
        click.echo("Failed to connect to Modbus server")
        return

    try:
        if sampling_rate <= 0:
            write_data(client, unit_id, function_code, address, count, random_values)
        else:
            interval = 1.0 / sampling_rate
            click.echo(f"Writing periodically at {sampling_rate} Hz (Ctrl+C to stop)")
            while True:
                write_data(client, unit_id, function_code, address, count, random_values)
                time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Stopped continuous writing")
        click.echo("Stopped periodic writing")
    finally:
        client.close()

@momodbus.command()
@click.option("--protocol", type=click.Choice(["rtu", "tcp"], case_sensitive=False), default="rtu", help="Protocol: 'rtu' (serial) or 'tcp' (network).")
@click.option("--port", default=None, help="Serial port for RTU (e.g., /dev/ttys000).")
@click.option("--baudrate", type=int, default=9600, help="Baudrate for RTU (e.g., 9600).")
@click.option("--host", default="0.0.0.0", help="IP address for TCP (e.g., 0.0.0.0 for all interfaces).")
@click.option("--tcp-port", type=int, default=502, help="TCP port (default: 502).")
@click.option("--unit-id", type=int, default=1, help="Slave unit ID (default: 1).")
@click.option("--coils", type=int, default=1000, help="Number of coils (default: 1000).")
@click.option("--discrete-inputs", type=int, default=1000, help="Number of discrete inputs (default: 1000).")
@click.option("--holding-registers", type=int, default=1000, help="Number of holding registers (default: 1000).")
@click.option("--input-registers", type=int, default=1000, help="Number of input registers (default: 1000).")
@click.option("--random-init", is_flag=True, help="Initialize with random values (coils: True/False; registers: 0-max-register-value).")
@click.option("--max-register-value", type=int, default=65535, help="Maximum value for random registers (default: 65535).")
@click.option("--random-update", is_flag=True, help="Periodically update coils/registers with new random values (1 Hz).")
def slave(protocol, port, baudrate, host, tcp_port, unit_id, coils, discrete_inputs, holding_registers, input_registers, random_init, max_register_value, random_update):
    """Run as a Modbus slave/server.

    Examples:
        Start TCP server with random updates and max register value of 1000:
            ./momodbus.py slave --protocol tcp --tcp-port 10502 --unit-id 1 --random-init --random-update --max-register-value 1000
        Start RTU server:
            ./momodbus.py slave --protocol rtu --port /dev/ttys000 --baudrate 9600 --unit-id 1
    """
    if max_register_value < 0 or max_register_value > 65535:
        raise click.UsageError("max-register-value must be between 0 and 65535")

    context = initialize_server_context(coils, discrete_inputs, holding_registers, input_registers, random_init, max_register_value)
    
    # Start random value update thread if requested
    if random_update:
        update_thread = threading.Thread(
            target=update_random_values,
            args=(context, unit_id, coils, holding_registers, max_register_value, 1.0),
            daemon=True
        )
        update_thread.start()
        logger.info("Started random value update thread (1 Hz)")

    try:
        if protocol == "rtu":
            if not port or not baudrate:
                raise click.UsageError("Port and baudrate are required for RTU")
            logger.info(f"Starting RTU server: port={port}, baudrate={baudrate}, unit_id={unit_id}")
            click.echo(f"Starting RTU server on {port} (Ctrl+C to stop)")
            StartSerialServer(
                context=context,
                port=port,
                baudrate=baudrate,
                parity="N",
                stopbits=1,
                bytesize=8
            )
        else:  # tcp
            logger.info(f"Starting TCP server: host={host}, port={tcp_port}, unit_id={unit_id}")
            click.echo(f"Starting TCP server on {host}:{tcp_port} (Ctrl+C to stop)")
            StartTcpServer(
                context=context,
                address=(host, tcp_port)
            )
    except KeyboardInterrupt:
        logger.info("Stopped Modbus server")
        click.echo("Stopped Modbus server")
    except Exception as e:
        logger.error(f"Server error: {e}")
        click.echo(f"Server error: {e}")

if __name__ == "__main__":
    momodbus()
