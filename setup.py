import pymysql

def create_table(cursor):
    
    # 1. 创建病人表 (patient)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient (
            patient_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '病历号',
            name VARCHAR(50) NOT NULL COMMENT '姓名',
            gender ENUM('男', '女') NOT NULL COMMENT '性别',
            phone_number VARCHAR(20) NOT NULL COMMENT '电话号码',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_patient_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='病人信息表'
    """)
    
    # 2. 创建科室表 (department)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS department (
            department_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '科室编号',
            department_name VARCHAR(100) NOT NULL COMMENT '科室名称',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科室信息表'
    """)
    
    # 3. 创建医生表 (doctor)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor (
            doctor_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '医生工号',
            name VARCHAR(50) NOT NULL COMMENT '姓名',
            gender ENUM('男', '女') NOT NULL COMMENT '性别',
            phone_number VARCHAR(20) NOT NULL COMMENT '电话号码',
            position VARCHAR(50) NULL COMMENT '职称',
            department_id INT NULL COMMENT '科室编号',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL,
            INDEX idx_doctor_name (name),
            INDEX idx_doctor_dept_pos (department_id, position)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医生信息表'
    """)
    
    # 4. 创建药品表 (drug)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug (
            drug_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '药品编号',
            drug_name VARCHAR(100) NOT NULL COMMENT '药品名称',
            stored_quantity INT NOT NULL DEFAULT 0 COMMENT '药品库存数量',
            drug_price DECIMAL(10,2) NOT NULL COMMENT '药品单价',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品信息表'
    """)
    
    # 5. 创建缴费表 (payment)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment (
            payment_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '缴费号',
            patient_id INT NOT NULL COMMENT '病历号',
            price DECIMAL(10,2) NOT NULL COMMENT '缴费价格',
            time TIMESTAMP NULL COMMENT '缴费时间',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            FOREIGN KEY (patient_id) REFERENCES patient(patient_id) ON DELETE CASCADE,
            INDEX idx_payment_patient (patient_id),
            INDEX idx_payment_patient_time (patient_id, time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缴费记录表'
    """)
    
    # 6. 创建挂号表 (registration)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registration (
            registration_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '挂号编号',
            patient_id INT NOT NULL COMMENT '病历号',
            department_id INT NOT NULL COMMENT '科室编号',
            doctor_id INT NULL COMMENT '医生工号',
            payment_id INT NULL COMMENT '缴费号',
            status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending' COMMENT '就诊状态：pending-未出诊, in_progress-出诊中, completed-已出诊',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            FOREIGN KEY (patient_id) REFERENCES patient(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE RESTRICT,
            FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id) ON DELETE SET NULL,
            FOREIGN KEY (payment_id) REFERENCES payment(payment_id) ON DELETE SET NULL,
            INDEX idx_registration_doctor (doctor_id),
            INDEX idx_registration_patient (patient_id),
            INDEX idx_registration_doctor_patient (doctor_id, patient_id),
            INDEX idx_registration_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='挂号记录表'
    """)
    
    # 7. 创建处方表 (prescription)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescription (
            prescription_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '处方号',
            registration_id INT NOT NULL COMMENT '挂号编号',
            drug_id INT NOT NULL COMMENT '药品编号',
            quantity INT NOT NULL COMMENT '药品数量',
            payment_id INT NOT NULL COMMENT '缴费号',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            FOREIGN KEY (registration_id) REFERENCES registration(registration_id) ON DELETE CASCADE,
            FOREIGN KEY (drug_id) REFERENCES drug(drug_id) ON DELETE RESTRICT,
            FOREIGN KEY (payment_id) REFERENCES payment(payment_id) ON DELETE CASCADE,
            INDEX idx_prescription_registration (registration_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='处方记录表'
    """)
    
    # 8. 创建存储过程和触发器
    create_stored_procedures(cursor)
    create_triggers(cursor)

def create_stored_procedures(cursor):
    """
    创建存储过程封装常用操作
    """
    # 1. 患者注册存储过程
    cursor.execute("""
        DROP PROCEDURE IF EXISTS sp_register_patient;
    """)
    cursor.execute("""
        CREATE PROCEDURE sp_register_patient(
            IN p_name VARCHAR(50),
            IN p_gender ENUM('男', '女'),
            IN p_phone_number VARCHAR(20),
            OUT p_patient_id INT
        )
        BEGIN
            DECLARE EXIT HANDLER FOR SQLEXCEPTION
            BEGIN
                ROLLBACK;
                SET p_patient_id = NULL;
            END;
            
            START TRANSACTION;
            
            INSERT INTO patient (name, gender, phone_number, created_at) 
            VALUES (p_name, p_gender, p_phone_number, NOW());
            
            SET p_patient_id = LAST_INSERT_ID();
            
            COMMIT;
        END;
    """)
    
    # 2. 创建挂号存储过程
    cursor.execute("""
        DROP PROCEDURE IF EXISTS sp_create_registration;
    """)
    cursor.execute("""
        CREATE PROCEDURE sp_create_registration(
            IN p_patient_id INT,
            IN p_department_id INT,
            OUT p_registration_id INT
        )
        BEGIN
            DECLARE v_payment_id INT;
            DECLARE EXIT HANDLER FOR SQLEXCEPTION
            BEGIN
                ROLLBACK;
                SET p_registration_id = NULL;
            END;
            
            START TRANSACTION;
            
            -- 检查患者是否存在
            IF NOT EXISTS (SELECT 1 FROM patient WHERE patient_id = p_patient_id) THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '患者不存在';
            END IF;
            
            -- 检查科室是否存在
            IF NOT EXISTS (SELECT 1 FROM department WHERE department_id = p_department_id) THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '科室不存在';
            END IF;
            
            -- 创建缴费记录（挂号费50元，time为NULL表示未缴费）
            INSERT INTO payment (patient_id, price, time, created_at) 
            VALUES (p_patient_id, 50.00, NULL, NOW());
            
            SET v_payment_id = LAST_INSERT_ID();
            
            -- 创建挂号记录，包含payment_id
            INSERT INTO registration (patient_id, department_id, payment_id, created_at) 
            VALUES (p_patient_id, p_department_id, v_payment_id, NOW());
            
            SET p_registration_id = LAST_INSERT_ID();
            
            COMMIT;
        END;
    """)
    
    # 3. 处理挂号存储过程
    cursor.execute("""
        DROP PROCEDURE IF EXISTS sp_process_registration;
    """)
    cursor.execute("""
        CREATE PROCEDURE sp_process_registration(
            IN p_registration_id INT,
            IN p_doctor_id INT,
            OUT p_success BOOLEAN
        )
        BEGIN
            DECLARE v_department_id INT;
            DECLARE v_doctor_department_id INT;
            
            DECLARE EXIT HANDLER FOR SQLEXCEPTION
            BEGIN
                ROLLBACK;
                SET p_success = FALSE;
            END;
            
            START TRANSACTION;
            
            -- 检查挂号是否存在
            SELECT department_id INTO v_department_id 
            FROM registration 
            WHERE registration_id = p_registration_id;
            
            IF v_department_id IS NULL THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '挂号不存在';
            END IF;
            
            -- 检查医生是否存在
            SELECT department_id INTO v_doctor_department_id 
            FROM doctor 
            WHERE doctor_id = p_doctor_id;
            
            IF v_doctor_department_id IS NULL THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '医生不存在';
            END IF;
            
            -- 检查医生是否属于该科室
            IF v_doctor_department_id != v_department_id THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '医生不属于该科室';
            END IF;
            
            -- 更新挂号记录（updated_at由触发器自动更新）
            UPDATE registration 
            SET doctor_id = p_doctor_id
            WHERE registration_id = p_registration_id;
            
            SET p_success = TRUE;
            
            COMMIT;
        END;
    """)
    
    # 4. 开具处方存储过程
    cursor.execute("""
        DROP PROCEDURE IF EXISTS sp_create_prescription;
    """)
    cursor.execute("""
        CREATE PROCEDURE sp_create_prescription(
            IN p_registration_id INT,
            IN p_drug_id INT,
            IN p_quantity INT,
            OUT p_prescription_id INT
        )
        BEGIN
            DECLARE v_drug_quantity INT;
            DECLARE v_patient_id INT;
            DECLARE v_drug_price DECIMAL(10,2);
            DECLARE v_total_price DECIMAL(10,2);
            DECLARE v_payment_id INT;
            
            DECLARE EXIT HANDLER FOR SQLEXCEPTION
            BEGIN
                ROLLBACK;
                SET p_prescription_id = NULL;
            END;
            
            START TRANSACTION;
            
            -- 检查挂号是否存在
            IF NOT EXISTS (SELECT 1 FROM registration WHERE registration_id = p_registration_id) THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '挂号不存在';
            END IF;
            
            -- 获取挂号对应的患者ID
            SELECT patient_id INTO v_patient_id 
            FROM registration WHERE registration_id = p_registration_id;
            
            -- 检查药品是否存在和库存
            SELECT stored_quantity, drug_price INTO v_drug_quantity, v_drug_price 
            FROM drug WHERE drug_id = p_drug_id;
            
            IF v_drug_quantity IS NULL THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '药品不存在';
            END IF;
            
            IF v_drug_quantity < p_quantity THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '药品库存不足';
            END IF;
            
            -- 计算药品总价
            SET v_total_price = v_drug_price * p_quantity;
            
            -- 创建药品费用缴费记录（time为NULL表示未缴费）
            INSERT INTO payment (patient_id, price, time, created_at) 
            VALUES (v_patient_id, v_total_price, NULL, NOW());
            
            SET v_payment_id = LAST_INSERT_ID();
            
            -- 插入处方记录（库存更新由触发器自动处理）
            INSERT INTO prescription (registration_id, drug_id, quantity, payment_id, created_at) 
            VALUES (p_registration_id, p_drug_id, p_quantity, v_payment_id, NOW());
            
            SET p_prescription_id = LAST_INSERT_ID();
            
            COMMIT;
        END;
    """)
    
    # 5. 完成缴费存储过程
    cursor.execute("""
        DROP PROCEDURE IF EXISTS sp_complete_payment;
    """)
    cursor.execute("""
        CREATE PROCEDURE sp_complete_payment(
            IN p_payment_id INT,
            OUT p_success BOOLEAN
        )
        BEGIN
            DECLARE EXIT HANDLER FOR SQLEXCEPTION
            BEGIN
                ROLLBACK;
                SET p_success = FALSE;
            END;
            
            START TRANSACTION;
            
            -- 检查缴费记录是否存在
            IF NOT EXISTS (SELECT 1 FROM payment WHERE payment_id = p_payment_id) THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '缴费记录不存在';
            END IF;
            
            -- 更新缴费时间（updated_at由触发器自动更新）
            UPDATE payment SET time = NOW()
            WHERE payment_id = p_payment_id;
            
            SET p_success = TRUE;
            
            COMMIT;
        END;
    """)

def create_triggers(cursor):
    """
    创建触发器实现自动化操作
    """
    # 1. 处方创建后自动更新药品库存
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_after_prescription_insert;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_after_prescription_insert
        AFTER INSERT ON prescription
        FOR EACH ROW
        BEGIN
            -- 更新药品库存
            UPDATE drug SET stored_quantity = stored_quantity - NEW.quantity 
            WHERE drug_id = NEW.drug_id;
        END;
    """)
    
    # 2. 处方创建后自动更新挂号状态为出诊中
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_after_prescription_insert_status;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_after_prescription_insert_status
        AFTER INSERT ON prescription
        FOR EACH ROW
        BEGIN
            -- 更新挂号状态为出诊中
            UPDATE registration 
            SET status = 'in_progress', updated_at = NOW()
            WHERE registration_id = NEW.registration_id 
            AND status = 'pending';
        END;
    """)

    # 3. 自动更新updated_at字段的触发器
    # 病人表
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_before_patient_update;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_before_patient_update
        BEFORE UPDATE ON patient
        FOR EACH ROW
        BEGIN
            SET NEW.updated_at = NOW();
        END;
    """)
    
    # 科室表
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_before_department_update;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_before_department_update
        BEFORE UPDATE ON department
        FOR EACH ROW
        BEGIN
            SET NEW.updated_at = NOW();
        END;
    """)
    
    # 医生表
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_before_doctor_update;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_before_doctor_update
        BEFORE UPDATE ON doctor
        FOR EACH ROW
        BEGIN
            SET NEW.updated_at = NOW();
        END;
    """)
    
    # 药品表
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_before_drug_update;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_before_drug_update
        BEFORE UPDATE ON drug
        FOR EACH ROW
        BEGIN
            SET NEW.updated_at = NOW();
        END;
    """)
    
    # 缴费表
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_before_payment_update;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_before_payment_update
        BEFORE UPDATE ON payment
        FOR EACH ROW
        BEGIN
            SET NEW.updated_at = NOW();
        END;
    """)
    
    # 挂号表
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_before_registration_update;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_before_registration_update
        BEFORE UPDATE ON registration
        FOR EACH ROW
        BEGIN
            SET NEW.updated_at = NOW();
        END;
    """)
    
    # 处方表
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_before_prescription_update;
    """)
    cursor.execute("""
        CREATE TRIGGER trg_before_prescription_update
        BEFORE UPDATE ON prescription
        FOR EACH ROW
        BEGIN
            SET NEW.updated_at = NOW();
        END;
    """)
    
    

def show_table_content(cursor, table_name):
    """
    显示指定表的内容
    
    Args:
        cursor: 数据库游标
        table_name: 表名
    """
    try:
        # 获取表数据
        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()
        
        print(f"\n=== {table_name} 表内容 ===")
        if records:
            # 显示列名
            headers = list(records[0].keys())
            header_line = " | ".join(f"{h:<15}" for h in headers)
            print(header_line)
            print("-" * len(header_line))
            
            # 显示数据
            for record in records:
                row_data = " | ".join(f"{str(v):<15}" for v in record.values())
                print(row_data)
            
            print("-" * len(header_line))
            print(f"记录数: {len(records)}")
        else:
            print("表为空")
            
    except Exception as e:
        print(f"查询表 {table_name} 失败: {e}")

def drop_all_tables_for_testing(cursor):
    """
    重置数据库：删除所有表、存储过程和触发器
    
    Args:
        cursor: 数据库游标
    """
    try:
        # 临时禁用外键检查，避免删除顺序问题
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 第一步：删除所有存储过程
        print("🗑️ 删除存储过程...")
        stored_procedures = [
            'sp_register_patient',
            'sp_create_registration', 
            'sp_process_registration',
            'sp_create_prescription',
            'sp_complete_payment'
        ]
        
        for sp_name in stored_procedures:
            cursor.execute(f"DROP PROCEDURE IF EXISTS {sp_name}")
            print(f"  ✅ 已删除存储过程: {sp_name}")
        
        # 第二步：删除所有触发器
        print("🗑️ 删除触发器...")
        triggers = [
            'trg_before_patient_update',
            'trg_before_department_update',
            'trg_before_doctor_update',
            'trg_before_drug_update',
            'trg_before_payment_update',
            'trg_before_registration_update',
            'trg_before_prescription_update'
        ]
        
        for trigger_name in triggers:
            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
            print(f"  ✅ 已删除触发器: {trigger_name}")
        
        # 第三步：删除所有表（按照从依赖表到基础表的顺序）
        print("🗑️ 删除表...")
        tables_to_drop = [
            'prescription',    # 处方表（依赖挂号、药品、缴费）
            'registration',    # 挂号表（依赖病人、科室、医生、缴费）
            'payment',         # 缴费表（依赖病人）
            'doctor',          # 医生表（依赖科室）
            'drug',            # 药品表
            'patient',         # 病人表
            'department'       # 科室表
        ]
        
        for table_name in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"  ✅ 已删除表: {table_name}")
        
        # 重新启用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        print("✅ 数据库重置完成！所有表、存储过程和触发器已删除")
        
    except Exception as e:
        print(f"❌ 数据库重置失败: {e}")

def show_all_tables_content(cursor):
    """
    显示所有表的内容
    
    Args:
        cursor: 数据库游标
    """
    show_table_content(cursor, 'patient')
    show_table_content(cursor, 'department')
    show_table_content(cursor, 'doctor')
    show_table_content(cursor, 'drug')
    show_table_content(cursor, 'payment')
    show_table_content(cursor,'registration')
    show_table_content(cursor, 'prescription')
