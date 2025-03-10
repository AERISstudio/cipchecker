// ✅ Firebase SDK 모듈 가져오기
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-auth.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-database.js";

// ✅ Firebase 설정 정보
const firebaseConfig = {
    apiKey: "AIzaSyCno_36Bl-DqjEk12lmFranNylngoo8Sd8",
    authDomain: "dshs-cip.firebaseapp.com",
    projectId: "dshs-cip",
    storageBucket: "dshs-cip.firebasestorage.app",
    messagingSenderId: "1033758614768",
    appId: "1:1033758614768:web:6cc73592e6b9052fdfd4e35",
    measurementId: "G-V8X4BKESWM",
    databaseURL: "https://dshs-cip-default-rtdb.firebaseio.com/"
};

// ✅ Firebase 초기화
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

// ✅ export 추가
export { auth, database };
