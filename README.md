# 📋 เอกสารสำหรับ PHP Developer - Need Corona API Integration

## 🎯 **ภาพรวม**

Odoo จะส่งข้อมูลการผลิต (Work Operation) มาให้ Endpoint ผ่าน HTTP POST ในรูปแบบ JSON
เมื่อ User กดปุ่ม Start/Finish Work Order ใน Odoo

---

## 📤 **ข้อมูลที่ Odoo จะส่งมา (JSON Request)**

### **🔗 HTTP Request:**

```d
POST https://your-server.com/api/work_operation.php
Content-Type: application/json
User-Agent: Odoo-MRP-Integration/1.0
```

### **📋 JSON Structure:**

```json
{
  "knockdown_no": "LP6807-03277",
  "station_name": "ติดตั้งโครงสร้าง", 
  "start_time": {
    "time": "2025-01-09 14:30:15",
    "status": true
  },
  "end_time": {
    "time": "2025-01-09 14:32:45",
    "status": true
  },
  "status": "started",
  "mo_id": 10040,
  "sub_mo_id": 10044,
  "sub_mo_name": "LP6807-03280"
}
```

### **📝 Field Descriptions:**

| Field | Type | Required | Description | ตัวอย่าง |
|-------|------|----------|-------------|----------|
| `knockdown_no` | string | ✅ | เลขที่ใบสั่งผลิตหลัก (Main MO) | "LP6807-03277" |
| `station_name` | string | ✅ | รหัสอ้างอิง Product (Internal Reference) | "SF-001" |
| `start_time` | object | ✅ | วัตถุเวลาเริ่มงาน | `{"time": "2025-01-09 14:30:15", "status": true}` |
| `end_time` | object | ✅ | วัตถุเวลาเสร็จงาน | `{"time": null, "status": false}` สำหรับ "started" |
| `status` | string | ✅ | สถานะการทำงาน | "started" หรือ "completed" |
| `mo_id` | integer | ℹ️ | ID ใบสั่งผลิตหลัก | 10040 |
| `sub_mo_id` | integer | ℹ️ | ID ใบสั่งผลิตย่อย | 10044 |
| `sub_mo_name` | string | ℹ️ | ชื่อใบสั่งผลิตย่อย | "LP6807-03280" |

### **⏰ Time Object Structure:**

```json
{
  "time": "2025-01-09 14:30:15",  // YYYY-MM-DD HH:MM:SS หรือ null
  "status": true                  // true = มีข้อมูล, false = ไม่มีข้อมูล
}
```

---

## 📥 **ข้อมูลที่ต้องส่งกลับ (JSON Response)**

### **✅ Success Response (HTTP 200):**

```json
{
  "success": true,
  "message": "Work operation data received and logged successfully",
  "log_id": 5541,
  "timestamp": "2025-01-09 14:30:15"
}
```

### **❌ Error Response (HTTP 400/500):**

```json
{
  "success": false,
  "error": "Missing required fields: knockdown_no",
  "timestamp": "2025-01-09 14:30:15"
}
```

### **🔴 Required Fields ทุกกรณี:**

- `success`: boolean (true/false)
- `timestamp`: string (YYYY-MM-DD HH:MM:SS)

### **🟢 Success Response เพิ่มเติม:**

- `message`: string (ข้อความสำเร็จ)
- `log_id`: integer/string (ID ของ log record ที่บันทึก)

### **🔴 Error Response เพิ่มเติม:**

- `error`: string (รายละเอียดข้อผิดพลาด)

---

## 🚨 **เหตุการณ์ที่อาจทำให้เกิดปัญหา**

### **1. 🔍 Station Name ไม่ตรงกัน**

**ปัญหา:** `station_name` ที่ส่งมาไม่ตรงกับข้อมูลในระบบ PHP

**ตัวอย่าง:**

- Odoo ส่ง: `"station_name": "ติดตั้งโครงสร้างเหล็ก"`
- PHP Database มี: `"ติดตั้งโครงสร้าง"` แต่ไม่มี `"ติดตั้งโครงสร้างเหล็ก"`

**แนะนำการจัดการ:**

```json
{
  "success": false,
  "error": "Station 'ติดตั้งโครงสร้างเหล็ก' ไม่พบค่าในฐานข้อมูล",
  "timestamp": "2025-01-09 14:30:15"
}
```

### **2. 📋 Knockdown No ไม่พบ**

**ปัญหา:** `knockdown_no` ไม่มีในระบบ PHP

**ตัวอย่าง:**

- Odoo ส่ง: `"knockdown_no": "LP6807-03277"`
- PHP Database ไม่มี record นี้

**แนะนำการจัดการ:**

```json
{
  "success": false,
  "error": "JOB 'LP6807-03277' ไม่พบค่าในฐานข้อมูล: {ข้อความ error msg.}",
  "timestamp": "2025-01-09 14:30:15"
}
```

### **3. ⏰ Time Format ผิด**

**ปัญหา:** เวลาที่ส่งมาไม่ตรงรูปแบบ

**ตัวอย่าง:**

```json
{
  "start_time": {
    "time": "invalid-date",
    "status": true
  }
}
```

**แนะนำการจัดการ:**

```json
{
  "success": false,
  "error": "Invalid datetime format : {ข้อความ error msg.}",
  "timestamp": "2025-01-09 14:30:15"
}
```

### **4. 🔄 Duplicate Records**

**ปัญหา:** ข้อมูลซ้ำกัน (เดียวกันส่งมาหลายครั้ง)

**แนะนำการจัดการ:**

```json
{
  "success": false,
  "error": "เกิดการส่งค่าซ้ำ ข้อมูล : {ข้อความ error msg.}",
  "timestamp": "2025-01-09 14:30:15"
}
```

### **5. 📊 Invalid Status Transition**

**ปัญหา:** เปลี่ยนสถานะไม่ถูกต้อง (เช่น ส่ง "completed" ก่อน "started")

**แนะนำการจัดการ:**

```json
{
  "success": false,
  "error": "Invalid status transition: {ข้อความ error msg.}",
  "timestamp": "2025-01-09 14:30:15"
}
```

---

## 🔧 **Validation**

### **1. Required Fields Validation:**

```php
$required_fields = ['knockdown_no', 'station_name', 'start_time', 'end_time', 'status'];
foreach ($required_fields as $field) {
    if (!isset($input_data[$field])) {
        return error_response("Missing required field: $field");
    }
}
```

### **2. Status Validation:**

```php
if (!in_array($input_data['status'], ['started', 'completed'])) {
    return error_response("Invalid status. Must be 'started' or 'completed'");
}
```

### **3. Time Object Validation:**

```php
if (!is_array($input_data['start_time']) || 
    !array_key_exists('time', $input_data['start_time']) ||
    !array_key_exists('status', $input_data['start_time'])) {
    return error_response("Invalid time object structure for start_time");
}
```

### **4. DateTime Validation:**

```php
if ($input_data['start_time']['status'] === true) {
    $date = DateTime::createFromFormat('Y-m-d H:i:s', $input_data['start_time']['time']);
    if (!$date) {
        return error_response("Invalid datetime format in start_time");
    }
}
```

---

## 📊 **ตัวอย่าง Use Cases**

### **Case 1: เริ่มงาน (Started)**

**Request:**

```json
{
  "knockdown_no": "LP6807-03277",
  "station_name": "ติดตั้งโครงสร้าง",
  "start_time": {"time": "2025-01-09 14:30:15", "status": true},
  "end_time": {"time": null, "status": false},
  "status": "started"
}
```

**ต้องได้รับ Resp ตามด้านล่าง:**

```json
{
  "success": true,
  "message": "Work started successfully",
  "log_id": 1001,
  "timestamp": "2025-01-09 14:30:15"
}
```

### **Case 2: เสร็จงาน (Completed)**

**Request:**

```json
{
  "knockdown_no": "LP6807-03277",
  "station_name": "ติดตั้งโครงสร้าง", 
  "start_time": {"time": "2025-01-09 14:30:15", "status": true},
  "end_time": {"time": "2025-01-09 14:45:30", "status": true},
  "status": "completed"
}
```

**Expected Response:**

```json
{
  "success": true,
  "message": "Work completed successfully",
  "log_id": 1002,
  "timestamp": "2025-01-09 14:45:30"
}
```

---

## 🛠️ **Database Schema ที่ควรมี**

```sql
CREATE TABLE work_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    knockdown_no VARCHAR(100) NOT NULL,
    station_name VARCHAR(100) NOT NULL,
    start_time DATETIME NULL,
    end_time DATETIME NULL,
    status ENUM('started', 'completed') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_knockdown_no (knockdown_no),
    INDEX idx_station_name (station_name),
    INDEX idx_status (status)
);

CREATE TABLE stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_name VARCHAR(100) UNIQUE NOT NULL,
    current_status ENUM('idle', 'started', 'completed') DEFAULT 'idle',
    current_knockdown_no VARCHAR(100) NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## 🚀 **Testing Commands**

### **Test เชื่อมต่อ:**

```bash
curl -X POST https://<dns>/api/work_operation.php \
  -H "Content-Type: application/json" \
  -d '{
    "knockdown_no": "TEST-001",
    "station_name": "ติดตั้งโครงสร้าง",
    "start_time": {"time": "2025-01-09 14:30:15", "status": true},
    "end_time": {"time": null, "status": false},
    "status": "started"
  }'
```

### **Test Missing Field:**

```bash
curl -X POST https://<dns>/work_operation.php \
  -H "Content-Type: application/json" \
  -d '{"status": "started"}'
```

---

- เมื่อมีปัญหา: ตรวจสอบ JSON structure และ validation
- Response ต้องเป็น JSON เสมอ
- HTTP Status Code ต้องสื่อสารอย่างถูกต้อง (200 = สำเร็จ, 400 = ข้อมูลผิด, 500 = ระบบผิดพลาด)

**สำคัญ:**
ระบบ Odoo จะบันทึก log ทุกกรณี ทั้งสำเร็จและไม่สำเร็จใน Manufacturing Order
# mrp_work_operation_api
