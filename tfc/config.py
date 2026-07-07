"""TFCConfig: one simulator run's parameters + the f_guard validation port.

Mirrors the input surface of pine/baseline_continuity.pine that the gate
cells exercise. Deliberately NOT ported: size_down (no calibrated R2 dump
exists -- plan risk 3; S8 ratified stand_aside anyway) and reg_exit=true
(ablation knob, default off in every recorded run). Both fail loudly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tfc.periods import tf_seconds

__all__ = ["TFCConfig", "GuardError"]


class GuardError(ValueError):
    """Pine f_guard runtime.error equivalent: misaligned configs fail LOUDLY."""


@dataclass(frozen=True)
class TFCConfig:
    chart_tf: str
    exec_tfs: tuple[str, ...]
    reg_mode: str = "off"  # 'off' | 'stand_aside'
    reg_tfs: tuple[str, ...] = ("M", "W", "D")
    gov_mode: str = "off"  # 'off' | 'ratchet'
    comm_rate: float = 0.0  # fraction of fill notional (0.000125 = 0.0125%)
    slip_ticks: int = 1
    mintick: float = 0.001  # xyz MSTRUSDC.P; OKX MSTR is 0.01
    initial_capital: float = 10_000.0  # strategy() initial_capital
    qty_step: float = 0.001
    allow_long: bool = True
    allow_short: bool = True
    reg_exit: bool = field(default=False)  # ablation knob; True is NOT ported

    def __post_init__(self) -> None:
        if self.reg_mode not in ("off", "stand_aside"):
            raise GuardError(
                f"reg_mode '{self.reg_mode}' not ported (size_down has no calibrated "
                "reference dump -- capture a TV R2 dump first; plan risk 3)"
            )
        if self.gov_mode not in ("off", "ratchet"):
            raise GuardError(f"unknown gov_mode '{self.gov_mode}'")
        if self.reg_exit:
            raise GuardError("reg_exit=true is not ported (default-off ablation knob)")
        if not self.exec_tfs:
            raise GuardError("empty exec gate: n_enabled == 0 never trades")
        self._guard_tfs(self.exec_tfs)
        if self.reg_mode != "off":
            self._guard_tfs(self.reg_tfs)

    def _guard_tfs(self, tfs: tuple[str, ...]) -> None:
        """Port of f_guard: chart TF must be <= AND must tile every gate TF."""
        cs = tf_seconds(self.chart_tf)
        for tf in tfs:
            gs = tf_seconds(tf)
            if gs < cs:
                raise GuardError(f"Gate TF '{tf}' is finer than the chart TF ({self.chart_tf})")
            if gs >= 86400:
                if 86400 % cs != 0:
                    raise GuardError(
                        f"Chart TF {self.chart_tf} does not divide 1D -- D/W/M "
                        "period-open reconstruction would be approximate"
                    )
            elif gs % cs != 0:
                raise GuardError(
                    f"Gate TF '{tf}' is not an integer multiple of the chart TF "
                    f"({self.chart_tf}) -- reconstruction would be approximate"
                )

    @property
    def slip(self) -> float:
        """Slippage in price units per fill (adverse)."""
        return self.slip_ticks * self.mintick
