import pymysql
import setup
import frontend
import entity.department 
import entity.doctor 
import entity.patient 
import entity.registration 
import entity.prescription 
import entity.payment 
import entity.drug 
import config



# 配置数据库连接
config = {
    'host': config.config['host'],
    'port': config.config['port'],
    'user': config.config['user'],
    'password': config.config['password'],
    'database': config.config['database'],
    'charset': config.config['charset'],
    'cursorclass': pymysql.cursors.DictCursor, # 设置返回结果为字典类型
    'autocommit': config.config['autocommit']  # 设置自动提交
}

# 建立连接
connection = pymysql.connect(**config)
cursor = connection.cursor()

# 可选：重置数据库，然后添加一些初始数据，第一次运行时没有数据库，需要先creat_table
# setup.drop_all_tables_for_testing(cursor)
# setup.create_table(cursor)
# entity.department.create_department(cursor, '内科') # 内科id=1
# entity.department.create_department(cursor, '外科') # 外科id=2
# entity.doctor.register_doctor(cursor, '张内科医生', '男', '13812345678', '主任医师', 1) 
# entity.doctor.register_doctor(cursor, '李内科医生', '女', '13898765432', '副主任医师', 1)
# entity.doctor.register_doctor(cursor, '陈外科医生', '女', '13898765432', '副主任医师', 2) 
# entity.doctor.register_doctor(cursor, '王外科医师', '男', '13856789123', '主任医师', 2)
# entity.drug.add_drug(cursor, '阿司匹林', 100, 5.5)
# entity.drug.add_drug(cursor, '头孢呋辛', 100, 9.5)
# entity.patient.register_patient(cursor, '张三', '男', '13812345678')
# entity.patient.register_patient(cursor, '王五', '男', '13856789123')

frontend.start(cursor)