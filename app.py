from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, auth, db
import pandas as pd
import os
from datetime import timedelta

app = Flask(__name__)

# ✅ Flask 세션 설정 (3시간 유지)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=3)
app.secret_key = os.urandom(24)  # 🔥 랜덤 보안 키 자동 생성

# 🔥 Firebase 초기화 (Realtime Database 포함)
cred = credentials.Certificate("dshs-cip-firebase-adminsdk-fbsvc-62090c1d93.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://dshs-cip-default-rtdb.firebaseio.com/"})

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
            return jsonify({"error": "❌ 학번을 입력하세요!"}), 400

        student_id = data.get("student_id", "").strip()

        if not student_id.isdigit() or len(student_id) not in [5, 7]:
            return jsonify({"error": "❌ 유효한 학번을 입력하세요!"}), 400

        try:
            user = auth.get_user(student_id)
        except:
            user = auth.create_user(uid=student_id)

        custom_token = auth.create_custom_token(student_id)
        session["student_id"] = student_id
        return jsonify({"token": custom_token.decode("utf-8"), "redirect": url_for("select")}), 200

    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return jsonify({"error": f"서버 오류 발생: {str(e)}"}), 500

# ✅ 공간 선택 페이지
@app.route("/select")
def select():
    if "student_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("select.html")

@app.route("/studyselect", methods=["GET"])
def studyselect_page():
    return render_template("studyselect.html")

@app.route("/study1", methods=["GET"])
def study1_page():
    return render_template("study1.html")

@app.route("/study2", methods=["GET"])
def study2_page():
    return render_template("study2.html")

@app.route("/study3", methods=["GET"])
def study3_page():
    return render_template("study3.html")

# ✅ 자습실1 선택 시 Firebase 및 엑셀 업데이트
@app.route("/update_select", methods=["POST"])
def update_select():
    try:
        if "student_id" not in session:
            return jsonify({"error": "❌ 로그인 후 이용하세요!"}), 403

        student_id = session["student_id"]
        class_num = student_id[1:3]  # 🔥 학번에서 반 번호 추출 (예: 21008 → "10"반)
        file_name = f"{class_num}반.xlsx"

        data = request.get_json()
        if not data:
            return jsonify({"error": "❌ 전송된 JSON 데이터가 없습니다."}), 400

        selected_room = data.get("selected_room")
        cip1 = data.get("cip1", "자습")
        cip2 = data.get("cip2", "자습")
        cip3 = data.get("cip3", "자습")

        # ✅ 자습실1 선택 시 Firebase 인원 증가
        if selected_room == "자습실1":
            try:
                room_ref = db.reference("rooms/자습실/자습실1")
                room_data = room_ref.get()

                # 🔥 데이터가 존재하지 않을 경우 기본 값 추가
                if room_data is None:
                    print("⚠️ Firebase에 자습실1 데이터가 없음! 초기화 진행...")
                    room_data = {"max_capacity": 30, "current_capacity": 0}
                    room_ref.set(room_data)

                current_capacity = room_data.get("current_capacity", 0)
                max_capacity = room_data.get("max_capacity", 0)

                if current_capacity >= max_capacity:
                    return jsonify({"error": "⚠️ 자습실1이(가) 이미 가득 찼습니다!"})

                # ✅ 현재 인원을 1 증가
                room_ref.update({"current_capacity": current_capacity + 1})
                
            except Exception as e:
                print(f"❌ Firebase 업데이트 오류: {e}")
                return jsonify({"error": "Firebase 업데이트 중 오류 발생"}), 500
            
        if selected_room == "자습실2":
            try:
                room_ref = db.reference("rooms/자습실/자습실2")
                room_data = room_ref.get()

                # 🔥 데이터가 존재하지 않을 경우 기본 값 추가
                if room_data is None:
                    print("⚠️ Firebase에 자습실2 데이터가 없음! 초기화 진행...")
                    room_data = {"max_capacity": 30, "current_capacity": 0}
                    room_ref.set(room_data)

                current_capacity = room_data.get("current_capacity", 0)
                max_capacity = room_data.get("max_capacity", 0)

                if current_capacity >= max_capacity:
                    return jsonify({"error": "⚠️ 자습실2이(가) 이미 가득 찼습니다!"})

                # ✅ 현재 인원을 1 증가
                room_ref.update({"current_capacity": current_capacity + 1})
                
            except Exception as e:
                print(f"❌ Firebase 업데이트 오류: {e}")
                return jsonify({"error": "Firebase 업데이트 중 오류 발생"}), 500
            
        # ✅ 자습실3 선택 시 Firebase 인원 증가
        if selected_room == "자습실3":
            try:
                room_ref = db.reference("rooms/자습실/자습실3")
                room_data = room_ref.get()

                # 🔥 데이터가 존재하지 않을 경우 기본 값 추가
                if room_data is None:
                    print("⚠️ Firebase에 자습실3 데이터가 없음! 초기화 진행...")
                    room_data = {"max_capacity": 30, "current_capacity": 0}
                    room_ref.set(room_data)

                current_capacity = room_data.get("current_capacity", 0)
                max_capacity = room_data.get("max_capacity", 0)

                if current_capacity >= max_capacity:
                    return jsonify({"error": "⚠️ 자습실3이(가) 이미 가득 찼습니다!"})

                # ✅ 현재 인원을 1 증가
                room_ref.update({"current_capacity": current_capacity + 1})
                
            except Exception as e:
                print(f"❌ Firebase 업데이트 오류: {e}")
                return jsonify({"error": "Firebase 업데이트 중 오류 발생"}), 500
            
        # ✅ 엑셀 파일 존재 확인 및 생성
        if not os.path.exists(file_name):
            df = pd.DataFrame(columns=["학번", "CIP2", "CIP3"])
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
            new_data = pd.DataFrame([[student_id, "자습실", cip2, cip3]], columns=["학번", "CIP2", "CIP3"])
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            df.loc[df["학번"] == student_id, ["CIP2", "CIP3"]] = ["자습실", cip2, cip3]

        # ✅ 학번 정렬 (마지막 두 자리 기준, 예외 처리 포함)
        try:
            df["학번_번호"] = df["학번"].str[-2:].astype(int, errors="ignore")
            df = df.sort_values(by="학번_번호").drop(columns=["학번_번호"])
        except Exception as e:
            print(f"⚠️ 학번 정렬 오류 발생: {e}")

        # ✅ 엑셀 저장
        df.to_excel(file_name, index=False, engine="openpyxl")

        return jsonify({"message": "✅ 자습실1 선택이 저장되었습니다."}), 200

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

if __name__ == "__main__":
    app.run(debug=True)
