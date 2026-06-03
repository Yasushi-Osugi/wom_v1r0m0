"""Main cockpit action for the Run Full Plan standard-output viewer path.

This module intentionally keeps Tk window creation out of import-time code so the
main cockpit can import it safely and tests can exercise the orchestration
helpers without opening a GUI.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pysi.runners.run_full_plan import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RUN_MODE,
    DEFAULT_SCENARIO_ID,
    WomRunConfig,
    run_full_plan,
    write_full_plan_outputs,
)

DEFAULT_COCKPIT_VIEWER_SCENARIO_ROOT = "examples/scenarios/japanese_rice_vslice_001"
COCKPIT_VIEWER_RUN_ID_PREFIX = "cockpit_viewer_"


def make_cockpit_viewer_run_id(now: datetime | None = None) -> str:
    """Return a timestamped run id for main-cockpit viewer launches."""

    effective_now = now or datetime.now()
    return f"{COCKPIT_VIEWER_RUN_ID_PREFIX}{effective_now:%Y%m%d_%H%M%S}"


def build_cockpit_viewer_run_config(
    *,
    scenario_root: str,
    scenario_id: str = DEFAULT_SCENARIO_ID,
    run_id: str | None = None,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> WomRunConfig:
    """Build the conservative v0r1 cockpit viewer Run Full Plan config."""

    return WomRunConfig(
        scenario_root=scenario_root,
        scenario_id=scenario_id,
        run_id=run_id or make_cockpit_viewer_run_id(),
        run_mode=DEFAULT_RUN_MODE,
        output_dir=output_dir,
    )


def run_full_plan_and_open_viewer(config: WomRunConfig) -> int:
    """Run the standard-output bridge, write artifacts, and open the viewer."""

    from pysi.gui.wom_run_full_plan_result_viewer import (
        launch_run_full_plan_result_viewer,
    )

    result = run_full_plan(config)
    result = write_full_plan_outputs(result, output_dir=config.output_dir)
    run_dir = Path(config.output_dir) / result.run_id
    return launch_run_full_plan_result_viewer(run_dir)
