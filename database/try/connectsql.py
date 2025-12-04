import pandas as pd
import mysql.connector
from mysql.connector import Error
import os

def execute_sql_file(cursor, conn, sql_file_path):
    """执行SQL文件创建表（需传入已连接的cursor和conn）"""
    if not os.path.exists(sql_file_path):
        print(f"❌ SQL文件不存在：{sql_file_path}")
        return False
    
    try:
        # 读取SQL文件内容
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 拆分SQL语句（过滤注释和空行）
        sql_statements = []
        for stmt in sql_content.split(';'):
            cleaned_stmt = '\n'.join([
                line.strip() for line in stmt.split('\n')
                if not line.strip().startswith('--') and line.strip()
            ])
            if cleaned_stmt:
                sql_statements.append(cleaned_stmt + ';')
        
        # 逐条执行SQL
        for stmt in sql_statements:
            cursor.execute(stmt)
            conn.commit()
        print(f"✅ SQL文件执行成功，表创建完成：{sql_file_path}")
        return True
    
    except Error as e:
        conn.rollback()
        print(f"❌ SQL文件执行失败：{e}")
        return False

# 1. 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "edu_agent"
}

# SQL文件路径（替换为你的实际路径，比如create_assistment2009.sql）
SQL_FILE_PATH = "/home/lst/Project_Edu/database/try/createtable.sql"

# 2. 连接MySQL并执行SQL文件创建表
conn = None
cursor = None
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ 数据库连接成功")
    
    # 执行SQL文件创建表
    if not execute_sql_file(cursor, conn, SQL_FILE_PATH):
        raise Exception("表创建失败，终止流程")

    # 3. 读取并预处理CSV
    csv_path = "/home/lst/data/assistment2009/skill_builder_data.csv"
    df = pd.read_csv(csv_path, low_memory=False)

    # 定义核心字段并筛选存在的列
    core_fields = ["user_id", "skill_name", "problem_id", "ms_first_response", "correct", "difficulty", "grade"]
    existing_fields = [f for f in core_fields if f in df.columns]
    df = df[existing_fields].drop_duplicates()

    # 处理skill_name缺失值和类型（关键修复）
    if "skill_name" in df.columns:
        df["skill_name"] = df["skill_name"].fillna("Unknown").astype(str)
    # 补全其他缺失值
    if "difficulty" in df.columns:
        df["difficulty"] = df.groupby("skill_name")["difficulty"].transform(
            lambda x: x.fillna(x.median()) if not x.isna().all() else 3
        )
    else:
        if {"problem_id", "correct"}.issubset(df.columns):
            problem_error = df.groupby("problem_id")["correct"].apply(
                lambda x: x.mean()
            ).reset_index(name="difficulty")
            df = df.merge(problem_error, on="problem_id", how="left")
    if "grade" in df.columns:
        df["grade"] = df["grade"].fillna("Unknown").astype(str)
    else:
        df["grade"] = "Unknown"

    # 标准化字段格式
    if "user_id" in df.columns:
        df["user_id"] = df["user_id"].astype(str)
    if "problem_id" in df.columns:
        df["problem_id"] = df["problem_id"].astype(str)

    print(f"✅ CSV预处理完成，有效数据行数：{len(df)}")

    # 4. 批量插入数据
    insert_sql = """
    INSERT IGNORE INTO assistment_raw (user_id, skill_name, problem_id, correct, difficulty, grade)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    batch_size = 1000  # 每批插入1000行（避免内存溢出）
    success_count = 0

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        values = [
            (
                str(row['user_id']),
                row['skill_name'],
                str(row['problem_id']),
                int(row['correct']),
                float(row['difficulty']),
                row['grade'] if pd.notna(row['grade']) else None
            )
            for _, row in batch.iterrows()
        ]
        
        try:
            cursor.executemany(insert_sql, values)
            conn.commit()
            success_count += len(values)
            print(f"已插入 {success_count}/{len(df)} 行")
        except Error as e:
            conn.rollback()
            print(f"批量插入失败（行{i}-{i+batch_size}）：{e}")

    print(f"✅ 数据导入完成，共插入 {success_count} 行")

except Error as e:
    print(f"❌ 数据库操作失败：{e}")
except Exception as e:
    print(f"❌ 流程终止：{e}")
finally:
    # 5. 关闭连接
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()
    print("✅ 数据库连接已关闭")