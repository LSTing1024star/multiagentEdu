启动 API 服务 (和之前一样):
```bash
python main.py
```

运行实验数据分析:
```bash
python main.py --analyze
```

运行此命令时，请确保 main.py 中 analyze_assessment_accuracy 和 analyze_plan_effectiveness 函数里的文件路径指向你实际的数据文件。我在代码中使用了 os.path.join(project_root, "data", "...")，这意味着它期望你的项目根目录下有一个 data 文件夹，里面存放着这些 CSV 文件。你可以根据你的实际情况修改这些路径。