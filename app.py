import streamlit as st
import pandas as pd
import numpy as np

# 페이지 기본 설정
st.set_page_config(page_title="K-PROTOCOL 6G Engine", layout="wide")
st.title("📡 K-PROTOCOL: 도심 6G 기하학적 왜곡 보정")

# --- K-PROTOCOL 절대 상수 ---
C_K = 297880197.6
R_EARTH = 6371000.0
G_STD = 9.80665
PI_SQ = np.pi ** 2

st.sidebar.header("📁 데이터 업로드 (드래그 앤 드롭)")
st.sidebar.info("용량이 큰 파일도 바로 올려주시면 됩니다!")
cell_file = st.sidebar.file_uploader("1. 기지국 데이터 (cell_info_final...)", type=["csv", "parquet"])
meas_file = st.sidebar.file_uploader("2. 측정 데이터 (scanner_measurements...)", type=["csv", "parquet"])

# 대용량 파일을 빠르게 처리하기 위한 캐싱 적용
@st.cache_data
def load_data(file):
    if file.name.endswith('.parquet'):
        return pd.read_parquet(file)
    return pd.read_csv(file)

if cell_file:
    df_cell = load_data(cell_file)
    
    if 'height_m' in df_cell.columns:
        # 고도가 없는 데이터 제외
        df_cell = df_cell.dropna(subset=['height_m']).copy()
        
        # 1단계: S_loc 계산
        df_cell['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df_cell['height_m'])) ** 2)
        df_cell['S_loc'] = PI_SQ / df_cell['g_loc']
        
        st.subheader("1. 🏢 기지국 고도 및 왜곡 지수 분석 완료")
        st.dataframe(df_cell[['cell_id_dummy', 'height_m', 'g_loc', 'S_loc']].head(10))

        if meas_file:
            df_meas = load_data(meas_file)
            
            # [자동 컬럼 매칭] 이름이 달라도 알아서 찾아냅니다!
            time_col = next((c for c in df_meas.columns if c in ['timestamp', 'time', 'time_ns']), None)
            id_col = 'cell_id_dummy'
            
            if time_col and id_col in df_meas.columns:
                # 데이터 결합
                df_merged = pd.merge(df_meas, df_cell[[id_col, 'S_loc']], on=id_col, how='inner')
                
                # K-PROTOCOL 보정 연산
                df_merged['SI_Dist(m)'] = 299792458.0 * (df_merged[time_col] * 1e-9)
                df_merged['K_Dist(m)'] = (C_K * df_merged[time_col] * 1e-9) / df_merged['S_loc']
                df_merged['Residual(오차)'] = np.abs(df_merged['SI_Dist(m)'] - df_merged['K_Dist(m)'])
                
                st.subheader("2. 🚀 6G 절대 거리 보정 결과")
                st.dataframe(df_merged[[id_col, time_col, 'S_loc', 'SI_Dist(m)', 'K_Dist(m)', 'Residual(오차)']].head(100))
            else:
                st.error("측정 파일에 시간이나 ID 컬럼을 찾을 수 없습니다. 컬럼명을 확인해 주세요.")
    else:
        st.error("기지국 데이터에 고도(height_m) 컬럼이 없습니다.")
else:
    st.info("👈 왼쪽 사이드바에 파일들을 드래그 앤 드롭해 주세요!")
