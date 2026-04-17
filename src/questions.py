"""
自省问答系统 — 三阶段问题定义（中英双语）

基于 Dan Koe 的 "人生重启协议"，分为：
  - 早晨：心理挖掘 (Psychological Excavation)
  - 全天：打断自动驾驶 (Interrupting Autopilot)
  - 晚间：综合洞察 (Synthesizing Insight)
"""

import random
from datetime import datetime


# ============================================================
# 早晨 — 心理挖掘 (Morning — Psychological Excavation)
# ============================================================

MORNING_QUESTIONS = [
    # --- 觉察痛苦 (Awareness of Pain) ---
    {
        "id": "m1",
        "section": "觉察痛苦",
        "en": "What is the dull and persistent dissatisfaction you've learned to live with? "
              "Not the deep suffering — but what you've learned to tolerate.",
        "zh": "你已经习以为常的、那种钝痛般的持久不满是什么？"
              "不是深层痛苦，而是你学会了忍受的东西。",
    },
    {
        "id": "m2",
        "section": "觉察痛苦",
        "en": "What do you complain about repeatedly but never actually change? "
              "Write down the three complaints you've voiced most often in the past year.",
        "zh": "你反复抱怨却从未真正改变的事情是什么？"
              "写下过去一年你最常发出的三个抱怨。",
    },
    {
        "id": "m3",
        "section": "觉察痛苦",
        "en": "For each complaint: What would someone who watched your behavior "
              "(not your words) conclude that you actually want?",
        "zh": "针对每个抱怨：如果有人只观察你的行为（而非听你的话），"
              "他会得出结论说你实际上想要什么？",
    },
    {
        "id": "m4",
        "section": "觉察痛苦",
        "en": "What truth about your current life would be unbearable to admit "
              "to someone you deeply respect?",
        "zh": "关于你目前生活的哪个真相，如果要向你深深尊敬的人承认，"
              "会令你难以承受？",
    },
    # --- 反愿景 (Anti-Vision) ---
    {
        "id": "m5",
        "section": "反愿景",
        "en": "If absolutely nothing changes for the next five years, describe an average Tuesday. "
              "Where do you wake up? What does your body feel like? What's the first thing you think about? "
              "Who's around you? What do you do between 9am and 6pm? How do you feel at 10pm?",
        "zh": "如果未来五年一切都不改变，描述一个普通的周二。"
              "你在哪醒来？身体感觉如何？脑中浮现的第一个念头是什么？"
              "身边有谁？9 点到 18 点你在做什么？晚上 10 点你的感受是？",
    },
    {
        "id": "m6",
        "section": "反愿景",
        "en": "Now do it but for ten years. What have you missed? What opportunities closed? "
              "Who gave up on you? What do people say about you when you're not in the room?",
        "zh": "现在把时间拉到十年后。你错过了什么？哪些机会已经关闭？"
              "谁放弃了你？当你不在场时，人们怎么评价你？",
    },
    {
        "id": "m7",
        "section": "反愿景",
        "en": "You're at the end of your life. You lived the safe version. You never broke the pattern. "
              "What was the cost? What did you never let yourself feel, try, or become?",
        "zh": "你走到了生命的尽头。你过了安全版本的人生，从未打破固有模式。"
              "代价是什么？你从未允许自己去感受、尝试或成为什么？",
    },
    {
        "id": "m8",
        "section": "反愿景",
        "en": "Who in your life is already living the future you just described? "
              "Someone five, ten, twenty years ahead on the same trajectory? "
              "What do you feel when you think about becoming them?",
        "zh": "你身边有谁已经活在你刚才描述的未来里？"
              "比你早五年、十年、二十年走在同一条轨迹上的人？"
              "当你想到自己可能变成他们时，你有什么感受？",
    },
    {
        "id": "m9",
        "section": "反愿景",
        "en": "What identity would you have to give up to actually change? "
              "('I am the type of person who...') "
              "What would it cost you socially to no longer be that person?",
        "zh": "要真正改变，你必须放弃什么身份认同？"
              "（'我是那种……的人'）"
              "不再做那样的人，在社交上需要付出什么代价？",
    },
    {
        "id": "m10",
        "section": "反愿景",
        "en": "What is the most embarrassing reason you haven't changed? "
              "The one that makes you sound weak, scared, or lazy rather than reasonable.",
        "zh": "你没有改变的最令人难堪的原因是什么？"
              "那个让你听起来软弱、害怕或懒惰（而非'合理'）的理由。",
    },
    {
        "id": "m11",
        "section": "反愿景",
        "en": "If your current behavior is a form of self-protection, "
              "what exactly are you protecting? And what is that protection costing you?",
        "zh": "如果你当前的行为是一种自我保护，"
              "你到底在保护什么？这种保护又让你付出了什么代价？",
    },
    # --- 最小可行愿景 (Vision MVP) ---
    {
        "id": "m12",
        "section": "最小可行愿景",
        "en": "Forget practicality for a minute. If you could snap your fingers and be living "
              "a different life in three years — not what's realistic, what you actually want — "
              "what does an average Tuesday look like?",
        "zh": "暂时忘掉可行性。如果你能打个响指就在三年后过上不同的生活——"
              "不是'现实的'，而是你真正想要的——一个普通的周二是什么样？",
    },
    {
        "id": "m13",
        "section": "最小可行愿景",
        "en": "What would you have to believe about yourself for that life to feel natural "
              "rather than forced? Write the identity statement: 'I am the type of person who...'",
        "zh": "你需要对自己持有什么样的信念，才能让那种生活感觉是自然的而非强撑的？"
              "写下身份宣言：'我是那种……的人'",
    },
    {
        "id": "m14",
        "section": "最小可行愿景",
        "en": "What is one thing you would do this week if you were already that person?",
        "zh": "如果你已经是那个人了，这周你会做的一件事是什么？",
    },
]


# ============================================================
# 全天 — 打断自动驾驶 (Daytime — Interrupting Autopilot)
# ============================================================

DAYTIME_QUESTIONS = [
    # --- 定时中断 (Timed Interrupts) ---
    {
        "id": "d1",
        "time": "11:00",
        "en": "What am I avoiding right now by doing what I'm doing?",
        "zh": "我现在做的事情，是在逃避什么？",
    },
    {
        "id": "d2",
        "time": "13:30",
        "en": "If someone filmed the last two hours, what would they "
              "conclude I want from my life?",
        "zh": "如果有人拍下过去两小时我的行为，他会觉得我想从人生中得到什么？",
    },
    {
        "id": "d3",
        "time": "15:15",
        "en": "Am I moving toward the life I hate or the life I want?",
        "zh": "我正在走向我厌恶的生活，还是我想要的生活？",
    },
    {
        "id": "d4",
        "time": "17:00",
        "en": "What's the most important thing I'm pretending isn't important?",
        "zh": "我在假装什么最重要的事情不重要？",
    },
    {
        "id": "d5",
        "time": "19:30",
        "en": "What did I do today out of identity protection rather than genuine desire?",
        "zh": "今天我做的哪些事是出于身份保护而非真心渴望？",
    },
    {
        "id": "d6",
        "time": "21:00",
        "en": "When did I feel most alive today? When did I feel most dead?",
        "zh": "今天什么时候我感觉最有活力？什么时候最死气沉沉？",
    },
    # --- 补充思考 (Supplementary) ---
    {
        "id": "d7",
        "time": None,
        "en": "What would change if I stopped needing people to see me as "
              "[the identity you protect]?",
        "zh": "如果我不再需要别人把我看作[你保护的那个身份]，会有什么改变？",
    },
    {
        "id": "d8",
        "time": None,
        "en": "Where in my life am I trading aliveness for safety?",
        "zh": "在我的生活中，哪些地方我在用活力换取安全感？",
    },
    {
        "id": "d9",
        "time": None,
        "en": "What's the smallest version of the person I want to become "
              "that I could be tomorrow?",
        "zh": "明天我能成为的、我想要成为的那个人的最小版本是什么？",
    },
]


# ============================================================
# 晚间 — 综合洞察 (Evening — Synthesizing Insight)
# ============================================================

EVENING_QUESTIONS = [
    {
        "id": "e1",
        "section": "洞察",
        "en": "After today, what feels most true about why you've been stuck?",
        "zh": "经过今天，关于你为什么一直停滞不前，什么感觉最真实？",
    },
    {
        "id": "e2",
        "section": "洞察",
        "en": "What is the actual enemy? Name it clearly. Not circumstances. Not other people. "
              "The internal pattern or belief that has been running the show.",
        "zh": "真正的敌人是什么？清晰地命名它。不是环境，不是他人。"
              "是一直在操控全局的那个内在模式或信念。",
    },
    {
        "id": "e3",
        "section": "反愿景压缩",
        "en": "Write a single sentence that captures what you refuse to let your life become. "
              "This is your anti-vision compressed. It should make you feel something when you read it.",
        "zh": "用一句话概括你拒绝让人生变成的样子。"
              "这是你反愿景的压缩版。读到它时，你应该有所触动。",
    },
    {
        "id": "e4",
        "section": "愿景 MVP",
        "en": "Write a single sentence that captures what you're building toward, "
              "knowing it will evolve. This is your vision MVP.",
        "zh": "用一句话概括你正在朝着什么方向努力，同时知道它会不断演变。"
              "这是你的最小可行愿景。",
    },
    {
        "id": "e5",
        "section": "目标透镜",
        "en": "One-year lens: What would have to be true in one year for you to know "
              "you've broken the old pattern? One concrete thing.",
        "zh": "一年透镜：一年后，什么事情必须成为现实，你才能确认自己打破了旧模式？"
              "一件具体的事。",
    },
    {
        "id": "e6",
        "section": "目标透镜",
        "en": "One-month lens: What would have to be true in one month "
              "for the one-year lens to remain possible?",
        "zh": "一月透镜：一个月后，什么事情必须成为现实，"
              "才能让一年目标依然可行？",
    },
    {
        "id": "e7",
        "section": "目标透镜",
        "en": "Daily lens: What are 2-3 actions you can timeblock tomorrow "
              "that the person you're becoming would simply do?",
        "zh": "每日透镜：明天你可以用时间块安排的 2-3 个行动是什么？"
              "那个你正在成为的人会自然而然去做的事。",
    },
]


# ============================================================
# 工具函数
# ============================================================

ALL_QUESTIONS = MORNING_QUESTIONS + DAYTIME_QUESTIONS + EVENING_QUESTIONS


def get_phase_by_time(hour=None):
    """根据当前小时返回阶段名称。"""
    if hour is None:
        hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 20:
        return "daytime"
    else:
        return "evening"


def get_questions_for_phase(phase):
    """根据阶段获取对应的问题列表。"""
    phase_map = {
        "morning": MORNING_QUESTIONS,
        "daytime": DAYTIME_QUESTIONS,
        "evening": EVENING_QUESTIONS,
    }
    return phase_map.get(phase, DAYTIME_QUESTIONS)


def pick_random_question(phase=None, exclude_ids=None):
    """
    随机挑选一个问题。
    - phase: 指定阶段，None 则根据当前时间自动判断
    - exclude_ids: 排除已展示过的问题 ID
    """
    if phase is None:
        phase = get_phase_by_time()

    questions = get_questions_for_phase(phase)
    if exclude_ids:
        questions = [q for q in questions if q["id"] not in exclude_ids]

    if not questions:
        # 所有问题都展示过了，重置
        questions = get_questions_for_phase(phase)

    return random.choice(questions)


def get_question_by_id(question_id):
    """根据 ID 查找问题。"""
    for q in ALL_QUESTIONS:
        if q["id"] == question_id:
            return q
    return None


if __name__ == "__main__":
    # 快速测试
    print(f"当前阶段: {get_phase_by_time()}")
    q = pick_random_question()
    print(f"\n随机问题 [{q['id']}]:")
    print(f"  EN: {q['en']}")
    print(f"  ZH: {q['zh']}")
    print(f"\n总计问题数: {len(ALL_QUESTIONS)}")
    print(f"  早晨: {len(MORNING_QUESTIONS)}")
    print(f"  全天: {len(DAYTIME_QUESTIONS)}")
    print(f"  晚间: {len(EVENING_QUESTIONS)}")
