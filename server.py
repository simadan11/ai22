from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, init_db, User
import face_module
import os
import shutil
import uuid
import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def index(request: Request, session_token: str = Cookie(None), db: Session = Depends(get_db)):
    user = None
    if session_token:
        user = db.query(User).filter(User.username == session_token).first()
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.post("/api/register")
async def register(username: str = Form(...), photo: UploadFile = File(...), db: Session = Depends(get_db)):
    if not username or not username.strip():
        return JSONResponse({"status": "error", "message": "Имя пользователя обязательно."})
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username, is_approved=False)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    if user.is_approved:
        return JSONResponse({"status": "error", "message": "Пользователь уже одобрен. Войдите через лицо."})

    img_bytes = await photo.read()
    face = face_module.get_face(img_bytes)
    if face is None:
         return JSONResponse({"status": "error", "message": "Лицо не найдено на фото. Попробуйте еще раз."})
    
    user_dir = os.path.join("data/faces/pending", username)
    os.makedirs(user_dir, exist_ok=True)
    
    # Save original photo for admin to review
    with open(os.path.join(user_dir, f"{uuid.uuid4().hex}.png"), "wb") as f:
        f.write(img_bytes)
        
    return JSONResponse({"status": "success", "message": "Заявка отправлена. Ожидайте одобрения администратором."})

@app.post("/api/login")
async def login(photo: UploadFile = File(...), db: Session = Depends(get_db)):
    img_bytes = await photo.read()
    username, conf = face_module.predict(img_bytes)
    
    if username:
        user = db.query(User).filter(User.username == username, User.is_approved == True).first()
        if user:
            response = JSONResponse({"status": "success", "username": username, "redirect": "/dashboard"})
            response.set_cookie(key="session_token", value=username)
            return response
            
    return JSONResponse({"status": "error", "message": "Лицо не распознано или нет доступа."})

@app.post("/api/logout")
def logout(response: JSONResponse):
    response = JSONResponse({"status": "success"})
    response.delete_cookie("session_token")
    return response

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, session_token: str = Cookie(None), db: Session = Depends(get_db)):
    if session_token != "admin":
        return templates.TemplateResponse("admin_login.html", {"request": request})
    
    pending_users = db.query(User).filter(User.is_approved == False).all()
    # Find photos for pending users
    pending_data = []
    for pu in pending_users:
        user_dir = os.path.join("data/faces/pending", pu.username)
        if os.path.exists(user_dir):
            photos = os.listdir(user_dir)
            if photos:
                 pending_data.append({"username": pu.username, "photo": f"/api/photo/pending/{pu.username}/{photos[0]}"})
                 
    return templates.TemplateResponse("admin.html", {"request": request, "pending_data": pending_data})

@app.post("/admin/login")
def admin_login_post(password: str = Form(...)):
    # simple hardcoded admin password for task simplicity
    if password == "admin":
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(key="session_token", value="admin")
        return response
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/approve")
def approve_user(username: str = Form(...), db: Session = Depends(get_db), session_token: str = Cookie(None)):
    if session_token != "admin":
        raise HTTPException(status_code=403)
        
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.is_approved = True
        db.commit()
        
        # move photos
        src_dir = os.path.join("data/faces/pending", username)
        dst_dir = os.path.join("data/faces/approved", username)
        if os.path.exists(src_dir):
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            shutil.rmtree(src_dir)
            
        # retrain model
        face_module.label_map = face_module.train_model() or {}
        
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/reject")
def reject_user(username: str = Form(...), db: Session = Depends(get_db), session_token: str = Cookie(None)):
    if session_token != "admin":
        raise HTTPException(status_code=403)
        
    user = db.query(User).filter(User.username == username).first()
    if user:
        db.delete(user)
        db.commit()
        
        src_dir = os.path.join("data/faces/pending", username)
        if os.path.exists(src_dir):
            shutil.rmtree(src_dir)
            
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/api/photo/{status}/{username}/{filename}")
def get_photo(status: str, username: str, filename: str):
    import mimetypes
    path = os.path.join("data/faces", status, username, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    with open(path, "rb") as f:
        return HTMLResponse(content=f.read(), media_type="image/png")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not session_token:
        return RedirectResponse(url="/")
        
    user = db.query(User).filter(User.username == session_token).first()
    if not user and session_token != "admin":
        return RedirectResponse(url="/")
        
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": session_token})

@app.post("/api/ping")
def ping(session_token: str = Cookie(None), db: Session = Depends(get_db)):
    if session_token:
        user = db.query(User).filter(User.username == session_token).first()
        if user:
            user.last_active = datetime.datetime.utcnow()
            db.commit()
    return {"status": "ok"}

@app.get("/api/users/active")
def get_active_users(session_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not session_token:
        raise HTTPException(status_code=403)
        
    users = db.query(User).filter(User.is_approved == True).all()
    now = datetime.datetime.utcnow()
    
    result = []
    for u in users:
        is_active = False
        if u.last_active and (now - u.last_active).total_seconds() < 10:
            is_active = True
        result.append({
            "username": u.username,
            "is_active": is_active,
            "is_admin": u.is_admin
        })
        
    return JSONResponse(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
