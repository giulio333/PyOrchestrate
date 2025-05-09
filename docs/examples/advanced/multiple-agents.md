---
title: Multiple Standalone Agents
---

# Multiple Standalone Agents Example

This advanced example demonstrates how to create, configure, and run multiple standalone agents simultaneously, each with different configurations and behaviors.

## Overview

In many real-world applications, you might need multiple agents working in parallel to monitor different aspects of a system. This example shows how to:

1. Create a sensor simulation agent with configurable parameters
2. Instantiate multiple instances of the same agent class with different configurations
3. Start all agents concurrently and wait for them to complete their tasks

## Agent Implementation

Let's create a `VirtualSensorAgent` that simulates readings from different types of sensors:

```python
import random
import time
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass

from PyOrchestrate.core.agent import PeriodicProcessAgent


class SensorType(Enum):
    """Supported sensor types."""

    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"


@dataclass
class SensorReading:
    """Represents a sensor reading with timestamp."""

    timestamp: float
    sensor_type: SensorType
    value: float
    location: str


class VirtualSensorAgent(PeriodicProcessAgent):
    """
    An agent that simulates periodic readings from a virtual sensor.
    Each agent can be configured to simulate a specific type of sensor
    with customized initial values and variance.
    """

    class Config(PeriodicProcessAgent.Config):
        sensor_type: SensorType = SensorType.TEMPERATURE
        location: str = "Main room"
        initial_value: float = 20.0
        max_variance: float = 1.0
        max_readings: int = 20
        execution_interval: float = 1.0

    config: Config

    def setup(self) -> None:
        """
        Agent initialization: sets initial values and prepares storage
        for sensor readings.
        """
        super().setup()

        # Current sensor value
        self.current_value = self.config.initial_value
        # List of readings
        self.readings: List[SensorReading] = []

        self.logger.info(
            f"Sensor agent {self.config.sensor_type.value} started in {self.config.location}"
        )
        self.logger.info(
            f"Initial values: {self.current_value} ± {self.config.max_variance}"
        )

    def generate_sensor_reading(self) -> SensorReading:
        """
        Generates a new sensor reading with a small random variation.

        Returns:
            SensorReading: The new sensor reading.
        """
        variance = random.uniform(-self.config.max_variance, self.config.max_variance)

        self.current_value += variance

        if self.config.sensor_type == SensorType.TEMPERATURE:
            self.current_value = max(min(self.current_value, 40.0), -10.0)
        elif self.config.sensor_type == SensorType.HUMIDITY:
            self.current_value = max(min(self.current_value, 100.0), 0.0)
        elif self.config.sensor_type == SensorType.PRESSURE:
            self.current_value = max(self.current_value, 900.0)

        # Create and return a new reading
        return SensorReading(
            timestamp=time.time(),
            sensor_type=self.config.sensor_type,
            value=round(self.current_value, 2),
            location=self.config.location,
        )

    def runner(self) -> None:
        """
        Performs a periodic reading from the virtual sensor.
        Terminates the agent when it reaches the maximum number of readings.
        """
        super().runner()

        if len(self.readings) >= self.config.max_readings:
            self.logger.info(
                f"Agent {self.config.sensor_type.value} has completed {self.config.max_readings} readings"
            )
            self.stop()
            return

        # Generate a new reading
        reading = self.generate_sensor_reading()
        self.readings.append(reading)

        self.logger.info(
            f"Reading {len(self.readings)}/{self.config.max_readings}: "
            f"{reading.sensor_type.value} in {reading.location} = "
            f"{reading.value}"
        )
```

This agent is a simulation of sensors that can measure temperature, humidity, or pressure. It generates readings with random variations and has built-in limits appropriate for each sensor type.

## Running Multiple Agents

Once we have the agent class defined, we can create multiple instances with different configurations:

```python
def run_multiple_sensor_agents():
    """
    Creates and starts multiple VirtualSensorAgent instances with different configurations.
    Waits for all agents to complete and prints a summary.
    """
    # Create three different sensor configurations
    temperature_config = VirtualSensorAgent.Config(
        sensor_type=SensorType.TEMPERATURE,
        location="Kitchen",
        initial_value=22.5,
        max_variance=0.5,
        max_readings=15,
        execution_interval=0.8,
    )

    humidity_config = VirtualSensorAgent.Config(
        sensor_type=SensorType.HUMIDITY,
        location="Bathroom",
        initial_value=65.0,
        max_variance=2.0,
        max_readings=10,
        execution_interval=1.2,
    )

    pressure_config = VirtualSensorAgent.Config(
        sensor_type=SensorType.PRESSURE,
        location="Outside",
        initial_value=1013.25,
        max_variance=0.75,
        max_readings=12,
        execution_interval=1.5,
        debug=True,
    )

    # Create agent instances
    temperature_agent = VirtualSensorAgent(config=temperature_config)
    humidity_agent = VirtualSensorAgent(config=humidity_config)
    pressure_agent = VirtualSensorAgent(config=pressure_config)

    # List of agents to manage them together
    agents = [temperature_agent, humidity_agent, pressure_agent]

    # Start all agents
    print("Starting sensor agents...")
    for agent in agents:
        agent.start()

    # Wait for all agents to complete
    for agent in agents:
        agent.join()

if __name__ == "__main__":
    run_multiple_sensor_agents()
```

## How It Works

1. **Configuration:** We create three different configurations for our sensor agents. Each configuration specifies:
   - The type of sensor (temperature, humidity, or pressure)
   - The location of the sensor
   - Initial value and maximum variance for the readings
   - Maximum number of readings to collect
   - Execution interval (how often readings are taken)

2. **Instantiation:** We create an instance of `VirtualSensorAgent` for each configuration. Each agent is independent and will simulate its specific sensor type.

3. **Parallel Execution:** We start all agents in parallel. Each agent runs in its own process due to inheriting from `PeriodicProcessAgent`.

4. **Synchronization:** We use the `join()` method to wait for all agents to complete their tasks. Each agent will stop automatically after collecting its configured maximum number of readings.

## When to Use This Pattern

Consider using multiple standalone agents when:

- You need to monitor or control multiple independent components
- You want to isolate failures (if one agent fails, others continue to function)
- Your agents need to run at different frequencies
- You want to utilize multiple CPU cores for better performance

::: tip Configuration Tip
When creating multiple instances of the same agent class with different configurations, it's best to create dedicated configuration objects rather than modifying default values. This ensures that each agent has a clear and well-defined behavior.
:::

## Complete Example

The complete example code is shown below:

```python
#!/usr/bin/env python3

import random
import time
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass

from PyOrchestrate.core.agent import PeriodicProcessAgent


class SensorType(Enum):
    """Supported sensor types."""

    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"


@dataclass
class SensorReading:
    """Represents a sensor reading with timestamp."""

    timestamp: float
    sensor_type: SensorType
    value: float
    location: str


class VirtualSensorAgent(PeriodicProcessAgent):
    """
    An agent that simulates periodic readings from a virtual sensor.
    Each agent can be configured to simulate a specific type of sensor
    with customized initial values and variance.
    """

    class Config(PeriodicProcessAgent.Config):
        sensor_type: SensorType = SensorType.TEMPERATURE
        location: str = "Main room"
        initial_value: float = 20.0
        max_variance: float = 1.0
        max_readings: int = 20
        execution_interval: float = 1.0

    config: Config

    def setup(self) -> None:
        """
        Agent initialization: sets initial values and prepares storage
        for sensor readings.
        """
        super().setup()

        # Current sensor value
        self.current_value = self.config.initial_value
        # List of readings
        self.readings: List[SensorReading] = []

        self.logger.info(
            f"Sensor agent {self.config.sensor_type.value} started in {self.config.location}"
        )
        self.logger.info(
            f"Initial values: {self.current_value} ± {self.config.max_variance}"
        )

    def generate_sensor_reading(self) -> SensorReading:
        """
        Generates a new sensor reading with a small random variation.

        Returns:
            SensorReading: The new sensor reading.
        """
        # Simulate a variation of the sensor value
        variance = random.uniform(-self.config.max_variance, self.config.max_variance)

        # Update the current value
        self.current_value += variance

        # Apply limits specific to sensor type
        if self.config.sensor_type == SensorType.TEMPERATURE:
            # Temperature has a realistic lower and upper limit
            self.current_value = max(min(self.current_value, 40.0), -10.0)
        elif self.config.sensor_type == SensorType.HUMIDITY:
            # Humidity between 0% and 100%
            self.current_value = max(min(self.current_value, 100.0), 0.0)
        elif self.config.sensor_type == SensorType.PRESSURE:
            # Atmospheric pressure cannot be negative
            self.current_value = max(self.current_value, 900.0)

        # Create and return a new reading
        return SensorReading(
            timestamp=time.time(),
            sensor_type=self.config.sensor_type,
            value=round(self.current_value, 2),
            location=self.config.location,
        )

    def runner(self) -> None:
        """
        Performs a periodic reading from the virtual sensor.
        Terminates the agent when it reaches the maximum number of readings.
        """
        super().runner()

        if len(self.readings) >= self.config.max_readings:
            self.logger.info(
                f"Agent {self.config.sensor_type.value} has completed {self.config.max_readings} readings"
            )
            self.stop()
            return

        # Generate a new reading
        reading = self.generate_sensor_reading()
        self.readings.append(reading)

        # Log the reading
        self.logger.info(
            f"Reading {len(self.readings)}/{self.config.max_readings}: "
            f"{reading.sensor_type.value} in {reading.location} = "
            f"{reading.value}"
        )

        self.logger.debug(
            f"Timestamp: {reading.timestamp}, Raw value: {self.current_value}"
        )

    def get_readings(self) -> List[SensorReading]:
        """
        Returns all readings recorded by this agent.

        Returns:
            List[SensorReading]: List of sensor readings.
        """
        return self.readings


def run_multiple_sensor_agents():
    """
    Creates and starts multiple VirtualSensorAgent instances with different configurations.
    Waits for all agents to complete and prints a summary.
    """
    # Create three different sensor configurations
    temperature_config = VirtualSensorAgent.Config(
        sensor_type=SensorType.TEMPERATURE,
        location="Kitchen",
        initial_value=22.5,
        max_variance=0.5,
        max_readings=15,
        execution_interval=0.8,
    )

    humidity_config = VirtualSensorAgent.Config(
        sensor_type=SensorType.HUMIDITY,
        location="Bathroom",
        initial_value=65.0,
        max_variance=2.0,
        max_readings=10,
        execution_interval=1.2,
    )

    pressure_config = VirtualSensorAgent.Config(
        sensor_type=SensorType.PRESSURE,
        location="Outside",
        initial_value=1013.25,
        max_variance=0.75,
        max_readings=12,
        execution_interval=1.5,
        debug=True,
    )

    # Create agent instances
    temperature_agent = VirtualSensorAgent(config=temperature_config)
    humidity_agent = VirtualSensorAgent(config=humidity_config)
    pressure_agent = VirtualSensorAgent(config=pressure_config)

    # List of agents to manage them together
    agents = [temperature_agent, humidity_agent, pressure_agent]

    # Start all agents
    print("Starting sensor agents...")
    for agent in agents:
        agent.start()

    # Wait for all agents to complete
    for agent in agents:
        agent.join()


if __name__ == "__main__":
    run_multiple_sensor_agents()
```
