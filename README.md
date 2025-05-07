# 快速简历生成器
此为华中科技大学计科辅修班软件工程课设项目(hbw)
一款基于 PyQt6 和 FPDF2 的现代化简历制作工具，助您快速生成专业级简历

## ✨ 核心功能

- 🖋️ 可视化表单编辑，告别繁琐排版
- 📚 六大核心模块：个人信息、教育背景、工作经历、项目经验、技能专长、语言能力
- 🔄 实时预览效果，所见即所得
- 💾 简历数据本地保存（JSON格式），随时继续编辑
- 🚀 一键导出标准PDF，完美适配招聘网站
- 🎨 多主题切换（开发中）

## 🛠️ 安装指南

### 基础环境
- Python 3.9 或更高版本
- 推荐使用 Conda 环境管理

### 详细步骤

#### 使用 Conda（推荐）
```bash
# 创建专属虚拟环境
conda create -n resume python=3.9

# 激活环境
conda activate resume

# 安装必要依赖
pip install pyqt6 fpdf2

# 启动应用
python resume_builder.py
