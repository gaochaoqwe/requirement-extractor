import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

class OptimizedDynamicTestDatabase:
    """
    优化后的动态测试数据库
    
    数据库结构：
    1. 基础数据表 - 合并所有基础数据（人员、领域、组件等）
    2. 任务表 - 记录每次表单生成请求
    3. 项目信息表 - 存储project_info数据
    4. 软件配置表 - 存储software_config数据
    5. 项目策划表 - 存储project_plan数据
    6. 需求分析表 - 存储requirement_analysis数据
    7. 测试用例表 - 存储test_case_generation数据
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 数据库文件放在db目录下
            db_dir = Path(__file__).parent
            db_path = db_dir / "optimized_dynamic_test.db"
        
        self.db_path = str(db_path)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 基础数据表 - 合并所有基础数据
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS base_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,  -- 数据类别：domain, test_manager, test_personnel, developer, aircraft_model, project_director, development_department, chief_designer, project_manager, component
                    name TEXT NOT NULL,
                    description TEXT,  -- 可选描述
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, name)
                )
            ''')
            
            # 2. 任务表 - 记录每次表单生成请求
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,  -- UUID格式的任务ID
                    session_id TEXT NOT NULL,  -- 会话ID
                    task_type TEXT NOT NULL,  -- 任务类型：form_generation
                    status TEXT NOT NULL DEFAULT 'pending',  -- 状态：pending, running, completed, failed
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    error_message TEXT,  -- 错误信息
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 3. 项目信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,  -- 关联任务ID
                    software_name TEXT NOT NULL,  -- 软件名称
                    software_version TEXT,  -- 软件版本
                    software_id TEXT,  -- 软件标识
                    domain TEXT,  -- 所属领域
                    aircraft_model TEXT,  -- 飞机型号
                    project_director TEXT,  -- 项目总师
                    development_department TEXT,  -- 研制部门
                    chief_designer TEXT,  -- 主任设计师
                    programming_language TEXT,  -- 编程语言
                    development_environment TEXT,  -- 开发环境
                    runtime_environment TEXT,  -- 运行环境
                    software_level TEXT,  -- 软件等级
                    additional_info TEXT,  -- 额外信息（JSON格式）
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            ''')
            
            # 4. 软件配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS software_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,  -- 关联任务ID
                    config_item_name TEXT,  -- 配置项名称
                    config_item_version TEXT,  -- 配置项版本
                    config_item_id TEXT,  -- 配置项标识
                    config_status TEXT,  -- 配置状态
                    config_type TEXT,  -- 配置类型
                    file_path TEXT,  -- 文件路径
                    checksum TEXT,  -- 校验和
                    size_info TEXT,  -- 大小信息
                    modification_time TEXT,  -- 修改时间
                    responsible_person TEXT,  -- 负责人
                    additional_config TEXT,  -- 额外配置信息（JSON格式）
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            ''')
            
            # 5. 项目策划表 - 重新设计以与Excel表格列结构完全对应
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_plan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,  -- 关联任务ID
                    plan_item_id TEXT,  -- 策划项ID（内部使用）
                    
                    -- Excel表格列对应字段（约13列，A到M列）
                    -- A列：ID（通常保持空白）
                    item_id TEXT,
                    -- B列：序号
                    sequence_number INTEGER,
                    -- C列：软件需求
                    software_requirement TEXT,
                    -- D列：标准子需求名称
                    standard_sub_requirement_name TEXT,
                    -- E列：标准子需求单位
                    standard_sub_requirement_unit TEXT,
                    -- F列：软件需求规格说明/影响域分析报告追踪
                    requirement_tracking TEXT,
                    -- G列：重要性
                    importance TEXT,
                    -- H列：是否完成测试
                    test_completed TEXT,
                    -- I列：需求分析（测试主管）
                    requirement_analysis_personnel TEXT,
                    -- J列：文档审查（测试人员）
                    document_review_personnel TEXT,
                    -- K列：静态分析（测试人员）
                    static_analysis_personnel TEXT,
                    -- L列：代码审查（测试人员）
                    code_review_personnel TEXT,
                    -- M列：动态测试（测试人员）
                    dynamic_test_personnel TEXT,
                    
                    -- 系统字段
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            ''')
            
            # 6. 需求分析表 - 重新设计以与Excel表格列结构完全对应
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS requirement_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,  -- 关联任务ID
                    requirement_id TEXT,  -- 需求ID（内部使用）
                    
                    -- Excel表格列对应字段（从第2列开始到通过准则列）
                    -- 第2列：序号
                    index_number REAL,
                    -- 第3列：软件名称  
                    software_name TEXT,
                    -- 第4列：软件版本
                    software_version TEXT,
                    -- 第5列：轮次信息
                    round_info TEXT,
                    -- 第6列：标准子需求名称
                    standard_sub_requirement_name TEXT,
                    -- 第7列：标准子需求标识
                    standard_sub_requirement_identifier TEXT,
                    -- 第8列：标准子需求测试单元
                    standard_sub_requirement_unit TEXT,
                    -- 第9列：任务需求追踪
                    task_requirement_trace TEXT,
                    -- 第10列：软件需求规格说明追踪
                    software_requirement_trace TEXT,
                    -- 第11列：软件需求规格说明需求名称
                    software_requirement_name TEXT,
                    -- 第12列：软件需求规格说明需求标识
                    software_requirement_identifier TEXT,
                    -- 第13列：需求描述
                    requirement_description TEXT,
                    -- 第14列：测试类型
                    test_type TEXT,
                    -- 第15列：测试项名称
                    test_item_name TEXT,
                    -- 第16列：测试项标识
                    test_item_identifier TEXT,
                    -- 第17列：过程标识
                    process_identifier TEXT,
                    -- 第18列：需求子项描述
                    requirement_sub_description TEXT,
                    -- 第19列：测试项描述
                    test_description TEXT,
                    -- 第20列：测试方法
                    test_method TEXT,
                    -- 第21列：充分性要求
                    adequacy_requirement TEXT,
                    -- 第22列：通过准则
                    pass_criteria TEXT,

                    -- 新增：渲染一致性关键字段
                    -- 第23列：英文标识（为列7/12/16的唯一真源）
                    english_identifier TEXT,
                    -- 软硬件组合标识（如 CT-<software_id>-<version>），用于构造列7/16
                    software_identifier TEXT,
                    
                    -- 系统字段
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            ''')
            
            # 7. 需求位置信息表 - 缓存需求在文档中的位置
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS requirement_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,  -- 会话ID
                    document_path TEXT NOT NULL,  -- 文档路径
                    document_hash TEXT,  -- 文档MD5哈希，用于检测文档是否变更
                    requirement_name TEXT NOT NULL,  -- 需求名称
                    chapter_number TEXT,  -- 章节编号（如3.2.1）
                    paragraph_index INTEGER,  -- 段落在文档中的索引位置
                    char_start_offset INTEGER,  -- 字符起始偏移量
                    char_end_offset INTEGER,  -- 字符结束偏移量
                    heading_text TEXT,  -- 标题完整文本
                    content_preview TEXT,  -- 内容预览（前100字符）
                    num_id TEXT,  -- Word自动编号ID
                    ilvl INTEGER,  -- 编号级别
                    style_id TEXT,  -- 样式ID
                    outline_level INTEGER,  -- 大纲级别
                    extraction_metadata TEXT,  -- 提取元数据（JSON格式）
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, document_path, requirement_name)
                )
            ''')
            
            # 8. 测试用例表 - 重新设计以与Excel表格列结构完全对应
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,  -- 关联任务ID
                    requirement_id TEXT,  -- 关联需求ID
                    
                    -- Excel表格列对应字段（从A列到AD列，共30列）
                    -- 第1列A：ID（测试用例ID）- 通常不填充
                    test_case_id TEXT,
                    -- 第2列B：序号
                    sequence_number INTEGER,
                    -- 第3列C：软件配置项名称
                    software_item_name TEXT,
                    -- 第4列D：被测软件版本
                    software_version TEXT,
                    -- 第5列E：测试轮次
                    test_round TEXT,
                    -- 第6列F：需求追溯
                    requirement_traceability TEXT,
                    -- 第7列G：测试项名称
                    test_item_name TEXT,
                    -- 第8列H：测试项标识
                    test_item_identifier TEXT,
                    -- 第9列I：测试用例名称
                    test_case_name TEXT,
                    -- 第10列J：测试用例编号
                    test_case_number TEXT,
                    -- 第11列K：测试类型
                    test_type TEXT,
                    -- 第12列L：测试描述
                    test_description TEXT,
                    -- 第13列M：预置条件
                    preconditions TEXT,
                    -- 第14列N：前提与约束
                    prerequisites_constraints TEXT,
                    -- 第15列O：输入/动作
                    input_actions TEXT,
                    -- 第16列P：输入条件
                    input_conditions TEXT,
                    -- 第17列Q：预期结果
                    expected_results TEXT,
                    -- 第18列R：通过准则
                    pass_criteria TEXT,
                    -- 第19列S：用例设计人
                    case_designer TEXT,
                    -- 第20列T：校对人
                    reviewer TEXT,
                    -- 第21列U：设计时间
                    design_time TEXT,
                    -- 第22列V：校对时间
                    review_time TEXT,
                    -- 第23列W：测试人员
                    test_personnel TEXT,
                    -- 第24列X：监督人员
                    supervisor TEXT,
                    -- 第25列Y：测试时间
                    test_time TEXT,
                    -- 第26列Z：测试结果（待填写）
                    test_result TEXT,
                    -- 第27列AA：测试结论
                    test_conclusion TEXT,
                    -- 第28列AB：问题报告单编号
                    issue_report_number TEXT,
                    -- 第29列AC：执行年月
                    execution_year_month TEXT,
                    -- 第30列AD：用例发现问题数
                    issues_found_count INTEGER,
                    
                    -- 系统字段
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id),
                    FOREIGN KEY (requirement_id) REFERENCES requirement_analysis (requirement_id)
                )
            ''')

            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_base_data_category ON base_data (category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks (session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_info_task ON project_info (task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_software_config_task ON software_config (task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_plan_task ON project_plan (task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_requirement_analysis_task ON requirement_analysis (task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_cases_task ON test_cases (task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_cases_requirement ON test_cases (requirement_id)')
            # 唯一索引：测试用例行级UPSERT (task_id, sequence_number)
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_test_cases_task_seq ON test_cases (task_id, sequence_number)')
            # 唯一索引：保证每个 task_id 的行索引唯一，支持行级幂等UPSERT
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_requirement_analysis_task_idx ON requirement_analysis (task_id, index_number)')
            
            # 兼容已有库：如果旧表缺少 english_identifier / software_identifier，则补充新增
            try:
                cursor.execute('PRAGMA table_info(requirement_analysis)')
                cols = [r[1] for r in cursor.fetchall()]
                if 'english_identifier' not in cols:
                    cursor.execute('ALTER TABLE requirement_analysis ADD COLUMN english_identifier TEXT')
                if 'software_identifier' not in cols:
                    cursor.execute('ALTER TABLE requirement_analysis ADD COLUMN software_identifier TEXT')
            except Exception as _:
                pass
            
            
            conn.commit()
            
            # 插入初始基础数据
            self._insert_initial_base_data()
            conn.commit()
    
    def _insert_initial_base_data(self):
        """初始化基础数据（当前保持空实现以避免AttributeError）。"""
        # 如需预置基础数据，可在此插入到 base_data 表。
        # 目前不强制插入，保持为空实现。
        return

    # ===== 任务生命周期管理 =====
    def create_task(self, session_id: str, task_type: str = 'form_generation') -> str:
        """创建任务并返回 task_id。"""
        task_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            _now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO tasks (task_id, session_id, task_type, status, start_time, created_at, updated_at)
                VALUES (?, ?, ?, 'pending', ?, ?, ?)
            ''', (task_id, session_id, task_type, _now_local, _now_local, _now_local))
            conn.commit()
        return task_id

    def create_task_with_id(self, task_id: str, session_id: str, task_type: str = 'form_generation') -> str:
        """使用指定的 task_id 创建任务（若已存在则忽略插入）。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 如果已存在则不再重复插入
            cursor.execute('SELECT 1 FROM tasks WHERE task_id = ? LIMIT 1', (task_id,))
            if cursor.fetchone() is None:
                _now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO tasks (task_id, session_id, task_type, status, start_time, created_at, updated_at)
                    VALUES (?, ?, ?, 'pending', ?, ?, ?)
                ''', (task_id, session_id, task_type, _now_local, _now_local, _now_local))
                conn.commit()
        return task_id

    def update_task_status(self, task_id: str, status: str, error_message: Optional[str] = None) -> None:
        """更新任务状态；当状态为 completed/failed 时写入 end_time。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            _now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if status in ('completed', 'failed'):
                cursor.execute('''
                    UPDATE tasks
                    SET status = ?, end_time = ?, error_message = ?, updated_at = ?
                    WHERE task_id = ?
                ''', (status, _now_local, error_message, _now_local, task_id))
            else:
                cursor.execute('''
                    UPDATE tasks
                    SET status = ?, updated_at = ?
                    WHERE task_id = ?
                ''', (status, _now_local, task_id))
            conn.commit()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态及基础信息；不存在返回 None。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT task_id, session_id, task_type, status, start_time, end_time, error_message FROM tasks WHERE task_id = ? LIMIT 1', (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务完整信息；不存在返回 None。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE task_id = ? LIMIT 1', (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_requirement_analysis(self, task_id: str, analysis_data_list: List[Dict[str, Any]]):
        """批量保存需求分析数据（按行UPSERT）。"""
        # 日志后备
        try:
            import logging
        except Exception:
            def log_info(msg: str, module: str = None):
                pass

        if not analysis_data_list:
            return

        for idx, row in enumerate(analysis_data_list, start=1):
            # 如果行内提供了 index_number，优先使用
            row_index = row.get('index_number') if isinstance(row.get('index_number'), int) else idx
            self.save_requirement_row(task_id, int(row_index), row)
        logger = logging.getLogger("db_operations")
        logger.info(f"[DB] 需求分析数据已保存：{len(analysis_data_list)} 条")

    # ===== 项目信息与软件配置存储 =====
    def save_project_info(self, task_id: str, project_info_data: Dict[str, Any]) -> None:
        """保存项目信息数据。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            _now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO project_info (
                    task_id, software_name, software_version, software_id, domain, aircraft_model,
                    project_director, development_department, chief_designer, programming_language,
                    development_environment, runtime_environment, software_level, additional_info, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(task_id),
                project_info_data.get('software_name'),
                project_info_data.get('software_version'),
                project_info_data.get('software_id'),
                project_info_data.get('domain'),
                project_info_data.get('aircraft_model'),
                project_info_data.get('project_director'),
                project_info_data.get('development_department'),
                project_info_data.get('chief_designer'),
                project_info_data.get('programming_language'),
                project_info_data.get('development_environment'),
                project_info_data.get('runtime_environment'),
                project_info_data.get('software_level'),
                json.dumps(project_info_data.get('additional_info', {})),
                _now_local
            ))
            conn.commit()

    def save_software_config(self, task_id: str, config_data: Dict[str, Any]) -> None:
        """保存软件配置数据。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            _now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO software_config (
                    task_id, config_item_name, config_item_version, config_item_id, config_status, config_type,
                    file_path, checksum, size_info, modification_time, responsible_person, additional_config, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(task_id),
                config_data.get('config_item_name'),
                config_data.get('config_item_version'),
                config_data.get('config_item_id'),
                config_data.get('config_status'),
                config_data.get('config_type'),
                config_data.get('file_path'),
                config_data.get('checksum'),
                config_data.get('size_info'),
                config_data.get('modification_time'),
                config_data.get('responsible_person'),
                json.dumps(config_data.get('additional_config', {})),
                _now_local
            ))
            conn.commit()

    # ===== 项目策划存储与迁移 =====
    def migrate_project_plan_table(self):
        """确保项目策划表结构与唯一索引存在（幂等）。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 表在初始化时已创建，这里仅确保唯一索引存在
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_project_plan_task_seq ON project_plan (task_id, sequence_number)')
            conn.commit()

    def save_project_plan(self, task_id: str, plan_data_list: List[Dict[str, Any]]) -> None:
        """保存项目策划数据；按 (task_id, sequence_number) 幂等UPSERT。"""
        if not plan_data_list:
            return
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 确保唯一索引存在
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_project_plan_task_seq ON project_plan (task_id, sequence_number)')
            for row in plan_data_list:
                seq = row.get('sequence_number')
                try:
                    seq = int(seq) if seq is not None else None
                except Exception:
                    seq = None
                _now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO project_plan (
                        task_id, plan_item_id, item_id, sequence_number, software_requirement,
                        standard_sub_requirement_name, standard_sub_requirement_unit, requirement_tracking,
                        importance, test_completed, requirement_analysis_personnel, document_review_personnel,
                        static_analysis_personnel, code_review_personnel, dynamic_test_personnel,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id, sequence_number) DO UPDATE SET
                        plan_item_id=excluded.plan_item_id,
                        item_id=excluded.item_id,
                        software_requirement=excluded.software_requirement,
                        standard_sub_requirement_name=excluded.standard_sub_requirement_name,
                        standard_sub_requirement_unit=excluded.standard_sub_requirement_unit,
                        requirement_tracking=excluded.requirement_tracking,
                        importance=excluded.importance,
                        test_completed=excluded.test_completed,
                        requirement_analysis_personnel=excluded.requirement_analysis_personnel,
                        document_review_personnel=excluded.document_review_personnel,
                        static_analysis_personnel=excluded.static_analysis_personnel,
                        code_review_personnel=excluded.code_review_personnel,
                        dynamic_test_personnel=excluded.dynamic_test_personnel,
                        updated_at=excluded.updated_at
                ''', (
                    str(task_id),
                    row.get('plan_item_id'),
                    row.get('item_id'),
                    seq,
                    row.get('software_requirement'),
                    row.get('standard_sub_requirement_name'),
                    row.get('standard_sub_requirement_unit'),
                    row.get('requirement_tracking'),
                    row.get('importance'),
                    row.get('test_completed'),
                    row.get('requirement_analysis_personnel'),
                    row.get('document_review_personnel'),
                    row.get('static_analysis_personnel'),
                    row.get('code_review_personnel'),
                    row.get('dynamic_test_personnel'),
                    _now_local,
                    _now_local
                ))
            conn.commit()

    # ===== 测试用例批量保存 =====
    def save_test_cases(self, task_id: str, test_cases_list: List[Dict[str, Any]]) -> None:
        """批量保存测试用例；按 (task_id, sequence_number) 幂等UPSERT。"""
        if not test_cases_list:
            return
        # 避免覆盖：基于当前已存在的序号集合进行分配
        try:
            existing = self.get_existing_sequence_numbers(task_id)
        except Exception:
            existing = set()
        try:
            cur = self.get_next_sequence_number(task_id)
        except Exception:
            cur = 1

        for row in test_cases_list:
            seq = row.get('sequence_number')
            # 规则：无效/重复的序号统一改为从 cur 开始的连续值
            if not isinstance(seq, int) or seq <= 0 or seq in existing:
                seq = cur
                cur += 1
            # 记录占用，避免同批次重复
            existing.add(int(seq))
            self.save_test_case_row(task_id, int(seq), row)

    # ===== 序号辅助函数，防止覆盖 =====
    def get_max_sequence_number(self, task_id: str) -> int:
        """获取当前 task 的最大 sequence_number；若无数据返回 0。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(sequence_number) FROM test_cases WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            try:
                return int(row[0]) if row and row[0] is not None else 0
            except Exception:
                return 0

    def get_next_sequence_number(self, task_id: str) -> int:
        """获取下一个可用的 sequence_number（= 当前最大值 + 1，若不存在则为 1）。"""
        return self.get_max_sequence_number(task_id) + 1

    def get_existing_sequence_numbers(self, task_id: str) -> set:
        """返回该 task 已存在的所有 sequence_number 集合。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT sequence_number FROM test_cases WHERE task_id = ?', (task_id,))
            rows = cursor.fetchall()
            return {int(r[0]) for r in rows if r and r[0] is not None}

    def save_requirement_row(self, task_id: str, row_index: int, row_data: Dict[str, Any]):
        """按行保存需求分析数据（UPSERT: task_id + index_number 唯一）。"""
        import logging
        
        # 使用简单的日志记录，避免导入问题
        logger = logging.getLogger("db_operations")
        
        def safe_str(value):
            if value is None:
                return ''
            elif isinstance(value, (dict, list)):
                return str(value)
            else:
                return str(value)

        # 记录开始存储
        test_item_name = row_data.get('test_item_name', '')
        test_item_identifier = row_data.get('test_item_identifier', '')
        logger.info(f"[DB_SAVE_START] ===== 开始保存需求分析数据 =====")
        logger.info(f"[DB_SAVE_START] Task ID: {task_id}")
        logger.info(f"[DB_SAVE_START] 行索引: {row_index}")
        logger.info(f"[DB_SAVE_START] 测试项名称: {test_item_name}")
        logger.info(f"[DB_SAVE_START] 测试项标识: {test_item_identifier}")
        logger.info(f"[DB_SAVE_START] 数据库路径: {self.db_path}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                logger.info(f"[DB_SAVE_CONN] 数据库连接成功")
                _now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                cursor.execute('''
                    INSERT INTO requirement_analysis (
                        task_id, requirement_id, index_number, software_name, software_version, round_info,
                        standard_sub_requirement_name, standard_sub_requirement_identifier, standard_sub_requirement_unit,
                        task_requirement_trace, software_requirement_trace, software_requirement_name, software_requirement_identifier,
                        requirement_description, test_type, test_item_name, test_item_identifier, process_identifier,
                        requirement_sub_description, test_description, test_method, adequacy_requirement, pass_criteria,
                        english_identifier, software_identifier, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id, index_number) DO UPDATE SET
                        requirement_id=excluded.requirement_id,
                        software_name=excluded.software_name,
                        software_version=excluded.software_version,
                        round_info=excluded.round_info,
                        standard_sub_requirement_name=excluded.standard_sub_requirement_name,
                        standard_sub_requirement_identifier=excluded.standard_sub_requirement_identifier,
                        standard_sub_requirement_unit=excluded.standard_sub_requirement_unit,
                        task_requirement_trace=excluded.task_requirement_trace,
                        software_requirement_trace=excluded.software_requirement_trace,
                        software_requirement_name=excluded.software_requirement_name,
                        software_requirement_identifier=excluded.software_requirement_identifier,
                        requirement_description=excluded.requirement_description,
                        test_type=excluded.test_type,
                        test_item_name=excluded.test_item_name,
                        test_item_identifier=excluded.test_item_identifier,
                        process_identifier=excluded.process_identifier,
                        requirement_sub_description=excluded.requirement_sub_description,
                        test_description=excluded.test_description,
                        test_method=excluded.test_method,
                        adequacy_requirement=excluded.adequacy_requirement,
                        pass_criteria=excluded.pass_criteria,
                        english_identifier=excluded.english_identifier,
                        software_identifier=excluded.software_identifier,
                        updated_at=excluded.updated_at
                ''', (
                    str(task_id),
                    safe_str(row_data.get('requirement_id')),
                    row_index,
                    safe_str(row_data.get('software_name')),
                    safe_str(row_data.get('software_version')),
                    safe_str(row_data.get('round_info')),
                    safe_str(row_data.get('standard_sub_requirement_name')),
                    safe_str(row_data.get('standard_sub_requirement_identifier')),
                    safe_str(row_data.get('standard_sub_requirement_unit')),
                    safe_str(row_data.get('task_requirement_trace')),
                    safe_str(row_data.get('software_requirement_trace')),
                    safe_str(row_data.get('software_requirement_name')),
                    safe_str(row_data.get('software_requirement_identifier')),
                    safe_str(row_data.get('requirement_description')),
                    safe_str(row_data.get('test_type')),
                    safe_str(row_data.get('test_item_name')),
                    safe_str(row_data.get('test_item_identifier')),
                    safe_str(row_data.get('process_identifier')),
                    safe_str(row_data.get('requirement_sub_description')),
                    safe_str(row_data.get('test_description')),
                    safe_str(row_data.get('test_method')),
                    safe_str(row_data.get('adequacy_requirement')),
                    safe_str(row_data.get('pass_criteria')),
                    safe_str(row_data.get('english_identifier')),
                    safe_str(row_data.get('software_identifier')),
                    _now_local,
                    _now_local
                ))
                conn.commit()
                logger.info(f"[DB_SAVE_OK] requirement_analysis 已保存/更新：task_id={task_id}, index_number={row_index}")
                return True
                
        except sqlite3.IntegrityError as e:
            logger.error(f"[DB_INTEGRITY_ERROR] 数据库完整性错误 - task_id: {task_id}, row: {row_index}, item: {test_item_name}, error: {str(e)}")
            raise
        except sqlite3.OperationalError as e:
            logger.error(f"[DB_OPERATIONAL_ERROR] 数据库操作错误 - task_id: {task_id}, row: {row_index}, item: {test_item_name}, error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[DB_UNKNOWN_ERROR] 未知数据库错误 - task_id: {task_id}, row: {row_index}, item: {test_item_name}, error: {str(e)}, type: {type(e).__name__}")
            # 记录详细的参数信息用于调试
            logger.error(f"[DB_ERROR_DETAILS] 详细参数信息 - row_data keys: {list(row_data.keys())}")
            import traceback
            logger.error(f"[DB_ERROR_STACK] 异常堆栈: {traceback.format_exc()}")
            raise

    def get_requirement_rows(self, task_id: str) -> List[Dict[str, Any]]:
        """按 task_id 获取需求分析所有行，按 index_number 排序返回字典列表。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    index_number, software_name, software_version, round_info,
                    standard_sub_requirement_name, standard_sub_requirement_identifier, standard_sub_requirement_unit,
                    task_requirement_trace, software_requirement_trace, software_requirement_name, software_requirement_identifier,
                    requirement_description, test_type, test_item_name, test_item_identifier, process_identifier,
                    requirement_sub_description, test_description, test_method, adequacy_requirement, pass_criteria,
                    english_identifier, software_identifier
                FROM requirement_analysis
                WHERE task_id = ?
                ORDER BY index_number ASC
            ''', (task_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== 基础数据查询方法 =====
    def get_base_data_by_category(self, category: str) -> List[Dict[str, str]]:
        """根据类别获取基础数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name, description FROM base_data WHERE category = ? ORDER BY name', (category,))
            return [{'value': row['name'], 'label': row['name'], 'description': row['description']} for row in cursor.fetchall()]
    
    def add_base_data(self, category: str, name: str, description: str = None) -> bool:
        """添加基础数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO base_data (category, name, description) 
                    VALUES (?, ?, ?)
                ''', (category, name, description))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    # ===== 快捷查询方法 =====
    def get_domains(self) -> List[Dict[str, str]]:
        """获取所有领域"""
        return self.get_base_data_by_category('domain')
    
    def get_test_managers(self) -> List[Dict[str, str]]:
        """获取所有测试主管"""
        return self.get_base_data_by_category('test_manager')
    
    def get_test_personnel(self) -> List[Dict[str, str]]:
        """获取所有测试人员"""
        return self.get_base_data_by_category('test_personnel')
    
    def get_developers(self) -> List[Dict[str, str]]:
        """获取所有开发人员"""
        return self.get_base_data_by_category('developer')
    
    def get_aircraft_models(self) -> List[Dict[str, str]]:
        """获取所有飞机型号"""
        return self.get_base_data_by_category('aircraft_model')
    
    def get_project_directors(self) -> List[Dict[str, str]]:
        """获取所有项目总师"""
        return self.get_base_data_by_category('project_director')
    
    def get_development_departments(self) -> List[Dict[str, str]]:
        """获取所有研制部门"""
        return self.get_base_data_by_category('development_department')
    
    def get_chief_designers(self) -> List[Dict[str, str]]:
        """获取所有主任设计师"""
        return self.get_base_data_by_category('chief_designer')
    
    def get_project_managers(self) -> List[Dict[str, str]]:
        """获取所有项目主管"""
        return self.get_base_data_by_category('project_manager')
    
    def get_components(self) -> List[Dict[str, str]]:
        """获取所有组件"""
        return self.get_base_data_by_category('component')
    
    # ===== 专门的添加方法 =====
    def add_chief_designer(self, name: str) -> bool:
        """添加主任设计师"""
        return self.add_base_data('chief_designer', name)
    
    def add_project_manager(self, name: str) -> bool:
        """添加项目主管"""
        return self.add_base_data('project_manager', name)
    
    def add_development_department(self, name: str) -> bool:
        """添加研制部门"""
        return self.add_base_data('development_department', name)
    
    def add_aircraft_model(self, name: str) -> bool:
        """添加飞机型号"""
        return self.add_base_data('aircraft_model', name)
    
    def add_project_director(self, name: str) -> bool:
        """添加项目总师"""
        return self.add_base_data('project_director', name)
    
    def add_domain(self, name: str) -> bool:
        """添加领域"""
        return self.add_base_data('domain', name)
    
    def add_test_manager(self, name: str) -> bool:
        """添加测试主管"""
        return self.add_base_data('test_manager', name)
    
    def add_test_personnel(self, name: str) -> bool:
        """添加测试人员"""
        return self.add_base_data('test_personnel', name)
    
    def add_developer(self, name: str) -> bool:
        """添加开发人员"""
        return self.add_base_data('developer', name)
    
    # ===== 需求位置信息管理 =====
    
    def save_requirement_position(self, session_id: str, document_path: str, 
                                  document_hash: str, position_info: Dict[str, Any]) -> bool:
        """
        保存需求位置信息
        
        Args:
            session_id: 会话ID
            document_path: 文档路径
            document_hash: 文档哈希值
            position_info: 位置信息字典，包含：
                - requirement_name: 需求名称
                - chapter_number: 章节编号
                - paragraph_index: 段落索引
                - char_start_offset: 字符起始偏移
                - char_end_offset: 字符结束偏移
                - heading_text: 标题文本
                - content_preview: 内容预览
                - num_id: Word编号ID
                - ilvl: 编号级别
                - style_id: 样式ID
                - outline_level: 大纲级别
                - extraction_metadata: 提取元数据
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO requirement_positions (
                        session_id, document_path, document_hash, requirement_name,
                        chapter_number, paragraph_index, char_start_offset, char_end_offset,
                        heading_text, content_preview, num_id, ilvl, style_id, outline_level,
                        extraction_metadata, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    session_id,
                    document_path,
                    document_hash,
                    position_info.get('requirement_name'),
                    position_info.get('chapter_number'),
                    position_info.get('paragraph_index'),
                    position_info.get('char_start_offset'),
                    position_info.get('char_end_offset'),
                    position_info.get('heading_text'),
                    position_info.get('content_preview'),
                    position_info.get('num_id'),
                    position_info.get('ilvl'),
                    position_info.get('style_id'),
                    position_info.get('outline_level'),
                    json.dumps(position_info.get('extraction_metadata', {}))
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"保存需求位置信息失败: {e}")
            return False
    
    def get_requirement_positions(self, session_id: str, document_path: str = None) -> List[Dict[str, Any]]:
        """
        获取需求位置信息
        
        Args:
            session_id: 会话ID
            document_path: 可选的文档路径过滤
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if document_path:
                    cursor.execute('''
                        SELECT * FROM requirement_positions 
                        WHERE session_id = ? AND document_path = ?
                        ORDER BY paragraph_index
                    ''', (session_id, document_path))
                else:
                    cursor.execute('''
                        SELECT * FROM requirement_positions 
                        WHERE session_id = ?
                        ORDER BY document_path, paragraph_index
                    ''', (session_id,))
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    result = dict(row)
                    # 解析JSON字段
                    if result['extraction_metadata']:
                        result['extraction_metadata'] = json.loads(result['extraction_metadata'])
                    results.append(result)
                
                return results
        except Exception as e:
            print(f"获取需求位置信息失败: {e}")
            return []
    
    def get_requirement_position_by_name(self, session_id: str, requirement_name: str) -> Optional[Dict[str, Any]]:
        """
        根据需求名称获取位置信息
        
        Args:
            session_id: 会话ID
            requirement_name: 需求名称
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM requirement_positions 
                    WHERE session_id = ? AND requirement_name = ?
                    LIMIT 1
                ''', (session_id, requirement_name))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    if result['extraction_metadata']:
                        result['extraction_metadata'] = json.loads(result['extraction_metadata'])
                    return result
                return None
        except Exception as e:
            print(f"获取需求位置信息失败: {e}")
            return None
    
    def is_document_positions_cached(self, session_id: str, document_path: str, document_hash: str) -> bool:
        """
        检查文档的位置信息是否已缓存且有效
        
        Args:
            session_id: 会话ID
            document_path: 文档路径
            document_hash: 文档哈希值
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM requirement_positions 
                    WHERE session_id = ? AND document_path = ? AND document_hash = ?
                ''', (session_id, document_path, document_hash))
                
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            print(f"检查缓存状态失败: {e}")
            return False
    
    def clear_requirement_positions(self, session_id: str, document_path: str = None) -> bool:
        """
        清除需求位置信息
        
        Args:
            session_id: 会话ID
            document_path: 可选的文档路径，如果提供则只清除该文档的位置信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if document_path:
                    cursor.execute('''
                        DELETE FROM requirement_positions 
                        WHERE session_id = ? AND document_path = ?
                    ''', (session_id, document_path))
                else:
                    cursor.execute('''
                        DELETE FROM requirement_positions 
                        WHERE session_id = ?
                    ''', (session_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"清除需求位置信息失败: {e}")
            return False 
    
    def migrate_requirement_analysis_table(self):
        """迁移requirement_analysis表结构以匹配Excel列结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查是否需要迁移
            cursor.execute("PRAGMA table_info(requirement_analysis)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # 如果已经包含新的列结构，则无需迁移
            if 'index_number' in columns:
                print("数据库表结构已经是最新版本，无需迁移")
                return
            
            print("开始迁移requirement_analysis表结构...")
            
            # 备份现有数据
            cursor.execute("SELECT * FROM requirement_analysis")
            old_data = cursor.fetchall()
            
            # 删除旧表
            cursor.execute("DROP TABLE IF EXISTS requirement_analysis_old")
            cursor.execute("ALTER TABLE requirement_analysis RENAME TO requirement_analysis_old")
            
            # 创建新表结构
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS requirement_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,  -- 关联任务ID
                    requirement_id TEXT,  -- 需求ID（内部使用）
                    
                    -- Excel表格列对应字段（从第2列开始到通过准则列）
                    -- 第2列：序号
                    index_number REAL,
                    -- 第3列：软件名称  
                    software_name TEXT,
                    -- 第4列：软件版本
                    software_version TEXT,
                    -- 第5列：轮次信息
                    round_info TEXT,
                    -- 第6列：标准子需求名称
                    standard_sub_requirement_name TEXT,
                    -- 第7列：标准子需求标识
                    standard_sub_requirement_identifier TEXT,
                    -- 第8列：标准子需求测试单元
                    standard_sub_requirement_unit TEXT,
                    -- 第9列：任务需求追踪
                    task_requirement_trace TEXT,
                    -- 第10列：软件需求规格说明追踪
                    software_requirement_trace TEXT,
                    -- 第11列：软件需求规格说明需求名称
                    software_requirement_name TEXT,
                    -- 第12列：软件需求规格说明需求标识
                    software_requirement_identifier TEXT,
                    -- 第13列：需求描述
                    requirement_description TEXT,
                    -- 第14列：测试类型
                    test_type TEXT,
                    -- 第15列：测试项名称
                    test_item_name TEXT,
                    -- 第16列：测试项标识
                    test_item_identifier TEXT,
                    -- 第17列：过程标识
                    process_identifier TEXT,
                    -- 第18列：需求子项描述
                    requirement_sub_description TEXT,
                    -- 第19列：测试项描述
                    test_description TEXT,
                    -- 第20列：测试方法
                    test_method TEXT,
                    -- 第21列：充分性要求
                    adequacy_requirement TEXT,
                    -- 第22列：通过准则
                    pass_criteria TEXT,
                    
                    -- 系统字段
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            ''')
            
            # 尝试迁移部分数据（如果有兼容的字段）
            if old_data:
                print(f"尝试迁移 {len(old_data)} 条现有数据...")
                # 注意：这里只能迁移兼容的字段，其他字段将为空
                for row in old_data:
                    try:
                        cursor.execute('''
                            INSERT INTO requirement_analysis (
                                task_id, requirement_id, test_item_name, test_item_identifier,
                                test_description, test_method, requirement_description, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row[1],  # task_id
                            row[2],  # requirement_id
                            row[8] if len(row) > 8 else None,  # test_item_name
                            row[7] if len(row) > 7 else None,  # test_item_identifier
                            row[9] if len(row) > 9 else None,  # test_description
                            row[10] if len(row) > 10 else None, # test_method
                            row[3] if len(row) > 3 else None,  # requirement_description
                            row[-1] if len(row) > 0 else datetime.now()  # created_at
                        ))
                    except Exception as e:
                        print(f"迁移数据行时出错: {e}")
                        continue
            
            # 重建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_requirement_analysis_task ON requirement_analysis (task_id)')
            
            conn.commit()
            print("requirement_analysis表结构迁移完成！") 
    
    def migrate_test_cases_table(self):
        """迁移test_cases表结构以匹配Excel列结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 检查并按需补充缺失列（兼容老库）。现阶段主要确保存在 sequence_number 列。
            cursor.execute("PRAGMA table_info(test_cases)")
            columns = [row[1] for row in cursor.fetchall()]
            try:
                if 'sequence_number' not in columns:
                    cursor.execute('ALTER TABLE test_cases ADD COLUMN sequence_number INTEGER')
            except Exception:
                pass
            
            # 重建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_cases_task ON test_cases (task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_cases_requirement ON test_cases (requirement_id)')
            # 新增：行级幂等唯一键 (task_id, sequence_number)
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_test_cases_task_seq ON test_cases (task_id, sequence_number)')

            
            conn.commit()
            print("test_cases表结构迁移完成！")

    def delete_test_cases_by_task(self, task_id: str) -> None:
        """删除某任务的所有测试用例（用于重新生成时清空）。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM test_cases WHERE task_id = ?', (task_id,))
            conn.commit()

    def save_test_case_row(self, task_id: str, sequence_number: int, row: Dict[str, Any]) -> None:
        """按行保存测试用例（UPSERT，唯一键为 task_id + sequence_number）。"""
        def s(v):
            if v is None:
                return None
            return v if isinstance(v, (int, float)) else str(v)
        import logging
        logger = logging.getLogger("db_operations")
        # 开始记录写入尝试
        try:
            logger.info(f"[DB_SAVE_START] ===== 开始保存测试用例 =====")
            logger.info(f"[DB_SAVE_START] Task ID: {task_id}")
            logger.info(f"[DB_SAVE_START] 行序号: {sequence_number}")
            logger.info(f"[DB_SAVE_START] 数据库路径: {self.db_path}")
            # 关键字段摘要
            try:
                _summary = {
                    'test_item_name': row.get('test_item_name'),
                    'test_case_name': row.get('test_case_name'),
                    'test_case_number': row.get('test_case_number'),
                    'test_type': row.get('test_type'),
                }
                logger.info(f"[DB_SAVE_SUMMARY] 关键字段: {_summary}")
            except Exception:
                pass

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 使用本地时间写入创建/更新时间，避免 SQLite CURRENT_TIMESTAMP(UTC)
                _now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                INSERT INTO test_cases (
                    task_id, requirement_id, test_case_id, sequence_number, software_item_name, software_version,
                    test_round, requirement_traceability, test_item_name, test_item_identifier, test_case_name,
                    test_case_number, test_type, test_description, preconditions, prerequisites_constraints,
                    input_actions, input_conditions, expected_results, pass_criteria, case_designer, reviewer,
                    design_time, review_time, test_personnel, supervisor, test_time, test_result,
                    test_conclusion, issue_report_number, execution_year_month, issues_found_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id, sequence_number) DO UPDATE SET
                    requirement_id=excluded.requirement_id,
                    test_case_id=excluded.test_case_id,
                    software_item_name=excluded.software_item_name,
                    software_version=excluded.software_version,
                    test_round=excluded.test_round,
                    requirement_traceability=excluded.requirement_traceability,
                    test_item_name=excluded.test_item_name,
                    test_item_identifier=excluded.test_item_identifier,
                    test_case_name=excluded.test_case_name,
                    test_case_number=excluded.test_case_number,
                    test_type=excluded.test_type,
                    test_description=excluded.test_description,
                    preconditions=excluded.preconditions,
                    prerequisites_constraints=excluded.prerequisites_constraints,
                    input_actions=excluded.input_actions,
                    input_conditions=excluded.input_conditions,
                    expected_results=excluded.expected_results,
                    pass_criteria=excluded.pass_criteria,
                    case_designer=excluded.case_designer,
                    reviewer=excluded.reviewer,
                    design_time=excluded.design_time,
                    review_time=excluded.review_time,
                    test_personnel=excluded.test_personnel,
                    supervisor=excluded.supervisor,
                    test_time=excluded.test_time,
                    test_result=excluded.test_result,
                    test_conclusion=excluded.test_conclusion,
                    issue_report_number=excluded.issue_report_number,
                    execution_year_month=excluded.execution_year_month,
                    issues_found_count=excluded.issues_found_count,
                    updated_at=excluded.updated_at
            ''', (
                str(task_id), s(row.get('requirement_id')), s(row.get('test_case_id')), int(sequence_number),
                s(row.get('software_item_name')), s(row.get('software_version')), s(row.get('test_round')),
                s(row.get('requirement_traceability')), s(row.get('test_item_name')), s(row.get('test_item_identifier')),
                s(row.get('test_case_name')), s(row.get('test_case_number')), s(row.get('test_type')),
                s(row.get('test_description')), s(row.get('preconditions')), s(row.get('prerequisites_constraints')),
                s(row.get('input_actions')), s(row.get('input_conditions')), s(row.get('expected_results')),
                s(row.get('pass_criteria')), s(row.get('case_designer')), s(row.get('reviewer')),
                s(row.get('design_time')), s(row.get('review_time')), s(row.get('test_personnel')),
                s(row.get('supervisor')), s(row.get('test_time')), s(row.get('test_result')),
                s(row.get('test_conclusion')), s(row.get('issue_report_number')), s(row.get('execution_year_month')),
                row.get('issues_found_count') if isinstance(row.get('issues_found_count'), int) else 0,
                _now_local, _now_local
            ))
                conn.commit()
                logger.info(f"[DB_SAVE_OK] test_cases 已保存/更新：task_id={task_id}, sequence_number={sequence_number}")
                return
        except sqlite3.IntegrityError as e:
            logger.error(f"[DB_INTEGRITY_ERROR] 测试用例完整性错误 - task_id: {task_id}, seq: {sequence_number}, error: {str(e)}")
            import traceback
            logger.error(f"[DB_ERROR_STACK] 异常堆栈: {traceback.format_exc()}")
            raise
        except sqlite3.OperationalError as e:
            logger.error(f"[DB_OPERATIONAL_ERROR] 测试用例操作错误 - task_id: {task_id}, seq: {sequence_number}, error: {str(e)}")
            import traceback
            logger.error(f"[DB_ERROR_STACK] 异常堆栈: {traceback.format_exc()}")
            raise
        except Exception as e:
            logger.error(f"[DB_UNKNOWN_ERROR] 测试用例未知错误 - task_id: {task_id}, seq: {sequence_number}, error: {str(e)}, type: {type(e).__name__}")
            try:
                logger.error(f"[DB_ERROR_DETAILS] 详细参数 keys: {list(row.keys())}")
            except Exception:
                pass
            import traceback
            logger.error(f"[DB_ERROR_STACK] 异常堆栈: {traceback.format_exc()}")
            raise
    
    def get_project_plan_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID获取项目策划数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, task_id, plan_item_id, item_id, sequence_number, software_requirement,
                       standard_sub_requirement_name, standard_sub_requirement_unit, requirement_tracking,
                       importance, test_completed, requirement_analysis_personnel, document_review_personnel,
                       static_analysis_personnel, code_review_personnel, dynamic_test_personnel,
                       created_at, updated_at
                FROM project_plan 
                WHERE task_id = ? 
                ORDER BY sequence_number ASC, id ASC
            ''', (task_id,))
            
            columns = [
                'id', 'task_id', 'plan_item_id', 'item_id', 'sequence_number', 'software_requirement',
                'standard_sub_requirement_name', 'standard_sub_requirement_unit', 'requirement_tracking',
                'importance', 'test_completed', 'requirement_analysis_personnel', 'document_review_personnel',
                'static_analysis_personnel', 'code_review_personnel', 'dynamic_test_personnel',
                'created_at', 'updated_at'
            ]
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_project_plans(self) -> List[Dict[str, Any]]:
        """获取所有项目策划数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, task_id, plan_item_id, item_id, sequence_number, software_requirement,
                       standard_sub_requirement_name, standard_sub_requirement_unit, requirement_tracking,
                       importance, test_completed, requirement_analysis_personnel, document_review_personnel,
                       static_analysis_personnel, code_review_personnel, dynamic_test_personnel,
                       created_at, updated_at
                FROM project_plan 
                ORDER BY created_at DESC, sequence_number ASC
            ''')
            
            columns = [
                'id', 'task_id', 'plan_item_id', 'item_id', 'sequence_number', 'software_requirement',
                'standard_sub_requirement_name', 'standard_sub_requirement_unit', 'requirement_tracking',
                'importance', 'test_completed', 'requirement_analysis_personnel', 'document_review_personnel',
                'static_analysis_personnel', 'code_review_personnel', 'dynamic_test_personnel',
                'created_at', 'updated_at'
            ]
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_project_plan_field(self, id: int, field_name: str, field_value: Any) -> bool:
        """更新项目策划表中的特定字段"""
        # 定义允许更新的字段
        allowed_fields = [
            'item_id', 'sequence_number', 'software_requirement', 'standard_sub_requirement_name',
            'standard_sub_requirement_unit', 'requirement_tracking', 'importance', 'test_completed',
            'requirement_analysis_personnel', 'document_review_personnel', 'static_analysis_personnel',
            'code_review_personnel', 'dynamic_test_personnel'
        ]
        
        if field_name not in allowed_fields:
            print(f"字段 {field_name} 不允许更新")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 动态构建SQL语句
                sql = f"UPDATE project_plan SET {field_name} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                cursor.execute(sql, (field_value, id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"更新项目策划字段失败: {e}")
            return False 
    
    def get_requirement_analysis_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID获取需求分析数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, task_id, requirement_id, index_number, software_name, software_version, round_info,
                       standard_sub_requirement_name, standard_sub_requirement_identifier, standard_sub_requirement_unit,
                       task_requirement_trace, software_requirement_trace, software_requirement_name, software_requirement_identifier,
                       requirement_description, test_type, test_item_name, test_item_identifier, process_identifier,
                       requirement_sub_description, test_description, test_method, adequacy_requirement, pass_criteria,
                       created_at, updated_at
                FROM requirement_analysis 
                WHERE task_id = ? 
                ORDER BY index_number ASC, id ASC
            ''', (task_id,))
            
            columns = [
                'id', 'task_id', 'requirement_id', 'index_number', 'software_name', 'software_version', 'round_info',
                'standard_sub_requirement_name', 'standard_sub_requirement_identifier', 'standard_sub_requirement_unit',
                'task_requirement_trace', 'software_requirement_trace', 'software_requirement_name', 'software_requirement_identifier',
                'requirement_description', 'test_type', 'test_item_name', 'test_item_identifier', 'process_identifier',
                'requirement_sub_description', 'test_description', 'test_method', 'adequacy_requirement', 'pass_criteria',
                'created_at', 'updated_at'
            ]
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_requirement_analysis(self) -> List[Dict[str, Any]]:
        """获取所有需求分析数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, task_id, requirement_id, index_number, software_name, software_version, round_info,
                       standard_sub_requirement_name, standard_sub_requirement_identifier, standard_sub_requirement_unit,
                       task_requirement_trace, software_requirement_trace, software_requirement_name, software_requirement_identifier,
                       requirement_description, test_type, test_item_name, test_item_identifier, process_identifier,
                       requirement_sub_description, test_description, test_method, adequacy_requirement, pass_criteria,
                       created_at, updated_at
                FROM requirement_analysis 
                ORDER BY created_at DESC, index_number ASC
            ''')
            
            columns = [
                'id', 'task_id', 'requirement_id', 'index_number', 'software_name', 'software_version', 'round_info',
                'standard_sub_requirement_name', 'standard_sub_requirement_identifier', 'standard_sub_requirement_unit',
                'task_requirement_trace', 'software_requirement_trace', 'software_requirement_name', 'software_requirement_identifier',
                'requirement_description', 'test_type', 'test_item_name', 'test_item_identifier', 'process_identifier',
                'requirement_sub_description', 'test_description', 'test_method', 'adequacy_requirement', 'pass_criteria',
                'created_at', 'updated_at'
            ]
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_requirement_analysis_field(self, id: int, field_name: str, field_value: Any) -> bool:
        """更新需求分析表中的特定字段"""
        # 定义允许更新的字段
        allowed_fields = [
            'index_number', 'software_name', 'software_version', 'round_info',
            'standard_sub_requirement_name', 'standard_sub_requirement_identifier', 'standard_sub_requirement_unit',
            'task_requirement_trace', 'software_requirement_trace', 'software_requirement_name', 'software_requirement_identifier',
            'requirement_description', 'test_type', 'test_item_name', 'test_item_identifier', 'process_identifier',
            'requirement_sub_description', 'test_description', 'test_method', 'adequacy_requirement', 'pass_criteria'
        ]
        
        if field_name not in allowed_fields:
            print(f"字段 {field_name} 不允许更新")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 动态构建SQL语句
                sql = f"UPDATE requirement_analysis SET {field_name} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                cursor.execute(sql, (field_value, id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"更新需求分析字段失败: {e}")
            return False 
    
    def get_test_cases_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID获取测试用例数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, task_id, requirement_id, test_case_id, sequence_number, software_item_name, software_version,
                       test_round, requirement_traceability, test_item_name, test_item_identifier, test_case_name,
                       test_case_number, test_type, test_description, preconditions, prerequisites_constraints,
                       input_actions, input_conditions, expected_results, pass_criteria, case_designer, reviewer,
                       design_time, review_time, test_personnel, supervisor, test_time, test_result,
                       test_conclusion, issue_report_number, execution_year_month, issues_found_count,
                       created_at, updated_at
                FROM test_cases 
                WHERE task_id = ? 
                ORDER BY sequence_number ASC, id ASC
            ''', (task_id,))
            
            columns = [
                'id', 'task_id', 'requirement_id', 'test_case_id', 'sequence_number', 'software_item_name', 'software_version',
                'test_round', 'requirement_traceability', 'test_item_name', 'test_item_identifier', 'test_case_name',
                'test_case_number', 'test_type', 'test_description', 'preconditions', 'prerequisites_constraints',
                'input_actions', 'input_conditions', 'expected_results', 'pass_criteria', 'case_designer', 'reviewer',
                'design_time', 'review_time', 'test_personnel', 'supervisor', 'test_time', 'test_result',
                'test_conclusion', 'issue_report_number', 'execution_year_month', 'issues_found_count',
                'created_at', 'updated_at'
            ]
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_test_cases(self) -> List[Dict[str, Any]]:
        """获取所有测试用例数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, task_id, requirement_id, test_case_id, sequence_number, software_item_name, software_version,
                       test_round, requirement_traceability, test_item_name, test_item_identifier, test_case_name,
                       test_case_number, test_type, test_description, preconditions, prerequisites_constraints,
                       input_actions, input_conditions, expected_results, pass_criteria, case_designer, reviewer,
                       design_time, review_time, test_personnel, supervisor, test_time, test_result,
                       test_conclusion, issue_report_number, execution_year_month, issues_found_count,
                       created_at, updated_at
                FROM test_cases 
                ORDER BY created_at DESC, sequence_number ASC
            ''')
            
            columns = [
                'id', 'task_id', 'requirement_id', 'test_case_id', 'sequence_number', 'software_item_name', 'software_version',
                'test_round', 'requirement_traceability', 'test_item_name', 'test_item_identifier', 'test_case_name',
                'test_case_number', 'test_type', 'test_description', 'preconditions', 'prerequisites_constraints',
                'input_actions', 'input_conditions', 'expected_results', 'pass_criteria', 'case_designer', 'reviewer',
                'design_time', 'review_time', 'test_personnel', 'supervisor', 'test_time', 'test_result',
                'test_conclusion', 'issue_report_number', 'execution_year_month', 'issues_found_count',
                'created_at', 'updated_at'
            ]
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_test_case_field(self, id: int, field_name: str, field_value: Any) -> bool:
        """更新测试用例表中的特定字段"""
        # 定义允许更新的字段
        allowed_fields = [
            'test_case_id', 'sequence_number', 'software_item_name', 'software_version', 'test_round',
            'requirement_traceability', 'test_item_name', 'test_item_identifier', 'test_case_name',
            'test_case_number', 'test_type', 'test_description', 'preconditions', 'prerequisites_constraints',
            'input_actions', 'input_conditions', 'expected_results', 'pass_criteria', 'case_designer', 'reviewer',
            'design_time', 'review_time', 'test_personnel', 'supervisor', 'test_time', 'test_result',
            'test_conclusion', 'issue_report_number', 'execution_year_month', 'issues_found_count'
        ]
        
        if field_name not in allowed_fields:
            print(f"字段 {field_name} 不允许更新")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 动态构建SQL语句
                sql = f"UPDATE test_cases SET {field_name} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                cursor.execute(sql, (field_value, id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"更新测试用例字段失败: {e}")
            return False 