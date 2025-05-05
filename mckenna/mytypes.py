"""Custom types module.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""
from __future__ import annotations
from typing import Dict, Union, TypedDict, Literal, Optional

NestedDict = Dict[str, Union[str, int, float, bool, "NestedDict"]]


class Geometry(TypedDict):
    """Typing for geometry subdictionary."""

    type: Literal["impinging_jet", "free_flame"]
    domain_width: float
    burner_diameter: float


class UniformDistr(TypedDict):
    """Typing for uniform distribution."""

    distribution: Literal["uniform"]
    min: float
    max: float


class NormalDistr(TypedDict):
    """Typing for normal distribution."""

    distribution: Literal["normal"]
    mean: float
    stdev: float


class Submodels(TypedDict):
    """Typing for submodels."""

    radiation: bool
    transport: Literal[
        "mixture-averaged", "multicomponent", "unity-Lewis-number"
    ]
    soret: bool


class BoundaryConditions(TypedDict):
    """Typing for boundary conditions subdictionary."""

    pressure: float
    burner_temperature: Union[float, UniformDistr, NormalDistr]
    stagnation_temperature: Union[float, UniformDistr, NormalDistr]
    composition: Optional[str]
    fuel: Optional[str]
    flow_rates: Dict[str, Union[float, UniformDistr, NormalDistr]]


class Samples(TypedDict):
    """Typing for samples subdictionary."""

    epistemic_samples: int
    aleatory_samples: int


class Meshing(TypedDict):
    """Typing for meshing subdictionary."""

    grid_min_size: float
    max_grid_points: float
    ratio: float
    slope: float
    curve: float
    prune: float


class Settings(TypedDict):
    """Typing for settings subdictionary."""

    meshing: Meshing
    uq: Optional[Samples]


class ConfigDict(TypedDict):
    """Typing for config file dictionary."""

    mode: Literal["uq", "single"]
    mechanism: str
    geometry: Geometry
    boundary_conditions: BoundaryConditions
    submodels: Submodels
    settings: Settings
