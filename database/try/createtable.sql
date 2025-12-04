USE edu_agent;

CREATE TABLE IF NOT EXISTS assistment_raw(
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(84) NOT NULL,
    problem_id INT NOT NULL,
    correct TINYINT NOT NULL,
    difficulty FLOAT NOT NULL,
    grade VARCHAR(20) NOT NULL,
    ms_first_response INT NOT NULL,
    overlap_time INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_record(user_id,problem_id,ms_first_response)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;