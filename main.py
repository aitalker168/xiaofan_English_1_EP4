import os, sys, json, re
from pathlib import Path
project_dir = Path(__file__).resolve().parent

import streamlit as st
st.set_page_config(page_title="⭐ English Learner", layout="centered", initial_sidebar_state="collapsed")

from utils import (
    load_course_data, load_video_config, save_video_config,
    parse_youtube_url, audio_button, recorder_widget,
    resolve_image_path, rotate_image, IMAGE_DIR
)
import streamlit.components.v1 as components

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
        "grammar_video_loaded": False,
        "grammar_video_id": "",
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
        .stButton > button { color: white !important; background: #4CAF50; border: none !important; padding: 16px 32px !important; font-size: 22px !important; border-radius: 16px !important; font-weight: 700 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important; }
        .stButton > button:hover { background: #45a049; }
        .stButton > button[kind="primary"] { background: #38BDF8 !important; }
        .stButton > button[kind="primary"]:hover { background: #0ea5e9 !important; }
        #big-image-section .stButton > button:not(:last-child) { background: #2196F3 !important; font-size: 28px !important; padding: 24px 40px !important; width: 100% !important; }
        #big-image-section .stButton > button:not(:last-child):hover { background: #1976D2 !important; }
        #big-image-section .stButton:last-child > button { background: #f44336 !important; font-size: 32px !important; padding: 28px 60px !important; border-radius: 24px !important; width: 100% !important; box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important; }
        #big-image-section .stButton:last-child > button:hover { background: #d32f2f !important; }
        .stImage > button { display: none !important; }
        .element-container .stImage > div > div > button { display: none !important; }
        .stTextInput input, .stTextArea textarea { color: #333 !important; background: white !important; border: 2px solid #ddd !important; border-radius: 12px !important; padding: 16px !important; font-size: 20px !important; }
        .stProgress > div > div { background: linear-gradient(90deg, #38BDF8, #A3E635) !important; }
        .stSuccess { color: #2e7d32; background: #e8f5e9; padding: 16px; border-radius: 16px; font-size: 22px; }
        .stWarning { color: #e65100; background: #fff3e0; padding: 16px; border-radius: 16px; font-size: 22px; }
        .stInfo { color: #1565c0; background: #e3f2fd; padding: 16px; border-radius: 16px; font-size: 22px; }
        </style>
    """, unsafe_allow_html=True)

def parse_youtube_video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|/v/)([a-zA-Z0-9_-]{11})", url)
    return m.group(1) if m else ""

def main():
    init_state()
    set_custom_style()

    # 检测关闭语法视频参数（通过URL参数通信）
    query_params = st.query_params
    if "close_grammar" in query_params:
        st.session_state.grammar_video_loaded = False
        st.session_state.grammar_video_id = ""
        st.query_params.clear()
        st.rerun()

    data = load_course_data()
    if data is None:
        st.warning("Please generate course_data.json first."); return

    # ========= 侧边栏 =========
    with st.sidebar:
        st.markdown("## 👨‍👦 Parent Control")
        video_cfg = load_video_config()
        new_url = st.text_input("📺 Lesson YouTube URL", value=video_cfg.get("youtube_url",""))
        if st.button("💾 Save Lesson Video", use_container_width=True):
            save_video_config(new_url); st.success("Saved!"); st.rerun()
        st.divider()
        total_sessions = data['course_metadata']['total_sessions']
        st.markdown(f"**Stars**: {'⭐'*min(st.session_state.stars,5)} {st.session_state.stars}")
        st.markdown(f"**Session**: {st.session_state.current_session+1}/{total_sessions}")
        if st.button("Reset Progress", use_container_width=True):
            for k in ["current_session","current_exercise","score","stars","finished_today","grammar_video_loaded"]:
                st.session_state.pop(k, None); st.rerun()

    # ========= 语法视频输入与加载（始终显示） =========
    st.markdown("---")
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        grammar_url = st.text_input("🎬 Grammar Video (optional)", 
                                    value=st.session_state.get("grammar_url_input",""),
                                    key="grammar_url_input",
                                    placeholder="Paste YouTube grammar video link here")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📥 Load Video", use_container_width=True):
            vid = parse_youtube_video_id(grammar_url)
            if vid:
                st.session_state.grammar_video_id = vid
                st.session_state.grammar_video_loaded = True
                st.rerun()
            else:
                st.error("Invalid YouTube URL")
    st.markdown("---")

    # ========= 语法视频播放器 + 控制按钮（一体化，使用随机id避免冲突） =========
    if st.session_state.grammar_video_loaded and st.session_state.grammar_video_id:
        vid = st.session_state.grammar_video_id
        import random
        uid = random.randint(1000,9999)
        player_id = f"grammar_player_{uid}"

        html_code = f"""
        <div id="grammar-container-{uid}" style="background: white; border-radius: 24px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: 12px 0;">
            <h3 style="color: #333; font-family: 'Quicksand', sans-serif; margin-top:0;">🎬 Grammar Video</h3>
            <div style="position:relative; width:100%; max-width:800px; margin:0 auto;">
                <div style="position:relative; padding-bottom:56.25%; height:0;">
                    <iframe id="{player_id}" 
                        src="https://www.youtube.com/embed/{vid}?rel=0&modestbranding=1&controls=1&playsinline=1&iv_load_policy=3&cc_load_policy=0&enablejsapi=1" 
                        style="position:absolute; top:0; left:0; width:100%; height:100%; border-radius:12px;" 
                        frameborder="0" allowfullscreen>
                    </iframe>
                </div>
            </div>
            <div style="display:flex; gap:12px; margin-top:16px;">
                <button onclick="playVideo_{uid}()" style="flex:1; padding:16px; font-size:22px; background:#4CAF50; color:white; border:none; border-radius:16px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">▶️ Play</button>
                <button onclick="pauseVideo_{uid}()" style="flex:1; padding:16px; font-size:22px; background:#FF9800; color:white; border:none; border-radius:16px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">⏸️ Pause</button>
                <button onclick="closeVideo_{uid}()" style="flex:1; padding:16px; font-size:22px; background:#f44336; color:white; border:none; border-radius:16px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">✖ Close</button>
            </div>
        </div>
        <script>
        var tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        var firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        var player_{uid};
        function onYouTubeIframeAPIReady() {{
            player_{uid} = new YT.Player('{player_id}', {{}});
        }}
        function playVideo_{uid}() {{ if(player_{uid}) player_{uid}.playVideo(); }}
        function pauseVideo_{uid}() {{ if(player_{uid}) player_{uid}.pauseVideo(); }}
        function closeVideo_{uid}() {{
            if(player_{uid}) player_{uid}.pauseVideo();
            // 隐藏自身
            var container = document.getElementById('grammar-container-{uid}');
            if(container) container.style.display = 'none';
            // 通知父页面关闭（通过postMessage）
            window.parent.postMessage('close_grammar_video', '*');
        }}
        </script>
        """
        components.html(html_code, height=500)

        # 注入一个全局监听 postMessage 的脚本，用于接收关闭信号
        st.markdown("""
        <script>
        window.addEventListener('message', function(event) {
            if (event.data === 'close_grammar_video') {
                // 通过修改URL参数触发Streamlit rerun
                var url = new URL(window.location.href);
                url.searchParams.set('close_grammar', '1');
                window.history.replaceState({}, '', url.href);
                // 手动触发Streamlit的rerun（通过点击隐藏按钮）
                // 实际上 Streamlit 会自动检测 URL 变化？不，需要页面刷新或 rerun 事件。
                // 最可靠的是直接重新加载页面（可能会丢失进度，但不会丢失session_state）
                // 或者我们可以使用streamlit的js函数来rerun
                // 这里采用简单方式：直接设置location.href（会导致页面刷新，session_state保持）
                // 但是为了保留进度，我们更希望只触发rerun而不刷新页面。
                // 可以使用Streamlit的postMessage机制？不，没有标准API。
                // 替代：在Python端我们已经在main开始时检测了query_params，但是需要rerun才能检测。
                // 因此我们这里需要触发rerun。常用的技巧：在页面中添加一个隐藏的按钮点击事件。
                // 我们可以通过创建一个隐藏的a标签并点击来触发location.reload？不行。
                // 另一个方法：使用window.location.reload(true)。但会刷新页面。
                // 为了避免刷新导致session_state丢失（但session_state存储在服务端，刷新不丢失），可以接受。
                // 然而刷新会重置当前UI状态（如展开的面板），但无关紧要。
                // 为了效果更好，我们可以使用fetch一个虚拟请求来触发Streamlit rerun？太复杂。
                // 这里选择使用location.reload()，因为session_state是服务端的，刷新后仍然保留。
                // 但我们的session_state清除是在Python检测到close_grammar参数后执行的，刷新后参数还在，会清除状态。
                // 所以先清除参数再刷新？不行，需要先让Python处理。
                // 更合理：我们在closeVideo中已经隐藏了容器，用户看不到视频了。
                // 然后Python端不需要立刻清除状态，下次rerun时（如用户操作其他按钮）再清除。
                // 但为了保险，我们可以在closeVideo中设置一个cookie或sessionStorage，然后Python端在每次运行时检测。
                // 但Python无法读取浏览器存储。
                // 最简单：让用户点击Close后，容器隐藏，状态保留，下次加载新视频时自动替换。
                // 所以Python端不需要清除！我们只需要隐藏容器。
                // 因此我们在closeVideo中已经隐藏了容器，且没有触发rerun。
                // 这已经达到了“关闭”的效果——视频消失了。
                // 当用户下次点击Load Video时，会重新设置session_state，覆盖旧的，再次显示。
                // 所以Python端不需要清除状态。
                // 修改：移除之前的query参数检测，不再清除状态。
                // 但为了状态整洁，可以在Load Video时覆盖，不需要清除。
                // 因此我们简化：Close按钮只隐藏容器，不触发任何Python状态更改。
                // 这样最简单且可靠。
            }
        });
        </script>
        """, unsafe_allow_html=True)

    # ========= 主课程内容（与之前一致） =========
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

    # 课程视频卡片
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        yt = load_video_config().get("youtube_url","")
        embed = parse_youtube_url(yt)
        if embed:
            st.components.v1.html(f'<div style="position:relative;padding-bottom:56.25%;height:0;"><iframe src="{embed}" style="position:absolute;top:0;left:0;width:100%;height:100%;" frameborder="0" allowfullscreen></iframe></div>', height=0)
        else:
            st.info("Enter a YouTube URL in the sidebar and save it.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 词汇
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

    # 大图
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

    # 练习
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
