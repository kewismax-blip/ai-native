from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import json
from typing import Any

from game_content import (
    AI_REVIEW_ITEMS,
    ALIGNMENT_OPTIONS_BY_ROLE,
    ALIGNMENT_ROLES,
    ANONYMOUS_RANKING,
    BADGE_DEFINITIONS,
    BOUNDED_KEYS,
    BOSS_QUESTIONS,
    ENDING_DEFINITIONS,
    EVIDENCE_ITEMS,
    FOOD_DEFINITIONS,
    LEVEL_THRESHOLDS,
    MINIGAME_FOOD_MAP,
    PRIORITY_TASKS,
    RANDOM_EVENTS,
    RANDOM_REWARDS,
    REMEDIATION_QUESTIONS,
    SCENES,
    SCOPE_BUDGET,
    SCOPE_TASKS,
    STAGE_FOUR_BONUS_EVENTS,
    STAGE_FOUR_EVIDENCE_CARDS,
    STAT_KEYS,
)


def ending_display_payload(ending_id: str, unlocked: bool) -> dict[str, str]:
    """Return user-facing ending archive text without leaking internal ids."""
    definition = ENDING_DEFINITIONS.get(ending_id, {})
    hidden = bool(definition.get("hidden")) or ending_id == "yaya_partner"
    if unlocked:
        return {
            "title": str(definition.get("name") or "未知结局"),
            "description": str(definition.get("description") or ""),
            "status": "已解锁",
        }
    if hidden:
        return {
            "title": "隐藏结局",
            "description": "达成特殊条件后解锁",
            "status": "未解锁",
        }
    return {
        "title": "结局未解锁",
        "description": "继续挑战可发现新的成长结局",
        "status": "未解锁",
    }


def initial_companion_state() -> dict[str, Any]:
    return {
        "id": "yaya",
        "name": "芽芽",
        "growth_points": 0,
        "stage": 1,
        "stage_name": "初来乍到",
        "mood": "期待",
        "food_inventory": {
            "verification_berry": 0,
            "action_cookie": 0,
            "evidence_star": 0,
            "review_cookie": 0,
        },
        "fed_rewards": {},
        "hint_tokens": 0,
        "energy_recovered": False,
        "last_reaction": "我会陪你完成这次方案救火。",
        "trait": None,
        "stage_rewards_claimed": {},
        "third_act_collaboration_hint": False,
    }


def initial_stage_three_state() -> dict[str, Any]:
    return {
        "started": False,
        "completed": False,
        "alignment_score": 0,
        "scope_score": 0,
        "bonus_score": 0,
        "clarity": 30,
        "team_trust": 30,
        "selected_scope": {},
        "random_event_id": None,
        "random_seed": None,
        "bonus_task_result": None,
        "reward_claimed": False,
    }


def initial_progression_state() -> dict[str, Any]:
    return {
        "check_in_count": 0,
        "streak": 0,
        "badge_fragments": 0,
        "badges": {},
        "reward_history": [],
        "anonymous_rank": None,
        "completed_acts": {},
    }


def initial_stage_four_state() -> dict[str, Any]:
    return {
        "started": False,
        "completed": False,
        "evidence_board": {
            "slots": {"user": None, "data": None, "execution": None, "risk": None},
            "support_cards": [],
            "submitted": False,
            "score": 0,
            "coverage": 0,
            "weak_slots": [],
        },
        "loadout": {
            "hint_tokens": 0,
            "reroll_cards": 0,
            "evidence_boost_cards": 0,
            "collaboration_cards": 0,
            "selected_items": [],
            "fragments_spent": 0,
        },
        "boss": {
            "seed": None,
            "questions": [],
            "current_index": 0,
            "credibility": 70,
            "answers": [],
            "score": 0,
            "used_items": [],
            "remediation_tasks": [],
            "completed": False,
        },
        "bonus_task": {
            "event_id": None,
            "submitted": False,
            "success": False,
            "reward_claimed": False,
        },
        "final_result": None,
    }


def initial_post_game_state() -> dict[str, Any]:
    return {
        "unlocked": False,
        "run_count": 0,
        "current_ending": None,
        "endings_unlocked": {},
        "ending_archive": [],
        "challenge_history": [],
        "new_game_plus_unlocked": False,
    }


def initial_game_state() -> dict[str, Any]:
    return {
        "version": 1,
        "mode": "quick",
        "started": False,
        "scene_id": "prologue",
        "xp": 0,
        "energy": 100,
        "mentor_trust": 30,
        "risk": 20,
        "stats": {
            "business": 25,
            "ai_collaboration": 30,
            "verification": 20,
            "collaboration": 20,
            "delivery": 15,
        },
        "processed_actions": {},
        "pending_feedback": None,
        "pending_next_scene": None,
        "badges": {},
        "inventory": {},
        "quests": {},
        "minigame_results": {},
        "history": [],
        "ending_id": None,
        "checkpoint_id": None,
        "current_act": "act_one",
        "stage_two_context": {},
        "stage_two_scores": {},
        "stage_two_result": None,
        "stage_three_preview": False,
        "stage_three": initial_stage_three_state(),
        "stage_three_result": None,
        "stage_four_preview": False,
        "progression": initial_progression_state(),
        "stage_four": initial_stage_four_state(),
        "post_game": initial_post_game_state(),
        "companion": initial_companion_state(),
        "reset_version": 0,
    }


def clamp(value: int | float) -> int:
    return max(0, min(100, round(value)))


def calculate_level(xp: int) -> tuple[int, str]:
    level, title = LEVEL_THRESHOLDS[0][1], LEVEL_THRESHOLDS[0][2]
    for threshold, candidate_level, candidate_title in LEVEL_THRESHOLDS:
        if xp < threshold:
            break
        level, title = candidate_level, candidate_title
    return level, title


def current_scene(game: dict[str, Any]) -> dict[str, Any]:
    return SCENES.get(game.get("scene_id", "prologue"), SCENES["prologue"])


def current_week(game: dict[str, Any]) -> int:
    return int(current_scene(game).get("week", 0))


def current_chapter(game: dict[str, Any]) -> str:
    return str(current_scene(game).get("chapter", "序章"))


def start_game(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    if updated.get("scene_id") == "prologue":
        updated["started"] = True
        updated["scene_id"] = SCENES["prologue"]["next_scene"]
    return updated


def _read_value(game: dict[str, Any], key: str) -> int:
    if key in STAT_KEYS:
        return int(game["stats"][key])
    return int(game[key])


def _write_value(game: dict[str, Any], key: str, value: int) -> None:
    if key in STAT_KEYS:
        game["stats"][key] = clamp(value)
    elif key in BOUNDED_KEYS:
        game[key] = clamp(value)
    elif key == "xp":
        game[key] = max(0, value)


def apply_choice(game: dict[str, Any], scene_id: str, option_id: str) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(game)
    action_key = f"{scene_id}:{option_id}"
    if updated.get("scene_id") != scene_id:
        return updated, False
    if updated.get("pending_feedback") is not None or action_key in updated.get("processed_actions", {}):
        return updated, False

    scene = SCENES.get(scene_id, {})
    option = scene.get("options", {}).get(option_id)
    if not option:
        return updated, False
    scene_title = scene.get("title", "未命名场景")
    option_title = option.get("title", option.get("text", "未命名选项"))

    changes: dict[str, dict[str, int]] = {}
    for key, delta in option.get("effects", {}).items():
        before = _read_value(updated, key)
        _write_value(updated, key, before + int(delta))
        after = _read_value(updated, key)
        changes[key] = {"before": before, "after": after, "delta": after - before}

    updated["processed_actions"][action_key] = True
    updated["pending_next_scene"] = option.get("next_scene")
    updated["pending_feedback"] = {
        "scene_id": scene_id,
        "option_id": option_id,
        "option_title": option_title,
        "feedback": option.get("feedback", "选择已经记录。"),
        "mentor_signal": option.get("mentor_signal", "导师会关注你的判断过程。"),
        "hr_signal": option.get("hr_signal", "暂无明显HR风险信号。"),
        "changes": changes,
        "xp_gained": changes.get("xp", {}).get("delta", 0),
    }
    updated["history"].append({
        "scene_id": scene_id,
        "scene_title": scene_title,
        "option_id": option_id,
        "option_title": option_title,
        "changes": deepcopy(changes),
    })
    return updated, True


def advance_scene(game: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(game)
    next_scene = updated.get("pending_next_scene")
    if not next_scene or next_scene not in SCENES:
        return updated, False
    updated["scene_id"] = next_scene
    updated["pending_feedback"] = None
    updated["pending_next_scene"] = None
    if next_scene == "stage_one_complete":
        updated["checkpoint_id"] = "stage_one_complete"
        updated["ending_id"] = None
        updated["current_act"] = "act_one"
        record_stage_check_in(updated, "act_one")
    return updated, True


def reset_game(game: dict[str, Any]) -> dict[str, Any]:
    reset_version = int(game.get("reset_version", 0)) + 1
    reset = initial_game_state()
    reset["reset_version"] = reset_version
    return reset


def stage_one_style(game: dict[str, Any]) -> str:
    option_ids = {(item["scene_id"], item["option_id"]) for item in game.get("history", [])}
    if ("scene_week2_ai_check", "B") in option_ids:
        return "证据稳健型"
    if ("scene_week2_ai_check", "A") in option_ids:
        return "速度优先型"
    if ("scene_week1_business_map", "C") in option_ids:
        return "AI效率优先型"
    if ("scene_week1_business_map", "B") in option_ids:
        return "导师协作型"
    if ("scene_week1_business_map", "A") in option_ids:
        return "独立分析型"
    return "成长探索型"


def calculate_companion_stage(growth_points: int) -> tuple[int, str]:
    if growth_points >= 12:
        return 6, "团队协调者"
    if growth_points >= 10:
        return 5, "协作侦察员"
    if growth_points >= 9:
        return 4, "证据守护者"
    if growth_points >= 6:
        return 3, "任务管家"
    if growth_points >= 3:
        return 2, "方案侦探"
    return 1, "初来乍到"


def _ensure_companion(game: dict[str, Any]) -> dict[str, Any]:
    companion = game.setdefault("companion", initial_companion_state())
    default = initial_companion_state()
    for key, value in default.items():
        if key not in companion:
            companion[key] = deepcopy(value)
    for food_id, amount in default["food_inventory"].items():
        companion.setdefault("food_inventory", {}).setdefault(food_id, amount)
    companion.setdefault("fed_rewards", {})
    companion.setdefault("stage_rewards_claimed", {})
    return companion


def _ensure_stage_three(game: dict[str, Any]) -> dict[str, Any]:
    stage_three = game.setdefault("stage_three", initial_stage_three_state())
    default = initial_stage_three_state()
    for key, value in default.items():
        if key not in stage_three:
            stage_three[key] = deepcopy(value)
    return stage_three


def _ensure_progression(game: dict[str, Any]) -> dict[str, Any]:
    progression = game.setdefault("progression", initial_progression_state())
    default = initial_progression_state()
    for key, value in default.items():
        if key not in progression:
            progression[key] = deepcopy(value)
    progression.setdefault("badges", {})
    progression.setdefault("reward_history", [])
    progression.setdefault("completed_acts", {})
    return progression


def _merge_defaults(target: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    for key, value in defaults.items():
        if key not in target:
            target[key] = deepcopy(value)
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_defaults(target[key], value)
    return target


def _ensure_stage_four(game: dict[str, Any]) -> dict[str, Any]:
    stage_four = game.setdefault("stage_four", initial_stage_four_state())
    return _merge_defaults(stage_four, initial_stage_four_state())


def _ensure_post_game(game: dict[str, Any]) -> dict[str, Any]:
    post_game = game.setdefault("post_game", initial_post_game_state())
    return _merge_defaults(post_game, initial_post_game_state())


def award_badge(game: dict[str, Any], badge_id: str) -> bool:
    if badge_id not in BADGE_DEFINITIONS:
        return False
    progression = _ensure_progression(game)
    badges = progression.setdefault("badges", {})
    if badge_id in badges:
        return False
    badges[badge_id] = deepcopy(BADGE_DEFINITIONS[badge_id])
    return True


def record_stage_check_in(game: dict[str, Any], act_id: str) -> bool:
    progression = _ensure_progression(game)
    completed = progression.setdefault("completed_acts", {})
    if completed.get(act_id):
        return False
    completed[act_id] = True
    progression["check_in_count"] = len(completed)
    progression["streak"] = len(completed)
    if progression["streak"] >= 3 and not game.get("processed_actions", {}).get("progression:three_act_reward"):
        companion = _ensure_companion(game)
        companion["hint_tokens"] = int(companion.get("hint_tokens", 0)) + 1
        companion["last_reaction"] = "连续完成三幕打卡，芽芽为你兑换了一张协作提示券。"
        game.setdefault("processed_actions", {})["progression:three_act_reward"] = True
        award_badge(game, "streak_keeper")
        progression["reward_history"].append({"id": "three_act_reward", "name": "连续三幕提示券", "quantity": 1})
    return True


def apply_companion_stage_reward(game: dict[str, Any], previous_stage: int = 1) -> dict[str, Any]:
    companion = _ensure_companion(game)
    new_stage, new_stage_name = calculate_companion_stage(int(companion.get("growth_points", 0)))
    companion["stage"] = new_stage
    companion["stage_name"] = new_stage_name
    claimed = companion.setdefault("stage_rewards_claimed", {})
    for stage in range(previous_stage + 1, new_stage + 1):
        key = str(stage)
        if claimed.get(key):
            continue
        if stage == 2:
            companion["hint_tokens"] = int(companion.get("hint_tokens", 0)) + 1
            companion["last_reaction"] = "我进化成方案侦探啦！送你一张提示券，遇到卡点可以用。"
        elif stage == 3:
            if not companion.get("energy_recovered"):
                _write_value(game, "energy", _read_value(game, "energy") + 5)
                companion["energy_recovered"] = True
            companion["last_reaction"] = "我变成任务管家了，帮你找回一点精力。"
        elif stage == 4:
            companion["third_act_collaboration_hint"] = True
            companion["last_reaction"] = "我进化为证据守护者！下一幕我会提醒你协作证据。"
        elif stage == 5:
            companion["third_act_collaboration_hint"] = True
            companion["last_reaction"] = "我成为协作侦察员了，会提醒你先看见团队约束。"
        elif stage == 6:
            companion["last_reaction"] = "我进化为团队协调者！现在我们更擅长把冲突变成可执行范围。"
        claimed[key] = True
    return game


def _apply_stage_one_companion_bonus(game: dict[str, Any], style: str) -> None:
    companion = _ensure_companion(game)
    inventory = companion["food_inventory"]
    if style == "独立分析型":
        companion["trait"] = "观察力"
        companion["last_reaction"] = "你喜欢先独立梳理，我会提醒你别忘记及时校准。"
    elif style == "导师协作型":
        companion["trait"] = "求助有方"
        companion["hint_tokens"] = int(companion.get("hint_tokens", 0)) + 1
        companion["last_reaction"] = "你很会找到关键支持，我把这份求助经验变成一张提示券。"
    elif style == "AI效率优先型":
        companion["trait"] = "效率感知"
        inventory["action_cookie"] += 1
        companion["last_reaction"] = "你很会提速，我带来一块行动饼；但别忘了看清AI边界。"
    elif style == "证据稳健型":
        companion["trait"] = "证据嗅觉"
        inventory["verification_berry"] += 1
        companion["last_reaction"] = "你很重视证据，这颗核验莓先放进背包。"
    elif style == "速度优先型":
        companion["trait"] = "快速行动"
        companion["mood"] = "紧张"
        companion["last_reaction"] = "你推进很快，但我闻到了一点风险味道，我们要慢半拍核验。"
    else:
        companion["trait"] = "好奇心"
        companion["last_reaction"] = "你还在探索自己的节奏，我会陪你试出更稳的做法。"


def build_stage_two_context(game: dict[str, Any]) -> dict[str, Any]:
    style = stage_one_style(game)
    mentor_hint_available = int(game.get("mentor_trust", 0)) >= 34
    verification_hint_available = int(game.get("stats", {}).get("verification", 0)) >= 25
    risk_watch = int(game.get("risk", 0)) >= 30
    low_energy = int(game.get("energy", 0)) <= 80
    message_parts = [f"你在第一幕呈现出“{style}”倾向。"]
    if mentor_hint_available:
        message_parts.append("导师信任已达到提示门槛，第二幕可获得一次导师提示。")
    if verification_hint_available:
        message_parts.append("结果验证能力已达到提示门槛，AI审查时可获得一次核验提示。")
    if risk_watch:
        message_parts.append("当前风险进入重点观察，HR信号会更明确。")
    if low_energy:
        message_parts.append("当前精力偏紧，第二幕不会阻止继续，但需要关注任务取舍。")
    return {
        "mentor_hint_available": mentor_hint_available,
        "verification_hint_available": verification_hint_available,
        "risk_watch": risk_watch,
        "low_energy": low_energy,
        "opening_message": " ".join(message_parts),
        "stage_one_style": style,
        "mentor_hint_used": False,
        "verification_hint_used": False,
    }


def enter_stage_two(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    record_stage_check_in(updated, "act_one")
    updated["stage_two_context"] = build_stage_two_context(updated)
    companion = _ensure_companion(updated)
    if not updated["processed_actions"].get("companion:stage_one_bonus"):
        _apply_stage_one_companion_bonus(updated, updated["stage_two_context"]["stage_one_style"])
        if updated["stage_two_context"].get("verification_hint_available"):
            companion["hint_tokens"] = int(companion.get("hint_tokens", 0)) + 1
            companion["last_reaction"] = companion["last_reaction"] + " 你的核验能力也兑换了一张提示券。"
        if updated["stage_two_context"].get("mentor_hint_available") and companion.get("trait") != "求助有方":
            companion["hint_tokens"] = int(companion.get("hint_tokens", 0)) + 1
            companion["last_reaction"] = companion["last_reaction"] + " 导师信任也为你兑换了一张提示券。"
        updated["processed_actions"]["companion:stage_one_bonus"] = True
    updated["current_act"] = "act_two"
    updated["checkpoint_id"] = None
    updated["scene_id"] = "stage_two_briefing"
    updated["ending_id"] = None
    updated["pending_feedback"] = None
    updated["pending_next_scene"] = None
    return updated


def enter_stage_three(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    record_stage_check_in(updated, "act_two")
    stage_three = _ensure_stage_three(updated)
    stage_three["started"] = True
    if stage_three.get("random_seed") is None:
        stage_three["random_seed"] = _stage_three_seed(updated)
    updated["current_act"] = "act_three"
    updated["checkpoint_id"] = None
    updated["scene_id"] = "stage_three_briefing"
    updated["ending_id"] = None
    updated["pending_feedback"] = None
    updated["pending_next_scene"] = None
    updated["stage_three_preview"] = False
    return updated


def use_stage_two_hint(game: dict[str, Any], hint_type: str) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(game)
    scene_id = updated.get("scene_id", "")
    action_key = f"hint:{scene_id}"
    companion = _ensure_companion(updated)
    if updated.get("processed_actions", {}).get(action_key):
        return updated, False
    if int(companion.get("hint_tokens", 0)) <= 0:
        return updated, False
    if hint_type not in {"verification", "mentor", "evidence"}:
        return updated, False
    companion["hint_tokens"] = int(companion.get("hint_tokens", 0)) - 1
    companion["mood"] = "思考"
    companion["last_reaction"] = "我用掉一张提示券，只给你思考方向，不替你做判断。"
    updated["processed_actions"][action_key] = True
    updated.setdefault("stage_two_context", {})[f"{hint_type}_hint_used"] = True
    return updated, True


def _apply_deltas(game: dict[str, Any], effects: dict[str, int]) -> dict[str, dict[str, int]]:
    changes: dict[str, dict[str, int]] = {}
    for key, delta in effects.items():
        before = _read_value(game, key)
        _write_value(game, key, before + int(delta))
        after = _read_value(game, key)
        changes[key] = {"before": before, "after": after, "delta": after - before}
    return changes


def calculate_food_reward(score: int, minigame_type: str) -> dict[str, Any]:
    if score < 50:
        food_id = "review_cookie"
        quantity = 1
    else:
        food_id = MINIGAME_FOOD_MAP[minigame_type]
        if score >= 85:
            quantity = 3
        elif score >= 70:
            quantity = 2
        else:
            quantity = 1
    food = FOOD_DEFINITIONS[food_id]
    return {
        "food_id": food_id,
        "food_name": food["name"],
        "quantity": quantity,
        "growth_value": quantity,
    }


def normalize_game_state(game: dict[str, Any] | None) -> dict[str, Any]:
    """Bring older in-session game objects up to the current companion schema."""
    if not isinstance(game, dict):
        return initial_game_state()
    normalized = deepcopy(game)
    defaults = initial_game_state()
    for key, value in defaults.items():
        if key not in normalized:
            normalized[key] = deepcopy(value)
    normalized.setdefault("stats", {})
    for key, value in defaults["stats"].items():
        normalized["stats"].setdefault(key, value)
    companion = _ensure_companion(normalized)
    _ensure_stage_three(normalized)
    _ensure_progression(normalized)
    stage_four = _ensure_stage_four(normalized)
    boss = stage_four.get("boss", {})
    questions = boss.get("questions", [])
    if isinstance(questions, list):
        boss["questions"] = [normalize_boss_question(question) for question in questions if question is not None]
    else:
        boss["questions"] = []
    if normalized.get("scene_id") == "stage_four_boss":
        invalid_questions = (
            not boss.get("questions")
            or any(not isinstance(question, dict) or not question.get("answers") for question in boss.get("questions", []))
        )
        if invalid_questions:
            boss["seed"] = _stage_four_seed(normalized)
            boss["questions"] = _boss_questions_for_seed(int(boss["seed"]))
            boss["current_index"] = 0
            boss["answers"] = []
            boss["completed"] = False
    _ensure_post_game(normalized)
    processed = normalized.setdefault("processed_actions", {})
    for result_key, result in normalized.get("minigame_results", {}).items():
        if result_key not in MINIGAME_FOOD_MAP:
            continue
        if "food_reward" not in result:
            result["food_reward"] = calculate_food_reward(int(result.get("score", 0)), result_key)
        result.setdefault("fed", bool(companion.get("fed_rewards", {}).get(result_key)))
        migration_key = f"companion:migrated_reward:{result_key}"
        if not result.get("fed") and not processed.get(migration_key):
            reward = result["food_reward"]
            companion["food_inventory"][reward["food_id"]] += int(reward["quantity"])
            processed[migration_key] = True
    if str(normalized.get("scene_id", "")).startswith("mini_") or normalized.get("scene_id") in {"stage_two_briefing", "stage_two_complete"}:
        normalized["current_act"] = "act_two"
    if normalized.get("scene_id") in {"stage_three_briefing", "stage_three_alignment", "stage_three_scope", "stage_three_random_event", "stage_three_complete"}:
        normalized["current_act"] = "act_three"
    if normalized.get("scene_id") in {"stage_four_briefing", "stage_four_loadout", "stage_four_evidence", "stage_four_boss", "stage_four_remediation", "stage_four_bonus", "stage_four_complete", "post_game_hub"}:
        normalized["current_act"] = "act_four"
    if normalized.get("checkpoint_id") == "stage_one_complete" or normalized.get("current_act") in {"act_two", "act_three", "act_four"}:
        record_stage_check_in(normalized, "act_one")
    if normalized.get("checkpoint_id") == "stage_two_complete" or normalized.get("current_act") in {"act_three", "act_four"}:
        record_stage_check_in(normalized, "act_two")
    if normalized.get("checkpoint_id") == "stage_three_complete" or normalized.get("current_act") == "act_four":
        record_stage_check_in(normalized, "act_three")
    if normalized.get("checkpoint_id") == "stage_four_complete":
        record_stage_check_in(normalized, "act_four")
    return normalized


def _companion_reaction(result_key: str, score: int, food_id: str) -> str:
    if result_key == "ai_review" and score >= 80:
        return "你把无来源数据和隐私风险都找出来了！这颗核验莓很甜。"
    if result_key == "ai_review" and score < 50:
        return "还有几个问题躲在方案里，我们先吃块复盘饼，再看看遗漏了什么。"
    if result_key == "priority" and score >= 80:
        return "你先处理了真正影响评审的问题，行动饼让我充满干劲。"
    if result_key == "priority" and score < 50:
        return "我们好像忙在了不太关键的地方，先吃复盘饼，把优先级再理一遍。"
    if result_key == "evidence" and score >= 80:
        return "真实访谈、历史数据、口径和反例都在，证据星亮起来了。"
    if result_key == "evidence" and score < 50:
        return "证据包还不够稳，我们吃块复盘饼，补上最关键的支撑。"
    if food_id == "verification_berry":
        return "核验莓让我更会找证据了，我们继续把风险拨开。"
    if food_id == "action_cookie":
        return "行动饼补充了推进力，下一步要把时间花在关键任务上。"
    if food_id == "evidence_star":
        return "证据星亮了一下，方案越来越像能上评审的样子。"
    return "复盘饼提醒我们：低分不是死路，复盘后还能往前走。"


def feed_companion(game: dict[str, Any], result_key: str) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    result = updated.get("minigame_results", {}).get(result_key)
    if not result:
        return updated, False, "还没有可喂食的奖励。"
    companion = _ensure_companion(updated)
    if companion.get("fed_rewards", {}).get(result_key):
        return updated, False, None
    reward = result.get("food_reward")
    if not reward:
        return updated, False, "奖励数据缺失。"
    food_id = reward["food_id"]
    quantity = int(reward["quantity"])
    inventory = companion["food_inventory"]
    if int(inventory.get(food_id, 0)) < quantity:
        return updated, False, "食物库存不足。"
    previous_stage = int(companion.get("stage", 1))
    inventory[food_id] -= quantity
    companion["growth_points"] = min(12, int(companion.get("growth_points", 0)) + int(reward["growth_value"]))
    companion["fed_rewards"][result_key] = True
    companion["mood"] = "兴奋" if int(reward["growth_value"]) >= 3 else "开心"
    companion["last_reaction"] = _companion_reaction(result_key, int(result.get("score", 0)), food_id)
    result["fed"] = True
    result["fed_quantity"] = quantity
    if int(result.get("score", 0)) < 50:
        result["remediation_status"] = result.get("remediation_status") or "pending"
    updated = apply_companion_stage_reward(updated, previous_stage)
    return updated, True, None


def feed_inventory_food(game: dict[str, Any], food_id: str) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    if food_id not in FOOD_DEFINITIONS:
        return updated, False, "食物不存在。"
    companion = _ensure_companion(updated)
    inventory = companion["food_inventory"]
    if int(inventory.get(food_id, 0)) <= 0:
        return updated, False, "食物库存不足。"
    action_key = f"feed_inventory:{food_id}:{sum(int(v) for v in companion.get('fed_rewards', {}).values() if isinstance(v, bool))}:{int(companion.get('growth_points', 0))}:{int(inventory.get(food_id, 0))}"
    if updated.get("processed_actions", {}).get(action_key):
        return updated, False, None
    previous_stage = int(companion.get("stage", 1))
    inventory[food_id] = int(inventory.get(food_id, 0)) - 1
    companion["growth_points"] = min(12, int(companion.get("growth_points", 0)) + 1)
    companion["mood"] = "开心"
    companion["last_reaction"] = _companion_reaction("inventory", 70, food_id)
    updated.setdefault("processed_actions", {})[action_key] = True
    updated = apply_companion_stage_reward(updated, previous_stage)
    return updated, True, None


def submit_remediation(game: dict[str, Any], result_key: str, answer_id: str) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    result = updated.get("minigame_results", {}).get(result_key)
    if not result:
        return updated, False, "没有可补救的挑战。"
    action_key = f"remediation:{result_key}"
    if updated.get("processed_actions", {}).get(action_key):
        return updated, False, None
    question = REMEDIATION_QUESTIONS.get(result_key)
    if not question:
        return updated, False, "补救题不存在。"
    correct = answer_id == question["correct"]
    if correct:
        _write_value(updated, "risk", _read_value(updated, "risk") - 3)
    updated["processed_actions"][action_key] = True
    result["remediation_status"] = "correct" if correct else "wrong"
    result["remediation_answer"] = answer_id
    result["remediation_risk_delta"] = -3 if correct else 0
    companion = _ensure_companion(updated)
    companion["mood"] = "思考"
    companion["last_reaction"] = "补救完成，原始分数不变，但我们把一个风险点补上了。" if correct else "答案还不够稳，不过你已经完成复盘，可以继续往前走。"
    return updated, True, None


def _mark_minigame_result(
    game: dict[str, Any],
    action_key: str,
    result_key: str,
    score: int,
    result: dict[str, Any],
    effects: dict[str, int],
    next_scene: str,
) -> dict[str, Any]:
    changes = _apply_deltas(game, effects)
    reward = calculate_food_reward(score, result_key)
    companion = _ensure_companion(game)
    companion["food_inventory"][reward["food_id"]] += int(reward["quantity"])
    game["processed_actions"][action_key] = True
    game.setdefault("stage_two_scores", {})[result_key] = score
    game.setdefault("minigame_results", {})[result_key] = {
        **deepcopy(result),
        "score": score,
        "changes": changes,
        "xp_gained": changes.get("xp", {}).get("delta", 0),
        "next_scene": next_scene,
        "food_reward": reward,
        "fed": False,
    }
    game["history"].append({
        "scene_id": game["scene_id"],
        "scene_title": SCENES.get(game.get("scene_id"), {}).get("title", "未命名场景"),
        "option_id": "submit",
        "option_title": result.get("history_title", "提交结果"),
        "changes": deepcopy(changes),
        "score": score,
    })
    return game


def submit_ai_review(game: dict[str, Any], selected_ids: list[str] | dict[str, str]) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    action_key = "mini_ai_review:submit"
    if updated.get("scene_id") != "mini_ai_review":
        return updated, False, "当前不在AI方案审查场景。"
    if action_key in updated.get("processed_actions", {}):
        return updated, False, None
    all_ids = {item["id"] for item in AI_REVIEW_ITEMS}
    if isinstance(selected_ids, dict):
        judgement_map = dict(selected_ids)
    else:
        return updated, False, "请完成全部5项判断后再提交。"
    correct = {item["id"] for item in AI_REVIEW_ITEMS if item["is_issue"]}
    if set(judgement_map) != all_ids:
        return updated, False, "请完成全部5项判断后再提交。"
    valid_judgements = {"unknown", "issue", "reasonable"}
    if any(judgement not in valid_judgements for judgement in judgement_map.values()):
        return updated, False, "存在无效选项。"
    selected = {item_id for item_id, judgement in judgement_map.items() if judgement == "issue"}
    missed_unknown = sorted(item_id for item_id in correct if judgement_map[item_id] == "unknown")
    missed_reasonable = sorted(item_id for item_id in correct if judgement_map[item_id] == "reasonable")
    false_positive = sorted(item_id for item in AI_REVIEW_ITEMS if not item["is_issue"] for item_id in [item["id"]] if judgement_map[item_id] == "issue")
    uncertain_reasonable = sorted(item_id for item in AI_REVIEW_ITEMS if not item["is_issue"] for item_id in [item["id"]] if judgement_map[item_id] == "unknown")
    missed = sorted(set(missed_unknown + missed_reasonable))
    score = clamp(100 - len(missed_unknown) * 10 - len(missed_reasonable) * 25 - len(false_positive) * 25 - len(uncertain_reasonable) * 10)
    if score >= 80:
        effects = {"verification": 10, "ai_collaboration": 6, "risk": -8, "xp": 80}
        feedback = "你识别出了关键问题，方案风险被及时拦住。"
    elif score >= 50:
        effects = {"verification": 5, "ai_collaboration": 3, "risk": -3, "xp": 50}
        feedback = "你发现了部分问题，但还需要更系统地检查安全和证据。"
    else:
        effects = {"verification": 1, "risk": 8, "mentor_trust": -3, "xp": 25}
        feedback = "关键问题没有被充分识别，预评审风险明显上升。"
    result = {
        "selected_ids": sorted(selected),
        "judgement_map": judgement_map,
        "correct_ids": sorted(correct),
        "missed_ids": missed,
        "missed_unknown_ids": missed_unknown,
        "missed_reasonable_ids": missed_reasonable,
        "false_positive_ids": false_positive,
        "uncertain_reasonable_ids": uncertain_reasonable,
        "feedback": feedback,
        "mentor_signal": "导师会关注你是否能说明每个判断背后的证据来源。",
        "hr_signal": "若同批新人普遍漏掉安全或因果问题，需要补充AI验证训练。" if updated.get("stage_two_context", {}).get("risk_watch") else "当前主要是个体能力信号，暂不需要HR额外介入。",
        "history_title": f"AI方案审查得分{score}",
    }
    updated = _mark_minigame_result(updated, action_key, "ai_review", score, result, effects, "mini_priority")
    return updated, True, None


def submit_priority(game: dict[str, Any], selected_ids: list[str]) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    action_key = "mini_priority:submit"
    if updated.get("scene_id") != "mini_priority":
        return updated, False, "当前不在任务优先级场景。"
    if action_key in updated.get("processed_actions", {}):
        return updated, False, None
    if not 1 <= len(selected_ids) <= 3:
        return updated, False, "请选择1—3项优先任务。"
    task_map = {task["id"]: task for task in PRIORITY_TASKS}
    if any(task_id not in task_map for task_id in selected_ids):
        return updated, False, "存在无效任务。"
    if len(set(selected_ids)) != len(selected_ids):
        return updated, False, "请不要重复选择同一任务。"
    tasks = [task_map[task_id] for task_id in selected_ids]
    total_cost = sum(int(task["cost"]) for task in tasks)
    if total_cost > 10:
        return updated, False, "任务预算超过10点，请重新取舍。"
    business_value_total = sum(int(task["business_value"]) for task in tasks)
    risk_reduction_total = sum(int(task["risk_reduction"]) for task in tasks)
    types = {str(task["type"]) for task in tasks}
    selected_set = set(selected_ids)
    combination_bonus = "real_business" in types and "feedback" in types
    best_practice_bonus = {"user_feedback", "data_definition", "mentor_calibration"}.issubset(selected_set)
    low_value_busy = types.issubset({"presentation", "learning"}) and "real_business" not in types
    combination_bonus_value = 15 if combination_bonus else 0
    best_practice_bonus_value = 10 if best_practice_bonus else 0
    low_value_penalty = 25 if low_value_busy else 0
    score = business_value_total * 4 + risk_reduction_total * 3 + combination_bonus_value + best_practice_bonus_value - low_value_penalty
    if "real_business" not in types:
        score = min(score, 60)
    score = clamp(score)
    effects = {
        "business": min(8, round(business_value_total / 2)),
        "delivery": 4 if combination_bonus else 1,
        "energy": -min(12, total_cost),
        "risk": -min(8, risk_reduction_total),
        "mentor_trust": 4 if combination_bonus else 0,
        "xp": 30 + business_value_total * 5,
    }
    result = {
        "selected_ids": selected_ids,
        "selected_names": [task["name"] for task in tasks],
        "total_cost": total_cost,
        "business_value_total": business_value_total,
        "risk_reduction_total": risk_reduction_total,
        "combination_bonus": combination_bonus,
        "combination_bonus_value": combination_bonus_value,
        "best_practice_bonus": best_practice_bonus,
        "best_practice_bonus_value": best_practice_bonus_value,
        "low_value_busy": low_value_busy,
        "low_value_penalty": low_value_penalty,
        "feedback": "你把真实业务证据和导师校准组合起来，方案可评审性明显提升。" if combination_bonus else "你完成了取舍，但还可以更聚焦会改变业务结论或风险判断的任务。",
        "mentor_signal": "导师会检查你是否优先处理了影响业务判断和风险判断的工作。",
        "hr_signal": "低价值忙碌出现，需提醒新人不要用表层优化替代业务补救。" if low_value_busy else "优先级选择未出现明显组织风险。",
        "history_title": f"任务优先级得分{score}",
    }
    updated = _mark_minigame_result(updated, action_key, "priority", score, result, effects, "mini_evidence")
    return updated, True, None


def submit_evidence(game: dict[str, Any], selected_ids: list[str]) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    action_key = "mini_evidence:submit"
    if updated.get("scene_id") != "mini_evidence":
        return updated, False, "当前不在证据包组装场景。"
    if action_key in updated.get("processed_actions", {}):
        return updated, False, None
    if not 3 <= len(selected_ids) <= 4:
        return updated, False, "请选择3—4项证据。"
    item_map = {item["id"]: item for item in EVIDENCE_ITEMS}
    if any(item_id not in item_map for item_id in selected_ids):
        return updated, False, "存在无效证据。"
    if len(set(selected_ids)) != len(selected_ids):
        return updated, False, "请不要重复选择同一证据。"
    items = [item_map[item_id] for item_id in selected_ids]
    evidence_reveal = []
    score = 0
    for item in items:
        if item["quality"] == "high":
            score += 25
            label = "强证据"
        elif item["quality"] == "medium":
            score += 10
            label = "中等证据"
        elif item["quality"] == "ai_only":
            score -= 15
            label = "AI推断"
        else:
            label = "主观判断"
        evidence_reveal.append({"text": item["text"], "label": label})
    if "metric_definition" not in selected_ids:
        score -= 10
        evidence_reveal.append({"text": "缺少已经核对的数据口径说明。", "label": "关键证据遗漏"})
    if "counter_example" not in selected_ids:
        score -= 10
        evidence_reveal.append({"text": "缺少反例：类似活动曾因奖励规则复杂导致参与下降。", "label": "关键证据遗漏"})
    score = clamp(score)
    if score >= 80:
        effects = {"verification": 12, "business": 8, "delivery": 5, "risk": -8, "xp": 100}
        feedback = "证据包结构扎实，既有真实反馈、历史数据，也有口径说明和反例。"
    elif score >= 50:
        effects = {"verification": 6, "business": 4, "delivery": 2, "risk": -3, "xp": 60}
        feedback = "证据包基本可用，但还需要补充口径或反例来支撑评审追问。"
    else:
        effects = {"verification": -3, "risk": 10, "mentor_trust": -3, "xp": 25}
        feedback = "证据包仍偏主观或依赖AI推断，难以支撑预评审。"
    result = {
        "selected_ids": selected_ids,
        "selected_names": [item["text"] for item in items],
        "evidence_reveal": evidence_reveal,
        "feedback": feedback,
        "mentor_signal": "导师会追问证据是否能支持“提升玩家参与度”这一结论。",
        "hr_signal": "证据薄弱会影响独立交付判断，需要观察是否为共性问题。" if score < 50 else "证据链表现可作为正向行为信号。",
        "history_title": f"证据包组装得分{score}",
    }
    updated = _mark_minigame_result(updated, action_key, "evidence", score, result, effects, "stage_two_complete")
    return updated, True, None


def _stage_three_seed(game: dict[str, Any]) -> int:
    scores = game.get("stage_two_scores", {})
    return int(game.get("xp", 0)) + int(game.get("risk", 0)) * 17 + int(scores.get("ai_review", 0)) * 3 + int(scores.get("priority", 0)) * 5 + int(scores.get("evidence", 0)) * 7


def _alignment_roles_for_seed(seed: int) -> list[dict[str, Any]]:
    roles = deepcopy(ALIGNMENT_ROLES)
    start = seed % len(roles)
    ordered = roles[start:] + roles[:start]
    return ordered[:3]


def get_stage_three_alignment_rounds(game: dict[str, Any]) -> list[dict[str, Any]]:
    stage_three = _ensure_stage_three(game)
    seed = int(stage_three.get("random_seed") or _stage_three_seed(game))
    return _alignment_roles_for_seed(seed)


def submit_alignment(game: dict[str, Any], responses: list[str]) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    action_key = "stage_three_alignment:submit"
    if updated.get("scene_id") != "stage_three_alignment":
        return updated, False, "当前不在需求拉齐会。"
    if action_key in updated.get("processed_actions", {}):
        return updated, False, None
    if len(responses) != 3:
        return updated, False, "请完成三轮回应。"
    stage_three = _ensure_stage_three(updated)
    rounds = get_stage_three_alignment_rounds(updated)
    total_score = 0
    response_details = []
    total_effects: dict[str, int] = {}
    for index, response_id in enumerate(responses):
        role = rounds[index]
        role_id = role["id"]
        options = ALIGNMENT_OPTIONS_BY_ROLE.get(role_id, {})
        if response_id not in options:
            return updated, False, "存在无效回应。"
        response = options[response_id]
        round_score = int(response["score"])
        total_score += round_score
        for key, delta in response["effects"].items():
            total_effects[key] = total_effects.get(key, 0) + int(delta)
        response_details.append({
            "round": index + 1,
            "role": role,
            "role_id": role_id,
            "response_id": response_id,
            "option_id": response_id,
            "response_title": response.get("title", response.get("text", "未命名回应")),
            "score": clamp(round_score),
        })
    score = clamp(round(total_score / 3))
    total_effects["xp"] = max(50, min(160, total_effects.get("xp", 0)))
    changes = _apply_deltas(updated, {key: delta for key, delta in total_effects.items() if key in (*BOUNDED_KEYS, "xp")})
    for key in ("clarity", "team_trust"):
        before = int(stage_three.get(key, 30))
        delta = total_effects.get(key, 0)
        after = clamp(before + delta)
        stage_three[key] = after
        changes[key] = {"before": before, "after": after, "delta": after - before}
    stage_three["alignment_score"] = score
    updated["processed_actions"][action_key] = True
    if score >= 80:
        award_badge(updated, "collaboration_driver")
    companion = _ensure_companion(updated)
    companion["mood"] = "开心" if score >= 70 else "思考"
    companion["last_reaction"] = "团队信任被你一点点拉起来了，先问约束比直接推进更稳。" if score >= 70 else "这场会还有点拧巴，下一步要把目标和范围说得更清楚。"
    updated.setdefault("minigame_results", {})["stage_three_alignment"] = {
        "score": score,
        "responses": response_details,
        "changes": changes,
        "feedback": "你把多方约束转化为可讨论的共同目标。" if score >= 70 else "需求拉齐还不够充分，后续范围取舍要更谨慎。",
        "mentor_signal": "导师会关注你是否能复述每个角色的真实约束。",
        "hr_signal": "这是协作成熟度信号，只用于游戏反馈，不进入正式评价。",
        "next_scene": "stage_three_scope",
    }
    updated["history"].append({"scene_id": "stage_three_alignment", "scene_title": "需求拉齐会", "option_id": "submit", "option_title": f"需求拉齐得分{score}", "changes": deepcopy(changes), "score": score})
    return updated, True, None


def calculate_scope_plan(selected_scope: dict[str, list[str]]) -> dict[str, Any]:
    task_map = {task["id"]: task for task in SCOPE_TASKS}
    all_task_ids = {task["id"] for task in SCOPE_TASKS}
    must = set(selected_scope.get("must", []))
    optional = set(selected_scope.get("optional", []))
    delayed = set(selected_scope.get("delayed", []))
    all_selected = must | optional | delayed
    invalid = sorted(task_id for task_id in all_selected if task_id not in task_map)
    duplicate_classification = bool((must & optional) or (must & delayed) or (optional & delayed))
    missing = sorted(all_task_ids - all_selected)
    extra = sorted(all_selected - all_task_ids)

    must_tasks = [task_map[task_id] for task_id in sorted(must) if task_id in task_map]
    optional_tasks = [task_map[task_id] for task_id in sorted(optional) if task_id in task_map]
    delayed_tasks = [task_map[task_id] for task_id in sorted(delayed) if task_id in task_map]
    must_cost = {
        "dev": sum(int(task["dev"]) for task in must_tasks),
        "art": sum(int(task["art"]) for task in must_tasks),
        "time": sum(int(task["time"]) for task in must_tasks),
    }
    optional_cost = {
        "dev": sum(int(task["dev"]) for task in optional_tasks),
        "art": sum(int(task["art"]) for task in optional_tasks),
        "time": sum(int(task["time"]) for task in optional_tasks),
    }
    over_budget = {key: max(0, must_cost[key] - SCOPE_BUDGET[key]) for key in SCOPE_BUDGET}
    has_core = "core_loop" in must
    has_risk_control = bool({"risk_monitor", "rollback_plan"} & must)
    has_user_understanding = bool({"onboarding", "data_tracking"} & must)
    has_mvp = bool(has_core and has_risk_control and len(must) >= 3 and not any(over_budget.values()))
    visual_count = sum(1 for task in must_tasks if task["category"] == "visual")
    visual_heavy = bool(must_tasks) and visual_count > len(must_tasks) / 2
    missing_core = not has_core
    missing_risk = not has_risk_control

    score = 0
    if has_core:
        score += 25
    if has_risk_control:
        score += 20
    if has_user_understanding:
        score += 15
    if not any(over_budget.values()):
        score += 20
    if len(must) in (3, 4, 5):
        score += 10
    if optional:
        score += 5
    if delayed:
        score += 5
    if missing_core:
        score -= 30
    if missing_risk:
        score -= 25
    if visual_heavy:
        score -= 20
    if any(over_budget.values()):
        score -= 30
    if len(must) > 6:
        score -= 10
    ideal_plan = bool(
        has_core
        and has_risk_control
        and has_user_understanding
        and not any(over_budget.values())
        and 3 <= len(must) <= 5
        and optional
        and delayed
        and not visual_heavy
        and ("rollback_plan" in must or "risk_monitor" in must)
    )
    score = max(0, min(100, score))
    if score >= 100 and not ideal_plan:
        score = 95
    delay_summary = [
        {
            "task_id": task["id"],
            "task_name": task["name"],
            "reason": "当前资源不足，延后至核心方案验证后。",
        }
        for task in delayed_tasks
    ]
    return {
        "valid": not invalid and not duplicate_classification and not missing and not extra and len(must) >= 3 and not any(over_budget.values()),
        "invalid": invalid,
        "extra": extra,
        "missing": missing,
        "duplicates": duplicate_classification,
        "must": sorted(must),
        "optional": sorted(optional),
        "delayed": sorted(delayed),
        "costs": must_cost,
        "must_cost": must_cost,
        "optional_cost": optional_cost,
        "remaining": {key: SCOPE_BUDGET[key] - must_cost[key] for key in SCOPE_BUDGET},
        "over_budget": over_budget,
        "has_core": has_core,
        "has_risk_control": has_risk_control,
        "has_user_understanding": has_user_understanding,
        "missing_core": missing_core,
        "missing_risk": missing_risk,
        "visual_heavy": visual_heavy,
        "has_mvp": bool(has_mvp),
        "ideal_plan": ideal_plan,
        "score": score,
        "business_value": sum(int(task["business"]) for task in must_tasks),
        "risk_value": sum(int(task["risk"]) for task in must_tasks),
        "must_tasks": deepcopy(must_tasks),
        "optional_tasks": deepcopy(optional_tasks),
        "delayed_tasks": deepcopy(delayed_tasks),
        "delay_summary": delay_summary,
    }


def submit_scope(game: dict[str, Any], selected_scope: dict[str, list[str]]) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    action_key = "stage_three_scope:submit"
    if updated.get("scene_id") != "stage_three_scope":
        return updated, False, "当前不在范围取舍板。"
    if action_key in updated.get("processed_actions", {}):
        return updated, False, None
    plan = calculate_scope_plan(selected_scope)
    if plan["invalid"]:
        return updated, False, "存在无效任务。"
    if plan["duplicates"]:
        return updated, False, "同一任务不能同时出现在多个槽位。"
    if plan["missing"] or plan["extra"]:
        return updated, False, f"请完成全部任务分类，仍有{len(plan['missing'])}项未分类。"
    if len(plan["must"]) < 3:
        return updated, False, "必做任务至少选择3项。"
    if any(plan["over_budget"].values()):
        return updated, False, "必做任务预算超限，请重新取舍。"
    score = int(plan["score"])
    effects = {
        "business": min(8, round(plan["business_value"] / 3)),
        "collaboration": 5 if plan["has_mvp"] else 2,
        "delivery": 7 if plan["has_mvp"] else 2,
        "risk": -min(10, round(plan["risk_value"] / 2)) if not plan["missing_risk"] else 7,
        "xp": 90 if score >= 80 else 60 if score >= 55 else 35,
    }
    changes = _apply_deltas(updated, effects)
    stage_three = _ensure_stage_three(updated)
    before_clarity = int(stage_three.get("clarity", 30))
    clarity_delta = 12 if plan["has_mvp"] else 4 if score >= 55 else -4
    stage_three["clarity"] = clamp(before_clarity + clarity_delta)
    changes["clarity"] = {"before": before_clarity, "after": stage_three["clarity"], "delta": stage_three["clarity"] - before_clarity}
    stage_three["scope_score"] = score
    stage_three["selected_scope"] = deepcopy(selected_scope)
    updated["processed_actions"][action_key] = True
    if plan["has_mvp"] and score >= 75:
        award_badge(updated, "scope_manager")
    companion = _ensure_companion(updated)
    if any(plan["over_budget"].values()):
        companion["last_reaction"] = "范围超预算了，先保核心和风险，再谈表现。"
    elif plan["missing_risk"]:
        companion["last_reaction"] = "我发现关键风险覆盖不足，回滚或监控至少要保住一个。"
    elif plan["has_mvp"]:
        companion["last_reaction"] = "这版范围更像团队能执行的最小可行方案了！"
    else:
        companion["last_reaction"] = "范围已经收窄，但还要继续检查风险覆盖。"
    companion["mood"] = "开心" if plan["has_mvp"] else "思考"
    updated.setdefault("minigame_results", {})["stage_three_scope"] = {
        **plan,
        "changes": changes,
        "feedback": "你在预算内形成了可上线最小方案。" if plan["has_mvp"] else "方案可以继续推进，但关键风险或核心范围仍需补齐。",
        "mentor_signal": "导师会验收必做范围是否同时覆盖核心机制和上线风险。",
        "hr_signal": "范围管理表现用于游戏化反馈，不进入正式绩效判断。",
        "next_scene": "stage_three_random_event",
    }
    updated["history"].append({"scene_id": "stage_three_scope", "scene_title": "范围取舍板", "option_id": "submit", "option_title": f"范围取舍得分{score}", "changes": deepcopy(changes), "score": score})
    return updated, True, None


def ensure_random_event(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    stage_three = _ensure_stage_three(updated)
    seed = int(stage_three.get("random_seed") or _stage_three_seed(updated))
    stage_three["random_seed"] = seed
    if not stage_three.get("random_event_id"):
        stage_three["random_event_id"] = RANDOM_EVENTS[seed % len(RANDOM_EVENTS)]["id"]
    return updated


def current_random_event(game: dict[str, Any]) -> dict[str, Any]:
    stage_three = _ensure_stage_three(game)
    seed = int(stage_three.get("random_seed") or _stage_three_seed(game))
    event_id = stage_three.get("random_event_id") or RANDOM_EVENTS[seed % len(RANDOM_EVENTS)]["id"]
    return next((event for event in RANDOM_EVENTS if event["id"] == event_id), RANDOM_EVENTS[0])


def random_reward_for_game(game: dict[str, Any]) -> dict[str, Any]:
    stage_three = _ensure_stage_three(game)
    seed = int(stage_three.get("random_seed") or _stage_three_seed(game))
    return deepcopy(RANDOM_REWARDS[(seed * 7 + 3) % len(RANDOM_REWARDS)])


def submit_random_event(game: dict[str, Any], option_id: str) -> tuple[dict[str, Any], bool, str | None]:
    updated = ensure_random_event(game)
    action_key = "stage_three_random_event:submit"
    if updated.get("scene_id") != "stage_three_random_event":
        return updated, False, "当前不在随机额外任务。"
    if action_key in updated.get("processed_actions", {}):
        return updated, False, None
    event = current_random_event(updated)
    option = event.get("options", {}).get(option_id)
    if not option:
        return updated, False, "请选择一个处理方式。"
    success = bool(option["success"])
    stage_three = _ensure_stage_three(updated)
    reward = random_reward_for_game(updated) if success else None
    stage_three["bonus_score"] = 100 if success else 0
    stage_three["bonus_task_result"] = {
        "event_id": event.get("id", "unknown_event"),
        "event_title": event.get("title", "未命名事件"),
        "option_id": option_id,
        "option_text": option.get("text", "未命名选项"),
        "success": success,
        "reward": reward,
    }
    updated["processed_actions"][action_key] = True
    if success:
        _apply_deltas(updated, {"xp": 60, "collaboration": 4})
        award_badge(updated, "incident_responder")
        if event["id"] in {"mentor_absent", "metric_changed"}:
            award_badge(updated, "hidden_finder")
        companion = _ensure_companion(updated)
        companion["mood"] = "兴奋"
        companion["last_reaction"] = "突发事件处理成功！这次应变会变成一个小奖励。"
    else:
        companion = _ensure_companion(updated)
        companion["mood"] = "思考"
        companion["last_reaction"] = "额外任务没成功也不会惩罚，我们保留主线方案继续前进。"
    return updated, True, None


def claim_random_reward(game: dict[str, Any]) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    action_key = "stage_three_random_event:claim_reward"
    stage_three = _ensure_stage_three(updated)
    result = stage_three.get("bonus_task_result")
    if not result or not result.get("success"):
        return updated, False, "没有可领取的随机奖励。"
    if stage_three.get("reward_claimed") or updated.get("processed_actions", {}).get(action_key):
        return updated, False, None
    reward = deepcopy(result.get("reward") or random_reward_for_game(updated))
    companion = _ensure_companion(updated)
    progression = _ensure_progression(updated)
    if reward["type"] == "food":
        companion["food_inventory"][reward["id"]] = int(companion["food_inventory"].get(reward["id"], 0)) + int(reward["quantity"])
        updated.setdefault("minigame_results", {})["stage_three_reward"] = {
            "score": 100,
            "food_reward": {
                "food_id": reward["id"],
                "food_name": reward["name"],
                "quantity": reward["quantity"],
                "growth_value": reward["quantity"],
            },
            "fed": False,
            "feedback": f"随机奖励获得{reward['name']}×{reward['quantity']}。",
        }
    elif reward["type"] == "hint":
        companion["hint_tokens"] = int(companion.get("hint_tokens", 0)) + int(reward["quantity"])
    elif reward["type"] == "fragment":
        progression["badge_fragments"] = int(progression.get("badge_fragments", 0)) + int(reward["quantity"])
    elif reward["type"] == "energy":
        _write_value(updated, "energy", _read_value(updated, "energy") + int(reward["quantity"]))
    else:
        updated.setdefault("inventory", {})[reward["id"]] = int(updated.setdefault("inventory", {}).get(reward["id"], 0)) + int(reward["quantity"])
    stage_three["reward_claimed"] = True
    result["reward_claimed"] = True
    progression["reward_history"].append(reward)
    updated["processed_actions"][action_key] = True
    companion["last_reaction"] = f"随机奖励领取成功：{reward['name']}×{reward['quantity']}。"
    return updated, True, None


def advance_stage_three_scene(game: dict[str, Any], result_key: str) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(game)
    result = updated.get("minigame_results", {}).get(result_key)
    if not result:
        return updated, False
    next_scene = result.get("next_scene")
    if next_scene not in SCENES:
        return updated, False
    updated["scene_id"] = next_scene
    if next_scene == "stage_three_random_event":
        updated = ensure_random_event(updated)
    return updated, True


def calculate_anonymous_rank(game: dict[str, Any]) -> dict[str, Any]:
    progression = _ensure_progression(game)
    current = {
        "name": "当前玩家",
        "act": "协作试炼",
        "xp": int(game.get("xp", 0)),
        "growth_points": int(game.get("companion", {}).get("growth_points", 0)),
        "badge_count": len(progression.get("badges", {})),
    }
    def score(item: dict[str, Any]) -> int:
        return int(item["xp"]) + int(item["growth_points"]) * 20 + int(item["badge_count"]) * 35
    current["score"] = score(current)
    ranking = [dict(item, score=score(item)) for item in ANONYMOUS_RANKING] + [current]
    ranking.sort(key=lambda item: item["score"], reverse=True)
    rank = next(index + 1 for index, item in enumerate(ranking) if item["name"] == "当前玩家")
    beaten = len([item for item in ranking if item["name"] != "当前玩家" and current["score"] > item["score"]])
    percentile = round(beaten / len(ANONYMOUS_RANKING) * 100)
    result = {"rank": rank, "total": len(ranking), "percentile": percentile, "score": current["score"], "ranking": ranking}
    progression["anonymous_rank"] = result
    return result


def calculate_stage_three_result(game: dict[str, Any]) -> dict[str, Any]:
    stage_three = _ensure_stage_three(game)
    alignment = int(stage_three.get("alignment_score", 0))
    scope = int(stage_three.get("scope_score", 0))
    scope_result = game.get("minigame_results", {}).get("stage_three_scope", {})
    bonus_result = stage_three.get("bonus_task_result") or {}
    random_success = bool(bonus_result.get("success"))
    base_score = round(alignment * 0.47 + scope * 0.53)
    bonus_points = 10 if random_success else 0
    overall = min(100, base_score + bonus_points)
    if overall >= 85:
        rating = "S"
    elif overall >= 70:
        rating = "A"
    elif overall >= 55:
        rating = "B"
    else:
        rating = "C"
    blocking_reasons = []
    if alignment < 50:
        blocking_reasons.append("需求拉齐不足")
    if scope < 55:
        blocking_reasons.append("范围取舍不足")
    if scope_result.get("has_mvp") is not True:
        blocking_reasons.append("未形成最小可行方案")
    if int(game.get("risk", 0)) >= 70:
        blocking_reasons.append("风险过高")
    if int(stage_three.get("clarity", 0)) < 45:
        blocking_reasons.append("方案清晰度不足")
    executable = bool(overall >= 60 and alignment >= 50 and scope >= 55 and scope_result.get("has_mvp") is True and int(game.get("risk", 0)) < 70 and int(stage_three.get("clarity", 0)) >= 45)
    rank = calculate_anonymous_rank(game)
    return {
        "overall_score": overall,
        "base_score": base_score,
        "bonus_points": bonus_points,
        "alignment_score": alignment,
        "scope_score": scope,
        "rating": rating,
        "executable": executable,
        "blocking_reasons": blocking_reasons,
        "anonymous_rank": rank,
        "mentor_advice": "请带着范围取舍依据进入最终成果验收，重点说明延后项和风险预案。" if executable else "请先补齐共同目标、必做范围和风险预案，再进入成果验收。",
        "hr_signal": "协作推进可控，可沉淀为新人跨团队任务样例。" if executable else "出现协作或范围管理风险，建议导师增加过程校准。",
        "project_comment": "已经形成团队可执行版本。" if executable else "方案还需要在协作试炼中补足执行共识。",
    }


def complete_stage_three(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    stage_three = _ensure_stage_three(updated)
    stage_three["completed"] = True
    updated["stage_three_result"] = calculate_stage_three_result(updated)
    updated["scene_id"] = "stage_three_complete"
    updated["checkpoint_id"] = "stage_three_complete"
    updated["current_act"] = "act_three"
    updated["ending_id"] = None
    record_stage_check_in(updated, "act_three")
    return updated


def enter_stage_four(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    record_stage_check_in(updated, "act_three")
    stage_four = _ensure_stage_four(updated)
    stage_four["started"] = True
    prepare_stage_four_loadout(updated)
    updated["current_act"] = "act_four"
    updated["checkpoint_id"] = None
    updated["scene_id"] = "stage_four_briefing"
    updated["ending_id"] = None
    updated["stage_four_preview"] = False
    return updated


def prepare_stage_four_loadout(game: dict[str, Any]) -> dict[str, Any]:
    stage_four = _ensure_stage_four(game)
    loadout = stage_four["loadout"]
    companion = _ensure_companion(game)
    progression = _ensure_progression(game)
    loadout["hint_tokens"] = int(companion.get("hint_tokens", 0))
    loadout["evidence_boost_cards"] = min(1, int(companion.get("food_inventory", {}).get("evidence_star", 0)))
    loadout["collaboration_cards"] = int(game.get("inventory", {}).get("collaboration_hint_card", 0))
    loadout.setdefault("reroll_cards", 0)
    loadout.setdefault("fragments_spent", 0)
    loadout["_available_fragments"] = int(progression.get("badge_fragments", 0))
    return game


def exchange_badge_fragments(game: dict[str, Any]) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    stage_four = _ensure_stage_four(updated)
    progression = _ensure_progression(updated)
    if int(progression.get("badge_fragments", 0)) < 3:
        return updated, False, "徽章碎片不足。"
    progression["badge_fragments"] = int(progression.get("badge_fragments", 0)) - 3
    stage_four["loadout"]["reroll_cards"] = int(stage_four["loadout"].get("reroll_cards", 0)) + 1
    stage_four["loadout"]["fragments_spent"] = int(stage_four["loadout"].get("fragments_spent", 0)) + 3
    return updated, True, None


def _stage_four_seed(game: dict[str, Any]) -> int:
    return int(game.get("xp", 0)) + int(game.get("risk", 0)) * 11 + int(game.get("stage_three", {}).get("alignment_score", 0)) * 3 + int(game.get("stage_three", {}).get("scope_score", 0)) * 5


def normalize_boss_question(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {
            "id": "legacy_question",
            "title": "导师追问",
            "question": str(raw) if raw is not None else "当前题目数据不完整。",
            "answers": {},
        }
    answers = raw.get("answers") or raw.get("options") or {}
    if isinstance(answers, list):
        answers = {
            str(index + 1): {
                "text": str(option),
                "evidence": 50,
                "boundary": 50,
                "action": 50,
            }
            for index, option in enumerate(answers)
        }
    if not isinstance(answers, dict):
        answers = {}
    normalized_answers: dict[str, dict[str, Any]] = {}
    for answer_id, answer in answers.items():
        if isinstance(answer, dict):
            normalized_answers[str(answer_id)] = {
                "text": str(answer.get("text") or answer.get("label") or answer.get("title") or "未命名回答"),
                "evidence": int(answer.get("evidence", 50)),
                "boundary": int(answer.get("boundary", 50)),
                "action": int(answer.get("action", 50)),
            }
        else:
            normalized_answers[str(answer_id)] = {"text": str(answer), "evidence": 50, "boundary": 50, "action": 50}
    return {
        "id": str(raw.get("id") or "unknown"),
        "title": str(raw.get("title") or raw.get("label") or raw.get("type") or "导师追问"),
        "body": str(raw.get("body") or raw.get("prompt") or raw.get("question") or raw.get("text") or "当前题目数据不完整。"),
        "prompt": str(raw.get("prompt") or raw.get("question") or raw.get("text") or raw.get("body") or "当前题目数据不完整。"),
        "focus": str(raw.get("focus") or raw.get("hint") or "导师当前关注证据、边界和下一步行动。"),
        "stakeholder_hint": str(raw.get("stakeholder_hint") or raw.get("hint") or "请结合相关协作方约束回答。"),
        "answers": normalized_answers,
        "correct_option": raw.get("correct_option", raw.get("answer")),
        "explanation": str(raw.get("explanation", "")),
        "hint": str(raw.get("hint", raw.get("focus", ""))),
    }


def _boss_questions_for_seed(seed: int) -> list[dict[str, Any]]:
    start = seed % len(BOSS_QUESTIONS)
    ordered = BOSS_QUESTIONS[start:] + BOSS_QUESTIONS[:start]
    return [normalize_boss_question(question) for question in deepcopy(ordered[:4])]


def ensure_boss_questions(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    boss = _ensure_stage_four(updated)["boss"]
    if boss.get("seed") is None:
        boss["seed"] = _stage_four_seed(updated)
    if not boss.get("questions"):
        boss["questions"] = _boss_questions_for_seed(int(boss["seed"]))
    else:
        boss["questions"] = [normalize_boss_question(question) for question in boss.get("questions", [])]
    return updated


def evaluate_stage_four_evidence(slots: dict[str, str | None], support_cards: list[str] | None = None) -> dict[str, Any]:
    card_map = {card["id"]: card for card in STAGE_FOUR_EVIDENCE_CARDS}
    support_cards = list(dict.fromkeys(support_cards or []))[:2]
    slot_results = {}
    weak_slots = []
    strong_combinations = []
    selected_core = [card_id for card_id in slots.values() if card_id]
    if len(set(selected_core)) != len(selected_core):
        return {"error": "同一证据不能重复使用。"}
    score = 0
    coverage = 0
    for slot, card_id in slots.items():
        card = card_map.get(card_id or "")
        if not card:
            slot_results[slot] = {"label": "关键证据缺失", "score": 0, "card_name": "未选择"}
            weak_slots.append(slot)
            continue
        matched = card.get("slot") == slot
        quality = card.get("quality")
        slot_score = 0
        label = "关键证据缺失"
        if quality == "high" and matched:
            slot_score, label = 25, "强证据"
            coverage += 1
        elif quality == "medium" and matched:
            slot_score, label = 16, "辅助证据"
            coverage += 1
        elif quality == "high" and not matched:
            slot_score, label = 10, "证据不匹配"
        elif quality == "low":
            slot_score, label = 0, "AI推断" if card_id in {"ai_summary", "ai_recommendation"} else "证据不匹配"
            if card_id in {"personal_feeling", "ai_recommendation"}:
                score -= 10
        if slot_score < 16:
            weak_slots.append(slot)
        score += slot_score
        slot_results[slot] = {"label": label, "score": slot_score, "card_name": card["name"], "quality": quality, "matched": matched}
    chosen = set(selected_core) | set(support_cards)
    if {"player_interviews", "activity_data"} <= chosen:
        score += 5
        strong_combinations.append("用户证据+数据证据均为高质量")
    if slots.get("execution") == "scope_plan" and slots.get("risk") == "rollback_plan":
        score += 5
        strong_combinations.append("最小可行方案范围清单+回滚方案")
    if {"risk_monitor", "rollback_plan"} <= chosen:
        score += 5
        strong_combinations.append("同时具备风险监控和回滚方案")
    score = max(0, min(100, score))
    return {
        "score": score,
        "coverage": coverage,
        "slot_results": slot_results,
        "weak_slots": sorted(set(weak_slots)),
        "strong_combinations": strong_combinations,
        "passed": score >= 60 and coverage >= 3,
        "support_cards": support_cards,
    }


def submit_stage_four_evidence(game: dict[str, Any], slots: dict[str, str | None], support_cards: list[str] | None = None) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    if updated.get("scene_id") != "stage_four_evidence":
        return updated, False, "当前不在成果证据装配台。"
    board = _ensure_stage_four(updated)["evidence_board"]
    if board.get("submitted"):
        return updated, False, None
    support_cards = support_cards or []
    if len(support_cards) > 2:
        return updated, False, "最多只能选择2张支撑证据。"
    if len(support_cards) != len(set(support_cards)):
        return updated, False, "同一张支撑证据不能重复选择。"
    required = {"user", "data", "execution", "risk"}
    if set(slots) != required or any(not slots.get(slot) for slot in required):
        return updated, False, "四个证据槽必须全部选择。"
    result = evaluate_stage_four_evidence(slots, support_cards)
    if result.get("error"):
        return updated, False, result["error"]
    board["slots"] = deepcopy(slots)
    board["support_cards"] = result["support_cards"]
    board["submitted"] = True
    board["score"] = result["score"]
    board["coverage"] = result["coverage"]
    board["weak_slots"] = result["weak_slots"]
    board["slot_results"] = result["slot_results"]
    board["strong_combinations"] = result["strong_combinations"]
    board["passed"] = result["passed"]
    updated["processed_actions"]["stage_four_evidence:submit"] = True
    _apply_deltas(updated, {"verification": 5 if result["passed"] else 1, "xp": 80 if result["passed"] else 35})
    return updated, True, None


def use_stage_four_item(game: dict[str, Any], item_id: str, question_id: str | None = None) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    stage_four = _ensure_stage_four(updated)
    loadout = stage_four["loadout"]
    boss = stage_four["boss"]
    question_id = question_id or (boss.get("questions") or [{"id": "unknown"}])[int(boss.get("current_index", 0))].get("id", "unknown")
    action_key = f"stage_four_item:{item_id}:{question_id}"
    if updated.get("processed_actions", {}).get(action_key):
        return updated, False, None
    inventory = updated.setdefault("inventory", {})
    if item_id == "hint_token":
        if int(loadout.get("hint_tokens", 0)) <= 0:
            return updated, False, "提示券不足。"
        loadout["hint_tokens"] -= 1
    elif item_id == "reroll_card":
        if int(loadout.get("reroll_cards", 0)) <= 0:
            return updated, False, "重抽卡不足。"
        loadout["reroll_cards"] -= 1
        seed = int(boss.get("seed") or _stage_four_seed(updated)) + int(boss.get("current_index", 0)) + 1
        pool = _boss_questions_for_seed(seed)
        used_ids = {q["id"] for q in boss.get("questions", [])}
        replacement = next((q for q in pool if q["id"] not in used_ids), pool[0])
        boss["questions"][int(boss.get("current_index", 0))] = replacement
    elif item_id == "collaboration_card":
        if int(loadout.get("collaboration_cards", 0)) <= 0:
            return updated, False, "协作提示卡不足。"
        loadout["collaboration_cards"] -= 1
        inventory["collaboration_hint_card"] = max(0, int(inventory.get("collaboration_hint_card", 0)) - 1)
    elif item_id == "evidence_boost":
        if int(loadout.get("evidence_boost_cards", 0)) <= 0:
            return updated, False, "证据强化卡不足。"
        loadout["evidence_boost_cards"] -= 1
        companion = _ensure_companion(updated)
        companion["food_inventory"]["evidence_star"] = max(0, int(companion["food_inventory"].get("evidence_star", 0)) - 1)
    elif item_id == "easter_card":
        if int(inventory.get("easter_card", 0)) <= 0:
            return updated, False, "彩蛋卡不足。"
        inventory["easter_card"] = max(0, int(inventory.get("easter_card", 0)) - 1)
        inventory["hidden_ending_fragment"] = int(inventory.get("hidden_ending_fragment", 0)) + 1
    else:
        return updated, False, "未知道具。"
    boss.setdefault("used_items", []).append({"item_id": item_id, "question_id": question_id})
    updated["processed_actions"][action_key] = True
    return updated, True, None


def _question_score(answer: dict[str, int], evidence_boost: bool = False) -> int:
    evidence = min(100, int(answer["evidence"]) + (10 if evidence_boost else 0))
    return round(evidence * 0.4 + int(answer["boundary"]) * 0.25 + int(answer["action"]) * 0.35)


def submit_boss_answer(game: dict[str, Any], answer_id: str) -> tuple[dict[str, Any], bool, str | None]:
    updated = ensure_boss_questions(game)
    if updated.get("scene_id") != "stage_four_boss":
        return updated, False, "当前不在导师问答终局追问。"
    stage_four = _ensure_stage_four(updated)
    boss = stage_four["boss"]
    if boss.get("completed"):
        return updated, False, None
    index = int(boss.get("current_index", 0))
    questions = boss.get("questions", [])
    if index >= len(questions):
        return updated, False, "终局追问已经结束。"
    question = normalize_boss_question(questions[index])
    question_id = question.get("id", f"boss_{index}")
    action_key = f"stage_four_boss:{question_id}:answer"
    if updated.get("processed_actions", {}).get(action_key):
        return updated, False, None
    answer = question.get("answers", {}).get(answer_id)
    if not answer:
        return updated, False, "请选择一个回答。"
    used_items = boss.get("used_items", [])
    boosted = any(item.get("item_id") == "evidence_boost" and item.get("question_id") == question_id for item in used_items)
    score = _question_score(answer, boosted)
    if score >= 90:
        delta = 12
    elif score >= 75:
        delta = 7
    elif score >= 60:
        delta = 2
    elif score >= 40:
        delta = -8
    else:
        delta = -15
    before = int(boss.get("credibility", 70))
    boss["credibility"] = clamp(before + delta)
    if boss["credibility"] < 25:
        boss.setdefault("remediation_tasks", []).append({"id": f"remediation_{question_id}", "question_id": question_id, "type": "补充上线验证指标", "completed": False})
    feedback = (
        f"证据支撑{answer['evidence']}分，边界意识{answer['boundary']}分，行动计划{answer['action']}分。"
        f"导师可信度变化{boss['credibility'] - before:+d}。"
    )
    record = {
        "question_id": question_id,
        "answer_id": answer_id,
        "score": score,
        "credibility_before": before,
        "credibility_after": boss["credibility"],
        "delta": boss["credibility"] - before,
        "dimensions": deepcopy(answer),
        "feedback": feedback,
    }
    boss.setdefault("answers", []).append(record)
    boss["score"] = round(sum(item["score"] for item in boss["answers"]) / len(boss["answers"]))
    updated["processed_actions"][action_key] = True
    _ensure_companion(updated)["last_reaction"] = "回答很稳，证据和边界都站住了。" if score >= 75 else "这题有点摇晃，补上证据或边界会更稳。"
    return updated, True, None


def advance_boss_question(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    boss = _ensure_stage_four(updated)["boss"]
    boss["current_index"] = int(boss.get("current_index", 0)) + 1
    if boss["current_index"] >= len(boss.get("questions", [])):
        boss["completed"] = True
        updated["scene_id"] = "stage_four_remediation" if boss.get("remediation_tasks") else "stage_four_bonus"
    return updated


def submit_remediation_task(game: dict[str, Any], task_id: str, success: bool) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    boss = _ensure_stage_four(updated)["boss"]
    action_key = f"stage_four_remediation:{task_id}"
    if updated.get("processed_actions", {}).get(action_key):
        return updated, False, None
    task = next((item for item in boss.get("remediation_tasks", []) if item["id"] == task_id), None)
    if not task:
        return updated, False, "补答任务不存在。"
    if success:
        boss["credibility"] = clamp(int(boss.get("credibility", 70)) + 5)
    task["completed"] = True
    task["success"] = bool(success)
    updated["processed_actions"][action_key] = True
    return updated, True, None


def ensure_stage_four_bonus(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    stage_four = _ensure_stage_four(updated)
    bonus = stage_four["bonus_task"]
    if not bonus.get("event_id"):
        seed = _stage_four_seed(updated) + int(stage_four["boss"].get("score", 0))
        bonus["event_id"] = STAGE_FOUR_BONUS_EVENTS[seed % len(STAGE_FOUR_BONUS_EVENTS)]["id"]
    return updated


def current_stage_four_bonus(game: dict[str, Any]) -> dict[str, Any]:
    bonus = _ensure_stage_four(game)["bonus_task"]
    event_id = bonus.get("event_id") or STAGE_FOUR_BONUS_EVENTS[0]["id"]
    return next((event for event in STAGE_FOUR_BONUS_EVENTS if event["id"] == event_id), STAGE_FOUR_BONUS_EVENTS[0])


def submit_stage_four_bonus(game: dict[str, Any], option_id: str) -> tuple[dict[str, Any], bool, str | None]:
    updated = ensure_stage_four_bonus(game)
    bonus = _ensure_stage_four(updated)["bonus_task"]
    if bonus.get("submitted"):
        return updated, False, None
    event = current_stage_four_bonus(updated)
    option = event.get("options", {}).get(option_id)
    if not option:
        return updated, False, "请选择一个加试回答。"
    success = bool(option["success"])
    bonus["submitted"] = True
    bonus["success"] = success
    bonus["bonus_points"] = 8 if success else 0
    bonus["option_id"] = option_id
    if success:
        reward = {"id": "hidden_ending_fragment", "type": "inventory", "name": "隐藏结局碎片", "quantity": 1}
        bonus["reward"] = reward
    return updated, True, None


def claim_stage_four_bonus_reward(game: dict[str, Any]) -> tuple[dict[str, Any], bool, str | None]:
    updated = deepcopy(game)
    bonus = _ensure_stage_four(updated)["bonus_task"]
    if not bonus.get("success"):
        return updated, False, "没有可领取的加试奖励。"
    if bonus.get("reward_claimed"):
        return updated, False, None
    reward = bonus.get("reward", {"id": "hidden_ending_fragment", "name": "隐藏结局碎片", "quantity": 1})
    updated.setdefault("inventory", {})[reward["id"]] = int(updated.setdefault("inventory", {}).get(reward["id"], 0)) + int(reward.get("quantity", 1))
    bonus["reward_claimed"] = True
    return updated, True, None


def determine_ending(game: dict[str, Any], final_result: dict[str, Any]) -> str:
    badges = _ensure_progression(game).get("badges", {})
    stage_two = game.get("stage_two_result", {})
    stage_three_result = game.get("stage_three_result", {})
    stage_three = game.get("stage_three", {})
    companion = _ensure_companion(game)
    inventory = game.get("inventory", {})
    evidence_score = final_result.get("evidence_score", 0)
    boss_score = final_result.get("boss_score", 0)
    final_score = final_result.get("final_score", 0)
    stage_three_bonus = game.get("stage_three", {}).get("bonus_task_result") or {}
    if companion.get("stage", 1) >= 6 and stage_three_bonus.get("success") and int(inventory.get("hidden_ending_fragment", 0)) > 0 and final_score >= 85:
        return "yaya_partner"
    if final_score >= 90 and stage_two.get("passed") and stage_three_result.get("executable") and evidence_score >= 85 and boss_score >= 85 and int(game.get("risk", 0)) <= 30 and len(badges) >= 4:
        return "full_chain_owner"
    if evidence_score >= 90 and int(game.get("stats", {}).get("verification", 0)) >= 75 and int(game.get("risk", 0)) <= 45:
        return "evidence_guardian"
    if int(stage_three.get("alignment_score", 0)) >= 85 and int(stage_three.get("team_trust", 0)) >= 70 and boss_score >= 75:
        return "collaboration_driver_end"
    if final_result.get("final_passed") and final_score >= 70 and int(game.get("risk", 0)) <= 50:
        return "steady_deliverer"
    return "high_potential"


def calculate_stage_four_final(game: dict[str, Any]) -> dict[str, Any]:
    stage_four = _ensure_stage_four(game)
    evidence_score = int(stage_four["evidence_board"].get("score", 0))
    boss_score = int(stage_four["boss"].get("score", 0))
    bonus_points = int(stage_four["bonus_task"].get("bonus_points", 0))
    base_score = round(evidence_score * 0.45 + boss_score * 0.55)
    final_score = min(100, round(base_score + bonus_points))
    final_passed = bool(final_score >= 60 and evidence_score >= 55 and boss_score >= 50 and int(stage_four["boss"].get("credibility", 0)) >= 35 and int(game.get("risk", 0)) < 75)
    result = {
        "evidence_score": evidence_score,
        "boss_score": boss_score,
        "boss_credibility": int(stage_four["boss"].get("credibility", 0)),
        "base_score": base_score,
        "bonus_points": bonus_points,
        "final_score": final_score,
        "final_passed": final_passed,
    }
    result["ending_id"] = determine_ending(game, result)
    return result


def complete_stage_four(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    stage_four = _ensure_stage_four(updated)
    stage_four["completed"] = True
    final_result = calculate_stage_four_final(updated)
    stage_four["final_result"] = final_result
    updated["ending_id"] = final_result["ending_id"]
    updated["checkpoint_id"] = "stage_four_complete"
    updated["scene_id"] = "stage_four_complete"
    updated["current_act"] = "act_four"
    post = _ensure_post_game(updated)
    post["unlocked"] = True
    post["run_count"] = int(post.get("run_count", 0)) + 1
    post["current_ending"] = updated["ending_id"]
    post.setdefault("endings_unlocked", {})[updated["ending_id"]] = deepcopy(ENDING_DEFINITIONS[updated["ending_id"]])
    post.setdefault("ending_archive", []).append({"ending_id": updated["ending_id"], "final_score": final_result["final_score"], "run": post["run_count"]})
    post["new_game_plus_unlocked"] = True
    record_stage_check_in(updated, "act_four")
    return updated


def enter_post_game_hub(game: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(game)
    if not _ensure_post_game(updated).get("unlocked"):
        return updated
    updated["scene_id"] = "post_game_hub"
    return updated


def export_game_save(game: dict[str, Any]) -> str:
    payload_game = deepcopy(game)
    for key in ["evidence_records", "growth_plan", "gate_results", "mentor_decisions", "demo_step", "demo_week"]:
        payload_game.pop(key, None)
    payload = {"schema_version": 1, "export_time": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"), "game": payload_game}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload["checksum"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return json.dumps(payload, ensure_ascii=False, indent=2)


def import_game_save(data: str | dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(data) if isinstance(data, str) else deepcopy(data)
    except Exception:
        return None, "成长档案不是有效JSON。"
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("game"), dict):
        return None, "成长档案格式不正确。"
    game = normalize_game_state(payload["game"])
    for key in BOUNDED_KEYS:
        if key in STAT_KEYS:
            game["stats"][key] = clamp(game["stats"][key])
        else:
            game[key] = clamp(game[key])
    game["xp"] = max(0, int(game.get("xp", 0)))
    return game, None


def start_new_game_plus(game: dict[str, Any]) -> dict[str, Any]:
    previous = normalize_game_state(game)
    new_game = initial_game_state()
    post = deepcopy(previous.get("post_game", initial_post_game_state()))
    post["new_game_plus_unlocked"] = True
    new_game["post_game"] = post
    new_game["companion"]["stage"] = previous.get("companion", {}).get("stage", 1)
    new_game["companion"]["stage_name"] = previous.get("companion", {}).get("stage_name", "初来乍到")
    new_game["companion"]["growth_points"] = previous.get("companion", {}).get("growth_points", 0)
    new_game["progression"]["badges"] = deepcopy(previous.get("progression", {}).get("badges", {}))
    new_game["mode"] = "new_game_plus"
    new_game["reset_version"] = int(previous.get("reset_version", 0)) + 1
    return new_game


def advance_after_minigame(game: dict[str, Any], result_key: str) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(game)
    result = updated.get("minigame_results", {}).get(result_key)
    if not result:
        return updated, False
    companion = _ensure_companion(updated)
    if not companion.get("fed_rewards", {}).get(result_key):
        return updated, False
    if result.get("remediation_status") == "pending":
        return updated, False
    next_scene = result.get("next_scene")
    if next_scene not in SCENES:
        return updated, False
    updated["scene_id"] = next_scene
    if next_scene == "stage_two_complete":
        updated["checkpoint_id"] = "stage_two_complete"
        updated["current_act"] = "act_two"
        updated["ending_id"] = None
        updated["stage_two_result"] = calculate_stage_two_result(updated)
        record_stage_check_in(updated, "act_two")
    return updated, True


def calculate_stage_two_result(game: dict[str, Any]) -> dict[str, Any]:
    scores = game.get("stage_two_scores", {})
    ai_review = int(scores.get("ai_review", 0))
    priority = int(scores.get("priority", 0))
    evidence = int(scores.get("evidence", 0))
    overall = round(ai_review * 0.35 + priority * 0.30 + evidence * 0.35)
    if overall >= 85:
        rating = "S"
    elif overall >= 70:
        rating = "A"
    elif overall >= 55:
        rating = "B"
    else:
        rating = "C"
    low_value_busy = bool(game.get("minigame_results", {}).get("priority", {}).get("low_value_busy"))
    risk_tags = []
    if low_value_busy:
        risk_tags.append("低价值忙碌")
    if ai_review < 50 or int(game.get("stats", {}).get("ai_collaboration", 0)) >= 35 and int(game.get("stats", {}).get("verification", 0)) < 45:
        risk_tags.append("AI依赖")
    if int(game.get("risk", 0)) >= 40:
        risk_tags.append("高风险")
    if evidence < 50:
        risk_tags.append("证据不足")
    if ai_review < 50:
        risk_tags.append("AI审查不足")

    if ai_review >= 80 and evidence >= 80 and not risk_tags:
        primary_behavior_type = "证据型推进者"
    elif priority >= 70 and int(game.get("mentor_trust", 0)) >= 35 and int(game.get("risk", 0)) <= 30 and not risk_tags:
        primary_behavior_type = "稳健协作型"
    elif priority >= 70 and not low_value_busy:
        primary_behavior_type = "速度优先型"
    else:
        primary_behavior_type = "成长探索型"
    passed = overall >= 60 and ai_review >= 50 and evidence >= 50 and int(game.get("risk", 0)) < 70
    return {
        "overall_score": overall,
        "rating": rating,
        "primary_behavior_type": primary_behavior_type,
        "risk_tags": risk_tags,
        "behavior_type": primary_behavior_type,
        "passed": passed,
        "project_owner_comment": "方案达到预评审要求，可以带着证据进入跨团队讨论。" if passed else "方案暂未达到预评审要求，需要在协作试炼中补足。",
        "mentor_next_step": "下一步请准备回答资源范围、数据口径和反例处理三个问题。",
        "hr_risk_judgement": "当前风险可控，重点观察后续协作质量。" if int(game.get("risk", 0)) < 40 else "风险仍偏高，建议导师在下一幕增加过程校准。",
    }
