import { getAuth, signInWithCustomToken } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-auth.js";
import { auth } from "/static/firebase_config.js";

function login() {
    let studentId = document.getElementById("studentId").value.trim();

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error("❌ 서버 응답 오류:", data.error);
            alert(data.error);  // 사용자에게 오류 표시
        } else if (data.token) {
            signInWithCustomToken(auth, data.token)
                .then(() => {
                    console.log("✅ 로그인 성공:", studentId);
                    window.location.href = data.redirect;  // 서버에서 받은 리디렉션 경로 사용
                })
                .catch(error => {
                    console.error("🔥 Firebase 로그인 실패:", error.message);
                });
        } else {
            console.error("❌ 알 수 없는 서버 응답:", data);
        }
    })
    .catch(error => {
        console.error("❌ 요청 실패:", error);
    });
}

window.login = login;
