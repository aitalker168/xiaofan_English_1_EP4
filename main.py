import os, sys, json
from pathlib import Path
project_dir = Path(__file__).resolve().parent

import streamlit as st
st.set_page_config(page_title="⭐ English Learner", layout="centered", initial_sidebar_state="collapsed")
from utils import (
    load_course_data, load_video_config, save_video_config,
    parse_youtube_url, audio_button, recorder_widget,
    resolve_image_path, rotate_image, IMAGE_DIR
)

def init_state():
    defaults = {
        "current_session": 0,
        "current_exercise": 0,
        "score": 0,
        "stars": 0,
        "wrong_words": set(),
        "finished_today": False,
        "big_image": None,
        "big_image_angle": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    wrong_file = project_dir / "wrong_words.json"
    if wrong_file.exists():
        try:
            with open(wrong_file, "r", encoding="utf-8") as f:
                st.session_state.wrong_words = set(json.load(f))
        except:
            pass

def save_wrong_words():
    wrong_file = project_dir / "wrong_words.json"
    with open(wrong_file, "w", encoding="utf-8") as f:
        json.dump(list(st.session_state.wrong_words), f)

def set_custom_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600;700&display=swap');
        * { font-family: 'Quicksand', 'Comic Sans MS', sans-serif; color: #333333; }
        .stApp { background-color: #f7f9fc; max-width: 800px; margin: 0 auto; }
        .main > div { padding: 0 20px; }
        .card { background: white; border-radius: 24px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: 12px 0; }
        .huge-text { font-size: 36px; font-weight: 700; }
        .progress-rabbit { text-align: center; font-size: 28px; margin-bottom: 10px; }
        .sidebar .sidebar-content { background: #fff3e0; }

        /* 所有按钮统一加大 */
        .stButton > button {
            padding: 16px 32px !important;
            font-size: 22px !important;
            border-radius: 16px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }
        .stButton > button[kind="primary"] { background: #38BDF8 !important; }
        .stButton > button[kind="primary"]:hover { background: #0ea5e9 !important; }

        /* 大图区域旋转按钮（大蓝色） */
        #big-image-section .stButton > button:not(:last-child) {
            background: #2196F3 !important;
            font-size: 28px !important;
            padding: 24px 40px !important;
            width: 100% !important;
        }
        #big-image-section .stButton > button:not(:last-child):hover {
            background: #1976D2 !important;
        }

        /* 关闭大图按钮（巨大红色） */
        #big-image-section .stButton:last-child > button {
            background: #f44336 !important;
            font-size: 32px !important;
            padding: 28px 60px !important;
            border-radius: 24px !important;
            width: 100% !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
        }
        #big-image-section .stButton:last-child > button:hover {
            background: #d32f2f !important;
        }

        /* 隐藏默认图片工具栏（右上角黑色放大缩小按钮） */
        .stImage > button { display: none !important; }
        .element-container .stImage > div > div > button { display: none !important; }

        /* 输入框 */
        .stTextInput input, .stTextArea textarea {
            color: #333 !important;
            background: white !important;
            border: 2px solid #ddd !important;
            border-radius: 12px !important;
            padding: 16px !important;
            font-size: 20px !important;
        }

        /* 进度条 */
        .stProgress > div > div { background: linear-gradient(90deg, #38BDF8, #A3E635) !important; }

        /* 反馈信息 */
        .stSuccess { color: #2e7d32; background: #e8f5e9; padding: 16px; border-radius: 16px; font-size: 22px; }
        .stWarning { color: #e65100; background: #fff3e0; padding: 16px; border-radius: 16px; font-size: 22px; }
        .stInfo { color: #1565c0; background: #e3f2fd; padding: 16px; border-radius: 16px; font-size: 22px; }
        </style>
    """, unsafe_allow_html=True)

def main():
    init_state()
    set_custom_style()
    data = load_course_data()
    if data is None:
        st.warning("Please generate course_data.json first."); return

    with st.sidebar:
        st.markdown("## 👨‍👦 Parent Control")
        video_cfg = load_video_config()
        new_url = st.text_input("📺 YouTube URL", value=video_cfg.get("youtube_url",""))
        if st.button("💾 Save", use_container_width=True):
            save_video_config(new_url); st.success("Saved!"); st.rerun()
        st.divider()
        total_sessions = data['course_metadata']['total_sessions']
        st.markdown(f"**Stars**: {'⭐'*min(st.session_state.stars,5)} {st.session_state.stars}")
        st.markdown(f"**Session**: {st.session_state.current_session+1}/{total_sessions}")
        if st.button("Reset Progress", use_container_width=True):
            for k in ["current_session","current_exercise","score","stars","finished_today"]:
                st.session_state.pop(k, None); st.rerun()

    weeks = data.get("weeks", [])
    if not weeks: st.warning("No course data"); return
    all_sessions = [s for w in weeks for s in w.get("sessions", [])]
    total = len(all_sessions)
    if total == 0: st.warning("No sessions"); return
    sess_idx = st.session_state.current_session % total
    sess = all_sessions[sess_idx]

    col1, col2, col3 = st.columns([1,6,1])
    with col1: st.markdown("🏠")
    with col2:
        ex_list = sess.get("exercises", [])
        prog = min(st.session_state.current_exercise / max(len(ex_list),1), 1.0)
        st.progress(prog)
        st.markdown(f"<div class='progress-rabbit'>🐰 Session {sess_idx+1}/{total}</div>", unsafe_allow_html=True)
    with col3: st.markdown(f"⭐{st.session_state.score}")
    st.markdown("---")
    st.markdown(f"## 📖 {sess.get('title','')}")

    # 视频卡片
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        yt = load_video_config().get("youtube_url","")
        embed = parse_youtube_url(yt)
        if embed:
            st.components.v1.html(f'<div style="position:relative;padding-bottom:56.25%;height:0;"><iframe src="{embed}" style="position:absolute;top:0;left:0;width:100%;height:100%;" frameborder="0" allowfullscreen></iframe></div>', height=0)
        else:
            st.info("Enter a YouTube URL in the sidebar and save it.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 核心词汇（不含中文）
    vocab = sess.get("vocabulary", [])
    if vocab:
        st.markdown("### 🗂️ Vocabulary")
        cols = st.columns(min(len(vocab), 3))
        for i, wd in enumerate(vocab):
            with cols[i % 3]:
                st.markdown("<div class='card' style='text-align:center;'>", unsafe_allow_html=True)
                img_fn = wd.get("image","")
                fp = resolve_image_path(img_fn)
                if fp and fp.exists():
                    st.image(fp, width=120, use_container_width=False)
                    if st.button("🔍 View Large", key=f"big_{sess_idx}_{i}", use_container_width=True):
                        st.session_state.big_image = str(fp)
                        st.session_state.big_image_angle = 0
                        st.rerun()
                else:
                    letter = wd["word"][0].upper()
                    seed = sum(ord(c) for c in wd["word"])
                    r,g,b = (seed*37)%200+55, (seed*41)%200+55, (seed*43)%200+55
                    st.markdown(f'<div style="width:120px;height:160px;background:rgb({r},{g},{b});border-radius:12px;display:flex;align-items:center;justify-content:center;margin:0 auto;"><span style="font-size:56px;color:white;font-weight:bold;">{letter}</span></div>', unsafe_allow_html=True)
                st.markdown(f"<span style='font-size:28px;font-weight:bold;'>{wd['word']}</span>", unsafe_allow_html=True)
                audio_button(wd["word"], key_suffix=f"voc_{sess_idx}_{i}")
                st.markdown("</div>", unsafe_allow_html=True)

    # 大图显示
    if st.session_state.big_image and os.path.exists(st.session_state.big_image):
        st.markdown("---")
        st.markdown('<div id="big-image-section">', unsafe_allow_html=True)
        st.markdown("### 🖼️ Large Image")
        img_path = Path(st.session_state.big_image)
        angle = st.session_state.big_image_angle % 360
        rotated_path = rotate_image(img_path, angle)
        st.image(rotated_path, use_container_width=True, clamp=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🔄 Rotate Left 90°", use_container_width=True):
                st.session_state.big_image_angle -= 90; st.rerun()
        with col_b2:
            if st.button("🔄 Rotate Right 90°", use_container_width=True):
                st.session_state.big_image_angle += 90; st.rerun()
        if st.button("✖ Close Image (Back)", key="close_big_image", use_container_width=True):
            st.session_state.big_image = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 练习题
    st.markdown("---")
    exercises = sess.get("exercises", [])
    ex_idx = st.session_state.current_exercise
    if ex_idx < len(exercises):
        ex = exercises[ex_idx]
        st.markdown(f"### ✏️ Exercise {ex_idx+1}/{len(exercises)}")
        q_type = ex.get("type","")
        if q_type == "listening_image":
            audio_text = ex.get("audio_text","")
            options = ex.get("options",[])
            correct = ex.get("correct","")
            st.markdown("🔊 **Listen and Choose** – press play, then pick the correct word.")
            audio_button(audio_text, label="🔊 Listen", key_suffix=f"listen_{ex['question_id']}")
            col_opts = st.columns(min(len(options),4))
            for j, opt in enumerate(options):
                opt_text = opt.get("text","")
                opt_img = opt.get("image","")
                with col_opts[j]:
                    fp = resolve_image_path(opt_img)
                    if fp and fp.exists():
                        st.image(fp, width=80, use_container_width=False)
                    if st.button(opt_text, key=f"opt_{ex['question_id']}_{j}", use_container_width=True):
                        if opt_text == correct:
                            st.balloons()
                            st.session_state.score += 10
                            st.session_state.stars += 1
                            st.success("✅ Correct! Great job!")
                        else:
                            st.warning("Think again!")
                            st.session_state.wrong_words.add(audio_text)
                            save_wrong_words()
            if st.button("Next ➔", key=f"next_{ex['question_id']}", use_container_width=True, type="primary"):
                st.session_state.current_exercise += 1; st.rerun()
        elif q_type == "spelling_puzzle":
            word = ex.get("word","")
            scrambled = ex.get("scrambled",[])
            st.markdown("**Spell the word** – type the letters in correct order.")
            img_w = ex.get("image","")
            fp = resolve_image_path(img_w)
            if fp and fp.exists():
                st.image(fp, width=100, use_container_width=False)
            user_input = st.text_input("Type the word (lowercase)", key=f"spell_{ex['question_id']}")
            if st.button("Check", key=f"check_{ex['question_id']}"):
                if user_input.strip() == word:
                    st.balloons(); st.session_state.score += 10; st.success("✅ Spelling correct!")
                else:
                    st.warning(f"Hint: {', '.join(scrambled)}")
            st.markdown("**Scrambled letters**: " + " ".join(scrambled))
            audio_button(word, label="🔊 Listen", key_suffix=f"spell_{ex['question_id']}")
            if st.button("Next ➔", key=f"next_spell_{ex['question_id']}", use_container_width=True, type="primary"):
                st.session_state.current_exercise += 1; st.rerun()
        elif q_type == "shadowing":
            sentence = ex.get("sentence","")
            chinese = ex.get("chinese","")
            st.markdown("### 🎤 Shadow the sentence")
            st.markdown(f"<div class='card' style='text-align:center;font-size:32px;'>{sentence}</div>", unsafe_allow_html=True)
            audio_button(sentence, label="🔊 Listen first", key_suffix=f"shadow_{ex['question_id']}")
            ph = f"shadow_{ex['question_id']}"
            recorder_widget(ph, key_suffix=ex['question_id'])
            voice_result = st.text_area("Your voice", placeholder=ph, key=ph, height=80)
            if voice_result and voice_result.strip():
                if voice_result.strip().lower() == sentence.lower():
                    st.balloons(); st.success("🌟 Perfect pronunciation!"); st.session_state.score += 20
                else:
                    st.info("💪 Keep trying!")
            if st.button("Next ➔", key=f"next_shadow_{ex['question_id']}", use_container_width=True, type="primary"):
                st.session_state.current_exercise += 1; st.rerun()
        else:
            st.info("Unknown exercise type")
            if st.button("Next"):
                st.session_state.current_exercise += 1; st.rerun()
    else:
        st.success("🎉 You've finished today's session!"); st.balloons()
        st.markdown(f"## Score: {st.session_state.score}")
        if not st.session_state.finished_today:
            st.session_state.finished_today = True; save_wrong_words()
        if st.button("Next Session 🚀", use_container_width=True, type="primary"):
            st.session_state.current_session += 1
            st.session_state.current_exercise = 0
            st.session_state.finished_today = False
            st.rerun()

if __name__ == "__main__":
    main()
