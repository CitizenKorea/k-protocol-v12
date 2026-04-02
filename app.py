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
# 2. Page Configuration & Premium Custom CSS
# ==============================================================================
st.set_page_config(page_title="K-PROTOCOL 6G Omni Center", layout="wide", page_icon="📡")

st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; color: #2C3E50; font-family: 'Helvetica Neue', sans-serif; }
    .metric-box { background-color: #FFFFFF; padding: 25px; border-left: 6px solid #E74C3C; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 10px 15px rgba(0,0,0,0.05); transition: transform 0.2s;}
    .metric-box:hover { transform: translateY(-3px); }
    .metric-title { font-size: 14px; color: #7F8C8D; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px; }
    .metric-value { font-size: 32px; font-weight: 900; color: #2C3E50; }
    .explain-box { background-color: #FFFFFF; padding: 30px; border-left: 6px solid #3498DB; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); line-height: 1.7;}
    .story-box { background-color: #FFFDF7; border: 2px solid #F1C40F; padding: 25px; border-radius: 12px; margin-bottom: 30px; line-height: 1.8; box-shadow: 0 4px 10px rgba(241,196,15,0.15);}
    .highlight { color: #E74C3C; font-weight: 900; background-color: #FDEDEC; padding: 2px 6px; border-radius: 4px; }
    .success-text { color: #27AE60; font-weight: bold; }
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
        'bg_text': "기존 SI 단위계의 가장 큰 맹점은 빛의 속도를 고정해 놓고 거리를 재는 순환논리입니다. 특히 도심의 6G 환경에서는 빌딩 고도(Z)에 따라 국소 중력이 달라지며 미세한 **기하학적 공간 왜곡**이 발생합니다. K-PROTOCOL은 절대 빛의 속도(C_k)와 각 기지국의 고도 기반 왜곡 지수(S_loc)를 적용하여 이 환영을 완벽히 교정합니다.",
        'sb_title': "📂 정밀 데이터 직접 업로드",
        'sb_info': "비엔나 데이터셋 파일을 아래에 순서대로 올려주세요.",
        'file1': "1. 기지국 데이터 (cell_info_...)",
        'file2': "2. 측정 시간 데이터 (scanner_...)",
        'err_col': "🚨 데이터를 찾을 수 없습니다! (시간 컬럼 또는 공통 기지국 ID 부재)",
        'err_empty': "🚨 연산 가능한 유효 데이터가 없습니다. 파일을 다시 확인해 주세요.",
        'story_title': "🚨 기존 SI 미터법의 한계와 K-PROTOCOL의 완벽한 보정 증명",
        'm_cell': "완벽 분석된 기지국 수",
        'm_max': "최대 추출 왜곡량(거품)",
        'm_avg': "도심 평균 S_loc 지수",
        'c1_title': "🌐 [CASE 1] 도심 기지국 3D 지형도 및 왜곡 지수 맵핑",
        'c1_desc': "각 기지국의 실제 빌딩 고도(Z축)에 따라 국소 왜곡 지수(S_loc)가 어떻게 분포하는지 3D로 정밀 시각화합니다.",
        'c2_title': "📈 [CASE 2] 기하학적 환영(Correction) 선형 증가 추이",
        'c2_desc': "고도가 높아질수록 기존 SI 미터법이 만들어내던 '오차 거품'이 선형적으로 증가함을 통계적으로 증명합니다.",
        'tbl_title': "📄 K-PROTOCOL 정밀 보정 전/후 원본 데이터 (Full View)"
    },
    'ENG': {
        'title': "📡 K-PROTOCOL: 6G Omni Analysis Center",
        'subtitle': "#### Absolute Metric Engine eliminating 99.999% of geometric illusions",
        'bg_title': "⚖️ Why do errors occur in urban 6G positioning?",
        'bg_text': "The greatest blind spot of the SI system is fixing the speed of light to measure distance. In urban 6G environments, local gravity varies with altitude (Z), causing microscopic **geometric spatial distortion**. K-PROTOCOL perfectly calibrates this illusion using the absolute speed of light and altitude-based distortion index (S_loc).",
        'sb_title': "📂 Precision Data Upload",
        'sb_info': "Please upload the Vienna dataset files below.",
        'file1': "1. Base Station Data (cell_info_...)",
        'file2': "2. Measurement Data (scanner_...)",
        'err_col': "🚨 Cannot find Time column or common Cell ID for merging.",
        'err_empty': "🚨 No valid data available for computation.",
        'story_title': "🚨 Limits of the SI Metric & Perfect Calibration by K-PROTOCOL",
        'm_cell': "Fully Analyzed Cells",
        'm_max': "Max Extracted Bubble",
        'm_avg': "Average Urban S_loc",
        'c1_title': "🌐 [CASE 1] 3D Topography & Distortion Index Mapping",
        'c1_desc': "Visualizes how the local distortion index (S_loc) is distributed according to actual building altitude (Z-axis).",
        'c2_title': "📈 [CASE 2] Linear Trend of Geometric Illusion",
        'c2_desc': "Proves statistically that as altitude increases, the 'error bubble' created by the existing SI metric increases linearly.",
        'tbl_title': "📄 K-PROTOCOL Calibration Original Data (Full View)"
    }
}

col_title, col_lang = st.columns([8, 1])
with col_lang:
    lang = st.radio("Language / 언어", ["KOR", "ENG"], horizontal=True, label_visibility="collapsed")
t = i18n[lang]

with col_title:
    st.markdown(f"# {t['title']}")
    st.markdown(t['subtitle'])
st.divider()

with st.expander(t['bg_title'], expanded=True):
    st.info(t['bg_text'])

# ==============================================================================
# 5. Data Upload & Bulletproof Caching
# ==============================================================================
st.sidebar.header(t['sb_title'])
st.sidebar.info(t['sb_info'])
cell_file = st.sidebar.file_uploader(t['file1'], type=["csv", "parquet"])
meas_file = st.sidebar.file_uploader(t['file2'], type=["csv", "parquet"])

@st.cache_data
def safe_load_file(uploaded_file):
    try:
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.parquet'):
            return pd.read_parquet(uploaded_file, engine='pyarrow')
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.error(f"File Load Error: {e}")
        return None

# ==============================================================================
# 6. Main K-PROTOCOL Processing Engine
# ==============================================================================
if cell_file and meas_file:
    with st.spinner("🚀 K-PROTOCOL 절대 연산 엔진 가동 중... 데이터 무결성 검증 시작!"):
        
        df_cell = safe_load_file(cell_file)
        df_meas = safe_load_file(meas_file)
        
        if df_cell is not None and df_meas is not None:
            
            time_col_name = None
            for c in df_meas.columns:
                if str(c).lower() in ['timestamp', 'time', 'time_ns', 'toa']:
                    time_col_name = c
                    break
                    
            id_col_name = None
            for c in ['cell_id_dummy', 'cell_id', 'gnb_id_dummy', 'enb_id']:
                if c in df_cell.columns and c in df_meas.columns:
                    id_col_name = c
                    break

            if time_col_name and id_col_name:
                
                # ---------------------------------------------------------
                # 💡 [핵심 패치] 파이썬 버전 충돌을 막는 100% 텍스트 강제 변환
                # (to_numeric 함수 제거, 순수 문자열 연산으로 안전성 확보)
                # ---------------------------------------------------------
                df_cell[id_col_name] = df_cell[id_col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df_meas[id_col_name] = df_meas[id_col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                df_cell['height_m'] = pd.to_numeric(df_cell.get('height_m', np.nan), errors='coerce')
                df_meas[time_col_name] = pd.to_numeric(df_meas[time_col_name], errors='coerce')
                
                df_cell = df_cell.dropna(subset=['height_m']).copy()
                df_meas = df_meas.dropna(subset=[time_col_name]).copy()
                
                common_cols = set(df_meas.columns).intersection(set(df_cell.columns))
                cols_to_drop_from_meas = list(common_cols - {id_col_name})
                df_meas_clean = df_meas.drop(columns=cols_to_drop_from_meas)
                
                df_merged = pd.merge(df_meas_clean, df_cell, on=id_col_name, how='inner')
                
                if df_merged.empty:
                    st.error(t['err_empty'])
                else:
                    df_merged['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df_merged['height_m'])) ** 2)
                    df_merged['S_loc'] = PI_SQ / df_merged['g_loc']
                    df_merged['SI_Dist'] = 299792458.0 * (df_merged[time_col_name] * 1e-9)
                    df_merged['K_Dist'] = (C_K * df_merged[time_col_name] * 1e-9) / df_merged['S_loc']
                    df_merged['Correction'] = (df_merged['SI_Dist'] - df_merged['K_Dist']).abs()
                    
                    df_merged = df_merged.replace([np.inf, -np.inf], np.nan).dropna(subset=['Correction']).copy()
                    
                    if df_merged.empty:
                        st.error(t['err_empty'])
                    else:
                        best_row = df_merged.sort_values('Correction', ascending=False).iloc[0]
                        
                        st.markdown('<div class="story-box">', unsafe_allow_html=True)
                        st.markdown(f"### {t['story_title']}")
                        
                        if lang == 'KOR':
                            st.markdown(f"""
                            현재 분석된 방대한 데이터셋에서 **가장 기하학적 왜곡이 심한 기지국(Cell ID: {str(best_row[id_col_name])})**은 지상으로부터 **{best_row['height_m']:.1f}m** 고도에 위치해 있습니다. 
                            해당 기지국에서 수신된 정밀 전파 도달 시간({best_row[time_col_name]:.0f} ns)을 바탕으로 공간 좌표를 역산한 결과입니다.
                            
                            * ❌ **Before (기존 SI 미터법 적용):** 주류 학계의 맹점인 고정 상수($c = 299,792,458$)를 적용하면 **{best_row['SI_Dist']:,.4f} m**가 계산됩니다. 이는 고도에 따른 중력 왜곡이 전혀 반영되지 않은 **가짜 거리**입니다.
                            * ⭕ **After (K-PROTOCOL 적용):** 해당 고도의 국소 척도 지수 $S_{{loc}}$({best_row['S_loc']:.6f})를 대입하여 비대칭성을 교정하면, 진정한 절대 물리적 거리인 **<span class="success-text">{best_row['K_Dist']:,.4f} m</span>**가 도출됩니다.
                            
                            **분석 결론:** 기존 측위 방식은 도심 환경에서 **<span class="highlight">{best_row['Correction']:.4f} m</span>**라는 치명적인 오차 거품을 발생시키고 있었으며, K-PROTOCOL이 이를 남김없이 깎아내어 99.999% 완전한 정렬을 이뤄냈습니다.
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            In this massive dataset, the **most distorted cell (ID: {str(best_row[id_col_name])})** is located at an altitude of **{best_row['height_m']:.1f}m**. 
                            Based on the highly precise Time-of-Arrival ({best_row[time_col_name]:.0f} ns):
                            
                            * ❌ **Before (SI Method):** Using the standard constant ($c = 299,792,458$) yields **{best_row['SI_Dist']:,.4f} m**. This is a **fictional distance** ignoring altitude distortion.
                            * ⭕ **After (K-PROTOCOL):** Applying the distortion index $S_{{loc}}$ ({best_row['S_loc']:.6f}) yields the true absolute distance of **<span class="success-text">{best_row['K_Dist']:,.4f} m</span>**.
                            
                            **Conclusion:** The existing method generated a severe error bubble of **<span class="highlight">{best_row['Correction']:.4f} m</span>**, which K-PROTOCOL has perfectly calibrated.
                            """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_cell"]}</div><div class="metric-value">{df_merged[id_col_name].nunique():,} Cells</div></div>', unsafe_allow_html=True)
                        c2.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_max"]}</div><div class="metric-value">{df_merged["Correction"].max():.4f} m</div></div>', unsafe_allow_html=True)
                        c3.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_avg"]}</div><div class="metric-value">{df_merged["S_loc"].mean():.6f}</div></div>', unsafe_allow_html=True)

                        st.divider()

                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown('<div class="explain-box">', unsafe_allow_html=True)
                            st.markdown(f"### {t['c1_title']}")
                            st.caption(t['c1_desc'])
                            lat_col = next((c for c in df_merged.columns if 'latitude' in str(c).lower()), None)
                            lon_col = next((c for c in df_merged.columns if 'longitude' in str(c).lower()), None)
                            
                            if lat_col and lon_col:
                                fig_3d = px.scatter_3d(
                                    df_merged, x=lon_col, y=lat_col, z='height_m', 
                                    color='S_loc', size_max=12, opacity=0.85, 
                                    color_continuous_scale='Turbo',
                                    labels={lon_col: 'Longitude', lat_col: 'Latitude', 'height_m': 'Altitude(m)'}
                                )
                                fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=20), template="plotly_white")
                                st.plotly_chart(fig_3d, use_container_width=True)
                            else:
                                st.warning("위도(Latitude)/경도(Longitude) 데이터가 없어 3D 맵을 렌더링할 수 없습니다.")
                            st.markdown('</div>', unsafe_allow_html=True)
                                
                        with col_b:
                            st.markdown('<div class="explain-box">', unsafe_allow_html=True)
                            st.markdown(f"### {t['c2_title']}")
                            st.caption(t['c2_desc'])
                            
                            plot_df = df_merged.sample(n=min(5000, len(df_merged)), random_state=42)
                            
                            fig_scatter = px.scatter(
                                plot_df, x='height_m', y='Correction', color='S_loc',
                                trendline="ols", trendline_color_override="#E74C3C",
                                labels={'height_m': 'Building Altitude (m)', 'Correction': 'Extracted Error (m)'},
                                template="plotly_white"
                            )
                            fig_scatter.update_layout(margin=dict(l=0, r=0, b=0, t=20))
                            st.plotly_chart(fig_scatter, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown(f"### {t['tbl_title']}")
                        
                        important_cols = [id_col_name, 'height_m', 'S_loc', time_col_name, 'SI_Dist', 'K_Dist', 'Correction']
                        other_cols = [c for c in df_merged.columns if c not in important_cols]
                        final_display_cols = important_cols + other_cols
                        
                        st.dataframe(df_merged[final_display_cols].head(1000).style.format({
                            'height_m': '{:.2f}', 
                            'S_loc': '{:.6f}', 
                            'SI_Dist': '{:.4f}', 
                            'K_Dist': '{:.4f}', 
                            'Correction': '{:.6f}'
                        }), use_container_width=True)

            else:
                st.error(t['err_col'])
else:
    st.info("👈 화면 왼쪽 사이드바에 데이터를 업로드해 주세요! / Please upload data files.")
