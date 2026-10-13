import sqlite3
import os
from typing import List, Dict, Optional
from pathlib import Path

class RegressionTestDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 数据库文件放在db目录下
            db_dir = Path(__file__).parent
            db_path = db_dir / "regression_test.db"
        
        self.db_path = str(db_path)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建领域表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建测试主管表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_managers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建测试人员表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_personnel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建开发人员表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS developers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建飞机型号表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aircraft_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建项目总师表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_directors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建研制部门表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS development_departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建主任设计师表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chief_designers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建组件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            
            # 插入初始数据
            self._insert_initial_data()
    
    def _insert_initial_data(self):
        """插入初始数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 初始领域数据
            domains = [
                ('通用软件',),
                ('嵌入式软件',),
                ('Web应用',),
                ('移动应用',),
                ('系统软件',),
                ('回归测试专用',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO domains (name) VALUES (?)', domains)
            
            # 初始测试主管数据
            managers = [
                ('张三',),
                ('李四',),
                ('王五',),
                ('回归主管',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO test_managers (name) VALUES (?)', managers)
            
            # 初始测试人员数据
            personnel = [
                ('测试员A',),
                ('测试员B',),
                ('测试员C',),
                ('回归测试员',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO test_personnel (name) VALUES (?)', personnel)
            
            # 初始开发人员数据
            developers = [
                ('开发者A',),
                ('开发者B',),
                ('开发者C',),
                ('回归开发者',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO developers (name) VALUES (?)', developers)
            
            # 初始飞机型号数据
            aircraft_models = [
                ('F-16',),
                ('F-35',),
                ('歼-20',),
                ('歼-10',),
                ('回归测试专用机型',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO aircraft_models (name) VALUES (?)', aircraft_models)
            
            # 初始项目总师数据
            project_directors = [
                ('王总师',),
                ('李总师',),
                ('赵总师',),
                ('回归测试总师',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO project_directors (name) VALUES (?)', project_directors)
            
            # 初始研制部门数据
            departments = [
                ('系统集成部',),
                ('软件研发部',),
                ('测试验证部',),
                ('质量保证部',),
                ('回归测试部',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO development_departments (name) VALUES (?)', departments)
            
            # 初始主任设计师数据
            chief_designers = [
                ('张设计师',),
                ('刘设计师',),
                ('陈设计师',),
                ('回归测试设计师',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO chief_designers (name) VALUES (?)', chief_designers)
            
            # 初始组件数据
            components = [
                ('雷达组件',),
                ('红外组件',),
                ('吊舱组件',)
            ]
            cursor.executemany('INSERT OR IGNORE INTO components (name) VALUES (?)', components)
            
            conn.commit()
    
    def get_domains(self) -> List[Dict[str, str]]:
        """获取所有领域"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM domains ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def get_test_managers(self) -> List[Dict[str, str]]:
        """获取所有测试主管"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM test_managers ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def get_test_personnel(self) -> List[Dict[str, str]]:
        """获取所有测试人员"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM test_personnel ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def get_developers(self) -> List[Dict[str, str]]:
        """获取所有开发人员"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM developers ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def add_domain(self, name: str) -> bool:
        """添加新领域"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO domains (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def add_test_manager(self, name: str) -> bool:
        """添加新测试主管"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO test_managers (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def add_test_personnel(self, name: str) -> bool:
        """添加新测试人员"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO test_personnel (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def add_developer(self, name: str) -> bool:
        """添加新开发人员"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO developers (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_aircraft_models(self) -> List[Dict[str, str]]:
        """获取所有飞机型号"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM aircraft_models ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def get_project_directors(self) -> List[Dict[str, str]]:
        """获取所有项目总师"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM project_directors ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def get_development_departments(self) -> List[Dict[str, str]]:
        """获取所有研制部门"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM development_departments ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def get_chief_designers(self) -> List[Dict[str, str]]:
        """获取所有主任设计师"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM chief_designers ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def get_components(self) -> List[Dict[str, str]]:
        """获取所有组件"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM components ORDER BY name')
            return [{'value': row['name'], 'label': row['name']} for row in cursor.fetchall()]
    
    def add_aircraft_model(self, name: str) -> bool:
        """添加新飞机型号"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO aircraft_models (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def add_project_director(self, name: str) -> bool:
        """添加新项目总师"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO project_directors (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def add_development_department(self, name: str) -> bool:
        """添加新研制部门"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO development_departments (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def add_chief_designer(self, name: str) -> bool:
        """添加新主任设计师"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO chief_designers (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def add_component(self, name: str) -> bool:
        """添加新组件"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO components (name) VALUES (?)', (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

# 创建全局数据库实例
regression_db_instance = RegressionTestDatabase() 