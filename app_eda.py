import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        ---
        **Population Trends 데이터셋 소개**  
        - 출처: 통계청 지역별 인구 동향 데이터  
        - 설명: 전국 및 각 지역(광역시·도)의 연도별 인구, 출생아수, 사망자수를 포함한 시계열 데이터로, 
          인구 구조의 변화와 지역 간 인구 격차를 분석할 수 있음  
        - 주요 변수:  
          - `연도`: 기준 연도  
          - `지역`: 전국, 시·도 구분  
          - `인구`: 각 연도 말 기준 인구 수 (명)  
          - `출생아수(명)`: 해당 연도 출생아 수  
          - `사망자수(명)`: 해당 연도 사망자 수

        이 앱에서는 이 데이터를 바탕으로 **연도별 인구 추이**, **지역 간 변화량 비교**, **인구 변화 예측** 등 다양한 분석을 제공합니다.
        각 탭에서 시각화와 통계 분석을 통해 인사이트를 얻어보세요!
        """)
        
# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
REGION_TRANSLATIONS = {
    "서울": "Seoul",
    "부산": "Busan",
    "대구": "Daegu",
    "인천": "Incheon",
    "광주": "Gwangju",
    "대전": "Daejeon",
    "울산": "Ulsan",
    "세종": "Sejong",
    "경기": "Gyeonggi",
    "강원": "Gangwon",
    "충북": "Chungbuk",
    "충남": "Chungnam",
    "전북": "Jeonbuk",
    "전남": "Jeonnam",
    "경북": "Gyeongbuk",
    "경남": "Gyeongnam",
    "제주": "Jeju",
    "전국": "National"
}

class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")

        uploaded_file = st.file_uploader("Upload population_trends.csv", type=["csv"])
        if not uploaded_file:
            st.info("Please upload the population_trends.csv file.")
            return

        df = pd.read_csv(uploaded_file)

        # Replace '-' with 0 in Sejong rows and convert columns to numeric
        df.replace('-', np.nan, inplace=True)
        df[df['지역'] == '세종'] = df[df['지역'] == '세종'].fillna('0')
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Convert 연도 to int
        df['연도'] = pd.to_numeric(df['연도'], errors='coerce').astype(int)

        # Translate region names
        df['지역'] = df['지역'].replace(REGION_TRANSLATIONS)

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
        ])

        with tab1:
            st.header("기초 통계")
            st.subheader("데이터프레임 구조")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("기초 통계량")
            st.dataframe(df.describe())

        with tab2:
            st.header("연도별 전체 인구 추이")
            national_df = df[df['지역'] == 'National']
            fig, ax = plt.subplots()
            ax.plot(national_df['연도'], national_df['인구'], label='Population')

            # Predict 2035 population safely
            recent = national_df.sort_values('연도', ascending=False).head(3)
            if len(recent) >= 3 and not recent[['출생아수(명)', '사망자수(명)']].isnull().any().any():
                net_change = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
                latest_year = national_df['연도'].max()
                latest_population = national_df.loc[national_df['연도'] == latest_year, '인구']
                if not latest_population.empty:
                    projected = latest_population.values[0] + net_change * (2035 - latest_year)
                    ax.plot(2035, projected, 'ro', label='Predicted 2035')

            ax.set_title("Yearly Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

        with tab3:
            st.header("지역별 인구 변화량 분석")
            latest_year = df['연도'].max()
            past_year = latest_year - 5
            delta_df = df[df['연도'].isin([past_year, latest_year])]
            pivot = delta_df.pivot(index='지역', columns='연도', values='인구')
            pivot.drop('National', errors='ignore', inplace=True)
            pivot['diff'] = pivot[latest_year] - pivot[past_year]
            pivot['rate'] = (pivot['diff'] / pivot[past_year]) * 100

            # Horizontal bar graph of diff
            fig1, ax1 = plt.subplots()
            pivot_sorted_diff = pivot.sort_values('diff', ascending=False)
            sns.barplot(x='diff', y='지역', data=pivot_sorted_diff.reset_index(), ax=ax1)
            ax1.set_title("Population Change in 5 Years")
            ax1.set_xlabel("Change (x1000)")
            ax1.set_ylabel("Region")
            st.pyplot(fig1)

            # Horizontal bar graph of rate (sorted by rate)
            fig2, ax2 = plt.subplots()
            pivot_sorted_rate = pivot.sort_values('rate', ascending=False)
            sns.barplot(x='rate', y='지역', data=pivot_sorted_rate.reset_index(), ax=ax2)
            ax2.set_title("Growth Rate in 5 Years (%)")
            ax2.set_xlabel("Rate (%)")
            ax2.set_ylabel("Region")
            st.pyplot(fig2)
            st.markdown("> Insight: Regions with highest absolute or relative growth are visible at the top of the charts.")

        with tab4:
            st.header("증감률 상위 지역 및 연도")
            temp_df = df[df['지역'] != 'National'].copy()
            temp_df.sort_values(['지역', '연도'], inplace=True)
            temp_df['증감'] = temp_df.groupby('지역')['인구'].diff()

            top100 = temp_df.sort_values('증감', ascending=False).head(100)
            styled = top100[['연도', '지역', '인구', '증감']].style.format({'증감': '{:,.0f}', '인구': '{:,.0f}'}).background_gradient(
                subset='증감', cmap='bwr', vmin=-top100['증감'].abs().max(), vmax=top100['증감'].abs().max())
            st.dataframe(styled, use_container_width=True)

        with tab5:
            st.header("누적 영역 그래프 시각화")
            pivot_area = df[df['지역'] != 'National'].pivot(index='연도', columns='지역', values='인구')
            pivot_area.fillna(0, inplace=True)

            fig, ax = plt.subplots(figsize=(12, 6))
            pivot_area.plot.area(ax=ax, cmap='tab20', linewidth=0)
            ax.set_title("Population Area by Region")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
