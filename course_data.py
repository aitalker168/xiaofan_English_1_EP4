# ====== 文件名: course_data.py ======
# 课程数据加载与访问辅助函数
import json
from pathlib import Path

def get_project_dir():
    return Path(__file__).resolve().parent

def load_course_data():
    data_file = get_project_dir() / "course_data.json"
    if not data_file.exists():
        return None
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_sessions(data):
    weeks = data.get("weeks", [])
    sessions = []
    for wk in weeks:
        sessions.extend(wk.get("sessions", []))
    return sessions

def get_session_by_index(data, idx):
    sessions = get_all_sessions(data)
    if 0 <= idx < len(sessions):
        return sessions[idx]
    return None

def get_wrong_words_file():
    return get_project_dir() / "wrong_words.json"

def load_wrong_words():
    f = get_wrong_words_file()
    if f.exists():
        try:
            with open(f, "r") as fp:
                return json.load(fp)
        except:
            return []
    return []

def save_wrong_words(word_list):
    f = get_wrong_words_file()
    with open(f, "w") as fp:
        json.dump(word_list, fp)