#!/usr/bin/env python3
"""
Fan control script for Raspberry Pi
Controls PWM fan based on CPU temperature
"""

import argparse
import configparser
import logging
import os
import sys
import time
from typing import NoReturn

import lgpio

# Default configuration
DEFAULT_CONFIG_FILE = "/etc/fan_control.conf"
DEFAULT_PWM_GPIO_NR = 14
DEFAULT_WAIT_TIME = 10
DEFAULT_PWM_FREQ = 10000

DEFAULT_MIN_TEMP = 55
DEFAULT_MIN_COOL_TEMP = 50
DEFAULT_MAX_TEMP = 75
DEFAULT_FAN_LOW = 50
DEFAULT_FAN_HIGH = 100
DEFAULT_FAN_OFF = 0
DEFAULT_FAN_MAX = 100

# Global variables
REMAIN_ACTIVATED = 0
args = None


def get_cpu_temperature() -> float:
    """
    Reads the CPU temperature from the system file.
    
    Returns:
        float: The current CPU temperature in Celsius.
    
    Raises:
        IOError: If unable to read the temperature file.
    """
    try:
        with open('/sys/devices/virtual/thermal/thermal_zone0/temp', 'r') as f:
            return float(f.read()) / 1000
    except (IOError, FileNotFoundError) as e:
        logging.error(f"Failed to read CPU temperature: {e}")
        raise


def set_fan_speed(fan: int, speed: float, curr_temp: float) -> None:
    """
    Sets the fan speed using PWM and logs the action.
    
    Args:
        fan (int): The fan control object.
        speed (float): The desired fan speed as a percentage (0-100).
        curr_temp (float): The current CPU temperature.
    
    Raises:
        lgpio.error: If unable to set the PWM.
    """
    try:
        # Convert percentage to duty cycle (0-1 range)
        duty_cycle = speed / 100.0
        lgpio.tx_pwm(fan, args.pwm_gpio, args.pwm_freq, duty_cycle)
        logging.info(f"Fan speed: {int(speed)}%, Temperature: {curr_temp:.1f}°C")
    except lgpio.error as e:
        logging.error(f"Failed to set fan speed: {e}")
        raise


def handle_fan_speed(fan: int) -> None:
    """
    Adjusts the fan speed based on the current CPU temperature.
    
    Args:
        fan (int): The fan control object.
    """
    global REMAIN_ACTIVATED
    curr_temp = get_cpu_temperature()
    
    # Fan off condition
    if not REMAIN_ACTIVATED and curr_temp < args.min_temp:
        set_fan_speed(fan, DEFAULT_FAN_OFF, curr_temp)
        return
    
    REMAIN_ACTIVATED = 1
    
    # Turn off the fan (cooling threshold)
    if curr_temp < args.min_cool_temp:
        set_fan_speed(fan, DEFAULT_FAN_OFF, curr_temp)
        REMAIN_ACTIVATED = 0
    
    # Low speed mode
    elif curr_temp < args.min_temp:
        set_fan_speed(fan, DEFAULT_FAN_LOW, curr_temp)
    
    # Maximum speed mode
    elif curr_temp > args.max_temp:
        set_fan_speed(fan, DEFAULT_FAN_MAX, curr_temp)
    
    # Dynamic fan speed
    else:
        adaptive_percentage = (curr_temp - args.min_temp) / (args.max_temp - args.min_temp)
        fan_activation_range = args.fan_high - args.fan_low
        new_speed = args.fan_low + (fan_activation_range * adaptive_percentage)
        set_fan_speed(fan, new_speed, curr_temp)


def shutdown(fan: int) -> None:
    """
    Performs a clean shutdown of the fan control.
    
    Args:
        fan (int): The fan control object.
    """
    try:
        # Set fan to low speed before shutdown
        set_fan_speed(fan, DEFAULT_FAN_LOW, 0)
        lgpio.gpiochip_close(fan)
        logging.info("Fan control shutdown complete.")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")


def main() -> NoReturn:
    """
    Main function to control the fan based on CPU temperature.
    
    This function runs in an infinite loop, periodically checking the CPU temperature
    and adjusting the fan speed accordingly.
    
    Raises:
        SystemExit: If a critical error occurs during execution.
    """
    fan_control = None
    try:
        # Open GPIO chip
        fan_control = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(fan_control, args.pwm_gpio)
        
        # Initialize fan with low speed
        set_fan_speed(fan_control, args.fan_low, 0)
        
        logging.info(f"Fan control started on GPIO {args.pwm_gpio}")
        
        while True:
            handle_fan_speed(fan_control)
            time.sleep(args.wait_time)
            
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Shutting down...")
    except Exception as e:
        logging.critical(f"Critical error occurred: {e}")
        raise SystemExit(1)
    finally:
        if fan_control is not None:
            shutdown(fan_control)
        return 0


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments for the fan control script.
    
    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Fan control script for Raspberry Pi",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--config", 
        default=DEFAULT_CONFIG_FILE, 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--min-temp", 
        type=int, 
        default=DEFAULT_MIN_TEMP, 
        help="Minimum temperature for fan activation"
    )
    parser.add_argument(
        "--min-cool-temp", 
        type=int, 
        default=DEFAULT_MIN_COOL_TEMP, 
        help="Minimum temperature for fan deactivation"
    )
    parser.add_argument(
        "--max-temp", 
        type=int, 
        default=DEFAULT_MAX_TEMP, 
        help="Maximum temperature for fan speed"
    )
    parser.add_argument(
        "--fan-low", 
        type=int, 
        default=DEFAULT_FAN_LOW, 
        help="Minimum fan speed percentage"
    )
    parser.add_argument(
        "--fan-high", 
        type=int, 
        default=DEFAULT_FAN_HIGH, 
        help="Maximum fan speed percentage"
    )
    parser.add_argument(
        "--wait-time", 
        type=int, 
        default=DEFAULT_WAIT_TIME, 
        help="Wait time between temperature checks"
    )
    parser.add_argument(
        "--pwm-gpio", 
        type=int, 
        default=DEFAULT_PWM_GPIO_NR, 
        help="GPIO pin for PWM fan control"
    )
    parser.add_argument(
        "--pwm-freq", 
        type=int, 
        default=DEFAULT_PWM_FREQ, 
        help="PWM frequency"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> None:
    """
    Parses the configuration file and updates the argument values.
    
    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    
    Raises:
        configparser.Error: If there's an error reading the configuration file.
    """
    config = configparser.ConfigParser()
    if os.path.exists(args.config):
        try:
            config.read(args.config)
            args.min_temp = config.getint('FanControl', 'min_temp', fallback=args.min_temp)
            args.min_cool_temp = config.getint('FanControl', 'min_cool_temp', fallback=args.min_cool_temp)
            args.max_temp = config.getint('FanControl', 'max_temp', fallback=args.max_temp)
            args.fan_low = config.getint('FanControl', 'fan_low', fallback=args.fan_low)
            args.fan_high = config.getint('FanControl', 'fan_high', fallback=args.fan_high)
            args.wait_time = config.getint('FanControl', 'wait_time', fallback=args.wait_time)
            args.pwm_gpio = config.getint('FanControl', 'pwm_gpio', fallback=args.pwm_gpio)
            args.pwm_freq = config.getint('FanControl', 'pwm_freq', fallback=args.pwm_freq)
            logging.info(f"Loaded configuration from {args.config}")
        except configparser.Error as e:
            logging.warning(f"Error reading config file: {e}. Using default values.")


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration file
    load_config(args)
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/fan_control.log')
        ]
    )
    
    logging.info(f"Starting fan control with settings: {vars(args)}")
    
    try:
        sys.exit(main())
    except SystemExit as e:
        sys.exit(e.code)
