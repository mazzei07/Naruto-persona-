from __future__ import annotations

from typing import Any, Dict, List


VERSION = "v30.0-scene-agenda-scheduler"


def compile_scene_agendas(scene: Dict[str, Any], actors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compile parallel NPC agendas before prose.

    This never chooses voluntary actions for a player-controlled actor.
    It only exposes what each NPC is currently trying to do, can perceive,
    and what can interrupt or pre-empt that agenda.
    """
    rows = []
    for item in actors or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("actor") or item.get("name") or "")
        if not name:
            continue
        player_controlled = bool(item.get("player_controlled")) or name == "Amatsu Uchiha"
        rows.append({
            "actor": name,
            "player_controlled": player_controlled,
            "position": item.get("position", "unknown"),
            "body_state": item.get("body_state", "unknown"),
            "perception": item.get("perception", []),
            "knowledge": item.get("knowledge", []),
            "current_objective": None if player_controlled else item.get("objective", ""),
            "current_action": None if player_controlled else item.get("current_action", ""),
            "attention_target": item.get("attention_target", ""),
            "urgency": item.get("urgency", "normal"),
            "reaction_window": item.get("reaction_window", "continuous"),
            "can_interrupt": item.get("can_interrupt", []),
            "must_not_assume": item.get("must_not_assume", []),
        })

    return {
        "version": VERSION,
        "scene": {
            "location": scene.get("location", ""),
            "time": scene.get("time", ""),
            "geometry": scene.get("geometry", ""),
            "public_pressure": scene.get("public_pressure", ""),
        },
        "agendas": rows,
        "scheduling_rules": [
            "NPCs do not freeze while another actor speaks or attacks.",
            "Resolve simultaneous actions by timing, distance, line of sight, attention, body state, and prior commitment.",
            "A reaction consumes time and attention; it cannot retroactively erase an already-started action.",
            "Speech competes with breath, movement, perception, and combat pressure.",
            "Only actors with a legitimate trigger react; spectators do not receive mandatory turns.",
            "Player-controlled Amatsu receives no inferred voluntary objective/action/reaction.",
            "When multiple NPCs could respond, rank by relevance and urgency rather than round-robin order.",
        ],
        "narration_order": [
            "establish concrete spatial/action change",
            "show the most causally relevant body/perception response",
            "allow speech only where it changes the scene",
            "carry simultaneous agendas forward",
            "leave an actionable window for the player when combat or decision belongs to Amatsu",
        ],
    }


def audit_scene_output(compiled: Dict[str, Any], proposed: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    actions = proposed.get("actions", []) if isinstance(proposed, dict) else []
    speakers = proposed.get("speakers", []) if isinstance(proposed, dict) else []

    if any((a.get("actor") == "Amatsu Uchiha" and a.get("source") != "user") for a in actions if isinstance(a, dict)):
        issues.append("player_control_violation")

    if len(speakers) >= 4 and proposed.get("single_shared_stimulus"):
        issues.append("possible_reaction_queue")

    if proposed.get("retroactive_counter"):
        issues.append("retroactive_counter_forbidden")

    if proposed.get("simultaneous_scene") and not proposed.get("causal_timing_checked"):
        issues.append("simultaneous_actions_need_timing_check")

    return {
        "status": "blocked" if issues else "reviewable",
        "issues": issues,
        "version": VERSION,
    }
