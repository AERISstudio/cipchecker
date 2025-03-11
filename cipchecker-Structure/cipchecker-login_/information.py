import firebase_admin
from firebase_admin import auth, credentials
import time
import csv
import sys

service_account_file = "dshs-cip-firebase-adminsdk-fbsvc-b3d332a6aa.json"


cred = credentials.Certificate(service_account_file)
firebase_admin.initialize_app(cred)

def delete_all_users():
    page = auth.list_users()
    while page:
        for user in page.users:
            try:
                auth.delete_user(user.uid)
                print(f"계정 삭제 완료: {user.uid}")
            except Exception as e:
                print(f"계정 삭제 실패 ({user.uid}): {e}")
        page = page.get_next_page()

def create_student_accounts():
    users_data = []

    for class_num in range(1, 11): 
        for student_num in range(1, 37):  
            student_id = f"24_1{class_num:02}{student_num:02}"  # 학번
            email = f"{student_id}@dshs.kr"  # 이메일 형태 변환
            password = "123456" 

            try:
                user = auth.create_user(
                    uid=student_id,  
                    email=email,  
                    password=password,  
                )
                print(f"계정 생성 완료: {student_id} (Email: {email})")
                users_data.append([student_id, email, password])  # 계정 정보 저장
            except Exception as e:
                print(f"계정 생성 실패 ({student_id}): {e}")

            time.sleep(0.1)

    # CSV 파일로 저장
    with open("student_accounts.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["학번", "이메일", "초기 비밀번호"])
        writer.writerows(users_data)

    print("CSV 파일 저장 완료: student_accounts.csv")

delete_all_users()

create_student_accounts()
