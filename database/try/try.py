import pandas as pd

# 读取CSV（替换为你的文件路径）
csv_path = "/home/lst/data/assistment2009/skill_builder_data.csv"
df = pd.read_csv(csv_path, low_memory=False)

# 1. 查看字段名（列名）
print("CSV字段名：", df.columns.tolist())

# 2. 查看数据类型（pandas推断的类型）
print("\n数据类型：")
print(df.dtypes)

# 3. 查看各字段的最大长度（用于定义MySQL的VARCHAR长度）
print("\n各字段最大长度：")
for col in df.select_dtypes(include=['object']).columns:  # 仅字符串字段
    max_len = df[col].astype(str).str.len().max()
    print(f"{col}: {max_len}（建议VARCHAR({int(max_len*1.2)})）")

# 4. 查看是否有缺失值
print("\n缺失值统计：")
print(df.isnull().sum())