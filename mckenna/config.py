"""Input file parser and validator.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""

# TODO: Handle unexpected keys in the configuration file.
import os
import yaml
from typing import Any, Dict, List, Type, Optional, Union, Tuple
from mckenna.utility import parse_composition


class ConfigValidationError(Exception):
    """Custom exception to collect all configuration file parsing errors."""

    pass


class ConfigValidator:
    """Custom config file validator class."""

    def __init__(self, config: dict) -> None:
        """Construct a custom validator.

        :param config: The content of the YAML configuration file.
        """
        self.config = config
        self.mode = config.get("mode")

    def validate(self):
        """Validate the confiuration file content."""
        self._require("mode", str, allowed=["uq", "single"])
        self._require("mechanism", str)
        self._validate_geometry()
        self._validate_boundary_conditions()
        self._validate_submodels()
        self._validate_settings()

    def _require(
        self,
        key: str,
        expected_type: Union[Type, Tuple[Type, ...]],
        parent: Optional[Dict[str, Any]] = None,
        allowed: Optional[List[Any]] = None,
    ):
        ctx = self.config if parent is None else parent
        if key not in ctx:
            raise ConfigValidationError(f"Missing required field: '{key}'")
        value = ctx[key]
        if not isinstance(value, expected_type):
            type_names = (
                expected_type.__name__
                if isinstance(expected_type, type)
                else ", ".join(t.__name__ for t in expected_type)
            )
            raise ConfigValidationError(
                f"'{key}' must be of type {type_names}"
            )
        if allowed and value not in allowed:
            raise ConfigValidationError(f"'{key}' must be one of: {allowed}")
        return value

    def _validate_geometry(self):
        geom = self._require("geometry", dict)
        self._require(
            "type", str, geom, allowed=["free_flame", "impinging_jet"]
        )
        self._require("domain_width", (int, float), geom)
        self._require("burner_diameter", (int, float), geom)

    def _validate_boundary_conditions(self):
        bc = self._require("boundary_conditions", dict)
        if self.mode == "uq":
            self._validate_stat_field(bc, "burner_temperature")
            self._validate_stat_field(bc, "stagnation_temperature")
            self._validate_flow_rates(
                bc.get("flow_rates", {}), expect_stat=True
            )
        elif self.mode == "single":
            self._require("composition", str, bc)
            try:
                comp = parse_composition(bc["composition"])
            except ValueError as e:
                raise ConfigValidationError(f"Invalid composition string: {e}")
            self._validate_numeric_field(bc, "burner_temperature")
            self._validate_numeric_field(bc, "stagnation_temperature")
            self._validate_flow_rates(
                bc.get("flow_rates", {}), expect_stat=False, comp=comp
            )
        else:
            raise ConfigValidationError(f"Invalid mode: {self.mode}")

    def _validate_stat_field(self, parent: Dict[str, Any], key: str):
        val = parent.get(key)
        if val is None:
            raise ConfigValidationError(f"'{key}' is required but not found")

        if not isinstance(val, dict):
            raise ConfigValidationError(f"'{key}' must be a dict in 'uq' mode")
        dist = self._require(
            "distribution", str, val, allowed=["uniform", "normal"]
        )
        if dist == "uniform":
            for param in ["min", "max"]:
                self._require(param, (int, float), val)
        elif dist == "normal":
            for param in ["mean", "stdev"]:
                self._require(param, (int, float), val)

    def _validate_numeric_field(self, parent: Dict[str, Any], key: str):
        val = parent.get(key)
        if val is None:
            raise ConfigValidationError(f"'{key}' is required but not found")

        if not isinstance(val, (int, float)):
            raise ConfigValidationError(
                f"'{key}' must be a float in 'single' mode"
            )

    def _validate_flow_rates(
        self,
        rates: Dict[str, Any],
        expect_stat: bool,
        comp: Optional[List[str]] = None,
    ):
        if not isinstance(rates, dict):
            raise ConfigValidationError("'flow_rates' must be a dictionary")

        if expect_stat is False:
            assert (
                comp is not None
            ), "When 'expect_stat' is 'False', 'comp' must be provided."
            missing_species = [sp for sp in comp if sp not in rates]
            if missing_species:
                raise ConfigValidationError(
                    "Composition species missing in "
                    f"flow_rates: {missing_species}"
                )

        for gas, val in rates.items():
            if expect_stat:
                self._validate_stat_field(rates, gas)
            else:
                self._validate_numeric_field(rates, gas)

    def _validate_submodels(self):
        sub = self._require("submodels", dict)
        self._require("radiation", bool, sub)
        transport = self._require(
            "transport",
            str,
            sub,
            allowed=[
                "mixture-averaged",
                "multicomponent",
                "unity-Lewis-number",
            ],
        )
        soret = self._require("soret", bool, sub)
        if soret and transport != "multicomponent":
            raise ConfigValidationError(
                "'soret' can only be true if 'transport' is 'multicomponent'"
            )

    def _validate_settings(self):
        settings = self._require("settings", dict)
        meshing = self._require("meshing", dict, settings)
        for key in [
            "grid_min_size",
            "max_grid_points",
            "ratio",
            "slope",
            "curve",
            "prune",
        ]:
            self._require(key, (int, float), meshing)
        if self.mode == "uq":
            uq_settings = self._require("uq", dict, settings)
            self._require("epistemic_samples", int, uq_settings)
            self._require("aleatory_samples", int, uq_settings)
        else:
            if "uq" in settings:
                raise ConfigValidationError(
                    "'settings.uq' should not be present in 'single' mode"
                )


def load_yaml_config(path: str) -> dict:
    """Load the YAML configuration file.

    :param path: Path to the configuration file.
    :raises ConfigValidationError: If loading the YAML file fails at any step.
    :return: The YAML configuration file content.
    :rtype: dict
    """
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"YAML syntax error: {e}")
    except FileNotFoundError:
        raise ConfigValidationError(f"Configuration file not found: {path}")
    except Exception as e:
        raise ConfigValidationError(
            f"Unexpected error while loading YAML: {e}"
        )


def validate_config_file(path: str) -> None:
    """Validate the YAML configuration file.

    :param path: Path to the configuration file.
    :raises ConfigValidationError: If there was an error in loading
        and validating the configuration file.
    """
    try:
        config = load_yaml_config(path)
        validator = ConfigValidator(config)
        validator.validate()
        print(
            f"[INFO]: '{os.path.basename(path)}' successfully "
            "loaded and validated."
        )
    except ConfigValidationError as e:
        print(f"[ERROR]: {e}")
