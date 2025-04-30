from flask import Flask, request, jsonify
from collections import deque   # 佇列（給 BFS 用）
import random                   # 隨機數/抽題都會用到
import requests                 # 如果之後要打外部 API

app = Flask(__name__)
# ========== LINE Token ==========
CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="

# ========== 📘 日語五十音資料區（kana_dict） ==========
kana_dict = {}

# 清音（基本音）
kana_dict.update({
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n"
})

# 濁音（有濁點）
kana_dict.update({
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo"
})

# 半濁音（有半濁點）
kana_dict.update({
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po"
})

# 拗音（拗合音，平假名 + 小字）
kana_dict.update({
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo"
})

# ========== 回傳純文字訊息 ==========

def reply_text(reply_token, text):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

# ========== 回傳音檔 ==========

def reply_audio(reply_token, original_content_url, duration):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{
            "type": "audio",
            "originalContentUrl": original_content_url,
            "duration": duration
        }]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

# ========== 同時回傳文字 + 音檔 ==========

def reply_text_audio(reply_token, text_msg, audio_url, duration):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": text_msg},
            {"type": "audio", "originalContentUrl": audio_url, "duration": duration}
        ]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

# ========== 音檔清單 ==========
audio_files = [
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7).m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)1.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)2.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)3.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)4.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)5.m4a"
]

# 與音檔對應的假名與羅馬拼音
audio_labels = [
    ("日語：あ", "羅馬拼音：a"),
    ("日語：い", "羅馬拼音：i"),
    ("日語：う", "羅馬拼音：u"),
    ("日語：え", "羅馬拼音：e"),
    ("日語：お", "羅馬拼音：o"),
    ("日語：か", "羅馬拼音：ka")
]

# 🏹 射飛鏢遊戲資料 (含繁體中文意義)
dart_words = {
    "みず": ("mizu", "水"),
    "たべる": ("taberu", "吃"),
    "のむ": ("nomu", "喝"),
    "いく": ("iku", "去"),
    "くるま": ("kuruma", "車"),
    "ともだち": ("tomodachi", "朋友"),
    "せんせい": ("sensei", "老師"),
    "ほん": ("hon", "書"),
    "いぬ": ("inu", "狗"),
    "ねこ": ("neko", "貓")
}

dart_sessions = {}

@app.route("/callback", methods=["POST"])
def callback():
body = request.get_json()
events = body.get("events", [])

for event in events:
    if event["type"] == "message":
        reply_token = event["replyToken"]
        user_id = event["source"]["userId"]
        text = event["message"]["text"].strip()

        if text == "主選單":
            menu = (
                "請選擇：\n"
                "1. 我要看五十音\n"
                "2. 我要聽音檔\n"
                "3. 我要玩迷宮遊戲\n"
                "4. 我要玩賽車遊戲\n"
                "5. 我要玩射飛鏢 進階篇\n"
                "6. 我要填問卷～\n\n"
                "【遊戲規則】\n"
                "📘 看五十音：查看所有平假名、片假名與羅馬拼音對照。\n"
                "🔊 聽音檔：播放50音發音音檔。\n"
                "🧩 迷宮遊戲：使用『上/下/左/右』移動角色，遇到假名選擇題時答對才能繼續。\n"
                "🏎 賽車遊戲：每次輸入『前進』會推進一格，抵達終點即勝利！\n"
                "🎯 射飛鏢：隨機射中一個日文單字，選出正確的羅馬拼音！"
            )
            reply_text(reply_token, menu)

        elif text == "1" or text == "我要看五十音":
            reply_text(reply_token, get_kana_table())
            
        elif text == "2" or text == "我要聽音檔":
            # 隨機選擇一個音檔並回覆假名 + 音檔（一次回覆）
            idx = random.randrange(len(audio_files))
            kana, roma = audio_labels[idx]
            reply_text_audio(
                reply_token,
                f"{kana} ({roma})",          # 文字訊息
                audio_files[idx],            # 音檔 URL
                2000                         # 長度 (毫秒)；請依實際音檔長度調整
        )

        elif text == "3" or text == "我要玩迷宮遊戲":
            players[user_id] = {"pos": (1, 1), "quiz": None, "game": "maze", "score": 0}
            reply_text(reply_token, render_map((1, 1)) + "\n🌟 迷宮遊戲開始！請輸入「上」「下」「左」「右」移動。")

        elif text == "4" or text == "我要玩賽車遊戲":
            players[user_id] = {"car_pos": 0, "game": "race", "quiz": None, "last_quiz": None, "last_msg": None}
            reply_text(reply_token, render_race(0) + "\n🏁 賽車遊戲開始！請輸入「前進」來推進你的車子。")

        elif text == "5" or text == "我要玩射飛鏢":
            # --- 先隨機選單字並產生選項、記錄 session ---
            word, (romaji, meaning) = random.choice(list(dart_words.items()))
            options = [romaji]
            while len(options) < 3:
                distractor = random.choice([v[0] for v in dart_words.values()])
                if distractor not in options:
                    options.append(distractor)
            random.shuffle(options)
            choice_map = {"A": options[0], "B": options[1], "C": options[2]}
            dart_sessions[user_id] = {
                "word": word,
                "meaning": meaning,
                "answer": romaji,
                "choice_map": choice_map
            }
            choices_text = "\n".join([f"{k}. {v}" for k, v in choice_map.items()])

            # --- 一次回覆三則訊息：圖片、情境、遊戲題目 ---
            headers = {
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            body = {
                "replyToken": reply_token,
                "messages": [
                    {
                        "type": "image",
                        "originalContentUrl": "https://i.imgur.com/5F3fhhn.png",
                        "previewImageUrl":  "https://i.imgur.com/5F3fhhn.png"
                    },
                    {
                        "type": "text",
                        "text": (
                            "🎯 情境題：你來到熱鬧的日式祭典射飛鏢攤位，"
                            "眼前的靶子上印有日語單字與其中文意義，"
                            "請射中一個單字後，選出其正確的羅馬拼音！"
                        )
                    },
                    {
                        "type": "text",
                        "text": (
                            f"🎯 射飛鏢結果：你射中了「{word}（{meaning}）」！\n"
                            f"請選出正確的羅馬拼音：\n{choices_text}"
                        )
                    }
                ]
            }
            requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)
            # 射飛鏢遊戲開始
            word, (romaji, meaning) = random.choice(list(dart_words.items()))
            options = [romaji]
            while len(options) < 3:
                distractor = random.choice([v[0] for v in dart_words.values()])
                if distractor not in options:
                    options.append(distractor)
            random.shuffle(options)
            dart_sessions[user_id] = {"word": word, "meaning": meaning, "answer": romaji, "options": options}
            choice_map = {"A": options[0], "B": options[1], "C": options[2]}
            dart_sessions[user_id]["choice_map"] = choice_map
            choices_text = "\n".join([f"{k}. {v}" for k, v in choice_map.items()])
            reply_text(
                reply_token,
                f"🎯 射飛鏢結果：你射中了「{word}（{meaning}）」！\n"
                f"請選出正確的羅馬拼音：\n{choices_text}"
            )

        elif user_id in dart_sessions and text in ["A", "B", "C"]:
            # 處理射飛鏢答案
            session = dart_sessions[user_id]
            if session["choice_map"][text] == session["answer"]:
                del dart_sessions[user_id]
                reply_text(reply_token, "🎯 命中！答對了！")
            else:
                choices_text = "\n".join([f"{k}. {v}" for k, v in session["choice_map"].items()])
                reply_text(
                    reply_token,
                    f"❌ 沒射中，再試一次！請選出「{session['word']}（{session['meaning']}）」的正確羅馬拼音：\n{choices_text}"
                )

        elif text == "6" or text == "我要填問卷～":
            reply_text(reply_token, "📋 請點選以下連結填寫問卷：\nhttps://forms.gle/w5GNDJ7PY9uWTpsG6")

        elif user_id in players and players[user_id].get("game") == "maze" and text in ["上", "下", "左", "右"]:
            result = maze_game(user_id, text)
            reply_text(reply_token, result["map"] + "\n💬 " + result["message"])

        elif user_id in players and players[user_id].get("game") == "maze" and players[user_id].get("quiz"):
            result = maze_game(user_id, text)
            reply_text(reply_token, result["map"] + "\n💬 " + result["message"])

        elif user_id in players and players[user_id].get("game") == "race" and text in ["A", "B", "C", "D"]:
            result = race_answer(user_id, text)
            reply_text(reply_token, result)

        elif user_id in players and players[user_id].get("game") == "race" and text == "前進":
            result = race_game(user_id)
            reply_text(reply_token, result)

        else:
            reply_text(reply_token,
                "📢 請輸入『主選單』")

def reply_text(reply_token, text):
headers = {
"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
"Content-Type": "application/json"
}
body = {
"replyToken": reply_token,
"messages": [{"type": "text", "text": text}]
}
requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)
"""
🏯 迷宮小遊戲（優化版 2025-05-01）
------------------------------------------------------
✅ 改進內容：
1. 代碼結構重組：使用類別結構整理迷宮遊戲邏輯，提高可維護性
2. 效能優化：減少不必要的全局變量訪問，優化地圖渲染
3. 錯誤處理：增強錯誤處理能力，防止各種邊緣情況引起的崩潰
4. 玩家體驗：改進消息提示，增加遊戲難度的漸進式調整
5. 代碼可讀性：添加詳細註釋，優化命名約定，遵循PEP 8規範
"""
import random
from collections import deque
from typing import Dict, List, Set, Tuple, Any, Optional

# ===== 1. MazeGame 類：封裝迷宮遊戲邏輯 =========================
class MazeGame:
    """迷宮遊戲核心類，管理地圖、玩家狀態和遊戲邏輯"""
    
    # 座標類型別名
    Pos = Tuple[int, int]
    
    # 方向映射
    DIRECTIONS = {
        "上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1),
        "UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)
    }
    
    # 單例模式：保存全局遊戲狀態
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MazeGame, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, maze_size: int = 7):
        """初始化迷宮遊戲"""
        if self._initialized:
            return
            
        self.maze_size = maze_size
        
        # 遊戲地圖與基本設置
        self.maze = [["⬜" for _ in range(maze_size)] for _ in range(maze_size)]
        self._create_boundary_walls()
        
        # 重要位置
        self.start: MazeGame.Pos = (1, 1)
        self.goal: MazeGame.Pos = (maze_size - 2, maze_size - 2)
        self.maze[self.goal[0]][self.goal[1]] = "⛩"
        
        # 特殊元素
        self.raw_walls: Set[MazeGame.Pos] = {
            (1, 1), (1, 2), (1, 4),
            (2, 2), (2, 6),
            (3, 1), (3, 3), (3, 5),
            (4, 4), (4, 5), (4, 6),
        }
        self.heart_positions: Set[MazeGame.Pos] = {(1, 3), (3, 4)}  # 💎
        self.portal_positions: Set[MazeGame.Pos] = {(2, 5), (4, 1)}  # 🌀
        
        # 玩家狀態
        self.players: Dict[str, Dict[str, Any]] = {}
        
        # 隨機題目位置
        self.quiz_positions: List[MazeGame.Pos] = []
        self._generate_quiz_positions()
        
        # 構建動態牆壁
        self.extra_walls: Set[MazeGame.Pos] = self._build_extra_walls()
        
        self._initialized = True
    
    def _create_boundary_walls(self) -> None:
        """建立邊界牆壁"""
        for i in range(self.maze_size):
            self.maze[0][i] = self.maze[self.maze_size-1][i] = "⬛"
            self.maze[i][0] = self.maze[i][self.maze_size-1] = "⬛"
    
    def _generate_quiz_positions(self, count: int = 5) -> None:
        """生成隨機題目位置"""
        self.quiz_positions = []
        while len(self.quiz_positions) < count:
            pos = (random.randint(1, self.maze_size-2), random.randint(1, self.maze_size-2))
            # 避免起點和終點
            if pos != self.start and pos != self.goal and pos not in self.quiz_positions:
                self.quiz_positions.append(pos)
    
    def _is_reachable(self, blocks: Set[Pos]) -> bool:
        """檢查在指定障礙物下，起點是否可達終點（BFS算法）"""
        q, seen = deque([self.start]), {self.start}
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        while q:
            y, x = q.popleft()
            if (y, x) == self.goal:
                return True
                
            for dy, dx in dirs:
                ny, nx = y + dy, x + dx
                new_pos = (ny, nx)
                
                # 檢查是否在範圍內、是否是障礙物、是否已訪問
                if (0 <= ny < self.maze_size and 0 <= nx < self.maze_size and 
                    new_pos not in blocks and
                    self.maze[ny][nx] != "⬛" and
                    new_pos not in seen):
                    seen.add(new_pos)
                    q.append(new_pos)
        
        return False
    
    def _build_extra_walls(self) -> Set[Pos]:
        """構建動態牆壁，確保迷宮仍有解"""
        # 保護起點、終點及其周圍的格子
        protected = {
            self.start, self.goal,
            (self.start[0] + 1, self.start[1]), (self.start[0], self.start[1] + 1),
            (self.goal[0] - 1, self.goal[1]), (self.goal[0], self.goal[1] - 1),
        }
        
        # 排除受保護位置、寶石和傳送門
        extra = {
            c for c in self.raw_walls
            if c not in protected and 
               c not in self.heart_positions and 
               c not in self.portal_positions
        }
        
        # 逐步移除導致無解的牆壁
        while extra and not self._is_reachable(extra):
            # 移除最遠的牆壁
            far_wall = max(extra, key=lambda w: 
                abs(w[0] - self.goal[0]) + abs(w[1] - self.goal[1]))
            extra.remove(far_wall)
        
        return extra if self._is_reachable(extra) else set()
    
    def _teleport(self, pos: Pos) -> Tuple[Pos, bool]:
        """若在傳送門上，傳送到隨機其它傳送門
        
        返回:
            (新位置, 是否傳送)
        """
        # 檢查是否可傳送
        if (len(self.portal_positions) <= 1 or 
            pos not in self.portal_positions or 
            pos == self.goal):
            return pos, False
        
        # 傳送到隨機其它傳送門
        dest = random.choice([p for p in self.portal_positions if p != pos])
        return dest, True
    
    def _collect_heart(self, pos: Pos, player: Dict[str, Any]) -> bool:
        """收集寶石並更新分數
        
        返回:
            是否收集到寶石
        """
        if pos in self.heart_positions:
            self.heart_positions.discard(pos)  # 安全移除
            player["score"] = player.get("score", 0) + 2
            player["items"] = player.get("items", 0) + 1
            return True
        return False
    
    def _generate_quiz(self, player: Dict[str, Any]) -> Dict[str, str]:
        """生成五十音測驗題
        
        返回:
            含有測驗題、選項和地圖的字典
        """
        # 取全局假名字典
        from __main__ import kana_dict
        
        # 隨機選擇一個假名及其羅馬拼音
        kana, ans = random.choice(list(kana_dict.items()))
        
        # 生成選項（正確答案+干擾項）
        opts = [ans]
        while len(opts) < 3:
            distractor = random.choice(list(kana_dict.values()))
            if distractor not in opts:
                opts.append(distractor)
        
        # 打亂選項順序
        random.shuffle(opts)
        choice_map = {"A": opts[0], "B": opts[1], "C": opts[2]}
        
        # 保存到玩家狀態
        player["quiz"] = (kana, ans, choice_map)
        player["score"] = player.get("score", 0) + 1  # 出題加1分
        
        # 格式化選項文本
        opt_txt = "\n".join(f"{k}. {v}" for k, v in choice_map.items())
        
        return {
            "map": self.render_map(player["pos"]),
            "message": f"❓ 挑戰：「{kana}」羅馬拼音？\n{opt_txt}"
        }
    
    def handle_move(self, user_id: str, direction: str) -> Dict[str, str]:
        """處理玩家移動
        
        參數:
            user_id: 玩家ID
            direction: 移動方向
            
        返回:
            包含渲染地圖和消息的字典
        """
        # 獲取或初始化玩家數據
        player = self.players.setdefault(
            user_id,
            {
                "pos": self.start, 
                "quiz": None, 
                "game": "maze", 
                "score": 0, 
                "items": 0
            }
        )
        
        # 標準化方向輸入
        direction = direction.strip().upper()
        
        # 處理答題優先
        if player.get("quiz"):
            return self._handle_quiz_answer(player, direction)
        
        # 處理移動
        if direction not in self.DIRECTIONS:
            return {
                "map": self.render_map(player["pos"]),
                "message": "請輸入方向（上/下/左/右）或回答題目（A/B/C）"
            }
        
        # 計算新位置
        dy, dx = self.DIRECTIONS[direction]
        ny, nx = player["pos"][0] + dy, player["pos"][1] + dx
        new_pos = (ny, nx)
        
        # 檢查是否撞牆
        if (not (0 <= ny < self.maze_size and 0 <= nx < self.maze_size) or
            self.maze[ny][nx] == "⬛" or
            new_pos in self.extra_walls):
            return {
                "map": self.render_map(player["pos"]),
                "message": "🚧 前方是牆，不能走喔！"
            }
        
        # 更新位置
        player["pos"] = new_pos
        info_messages = []  # 收集發生事件的消息
        
        # 處理傳送門
        player["pos"], did_teleport = self._teleport(player["pos"])
        if did_teleport:
            info_messages.append("🌀 傳送門啟動！")
        
        # 處理寶石收集
        if self._collect_heart(player["pos"], player):
            info_messages.append("💎 撿到寶石！（+2 分）")
        
        # 檢查是否抵達終點
        if player["pos"] == self.goal:
            return self._handle_goal_reached(user_id, player)
        
        # 隨機或指定位置出題
        if (player["pos"] in self.quiz_positions or 
            # 根據已收集寶石調整隨機題目出現機率
            random.random() < (0.3 + min(0.3, player.get("items", 0) * 0.1))):
            return self._generate_quiz(player)
        
        # 一般移動回覆
        info_line = "\n".join(info_messages) if info_messages else "你移動了～"
        return {
            "map": self.render_map(player["pos"]),
            "message": f"{info_line}\n目前得分：{player.get('score', 0)} 分"
        }
    
    def _handle_quiz_answer(self, player: Dict[str, Any], answer: str) -> Dict[str, str]:
        """處理玩家對測驗題的回答
        
        參數:
            player: 玩家數據
            answer: 玩家回答
            
        返回:
            包含結果的字典
        """
        kana, ans, choice_map = player["quiz"]
        
        # 檢查答案格式
        if answer not in {"A", "B", "C"}:
            opts = "\n".join(f"{k}. {v}" for k, v in choice_map.items())
            return {
                "map": self.render_map(player["pos"]),
                "message": f"❓ 先回答題目：「{kana}」羅馬拼音？\n{opts}"
            }
        
        # 檢查答案正確性
        correct = (choice_map[answer] == ans)
        feedback = "✅ 正確，請繼續前進！" if correct else "❌ 錯誤，再試一次！"
        
        # 答對則清除題目狀態
        if correct:
            player["quiz"] = None
        
        # 返回結果
        opts = "\n".join(f"{k}. {v}" for k, v in choice_map.items())
        return {
            "map": self.render_map(player["pos"]),
            "message": feedback if correct else f"{feedback}\n{opts}"
        }
    
    def _handle_goal_reached(self, user_id: str, player: Dict[str, Any]) -> Dict[str, str]:
        """處理玩家抵達終點
        
        參數:
            user_id: 玩家ID
            player: 玩家數據
            
        返回:
            包含結果的字典
        """
        # 獲取玩家成績
        score = player.get("score", 0)
        gems = player.get("items", 0)
        
        # 清理遊戲狀態
        self.players.pop(user_id, None)
        self.heart_positions = {(1, 3), (3, 4)}  # 重置寶石
        self.portal_positions = {(2, 5), (4, 1)}  # 重置傳送門
        self.extra_walls = self._build_extra_walls()  # 重建牆壁
        
        # 根據分數給出鼓勵
        encour = (
            "🌟 迷宮大師！" if score >= 12 else
            "🏆 精通迷宮！" if score >= 8 else
            "👍 表現不錯，再接再厲！" if score >= 5 else
            "💪 加油！多多練習會更好！"
        )
        
        return {
            "map": self.render_map(self.goal) + "\n🏁 YOU WIN!",
            "message": (
                f"🎉 抵達終點！{encour}\n"
                f"共 {score} 分、{gems} 顆寶石！\n"
                f"➡️ 輸入『主選單』重新開始"
            )
        }
    
    def render_map(self, player_pos: Pos) -> str:
        """渲染地圖為字串
        
        參數:
            player_pos: 玩家位置
            
        返回:
            地圖字串
        """
        rows = []
        for y in range(self.maze_size):
            row = []
            for x in range(self.maze_size):
                cell = (y, x)
                # 按優先順序決定顯示內容
                if cell == player_pos:
                    row.append("😊")
                elif cell == self.goal:
                    row.append("⛩")
                elif cell in self.heart_positions:
                    row.append("💎")
                elif cell in self.portal_positions:
                    row.append("🌀")
                elif self.maze[y][x] == "⬛" or cell in self.extra_walls:
                    row.append("⬛")
                else:
                    row.append(self.maze[y][x])
            rows.append("".join(row))
        return "\n".join(rows)
    
    def reset_game(self, user_id: str = None) -> None:
        """重置遊戲狀態
        
        參數:
            user_id: 指定玩家ID，為None則重置所有玩家
        """
        if user_id is not None:
            # 重置單個玩家
            self.players.pop(user_id, None)
        else:
            # 重置所有遊戲狀態
            self.players.clear()
            self.heart_positions = {(1, 3), (3, 4)}
            self.portal_positions = {(2, 5), (4, 1)}
            self.extra_walls = self._build_extra_walls()
            self._generate_quiz_positions()


# ===== 2. 向外部程式提供相容的接口函數 ================================

def maze_game(user_id: str, message: str) -> Dict[str, str]:
    """迷宮遊戲入口函數，保持與原程式相容的接口
    
    參數:
        user_id: 玩家ID
        message: 玩家輸入的訊息
        
    返回:
        包含地圖和回應訊息的字典
    """
    # 創建或獲取遊戲實例
    game = MazeGame()
    
    # 處理玩家輸入
    return game.handle_move(user_id, message)


def render_map(player_pos: Tuple[int, int]) -> str:
    """渲染地圖函數，保持與原程式相容的接口
    
    參數:
        player_pos: 玩家位置
        
    返回:
        渲染後的地圖字串
    """
    # 創建或獲取遊戲實例
    game = MazeGame()
    
    # 渲染並返回地圖
    return game.render_map(player_pos)


# 如果單獨運行這個文件進行測試
if __name__ == "__main__":
    # 測試代碼可在這裡執行
    game = MazeGame()
    print("地圖初始化成功:")
    print(game.render_map((1, 1)))
    print("\n可以使用maze_game()函數進行遊戲")

# 🏎 強化版賽車遊戲（修正版）
# ------------------------------------------------------------
# 特色（維持不變）：
# ⛽ Fuel、💰 Gold Coins、🚀 Nitro、⭐ Score
# 本次修正：
# 1. 避免 KeyError／NameError：coins 與 nitro 預設值、防止 current_user 未先定義
# 2. player.setdefault 用於兼容舊玩家資料
# 3. coins／nitro 讀取改成 get()，確保安全
# ------------------------------------------------------------

import random

TRACK_LEN = 10        # 賽道長度
COIN_COUNT = 3        # 金幣數量
FUEL_MAX = 3          # 初始油料
NITRO_CHANCE = 0.25   # Nitro 機率

# ⭐ 若主程式尚未宣告，先給預設
try:
    players
except NameError:
    players = {}
try:
    kana_dict
except NameError:
    kana_dict = {}
# 避免 current_user 未定義
current_user = None

# ------------------------------------------------------------

def render_race(pos, kana=None, options=None):
    """賽道與題目畫面 (保持原接口)"""
    track = ["⬜" for _ in range(TRACK_LEN)]
    player = players.get(current_user, {}) if current_user else {}

    # 繪製金幣
    for coin in player.get("coins", set()):
        if 0 <= coin < TRACK_LEN:
            track[coin] = "💰"
    if pos < TRACK_LEN:
        track[pos] = "🏎"

    race_line = "🚗 賽車進度：\n" + "".join(track)
    status = (
        f"\n⛽ Fuel: {player.get('fuel', 0)}  "
        f"⭐ Score: {player.get('score', 0)}  "
        f"🚀 Nitro: {player.get('nitro', 0)}"
    )

    # 終點
    if pos >= TRACK_LEN:
        return (
            "🏁 你贏了！賽車抵達終點！\n"
            f"⭐ 最終得分：{player.get('score', 0)}\n"
            "輸入 '主選單' 重新開始"
        )

    if kana and options:
        options_text = "\n".join([f"{k}. {v}" for k, v in options.items()])
        return (
            f"{race_line}{status}\n\n❓ 請問「{kana}」的羅馬拼音是？\n"
            f"{options_text}\n請按按鈕作答（A/B/C）。"
        )

    return race_line + status


# ------------------------------------------------------------
# 🏎 賽車遊戲回答處理


def race_answer(user, answer):
    player = players.get(user)
    if not player or not player.get("last_quiz"):
        return "沒有待回答的題目，請輸入『前進』以獲得新題目。"

    global current_user
    current_user = user  # 供 render_race 取得玩家資料

    kana, correct, choice_map = player["last_quiz"]

    # ===== 正確答案 =====
    if answer in choice_map and choice_map[answer] == correct:
        step = 1
        nitro_msg = ""
        if random.random() < NITRO_CHANCE:
            extra = random.randint(1, 2)
            step += extra
            player["nitro"] = player.get("nitro", 0) + 1
            nitro_msg = f"🚀 Nitro！額外前進 {extra} 格！"

        player["car_pos"] += step

        # 撿金幣
        if player["car_pos"] in player.get("coins", set()):
            player.setdefault("coins", set()).discard(player["car_pos"])
            player["score"] = player.get("score", 0) + 2
            coin_msg = "💰 撿到金幣 +2 分！"
        else:
            coin_msg = ""

        # 清除題目
        player["quiz"] = None
        player["last_quiz"] = None

        return (
            render_race(player["car_pos"]) +
            f"\n✅ 回答正確！{nitro_msg} {coin_msg}\n請輸入『前進』以獲得新題目！"
        )

    # ===== 錯誤答案 =====
    player["fuel"] = player.get("fuel", FUEL_MAX) - 1
    if player["fuel"] <= 0:
        players.pop(user, None)
        return (
            render_race(player["car_pos"]) +
            "\n🛑 油料耗盡，遊戲結束！輸入 '主選單' 重新開始"
        )

    return (
        render_race(player["car_pos"], kana, choice_map) +
        f"\n❌ 回答錯誤，燃料 -1！剩餘 {player['fuel']} 格，再試一次！"
    )


# ------------------------------------------------------------
# 🏎 賽車遊戲主流程


def race_game(user):
    # 若舊資料缺少新欄位，setdefault 補齊
    player = players.setdefault(user, {})
    player.setdefault("game", "race")
    player.setdefault("car_pos", 0)
    player.setdefault("fuel", FUEL_MAX)
    player.setdefault("score", 0)
    player.setdefault("coins", set(random.sample(range(1, TRACK_LEN - 1), COIN_COUNT)))
    player.setdefault("nitro", 0)

    global current_user
    current_user = user

    # 若已有題目
    if player.get("quiz"):
        kana, correct, choice_map = player["quiz"]
        player["last_quiz"] = (kana, correct, choice_map)
        return render_race(player["car_pos"], kana, choice_map)

    # 產生新題目
    if not kana_dict:
        return "⚠️ kana_dict 尚未初始化，無法出題！"
    kana, correct = random.choice(list(kana_dict.items()))
    options = [correct]
    while len(options) < 3 and len(kana_dict) >= 3:
        distractor = random.choice(list(kana_dict.values()))
        if distractor not in options:
            options.append(distractor)
    # 若題庫不足 3 個選項，填入重複值避免無限迴圈
    while len(options) < 3:
        options.append(correct)
    random.shuffle(options)
    choice_map = {"A": options[0], "B": options[1], "C": options[2]}

    player["quiz"] = (kana, correct, choice_map)
    player["last_quiz"] = (kana, correct, choice_map)

    return render_race(player["car_pos"], kana, choice_map)

# 📘 回傳日語五十音表格式文字
def get_kana_table():
    table = "📘【日語五十音對照表】"
    groups = [
        ("清音 (基本音)", [
            ("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o"),
            ("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko"),
            ("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so"),
            ("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to"),
            ("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no"),
            ("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho"),
            ("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo"),
            ("や", "ya"), ("ゆ", "yu"), ("よ", "yo"),
            ("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro"),
            ("わ", "wa"), ("を", "wo"), ("ん", "n")
        ]),
        ("濁音 (加上濁點)", [
            ("が", "ga"), ("ぎ", "gi"), ("ぐ", "gu"), ("げ", "ge"), ("ご", "go"),
            ("ざ", "za"), ("じ", "ji"), ("ず", "zu"), ("ぜ", "ze"), ("ぞ", "zo"),
            ("だ", "da"), ("ぢ", "ji"), ("づ", "zu"), ("で", "de"), ("ど", "do"),
            ("ば", "ba"), ("び", "bi"), ("ぶ", "bu"), ("べ", "be"), ("ぼ", "bo")
        ]),
        ("半濁音 (加上半濁點)", [
            ("ぱ", "pa"), ("ぴ", "pi"), ("ぷ", "pu"), ("ぺ", "pe"), ("ぽ", "po")
        ]),
        ("拗音 (小字組合音)", [
            ("きゃ", "kya"), ("きゅ", "kyu"), ("きょ", "kyo"),
            ("しゃ", "sha"), ("しゅ", "shu"), ("しょ", "sho"),
            ("ちゃ", "cha"), ("ちゅ", "chu"), ("ちょ", "cho"),
            ("にゃ", "nya"), ("にゅ", "nyu"), ("にょ", "nyo"),
            ("ひゃ", "hya"), ("ひゅ", "hyu"), ("ひょ", "hyo"),
            ("みゃ", "mya"), ("みゅ", "myu"), ("みょ", "myo"),
            ("りゃ", "rya"), ("りゅ", "ryu"), ("りょ", "ryo"),
            ("ぎゃ", "gya"), ("ぎゅ", "gyu"), ("ぎょ", "gyo"),
            ("じゃ", "ja"), ("じゅ", "ju"), ("じょ", "jo"),
            ("びゃ", "bya"), ("びゅ", "byu"), ("びょ", "byo"),
            ("ぴゃ", "pya"), ("ぴゅ", "pyu"), ("ぴょ", "pyo")
        ])
    ]
    for title, kana_group in groups:
        table += f"\n\n🔹 {title}\n"
        for i in range(0, len(kana_group), 5):
            row = kana_group[i:i+5]
            line = "  ".join([f"{kana} → {roma}" for kana, roma in row])
            table += line + "\n"
    return table.strip()
