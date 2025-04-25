from __future__ import annotations
from flask import Flask, request, jsonify
from typing import Dict, Tuple, Any, Set
from collections import deque
import os
import random
import requests

###############################################################################
# 0. Flask / LINE helpers
###############################################################################
app = Flask(__name__)
CHANNEL_ACCESS_TOKEN: str = os.getenv("CHANNEL_ACCESS_TOKEN", "REPLACE_ME")
HEADERS = {
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


def _line_reply(reply_token: str, messages: list[dict[str, Any]]):
    """Lightweight wrapper for LINE reply API (v2)"""
    payload = {"replyToken": reply_token, "messages": messages}
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=HEADERS,
        json=payload,
        timeout=10,
    )


def reply_text(reply_token: str, text: str):
    _line_reply(reply_token, [{"type": "text", "text": text}])


def reply_audio(reply_token: str, url: str, duration_ms: int):
    _line_reply(
        reply_token,
        [{"type": "audio", "originalContentUrl": url, "duration": duration_ms}],
    )


def reply_text_audio(reply_token: str, text: str, url: str, duration_ms: int):
    _line_reply(
        reply_token,
        [
            {"type": "text", "text": text},
            {"type": "audio", "originalContentUrl": url, "duration": duration_ms},
        ],
    )

###############################################################################
# 1. Core data – kana / audio / word lists
###############################################################################
# 1‑1. kana dict --------------------------------------------------------------
kana_dict: Dict[str, str] = {
    # 清音
    **{
        "あ": "a",
        "い": "i",
        "う": "u",
        "え": "e",
        "お": "o",
        "か": "ka",
        "き": "ki",
        "く": "ku",
        "け": "ke",
        "こ": "ko",
        "さ": "sa",
        "し": "shi",
        "す": "su",
        "せ": "se",
        "そ": "so",
        "た": "ta",
        "ち": "chi",
        "つ": "tsu",
        "て": "te",
        "と": "to",
        "な": "na",
        "に": "ni",
        "ぬ": "nu",
        "ね": "ne",
        "の": "no",
        "は": "ha",
        "ひ": "hi",
        "ふ": "fu",
        "へ": "he",
        "ほ": "ho",
        "ま": "ma",
        "み": "mi",
        "む": "mu",
        "め": "me",
        "も": "mo",
        "や": "ya",
        "ゆ": "yu",
        "よ": "yo",
        "ら": "ra",
        "り": "ri",
        "る": "ru",
        "れ": "re",
        "ろ": "ro",
        "わ": "wa",
        "を": "wo",
        "ん": "n",
    },
    # 濁音
    **{
        "が": "ga",
        "ぎ": "gi",
        "ぐ": "gu",
        "げ": "ge",
        "ご": "go",
        "ざ": "za",
        "じ": "ji",
        "ず": "zu",
        "ぜ": "ze",
        "ぞ": "zo",
        "だ": "da",
        "ぢ": "ji",
        "づ": "zu",
        "で": "de",
        "ど": "do",
        "ば": "ba",
        "び": "bi",
        "ぶ": "bu",
        "べ": "be",
        "ぼ": "bo",
    },
    # 半濁音
    **{"ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po"},
    # 拗音
    **{
        "きゃ": "kya",
        "きゅ": "kyu",
        "きょ": "kyo",
        "しゃ": "sha",
        "しゅ": "shu",
        "しょ": "sho",
        "ちゃ": "cha",
        "ちゅ": "chu",
        "ちょ": "cho",
        "にゃ": "nya",
        "にゅ": "nyu",
        "にょ": "nyo",
        "ひゃ": "hya",
        "ひゅ": "hyu",
        "ひょ": "hyo",
        "みゃ": "mya",
        "みゅ": "myu",
        "みょ": "myo",
        "りゃ": "rya",
        "りゅ": "ryu",
        "りょ": "ryo",
        "ぎゃ": "gya",
        "ぎゅ": "gyu",
        "ぎょ": "gyo",
        "じゃ": "ja",
        "じゅ": "ju",
        "じょ": "jo",
        "びゃ": "bya",
        "びゅ": "byu",
        "びょ": "byo",
        "ぴゃ": "pya",
        "ぴゅ": "pyu",
        "ぴょ": "pyo",
    },
}


# 1‑2. audio ------------------------------------------------------------------
audio_files: list[str] = [
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7).m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)1.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)2.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)3.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)4.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)5.m4a",
]

# (kana, romaji) label for each audio sample
audio_labels: list[Tuple[str, str]] = [
    ("日語：あ", "羅馬拼音：a"),
    ("日語：い", "羅馬拼音：i"),
    ("日語：う", "羅馬拼音：u"),
    ("日語：え", "羅馬拼音：e"),
    ("日語：お", "羅馬拼音：o"),
    ("日語：か", "羅馬拼音：ka"),
]


# 1‑3. dart‑throwing word set --------------------------------------------------
dart_words: Dict[str, Tuple[str, str]] = {
    "みず": ("mizu", "水"),
    "たべる": ("taberu", "吃"),
    "のむ": ("nomu", "喝"),
    "いく": ("iku", "去"),
    "くるま": ("kuruma", "車"),
    "ともだち": ("tomodachi", "朋友"),
    "せんせい": ("sensei", "老師"),
    "ほん": ("hon", "書"),
    "いぬ": ("inu", "狗"),
    "ねこ": ("neko", "貓"),
}

###############################################################################
# 2. Maze game (bug‑fixed)
###############################################################################
Pos = Tuple[int, int]
maze_size: int = 7
# base grid (border walls only)
maze_grid = [["⬜" for _ in range(maze_size)] for _ in range(maze_size)]
for i in range(maze_size):
    maze_grid[0][i] = maze_grid[maze_size - 1][i] = "⬛"
    maze_grid[i][0] = maze_grid[i][maze_size - 1] = "⬛"

start: Pos = (1, 1)
goal: Pos = (maze_size - 2, maze_size - 2)
maze_grid[goal[0]][goal[1]] = "⛩"

# Static decorative walls inside the maze (removable)
_raw_walls: Set[Pos] = {
    (1, 2), (1, 4),
    (2, 2), (2, 5),
    (3, 3),
    (4, 1), (4, 4), (4, 5),
}
INIT_HEARTS: Set[Pos] = {(1, 3), (3, 4)}  # 💎
INIT_PORTALS: Set[Pos] = {(2, 5), (4, 2)}  # 🌀 (must be ≥2 to activate)

quiz_positions: list[Pos] = [
    (random.randint(1, maze_size - 2), random.randint(1, maze_size - 2))
    for _ in range(5)
]

# -----------------------------------------------------------------------------
_players: Dict[str, Dict[str, Any]] = {}
_heart_positions: Set[Pos] = set(INIT_HEARTS)
_portal_positions: Set[Pos] = set(INIT_PORTALS)
_extra_walls: Set[Pos] = set()  # populated by _build_extra_walls()


def _is_reachable(blocks: Set[Pos]) -> bool:
    """Return True if start → goal path exists when treating *blocks* as walls."""
    dq, seen = deque([start]), {start}
    while dq:
        y, x = dq.popleft()
        if (y, x) == goal:
            return True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if (
                0 <= ny < maze_size
                and 0 <= nx < maze_size
                and maze_grid[ny][nx] != "⬛"
                and (ny, nx) not in blocks
                and (ny, nx) not in seen
            ):
                seen.add((ny, nx))
                dq.append((ny, nx))
    return False


def _build_extra_walls() -> Set[Pos]:
    protected = {start, goal}
    extra = {w for w in _raw_walls if w not in protected}
    while extra and not _is_reachable(extra):
        # remove the farthest wall (Manhattan distance) until path opens
        del_wall = max(extra, key=lambda w: abs(w[0] - goal[0]) + abs(w[1] - goal[1]))
        extra.remove(del_wall)
    return extra if _is_reachable(extra) else set()


_extra_walls = _build_extra_walls()


# ---------------- teleport & collect helpers ----------------------------------

def _teleport(pos: Pos) -> Tuple[Pos, bool]:
    if len(_portal_positions) <= 1 or pos not in _portal_positions:
        return pos, False
    dest = random.choice([p for p in _portal_positions if p != pos])
    return dest, True


def _collect_heart(user_state: Dict[str, Any]):
    pos = user_state["pos"]
    if pos in _heart_positions:
        _heart_positions.discard(pos)
        user_state["score"] += 2
        user_state["gems"] += 1
        return True
    return False


# ---------------- main game routine -----------------------------------------

def maze_game(user_id: str, msg: str) -> Dict[str, str]:
    """Process maze input and return {"map": ..., "message": ...}."""
    state = _players.setdefault(
        user_id,
        {"pos": start, "quiz": None, "score": 0, "gems": 0, "game": "maze"},
    )

    # ── 1) answer quiz first ────────────────────────────────────────────────
    if state["quiz"]:
        kana, ans, choice_map = state["quiz"]
        if msg not in {"A", "B", "C"}:
            opts = "\n".join(f"{k}. {v}" for k, v in choice_map.items())
            return {
                "map": render_map(state["pos"]),
                "message": f"❓ 先回答：「{kana}」羅馬拼音？\n{opts}",
            }
        correct = choice_map[msg] == ans
        if correct:
            state["quiz"] = None
            feedback = "✅ 正確，請繼續前進！"
        else:
            feedback = "❌ 錯誤，再試一次！"
        opts = "\n".join(f"{k}. {v}" for k, v in choice_map.items())
        return {
            "map": render_map(state["pos"]),
            "message": feedback if correct else f"{feedback}\n{opts}",
        }

    # ── 2) movement ─────────────────────────────────────────────────────────
    dir_map = {"上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1)}
    if msg not in dir_map:
        return {
            "map": render_map(state["pos"]),
            "message": "請輸入方向（上/下/左/右）或回答題目 A/B/C",
        }

    dy, dx = dir_map[msg]
    ny, nx = state["pos"][0] + dy, state["pos"][1] + dx
    new_pos = (ny, nx)

    if (
        not (0 <= ny < maze_size and 0 <= nx < maze_size)
        or maze_grid[ny][nx] == "⬛"
        or new_pos in _extra_walls
    ):
        return {
            "map": render_map(state["pos"]),
            "message": "🚧 前方是牆，不能走喔！",
        }

    state["pos"] = new_pos
    info_lines: list[str] = []

    # teleport (once)
    state["pos"], did_tp = _teleport(state["pos"])
    if did_tp:
        info_lines.append("🌀 傳送門啟動！")

    # heart collection
    if _collect_heart(state):
        info_lines.append("💎 撿到寶石！（+2 分）")

    # reached goal
    if state["pos"] == goal:
        score, gems = state["score"], state["gems"]
        _players.pop(user_id, None)
        # reset dynamic sets for next run
        _heart_positions.clear(); _heart_positions.update(INIT_HEARTS)
        _portal_positions.clear(); _portal_positions.update(INIT_PORTALS)
        global _extra_walls
        _extra_walls = _build_extra_walls()

        remark = (
            "🌟 迷宮大師！" if score >= 10 else "👍 表現不錯，再接再厲！" if score >= 5 else "💪 加油！多多練習會更好！"
        )
        return {
            "map": render_map(goal) + "\n🏁 YOU WIN!",
            "message": f"🎉 抵達終點！{remark}\n{score} 分／{gems} 顆寶石\n➡️ 輸入『主選單』重新開始",
        }

    # maybe quiz
    if state["pos"] in quiz_positions or random.random() < 0.4:
        kana, ans = random.choice(list(kana_dict.items()))
        options = [ans]
        while len(options) < 3:
            d = random.choice(list(kana_dict.values()))
            if d not in options:
                options.append(d)
        random.shuffle(options)
        choice_map = {"A": options[0], "B": options[1], "C": options[2]}
        state["quiz"] = (kana, ans, choice_map)
        state["score"] += 1
        opts = "\n".join(f"{k}. {v}" for k, v in choice_map.items())
        return {
            "map": render_map(state["pos"]),
            "message": f"❓ 挑戰：「{kana}」羅馬拼音？\n{opts}",
        }

    info_lines.append("你移動了～")
    return {
        "map": render_map(state["pos"]),
        "message": "\n".join(info_lines) + f"\n目前得分：{state['score']} 分",
    }


# ---------------- map rendering ---------------------------------------------

def render_map(player_pos: Pos) -> str:
    rows = []
    for y in range(maze_size):
        row_cells: list[str] = []
        for x in range(maze_size):
            p = (y, x)
            if p == player_pos:
                row_cells.append("😊")
            elif p == goal:
                row_cells.append("⛩")
            elif p in _heart_positions:
                row_cells.append("💎")
            elif p in _portal_positions:
                row_cells.append("🌀")
            elif maze_grid[y][x] == "⬛" or p in _extra_walls:
                row_cells.append("⬛")
            else:
                row_cells.append("⬜")
        rows.append("".join(row_cells))
    return "\n".join(rows)

###############################################################################
# 3. Racing game (unchanged from previous spec)
###############################################################################
_racers: Dict[str, Dict[str, Any]] = {}


def render_race(pos: int, kana: str | None = None, opts: Dict[str, str] | None = None) -> str:
    track = ["⬜" for _ in range(10)]
    if pos >= len(track):
        return "🏁 你贏了！賽車抵達終點！\n輸入 '主選單' 重新開始"
    track[pos] = "🏎"
    race_line = "🚗 賽車進度：\n" + "".join(track)
    if kana and opts:
        opt_text = "\n".join(f"{k}. {v}" for k, v in opts.items())
        return f"{race_line}\n\n❓ 『{kana}』的羅馬拼音是？\n{opt_text}\n請輸入 A/B/C/D。"
    return race_line


def race_game(user_id: str) -> str:
    st = _racers[user_id]
    st["car_pos"] += 1
    if st["car_pos"] >= 10:
        _racers.pop(user_id, None)
        return render_race(10)
    # 40% chance ask quiz
    if random.random() < 0.4:
        kana, ans = random.choice(list(kana_dict.items()))
        options = [ans]
        while len(options) < 4:
            d = random.choice(list(kana_dict.values()))
            if d not in options:
                options.append(d)
        random.shuffle(options)
        st["quiz"] = {k: v for k, v in zip("ABCD", options)}
        st["answer"] = ans
        return render_race(st["car_pos"], kana, st["quiz"])
    return render_race(st["car_pos"])


def race_answer(user_id: str, choice: str) -> str:
    st = _racers.get(user_id)
    if not st or not st.get("quiz"):
        return "❌ 目前沒有題目，請先『前進』。"
    correct = st["quiz"].get(choice) == st["answer"]
    st.pop("quiz", None)
    st.pop("answer", None)
    return ("✅ 正確！繼續『前進』！" if correct else "❌ 錯誤，再試一次！")

###############################################################################
# 4. Dart‑throwing game (word → romaji)
###############################################################################
_dart_sessions: Dict[str, Dict[str, Any]] = {}


def start_dart_game(user_id: str) -> Tuple[str, str]:
    word, (romaji, meaning) = random.choice(list(dart_words.items()))
    options = [romaji]
    while len(options) < 3:
        d = random.choice([v[0] for v in dart_words.values()])
        if d not in options:
            options.append(d)
    random.shuffle(options)
    choice_map = {k: v for k, v in zip("ABC", options)}
    _dart_sessions[user_id] = {
        "word": word,
        "meaning": meaning,
        "answer": romaji,
        "choices": choice_map,
    }
    text = "\n".join(f"{k}. {v}" for k, v in choice_map.items())
    return (
        word,
        f"🎯 射飛鏢結果：你射中了「{word}（{meaning}）」！\n請選出正確的羅馬拼音：\n{text}",
    )


def dart_answer(user_id: str, choice: str) -> str:
    session = _dart_sessions.get(user_id)
    if not session:
        return "❌ 尚未開始射飛鏢，請輸入『我要玩射飛鏢』。"
    if session["choices"].get(choice) == session["answer"]:
        _dart_sessions.pop(user_id, None)
        return "🎯 命中！答對了！"
    else:
        text = "\n".join(f"{k}. {v}" for k, v in session["choices"].items())
        return f"❌ 沒射中，再試一次！\n{text}"

###############################################################################
# 5. Kana table helper (simple, monospaced)
###############################################################################

def get_kana_table() -> str:
    lines = ["五十音對照表 (日語 → Romaji)"]
    for k, r in kana_dict.items():
        lines.append(f"{k:2} : {r}")
    return "\n".join(lines)

###############################################################################
# 6. Webhook callback
###############################################################################
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json(force=True)
    for event in body.get("events", []):
        if event.get("type") != "message":
            continue
        reply_token = event["replyToken"]
        user_id = event["source"]["userId"]
        text = event["message"].get("text", "").strip()

        # ── main menu ───────────────────────────────────────────────────────
        if text == "主選單":
            menu = (
                "請選擇：\n"
                "1. 我要看五十音\n"
                "2. 我要聽音檔\n"
                "3. 我要玩迷宮遊戲\n"
                "4. 我要玩賽車遊戲\n"
                "5. 我要玩射飛鏢\n"
                "6. 我要填問卷～\n\n"
                "【遊戲規則】\n"
                "📘 看五十音：查看假名與羅馬拼音對照。\n"
                "🔊 聽音檔：播放 50 音發音。\n"
                "🧩 迷宮：『上/下/左/右』移動；遇到題目 A/B/C 作答。\n"
                "🏎 賽車：輸入『前進』推進；題目 A/B/C/D。\n"
                "🎯 射飛鏢：A/B/C 選出羅馬拼音！"
            )
            reply_text(reply_token, menu)
            continue

        # ── option 1: kana table ───────────────────────────────────────────
        if text in {"1", "我要看五十音"}:
            reply_text(reply_token, get_kana_table())
            continue

        # ── option 2: audio ────────────────────────────────────────────────
        if text in {"2", "我要聽音檔"}:
            idx = random.randrange(len(audio_files))
            kana, roma = audio_labels[idx]
            reply_text_audio(reply_token, f"{kana} ({roma})", audio_files[idx], 2000)
            continue

        # ── option 3: maze ─────────────────────────────────────────────────
        if text in {"3", "我要玩迷宮遊戲"}:
            _players[user_id] = {"pos": start, "quiz": None, "score": 0, "gems": 0, "game": "maze"}
            reply_text(reply_token, render_map(start) + "\n🌟 迷宮遊戲開始！請輸入『上/下/左/右』。")
            continue

        # ── option 4: race ─────────────────────────────────────────────────
        if text in {"4", "我要玩賽車遊戲"}:
            _racers[user_id] = {"car_pos": 0}
            reply_text(reply_token, render_race(0) + "\n🏁 賽車開始！請輸入『前進』。")
            continue

        # ── option 5: dart ─────────────────────────────────────────────────
        if text in {"5", "我要玩射飛鏢"}:
            word, msg_txt = start_dart_game(user_id)
            _line_reply(
                reply_token,
                [
                    {
                        "type": "image",
                        "originalContentUrl": "https://i.imgur.com/5F3fhhn.png",
                        "previewImageUrl": "https://i.imgur.com/5F3fhhn.png",
                    },
                    {
                        "type": "text",
                        "text": (
                            "🎯 情境題：你來到熱鬧的日式祭典射飛鏢攤位，\n"
                            "請射中靶子並選出正確的羅馬拼音！"
                        ),
                    },
                    {"type": "text", "text": msg_txt},
                ],
            )
            continue

        # ── option 6: questionnaire ───────────────────────────────────────
        if text in {"6", "我要填問卷～"}:
            reply_text(reply_token, "📋 請點選以下連結填寫問卷：\nhttps://forms.gle/w5GNDJ7PY9uWTpsG6")
            continue

        # ── in‑game routing -------------------------------------------------
        if user_id in _players and _players[user_id]["game"] == "maze":
            res = maze_game(user_id, text)
            reply_text(reply_token, res["map"] + "\n💬 " + res["message"])
            continue

        if user_id in _racers and text == "前進":
            reply_text(reply_token, race_game(user_id))
            continue

        if user_id in _racers and text in {"A", "B", "C", "D"}:
            reply_text(reply_token, race_answer(user_id, text))
            continue

        if user_id in _dart_sessions and text in {"A", "B", "C"}:
            reply_text(reply_token, dart_answer(user_id, text))
            continue

        # ── fallback ───────────────────────────────────────────────────────
        reply_text(reply_token, "📢 輸入『主選單』來開始！")

    return jsonify(success=True)

###############################################################################
# 7. Health check
###############################################################################
@app.route("/ping")
def ping():
    return "pong", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
