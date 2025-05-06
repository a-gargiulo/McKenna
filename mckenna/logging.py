"""Some utility logging functions.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""
from colorama import init, Fore, Style
import datetime


init(autoreset=True)


def log_info(message: str) -> None:
    """Log an information message.

    :param message: Message to log.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"[{timestamp}] "
        f"[{Fore.BLUE}{Style.BRIGHT}INFO{Style.RESET_ALL}]: "
        f"{message}"
    )


def log_warning(message: str) -> None:
    """Log a warning message.

    :param message: Message to log.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"[{timestamp}] "
        f"[{Fore.YELLOW}{Style.BRIGHT}WARNING{Style.RESET_ALL}]: "
        f" {message}"
    )


def log_todo(message: str) -> None:
    """Log a todo message.

    :param message: Message to log.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"[{timestamp}] "
        f"[{Fore.GREEN}{Style.BRIGHT}TODO{Style.RESET_ALL}]: "
        f" {message}"
    )


def log_error(message: str) -> None:
    """Log an error message.

    :param message: Message to log.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"[{timestamp}] "
        f"[{Fore.RED}{Style.BRIGHT}ERROR{Style.RESET_ALL}]: "
        f"{message}"
    )
