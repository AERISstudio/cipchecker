from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, auth, db
import pandas as pd
import os
import schedule
import time
import threading

app = Flask(__name__)
app.secret_key = "super_secret_key"

# 🔥 Firebase 초기화 (Realtime Database)
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
        return redirect(url_for("selection"))

    return render_template("login.html")

# ✅ 공간 선택 페이지
@app.route("/selection")
def selection():
    if "student_id" not in session:
        return redirect(url_for("login"))
    return render_template("selection.html")

# ✅ 활동별 페이지 라우팅
@app.route("/study")
def study():
    return render_template("study.html") if "student_id" in session else "❌ 로그인 후 이용하세요!", 403

@app.route("/activity")
def activity():
    return render_template("activity.html") if "student_id" in session else "❌ 로그인 후 이용하세요!", 403

@app.route("/academy")
def academy():
    return render_template("academy.html") if "student_id" in session else "❌ 로그인 후 이용하세요!", 403

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
    if "student_id" not in session:
        return jsonify({"error": "❌ 로그인 후 이용하세요!"}), 403

    student_id = session["student_id"]
    class_num = student_id[1]  # 학번에서 반 번호 추출
    file_name = f"{class_num}반.xlsx"

    if not request.is_json:
        return jsonify({"error": "❌ 요청 데이터가 JSON 형식이 아닙니다."}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "❌ 전송된 JSON 데이터가 비어 있습니다."}), 400

    # ✅ 기본값: 모든 CIP는 "자습"
    cip1, cip2, cip3 = "자습", "자습", "자습"

    # ✅ 학원이 선택된 경우 CIP2, CIP3을 학원으로 변경
    if data.get("academy_selected", False):  
        cip2, cip3 = "학원", "학원"
    else:
        # ✅ 기존 방식대로 1, 2, 3을 선택해서 변경 가능
        cip1 = data.get("cip1", "자습")
        cip2 = data.get("cip2", "자습")
        cip3 = data.get("cip3", "자습")

    # 🔥 엑셀 파일이 없으면 생성
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=["학번", "CIP1", "CIP2", "CIP3"])
        df.to_excel(file_name, index=False, engine="openpyxl")

    # 🔥 기존 엑셀 파일 로드
    df = pd.read_excel(file_name, engine="openpyxl")

    # 🔥 학번이 없으면 추가, 있으면 수정
    if student_id not in df["학번"].astype(str).values:
        new_data = pd.DataFrame([[student_id, cip1, cip2, cip3]], columns=["학번", "CIP1", "CIP2", "CIP3"])
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df.loc[df["학번"].astype(str) == student_id, ["CIP1", "CIP2", "CIP3"]] = [cip1, cip2, cip3]

    # 🔥 학번 정렬 (마지막 두 자리 기준)
    df["학번"] = df["학번"].astype(str)
    df = df.sort_values(by=df["학번"].str[-2:].astype(int))

    # 🔥 엑셀 저장
    df.to_excel(file_name, index=False, engine="openpyxl")

    return jsonify({"message": "✅ 선택이 저장되었습니다."}), 200

# ✅ 10반 엑셀 초기화 (매일 12시)
def reset_excel_data():
    for class_num in range(1, 11):
        file_name = f"{class_num}반.xlsx"
        if not os.path.exists(file_name):
            continue

        df = pd.read_excel(file_name, engine="openpyxl")

        if "CIP1" in df.columns and "CIP2" in df.columns and "CIP3" in df.columns:
            df["CIP1"] = "자습"
            df["CIP2"] = "자습"
            df["CIP3"] = "자습"
            df.to_excel(file_name, index=False, engine="openpyxl")
            print(f"✅ {file_name} 데이터 초기화 완료")

# ✅ Firebase 공간 인원 초기화 (매일 12시)
def reset_room_capacity():
    rooms_ref = db.reference("rooms")
    rooms_data = rooms_ref.get()

    if not rooms_data:
        return

    for room_type, rooms in rooms_data.items():
        for room_name in rooms.keys():
            rooms_ref.child(room_type).child(room_name).update({"current_capacity": 0})
    
    print("✅ 모든 방의 현재 인원 초기화 완료!")

# 🔥 매일 12시 자동 실행
schedule.every().day.at("00:00").do(reset_room_capacity)
schedule.every().day.at("00:00").do(reset_excel_data)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)
