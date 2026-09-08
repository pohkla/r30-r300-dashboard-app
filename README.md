# R300

R300 เป็น Project พัฒนา Expert Advisor `R300_EA` ด้วย MQL5 สำหรับ MetaTrader 5
Broker ปัจจุบันคือ XM และ Symbol ทองคือ `GOLD`
เวอร์ชัน 1.00 เป็น Skeleton แบบ **SIGNAL/BACKTEST SAFE MODE** เท่านั้น ยังไม่มีสัญญาณหรือกลยุทธ์
Trading Logic ทั้งหมดต้องกำหนดใน `docs/R300_SPEC.md` ก่อนพัฒนา

## Project structure

```text
R300/
├── src/
│   ├── R300_EA.mq5          # OnInit / OnDeinit / OnTick
│   ├── R300_Config.mqh      # Inputs, version, magic number, fixed Safe Mode
│   ├── R300_Trend.mqh       # H4 trend placeholder
│   ├── R300_Structure.mqh   # H1 BOS / CHOCH / swings placeholder
│   ├── R300_Setup.mqh       # M15 Volume Profile / RSI Divergence / Fibonacci
│   ├── R300_Entry.mqh       # M5 Break & Retest / Rejection / Engulfing
│   ├── R300_Risk.mqh        # Sizing / SL / maximum risk placeholder
│   └── R300_Exit.mqh        # TP / BE / trailing / structure / partial close
├── docs/
│   └── R300_SPEC.md
├── backtest/
│   └── .gitkeep
├── scripts/
│   └── deploy-mt5.ps1
├── README.md
└── .gitignore
```

## Architecture / Inputs

ทุกโมดูลเป็น interface ที่คืน `R300_NOT_IMPLEMENTED` ไม่มีการคำนวณหรือยืนยันเงื่อนไขใด ๆ
`OnTick()` ว่างโดยตั้งใจ ไม่เรียกโมดูลและไม่จัดการบัญชีหรือ Position
`InpMagicNumber = 300` ใช้เป็น metadata เท่านั้น
`InpExpectedSymbol = GOLD` ใช้แจ้งเตือนใน Log เมื่อ Symbol ต่างกัน ไม่ใช่กฎเทรด
`R300_SAFE_MODE = true` เป็นค่าคงที่ ไม่มี Input ที่เปิดการซื้อขายได้

## Compile ใน MetaEditor

1. เปิด MetaEditor ของ MT5 (กด F4 จาก MT5)
2. เลือก File > Open แล้วเปิด `D:\black\Project\R300\src\R300_EA.mq5`
3. ให้ไฟล์ `.mqh` ทั้ง 7 ไฟล์อยู่ในโฟลเดอร์เดียวกัน เพราะใช้ local includes
4. กด F7 และตรวจแท็บ Errors: ต้องได้ 0 errors และตรวจ warnings
5. ไฟล์ `R300_EA.ex5` จะอยู่ข้าง Source และถูก Git ignore

อ้างอิงรูปแบบ event handlers: [MQL5 Reference](https://www.mql5.com/en/docs/basis/function/events)

## Deploy ไป MT5 (เมื่อผู้ใช้สั่งให้ Deploy เท่านั้น)

เปิด PowerShell ที่ `D:\black\Project\R300` แล้วใช้:

```powershell
# ตรวจสอบและแสดงแผนโดยไม่ copy
.\scripts\deploy-mt5.ps1 -WhatIf

# Copy จริงเมื่อพร้อมและได้รับคำสั่ง Deploy
.\scripts\deploy-mt5.ps1
```

Source: `D:\black\Project\R300\src`

Destination ที่แน่นอน:
`C:\Users\Phadungsak\AppData\Roaming\MetaQuotes\Terminal\BB16F565FAAA6B23A20C26C49416FF05\MQL5\Experts\R300_EA`

ตรวจ MT5 File > Open Data Folder ว่าตรงกับ terminal นี้ก่อน Deploy
ไม่มีการเติม `MQL5` ซ้ำ สคริปต์ตรวจ source ครบและตรวจโฟลเดอร์ MQL5/Experts ก่อน
สร้างเฉพาะโฟลเดอร์ R300_EA หากยังไม่มี คัดลอกเฉพาะ `.mq5` / `.mqh` ที่ระบุ 8 ไฟล์
ทับไฟล์ชื่อเดียวกัน แสดงแต่ละไฟล์ที่ copy และหยุดเมื่อ error โดยไม่มีการลบไฟล์อื่น
หาก copy ล้มเหลวกลางทาง อาจมีบางไฟล์ถูก copy แล้ว ให้แก้สาเหตุและรันใหม่
สคริปต์ไม่ copy `.ex5` และไม่ compile ให้อัตโนมัติ

หลัง Deploy ให้เปิด `MQL5\Experts\R300_EA\R300_EA.mq5` ใน MetaEditor แล้วกด F7
จากนั้น Refresh รายการ Expert Advisors ใน Navigator ของ MT5

## Backtest

1. Deploy และ Compile สำเนาใน MT5 ตามขั้นตอนด้านบน
2. เปิด Strategy Tester (Ctrl+R) เลือก `R300_EA` และ Symbol `GOLD`
3. เลือก timeframe เช่น M5 สำหรับตรวจ lifecycle ของ Skeleton (ยังไม่ใช่กฎกลยุทธ์)
4. เลือกช่วงข้อมูลที่มี แล้วเริ่ม Single Test; ค่าช่วงเวลา, model, deposit, leverage และเกณฑ์กลยุทธ์ยังเป็น TODO ใน SPEC
5. ตรวจ Journal ว่ามี `R300 EA initialized`, Trading mode, Symbol, Broker และ Server
6. ผลที่คาดหวังคือไม่มี Order / Deal / Position ที่ EA สร้างขึ้น ไม่มีสัญญาณ และไม่มีผลตอบแทนให้ประเมินกลยุทธ์

เก็บผลทดสอบที่สร้างขึ้นใน `backtest/results/` หรือ `backtest/reports/` ซึ่ง Git ignore ไว้
Demo Forward Test จะกำหนดภายหลังใน SPEC

## Safety warning

**เวอร์ชันปัจจุบันยังไม่อนุญาต Auto Trading** ให้ปิด Algo Trading สำหรับการใช้งานบนกราฟ
Skeleton ไม่มีคำสั่งซื้อขายแม้เปิดปุ่ม Algo Trading: ไม่มี Buy/Sell, OrderSend,
การเปิดหรือแก้ไข Position, external API, DLL หรือ WebRequest
Safe Mode ใช้กับทุกบัญชีและ Strategy Tester ไม่สามารถปิดผ่าน Inputs
อย่าใช้ผลทดสอบ Skeleton เป็นหลักฐานประสิทธิภาพกลยุทธ์ เพราะยังไม่มี Trading Logic
