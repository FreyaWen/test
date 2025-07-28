# streamlit run ./procedure/encoding_matrics_web.py
# streamlit run encoding_matrics_web.py

import streamlit as st
import random
from datetime import datetime
import os
import pandas as pd
from audio_recorder_streamlit import audio_recorder

# ===== 配置参数 =====
WORD_POOL_FILE = 'word_pool.txt'  # 词池路径
N_TRIALS = 10  # 实验的轮次数
DATA_DIR = 'data'  # 数据存储路径
os.makedirs(DATA_DIR, exist_ok=True)

# ===== 读取词池 =====
@st.cache_data
def load_word_pool():
    with open(WORD_POOL_FILE, 'r', encoding='utf-8') as f:
        raw = f.read().replace('\n', '、').replace('，', '、').replace(',', '、')
        words = list({w.strip() for w in raw.split('、') if w.strip()})
    return words

# ===== 页面设置 =====
st.set_page_config(page_title="Encoding Task", layout="centered")
st.title("🧠 Encoding Task")

# ===== 实验信息填写 =====
if 'start' not in st.session_state:
    st.markdown("请填写以下信息以开始实验：")
    with st.form(key='info_form'):
        col1, col2 = st.columns(2)
        group = col1.selectbox("被试分组（决定每轮目标词数量）", ["1", "2", "3"])
        sub_id = col2.text_input("被试编号", max_chars=10)
        gender = col1.selectbox("性别", ["male", "female"])
        age = col2.text_input("年龄")
        handedness = col1.selectbox("利手", ["right", "left", "both"])
        submitted = st.form_submit_button("开始实验")

    if submitted and sub_id:
        st.session_state['start'] = True
        st.session_state['group'] = int(group)
        st.session_state['sub_id'] = sub_id
        st.session_state['gender'] = gender
        st.session_state['age'] = age
        st.session_state['handedness'] = handedness
        st.session_state['trial'] = 0
        st.session_state['results'] = []

        # 只在第一次加载时加载词池
        if 'word_list' not in st.session_state:
            st.session_state['word_list'] = load_word_pool()
            random.shuffle(st.session_state['word_list'])

        total_needed = N_TRIALS * st.session_state['group']
        if len(st.session_state['word_list']) < total_needed:
            st.error("❌ 词语池不足，请检查 word_pool.txt 文件。")
            st.stop()
        st.rerun()

# ===== 实验主程序 =====
if st.session_state.get('start', False):
    trial = st.session_state['trial']
    group_n = st.session_state['group']
    word_list = st.session_state['word_list']

    if trial < N_TRIALS:
        # 确保每个试次的目标词是固定的
        if f'target_words_trial_{trial}' not in st.session_state:
            # 每个试次根据被试分组随机确定目标词数量
            target_count = group_n  # 根据分组来设置目标词数量
            total_words = 9  # 每轮展示 9 个词
            non_target_count = total_words - target_count
            target_words = random.sample(word_list, target_count)  # 随机选取目标词
            non_target_words = random.sample([w for w in word_list if w not in target_words], non_target_count)  # 随机选取非目标词
            all_words = target_words + non_target_words
            random.shuffle(all_words)  # 打乱词汇顺序
            matrix = [all_words[i:i + 3] for i in range(0, 9, 3)]  # 3x3 矩阵

            # 将当前试次的目标词保存到 session_state
            st.session_state[f'target_words_trial_{trial}'] = target_words
            st.session_state[f'matrix_trial_{trial}'] = matrix  # 保存矩阵数据

        target_words = st.session_state[f'target_words_trial_{trial}']  # 从 session_state 中加载目标词
        matrix = st.session_state[f'matrix_trial_{trial}']  # 从 session_state 中加载矩阵

        # 展示实验轮次和目标词
        st.subheader(f"第 {trial + 1} 轮 / 共 {N_TRIALS} 轮")
        st.markdown(f"### 🎯 目标词：**{', '.join(target_words)}**")

        # 创建矩阵，目标词加色
        for row in matrix:
            row_html = ""
            for word in row:
                if word in target_words:
                    row_html += f"<span style='background-color: yellow; padding: 3px;'>{word}</span>&nbsp;&nbsp;"
                else:
                    row_html += f"{word}&nbsp;&nbsp;"
            st.markdown(row_html, unsafe_allow_html=True)

        # 音频录制部分：使用 Streamlit 的 audio_recorder
        st.markdown("### 🎤 请录制你的音频")

        # 初始化录音标志
        if 'record_flag' not in st.session_state:
            st.session_state['record_flag'] = False

        # 控制按钮：点击按钮来开始录音
        def start_recording():
            st.session_state['record_flag'] = True

        # 控制按钮：点击按钮来停止录音
        def stop_recording():
            st.session_state['record_flag'] = False

        # 显示开始录音和停止录音的按钮
        if st.session_state['record_flag']:
            # 录音进行中
            audio_bytes = audio_recorder()
            st.button("停止录音", on_click=stop_recording)
        else:
            # 录音停止
            audio_bytes = None
            st.button("开始录音", on_click=start_recording)

        if audio_bytes:
            # 保存音频文件
            audio_filename = f"{st.session_state['sub_id']}_Trial{trial + 1}.wav"
            audio_path = os.path.join(DATA_DIR, audio_filename)

            # 保存音频文件到本地
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            # 保存录音结果
            st.session_state["audio_filename"] = audio_filename
            st.success(f"音频录制完成，文件名：{audio_filename}")
            st.audio(audio_bytes, format="audio/wav")  # 播放录音

            # 保存实验数据
            result = {
                'group': group_n,
                'sub_id': st.session_state['sub_id'],
                'gender': st.session_state['gender'],
                'age': st.session_state['age'],
                'handedness': st.session_state['handedness'],
                'trial': trial + 1,
                'target_words': ', '.join(target_words),
                'audio_filename': audio_filename,  # 保存音频文件名
                'cue_word': '',  # 线索词可以后续添加
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            st.session_state['results'].append(result)

        # 收集线索词
        with st.form(key=f'trial_form_{trial}'):
            cue = st.text_input("请输入你联想到的线索词", key=f'cue_{trial}')
            submitted = st.form_submit_button("提交")

        # 提交线索词后更新结果并继续下一轮
        if submitted:
            if not cue.strip():
                st.warning("⚠️ 请先输入线索词！")
            else:
                # 更新结果中的线索词
                st.session_state['results'][-1]['cue_word'] = cue.strip()
                st.session_state['trial'] += 1
                st.experimental_rerun()  # 提交后更新试次

    else:
        # 实验完成，保存数据
        filename = f"encoding_G{group_n}S{st.session_state['sub_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        save_path = os.path.join(DATA_DIR, filename)
        df = pd.DataFrame(st.session_state['results'])
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        st.success("🎉 实验完成，感谢参与！")
        st.markdown(f"📄 数据已保存为：`{filename}`")
        st.dataframe(df)

        if st.button("重新开始实验"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
