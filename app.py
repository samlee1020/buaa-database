from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import entity.patient as patient_module
import entity.department as department_module
import entity.registration as registration_module
import entity.prescription as prescription_module
import entity.payment as payment_module
import entity.doctor as doctor_module
import entity.drug as drug_module
import setup
import config

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 生产环境请使用强密钥

# 数据库配置
config = {
    'host': config.config['host'],
    'port': config.config['port'],
    'user': config.config['user'],
    'password': config.config['password'],
    'database': config.config['database'],
    'charset': config.config['charset'],
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': config.config['autocommit']
}

# 挂号费用
registration_fee = 50

def get_db_connection():
    """获取数据库连接"""
    connection = pymysql.connect(**config)
    return connection

# 主页 - 角色选择
@app.route('/')
def index():
    return render_template('index.html')

# 患者功能路由
@app.route('/patient')
def patient_home():
    return render_template('patient/index.html')

@app.route('/patient/query', methods=['GET', 'POST'])
def patient_query():
    if request.method == 'POST':
        query_type = request.form.get('query_type')
        query_key = request.form.get('query_key')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if query_type and query_key:
            results = patient_module.query_patient(cursor, **{query_type: query_key})
        else:
            results = patient_module.query_patient(cursor)
        
        cursor.close()
        connection.close()
        
        return render_template('patient/query_result.html', results=results, query_type=query_type, query_key=query_key)
    
    return render_template('patient/query.html')

@app.route('/patient/register', methods=['GET', 'POST'])
def patient_register():
    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        phone_number = request.form.get('phone_number')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # 使用存储过程注册患者
            cursor.callproc('sp_register_patient', [name, gender, phone_number, 0])
            cursor.execute("SELECT @_sp_register_patient_3")
            result = cursor.fetchone()
            patient_id = result['@_sp_register_patient_3']
            
            cursor.close()
            connection.close()
            
            if patient_id:
                flash(f'注册成功！您的病历号是：{patient_id}', 'success')
                return redirect(url_for('patient_login'))
            else:
                flash('注册失败，请重试', 'error')
        except Exception as e:
            flash(f'注册失败：{str(e)}', 'error')
            cursor.close()
            connection.close()
    
    return render_template('patient/register.html')

@app.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        
        try:
            patient_id = int(patient_id)
            connection = get_db_connection()
            cursor = connection.cursor()
            
            result = patient_module.query_patient(cursor, patient_id=patient_id)
            
            if result:
                session['patient_id'] = patient_id
                session['patient_name'] = result[0]['name'] if result else '未知'
                flash(f'登录成功！欢迎 {session["patient_name"]}', 'success')
                return redirect(url_for('patient_dashboard'))
            else:
                flash('病历号不存在，请先注册', 'error')
            
            cursor.close()
            connection.close()
        except ValueError:
            flash('请输入有效的病历号', 'error')
    
    return render_template('patient/login.html')

@app.route('/patient/dashboard')
def patient_dashboard():
    if 'patient_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('patient_login'))
    
    return render_template('patient/dashboard.html')

@app.route('/patient/update_info', methods=['GET', 'POST'])
def patient_update_info():
    if 'patient_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('patient_login'))
    
    if request.method == 'POST':
        update_type = request.form.get('update_type')
        new_value = request.form.get('new_value')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        success = patient_module.update_patient(cursor, session['patient_id'], **{update_type: new_value})
        
        cursor.close()
        connection.close()
        
        if success:
            # 如果更新的是姓名，同步更新session中的患者姓名
            if update_type == 'name':
                session['patient_name'] = new_value
            flash('信息更新成功', 'success')
        else:
            flash('信息更新失败', 'error')
        
        return redirect(url_for('patient_dashboard'))
    
    return render_template('patient/update_info.html')

@app.route('/patient/query_department', methods=['GET', 'POST'])
def patient_query_department():
    department_name = request.form.get('department_name', '') if request.method == 'POST' else ''
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if department_name:
        results = department_module.query_department(cursor, department_name=department_name)
    else:
        results = department_module.query_department(cursor)
    
    cursor.close()
    connection.close()
    
    return render_template('patient/departments.html', results=results, department_name=department_name)

@app.route('/patient/create_registration', methods=['GET', 'POST'])
def patient_create_registration():
    if 'patient_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('patient_login'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if request.method == 'POST':
        department_id = request.form.get('department_id')
        
        if department_id:
            try:
                # 使用存储过程创建挂号
                cursor.callproc('sp_create_registration', [session['patient_id'], int(department_id), 0])
                cursor.execute("SELECT @_sp_create_registration_2")
                result = cursor.fetchone()
                registration_id = result['@_sp_create_registration_2']
                
                if registration_id:
                    flash('挂号成功！', 'success')
                else:
                    flash('挂号失败，请重试', 'error')
            except Exception as e:
                flash(f'挂号失败：{str(e)}', 'error')
        
        cursor.close()
        connection.close()
        return redirect(url_for('patient_dashboard'))
    
    # 获取所有科室
    departments = department_module.query_department(cursor)
    cursor.close()
    connection.close()
    
    return render_template('patient/create_registration.html', departments=departments)

@app.route('/patient/query_registration')
def patient_query_registration():
    if 'patient_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('patient_login'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    results = registration_module.query_registration(cursor, patient_id=session['patient_id'])
    
    cursor.close()
    connection.close()
    
    return render_template('patient/registrations.html', results=results)

@app.route('/patient/query_prescription')
def patient_query_prescription():
    if 'patient_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('patient_login'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    results = prescription_module.query_prescription(cursor, patient_id=session['patient_id'])
    
    cursor.close()
    connection.close()
    
    return render_template('patient/prescriptions.html', results=results)

@app.route('/patient/pay', methods=['GET', 'POST'])
def patient_pay():
    if 'patient_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('patient_login'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if request.method == 'POST':
        payment_id = request.form.get('payment_id')
        
        if payment_id:
            try:
                # 使用存储过程完成缴费
                cursor.callproc('sp_complete_payment', [int(payment_id), 0])
                cursor.execute("SELECT @_sp_complete_payment_1")
                result = cursor.fetchone()
                success = result['@_sp_complete_payment_1']
                
                if success:
                    flash('缴费成功！', 'success')
                else:
                    flash('缴费失败，请重试', 'error')
            except Exception as e:
                flash(f'缴费失败：{str(e)}', 'error')
        
        cursor.close()
        connection.close()
        return redirect(url_for('patient_dashboard'))
    
    # 获取待缴费信息
    results = payment_module.query_payment(cursor, patient_id=session['patient_id'], time_is_null=True)
    
    cursor.close()
    connection.close()
    
    return render_template('patient/pay.html', results=results)

@app.route('/patient/logout')
def patient_logout():
    session.pop('patient_id', None)
    session.pop('patient_name', None)
    flash('已退出登录', 'success')
    return redirect(url_for('patient_home'))

@app.route('/patient/delete_account')
def patient_delete_account():
    if 'patient_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('patient_login'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # 删除患者（根据外键约束，会级联删除相关记录）
        success = patient_module.delete_patient(cursor, session['patient_id'])
        
        if success:
            # 清除会话
            session.pop('patient_id', None)
            session.pop('patient_name', None)
            flash('病历删除成功！所有相关信息已清除', 'success')
            cursor.close()
            connection.close()
            return redirect(url_for('patient_home'))
        else:
            flash('病历删除失败，请重试', 'error')
            cursor.close()
            connection.close()
            return redirect(url_for('patient_dashboard'))
            
    except Exception as e:
        flash(f'删除病历时发生错误: {e}', 'error')
        cursor.close()
        connection.close()
        return redirect(url_for('patient_dashboard'))

# 医生功能路由
@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        
        try:
            doctor_id = int(doctor_id)
            connection = get_db_connection()
            cursor = connection.cursor()
            
            if doctor_module.check_doctor_exists(cursor, doctor_id):
                session['doctor_id'] = doctor_id
                doctor_info = doctor_module.query_doctor(cursor, doctor_id=doctor_id)
                session['doctor_name'] = doctor_info[0]['name'] if doctor_info else '未知'
                flash(f'登录成功！欢迎 {session["doctor_name"]} 医生', 'success')
                return redirect(url_for('doctor_dashboard'))
            else:
                flash('工号不存在，请联系管理员', 'error')
            
            cursor.close()
            connection.close()
        except ValueError:
            flash('请输入有效的工号', 'error')
    
    return render_template('doctor/login.html')

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'doctor_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('doctor_login'))
    
    return render_template('doctor/dashboard.html')

@app.route('/doctor/registrations')
def doctor_registrations():
    if 'doctor_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('doctor_login'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # 查询未出诊和出诊中的挂号
    results = []
    pending_results = registration_module.query_registration(cursor, doctor_id=session['doctor_id'], status='pending')
    in_progress_results = registration_module.query_registration(cursor, doctor_id=session['doctor_id'], status='in_progress')
    
    # 合并结果
    if pending_results:
        results.extend(pending_results)
    if in_progress_results:
        results.extend(in_progress_results)
    
    # 获取药品列表用于处方开具
    drugs = drug_module.query_drug(cursor)
    
    cursor.close()
    connection.close()
    
    return render_template('doctor/registrations.html', results=results, drugs=drugs)

@app.route('/doctor/complete_registration', methods=['POST'])
def doctor_complete_registration():
    if 'doctor_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('doctor_login'))
    
    registration_id = request.form.get('registration_id')
    
    if not registration_id:
        flash('请提供挂号编号', 'error')
        return redirect(url_for('doctor_registrations'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # 检查该挂号是否属于当前医生
        cursor.execute("SELECT doctor_id FROM registration WHERE registration_id = %s", (registration_id,))
        registration = cursor.fetchone()
        
        if not registration:
            flash('挂号记录不存在', 'error')
        elif registration['doctor_id'] != session['doctor_id']:
            flash('您无权操作此挂号记录', 'error')
        else:
            # 更新挂号状态为已出诊
            success = registration_module.update_registration_status(cursor, int(registration_id), 'completed')
            
            if success:
                flash('就诊完成！该挂号已标记为已出诊', 'success')
            else:
                flash('就诊完成操作失败，请重试', 'error')
        
        cursor.close()
        connection.close()
        return redirect(url_for('doctor_registrations'))
        
    except Exception as e:
        flash(f'操作失败：{str(e)}', 'error')
        cursor.close()
        connection.close()
        return redirect(url_for('doctor_registrations'))

@app.route('/doctor/create_prescription', methods=['POST'])
def doctor_create_prescription():
    if 'doctor_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('doctor_login'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    registration_id = request.form.get('registration_id')
    drug_id = request.form.get('drug_id')
    quantity = request.form.get('quantity')
    
    if registration_id and drug_id and quantity:
        try:
            # 检查该挂号是否属于当前医生
            cursor.execute("SELECT doctor_id FROM registration WHERE registration_id = %s", (registration_id,))
            registration = cursor.fetchone()
            
            if not registration:
                flash('挂号记录不存在', 'error')
            elif registration['doctor_id'] != session['doctor_id']:
                flash('您无权操作此挂号记录', 'error')
            else:
                # 使用存储过程开具处方（现在会自动创建缴费记录）
                cursor.callproc('sp_create_prescription', [
                    int(registration_id), 
                    int(drug_id), 
                    int(quantity), 
                    0
                ])
                cursor.execute("SELECT @_sp_create_prescription_3")
                result = cursor.fetchone()
                prescription_id = result['@_sp_create_prescription_3']
                
                if prescription_id:
                    flash('处方开具成功！', 'success')
                else:
                    flash('处方开具失败，请重试', 'error')
        except Exception as e:
            flash(f'处方开具失败：{str(e)}', 'error')
    else:
        flash('请填写完整信息', 'error')
    
    cursor.close()
    connection.close()
    return redirect(url_for('doctor_registrations'))

@app.route('/doctor/logout')
def doctor_logout():
    session.pop('doctor_id', None)
    session.pop('doctor_name', None)
    flash('已退出登录', 'success')
    return redirect(url_for('index'))

# 管理员功能路由
@app.route('/admin')
def admin_home():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # 获取统计数据
    stats = {}
    
    # 患者总数
    try:
        cursor.execute("SELECT COUNT(*) as count FROM patient")
        stats['patient_count'] = cursor.fetchone()['count']
    except:
        stats['patient_count'] = 0
    
    # 医生总数
    try:
        cursor.execute("SELECT COUNT(*) as count FROM doctor")
        stats['doctor_count'] = cursor.fetchone()['count']
    except:
        stats['doctor_count'] = 0
    
    # 今日挂号数（简化处理，获取所有挂号数）
    try:
        cursor.execute("SELECT COUNT(*) as count FROM registration")
        stats['registration_count'] = cursor.fetchone()['count']
    except:
        stats['registration_count'] = 0
    
    # 药品种类数
    try:
        cursor.execute("SELECT COUNT(*) as count FROM drug")
        stats['drug_count'] = cursor.fetchone()['count']
    except:
        stats['drug_count'] = 0
    
    cursor.close()
    connection.close()
    
    return render_template('admin/index.html', stats=stats)

@app.route('/admin/departments', methods=['GET', 'POST'])
def admin_departments():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name')
            if name:
                department_module.create_department(cursor, name)
                flash('科室添加成功！', 'success')
        elif action == 'update':
            department_id = request.form.get('department_id')
            new_name = request.form.get('new_name')
            if department_id and new_name:
                department_module.update_department(cursor, department_id, new_name)
                flash('科室更新成功！', 'success')
        elif action == 'delete':
            department_id = request.form.get('department_id')
            if department_id:
                success = department_module.delete_department(cursor, int(department_id))
                if success:
                    flash('科室删除成功！', 'success')
                else:
                    flash('科室删除失败，请检查是否有医生关联该科室', 'error')
    
    departments = department_module.query_department(cursor)
    cursor.close()
    connection.close()
    
    return render_template('admin/departments.html', departments=departments)

@app.route('/admin/process_registration', methods=['GET', 'POST'])
def admin_process_registration():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if request.method == 'POST':
        registration_id = request.form.get('registration_id')
        doctor_id = request.form.get('doctor_id')
        
        if registration_id and doctor_id:
            try:
                # 使用存储过程处理挂号
                cursor.callproc('sp_process_registration', [int(registration_id), int(doctor_id), 0])
                cursor.execute("SELECT @_sp_process_registration_2")
                result = cursor.fetchone()
                success = result['@_sp_process_registration_2']
                
                if success:
                    flash('挂号受理成功！', 'success')
                else:
                    flash('挂号受理失败', 'error')
            except Exception as e:
                flash(f'挂号受理失败：{str(e)}', 'error')
    
    # 获取未受理的挂号
    registrations = registration_module.query_registration(cursor, unassigned_only=True)
    # 获取医生列表
    doctors = doctor_module.query_doctor(cursor)
    
    cursor.close()
    connection.close()
    
    return render_template('admin/process_registration.html', 
                         registrations=registrations, doctors=doctors)

@app.route('/admin/doctors', methods=['GET', 'POST'])
def admin_doctors():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name')
            gender = request.form.get('gender')
            phone_number = request.form.get('phone_number')
            if name and gender and phone_number:
                doctor_module.register_doctor(cursor, name, gender, phone_number)
                flash('医生添加成功！', 'success')
        elif action == 'update_department':
            doctor_id = request.form.get('doctor_id')
            department_id = request.form.get('department_id')
            if doctor_id and department_id:
                doctor_module.set_doctor_department(cursor, int(doctor_id), int(department_id))
                flash('医生科室更新成功！', 'success')
        elif action == 'update_position':
            doctor_id = request.form.get('doctor_id')
            position = request.form.get('position')
            if doctor_id and position:
                doctor_module.set_doctor_position(cursor, int(doctor_id), position)
                flash('医生职称更新成功！', 'success')
        elif action == 'delete':
            doctor_id = request.form.get('doctor_id')
            if doctor_id:
                success = doctor_module.delete_doctor(cursor, int(doctor_id))
                if success:
                    flash('医生删除成功！', 'success')
                else:
                    flash('医生删除失败，请重试', 'error')
    
    doctors = doctor_module.query_doctor(cursor)
    departments = department_module.query_department(cursor)
    
    cursor.close()
    connection.close()
    
    return render_template('admin/doctors.html', doctors=doctors, departments=departments)

@app.route('/admin/drugs', methods=['GET', 'POST'])
def admin_drugs():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name')
            quantity = request.form.get('quantity')
            price = request.form.get('price')
            if name and quantity and price:
                drug_module.add_drug(cursor, name, int(quantity), float(price))
                flash('药品添加成功！', 'success')
        elif action == 'update':
            drug_id = request.form.get('drug_id')
            update_type = request.form.get('update_type')
            new_value = request.form.get('new_value')
            if drug_id and update_type and new_value:
                # 映射参数名：price -> drug_price, stored_quantity -> stored_quantity
                param_mapping = {'price': 'drug_price', 'stored_quantity': 'stored_quantity'}
                mapped_type = param_mapping.get(update_type, update_type)
                drug_module.update_drug_info(cursor, int(drug_id), **{mapped_type: new_value})
                flash('药品信息更新成功！', 'success')
        elif action == 'delete':
            drug_id = request.form.get('drug_id')
            if drug_id:
                success = drug_module.delete_drug(cursor, int(drug_id))
                if success:
                    flash('药品删除成功！', 'success')
                else:
                    flash('药品删除失败，请检查是否有处方关联该药品', 'error')
    
    drugs = drug_module.query_drug(cursor)
    
    cursor.close()
    connection.close()
    
    return render_template('admin/drugs.html', drugs=drugs)

@app.route('/admin/registrations', methods=['GET', 'POST'])
def admin_registrations():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'delete':
            registration_id = request.form.get('registration_id')
            if registration_id:
                success = registration_module.delete_registration(cursor, int(registration_id))
                if success:
                    flash('挂号删除成功！', 'success')
                else:
                    flash('挂号删除失败，请检查是否有处方关联该挂号', 'error')
    
    # 获取所有挂号记录
    registrations = registration_module.query_registration(cursor)
    
    cursor.close()
    connection.close()
    
    return render_template('admin/registrations.html', registrations=registrations)

@app.route('/admin/prescriptions', methods=['GET', 'POST'])
def admin_prescriptions():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'delete':
            prescription_id = request.form.get('prescription_id')
            if prescription_id:
                success = prescription_module.delete_prescription(cursor, int(prescription_id))
                if success:
                    flash('处方删除成功！', 'success')
                else:
                    flash('处方删除失败，请重试', 'error')
    
    # 获取所有处方记录
    prescriptions = prescription_module.query_prescription(cursor)
    
    cursor.close()
    connection.close()
    
    return render_template('admin/prescriptions.html', prescriptions=prescriptions)

@app.route('/admin/tables')
def admin_tables():
    table_name = request.args.get('table', '')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if table_name:
        results = []
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            results = cursor.fetchall()
        except Exception as e:
            flash(f'查询表 {table_name} 失败: {e}', 'error')
    else:
        # 显示所有表
        tables = ['patient', 'department', 'doctor', 'drug', 'payment', 'registration', 'prescription']
        all_results = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT * FROM {table}")
                all_results[table] = cursor.fetchall()
            except Exception as e:
                all_results[table] = []
        
        cursor.close()
        connection.close()
        return render_template('admin/tables.html', all_results=all_results, selected_table='all')
    
    cursor.close()
    connection.close()
    return render_template('admin/tables.html', results=results, selected_table=table_name)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'reset_tables':
            connection = get_db_connection()
            cursor = connection.cursor()
            
            try:
                # 重置表
                setup.drop_all_tables_for_testing(cursor)
                setup.create_table(cursor)
                flash('数据库重置成功！所有表已重建', 'success')
                department_module.create_department(cursor, '内科') # 内科id=1
                department_module.create_department(cursor, '外科') # 外科id=2
                doctor_module.register_doctor(cursor, '张内科医生', '男', '13812345678', '主任医师', 1) 
                doctor_module.register_doctor(cursor, '李内科医生', '女', '13898765432', '副主任医师', 1)
                doctor_module.register_doctor(cursor, '陈外科医生', '女', '13898765432', '副主任医师', 2) 
                doctor_module.register_doctor(cursor, '王外科医师', '男', '13856789123', '主任医师', 2)
                drug_module.add_drug(cursor, '阿司匹林', 100, 5.5)
                drug_module.add_drug(cursor, '头孢呋辛', 100, 9.5)
                patient_module.register_patient(cursor, '张三', '男', '13812345678')
                patient_module.register_patient(cursor, '王五', '男', '13856789123')
            except Exception as e:
                flash(f'数据库重置失败: {e}', 'error')
            
            cursor.close()
            connection.close()
    
    return render_template('admin/settings.html', config=config)

if __name__ == '__main__':
    setup.create_table(get_db_connection().cursor())
    app.run(debug=True, host='0.0.0.0', port=8080)
