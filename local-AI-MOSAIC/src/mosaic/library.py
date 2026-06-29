"""The persistent capability library.

Loads capabilities from YAML, holds them in memory for retrieval, and persists
the *evolving* state (performance scores, usage counts, learned synergies and
incompatibilities) to a small JSON file so learning survives restarts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

import yaml

from mosaic.schema import Capability


class CapabilityLibrary:
    def __init__(self, capabilities: Optional[Iterable[Capability]] = None):
        self._caps: dict[str, Capability] = {}
        for c in capabilities or []:
            self.add(c)

    def __len__(self) -> int:
        return len(self._caps)

    def __iter__(self):
        return iter(self._caps.values())

    def __contains__(self, cap_id: str) -> bool:
        return cap_id in self._caps

    def add(self, cap: Capability) -> None:
        self._caps[cap.id] = cap

    def get(self, cap_id: str) -> Optional[Capability]:
        return self._caps.get(cap_id)

    def all(self) -> list[Capability]:
        return list(self._caps.values())

    @classmethod
    def from_dir(cls, path: str | Path) -> "CapabilityLibrary":
        lib = cls()
        for f in sorted(Path(path).glob("**/*.y*ml")):
            data = yaml.safe_load(f.read_text()) or {}
            items = data if isinstance(data, list) else data.get("capabilities", [data])
            for item in items:
                if item:
                    lib.add(Capability(**item))
        return lib

    def find_similar(self, cap: Capability, by_domain: bool = True,
                     by_role: bool = True, exclude_self: bool = True) -> list[Capability]:
        out: list[Capability] = []
        target_domains = set(cap.domain_expertise)
        for other in self._caps.values():
            if exclude_self and other.id == cap.id:
                continue
            if by_role and other.role != cap.role:
                continue
            if by_domain and not (set(other.domain_expertise) & target_domains):
                continue
            out.append(other)
        return out

    def archive(self, cap_id: str) -> Optional[Capability]:
        """Remove from active library (whitepaper: prune low performers).

        Note: this only drops the in-memory entry; the source YAML is never
        modified or deleted.
        """
        return self._caps.pop(cap_id, None)

    # --- persistence of evolving state ---
    def save_state(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        state = {
            cid: {
                "performance_score": c.performance_score,
                "usage_count": c.usage_count,
                "successful_compositions": c.successful_compositions,
                "incompatible_capabilities": c.incompatible_capabilities,
            }
            for cid, c in self._caps.items()
        }
        p.write_text(json.dumps(state, indent=2))

    def load_state(self, path: str | Path) -> None:
        p = Path(path)
        if not p.exists():
            return
        state = json.loads(p.read_text())
        for cid, s in state.items():
            c = self._caps.get(cid)
            if not c:
                continue
            c.performance_score = s.get("performance_score", c.performance_score)
            c.usage_count = s.get("usage_count", c.usage_count)
            c.successful_compositions = s.get("successful_compositions", c.successful_compositions)
            c.incompatible_capabilities = s.get("incompatible_capabilities", c.incompatible_capabilities)
