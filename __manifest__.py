{
    'name': 'Need Corona Api Adapter',
    'version': '17.0.1.0.21',
    'category': 'Manufacturing',
    'summary': 'Send work operation data to external PHP API',
    'description': """
        โมดูลนี้ทำหน้าที่เป็น API Gateway สำหรับสนับสนุนการส่งข้อมูลการผลิตจาก Odoo ไปยังระบบ Need Corona
        Features:
        - ส่งข้อมูลการผลิต (MRP Module)จาก Odoo ไปยังระบบ Need Corona
        - หา Main MO อัตโนมัติจาก Sub MO เพื่อใช้เป็น knockdown_no
        - จัดการ System Parameters ผ่าน Code แทน XML
        - บันทึก API Logs พร้อม JSON ข้อมูลใน Internal Log Note ของ MO
    """,
    'author': 'Need Shopping',
    'depends': ['mrp', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        # 'data/assets.xml',  # Temporarily disabled for compatibility
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
} 