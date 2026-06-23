from __future__ import annotations

from copy import deepcopy
from html import escape
from typing import Any

import streamlit as st

from ai_runtime import optional_ai_text
from game_content import (
    AI_REVIEW_ITEMS,
    ALIGNMENT_OPTIONS_BY_ROLE,
    BADGE_DEFINITIONS,
    DISPLAY_NAMES,
    ENDING_DEFINITIONS,
    EVIDENCE_ITEMS,
    FOOD_DEFINITIONS,
    GAME_ACTS,
    PRIORITY_TASKS,
    RANDOM_REWARDS,
    REMEDIATION_QUESTIONS,
    SCENES,
    SCOPE_BUDGET,
    SCOPE_TASKS,
    STAT_KEYS,
    STAGE_FOUR_EVIDENCE_CARDS,
    STAGE_FOUR_SLOT_NAMES,
)
from game_engine import (
    advance_after_minigame,
    advance_boss_question,
    advance_stage_three_scene,
    advance_scene,
    apply_choice,
    calculate_anonymous_rank,
    calculate_level,
    calculate_scope_plan,
    claim_random_reward,
    claim_stage_four_bonus_reward,
    complete_stage_four,
    complete_stage_three,
    current_random_event,
    current_stage_four_bonus,
    current_chapter,
    current_week,
    enter_post_game_hub,
    enter_stage_four,
    enter_stage_three,
    enter_stage_two,
    ending_display_payload,
    ensure_boss_questions,
    ensure_stage_four_bonus,
    exchange_badge_fragments,
    export_game_save,
    feed_companion,
    feed_inventory_food,
    get_stage_three_alignment_rounds,
    import_game_save,
    normalize_boss_question,
    prepare_stage_four_loadout,
    submit_alignment,
    reset_game,
    submit_random_event,
    submit_boss_answer,
    submit_remediation_task,
    submit_scope,
    submit_stage_four_bonus,
    submit_stage_four_evidence,
    start_game,
    start_new_game_plus,
    submit_ai_review,
    submit_evidence,
    submit_priority,
    submit_remediation,
    use_stage_four_item,
    use_stage_two_hint,
)


FOCUS_STATS = ("ai_collaboration", "verification", "delivery")
INITIAL_STATS = {"business": 25, "ai_collaboration": 30, "verification": 20, "collaboration": 20, "delivery": 15}


def scroll_to_top() -> None:
    st.markdown('<div id="page-top"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <script>
        const target = window.parent.document.getElementById("page-top") || document.getElementById("page-top");
        if (target) {
            target.scrollIntoView({behavior: "smooth", block: "start"});
        } else {
            window.parent.scrollTo({top: 0, behavior: "smooth"});
        }
        </script>
        """,
        unsafe_allow_html=True,
    )


def _rerun_top() -> None:
    st.session_state.need_scroll_top = True
    st.rerun()


def _inject_game_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container{padding-bottom:5rem}.game-hero{min-height:184px;padding:1.35rem 1.55rem;border:1px solid #E7EAF2;border-radius:24px;background:linear-gradient(120deg,#EAF3FF 0%,#FFF0F6 56%,#FFF8D9 100%);box-shadow:0 12px 28px rgba(53,65,92,.075);margin-bottom:.9rem;display:flex;flex-direction:column;justify-content:center}.game-hero h1{margin:.2rem 0 .45rem;font-size:2.35rem;line-height:1.12;font-weight:760;color:#273142}.game-hero p{margin:0;color:#667085;line-height:1.65;max-width:820px}.game-kicker{color:#5B8FF9;font-size:.74rem;font-weight:780;letter-spacing:.12em}.game-page-note{font-size:.82rem;color:#667085;margin-top:.55rem}
        .game-intro-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin:.9rem 0}.intro-card{padding:1rem;background:#fff;border:1px solid #EEE8E2;border-radius:18px;box-shadow:0 8px 20px rgba(53,65,92,.055);min-height:128px}.intro-no{display:inline-flex;width:28px;height:28px;align-items:center;justify-content:center;border-radius:50%;background:#EAF3FF;color:#5B8FF9;font-weight:800;font-size:.78rem}.intro-title{font-size:1rem;font-weight:760;margin:.65rem 0 .35rem;color:#273142}.intro-text{font-size:.86rem;color:#667085;line-height:1.6}.balance-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.6rem}.balance-item{padding:.72rem .85rem;border-radius:14px;background:#FFFDFB;border:1px solid #EEE8E2;color:#475467;font-size:.9rem}
        .act-track{display:grid;grid-template-columns:repeat(4,1fr);gap:.55rem;margin:.85rem 0 1rem}.act-item{padding:.7rem .8rem;border-radius:15px;background:#F8FAFC;border:1px solid #E7EAF2;color:#667085}.act-item.current{background:linear-gradient(90deg,#EAF3FF,#F1EDFF);border-color:#C9D9FF;color:#273142;box-shadow:0 8px 18px rgba(91,143,249,.10)}.act-item.done{background:#EAFBF5;border-color:#BFEEDC;color:#26755F}.act-item.locked{background:#FAFAFA;color:#98A2B3}.act-name{font-weight:760;font-size:.9rem}.act-desc{font-size:.74rem;line-height:1.45;margin-top:.25rem}
        .hud-shell{background:#fff;border:1px solid #EEE8E2;border-radius:22px;padding:1rem 1.05rem;box-shadow:0 8px 24px rgba(53,65,92,.055);margin:.8rem 0}.hud-top{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:.75rem}.hud-stage{font-weight:760;color:#273142;font-size:1.05rem}.hud-level{padding:.42rem .7rem;border-radius:999px;background:#F1EDFF;color:#6757C8;font-weight:780;font-size:.88rem}.hud-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.65rem;margin:.65rem 0}.hud-card{padding:.72rem .78rem;background:#FFFDFB;border:1px solid #EEE8E2;border-radius:15px}.hud-label{color:#667085;font-size:.72rem;font-weight:560}.hud-value{color:#273142;font-size:1rem;font-weight:780;margin-top:.2rem}.hud-risk{background:#FFF8D9}.hud-energy{background:#EAFBF5}.hud-trust{background:#EAF3FF}.hud-bar{height:6px;margin-top:.45rem;background:#F0F1F4;border-radius:99px;overflow:hidden}.hud-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#5B8FF9,#9B8AFB)}.hud-fill.energy{background:linear-gradient(90deg,#63D7B0,#69C0FF)}.hud-fill.risk{background:linear-gradient(90deg,#FFD66B,#FFB45B)}
        .ability-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:.6rem;margin:.6rem 0}.ability-card{padding:.68rem .75rem;border-radius:14px;background:#FFFDFB;border:1px solid #EEE8E2}.ability-name{font-size:.72rem;color:#667085}.ability-score{font-size:.98rem;font-weight:780;color:#273142}.ability-bar{height:5px;margin-top:.4rem;background:#F0F1F4;border-radius:99px;overflow:hidden}.ability-fill{height:100%;background:linear-gradient(90deg,#5B8FF9,#9B8AFB);border-radius:99px}
        .scene-card{padding:1.1rem 1.2rem;border-radius:20px;background:#fff;border:1px solid #EEE8E2;box-shadow:0 8px 22px rgba(53,65,92,.06);margin-bottom:.8rem}.scene-card.stage-two{background:linear-gradient(120deg,#F1EDFF,#FFF2E2)}.scene-card.evidence{background:linear-gradient(120deg,#EAFBF5,#EAF3FF)}.scene-chip{display:inline-block;padding:.22rem .55rem;border-radius:99px;background:#EAF3FF;color:#3F72C8;font-size:.72rem;font-weight:760}.scene-card h2{margin:.6rem 0 .45rem;font-size:1.45rem;font-weight:760}.scene-card p{color:#667085;line-height:1.68;margin:0}.option-card-title{font-weight:740;color:#273142;font-size:1rem}.option-effect{font-size:.78rem;color:#667085;margin:.35rem 0}.tradeoff-tags{display:flex;flex-wrap:wrap;gap:.35rem;margin:.55rem 0}.tradeoff-tag{padding:.22rem .52rem;border-radius:999px;background:#EAF3FF;color:#3F72C8;font-size:.74rem;font-weight:650}.mini-progress{display:inline-block;margin-bottom:.45rem;padding:.25rem .62rem;border-radius:999px;background:#FFF2E2;color:#986000;font-size:.76rem;font-weight:760}.feedback-card{padding:1rem 1.05rem;border-radius:18px;background:#F1EDFF;border:1px solid #DED5FF;margin:.7rem 0}.feedback-card strong{color:#4F46A5}.signal-card{padding:.85rem .95rem;border-radius:15px;height:100%;border:1px solid #EEE8E2;background:#fff;font-size:.9rem;line-height:1.6}.signal-card.mentor{border-top:4px solid #9B8AFB}.signal-card.hr{border-top:4px solid #FFB45B}.delta-positive{color:#2D8C6F;font-weight:760}.delta-negative{color:#D94F4F;font-weight:760}.delta-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.55rem;margin:.6rem 0}.delta-card{padding:.68rem .75rem;border:1px solid #EEE8E2;border-radius:14px;background:#fff}.history-row{padding:.72rem .85rem;border-left:4px solid #69C0FF;background:#F7FAFF;border-radius:10px;margin:.5rem 0;color:#475467;font-size:.9rem}.complete-summary{display:grid;grid-template-columns:repeat(2,1fr);gap:.75rem;margin:.8rem 0}.summary-card{padding:.9rem 1rem;border-radius:16px;background:#fff;border:1px solid #EEE8E2;box-shadow:0 6px 18px rgba(53,65,92,.045)}.summary-label{font-size:.74rem;color:#667085}.summary-value{font-size:1rem;color:#273142;font-weight:760;margin-top:.25rem}.dev-note{padding:.85rem 1rem;border-radius:15px;background:#FFF8D9;border:1px solid #F5E6A7;color:#6E5600;margin-top:.7rem}
        .companion-panel{position:sticky;top:1rem;padding:1rem;border-radius:24px;background:linear-gradient(160deg,#FFFFFF,#F4F8FF 46%,#F1EDFF);border:1px solid #E7EAF2;box-shadow:0 12px 28px rgba(53,65,92,.075)}.companion-rail{position:fixed;right:28px;top:118px;bottom:28px;width:350px;max-height:none;overflow-y:auto;z-index:999;border-radius:28px;padding:1.15rem;background:linear-gradient(160deg,#FFFFFF 0%,#F4F8FF 48%,#F1EDFF 100%);border:1px solid #DDE6F6;box-shadow:0 18px 42px rgba(53,65,92,.14)}.companion-rail-title{font-size:1rem;font-weight:820;color:#273142;line-height:1.25}.companion-rail-sub{margin-top:.18rem;font-size:.68rem;line-height:1.4;color:#667085}.yaya-rail-wrap{display:flex;justify-content:center;margin:.78rem 0 .68rem}.yaya-rail{position:relative;width:92px;height:86px;border-radius:46% 46% 42% 42%;background:linear-gradient(145deg,#69C0FF,#63D7B0 52%,#9B8AFB);box-shadow:inset 0 -8px 18px rgba(255,255,255,.28),0 10px 22px rgba(91,143,249,.16);animation:yayaBreath 3s ease-in-out infinite}.yaya-stage-icon{position:absolute;right:-8px;top:-8px;padding:.18rem .24rem;border-radius:999px;background:#fff;border:1px solid #DDE6F6;box-shadow:0 6px 14px rgba(53,65,92,.12);font-size:1rem}.yaya-rail:before,.yaya-rail:after{content:"";position:absolute;top:28px;width:10px;height:14px;border-radius:50%;background:#273142}.yaya-rail:before{left:27px}.yaya-rail:after{right:27px}.yaya-rail .yaya-mouth{position:absolute;left:50%;top:51px;width:22px;height:10px;transform:translateX(-50%);border-bottom:3px solid #273142;border-radius:0 0 22px 22px}.yaya-rail.thinking .yaya-mouth{width:18px;height:4px;border-bottom:3px solid #273142;border-radius:999px}.yaya-rail.excited,.yaya-rail.happy{animation:yayaHappy 1.6s ease-in-out infinite}.yaya-rail.sad{animation:yayaSad 2.4s ease-in-out infinite;opacity:.78}.yaya-rail .yaya-sprout{position:absolute;left:50%;top:-14px;width:24px;height:22px;transform:translateX(-50%)}.yaya-rail .yaya-sprout:before,.yaya-rail .yaya-sprout:after{content:"";position:absolute;width:15px;height:10px;border-radius:100% 0 100% 0;background:#63D7B0}.yaya-rail .yaya-sprout:before{left:2px;transform:rotate(-25deg)}.yaya-rail .yaya-sprout:after{right:2px;transform:scaleX(-1) rotate(-25deg)}.yaya-rail.feed{animation:yayaBounce .65s ease}.yaya-rail.level-up{animation:yayaLevel .9s ease}.rail-meta-grid{display:grid;grid-template-columns:1fr;gap:.42rem;margin:.55rem 0}.rail-meta-card{padding:.45rem .55rem;border-radius:12px;background:rgba(255,255,255,.78);border:1px solid #EEE8E2;font-size:.72rem;color:#475467;line-height:1.35}.rail-bag{margin:.55rem 0;padding:.55rem .65rem;border-radius:14px;background:rgba(255,255,255,.78);border:1px solid #EEE8E2;color:#475467;font-size:.74rem}.rail-bag summary{cursor:pointer;font-weight:780;color:#273142}.rail-bag div{margin-top:.34rem}.rail-reaction{margin-top:.55rem;padding:.58rem .65rem;border-radius:14px;background:#EAFBF5;border:1px solid #C8F0E3;color:#356B5C;font-size:.72rem;line-height:1.45}.ai-practice-card{padding:1rem 1.05rem;border-radius:18px;background:linear-gradient(120deg,#EAF3FF,#F1EDFF);border:1px solid #DDE6F6;margin:.85rem 0}.star-burst{position:absolute;inset:-12px;pointer-events:none}.star-burst:before,.star-burst:after{content:"✦";position:absolute;color:#FFD66B;font-size:22px;animation:twinkle 1.1s ease infinite}.star-burst:before{left:6px;top:8px}.star-burst:after{right:4px;bottom:2px}@keyframes yayaBreath{0%,100%{transform:scale(1)}50%{transform:scale(1.025)}}@keyframes yayaHappy{0%,100%{transform:translateY(0) scale(1.02)}50%{transform:translateY(-5px) scale(1.05)}}@keyframes yayaSad{0%,100%{transform:translateY(3px)}50%{transform:translateY(7px)}}@keyframes yayaBounce{0%,100%{transform:translateY(0)}45%{transform:translateY(-12px) scale(1.04)}}@keyframes yayaLevel{0%{transform:scale(.94)}45%{transform:scale(1.12)}100%{transform:scale(1)}}@keyframes twinkle{0%,100%{opacity:.3;transform:scale(.8)}50%{opacity:1;transform:scale(1.2)}}.food-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.45rem;margin:.55rem 0}.food-pill{padding:.48rem .55rem;border-radius:13px;background:#FFFDFB;border:1px solid #EEE8E2;font-size:.78rem;color:#475467}.reaction{padding:.72rem .82rem;border-radius:16px;background:#EAFBF5;border:1px solid #C8F0E3;color:#356B5C;font-size:.86rem;line-height:1.55}.reward-card,.reward-pop{animation:rewardPop .72s cubic-bezier(.2,.9,.2,1);box-shadow:0 12px 30px rgba(255,180,91,.18)}.reward-card{padding:.85rem .95rem;border-radius:18px;background:linear-gradient(120deg,#FFF8D9,#EAFBF5);border:1px solid #EEE8E2;margin:.7rem 0}.celebrate-card{position:relative;overflow:hidden}.celebrate-card:after{content:"";position:absolute;inset:-20%;background:radial-gradient(circle at 20% 30%,rgba(255,214,107,.55),transparent 16%),radial-gradient(circle at 80% 25%,rgba(255,126,182,.45),transparent 15%),radial-gradient(circle at 60% 80%,rgba(99,215,176,.45),transparent 14%);animation:confettiFade 1.8s ease-out forwards;pointer-events:none}.flip-card{padding:.72rem .85rem;border-radius:14px;background:#FFFDFB;border:1px solid #EEE8E2;margin:.4rem 0;animation:cardFlip .55s ease both;transform-origin:center}.tray{padding:.75rem .85rem;border-radius:16px;background:#FFF2E2;border:1px solid #F5DFC0;margin:.6rem 0}.tray strong{color:#9A5C00}.evidence-slot{padding:.72rem .85rem;border-radius:14px;background:#EAFBF5;border:1px solid #C8F0E3;margin:.4rem 0}.reveal-row{padding:.68rem .8rem;border-radius:14px;background:#FFFDFB;border:1px solid #EEE8E2;margin:.4rem 0;animation:cardFlip .5s ease both}.reveal-label{display:inline-block;margin-right:.45rem;padding:.16rem .48rem;border-radius:999px;background:#EAF3FF;color:#3F72C8;font-size:.72rem;font-weight:760}@keyframes rewardPop{0%{transform:scale(.94);opacity:.3}60%{transform:scale(1.035);opacity:1}100%{transform:scale(1)}}@keyframes confettiFade{0%{opacity:0;transform:scale(.9)}25%{opacity:1}100%{opacity:0;transform:scale(1.08)}}@keyframes cardFlip{0%{transform:rotateY(72deg) scale(.98);opacity:.25}100%{transform:rotateY(0) scale(1);opacity:1}}
        .stage-three-card{padding:1rem 1.05rem;border-radius:18px;background:linear-gradient(120deg,#F1EDFF,#FFF0F6);border:1px solid #DED5FF;margin:.75rem 0}.role-card{padding:.85rem .95rem;border-radius:16px;background:#FFFFFF;border:1px solid #EEE8E2;margin:.55rem 0}.scope-board{padding:.8rem .9rem;border-radius:16px;background:#FFFDFB;border:1px solid #EEE8E2;margin:.55rem 0}.resource-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.55rem;margin:.65rem 0}.resource-card{padding:.65rem .75rem;border-radius:14px;background:#EAF3FF;border:1px solid #D3E4FF;font-weight:760;color:#273142}.badge-pill{display:inline-block;margin:.18rem .25rem .18rem 0;padding:.28rem .58rem;border-radius:999px;background:#F1EDFF;color:#6757C8;font-size:.78rem;font-weight:760}.rank-card{padding:.85rem .95rem;border-radius:16px;background:#EAFBF5;border:1px solid #C8F0E3;margin:.55rem 0}.reward-pop{padding:1rem;border-radius:18px;background:linear-gradient(120deg,#FFF8D9,#FFF0F6);border:1px solid #F4DDB9;box-shadow:0 8px 22px rgba(255,180,91,.12);margin:.75rem 0}.hidden-ending{border:2px solid #FFD66B!important;box-shadow:0 16px 36px rgba(255,180,91,.22)!important}
        .game-intro-page{width:100%!important;max-width:none!important;min-height:calc(100vh - 3rem);margin:0!important;padding:1.2rem 1.4rem 2.4rem!important;box-sizing:border-box}.game-intro-shell{width:100%;min-height:calc(100vh - 4rem);display:grid;grid-template-rows:auto auto auto auto;gap:1.25rem}.game-intro-page .intro-hero{min-height:280px;padding:2.35rem 2.6rem;border-radius:32px;margin:0;background:linear-gradient(120deg,#EAF3FF 0%,#FFF0F6 55%,#FFF8D9 100%);box-shadow:0 18px 44px rgba(53,65,92,.10)}.game-intro-page .intro-hero h1{font-size:clamp(3rem,5vw,5rem);line-height:1.05;margin:.35rem 0 .85rem}.game-intro-page .intro-hero p{font-size:1.22rem;line-height:1.75;max-width:1080px}.game-intro-page .game-page-note{font-size:1.02rem;max-width:1080px}.game-intro-page .act-track{margin:0;gap:1.15rem}.game-intro-page .act-item{min-height:92px;padding:.95rem 1rem;border-radius:18px}.game-intro-page .act-name{font-size:1rem}.game-intro-page .act-desc{font-size:.82rem;line-height:1.55}.game-intro-page .game-intro-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1.15rem;margin:0}.game-intro-page .intro-card{min-height:210px;padding:1.45rem 1.5rem;border-radius:24px;background:#FFFFFF;border:1px solid #E7EAF2;box-shadow:0 14px 32px rgba(53,65,92,.075)}.game-intro-page .intro-no{width:38px;height:38px;font-size:.92rem}.game-intro-page .intro-title{font-size:1.28rem;margin:.9rem 0 .5rem}.game-intro-page .intro-text{font-size:1.02rem;line-height:1.72}.intro-main-grid{display:grid;grid-template-columns:1.12fr .88fr;gap:1.35rem;align-items:stretch;margin:0}.intro-panel{min-height:250px;padding:1.65rem 1.75rem;border-radius:28px;background:#FFFFFF;border:1px solid #E7EAF2;box-shadow:0 14px 34px rgba(53,65,92,.075)}.intro-panel h2{font-size:2rem;margin:0 0 1.2rem;color:#273142}.game-intro-page .balance-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.95rem}.game-intro-page .balance-item{min-height:92px;padding:1.1rem 1.2rem;font-size:1.08rem;line-height:1.6;border-radius:20px;display:flex;align-items:center}.intro-goal-card{min-height:170px;padding:1.6rem 1.75rem;border-radius:24px;background:linear-gradient(135deg,#EAF3FF,#F1EDFF);border:1px solid #DDE6F6;display:flex;align-items:center}.intro-goal-card p{margin:0;font-size:1.18rem;line-height:1.82;color:#273142;font-weight:680}.intro-caption{margin-top:.25rem;color:#667085;font-size:.9rem}.intro-start-zone{margin-top:.25rem}.intro-start-zone div[data-testid="stButton"] button{height:64px;border-radius:18px;font-size:1.08rem;font-weight:760}
        @media(max-width:1199px){.companion-rail{position:relative;right:auto;top:auto;bottom:auto;width:100%;max-height:none;margin:1rem 0}}@media(max-width:980px){.game-intro-page .game-intro-grid,.intro-main-grid{grid-template-columns:1fr}.game-intro-page{padding:1rem!important}.game-intro-page .intro-hero{min-height:auto;padding:1.5rem}}@media(max-width:900px){.game-intro-grid,.hud-grid,.ability-grid,.complete-summary,.food-grid{grid-template-columns:1fr}.hud-top{align-items:flex-start;flex-direction:column}.game-hero{min-height:auto}.game-hero h1{font-size:1.9rem}.delta-grid{grid-template-columns:repeat(2,1fr)}.companion-panel{position:relative;top:auto}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_companion_layout_styles() -> None:
    st.markdown(
        """
        <style>
        @media (min-width:1200px) {
            .block-container {
                padding-right: 430px !important;
            }
        }
        @media (max-width:1199px) {
            .block-container {
                padding-right: 1rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _bar(label: str, value: int, css: str = "") -> str:
    safe_label = escape(label)
    return (
        f'<div class="hud-card {css}"><div class="hud-label">{safe_label}</div>'
        f'<div class="hud-value">{value}/100</div><div class="hud-bar">'
        f'<div class="hud-fill {css}" style="width:{value}%"></div></div></div>'
    )


def _render_hud(game: dict[str, Any]) -> None:
    level, title = calculate_level(game["xp"])
    st.markdown(
        '<div class="hud-shell">'
        f'<div class="hud-top"><div class="hud-stage">第{current_week(game)}周·{escape(current_chapter(game))}</div>'
        f'<div class="hud-level">等级{level} {escape(title)} · {game["xp"]}经验值</div></div>'
        '<div class="hud-grid">'
        f'{_bar("精力", game["energy"], "energy")}'
        f'{_bar("导师信任", game["mentor_trust"], "trust")}'
        f'{_bar("风险", game["risk"], "risk")}'
        '</div><div class="hud-grid">'
        f'{_bar("AI协作", game["stats"]["ai_collaboration"])}'
        f'{_bar("结果验证", game["stats"]["verification"])}'
        f'{_bar("独立交付", game["stats"]["delivery"])}'
        '</div></div>',
        unsafe_allow_html=True,
    )
    with st.expander("这些数值会影响什么？"):
        st.markdown(
            """
- 精力：决定高消耗选项是否可用。精力过低会触发高负荷风险，将在后续关卡中生效。
- 导师信任：决定是否能够获得导师支持，以及是否能够解锁更高的独立工作权限，将在后续关卡中生效。
- 风险：风险过高会触发导师或HR介入，并影响最终成长结局，将在后续关卡中生效。
- AI协作：影响AI相关任务和工具使用的完成效果。
- 结果验证：决定新人是否能够识别AI错误、证据不足和安全风险。
- 独立交付：决定新人是否能够通过最终90天评审，将在后续关卡中生效。
            """
        )
    with st.expander("查看完整能力"):
        ability_html = '<div class="ability-grid">'
        for key in STAT_KEYS:
            score = game["stats"][key]
            ability_html += (
                f'<div class="ability-card"><div class="ability-name">{DISPLAY_NAMES[key]}</div>'
                f'<div class="ability-score">{score}</div><div class="ability-bar">'
                f'<div class="ability-fill" style="width:{score}%"></div></div></div>'
            )
        st.markdown(ability_html + "</div>", unsafe_allow_html=True)


def _stage_next_points(points: int) -> int:
    if points < 3:
        return 3 - points
    if points < 6:
        return 6 - points
    if points < 9:
        return 9 - points
    return 0


def render_companion_rail(game: dict[str, Any]) -> None:
    companion = game.get("companion", {})
    inventory = companion.get("food_inventory", {})
    mood = companion.get("mood", "期待")
    mood_class = {"思考": "thinking", "兴奋": "excited", "开心": "happy", "期待": "waiting", "失落": "sad"}.get(mood, "waiting")
    animation = companion.get("animation", "")
    points = int(companion.get("growth_points", 0))
    progress = min(100, round(points / 12 * 100))
    stage = int(companion.get("stage", 1))
    stage_icon = {1: "", 2: "🔎", 3: "📋", 4: "🛡️", 5: "🎧", 6: "👑"}.get(stage, "👑")
    stage_reactions = {
        1: "我会陪你完成这次挑战，先把问题看清楚。",
        2: "我已经进入侦察状态，适合帮你发现AI输出里的可疑点。",
        3: "我开始像任务管家一样提醒你：先处理真正影响交付的事。",
        4: "证据守护者上线，别忘了来源、口径、反例和人工判断。",
        5: "协作信号增强，我会提醒你把导师和团队约束转成行动。",
        6: "终局状态开启，把证据链、AI边界和下一步计划说清楚。",
    }
    reaction = companion.get("last_reaction") or stage_reactions.get(stage, "我会陪你完成这次挑战。")

    star = '<div class="star-burst"></div>' if animation == "level-up" or points >= 9 else ""
    bag_html = "".join(
        f'<div>{escape(defn["name"])}×{int(inventory.get(food_id, 0))}</div>'
        for food_id, defn in FOOD_DEFINITIONS.items()
    )
    st.markdown(
        f'<div class="companion-rail">'
        f'<div class="companion-rail-title">成长搭子·{escape(companion.get("name", "芽芽"))} {escape(stage_icon)}</div>'
        f'<div class="companion-rail-sub">抽象职场成长伙伴｜不用于正式人才评价</div>'
        f'<div class="yaya-rail-wrap"><div class="yaya-rail {mood_class} {escape(animation)}">'
        f'<div class="yaya-sprout"></div>{star}<div class="yaya-stage-icon">{escape(stage_icon or "芽")}</div><div class="yaya-mouth"></div></div></div>'
        f'<div class="summary-label">成长值</div><div class="summary-value">{points}/12 · {escape(companion.get("stage_name", "初来乍到"))}</div>'
        f'<div class="hud-bar"><div class="hud-fill" style="width:{progress}%"></div></div>'
        f'<div class="rail-meta-grid">'
        f'<div class="rail-meta-card">心情：{escape(mood)}</div>'
        f'<div class="rail-meta-card">特质：{escape(companion.get("trait") or "未形成")}</div>'
        f'<div class="rail-meta-card">提示券：{int(companion.get("hint_tokens", 0))}</div>'
        f'<div class="rail-meta-card">下阶段：{_stage_next_points(points)}点</div>'
        f'</div>'
        f'<details class="rail-bag"><summary>背包库存</summary>{bag_html}</details>'
        f'<div class="rail-reaction">{escape(reaction)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _second_act_columns(game: dict[str, Any], renderer) -> None:
    _render_with_companion_rail(game, renderer)


def _companion_columns(game: dict[str, Any], renderer) -> None:
    _render_with_companion_rail(game, renderer)


def _render_with_companion_rail(game: dict[str, Any], renderer) -> None:
    render_companion_rail(game)
    renderer(game)


def _render_scene_with_companion_rail(game: dict[str, Any], scene: dict[str, Any]) -> None:
    render_companion_rail(game)
    _render_scene_header(scene)
    if game["pending_feedback"]:
        _render_feedback(game)
    else:
        _render_options(game, scene)


def _hint_available(game: dict[str, Any]) -> bool:
    companion = game.get("companion", {})
    return int(companion.get("hint_tokens", 0)) > 0 and not game.get("processed_actions", {}).get(f"hint:{game.get('scene_id')}")


def _render_hint_button(game: dict[str, Any], hint_type: str, label: str, text: str, source: str) -> None:
    if game.get("processed_actions", {}).get(f"hint:{game.get('scene_id')}"):
        st.info(f"{label}：{text}")
        return
    if _hint_available(game):
        if st.button(f"{label}（消耗1张提示券）", width="stretch"):
            updated, used = use_stage_two_hint(game, hint_type)
            if used:
                st.session_state.game = updated
                _rerun_top()
    else:
        st.caption(f"暂无可用提示券。提示来源：{source}。")


def _evaluate_prompt(prompt: str) -> tuple[int, list[str], str]:
    checks = [
        ("角色", ["你是", "作为", "扮演", "角色"]),
        ("业务背景", ["背景", "项目", "活动", "用户", "玩家", "业务"]),
        ("目标", ["目标", "请", "需要", "产出", "帮助"]),
        ("输出格式", ["格式", "表格", "清单", "分点", "JSON", "模板"]),
        ("核验要求", ["核验", "来源", "证据", "口径", "验证", "反例"]),
        ("安全边界", ["隐私", "敏感", "脱敏", "不得", "安全"]),
    ]
    matched = [name for name, words in checks if any(word in prompt for word in words)]
    missing = [name for name, _ in checks if name not in matched]
    score = round(len(matched) / len(checks) * 100)
    fallback = (
        "建议改写：你是一名游戏活动策划助理。背景是我需要在60分钟内修复一份活动方案初稿。"
        "请基于脱敏材料输出：1.风险清单；2.需要人工核验的数据来源；3.可评审方案结构；4.不得处理任何个人隐私。"
        "请用表格呈现，并标注哪些结论必须由我本人判断。"
    )
    return score, missing, fallback


def _render_prompt_rewrite_challenge(game: dict[str, Any]) -> None:
    st.markdown('<div class="ai-practice-card"><strong>AI提示词改写挑战</strong><br>先练一次如何让AI帮你审查方案，但不让AI替你做业务判断。</div>', unsafe_allow_html=True)
    prompt_key = f"stage2_prompt_challenge_{game.get('reset_version', 0)}"
    result_key = f"{prompt_key}_result"
    prompt = st.text_area(
        "写下你会给AI的提示词",
        key=prompt_key,
        placeholder="例如：请帮我检查这份活动方案有哪些风险……",
    )
    if st.button("评价并优化提示词", key=f"{prompt_key}_button"):
        score, missing, fallback = _evaluate_prompt(prompt)
        ai_prompt = (
            f"用户提示词：{prompt}\n评分：{score}\n缺失要素：{missing}\n"
            "请给出优化版提示词和一句改进说明。不要要求输入隐私或未授权内部资料。"
        )
        optimized = optional_ai_text("互动闯关提示词改写", ai_prompt, fallback)
        st.session_state[result_key] = {"score": score, "missing": missing, "optimized": optimized}
    result = st.session_state.get(result_key)
    if result:
        missing_text = "、".join(result["missing"]) if result["missing"] else "结构完整"
        st.markdown(
            f'<div class="feedback-card"><strong>提示词完整度：{result["score"]}分</strong><br>'
            f'待补要素：{escape(missing_text)}<br><br>{escape(result["optimized"])}</div>',
            unsafe_allow_html=True,
        )
        st.caption("AI仅用于辅助分析和内容生成，最终判断需由本人、导师或HR确认。")


def _render_act_track(game: dict[str, Any]) -> None:
    current_act = game.get("current_act", "act_one")
    checkpoint_id = game.get("checkpoint_id")
    completed = set()
    if checkpoint_id in {"stage_one_complete", "stage_two_complete", "stage_three_complete"} or current_act in {"act_two", "act_three", "act_four"}:
        completed.add("act_one")
    if checkpoint_id in {"stage_two_complete", "stage_three_complete"} or current_act in {"act_three", "act_four"}:
        completed.add("act_two")
    if checkpoint_id == "stage_three_complete" or current_act == "act_four":
        completed.add("act_three")
    html = '<div class="act-track">'
    for act in GAME_ACTS:
        act_id = act.get("id", "unknown")
        status = "current" if act_id == current_act else "done" if act_id in completed else "locked"
        if act.get("locked") and act_id not in completed and act_id != current_act:
            suffix = "待解锁"
        elif act_id in completed:
            suffix = "✓已完成"
        elif act_id == current_act:
            suffix = "进行中"
        else:
            suffix = "待解锁"
        html += (
            f'<div class="act-item {status}"><div class="act-name">{escape(act.get("name", "未命名阶段"))} · {escape(suffix)}</div>'
            f'<div class="act-desc">{escape(act.get("description", ""))}</div></div>'
        )
    st.markdown(html + "</div>", unsafe_allow_html=True)


def _render_intro_page(game: dict[str, Any]) -> None:
    st.markdown(
        '<div class="game-intro-page"><div class="game-intro-shell">'
        '<section class="game-hero intro-hero">'
        '<div class="game-kicker">互动成长副本</div>'
        '<h1>欢迎进入《职场开局》</h1>'
        '<p>你将在90天内，从职场新人逐步成长为能够独立交付成果的团队成员。</p>'
        '<div class="game-page-note">你将面对真实项目、AI错误、时间冲突、团队协作和导师考验。每一次选择，都会改变你的能力、精力、导师信任和风险。</div>'
        '</section>',
        unsafe_allow_html=True,
    )
    _render_act_track(game)
    cards = [
        ("01", "阅读事件", "面对真实的业务任务、AI失误、团队冲突和风险场景。"),
        ("02", "作出选择", "不同处理方式会在速度、质量、精力和风险之间产生不同结果。"),
        ("03", "观察后果", "系统会立即反馈数值变化、导师信号和HR风险信号。"),
        ("04", "完成成长", "积累经验值，提高能力，并逐步完成90天成长目标。"),
    ]
    st.markdown(
        '<div class="game-intro-grid">' + "".join(
            f'<div class="intro-card"><div class="intro-no">{no}</div><div class="intro-title">{escape(title)}</div><div class="intro-text">{escape(text)}</div></div>'
            for no, title, text in cards
        ) + '</div>'
        '<div class="intro-main-grid">'
        '<section class="intro-panel">'
        '<h2>你需要平衡什么</h2>'
        '<div class="balance-grid">'
        '<div class="balance-item">快速交付与成果质量</div>'
        '<div class="balance-item">AI效率与人工核验</div>'
        '<div class="balance-item">独立推进与及时求助</div>'
        '<div class="balance-item">当前任务与长期成长</div>'
        '</div>'
        '</section>'
        '<section class="intro-panel">'
        '<h2>游戏目标</h2>'
        '<div class="intro-goal-card"><p>在精力没有耗尽、风险可控的情况下，提高AI协作、结果验证和独立交付能力，完成90天最终评审。</p></div>'
        '</section>'
        '</div>'
        '<div class="intro-caption">快速体验约3—5分钟。当前人物、事件和数值均为模拟内容，不用于正式人才评价。</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="intro-start-zone">', unsafe_allow_html=True)
    if st.button("开始我的90天冒险", type="primary", width="stretch"):
        updated = deepcopy(game)
        updated["started"] = True
        updated["scene_id"] = "prologue"
        st.session_state.game = updated
        _rerun_top()
    st.markdown('</div></div></div>', unsafe_allow_html=True)


def _render_scene_header(scene: dict[str, Any]) -> None:
    st.markdown(
        f'<div class="scene-card"><span class="scene-chip">{escape(scene.get("chapter", "剧情事件"))}</span>'
        f'<h2>{escape(scene.get("title", "未命名场景"))}</h2><p>{escape(scene.get("story", ""))}</p></div>',
        unsafe_allow_html=True,
    )


def _render_prologue(game: dict[str, Any]) -> None:
    scene = SCENES["prologue"]
    _render_scene_header(scene)
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("#### 角色身份")
            st.write(scene["role"])
            st.markdown("#### 90天目标")
            st.write(scene["goal"])
    with right:
        with st.expander("查看游戏规则", expanded=True):
            for rule in scene["rules"]:
                st.markdown(f"- {rule}")
    if st.button("进入第1周", type="primary", width="stretch"):
        st.session_state.game = start_game(game)
        _rerun_top()


def _render_options(game: dict[str, Any], scene: dict[str, Any]) -> None:
    for option_id, option in scene.get("options", {}).items():
        with st.container(border=True):
            st.markdown(f'<div class="option-card-title">{option_id}. {escape(option.get("title", option.get("text", "未命名选项")))}</div>', unsafe_allow_html=True)
            st.caption(option.get("description", ""))
            tags = option.get("tradeoffs", ["影响精力、信任、风险和能力"])
            st.markdown(
                '<div class="tradeoff-tags">' + "".join(
                    f'<span class="tradeoff-tag">{escape(tag)}</span>' for tag in tags
                ) + "</div>",
                unsafe_allow_html=True,
            )
            if st.button(f"选择{option_id}", width="stretch"):
                updated, applied = apply_choice(game, game["scene_id"], option_id)
                if applied:
                    st.session_state.game = updated
                    _rerun_top()
                else:
                    st.info("这个选择已经结算，或当前正在等待进入下一幕。")


def _render_feedback(game: dict[str, Any]) -> None:
    feedback = game["pending_feedback"]
    st.markdown(
        f'<div class="feedback-card"><strong>选择反馈·{escape(feedback["option_id"])}</strong><br>'
        f'{escape(feedback["feedback"])}</div>',
        unsafe_allow_html=True,
    )
    st.success(f"获得经验值：{feedback['xp_gained']}")
    mentor_col, hr_col = st.columns(2)
    with mentor_col:
        st.markdown(f'<div class="signal-card mentor"><strong>导师信号</strong><br>{escape(feedback["mentor_signal"])}</div>', unsafe_allow_html=True)
    with hr_col:
        st.markdown(f'<div class="signal-card hr"><strong>HR信号</strong><br>{escape(feedback["hr_signal"])}</div>', unsafe_allow_html=True)
    with st.expander("查看数值变化", expanded=True):
        st.markdown('<div class="delta-grid">' + "".join(
            f'<div class="delta-card"><div class="hud-label">{DISPLAY_NAMES[key]}</div>'
            f'<div class="{"delta-positive" if change["delta"] >= 0 else "delta-negative"}">{change["delta"]:+d}</div>'
            f'<small>{change["before"]}→{change["after"]}</small></div>'
            for key, change in feedback["changes"].items()
        ) + "</div>", unsafe_allow_html=True)
    if st.button("进入下一幕", type="primary", width="stretch"):
        updated, advanced = advance_scene(game)
        if advanced:
            st.session_state.game = updated
            _rerun_top()


def _behavior_summary(game: dict[str, Any]) -> str:
    history = game.get("history", [])
    option_ids = {(item["scene_id"], item["option_id"]) for item in history}
    if ("scene_week2_ai_check", "B") in option_ids:
        return "你愿意投入更多精力换取更稳妥的判断。"
    if ("scene_week2_ai_check", "A") in option_ids:
        return "你重视交付速度，但结果验证风险有所增加。"
    if ("scene_week1_business_map", "C") in option_ids:
        return "你目前较依赖AI，需要增加事实核验。"
    if ("scene_week1_business_map", "A") in option_ids:
        return "你更倾向于先独立分析，再集中向导师求助。"
    return "你能在导师支持和自主推进之间保持相对稳健的节奏。"


def _stage_one_style_description(style: str) -> str:
    descriptions = {
        "独立分析型": "你倾向于先独立建立框架，再带着问题集中校准。",
        "导师协作型": "你善于利用导师快速获得关键路径，但后续需要补足独立产出。",
        "AI效率优先型": "你愿意用AI提高速度，但需要加强资料边界和事实核验。",
        "证据稳健型": "你愿意投入精力保护判断质量，适合承担证据链补强任务。",
        "速度优先型": "你重视交付速度，但需要避免让未经验证的信息进入方案。",
        "成长探索型": "你还在探索自己的工作方式，适合在第二幕观察取舍策略。",
    }
    return descriptions.get(style, descriptions["成长探索型"])


def _largest_improvement(game: dict[str, Any]) -> str:
    deltas = {key: game["stats"][key] - INITIAL_STATS[key] for key in STAT_KEYS}
    key, value = max(deltas.items(), key=lambda item: item[1])
    return f"{DISPLAY_NAMES[key]}+{value}"


def _render_complete(game: dict[str, Any]) -> None:
    level, title = calculate_level(game["xp"])
    st.markdown(
        '<div class="scene-card"><span class="scene-chip">阶段结算</span>'
        '<h2>基础剧情完成</h2>'
        '<p>你已经完成业务地图和AI核验两个关键场景。下一幕将进入方案救火。</p></div>',
        unsafe_allow_html=True,
    )
    preview_context = enter_stage_two(game)["stage_two_context"]
    summary_items = [
        ("当前等级", f"等级{level}·{title}"),
        ("当前经验值", str(game["xp"])),
        ("最大能力提升", _largest_improvement(game)),
        ("当前风险", f"{game['risk']}/100"),
        ("导师信任变化", f"30→{game['mentor_trust']}"),
        ("你的开局风格", preview_context["stage_one_style"]),
    ]
    st.markdown('<div class="complete-summary">' + "".join(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(value)}</div></div>'
        for label, value in summary_items
    ) + "</div>", unsafe_allow_html=True)
    st.info(f"{_stage_one_style_description(preview_context['stage_one_style'])}该结果将影响下一幕中的提示、风险解释和导师支持。")
    with st.expander("查看两次关键选择", expanded=False):
        for item in game["history"]:
            st.markdown(
                f'<div class="history-row"><strong>{escape(item["scene_title"])}</strong><br>'
                f'{escape(item["option_id"])}. {escape(item["option_title"])}</div>',
                unsafe_allow_html=True,
            )
    primary, secondary = st.columns([2, 1])
    with primary:
        if st.button("进入第二幕·方案救火", type="primary", width="stretch"):
            st.session_state.game = enter_stage_two(game)
            _rerun_top()
    with secondary:
        if st.button("重新开始冒险", width="stretch"):
            st.session_state.game = reset_game(game)
            _rerun_top()


def _render_stage_two_briefing(game: dict[str, Any]) -> None:
    scene = SCENES["stage_two_briefing"]
    _render_scene_header(scene)
    context = game.get("stage_two_context") or enter_stage_two(game)["stage_two_context"]
    st.info(context["opening_message"])
    items = [
        ("第一幕行为风格", context["stage_one_style"]),
        ("当前精力", f'{game["energy"]}/100'),
        ("当前导师信任", f'{game["mentor_trust"]}/100'),
        ("当前风险", f'{game["risk"]}/100'),
        ("导师提示", "可用" if context["mentor_hint_available"] else "不可用"),
        ("核验提示", "可用" if context["verification_hint_available"] else "不可用"),
        ("重点风险观察", "是" if context["risk_watch"] else "否"),
        ("精力紧张", "是" if context["low_energy"] else "否"),
    ]
    st.markdown('<div class="complete-summary">' + "".join(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(value)}</div></div>'
        for label, value in items
    ) + "</div>", unsafe_allow_html=True)
    _render_prompt_rewrite_challenge(game)
    if st.button("开始方案审查", type="primary", width="stretch"):
        updated = deepcopy(game)
        updated["scene_id"] = "mini_ai_review"
        st.session_state.game = updated
        _rerun_top()


def _render_minigame_result(result: dict[str, Any], next_label: str, result_key: str, game: dict[str, Any]) -> None:
    st.markdown(
        f'<div class="feedback-card"><strong>提交结果·{result["score"]}分</strong><br>{escape(result["feedback"])}</div>',
        unsafe_allow_html=True,
    )
    mentor_col, hr_col = st.columns(2)
    with mentor_col:
        st.markdown(f'<div class="signal-card mentor"><strong>导师信号</strong><br>{escape(result["mentor_signal"])}</div>', unsafe_allow_html=True)
    with hr_col:
        st.markdown(f'<div class="signal-card hr"><strong>HR信号</strong><br>{escape(result["hr_signal"])}</div>', unsafe_allow_html=True)
    with st.expander("查看数值变化", expanded=True):
        st.markdown('<div class="delta-grid">' + "".join(
            f'<div class="delta-card"><div class="hud-label">{DISPLAY_NAMES[key]}</div>'
            f'<div class="{"delta-positive" if change["delta"] >= 0 else "delta-negative"}">{change["delta"]:+d}</div>'
            f'<small>{change["before"]}→{change["after"]}</small></div>'
            for key, change in result["changes"].items()
        ) + "</div>", unsafe_allow_html=True)
    reward = result.get("food_reward", {})
    st.markdown(
        f'<div class="reward-card"><strong>获得奖励：{escape(reward.get("food_name", ""))}×{int(reward.get("quantity", 0))}</strong><br>'
        f'喂给芽芽后成长值+{int(reward.get("growth_value", 0))}，并解锁下一项挑战。</div>',
        unsafe_allow_html=True,
    )
    fed = game.get("companion", {}).get("fed_rewards", {}).get(result_key)
    if not fed:
        if st.button("喂给芽芽", type="primary", width="stretch", key=f"feed_{result_key}_{game.get('reset_version', 0)}"):
            updated, fed_now, error = feed_companion(game, result_key)
            if fed_now:
                st.session_state.game = updated
                _rerun_top()
            elif error:
                st.warning(error)
        return
    st.success("芽芽已经吃下奖励，可以继续推进。")
    if result.get("remediation_status") == "pending":
        question = REMEDIATION_QUESTIONS.get(result_key, {})
        st.markdown("#### 30秒复盘问题")
        options = question.get("options", {})
        answer = st.radio(
            question.get("question", "复盘问题"),
            list(options.keys()),
            format_func=lambda option_id: options.get(option_id, "未命名选项"),
            key=f"remediation_{result_key}_{game.get('reset_version', 0)}",
        )
        if st.button("提交补救回答", width="stretch", key=f"submit_remediation_{result_key}_{game.get('reset_version', 0)}"):
            updated, applied, error = submit_remediation(game, result_key, answer)
            if applied:
                st.session_state.game = updated
                _rerun_top()
            elif error:
                st.warning(error)
        return
    if result.get("remediation_status") in {"correct", "wrong"}:
        if result.get("remediation_status") == "correct":
            st.info("补救完成：风险-3，原始小游戏分数保持不变。")
        else:
            st.info("补救已完成，原始小游戏分数保持不变，可以继续。")
    if st.button(next_label, type="primary", width="stretch", key=f"next_{result_key}_{game.get('reset_version', 0)}"):
        updated, advanced = advance_after_minigame(game, result_key)
        if advanced:
            st.session_state.game = updated
            _rerun_top()
        else:
            st.info("请先完成喂食或补救问题。")


def _render_ai_review(game: dict[str, Any]) -> None:
    scene = SCENES["mini_ai_review"]
    _render_scene_header(scene)
    st.markdown('<span class="mini-progress">1/3方案审查</span>', unsafe_allow_html=True)
    _render_hint_button(
        game,
        "verification",
        "使用核验提示",
        "分别检查数据来源、因果关系、信息安全和执行约束。",
        "第一幕奖励、导师信任奖励或芽芽成长解锁",
    )
    result = game.get("minigame_results", {}).get("ai_review")
    if result:
        st.write(f"正确识别项：{', '.join(result['correct_ids'])}")
        st.write(f"漏选项：{', '.join(result['missed_ids']) or '无'}")
        st.write(f"错选项：{', '.join(result['false_positive_ids']) or '无'}")
        _render_minigame_result(result, "进入任务优先级决策", "ai_review", game)
        return
    judgements = {}
    judged_count = 0
    for item in AI_REVIEW_ITEMS:
        with st.container(border=True):
            st.markdown(f"**判断项{item['id']}**")
            st.write(item["text"])
            choice = st.radio(
                "你的判断",
                ["unknown", "issue", "reasonable"],
                format_func=lambda value: {"unknown": "暂不确定", "issue": "存在问题", "reasonable": "内容合理"}[value],
                horizontal=True,
                key=f"ai_review_judge_{item['id']}_{game.get('reset_version', 0)}",
            )
            judgements[item["id"]] = choice
            if choice != "unknown":
                judged_count += 1
    st.caption(f"已判断数量：{judged_count}/{len(AI_REVIEW_ITEMS)}")
    if st.button("提交方案审查", type="primary", width="stretch"):
        updated, applied, error = submit_ai_review(game, judgements)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_priority(game: dict[str, Any]) -> None:
    scene = SCENES["mini_priority"]
    _render_scene_header(scene)
    st.markdown('<span class="mini-progress">2/3任务决策</span>', unsafe_allow_html=True)
    _render_hint_button(
        game,
        "mentor",
        "向导师确认优先级",
        "评审前优先处理会改变业务结论或风险判断的任务。",
        "第一幕奖励、导师信任奖励或芽芽成长解锁",
    )
    result = game.get("minigame_results", {}).get("priority")
    if result:
        st.write(f"已选择：{'、'.join(result['selected_names'])}")
        st.write(f"任务预算：{result['total_cost']}/10")
        st.write("组合奖励：已触发" if result["combination_bonus"] else "组合奖励：未触发")
        if result["low_value_busy"]:
            st.warning("识别到低价值忙碌：表层优化多于真实业务补救。")
        _render_minigame_result(result, "进入证据包组装", "priority", game)
        return
    selected = []
    total_cost = 0
    selected_names = []
    st.markdown("#### 候选任务区")
    for task in PRIORITY_TASKS:
        label = f'{task["name"]}｜成本{task["cost"]}｜业务价值{task["business_value"]}｜降风险{task["risk_reduction"]}'
        if st.checkbox(label, key=f"priority_{task['id']}_{game.get('reset_version', 0)}"):
            selected.append(task["id"])
            selected_names.append(task["name"])
            total_cost += int(task["cost"])
    remaining = 10 - total_cost
    st.markdown(
        f'<div class="tray"><strong>本轮任务托盘</strong><br>'
        f'已选：{escape("、".join(selected_names) if selected_names else "暂无")}<br>'
        f'剩余预算：{remaining}/10</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"请选择1—3项。当前已选{len(selected)}项。")
    if total_cost > 10:
        st.error("任务预算超过10点，请减少选择。")
    if st.button("提交优先级决策", type="primary", width="stretch", disabled=total_cost > 10):
        updated, applied, error = submit_priority(game, selected)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_evidence(game: dict[str, Any]) -> None:
    scene = SCENES["mini_evidence"]
    _render_scene_header(scene)
    st.markdown('<span class="mini-progress">3/3证据组装</span>', unsafe_allow_html=True)
    result = game.get("minigame_results", {}).get("evidence")
    if result:
        st.write("已选择证据：")
        for name in result["selected_names"]:
            st.markdown(f"- {name}")
        st.markdown("#### 证据槽位揭示")
        for item in result.get("evidence_reveal", []):
            st.markdown(
                f'<div class="reveal-row"><span class="reveal-label">{escape(item["label"])}</span>{escape(item["text"])}</div>',
                unsafe_allow_html=True,
            )
        _render_minigame_result(result, "查看第二幕综合结算", "evidence", game)
        return
    selected = []
    item_options = [""] + [item["id"] for item in EVIDENCE_ITEMS]
    item_text = {item["id"]: item["text"] for item in EVIDENCE_ITEMS}
    item_text[""] = "空槽位"
    st.markdown("#### 证据库→证据包槽位")
    for slot in range(1, 5):
        choice = st.selectbox(
            f"证据槽位{slot}",
            item_options,
            format_func=lambda item_id: item_text[item_id],
            key=f"evidence_slot_{slot}_{game.get('reset_version', 0)}",
        )
        if choice:
            selected.append(choice)
            st.markdown(f'<div class="evidence-slot">槽位{slot}：{escape(item_text[choice])}</div>', unsafe_allow_html=True)
    selected = list(dict.fromkeys(selected))
    st.caption(f"请选择3—4项证据。当前有效证据{len(selected)}项，重复放入同一证据只计算一次。")
    if st.button("提交证据包", type="primary", width="stretch"):
        updated, applied, error = submit_evidence(game, selected)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_stage_two_complete(game: dict[str, Any]) -> None:
    result = game.get("stage_two_result") or {}
    companion = game.get("companion", {})
    if int(companion.get("growth_points", 0)) >= 9 and not game.get("processed_actions", {}).get("companion:stage_two_balloons"):
        st.balloons()
        updated = deepcopy(game)
        updated["processed_actions"]["companion:stage_two_balloons"] = True
        st.session_state.game = updated
    st.markdown(
        '<div class="scene-card stage-two"><span class="scene-chip">第二幕结算</span>'
        '<h2>你与芽芽共同完成了方案救火。</h2>'
        '<p>你已经把一份存在问题的AI初稿推进到预评审前状态。下面是本幕行为信号和芽芽成长结果。</p></div>',
        unsafe_allow_html=True,
    )
    scores = game.get("stage_two_scores", {})
    eaten = [
        FOOD_DEFINITIONS[result_data.get("food_reward", {}).get("food_id", "")]["name"]
        for result_data in game.get("minigame_results", {}).values()
        if result_data.get("fed") and result_data.get("food_reward", {}).get("food_id") in FOOD_DEFINITIONS
    ]
    summary_items = [
        ("芽芽最终形态", companion.get("stage_name", "初来乍到")),
        ("芽芽成长值", f'{companion.get("growth_points", 0)}/12'),
        ("吃过的食物", "、".join(eaten) if eaten else "暂无"),
        ("宠物特质", companion.get("trait") or "未形成"),
        ("第二幕综合分", str(result.get("overall_score", 0))),
        ("评级", result.get("rating", "-")),
        ("主行为类型", result.get("primary_behavior_type", result.get("behavior_type", "-"))),
        ("风险标签", "、".join(result.get("risk_tags", [])) if result.get("risk_tags") else "无明显风险标签"),
        ("AI方案审查", str(scores.get("ai_review", 0))),
        ("任务优先级", str(scores.get("priority", 0))),
        ("证据包组装", str(scores.get("evidence", 0))),
        ("最大能力提升", _largest_improvement(game)),
        ("当前精力", f'{game["energy"]}/100'),
        ("导师信任", f'{game["mentor_trust"]}/100'),
        ("当前风险", f'{game["risk"]}/100'),
    ]
    st.markdown('<div class="complete-summary">' + "".join(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(value)}</div></div>'
        for label, value in summary_items
    ) + "</div>", unsafe_allow_html=True)
    if int(companion.get("growth_points", 0)) >= 9:
        st.success("芽芽进化为证据守护者。")
    st.info(companion.get("last_reaction", "芽芽记录下了你的方案救火过程。"))
    st.success("方案达到预评审要求" if result.get("passed") else "方案暂未达到预评审要求，需要在协作试炼中补足")
    st.markdown(f'<div class="signal-card"><strong>项目负责人评价</strong><br>{escape(result.get("project_owner_comment", ""))}</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f'<div class="signal-card mentor"><strong>导师下一步建议</strong><br>{escape(result.get("mentor_next_step", ""))}</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div class="signal-card hr"><strong>HR风险判断</strong><br>{escape(result.get("hr_risk_judgement", ""))}</div>', unsafe_allow_html=True)
    primary, secondary = st.columns([2, 1])
    with primary:
        if st.button("进入第三幕·协作试炼", type="primary", width="stretch"):
            st.session_state.game = enter_stage_three(game)
            _rerun_top()
    with secondary:
        if st.button("重新开始冒险", width="stretch"):
            st.session_state.game = reset_game(game)
            _rerun_top()
    if game.get("stage_three_preview"):
        st.info("下一幕·协作试炼：导师临时缺席，程序、美术和运营同时对方案提出质疑。你需要在有限时间内重新定义可执行范围。")


def _render_stage_three_briefing(game: dict[str, Any]) -> None:
    scene = SCENES["stage_three_briefing"]
    _render_scene_header(scene)
    stage_two = game.get("stage_two_result") or {}
    companion = game.get("companion", {})
    progression = game.get("progression", {})
    rank = calculate_anonymous_rank(game)
    badges = progression.get("badges", {})
    items = [
        ("第二幕综合评级", stage_two.get("rating", "-")),
        ("当前风险", f'{game["risk"]}/100'),
        ("导师信任", f'{game["mentor_trust"]}/100'),
        ("芽芽形态", companion.get("stage_name", "初来乍到")),
        ("协作提示", "已解锁" if companion.get("third_act_collaboration_hint") else "未解锁"),
        ("当前徽章", str(len(badges))),
        ("匿名进度位置", f'第{rank["rank"]}/{rank["total"]}名'),
        ("阶段打卡", f'{progression.get("check_in_count", 0)}幕'),
    ]
    st.markdown('<div class="complete-summary">' + "".join(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(value)}</div></div>'
        for label, value in items
    ) + "</div>", unsafe_allow_html=True)
    st.info("模拟匿名榜单仅用于游戏反馈，不代表真实员工数据或正式人才评价。")
    if st.button("开始需求拉齐会", type="primary", width="stretch"):
        updated = deepcopy(game)
        updated["scene_id"] = "stage_three_alignment"
        st.session_state.game = updated
        _rerun_top()


def _render_alignment(game: dict[str, Any]) -> None:
    scene = SCENES["stage_three_alignment"]
    _render_scene_header(scene)
    result = game.get("minigame_results", {}).get("stage_three_alignment")
    if result:
        st.markdown(f'<div class="feedback-card"><strong>需求拉齐得分·{result["score"]}分</strong><br>{escape(result["feedback"])}</div>', unsafe_allow_html=True)
        for item in result["responses"]:
            st.markdown(
                f'<div class="role-card"><strong>第{item["round"]}轮｜{escape(item["role"]["name"])}</strong><br>'
                f'{escape(item["role"]["challenge"])}<br>回应：{escape(item["response_title"])}｜单轮{item["score"]}分</div>',
                unsafe_allow_html=True,
            )
        with st.expander("查看数值变化", expanded=True):
            st.markdown('<div class="delta-grid">' + "".join(
                f'<div class="delta-card"><div class="hud-label">{DISPLAY_NAMES.get(key, key)}</div>'
                f'<div class="{"delta-positive" if change["delta"] >= 0 else "delta-negative"}">{change["delta"]:+d}</div>'
                f'<small>{change["before"]}→{change["after"]}</small></div>'
                for key, change in result["changes"].items()
            ) + "</div>", unsafe_allow_html=True)
        if st.button("进入范围取舍板", type="primary", width="stretch"):
            updated, advanced = advance_stage_three_scene(game, "stage_three_alignment")
            if advanced:
                st.session_state.game = updated
                _rerun_top()
        return
    rounds = get_stage_three_alignment_rounds(game)
    responses = []
    st.markdown('<span class="mini-progress">1/3需求拉齐</span>', unsafe_allow_html=True)
    for index, role in enumerate(rounds, start=1):
        role_options = ALIGNMENT_OPTIONS_BY_ROLE[role["id"]]
        st.markdown(
            f'<div class="role-card"><strong>第{index}/3轮｜{escape(role["name"])}</strong><br>{escape(role["challenge"])}</div>',
            unsafe_allow_html=True,
        )
        choice = st.radio(
            "选择回应方式",
            ["A", "B", "C"],
            format_func=lambda option_id, options=role_options: f'{option_id}. {options.get(option_id, {}).get("title", options.get(option_id, {}).get("text", "未命名回应"))}',
            key=f"alignment_round_{index}_{game.get('reset_version', 0)}",
        )
        st.caption(role_options[choice].get("description", ""))
        responses.append(choice)
    if st.button("提交需求拉齐结果", type="primary", width="stretch"):
        updated, applied, error = submit_alignment(game, responses)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_scope(game: dict[str, Any]) -> None:
    scene = SCENES["stage_three_scope"]
    _render_scene_header(scene)
    result = game.get("minigame_results", {}).get("stage_three_scope")
    if result:
        st.markdown(f'<div class="feedback-card"><strong>范围取舍得分·{result["score"]}分</strong><br>{escape(result["feedback"])}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="resource-grid"><div class="resource-card">必做开发：{result["must_cost"]["dev"]}/{SCOPE_BUDGET["dev"]}</div>'
            f'<div class="resource-card">必做美术：{result["must_cost"]["art"]}/{SCOPE_BUDGET["art"]}</div>'
            f'<div class="resource-card">必做时间：{result["must_cost"]["time"]}/{SCOPE_BUDGET["time"]}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="resource-grid"><div class="resource-card">备用开发：{result["optional_cost"]["dev"]}</div>'
            f'<div class="resource-card">备用美术：{result["optional_cost"]["art"]}</div>'
            f'<div class="resource-card">备用时间：{result["optional_cost"]["time"]}</div></div>',
            unsafe_allow_html=True,
        )
        for title, key in [("必做任务", "must_tasks"), ("可选任务", "optional_tasks"), ("延后任务", "delayed_tasks")]:
            names = [task["name"] for task in result.get(key, [])]
            st.markdown(f"**{title}**：{escape('、'.join(names) if names else '暂无')}")
        if result.get("delay_summary"):
            with st.expander("延期说明", expanded=True):
                for item in result["delay_summary"]:
                    st.markdown(f'- {item["task_name"]}：{item["reason"]}')
        if result.get("ideal_plan"):
            st.success("形成了完整且可回滚的理想最小可行方案。")
        elif result.get("has_mvp"):
            st.info("已经形成可执行最小可行方案，但仍有优化空间。")
        else:
            st.warning("尚未形成最小可行方案。")
        if result["missing_core"]:
            st.warning("核心活动机制缺失。")
        if result["missing_risk"]:
            st.warning("风险监控或回滚方案缺失。")
        if result["visual_heavy"]:
            st.warning("范围失衡：视觉或传播功能多于可执行核心。")
        if st.button("进入随机额外任务", type="primary", width="stretch"):
            updated, advanced = advance_stage_three_scene(game, "stage_three_scope")
            if advanced:
                st.session_state.game = updated
                _rerun_top()
        return
    st.markdown('<span class="mini-progress">2/3范围取舍</span>', unsafe_allow_html=True)
    slot_options = ["unclassified", "must", "optional", "delayed"]
    slot_names = {"unclassified": "未分类", "must": "必做", "optional": "可选", "delayed": "延后"}
    selected_scope = {"must": [], "optional": [], "delayed": []}
    for task in SCOPE_TASKS:
        with st.container(border=True):
            st.markdown(f'**{task["name"]}**')
            st.caption(f'开发{task["dev"]}｜美术{task["art"]}｜时间{task["time"]}｜业务价值{task["business"]}｜风险价值{task["risk"]}')
            slot = st.radio(
                "放入槽位",
                slot_options,
                format_func=lambda value: slot_names[value],
                horizontal=True,
                key=f"scope_{task['id']}_{game.get('reset_version', 0)}",
            )
            if slot != "unclassified":
                selected_scope[slot].append(task["id"])
    plan = calculate_scope_plan(selected_scope)
    st.markdown(
        f'<div class="resource-grid"><div class="resource-card">必做开发：{plan["must_cost"]["dev"]}/{SCOPE_BUDGET["dev"]}</div>'
        f'<div class="resource-card">必做美术：{plan["must_cost"]["art"]}/{SCOPE_BUDGET["art"]}</div>'
        f'<div class="resource-card">必做时间：{plan["must_cost"]["time"]}/{SCOPE_BUDGET["time"]}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="resource-grid"><div class="resource-card">备用开发：{plan["optional_cost"]["dev"]}</div>'
        f'<div class="resource-card">备用美术：{plan["optional_cost"]["art"]}</div>'
        f'<div class="resource-card">备用时间：{plan["optional_cost"]["time"]}</div></div>',
        unsafe_allow_html=True,
    )
    must_names = [task["name"] for task in SCOPE_TASKS if task["id"] in plan["must"]]
    st.markdown(f'<div class="tray"><strong>当前必做任务</strong><br>{escape("、".join(must_names) if must_names else "暂无")}</div>', unsafe_allow_html=True)
    if any(plan["over_budget"].values()):
        st.error("当前必做任务预算超限。")
    if plan["missing_core"]:
        st.warning("风险提示：核心活动机制缺失。")
    if plan["missing_risk"]:
        st.warning("风险提示：风险监控或回滚方案至少需要一个。")
    if plan["has_mvp"]:
        st.success("当前范围已接近可上线最小方案。")
    st.caption(f"未分类数量：{len(plan['missing'])}")
    if plan["missing"]:
        st.warning(f"仍有{len(plan['missing'])}项任务未分类。")
    if st.button("提交范围取舍", type="primary", width="stretch", disabled=any(plan["over_budget"].values()) or bool(plan["missing"])):
        updated, applied, error = submit_scope(game, selected_scope)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_random_event(game: dict[str, Any]) -> None:
    if not game.get("stage_three", {}).get("random_event_id"):
        from game_engine import ensure_random_event
        st.session_state.game = ensure_random_event(game)
        _rerun_top()
    event = current_random_event(game)
    scene = SCENES["stage_three_random_event"]
    _render_scene_header(scene)
    st.markdown('<span class="mini-progress">3/3临场应变</span>', unsafe_allow_html=True)
    st.markdown('<div class="reward-pop"><strong>抽取突发事件盲盒</strong><br>本轮事件已由随机种子固定，刷新不会重复抽取。额外任务失败不会影响基础成绩；成功只增加奖励分并掉落奖励。</div>', unsafe_allow_html=True)
    result = game.get("stage_three", {}).get("bonus_task_result")
    if result:
        if result["success"]:
            st.success("额外任务成功，不影响主线评分，并获得一次随机奖励。")
            reward = result.get("reward") or {}
            st.markdown(f'<div class="reward-pop"><strong>掉落奖励：{escape(reward.get("name", ""))}×{int(reward.get("quantity", 0))}</strong></div>', unsafe_allow_html=True)
            if not game.get("stage_three", {}).get("reward_claimed"):
                if st.button("领取随机奖励", type="primary", width="stretch"):
                    updated, claimed, error = claim_random_reward(game)
                    if claimed:
                        st.session_state.game = updated
                        _rerun_top()
                    elif error:
                        st.warning(error)
                return
            st.info("随机奖励已领取，刷新不会重复掉落。")
            if game.get("minigame_results", {}).get("stage_three_reward") and not game.get("companion", {}).get("fed_rewards", {}).get("stage_three_reward"):
                if st.button("把随机食物喂给芽芽", type="primary", width="stretch"):
                    updated, fed, error = feed_companion(game, "stage_three_reward")
                    if fed:
                        st.session_state.game = updated
                        _rerun_top()
                    elif error:
                        st.warning(error)
                return
        else:
            st.info("额外任务没有成功，但不会扣分、扣资源或增加风险。")
        if st.button("进入第三幕综合结算", type="primary", width="stretch"):
            st.session_state.game = complete_stage_three(game)
            _rerun_top()
        return
    st.markdown(
        f'<div class="stage-three-card flip-card"><strong>盲盒事件：{escape(event.get("title", "未命名事件"))}</strong><br>{escape(event.get("challenge", ""))}</div>',
        unsafe_allow_html=True,
    )
    event_options = event.get("options", {})
    choice = st.radio(
        "选择应对方式",
        list(event_options.keys()),
        format_func=lambda option_id: f'{option_id}. {event_options.get(option_id, {}).get("text", "未命名选项")}',
        key=f"random_event_{event.get('id', 'unknown')}_{game.get('reset_version', 0)}",
    )
    if st.button("提交临场应变", type="primary", width="stretch"):
        updated, applied, error = submit_random_event(game, choice)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_stage_three_complete(game: dict[str, Any]) -> None:
    result = game.get("stage_three_result") or {}
    stage_three = game.get("stage_three", {})
    progression = game.get("progression", {})
    companion = game.get("companion", {})
    badges = progression.get("badges", {})
    rank = result.get("anonymous_rank") or calculate_anonymous_rank(game)
    st.markdown(
        '<div class="scene-card stage-two"><span class="scene-chip">第三幕结算</span>'
        '<h2>协作试炼完成</h2><p>你把预评审后的方案推进到了团队可执行版本判断。</p></div>',
        unsafe_allow_html=True,
    )
    summary_items = [
        ("需求拉齐得分", str(stage_three.get("alignment_score", 0))),
        ("范围取舍得分", str(stage_three.get("scope_score", 0))),
        ("随机任务", "成功" if stage_three.get("bonus_task_result", {}).get("success") else "未成功"),
        ("基础协作分", str(result.get("base_score", 0))),
        ("随机奖励分", str(result.get("bonus_points", 0))),
        ("最终综合分", str(result.get("overall_score", 0))),
        ("第三幕评级", result.get("rating", "-")),
        ("团队信任", f'{stage_three.get("team_trust", 0)}/100'),
        ("范围清晰度", f'{stage_three.get("clarity", 0)}/100'),
        ("芽芽新形态", companion.get("stage_name", "初来乍到")),
        ("匿名榜名次", f'第{rank["rank"]}/{rank["total"]}名'),
        ("超过匿名玩家", f'{rank["percentile"]}%'),
    ]
    st.markdown('<div class="complete-summary">' + "".join(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(value)}</div></div>'
        for label, value in summary_items
    ) + "</div>", unsafe_allow_html=True)
    if badges:
        st.markdown("#### 获得徽章")
        st.markdown("".join(f'<span class="badge-pill">{escape(badge["name"])}</span>' for badge in badges.values()), unsafe_allow_html=True)
    rewards = progression.get("reward_history", [])
    if rewards:
        st.markdown("#### 获得奖励")
        st.markdown("、".join(escape(item["name"]) for item in rewards))
    st.success("已经形成团队可执行版本" if result.get("executable") else "暂未形成稳定的团队可执行版本，但主线不会中断")
    if result.get("blocking_reasons"):
        st.warning("阻塞原因：" + "、".join(result["blocking_reasons"]))
    st.markdown(f'<div class="signal-card mentor"><strong>导师建议</strong><br>{escape(result.get("mentor_advice", ""))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="signal-card hr"><strong>HR行为信号</strong><br>{escape(result.get("hr_signal", ""))}</div>', unsafe_allow_html=True)
    st.info("模拟匿名榜单仅用于游戏反馈，不代表真实员工数据或正式人才评价。")
    primary, secondary = st.columns([2, 1])
    with primary:
        if st.button("进入第四幕·成果验收", type="primary", width="stretch"):
            st.session_state.game = enter_stage_four(game)
            _rerun_top()
    with secondary:
        if st.button("重新开始冒险", width="stretch"):
            st.session_state.game = reset_game(game)
            _rerun_top()
    st.info("下一幕：成果验收。你需要装配最终证据包，并接受导师问答与终局评审。")


def _stage_four_card_map() -> dict[str, dict[str, Any]]:
    if isinstance(STAGE_FOUR_EVIDENCE_CARDS, dict):
        return STAGE_FOUR_EVIDENCE_CARDS
    return {
        str(card.get("id")): card
        for card in STAGE_FOUR_EVIDENCE_CARDS
        if isinstance(card, dict) and card.get("id")
    }


def _card_label(card_id: str) -> str:
    card = _stage_four_card_map().get(card_id, {})
    slot = card.get("slot")
    quality = card.get("quality", "unknown")
    slot_name = STAGE_FOUR_SLOT_NAMES.get(slot, "支撑证据") if slot else "支撑证据"
    return f'{card.get("name", card_id)}｜{slot_name}｜{quality}'


def _render_stage_four_briefing(game: dict[str, Any]) -> None:
    companion = game.get("companion", {})
    stage_three = game.get("stage_three_result") or {}
    stage_two = game.get("stage_two_result") or {}
    stage_three_state = game.get("stage_three", {})
    progression = game.get("progression", {})
    scope_result = (game.get("minigame_results", {}).get("stage_three_scope") or {})
    rank = calculate_anonymous_rank(game)
    st.markdown(
        '<div class="scene-card stage-two"><span class="scene-chip">第四幕·成果验收</span>'
        '<h2>最终评审将在30分钟后开始</h2><p>前三幕中，你已经完成方案修复、团队拉齐和范围取舍。现在需要把分散的成果整理成可以被追问、被核验、被执行的最终交付。</p></div>',
        unsafe_allow_html=True,
    )
    items = [
        ("第一幕风格", (game.get("stage_two_context") or {}).get("stage_one_style", "成长探索型")),
        ("第二幕评级", stage_two.get("rating", "-")),
        ("第三幕结果", "团队可执行" if stage_three.get("executable") else "仍需补强"),
        ("第三幕评级", stage_three.get("rating", "-")),
        ("当前风险", f'{game.get("risk", 0)}/100'),
        ("导师信任", f'{game.get("mentor_trust", 0)}/100'),
        ("团队信任", f'{stage_three_state.get("team_trust", 0)}/100'),
        ("徽章数量", len(progression.get("badges", {}))),
        ("徽章碎片", progression.get("badge_fragments", 0)),
        ("提示券", companion.get("hint_tokens", 0)),
        ("芽芽形态", companion.get("stage_name", "初来乍到")),
        ("理想最小可行方案", "已形成" if scope_result.get("ideal_plan") else "仍有优化空间"),
        ("匿名进度", f'第{rank["rank"]}/{rank["total"]}名'),
    ]
    st.markdown('<div class="complete-summary">' + "".join(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(str(value))}</div></div>'
        for label, value in items
    ) + "</div>", unsafe_allow_html=True)
    st.info("终局评审不会改变正式成长证据链。这里产生的是互动闯关行为信号，仅保存在当前会话。")
    if st.button("整理终局装备", type="primary", width="stretch"):
        updated = prepare_stage_four_loadout(game)
        updated["scene_id"] = "stage_four_loadout"
        st.session_state.game = updated
        _rerun_top()


def _render_stage_four_loadout(game: dict[str, Any]) -> None:
    game = prepare_stage_four_loadout(game)
    stage_four = game.get("stage_four", {})
    loadout = stage_four.get("loadout", {})
    companion = game.get("companion", {})
    progression = game.get("progression", {})
    st.markdown(
        '<div class="scene-card"><span class="scene-chip">终局装备</span>'
        '<h2>选择你带进评审室的资源</h2><p>提示券、重抽卡、证据强化卡和协作提示卡只能提供轻量辅助，不会替你完成判断。</p></div>',
        unsafe_allow_html=True,
    )
    items = [
        ("提示券", loadout.get("hint_tokens", companion.get("hint_tokens", 0))),
        ("重抽卡", loadout.get("reroll_cards", 0)),
        ("证据强化卡", loadout.get("evidence_boost_cards", 0)),
        ("协作提示卡", loadout.get("collaboration_cards", 0)),
        ("徽章碎片", progression.get("badge_fragments", 0)),
    ]
    st.markdown('<div class="complete-summary">' + "".join(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(str(value))}</div></div>'
        for label, value in items
    ) + "</div>", unsafe_allow_html=True)
    if progression.get("badge_fragments", 0) >= 3:
        if st.button("消耗3枚徽章碎片兑换1张重抽卡", width="stretch"):
            updated, applied, error = exchange_badge_fragments(game)
            if applied:
                st.session_state.game = updated
                _rerun_top()
            elif error:
                st.warning(error)
    st.markdown('<div class="dev-note">装备会在导师追问中消耗。证据板阶段仍主要依靠你选择的真实证据。</div>', unsafe_allow_html=True)
    if st.button("进入证据板", type="primary", width="stretch"):
        updated = deepcopy(game)
        updated["scene_id"] = "stage_four_evidence"
        st.session_state.game = updated
        _rerun_top()


def _render_stage_four_evidence(game: dict[str, Any]) -> None:
    board = game.get("stage_four", {}).get("evidence_board", {})
    st.markdown(
        '<div class="scene-card evidence"><span class="scene-chip">终局证据板</span>'
        '<h2>装配四格证据链</h2><p>分别为用户证据、数据证据、执行证据和风险证据选择最能支撑方案的材料。</p></div>',
        unsafe_allow_html=True,
    )
    if board.get("submitted"):
        st.success(f'证据板得分：{board.get("score", 0)}｜覆盖度：{board.get("coverage", 0)}')
        for slot_id, result in (board.get("slot_results") or {}).items():
            status = result.get("label", "需补强")
            st.markdown(
                f'<div class="reveal-row flip-card"><span class="reveal-label">{escape(STAGE_FOUR_SLOT_NAMES.get(slot_id, slot_id))}</span>'
                f'{escape(result.get("card_name", "-"))}｜{escape(status)}｜{escape(str(result.get("score", 0)))}分</div>',
                unsafe_allow_html=True,
            )
        if board.get("weak_slots"):
            st.warning("薄弱槽位：" + "、".join(STAGE_FOUR_SLOT_NAMES.get(slot, slot) for slot in board["weak_slots"]))
        if board.get("strong_combinations"):
            st.info("组合加成：" + "、".join(board["strong_combinations"]))
        if st.button("进入导师追问", type="primary", width="stretch"):
            updated = ensure_boss_questions(game)
            updated["scene_id"] = "stage_four_boss"
            st.session_state.game = updated
            _rerun_top()
        return

    card_map = _stage_four_card_map()
    card_options = [""] + list(card_map.keys())
    slots: dict[str, str | None] = {}
    cols = st.columns(2)
    for index, slot_id in enumerate(("user", "data", "execution", "risk")):
        with cols[index % 2]:
            value = st.selectbox(
                STAGE_FOUR_SLOT_NAMES[slot_id],
                card_options,
                format_func=lambda card_id: "请选择证据卡" if not card_id else _card_label(card_id),
                key=f"stage4_slot_{slot_id}_{game.get('reset_version', 0)}",
            )
            slots[slot_id] = value or None
    selected = [card for card in slots.values() if card]
    if len(selected) != len(set(selected)):
        st.warning("同一张证据卡不能放入多个核心槽位。")
    support_options = [""] + [card_id for card_id in card_map.keys() if card_id not in selected]
    support_one = st.selectbox(
        "支撑证据1",
        support_options,
        format_func=lambda card_id: "不选择" if not card_id else _card_label(card_id),
        key=f"stage4_support_one_{game.get('reset_version', 0)}",
    )
    support_two_options = [""] + [card_id for card_id in support_options if card_id and card_id != support_one]
    support_two = st.selectbox(
        "支撑证据2",
        support_two_options,
        format_func=lambda card_id: "不选择" if not card_id else _card_label(card_id),
        key=f"stage4_support_two_{support_one}_{game.get('reset_version', 0)}",
    )
    support_cards = [card_id for card_id in [support_one, support_two] if card_id]
    if support_cards:
        st.markdown("".join(f'<div class="flip-card">{escape(_card_label(card_id))}</div>' for card_id in support_cards), unsafe_allow_html=True)
    if st.button("提交终局证据板", type="primary", width="stretch"):
        missing_slots = [STAGE_FOUR_SLOT_NAMES.get(slot_id, slot_id) for slot_id, card_id in slots.items() if not card_id]
        if missing_slots:
            st.warning("请先补齐主槽位：" + "、".join(missing_slots))
            return
        if len(support_cards) > 2:
            st.warning("最多只能选择2张支撑证据，请先取消一张再继续。")
            return
        updated, applied, error = submit_stage_four_evidence(game, slots, support_cards)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_stage_four_boss(game: dict[str, Any]) -> None:
    game = ensure_boss_questions(game)
    st.session_state.game = game
    stage_four = game.get("stage_four", {})
    boss = stage_four.get("boss", {})
    questions = boss.get("questions", [])
    index = int(boss.get("current_index", 0))
    st.markdown(
        '<div class="scene-card stage-two"><span class="scene-chip">终局导师追问</span>'
        '<h2>导师开始连续追问</h2><p>每一次回答都会影响可信度。你可以消耗装备获得有限帮助，但最终判断仍由你完成。</p></div>',
        unsafe_allow_html=True,
    )
    st.metric("当前可信度", boss.get("credibility", 70))
    if boss.get("completed") or index >= len(questions):
        st.success(f'导师追问均分：{boss.get("score", 0)}')
        next_label = "进入补答环节" if boss.get("remediation_tasks") else "进入隐藏挑战"
        if st.button(next_label, type="primary", width="stretch"):
            updated = advance_boss_question(game)
            st.session_state.game = updated
            _rerun_top()
        return

    question = normalize_boss_question(questions[index])
    question_id = question.get("id", f"boss_{index}")
    if not question.get("prompt") and not question.get("body"):
        st.warning("当前题目数据不完整，请返回上一页重试。")
        return
    question_title = question.get("title", "导师追问")
    question_body = question.get("body") or question.get("prompt") or ""
    question_focus = question.get("focus", "导师当前关注证据、边界和下一步行动。")
    st.markdown(
        f'<div class="stage-three-card"><strong>第{index + 1}/{len(questions)}问：{escape(question_title)}</strong><br>'
        f'{escape(question_body)}<br><span class="game-page-note">关注点：{escape(question_focus)}</span></div>',
        unsafe_allow_html=True,
    )
    used = boss.get("used_items", [])
    loadout = stage_four.get("loadout", {})
    item_cols = st.columns(4)
    item_defs = [
        ("hint_token", "使用提示券", loadout.get("hint_tokens", 0)),
        ("reroll_card", "使用重抽卡", loadout.get("reroll_cards", 0)),
        ("evidence_boost", "使用证据强化", loadout.get("evidence_boost_cards", 0)),
        ("collaboration_card", "使用协作提示", loadout.get("collaboration_cards", 0)),
    ]
    for col, (item_id, label, count) in zip(item_cols, item_defs):
        with col:
            disabled = count <= 0 or any(item.get("item_id") == item_id and item.get("question_id") == question_id for item in used)
            if st.button(f"{label}({count})", disabled=disabled, width="stretch", key=f"stage4_item_{item_id}_{question_id}"):
                updated, applied, error = use_stage_four_item(game, item_id, question_id)
                if applied:
                    st.session_state.game = updated
                    _rerun_top()
                elif error:
                    st.warning(error)
    if any(item.get("item_id") == "hint_token" and item.get("question_id") == question_id for item in used):
        st.info("提示：先说明你依据了哪些证据，再承认边界，最后给出下一步行动。")
    if any(item.get("item_id") == "collaboration_card" and item.get("question_id") == question_id for item in used):
        st.info("协作提示：把程序、美术、运营或产品的约束转成共同可执行标准。")
    if any(item.get("item_id") == "evidence_boost" and item.get("question_id") == question_id for item in used):
        st.info("证据强化已生效：本题会小幅提升证据表达得分。")

    defense_key = f"boss_defense_{question_id}_{game.get('reset_version', 0)}"
    defense_result_key = f"{defense_key}_result"
    st.markdown("#### 导师主观答辩")
    defense = st.text_area(
        "如何证明这不是AI代写，而是你的业务判断？",
        key=defense_key,
        placeholder="请说明你使用了哪些证据、哪些判断由你完成、AI边界在哪里、下一步如何验证。",
    )
    if st.button("评价主观答辩", key=f"{defense_key}_button"):
        signals = {
            "证据": any(word in defense for word in ["证据", "来源", "访谈", "数据", "口径"]),
            "人工判断": any(word in defense for word in ["我判断", "本人", "人工", "取舍", "负责"]),
            "AI边界": any(word in defense for word in ["AI", "边界", "辅助", "不能", "不得"]),
            "行动方案": any(word in defense for word in ["下一步", "验证", "小流量", "复盘", "回滚"]),
        }
        score = sum(25 for passed in signals.values() if passed)
        fallback = (
            f"主观答辩完整度：{score}分。"
            f"已覆盖：{'、'.join(name for name, passed in signals.items() if passed) or '暂无'}。"
            "建议补充证据来源、本人取舍、AI仅辅助的边界，以及下一步验证动作。"
        )
        prompt = f"答辩文本：{defense}\n评分信号：{signals}\n请用导师口吻给出追问和改写建议。"
        st.session_state[defense_result_key] = optional_ai_text("导师主观答辩反馈", prompt, fallback)
    if st.session_state.get(defense_result_key):
        st.markdown(f'<div class="feedback-card">{escape(st.session_state[defense_result_key])}</div>', unsafe_allow_html=True)
        st.caption("AI仅用于辅助分析和内容生成，最终判断需由本人、导师或HR确认。")

    answered = [answer for answer in boss.get("answers", []) if answer.get("question_id") == question_id]
    if answered:
        last = answered[-1]
        st.markdown(
            f'<div class="feedback-card"><strong>本题得分：{last.get("score", 0)}</strong><br>{escape(last.get("feedback", ""))}</div>',
            unsafe_allow_html=True,
        )
        if st.button("进入下一问", type="primary", width="stretch"):
            st.session_state.game = advance_boss_question(game)
            _rerun_top()
        return

    answers = question.get("answers", {})
    if not answers:
        st.warning("当前题目选项数据不完整，请返回上一页重试。")
        return
    answer_id = st.radio(
        "选择你的回答",
        list(answers.keys()),
        format_func=lambda option_id: f'{option_id}. {answers.get(option_id, {}).get("text", "未命名回答")}',
        key=f"boss_answer_{question_id}_{game.get('reset_version', 0)}",
    )
    if st.button("提交回答", type="primary", width="stretch"):
        updated, applied, error = submit_boss_answer(game, answer_id)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_stage_four_remediation(game: dict[str, Any]) -> None:
    boss = game.get("stage_four", {}).get("boss", {})
    tasks = boss.get("remediation_tasks", [])
    st.markdown(
        '<div class="scene-card"><span class="scene-chip">导师补答</span>'
        '<h2>可信度触底后的补救</h2><p>补答只帮助你恢复可信度，不改写原始追问得分。</p></div>',
        unsafe_allow_html=True,
    )
    if not tasks:
        st.info("当前没有补答任务。")
        if st.button("进入隐藏挑战", type="primary", width="stretch"):
            updated = deepcopy(game)
            updated["scene_id"] = "stage_four_bonus"
            st.session_state.game = updated
            _rerun_top()
        return
    pending = [task for task in tasks if not task.get("completed")]
    if not pending:
        st.success("补答任务已完成。")
        if st.button("进入隐藏挑战", type="primary", width="stretch"):
            updated = deepcopy(game)
            updated["scene_id"] = "stage_four_bonus"
            st.session_state.game = updated
            _rerun_top()
        return
    task = pending[0]
    st.warning(task.get("question", "请补充关键证据和行动计划。"))
    answer = st.radio(
        "选择补答方向",
        ["补充证据来源、边界和下一步验证动作", "重复强调方案已经足够完整"],
        key=f"stage4_remediation_{task['id']}_{game.get('reset_version', 0)}",
    )
    if st.button("提交补答", type="primary", width="stretch"):
        updated, applied, error = submit_remediation_task(game, task["id"], answer.startswith("补充证据"))
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_stage_four_bonus(game: dict[str, Any]) -> None:
    game = ensure_stage_four_bonus(game)
    event = current_stage_four_bonus(game)
    bonus = game.get("stage_four", {}).get("bonus_task", {})
    st.markdown(
        '<div class="scene-card evidence"><span class="scene-chip">隐藏挑战</span>'
        f'<h2>{escape(event.get("title", "终局彩蛋"))}</h2><p>{escape(event.get("description", ""))}</p></div>',
        unsafe_allow_html=True,
    )
    if bonus.get("submitted"):
        if bonus.get("success"):
            st.success("隐藏挑战成功，获得终局加分和隐藏碎片。")
            if not bonus.get("reward_claimed"):
                if st.button("领取隐藏奖励", type="primary", width="stretch"):
                    updated, applied, error = claim_stage_four_bonus_reward(game)
                    if applied:
                        st.session_state.game = updated
                        _rerun_top()
                    elif error:
                        st.warning(error)
                    return
        else:
            st.info("隐藏挑战未成功，但不会扣分，也不会阻断通关。")
        if st.button("进入终局结算", type="primary", width="stretch"):
            st.session_state.game = complete_stage_four(game)
            _rerun_top()
        return
    option_id = st.radio(
        "选择应对方式",
        list(event.get("options", {}).keys()),
        format_func=lambda key: f'{key}. {event.get("options", {}).get(key, {}).get("text", "未命名选项")}',
        key=f"stage4_bonus_{event.get('id')}_{game.get('reset_version', 0)}",
    )
    if st.button("提交隐藏挑战", type="primary", width="stretch"):
        updated, applied, error = submit_stage_four_bonus(game, option_id)
        if applied:
            st.session_state.game = updated
            _rerun_top()
        elif error:
            st.warning(error)


def _render_stage_four_complete(game: dict[str, Any]) -> None:
    result = game.get("stage_four", {}).get("final_result") or {}
    ending_id = game.get("ending_id") or result.get("ending_id") or "high_potential"
    ending = ENDING_DEFINITIONS.get(ending_id, ENDING_DEFINITIONS["high_potential"])
    rank = calculate_anonymous_rank(game)
    ending_class = "celebrate-card hidden-ending" if ending_id == "yaya_partner" else "celebrate-card"
    st.markdown(
        f'<div class="scene-card stage-two {ending_class}"><span class="scene-chip">终局结算</span>'
        '<h2>90天成果验收完成</h2><p>你完成了证据装配、导师追问和终局挑战。现在可以进入成长基地查看归档与复盘。</p></div>',
        unsafe_allow_html=True,
    )
    items = [
        ("最终结局", ending["name"]),
        ("终局总分", result.get("final_score", 0)),
        ("证据板", result.get("evidence_score", 0)),
        ("导师追问", result.get("boss_score", 0)),
        ("隐藏加分", result.get("bonus_points", 0)),
        ("是否通过", "通过终局评审" if result.get("final_passed") else "保留成长项后通过"),
        ("匿名榜名次", f'第{rank["rank"]}/{rank["total"]}名'),
        ("芽芽形态", game.get("companion", {}).get("stage_name", "初来乍到")),
    ]
    st.markdown('<div class="complete-summary">' + "".join(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(str(value))}</div></div>'
        for label, value in items
    ) + "</div>", unsafe_allow_html=True)
    if ending_id == "yaya_partner":
        st.success("隐藏结局解锁：" + ending.get("description", ""))
    else:
        st.success(ending.get("description", ""))
    badges = game.get("progression", {}).get("badges", {})
    if badges:
        st.markdown("#### 已解锁徽章")
        st.markdown("".join(f'<span class="badge-pill">{escape(badge["name"])}</span>' for badge in badges.values()), unsafe_allow_html=True)
    rewards = game.get("progression", {}).get("reward_history", [])
    if rewards:
        st.markdown("#### 本轮获得奖励")
        st.markdown("、".join(escape(reward.get("name", "奖励")) for reward in rewards))
    if result.get("strengths"):
        st.info("优势：" + "、".join(result["strengths"]))
    if result.get("improvements"):
        st.warning("后续提升：" + "、".join(result["improvements"]))
    st.download_button(
        "导出闯关存档JSON",
        data=export_game_save(game),
        file_name="career_start_game_save.json",
        mime="application/json",
        width="stretch",
    )
    if st.button("进入成长基地", type="primary", width="stretch"):
        st.session_state.game = enter_post_game_hub(game)
        _rerun_top()


def _render_post_game_hub(game: dict[str, Any]) -> None:
    post_game = game.get("post_game", {})
    progression = game.get("progression", {})
    endings = post_game.get("endings_unlocked", {})
    st.markdown(
        '<div class="scene-card evidence"><span class="scene-chip">成长基地</span>'
        '<h2>通关后的成长基地</h2><p>这里用于查看结局归档、芽芽状态、徽章和轻量复盘挑战。所有内容仍是模拟游戏数据。</p></div>',
        unsafe_allow_html=True,
    )
    if not post_game.get("unlocked"):
        st.warning("成长基地将在完成第四幕后解锁。")
        return
    st.markdown("#### 结局图鉴")
    cols = st.columns(3)
    for index, ending_id in enumerate(ENDING_DEFINITIONS):
        with cols[index % 3]:
            payload = ending_display_payload(ending_id, bool(endings.get(ending_id)))
            st.markdown(
                f'<div class="summary-card">'
                f'<div class="summary-label">{escape(payload["status"])}</div>'
                f'<div class="summary-value">{escape(payload["title"])}</div>'
                f'<div class="intro-text">{escape(payload["description"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.markdown("#### 芽芽小屋")
    st.info("芽芽状态已固定在右下角宠物坞中，操作页面时也会保持可见。")
    st.markdown("#### 徽章墙")
    badges = progression.get("badges", {})
    if badges:
        st.markdown("".join(f'<span class="badge-pill">{escape(badge["name"])}</span>' for badge in badges.values()), unsafe_allow_html=True)
    else:
        st.info("还没有获得徽章。")
    st.markdown("#### 轻量复盘挑战")
    challenge_cols = st.columns(3)
    challenges = [
        ("evidence_replay", "再看一次证据链", "巩固证据、边界和验证思路。"),
        ("mentor_replay", "复盘导师追问", "整理追问里的薄弱回答。"),
        ("scope_replay", "回看范围取舍", "确认哪些任务真正影响上线。"),
    ]
    for col, (challenge_id, title, desc) in zip(challenge_cols, challenges):
        with col:
            st.markdown(f'<div class="signal-card"><strong>{escape(title)}</strong><br>{escape(desc)}</div>', unsafe_allow_html=True)
            action_key = f"post_challenge:{challenge_id}"
            claimed = game.get("processed_actions", {}).get(action_key)
            if st.button("完成一次复盘", key=f"post_challenge_{challenge_id}_{game.get('reset_version', 0)}", width="stretch", disabled=bool(claimed)):
                updated = deepcopy(game)
                history = updated.setdefault("post_game", {}).setdefault("challenge_history", [])
                history.append({"id": challenge_id, "result": "completed"})
                updated["xp"] = int(updated.get("xp", 0)) + 10
                updated.setdefault("progression", {})["badge_fragments"] = int(updated.setdefault("progression", {}).get("badge_fragments", 0)) + 1
                updated.setdefault("companion", {}).setdefault("food_inventory", {})["review_cookie"] = int(updated["companion"]["food_inventory"].get("review_cookie", 0)) + 1
                updated.setdefault("processed_actions", {})[action_key] = True
                st.session_state.game = updated
                _rerun_top()
            if claimed:
                st.caption("本次会话已领取奖励。")
    st.markdown("#### 匿名成长榜")
    rank = calculate_anonymous_rank(game)
    st.markdown(
        f'<div class="rank-card">模拟匿名榜：当前第{rank["rank"]}/{rank["total"]}名，超过{rank["percentile"]}%的匿名玩家。本榜不代表真实员工排名。</div>',
        unsafe_allow_html=True,
    )
    st.download_button(
        "导出当前成长档案",
        data=export_game_save(game),
        file_name="career_start_post_game_save.json",
        mime="application/json",
        width="stretch",
    )
    uploaded = st.file_uploader("导入闯关存档JSON", type=["json"], key=f"import_game_save_{game.get('reset_version', 0)}")
    if uploaded is not None:
        imported, error = import_game_save(uploaded.getvalue().decode("utf-8"))
        if imported:
            st.session_state.game = imported
            st.success("存档已导入。")
            _rerun_top()
        else:
            st.warning(error or "存档导入失败。")
    if st.button("开启New Game+", type="primary", width="stretch"):
        st.session_state.game = start_new_game_plus(game)
        _rerun_top()


def render_game_page() -> None:
    _inject_game_styles()
    if st.session_state.pop("need_scroll_top", False):
        scroll_to_top()
    game = st.session_state.game
    if not game.get("started"):
        _render_intro_page(game)
        return
    _inject_companion_layout_styles()
    st.markdown(
        '<section class="game-hero"><div class="game-kicker">AI新人90天成长副本</div>'
        '<h1>职场开局·互动闯关</h1><p>在真实业务选择中观察能力、信任与风险变化。当前已开放开局判断、方案救火、协作试炼和成果验收完整闭环。</p></section>',
        unsafe_allow_html=True,
    )
    _render_act_track(game)
    _render_hud(game)
    scene = SCENES.get(game["scene_id"], SCENES["prologue"])
    if game["scene_id"] == "prologue":
        _render_with_companion_rail(game, _render_prologue)
    elif game["scene_id"] == "stage_one_complete":
        _render_with_companion_rail(game, _render_complete)
    elif game["scene_id"] == "stage_two_briefing":
        _second_act_columns(game, _render_stage_two_briefing)
    elif game["scene_id"] == "mini_ai_review":
        _second_act_columns(game, _render_ai_review)
    elif game["scene_id"] == "mini_priority":
        _second_act_columns(game, _render_priority)
    elif game["scene_id"] == "mini_evidence":
        _second_act_columns(game, _render_evidence)
    elif game["scene_id"] == "stage_two_complete":
        _second_act_columns(game, _render_stage_two_complete)
    elif game["scene_id"] == "stage_three_briefing":
        _companion_columns(game, _render_stage_three_briefing)
    elif game["scene_id"] == "stage_three_alignment":
        _companion_columns(game, _render_alignment)
    elif game["scene_id"] == "stage_three_scope":
        _companion_columns(game, _render_scope)
    elif game["scene_id"] == "stage_three_random_event":
        _companion_columns(game, _render_random_event)
    elif game["scene_id"] == "stage_three_complete":
        _companion_columns(game, _render_stage_three_complete)
    elif game["scene_id"] == "stage_four_briefing":
        _companion_columns(game, _render_stage_four_briefing)
    elif game["scene_id"] == "stage_four_loadout":
        _companion_columns(game, _render_stage_four_loadout)
    elif game["scene_id"] == "stage_four_evidence":
        _companion_columns(game, _render_stage_four_evidence)
    elif game["scene_id"] == "stage_four_boss":
        _companion_columns(game, _render_stage_four_boss)
    elif game["scene_id"] == "stage_four_remediation":
        _companion_columns(game, _render_stage_four_remediation)
    elif game["scene_id"] == "stage_four_bonus":
        _companion_columns(game, _render_stage_four_bonus)
    elif game["scene_id"] == "stage_four_complete":
        _companion_columns(game, _render_stage_four_complete)
    elif game["scene_id"] == "post_game_hub":
        _render_post_game_hub(game)
    else:
        _render_scene_with_companion_rail(game, scene)
