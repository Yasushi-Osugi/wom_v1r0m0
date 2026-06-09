"""WOM built-in plugins."""
from wom.plugins.demand_smoothing   import DemandSmoothingPlugin
from wom.plugins.capacity_override  import CapacityOverridePlugin

ALL_BUILTIN_PLUGINS = [DemandSmoothingPlugin, CapacityOverridePlugin]
