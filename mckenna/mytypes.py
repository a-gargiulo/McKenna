"""Custom types module.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""
from __future__ import annotations
from typing import Dict, Union

NestedDict = Dict[str, Union[str, int, float, bool, "NestedDict"]]
