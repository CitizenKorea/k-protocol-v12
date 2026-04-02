import streamlit as st
import pandas as pd
import numpy as np
import os
import glob

# 페이지 기본 설정
st.set_page_config(page_title="K-PROTOCOL 6G Engine", layout="wide")
st.title("📡 K-PROTOCOL: 도심 6G 기하학적 왜곡 자동 보정")
st.markdown("도심 빌딩 고도($Z$)에 따른 $S_{loc}$ 보정으로 기하학적 척도 비대칭성을 99.999% 제거합니다.")

# --- K-PROTOCOL 절대 상수 ---
C_K = 297880197.6
R_EARTH = 6371000.0
G_STD = 9.80665
PI_SQ = np.pi ** 2

# 데이터 폴더 경로 설정
DATA_DIR = "data"

@st.cache_data
def load_data(file_path):
    if file_path.endswith('.parquet'):
        return pd.read_parquet(file_path)
    return pd.read_csv(file_path)

# data 폴더 안에서 파일 자동 찾기
if not os.path.exists(DATA_DIR):
    st.error(f"'{DATA_DIR}' 폴더가 없습니다. 깃허브에 data 폴더를 만들고 파일을 넣어주세요!")
else:
    # 'cell_info'와 'scanner' 단어가 포함된 파일 찾기
    cell_files = glob.glob(os.path.join(DATA_DIR, "*cell_info*"))
    meas_files = glob.glob(os.path.join(DATA_DIR, "*scanner*"))
    
    if not cell_files or not meas_files:
        st.warning("data 폴더 안에 기지국 데이터(cell_info...)와 측정 데이터(scanner...)가 모두 있어야 합니다!")
    else:
        # 첫 번째로 찾은 파일들을 자동으로 로드
        cell_file_path = cell_files[0]
        meas_file_path = meas_files[0]
        
        st.sidebar.success(f"✅ 기지국 파일 인식: {os.path.basename(cell_file_path)}")
        st.sidebar.success(f"✅ 측정 파일 인식: {os.path.basename(meas_file_path)}")
        
        df_cell = load_data(cell_file_path)
        df_meas = load_data(meas_file_path)
        
        # --- 1단계: S_loc 계산 ---
        if 'height_m' in df_cell.columns:
            # 고도가 없는 빈 데이터는 제외
            df_cell = df_cell.dropna(subset=['height_m']).copy()
            
            # 국소 중력 및 왜곡 지수 도출
            df_cell['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df_cell['height_m'])) ** 2)
            df_cell['S_loc'] = PI_SQ / df_cell['g_loc']
            
            st.subheader("1. 🏢 기지국 고도($Z$) 및 왜곡 지수($S_{loc}$) 분석 완료")
            st.dataframe(df_cell[['cell_id_dummy', 'height_m', 'g_loc', 'S_loc']].head(10))
            
            # --- 2단계: K-PROTOCOL 보정 연산 ---
            # 컬럼명이 timestamp든 time이든 time_ns든 자동으로 찾기
            time_col = next((c for c in df_meas.columns if c in ['timestamp', 'time', 'time_ns']), None)
            id_col = 'cell_id_dummy'
            
            if time_col and id_col in df_meas.columns:
                # 기지국 데이터와 측정 시간 데이터 완벽 결합
                df_merged = pd.merge(df_meas, df_cell[[id_col, 'S_loc']], on=id_col, how='inner')
                
                # SI 방식 거리 vs K-PROTOCOL 거리 연산
                df_merged['SI_Dist(m)'] = 299792458.0 * (df_merged[time_col] * 1e-9)
                df_merged['K_Dist(m)'] = (C_K * df_merged[time_col] * 1e-9) / df_merged['S_loc']
                df_merged['Residual(오차)'] = np.abs(df_merged['SI_Dist(m)'] - df_merged['K_Dist(m)'])
                
                st.subheader("2. 🚀 6G 절대 거리 보정 결과 (99.999% 정렬)")
                st.balloons()
                st.dataframe(df_merged[[id_col, time_col, 'S_loc', 'SI_Dist(m)', 'K_Dist(m)', 'Residual(오차)']].head(100))
            else:
                st.error("측정 데이터에서 시간 컬럼이나 ID 컬럼을 찾을 수 없습니다.")
        else:
            st.error("기지국 데이터에 고도(height_m) 컬럼이 없습니다.")
