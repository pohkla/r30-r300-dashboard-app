# R30 / R300 Dashboard — Render + GitHub JSON

เวอร์ชันออนไลน์ฟรีในรูปแบบเดียวกับ Vehicle Dashboard

- `/dashboard` หน้า Dashboard สาธารณะ
- `/login` หน้าเข้าสู่ระบบผู้ดูแล
- `/admin` หน้าจัดการ เพิ่ม และแก้ไขแผน
- GitHub JSON เป็นแหล่งจัดเก็บข้อมูลถาวร
- Render Free เป็น Web Service สำหรับรัน FastAPI

## โครงสร้าง

```text
main.py                 FastAPI, Login, GitHub API และการคำนวณ
templates/              Dashboard, Login และฟอร์มแผน
static/style.css        ธีมของระบบ
data/trades.json        ข้อมูลเริ่มต้น 11 แผน/ใช้ทดสอบ Local
requirements.txt        Python dependencies
render.yaml             Blueprint สำหรับ Render
.env.example            ตัวอย่าง Environment Variables
```

## 1. เตรียม GitHub Repository เก็บข้อมูล

สร้าง Repository เช่น `r30-r300-dashboard-data` แล้วสร้างไฟล์:

```text
data/trades.json
```

ให้นำไฟล์ `data/trades.json` จากแพ็กเกจนี้ไปใส่ เพื่อรักษาข้อมูล 11 แผนเดิม

สร้าง Fine-grained Personal Access Token โดยให้สิทธิ์เฉพาะ Repository นี้:

- Repository permissions → Contents → Read and write
- ไม่ต้องเปิดสิทธิ์อื่น

## 2. เตรียม GitHub Repository สำหรับตัวระบบ

สร้าง Repository อีกตัว เช่น `r30-r300-dashboard-app` แล้วอัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้ โดยไม่อัปโหลดไฟล์ `.env`

## 3. Deploy บน Render Free

1. Login Render และเชื่อมบัญชี GitHub
2. เลือก **New → Blueprint** แล้วเลือก Repository ของตัวระบบ
3. Render จะอ่าน `render.yaml`
4. เลือก Plan: **Free**
5. ตั้งค่า Secret Environment Variables:

| Key | ค่า |
|---|---|
| `ADMIN_PASSWORD` | รหัสผ่านหน้า Admin ที่ตั้งเอง |
| `GITHUB_TOKEN` | Fine-grained Token |
| `GITHUB_REPO` | `username/r30-r300-dashboard-data` |

ค่าที่เตรียมให้อัตโนมัติใน `render.yaml`:

- `SESSION_SECRET` สุ่มโดย Render
- `GITHUB_FILE=data/trades.json`
- `GITHUB_BRANCH=main`
- `COOKIE_SECURE=true`

## 4. URL หลัง Deploy

```text
https://ชื่อ-service.onrender.com/dashboard
https://ชื่อ-service.onrender.com/login
https://ชื่อ-service.onrender.com/admin
```

## ทดสอบในเครื่อง

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
set COOKIE_SECURE=false
set ADMIN_PASSWORD=รหัสผ่านทดสอบ
uvicorn main:app --reload
```

เปิด `http://127.0.0.1:8000/dashboard`

ทดสอบระบบแบบอัตโนมัติ:

```bash
python tests/smoke_test.py
```

หากไม่ตั้งค่า GitHub ระบบจะอ่านและเขียน `data/trades.json` ในเครื่องเพื่อการทดสอบเท่านั้น

## หมายเหตุ Render Free

- เมื่อไม่มีผู้เข้าใช้งานประมาณ 15 นาที Service จะพัก
- การเปิดครั้งแรกหลังพักอาจรอประมาณ 1 นาที
- ห้ามเก็บข้อมูลสำคัญใน filesystem ของ Render เพราะข้อมูลอาจหายเมื่อ Restart
- ระบบนี้จึงบันทึกข้อมูลจริงไว้ใน GitHub JSON
