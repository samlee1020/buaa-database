import pymysql
import entity.registration as registration_module
import entity.drug as drug_module
import entity.payment as payment_module

def create_prescription(cursor, registration_id, drug_id, quantity, payment_id):
    """
    开具新处方
    
    Args:
        cursor: 数据库游标
        registration_id: 挂号编号
        drug_id: 药品编号
        quantity: 药品数量
        payment_id: 缴费号
    
    Returns:
        int: 新创建的处方号，失败返回None
    """
    try:
        # 1. 检查挂号是否存在
        if not registration_module.check_registration_exists(cursor, registration_id):
            print(f"❌ 开具处方失败：挂号编号 {registration_id} 不存在")
            return None

        # 2. 检查药品是否存在
        if not drug_module.check_drug_exists(cursor, drug_id):
            print(f"❌ 开具处方失败：药品编号 {drug_id} 不存在")
            return None

        # 3. 检查缴费记录是否存在
        if not payment_module.check_payment_exists(cursor, payment_id):
            print(f"❌ 开具处方失败：缴费号 {payment_id} 不存在")
            return None
        
        # 4. 检查药品库存是否足够
        cursor.execute("SELECT stored_quantity FROM drug WHERE drug_id = %s", (drug_id,))
        drug = cursor.fetchone()
        if not drug or drug['stored_quantity'] < quantity:
            print(f"❌ 开具处方失败：药品库存不足。当前库存: {drug['stored_quantity'] if drug else 0}, 需求: {quantity}")
            return None

        # 5. 插入新处方记录
        sql = """
        INSERT INTO prescription (registration_id, drug_id, quantity, payment_id, created_at) 
        VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(sql, (registration_id, drug_id, quantity, payment_id))
        
        # 6. 获取刚插入的处方号
        cursor.execute("SELECT LAST_INSERT_ID()")
        result = cursor.fetchone()
        
        if isinstance(result, tuple):
            prescription_id = result[0]
        else:
            prescription_id = result['LAST_INSERT_ID()']
        
        # 7. 查询并打印详细信息
        # 获取病人姓名
        cursor.execute("SELECT p.name FROM registration r JOIN patient p ON r.patient_id = p.patient_id WHERE r.registration_id = %s", (registration_id,))
        patient = cursor.fetchone()
        patient_name = patient['name'] if patient else "未知病人"

        # 获取药品名称
        cursor.execute("SELECT drug_name FROM drug WHERE drug_id = %s", (drug_id,))
        drug_info = cursor.fetchone()
        drug_name = drug_info['drug_name'] if drug_info else "未知药品"
        
        print(f"✅ 处方开具成功！")
        print(f"   处方号: {prescription_id}")
        print(f"   病人: {patient_name} (挂号号: {registration_id})")
        print(f"   药品: {drug_name} (药品ID: {drug_id})")
        print(f"   数量: {quantity}")
        print(f"   关联缴费号: {payment_id}")
        
        return prescription_id
        
    except Exception as e:
        print(f"❌ 开具处方失败: {e}")
        return None

def check_prescription_exists(cursor, prescription_id):
    """
    判断处方ID是否存在
    
    Args:
        cursor: 数据库游标
        prescription_id: 处方号
    
    Returns:
        bool: 存在返回True，不存在返回False
    """
    try:
        # 查询处方是否存在
        cursor.execute("SELECT prescription_id FROM prescription WHERE prescription_id = %s", (prescription_id,))
        result = cursor.fetchone()
        
        if result:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ 检查处方ID失败: {e}")
        return False
    
def delete_prescription(cursor, prescription_id):
    """
    删除处方记录
    
    Args:
        cursor: 数据库游标
        prescription_id: 处方号
    
    Returns:
        bool: 删除是否成功
    """
    try:
        # 检查处方是否存在
        cursor.execute("SELECT p.*, r.patient_id, d.drug_name FROM prescription p JOIN registration r ON p.registration_id = r.registration_id JOIN drug d ON p.drug_id = d.drug_id WHERE p.prescription_id = %s", (prescription_id,))
        prescription = cursor.fetchone()
        
        if not prescription:
            print(f"❌ 处方号 {prescription_id} 不存在")
            return False
        
        # 删除处方记录
        sql = "DELETE FROM prescription WHERE prescription_id = %s"
        cursor.execute(sql, (prescription_id,))
        
        print(f"✅ 处方删除成功！")
        print(f"   已删除处方: 编号 {prescription_id}")
        print(f"   挂号号: {prescription['registration_id']}")
        print(f"   药品: {prescription['drug_name']} (药品ID: {prescription['drug_id']})")
        print(f"   数量: {prescription['quantity']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 删除处方失败: {e}")
        return False

def query_prescription(cursor, prescription_id=None, registration_id=None, drug_id=None, payment_id=None, patient_id=None):
    """
    查询处方信息
    
    Args:
        cursor: 数据库游标
        prescription_id: 处方号（可选）
        registration_id: 挂号编号（可选）
        drug_id: 药品编号（可选）
        payment_id: 缴费号（可选）
        patient_id: 患者ID（可选）
    
    Returns:
        list: 查询结果列表
    """
    try:
        # 构建查询条件
        conditions = []
        params = []
        
        if prescription_id:
            conditions.append("p.prescription_id = %s")
            params.append(prescription_id)
        
        if registration_id:
            conditions.append("p.registration_id = %s")
            params.append(registration_id)
            
        if drug_id:
            conditions.append("p.drug_id = %s")
            params.append(drug_id)

        if payment_id:
            conditions.append("p.payment_id = %s")
            params.append(payment_id)
            
        if patient_id:
            conditions.append("r.patient_id = %s")
            params.append(patient_id)
        
        # 构建SQL查询，关联查询获取完整信息（包含缴费状态）
        sql = """
        SELECT 
            p.prescription_id, p.registration_id, p.drug_id, p.quantity, p.payment_id, p.created_at,
            r.patient_id, pat.name as patient_name,
            d.drug_name, d.drug_price,
            doc.name as doctor_name,
            dept.department_name,
            pay.time as payment_time  -- 缴费时间，NULL表示未缴费
        FROM prescription p
        LEFT JOIN registration r ON p.registration_id = r.registration_id
        LEFT JOIN patient pat ON r.patient_id = pat.patient_id
        LEFT JOIN drug d ON p.drug_id = d.drug_id
        LEFT JOIN doctor doc ON r.doctor_id = doc.doctor_id
        LEFT JOIN department dept ON r.department_id = dept.department_id
        LEFT JOIN payment pay ON p.payment_id = pay.payment_id  -- 关联缴费表
        """
        
        if conditions:
            sql += f" WHERE {' AND '.join(conditions)}"
        
        sql += " ORDER BY p.prescription_id"
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # 输出查询结果
        print(f"\n🔍 查询到 {len(results)} 条处方记录")
        print("-" * 120)
        print(f"{'处方号':<10} {'患者':<15} {'科室':<10} {'医生':<10} {'药品':<15} {'数量':<8} {'单价':<8} {'总价':<10} {'创建时间':<20}")
        print("-" * 120)
        
        if results:
            for pre in results:
                created_time = str(pre['created_at']) if pre['created_at'] else 'NULL'
                total_price = pre['drug_price'] * pre['quantity'] if pre['drug_price'] else 0
                
                print(f"{pre['prescription_id']:<10} {pre['patient_name'] or '未知':<15} "
                      f"{pre['department_name'] or '未知':<10} {pre['doctor_name'] or '未知':<10} "
                      f"{pre['drug_name'] or '未知':<15} {pre['quantity']:<8} "
                      f"{pre['drug_price'] or 0:<8.2f} {total_price:<10.2f} {created_time:<20}")
        else:
            print("  没有找到匹配的处方记录")
        
        print("-" * 120)
        
        return results
        
    except Exception as e:
        print(f"❌ 查询处方失败: {e}")
        return []
