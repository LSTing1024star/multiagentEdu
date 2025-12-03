from db_utils import MySQLConnector

# 数据库配置（请替换为你的实际信息）
DB_CONFIG = {
    "host": "localhost",    # 数据库主机（通常是localhost）
    "user": "ting",  # 例如root或管理员提供的用户
    "password": "123",
    "database": None        # 初始不指定数据库，先创建
}

# 初始化连接器
db = MySQLConnector(**DB_CONFIG)

# 1. 连接到MySQL服务器（不指定数据库）
if not db.connect():
    exit(1)

# 2. 创建数据库edu_agent
create_db_sql = """
CREATE DATABASE IF NOT EXISTS edu_agent 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_general_ci;
"""
if not db.execute_sql(create_db_sql):
    db.close()
    exit(1)

# 3. 切换到edu_agent数据库（重新连接指定数据库）
db.database = "edu_agent"
if not db.connect():  # 重新连接到新数据库
    db.close()
    exit(1)

# 4. 导入表结构（替换为你的SQL文件路径）
sql_file_path = "/home/lst/Project_Edu/database/init_assistment_tables.sql"
if not db.execute_sql_file(sql_file_path):
    db.close()
    exit(1)

# 5. 验证表是否创建成功
tables = db.query("SHOW TABLES;")
print("当前数据库中的表：")
for table in tables:
    print(f"- {table}")

    import pandas as pd

# 6. 读取CSV文件（替换为你的CSV路径）
csv_path = "/home/lst/data/skill_builder_data.csv"
try:
    df = pd.read_csv(csv_path)
    print(f"✅ 成功读取CSV文件，共 {len(df)} 行数据")
except Exception as e:
    print(f"❌ 读取CSV失败: {e}")
    db.close()
    exit(1)

# 7. 导入数据到assistment_raw表（根据表结构调整字段映射）
insert_sql = """
INSERT INTO assistment_raw 
(user_id, skill_name, problem_id, correct, difficulty, grade)
VALUES (%s, %s, %s, %s, %s, %s)
"""

# 批量插入（每1000行提交一次，避免内存溢出）
batch_size = 1000
success_count = 0

for i in range(0, len(df), batch_size):
    batch_data = df.iloc[i:i+batch_size]
    values_list = []
    
    for _, row in batch_data.iterrows():
        # 处理空值和类型转换（根据实际CSV字段调整）
        values = (
            str(row.get("user_id", "")),
            row.get("skill_name", ""),
            str(row.get("problem_id", "")),
            int(row.get("correct", 0)),
            float(row.get("difficulty", 0)) if pd.notna(row.get("difficulty")) else None,
            row.get("grade", "")
        )
        values_list.append(values)
    
    # 执行批量插入
    cursor = db.connection.cursor()
    try:
        cursor.executemany(insert_sql, values_list)
        db.connection.commit()
        success_count += len(values_list)
        print(f"已导入 {success_count}/{len(df)} 行数据")
    except Error as e:
        db.connection.rollback()
        print(f"❌ 批量插入失败: {e}（行范围：{i}-{i+batch_size}）")
    finally:
        cursor.close()

print(f"✅ 数据导入完成，成功插入 {success_count} 行")

# 8. 验证数据是否导入成功
count = db.query("SELECT COUNT(*) AS total FROM assistment_raw;")
if count:
    print(f"assistment_raw表总数据量：{count[0]['total']}")

# 9. 关闭连接
db.close()