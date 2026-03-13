import pymysql
import entity.patient as patient_module
import entity.department as department_module
import entity.registration as registration_module
import entity.prescription as prescription_module
import entity.payment as payment_module
import entity.doctor as doctor_module
import entity.drug as drug_module
import setup

registration_fee = 50 # 挂号费用

# 简单的业务逻辑
def start(cursor):
    while True:
        print("""
欢迎使用门诊管理系统
请选择：
    1. 以病人身份继续
    2. 以医生身份继续
    3. 以系统管理员身份继续
    4. 退出系统
    """)
        choice = input("请输入您的选择：")
        if choice == "1":
            patient_menu(cursor)
        elif choice == "2":
            doctor_menu(cursor)
        elif choice == "3":
            admin_menu(cursor) 
        elif choice == "4":
            break
        else:
            print("输入错误，请重新输入")
    
    print("感谢使用，期待下次再见！")

def patient_menu(cursor):
    while True:
        print("""
你现在是【病人】身份
请选择：
    1. 查询信息
    2. 注册
    3. 登陆
    4. 返回上一级
    """)
        choice = input("请输入您的选择：")
        if choice == "1":
            patient_query(cursor)
        elif choice == "2":
            patient_register(cursor)
        elif choice == "3":
            patient_login(cursor)
        elif choice == "4":
            break
        else:
            print("输入错误，请重新输入")

def doctor_menu(cursor):
    print("你现在是【医生】身份")
    doctor_id = int(input("请输入工号以登陆："))
    print("正在查询您的信息...")
    if not doctor_module.check_doctor_exists(cursor, doctor_id):
        print("未找到您的信息，请先联系管理员入职")
        return
    else:
        doctor_module.query_doctor(cursor, doctor_id=doctor_id)
    
    while True:
        print("""
请选择操作：
    1. 查看待办挂号（未出诊和出诊中）
    2. 出诊并开具处方
    3. 完成就诊
    4. 退出登陆
        """)
        choice = input("请输入您的选择：")
        if choice == "1":
            doctor_query_registration(cursor, doctor_id)
        elif choice == "2":
            doctor_create_prescription(cursor, doctor_id)
        elif choice == "3":
            doctor_complete_registration(cursor, doctor_id)
        elif choice == "4":
            break
        else:
            print("输入错误，请重新输入")

def admin_menu(cursor):
    while True:
        print("""
您已进入管理员界面！
请选择功能：
    1. 科室管理
    2. 挂号受理
    3. 医生管理
    4. 药品管理
    5. 挂号管理
    6. 处方管理
    7. 显示表内容
    8. 系统重置
    9. 返回上一级
        """)
        choice = input("请输入你的选择")
        if choice == "1":
            department_mangement(cursor)
        elif choice == "2":
            registration_process(cursor)
        elif choice == "3":
            doctors_management(cursor)
        elif choice == "4":
            drugs_management(cursor)
        elif choice == "5":
            registration_management(cursor)
        elif choice == "6":
            prescription_management(cursor)
        elif choice == "7":
            table = input("请输入要显示的表名（留空显示所有表）：")
            if table:
                setup.show_table_content(cursor, table)
            else:
                setup.show_all_tables_content(cursor)
        elif choice == "8":
            print("请注意，此操作会清空所有表数据，然后重建表，请确认！")
            choice = input("确认重置吗？(y/n)")
            if choice == "y":
                setup.drop_all_tables_for_testing(cursor)
                setup.create_table(cursor)
                print("重置成功！")
            else:
                print("操作已取消")
        elif choice == "9":
            break
        else:
            print("输入错误，请重新输入")

# patient
def patient_query(cursor):
    print("""
请输入查询关键字（病历号patient_id、姓名name、手机号phone_number）
输入格式：\"type keyword\"，如\"name 张三\"
    """)
    while True:
        query_str = input("请输入查询字符串：")
        try:
            query_type, query_key = query_str.split()
            if query_type not in ["patient_id", "name", "phone_number"]:
                print("输入错误，请重新输入")
                continue
            break
        except ValueError:
            print("输入错误，请重新输入")
            continue
    patient_module.query_patient(cursor, **{query_type: query_key})

def patient_register(cursor):
    print("""
请输入您的信息：
    """)
    name = input("输入您的姓名：")
    gender = input("输入您的性别（男/女）：")
    phone_number = input("输入您的手机号：")
    
    try:
        # 使用存储过程注册患者
        cursor.callproc('sp_register_patient', [name, gender, phone_number, 0])
        cursor.execute("SELECT @_sp_register_patient_3")
        result = cursor.fetchone()
        patient_id = result['@_sp_register_patient_3']
        
        if patient_id:
            print(f"✅ 病人注册成功！病历号: {patient_id}")
        else:
            print("❌ 病人注册失败")
    except Exception as e:
        print(f"❌ 病人注册失败: {e}")

def patient_login(cursor):
    print("""
请输入病历号以登陆
    """)
    patient_id = int(input("请输入病历号："))
    print("正在查询您的信息...")
    result = patient_module.query_patient(cursor, patient_id=patient_id)
    if not result:
        print("未找到您的信息，请先注册")
        return
    while True:
        print("""
请选择业务：
    1. 修改信息
    2. 删除病历
    3. 科室查询
    4. 挂号
    5. 挂号查询
    6. 处方查询
    7. 缴费
    8. 退出登陆
        """)
        choice = input("请输入您的选择：")
        if choice == "1":
            patient_change_info(cursor, patient_id)
        elif choice == "2":
            patient_module.delete_patient(cursor, patient_id)
        elif choice == "3":
            patient_query_department(cursor)
        elif choice == "4":
            patient_creat_registrations(cursor, patient_id)
        elif choice == "5":
            registration_module.query_registration(cursor, patient_id=patient_id)
        elif choice == "6":
            registration_id = int(input("请输入要查询的处方对应的挂号ID："))
            prescription_module.query_prescription(cursor, registration_id=registration_id)
        elif choice == "7":
            patient_pay(cursor, patient_id)
        elif choice == "8":
            break
        else:
            print("输入错误，请重新输入")

def patient_change_info(cursor, patient_id):
    print("""
请输入修改关键字（姓名name、手机号phone_number）
输入格式：\"type keyword\"，如\"name 张三\"
    """)
    while True:
        query_str = input("请输入查询字符串：")
        try:
            query_type, query_key = query_str.split()
            if query_type not in ["name", "phone_number"]:
                print("输入错误，请重新输入")
                continue
            break
        except ValueError:
            print("输入错误，请重新输入")
            continue
    patient_module.update_patient(cursor, patient_id, **{query_type: query_key})

def patient_query_department(cursor):
    department_name = input("请输入科室名称（留空查询所有科室）：")
    if department_name:
        department_module.query_department(cursor, department_name=department_name)
    else:
        department_module.query_department(cursor)

def patient_creat_registrations(cursor, patient_id):
    print("正在列出所有科室...")
    department_module.query_department(cursor)
    department_id = int(input("请输入科室ID："))
    
    try:
        # 使用存储过程创建挂号
        cursor.callproc('sp_create_registration', [patient_id, department_id, 0])
        cursor.execute("SELECT @_sp_create_registration_2")
        result = cursor.fetchone()
        registration_id = result['@_sp_create_registration_2']
        
        if registration_id:
            print(f"✅ 挂号成功！挂号编号: {registration_id}")
        else:
            print("❌ 挂号失败")
    except Exception as e:
        print(f"❌ 挂号失败: {e}")

def patient_pay(cursor, patient_id):
    print("正在列出所有待缴费信息")
    payment_module.query_payment(cursor, patient_id=patient_id, time_is_null=True)
    payment_id = int(input("请输入要缴费的缴费单ID："))
    
    try:
        # 使用存储过程完成缴费
        cursor.callproc('sp_complete_payment', [payment_id, 0])
        cursor.execute("SELECT @_sp_complete_payment_1")
        result = cursor.fetchone()
        success = result['@_sp_complete_payment_1']
        
        if success:
            print("✅ 缴费成功！")
        else:
            print("❌ 缴费失败")
    except Exception as e:
        print(f"❌ 缴费失败: {e}")

# doctor
def doctor_query_registration(cursor, doctor_id):
    print("这里是医生查看待办挂号界面")
    print("正在列出所有未出诊和出诊中的挂号信息...")
    
    # 查询未出诊和出诊中的挂号
    pending_results = registration_module.query_registration(cursor, doctor_id=doctor_id, status='pending')
    in_progress_results = registration_module.query_registration(cursor, doctor_id=doctor_id, status='in_progress')
    
    if not pending_results and not in_progress_results:
        print("暂无待办挂号")
    else:
        print(f"共有 {len(pending_results) + len(in_progress_results)} 个待办挂号")

def doctor_complete_registration(cursor, doctor_id):
    print("这里是完成就诊界面")
    print("正在列出所有未出诊和出诊中的挂号信息...")
    
    # 查询未出诊和出诊中的挂号
    pending_results = registration_module.query_registration(cursor, doctor_id=doctor_id, status='pending')
    in_progress_results = registration_module.query_registration(cursor, doctor_id=doctor_id, status='in_progress')
    
    if not pending_results and not in_progress_results:
        print("暂无待办挂号，无需完成就诊")
        return
    
    # 显示挂号列表
    print("\n待办挂号列表：")
    all_results = []
    if pending_results:
        all_results.extend(pending_results)
    if in_progress_results:
        all_results.extend(in_progress_results)
    
    for i, reg in enumerate(all_results, 1):
        patient_name = reg['patient_name'] if reg['patient_name'] else '未知病人'
        dept_name = reg['department_name'] if reg['department_name'] else '未知科室'
        status_display = '未出诊' if reg['status'] == 'pending' else '出诊中'
        print(f"{i}. 挂号编号: {reg['registration_id']}, 患者: {patient_name}, 科室: {dept_name}, 状态: {status_display}")
    
    try:
        choice = int(input("\n请选择要完成就诊的挂号编号（输入序号）："))
        if choice < 1 or choice > len(all_results):
            print("输入错误，请重新选择")
            return
        
        selected_reg = all_results[choice - 1]
        registration_id = selected_reg['registration_id']
        
        # 确认操作
        confirm = input(f"确定要标记挂号 {registration_id} 为已出诊吗？(y/n): ")
        if confirm.lower() == 'y':
            success = registration_module.update_registration_status(cursor, registration_id, 'completed')
            if success:
                print("✅ 就诊完成！该挂号已标记为已出诊")
            else:
                print("❌ 就诊完成操作失败，请重试")
        else:
            print("操作已取消")
            
    except ValueError:
        print("输入错误，请输入有效的数字")
    except Exception as e:
        print(f"操作失败：{e}")

def doctor_create_prescription(cursor, doctor_id):
    print("这里是医生开具处方界面")
    registration_id = int(input("请输入要开处方的挂号ID："))
    print("正在列出所有药品信息")
    drug_module.query_drug(cursor)
    drug_id = int(input("请输入药品ID："))
    quantity = int(input("请输入药品数量："))
    print("正在查询药品信息...")
    if not drug_module.check_drug_exists(cursor, drug_id):
        print("未找到药品信息，请先联系管理员添加药品")
        return

    try:
        # 使用存储过程开具处方（现在会自动创建缴费记录）
        cursor.callproc('sp_create_prescription', [
            registration_id, 
            drug_id, 
            quantity, 
            0
        ])
        cursor.execute("SELECT @_sp_create_prescription_3")
        result = cursor.fetchone()
        prescription_id = result['@_sp_create_prescription_3']
        
        if prescription_id:
            print(f"✅ 处方开具成功！处方编号: {prescription_id}")
        else:
            print("❌ 处方开具失败")
    except Exception as e:
        print(f"❌ 处方开具失败: {e}")

# admin

def department_mangement(cursor):
    print("这里是科室管理界面")
    print("正在列出所有科室信息...")
    department_module.query_department(cursor)
    while True:
        print("""
请选择操作：
    1. 新增科室
    2. 修改科室名称
    3. 删除科室
    4. 返回上一级
        """)
        choice = input("请输入您的选择：")
        if choice == "1":
            name = input("请输入新增科室名称：")
            department_module.create_department(cursor, name)
        elif choice == "2":
            department_id = input("请输入科室ID：")
            new_name = input("请输入新的科室名称：")
            department_module.update_department(cursor, department_id, new_name)
        elif choice == "3":
            department_id = int(input("请输入要删除的科室ID："))
            department_module.delete_department(cursor, department_id)
        elif choice == "4":
            break
        else:
            print("输入错误，请重新输入")

def registration_process(cursor):
    print("这里是挂号受理界面")
    print("正在列出所有未受理挂号信息...")
    registration_module.query_registration(cursor, unassigned_only=True)
    registration_id = int(input("请输入挂号ID："))
    doctor_id = int(input("请输入医生ID："))
    
    try:
        # 使用存储过程处理挂号
        cursor.callproc('sp_process_registration', [registration_id, doctor_id, 0])
        cursor.execute("SELECT @_sp_process_registration_2")
        result = cursor.fetchone()
        success = result['@_sp_process_registration_2']
        
        if success:
            print("✅ 挂号受理成功！")
        else:
            print("❌ 挂号受理失败")
    except Exception as e:
        print(f"❌ 挂号受理失败: {e}")

def doctors_management(cursor):
    print("这里是医生管理界面")
    print("正在列出所有医生信息...")
    doctor_module.query_doctor(cursor)
    while True:
        print("""
请选择操作：
    1. 修改医生所属科室
    2. 修改医生职称
    3. 新增医生
    4. 删除医生
    5. 返回上一级
        """)
        choice = input("请输入您的选择：")
        if choice == "1":
            print("正在列出所有科室信息...")
            department_module.query_department(cursor)
            doctor_id = int(input("请输入医生ID："))
            department_id = int(input("请输入新的科室ID："))
            doctor_module.set_doctor_department(cursor, doctor_id, department_id)
        elif choice == "2":
            doctor_id = int(input("请输入医生ID："))
            position = input("请输入新的职称：")
            doctor_module.set_doctor_position(cursor, doctor_id, position)
        elif choice == "3":
            name = input("请输入医生姓名：")
            gender = input("请输入医生性别（男/女）：")
            phone_number = input("请输入医生手机号：")
            doctor_module.register_doctor(cursor, name, gender, phone_number)
        elif choice == "4":
            doctor_id = int(input("请输入要删除的医生ID："))
            doctor_module.delete_doctor(cursor, doctor_id)
        elif choice == "5":
            break
        else:
            print("输入错误，请重新输入")

def drugs_management(cursor):
    print("这里是药品管理界面")
    print("正在列出所有药品信息...")
    drug_module.query_drug(cursor)
    while True:
        print("""
请选择操作：
    1. 新增药品
    2. 修改药品信息（价格、库存）
    3. 删除药品
    4. 返回上一级
        """)
        choice = input("请输入您的选择：")
        if choice == "1":
            name = input("请输入药品名称：")
            quantity = int(input("请输入药品库存："))
            price = float(input("请输入药品价格："))
            drug_module.add_drug(cursor, name, quantity, price)
        elif choice == "2":
            drug_id = int(input("请输入药品ID："))
            if not drug_module.check_drug_exists(cursor, drug_id):
                print("未找到药品信息，请先联系管理员添加药品")
                return
            print("请输入修改关键字（价格price、库存stored_quantity）")
            print("输入格式：\"type keyword\"，如\"price 100.0\"")
            while True:
                query_str = input("请输入查询字符串：")
                try:
                    query_type, query_key = query_str.split()
                    if query_type not in ["price", "stored_quantity"]:
                        print("输入错误，请重新输入")
                        continue
                    break
                except ValueError:
                    print("输入错误，请重新输入")
                    continue
            drug_module.update_drug_info(cursor, drug_id, **{query_type: query_key})
        elif choice == "3":
            drug_id = int(input("请输入要删除的药品ID："))
            drug_module.delete_drug(cursor, drug_id)
        elif choice == "4":
            break
        else:
            print("输入错误，请重新输入")

def registration_management(cursor):
    print("这里是挂号管理界面")
    print("正在列出所有挂号信息...")
    registration_module.query_registration(cursor)
    while True:
        print("""
请选择操作：
    1. 删除挂号
    2. 返回上一级
        """)
        choice = input("请输入您的选择：")
        if choice == "1":
            registration_id = int(input("请输入要删除的挂号ID："))
            registration_module.delete_registration(cursor, registration_id)
        elif choice == "2":
            break
        else:
            print("输入错误，请重新输入")

def prescription_management(cursor):
    print("这里是处方管理界面")
    print("正在列出所有处方信息...")
    prescription_module.query_prescription(cursor)
    while True:
        print("""
请选择操作：
    1. 删除处方
    2. 返回上一级
        """)
        choice = input("请输入您的选择：")
        if choice == "1":
            prescription_id = int(input("请输入要删除的处方ID："))
            prescription_module.delete_prescription(cursor, prescription_id)
        elif choice == "2":
            break
        else:
            print("输入错误，请重新输入")