const MODELS_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/';
let stream = null;
let detectionInterval = null;
let isModelsLoaded = false;

async function loadModels() {
    const msg = document.getElementById('status-msg');
    if(msg) msg.innerText = "Загрузка нейросети (подготовка моделей)...";
    
    try {
        await faceapi.nets.tinyFaceDetector.loadFromUri(MODELS_URL);
        await faceapi.nets.faceLandmark68Net.loadFromUri(MODELS_URL);
        await faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL);
        isModelsLoaded = true;
        if(msg) msg.innerText = "Нейросеть готова к работе.";
        document.querySelectorAll('button').forEach(b => b.disabled = false);
    } catch (e) {
        if(msg) {
            msg.innerText = "Ошибка загрузки ИИ. Проверьте интернет.";
            msg.style.color = "var(--danger)";
        }
        console.error(e);
    }
}

async function startCamera(mode) {
    if (!isModelsLoaded) return;
    
    document.getElementById('home-ui').style.display = 'none';
    document.getElementById('camera-ui').style.display = 'block';
    
    const isRegister = (mode === 'register');
    document.getElementById('register-controls').style.display = isRegister ? 'block' : 'none';
    document.getElementById('camera-title').innerText = isRegister ? 'Создание слепка лица' : 'Биометрический вход';
    
    const msg = document.getElementById('camera-msg');
    msg.innerText = "Включение камеры...";
    msg.style.color = "var(--text)";

    const video = document.getElementById('video');
    const overlay = document.getElementById('canvas-overlay');

    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
        video.srcObject = stream;
    } catch (err) {
        msg.innerText = "Ошибка доступа к камере.";
        msg.style.color = "var(--danger)";
        return;
    }

    video.onloadedmetadata = () => {
        overlay.width = video.videoWidth;
        overlay.height = video.videoHeight;
        if (!isRegister) {
            startLoginDetection(video, overlay, msg);
        }
    };
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }
    if (detectionInterval) {
        clearInterval(detectionInterval);
        detectionInterval = null;
    }
    document.getElementById('home-ui').style.display = 'block';
    document.getElementById('camera-ui').style.display = 'none';
}

async function captureAndRegister() {
    const username = document.getElementById('username').value.trim();
    const msg = document.getElementById('camera-msg');
    const btn = document.getElementById('reg-btn');

    if (!username) {
        msg.innerText = 'Введите ваше имя!';
        msg.style.color = "var(--danger)";
        return;
    }

    let db = getDB();
    if (db.users.find(u => u.username.toLowerCase() === username.toLowerCase())) {
        msg.innerText = 'Пользователь с таким именем уже существует!';
        msg.style.color = "var(--danger)";
        return;
    }

    msg.innerText = "Сканирование лица, смотрите в камеру...";
    msg.style.color = "var(--text)";
    btn.disabled = true;

    const video = document.getElementById('video');
    
    const detection = await faceapi.detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
                                   .withFaceLandmarks()
                                   .withFaceDescriptor();

    if (!detection) {
        msg.innerText = "Лицо не найдено. Пожалуйста, улучшите освещение.";
        msg.style.color = "var(--danger)";
        btn.disabled = false;
        return;
    }

    // Делаем скриншот для админа
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const photoUrl = canvas.toDataURL('image/jpeg', 0.8);

    db.users.push({
        username: username,
        descriptor: Array.from(detection.descriptor), // Float32Array to Array for JSON
        isApproved: false,
        isAdmin: false,
        lastActive: 0
    });
    db.pendingPhotos[username] = photoUrl;
    saveDB(db);

    msg.innerText = "✅ Заявка отправлена. Ожидайте одобрения администратором.";
    msg.style.color = "var(--success)";
    document.getElementById('register-controls').style.display = 'none';

    setTimeout(() => { stopCamera(); }, 3000);
}

function startLoginDetection(video, overlay, msg) {
    const db = getDB();
    const labeledDescriptors = [];
    
    db.users.forEach(u => {
        if (u.isApproved && u.descriptor && u.descriptor.length > 0) {
            labeledDescriptors.push(new faceapi.LabeledFaceDescriptors(
                u.username,
                [new Float32Array(u.descriptor)]
            ));
        }
    });

    if (labeledDescriptors.length === 0) {
        msg.innerText = "База лиц пуста или вам еще не одобрили доступ.";
        msg.style.color = "var(--danger)";
        return;
    }

    const faceMatcher = new faceapi.FaceMatcher(labeledDescriptors, 0.5); // 0.5 - порог строгости

    detectionInterval = setInterval(async () => {
        if (video.paused || video.ended) return;

        const detection = await faceapi.detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
                                       .withFaceLandmarks()
                                       .withFaceDescriptor();

        const dims = faceapi.matchDimensions(overlay, video, true);
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0, 0, overlay.width, overlay.height);

        if (detection) {
            const resized = faceapi.resizeResults(detection, dims);
            faceapi.draw.drawDetections(overlay, resized);

            const match = faceMatcher.findBestMatch(detection.descriptor);
            if (match.label !== 'unknown') {
                clearInterval(detectionInterval);
                ctx.clearRect(0, 0, overlay.width, overlay.height);
                msg.innerText = "✅ Доступ разрешен: " + match.label;
                msg.style.color = "var(--success)";
                
                setTimeout(() => {
                    setCurrentUser(match.label);
                    window.location.href = 'dashboard.html';
                }, 1500);
            } else {
                msg.innerText = "❌ Лицо не распознано в базе.";
                msg.style.color = "var(--danger)";
            }
        } else {
            msg.innerText = "Поиск лица...";
            msg.style.color = "var(--text)";
        }
    }, 500);
}

// Запускаем загрузку моделей, если мы на главной странице
if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname.indexOf('.html') === -1) {
    if (getCurrentUser()) {
        window.location.href = 'dashboard.html';
    } else {
        loadModels();
    }
}
