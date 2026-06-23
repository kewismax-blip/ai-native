from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import os
import random
import urllib.request
from datetime import datetime
from html import escape
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from ai_runtime import ai_available, ai_mode_label, optional_ai_json, optional_ai_text
from game_engine import initial_game_state, normalize_game_state
from game_ui import render_game_page


logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="职场开局｜AI新人90天成长副本",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


PRIMARY_ROLES = {
    "技术研发": ["客户端研发", "服务端研发", "前端研发", "测试开发", "算法工程师", "技术美术"],
    "产品": ["产品经理", "平台产品", "商业化产品", "用户产品", "AI产品经理"],
    "游戏策划": ["系统策划", "数值策划", "活动策划", "关卡策划", "文案策划"],
    "设计": ["视觉设计", "交互设计", "游戏美术", "动效设计", "用户体验设计"],
    "内容": ["内容策划", "编辑", "视频内容", "社区内容", "IP内容运营"],
    "运营": ["游戏运营", "用户运营", "活动运营", "社区运营", "产品运营"],
    "市场与品牌": ["品牌营销", "市场策划", "媒介投放", "公关传播", "增长营销"],
    "销售与商务": ["商务拓展", "渠道合作", "客户成功", "解决方案销售", "商业分析"],
    "数据分析": ["业务分析", "用户研究", "数据产品", "经营分析", "数据科学"],
    "HR与职能": ["招聘", "学习发展", "HRBP", "组织发展", "财务与法务"],
}

EXPERIENCE_LEVELS = ["应届生", "实习转正", "1年以内", "1—3年", "3—5年", "5年以上"]
BUSINESS_STAGES = ["探索期", "快速成长期", "稳定运营期", "转型期"]
WORK_MODES = ["独立执行", "项目协作", "跨团队协作", "客户或用户沟通", "数据分析", "内容生产"]
WORK_PACES = ["平稳", "阶段性忙碌", "持续高强度"]
AI_OPTIONS = ["从未尝试", "需要指导", "可以独立完成", "可以指导他人"]
AI_OPTION_SCORES = {option: index for index, option in enumerate(AI_OPTIONS)}
AI_QUESTIONS = {
    "ai_frequency": "是否经常使用生成式AI",
    "ai_prompt": "是否能写结构化提示词",
    "ai_context": "是否能向AI提供充分的业务背景",
    "ai_verify": "是否能识别AI事实错误",
    "ai_docs": "是否会使用AI处理文档",
    "ai_data": "是否会使用AI处理数据",
    "ai_workflow": "是否建立过自动化工作流",
    "ai_security": "是否理解敏感信息和数据安全要求",
    "ai_business": "是否能将AI应用到真实业务交付",
}
LEARNING_STYLES = ["真实项目", "导师示范", "案例拆解", "短课程", "同伴协作", "自主探索"]
PROBLEM_HANDLING = ["先独立搜索和尝试", "优先询问导师", "与同伴讨论", "拆解问题后再求助", "容易搁置等待"]
ABILITY_OPTIONS = [
    "业务理解", "用户分析", "数据分析", "跨团队协作", "结构化表达", "项目推进",
    "独立决策", "AI协作", "结果验证", "自动化工作流", "安全合规", "复盘沉淀",
]
INTENSITY_OPTIONS = ["轻量：7项核心任务", "标准：10项任务", "挑战：10项核心任务+2项挑战任务"]
TASK_STATUSES = ["未开始", "进行中", "待补充", "待导师验收", "已完成", "延期"]
DOPAMINE_COLORS = ["#5B8FF9", "#63D7B0", "#9B8AFB", "#FFB45B", "#FF7EB6", "#FFD66B"]
STAGE_COLORS = ["#69C0FF", "#63D7B0", "#9B8AFB", "#FFB45B", "#FF7EB6"]
STAGE_SOFT_COLORS = ["#EAF3FF", "#EAFBF5", "#F1EDFF", "#FFF2E2", "#FFF0F6"]

PAGES = ["首页", "智能画像", "诊断报告", "成长地图", "每周复盘", "互动闯关", "90天自动演示", "导师面板", "HR驾驶舱"]
NAV_GROUPS = {
    "growth": {
        "label": "成长旅程",
        "pages": ["智能画像", "诊断报告", "成长地图", "每周复盘"],
    },
    "play": {
        "label": "互动体验",
        "pages": ["互动闯关", "90天自动演示"],
    },
    "manage": {
        "label": "带教与洞察",
        "pages": ["导师面板", "HR驾驶舱"],
    },
}
PAGE_TO_GROUP = {
    page: group_id
    for group_id, group in NAV_GROUPS.items()
    for page in group["pages"]
}

ROLE_BLUEPRINTS = {
    "技术研发": {
        "object": "可运行的业务模块", "research": "技术方案与代码基线", "user": "上下游开发者和用户",
        "data": "日志、性能与缺陷数据", "partner": "产品、策划、测试和其他研发", "deliverable": "技术方案与可运行模块",
    },
    "产品": {
        "object": "产品功能方案", "research": "竞品功能与用户反馈", "user": "核心用户",
        "data": "功能使用与转化数据", "partner": "设计、研发和运营", "deliverable": "产品需求文档与验证方案",
    },
    "游戏策划": {
        "object": "游戏活动或玩法方案", "research": "同类游戏与活动案例", "user": "目标玩家",
        "data": "参与、留存与付费数据", "partner": "程序、美术、运营和测试", "deliverable": "可评审的游戏策划方案",
    },
    "设计": {
        "object": "视觉或体验设计方案", "research": "设计趋势与同类体验", "user": "目标用户和项目团队",
        "data": "可用性反馈与素材表现", "partner": "产品、策划、研发和其他设计", "deliverable": "设计提案、原型与规范",
    },
    "内容": {
        "object": "内容产品或传播方案", "research": "内容案例与用户偏好", "user": "内容消费者和社区用户",
        "data": "阅读、互动与传播数据", "partner": "运营、市场和设计", "deliverable": "内容方案与成品样稿",
    },
    "运营": {
        "object": "运营活动与用户策略", "research": "运营案例与用户反馈", "user": "目标用户和社群",
        "data": "活跃、转化与留存数据", "partner": "产品、内容、市场和客服", "deliverable": "运营方案、执行清单与复盘",
    },
    "市场与品牌": {
        "object": "市场传播或品牌项目", "research": "行业传播案例与受众洞察", "user": "目标受众",
        "data": "触达、互动与转化数据", "partner": "产品、内容、设计和渠道", "deliverable": "传播策略与整合营销方案",
    },
    "销售与商务": {
        "object": "客户方案或合作项目", "research": "行业、客户与合作案例", "user": "客户和合作伙伴",
        "data": "线索、转化与客户反馈", "partner": "产品、交付、法务和运营", "deliverable": "客户方案与合作推进计划",
    },
    "数据分析": {
        "object": "业务分析与决策建议", "research": "业务链路与指标口径", "user": "业务决策者",
        "data": "业务指标、用户行为与实验数据", "partner": "产品、运营和研发", "deliverable": "分析报告与决策建议",
    },
    "HR与职能": {
        "object": "组织或职能解决方案", "research": "政策、流程与员工需求", "user": "员工、管理者和业务团队",
        "data": "组织、流程与服务数据", "partner": "业务负责人、员工和职能伙伴", "deliverable": "可执行的职能方案与机制",
    },
}

STAGE_DEFINITIONS = [
    {"name": "新手营地", "range": "0—14天", "goal": "建立组织和AI协作基础"},
    {"name": "业务探索区", "range": "15—30天", "goal": "理解用户、业务和数据"},
    {"name": "协作试炼场", "range": "31—50天", "goal": "完成跨团队小型任务"},
    {"name": "真实项目区", "range": "51—80天", "goal": "承担真实业务交付"},
    {"name": "成果答辩厅", "range": "81—90天", "goal": "展示成果并沉淀方法"},
]

DEMO_EVENTS = [
    {"week": 0, "title": "新人完成画像", "detail": "小鹅完成岗位、工作场景、AI能力与学习偏好诊断。", "xp": 0, "metrics": {"业务理解": 25, "AI协作": 30, "跨团队协作": 20, "独立交付": 15}, "risk": "低", "adjustment": "建立个性化基线，识别AI结果验证和独立交付为优先差距。", "mentor": False},
    {"week": 1, "title": "生成90天成长路径", "detail": "系统将目标拆成五个区域、十项任务和五个导师检查点。", "xp": 40, "metrics": {"业务理解": 30, "AI协作": 32, "跨团队协作": 22, "独立交付": 18}, "risk": "低", "adjustment": "将案例拆解、真实项目和导师示范组合为主要培养方式。", "mentor": False},
    {"week": 2, "title": "完成AI基础任务", "detail": "新人完成结构化提示、事实核验和安全边界练习，并提交两项有效基础证据。", "xp": 140, "metrics": {"业务理解": 34, "AI协作": 46, "跨团队协作": 24, "独立交付": 22}, "risk": "低", "adjustment": "AI基础通过，下一步进入竞品与用户证据分析。", "mentor": False, "task_updates": {1: "已完成"}, "evidence_action": "foundation"},
    {"week": 3, "title": "临时项目导致竞品任务延期", "detail": "临时业务安排占用成长时间，竞品与用户证据任务未按期完成。", "xp": 140, "metrics": {"业务理解": 34, "AI协作": 47, "跨团队协作": 27, "独立交付": 21}, "risk": "中", "adjustment": "记录延期原因，不把业务忙碌简单判断为学习意愿不足。", "mentor": False, "task_updates": {2: "延期"}},
    {"week": 3, "title": "系统识别中风险", "detail": "延期、低信心和真实业务经验不足同时出现，触发关注信号。", "xp": 140, "metrics": {"业务理解": 35, "AI协作": 47, "跨团队协作": 27, "独立交付": 20}, "risk": "中", "adjustment": "风险来自任务设计与时间冲突，需要调计划而不是追加压力。", "mentor": False},
    {"week": 4, "title": "自动调整下一周计划", "detail": "减少理论学习，将竞品范围从3个收敛为1个深度案例，并增加低难度真实业务任务。", "xp": 170, "metrics": {"业务理解": 40, "AI协作": 50, "跨团队协作": 30, "独立交付": 27}, "risk": "中", "adjustment": "用更小的真实交付建立成功体验，同时保留关键能力训练。", "mentor": False},
    {"week": 4, "title": "触发导师30分钟一对一", "detail": "导师示范一次从业务问题、AI辅助到人工判断的完整过程。", "xp": 200, "metrics": {"业务理解": 44, "AI协作": 54, "跨团队协作": 34, "独立交付": 31}, "risk": "中", "adjustment": "导师聚焦示范与校准，不替新人直接完成任务。", "mentor": True},
    {"week": 6, "title": "完成第一次跨团队协作", "detail": "新人和运营、程序共同完成一个低风险活动方案走查，并提交协作证据。", "xp": 420, "metrics": {"业务理解": 55, "AI协作": 61, "跨团队协作": 56, "独立交付": 42}, "risk": "低", "adjustment": "跨团队协作达到阶段标准，解锁真实项目区。", "mentor": False, "task_updates": {2: "已完成", 4: "已完成", 5: "已完成"}, "evidence_action": "cross_team"},
    {"week": 8, "title": "提交活动方案成长证据", "detail": "新人提交活动方案初稿，系统开始检查成果、业务证据、人机分工与AI验证过程。", "xp": 520, "metrics": {"业务理解": 57, "AI协作": 62, "跨团队协作": 58, "独立交付": 44}, "risk": "中", "adjustment": "方案结构完整，但用户证据和AI核验记录不足，任务进入待补充。", "mentor": True, "evidence_action": "initial"},
    {"week": 8, "title": "系统生成补证要求", "detail": "四维评价发现证据质量与AI验证能力偏低，要求补充用户反馈、数据口径和反例。", "xp": 540, "metrics": {"业务理解": 58, "AI协作": 62, "跨团队协作": 58, "独立交付": 44}, "risk": "中", "adjustment": "不否定成果本身，聚焦补齐可追溯证据和人工判断。", "mentor": True},
    {"week": 8, "title": "导师退回并提出追问", "detail": "导师追问哪些结论来自真实玩家、哪些仍是AI推测，并确认最小补证范围。", "xp": 560, "metrics": {"业务理解": 59, "AI协作": 63, "跨团队协作": 60, "独立交付": 45}, "risk": "中", "adjustment": "导师不代写方案，只确认问题、证据标准与任务范围。", "mentor": True, "evidence_action": "mentor_return"},
    {"week": 9, "title": "新人补充用户反馈和数据口径", "detail": "新人补充5名玩家访谈、近3期活动数据口径和两条反例证据，重新提交成果。", "xp": 700, "metrics": {"业务理解": 68, "AI协作": 72, "跨团队协作": 65, "独立交付": 65}, "risk": "中", "adjustment": "补证后四维评分提升，任务进入待导师验收。", "mentor": True, "evidence_action": "supplement"},
    {"week": 9, "title": "导师确认补充后通过", "detail": "导师确认业务证据、AI验证和个人判断达到要求，任务状态更新为已完成。", "xp": 820, "metrics": {"业务理解": 72, "AI协作": 76, "跨团队协作": 68, "独立交付": 72}, "risk": "低", "adjustment": "风险下降，允许新人扩大独立工作范围并进入跨职能评审。", "mentor": False, "evidence_action": "mentor_pass"},
    {"week": 11, "title": "完成跨职能评审", "detail": "新人主持评审，回应程序、美术和运营的质疑并完成第二版。", "xp": 1080, "metrics": {"业务理解": 80, "AI协作": 78, "跨团队协作": 82, "独立交付": 79}, "risk": "低", "adjustment": "成果已具备可执行性，进入答辩与方法沉淀。", "mentor": False, "task_updates": {8: "已完成"}},
    {"week": 12, "title": "完成成果答辩和AI协作手册", "detail": "新人完成90天成果展示，沉淀提示、验证、安全边界和复盘方法。", "xp": 1460, "metrics": {"业务理解": 88, "AI协作": 86, "跨团队协作": 86, "独立交付": 90}, "risk": "低", "adjustment": "90天副本完成，建议下一阶段承担更高不确定性的真实项目。", "mentor": False, "complete_all": True},
]

DEMO_PROFILE = {
    "nickname": "小鹅", "primary_role": "游戏策划", "secondary_role": "活动策划", "experience": "应届生",
    "business_stage": "快速成长期", "work_modes": ["项目协作", "跨团队协作", "数据分析"],
    "expected_deliverable": "能够独立完成一份游戏活动策划方案", "real_project": "已进入，承担辅助任务",
    "work_pace": "阶段性忙碌", "weekly_growth_hours": 6, "mentor_hours": 1.0,
    "learning_styles": ["真实项目", "导师示范", "案例拆解"], "problem_handling": "拆解问题后再求助",
    "confidence": 2, "worry": "不了解如何将AI应用于真实策划工作，也担心独立判断不足。",
    "mentor_help": "希望导师示范一次真实活动方案的分析过程，并在关键节点校准。",
    "abilities": ["用户分析", "数据分析", "跨团队协作", "AI协作", "独立决策"],
    "core_goal": "90天内独立完成一份可进入评审的游戏活动策划方案",
    "task_intensity": INTENSITY_OPTIONS[1], "auto_adjust": True, "enter_auto_demo": True,
}

DEMO_AI_ANSWERS = {
    "ai_frequency": "可以独立完成", "ai_prompt": "需要指导", "ai_context": "需要指导",
    "ai_verify": "需要指导", "ai_docs": "可以独立完成", "ai_data": "需要指导",
    "ai_workflow": "从未尝试", "ai_security": "可以独立完成", "ai_business": "需要指导",
}


def inject_styles() -> None:
    width_mode = st.session_state.get("sidebar_width_mode", "normal")
    width_values = {"narrow": "224px", "normal": "252px", "wide": "288px"}
    sidebar_width = width_values.get(width_mode, "252px")
    collapse_left = f"calc({sidebar_width} - 48px)"
    st.markdown(
        """
        <style>
        :root{--page-bg:#FFF9F5;--surface:#FFFFFF;--surface-soft:#FFFDFB;--text:#273142;--muted:#667085;--line:#EEE8E2;--blue:#5B8FF9;--sky:#69C0FF;--mint:#63D7B0;--purple:#9B8AFB;--orange:#FFB45B;--pink:#FF7EB6;--yellow:#FFD66B;--red:#FF6B6B;--blue-soft:#EAF3FF;--mint-soft:#EAFBF5;--purple-soft:#F1EDFF;--orange-soft:#FFF2E2;--pink-soft:#FFF0F6;--yellow-soft:#FFF8D9}
        footer{visibility:hidden}header{background:transparent!important}.stApp{background:linear-gradient(180deg,#FFF9F5 0%,#FFFFFF 42%,#FFFDFB 100%);color:var(--text);font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",-apple-system,BlinkMacSystemFont,sans-serif}.block-container{max-width:1360px;padding-top:1.25rem;padding-bottom:4rem}h1,h2,h3,h4,p,label{color:var(--text)}h1{font-weight:760}h2,h3{font-weight:720}.breadcrumb{font-size:.78rem;color:#8A94A6;margin:.15rem 0 .8rem}.breadcrumb strong{color:#5B667A;font-weight:650}

        /* 侧边栏容器 */
        [data-testid="stSidebar"]{background:linear-gradient(180deg,#FFFDFB 0%,#F8FBFF 100%);border-right:1px solid var(--line);min-width:var(--sidebar-width)!important;max-width:var(--sidebar-width)!important;width:var(--sidebar-width)!important}
        [data-testid="stSidebar"] .sidebar-brand-mini,[data-testid="stSidebar"] .nav-section-title,[data-testid="stSidebar"] .nav-foot,[data-testid="stSidebar"] .nav-gap,[data-testid="stSidebar"] .sidebar-tools{font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",-apple-system,BlinkMacSystemFont,sans-serif;color:var(--text)}

        /* 品牌控制区 */
        [data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{padding-top:.45rem}
        [data-testid="stSidebar"] .sidebar-brand-mini{padding:.72rem .85rem;border-radius:16px;background:linear-gradient(135deg,#FFFFFF,#F4F8FF 62%,#FFF0F6);border:1px solid #E4EAF4;box-shadow:0 8px 18px rgba(53,65,92,.06);margin-bottom:.85rem}
        [data-testid="stSidebar"] .sidebar-brand-mini .brand-title{font-size:1rem;font-weight:800;color:#273142;line-height:1.2}
        [data-testid="stSidebar"] .sidebar-brand-mini .brand-sub{margin-top:.18rem;font-size:.72rem;color:#667085}
        [data-testid="stSidebar"] .nav-section-title{display:flex;align-items:center;gap:.45rem;margin:.85rem .15rem .35rem;padding:.28rem .2rem;font-size:.78rem;font-weight:780;color:#667085;letter-spacing:.02em}
        [data-testid="stSidebar"] .nav-section-main{font-size:.8rem;font-weight:800;color:#475467;line-height:1.2}
        [data-testid="stSidebar"] .nav-section-sub{margin:.08rem .3rem .28rem 1rem;font-size:.66rem;color:#98A2B3;font-weight:500;line-height:1.25;letter-spacing:0}
        [data-testid="stSidebar"] .nav-dot{width:7px;height:7px;border-radius:999px;background:#9B8AFB;box-shadow:0 0 0 4px rgba(155,138,251,.12)}
        [data-testid="stSidebar"] .nav-growth .nav-dot{background:#5B8FF9;box-shadow:0 0 0 4px rgba(91,143,249,.12)}
        [data-testid="stSidebar"] .nav-play .nav-dot{background:#9B8AFB;box-shadow:0 0 0 4px rgba(155,138,251,.14)}
        [data-testid="stSidebar"] .nav-manage .nav-dot{background:#63D7B0;box-shadow:0 0 0 4px rgba(99,215,176,.14)}
        [data-testid="stSidebar"] .nav-subtree{border-left:2px solid #E7EAF2;margin-left:.65rem;padding-left:.6rem;margin-bottom:.45rem}
        [data-testid="stSidebar"] .brand-card{position:relative;min-height:66px;padding:.78rem 3.35rem .7rem .95rem;border-radius:18px;background:linear-gradient(135deg,#FFFFFF 0%,#F4F8FF 58%,#FFF0F6 100%);border:1px solid #E4EAF4;box-shadow:0 10px 24px rgba(53,65,92,.07);margin:0 0 .72rem;overflow:hidden}
        [data-testid="stSidebar"] .brand-card:after{content:"";position:absolute;right:-18px;bottom:-22px;width:76px;height:76px;border-radius:50%;background:rgba(155,138,251,.12);pointer-events:none}
        [data-testid="stSidebar"] .brand-title{font-size:1.08rem;font-weight:780;line-height:1.2}
        [data-testid="stSidebar"] .brand-sub{font-size:.73rem;color:#667085;margin-top:.25rem}
        [data-testid="stSidebar"] .brand-card.compact{min-height:48px;padding:.7rem .85rem}.brand-card.compact .brand-sub{display:none}
        [data-testid="stSidebar"] .sidebar-tools{padding:.55rem .6rem .75rem;border-radius:16px;background:rgba(255,255,255,.72);border:1px solid #EEF1F6;margin:0 0 .72rem;font-size:.78rem}
        [data-testid="stSidebar"] .nav-foot{font-size:.76rem;color:#8A94A6;margin-top:1rem}
        [data-testid="stSidebar"] .nav-gap{height:.55rem}

        /* 展开/折叠控件 */
        [data-testid="stToolbarActions"],[data-testid="stAppDeployButton"],[data-testid="stMainMenu"],[data-testid="stMainMenuButton"]{visibility:hidden!important;pointer-events:none!important}
        [data-testid="stIconMaterial"]{font-family:"Material Symbols Rounded","Material Symbols Outlined","Material Icons"!important;font-weight:400!important;font-style:normal!important;letter-spacing:normal!important;text-transform:none!important;-webkit-font-feature-settings:"liga"!important;-webkit-font-smoothing:antialiased!important}
        [data-testid="stSidebarCollapseButton"]{position:fixed!important;top:20px!important;left:var(--sidebar-collapse-left)!important;display:flex!important;visibility:visible!important;opacity:1!important;z-index:999999!important}
        [data-testid="stSidebarCollapseButton"] button[data-testid="stBaseButton-headerNoPadding"]{position:relative!important;width:34px!important;height:34px!important;min-height:34px!important;padding:0!important;display:flex!important;align-items:center!important;justify-content:center!important;border:1px solid #DDE5F2!important;border-radius:12px!important;background:#FFFFFF!important;box-shadow:0 6px 14px rgba(53,65,92,.10)!important;color:#5F6B7A!important;transition:all .18s ease!important}
        [data-testid="stSidebarCollapseButton"] button[data-testid="stBaseButton-headerNoPadding"]:hover{background:var(--blue-soft)!important;transform:scale(1.05)}
        [data-testid="stSidebarCollapseButton"] button[data-testid="stBaseButton-headerNoPadding"] [data-testid="stIconMaterial"],[data-testid="stSidebarCollapseButton"] button[data-testid="stBaseButton-headerNoPadding"]>span{display:none!important}
        [data-testid="stSidebarCollapseButton"] button[data-testid="stBaseButton-headerNoPadding"]::after{content:"‹";font-size:22px;line-height:1;font-weight:650;color:#5F6B7A;pointer-events:none}
        [data-testid="stExpandSidebarButton"],[data-testid="collapsedControl"] button{position:fixed!important;top:14px!important;left:14px!important;width:46px!important;height:42px!important;min-height:42px!important;padding:0!important;display:flex!important;align-items:center!important;justify-content:center!important;border:1px solid #DDE5F2!important;border-radius:14px!important;background:#FFFFFF!important;box-shadow:0 8px 20px rgba(53,65,92,.10)!important;color:#273142!important;visibility:visible!important;opacity:1!important;z-index:999999!important;transition:all .18s ease!important}
        [data-testid="stExpandSidebarButton"]:hover,[data-testid="collapsedControl"] button:hover{background:var(--blue-soft)!important;transform:scale(1.05)}
        [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"],[data-testid="collapsedControl"] [data-testid="stIconMaterial"],[data-testid="stExpandSidebarButton"]>span,[data-testid="collapsedControl"] button>span{display:none!important}
        [data-testid="stExpandSidebarButton"]::before,[data-testid="collapsedControl"] button::before{content:"职";font-size:.96rem;font-weight:820;color:#5B8FF9;pointer-events:none}

        /* 页面导航 */
        [data-testid="stSidebar"] div.stButton>button{justify-content:flex-start;text-align:left;border-radius:16px;min-height:42px;font-size:.88rem;font-weight:680;padding:.52rem .76rem;border:1px solid #E7EAF2;background:linear-gradient(90deg,#FFFFFF,#FAFBFF);box-shadow:0 5px 14px rgba(53,65,92,.045);transition:all .2s ease;color:#475467}
        [data-testid="stSidebar"] div.stButton>button:hover{background:#F4F8FF;border-color:#CFDDF8;transform:translateX(2px);box-shadow:0 8px 18px rgba(53,65,92,.075);color:#273142}
        [data-testid="stSidebar"] div.stButton>button[kind="primary"],[data-testid="stSidebar"] div.stButton [data-testid="stBaseButton-primary"]{position:relative;background:linear-gradient(90deg,#EAF3FF,#F1EDFF);border:1px solid #D9CCFF;color:#273142;font-weight:740;box-shadow:0 0 0 3px rgba(155,138,251,.06),0 8px 18px rgba(155,138,251,.12);animation:none}
        [data-testid="stSidebar"] div.stButton>button[kind="primary"]::before,[data-testid="stSidebar"] div.stButton [data-testid="stBaseButton-primary"]::before{content:"";position:absolute;left:0;top:9px;bottom:9px;width:4px;border-radius:999px;background:#9B8AFB}
        [data-testid="stSidebar"] div.stButton>button[kind="secondary"],[data-testid="stSidebar"] div.stButton [data-testid="stBaseButton-secondary"]{background:linear-gradient(90deg,#FFFFFF,#FAFBFF);border:1px solid #E7EAF2;color:#475467}
        [data-testid="stSidebar"] div.stButton>button[kind="tertiary"],[data-testid="stSidebar"] div.stButton [data-testid="stBaseButton-tertiary"]{min-height:36px;border:1px solid #EEF1F6;background:rgba(255,255,255,.62);border-radius:11px;margin:.12rem 0;padding:.36rem .62rem;font-size:.8rem;font-weight:560;color:#5F6B7A;box-shadow:none}
        [data-testid="stSidebar"] div.stButton>button[kind="tertiary"]:hover,[data-testid="stSidebar"] div.stButton [data-testid="stBaseButton-tertiary"]:hover{background:#EAF3FF;border-color:#DCE9FF;color:#273142;transform:translateX(2px);box-shadow:none}
        @keyframes navPulse{0%,100%{box-shadow:0 0 0 2px rgba(155,138,251,.06),0 8px 18px rgba(155,138,251,.12)}50%{box-shadow:0 0 0 4px rgba(255,126,182,.10),0 10px 22px rgba(155,138,251,.18)}}

        /* 响应式布局 */
        @media(max-width:1100px){[data-testid="stSidebar"]{min-width:min(var(--sidebar-width),240px)!important;max-width:min(var(--sidebar-width),240px)!important;width:min(var(--sidebar-width),240px)!important}[data-testid="stSidebarCollapseButton"]{left:calc(min(var(--sidebar-width),240px) - 48px)!important}}
        .hero-shell{display:grid;grid-template-columns:1.15fr .85fr;gap:1.5rem;padding:2.7rem 3rem;border:1px solid #E5EAF2;border-radius:30px;background:linear-gradient(125deg,#F4F8FF 0%,#FFF5FA 56%,#FFF9EE 100%);box-shadow:0 20px 50px rgba(72,82,110,.10);overflow:hidden}.hero-kicker{color:var(--blue);font-size:.78rem;font-weight:850;letter-spacing:.14em}.hero-copy h1{font-size:3.15rem;line-height:1.1;margin:.55rem 0 1rem}.hero-copy p{font-size:1.05rem;color:var(--muted);line-height:1.8}.hero-note{margin-top:1rem;color:#7D8798;font-size:.84rem}.orbit{position:relative;min-height:320px}.orbit-track{position:absolute;inset:35px 20px;border:2px dashed #C9D9F8;border-radius:50%}.orbit-center{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:112px;height:112px;border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;background:linear-gradient(135deg,#5B8FF9,#9B8AFB);color:white;font-weight:850;box-shadow:0 16px 30px rgba(91,143,249,.22)}.orbit-card{position:absolute;padding:.65rem .8rem;background:white;border:1px solid var(--line);border-radius:14px;box-shadow:0 8px 22px rgba(56,68,98,.09);font-size:.8rem;font-weight:750;animation:float 4s ease-in-out infinite}.orbit-card.one{left:4%;top:16%;border-top:4px solid var(--sky)}.orbit-card.two{right:2%;top:21%;border-top:4px solid var(--mint);animation-delay:.7s}.orbit-card.three{left:9%;bottom:13%;border-top:4px solid var(--purple);animation-delay:1.4s}.orbit-card.four{right:3%;bottom:10%;border-top:4px solid var(--pink);animation-delay:2.1s}@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
        .glass{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:1.15rem 1.2rem;box-shadow:0 10px 28px rgba(53,65,92,.08);transition:transform .2s ease,box-shadow .2s ease}.glass:hover,.insight:hover,.world-node:hover{transform:translateY(-3px);box-shadow:0 15px 32px rgba(53,65,92,.11)}.feature-card{min-height:148px;border-top:5px solid var(--blue)}.feature-card.mentor{border-top-color:var(--purple)}.feature-card.hr{border-top-color:var(--orange)}.feature-no{color:var(--blue);font-size:.74rem;font-weight:850}.feature-title{font-size:1.05rem;font-weight:780;margin:.45rem 0}.feature-text{color:var(--muted);font-size:.87rem;line-height:1.65}
        .section-title{font-size:1.4rem;font-weight:850;margin:1.6rem 0 .75rem}.section-sub{color:var(--muted);margin-top:-.4rem;margin-bottom:1rem}.step-line{display:grid;grid-template-columns:repeat(5,1fr);gap:.65rem;margin:1rem 0 1.4rem}.step{padding:.75rem;border-radius:14px;text-align:center;background:#F5F6F8;border:1px solid #EAECF0;color:#98A2B3;font-size:.8rem;transition:.2s}.step:before{content:"○";margin-right:.35rem}.step.done{color:#3D7F6B;background:var(--mint-soft);border-color:#C8F0E3}.step.done:before{content:"✓"}.step.active{color:white;background:var(--step-color,var(--blue));border-color:transparent;transform:scale(1.035);box-shadow:0 8px 20px rgba(91,143,249,.18)}.step-1{--step-color:var(--blue)}.step-2{--step-color:var(--orange)}.step-3{--step-color:var(--purple)}.step-4{--step-color:var(--mint)}.step-5{--step-color:var(--pink)}
        .wizard-banner{padding:1rem 1.2rem;border-radius:18px;margin-bottom:1rem;border:1px solid var(--line)}.wizard-banner.step-1{background:var(--blue-soft)}.wizard-banner.step-2{background:var(--orange-soft)}.wizard-banner.step-3{background:var(--purple-soft)}.wizard-banner.step-4{background:var(--mint-soft)}.wizard-banner.step-5{background:var(--pink-soft)}.demo-tag{display:inline-block;color:#8A6411;background:var(--yellow-soft);border:1px solid #F2DE93;padding:.24rem .6rem;border-radius:99px;font-size:.76rem;font-weight:750}.ai-note{padding:.9rem 1rem;border-left:4px solid var(--mint);background:var(--mint-soft);border-radius:12px;color:#356B5C;font-size:.88rem}.hint-card{padding:1rem 1.1rem;border-radius:18px;background:linear-gradient(180deg,#F5F8FF 0%,#EEF3FF 100%);border:1px solid #D8E3F5;margin:.7rem 0 1rem;box-shadow:0 8px 20px rgba(53,65,92,.045)}.hint-title{font-size:1.02rem;font-weight:760;color:#273142;margin-bottom:.6rem;line-height:1.5}.hint-list{margin:0;padding-left:1.2rem}.hint-list li{margin:.28rem 0;line-height:1.7;color:#4B5870}.insight{padding:1rem;border-radius:18px;background:white;border:1px solid var(--line);box-shadow:0 8px 22px rgba(53,65,92,.06);min-height:132px;transition:.2s}.insight h4{margin:0 0 .55rem}.insight p{color:var(--muted);font-size:.86rem;line-height:1.65;margin:0}
        .world-map{display:grid;grid-template-columns:repeat(5,1fr);gap:1rem;position:relative;margin:1.2rem 0 1.5rem}.world-map:before{content:"";position:absolute;left:8%;right:8%;top:47%;border-top:2px dashed #D7DCE5;z-index:0}.world-node{position:relative;z-index:1;padding:1rem;border-radius:20px;background:var(--node-soft,#F7F8FA);border:1px solid var(--line);min-height:184px;transition:.2s}.world-node.unlocked{border-color:var(--node-color,#B8C4D6)}.world-node.active{transform:translateY(-5px);border-color:var(--node-color,var(--blue));box-shadow:0 16px 30px rgba(53,65,92,.12)}.world-node.locked{background:#FAFAFA;color:#98A2B3}.node-index{display:inline-flex;width:34px;height:34px;border-radius:50%;align-items:center;justify-content:center;background:var(--node-color,#D0D5DD);color:white;font-weight:850}.node-status{float:right;font-size:.7rem;padding:.22rem .55rem;border-radius:99px;background:white;color:var(--muted);border:1px solid var(--line)}.node-title{font-weight:850;margin:.8rem 0 .25rem}.node-range{font-size:.74rem;color:var(--node-color,var(--blue));font-weight:750}.node-goal{font-size:.82rem;color:var(--muted);line-height:1.5;margin-top:.5rem}.node-xp{margin-top:.7rem;color:var(--purple);font-size:.78rem;font-weight:750}
        .boundary-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.65rem}.boundary{padding:.8rem;border-radius:12px;background:#FAFBFC;border:1px solid var(--line);color:var(--muted);font-size:.84rem}.boundary strong{display:block;color:var(--blue);margin-bottom:.25rem}.risk-low,.risk-medium,.risk-high{display:inline-block;padding:.22rem .65rem;border-radius:99px;font-size:.76rem;font-weight:800}.risk-low{color:#347B65;background:var(--mint-soft)}.risk-medium{color:#9A6B00;background:var(--yellow-soft)}.risk-high{color:#B43C3C;background:#FFF0F0}
        .event-hero{padding:1.35rem 1.45rem;border-radius:20px;background:linear-gradient(120deg,var(--blue-soft),var(--purple-soft));border:1px solid #DDE7FA}.event-week{font-size:.74rem;color:var(--blue);font-weight:850;letter-spacing:.12em}.event-title{font-size:1.45rem;font-weight:850;margin:.4rem 0}.event-detail{color:var(--muted);line-height:1.7}.decision-card{padding:1rem 1.1rem;border-radius:16px;background:linear-gradient(120deg,var(--mint-soft),var(--purple-soft));border:1px solid var(--line);color:var(--text)}.timeline-row{display:grid;grid-template-columns:65px 18px 1fr;gap:.7rem;align-items:start;padding:.35rem 0}.timeline-week{color:#98A2B3;font-size:.78rem;text-align:right}.timeline-dot{width:12px;height:12px;border-radius:50%;background:#E1E4E9;margin-top:.2rem}.timeline-dot.done{background:var(--mint)}.timeline-dot.current{background:var(--orange);box-shadow:0 0 0 5px rgba(255,180,91,.16)}.timeline-text{color:#98A2B3;font-size:.83rem}.timeline-text.done,.timeline-text.current{color:var(--text)}.brief{padding:1.1rem 1.2rem;border-radius:16px;background:linear-gradient(135deg,var(--blue-soft),var(--purple-soft));border:1px solid var(--line);color:var(--text);line-height:1.75}.focus-person{padding:.8rem;border-radius:13px;background:white;border:1px solid var(--line);box-shadow:0 6px 18px rgba(53,65,92,.05);margin:.45rem 0}.focus-meta{font-size:.78rem;color:var(--muted);margin-top:.2rem}.summary-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.7rem}.summary-item{background:var(--surface-soft);border:1px solid var(--line);border-radius:13px;padding:.8rem}.summary-label{font-size:.72rem;color:#98A2B3}.summary-value{margin-top:.25rem;font-weight:750;color:var(--text)}
        .evidence-shell{padding:1rem 1.1rem;border-radius:18px;background:var(--blue-soft);border:1px solid #CFE1FF;margin:.8rem 0}.score-card{padding:.8rem;border-radius:15px;background:var(--purple-soft);border:1px solid #DDD5FF;text-align:center}.score-number{font-size:1.55rem;font-weight:850;color:var(--purple)}.status-supplement{padding:.8rem 1rem;border-radius:14px;background:var(--yellow-soft);border-left:4px solid var(--yellow)}.status-mentor{padding:.8rem 1rem;border-radius:14px;background:var(--orange-soft);border-left:4px solid var(--orange)}.status-pass{padding:.8rem 1rem;border-radius:14px;background:var(--mint-soft);border-left:4px solid var(--mint)}.gate-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1rem 0}.gate-card{padding:1rem 1.1rem;border-radius:20px;background:white;border:1px solid var(--line);border-top:6px solid var(--gate-color);box-shadow:0 8px 24px rgba(53,65,92,.07)}.gate-title{font-size:1.08rem;font-weight:850}.gate-state{display:inline-block;margin:.45rem 0;padding:.2rem .55rem;border-radius:99px;background:var(--gate-soft);color:var(--text);font-size:.75rem;font-weight:800}.gate-list{font-size:.8rem;line-height:1.65;color:var(--muted)}.action-card{padding:1rem 1.1rem;border-radius:18px;background:white;border:1px solid var(--line);border-top:5px solid var(--card-color,var(--blue));box-shadow:0 8px 22px rgba(53,65,92,.06)}.xiaoe-card{padding:1rem 1.1rem;border-radius:20px;background:linear-gradient(120deg,var(--blue-soft),var(--pink-soft));border:2px solid #BFD4FF;box-shadow:0 12px 28px rgba(91,143,249,.12)}
        div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:.9rem 1rem;border-radius:18px;box-shadow:0 7px 20px rgba(53,65,92,.06)}div[data-testid="stMetric"] label{color:var(--muted)!important}div.stButton>button,div.stFormSubmitButton>button{border-radius:12px;font-weight:750;border:1px solid #C7D7F5;min-height:2.7rem;background:white;color:var(--text)}div.stButton>button:hover,div.stFormSubmitButton>button:hover{border-color:var(--blue);color:var(--blue);background:var(--blue-soft)}div.stButton>button[kind="primary"],div.stFormSubmitButton>button[kind="primary"]{background:linear-gradient(90deg,var(--blue),var(--purple));border:0;color:white;box-shadow:0 8px 20px rgba(91,143,249,.22)}[data-testid="stForm"]{background:white;border:1px solid var(--line);border-radius:22px;padding:1.3rem;box-shadow:0 10px 26px rgba(53,65,92,.06)}
        .stTextInput input,.stTextArea textarea,.stNumberInput input,[data-baseweb="select"]>div{background:white!important;color:var(--text)!important;border-color:#DDE1E8!important}[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]{background:white!important;color:var(--text)!important}[role="option"]{background:white!important;color:var(--text)!important}[role="option"]:hover{background:var(--blue-soft)!important}.stProgress>div>div>div>div{background:linear-gradient(90deg,var(--blue),var(--mint))}
        @media(max-width:800px){.hero{padding:2rem 1.4rem}.hero h1{font-size:2.15rem}.hero:after{display:none}.hero-shell{grid-template-columns:1fr;padding:1.6rem 1.2rem}.hero-copy h1{font-size:2.15rem}.orbit{min-height:260px}.world-map:before{display:none}.step-line,.world-map,.gate-grid{grid-template-columns:1fr}.summary-grid,.boundary-grid{grid-template-columns:1fr}.block-container{padding-left:1rem;padding-right:1rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <style>
        :root{{--sidebar-width:{sidebar_width};--sidebar-collapse-left:{collapse_left}}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    defaults: dict[str, Any] = {
        "current_page": "首页", "nav_open_group": None, "sidebar_compact": False, "sidebar_width_mode": "normal",
        "wizard_step": 1, "profile": None, "diagnosis": None, "growth_plan": [], "reviews": [],
        "wizard_nickname": "", "wizard_primary_role": "游戏策划", "wizard_secondary_role": "活动策划",
        "wizard_experience": "应届生", "wizard_business_stage": "快速成长期",
        "wizard_work_modes": ["项目协作"], "wizard_expected_deliverable": "", "wizard_real_project": "尚未进入",
        "wizard_work_pace": "平稳", "wizard_weekly_growth_hours": 6, "wizard_mentor_hours": 1.0,
        "wizard_learning_styles": ["真实项目", "导师示范"], "wizard_problem_handling": PROBLEM_HANDLING[0],
        "wizard_confidence": 3, "wizard_worry": "", "wizard_mentor_help": "", "wizard_abilities": ["业务理解", "AI协作", "跨团队协作"],
        "wizard_subjective_problem": "", "wizard_ai_help_tasks": "",
        "wizard_core_goal": "", "wizard_task_intensity": INTENSITY_OPTIONS[1], "wizard_auto_adjust": True, "wizard_enter_auto_demo": False,
        "review_week": 1, "review_completed": [], "review_unfinished": [], "review_difficulty": "",
        "review_output": "", "review_confidence": 3, "review_hours": 6,
        "review_subjective_done": "", "review_subjective_blocked": "", "review_subjective_next": "",
        "demo_step": 0, "demo_week": 0, "demo_running": False, "demo_speed": 1, "demo_tick": 0, "current_event": "等待开始",
        "growth_metrics": {"XP": 0, "业务理解": 25, "AI协作": 30, "跨团队协作": 20, "独立交付": 15},
        "risk_level": "低", "mentor_triggered": False,
        "demo_adjustment": "等待系统生成成长策略。", "demo_history": [],
        "demo_requested": False,
        "baseline_capabilities": None, "latest_capabilities": None,
        "pending_adjustment": None, "dynamic_task_counter": 0,
        "evidence_records": {}, "evidence_signatures": [], "evidence_counter": 0,
        "mentor_decisions": [], "gate_results": {},
        "action_cards": {"newcomer": {}, "mentor": {}, "hr": {}},
        "demo_evidence_stage": "未提交", "demo_evidence_task_id": None,
        "task_status_overrides": {},
        "llm_hr_brief": None,
        "ai_today_advice": "", "ai_profile_interpretation": "", "ai_profile_signature": "", "ai_diagnosis_summary": "",
        "ai_growth_config": None, "ai_review_feedback": "", "ai_demo_narration": "",
        "ai_mentor_questions": "", "ai_hr_insight": "", "demo_random_seed": None, "demo_random_script": None,
        "game": initial_game_state(),
    }
    defaults.update({key: "需要指导" for key in AI_QUESTIONS})
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    st.session_state.game = normalize_game_state(st.session_state.get("game"))


def get_page_group(page_name: str) -> str | None:
    return PAGE_TO_GROUP.get(page_name)


def navigate_to(page_name: str) -> None:
    if page_name not in PAGES:
        return
    st.session_state.current_page = page_name
    st.session_state.nav_open_group = get_page_group(page_name)
    st.session_state.need_scroll_top = True


def toggle_nav_group(group_id: str) -> None:
    if group_id not in NAV_GROUPS:
        return
    st.session_state.nav_open_group = "__closed__" if st.session_state.nav_open_group == group_id else group_id


def navigate(page: str) -> None:
    navigate_to(page)


def render_breadcrumb() -> None:
    page = st.session_state.current_page
    group_id = get_page_group(page)
    if page == "首页":
        label = "首页"
    elif group_id:
        label = f'{NAV_GROUPS[group_id]["label"]} / <strong>{escape(page)}</strong>'
    else:
        label = escape(page)
    st.markdown(f'<div class="breadcrumb">{label}</div>', unsafe_allow_html=True)


def optional_ai_config() -> dict[str, str]:
    from ai_runtime import ai_config

    return ai_config()


def current_ai_mode() -> str:
    return "AI增强模式" if ai_available() else "本地规则稳定模式"


def optional_ai_enhance(purpose: str, source_text: str, fallback: str) -> str:
    prompt = (
        "请优化以下新人培养建议，保持专业、简洁，不改变分数、状态、阶段闸门、"
        f"安全判断或是否触发导师。\n\n{source_text}"
    )
    return optional_ai_text(purpose, prompt, fallback, temperature=0.2)


def ai_safety_caption() -> None:
    st.caption("AI仅用于辅助分析和内容生成，最终判断需由本人、导师或HR确认。")


def render_ai_mode_hint() -> None:
    st.caption(f"{ai_mode_label()}｜AI仅用于辅助分析和内容生成，最终判断需由本人、导师或HR确认。")


def render_ai_output(text: str) -> None:
    st.markdown(f'<div class="brief">{escape(text)}</div>', unsafe_allow_html=True)
    ai_safety_caption()


def has_text(*values: Any) -> bool:
    return any(str(value).strip() for value in values if value is not None)


def clear_ai_output(key: str) -> None:
    st.session_state[key] = "" if isinstance(st.session_state.get(key), str) else None


def render_ai_prereq_hint(title: str, items: list[str]) -> None:
    list_html = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(
        f"""
        <div class="hint-card">
          <div class="hint-title">{escape(title)}</div>
          <ul class="hint-list">{list_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def profile_is_ready() -> bool:
    profile = st.session_state.get("profile")
    plan = st.session_state.get("growth_plan", [])
    if not profile or not isinstance(profile, dict):
        return False
    return has_text(
        profile.get("nickname", ""),
        profile.get("core_goal", ""),
        profile.get("expected_deliverable", ""),
    ) and bool(plan)


def top_capabilities(capabilities: dict[str, int], reverse: bool = True, count: int = 2) -> list[str]:
    return [name for name, _ in sorted(capabilities.items(), key=lambda item: item[1], reverse=reverse)[:count]]


def build_profile_input_signature(profile: dict[str, Any], diagnosis: dict[str, Any]) -> str:
    payload = {
        "profile": profile,
        "diagnosis": diagnosis,
        "subjective_problem": st.session_state.get("wizard_subjective_problem", ""),
        "ai_help_tasks": st.session_state.get("wizard_ai_help_tasks", ""),
        "core_goal": st.session_state.get("wizard_core_goal", ""),
        "expected_deliverable": st.session_state.get("wizard_expected_deliverable", ""),
    }
    return hashlib.md5(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def sync_secondary_role() -> None:
    roles = PRIMARY_ROLES[st.session_state.wizard_primary_role]
    if st.session_state.wizard_secondary_role not in roles:
        st.session_state.wizard_secondary_role = roles[0]


def calculate_ai_diagnosis(answers: dict[str, str]) -> dict[str, Any]:
    raw = {key: AI_OPTION_SCORES[value] for key, value in answers.items()}
    score = lambda keys: round(sum(raw[key] for key in keys) / (3 * len(keys)) * 100)
    dimensions = {
        "AI工具使用": score(["ai_frequency", "ai_prompt", "ai_docs", "ai_data", "ai_workflow"]),
        "AI结果验证": score(["ai_context", "ai_verify"]),
        "AI业务应用": score(["ai_context", "ai_data", "ai_business"]),
        "AI安全意识": score(["ai_security"]),
    }
    maturity_score = round(sum(dimensions.values()) / len(dimensions))
    if maturity_score < 25:
        level = "L1观察者"
    elif maturity_score < 50:
        level = "L2协作新手"
    elif maturity_score < 75:
        level = "L3业务协作者"
    else:
        level = "L4人机协同引领者"
    dimensions["AI协作成熟度"] = maturity_score
    return {"dimensions": dimensions, "maturity_score": maturity_score, "maturity_level": level}


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def build_capability_scores(profile: dict[str, Any], ai_diagnosis: dict[str, Any]) -> dict[str, int]:
    experience_bonus = {"应届生": 0, "实习转正": 5, "1年以内": 8, "1—3年": 16, "3—5年": 24, "5年以上": 30}[profile["experience"]]
    project_bonus = {"尚未进入": 0, "已进入，承担辅助任务": 12, "已进入，承担核心任务": 22}[profile["real_project"]]
    ai_data_score = AI_OPTION_SCORES[profile["ai_answers"]["ai_data"]] * 8
    collaboration_signals = sum(mode in profile["work_modes"] for mode in ["项目协作", "跨团队协作", "客户或用户沟通"])
    data_signal = 18 if "数据分析" in profile["work_modes"] else 5
    return {
        "业务理解": clamp_score(32 + experience_bonus + project_bonus + (8 if profile["business_stage"] == "稳定运营期" else 3)),
        "AI协作": ai_diagnosis["maturity_score"],
        "跨团队协作": clamp_score(28 + experience_bonus * 0.7 + collaboration_signals * 13),
        "数据意识": clamp_score(25 + data_signal + ai_data_score + experience_bonus * 0.5),
        "独立交付": clamp_score(18 + profile["confidence"] * 9 + experience_bonus + project_bonus),
    }


def enrich_diagnosis(profile: dict[str, Any], diagnosis: dict[str, Any]) -> dict[str, Any]:
    result = dict(diagnosis)
    capabilities = build_capability_scores(profile, diagnosis)
    sorted_capabilities = sorted(capabilities.items(), key=lambda item: item[1], reverse=True)
    strengths = [f"{name}表现相对突出（{score}分）" for name, score in sorted_capabilities[:2]]
    gaps = [f"{name}需要优先补齐（{score}分）" for name, score in sorted_capabilities[-2:]]
    risks = []
    if profile["work_pace"] == "持续高强度":
        risks.append("持续高强度节奏可能挤占成长任务时间。")
    if profile["confidence"] <= 2:
        risks.append("独立开展真实业务的信心偏低，需要设计低风险成功体验。")
    if diagnosis["dimensions"]["AI结果验证"] < 50:
        risks.append("AI结果验证能力不足，可能把流畅表达误判为可靠结论。")
    if profile["mentor_hours"] < 0.5:
        risks.append("导师可投入时间有限，需要将检查点集中在高风险决策。")
    if not risks:
        risks.append("当前风险总体可控，仍需防止成长任务与真实业务脱节。")
    if profile["confidence"] <= 2 or diagnosis["maturity_score"] < 40:
        mentor_intensity = "强化带教：前4周每周一次30分钟沟通，关键交付前增加验收。"
    elif profile["real_project"] == "已进入，承担核心任务":
        mentor_intensity = "关键节点带教：聚焦范围、质量和风险决策，不替代新人执行。"
    else:
        mentor_intensity = "标准带教：每两周一次结构化沟通，每周异步检查成果。"
    learning_styles = profile["learning_styles"] or ["真实项目", "导师示范"]
    result.update({
        "capabilities": capabilities, "strengths": strengths, "gaps": gaps, "risks": risks,
        "baseline_capabilities": dict(capabilities),
        "recommended_method": f"以{'、'.join(learning_styles[:3])}为主，将训练嵌入{ROLE_BLUEPRINTS[profile['primary_role']]['object']}真实场景。",
        "mentor_intensity": mentor_intensity,
    })
    return result


def collect_profile() -> dict[str, Any]:
    answers = {key: st.session_state[key] for key in AI_QUESTIONS}
    return {
        "nickname": st.session_state.wizard_nickname.strip(), "primary_role": st.session_state.wizard_primary_role,
        "secondary_role": st.session_state.wizard_secondary_role, "experience": st.session_state.wizard_experience,
        "business_stage": st.session_state.wizard_business_stage, "work_modes": st.session_state.wizard_work_modes,
        "expected_deliverable": st.session_state.wizard_expected_deliverable.strip(), "real_project": st.session_state.wizard_real_project,
        "work_pace": st.session_state.wizard_work_pace, "weekly_growth_hours": st.session_state.wizard_weekly_growth_hours,
        "mentor_hours": st.session_state.wizard_mentor_hours, "ai_answers": answers,
        "learning_styles": st.session_state.wizard_learning_styles, "problem_handling": st.session_state.wizard_problem_handling,
        "confidence": st.session_state.wizard_confidence, "worry": st.session_state.wizard_worry.strip(),
        "mentor_help": st.session_state.wizard_mentor_help.strip(), "abilities": st.session_state.wizard_abilities,
        "core_goal": st.session_state.wizard_core_goal.strip(), "task_intensity": st.session_state.wizard_task_intensity,
        "auto_adjust": st.session_state.wizard_auto_adjust, "enter_auto_demo": st.session_state.wizard_enter_auto_demo,
    }


def generate_legacy_plan(profile: dict[str, Any]) -> list[dict[str, Any]]:
    blueprint = ROLE_BLUEPRINTS[profile["primary_role"]]
    base_titles = [
        f"绘制{profile['secondary_role']}业务地图", "完成AI协作基本功训练", f"拆解3个{blueprint['research']}",
        f"完成一次{blueprint['user']}问题分析", "与协作伙伴完成最小方案", f"用{blueprint['data']}验证假设",
        f"独立起草{blueprint['deliverable']}", "完成关键成果质量校准", "主持跨职能评审与迭代", "完成90天成果答辩与方法沉淀",
    ]
    base_stages = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    challenge_titles = ["设计一个可复用AI工作流", "向团队完成一次方法分享"]
    if profile["task_intensity"].startswith("轻量"):
        selected = [(base_stages[index], base_titles[index], "必修任务") for index in [0, 1, 2, 3, 4, 6, 9]]
    else:
        selected = [
            (stage, title, "选修任务" if index > 7 else "必修任务")
            for index, (stage, title) in enumerate(zip(base_stages, base_titles))
        ]
        if profile["task_intensity"].startswith("挑战"):
            selected.extend([(3, challenge_titles[0], "挑战任务"), (4, challenge_titles[1], "挑战任务")])
    plan = []
    abilities = profile.get("abilities") or ["业务理解", "AI协作", "独立决策"]
    for index, (stage, title, task_type) in enumerate(selected):
        plan.append({
            "id": f"task_{index + 1}", "stage": stage, "name": title,
            "purpose": f"围绕{profile['core_goal']}建立可验证的业务能力。",
            "action": "使用真实业务素材完成任务，并在关键判断点记录依据。",
            "human": "定义目标、判断业务价值、承担结果责任并完成最终决策。",
            "ai": "辅助检索、拆解、生成初稿、检查遗漏和整理复盘。",
            "verify": "事实、数据口径、用户结论、业务取舍和最终交付必须人工验证。",
            "forbidden": "个人隐私、未公开经营数据、账号密钥、受限代码和未经授权的内部材料不得输入AI。",
            "deliverable": f"{title}的可评审成果", "criteria": "结论有证据、过程可追溯、成果经导师或协作方确认。",
            "hours": 4 + index % 3, "xp": 80 + index * 20, "status": "未开始",
            "skill_reward": abilities[index % len(abilities)], "task_type": task_type, "dynamic": False,
            "mentor_checkpoint": "确认任务边界、证据质量和验收标准。", "risk_event": "时间被业务挤占或过度依赖AI初稿。",
        })
    return plan


def generate_personalized_plan(profile: dict[str, Any], diagnosis: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        blueprint = ROLE_BLUEPRINTS[profile["primary_role"]]
        concrete_dimensions = {key: diagnosis["dimensions"][key] for key in ["AI工具使用", "AI结果验证", "AI业务应用", "AI安全意识"]}
        low_dimensions = sorted(concrete_dimensions.items(), key=lambda item: item[1])[:2]
        focus = "、".join(name for name, _ in low_dimensions)
        learning_styles = profile["learning_styles"] or ["真实项目", "导师示范"]
        learning = "、".join(learning_styles[:2])
        specs = [
            (0, f"绘制{profile['secondary_role']}业务与协作地图", "组织理解", "访谈关键协作方，标注输入、决策、输出和责任边界。", "业务地图与关键人清单", 80),
            (0, "完成AI协作基本功与安全基线", "AI协作", "围绕真实工作完成提示、校验、安全判断三组练习。", "个人AI协作与安全清单", 100),
            (1, f"完成{blueprint['research']}竞品与用户证据分析", "业务理解", "选择真实案例，区分事实、推测和可验证假设。", "证据化分析简报", 120),
            (1, f"用{blueprint['data']}验证一个业务问题", "数据意识", "提出三个业务问题，核对口径并给出下一步验证动作。", "数据观察与行动建议", 140),
            (2, f"共创一个{blueprint['object']}最小方案", "跨团队协作", f"与{blueprint['partner']}完成一次范围明确的小型协作。", "最小方案与责任清单", 160),
            (2, "主持一次跨团队走查", "跨团队协作", "收集分歧、判断优先级、形成变更记录并确认责任人。", "走查纪要与变更说明", 180),
            (3, f"独立起草{blueprint['deliverable']}", "独立交付", f"直接对齐90天目标“{profile['core_goal']}”，完成可评审初稿。", f"{blueprint['deliverable']}初稿", 220),
            (3, "完成质量补证与风险验证", "AI结果验证", "针对评审质疑补充用户、数据或技术证据，并记录AI错误。", "证据包与风险清单", 200),
            (4, "主持跨职能成果评审", "独立交付", "清晰说明目标、证据、取舍、风险和下一步，完成方案迭代。", "评审纪要与最终版本", 230),
            (4, "完成90天答辩与个人AI协作手册", "复盘沉淀", "沉淀有效提示、验证方法、安全边界和下一阶段计划。", "成果答辩与AI协作手册", 270),
        ]
        challenge_specs = [
            (3, "设计一个可复用AI工作流", "自动化工作流", "把一个高频任务拆成输入、处理、人工检查和输出四个环节，并完成安全审查。", "可复用AI工作流说明", 240),
            (4, "向团队完成一次方法分享", "影响力", "用真实案例分享人机分工、验证方法、失败经验和适用边界。", "团队分享材料与反馈记录", 260),
        ]
        if profile["task_intensity"].startswith("轻量"):
            selected_specs = [specs[index] for index in [0, 1, 2, 3, 4, 6, 9]]
        elif profile["task_intensity"].startswith("挑战"):
            selected_specs = specs + challenge_specs
        else:
            selected_specs = specs
        plan = []
        ability_cycle = profile["abilities"] or ["业务理解", "AI协作", "独立决策"]
        for index, (stage, name, reward, action, deliverable, xp) in enumerate(selected_specs, start=1):
            hours = max(2, round(3 + stage * 1.2 + index % 2))
            if profile["work_pace"] == "持续高强度":
                hours = max(2, hours - 1)
            project_note = "优先使用当前真实项目素材。" if profile["real_project"] != "尚未进入" and stage >= 2 else "使用可公开或脱敏的业务材料。"
            if profile["task_intensity"].startswith("挑战") and index > 10:
                task_type = "挑战任务"
            elif not profile["task_intensity"].startswith("轻量") and index > 8:
                task_type = "选修任务"
            else:
                task_type = "必修任务"
            plan.append({
                "id": f"task_{index}", "stage": stage, "name": name,
                "purpose": f"支撑“{profile['core_goal']}”，重点提升{focus}。",
                "action": f"采用{learning}方式。{action}{project_note}",
                "human": "定义目标、判断业务价值、处理取舍、对外沟通并承担最终结果责任。",
                "ai": "辅助检索、结构化拆解、生成备选、检查遗漏、模拟质疑和整理过程记录。",
                "verify": "事实来源、数据口径、用户洞察、业务决策、风险判断和最终交付必须由人验证。",
                "forbidden": "个人隐私、未公开经营数据、账号密钥、受限代码、商业机密和未经授权的内部材料不得输入AI。",
                "deliverable": deliverable, "criteria": "成果可被协作方理解，关键结论有证据，AI参与过程可追溯，导师确认验收标准。",
                "hours": hours, "xp": xp, "status": "未开始", "skill_reward": reward if reward else ability_cycle[index % len(ability_cycle)],
                "task_type": task_type, "dynamic": False,
                "mentor_checkpoint": ["确认组织理解与安全边界", "校准问题与证据质量", "观察协作与责任承担", "验收真实交付质量", "评价成果与下一阶段潜力"][stage],
                "risk_event": ["信息过载或安全边界不清", "分析停留在AI摘要", "协作责任不清或等待导师答案", "质量不达标或缺乏证据", "只展示结果而未沉淀方法"][stage],
            })
        return plan
    except Exception as exc:
        logger.exception("generate_personalized_plan failed; fallback to legacy plan: %s", type(exc).__name__)
        if os.getenv("AI_NATIVE_DEV_MODE", "").strip() == "1":
            st.info("个性化计划生成失败，已切换至稳定模板。")
        return generate_legacy_plan(profile)


def load_demo_wizard() -> None:
    for key, value in DEMO_PROFILE.items():
        st.session_state[f"wizard_{key}"] = value
    for key, value in DEMO_AI_ANSWERS.items():
        st.session_state[key] = value
    st.session_state.wizard_step = 1
    st.session_state.current_page = "智能画像"


def initialize_demo_profile() -> None:
    load_demo_wizard()
    profile = collect_profile()
    diagnosis = enrich_diagnosis(profile, calculate_ai_diagnosis(profile["ai_answers"]))
    st.session_state.profile = profile
    st.session_state.diagnosis = diagnosis
    demo_baseline = {"业务理解": 25, "AI协作": 30, "跨团队协作": 20, "数据意识": diagnosis["capabilities"]["数据意识"], "独立交付": 15}
    st.session_state.baseline_capabilities = demo_baseline
    st.session_state.latest_capabilities = None
    st.session_state.growth_plan = generate_personalized_plan(profile, diagnosis)
    st.session_state.reviews = []
    st.session_state.pending_adjustment = None
    st.session_state.dynamic_task_counter = 0
    reset_demo()
    st.session_state.current_page = "90天自动演示"


def render_demo_disclaimer() -> None:
    st.markdown('<span class="demo-tag">模拟数据</span>', unsafe_allow_html=True)


def render_sidebar_navigation() -> None:
    current_page = st.session_state.current_page
    current_group = get_page_group(current_page)
    if current_page != "首页" and st.session_state.nav_open_group is None and current_group:
        st.session_state.nav_open_group = current_group

    home_type = "primary" if current_page == "首页" else "secondary"
    if st.button("首页", key="nav_home", type=home_type, width="stretch"):
        st.session_state.current_page = "首页"
        st.session_state.nav_open_group = None
        st.session_state.need_scroll_top = True
        st.rerun()

    for group_id, group in NAV_GROUPS.items():
        label = escape(group.get("label", "未命名分组"))
        subtitles = {
            "growth": "学习路径与复盘",
            "play": "游戏化闯关与演示",
            "manage": "导师与HR视角",
        }
        subtitle = escape(subtitles.get(group_id, ""))
        opened = st.session_state.nav_open_group == group_id
        symbol = "⌄" if opened else "›"
        group_type = "primary" if opened or current_group == group_id else "secondary"
        icons = {"growth": "⭐", "play": "🎮", "manage": "🔍"}
        icon = icons.get(group_id, "◆")
        if st.button(f"{icon} {label}  {symbol}", key=f"nav_group_{group_id}", type=group_type, width="stretch"):
            toggle_nav_group(group_id)
            st.rerun()
        st.markdown(f'<div class="nav-section-sub">{subtitle}</div>', unsafe_allow_html=True)
        if opened:
            st.markdown('<div class="nav-subtree">', unsafe_allow_html=True)
            for page in group["pages"]:
                page_type = "primary" if current_page == page else "tertiary"
                if st.button(page, key=f"nav_page_{page}", type=page_type, width="stretch"):
                    navigate_to(page)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand-mini"><div class="brand-title">职场开局</div>'
            '<div class="brand-sub">AI新人90天成长副本</div></div>',
            unsafe_allow_html=True,
        )
        render_sidebar_navigation()
        st.divider()
        if st.session_state.profile:
            sync_task_statuses()
            profile = st.session_state.profile
            st.markdown(f"**{escape(profile['nickname'])}**")
            st.caption(f"{profile['primary_role']}·{profile['secondary_role']}")
            completed = sum(task["status"] == "已完成" for task in st.session_state.growth_plan)
            st.progress(completed / max(len(st.session_state.growth_plan), 1))
            st.caption(f"成长进度{completed}/{len(st.session_state.growth_plan)}")
        st.caption(f"运行模式：{current_ai_mode()}")
        with st.expander("显示设置", expanded=False):
            st.toggle("紧凑", key="sidebar_compact")
            st.radio(
                "侧边栏宽度",
                ["narrow", "normal", "wide"],
                format_func={"narrow": "窄", "normal": "标准", "wide": "宽"}.get,
                horizontal=True,
                key="sidebar_width_mode",
            )
        st.markdown('<div class="nav-foot">当前版本为AI产品概念演示</div>', unsafe_allow_html=True)


def render_home() -> None:
    st.markdown(
        """
        <section class="hero-shell">
          <div class="hero-copy">
            <div class="hero-kicker">AI新人90天成长副本</div>
            <h1>职场开局</h1>
            <p>以成长证据为基础的AI Native新人适应与独立交付能力验证系统。智能规则引擎连接成果提交、证据评价、导师验收和HR信号；人负责判断、责任与最终决策。</p>
            <div class="hero-note">当前版本为AI产品概念演示，使用本地规则引擎和模拟数据稳定展示完整业务流程。</div>
          </div>
          <div class="orbit">
            <div class="orbit-track"></div><div class="orbit-center">90天<br>成长轨道</div>
            <div class="orbit-card one">画像诊断</div><div class="orbit-card two">动态任务</div>
            <div class="orbit-card three">导师介入</div><div class="orbit-card four">HR洞察</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="glass"><div class="feature-no">90天自动演示</div><div class="feature-title">一键体验完整90天</div><div class="feature-text">自动播放画像、任务延期、风险识别、计划调整、导师介入和成果答辩等关键事件。</div></div>', unsafe_allow_html=True)
        if st.button("一键体验完整90天", type="primary", width="stretch"):
            initialize_demo_profile()
            st.rerun()
    with right:
        st.markdown('<div class="glass"><div class="feature-no">个性化诊断</div><div class="feature-title">创建我的成长副本</div><div class="feature-text">通过五步向导诊断岗位场景、AI能力、学习偏好与带教资源，生成专属成长策略。</div></div>', unsafe_allow_html=True)
        if st.button("创建我的成长副本", width="stretch"):
            st.session_state.current_page = "智能画像"
            st.rerun()

    st.markdown('<div class="section-title">AI成长助理控制台</div>', unsafe_allow_html=True)
    render_ai_mode_hint()
    mode_cols = st.columns([1, 2])
    with mode_cols[0]:
        mode_text = ai_mode_label()
        mode_color = "#63D7B0" if ai_available() else "#FFB45B"
        st.markdown(
            f'<div class="action-card" style="--card-color:{mode_color}"><strong>当前模式</strong><br>{escape(mode_text)}</div>',
            unsafe_allow_html=True,
        )
    with mode_cols[1]:
        st.markdown(
            '<div class="glass"><strong>可用能力</strong><br>'
            '画像分析、路径生成、复盘建议、导师追问、HR洞察、闯关提示词反馈。'
            '<br><span style="color:#667085">无API时使用本地规则稳定模式，有API时自动启用AI增强。</span></div>',
            unsafe_allow_html=True,
        )
    render_ai_prereq_hint(
        "使用今日成长建议前，请先确认这些信息：",
        [
            "已生成新人画像和成长计划。",
            "智能画像第2步：填写“90天内预期交付成果”。",
            "智能画像第4步：填写“主观成长问题”和“希望AI帮忙的任务”。",
            "智能画像第5步：确认“90天核心目标”。",
        ],
    )
    if st.button("让AI帮我生成今日成长建议", type="primary", key="home_ai_advice"):
        if not profile_is_ready():
            clear_ai_output("ai_today_advice")
            st.warning("请先补齐必要信息，再生成今日成长建议。")
            render_ai_prereq_hint(
                "生成今日成长建议前，需要先补充这些信息：",
                [
                    "智能画像第1步：填写新人昵称和岗位。",
                    "智能画像第2步：填写“90天内预期交付成果”。",
                    "智能画像第4步：填写“用自己的话描述你现在最想解决的成长问题”和“你希望AI在哪些任务上帮你”。",
                    "智能画像第5步：确认“90天核心目标”，并点击“生成诊断与成长策略”。",
                    "或者：首页点击“一键体验完整90天”载入模拟画像后再生成。",
                ],
            )
        else:
            profile = st.session_state.profile
            completed = sum(task.get("status") == "已完成" for task in st.session_state.growth_plan)
            total = len(st.session_state.growth_plan)
            fallback = (
                f"今天建议先聚焦一个最小可交付成果：围绕{profile.get('core_goal', '当前成长目标')}，选择1项真实业务任务推进。"
                f"当前已完成{completed}/{total or 0}项任务，优先补齐证据来源、AI输出核验和导师校准记录。"
                "如果时间有限，先交付一页可验证成果，而不是继续扩大学习范围。"
            )
            prompt = (
                f"新人画像：{profile}\n任务进度：{completed}/{total}\n风险：{st.session_state.risk_level}\n"
                f"最近事件：{st.session_state.current_event}\n请生成今日成长建议，包含优先任务、AI协作方式和需要人工确认的内容。"
            )
            st.session_state.ai_today_advice = optional_ai_text("今日成长建议", prompt, fallback)
    if st.session_state.ai_today_advice:
        render_ai_output(st.session_state.ai_today_advice)

    st.markdown('<div class="section-title">一套引擎，服务三类角色</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    features = [
        ("01", "新人", "知道为什么学、如何与AI协作、何时需要人工判断，并用真实成果证明成长。"),
        ("02", "导师", "获得本周带教重点、风险提示、验收任务和一对一沟通问题，减少低效跟进。"),
        ("03", "HR", "看见批次进度、岗位差异、导师负载和高频障碍，将个体信号转化为组织行动。"),
    ]
    for col, (number, title, text) in zip(cols, features):
        with col:
            role_class = "mentor" if title == "导师" else "hr" if title == "HR" else ""
            st.markdown(f'<div class="glass feature-card {role_class}"><div class="feature-no">{number}</div><div class="feature-title">{title}</div><div class="feature-text">{text}</div></div>', unsafe_allow_html=True)


def render_step_indicator(step: int) -> None:
    labels = ["基础身份", "工作场景", "AI能力", "学习方式", "确认目标"]
    html = '<div class="step-line">'
    for index, label in enumerate(labels, start=1):
        state = "active" if index == step else "done" if index < step else ""
        html += f'<div class="step step-{index} {state}">{index:02d}·{label}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)
    st.progress(step / 5, text=f"画像进度{step}/5")


def validate_wizard_step(step: int) -> str | None:
    if step == 1 and not st.session_state.wizard_nickname.strip():
        return "请填写新人昵称。"
    if step == 2:
        if not st.session_state.wizard_work_modes:
            return "请至少选择1项当前主要工作方式。"
        if not st.session_state.wizard_expected_deliverable.strip():
            return "请填写90天内预期交付成果。"
    if step == 4:
        if not st.session_state.wizard_learning_styles:
            return "请至少选择1项偏好的学习方式。"
        if not 3 <= len(st.session_state.wizard_abilities) <= 5:
            return "请选择3—5项希望提升的能力。"
    if step == 5 and not st.session_state.wizard_core_goal.strip():
        return "请确认90天核心目标。"
    return None


def wizard_navigation(step: int) -> None:
    left, middle, right = st.columns([1, 2, 1])
    with left:
        if step > 1 and st.button("上一步", width="stretch"):
            st.session_state.wizard_step -= 1
            st.rerun()
    with right:
        label = "生成诊断与成长策略" if step == 5 else "下一步"
        if st.button(label, type="primary", width="stretch"):
            error = validate_wizard_step(step)
            if error:
                st.warning(error)
            elif step < 5:
                st.session_state.wizard_step += 1
                st.rerun()
            else:
                profile = collect_profile()
                diagnosis = enrich_diagnosis(profile, calculate_ai_diagnosis(profile["ai_answers"]))
                st.session_state.profile = profile
                st.session_state.diagnosis = diagnosis
                st.session_state.baseline_capabilities = dict(diagnosis["baseline_capabilities"])
                st.session_state.latest_capabilities = None
                st.session_state.growth_plan = generate_personalized_plan(profile, diagnosis)
                st.session_state.reviews = []
                st.session_state.evidence_records = {}
                st.session_state.evidence_signatures = []
                st.session_state.evidence_counter = 0
                st.session_state.mentor_decisions = []
                st.session_state.gate_results = {}
                st.session_state.action_cards = {"newcomer": {}, "mentor": {}, "hr": {}}
                st.session_state.task_status_overrides = {}
                st.session_state.pending_adjustment = None
                st.session_state.dynamic_task_counter = 0
                st.session_state.llm_hr_brief = None
                st.session_state.ai_today_advice = ""
                st.session_state.ai_profile_interpretation = ""
                st.session_state.ai_profile_signature = ""
                st.session_state.ai_diagnosis_summary = ""
                st.session_state.ai_growth_config = None
                st.session_state.ai_review_feedback = ""
                st.session_state.ai_demo_narration = ""
                st.session_state.ai_mentor_questions = ""
                st.session_state.ai_hr_insight = ""
                for task in st.session_state.growth_plan:
                    st.session_state[f"task_status_{task['id']}"] = "未开始"
                st.session_state.demo_requested = profile["enter_auto_demo"]
                st.session_state.current_page = "诊断报告"
                st.rerun()


def render_wizard() -> None:
    st.markdown('<div class="section-title">智能画像诊断</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">五步完成岗位、场景、AI能力、学习方式和目标诊断。所有结果仅保存在当前会话。</div>', unsafe_allow_html=True)
    if st.button("载入模拟画像", key="load_demo_wizard"):
        load_demo_wizard()
        st.rerun()
    step = st.session_state.wizard_step
    render_step_indicator(step)
    step_names = ["基础身份", "工作场景", "AI能力诊断", "学习方式", "确认目标"]
    st.markdown(f'<div class="wizard-banner step-{step}"><strong>第{step}步·{step_names[step - 1]}</strong><br><span style="color:#667085">每一步的信息都会影响成长任务、风险判断和导师检查点。</span></div>', unsafe_allow_html=True)

    if step == 1:
        st.markdown("### 基础身份")
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("新人昵称*", key="wizard_nickname")
            st.selectbox("一级岗位族", list(PRIMARY_ROLES), key="wizard_primary_role", on_change=sync_secondary_role)
            sync_secondary_role()
            st.selectbox("二级岗位", PRIMARY_ROLES[st.session_state.wizard_primary_role], key="wizard_secondary_role")
        with c2:
            st.selectbox("工作经验", EXPERIENCE_LEVELS, key="wizard_experience")
            st.selectbox("所处业务阶段", BUSINESS_STAGES, key="wizard_business_stage")
            st.markdown('<div class="ai-note">岗位和业务阶段会影响任务类型、交付标准与导师检查频率。</div>', unsafe_allow_html=True)
    elif step == 2:
        st.markdown("### 工作场景")
        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("当前主要工作方式", WORK_MODES, key="wizard_work_modes")
            st.text_area("90天内预期交付成果*", key="wizard_expected_deliverable")
            st.radio("是否已经进入真实项目", ["尚未进入", "已进入，承担辅助任务", "已进入，承担核心任务"], key="wizard_real_project")
        with c2:
            st.selectbox("当前工作节奏", WORK_PACES, key="wizard_work_pace")
            st.number_input("每周可投入成长时间（小时）", min_value=1, max_value=30, step=1, key="wizard_weekly_growth_hours")
            st.number_input("导师每周可投入时间（小时）", min_value=0.0, max_value=8.0, step=0.5, key="wizard_mentor_hours")
    elif step == 3:
        st.markdown("### AI能力诊断")
        st.caption("请按真实工作表现作答。系统会计算工具使用、结果验证、业务应用、安全意识与协作成熟度。")
        left, right = st.columns(2)
        for index, (key, question) in enumerate(AI_QUESTIONS.items()):
            with left if index % 2 == 0 else right:
                st.selectbox(question, AI_OPTIONS, key=key)
        preview = calculate_ai_diagnosis({key: st.session_state[key] for key in AI_QUESTIONS})
        st.info(f"当前AI协作成熟度预估：{preview['maturity_level']}（{preview['maturity_score']}分）")
    elif step == 4:
        st.markdown("### 学习方式")
        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("偏好的学习方式", LEARNING_STYLES, key="wizard_learning_styles")
            st.selectbox("遇到问题时通常如何处理", PROBLEM_HANDLING, key="wizard_problem_handling")
            st.slider("当前信心评分", 1, 5, key="wizard_confidence")
        with c2:
            st.text_area("最担心的问题", key="wizard_worry")
            st.text_area("希望导师提供的帮助", key="wizard_mentor_help")
            st.text_area("用自己的话描述你现在最想解决的成长问题", key="wizard_subjective_problem")
            st.text_area("你希望AI在哪些任务上帮你？", key="wizard_ai_help_tasks")
            st.multiselect("希望提升的3—5项能力", ABILITY_OPTIONS, key="wizard_abilities")
    else:
        st.markdown("### 确认目标")
        profile_preview = collect_profile()
        st.markdown(
            f"""
            <div class="summary-grid">
              <div class="summary-item"><div class="summary-label">身份</div><div class="summary-value">{escape(profile_preview['nickname'] or '待填写')}·{profile_preview['secondary_role']}</div></div>
              <div class="summary-item"><div class="summary-label">业务场景</div><div class="summary-value">{profile_preview['business_stage']}·{profile_preview['work_pace']}</div></div>
              <div class="summary-item"><div class="summary-label">预期交付</div><div class="summary-value">{escape(profile_preview['expected_deliverable'] or '待确认')}</div></div>
              <div class="summary-item"><div class="summary-label">成长资源</div><div class="summary-value">新人每周{profile_preview['weekly_growth_hours']}小时·导师每周{profile_preview['mentor_hours']:g}小时</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        default_goal = st.session_state.wizard_expected_deliverable
        if not st.session_state.wizard_core_goal and default_goal:
            st.session_state.wizard_core_goal = default_goal
        st.text_area("90天核心目标*", key="wizard_core_goal")
        st.selectbox("90天任务强度", INTENSITY_OPTIONS, key="wizard_task_intensity")
        st.checkbox("允许系统根据复盘自动调整计划", key="wizard_auto_adjust")
        st.checkbox("完成后进入自动演示模式", key="wizard_enter_auto_demo")
        st.markdown('<div class="ai-note">AI负责生成建议和监测风险；导师与新人共同确认目标、验收成果并承担最终决策责任。</div>', unsafe_allow_html=True)
    with st.expander("AI画像解读", expanded=bool(st.session_state.ai_profile_interpretation)):
        render_ai_mode_hint()
        st.caption("根据已填写的岗位、AI能力、学习偏好和主观目标生成辅助解读。")
        render_ai_prereq_hint(
            "AI画像解读会读取以下关键变量：",
            [
                "第2步“工作场景”：90天内预期交付成果。",
                "第4步“学习方式”：用自己的话描述你现在最想解决的成长问题。",
                "第4步“学习方式”：你希望AI在哪些任务上帮你。",
                "第5步“确认目标”：90天核心目标。",
            ],
        )
        button_label = "重新生成AI画像解读" if st.session_state.ai_profile_interpretation else "生成AI画像解读"
        if st.button(button_label, key="generate_ai_profile_interpretation"):
            subjective_problem = st.session_state.wizard_subjective_problem.strip()
            ai_help_tasks = st.session_state.wizard_ai_help_tasks.strip()
            expected_deliverable = st.session_state.wizard_expected_deliverable.strip()
            core_goal = st.session_state.wizard_core_goal.strip()
            if not any([subjective_problem, ai_help_tasks, expected_deliverable, core_goal]):
                clear_ai_output("ai_profile_interpretation")
                st.session_state.ai_profile_signature = ""
                st.warning("请先补充至少一个关键变量，再生成AI画像解读。")
                render_ai_prereq_hint(
                    "AI画像解读至少需要以下任意一类信息：",
                    [
                        "第2步“工作场景”：90天内预期交付成果。",
                        "第4步“学习方式”：主观成长问题。",
                        "第4步“学习方式”：希望AI帮忙的任务。",
                        "第5步“确认目标”：90天核心目标。",
                    ],
                )
                return
            profile_preview = collect_profile()
            diagnosis_preview = calculate_ai_diagnosis({key: st.session_state[key] for key in AI_QUESTIONS})
            signature = build_profile_input_signature(profile_preview, diagnosis_preview)
            weak_dimensions = [
                name for name, score in diagnosis_preview["dimensions"].items()
                if name in {"AI工具使用", "AI结果验证", "AI业务应用", "AI安全意识"} and score < 55
            ]
            user_goal = expected_deliverable or core_goal or "尚未填写"
            fallback = (
                f"1.我读取到的关键信息：你当前最想解决的问题是：{subjective_problem or '尚未填写'}；"
                f"你希望AI帮忙的任务是：{ai_help_tasks or '尚未填写'}；预期交付是：{user_goal}。\n\n"
                f"2.工作风格倾向：你更适合以{profile_preview['primary_role']}场景中的真实项目为主线，配合导师示范和短周期复盘。\n\n"
                f"3.AI协作成熟度：{diagnosis_preview['maturity_level']}，建议先强化{'、'.join(weak_dimensions[:2]) if weak_dimensions else 'AI结果验证和业务应用'}。\n\n"
                f"4.当前成长风险：围绕“{user_goal}”推进时，如果只依赖AI初稿，容易缺少业务证据和人工判断；"
                f"{'同时需要处理“' + subjective_problem + '”。' if subjective_problem else '当前主观卡点尚未补充，建议继续明确。'}\n\n"
                f"5.推荐训练方式：每周选择1个真实小任务，用AI辅助{ai_help_tasks or '整理材料、检查遗漏'}，但由本人判断结论，并请导师确认验收标准。\n\n"
                f"6.适合任务强度：{profile_preview['task_intensity']}。\n\n"
                "7.判断依据：岗位类型、AI核验能力、学习方式、主观目标、预期交付和希望AI协助的任务。"
            )
            prompt = (
                f"画像：{profile_preview}\nAI诊断：{diagnosis_preview}\n"
                "请必须结合以下用户主观输入进行分析：\n"
                f"主观成长问题：{subjective_problem or '尚未填写'}\n"
                f"希望AI帮忙的任务：{ai_help_tasks or '尚未填写'}\n"
                f"预期交付：{expected_deliverable or '尚未填写'}\n"
                f"90天核心目标：{core_goal or '尚未填写'}\n\n"
                "输出结构必须包括：\n"
                "1.我读取到的关键信息\n"
                "2.工作风格倾向\n"
                "3.AI协作成熟度\n"
                "4.当前成长风险\n"
                "5.推荐训练方式\n"
                "6.适合任务强度\n"
                "7.判断依据\n\n"
                "如果主观输入为空，不要编造用户需求。"
            )
            st.session_state.ai_profile_interpretation = optional_ai_text("AI画像解读", prompt, fallback)
            st.session_state.ai_profile_signature = signature
        if st.session_state.ai_profile_interpretation:
            current_profile = collect_profile()
            current_diagnosis = calculate_ai_diagnosis({key: st.session_state[key] for key in AI_QUESTIONS})
            current_signature = build_profile_input_signature(current_profile, current_diagnosis)
            if st.session_state.get("ai_profile_signature") != current_signature:
                st.info("画像信息已变更，请点击“重新生成AI画像解读”获取最新结果。")
            else:
                render_ai_output(st.session_state.ai_profile_interpretation)
    wizard_navigation(step)


def require_profile() -> bool:
    if st.session_state.profile and st.session_state.diagnosis:
        return True
    st.info("请先完成智能画像，或从首页选择“一键体验完整90天”。")
    if st.button("前往智能画像", type="primary"):
        navigate("智能画像")
        st.rerun()
    return False


def sync_task_statuses() -> None:
    for task in st.session_state.growth_plan:
        key = f"task_status_{task['id']}"
        override = st.session_state.task_status_overrides.pop(task["id"], None)
        if override:
            task["status"] = override
            st.session_state[key] = override
            continue
        evidence = latest_evidence(task["id"])
        if evidence:
            task["status"] = evidence["status"]
            st.session_state[key] = evidence["status"]
        elif st.session_state.demo_step > 0:
            st.session_state[key] = task["status"]
        elif key in st.session_state:
            task["status"] = st.session_state[key]


def render_radar_chart(capabilities: dict[str, int]) -> None:
    labels = list(capabilities)
    values = list(capabilities.values())
    figure = go.Figure()
    figure.add_trace(go.Scatterpolar(
        r=values + [values[0]], theta=labels + [labels[0]], fill="toself",
        line=dict(color="#5B8FF9", width=3), fillcolor="rgba(155,138,251,.20)",
        marker=dict(color="#9B8AFB", size=7), name="当前能力",
    ))
    figure.update_layout(
        height=390, margin=dict(l=35, r=35, t=35, b=25), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#273142"),
        polar=dict(
            bgcolor="#FFFDFB",
            radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="#E8EAF0", linecolor="#DDE1E8"),
            angularaxis=dict(gridcolor="#E8EAF0", linecolor="#DDE1E8"),
        ),
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def render_diagnosis_report() -> None:
    if not require_profile():
        return
    profile = st.session_state.profile
    diagnosis = st.session_state.diagnosis
    if "capabilities" not in diagnosis:
        diagnosis = enrich_diagnosis(profile, diagnosis)
        st.session_state.diagnosis = diagnosis

    st.markdown('<div class="section-title">AI成长策略与诊断报告</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">从岗位场景、AI能力、学习偏好和带教资源生成。诊断是成长策略输入，不是人才评价结论。</div>', unsafe_allow_html=True)
    top1, top2, top3, top4 = st.columns(4)
    top1.metric("新人", profile["nickname"])
    top2.metric("岗位", profile["secondary_role"])
    top3.metric("AI成熟度", diagnosis["maturity_level"])
    top4.metric("导师投入", f"{profile['mentor_hours']:g}小时/周")

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("### 能力雷达")
        render_radar_chart(diagnosis["capabilities"])
    with right:
        st.markdown("### 新人画像摘要")
        st.markdown(
            f"""
            <div class="glass">
              <div class="summary-grid">
                <div class="summary-item"><div class="summary-label">目标</div><div class="summary-value">{escape(profile['core_goal'])}</div></div>
                <div class="summary-item"><div class="summary-label">业务环境</div><div class="summary-value">{profile['business_stage']}·{profile['work_pace']}</div></div>
                <div class="summary-item"><div class="summary-label">真实项目</div><div class="summary-value">{profile['real_project']}</div></div>
                <div class="summary-item"><div class="summary-label">学习方式</div><div class="summary-value">{'、'.join(profile['learning_styles'])}</div></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(f'<div class="ai-note"><strong>AI协作成熟度</strong><br>{diagnosis["maturity_level"]}·{diagnosis["maturity_score"]}分。当前优先建立“提出好问题—验证AI结果—进入真实业务”的闭环。</div>', unsafe_allow_html=True)

    st.markdown("### 培养决策解释")
    cols = st.columns(4)
    cards = [
        ("当前优势", "；".join(diagnosis["strengths"])),
        ("核心能力差距", "；".join(diagnosis["gaps"])),
        ("推荐培养方式", diagnosis["recommended_method"]),
        ("导师带教强度", diagnosis["mentor_intensity"]),
    ]
    for col, (title, text) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="insight"><h4>{title}</h4><p>{escape(text)}</p></div>', unsafe_allow_html=True)

    st.markdown("### 90天风险点")
    for risk in diagnosis["risks"]:
        st.warning(risk)
    st.markdown("### AI诊断摘要")
    render_ai_mode_hint()
    render_ai_prereq_hint(
        "AI诊断摘要会依据这些画像信息生成：",
        [
            "已完成智能画像和成长目标确认。",
            "如内容不准确，请回到智能画像第2步修改“预期交付”。",
            "如主观目标变化，请回到第4步修改“主观成长问题”。",
            "如90天方向变化，请回到第5步修改“90天核心目标”后重新生成诊断。",
        ],
    )
    tone = st.radio("选择报告口吻", ["严肃导师版", "鼓励陪伴版", "HR汇报版"], horizontal=True, key="ai_diagnosis_tone")
    if st.button("AI解读我的诊断结果", key="generate_ai_diagnosis_summary"):
        if not profile_is_ready():
            clear_ai_output("ai_diagnosis_summary")
            st.warning("请先完成智能画像并生成成长策略。")
        else:
            capabilities = diagnosis["capabilities"]
            strengths = top_capabilities(capabilities, True, 2)
            gaps = top_capabilities(capabilities, False, 2)
            fallback = (
                f"优势：当前最稳的是{'、'.join(strengths)}，可以作为进入真实任务的起点。\n\n"
                f"短板：最需要补齐的是{'、'.join(gaps)}，建议用小任务验证而不是只补理论。\n\n"
                f"风险：未来30天最容易卡在证据不足、AI输出未核验或任务范围过大。\n\n"
                f"建议：围绕“{profile.get('expected_deliverable') or profile.get('core_goal')}”优先组合“1个真实业务观察+1次AI核验练习+1次导师校准”，口吻：{tone}。"
            )
            prompt = (
                f"画像：{profile}\n诊断：{diagnosis}\n报告口吻：{tone}\n"
                f"预期交付：{profile.get('expected_deliverable')}\n90天目标：{profile.get('core_goal')}\n"
                "请输出优势、短板、风险、建议四段。不要作正式人才评价。"
            )
            st.session_state.ai_diagnosis_summary = optional_ai_text("诊断报告解读", prompt, fallback, temperature=0.35)
    if st.session_state.ai_diagnosis_summary:
        render_ai_output(st.session_state.ai_diagnosis_summary)
    st.markdown('<div class="ai-note"><strong>AI使用安全提示</strong><br>任何个人隐私、账号密钥、未公开经营数据、商业机密、受限代码和未经授权的内部材料都不得输入AI。AI输出不能替代事实核验和业务责任。</div>', unsafe_allow_html=True)
    if st.session_state.demo_requested:
        st.info("你在画像中选择了自动演示。请先确认诊断结果，再进入90天演示。")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("查看90天成长地图", type="primary", width="stretch"):
            navigate("成长地图")
            st.rerun()
    with c2:
        if st.button("进入90天自动演示", width="stretch"):
            navigate("90天自动演示")
            st.rerun()


def stage_unlock_state(stage_index: int, plan: list[dict[str, Any]]) -> tuple[str, str]:
    demo_thresholds = [0, 3, 5, 8, 11]
    if st.session_state.demo_week >= demo_thresholds[stage_index] and st.session_state.demo_step > 0:
        return "active" if st.session_state.demo_week < (demo_thresholds[stage_index + 1] if stage_index < 4 else 13) else "unlocked", "已解锁"
    if stage_index == 0:
        return "active", "进行中"
    previous = [task for task in plan if task["stage"] == stage_index - 1]
    if previous and all(task["status"] == "已完成" for task in previous):
        return "active", "已解锁"
    return "locked", "待解锁"


def get_task(task_id: str) -> dict[str, Any] | None:
    return next((task for task in st.session_state.growth_plan if task["id"] == task_id), None)


def latest_evidence(task_id: str | None = None) -> dict[str, Any] | None:
    if task_id:
        records = st.session_state.evidence_records.get(task_id, [])
        return records[-1] if records else None
    records = [record for items in st.session_state.evidence_records.values() for record in items]
    return max(records, key=lambda item: item["submitted_at"], default=None)


def evidence_widget_keys(task_id: str) -> dict[str, str]:
    keys = {name: f"evidence_{task_id}_{name}" for name in ["outcome", "summary", "ai_work", "human", "verification", "problems", "self_score"]}
    defaults = {"outcome": "", "summary": "", "ai_work": "", "human": "", "verification": "", "problems": "", "self_score": 70}
    for name, key in keys.items():
        if key not in st.session_state:
            st.session_state[key] = defaults[name]
    return keys


def load_demo_evidence(task: dict[str, Any], supplement: bool = False) -> None:
    keys = evidence_widget_keys(task["id"])
    if supplement:
        values = {
            "outcome": "完成真实游戏活动或玩法方案第二版，补充目标玩家反馈、关键数据口径和方案取舍说明。",
            "summary": "模拟成果摘要：https://example.com/demo-v2；访谈5名目标玩家，核对近3期活动参与率和留存口径，补充两条反例证据。",
            "ai_work": "AI辅助归类访谈记录、检查方案结构并生成风险清单，没有代替业务结论。",
            "human": "本人判断玩家痛点、选择活动机制、确认资源取舍，并对最终方案和数据口径负责。",
            "verification": "逐条回看访谈原文，与数据同学核对指标口径，对AI总结抽样复核，并用反例检查结论。",
            "problems": "样本量仍有限，后续需要上线小流量验证。", "self_score": 88,
        }
    else:
        values = {
            "outcome": "完成一份结构完整的游戏活动策划方案初稿。",
            "summary": "模拟成果摘要：包含活动目标、玩法流程、奖励框架和排期，但暂未补充真实玩家反馈与数据口径。",
            "ai_work": "AI辅助生成方案结构、整理竞品玩法和润色表达。",
            "human": "本人选择活动主题并调整奖励结构，最终方案由本人确认。",
            "verification": "人工检查了方案结构，但尚未逐条核验AI来源和数据口径。",
            "problems": "真实用户证据不足，对AI整理的竞品结论核验不充分。", "self_score": 68,
        }
    for name, value in values.items():
        st.session_state[keys[name]] = value


def score_evidence(data: dict[str, Any]) -> dict[str, Any]:
    combined = " ".join(str(value) for value in data.values())
    evidence_signals = ["用户", "玩家", "数据", "反馈", "来源", "口径", "访谈", "日志", "链接", "反例"]
    verify_signals = ["核验", "来源", "对照", "数据", "人工", "事实", "抽样", "反例", "原文", "口径"]
    decision_signals = ["判断", "决策", "取舍", "选择", "负责", "确认", "风险", "优先级"]
    role_words = ROLE_BLUEPRINTS[st.session_state.profile["primary_role"]]
    role_signals = [role_words["object"], role_words["user"], role_words["data"], role_words["deliverable"]]
    safety_phrases = ["上传了未脱敏", "输入了内部数据", "输入了用户隐私", "输入了账号密钥", "上传商业机密", "未遵守安全"]
    safety_risk = any(phrase in combined for phrase in safety_phrases)
    business = clamp_score(38 + min(20, len(data["outcome"]) // 5) + sum(word in combined for word in role_signals) * 6 + data["self_score"] * .2)
    evidence = clamp_score(28 + min(22, len(data["summary"]) // 7) + min(32, sum(word in combined for word in evidence_signals) * 5) + (8 if "http" in data["summary"] else 0))
    ai_verify = clamp_score(24 + min(20, len(data["verification"]) // 5) + min(40, sum(word in data["verification"] for word in verify_signals) * 7) + min(10, len(data["ai_work"]) // 12))
    independent = clamp_score(30 + min(24, len(data["human"]) // 5) + min(28, sum(word in data["human"] for word in decision_signals) * 6) + data["self_score"] * .18)
    scores = {"业务相关性": business, "证据质量": evidence, "AI验证能力": ai_verify, "独立交付能力": independent}
    overall = round(sum(scores.values()) / len(scores))
    if safety_risk or overall < 60:
        conclusion = "需要导师介入"
    elif overall < 75:
        conclusion = "补充后通过"
    else:
        conclusion = "通过验收"
    missing = []
    if business < 75:
        missing.append("补充成果与真实业务目标、用户价值或岗位交付的对应关系")
    if evidence < 75:
        missing.append("补充用户反馈、数据口径、来源链接或反例证据")
    if ai_verify < 75:
        missing.append("说明如何逐条核验AI事实、数据和推测性结论")
    if independent < 75:
        missing.append("明确本人完成的判断、取舍和最终责任")
    if safety_risk:
        missing.insert(0, "立即停止使用相关材料并由导师确认AI安全风险")
    rule_next_action = missing[0] if missing else "将本次验证方法沉淀到个人AI协作手册。"
    next_action = optional_ai_enhance("生成补证建议", combined, rule_next_action)
    return {
        "scores": scores, "overall": overall, "conclusion": conclusion, "safety_risk": safety_risk,
        "met": [name for name, score in scores.items() if score >= 75],
        "missing": missing or ["当前证据完整，可进入成果复盘与方法沉淀。"],
        "next_action": next_action,
        "mentor_review": conclusion != "通过验收",
    }


def refresh_capabilities_from_evidence() -> None:
    records = [record for items in st.session_state.evidence_records.values() for record in items]
    if not records:
        return
    baseline = st.session_state.baseline_capabilities or st.session_state.diagnosis["capabilities"]
    best = {name: max(record["evaluation"]["scores"][name] for record in records) for name in ["业务相关性", "证据质量", "AI验证能力", "独立交付能力"]}
    st.session_state.latest_capabilities = {
        "业务理解": min(100, max(baseline["业务理解"], round(best["业务相关性"] * .75))),
        "AI协作": min(100, max(baseline["AI协作"], round(best["AI验证能力"] * .8))),
        "跨团队协作": max(baseline["跨团队协作"], st.session_state.growth_metrics.get("跨团队协作", baseline["跨团队协作"]) if st.session_state.demo_step else baseline["跨团队协作"]),
        "数据意识": min(100, max(baseline.get("数据意识", 30), round(best["证据质量"] * .8))),
        "独立交付": min(100, max(baseline["独立交付"], round(best["独立交付能力"] * .8))),
    }


def update_action_cards(source: str, evidence: dict[str, Any] | None = None, review: dict[str, Any] | None = None) -> None:
    risk = evidence["evaluation"]["conclusion"] if evidence else (review["risk"] if review else st.session_state.risk_level)
    missing = evidence["evaluation"]["missing"] if evidence else (review["delay"] if review else ["继续收集真实业务证据"])
    priorities = review["priorities"] if review else ([evidence["evaluation"]["next_action"], "完成当前核心任务", "与导师校准验收标准"] if evidence else ["推进当前任务", "补充业务证据", "记录AI验证过程"])
    task_name = evidence["task_name"] if evidence else "当前重点成果"
    mentor_question = optional_ai_enhance(
        "生成导师追问", f"任务：{task_name}\n风险：{risk}\n待补充：{missing[0]}",
        "哪些结论来自真实用户或数据，哪些仍是AI推测？",
    )
    st.session_state.action_cards = {
        "newcomer": {"title": "新人行动卡", "items": priorities[:3], "supplement": missing[0], "risk": risk, "ai": "让AI辅助整理与查漏，但事实、数据口径和最终结论必须人工验证。"},
        "mentor": {"title": "导师行动卡", "check": f"检查{task_name}的证据来源与人工判断", "ask": mentor_question, "accept": task_name, "scope": "证据不足时先缩小任务范围，不直接替新人完成。"},
        "hr": {"title": "HR信号卡", "signal": risk not in {"低", "通过验收"}, "type": "AI结果验证与真实业务证据", "level": "共性问题" if source == "review" else "个体信号", "support": "关注同类新人是否需要AI验证微课、脱敏任务池或导师容量支持。"},
    }


def submit_task_evidence(task: dict[str, Any], data: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    normalized = "|".join(str(data[key]).strip() for key in ["outcome", "summary", "ai_work", "human", "verification", "problems", "self_score"])
    signature = hashlib.sha256(f"{task['id']}|{normalized}".encode("utf-8")).hexdigest()
    if signature in st.session_state.evidence_signatures:
        return None, "同一成果证据已经提交并计分，请补充新内容后再提交。"
    evaluation = score_evidence(data)
    previous = latest_evidence(task["id"])
    st.session_state.evidence_counter += 1
    if evaluation["conclusion"] == "通过验收" and previous and previous["evaluation"]["conclusion"] != "通过验收":
        status = "待导师验收"
        evaluation["mentor_review"] = True
    elif evaluation["conclusion"] == "通过验收":
        status = "已完成"
    elif evaluation["conclusion"] == "补充后通过":
        status = "待补充"
    else:
        status = "待导师验收"
    record = {
        "id": f"evidence_{st.session_state.evidence_counter}", "task_id": task["id"], "task_name": task["name"],
        "submitted_at": datetime.now().isoformat(timespec="seconds"), "data": dict(data), "evaluation": evaluation,
        "status": status, "mentor_decision": None, "supplement_requirement": evaluation["next_action"],
    }
    st.session_state.evidence_records.setdefault(task["id"], []).append(record)
    st.session_state.evidence_signatures.append(signature)
    task["status"] = status
    st.session_state.task_status_overrides[task["id"]] = status
    refresh_capabilities_from_evidence()
    update_action_cards("evidence", evidence=record)
    return record, None


def render_evidence_evaluation(record: dict[str, Any]) -> None:
    evaluation = record["evaluation"]
    st.markdown("#### 智能规则评价")
    columns = st.columns(5)
    for column, (name, score) in zip(columns[:4], evaluation["scores"].items()):
        column.markdown(f'<div class="score-card"><div>{escape(name)}</div><div class="score-number">{score}</div></div>', unsafe_allow_html=True)
    columns[4].metric("综合评分", evaluation["overall"])
    status_class = "status-pass" if evaluation["conclusion"] == "通过验收" else "status-supplement" if evaluation["conclusion"] == "补充后通过" else "status-mentor"
    st.markdown(f'<div class="{status_class}"><strong>{escape(evaluation["conclusion"])}</strong><br>当前任务状态：{escape(record["status"])}。AI评价仅用于成长辅助，最终评价由导师和HR确认。</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        st.markdown("**已达到要求**")
        for item in evaluation["met"] or ["暂未有维度达到75分"]:
            st.markdown(f"- {item}")
    with right:
        st.markdown("**需要补充的证据**")
        for item in evaluation["missing"]:
            st.markdown(f"- {item}")
    st.markdown(f"**下一次改进动作**：{evaluation['next_action']}")
    st.markdown(f"**是否需要导师复核**：{'需要' if evaluation['mentor_review'] else '暂不需要'}")
    with st.expander("查看评分依据"):
        st.markdown(
            "- **业务相关性**：检查成果是否对应岗位交付、真实业务目标、目标用户和关键业务数据。\n"
            "- **证据质量**：检查是否提供用户反馈、数据口径、来源链接、访谈记录、日志或反例。\n"
            "- **AI验证能力**：检查是否说明人工核验、来源对照、事实检查、抽样复核和反例验证。\n"
            "- **独立交付能力**：检查本人是否完成关键判断、取舍、优先级选择并承担最终责任。\n"
            "- **安全红线**：出现未脱敏内部数据、用户隐私、账号密钥或商业机密输入AI等描述时，直接触发导师介入。\n"
            "- 当前评价是本地模拟规则评价，不是正式人才评价；最终结论由导师和HR确认。"
        )


def render_task_evidence(task: dict[str, Any]) -> None:
    keys = evidence_widget_keys(task["id"])
    latest = latest_evidence(task["id"])
    st.markdown('<div class="evidence-shell"><strong>提交成长证据</strong><br>正式成长状态主要由证据验收结果更新；文本、链接和模拟示例均可使用。</div>', unsafe_allow_html=True)
    demo_left, demo_right = st.columns(2)
    with demo_left:
        if st.button("加载模拟成果", key=f"load_evidence_{task['id']}", width="stretch"):
            load_demo_evidence(task)
            st.rerun()
    with demo_right:
        if latest and latest["status"] in {"待补充", "待导师验收"} and st.button("加载模拟补证", key=f"load_supplement_{task['id']}", width="stretch"):
            load_demo_evidence(task, supplement=True)
            st.rerun()
    with st.form(f"evidence_form_{task['id']}"):
        left, right = st.columns(2)
        with left:
            st.text_area("本次完成的成果*", key=keys["outcome"])
            st.text_area("成果链接或成果摘要*", key=keys["summary"])
            st.text_area("使用AI完成了哪些工作*", key=keys["ai_work"])
        with right:
            st.text_area("哪些内容由本人判断和决策*", key=keys["human"])
            st.text_area("如何验证AI输出*", key=keys["verification"])
            st.text_area("遇到的主要问题", key=keys["problems"])
            st.slider("自评完成度", 0, 100, key=keys["self_score"])
        submitted = st.form_submit_button("提交证据并评价", type="primary", width="stretch")
    if submitted:
        data = {name: st.session_state[key] for name, key in keys.items()}
        required = [data[name].strip() for name in ["outcome", "summary", "ai_work", "human", "verification"]]
        if not all(required):
            st.warning("请完整填写成果、成果摘要、人机分工和AI验证方式。")
        else:
            _, error = submit_task_evidence(task, data)
            if error:
                st.warning(error)
            else:
                st.rerun()
    latest = latest_evidence(task["id"])
    if latest:
        render_evidence_evaluation(latest)


def evaluate_growth_gates() -> dict[str, dict[str, Any]]:
    plan = st.session_state.growth_plan
    latest_records = [records[-1] for records in st.session_state.evidence_records.values() if records]
    valid_records = [
        record for record in latest_records
        if not record["evaluation"]["safety_risk"]
        and (record["status"] == "已完成" or record.get("mentor_decision") == "通过验收")
    ]
    no_high_safety_risk = not any(record["evaluation"]["safety_risk"] for record in latest_records)

    def task_done(*keywords: str) -> bool:
        return any(task["status"] == "已完成" and any(keyword in task["name"] for keyword in keywords) for task in plan)

    cross_team_done = task_done("跨团队", "共创", "走查")
    real_delivery_evidence = any((get_task(record["task_id"]) or {}).get("stage", 0) >= 3 for record in valid_records)
    mentor_expanded = any(decision["decision"] == "通过验收" for decision in st.session_state.mentor_decisions) or st.session_state.demo_week >= 9
    quality_scores = [record["evaluation"]["scores"]["证据质量"] for record in valid_records]
    independent_scores = [record["evaluation"]["scores"]["独立交付能力"] for record in valid_records]
    gates = {
        "30天闸门": {
            "subtitle": "完成适应", "color": "#69C0FF", "soft": "#EAF3FF",
            "conditions": {
                "完成组织和业务地图": task_done("业务与协作地图", "业务地图"),
                "完成AI安全基线": task_done("AI协作基本功", "AI安全"),
                "至少提交2项有效成长证据": len(valid_records) >= 2,
                "没有高风险安全问题": no_high_safety_risk,
            },
            "adjustment": "优先补齐组织理解、AI安全和两项可验证成果，再扩大任务范围。",
        },
        "60天闸门": {
            "subtitle": "形成贡献", "color": "#9B8AFB", "soft": "#F1EDFF",
            "conditions": {
                "完成至少1项跨团队任务": cross_team_done,
                "完成至少1项真实业务成果": real_delivery_evidence,
                "证据质量达到合格标准": bool(quality_scores) and max(quality_scores) >= 60,
                "导师确认可以扩大独立工作范围": mentor_expanded,
            },
            "adjustment": "缩小真实任务范围，补充协作方反馈，并由导师确认下一步独立边界。",
        },
        "90天闸门": {
            "subtitle": "独立交付", "color": "#FF7EB6", "soft": "#FFF0F6",
            "conditions": {
                "完成核心业务交付": task_done("独立起草", "核心业务交付"),
                "完成跨职能评审": task_done("跨职能成果评审", "跨职能评审"),
                "完成AI协作手册": task_done("AI协作手册"),
                "独立交付能力达到目标水平": bool(independent_scores) and max(independent_scores) >= 75,
            },
            "adjustment": "针对未通过项安排补证、复评或缩小范围后的真实交付，不以展示材料替代能力验证。",
        },
    }
    for gate in gates.values():
        gate["passed"] = all(gate["conditions"].values())
        gate["met"] = [name for name, met in gate["conditions"].items() if met]
        gate["unmet"] = [name for name, met in gate["conditions"].items() if not met]
    st.session_state.gate_results = gates
    return gates


def render_growth_gates() -> None:
    gates = evaluate_growth_gates()
    html = '<div class="gate-grid">'
    for name, gate in gates.items():
        met = "".join(f"✓ {escape(item)}<br>" for item in gate["met"]) or "暂无已满足条件<br>"
        unmet = "".join(f"○ {escape(item)}<br>" for item in gate["unmet"]) or "全部条件已满足<br>"
        state = "已通过" if gate["passed"] else "验证中"
        html += f'''<div class="gate-card" style="--gate-color:{gate['color']};--gate-soft:{gate['soft']}">
        <div class="gate-title">{escape(name)}·{escape(gate['subtitle'])}</div><span class="gate-state">{state}</span>
        <div class="gate-list"><strong>已满足</strong><br>{met}<br><strong>未满足</strong><br>{unmet}</div>
        <div class="gate-list"><strong>调整建议</strong><br>{escape(gate['adjustment'])}</div></div>'''
    st.markdown(html + "</div>", unsafe_allow_html=True)


def build_growth_report_markdown() -> str:
    profile = st.session_state.profile
    gates = evaluate_growth_gates()
    lines = [
        f"# {profile['nickname']}的90天成长报告", "", "> 本报告由本地规则引擎生成，用于成长辅助，最终评价由导师和HR确认。", "",
        "## 画像与目标", f"- 岗位：{profile['primary_role']}·{profile['secondary_role']}", f"- 90天目标：{profile['core_goal']}",
        f"- 任务强度：{profile['task_intensity']}", "", "## 成长任务",
    ]
    for task in st.session_state.growth_plan:
        evidence = latest_evidence(task["id"])
        evidence_text = f"；证据评价{evidence['evaluation']['overall']}分·{evidence['evaluation']['conclusion']}" if evidence else "；尚未提交证据"
        lines.append(f"- [{task['status']}] {task['name']}（{task.get('task_type', '必修任务')}，{task['xp']}经验值{evidence_text}）")
    lines.extend(["", "## 30—60—90阶段闸门"])
    for name, gate in gates.items():
        lines.append(f"### {name}·{gate['subtitle']}：{'已通过' if gate['passed'] else '验证中'}")
        lines.append(f"- 已满足：{'、'.join(gate['met']) or '暂无'}")
        lines.append(f"- 未满足：{'、'.join(gate['unmet']) or '无'}")
        lines.append(f"- 调整建议：{gate['adjustment']}")
    records = [record for items in st.session_state.evidence_records.values() for record in items]
    lines.extend(["", "## 成长证据链"])
    for record in records:
        lines.append(f"- {record['task_name']}：{record['evaluation']['overall']}分·{record['status']}；{record['data']['summary']}")
    if not records:
        lines.append("- 尚未提交成长证据。")
    return "\n".join(lines)


def build_review_markdown() -> str:
    if not st.session_state.reviews:
        return "# 每周复盘\n\n尚未提交复盘。"
    review = st.session_state.reviews[-1]
    result = review["result"]
    lines = [f"# 第{review['input']['week']}周成长复盘", "", f"- 风险等级：{result['risk']}", f"- 成长总结：{result['summary']}", "", "## 下周优先任务"]
    lines.extend(f"{index}. {item}" for index, item in enumerate(result["priorities"], 1))
    lines.extend(["", "## 导师建议", result["mentor"], "", "## 调整原因", result["reason"]])
    return "\n".join(lines)


def build_mentor_card_markdown() -> str:
    card = st.session_state.action_cards.get("mentor") or {}
    if not card:
        return "# 导师一对一沟通卡\n\n尚未形成复盘或证据评价。"
    return "\n".join([
        "# 导师一对一沟通卡", "", f"- 本周检查：{card['check']}", f"- 建议追问：{card['ask']}",
        f"- 待验收成果：{card['accept']}", f"- 任务范围建议：{card['scope']}", "", "> AI负责整理信号，导师负责判断、追问与最终验收。",
    ])


def build_hr_brief_csv(data: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["新人", "岗位族", "成长进度", "AI成熟度", "风险", "导师", "主要障碍", "当前阶段"])
    writer.writeheader()
    for item in data:
        writer.writerow({key: item[key] for key in writer.fieldnames})
    return output.getvalue()


def render_task_detail(task: dict[str, Any]) -> None:
    key = f"task_status_{task['id']}"
    if key not in st.session_state:
        st.session_state[key] = task["status"]
    st.selectbox("完成状态（模拟手动控制）", TASK_STATUSES, key=key)
    task["status"] = st.session_state[key]
    st.markdown(f"**任务目的**  \n{task['purpose']}")
    st.markdown(f"**具体行动**  \n{task['action']}")
    st.markdown(
        f"""
        <div class="boundary-grid">
          <div class="boundary"><strong>人负责什么</strong>{escape(task['human'])}</div>
          <div class="boundary"><strong>AI负责什么</strong>{escape(task['ai'])}</div>
          <div class="boundary"><strong>必须人工验证</strong>{escape(task['verify'])}</div>
          <div class="boundary"><strong>不得输入AI</strong>{escape(task['forbidden'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**交付成果**  \n{task['deliverable']}")
    c2.markdown(f"**验收标准**  \n{task['criteria']}")
    c3.markdown(f"**预计用时与奖励**  \n{task['hours']}小时·{task['xp']}经验值")
    render_task_evidence(task)


def render_growth_map() -> None:
    if not require_profile():
        return
    sync_task_statuses()
    profile = st.session_state.profile
    plan = st.session_state.growth_plan
    completed = sum(task["status"] == "已完成" for task in plan)
    earned_xp = sum(task["xp"] for task in plan if task["status"] == "已完成")
    total_xp = sum(task["xp"] for task in plan)
    st.markdown('<div class="section-title">30—60—90天成长世界地图</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{escape(profile["nickname"])}的核心目标：{escape(profile["core_goal"])}</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("任务进度", f"{completed}/{len(plan)}")
    m2.metric("当前经验值", f"{earned_xp}")
    m3.metric("总经验值", f"{total_xp}")
    m4.metric("自动调整", "已开启" if profile["auto_adjust"] else "需确认")
    st.progress(completed / len(plan), text=f"整体成长进度{completed / len(plan):.0%}")
    type_counts = {task_type: sum(task.get("task_type", "必修任务") == task_type for task in plan) for task_type in ["必修任务", "选修任务", "挑战任务"]}
    dynamic_count = sum(bool(task.get("dynamic")) for task in plan)
    st.caption(
        f"任务结构：必修{type_counts['必修任务']}项·选修{type_counts['选修任务']}项·挑战{type_counts['挑战任务']}项"
        + (f"·动态调整{dynamic_count}项" if dynamic_count else "")
    )
    st.markdown("### 30—60—90阶段闸门")
    render_growth_gates()
    st.download_button(
        "导出个人90天成长报告（Markdown）", build_growth_report_markdown(),
        file_name=f"{profile['nickname']}_90天成长报告.md", mime="text/markdown", key="download_growth_report",
    )
    with st.expander("AI任务配置器", expanded=False):
        render_ai_mode_hint()
        render_ai_prereq_hint(
            "AI任务配置器需要这些排序依据：",
            [
                "至少填写“当前最紧急业务任务”。",
                "或至少填写“最担心的能力短板”。",
                "本周可投入时间会用于判断任务难度和导师介入建议。",
            ],
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            weekly_hours = st.number_input("本周可投入时间", min_value=1, max_value=40, value=int(profile.get("weekly_growth_hours", 6)), key="ai_growth_hours")
        with c2:
            urgent_task = st.text_input("当前最紧急业务任务", key="ai_growth_urgent")
        with c3:
            weak_spot = st.text_input("最担心的能力短板", key="ai_growth_weak")
        if st.button("AI调整本周成长路径", key="generate_ai_growth_config"):
            if not has_text(urgent_task, weak_spot):
                clear_ai_output("ai_growth_config")
                st.warning("请先补充排序依据，再生成本周成长路径调整建议。")
                render_ai_prereq_hint(
                    "请至少补充以下任意一项：",
                    [
                        "当前最紧急业务任务。",
                        "最担心的能力短板。",
                    ],
                )
            else:
                open_tasks = [task for task in plan if task["status"] not in {"已完成"}]
                priority_tasks = open_tasks[:2]
                delayed_task = open_tasks[2]["name"] if len(open_tasks) > 2 else "暂无需要推迟的任务"
                mentor_needed = "是" if weekly_hours <= 4 or "信心" in weak_spot or "核验" in weak_spot else "建议轻量校准"
                fallback = (
                    f"建议优先做：1.{priority_tasks[0]['name'] if priority_tasks else '提交一项成长证据'}；"
                    f"2.{priority_tasks[1]['name'] if len(priority_tasks) > 1 else '完成AI结果核验清单'}。\n\n"
                    f"可以推迟：{delayed_task}。\n\n"
                    f"是否需要导师介入：{mentor_needed}。\n\n"
                    f"排序原因：本周可投入{weekly_hours}小时，需先围绕“{urgent_task or profile['core_goal']}”形成可验证成果，再处理“{weak_spot or 'AI结果验证'}”。\n\n"
                    "任务难度：中。"
                )
                prompt = (
                    f"画像：{profile}\n未完成任务：{open_tasks[:6]}\n本周时间：{weekly_hours}\n"
                    f"当前最紧急业务任务：{urgent_task}\n最担心的能力短板：{weak_spot}\n"
                    "请给出本周2个优先任务、1个可推迟任务、导师介入建议、排序原因和难度。"
                )
                st.session_state.ai_growth_config = {
                    "text": optional_ai_text("AI任务配置器", prompt, fallback),
                    "accepted": False,
                }
        if st.session_state.ai_growth_config:
            render_ai_output(st.session_state.ai_growth_config["text"])
            a1, a2 = st.columns(2)
            with a1:
                if st.button("采纳为本周建议", key="accept_ai_growth_config"):
                    st.session_state.ai_growth_config["accepted"] = True
                    st.success("已保存为本周建议，原成长计划未被直接覆盖。")
            with a2:
                if st.button("仅保存为参考", key="save_ai_growth_config"):
                    st.info("已保留为参考建议，后续仍以原计划和导师确认为准。")

    node_html = '<div class="world-map">'
    for index, stage in enumerate(STAGE_DEFINITIONS):
        css_state, status = stage_unlock_state(index, plan)
        stage_tasks = [task for task in plan if task["stage"] == index]
        stage_xp = sum(task["xp"] for task in stage_tasks)
        completed_stage = stage_tasks and all(task["status"] == "已完成" for task in stage_tasks)
        node_mark = "✓" if completed_stage else str(index + 1)
        node_html += f"""
        <div class="world-node {css_state}" style="--node-color:{STAGE_COLORS[index]};--node-soft:{STAGE_SOFT_COLORS[index]}">
          <span class="node-index">{node_mark}</span><span class="node-status">{status}</span>
          <div class="node-title">{stage['name']}</div><div class="node-range">{stage['range']}</div>
          <div class="node-goal">{stage['goal']}</div><div class="node-xp">能力奖励·{stage_xp}经验值</div>
        </div>"""
    st.markdown(node_html + "</div>", unsafe_allow_html=True)

    for index, stage in enumerate(STAGE_DEFINITIONS):
        stage_tasks = [task for task in plan if task["stage"] == index]
        _, status = stage_unlock_state(index, plan)
        with st.expander(f"{index + 1}. {stage['name']}｜{stage['goal']}｜{status}", expanded=index == 0):
            st.markdown(f"**导师检查点**：{stage_tasks[0]['mentor_checkpoint'] if stage_tasks else '确认阶段成果'}")
            st.markdown(f"**风险事件**：{stage_tasks[0]['risk_event'] if stage_tasks else '暂无'}")
            for task in stage_tasks:
                task_type = task.get("task_type", "必修任务")
                dynamic_badge = " · 动态调整任务" if task.get("dynamic") else ""
                st.markdown(f"#### {task['name']} · {task_type}{dynamic_badge} · +{task['xp']}经验值 · 奖励{task['skill_reward']}")
                render_task_detail(task)
                st.divider()


def reset_demo() -> None:
    st.session_state.demo_step = 0
    st.session_state.demo_week = 0
    st.session_state.demo_running = False
    st.session_state.demo_speed = 1
    st.session_state.demo_tick = 0
    st.session_state.current_event = "等待开始"
    st.session_state.demo_adjustment = "等待系统生成成长策略。"
    st.session_state.growth_metrics = {"XP": 0, "业务理解": 25, "AI协作": 30, "跨团队协作": 20, "独立交付": 15}
    st.session_state.risk_level = "低"
    st.session_state.mentor_triggered = False
    st.session_state.demo_history = []
    st.session_state.evidence_records = {}
    st.session_state.evidence_signatures = []
    st.session_state.evidence_counter = 0
    st.session_state.mentor_decisions = []
    st.session_state.gate_results = {}
    st.session_state.action_cards = {"newcomer": {}, "mentor": {}, "hr": {}}
    st.session_state.task_status_overrides = {}
    st.session_state.demo_evidence_stage = "未提交"
    st.session_state.demo_evidence_task_id = None
    st.session_state.latest_capabilities = None
    st.session_state.pending_adjustment = None
    st.session_state.reviews = []
    st.session_state.dynamic_task_counter = 0
    st.session_state.llm_hr_brief = None
    if st.session_state.profile and st.session_state.diagnosis:
        st.session_state.growth_plan = generate_personalized_plan(st.session_state.profile, st.session_state.diagnosis)
    else:
        st.session_state.growth_plan = []
    for task in st.session_state.growth_plan:
        st.session_state[f"task_status_{task['id']}"] = "未开始"


def apply_demo_evidence_action(action: str) -> None:
    target = next((task for task in st.session_state.growth_plan if "独立起草" in task["name"]), st.session_state.growth_plan[min(6, len(st.session_state.growth_plan) - 1)])
    st.session_state.demo_evidence_task_id = target["id"]
    if action == "foundation":
        for task in st.session_state.growth_plan[:2]:
            data = {
                "outcome": f"完成{task['name']}并形成可复用清单，明确游戏活动或玩法方案、目标玩家、参与留存付费数据与可评审的游戏策划方案之间的关系。", "summary": "模拟成果摘要：https://example.com/foundation；包含目标玩家访谈原文、数据口径、来源链接、反例和安全检查结果。",
                "ai_work": "AI辅助整理访谈记录、检查遗漏和生成清单初稿。", "human": "本人确认业务流程、判断责任边界、核对安全要求并对最终内容负责。",
                "verification": "逐条对照原始访谈、用户反馈、数据口径和制度公开信息，人工抽样核验AI来源、事实、推测与安全边界，并记录反例。",
                "problems": "首次整理信息较多，后续需要持续更新。", "self_score": 86,
            }
            submit_task_evidence(task, data)
        st.session_state.demo_evidence_task_id = None
    elif action == "cross_team":
        task = next((item for item in st.session_state.growth_plan if "共创" in item["name"]), st.session_state.growth_plan[4])
        data = {
            "outcome": "完成一次跨团队游戏活动或玩法方案共创和走查，围绕目标玩家、参与留存付费数据形成可评审的游戏策划方案。", "summary": "模拟成果摘要：https://example.com/collaboration；记录运营、程序和策划的用户反馈、数据口径、责任清单、变更来源与反例。",
            "ai_work": "AI辅助归类分歧、整理会议纪要和检查遗漏。", "human": "本人判断优先级、协调取舍、确认责任人并对方案结论负责。",
            "verification": "会后由各协作方逐条确认纪要，对照用户原始反馈和数据口径，人工抽样核验AI来源、事实与总结，并保留反例和未决事项。",
            "problems": "部分资源排期仍需后续确认。", "self_score": 82,
        }
        submit_task_evidence(task, data)
        st.session_state.demo_evidence_task_id = None
    elif action in {"initial", "supplement"}:
        load_demo_evidence(target, supplement=action == "supplement")
        keys = evidence_widget_keys(target["id"])
        data = {name: st.session_state[key] for name, key in keys.items()}
        record, _ = submit_task_evidence(target, data)
        if record:
            st.session_state.demo_evidence_stage = "待补充" if action == "initial" else "待导师验收"
    elif action == "mentor_return":
        record = latest_evidence(target["id"])
        if record and not record.get("mentor_decision"):
            apply_mentor_decision(record, "退回补充")
        st.session_state.demo_evidence_stage = "导师已退回"
    elif action == "mentor_pass":
        record = latest_evidence(target["id"])
        if record and record.get("mentor_decision") != "通过验收":
            apply_mentor_decision(record, "通过验收")
        st.session_state.demo_evidence_stage = "补充后通过"


def apply_demo_event(event_index: int) -> None:
    if event_index >= len(DEMO_EVENTS):
        st.session_state.demo_running = False
        return
    event = DEMO_EVENTS[event_index]
    st.session_state.demo_step = event_index + 1
    st.session_state.demo_week = event["week"]
    st.session_state.current_event = event.get("title", "未命名事件")
    st.session_state.demo_adjustment = event["adjustment"]
    st.session_state.risk_level = event["risk"]
    st.session_state.mentor_triggered = event["mentor"]
    st.session_state.growth_metrics = {"XP": event["xp"], **event["metrics"]}
    st.session_state.demo_history = list(range(event_index + 1))
    for task_index, status in event.get("task_updates", {}).items():
        if task_index < len(st.session_state.growth_plan):
            task = st.session_state.growth_plan[task_index]
            task["status"] = status
            st.session_state[f"task_status_{task['id']}"] = status
            st.session_state.task_status_overrides[task["id"]] = status
    if event.get("evidence_action"):
        apply_demo_evidence_action(event["evidence_action"])
    if event.get("complete_all"):
        for task in st.session_state.growth_plan:
            task["status"] = "已完成"
            st.session_state[f"task_status_{task['id']}"] = "已完成"
        st.session_state.demo_running = False


def advance_demo() -> None:
    apply_demo_event(st.session_state.demo_step)


def render_demo_timeline() -> None:
    html = '<div class="glass">'
    current_index = st.session_state.demo_step - 1
    for index, event in enumerate(DEMO_EVENTS):
        state = "done" if index < current_index else "current" if index == current_index else ""
        html += f"""
        <div class="timeline-row">
          <div class="timeline-week">第{event['week']}周</div>
          <div class="timeline-dot {state}"></div>
          <div class="timeline-text {state}">{event.get('title', '未命名事件')}</div>
        </div>"""
    st.markdown(html + "</div>", unsafe_allow_html=True)


def _render_demo_player() -> None:
    controls = st.columns([1, 1, 1, 1, 1, 1.3])
    with controls[0]:
        if st.button("开始", type="primary", width="stretch"):
            if st.session_state.demo_step >= len(DEMO_EVENTS):
                reset_demo()
            st.session_state.demo_running = True
            advance_demo()
    with controls[1]:
        if st.button("暂停", width="stretch"):
            st.session_state.demo_running = False
    with controls[2]:
        if st.button("继续", width="stretch"):
            if st.session_state.demo_step < len(DEMO_EVENTS):
                st.session_state.demo_running = True
    with controls[3]:
        if st.button("播放下一幕", width="stretch"):
            st.session_state.demo_running = False
            advance_demo()
    with controls[4]:
        if st.button("加速", width="stretch"):
            st.session_state.demo_speed = {1: 2, 2: 4, 4: 1}[st.session_state.demo_speed]
    with controls[5]:
        if st.button("重置", width="stretch"):
            reset_demo()

    if st.session_state.demo_running and st.session_state.demo_step < len(DEMO_EVENTS):
        st.session_state.demo_tick += 1
        threshold = 2 if st.session_state.demo_speed == 1 else 1
        if st.session_state.demo_tick >= threshold:
            steps = 2 if st.session_state.demo_speed == 4 else 1
            for _ in range(steps):
                if st.session_state.demo_step < len(DEMO_EVENTS):
                    advance_demo()
            st.session_state.demo_tick = 0

    st.caption(f"播放状态：{'自动播放中' if st.session_state.demo_running else '已暂停'}｜速度：{st.session_state.demo_speed}×｜进度：{st.session_state.demo_step}/{len(DEMO_EVENTS)}")
    current_index = max(0, st.session_state.demo_step - 1)
    event = DEMO_EVENTS[current_index] if st.session_state.demo_step else {
        "week": 0, "title": "等待开始", "detail": "点击“开始”自动连续播放，或点击“播放下一幕”逐步讲解。"
    }
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown(
            f"""
            <div class="event-hero">
              <div class="event-week">WEEK {event['week']:02d}</div>
              <div class="event-title">{event.get('title', '未命名事件')}</div>
              <div class="event-detail">{event['detail']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        metrics = st.session_state.growth_metrics
        row1 = st.columns(5)
        row1[0].metric("经验值", metrics["XP"])
        row1[1].metric("业务理解", metrics["业务理解"])
        row1[2].metric("AI协作", metrics["AI协作"])
        row1[3].metric("跨团队协作", metrics["跨团队协作"])
        row1[4].metric("独立交付", metrics["独立交付"])
        risk_class = {"低": "risk-low", "中": "risk-medium", "高": "risk-high"}[st.session_state.risk_level]
        st.markdown(
            f"""
            <div class="decision-card">
              <strong>智能规则调整说明</strong><br>{escape(st.session_state.demo_adjustment)}<br><br>
              风险等级：<span class="{risk_class}">{st.session_state.risk_level}</span>　
              导师介入：<strong>{'需要' if st.session_state.mentor_triggered else '暂不需要'}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        evidence = latest_evidence(st.session_state.demo_evidence_task_id)
        if evidence:
            evaluation = evidence["evaluation"]
            score_text = " · ".join(f"{name}{score}" for name, score in evaluation["scores"].items())
            evidence_class = "status-pass" if evidence["status"] == "已完成" else "status-supplement" if evidence["status"] == "待补充" else "status-mentor"
            st.markdown(
                f'<div class="{evidence_class}"><strong>成长证据链·{escape(st.session_state.demo_evidence_stage)}</strong><br>'
                f'{escape(evidence["task_name"])}｜综合{evaluation["overall"]}分<br>{escape(score_text)}<br>'
                f'补证要求：{escape(evidence["supplement_requirement"])}</div>', unsafe_allow_html=True,
            )
        st.markdown('<div class="ai-note"><strong>协同原则</strong><br>AI提供监测和建议，导师确认风险判断与带教动作，新人对工作成果和最终决策负责。</div>', unsafe_allow_html=True)
    with right:
        st.markdown("### 关键事件时间线")
        render_demo_timeline()

    if st.session_state.demo_step >= len(DEMO_EVENTS):
        st.success("90天自动演示完成。新人已完成成果答辩和个人AI协作手册。")
        st.session_state.demo_running = False


if hasattr(st, "fragment"):
    render_demo_player = st.fragment(run_every=0.6)(_render_demo_player)
else:
    render_demo_player = _render_demo_player


def render_auto_demo() -> None:
    if not st.session_state.profile:
        initialize_demo_profile()
    render_demo_disclaimer()
    st.markdown('<div class="section-title">90天自动演示</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">通过{len(DEMO_EVENTS)}个关键事件展示系统如何监测成长、评价证据、调整任务、触发导师介入并形成组织信号。</div>', unsafe_allow_html=True)
    render_ai_prereq_hint(
        "生成AI旁白前，请先完成：",
        [
            "点击“随机生成一次90天成长剧本”。",
            "确认本轮随机剧本已显示在页面中。",
            "系统会结合随机剧本和当前演示事件生成旁白。",
        ],
    )
    if st.button("随机生成一次90天成长剧本", key="randomize_demo_script"):
        seed = random.randint(1000, 999999)
        rng = random.Random(seed)
        st.session_state.demo_random_seed = seed
        st.session_state.demo_random_script = {
            "临时项目冲突": rng.choice(["运营活动提前上线", "版本排期压缩", "竞品突发动作需要快速分析"]),
            "导师可用性": rng.choice(["导师本周可用30分钟", "导师临时参加评审", "导师只能异步反馈"]),
            "任务延期": rng.choice(["竞品分析延期", "用户访谈延期", "数据口径确认延期"]),
            "AI误判风险": rng.choice(["把相关性误判为因果", "引用无来源玩家数据", "忽略敏感信息边界"]),
            "跨团队协作事件": rng.choice(["程序要求缩小范围", "美术资源被抽调", "运营担心规则过复杂"]),
        }
        st.session_state.ai_demo_narration = ""
        st.rerun()
    if st.session_state.demo_random_script:
        render_ai_mode_hint()
        script = st.session_state.demo_random_script
        st.markdown(
            '<div class="glass"><strong>本轮随机成长剧本</strong><br>'
            + "｜".join(f"{escape(k)}：{escape(v)}" for k, v in script.items())
            + f'<br><span style="color:#667085">随机种子：{st.session_state.demo_random_seed}</span></div>',
            unsafe_allow_html=True,
        )
        if st.button("生成AI旁白", key="generate_demo_narration"):
            if not st.session_state.demo_random_script:
                clear_ai_output("ai_demo_narration")
                st.warning("请先生成随机剧本，再生成AI旁白。")
                render_ai_prereq_hint(
                    "AI旁白需要以下前置内容：",
                    [
                        "本轮90天随机成长剧本。",
                        "当前自动演示事件。",
                        "系统调整说明。",
                    ],
                )
            else:
                event = DEMO_EVENTS[min(st.session_state.demo_step, len(DEMO_EVENTS) - 1)]
                event_title = event.get("title", "当前事件")
                event_detail = event.get("detail", "")
                event_adjustment = event.get("adjustment", "")
                fallback = (
                    f"当前发生了：{event_title}。{event_detail}"
                    f"系统调整逻辑：{event_adjustment}"
                    "新人应先明确最小交付物，核验AI输出来源，再向导师同步需要决策的风险。"
                )
                prompt = (
                    f"当前事件标题：{event_title}\n"
                    f"事件详情：{event_detail}\n"
                    f"系统调整：{event_adjustment}\n"
                    f"随机剧本：{script}\n"
                    "请生成当前发生了什么、为什么这样调整、新人如何应对三段旁白。"
                )
                st.session_state.ai_demo_narration = optional_ai_text("90天自动演示AI旁白", prompt, fallback)
        if st.session_state.ai_demo_narration:
            render_ai_output(st.session_state.ai_demo_narration)
    if not hasattr(st, "fragment"):
        st.info("当前Streamlit版本不支持片段级自动刷新，请使用“播放下一幕”完成稳定演示。")
    render_demo_player()


def load_demo_review() -> None:
    names = [task["name"] for task in st.session_state.growth_plan]
    ai_task = next((name for name in names if "AI协作基本功" in name), names[0] if names else "AI基础学习")
    competitor_task = next((name for name in names if "竞品" in name), names[1] if len(names) > 1 else "竞品分析")
    st.session_state.review_week = 3
    st.session_state.review_completed = [ai_task]
    st.session_state.review_unfinished = [competitor_task]
    st.session_state.review_difficulty = "临时业务安排占用了学习时间，对独立开展真实业务仍缺乏信心。"
    st.session_state.review_output = "完成AI基础学习和提示词、安全边界练习记录。"
    st.session_state.review_confidence = 2
    st.session_state.review_hours = 6


def generate_review_result(data: dict[str, Any]) -> dict[str, Any]:
    text = data["difficulty"] + " " + " ".join(data["unfinished"])
    is_fixed_demo = (
        st.session_state.profile
        and st.session_state.profile["nickname"] == "小鹅"
        and any("AI协作基本功" in item or "AI基础" in item for item in data["completed"])
        and ("竞品" in text or "临时业务" in text)
    )
    if is_fixed_demo:
        return {
            "summary": "本周已完成AI基础学习并形成初步协作方法，但临时业务安排影响原计划，竞品任务尚未完成。新人对独立开展真实业务仍缺乏信心。",
            "risk": "中",
            "keep": ["保留AI提示词与安全检查清单，并在真实任务中复用。"],
            "delay": ["将竞品与用户证据分析延期到下周，收敛为1个深度案例。"],
            "add": ["新增低难度真实业务任务：用AI辅助整理一页玩家反馈摘要，结论由新人核验。"],
            "priorities": ["完成1个深度竞品案例", "完成一页真实玩家反馈摘要", "与导师校准分析结论"],
            "reason": "减少理论任务，避免在业务高峰继续堆叠学习负担；用低难度真实交付建立信心，并保留关键证据训练。",
            "mentor": "建议导师安排一次30分钟一对一沟通，示范从业务问题、AI辅助到人工判断的完整过程，并确认下周验收标准。",
            "questions": ["你最不确定的是提出问题、使用AI、判断结果还是形成结论？", "临时业务中有哪些素材可以直接转化为成长任务？", "什么最小成果能提升你独立开展业务的信心？"],
        }
    unfinished_count = len(data["unfinished"])
    if unfinished_count >= 3 or data["confidence"] <= 1:
        risk = "高"
    elif unfinished_count or data["confidence"] <= 3:
        risk = "中"
    else:
        risk = "低"
    profile = st.session_state.profile
    blueprint = ROLE_BLUEPRINTS[profile["primary_role"]]
    priorities = list(dict.fromkeys(data["unfinished"] + [
        f"完成一页{blueprint['object']}真实业务观察", "复用本周AI协作方法完成小型交付", "与导师完成成果校准",
    ]))[:3]
    return {
        "summary": f"第{data['week']}周完成{len(data['completed'])}项任务，仍有{unfinished_count}项需要调整，当前信心为{data['confidence']}/5。",
        "risk": risk,
        "keep": ["保留已完成任务中的有效方法，并记录可复用的人机协作步骤。"],
        "delay": [f"延期并收敛范围：{item}" for item in data["unfinished"]] or ["暂无延期任务。"],
        "add": [f"新增低难度验证任务：围绕{blueprint['object']}完成一页真实业务观察。"],
        "priorities": priorities,
        "reason": f"结合下周{data['hours']}小时投入和当前风险，优先缩小范围、增加真实反馈并保留人工验证。",
        "mentor": "建议导师用15—30分钟确认任务边界、证据质量和验收标准，不直接替新人完成任务。",
        "questions": ["本周哪项成果最能证明你的进步？", "未完成的主要原因是时间、方法还是协作资源？", "下周哪个节点最需要导师反馈？"],
    }


def sync_review_task_statuses(data: dict[str, Any]) -> None:
    completed_names = set(data["completed"])
    unfinished_names = set(data["unfinished"])
    for task in st.session_state.growth_plan:
        if task["name"] in completed_names:
            evidence = latest_evidence(task["id"])
            status = "已完成" if evidence and evidence["status"] == "已完成" else "待导师验收"
            task["status"] = status
            st.session_state[f"task_status_{task['id']}"] = status
            st.session_state.task_status_overrides[task["id"]] = status
        elif task["name"] in unfinished_names:
            task["status"] = "延期"
            st.session_state[f"task_status_{task['id']}"] = "延期"
            st.session_state.task_status_overrides[task["id"]] = "延期"


def make_dynamic_task(name: str) -> dict[str, Any]:
    st.session_state.dynamic_task_counter += 1
    incomplete_stages = [task["stage"] for task in st.session_state.growth_plan if task["status"] != "已完成"]
    stage = min(incomplete_stages) if incomplete_stages else 4
    clean_name = name.removeprefix("新增低难度真实业务任务：").removeprefix("新增低难度验证任务：")
    return {
        "id": f"dynamic_task_{st.session_state.dynamic_task_counter}", "stage": stage,
        "name": clean_name, "purpose": "根据每周复盘新增，用更小的真实交付降低风险并形成反馈。",
        "action": "使用真实或脱敏业务材料完成最小成果，并记录AI参与、人工验证和导师反馈。",
        "human": "确认问题、判断证据、承担业务取舍和最终交付责任。",
        "ai": "辅助整理材料、生成结构、检查遗漏和形成复盘草稿。",
        "verify": "事实、数据、用户反馈和最终业务结论必须由新人或导师人工验证。",
        "forbidden": "个人隐私、账号密钥、未公开经营数据、商业机密和未经授权的内部材料不得输入AI。",
        "deliverable": "一页可验收的真实业务成果", "criteria": "范围清晰、证据可追溯、人工验证完整，并获得导师或协作方反馈。",
        "hours": 3, "xp": 90, "status": "未开始", "skill_reward": "真实业务信心",
        "mentor_checkpoint": "确认任务范围、证据来源和人工验证结果。", "risk_event": "新增任务再次被业务挤占或把AI初稿直接作为结论。",
        "task_type": "选修任务", "dynamic": True,
    }


def apply_review_adjustment(data: dict[str, Any], result: dict[str, Any]) -> None:
    existing_dynamic_names = {task["name"] for task in st.session_state.growth_plan if task.get("dynamic")}
    for name in result["add"]:
        task = make_dynamic_task(name)
        if task["name"] not in existing_dynamic_names:
            st.session_state.growth_plan.append(task)
            existing_dynamic_names.add(task["name"])


def update_capabilities_from_review(data: dict[str, Any]) -> None:
    baseline = st.session_state.baseline_capabilities or st.session_state.diagnosis["capabilities"]
    completed_gain = min(12, len(data["completed"]) * 3)
    confidence_gain = max(-2, data["confidence"] - st.session_state.profile["confidence"]) * 2
    st.session_state.latest_capabilities = {
        "业务理解": min(100, baseline["业务理解"] + completed_gain),
        "AI协作": min(100, baseline["AI协作"] + completed_gain // 2 + 2),
        "跨团队协作": min(100, baseline["跨团队协作"] + (3 if any("协作" in name or "走查" in name for name in data["completed"]) else 0)),
        "数据意识": min(100, baseline.get("数据意识", 30) + (3 if any("数据" in name or "证据" in name for name in data["completed"]) else 0)),
        "独立交付": max(0, min(100, baseline["独立交付"] + completed_gain // 2 + confidence_gain)),
    }


def render_review_result(result: dict[str, Any]) -> None:
    risk_class = {"低": "risk-low", "中": "risk-medium", "高": "risk-high"}[result["risk"]]
    st.markdown(f'<div class="brief"><strong>本周成长总结</strong><br>{escape(result["summary"])}<br><br>风险等级：<span class="{risk_class}">{result["risk"]}</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, title, items in [(c1, "保留任务", result["keep"]), (c2, "延期任务", result["delay"]), (c3, "新增任务", result["add"])]:
        with col:
            st.markdown(f"#### {title}")
            for item in items:
                st.markdown(f"- {item}")
    st.markdown("#### 下周三个优先任务")
    for index, item in enumerate(result["priorities"], start=1):
        st.markdown(f"**{index}.** {item}")
    st.markdown(f'<div class="decision-card"><strong>计划调整原因</strong><br>{escape(result["reason"])}<br><br><strong>导师介入建议</strong><br>{escape(result["mentor"])}</div>', unsafe_allow_html=True)
    st.markdown("#### 下次一对一沟通建议问题")
    for question in result["questions"]:
        st.markdown(f"- {question}")


def render_action_card(role: str) -> None:
    card = st.session_state.action_cards.get(role) or {}
    if not card:
        return
    color = {"newcomer": "#5B8FF9", "mentor": "#9B8AFB", "hr": "#FFB45B"}[role]
    if role == "newcomer":
        items = "".join(f"<li>{escape(item)}</li>" for item in card["items"])
        body = f"<strong>下周三项优先任务</strong><ul>{items}</ul><strong>需要补充</strong>：{escape(card['supplement'])}<br><strong>当前风险</strong>：{escape(str(card['risk']))}<br><strong>推荐AI协作方式</strong>：{escape(card['ai'])}"
    elif role == "mentor":
        body = f"<strong>本周检查</strong>：{escape(card['check'])}<br><strong>建议追问</strong>：{escape(card['ask'])}<br><strong>待验收成果</strong>：{escape(card['accept'])}<br><strong>范围建议</strong>：{escape(card['scope'])}"
    else:
        signal = "已产生" if card["signal"] else "未产生"
        body = f"<strong>风险信号</strong>：{signal}<br><strong>风险类型</strong>：{escape(card['type'])}<br><strong>信号性质</strong>：{escape(card['level'])}<br><strong>组织资源建议</strong>：{escape(card['support'])}"
    st.markdown(f'<div class="action-card" style="--card-color:{color}"><h4>{escape(card.get("title", "未命名卡片"))}</h4>{body}</div>', unsafe_allow_html=True)


def render_weekly_review() -> None:
    if not require_profile():
        return
    st.markdown('<div class="section-title">每周复盘与动态调整</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">复盘结果同时服务新人、导师与HR。AI提出调整建议，关键变更仍由人确认。</div>', unsafe_allow_html=True)
    if st.button("加载模拟复盘"):
        load_demo_review()
        st.rerun()
    with st.expander("AI复盘教练", expanded=False):
        render_ai_mode_hint()
        render_ai_prereq_hint(
            "AI复盘教练需要至少一类复盘信息：",
            [
                "填写“本周做成了什么”。",
                "或填写“本周哪里卡住了”。",
                "或填写“下周最想改善什么”。",
                "也可以先点击“加载模拟复盘”，再生成反馈。",
            ],
        )
        left, middle, right = st.columns(3)
        with left:
            st.text_area("本周做成了什么？", key="review_subjective_done")
        with middle:
            st.text_area("本周哪里卡住了？", key="review_subjective_blocked")
        with right:
            st.text_area("下周最想改善什么？", key="review_subjective_next")
        if st.button("生成AI复盘反馈", key="generate_ai_review_feedback"):
            has_review_input = has_text(
                st.session_state.review_subjective_done,
                st.session_state.review_subjective_blocked,
                st.session_state.review_subjective_next,
                st.session_state.review_output,
                st.session_state.review_difficulty,
                " ".join(st.session_state.review_completed),
                " ".join(st.session_state.review_unfinished),
            )
            if not has_review_input:
                clear_ai_output("ai_review_feedback")
                st.warning("请先补充复盘内容，再生成AI复盘反馈。")
                render_ai_prereq_hint(
                    "请至少完成以下任意一项：",
                    [
                        "填写本周做成了什么。",
                        "填写本周哪里卡住了。",
                        "填写下周最想改善什么。",
                        "点击“加载模拟复盘”。",
                    ],
                )
            else:
                fallback_risk = "暂无明显风险" if len(st.session_state.review_unfinished) <= 1 and st.session_state.review_confidence >= 3 else "存在任务延期或信心不足风险"
                fallback = (
                    f"本周成长总结：你完成了“{st.session_state.review_subjective_done or st.session_state.review_output or '已填写的复盘任务'}”，已经形成可复盘素材。\n\n"
                    f"卡点归因：主要卡在“{st.session_state.review_subjective_blocked or st.session_state.review_difficulty or '待进一步拆解的任务阻塞'}”，需要把问题拆成可验证的小动作。\n\n"
                    f"下周行动建议：围绕“{st.session_state.review_subjective_next or '补齐一项真实成果证据'}”安排3个优先任务，并保留一次导师校准。\n\n"
                    f"给导师的一句话同步：我需要你帮我确认任务边界、证据质量和AI输出是否经过人工验证。\n\n"
                    f"给HR的风险提示：{fallback_risk}。"
                )
                prompt = (
                    f"画像：{st.session_state.profile}\n"
                    f"本周做成了什么：{st.session_state.review_subjective_done}\n"
                    f"本周哪里卡住了：{st.session_state.review_subjective_blocked}\n"
                    f"下周最想改善什么：{st.session_state.review_subjective_next}\n"
                    f"已有复盘字段：已完成={st.session_state.review_completed}，未完成={st.session_state.review_unfinished}，困难={st.session_state.review_difficulty}，成果={st.session_state.review_output}\n"
                    "请输出成长总结、卡点归因、下周行动、导师同步、HR风险提示。"
                )
                st.session_state.ai_review_feedback = optional_ai_text("AI复盘教练", prompt, fallback)
        if st.session_state.ai_review_feedback:
            render_ai_output(st.session_state.ai_review_feedback)
    plan_names = [task["name"] for task in st.session_state.growth_plan]
    with st.form("weekly_review_form"):
        left, right = st.columns(2)
        with left:
            st.number_input("当前周次", min_value=1, max_value=13, step=1, key="review_week")
            st.multiselect("已完成任务", plan_names, key="review_completed")
            st.multiselect("未完成任务", plan_names, key="review_unfinished")
            st.text_area("本周遇到的困难*", key="review_difficulty")
        with right:
            st.text_area("本周形成的成果", key="review_output")
            st.slider("当前信心评分", 1, 5, key="review_confidence")
            st.number_input("下周可投入时间（小时）", min_value=1, max_value=30, step=1, key="review_hours")
        submitted = st.form_submit_button("提交复盘并调整计划", type="primary", width="stretch")
    if submitted:
        if not st.session_state.review_difficulty.strip():
            st.warning("请填写本周遇到的困难。")
        elif not st.session_state.review_completed and not st.session_state.review_unfinished:
            st.warning("请至少选择一项已完成或未完成任务。")
        elif set(st.session_state.review_completed) & set(st.session_state.review_unfinished):
            st.warning("同一任务不能同时标记为已完成和未完成，请调整后再提交。")
        else:
            data = {
                "week": st.session_state.review_week, "completed": st.session_state.review_completed,
                "unfinished": st.session_state.review_unfinished, "difficulty": st.session_state.review_difficulty,
                "output": st.session_state.review_output, "confidence": st.session_state.review_confidence,
                "hours": st.session_state.review_hours,
            }
            result = generate_review_result(data)
            sync_review_task_statuses(data)
            update_capabilities_from_review(data)
            record = {"submitted_at": datetime.now().isoformat(timespec="seconds"), "input": data, "result": result, "adjustment_applied": False}
            if st.session_state.profile["auto_adjust"]:
                apply_review_adjustment(data, result)
                record["adjustment_applied"] = True
                st.session_state.pending_adjustment = None
            else:
                st.session_state.pending_adjustment = {"input": data, "result": result}
            update_action_cards("review", review=result)
            st.session_state.reviews.append(record)
            st.rerun()
    elif st.session_state.reviews:
        render_review_result(st.session_state.reviews[-1]["result"])
    if st.session_state.profile["auto_adjust"] and st.session_state.reviews:
        st.success("已完成任务和延期任务已同步，新增任务已写入成长地图。")
    elif st.session_state.pending_adjustment:
        st.warning("系统提出调整建议，等待新人或导师确认。已完成与延期状态已同步，但新增任务尚未写入成长计划。")
        accept_col, reject_col = st.columns(2)
        with accept_col:
            if st.button("接受调整", type="primary", width="stretch"):
                pending = st.session_state.pending_adjustment
                apply_review_adjustment(pending["input"], pending["result"])
                if st.session_state.reviews:
                    st.session_state.reviews[-1]["adjustment_applied"] = True
                st.session_state.pending_adjustment = None
                st.rerun()
        with reject_col:
            if st.button("暂不调整", width="stretch"):
                st.session_state.pending_adjustment = None
                st.rerun()
    if st.session_state.reviews:
        st.markdown("### 三方联动·新人下一步")
        render_action_card("newcomer")
        st.download_button(
            "导出最近一次周复盘（Markdown）", build_review_markdown(),
            file_name=f"第{st.session_state.reviews[-1]['input']['week']}周复盘.md", mime="text/markdown", key="download_weekly_review",
        )


def current_stage_index() -> int:
    if st.session_state.demo_step:
        week = st.session_state.demo_week
        return 0 if week < 3 else 1 if week < 6 else 2 if week < 9 else 3 if week < 12 else 4
    sync_task_statuses()
    for index in range(5):
        tasks = [task for task in st.session_state.growth_plan if task["stage"] == index]
        if tasks and not all(task["status"] == "已完成" for task in tasks):
            return index
    return 4


def apply_mentor_decision(record: dict[str, Any], decision: str) -> None:
    task = get_task(record["task_id"])
    if not task:
        return
    if decision == "通过验收":
        status = "已完成"
        requirement = "导师已确认成果证据、AI验证过程和独立判断达到当前阶段要求。"
        st.session_state.risk_level = "低"
    elif decision == "退回补充":
        status = "待补充"
        requirement = record["evaluation"]["next_action"]
    else:
        status = "待补充"
        requirement = "将任务收敛为一个用户问题、一项核心机制和一组可核验数据，完成后重新提交。"
        task["scope_adjustment"] = requirement
    task["status"] = status
    st.session_state[f"task_status_{task['id']}"] = status
    st.session_state.task_status_overrides[task["id"]] = status
    record["status"] = status
    record["mentor_decision"] = decision
    record["evaluation"]["mentor_review"] = False
    record["supplement_requirement"] = requirement
    st.session_state.mentor_decisions.append({
        "record_id": record["id"], "task_id": task["id"], "task_name": task["name"],
        "decision": decision, "requirement": requirement, "decided_at": datetime.now().isoformat(timespec="seconds"),
    })
    update_action_cards("evidence", evidence=record)


def pending_mentor_evidence() -> list[dict[str, Any]]:
    records = [items[-1] for items in st.session_state.evidence_records.values() if items]
    return [
        record for record in records
        if not record.get("mentor_decision")
        and record["status"] in {"待补充", "待导师验收"}
        and record["evaluation"]["mentor_review"]
    ]


def render_mentor_acceptance() -> None:
    pending = pending_mentor_evidence()
    st.markdown("### 成长证据验收")
    if not pending:
        st.info("当前没有待导师处理的成长证据。新人提交证据或自动演示进入第8周后，此处会出现验收卡。")
        return
    for record in pending:
        evaluation = record["evaluation"]
        with st.expander(f"{record['task_name']}｜{record['status']}｜综合{evaluation['overall']}分", expanded=True):
            st.markdown(f'<div class="status-mentor"><strong>新人提交的成果摘要</strong><br>{escape(record["data"]["summary"])}</div>', unsafe_allow_html=True)
            score_columns = st.columns(4)
            for column, (name, score) in zip(score_columns, evaluation["scores"].items()):
                column.metric(name, score)
            st.markdown("**AI识别的主要问题**")
            for item in evaluation["missing"]:
                st.markdown(f"- {item}")
            st.markdown("**建议导师追问**：哪些结论来自真实用户或数据？哪些仍是AI推测？如果范围减半，最小可验证成果是什么？")
            if record.get("mentor_decision"):
                st.success(f"导师决定：{record['mentor_decision']}。{record['supplement_requirement']}")
                continue
            pass_col, return_col, scope_col = st.columns(3)
            with pass_col:
                if st.button("通过验收", key=f"mentor_pass_{record['id']}", type="primary", width="stretch"):
                    apply_mentor_decision(record, "通过验收")
                    st.rerun()
            with return_col:
                if st.button("退回补充", key=f"mentor_return_{record['id']}", width="stretch"):
                    apply_mentor_decision(record, "退回补充")
                    st.rerun()
            with scope_col:
                if st.button("调整任务范围", key=f"mentor_scope_{record['id']}", width="stretch"):
                    apply_mentor_decision(record, "调整任务范围")
                    st.rerun()


def render_mentor_panel() -> None:
    if not require_profile():
        return
    if st.session_state.profile["nickname"] == "小鹅":
        render_demo_disclaimer()
    sync_task_statuses()
    profile = st.session_state.profile
    diagnosis = st.session_state.diagnosis
    stage_index = current_stage_index()
    completed = [task for task in st.session_state.growth_plan if task["status"] == "已完成"]
    delayed = [task for task in st.session_state.growth_plan if task["status"] == "延期"]
    risk = st.session_state.risk_level if st.session_state.demo_step else (st.session_state.reviews[-1]["result"]["risk"] if st.session_state.reviews else "低")
    latest_review = st.session_state.reviews[-1]["result"] if st.session_state.reviews else None
    st.markdown('<div class="section-title">导师带教面板</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">AI不是替代导师，而是把过程信号整理成更聚焦的带教动作。</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("当前阶段", STAGE_DEFINITIONS[stage_index]["name"])
    m2.metric("已完成任务", len(completed))
    m3.metric("延期任务", len(delayed))
    m4.metric("风险等级", risk)
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("### 核心能力变化")
        labels = ["业务理解", "AI协作", "跨团队协作", "独立交付"]
        baseline = st.session_state.baseline_capabilities or diagnosis.get("baseline_capabilities", diagnosis["capabilities"])
        current_metrics = st.session_state.growth_metrics if st.session_state.demo_step else st.session_state.latest_capabilities
        if current_metrics:
            figure = go.Figure()
            figure.add_trace(go.Bar(name="画像基线", x=labels, y=[baseline[label] for label in labels], marker_color="#BFD4FF"))
            figure.add_trace(go.Bar(name="当前评估", x=labels, y=[current_metrics[label] for label in labels], marker_color="#63D7B0"))
            figure.update_layout(barmode="group", height=330, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#273142", yaxis=dict(range=[0, 100], gridcolor="#E8EAF0"), xaxis=dict(gridcolor="#E8EAF0"), legend=dict(orientation="h"))
            st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
        else:
            st.info("尚未形成后续评估数据。完成自动演示事件或提交每周复盘后，系统才会展示能力变化。")
            baseline_figure = go.Figure(go.Bar(x=labels, y=[baseline[label] for label in labels], marker_color=DOPAMINE_COLORS[:4], text=[baseline[label] for label in labels], textposition="auto"))
            baseline_figure.update_layout(title="当前画像基线", height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#273142", yaxis=dict(range=[0, 100], gridcolor="#E8EAF0"), xaxis=dict(gridcolor="#E8EAF0"))
            st.plotly_chart(baseline_figure, width="stretch", config={"displayModeBar": False})
    with right:
        obstacle = latest_review["summary"] if latest_review else (profile["worry"] or "当前尚未出现明确障碍，需继续观察真实任务表现。")
        advice = latest_review["mentor"] if latest_review else diagnosis["mentor_intensity"]
        st.markdown(f'<div class="insight"><h4>系统识别的主要障碍</h4><p>{escape(obstacle)}</p></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'<div class="insight"><h4>本周导师建议</h4><p>{escape(advice)}</p></div>', unsafe_allow_html=True)
    st.markdown("### 三方联动·导师本周动作")
    render_action_card("mentor")
    st.download_button(
        "导出导师一对一沟通卡（Markdown）", build_mentor_card_markdown(),
        file_name="导师一对一沟通卡.md", mime="text/markdown", key="download_mentor_card",
    )
    with st.expander("AI导师追问生成器", expanded=False):
        render_ai_mode_hint()
        render_ai_prereq_hint(
            "生成导师追问前，请先输入：",
            [
                "新人提交的成果摘要。",
                "或成果证据描述。",
                "或导师观察到的具体问题。",
            ],
        )
        mentor_observation = st.text_area("请输入新人提交的成果摘要或导师观察", key="ai_mentor_observation")
        if st.button("生成导师追问", key="generate_ai_mentor_questions"):
            if not has_text(mentor_observation):
                clear_ai_output("ai_mentor_questions")
                st.warning("请先输入新人提交的成果摘要或导师观察，再生成导师追问。")
                render_ai_prereq_hint(
                    "可输入的内容示例：",
                    [
                        "新人提交的成果摘要。",
                        "成果证据、AI使用方式或验证记录。",
                        "导师观察到的卡点、风险或不确定结论。",
                    ],
                )
            else:
                fallback = (
                    f"基于导师观察“{mentor_observation}”，建议追问：\n\n"
                    "1.你这份成果最关键的业务证据来自哪里？考察点：证据来源是否可追溯。建议反馈：请补充原始材料或口径说明。是否需要补证：视证据完整度而定。\n\n"
                    "2.AI在其中具体做了哪些工作，哪些结论由你本人判断？考察点：人机边界。建议反馈：要求新人标注AI辅助、人工判断和最终责任。\n\n"
                    "3.如果方案上线后数据不符合预期，你下一步会怎么验证？考察点：行动计划和风险意识。建议反馈：引导其形成小流量验证或回滚方案。"
                )
                prompt = (
                    f"新人画像：{profile}\n当前阶段：{STAGE_DEFINITIONS[stage_index]['name']}\n导师观察：{mentor_observation}\n"
                    "请生成3个导师追问，每个包含考察点、反馈方式、是否需要补证。"
                )
                st.session_state.ai_mentor_questions = optional_ai_text("AI导师追问生成器", prompt, fallback)
        if st.session_state.ai_mentor_questions:
            render_ai_output(st.session_state.ai_mentor_questions)
    render_mentor_acceptance()
    questions = latest_review["questions"] if latest_review else ["新人当前最缺少哪类业务证据？", "哪些决策应由新人独立完成，哪些需要导师把关？", "下周最小可验证成果是什么？"]
    st.markdown("### 下一次一对一沟通问题")
    for question in questions:
        st.markdown(f"- {question}")
    st.markdown("### 需要导师验收的任务")
    acceptance_tasks = [task for task in st.session_state.growth_plan if task["stage"] in {stage_index, min(stage_index + 1, 4)} and task["status"] != "已完成"][:4]
    for task in acceptance_tasks:
        st.markdown(f"- **{task['name']}**：{task['mentor_checkpoint']} 验收重点：{task['criteria']}")


def build_hr_demo_data() -> list[dict[str, Any]]:
    roles = ["技术研发", "产品", "游戏策划", "设计", "运营", "数据分析", "市场与品牌", "HR与职能"]
    maturities = ["L1观察者", "L2协作新手", "L3业务协作者", "L4人机协同引领者"]
    mentors = ["导师A", "导师B", "导师C", "导师D", "导师E", "导师F"]
    obstacles = ["真实业务经验不足", "AI结果验证薄弱", "跨团队协作卡点", "业务高峰挤占时间", "目标范围过大", "数据口径不清"]
    progress_values = [82, 65, 47, 91, 36, 58, 74, 69, 28, 88, 53, 62, 77, 44, 71, 33, 84, 56, 68, 49]
    risks = ["低", "中", "中", "低", "高", "中", "低", "低", "高", "低", "中", "中", "低", "高", "低", "高", "低", "中", "低", "中"]
    data = []
    for index in range(20):
        progress = progress_values[index]
        if index == 0:
            demo_active = bool(st.session_state.profile and st.session_state.profile.get("nickname") == "小鹅")
            demo_progress = min(100, round(st.session_state.demo_week / 12 * 100)) if demo_active else 47
            demo_risk = st.session_state.risk_level if demo_active else "中"
            demo_stage = STAGE_DEFINITIONS[current_stage_index()]["name"] if demo_active else "业务探索区"
            data.append({
                "新人": "小鹅", "岗位族": "游戏策划", "成长进度": demo_progress,
                "AI成熟度": st.session_state.diagnosis["maturity_level"] if demo_active else "L2协作新手",
                "风险": demo_risk, "导师": "导师A", "主要障碍": "AI结果验证薄弱" if demo_risk != "低" else "补证后扩大独立范围",
                "当前阶段": demo_stage, "highlight": True,
            })
        else:
            data.append({
                "新人": f"新人{index + 1:02d}", "岗位族": roles[index % len(roles)], "成长进度": progress,
                "AI成熟度": maturities[min(3, max(0, progress // 25))], "风险": risks[index],
                "导师": mentors[index % len(mentors)], "主要障碍": obstacles[(index * 2 + index // 4) % len(obstacles)],
                "当前阶段": STAGE_DEFINITIONS[min(4, progress // 20)]["name"], "highlight": False,
            })
    return data


def style_chart(figure: go.Figure, height: int = 340) -> go.Figure:
    figure.update_layout(height=height, margin=dict(l=25, r=20, t=45, b=35), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#273142", xaxis=dict(gridcolor="#E8EAF0", zerolinecolor="#E8EAF0"), yaxis=dict(gridcolor="#E8EAF0", zerolinecolor="#E8EAF0"), legend=dict(orientation="h"), hoverlabel=dict(bgcolor="#FFFFFF", font_color="#273142", bordercolor="#EEE8E2"))
    return figure


def render_hr_dashboard() -> None:
    data = build_hr_demo_data()
    if not st.session_state.action_cards.get("hr"):
        update_action_cards("dashboard")
    st.markdown('<span class="demo-tag">模拟数据</span>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">HR批次成长驾驶舱</div>', unsafe_allow_html=True)
    st.warning("以下内容为模拟数据，不代表腾讯真实员工或内部数据。")
    low = sum(item["风险"] == "低" for item in data)
    medium = sum(item["风险"] == "中" for item in data)
    high = sum(item["风险"] == "高" for item in data)
    metrics = st.columns(4)
    metrics[0].metric("新人总数", len(data))
    metrics[1].metric("正常", low)
    metrics[2].metric("需要关注", medium)
    metrics[3].metric("高风险", high)
    xiaoe = next(item for item in data if item["新人"] == "小鹅")
    risk_class = {"低": "risk-low", "中": "risk-medium", "高": "risk-high"}[xiaoe["风险"]]
    st.markdown(
        f'<div class="xiaoe-card"><strong>重点联动新人·小鹅</strong><br>进度{xiaoe["成长进度"]}%｜{escape(xiaoe["当前阶段"])}｜'
        f'<span class="{risk_class}">{xiaoe["风险"]}风险</span>｜{escape(xiaoe["主要障碍"])}</div>', unsafe_allow_html=True,
    )
    with st.expander("展开小鹅的成长证据与联动详情", expanded=st.session_state.demo_week in {3, 8, 9}):
        evidence = latest_evidence(st.session_state.demo_evidence_task_id)
        current_task = get_task(st.session_state.demo_evidence_task_id) if st.session_state.demo_evidence_task_id else None
        last_decision = st.session_state.mentor_decisions[-1] if st.session_state.mentor_decisions else None
        st.markdown(f"**最近关键事件**：{st.session_state.current_event if st.session_state.demo_step else '等待自动演示推进'}")
        st.markdown(f"**当前任务**：{current_task['name'] if current_task else '生成90天路径并进入真实任务'}")
        st.markdown(f"**成果评价**：{evidence['evaluation']['overall']}分·{evidence['evaluation']['conclusion']}" if evidence else "**成果评价**：尚未提交成长证据")
        st.markdown(f"**导师动作**：{last_decision['decision']}·{last_decision['requirement']}" if last_decision else "**导师动作**：按关键检查点观察，暂未形成验收决定")
        next_plan = evidence["evaluation"]["next_action"] if evidence else "推进当前任务并记录人机分工与验证过程"
        st.markdown(f"**下一步计划**：{next_plan}")

    role_names = sorted({item["岗位族"] for item in data})
    role_progress = [round(sum(item["成长进度"] for item in data if item["岗位族"] == role) / sum(item["岗位族"] == role for item in data)) for role in role_names]
    maturity_names = ["L1观察者", "L2协作新手", "L3业务协作者", "L4人机协同引领者"]
    maturity_counts = [sum(item["AI成熟度"] == name for item in data) for name in maturity_names]
    left, right = st.columns(2)
    with left:
        figure = go.Figure(go.Bar(x=role_progress, y=role_names, orientation="h", marker_color=[DOPAMINE_COLORS[index % len(DOPAMINE_COLORS)] for index in range(len(role_names))], text=role_progress, textposition="auto"))
        figure.update_layout(title="各岗位平均成长进度", xaxis=dict(range=[0, 100]))
        st.plotly_chart(style_chart(figure), width="stretch", config={"displayModeBar": False})
    with right:
        figure = go.Figure(go.Pie(labels=maturity_names, values=maturity_counts, hole=.55, marker_colors=DOPAMINE_COLORS[:4]))
        figure.update_layout(title="AI协作成熟度分布")
        st.plotly_chart(style_chart(figure), width="stretch", config={"displayModeBar": False})

    mentor_names = sorted({item["导师"] for item in data})
    mentor_load = [sum(item["导师"] == mentor for item in data) for mentor in mentor_names]
    obstacle_names = sorted({item["主要障碍"] for item in data})
    obstacle_counts = [sum(item["主要障碍"] == obstacle for item in data) for obstacle in obstacle_names]
    left, right = st.columns(2)
    with left:
        figure = go.Figure(go.Bar(x=mentor_names, y=mentor_load, marker_color=DOPAMINE_COLORS, text=mentor_load, textposition="auto"))
        figure.update_layout(title="各导师带教负载")
        st.plotly_chart(style_chart(figure, 310), width="stretch", config={"displayModeBar": False})
    with right:
        figure = go.Figure(go.Bar(x=obstacle_counts, y=obstacle_names, orientation="h", marker_color=[DOPAMINE_COLORS[(index + 2) % len(DOPAMINE_COLORS)] for index in range(len(obstacle_names))], text=obstacle_counts, textposition="auto"))
        figure.update_layout(title="高频成长障碍")
        st.plotly_chart(style_chart(figure, 310), width="stretch", config={"displayModeBar": False})

    role_risk_matrix = [[sum(item["岗位族"] == role and item["风险"] == risk for item in data) for role in role_names] for risk in ["低", "中", "高"]]
    heatmap = go.Figure(go.Heatmap(z=role_risk_matrix, x=role_names, y=["正常", "关注", "高风险"], colorscale=[[0, "#FFFFFF"], [.38, "#FFF8D9"], [.7, "#FFD9A8"], [1, "#FF6B6B"]], showscale=False, text=role_risk_matrix, texttemplate="%{text}", hoverlabel=dict(bgcolor="#FFFFFF", font_color="#273142")))
    heatmap.update_layout(title="岗位风险热力图")
    st.plotly_chart(style_chart(heatmap, 300), width="stretch", config={"displayModeBar": False})

    st.markdown("### 本周需要HR重点关注的人")
    focus_people = sorted([item for item in data if item["风险"] in {"中", "高"}], key=lambda item: (item["风险"] != "高", item["成长进度"]))[:6]
    cols = st.columns(3)
    for index, person in enumerate(focus_people):
        with cols[index % 3]:
            risk_class = "risk-high" if person["风险"] == "高" else "risk-medium"
            st.markdown(f'<div class="focus-person"><strong>{person["新人"]}·{person["岗位族"]}</strong><div class="focus-meta">进度{person["成长进度"]}%｜<span class="{risk_class}">{person["风险"]}</span><br>{person["主要障碍"]}｜{person["导师"]}</div></div>', unsafe_allow_html=True)
    st.markdown("### 三方联动·HR信号")
    render_action_card("hr")
    st.markdown("### 本周信号如何转化为组织行动")
    signal_cols = st.columns(3)
    signals = [
        ("6名新人", "AI结果验证薄弱", "增加AI验证微课"),
        ("4名新人", "真实业务机会不足", "建立脱敏任务池"),
        ("2名导师", "带教负载偏高", "调整带教分配"),
    ]
    for column, (count, signal, action) in zip(signal_cols, signals):
        with column:
            st.markdown(f'<div class="action-card" style="--card-color:#FFB45B"><strong>{escape(count)}·{escape(signal)}</strong><br>组织行动：{escape(action)}</div>', unsafe_allow_html=True)
    st.markdown("### 本周培养简报")
    fallback_brief = "本周20名模拟新人中，4人进入高风险，主要集中在业务高峰挤占成长时间、真实业务经验不足和AI结果验证薄弱。建议HR优先检查高风险新人的任务范围与导师容量，并将“证据化使用AI”加入共性训练。当前导师负载整体可控，但导师A与导师B承担的跨团队任务较多，应避免把带教质量完全依赖个人经验。"
    st.markdown(f'<div class="brief">{escape(fallback_brief)}</div>', unsafe_allow_html=True)
    st.markdown("### AI组织洞察")
    render_ai_mode_hint()
    render_ai_prereq_hint(
        "生成HR组织洞察前，请先补充关注点：",
        [
            "填写HR本周最关心的组织问题。",
            "系统只会基于模拟批次数据和你填写的关注点生成组织洞察。",
            "AI输出仅用于辅助分析，不能替代HR判断。",
        ],
    )
    ai_hr_focus = st.text_area(
        "请输入本周HR关注点或组织问题",
        key="ai_hr_focus",
        placeholder="例如：高风险新人集中在哪些岗位？导师负载是否过高？AI结果验证能力如何集中训练？",
    )
    if st.button("生成HR组织洞察简报", key="generate_ai_hr_insight"):
        if not has_text(ai_hr_focus):
            clear_ai_output("ai_hr_insight")
            st.warning("请先填写本周HR关注点或组织问题，再生成AI组织洞察简报。")
            render_ai_prereq_hint(
                "可以从这些角度填写关注点：",
                [
                    "高风险新人集中在哪些岗位。",
                    "导师负载是否过高。",
                    "AI结果验证能力是否需要集中训练。",
                    "真实业务机会是否不足。",
                ],
            )
        else:
            fallback = (
                f"围绕HR本周关注点“{ai_hr_focus}”，当前新人群体风险为：{high}名高风险、{medium}名需要关注，主要障碍集中在AI结果验证、真实业务机会和跨团队协作。\n\n"
                "高潜特征：进度较高且风险较低的新人通常能主动提交证据、向导师校准边界，并记录AI核验过程。\n\n"
                "需要导师介入的人群：高风险新人、进度低于50%且存在证据不足的人、导师负载过高团队中的新人。\n\n"
                "组织层面培训建议：增加AI验证微课、脱敏任务池和导师检查点模板。\n\n"
                "下一轮培养机制优化：把成长任务与真实项目合并，减少纯理论学习堆叠。"
            )
            prompt = (
                f"HR本周关注点：{ai_hr_focus}\n"
                f"HR模拟批次数据：{data}\n"
                "请生成新人群体风险、高潜特征、导师介入人群、组织培训建议和机制优化。"
            )
            st.session_state.ai_hr_insight = optional_ai_text("AI组织洞察简报", prompt, fallback)
    if st.session_state.ai_hr_insight:
        render_ai_output(st.session_state.ai_hr_insight)
    st.markdown("### 建议组织层面增加的培训或资源")
    for item in ["增加30分钟AI结果验证微课，覆盖事实核验、数据口径和引用来源。", "提供可脱敏的真实业务任务池，帮助新人获得低风险成功体验。", "建立导师检查点模板，统一目标、证据、风险和验收四类问题。", "为持续高强度团队设置成长任务减负机制，允许任务与真实项目合并。"]:
        st.markdown(f"- {item}")
    st.download_button(
        "导出HR本周培养简报（CSV）", build_hr_brief_csv(data),
        file_name="HR本周培养简报_模拟数据.csv", mime="text/csv", key="download_hr_brief",
    )


def render_placeholder(title: str, description: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.info(description)


def main() -> None:
    init_state()
    inject_styles()
    render_sidebar()
    render_breadcrumb()
    page = st.session_state.current_page
    if page == "首页":
        render_home()
    elif page == "智能画像":
        render_wizard()
    elif page == "诊断报告":
        render_diagnosis_report()
    elif page == "成长地图":
        render_growth_map()
    elif page == "每周复盘":
        render_weekly_review()
    elif page == "互动闯关":
        try:
            render_game_page()
        except Exception as exc:
            logger.exception("互动闯关模块渲染失败: %s", exc)
            st.markdown(
                """
                <div class="glass" style="border-left:5px solid var(--red);">
                <h3>当前模块出现异常</h3>
                <p>请点击重试；若仍失败，可先返回首页或重置本轮进度。</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            left, right = st.columns(2)
            with left:
                if st.button("重试互动闯关", type="primary", width="stretch"):
                    st.session_state.need_scroll_top = True
                    st.rerun()
            with right:
                if st.button("返回首页", width="stretch"):
                    st.session_state.current_page = "首页"
                    st.session_state.nav_open_group = None
                    st.session_state.need_scroll_top = True
                    st.rerun()
            st.caption(f"调试信息：{type(exc).__name__}: {exc}")
            if os.getenv("DEBUG_STREAMLIT_ERRORS") == "1":
                st.exception(exc)
    elif page == "90天自动演示":
        render_auto_demo()
    elif page == "导师面板":
        render_mentor_panel()
    elif page == "HR驾驶舱":
        render_hr_dashboard()
    else:
        st.error("页面状态异常，已返回首页。")
        st.session_state.current_page = "首页"
        st.session_state.nav_open_group = None
        st.rerun()


if __name__ == "__main__":
    main()
