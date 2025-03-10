import { auth } from "/static/firebase_config.js";
import { signInWithCustomToken } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-auth.js";

function login() {
    let studentId = document.getElementById("studentId").value.trim();

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            signInWithCustomToken(auth, data.token)
                .then(() => {
                    console.log("✅ 로그인 성공:", studentId);
                    window.location.href = data.redirect; // 🔥 Flask에서 반환한 경로로 이동
                })
                .catch(error => {
                    console.error("❌ Firebase 로그인 실패:", error.message);
                });
        } else {
            console.error("❌ 서버 응답 오류:", data.error);
        }
    })
    .catch(error => console.error("❌ 요청 중 오류 발생:", error));
}

window.login = login; // ✅ HTML에서 호출할 수 있도록 설정
