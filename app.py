from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, auth, db
import pandas as pd
import os
import schedule
import time
import threading
from datetime import timedelta

app = Flask(__name__)

# ✅ Flask 세션 설정 (3시간 유지)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=3)
app.secret_key = os.urandom(24)  # 🔥 랜덤 보안 키 자동 생성

# 🔥 Firebase 초기화 (Realtime Database 포함)
cred = credentials.Certificate("dshs-cip-firebase-adminsdk-fbsvc-62090c1d93.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://dshs-cip-default-rtdb.firebaseio.com/"})

# ✅ 로그인 페이지
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()

        # ✅ 관리자 모드 (0000000 입력 시)
        if student_id == "0000000":
            return redirect(url_for("admin_dashboard"))

        if not student_id.isdigit() or len(student_id) not in [5, 7]:
            return "❌ 유효한 학번을 입력하세요!", 400

        # 🔥 Firebase에서 학번으로 사용자 확인 또는 생성
        try:
            user = auth.get_user(student_id)
        except:
            user = auth.create_user(uid=student_id)

        session["student_id"] = student_id
        session.permanent = True  # ✅ 세션 지속 모드 활성화
        print(f"✅ 세션 저장 완료: {session['student_id']}")

        return redirect(url_for("selection"))

    return render_template("login.html")

# ✅ 로그인 처리 (POST 요청)
@app.route("/login", methods=["POST"])
def student_login():
    try:
        data = request.json
        student_id = data.get("student_id", "").strip()

        # 🔥 학번 유효성 검사
        if not student_id.isdigit() or len(student_id) not in [5, 7]:
            return jsonify({"error": "❌ 유효한 학번을 입력하세요!"}), 400

        # 🔥 Firebase에서 사용자 확인 또는 생성
        try:
            user = auth.get_user(student_id)
        except:
            user = auth.create_user(uid=student_id)

        # 🔥 Firebase Custom Token 생성 및 세션 저장
        custom_token = auth.create_custom_token(student_id)
        session["student_id"] = student_id
        return jsonify({"token": custom_token.decode("utf-8"), "message": "✅ 로그인 성공"}), 200

    except Exception as e:
        print(f"❌ 로그인 중 서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {str(e)}"}), 500

# ✅ 공간 선택 페이지
@app.route("/selection")
def selection():
    if "student_id" not in session:
        return redirect(url_for("login"))
    return render_template("selection.html")

# ✅ 활동별 페이지 라우팅
@app.route("/study")
def study():
    return render_template("study.html") if "student_id" in session else redirect(url_for("login"))

@app.route("/activity")
def activity():
    return render_template("activity.html") if "student_id" in session else redirect(url_for("login"))

@app.route("/academy")
def academy():
    return render_template("academy.html") if "student_id" in session else redirect(url_for("login"))

# ✅ 관리자 대시보드 (10반 엑셀 조회)
@app.route("/admin_dashboard")
def admin_dashboard():
    if "student_id" not in session or session["student_id"] != "0000000":
        return "❌ 관리자 전용 페이지입니다!", 403

    excel_data = {}
    for class_num in range(1, 11):
        file_name = f"{class_num}반.xlsx"
        if os.path.exists(file_name):
            df = pd.read_excel(file_name, engine="openpyxl")
            excel_data[f"{class_num}반"] = df.to_dict(orient="records")
        else:
            excel_data[f"{class_num}반"] = "파일 없음"

    return render_template("admin_dashboard.html", excel_data=excel_data)

# ✅ 선택한 활동을 엑셀에 저장
@app.route("/update_excel", methods=["POST"])
def update_excel():
    try:
        if "student_id" not in session:
            return jsonify({"error": "❌ 로그인 후 이용하세요!"}), 403

        student_id = session["student_id"]
        class_num = student_id[1:3]  # 🔥 학번에서 반 번호 추출 (예: 21008 → "10"반)
        file_name = f"{class_num}반.xlsx"

        print(f"📂 엑셀 파일명: {file_name}")
        print(f"👤 학생 ID: {student_id}")

        # ✅ JSON 데이터 확인
        data = request.get_json()
        if not data:
            print("❌ JSON 데이터 없음!")
            return jsonify({"error": "❌ 전송된 JSON 데이터가 없습니다."}), 400

        print(f"✅ 받은 JSON 데이터: {data}")

        cip1, cip2, cip3 = "자습", "자습", "자습"

        if data.get("academy_selected", False):  
            cip2, cip3 = "학원", "학원"
        else:
            cip1 = data.get("cip1", "자습")
            cip2 = data.get("cip2", "자습")
            cip3 = data.get("cip3", "자습")

        # 🔥 엑셀 파일 존재 확인 및 생성
        if not os.path.exists(file_name):
            print(f"⚠️ {file_name} 파일 없음! 새로 생성 중...")
            df = pd.DataFrame(columns=["학번", "CIP1", "CIP2", "CIP3"])
            df.to_excel(file_name, index=False, engine="openpyxl")

        # 🔥 기존 엑셀 파일 로드
        try:
            df = pd.read_excel(file_name, engine="openpyxl")
        except Exception as e:
            print(f"❌ 엑셀 파일 로드 실패: {e}")
            return jsonify({"error": f"❌ 엑셀 파일 로드 오류: {str(e)}"}), 500

        # 🔥 학번 컬럼이 존재하는지 확인 후 변환
        if "학번" not in df.columns:
            print("⚠️ '학번' 컬럼 없음! 추가 중...")
            df["학번"] = ""

        df["학번"] = df["학번"].astype(str).fillna("")  # 🔥 NaN 값 제거 후 문자열 변환

        # 🔥 학번이 없으면 추가, 있으면 수정
        if student_id not in df["학번"].values:
            print(f"➕ 신규 학번 추가: {student_id}")
            new_data = pd.DataFrame([[student_id, cip1, cip2, cip3]], columns=["학번", "CIP1", "CIP2", "CIP3"])
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            print(f"🔄 기존 학번 수정: {student_id}")
            df.loc[df["학번"] == student_id, ["CIP1", "CIP2", "CIP3"]] = [cip1, cip2, cip3]

        # 🔥 학번 정렬 (마지막 두 자리 기준)
        try:
            df["학번_번호"] = df["학번"].str[-2:].astype(int)  # 🔥 학번 마지막 2자리 정수 변환
            df = df.sort_values(by="학번_번호").drop(columns=["학번_번호"])  # 🔥 정렬 후 임시 컬럼 삭제
        except Exception as e:
            print(f"⚠️ 학번 정렬 오류 발생: {e}")

        # 🔥 엑셀 저장
        df.to_excel(file_name, index=False, engine="openpyxl")
        print(f"✅ {file_name} 업데이트 완료!")

        return jsonify({"message": "✅ 선택이 저장되었습니다."}), 200

    except Exception as e:
        print(f"❌ 서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {str(e)}"}), 500


# 🔥 자동 초기화 (매일 12시)
schedule.every().day.at("00:00").do(lambda: print("🔄 데이터 초기화 실행!"))

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)
