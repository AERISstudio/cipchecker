import { auth } from "../firebase_config.js";
import { signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-auth.js";

function login() {
    let studentId = document.getElementById("studentId").value.trim();
    let password = document.getElementById("password").value.trim();

    let email = studentId;  

    console.log("🟢 변환된 이메일:", email);

    // Firebase 로그인 요청
    signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            console.log("로그인 성공:", userCredential.user);
            window.location.href = "../main.html";  
        })
        .catch((error) => {
            console.error("로그인 실패:", error.message);
            document.getElementById("error-message").innerText = "로그인 실패: " + error.message;
        });
}

window.login = login;
