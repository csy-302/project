from flask import Flask, render_template, request, redirect, url_for
import requests
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
import os
import random

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'search_db.db')

# 네이버 API 설정 (발급받은 키 입력)
CLIENT_ID = "5jqT2Bae0s2_LI6FdhOv"
CLIENT_SECRET = ""

def get_db_connection():
    # 데이터베이스 연결 및 딕셔너리 형태 설정
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_naver_weather():
    """네이버 날씨 정보를 크롤링하여 반환합니다."""
    try:
        # 네이버에서 '날씨' 검색 결과 페이지
        url = "https://search.naver.com/search.naver?query=날씨"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 온도 추출 (네이버 날씨의 현재 온도 클래스)
        temp_element = soup.select_one('.temperature_text strong')
        temp = temp_element.text.replace('현재 온도', '').strip() if temp_element else "0°"

        # 2. 날씨 상태 (흐림, 맑음 등)
        status_element = soup.select_one('.status_wrap .before_slash')
        status = status_element.text.strip() if status_element else "정보 없음"

        # 3. 미세먼지 상태
        dust_elements = soup.select('.today_chart_list .txt')
        dust = dust_elements[0].text.strip() if dust_elements else "보통"
        
        return {
            'temp': temp,
            'status': status,
            'dust': dust
        }
    except Exception as e:
        print(f"날씨 크롤링 중 오류 발생: {e}")
        return None

def get_constellation_fortune():
    try:
        url = "https://m.search.naver.com/search.naver?query=별자리+운세"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        fortune_list = []
        
        # [추가] 별자리별 아이콘 매핑 사전
        const_icons = {
            "물병자리": "♒", "물고기자리": "♓", "양자리": "♈", 
            "황소자리": "♉", "쌍둥이자리": "♊", "게자리": "♋", 
            "사자자리": "♌", "처녀자리": "♍", "천칭자리": "♎", 
            "전갈자리": "♏", "사수자리": "♐", "염소자리": "♑"
        }
        constellations = list(const_icons.keys())

        all_lis = soup.find_all('li')

        for li in all_lis:
            li_text = li.get_text(separator=" ", strip=True)
            for name in constellations:
                if any(f['name'] == name for f in fortune_list):
                    continue
                
                if name in li_text:
                    content = li_text.replace(name, "").replace("내용보기", "").strip()
                    if len(content) > 10:
                        fortune_list.append({
                            "name": name,
                            "icon": const_icons.get(name, "✨"), # [추가] 아이콘 할당
                            "content": content
                        })

        # 별자리 순서대로 정렬
        fortune_list.sort(key=lambda x: constellations.index(x['name']))
        return fortune_list
    except Exception as e:
        print(f"운세 아이콘 추가 중 오류: {e}")
        return []

def get_const_by_date(month, day):
    """월/일을 입력받아 별자리를 반환합니다."""
    if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "양자리"
    elif (month == 4 and day >= 20) or (month == 5 and day <= 20): return "황소자리"
    elif (month == 5 and day >= 21) or (month == 6 and day <= 21): return "쌍둥이자리"
    elif (month == 6 and day >= 22) or (month == 7 and day <= 22): return "게자리"
    elif (month == 7 and day >= 23) or (month == 8 and day <= 22): return "사자자리"
    elif (month == 8 and day >= 23) or (month == 9 and day <= 23): return "처녀자리"
    elif (month == 9 and day >= 24) or (month == 10 and day <= 22): return "천칭자리"
    elif (month == 10 and day >= 23) or (month == 11 and day <= 22): return "전갈자리"
    elif (month == 11 and day >= 23) or (month == 12 and day <= 24): return "사수자리"
    elif (month == 12 and day >= 25) or (month == 1 and day <= 19): return "염소자리"
    elif (month == 1 and day >= 20) or (month == 2 and day <= 18): return "물병자리"
    else: return "물고기자리"

@app.route('/fortune')
def fortune():
    fortune_data = get_constellation_fortune()
    
    # 생일 정보 가져오기 (예: 0520)
    birthday = request.args.get('birthday', '')
    my_fortune = None
    
    if birthday and len(birthday) == 4:
        try:
            month = int(birthday[:2])
            day = int(birthday[2:])
            my_const_name = get_const_by_date(month, day)
            
            # 전체 운세 리스트에서 내 별자리 찾기
            for f in fortune_data:
                if f['name'] == my_const_name:
                    my_fortune = f
                    break
        except:
            pass
            
    return render_template('fortune.html', fortunes=fortune_data, my_fortune=my_fortune, birthday=birthday)

def get_zodiac_fortune():
    """네이버에서 오늘의 띠별 운세를 크롤링합니다."""
    try:
        url = "https://m.search.naver.com/search.naver?query=띠별+운세"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        zodiac_list = []
        # 12지신 정보 매핑
        zodiac_icons = {
            "쥐띠": "🐭", "소띠": "🐮", "호랑이띠": "🐯", "토끼띠": "🐰", 
            "용띠": "🐲", "뱀띠": "🐍", "말띠": "🐴", "양띠": "🐑", 
            "원숭이띠": "🐵", "닭띠": "🐔", "개띠": "🐶", "돼지띠": "🐷"
        }
        zodiac_names = list(zodiac_icons.keys())

        # 모든 리스트 항목을 뒤져서 띠 이름이 포함된 데이터를 찾습니다.
        all_lis = soup.find_all('li')

        for li in all_lis:
            li_text = li.get_text(separator=" ", strip=True)
            for name in zodiac_names:
                if any(f['name'] == name for f in zodiac_list):
                    continue
                
                if name in li_text:
                    # '내용보기' 문구와 띠 이름을 제거하여 순수 운세만 추출
                    content = li_text.replace(name, "").replace("내용보기", "").strip()
                    if len(content) > 10:
                        zodiac_list.append({
                            "name": name,
                            "icon": zodiac_icons[name],
                            "content": content
                        })

        # 12지신 순서대로 정렬
        zodiac_list.sort(key=lambda x: zodiac_names.index(x['name']))
        return zodiac_list
    except Exception as e:
        print(f"띠별 운세 크롤링 오류: {e}")
        return []

def get_zodiac_name_by_year(year):
    """출생 연도를 입력받아 해당하는 띠 이름을 반환합니다."""
    # 12지신 순서 (자, 축, 인, 묘, 진, 사, 오, 미, 신, 유, 술, 해)
    zodiac_order = ["쥐띠", "소띠", "호랑이띠", "토끼띠", "용띠", "뱀띠", 
                    "말띠", "양띠", "원숭이띠", "닭띠", "개띠", "돼지띠"]
    
    # 공식: (연도 - 4) % 12
    index = (year - 4) % 12
    return zodiac_order[index]

# 띠별 운세 페이지 라우트
@app.route('/zodiac')
def zodiac_fortune():
    zodiac_data = get_zodiac_fortune()
    
    # 사용자가 입력한 출생 연도 가져오기 (예: 1995)
    birth_year = request.args.get('year', '')
    my_zodiac_fortune = None
    
    if birth_year and birth_year.isdigit():
        try:
            year = int(birth_year)
            my_zodiac_name = get_zodiac_name_by_year(year)
            
            # 전체 띠 리스트에서 내 띠 찾기
            for f in zodiac_data:
                if f['name'] == my_zodiac_name:
                    my_zodiac_fortune = f
                    break
        except:
            pass
            
    return render_template('zodiac.html', fortunes=zodiac_data, my_fortune=my_zodiac_fortune, year=birth_year)

def init_db():
    with app.app_context():
        conn = get_db_connection()
        # 기존 검색 로그 테이블
        conn.execute('''CREATE TABLE IF NOT EXISTS search_logs 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT, term_date DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS streamers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nickname TEXT NOT NULL,
                        profile_image TEXT,
                        channel_url TEXT,
                        is_partner BOOLEAN DEFAULT 1)''')
        
        # 기존 데이터를 완전히 지우고 최신 데이터로 업데이트
        conn.execute("DELETE FROM streamers") 
        
        # 2025년 기준 실제 활성 파트너 스트리머 채널 ID 반영
        sample_streamers = [
            ('풍월량', 'https://nng-phinf.pstatic.net/MjAyMzEyMjBfNzgg/MDAxNzAyOTk5MDU4NTQ1.q74UANafs4egu_GflqIXrKZvqweabjdsqb3q7F-vEPEg.0DlZf3Myopu6ITUmTkOYLU-GKcBLotgKn61A0o9ZAN4g.PNG/7d354ef2-b2a8-4276-8c12-5be7f6301ae0-profile_image-600x600.png?type=f120_120_na', 'https://chzzk.naver.com/7ce8032370ac5121dcabce7bad375ced'),
            ('한동숙', 'https://nng-phinf.pstatic.net/MjAyMzEyMTVfMTgx/MDAxNzAyNjAxMjEyMTYw.Hw6vs76aI0L1zeu4fziwXDE35gidFriwTSgAjq7KWxUg.0V3KaKvctGKcVYa76UiDVTXMjXeUSuUezHX6nGU4y9kg.PNG/123.png?type=f120_120_na', 'https://chzzk.naver.com/75cbf189b3bb8f9f687d2aca0d0a382b'),
            ('서새봄', 'https://nng-phinf.pstatic.net/MjAyMzEyMThfMTU0/MDAxNzAyODY5MDk1NTY1.oTT5XMYykEunzMRCJToJl5Fl7DUzs4QEGvjshF2E87cg.OJrKteepM6J4JyAkcNvGSG4b2bSO9h9BRu9uc07Oteog.JPEG/1702869083892.jpg?type=f120_120_na', 'https://chzzk.naver.com/458f6ec20b034f49e0fc6d03921646d2'),
            ('랄로', 'https://nng-phinf.pstatic.net/MjAyNDAyMTVfMTg5/MDAxNzA4MDAxOTkzNTM3.eFfaNqILr5WMC1imgLS-sUG85KB8dQpRGE7RuxRU8Jkg.TQ1EdEPnPVS256zEqmpPg-0IAcVBCP62gn0uiUMDu2sg.PNG/%ED%94%84%EC%82%AC_%EC%B4%88%EB%A1%9D.png?type=f120_120_na', 'https://chzzk.naver.com/3497a9a7221cc3ee5d3f95991d9f95e9'),
            ('괴물쥐', 'https://nng-phinf.pstatic.net/MjAyNDAxMjlfMzkg/MDAxNzA2NTMxMzQ1Nzkx.4gWW7mvPJ4VPeQ-2lKiJ0oP9aGdUWzlU3QhPaGDg6nQg.5QXsCUrhprxH3gEIhP5lRVqb24K6CKkt91t41dbiq1Ug.JPEG/%EA%B4%B4%EB%AC%BC%EC%A5%90.jpg?type=f120_120_na', 'https://chzzk.naver.com/c7ded8ea6b0605d3c78e18650d2df83b'),
            ('릴카', 'https://nng-phinf.pstatic.net/MjAyMzEyMTlfNzkg/MDAxNzAyOTU0MTY4MDM4.2EH-ix9ISRu6b9NHV4NX-ZbLR_IWtnSx05rra91S9g8g.LQl6er9Fy9_Axi0B8vdVYXoEYfl_i-eY7OwoPlDmcl0g.PNG/%ED%94%84%EB%A1%9C%ED%95%84_%EC%82%AC%EC%A7%84%28%EC%A0%95%EB%B0%A9%ED%98%95%29.png?type=f120_120_na', 'https://chzzk.naver.com/4d0b7d3f825ea982b95f0a5c2b4782d3'),
            ('양띵', 'https://nng-phinf.pstatic.net/MjAyNDAxMjBfMjQ5/MDAxNzA1NzM0MTcwNjIy.zAtW4G0NeaCL9rUx1epXqp_0ilbmJL6Tw8PA3Z032YYg.S1g5UC4nEzxXXELyAkR8CxAZlXxx9dv6q7-LNg5xa1Ug.PNG/6020327d-1cd3-4afb-aefd-62cfbb6f9695-profile_image-300x300.png?type=f120_120_na', 'https://chzzk.naver.com/1aeb0ca60649660a2e534592ce480f34')
        ]
        
        conn.executemany("INSERT INTO streamers (nickname, profile_image, channel_url) VALUES (?, ?, ?)", sample_streamers)
        conn.commit()
        conn.close()
        print("[*] 치지직 채널 주소 정밀 업데이트 완료")

@app.route('/chzzk')
def chzzk_list():
    conn = get_db_connection()
    streamers = conn.execute("SELECT * FROM streamers").fetchall()
    conn.close()
    return render_template('chzzk.html', streamers=streamers)

# Flask 실행 시 맨 처음 딱 한 번만 실행되도록 설정
with app.app_context():
    init_db()

def get_recommended_menu(weather_status):
    """날씨 상태에 맞는 메뉴 하나를 무작위로 추천합니다."""
    # 날씨별 메뉴 데이터베이스
    menu_db = {
        "비": ["짬뽕", "해물파전", "칼국수", "수제비", "쌀국수", "부대찌개"],
        "눈": ["우동", "라면", "만두전골", "샤브샤브", "김치찌개"],
        "흐림": ["된장찌개", "국밥", "버섯전골", "아구찜", "고등어조림"],
        "맑음": ["냉면", "비빔밥", "돈가스", "초밥", "파스타", "샌드위치", "제육볶음"],
        "더움": ["메밀소바", "콩국수", "물회", "막국수"]
    }
    
    # 상태 판별 로직
    if "비" in weather_status:
        category = "비"
    elif "눈" in weather_status:
        category = "눈"
    elif "흐림" in weather_status or "구름" in weather_status:
        category = "흐림"
    elif "더움" in weather_status: # 기온이 높을 때 대비 (필요시 추가)
        category = "더움"
    else:
        category = "맑음"
    
    return random.choice(menu_db[category])

def get_random_quote():
    """오늘의 명언 리스트 중 하나를 반환합니다."""
    quotes = [
        {"text": "어제보다 나은 내일을 만드는 건 오늘의 나다.", "author": "미상"},
        {"text": "행복은 습관이다. 그것을 몸에 익혀라.", "author": "허버드"},
        {"text": "시작하는 방법은 그만 말하고 이제 행동하는 것이다.", "author": "월트 디즈니"},
        {"text": "문제는 목적지에 얼마나 빨리 가느냐가 아니라, 그 목적지가 어디냐는 것이다.", "author": "에이브러햄 링컨"},
        {"text": "당신이 할 수 있다고 믿든 할 수 없다고 믿든, 당신이 믿는 대로 될 것이다.", "author": "헨리 포드"},
        {"text": "오늘 당신이 하는 일이 당신의 미래를 만든다.", "author": "간디"},
        {"text": "실패는 성공을 맛내기 위해 곁들이는 양념이다.", "author": "트루먼 카포티"},
        {"text": "길을 찾을 수 없다면, 만들어라.", "author": "필립 시드니"},
        {"text": "인생은 속도가 아니라 방향이다.", "author": "괴테"},
        {"text": "작은 기회로부터 종종 위대한 업적이 시작된다.", "author": "데모스테네스"},
        {"text": "지옥을 걷고 있다면, 계속해서 걸어가라.", "author": "윈스턴 처칠"},
        {"text": "미래를 예측하는 가장 좋은 방법은 미래를 창조하는 것이다.", "author": "피터 드러커"},
        {"text": "너무 소심하고 까다롭게 살지 마라. 인생은 모두 실험이다.", "author": "랄프 왈도 에머슨"},
        {"text": "꿈을 기록하는 것이 나의 목표였던 적은 없다. 꿈을 실현하는 것이 나의 목표다.", "author": "만 레이"},
        {"text": "고난은 인간의 진정한 가치를 시험하는 기회다.", "author": "에픽테토스"},
        {"text": "단번에 바다를 만들려고 하지 마라. 작은 시냇물부터 시작하라.", "author": "미상"},
        {"text": "성공이 끝은 아니다. 실패가 치명적인 것도 아니다. 중요한 것은 계속하려는 용기다.", "author": "윈스턴 처칠"},
        {"text": "할 수 있다고 생각하면 할 수 있고, 할 수 없다고 생각하면 할 수 없다.", "author": "최선을 다하는 당신"},
        {"text": "오늘의 고통은 내일의 힘이 된다.", "author": "미상"},
        {"text": "휴식은 게으름이 아니다. 때때로 풀밭에 누워 물소리를 듣는 것은 필수다.", "author": "존 러벅"}
    ]
    return random.choice(quotes)

@app.route('/')
def index():
    query = request.args.get('query', '').strip()
    results = []
    error_msg = None
    weather_data = get_naver_weather()
    quote = get_random_quote()
    
   #날씨 기반 메뉴 추천
    recommended_menu = "비빔밥" # 기본값
    if weather_data:
        recommended_menu = get_recommended_menu(weather_data['status'])

    if query:
        # 데이터 저장 시도
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO search_logs (keyword) VALUES (?)", (query,))
            conn.commit()
            conn.close()
            print(f"[저장성공] 검색어: {query}")
        except Exception as e:
            print(f"[저장실패] {e}")
            error_msg = f"데이터베이스 저장 오류: {e}"

        # 네이버 API 호출
        url = f"https://openapi.naver.com/v1/search/blog.json?query={query}&display=10"
        headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
        
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                results = resp.json().get('items', [])
            else:
                error_msg = f"API 오류: {resp.status_code}"
        except Exception as e:
            error_msg = f"연결 오류: {e}"

    return render_template('index.html', results=results, query=query, error_msg=error_msg, weather=weather_data, menu=recommended_menu, quote=quote)

@app.route('/rank')
def rank():
    rankings = []
    try:
        conn = get_db_connection()
        # 검색량 기준 내림차순 정렬
        cur = conn.execute("""
            SELECT keyword, COUNT(*) as cnt 
            FROM search_logs 
            GROUP BY keyword 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        rankings = cur.fetchall()
        conn.close()
    except Exception as e:
        print(f"[조회실패] {e}")
    
    return render_template('rank.html', rankings=rankings)

@app.route('/rank/chart')
def rank_chart():
    rankings = []
    try:
        conn = get_db_connection()
        cur = conn.execute("""
            SELECT keyword, COUNT(*) as cnt 
            FROM search_logs 
            GROUP BY keyword 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        rankings = cur.fetchall()
        conn.close()
        
        processed_data = []
        if rankings:
            max_val = rankings[0]['cnt']
            # 순위별 색상 지정 (1위: 금색, 2위: 은색, 3위: 동색, 나머지는 초록 계열)
            colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#32CD32', '#228B22', 
                      '#008000', '#006400', '#2E8B57', '#3CB371', '#66CDAA']
            
            for i, row in enumerate(rankings):
                width_percent = (row['cnt'] / max_val) * 100
                processed_data.append({
                    'keyword': row['keyword'],
                    'cnt': row['cnt'],
                    'width': width_percent,
                    'color': colors[i] if i < len(colors) else '#03C75A' # 색상 할당
                })
    except Exception as e:
        print(f"조회 실패: {e}")
        processed_data = []
    
    return render_template('rank_chart.html', rankings=processed_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)