import pymysql
import datetime

def create_payment(cursor, patient_id, price, time=None):
    """
    创建缴费记录
    
    Args:
        cursor: 数据库游标
        patient_id: 病历号
        price: 缴费价格
        time: 缴费时间（可选，默认为当前时间）
    
    Returns:
        int: 新创建的缴费号，失败返回None
    """
    try:
        # 插入新缴费记录
        sql = """
        INSERT INTO payment (patient_id, price, time, created_at) 
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(sql, (patient_id, price, time))
        
        # 获取刚插入的缴费号
        cursor.execute("SELECT LAST_INSERT_ID()")
        result = cursor.fetchone()
        
        if isinstance(result, tuple):
            payment_id = result[0]
        else:
            payment_id = result['LAST_INSERT_ID()']
        
        print(f"✅ 缴费记录创建成功！缴费号: {payment_id}")
        return payment_id
        
    except Exception as e:
        print(f"❌ 创建缴费记录失败: {e}")
        return None

def query_payment(cursor, payment_id=None, patient_id=None, time_is_null=False):
    """
    查询缴费信息
    
    Args:
        cursor: 数据库游标
        payment_id: 缴费号（可选）
        patient_id: 病历号（可选）
        time_is_null: 是否只查询缴费时间为NULL的记录（可选，默认为False）
    
    Returns:
        list: 查询结果列表
    """
    try:
        # 构建查询条件
        conditions = []
        params = []
        
        if payment_id:
            conditions.append("payment_id = %s")
            params.append(payment_id)
        
        if patient_id:
            conditions.append("patient_id = %s")
            params.append(patient_id)
            
        if time_is_null:
            conditions.append("time IS NULL")
        
        # 构建SQL查询
        if not conditions:
            sql = "SELECT * FROM payment ORDER BY payment_id"
        else:
            sql = f"SELECT * FROM payment WHERE {' AND '.join(conditions)} ORDER BY payment_id"
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # 输出查询结果
        print(f"\n🔍 查询到 {len(results)} 条缴费记录")
        print("-" * 120)
        print(f"{'缴费号':<10} {'病历号':<10} {'缴费价格':<12} {'缴费时间':<20} {'创建时间':<20}")
        print("-" * 120)
        
        if results:
            for payment in results:
                payment_time = str(payment['time']) if payment['time'] else 'NULL'
                created_time = str(payment['created_at']) if payment['created_at'] else 'NULL'
                
                print(f"{payment['payment_id']:<10} {payment['patient_id']:<10} {payment['price']:<12} "
                      f"{payment_time:<20} {created_time:<20}")
        else:
            print("  没有找到匹配的缴费记录")
        
        print("-" * 120)
        
        return results
        
    except Exception as e:
        print(f"❌ 查询缴费记录失败: {e}")
        return []

def complete_payment(cursor, payment_id):
    """
    完成缴费操作，将缴费时间设置为当前时间
    
    Args:
        cursor: 数据库游标
        payment_id: 缴费号
    
    Returns:
        bool: 缴费操作是否成功
    """
    try:
        # 1. 检查缴费记录是否存在
        if not check_payment_exists(cursor, payment_id):
            print(f"❌ 缴费失败：缴费号 {payment_id} 不存在")
            return False
        
        # 2. 查询当前缴费记录信息
        cursor.execute("SELECT patient_id, price, time FROM payment WHERE payment_id = %s", (payment_id,))
        payment = cursor.fetchone()
        
        if not payment:
            print(f"❌ 缴费失败：缴费号 {payment_id} 的记录不存在")
            return False
        
        # 3. 检查是否已经缴费过
        if payment['time']:
            print(f"⚠️ 缴费号 {payment_id} 已经缴费过，缴费时间: {payment['time']}")
            return True
        
        # 4. 更新缴费时间
        sql = """
        UPDATE payment 
        SET time = NOW(), updated_at = NOW() 
        WHERE payment_id = %s
        """
        cursor.execute(sql, (payment_id,))
        
        # 5. 查询并打印详细信息
        # 获取病人姓名
        cursor.execute("SELECT name FROM patient WHERE patient_id = %s", (payment['patient_id'],))
        patient = cursor.fetchone()
        patient_name = patient['name'] if patient else "未知病人"
        
        print(f"✅ 缴费成功！")
        print(f"   缴费号: {payment_id}")
        print(f"   病人: {patient_name} (病历号: {payment['patient_id']})")
        print(f"   缴费金额: {payment['price']} 元")
        print(f"   缴费时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 缴费失败: {e}")
        return False

def check_payment_exists(cursor, payment_id):
    """
    判断缴费ID是否存在
    
    Args:
        cursor: 数据库游标
        payment_id: 缴费号
    
    Returns:
        bool: 存在返回True，不存在返回False
    """
    try:
        # 查询缴费记录是否存在
        cursor.execute("SELECT payment_id FROM payment WHERE payment_id = %s", (payment_id,))
        result = cursor.fetchone()
        
        if result:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ 检查缴费ID失败: {e}")
        return False


