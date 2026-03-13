import pymysql

def register_doctor(cursor, name, gender, phone_number, position=None, department_id=None):
    """
    新医生注册
    
    Args:
        cursor: 数据库游标
        name: 医生姓名
        gender: 性别 ('男' 或 '女')
        phone_number: 电话号码
        position: 职称（可选，如：主任医师、副主任医师、主治医师等）
        department_id: 科室编号（可选，需要先存在对应科室）
    
    Returns:
        int: 新注册医生的工号，失败返回None
    """
    try:
        # 插入新医生信息
        sql = """
        INSERT INTO doctor (name, gender, phone_number, position, department_id, created_at) 
        VALUES (%s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(sql, (name, gender, phone_number, position, department_id))
        
        # 获取刚插入的医生工号
        cursor.execute("SELECT LAST_INSERT_ID()")
        result = cursor.fetchone()
        
        if isinstance(result, tuple):
            doctor_id = result[0]
        else:
            doctor_id = result['LAST_INSERT_ID()']
        
        print(f"✅ 医生注册成功！工号: {doctor_id}")
        return doctor_id
        
    except Exception as e:
        print(f"❌ 医生注册失败: {e}")
        return None

def query_doctor(cursor, doctor_id=None, name=None, phone_number=None, position=None, department_id=None):
    """
    查询医生信息
    
    Args:
        cursor: 数据库游标
        doctor_id: 医生工号（可选）
        name: 姓名（可选，支持模糊查询）
        phone_number: 电话号码（可选，支持模糊查询）
        position: 职称（可选，支持模糊查询）
        department_id: 科室编号（可选）
    
    Returns:
        list: 查询结果列表
    """
    try:
        # 构建查询条件
        conditions = []
        params = []
        
        if doctor_id:
            conditions.append("d.doctor_id = %s")
            params.append(doctor_id)
        
        if name:
            conditions.append("d.name LIKE %s")
            params.append(f"%{name}%")
        
        if phone_number:
            conditions.append("d.phone_number LIKE %s")
            params.append(f"%{phone_number}%")
        
        if position:
            conditions.append("d.position LIKE %s")
            params.append(f"%{position}%")
        
        if department_id:
            conditions.append("d.department_id = %s")
            params.append(department_id)
        
        # 构建SQL查询，包含科室名称
        if not conditions:
            sql = """
            SELECT d.*, dept.department_name 
            FROM doctor d 
            LEFT JOIN department dept ON d.department_id = dept.department_id 
            ORDER BY d.doctor_id
            """
        else:
            sql = f"""
            SELECT d.*, dept.department_name 
            FROM doctor d 
            LEFT JOIN department dept ON d.department_id = dept.department_id 
            WHERE {' AND '.join(conditions)} 
            ORDER BY d.doctor_id
            """
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # 输出查询结果
        print(f"\n🔍 查询到 {len(results)} 条医生记录")
        print("-" * 120)
        print(f"{'工号':<8} {'姓名':<10} {'性别':<6} {'电话号码':<15} {'职称':<12} {'科室':<15} {'科室ID':<8} {'创建时间':<20}")
        print("-" * 120)
        
        if results:
            for doctor in results:
                dept_name = doctor['department_name'] if doctor['department_name'] else '未分配'
                dept_id = doctor['department_id'] if doctor['department_id'] else 'NULL'
                position = doctor['position'] if doctor['position'] else '未分配'
                created_time = str(doctor['created_at']) if doctor['created_at'] else 'NULL'
                
                print(f"{doctor['doctor_id']:<8} {doctor['name']:<10} {doctor['gender']:<6} "
                      f"{doctor['phone_number']:<15} {position:<12} {dept_name:<15} {dept_id:<8} {created_time:<20}")
        else:
            print("  没有找到匹配的医生记录")
        
        print("-" * 120)
        
        return results
        
    except Exception as e:
        print(f"❌ 查询医生失败: {e}")
        return []

def set_doctor_department(cursor, doctor_id, department_id):
    """
    设置医生所属科室
    
    Args:
        cursor: 数据库游标
        doctor_id: 医生工号
        department_id: 科室编号
    
    Returns:
        bool: 设置是否成功
    """
    try:
        # 1. 检查医生是否存在
        cursor.execute("SELECT name, department_id FROM doctor WHERE doctor_id = %s", (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            print(f"❌ 医生工号 {doctor_id} 不存在")
            return False
        
        # 2. 检查科室是否存在
        cursor.execute("SELECT department_name FROM department WHERE department_id = %s", (department_id,))
        department = cursor.fetchone()
        
        if not department:
            print(f"❌ 科室编号 {department_id} 不存在")
            return False
        
        # 3. 获取当前信息
        current_dept_id = doctor['department_id']
        doctor_name = doctor['name']
        dept_name = department['department_name']
        
        # 4. 检查是否已经是该科室
        if current_dept_id == department_id:
            print(f"⚠️ 医生 {doctor_name} 已经在科室 {dept_name} 中")
            return True
        
        # 5. 更新医生科室
        sql = """
        UPDATE doctor 
        SET department_id = %s, updated_at = NOW() 
        WHERE doctor_id = %s
        """
        cursor.execute(sql, (department_id, doctor_id))
        
        # 6. 输出结果信息
        if current_dept_id:
            # 获取原科室名称
            cursor.execute("SELECT department_name FROM department WHERE department_id = %s", (current_dept_id,))
            old_dept = cursor.fetchone()
            old_dept_name = old_dept['department_name'] if old_dept else "未知科室"
            print(f"✅ 医生科室设置成功！")
            print(f"   医生: {doctor_name} (工号: {doctor_id})")
            print(f"   从: {old_dept_name} → 调入: {dept_name}")
        else:
            print(f"✅ 医生科室设置成功！")
            print(f"   医生: {doctor_name} (工号: {doctor_id})")
            print(f"   分配到: {dept_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置医生科室失败: {e}")
        return False

def remove_doctor_department(cursor, doctor_id):
    """
    移除医生科室（设为未分配状态）
    
    Args:
        cursor: 数据库游标
        doctor_id: 医生工号
    
    Returns:
        bool: 移除是否成功
    """
    try:
        # 检查医生是否存在
        cursor.execute("SELECT name, department_id FROM doctor WHERE doctor_id = %s", (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            print(f"❌ 医生工号 {doctor_id} 不存在")
            return False
        
        # 检查是否已经有科室
        if not doctor['department_id']:
            print(f"⚠️ 医生 {doctor['name']} 已经是未分配状态")
            return True
        
        # 获取当前科室名称
        cursor.execute("SELECT department_name FROM department WHERE department_id = %s", (doctor['department_id'],))
        dept = cursor.fetchone()
        dept_name = dept['department_name'] if dept else "未知科室"
        
        # 更新为NULL
        sql = """
        UPDATE doctor 
        SET department_id = NULL, updated_at = NOW() 
        WHERE doctor_id = %s
        """
        cursor.execute(sql, (doctor_id,))
        
        print(f"✅ 医生科室移除成功！")
        print(f"   医生: {doctor['name']} (工号: {doctor_id})")
        print(f"   从 {dept_name} 移除，现为未分配状态")
        
        return True
        
    except Exception as e:
        print(f"❌ 移除医生科室失败: {e}")
        return False

def set_doctor_position(cursor, doctor_id, position):
    """
    设置医生职称
    
    Args:
        cursor: 数据库游标
        doctor_id: 医生工号
        position: 职称（如：主任医师、副主任医师、主治医师、住院医师等）
    
    Returns:
        bool: 设置是否成功
    """
    try:
        # 1. 检查医生是否存在
        cursor.execute("SELECT name, position FROM doctor WHERE doctor_id = %s", (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            print(f"❌ 医生工号 {doctor_id} 不存在")
            return False
        
        # 2. 获取当前信息
        current_position = doctor['position']
        doctor_name = doctor['name']
        
        # 3. 检查是否已经是该职称
        if current_position == position:
            print(f"⚠️ 医生 {doctor_name} 的职称已经是 '{position}'")
            return True
        
        # 4. 更新医生职称
        sql = """
        UPDATE doctor 
        SET position = %s, updated_at = NOW() 
        WHERE doctor_id = %s
        """
        cursor.execute(sql, (position, doctor_id))
        
        # 5. 输出结果信息
        if current_position:
            print(f"✅ 医生职称设置成功！")
            print(f"   医生: {doctor_name} (工号: {doctor_id})")
            print(f"   职称: {current_position} → {position}")
        else:
            print(f"✅ 医生职称设置成功！")
            print(f"   医生: {doctor_name} (工号: {doctor_id})")
            print(f"   设置职称: {position}")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置医生职称失败: {e}")
        return False

def delete_doctor(cursor, doctor_id):
    """
    删除医生记录
    
    Args:
        cursor: 数据库游标
        doctor_id: 医生工号
    
    Returns:
        bool: 删除是否成功
    """
    try:
        # 检查医生是否存在
        cursor.execute("SELECT name FROM doctor WHERE doctor_id = %s", (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            print(f"❌ 医生工号 {doctor_id} 不存在")
            return False
        
        # 删除医生记录
        sql = "DELETE FROM doctor WHERE doctor_id = %s"
        cursor.execute(sql, (doctor_id,))
        
        print(f"✅ 医生删除成功！")
        print(f"   已删除医生: {doctor['name']} (工号: {doctor_id})")
        
        return True
        
    except Exception as e:
        print(f"❌ 删除医生失败: {e}")
        return False

def remove_doctor_position(cursor, doctor_id):
    """
    移除医生职称（设为未分配状态）
    
    Args:
        cursor: 数据库游标
        doctor_id: 医生工号
    
    Returns:
        bool: 移除是否成功
    """
    try:
        # 1. 检查医生是否存在
        cursor.execute("SELECT name, position FROM doctor WHERE doctor_id = %s", (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            print(f"❌ 医生工号 {doctor_id} 不存在")
            return False
        
        # 2. 检查是否已经有职称
        if not doctor['position']:
            print(f"⚠️ 医生 {doctor['name']} 已经是未分配职称状态")
            return True
        
        # 3. 更新为NULL
        sql = """
        UPDATE doctor 
        SET position = NULL, updated_at = NOW() 
        WHERE doctor_id = %s
        """
        cursor.execute(sql, (doctor_id,))
        
        print(f"✅ 医生职称移除成功！")
        print(f"   医生: {doctor['name']} (工号: {doctor_id})")
        print(f"   职称 '{doctor['position']}' 已移除，现为未分配状态")
        
        return True
        
    except Exception as e:
        print(f"❌ 移除医生职称失败: {e}")
        return False
    
def check_doctor_exists(cursor, doctor_id):
    """
    判断医生ID是否存在
    
    Args:
        cursor: 数据库游标
        doctor_id: 医生工号
    
    Returns:
        bool: 存在返回True，不存在返回False
    """
    try:
        # 查询医生是否存在
        cursor.execute("SELECT doctor_id FROM doctor WHERE doctor_id = %s", (doctor_id,))
        result = cursor.fetchone()
        
        if result:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ 检查医生ID失败: {e}")
        return False