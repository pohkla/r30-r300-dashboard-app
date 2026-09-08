# R300 Trading System Specification

## 1. Objective
พัฒนา R300_EA ด้วย MQL5 สำหรับ MetaTrader 5 เริ่มจาก Skeleton แบบ SIGNAL/BACKTEST SAFE MODE
Trading Logic จะกำหนดในเอกสารนี้ภายหลัง ห้ามอนุมานกลยุทธ์จากชื่อโมดูล

## 2. Supported Markets
- Broker ปัจจุบัน: XM
- Symbol ทองปัจจุบัน: GOLD
- TODO: ตลาดเพิ่มเติมและข้อกำหนดสัญญาที่เกี่ยวข้อง

## 3. Multi-Timeframe Architecture
- H4: Trend Detection
- H1: Market Structure
- M15: Setup
- M5: Entry Confirmation
- TODO: วิธีเชื่อมเงื่อนไขระหว่าง timeframe และเวลาประเมินข้อมูล

## 4. H4 Trend
TODO: Trend algorithm และเงื่อนไขทั้งหมด

## 5. H1 Market Structure
TODO: BOS, CHOCH, Swing High / Swing Low

## 6. M15 Setup
TODO: Volume Profile, RSI Divergence, Fibonacci และวิธีใช้ร่วมกัน

## 7. M5 Entry
TODO: Break & Retest, Rejection, Engulfing และเงื่อนไขยืนยัน

## 8. Stop Loss
TODO: วิธีคำนวณและตรวจสอบ Stop Loss

## 9. Take Profit
TODO: วิธีคำนวณ Take Profit

## 10. Position Sizing
TODO: วิธีคำนวณขนาด Position และการปัดตามข้อกำหนด Symbol

## 11. Risk Management
TODO: ระดับความเสี่ยงและ Maximum risk protection

## 12. Exit Strategy
TODO: Take Profit, Break Even, Trailing Stop, Structure Exit, Partial Close

## 13. Trading Session
TODO: ช่วงเวลาและ timezone ที่ใช้

## 14. Spread / Slippage Filter
TODO: เงื่อนไขและค่าที่อนุญาต

## 15. News Filter
TODO: แหล่งข้อมูลและกฎที่อนุญาต

## 16. Backtest Rules
รองรับการโหลด EA ผ่าน MT5 Strategy Tester เพื่อทดสอบ initialization และ lifecycle
Skeleton ปัจจุบันต้องไม่มีการซื้อขายและไม่มีผลตอบแทนกลยุทธ์ให้ประเมิน
TODO: ช่วงข้อมูล, model, deposit, leverage, costs และเกณฑ์ประเมินกลยุทธ์

## 17. Forward Test Rules
วางแผนรองรับ Demo Forward Test ในอนาคต เวอร์ชันนี้ยังไม่มีการซื้อขายอัตโนมัติ
TODO: แผน Demo Forward Test, ระยะเวลา และเกณฑ์ผ่าน

## 18. Safety Rules
- เวอร์ชันแรกห้ามเปิด Order หรือ Position ในทุกสภาพแวดล้อม รวมถึง Tester และ Demo
- ห้าม Buy, Sell, OrderSend หรือการจัดการ Position จริง
- Safe Mode เป็นค่าคงที่ ไม่สามารถปิดผ่าน Inputs
- ห้าม external API, DLL และ WebRequest ในเวอร์ชันนี้
- ห้ามสร้างกลยุทธ์เอง กฎที่ยังไม่กำหนดต้องคงเป็น TODO
- แก้ไขเฉพาะ Project; การ Deploy ต้องได้รับคำสั่งชัดเจนจากผู้ใช้ก่อน
- TODO: ข้อกำหนดเพิ่มเติมสำหรับเวอร์ชันอนาคต
