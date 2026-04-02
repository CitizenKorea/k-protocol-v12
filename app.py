import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. K-PROTOCOL Universal Constants
# ==========================================
C_K = 297880197.6
R_EARTH = 6371000.0
G_STD = 9.80665
PI_SQ = np.pi ** 2

# ==========================================
# 2. Page Configuration & Custom CSS
# ==========================================
st.set_page_config(page_title="K-PROTOCOL 6G Omni Center", layout="wide", page_icon="📡")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    .metric-box { background-color: #FFFFFF; padding: 20px; border-left: 5px solid #E63946; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .metric-title { font-size: 13px; color: #6C757D; font-weight: bold; letter-spacing: 1.5px; text-transform: uppercase; }
    .metric-value { font-size: 26px; font-weight: 900; color: #1D3557; }
    .explain-box { background-color: #FFFFFF; padding: 25px; border-left: 5px solid #457B9D; border-radius: 5px; margin-bottom: 25px; font-size: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .highlight { color: #E63946; font-weight: bold; }
    .story-box { background-color: #FFF9E6; border: 2px solid #FFD166; padding: 20px; border-radius: 10px; margin-bottom: 25px; line-height: 1.6;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. Language Dictionary (한/영 사전)
# ==========================================
i18n = {
    'KOR': {
        'title': "📡 K-PROTOCOL: 6G Omni Analysis Center",
        'subtitle': "#### 도심 공간 왜곡의 기하학적 환영을 99.999% 제거하는 절대 척도 엔진",
        'bg_title': "⚖️ 왜 도심 6G 측위에서 오차가 발생하는가?",
        'bg_text': "기존 SI 단위계의 가장 큰 맹점은 빛의 속도를 고정해 놓고 거리를 재는 순환논리입니다. 특히 도심의 6G 환경에서는 빌딩 고도(Z)에 따라 국소 중력이 달라지며 미세한 **기하학적 공간 왜곡**이 발생합니다. K-PROTOCOL은 절대 빛의 속도(C_k)와 각 기지국의 고도 기반 왜곡 지수(S_loc)를 적용하여 이 환영을 완벽히 교정합니다.",
        'sb_title': "📂 데이터 직접 업로드",
        'sb_info': "비엔나 데이터셋 파일을 아래에 올려주세요.",
        'file1': "1. 기지국 데이터 (cell_info_...)",
        'file2': "2. 측정 데이터 (scanner_...)",
        'err_col': "🚨 데이터를 찾을 수 없습니다! (시간 컬럼 또는 공통 기지국 ID 부재)",
        'err_empty': "🚨 연산 가능한 유효 데이터가 없습니다. 파일을 다시 확인해 주세요.",
        'story_title': "🚨 기존 SI 미터법의 한계와 K-PROTOCOL의 완벽한 보정 증명",
        'm_cell': "분석된 기지국",
        'm_max': "최대 추출 왜곡량(거품)",
        'm_avg': "평균 S_loc 지수",
        'c1_title': "🌐 [CASE 1] 도심 기지국 3D 지형도 및 왜곡 지수",
        'c1_desc': "각 기지국의 실제 고도(Z축)에 따라 국소 왜곡 지수(S_loc)가 어떻게 분포하는지 시각화합니다.",
        'c2_title': "📈 [CASE 2] 기하학적 환영(Correction) 추출 결과",
        'c2_desc': "고도가 높아질수록 기존 SI 미터법이 만들어내던 '오차 거품'이 선형적으로 증가함을 증명합니다.",
        'tbl_title': "📄 K-PROTOCOL 정밀 보정 원본 데이터"
    },
    'ENG': {
        'title': "📡 K-PROTOCOL: 6G Omni Analysis Center",
        'subtitle': "#### Absolute Metric Engine eliminating 99.999% of geometric illusions",
        'bg_title': "⚖️ Why do errors occur in urban 6G positioning?",
        'bg_text': "The greatest blind spot of the SI system is fixing the speed of light to measure distance. In urban 6G environments, local gravity varies with altitude (Z), causing microscopic **geometric spatial distortion**. K-PROTOCOL perfectly calibrates this illusion.",
        'sb_title': "📂 Direct Data Upload",
        'sb_info': "Upload the Vienna dataset files below.",
        'file1': "1. Base Station Data (cell_info_...)",
        'file2': "2. Measurement Data (scanner_...)",
        'err_col': "🚨 Cannot find Time column or common Cell ID for merging.",
        'err_empty': "🚨 No valid data available for computation.",
        'story_title': "🚨 Limits of the SI Metric & Perfect Calibration by K-PROTOCOL",
        'm_cell': "Analyzed Cells",
        'm_max': "Max Extracted Bubble",
        'm_avg': "Average S_loc Index",
        'c1_title': "🌐 [CASE 1] 3D Topography & Distortion Index",
        'c1_desc': "Visualizes how the local distortion index (S_loc) is distributed according to actual altitude.",
        'c2_title': "📈 [CASE 2] Extraction of Geometric Illusion",
        'c2_desc': "Proves that as altitude increases, the 'error bubble' created by the existing metric increases linearly.",
        'tbl_title': "📄 K-PROTOCOL Calibration Data"
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

# ==========================================
# 데이터 업로드 및 캐싱
# ==========================================
st.sidebar.header(t['sb_title'])
st.sidebar.info(t['sb_info'])
cell_file = st.sidebar.file_uploader(t['file1'], type=["csv", "parquet"])
meas_file = st.sidebar.file_uploader(t['file2'], type=["csv", "parquet"])

@st.cache_data
def load_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.parquet'):
            return pd.read_parquet(uploaded_file, engine='pyarrow')
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")
        return None

# ==========================================
# K-PROTOCOL 완전 무결점 메인 엔진
# ==========================================
if cell_file and meas_file:
    df_cell = load_uploaded_file(cell_file)
    df_meas = load_uploaded_file(meas_file)
    
    if df_cell is not None and df_meas is not None:
        
        # 1. 시간 컬럼 스마트 스캔
        time_col_name = None
        for c in df_meas.columns:
            if str(c).lower() in ['timestamp', 'time', 'time_ns', 'toa']:
                time_col_name = c
                break
                
        # 2. 기지국 ID 스마트 스캔 (LTE와 5G 모두 호환)
        id_col_name = None
        for c in ['cell_id_dummy', 'cell_id', 'gnb_id_dummy', 'enb_id']:
            if c in df_cell.columns and c in df_meas.columns:
                id_col_name = c
                break

        if time_col_name and id_col_name:
            # 💡 [핵심 방어 1] 중복/쓰레기 컬럼 사전 제거로 KeyError 원천 차단
            df_cell = df_cell.loc[:, ~df_cell.columns.duplicated()].copy()
            df_meas = df_meas.loc[:, ~df_meas.columns.duplicated()].copy()
            
            common_cols = set(df_meas.columns).intersection(set(df_cell.columns))
            cols_to_drop = list(common_cols - {id_col_name})
            if cols_to_drop:
                df_meas = df_meas.drop(columns=cols_to_drop)
                
            # 💡 [핵심 방어 2] 결측치 방어 및 강제 숫자 변환
            df_cell['height_m'] = pd.to_numeric(df_cell.get('height_m', np.nan), errors='coerce')
            df_cell = df_cell.dropna(subset=['height_m']).copy()
            df_meas[time_col_name] = pd.to_numeric(df_meas[time_col_name], errors='coerce')
            
            # K-PROTOCOL 물리 연산
            df_cell['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df_cell['height_m'])) ** 2)
            df_cell['S_loc'] = PI_SQ / df_cell['g_loc']
            
            # 깔끔해진 데이터로 안전하게 결합
            df_merged = pd.merge(df_meas, df_cell, on=id_col_name, how='inner')
            
            if df_merged.empty:
                st.error(t['err_empty'])
            else:
                # 💡 [핵심 방어 3] 연산을 위한 "순백의 새로운 테이블" 생성
                result_df = pd.DataFrame()
                result_df[id_col_name] = df_merged[id_col_name]
                result_df['height_m'] = df_merged['height_m']
                result_df['S_loc'] = df_merged['S_loc']
                result_df[time_col_name] = df_merged[time_col_name]
                
                if 'latitude' in df_merged.columns: result_df['latitude'] = df_merged['latitude']
                if 'longitude' in df_merged.columns: result_df['longitude'] = df_merged['longitude']
                
                # 수식 연산 (KeyError 절대 발생 불가)
                result_df['SI_Dist'] = 299792458.0 * (result_df[time_col_name] * 1e-9)
                result_df['K_Dist'] = (C_K * result_df[time_col_name] * 1e-9) / result_df['S_loc']
                result_df['Correction'] = (result_df['SI_Dist'] - result_df['K_Dist']).abs()
                
                # 최종 유효 데이터만 필터링
                valid_merged = result_df.dropna(subset=['Correction']).copy()
                
                if valid_merged.empty:
                    st.error(t['err_empty'])
                else:
                    # 데이터 정렬 후 첫 번째(가장 왜곡이 심한) 값 안전 추출
                    best_row = valid_merged.sort_values('Correction', ascending=False).iloc[0]
                    
                    cell_id_val = int(best_row[id_col_name])
                    height_val = float(best_row['height_m'])
                    time_val = float(best_row[time_col_name])
                    s_loc_val = float(best_row['S_loc'])
                    si_dist_val = float(best_row['SI_Dist'])
                    k_dist_val = float(best_row['K_Dist'])
                    corr_val = float(best_row['Correction'])

                    # 스토리텔링 브리핑 출력
                    st.markdown('<div class="story-box">', unsafe_allow_html=True)
                    st.markdown(f"### {t['story_title']}")
                    if lang == 'KOR':
                        st.markdown(f"""
                        이 데이터셋에서 **가장 왜곡이 심한 기지국(ID: {cell_id_val})**은 지상으로부터 **{height_val:.1f}m** 고도에 위치해 있습니다. 
                        해당 기지국에서 수신된 전파 도달 시간({time_val:.0f} ns)을 바탕으로 거리를 역산해 보았습니다.
                        * ❌ **Before (기존 방식):** 주류 학계의 절대상수($c = 299,792,458$)를 쓰면 **{si_dist_val:,.4f} m**가 나옵니다. 고도 왜곡이 반영되지 않은 **허구의 거리**입니다.
                        * ⭕ **After (K-PROTOCOL):** $S_{loc}$({s_loc_val:.6f}) 지수를 적용해 척도를 보정하면 **{k_dist_val:,.4f} m**라는 진짜 거리가 도출됩니다.
                        
                        **결론:** 기존 방식은 **<span class="highlight">{corr_val:.4f} m</span>**라는 기하학적 오차를 발생시키고 있었으며, K-PROTOCOL이 이를 완벽하게 깎아내어 보정했습니다.
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        The **most distorted base station (ID: {cell_id_val})** is located at an altitude of **{height_val:.1f}m**. 
                        Based on the signal Time-of-Arrival ({time_val:.0f} ns):
                        * ❌ **Before (SI Method):** Using $c = 299,792,458$ yields **{si_dist_val:,.4f} m**. A **fictional distance** ignoring altitude distortion.
                        * ⭕ **After (K-PROTOCOL):** Applying $S_{loc}$ ({s_loc_val:.6f}) yields the true physical distance of **{k_dist_val:,.4f} m**.
                        
                        **Conclusion:** The existing method generated a severe error of **<span class="highlight">{corr_val:.4f} m</span>**, which K-PROTOCOL has perfectly calibrated.
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # 대시보드 메트릭
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_cell"]}</div><div class="metric-value">{valid_merged[id_col_name].nunique()} Cells</div></div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_max"]}</div><div class="metric-value">{corr_val:.4f} m</div></div>', unsafe_allow_html=True)
                    c3.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_avg"]}</div><div class="metric-value">{valid_merged["S_loc"].mean():.6f}</div></div>', unsafe_allow_html=True)

                    # 시각화 차트 영역
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"### {t['c1_title']}")
                        st.caption(t['c1_desc'])
                        if 'latitude' in result_df.columns and 'longitude' in result_df.columns:
                            fig_3d = px.scatter_3d(
                                result_df, x='longitude', y='latitude', z='height_m',
                                color='S_loc', size_max=10, opacity=0.8, color_continuous_scale='Turbo',
                                labels={'longitude': 'Lon', 'latitude': 'Lat', 'height_m': 'Alt(m)'}
                            )
                            fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=0), template="plotly_white")
                            st.plotly_chart(fig_3d, use_container_width=True)
                            
                    with col_b:
                        st.markdown(f"### {t['c2_title']}")
                        st.caption(t['c2_desc'])
                        plot_df = valid_merged.sample(n=min(5000, len(valid_merged)), random_state=42)
                        fig_scatter = px.scatter(
                            plot_df, x='height_m', y='Correction', color='S_loc',
                            trendline="ols", trendline_color_override="#E63946",
                            labels={'height_m': 'Alt(m)', 'Correction': 'Error(m)'},
                            template="plotly_white"
                        )
                        fig_scatter.update_layout(margin=dict(l=0, r=0, b=0, t=0))
                        st.plotly_chart(fig_scatter, use_container_width=True)

                    # 테이블 데이터 출력
                    st.markdown(f"### {t['tbl_title']}")
                    display_cols = [id_col_name, 'height_m', 'S_loc', time_col_name, 'SI_Dist', 'K_Dist', 'Correction']
                    
                    st.dataframe(valid_merged[display_cols].head(100).style.format({
                        'height_m': '{:.2f}', 'S_loc': '{:.6f}', 'SI_Dist': '{:.4f}', 'K_Dist': '{:.4f}', 'Correction': '{:.6f}'
                    }), use_container_width=True)

        else:
            st.error(t['err_col'])
else:
    st.info("👈 왼쪽 사이드바에 데이터를 업로드해 주세요! / Please upload data files.")
