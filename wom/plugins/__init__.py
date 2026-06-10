"""WOM built-in plugins."""
from wom.plugins.demand_smoothing   import DemandSmoothingPlugin
from wom.plugins.capacity_override  import CapacityOverridePlugin
from wom.engine.harvest_batch_plugin import HarvestBatchPlugin

ALL_BUILTIN_PLUGINS = [
    DemandSmoothingPlugin,
    CapacityOverridePlugin,
    HarvestBatchPlugin,
]
