USE edu_agent;

-- 1. 原始数据集表（存储skill_builder_data.csv的核心字段）
CREATE TABLE IF NOT EXISTS assistment_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,  -- 学生ID（对应数据集中的user_id）
    skill_name VARCHAR(100) NOT NULL,  -- 知识点名称
    problem_id VARCHAR(20) NOT NULL,  -- 题目ID
    correct TINYINT NOT NULL,  -- 是否正确（1=正确，0=错误）
    difficulty FLOAT,  -- 题目难度（原始数据中的difficulty字段）
    grade VARCHAR(20),  -- 年级（如"Grade 7"）
    error_rate FLOAT,  -- 题目错误率（衍生字段，1 - 正确率）
    difficulty_level INT,  -- 难度等级（1-5级，衍生字段）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_record (user_id, problem_id)  -- 避免重复数据
);

-- 2. 学生信息表（从原始数据中提取的学生基础信息）
CREATE TABLE IF NOT EXISTS students (
    student_id VARCHAR(20) PRIMARY KEY,  -- 格式化为"S+user_id"（如"S92523"）
    original_user_id VARCHAR(20) NOT NULL,  -- 原始数据集的user_id（用于关联）
    grade VARCHAR(20) NOT NULL,  -- 年级（如"初一"）
    subject VARCHAR(20) DEFAULT 'math',  -- 默认为数学（数据集主要是数学题）
    learning_preference VARCHAR(20),  -- 学习偏好（video/text）
    accuracy FLOAT,  -- 平均正确率（衍生字段）
    total_problems INT,  -- 总做题数（衍生字段）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (original_user_id) REFERENCES assistment_raw(user_id)
);

-- 3. 学生答题记录表（新增/修改：包含用户指定的唯一约束）
CREATE TABLE IF NOT EXISTS student_problem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL,  -- 关联students表的student_id
    original_problem_id VARCHAR(20) NOT NULL,  -- 原始题目ID（关联assistment_raw）
    interaction_time DATETIME(6) NOT NULL,  -- 高精度时间戳（毫秒级）
    attempt_number INT NOT NULL,  -- 答题次数（第N次作答）
    correct TINYINT,  -- 本次答题是否正确
    time_spent INT,  -- 答题耗时（秒）
    hint_used TINYINT DEFAULT 0,  -- 是否使用提示（1=是，0=否）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- 外键关联
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (original_problem_id) REFERENCES assistment_raw(problem_id),
    -- 用户指定的唯一约束：学生+题目+时间+答题次数 组合唯一
    UNIQUE KEY unique_attempt (student_id, original_problem_id, interaction_time, attempt_number)
);

-- 4. 学生知识点掌握表（记录学生已掌握的知识点）
CREATE TABLE IF NOT EXISTS student_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL,
    skill_name VARCHAR(100) NOT NULL,  -- 知识点名称
    mastery_status TINYINT DEFAULT 1,  -- 1=已掌握，0=未掌握（根据correct字段判断）
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    UNIQUE KEY unique_student_skill (student_id, skill_name)  -- 避免重复记录
);

-- 5. 学习资源表（从题目数据中提取的学习资源信息）
CREATE TABLE IF NOT EXISTS learning_resources (
    resource_id VARCHAR(20) PRIMARY KEY,  -- 格式化为"r_+problem_id"（如"r_P001"）
    original_problem_id VARCHAR(20) NOT NULL,  -- 原始题目ID
    knowledge_point VARCHAR(100) NOT NULL,  -- 对应知识点（即skill_name）
    error_rate FLOAT NOT NULL,  -- 错误率
    difficulty_level INT NOT NULL,  -- 难度等级（1-5）
    format_type VARCHAR(10),  -- 资源格式（video/text）
    avg_correct_rate FLOAT,  -- 平均正确率
    completion_standard VARCHAR(100),  -- 完成标准（如"5道题≥80%正确率"）
    FOREIGN KEY (original_problem_id) REFERENCES assistment_raw(problem_id)
);

-- 6. 知识点关联表（知识图谱数据）
CREATE TABLE IF NOT EXISTS knowledge_relations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_category VARCHAR(50) NOT NULL,  -- 父分类（如"代数基础"）
    skill_name VARCHAR(100) NOT NULL,  -- 知识点名称（如"Addition"）
    UNIQUE KEY unique_skill_category (parent_category, skill_name)  -- 避免重复关联
);

CREATE TABLE IF NOT EXISTS student_agent_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,  -- 关联系统内部学生ID（来自students_info表）
    agent_id VARCHAR(50) NOT NULL,  -- 智能体标识（如"assessment_agent"、"tutor_agent"）
    interaction_type VARCHAR(30) NOT NULL,  -- 交互类型（如"学业评估"、"资源推荐"、"知识点答疑"）
    user_query TEXT NOT NULL,  -- 学生输入的问题/请求
    agent_response TEXT NOT NULL,  -- 智能体的回复内容
    related_knowledge VARCHAR(255),  -- 本次交互涉及的知识点（多个用逗号分隔，如"一元二次方程,几何证明"）
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 交互开始时间
    end_time TIMESTAMP,  -- 交互结束时间（智能体回复完成时间）
    status VARCHAR(20) DEFAULT 'completed',  -- 交互状态（completed=完成，interrupted=中断）
    -- 外键关联（确保学生存在）
    FOREIGN KEY (student_id) REFERENCES students_info(student_id),
    -- 索引优化（按学生ID和时间查询历史对话）
    INDEX idx_student_time (student_id, start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;