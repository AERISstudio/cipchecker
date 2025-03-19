from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, get_flashed_messages
import firebase_admin
from firebase_admin import credentials, auth, db
import pandas as pd
from flask_session import Session
import os
from datetime import timedelta, datetime
import openpyxl
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ✅ Flask 세션 설정 (3시간 유지)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=3)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "Fl@skS3cr3t#2025!")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
Session(app)

# 🔥 Firebase 초기화 (Realtime Database 포함)
cred = credentials.Certificate("dshs-cip-firebase-adminsdk-fbsvc-d04e1b4bf0.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://dshs-cip-default-rtdb.firebaseio.com/"})

# 🔥 APScheduler 설정
scheduler = BackgroundScheduler()

def delete_old_data():
    try:
        db.reference('login_times').delete()
        rooms_ref = db.reference('rooms')
        rooms_snapshot = rooms_ref.get()
        if rooms_snapshot:
            for room_id in rooms_snapshot:
                rooms_ref.child(room_id).child('current_count').delete()
        print("✅ 12시간마다 데이터 삭제 완료")
    except Exception as e:
        print(f"❌ 데이터 삭제 오류: {e}")

# 12시간마다 delete_old_data 함수 실행
scheduler.add_job(delete_old_data, 'interval', hours=12)
scheduler.start()

# ✅ 로그인 페이지
@app.route("/", methods=["GET"])
def login_page():
    return render_template("login.html")

# ✅ 로그인 처리
@app.route("/login", methods=["POST"])
def student_login():
    try:
        data = request.json
        if not data or "student_id" not in data:
            flash("❌ 학번을 입력하세요!", "error")
            return redirect(url_for("login_page"))

        student_id = data.get("student_id", "").strip()

        if not student_id.isdigit() or len(student_id) not in [5, 7]:
            flash("❌ 유효한 학번을 입력하세요!", "error")
            return redirect(url_for("login_page"))

        # 🔥 로그인 시각 확인
        ref = db.reference(f"login_times/{student_id}")
        last_login_time = ref.get()
        current_time = datetime.now()

        if last_login_time:
            last_login_time = datetime.strptime(last_login_time, "%Y-%m-%d %H:%M:%S")
            time_diff = current_time - last_login_time
            if time_diff.total_seconds() < 12 * 3600:
                flash("이미 기록되었습니다. 수정이 필요할시 담당선생님께 찾아가세요", "error")
                return redirect(url_for("login_page"))

        try:
            user = auth.get_user(student_id)
        except:
            user = auth.create_user(uid=student_id)

        custom_token = auth.create_custom_token(student_id)
        session["student_id"] = student_id

        # 🔥 로그인 시각 저장
        ref.set(current_time.strftime("%Y-%m-%d %H:%M:%S"))

        return jsonify({"token": custom_token.decode("utf-8"), "redirect": url_for("select")}), 200

    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        flash(f"서버 오류 발생: {str(e)}", "error")
        return redirect(url_for("login_page"))

# ✅ 공간 선택 페이지
@app.route("/select")
def select():
    if "student_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("select.html")

@app.route("/PerformenceRoom/performenceselect", methods=["GET"])
def performenceselect_page():
    return render_template("PerformenceRoom/performenceselect.html")

@app.route("/PerformenceRoom/performence1", methods=["GET"])
def performence1_page():
    return render_template("PerformenceRoom/performence1.html")

@app.route("/PerformenceRoom/performence2", methods=["GET"])
def performence2_page():
    return render_template("PerformenceRoom/performence2.html")

@app.route("/academy")
def academy():
    return render_template("academy.html")

@app.route("/ActivityRoom/activityselect", methods=["GET"])
def activityselect_page():
    return render_template("ActivityRoom/activityselect.html")

@app.route("/ActivityRoom/activity1", methods=["GET"])
def activity1_page():
    return render_template("ActivityRoom/activity1.html")

@app.route("/ActivityRoom/activity2", methods=["GET"])
def activity2_page():
    return render_template("ActivityRoom/activity2.html")

@app.route("/ActivityRoom/activity3", methods=["GET"])
def activity3_page():
    return render_template("ActivityRoom/activity3.html")

@app.route("/StudyRoom/studyselect", methods=["GET"])
def studyselect_page():
    return render_template("StudyRoom/studyselect.html")

@app.route("/StudyRoom/study1", methods=["GET"])
def study1_page():
    return render_template("StudyRoom/study1.html")

@app.route("/StudyRoom/study2", methods=["GET"])
def study2_page():
    return render_template("StudyRoom/study2.html")

@app.route("/StudyRoom/study3", methods=["GET"])
def study3_page():
    return render_template("StudyRoom/study3.html")

@app.route("/StudyRoom/study4", methods=["GET"])
def study4_page():
    return render_template("StudyRoom/study4.html")

@app.route("/StudyRoom/study5", methods=["GET"])
def study5_page():
    return render_template("StudyRoom/study5.html")

# ✅ 자습실1 선택 시 Firebase 및 엑셀 업데이트
@app.route("/update_select", methods=["POST"])
def update_select():
    try:
        if "student_id" not in session:
            return jsonify({"error": "❌ 로그인 후 이용하세요!"}), 403

        student_id = session["student_id"]
        class_num = student_id[1:3]  # 예: 21008 → "10"반
        file_name = f"{class_num}반.xlsx"  # 이미 만들어진 파일이어야 함

        # 학번.csv 파일에서 이름 가져오기
        name_file = "학번.csv"
        if not os.path.exists(name_file):
            return jsonify({"error": "❌ 이름 파일이 없습니다."}), 500

        name_df = pd.read_csv(name_file)
        if "학번" not in name_df.columns or "이름" not in name_df.columns:
            return jsonify({"error": "❌ CSV 파일에 '학번' 또는 '이름' 열이 없습니다."}), 500

        student_name = name_df.loc[name_df["학번"] == int(student_id), "이름"].values[0]

        data = request.get_json()
        if not data:
            return jsonify({"error": "❌ 전송된 JSON 데이터가 없습니다."}), 400

        # selected_room 값 처리
        selected_room = data.get("selected_room")
        if selected_room is None or str(selected_room).strip() == "":
            return jsonify({"error": "❌ 방이 선택되지 않았습니다."}), 400
        selected_room = str(selected_room).strip()

        cip2 = data.get("cip2", "자습")
        cip3 = data.get("cip3", "자습")
    
        # [1] 기존 반별 엑셀 파일 업데이트 (미리 만들어진 파일이어야 함)
        if not os.path.exists(file_name):
            return jsonify({"error": f"❌ {file_name} 파일이 존재하지 않습니다."}), 400

        try:
            df = pd.read_excel(file_name, engine="openpyxl")
        except Exception as e:
            print(f"❌ 엑셀 파일 로드 오류: {e}")
            return jsonify({"error": "엑셀 파일을 불러오는 중 오류 발생"}), 500

        df["학번"] = df["학번"].astype(str).fillna("")
        if student_id not in df["학번"].values:
            new_data = pd.DataFrame([[student_id, student_name, cip2, cip3]],
                                    columns=["학번", "이름", "CIP2", "CIP3"])
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            df.loc[df["학번"] == student_id, ["이름", "CIP2", "CIP3"]] = [student_name, cip2, cip3]

        try:
            df["학번_번호"] = df["학번"].str[-2:].astype(int, errors="ignore")
            df = df.sort_values(by="학번_번호").drop(columns=["학번_번호"])
        except Exception as e:
            print(f"⚠️ 학번 정렬 오류 발생: {e}")

        df.to_excel(file_name, index=False, engine="openpyxl")
    
        # [2] 선택된 방에 해당하는 엑셀 파일 업데이트 (미리 만들어진 파일 사용)
        room_file_name = f"{selected_room}.xlsx"
        # 만약 파일이 없다면 자동으로 빈 파일을 생성
        if not os.path.exists(room_file_name):
            room_df = pd.DataFrame(columns=["학번", "이름", "CIP2", "CIP3"])
            room_df.to_excel(room_file_name, index=False, engine="openpyxl")
    
        try:
            room_df = pd.read_excel(room_file_name, engine="openpyxl")
        except Exception as e:
            print(f"❌ 방별 엑셀 파일 로드 오류: {e}")
            return jsonify({"error": "방별 엑셀 파일을 불러오는 중 오류 발생"}), 500

        room_df["학번"] = room_df["학번"].astype(str).fillna("")
        if student_id not in room_df["학번"].values:
            new_room_data = pd.DataFrame([[student_id, student_name, cip2, cip3]],
                                         columns=["학번", "이름", "CIP2", "CIP3"])
            room_df = pd.concat([room_df, new_room_data], ignore_index=True)
        else:
            room_df.loc[room_df["학번"] == student_id, ["이름", "CIP2", "CIP3"]] = [student_name, cip2, cip3]

        room_df.to_excel(room_file_name, index=False, engine="openpyxl")
    
        return jsonify({"message": "✅ 자습실 선택이 저장되었습니다."}), 200

    except Exception as e:
        print(f"❌ 서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {str(e)}"}), 500

# ✅ 학원 자습 선택 시 엑셀 업데이트
@app.route("/save_to_excel", methods=["POST"])
def save_to_excel():
    try:
        if "student_id" not in session:
            return jsonify({"error": "❌ 로그인 후 이용하세요!"}), 403

        student_id = session["student_id"]
        class_num = student_id[1:3]  # 🔥 학번에서 반 번호 추출 (예: 21008 → "10"반)
        file_name = f"{class_num}반.xlsx"

        # 학번.csv 파일에서 이름 가져오기
        name_file = "학번.csv"
        if not os.path.exists(name_file):
            return jsonify({"error": "❌ 이름 파일이 없습니다."}), 500

        name_df = pd.read_csv(name_file)
        if "학번" not in name_df.columns or "이름" not in name_df.columns:
            return jsonify({"error": "❌ CSV 파일에 '학번' 또는 '이름' 열이 없습니다."}), 500

        student_name = name_df.loc[name_df["학번"] == int(student_id), "이름"].values[0]

        # ✅ 엑셀 파일 존재 확인 및 생성
        if not os.path.exists(file_name):
            df = pd.DataFrame(columns=["학번", "이름", "CIP2", "CIP3"])
            df.to_excel(file_name, index=False, engine="openpyxl")

        # ✅ 엑셀 파일 읽기 (오류 대비)
        try:
            df = pd.read_excel(file_name, engine="openpyxl")
        except Exception as e:
            print(f"❌ 엑셀 파일 로드 오류: {e}")
            return jsonify({"error": "엑셀 파일을 불러오는 중 오류 발생"}), 500

        # ✅ 학번이 없으면 추가, 있으면 수정
        df["학번"] = df["학번"].astype(str).fillna("")
        if student_id not in df["학번"].values:
            new_data = pd.DataFrame([[student_id, student_name, "학원 자습", "학원 자습"]], columns=["학번", "이름", "CIP2", "CIP3"])
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            df.loc[df["학번"] == student_id, ["이름", "CIP2", "CIP3"]] = [student_name, "학원 자습", "학원 자습"]

        # ✅ 학번 정렬 (마지막 두 자리 기준, 예외 처리 포함)
        try:
            df["학번_번호"] = df["학번"].str[-2:].astype(int, errors="ignore")
            df = df.sort_values(by="학번_번호").drop(columns=(["학번_번호"]))
        except Exception as e:
            print(f"⚠️ 학번 정렬 오류 발생: {e}")

        # ✅ 엑셀 저장
        df.to_excel(file_name, index=False, engine="openpyxl")

        return jsonify({"message": "✅ 학원 자습 선택이 저장되었습니다."}), 200

    except Exception as e:
        print(f"❌ 서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {str(e)}"}), 500

# ✅ 출력 페이지 (버튼 클릭 시 이동)
@app.route("/admin_print")
def admin_print():
    return render_template("admin_print.html")

@app.route("/get_excel_data")
def get_excel_data():
    try:
        class_num = request.args.get("class")
        formatted_class_num = f"{int(class_num):02d}"
        file_name = f"{formatted_class_num}반.xlsx"
        if not os.path.exists(file_name):
            return jsonify({"error": f"{class_num}반 엑셀 파일이 없습니다."})
        df = pd.read_excel(file_name, engine="openpyxl")
        return jsonify(df.to_dict(orient="records"))
    
    except Exception as e:
        print(f"❌ 엑셀 데이터 로드 오류: {e}")
        return jsonify({"error": "엑셀 데이터 로드 중 오류 발생"}), 500

@app.route("/get_room_data")
def get_room_data():
    try:
        room = request.args.get("room")
        if not room:
            return jsonify({"error": "❌ 방 이름을 제공해주세요."}), 400
        
        room_file_name = f"{room}.xlsx"
        if not os.path.exists(room_file_name):
            return jsonify({"error": f"❌ {room} 엑셀 파일이 존재하지 않습니다."}), 400
        
        df = pd.read_excel(room_file_name, engine="openpyxl")
        return jsonify(df.to_dict(orient="records"))
    
    except Exception as e:
        print(f"❌ 방 데이터 로드 오류: {e}")
        return jsonify({"error": "방 데이터 로드 중 오류 발생"}), 500

if __name__ == "__main__":  
    app.run(host='0.0.0.0', port=5000)