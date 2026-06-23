from __future__ import annotations

from typing import Any


DISPLAY_NAMES = {
    "business": "业务理解",
    "ai_collaboration": "AI协作",
    "verification": "结果验证",
    "collaboration": "跨团队协作",
    "delivery": "独立交付",
    "energy": "精力",
    "mentor_trust": "导师信任",
    "risk": "风险",
    "xp": "经验值",
}

STAT_KEYS = ("business", "ai_collaboration", "verification", "collaboration", "delivery")
BOUNDED_KEYS = (*STAT_KEYS, "energy", "mentor_trust", "risk")

LEVEL_THRESHOLDS = [
    (0, 1, "成长新兵"),
    (60, 2, "业务探索者"),
    (140, 3, "AI协作者"),
    (260, 4, "证据守门人"),
    (420, 5, "独立交付者"),
]

BADGE_DEFINITIONS = {
    "first_choice": {"name": "关键第一步", "description": "完成第一次业务选择。"},
    "verification_guard": {"name": "证据守门人", "description": "在关键决策中主动核验AI信息。"},
    "collaboration_driver": {"name": "协作推进者", "description": "在需求拉齐会中高质量识别约束并推进共同目标。"},
    "scope_manager": {"name": "范围管理者", "description": "在预算内形成可执行最小方案。"},
    "incident_responder": {"name": "临场应变者", "description": "成功完成协作试炼中的随机额外任务。"},
    "hidden_finder": {"name": "隐藏任务发现者", "description": "触发特殊随机事件或彩蛋奖励。"},
    "streak_keeper": {"name": "连续打卡者", "description": "连续完成三个阶段打卡。"},
}

GAME_ACTS = [
    {
        "id": "act_one",
        "name": "开局判断",
        "description": "理解业务、选择学习方式并识别AI基础风险。",
    },
    {
        "id": "act_two",
        "name": "方案救火",
        "description": "在有限时间内把有问题的AI初稿整理为可评审方案。",
    },
    {
        "id": "act_three",
        "name": "协作试炼",
        "description": "处理导师缺席、跨团队冲突和范围取舍。",
    },
    {
        "id": "act_four",
        "name": "成果验收",
        "description": "提交证据、接受导师验收并形成最终成长结局。",
        "locked": False,
    },
]

ENDING_DEFINITIONS: dict[str, dict[str, Any]] = {
    "full_chain_owner": {"name": "全链路负责人", "description": "能把证据、协作、范围和风险串成完整交付闭环。"},
    "evidence_guardian": {"name": "证据守门人", "description": "最擅长用可追溯证据保护业务判断质量。"},
    "collaboration_driver_end": {"name": "协作推进者", "description": "能把多方约束转成共同目标和可执行范围。"},
    "steady_deliverer": {"name": "稳健交付者", "description": "在风险可控前提下完成稳定交付。"},
    "high_potential": {"name": "高潜成长型", "description": "仍需补强部分能力，但已经形成清晰成长方向。"},
    "yaya_partner": {"name": "芽芽的全链路搭档", "description": "隐藏结局。你和芽芽完成了从证据到协作再到验收的全链路挑战。", "hidden": True},
}

CHECKPOINT_DEFINITIONS = {
    "stage_one_complete": {
        "name": "开局判断完成",
        "description": "完成业务理解和AI基础核验两项判断。",
    },
    "stage_two_complete": {
        "name": "方案救火完成",
        "description": "完成AI方案审查、任务优先级和证据包组装。",
    },
    "stage_three_complete": {
        "name": "协作试炼完成",
        "description": "完成跨团队拉齐、范围取舍和临场应变。",
    },
    "stage_four_complete": {
        "name": "成果验收完成",
        "description": "完成终局评审、导师问答和最终成长结论。",
    },
}

AI_REVIEW_ITEMS = [
    {"id": "1", "text": "声称“80%的玩家喜欢限时抽奖”，但没有任何数据来源。", "is_issue": True},
    {"id": "2", "text": "因为高活跃玩家更常参加活动，所以直接断定活动导致高活跃。", "is_issue": True},
    {"id": "3", "text": "建议上传完整用户手机号列表给AI进行分群分析。", "is_issue": True},
    {"id": "4", "text": "方案完全没有考虑活动预算和开发周期。", "is_issue": True},
    {"id": "5", "text": "建议先进行小流量测试，再根据结果调整方案。", "is_issue": False},
]

PRIORITY_TASKS = [
    {"id": "training", "name": "参加2小时通用培训", "cost": 3, "business_value": 2, "risk_reduction": 1, "type": "learning"},
    {"id": "user_feedback", "name": "整理真实用户反馈", "cost": 4, "business_value": 5, "risk_reduction": 3, "type": "real_business"},
    {"id": "ppt_animation", "name": "优化汇报PPT动画", "cost": 2, "business_value": 1, "risk_reduction": 0, "type": "presentation"},
    {"id": "mentor_calibration", "name": "与导师进行30分钟校准", "cost": 2, "business_value": 4, "risk_reduction": 4, "type": "feedback"},
    {"id": "data_definition", "name": "补充活动数据口径", "cost": 4, "business_value": 5, "risk_reduction": 5, "type": "real_business"},
    {"id": "ai_drawing", "name": "学习新的AI绘图工具", "cost": 3, "business_value": 2, "risk_reduction": 1, "type": "learning"},
]

EVIDENCE_ITEMS = [
    {"id": "personal_feeling", "text": "我个人感觉玩家会喜欢。", "quality": "low"},
    {"id": "ai_analysis", "text": "AI生成的用户分析。", "quality": "ai_only"},
    {"id": "player_interviews", "text": "5名真实玩家访谈记录。", "quality": "high"},
    {"id": "activity_data", "text": "近3期同类活动参与数据。", "quality": "high"},
    {"id": "metric_definition", "text": "已经核对的数据口径说明。", "quality": "high"},
    {"id": "social_comment", "text": "一条社交媒体评论。", "quality": "medium"},
    {"id": "counter_example", "text": "反例：类似活动曾因奖励规则复杂导致参与下降。", "quality": "high"},
]

FOOD_DEFINITIONS = {
    "verification_berry": {"name": "核验莓", "emoji": "●", "theme": "#9B8AFB"},
    "action_cookie": {"name": "行动饼", "emoji": "●", "theme": "#FFB45B"},
    "evidence_star": {"name": "证据星", "emoji": "★", "theme": "#63D7B0"},
    "review_cookie": {"name": "复盘饼", "emoji": "●", "theme": "#FFD66B"},
}

ALIGNMENT_ROLES = [
    {"id": "product", "name": "产品", "challenge": "希望增加更多玩法，以提升传播效果。"},
    {"id": "engineering", "name": "程序", "challenge": "认为当前开发周期不足，只能保留核心功能。"},
    {"id": "art", "name": "美术", "challenge": "资源已被其他项目占用，无法制作全部新素材。"},
    {"id": "operation", "name": "运营", "challenge": "担心玩法复杂，用户理解成本过高。"},
]

ALIGNMENT_OPTIONS_BY_ROLE = {
    "product": {
        "A": {
            "title": "保留全部玩法，要求团队加速",
            "description": "继续追求完整玩法，但会放大协作压力。",
            "effects": {"collaboration": -2, "team_trust": -5, "clarity": -2, "risk": 6, "mentor_trust": -2, "xp": 25},
            "score": 35,
        },
        "B": {
            "title": "确认核心增长目标，删减低价值玩法",
            "description": "先锁定增长目标，再删除低价值范围。",
            "effects": {"collaboration": 6, "team_trust": 6, "clarity": 9, "risk": -4, "mentor_trust": 3, "xp": 65},
            "score": 86,
        },
        "C": {
            "title": "先保留核心玩法，再安排灰度验证",
            "description": "保住核心玩法，用灰度验证降低决策风险。",
            "effects": {"collaboration": 5, "team_trust": 5, "clarity": 7, "risk": -3, "mentor_trust": 2, "xp": 60},
            "score": 91,
        },
    },
    "engineering": {
        "A": {
            "title": "要求程序按原方案全部实现",
            "description": "忽视工程周期约束，风险明显上升。",
            "effects": {"collaboration": -3, "team_trust": -6, "clarity": -2, "risk": 8, "mentor_trust": -2, "xp": 20},
            "score": 30,
        },
        "B": {
            "title": "确认工期瓶颈，保留核心机制和回滚方案",
            "description": "先确认工程瓶颈，保住核心闭环和回滚能力。",
            "effects": {"collaboration": 7, "team_trust": 8, "clarity": 10, "risk": -6, "mentor_trust": 4, "xp": 70},
            "score": 92,
        },
        "C": {
            "title": "让AI自动生成技术方案并直接排期",
            "description": "AI能辅助拆解，但不能替代工程评估。",
            "effects": {"ai_collaboration": 3, "collaboration": 1, "team_trust": -3, "clarity": 1, "risk": 6, "xp": 40},
            "score": 48,
        },
    },
    "art": {
        "A": {
            "title": "坚持制作全部新素材",
            "description": "继续追求完整视觉规格，但会冲击资源现实。",
            "effects": {"collaboration": -2, "team_trust": -5, "clarity": -1, "risk": 6, "xp": 25},
            "score": 35,
        },
        "B": {
            "title": "复用现有素材，降低非核心表现规格",
            "description": "复用素材保证上线可行性，把表现投入留给核心点。",
            "effects": {"collaboration": 7, "team_trust": 7, "clarity": 8, "risk": -4, "mentor_trust": 3, "xp": 65},
            "score": 84,
        },
        "C": {
            "title": "保留一项重点动画，其余改为轻量表现",
            "description": "保留视觉记忆点，同时控制美术范围。",
            "effects": {"collaboration": 6, "team_trust": 6, "clarity": 7, "risk": -3, "xp": 60},
            "score": 91,
        },
    },
    "operation": {
        "A": {
            "title": "保持复杂玩法，由运营加强说明",
            "description": "把理解成本交给运营说明，可能影响用户体验。",
            "effects": {"collaboration": -1, "team_trust": -3, "clarity": -5, "risk": 6, "xp": 25},
            "score": 38,
        },
        "B": {
            "title": "简化首轮规则，增加新手引导",
            "description": "降低理解门槛，优先保护首轮参与。",
            "effects": {"collaboration": 7, "team_trust": 7, "clarity": 10, "risk": -5, "mentor_trust": 3, "xp": 65},
            "score": 86,
        },
        "C": {
            "title": "先小流量测试，再根据用户反馈调整",
            "description": "用小流量测试把运营担心转成证据。",
            "effects": {"collaboration": 6, "team_trust": 6, "clarity": 7, "risk": -6, "xp": 65},
            "score": 92,
        },
    },
}

SCOPE_TASKS = [
    {"id": "core_loop", "name": "核心活动机制", "dev": 4, "art": 1, "time": 3, "business": 6, "risk": 3, "critical": True, "category": "core"},
    {"id": "onboarding", "name": "新手引导", "dev": 2, "art": 1, "time": 2, "business": 4, "risk": 3, "critical": False, "category": "usability"},
    {"id": "extra_animation", "name": "额外美术动画", "dev": 1, "art": 4, "time": 3, "business": 2, "risk": 0, "critical": False, "category": "visual"},
    {"id": "reward_skins", "name": "多套奖励皮肤", "dev": 1, "art": 4, "time": 3, "business": 3, "risk": 0, "critical": False, "category": "visual"},
    {"id": "data_tracking", "name": "用户数据埋点", "dev": 3, "art": 0, "time": 2, "business": 4, "risk": 5, "critical": True, "category": "risk"},
    {"id": "risk_monitor", "name": "风险监控方案", "dev": 2, "art": 0, "time": 2, "business": 3, "risk": 6, "critical": True, "category": "risk"},
    {"id": "social_share", "name": "社交分享入口", "dev": 3, "art": 2, "time": 2, "business": 4, "risk": 1, "critical": False, "category": "growth"},
    {"id": "rollback_plan", "name": "备用回滚方案", "dev": 2, "art": 0, "time": 1, "business": 2, "risk": 6, "critical": True, "category": "risk"},
]

SCOPE_BUDGET = {"dev": 10, "art": 7, "time": 10}

RANDOM_EVENTS = [
    {
        "id": "engineering_cut",
        "title": "程序工期临时缩短20%",
        "challenge": "请判断最稳妥的应对方式。",
        "options": {
            "A": {"text": "保留核心机制、埋点和回滚，延后非核心表现", "success": True},
            "B": {"text": "删掉风险监控，保留传播入口", "success": False},
            "C": {"text": "维持全部范围，要求程序加班完成", "success": False},
        },
    },
    {
        "id": "art_reassigned",
        "title": "美术资源临时被抽走",
        "challenge": "你需要让方案仍然可以上线。",
        "options": {
            "A": {"text": "使用现有素材和轻量样式，保留玩法闭环", "success": True},
            "B": {"text": "继续等待全新素材完成", "success": False},
            "C": {"text": "把所有活动目标改成视觉展示", "success": False},
        },
    },
    {
        "id": "ops_emergency_entry",
        "title": "运营要求增加一个紧急入口",
        "challenge": "请决定如何处理新增诉求。",
        "options": {
            "A": {"text": "确认入口目标和影响面，只纳入低成本灰度入口", "success": True},
            "B": {"text": "直接追加入口，不重新评估范围", "success": False},
            "C": {"text": "完全拒绝运营诉求，不讨论替代方案", "success": False},
        },
    },
    {
        "id": "mentor_absent",
        "title": "导师临时无法参加评审",
        "challenge": "你需要保留协作质量。",
        "options": {
            "A": {"text": "整理决策依据，请代理评审人确认风险边界", "success": True},
            "B": {"text": "跳过校准，先按自己的理解推进", "success": False},
            "C": {"text": "暂停所有工作，等待导师回来", "success": False},
        },
    },
    {
        "id": "metric_changed",
        "title": "关键数据口径突然变化",
        "challenge": "你需要处理证据链波动。",
        "options": {
            "A": {"text": "标注口径变化，重算关键指标并保留版本说明", "success": True},
            "B": {"text": "沿用旧口径，避免影响评审节奏", "success": False},
            "C": {"text": "删除全部数据，只保留主观判断", "success": False},
        },
    },
    {
        "id": "usability_blocker",
        "title": "测试发现核心玩法存在理解障碍",
        "challenge": "请快速补救可理解性问题。",
        "options": {
            "A": {"text": "补充新手引导和小流量验证，暂缓复杂扩展", "success": True},
            "B": {"text": "继续增加奖励，试图用奖励覆盖理解问题", "success": False},
            "C": {"text": "忽略测试反馈，等上线后再看数据", "success": False},
        },
    },
]

RANDOM_REWARDS = [
    {"id": "verification_berry", "type": "food", "name": "核验莓", "quantity": 1},
    {"id": "action_cookie", "type": "food", "name": "行动饼", "quantity": 1},
    {"id": "evidence_star", "type": "food", "name": "证据星", "quantity": 1},
    {"id": "hint_token", "type": "hint", "name": "提示券", "quantity": 1},
    {"id": "badge_fragment", "type": "fragment", "name": "徽章碎片", "quantity": 1},
    {"id": "energy_supply", "type": "energy", "name": "精力补给", "quantity": 6},
    {"id": "collaboration_hint_card", "type": "inventory", "name": "协作提示卡", "quantity": 1},
    {"id": "easter_card", "type": "inventory", "name": "彩蛋卡", "quantity": 1},
]

ANONYMOUS_RANKING = [
    {"name": "玩家A17", "act": "方案救火", "xp": 240, "growth_points": 4, "badge_count": 1},
    {"name": "玩家B04", "act": "协作试炼", "xp": 430, "growth_points": 8, "badge_count": 2},
    {"name": "玩家C22", "act": "开局判断", "xp": 130, "growth_points": 1, "badge_count": 0},
    {"name": "玩家D09", "act": "协作试炼", "xp": 520, "growth_points": 9, "badge_count": 3},
    {"name": "玩家E31", "act": "方案救火", "xp": 330, "growth_points": 6, "badge_count": 1},
    {"name": "玩家F12", "act": "协作试炼", "xp": 610, "growth_points": 10, "badge_count": 4},
    {"name": "玩家G28", "act": "方案救火", "xp": 290, "growth_points": 5, "badge_count": 1},
    {"name": "玩家H03", "act": "协作试炼", "xp": 470, "growth_points": 7, "badge_count": 2},
]

STAGE_FOUR_EVIDENCE_CARDS = [
    {"id": "player_interviews", "name": "5名真实玩家访谈", "slot": "user", "quality": "high"},
    {"id": "social_comment", "name": "单条社交媒体评论", "slot": "user", "quality": "medium"},
    {"id": "activity_data", "name": "近3期同类活动数据", "slot": "data", "quality": "high"},
    {"id": "metric_definition", "name": "已核对的数据口径", "slot": "data", "quality": "high"},
    {"id": "ai_summary", "name": "AI自动生成的数据总结", "slot": "data", "quality": "low"},
    {"id": "alignment_minutes", "name": "跨团队需求拉齐纪要", "slot": "execution", "quality": "high"},
    {"id": "scope_plan", "name": "已确认的最小可行方案范围清单", "slot": "execution", "quality": "high"},
    {"id": "prototype_image", "name": "方案原型截图", "slot": "execution", "quality": "medium"},
    {"id": "risk_monitor", "name": "风险监控方案", "slot": "risk", "quality": "high"},
    {"id": "rollback_plan", "name": "备用回滚方案", "slot": "risk", "quality": "high"},
    {"id": "personal_feeling", "name": "我认为这个方案可行", "slot": None, "quality": "low"},
    {"id": "ai_recommendation", "name": "AI认为该方案成功率较高", "slot": None, "quality": "low"},
]

STAGE_FOUR_SLOT_NAMES = {
    "user": "用户证据",
    "data": "数据证据",
    "execution": "执行证据",
    "risk": "风险控制证据",
}

BOSS_QUESTIONS = [
    {
        "id": "data_source",
        "type": "数据来源质疑",
        "question": "你如何证明活动能够提升参与度？",
        "focus": "导师当前最关注结论是否有可追溯证据。",
        "stakeholder_hint": "产品更关心指标是否能支撑增长判断。",
        "answers": {
            "A": {"text": "AI分析显示活动大概率有效，可以直接上线。", "evidence": 20, "boundary": 10, "action": 25},
            "B": {"text": "访谈和历史数据支持该方向，但样本有限，因此先灰度验证并观察参与率。", "evidence": 95, "boundary": 90, "action": 90},
            "C": {"text": "当前无法完全证明，我们可以取消活动。", "evidence": 40, "boundary": 85, "action": 20},
        },
    },
    {
        "id": "causality",
        "type": "因果关系质疑",
        "question": "你如何避免把相关性误判为活动效果？",
        "focus": "导师当前最关注你是否承认因果边界。",
        "stakeholder_hint": "数据同学会关注对照、时间窗口和指标口径。",
        "answers": {
            "A": {"text": "先说明目前只能证明相关性，再设计灰度对照和上线后复盘。", "evidence": 88, "boundary": 95, "action": 88},
            "B": {"text": "只要数据上涨，就可以说明活动有效。", "evidence": 30, "boundary": 20, "action": 30},
            "C": {"text": "把因果问题交给AI重新分析即可。", "evidence": 45, "boundary": 35, "action": 40},
        },
    },
    {
        "id": "user_value",
        "type": "用户价值质疑",
        "question": "用户为什么愿意参与这次活动？",
        "focus": "导师当前最关注用户价值是否来自真实反馈。",
        "stakeholder_hint": "运营更关心首轮理解成本和参与动机。",
        "answers": {
            "A": {"text": "奖励足够多，用户自然会来。", "evidence": 35, "boundary": 30, "action": 35},
            "B": {"text": "访谈显示用户在意低门槛奖励和明确反馈，因此首轮规则简化并安排引导。", "evidence": 90, "boundary": 82, "action": 92},
            "C": {"text": "先做复杂玩法，后续再解释。", "evidence": 25, "boundary": 20, "action": 25},
        },
    },
    {
        "id": "dev_resource",
        "type": "开发资源质疑",
        "question": "如果开发资源不足，你优先保什么？",
        "focus": "导师当前最关注范围取舍是否可执行。",
        "stakeholder_hint": "程序更关心回滚成本，而不是活动创意本身。",
        "answers": {
            "A": {"text": "保留核心机制、埋点和回滚，延后非核心表现。", "evidence": 86, "boundary": 85, "action": 92},
            "B": {"text": "所有功能都要上线，否则方案不完整。", "evidence": 20, "boundary": 15, "action": 30},
            "C": {"text": "删掉监控，先把视觉做完整。", "evidence": 35, "boundary": 35, "action": 35},
        },
    },
    {
        "id": "rollback",
        "type": "风险与回滚质疑",
        "question": "活动效果异常时如何止损？",
        "focus": "导师当前最关注风险触发条件和回滚方案。",
        "stakeholder_hint": "运营和程序都会关注异常阈值、回滚责任人和用户公告。",
        "answers": {
            "A": {"text": "设置参与率、投诉率和奖励异常阈值，触发后按回滚方案下线入口。", "evidence": 92, "boundary": 88, "action": 94},
            "B": {"text": "出现问题再临时讨论。", "evidence": 20, "boundary": 20, "action": 25},
            "C": {"text": "只要活动目标正确，风险可以接受。", "evidence": 25, "boundary": 15, "action": 20},
        },
    },
    {
        "id": "ai_human",
        "type": "AI与人工分工质疑",
        "question": "这份方案里AI和人分别负责什么？",
        "focus": "导师当前最关注你是否承担判断责任。",
        "stakeholder_hint": "HR更关心AI是否辅助过程，而不是替代责任人。",
        "answers": {
            "A": {"text": "AI负责摘要和备选方案，人负责证据核验、范围判断和最终责任。", "evidence": 86, "boundary": 92, "action": 88},
            "B": {"text": "AI已经给出方案，我负责提交。", "evidence": 35, "boundary": 20, "action": 30},
            "C": {"text": "人不应该使用AI。", "evidence": 30, "boundary": 70, "action": 25},
        },
    },
    {
        "id": "team_consensus",
        "type": "团队共识质疑",
        "question": "你如何证明团队已经对范围达成共识？",
        "focus": "导师当前最关注协作证据是否可复盘。",
        "stakeholder_hint": "美术、程序和运营都希望看到明确的延后清单。",
        "answers": {
            "A": {"text": "我有需求拉齐纪要、最小可行方案范围清单和延后项说明。", "evidence": 90, "boundary": 82, "action": 86},
            "B": {"text": "大家口头上应该都同意了。", "evidence": 25, "boundary": 30, "action": 25},
            "C": {"text": "我会请导师帮我说服大家。", "evidence": 40, "boundary": 50, "action": 45},
        },
    },
    {
        "id": "post_launch",
        "type": "上线后验证质疑",
        "question": "上线后你如何判断方案是否成功？",
        "focus": "导师当前最关注指标、周期和下一步行动。",
        "stakeholder_hint": "产品和运营更关心上线后如何形成可复用经验。",
        "answers": {
            "A": {"text": "看活动是否热闹。", "evidence": 30, "boundary": 25, "action": 25},
            "B": {"text": "观察参与率、完成率、投诉率和留存变化，并在灰度后复盘是否扩大范围。", "evidence": 88, "boundary": 86, "action": 92},
            "C": {"text": "只看最终收入。", "evidence": 45, "boundary": 35, "action": 45},
        },
    },
]

STAGE_FOUR_BONUS_EVENTS = [
    {"id": "elevator_pitch", "title": "30秒电梯陈述", "options": {"A": {"text": "用一句目标、一条证据和一个风险预案说明方案。", "success": True}, "B": {"text": "复述所有细节。", "success": False}}},
    {"id": "human_ai_split", "title": "一句话解释人机分工", "options": {"A": {"text": "AI提效，人负责判断、核验和最终责任。", "success": True}, "B": {"text": "AI决定方案，人执行即可。", "success": False}}},
    {"id": "metric_pick", "title": "选择最重要的上线指标", "options": {"A": {"text": "参与率和完成率。", "success": True}, "B": {"text": "PPT页数。", "success": False}}},
    {"id": "hidden_risk", "title": "识别一条隐藏风险", "options": {"A": {"text": "奖励规则复杂导致理解成本上升。", "success": True}, "B": {"text": "颜色不够鲜艳。", "success": False}}},
    {"id": "stop_loss", "title": "为失败方案设计止损条件", "options": {"A": {"text": "投诉率或奖励异常超过阈值即回滚。", "success": True}, "B": {"text": "上线后不再调整。", "success": False}}},
]

MINIGAME_FOOD_MAP = {
    "ai_review": "verification_berry",
    "priority": "action_cookie",
    "evidence": "evidence_star",
}

REMEDIATION_QUESTIONS = {
    "ai_review": {
        "question": "30秒复盘：下次审查AI方案时，最应该同时检查哪四类风险？",
        "options": {
            "A": "数据来源、因果关系、信息安全和执行约束",
            "B": "标题是否好看、PPT动画、口号和颜色",
            "C": "只检查AI有没有给出完整段落",
        },
        "correct": "A",
    },
    "priority": {
        "question": "30秒复盘：预评审前，哪类任务最值得优先处理？",
        "options": {
            "A": "会改变业务结论或风险判断的真实业务任务，并尽快校准",
            "B": "先把PPT动画做得更顺滑",
            "C": "继续学习更多通用课程，暂不接触方案问题",
        },
        "correct": "A",
    },
    "evidence": {
        "question": "30秒复盘：一份可靠证据包最应该补齐什么？",
        "options": {
            "A": "真实反馈、历史数据、口径说明和反例",
            "B": "个人感觉和AI生成的漂亮总结",
            "C": "只保留支持自己观点的材料",
        },
        "correct": "A",
    },
}

SCENES: dict[str, dict[str, Any]] = {
    "prologue": {
        "week": 0,
        "chapter": "序章·入职任务",
        "title": "90天成长副本已开启",
        "story": "新人“小鹅”加入游戏业务团队，90天后需要独立完成一份活动策划方案。",
        "role": "游戏策划新人·小鹅",
        "goal": "90天后独立完成一份可进入评审的游戏活动策划方案。",
        "next_scene": "scene_week1_business_map",
        "rules": [
            "每个选择只结算一次，能力、精力、信任和风险会实时变化。",
            "选择后先查看反馈，再点击“进入下一幕”。",
            "AI可以辅助分析，人负责判断、验证和最终决策。",
            "本阶段数据只保存在互动闯关状态中，不影响正式成长计划。",
        ],
    },
    "scene_week1_business_map": {
        "week": 1,
        "chapter": "第一章·业务地图",
        "title": "一周读懂活动策划流程",
        "story": "小鹅收到大量业务资料，但只有一周时间理解活动策划流程。你会如何安排第一步？",
        "options": {
            "A": {
                "title": "独立阅读全部材料后整理问题",
                "description": "先建立完整认知，再带着问题与导师和团队沟通。",
                "tradeoffs": ["精力消耗较高", "提升业务理解", "独立推进更强"],
                "effects": {"energy": -15, "business": 7, "delivery": 3, "mentor_trust": 1, "risk": -2, "xp": 40},
                "feedback": "你建立了较完整的业务框架，但一次性阅读全部材料消耗了较多精力。",
                "mentor_signal": "导师看到你具备主动拆解问题的意识，可在问题清单形成后做一次集中校准。",
                "hr_signal": "当前无明显风险；需关注高投入学习方式是否能长期持续。",
                "next_scene": "scene_week2_ai_check",
            },
            "B": {
                "title": "请导师用30分钟讲清核心流程",
                "description": "先获得关键路径，再用剩余时间补充材料和问题。",
                "tradeoffs": ["精力消耗较低", "导师参与较多", "风险较低"],
                "effects": {"energy": -7, "business": 5, "mentor_trust": 4, "delivery": -1, "risk": -4, "xp": 35},
                "feedback": "你快速抓住了核心流程，也建立了导师连接，但独立梳理能力需要在后续任务中补足。",
                "mentor_signal": "导师信任提升，下一步应让新人复述流程并独立产出业务地图。",
                "hr_signal": "带教资源使用合理，暂不需要额外组织介入。",
                "next_scene": "scene_week2_ai_check",
            },
            "C": {
                "title": "直接使用AI总结全部内部资料",
                "description": "追求快速形成摘要，但没有先确认资料边界和核验方式。",
                "tradeoffs": ["更强调交付速度", "提升AI协作", "风险可能上升"],
                "effects": {"energy": -3, "ai_collaboration": 4, "business": 2, "verification": -3, "risk": 10, "xp": 30},
                "feedback": "你快速获得了信息框架，但直接处理内部资料带来安全和事实核验风险。",
                "mentor_signal": "导师需要尽快确认资料是否允许输入AI，并要求新人回到原始材料核验关键结论。",
                "hr_signal": "出现AI安全与验证风险信号，建议强化敏感信息边界提醒。",
                "next_scene": "scene_week2_ai_check",
            },
        },
    },
    "scene_week2_ai_check": {
        "week": 2,
        "chapter": "第二章·AI核验",
        "title": "一条没有来源的玩家数据",
        "story": "AI生成的活动建议中出现一条没有来源的玩家数据。评审就在眼前，你会如何处理？",
        "options": {
            "A": {
                "title": "直接使用，先保证交付速度",
                "description": "保留数据并快速提交，把速度放在证据之前。",
                "tradeoffs": ["更强调交付速度", "精力消耗较低", "风险可能上升"],
                "effects": {"energy": -3, "delivery": 3, "verification": -5, "mentor_trust": -3, "risk": 12, "xp": 25},
                "feedback": "交付速度提高了，但未经验证的数据会放大业务判断和评审风险。",
                "mentor_signal": "导师信任下降，需要立即追问数据来源并重新确认交付质量。",
                "hr_signal": "出现AI结果验证薄弱信号；若批次内重复发生，应增加验证训练。",
                "next_scene": "stage_one_complete",
            },
            "B": {
                "title": "暂停提交，核查数据来源和口径",
                "description": "回到原始来源，确认样本、时间范围和指标定义。",
                "tradeoffs": ["精力消耗较高", "提升结果验证", "风险较低"],
                "effects": {"energy": -12, "verification": 9, "business": 4, "mentor_trust": 5, "risk": -8, "xp": 55},
                "feedback": "你牺牲了部分速度，但保护了方案可信度，并建立了正确的AI验证习惯。",
                "mentor_signal": "导师信任明显提升，可以逐步扩大你独立处理分析任务的范围。",
                "hr_signal": "验证能力形成正向证据，无需介入，可沉淀为团队示范案例。",
                "next_scene": "stage_one_complete",
            },
            "C": {
                "title": "删除该数据，只保留无法验证的定性判断",
                "description": "移除高风险数据，但没有继续寻找更可靠的业务证据。",
                "tradeoffs": ["风险略微下降", "证据仍需补强", "独立交付放慢"],
                "effects": {"energy": -6, "verification": 3, "delivery": -1, "risk": -3, "xp": 35},
                "feedback": "你避免了直接使用错误数据，但方案的证据强度仍然不足。",
                "mentor_signal": "导师建议补充最小可验证证据，而不是只删除问题信息。",
                "hr_signal": "风险暂时下降；新人仍需要业务证据搜集方法支持。",
                "next_scene": "stage_one_complete",
            },
        },
    },
    "stage_one_complete": {
        "week": 2,
        "chapter": "阶段结算",
        "title": "开局判断完成",
        "story": "你已经完成业务地图和AI核验两个关键场景。下一幕将进入方案救火。",
    },
    "stage_two_briefing": {
        "week": 3,
        "chapter": "第二幕·方案救火",
        "title": "60分钟后的方案预评审",
        "story": "项目负责人将在60分钟后进行活动方案预评审。AI已经生成了一版初稿，但其中可能存在无来源数据、逻辑跳跃、安全风险、资源冲突和证据不足。你需要在有限精力下完成三项任务：审查AI方案、安排补救任务、组装可靠证据包。",
        "next_scene": "mini_ai_review",
    },
    "mini_ai_review": {
        "week": 3,
        "chapter": "第二幕·1/3方案审查",
        "title": "AI方案审查",
        "story": "AI生成了一段活动建议，请判断其中哪些内容存在问题。",
        "type": "mini_game_ai_review",
        "next_scene": "mini_priority",
    },
    "mini_priority": {
        "week": 3,
        "chapter": "第二幕·2/3任务决策",
        "title": "任务优先级决策",
        "story": "AI初稿的问题已经找到，但距离预评审只剩有限时间。你拥有10点任务预算，需要选择1—3项优先处理。",
        "type": "mini_game_priority",
        "next_scene": "mini_evidence",
    },
    "mini_evidence": {
        "week": 3,
        "chapter": "第二幕·3/3证据组装",
        "title": "证据包组装",
        "story": "方案已经基本修复。为了支持“新活动能够提升玩家参与度”这一结论，你需要选择3—4项最有价值的证据。",
        "type": "mini_game_evidence",
        "next_scene": "stage_two_complete",
    },
    "stage_two_complete": {
        "week": 4,
        "chapter": "阶段结算",
        "title": "方案救火完成",
        "story": "你已经完成AI方案审查、任务优先级决策和证据包组装。下一幕将进入协作试炼。",
    },
    "stage_three_briefing": {
        "week": 5,
        "chapter": "第三幕·协作试炼",
        "title": "跨团队评审前夜",
        "story": "方案已经通过预评审，但程序、美术、运营和产品分别提出新的约束。你需要在有限资源内重新拉齐目标、缩小范围并处理突发事件。",
        "next_scene": "stage_three_alignment",
    },
    "stage_three_alignment": {
        "week": 6,
        "chapter": "第三幕·1/3需求拉齐",
        "title": "需求拉齐会",
        "story": "四个角色轮流提出约束。你需要在三轮回应中识别真实约束，重新定义共同目标。",
        "type": "mini_game_alignment",
        "next_scene": "stage_three_scope",
    },
    "stage_three_scope": {
        "week": 7,
        "chapter": "第三幕·2/3范围取舍",
        "title": "范围取舍板",
        "story": "你需要把候选任务放入必做、可选或延后，并在开发、美术和时间预算内形成可上线最小方案。",
        "type": "mini_game_scope",
        "next_scene": "stage_three_random_event",
    },
    "stage_three_random_event": {
        "week": 8,
        "chapter": "第三幕·3/3临场应变",
        "title": "随机额外任务",
        "story": "协作推进中出现突发情况。额外任务失败不会扣分，但成功可获得随机奖励。",
        "type": "mini_game_random_event",
        "next_scene": "stage_three_complete",
    },
    "stage_three_complete": {
        "week": 8,
        "chapter": "阶段结算",
        "title": "协作试炼完成",
        "story": "你已经完成跨团队拉齐、范围取舍和临场应变，活动方案进入团队可执行版本判断。",
    },
    "stage_four_briefing": {
        "week": 10,
        "chapter": "第四幕·成果验收",
        "title": "最终评审将在30分钟后开始",
        "story": "前三幕中，你已经完成方案修复、团队拉齐和范围取舍。现在需要把分散的成果整理成可以被追问、被核验、被执行的最终交付。",
        "next_scene": "stage_four_loadout",
    },
    "stage_four_loadout": {
        "week": 10,
        "chapter": "第四幕·终局装备",
        "title": "终局装备整理",
        "story": "把前三幕积累的提示券、徽章碎片和协作道具整理成终局评审可用资源。",
        "next_scene": "stage_four_evidence",
    },
    "stage_four_evidence": {
        "week": 11,
        "chapter": "第四幕·证据装配",
        "title": "成果证据装配台",
        "story": "把用户、数据、执行和风险控制证据装配成最终成果包。",
        "type": "stage_four_evidence",
        "next_scene": "stage_four_boss",
    },
    "stage_four_boss": {
        "week": 12,
        "chapter": "第四幕·导师问答",
        "title": "导师问答终局追问",
        "story": "导师会连续追问证据、边界和下一步行动。请用可信证据守住成果。",
        "type": "stage_four_boss",
        "next_scene": "stage_four_bonus",
    },
    "stage_four_remediation": {
        "week": 12,
        "chapter": "第四幕·快速补答",
        "title": "快速补答",
        "story": "导师信任偏低时，需要补充关键证据、边界或上线验证指标。",
        "next_scene": "stage_four_bonus",
    },
    "stage_four_bonus": {
        "week": 12,
        "chapter": "第四幕·随机加试",
        "title": "终局随机加试",
        "story": "完成最后一个短挑战。失败不扣分，成功可获得奖励分和终局奖励。",
        "type": "stage_four_bonus",
        "next_scene": "stage_four_complete",
    },
    "stage_four_complete": {
        "week": 12,
        "chapter": "终局结算",
        "title": "90天成长副本完成",
        "story": "你已经完成最终成果验收，系统生成游戏化成长报告。",
    },
    "post_game_hub": {
        "week": 12,
        "chapter": "成长基地",
        "title": "通关后的成长基地",
        "story": "查看结局图鉴、徽章墙、芽芽房间、挑战看板和匿名成长榜。",
    },
}
