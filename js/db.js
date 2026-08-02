const DB_KEY = 'command_center_db';

// Инициализация локальной базы данных
function getDB() {
    let db = localStorage.getItem(DB_KEY);
    if (!db) {
        db = {
            users: [
                // Создаем админа по умолчанию
                { username: 'admin', descriptor: null, isApproved: true, isAdmin: true, lastActive: 0 }
            ],
            pendingPhotos: {}
        };
        saveDB(db);
    } else {
        db = JSON.parse(db);
    }
    return db;
}

function saveDB(db) {
    localStorage.setItem(DB_KEY, JSON.stringify(db));
}

// Текущий авторизованный пользователь
function getCurrentUser() {
    return localStorage.getItem('currentUser');
}

function setCurrentUser(username) {
    localStorage.setItem('currentUser', username);
}

function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}

// Пинг активности (чтобы быть "В сети")
function pingActivity() {
    const username = getCurrentUser();
    if (username) {
        let db = getDB();
        let user = db.users.find(u => u.username === username);
        if (user) {
            user.lastActive = Date.now();
            saveDB(db);
        } else {
            // Если пользователя удалили админы
            logout();
        }
    }
}
