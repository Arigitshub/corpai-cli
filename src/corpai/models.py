"""Data models for CorpAI roles, messages, and org structure."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class RankLevel(Enum):
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    OWNER = 6

    @classmethod
    def from_string(cls, s: str) -> Optional["RankLevel"]:
        s = s.strip().upper()
        if s == "OWNER":
            return cls.OWNER
        for member in cls:
            if member.name == s or s.startswith(member.name):
                return member
        return None


RANK_NAMES = {
    RankLevel.L1: "Operator",
    RankLevel.L2: "Specialist",
    RankLevel.L3: "Manager",
    RankLevel.L4: "Director",
    RankLevel.L5: "Executive",
    RankLevel.OWNER: "Human Principal",
}


class MessageType(Enum):
    TASK = "TASK"
    REPORT = "REPORT"
    ESCALATION = "ESCALATION"
    NOTIFICATION = "NOTIFICATION"
    OVERRIDE = "OVERRIDE"


class Priority(Enum):
    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4
    P5 = 5

    @classmethod
    def from_string(cls, s: str) -> Optional["Priority"]:
        s = s.strip().upper()
        for member in cls:
            if member.name == s:
                return member
        return None


REQUIRED_IDENTITY_FIELDS = {"rank", "reports to", "direct reports", "domain"}
REQUIRED_SECTIONS = {"identity", "responsibilities", "escalation triggers", "communication patterns"}


@dataclass
class Role:
    path: Path
    title: str
    rank: Optional[RankLevel]
    reports_to: str
    direct_reports: list[str]
    domain: str
    department: str
    responsibilities: list[str] = field(default_factory=list)
    escalation_triggers: list[dict] = field(default_factory=list)
    has_personality: bool = False
    raw_sections: dict[str, str] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        if self.rank and self.rank != RankLevel.OWNER:
            return f"[{self.rank.name}] {self.title}"
        return self.title


@dataclass
class LintError:
    path: Path
    level: str  # "error" | "warning"
    message: str
    field: Optional[str] = None


@dataclass
class OrgNode:
    role: Role
    children: list["OrgNode"] = field(default_factory=list)
    parent: Optional["OrgNode"] = None


@dataclass
class SimMessage:
    msg_type: MessageType
    from_role: str
    to_role: str
    priority: Priority
    subject: str
    step: int
