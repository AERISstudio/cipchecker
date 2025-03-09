import { getAuth, signInWithCustomToken } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-auth.js";
import { auth } from "../static/firebase_config.js";

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
                    console.log(" 로그인 성공:", studentId);
                    window.location.href = "/selection";
                })
                .catch(error => {
                    console.error(" Firebase 로그인 실패:", error.message);
                });
        } else {
            console.error(" 서버 응답 오류:", data.error);
        }
    });
}

window.login = login;
