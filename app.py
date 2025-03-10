from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, auth, db
import pandas as pd
import os
import threading
import schedule
import time
from datetime import timedelta

app = Flask(__name__)

# ✅ Flask 세션 설정 (3시간 유지)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=3)
app.secret_key = os.urandom(24)  # 🔥 랜덤 보안 키 자동 생성

# 🔥 Firebase 초기화 (Realtime Database 포함)
cred = credentials.Certificate("dshs-cip-firebase-adminsdk-fbsvc-62090c1d93.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://dshs-cip-default-rtdb.firebaseio.com/"})

# ✅ 로그인 페이지 (GET 요청)
@app.route("/", methods=["GET"])
def login_page():
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
        return jsonify({"token": custom_token.decode("utf-8"), "redirect": url_for("selection")}), 200

    except Exception as e:
        print(f"❌ 로그인 중 서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {str(e)}"}), 500

# ✅ 공간 선택 페이지
@app.route("/selection")
def selection():
    if "student_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("selection.html")

# ✅ 활동별 페이지 라우팅
@app.route("/study")
def study():
    return render_template("study.html") if "student_id" in session else redirect(url_for("login_page"))

@app.route("/activity")
def activity():
    return render_template("activity.html") if "student_id" in session else redirect(url_for("login_page"))

@app.route("/academy")
def academy():
    return render_template("academy.html") if "student_id" in session else redirect(url_for("login_page"))

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
            return jsonify({"error": "❌ 전송된 JSON 데이터가 없습니다."}), 400

        cip1, cip2, cip3 = "자습", "자습", "자습"

        if data.get("academy_selected", False):  
            cip2, cip3 = "학원", "학원"
        else:
            cip1 = data.get("cip1", "자습")
            cip2 = data.get("cip2", "자습")
            cip3 = data.get("cip3", "자습")

        # 🔥 엑셀 파일 존재 확인 및 생성
        if not os.path.exists(file_name):
            df = pd.DataFrame(columns=["학번", "CIP1", "CIP2", "CIP3"])
            df.to_excel(file_name, index=False, engine="openpyxl")

        # 🔥 기존 엑셀 파일 로드
        df = pd.read_excel(file_name, engine="openpyxl")
        
        # 🔥 학번이 없으면 추가, 있으면 수정
        df["학번"] = df["학번"].astype(str).fillna("")
        if student_id not in df["학번"].values:
            new_data = pd.DataFrame([[student_id, cip1, cip2, cip3]], columns=["학번", "CIP1", "CIP2", "CIP3"])
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            df.loc[df["학번"] == student_id, ["CIP1", "CIP2", "CIP3"]] = [cip1, cip2, cip3]

        # 🔥 학번 정렬 (마지막 두 자리 기준)
        df["학번_번호"] = df["학번"].str[-2:].astype(int)
        df = df.sort_values(by="학번_번호").drop(columns=["학번_번호"])

        # 🔥 엑셀 저장
        df.to_excel(file_name, index=False, engine="openpyxl")

        return jsonify({"message": "✅ 선택이 저장되었습니다."}), 200

    except Exception as e:
        print(f"❌ 서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {str(e)}"}), 500

# ✅ 출력 페이지 (버튼 클릭 시 이동)
@app.route("/admin_print")
def admin_print():
    return render_template("admin_print.html")

@app.route("/get_excel_data")
def get_excel_data():
    class_num = request.args.get("class")  # URL에서 class_num 가져오기
    formatted_class_num = f"{int(class_num):02d}"  # 🔥 앞에 0이 붙은 두 자리 숫자로 변환 (예: "1" → "01")

    file_name = f"{formatted_class_num}반.xlsx"  # 🔥 실제 저장된 파일명 형식 맞추기

    # 🔥 디버깅: 현재 폴더 내 파일 리스트 출력
    existing_files = os.listdir(".")
    print(f"📂 존재하는 엑셀 파일: {existing_files}")  

    # 🔥 해당 반의 엑셀 파일이 존재하는지 확인
    if file_name not in existing_files:
        print(f"❌ {file_name} 파일이 존재하지 않습니다!")
        return jsonify({"error": f"{class_num}반 엑셀 파일이 없습니다."})

    # 🔥 엑셀 파일 읽기
    try:
        df = pd.read_excel(file_name, engine="openpyxl")
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        print(f"❌ 엑셀 파일 로드 오류: {e}")
        return jsonify({"error": f"엑셀 파일을 불러오는 중 오류 발생: {str(e)}"})



if __name__ == "__main__":
    app.run(debug=True)
