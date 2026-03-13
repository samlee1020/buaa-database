import pymysql

def register_patient(cursor, name, gender, phone_number):
    """
    新病人注册
    
    Args:
        cursor: 数据库游标
        name: 病人姓名
        gender: 性别 ('男' 或 '女')
        phone_number: 电话号码
    
    Returns:
        int: 新注册病人的病历号，失败返回None
    """
    try:
        # 插入新病人信息
        sql = """
        INSERT INTO patient (name, gender, phone_number, created_at) 
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(sql, (name, gender, phone_number))
        
        # 获取刚插入的病历号
        cursor.execute("SELECT LAST_INSERT_ID()")
        result = cursor.fetchone()
        
        if isinstance(result, tuple):
            patient_id = result[0]
        else:
            patient_id = result['LAST_INSERT_ID()']
        
        print(f"✅ 病人注册成功！病历号: {patient_id}")
        return patient_id
        
    except Exception as e:
        print(f"❌ 病人注册失败: {e}")
        return None

def query_patient(cursor, patient_id=None, name=None, phone_number=None):
    """
    查询病人信息
    
    Args:
        cursor: 数据库游标
        patient_id: 病历号（可选）
        name: 姓名（可选，支持模糊查询）
        phone_number: 电话号码（可选，支持模糊查询）
    
    Returns:
        list: 查询结果列表
    """
    try:
        # 构建查询条件
        conditions = []
        params = []
        
        if patient_id:
            conditions.append("patient_id = %s")
            params.append(patient_id)
        
        if name:
            conditions.append("name LIKE %s")
            params.append(f"%{name}%")
        
        if phone_number:
            conditions.append("phone_number LIKE %s")
            params.append(f"%{phone_number}%")
        
        # 如果没有查询条件，返回所有病人
        if not conditions:
            sql = "SELECT * FROM patient ORDER BY patient_id"
        else:
            sql = f"SELECT * FROM patient WHERE {' AND '.join(conditions)} ORDER BY patient_id"
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # 输出查询结果
        print(f"\n🔍 查询到 {len(results)} 条病人记录")
        print("-" * 90)
        print(f"{'病历号':<8} {'姓名':<10} {'性别':<6} {'电话号码':<15} {'创建时间':<20}")
        print("-" * 90)
        
        if results:
            for patient in results:
                # 确保时间字段正确显示
                created_time = str(patient['created_at']) if patient['created_at'] else 'NULL'
                print(f"{patient['patient_id']:<8} {patient['name']:<10} {patient['gender']:<6} "
                      f"{patient['phone_number']:<15} {created_time:<20}")
        else:
            print("  没有找到匹配的病人记录")
        
        print("-" * 90)
        
        return results
        
    except Exception as e:
        print(f"❌ 查询病人失败: {e}")
        return []

def update_patient(cursor, patient_id, name=None, phone_number=None):
    """
    修改病人信息
    
    Args:
        cursor: 数据库游标
        patient_id: 病历号
        name: 新姓名（可选）
        phone_number: 新电话号码（可选）
    
    Returns:
        bool: 修改是否成功
    """
    try:
        # 检查病人是否存在
        cursor.execute("SELECT * FROM patient WHERE patient_id = %s", (patient_id,))
        if not cursor.fetchone():
            print(f"❌ 病历号 {patient_id} 不存在")
            return False
        
        # 构建更新语句
        updates = []
        params = []
        
        if name:
            updates.append("name = %s")
            params.append(name)
        
        if phone_number:
            updates.append("phone_number = %s")
            params.append(phone_number)
        
        if not updates:
            print("❌ 没有提供要更新的信息")
            return False
        
        # 添加更新时间和病历号
        updates.append("updated_at = NOW()")
        params.append(patient_id)
        
        sql = f"UPDATE patient SET {', '.join(updates)} WHERE patient_id = %s"
        cursor.execute(sql, params)
        
        print(f"✅ 病人 {patient_id} 信息更新成功")
        return True
        
    except Exception as e:
        print(f"❌ 更新病人信息失败: {e}")
        return False

def delete_patient(cursor, patient_id):
    """
    删除病人信息
    
    Args:
        cursor: 数据库游标
        patient_id: 病历号
    
    Returns:
        bool: 删除是否成功
    """
    try:
        # 检查病人是否存在
        cursor.execute("SELECT * FROM patient WHERE patient_id = %s", (patient_id,))
        if not cursor.fetchone():
            print(f"❌ 病历号 {patient_id} 不存在")
            return False
        
        # 删除病人（由于外键约束，相关的挂号、缴费等记录会自动删除）
        cursor.execute("DELETE FROM patient WHERE patient_id = %s", (patient_id,))
        
        print(f"✅ 病人 {patient_id} 删除成功")
        return True
        
    except Exception as e:
        print(f"❌ 删除病人失败: {e}")
        return False

def check_patient_exists(cursor, patient_id):
    """
    判断病人ID是否存在
    
    Args:
        cursor: 数据库游标
        patient_id: 病历号
    
    Returns:
        bool: 存在返回True，不存在返回False
    """
    try:
        # 查询病人是否存在
        cursor.execute("SELECT patient_id FROM patient WHERE patient_id = %s", (patient_id,))
        result = cursor.fetchone()
        
        if result:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ 检查病人ID失败: {e}")
        return False
