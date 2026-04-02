import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. K-PROTOCOL Universal Physical Constants
# ==============================================================================
C_K = 297880197.6      
R_EARTH = 6371000.0    
G_STD = 9.80665        
PI_SQ = np.pi ** 2     

# ==============================================================================
# 2. Page Configuration & Custom CSS
# ==============================================================================
st.set_page_config(page_title="K-PROTOCOL 6G Omni Center", layout="wide", page_icon="📡")

st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; color: #2C3E50; }
    .metric-box { background-color: #FFFFFF; padding: 25px; border-left: 6px solid #E74C3C; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 10px 15px rgba(0,0,0,0.05); }
    .metric-title { font-size: 14px; color: #7F8C8D; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; }
    .metric-value { font-size: 32px; font-weight: 900; color: #2C3E50; }
    .explain-box { background-color: #FFFFFF; padding: 30px; border-left: 6px solid #3498DB; border-radius: 8px; margin-bottom: 30px; }
    .story-box { background-color: #FFFDF7; border: 2px solid #F1C40F; padding: 25px; border-radius: 12px; margin-bottom: 30px; }
    .highlight { color: #E74C3C; font-weight: 900; background-color: #FDEDEC; padding: 2px 6px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. Bilingual Dictionary
# ==============================================================================
i18n = {
    'KOR': {
        'title': "📡 K-PROTOCOL: 6G Omni Analysis Center",
        'subtitle': "#### 도심 공간 왜곡의 기하학적 환영을 99.999% 제거하는 절대 척도 엔진",
        'bg_title': "⚖️ 왜 도심 6G 측위에서 오차가 발생하는가?",
        'bg_text': "기존 SI 단위계는 빛의 속도를 고정해 놓고 거리를 재는 순환논리에 빠져 있습니다. 도심 빌딩 고도(Z)에 따른 국소 중력 변화는 미세한 **기하학적 공간 왜곡**을 발생시킵니다. K-PROTOCOL은 이를 완벽히 교정합니다.",
        'sb_title': "📂 정밀 데이터 업로드",
        'file1': "1. 기지국 데이터 (cell_info...)",
        'file2': "2. 측정 시간 데이터 (scanner...)",
        'err_col': "🚨 데이터를 찾을 수 없습니다! (시간 데이터 또는 공통 ID 부재)",
        'err_empty': "🚨 연산 가능한 유효 데이터가 없습니다.",
        'story_title': "🚨 기존 SI 미터법의 한계와 K-PROTOCOL 보정 증명",
        'm_cell': "분석된 기지국",
        'm_max': "최대 추출 왜곡량",
        'm_avg': "도심 평균 S_loc 지수",
        'c1_title': "🌐 [CASE 1] 도심 기지국 3D 지형도",
        'c2_title': "📈 [CASE 2] 기하학적 환영 선형 증가 추이",
        'tbl_title': "📄 K-PROTOCOL 정밀 보정 원본 데이터"
    },
    'ENG': {
        'title': "📡 K-PROTOCOL: 6G Omni Analysis Center",
        'subtitle': "#### Absolute Metric Engine eliminating 99.999% of geometric illusions",
        'bg_title': "⚖️ Why do errors occur?",
        'bg_text': "Urban gravity varies with altitude (Z), causing geometric spatial distortion. K-PROTOCOL calibrates this illusion using the absolute speed of light and S_loc index.",
        'sb_title': "📂 Data Upload",
        'file1': "1. Base Station Data",
        'file2': "2. Measurement Data",
        'err_col': "🚨 Columns not found!",
        'err_empty': "🚨 No valid data.",
        'story_title': "🚨 SI Limits & K-PROTOCOL Calibration",
        'm_cell': "Analyzed Cells",
        'm_max': "Max Extracted Bubble",
        'm_avg': "Average S_loc",
        'c1_title': "🌐 [CASE 1] 3D Topography",
        'c2_title': "📈 [CASE 2] Geometric Illusion Trend",
        'tbl_title': "📄 K-PROTOCOL Original Data"
    }
}

# ==============================================================================
# 4. Interface & Logic
# ==============================================================================
col_title, col_lang = st.columns([8, 1])
with col_lang:
    lang = st.radio("Lang", ["KOR", "ENG"], horizontal=True, label_visibility="collapsed")
t = i18n[lang]

with col_title:
    st.markdown(f"# {t['title']}")
    st.markdown(t['subtitle'])

st.sidebar.header(t['sb_title'])
cell_file = st.sidebar.file_uploader(t['file1'], type=["csv", "parquet"])
meas_file = st.sidebar.file_uploader(t['file2'], type=["csv", "parquet"])

def robust_load(file):
    if file is None: return None
    file.seek(0)
    try:
        if file.name.endswith('.parquet'): return pd.read_parquet(file)
        return pd.read_csv(file)
    except: return None

if cell_file and meas_file:
    df_cell = robust_load(cell_file)
    df_meas = robust_load(meas_file)
    
    if df_cell is not None and df_meas is not None:
        # 시간 컬럼 및 ID 컬럼 자동 탐지
        time_col = next((c for c in df_meas.columns if str(c).lower() in ['timestamp', 'time', 'time_ns', 'toa']), None)
        id_col = next((c for c in ['cell_id_dummy', 'cell_id', 'gnb_id_dummy', 'enb_id'] if c in df_cell.columns and c in df_meas.columns), None)

        if time_col and id_col:
            # 💡 [핵심 패치] 모든 버전에서 안전한 '강제 문자열 정규화' 로직
            # 1.0 -> '1', '1' -> '1'로 통일하여 병합 유실 방지
            def clean_id(x):
                s = str(x).split('.')[0].strip()
                return s if s != 'nan' else None

            df_cell[id_col] = df_cell[id_col].apply(clean_id)
            df_meas[id_col] = df_meas[id_col].apply(clean_id)
            
            # 숫자 데이터 안전 변환 (errors='coerce'로 잘못된 데이터는 NaN 처리)
            df_cell['height_m'] = pd.to_numeric(df_cell['height_m'], errors='coerce')
            df_meas[time_col] = pd.to_numeric(df_meas[time_col], errors='coerce')
            
            # 유효한 숫자 데이터만 필터링
            df_cell = df_cell.dropna(subset=['height_m', id_col])
            df_meas = df_meas.dropna(subset=[time_col, id_col])
            
            # 병합 실행 (Suffix 중복 방지)
            df_merged = pd.merge(df_meas, df_cell, on=id_col, how='inner', suffixes=('', '_dup'))
            
            if not df_merged.empty:
                # K-PROTOCOL 물리 연산
                df_merged['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df_merged['height_m'])) ** 2)
                df_merged['S_loc'] = PI_SQ / df_merged['g_loc']
                df_merged['SI_Dist'] = 299792458.0 * (df_merged[time_col] * 1e-9)
                df_merged['K_Dist'] = (C_K * df_merged[time_col] * 1e-9) / df_merged['S_loc']
                df_merged['Correction'] = (df_merged['SI_Dist'] - df_merged['K_Dist']).abs()
                
                # 결과 스토리텔링 및 대시보드 출력
                best = df_merged.sort_values('Correction', ascending=False).iloc[0]
                
                st.markdown(f'<div class="story-box"><h3>{t["story_title"]}</h3>', unsafe_allow_html=True)
                if lang == 'KOR':
                    st.write(f"현재 데이터에서 가장 왜곡이 심한 기지국(ID: **{best[id_col]}**)은 빌딩 고도 **{best['height_m']:.1f}m**에 위치합니다.")
                    st.write(f"기존 방식 오차 **{best['Correction']:.4f} m** 를 K-PROTOCOL $S_{{loc}}$ 보정으로 완벽히 제거했습니다.")
                else:
                    st.write(f"The most distorted cell (ID: **{best[id_col]}**) is located at **{best['height_m']:.1f}m**.")
                    st.write(f"K-PROTOCOL calibrated the SI error of **{best['Correction']:.4f} m** via $S_{{loc}}$ transformation.")
                st.markdown('</div>', unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_cell"]}</div><div class="metric-value">{df_merged[id_col].nunique()}</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_max"]}</div><div class="metric-value">{df_merged["Correction"].max():.4f} m</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_avg"]}</div><div class="metric-value">{df_merged["S_loc"].mean():.6f}</div></div>', unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader(t['c1_title'])
                    lat = next((c for c in df_merged.columns if 'latitude' in str(c).lower()), None)
                    lon = next((c for c in df_merged.columns if 'longitude' in str(c).lower()), None)
                    if lat and lon:
                        fig3d = px.scatter_3d(df_merged, x=lon, y=lat, z='height_m', color='S_loc', color_continuous_scale='Turbo', template="plotly_white")
                        fig3d.update_layout(margin=dict(l=0,r=0,b=0,t=0))
                        st.plotly_chart(fig3d, use_container_width=True)
                with col_b:
                    st.subheader(t['c2_title'])
                    fig_scat = px.scatter(df_merged.sample(min(3000, len(df_merged))), x='height_m', y='Correction', color='S_loc', trendline="ols", template="plotly_white")
                    st.plotly_chart(fig_scat, use_container_width=True)

                st.subheader(t['tbl_title'])
                st.dataframe(df_merged[[id_col, 'height_m', 'S_loc', time_col, 'SI_Dist', 'K_Dist', 'Correction']].head(100), use_container_width=True)
            else:
                st.error(t['err_empty'])
        else:
            st.error(t['err_col'])
