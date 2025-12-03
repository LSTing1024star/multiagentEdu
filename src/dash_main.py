import dash
from dash import dcc, html, Input, Output, State, callback
import json
from datetime import datetime
import sys
import os

# 添加项目路径
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)

# 导入数据处理和数据库管理模块
from functions.dataprocessor import AssistmentDataProcessor
from agents.Agent_dbmanager import DatabaseManagerAgent

# 初始化应用
app = dash.Dash(__name__, title="教育智能助手可视化面板（真实数据版）")
server = app.server

# 初始化数据库管理智能体（对接真实CSV数据）
# 请根据实际CSV文件路径修改data_path参数
db_agent = DatabaseManagerAgent(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")

# 从数据中获取有效学生ID列表（用于下拉选择）
valid_student_ids = list(db_agent.student_basic_data.keys())
# 从知识图谱获取有效知识点（用于学科/知识点选择）
knowledge_points = []
for category, skills in db_agent.knowledge_graph.items():
    knowledge_points.extend(skills) if isinstance(skills, list) else None
knowledge_points = list(set(knowledge_points))

# 页面布局
app.layout = html.Div([
    # 标题区
    html.Div([
        html.H1("教育智能助手（真实数据版）", style={"textAlign": "center", "padding": "20px"})
    ]),
    
    # 输入区
    html.Div([
        html.Div([
            html.Label("学生ID:"),
            dcc.Dropdown(
                id="student-id",
                options=[{"label": id, "value": id} for id in valid_student_ids[:10]],  # 显示前10个学生
                value=valid_student_ids[0] if valid_student_ids else "S92523",
                style={"width": "100%", "marginBottom": "10px"}
            )
        ], style={"width": "20%", "padding": "10px"}),
        
        html.Div([
            html.Label("知识点:"),
            dcc.Dropdown(
                id="knowledge-point",
                options=[{"label": kp, "value": kp} for kp in knowledge_points[:10]],  # 显示前10个知识点
                value=knowledge_points[0] if knowledge_points else "Addition",
                style={"width": "100%", "marginBottom": "10px"}
            )
        ], style={"width": "20%", "padding": "10px"}),
        
        html.Div([
            html.Label("长期目标:"),
            dcc.Input(
                id="long-term-goal",
                value="提升薄弱知识点掌握度",
                style={"width": "100%", "marginBottom": "10px"}
            )
        ], style={"width": "30%", "padding": "10px"}),
        
        html.Div([
            html.Label("问题描述:"),
            dcc.Input(
                id="question-desc",
                placeholder="输入关于该知识点的问题...",
                style={"width": "100%", "marginBottom": "10px"}
            )
        ], style={"width": "30%", "padding": "10px"})
    ], style={"display": "flex", "flexWrap": "wrap"}),
    
    # 功能选择区
    html.Div([
        html.Button("1. 学生画像", id="btn-student-profile", style={"margin": "5px", "padding": "8px 15px"}),
        html.Button("2. 知识点分析", id="btn-knowledge-analysis", style={"margin": "5px", "padding": "8px 15px"}),
        html.Button("3. 资源推荐", id="btn-resource-recommend", style={"margin": "5px", "padding": "8px 15px"}),
    ], style={"textAlign": "center", "margin": "20px"}),
    
    # 结果展示区
    html.Div([
        html.Div(id="result-container", style={
            "border": "1px solid #ddd",
            "borderRadius": "5px",
            "padding": "20px",
            "margin": "10px"
        })
    ]),

    # 数据统计区
    html.Div([
        html.H3("数据集统计", style={"textAlign": "center", "marginTop": "30px"}),
        html.Div(id="data-stats", style={
            "border": "1px solid #ddd",
            "borderRadius": "5px",
            "padding": "20px",
            "margin": "10px"
        })
    ])
])

# 初始化数据集统计信息
@callback(
    Output("data-stats", "children"),
    Input("btn-student-profile", "n_clicks"),
    prevent_initial_call=False
)
def init_data_stats(n_clicks):
    stats = db_agent.get_resource_statistics()
    return [
        html.P(f"总资源数: {stats.get('总资源数', 'N/A')}"),
        html.P(f"平均错误率: {stats.get('平均错误率', 'N/A')}"),
        html.P(f"难度分布: {', '.join([f'{k}级: {v}个' for k, v in stats.get('难度分布', {}).items()])}"),
        html.P(f"资源格式分布: {', '.join([f'{k}: {v}个' for k, v in stats.get('格式分布', {}).items()])}")
    ]

# 学生画像展示
@callback(
    Output("result-container", "children"),
    Input("btn-student-profile", "n_clicks"),
    State("student-id", "value"),
    prevent_initial_call=True
)
def show_student_profile(n_clicks, student_id):
    student_data = db_agent.query_student_basic(student_id)
    if "error" in student_data:
        return html.P(f"错误: {student_data['error']}")
    
    return [
        html.H3("👤 学生画像"),
        html.P(f"学生ID: {student_id} | 查询时间: {datetime.now().strftime('%H:%M:%S')}"),
        html.Div([
            html.Div([
                html.H4("基础信息"),
                html.P(f"年级: {student_data.get('grade', '未知')}"),
                html.P(f"学科: {student_data.get('subject', '未知')}"),
                html.P(f"学习偏好: {student_data.get('learning_preference', '未知')}")
            ], style={"width": "50%", "float": "left"}),
            html.Div([
                html.H4("行为画像"),
                html.P(f"答题正确率: {student_data.get('behavior_portrait', {}).get('accuracy', '未知')}"),
                html.P(f"总答题数: {student_data.get('behavior_portrait', {}).get('total_problems', '未知')}"),
                html.P(f"已掌握知识点: {', '.join(student_data.get('behavior_portrait', {}).get('mastered_skills', ['无']))}")
            ], style={"width": "50%", "float": "left"})
        ]),
        html.Div(style={"clear": "both"})
    ]

# 知识点分析展示
@callback(
    Output("result-container", "children", allow_duplicate=True),
    Input("btn-knowledge-analysis", "n_clicks"),
    State("knowledge-point", "value"),
    prevent_initial_call=True
)
def show_knowledge_analysis(n_clicks, knowledge_point):
    # 查询知识点关联关系
    related = db_agent.query_knowledge_relation(knowledge_point)
    # 查询该知识点的资源（获取错误率和难度）
    resource = db_agent.query_resource(knowledge_point=knowledge_point)
    
    return [
        html.H3(f"📚 知识点分析: {knowledge_point}"),
        html.P(f"查询时间: {datetime.now().strftime('%H:%M:%S')}"),
        html.Div([
            html.Div([
                html.H4("关联知识点"),
                html.Ul([html.Li(rel) for rel in related])
            ], style={"width": "50%", "float": "left"}),
            html.Div([
                html.H4("资源数据"),
                html.P(f"错误率: {resource.get('error_rate', '未知') if resource else '无数据'}"),
                html.P(f"难度等级: {resource.get('difficulty_level', '未知') if resource else '无数据'}"),
                html.P(f"平均正确率: {resource.get('avg_correct_rate', '未知') if resource else '无数据'}")
            ], style={"width": "50%", "float": "left"})
        ]),
        html.Div(style={"clear": "both"})
    ]

# 资源推荐展示
@callback(
    Output("result-container", "children", allow_duplicate=True),
    Input("btn-resource-recommend", "n_clicks"),
    State("student-id", "value"),
    State("knowledge-point", "value"),
    prevent_initial_call=True
)
def show_resource_recommendation(n_clicks, student_id, knowledge_point):
    student_data = db_agent.query_student_basic(student_id)
    # 根据学生学习偏好和知识点查询资源
    resource = db_agent.query_resource(
        knowledge_point=knowledge_point,
        format=student_data.get("learning_preference", "text")
    )
    
    if not resource:
        # 如果没有匹配格式的资源，查询任意格式
        resource = db_agent.query_resource(knowledge_point=knowledge_point)
    
    return [
        html.H3("📖 资源推荐"),
        html.P(f"学生ID: {student_id} | 知识点: {knowledge_point} | 查询时间: {datetime.now().strftime('%H:%M:%S')}"),
        html.Div([
            html.H4(f"推荐资源: {resource.get('resource_id', '无')}" if resource else "无匹配资源"),
            resource and html.Ul([
                html.Li(f"知识点: {resource.get('knowledge_point')}"),
                html.Li(f"格式: {resource.get('format')}"),
                html.Li(f"难度等级: {resource.get('difficulty_level')}"),
                html.Li(f"完成标准: {resource.get('completion_standard')}"),
                html.Li(f"相关题目: {', '.join(resource.get('related_problems', []))}")
            ]) or html.P("未找到相关学习资源")
        ])
    ]

if __name__ == "__main__":
    app.run(host="0.0.0.0",
    port=8050,
    debug=True)