import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional

class MySQLConnector:
    def __init__(self, host: str, user: str, password: str, database: Optional[str] = None):
        """初始化数据库连接参数"""
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database  # 可选：直接连接到指定数据库
            )
            if self.connection.is_connected():
                print(f"✅ 成功连接到数据库: {self.database or 'MySQL服务器'}")
                return True
        except Error as e:
            print(f"❌ 连接失败: {e}")
            return False

    def execute_sql(self, sql: str, params: Optional[tuple] = None) -> bool:
        """执行单条SQL语句（CREATE/INSERT/UPDATE/DELETE等）"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params or ())
            self.connection.commit()  # 提交事务
            print(f"✅ SQL执行成功: {sql[:50]}...")
            return True
        except Error as e:
            self.connection.rollback()  # 出错时回滚
            print(f"❌ SQL执行失败: {e} (SQL: {sql[:50]}...)")
            return False
        finally:
            if cursor:
                cursor.close()

    def execute_sql_file(self, file_path: str) -> bool:
        """执行SQL文件（如创建表结构）"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False

        cursor = None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            # 按分号分割SQL语句（处理多行语句）
            sql_commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]

            cursor = self.connection.cursor()
            for cmd in sql_commands:
                cursor.execute(cmd)
            self.connection.commit()
            print(f"✅ SQL文件执行成功: {file_path}")
            return True
        except Error as e:
            self.connection.rollback()
            print(f"❌ SQL文件执行失败: {e} (文件: {file_path})")
            return False
        except FileNotFoundError:
            print(f"❌ 文件不存在: {file_path}")
            return False
        finally:
            if cursor:
                cursor.close()

    def query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行查询语句，返回字典格式结果"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return []

        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)  # 返回字典（字段名:值）
            cursor.execute(sql, params or ())
            result = cursor.fetchall()
            print(f"✅ 查询成功，返回 {len(result)} 条数据")
            return result
        except Error as e:
            print(f"❌ 查询失败: {e} (SQL: {sql[:50]}...)")
            return []
        finally:
            if cursor:
                cursor.close()

    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ 数据库连接已关闭")