# -*- coding: utf-8 -*-
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
                             QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
                             QTabWidget, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
from fpdf import FPDF
import json
import os

# --- 中文字体设置 ---
CHINESE_FONT_PATH = 'C:/Windows/Fonts/simkai.ttf' # <--- 确认或修改路径
CHINESE_FONT_NAME = 'chinese'

class PDF(FPDF):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加中文字体
        try:
            self.add_font(CHINESE_FONT_NAME, '', CHINESE_FONT_PATH)
            self.add_font(CHINESE_FONT_NAME, 'B', CHINESE_FONT_PATH) # 粗体
            self.add_font(CHINESE_FONT_NAME, 'I', CHINESE_FONT_PATH) # 斜体
            self.font_added = True
            print(f"成功加载字体: {CHINESE_FONT_PATH}")
        except Exception as e:
            print(f"错误：无法加载字体文件 '{CHINESE_FONT_PATH}'. 请确保文件存在且路径正确。")
            print(f"错误信息: {e}")
            print("PDF中的中文将无法正常显示或样式不全。")
            self.font_added = False

    def header(self):
        pass

    def footer(self):
        self.set_y(-15) # 距离底部1.5厘米
        if self.font_added:
            self.set_font(CHINESE_FONT_NAME, '', 8) # 页脚使用普通字体
        else:
            self.set_font('Arial', 'I', 8) # Fallback
        self.set_text_color(128, 128, 128) # 灰色页脚
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')

    def set_chinese_font(self, style='', size=12):
        """设置中文字体（如果已加载）"""
        if self.font_added:
            try:
                self.set_font(CHINESE_FONT_NAME, style, size)
            except RuntimeError:
                 print(f"警告：字体 '{CHINESE_FONT_NAME}' 可能不支持样式 '{style}'，回退到常规样式。")
                 self.set_font(CHINESE_FONT_NAME, '', size)
        else:
            self.set_font('Arial', style, size) # Fallback

    def multi_cell_chinese(self, w, h, txt, border=0, align='J', fill=False):
        """支持中文的 multi_cell"""
        if self.font_added:
            self.multi_cell(w, h, txt, border, align, fill)
        else:
            print(f"警告: 中文字体未加载，尝试输出多行文本: {txt[:30]}...")
            self.multi_cell(w, h, txt, border, align, fill) # 尝试输出

    def cell_chinese(self, w, h=0, txt="", border=0, ln=0, align="", fill=False, link=""):
         """支持中文的 cell"""
         if self.font_added:
             self.cell(w, h, txt, border, ln, align, fill, link)
         else:
            print(f"警告: 中文字体未加载，尝试输出单元格文本: {txt[:30]}...")
            self.cell(w, h, txt, border, ln, align, fill, link) # 尝试输出


class ResumeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简历生成器")
        self.setGeometry(100, 100, 900, 700)

        # --- 跟踪当前正在编辑的条目索引 ---
        self.editing_index = {
            "education": None,
            "experience": None,
            "projects": None,
            "skills": None,
            "languages": None
        }

        # 简历数据结构
        self.reset_resume_data()

        # 初始化UI
        self.init_ui()

    def reset_resume_data(self):
        """重置简历数据结构"""
        self.resume_data = {
            "personal_info": {
                "name": "", "email": "", "phone": "", "address": "",
                "linkedin": "", "github": "", "summary": ""
            },
            "education": [], "experience": [], "projects": [],
            "skills": [], "languages": []
        }
        # 重置编辑状态
        for key in self.editing_index:
            self.editing_index[key] = None


    def init_ui(self):

        # 中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 左侧表单区域 (使用QTabWidget组织不同部分)
        self.tabs = QTabWidget()

        # --- 创建各个标签页 ---
        personal_tab = self.create_personal_info_tab()
        self.tabs.addTab(personal_tab, "个人信息")

        education_tab = self.create_education_tab()
        self.tabs.addTab(education_tab, "教育经历")

        experience_tab = self.create_experience_tab()
        self.tabs.addTab(experience_tab, "工作经历")

        projects_tab = self.create_projects_tab()
        self.tabs.addTab(projects_tab, "项目经历")

        skills_tab = self.create_skills_tab()
        self.tabs.addTab(skills_tab, "技能")

        languages_tab = self.create_languages_tab()
        self.tabs.addTab(languages_tab, "语言能力")

        # --- 右侧控制按钮区域 ---
        control_widget = QWidget()
        control_layout = QVBoxLayout()
        control_widget.setLayout(control_layout)
        control_widget.setFixedWidth(180) # 给控制区域一个固定宽度

        # 按钮样式
        button_style = """
        QPushButton {
            background-color: #%s;
            color: white;
            padding: 8px;
            border-radius: 4px;
            min-height: 25px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #%s;
        }
        QPushButton:pressed {
            background-color: #%s;
        }
        """
        def create_styled_button(text, color_hex, hover_hex, pressed_hex):
            btn = QPushButton(text)
            btn.setStyleSheet(button_style % (color_hex, hover_hex, pressed_hex))
            return btn

        preview_btn = create_styled_button("预览简历", "4CAF50", "45a049", "3c8a40")
        preview_btn.clicked.connect(self.preview_resume)
        control_layout.addWidget(preview_btn)

        export_btn = create_styled_button("导出PDF", "2196F3", "1e88e5", "1976d2")
        export_btn.clicked.connect(self.export_to_pdf)
        control_layout.addWidget(export_btn)

        save_btn = create_styled_button("保存简历", "FF9800", "fb8c00", "f57c00")
        save_btn.clicked.connect(self.save_resume)
        control_layout.addWidget(save_btn)

        load_btn = create_styled_button("加载简历", "9C27B0", "8e24aa", "7b1fa2")
        load_btn.clicked.connect(self.load_resume)
        control_layout.addWidget(load_btn)

        clear_btn = create_styled_button("清空所有", "F44336", "e53935", "d32f2f")
        clear_btn.clicked.connect(self.clear_all)
        control_layout.addWidget(clear_btn)

        control_layout.addStretch() # 弹性空间将按钮推到顶部

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True) # 允许换行
        control_layout.addWidget(self.status_label)

        # 添加到主布局
        main_layout.addWidget(self.tabs, stretch=4) # 左侧占更大比例
        main_layout.addWidget(control_widget, stretch=1) # 右侧占较小比例

    def create_personal_info_tab(self):

        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()

        basic_layout.addRow("姓名*:", self.name_edit)
        basic_layout.addRow("邮箱*:", self.email_edit)
        basic_layout.addRow("电话*:", self.phone_edit)
        basic_layout.addRow("地址:", self.address_edit)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 在线资料
        online_group = QGroupBox("在线资料")
        online_layout = QFormLayout()

        self.linkedin_edit = QLineEdit()
        self.github_edit = QLineEdit()

        online_layout.addRow("LinkedIn:", self.linkedin_edit)
        online_layout.addRow("GitHub:", self.github_edit)

        online_group.setLayout(online_layout)
        layout.addWidget(online_group)

        # 个人简介
        summary_group = QGroupBox("个人简介 / 职业目标")
        summary_layout = QVBoxLayout()

        self.summary_edit = QTextEdit()
        self.summary_edit.setPlaceholderText("简要描述你的专业背景、职业目标和核心优势...")
        self.summary_edit.setFixedHeight(100) # 给一个初始高度

        summary_layout.addWidget(self.summary_edit)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        layout.addStretch()

        return tab

    # --- 更新列表显示的方法 ---
    def update_education_list(self):
        self.education_list.clear()
        for i, edu in enumerate(self.resume_data["education"]):
            degree_str = f" ({edu['degree']})" if edu.get('degree') else ""
            item_text = f"{edu.get('school','N/A')} - {edu.get('major','N/A')}{degree_str} [{edu.get('start_year','?')}-{edu.get('end_year','?')}]"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, i) # 存储原始索引
            self.education_list.addItem(item)

    def update_experience_list(self):
        self.experience_list.clear()
        for i, exp in enumerate(self.resume_data["experience"]):
            item_text = f"{exp.get('company','N/A')} - {exp.get('position','N/A')} [{exp.get('start_date','?')} 至 {exp.get('end_date','?')}]"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.experience_list.addItem(item)

    def update_projects_list(self):
        self.projects_list.clear()
        for i, project in enumerate(self.resume_data["projects"]):
            date_str = f" ({project['date']})" if project.get('date') else ""
            item_text = f"{project.get('name','N/A')}{date_str} - {project.get('role','N/A')}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.projects_list.addItem(item)

    def update_skills_list(self):
        self.skills_list.clear()
        # 为了编辑功能，这里使用简单列表显示，并存储原始索引
        for i, skill in enumerate(self.resume_data["skills"]):
             level_str = f" ({skill['level']})" if skill.get('level') and skill['level'] != '未指定' else ""
             type_str = f" [{skill.get('type', '未分类')}]" # 显示类别以便区分
             item_text = f"{skill.get('name','N/A')}{level_str}{type_str}"
             item = QListWidgetItem(item_text)
             item.setData(Qt.ItemDataRole.UserRole, i) # 存储原始索引
             self.skills_list.addItem(item)

    def update_languages_list(self):
        self.languages_list.clear()
        for i, language in enumerate(self.resume_data["languages"]):
            level_str = f" ({language['level']})" if language.get('level') and language['level'] != '未指定' else ""
            item_text = f"{language.get('name','N/A')}{level_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.languages_list.addItem(item)

    def create_education_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        list_group = QGroupBox("已添加的教育经历 (单击条目进行编辑)") # 提示用户可以点击
        list_layout = QVBoxLayout()
        self.education_list = QListWidget()
        self.education_list.setStyleSheet("QListWidget::item { padding: 3px; }")
        # --- 修改：连接 itemClicked 信号 ---
        self.education_list.itemClicked.connect(self.load_education_for_edit)
        list_layout.addWidget(self.education_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group, stretch=1)

        edu_form = QGroupBox("添加/编辑 教育经历")
        form_layout = QFormLayout()

        self.school_edit = QLineEdit()
        self.major_edit = QLineEdit()
        self.degree_combo = QComboBox()
        self.degree_combo.addItems(["无", "学士", "硕士", "博士"])
        self.start_year_edit = QLineEdit()
        self.start_year_edit.setPlaceholderText("YYYY")
        self.end_year_edit = QLineEdit()
        self.end_year_edit.setPlaceholderText("YYYY 或 至今")
        self.gpa_edit = QLineEdit()
        self.gpa_edit.setPlaceholderText("可选，如 3.8/4.0")
        self.edu_desc_edit = QTextEdit()
        self.edu_desc_edit.setPlaceholderText("可选：相关核心课程、荣誉、奖项、毕业设计...")
        self.edu_desc_edit.setFixedHeight(60)

        form_layout.addRow("学校*:", self.school_edit)
        form_layout.addRow("专业*:", self.major_edit)
        form_layout.addRow("学位:", self.degree_combo)
        form_layout.addRow("开始年份*:", self.start_year_edit)
        form_layout.addRow("结束年份*:", self.end_year_edit)
        form_layout.addRow("GPA:", self.gpa_edit)
        form_layout.addRow("补充描述:", self.edu_desc_edit)

        btn_layout = QHBoxLayout()

        self.add_edu_btn = QPushButton("添加") # 将按钮保存为实例属性，方便修改文本
        self.add_edu_btn.clicked.connect(self.save_education_entry)
        del_edu_btn = QPushButton("删除选中")
        del_edu_btn.clicked.connect(self.delete_education)

        self.cancel_edit_edu_btn = QPushButton("取消编辑")
        self.cancel_edit_edu_btn.clicked.connect(self.clear_education_form) # 清空表单即取消编辑
        self.cancel_edit_edu_btn.setVisible(False) # 初始隐藏

        btn_layout.addWidget(self.add_edu_btn)
        btn_layout.addWidget(del_edu_btn)
        btn_layout.addWidget(self.cancel_edit_edu_btn) # 添加到布局
        btn_layout.addStretch()

        form_layout.addRow(btn_layout)
        edu_form.setLayout(form_layout)
        layout.addWidget(edu_form)

        return tab

    def create_experience_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        list_group = QGroupBox("已添加的工作经历 (单击条目进行编辑)")
        list_layout = QVBoxLayout()
        self.experience_list = QListWidget()
        self.experience_list.setStyleSheet("QListWidget::item { padding: 3px; }")
        self.experience_list.itemClicked.connect(self.load_experience_for_edit) # 连接信号
        list_layout.addWidget(self.experience_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group, stretch=1)

        exp_form = QGroupBox("添加/编辑 工作经历")
        form_layout = QFormLayout()

        self.company_edit = QLineEdit()
        self.position_edit = QLineEdit()
        self.exp_start_edit = QLineEdit()
        self.exp_start_edit.setPlaceholderText("YYYY-MM")
        self.exp_end_edit = QLineEdit()
        self.exp_end_edit.setPlaceholderText("YYYY-MM 或 '至今'")
        self.exp_desc_edit = QTextEdit()
        self.exp_desc_edit.setPlaceholderText("使用 STAR 法则描述关键职责和成就...\n- 负责...\n- 运用...")
        self.exp_desc_edit.setFixedHeight(80)

        form_layout.addRow("公司*:", self.company_edit)
        form_layout.addRow("职位*:", self.position_edit)
        form_layout.addRow("开始时间*:", self.exp_start_edit)
        form_layout.addRow("结束时间*:", self.exp_end_edit)
        form_layout.addRow("工作描述*:", self.exp_desc_edit)

        btn_layout = QHBoxLayout()
        self.add_exp_btn = QPushButton("添加") # 保存为实例属性
        self.add_exp_btn.clicked.connect(self.save_experience_entry) # 连接到保存函数
        del_exp_btn = QPushButton("删除选中")
        del_exp_btn.clicked.connect(self.delete_experience)
        self.cancel_edit_exp_btn = QPushButton("取消编辑")
        self.cancel_edit_exp_btn.clicked.connect(self.clear_experience_form)
        self.cancel_edit_exp_btn.setVisible(False)

        btn_layout.addWidget(self.add_exp_btn)
        btn_layout.addWidget(del_exp_btn)
        btn_layout.addWidget(self.cancel_edit_exp_btn)
        btn_layout.addStretch()

        form_layout.addRow(btn_layout)
        exp_form.setLayout(form_layout)
        layout.addWidget(exp_form)

        return tab

    def create_projects_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        list_group = QGroupBox("已添加的项目 (单击条目进行编辑)")
        list_layout = QVBoxLayout()
        self.projects_list = QListWidget()
        self.projects_list.setStyleSheet("QListWidget::item { padding: 3px; }")
        self.projects_list.itemClicked.connect(self.load_project_for_edit) # 连接信号
        list_layout.addWidget(self.projects_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group, stretch=1)

        project_form = QGroupBox("添加/编辑 项目")
        form_layout = QFormLayout()

        self.project_name_edit = QLineEdit()
        self.project_role_edit = QLineEdit()
        self.project_role_edit.setPlaceholderText("例如：独立开发者, 项目组长...")
        self.project_date_edit = QLineEdit()
        self.project_date_edit.setPlaceholderText("YYYY-MM 或 YYYY")
        self.project_desc_edit = QTextEdit()
        self.project_desc_edit.setPlaceholderText("简述项目目标、个人贡献、技术栈...")
        self.project_desc_edit.setFixedHeight(80)
        self.project_link_edit = QLineEdit()
        self.project_link_edit.setPlaceholderText("可选 - GitHub/演示/博客链接")

        form_layout.addRow("项目名称*:", self.project_name_edit)
        form_layout.addRow("你的角色*:", self.project_role_edit)
        form_layout.addRow("项目日期:", self.project_date_edit)
        form_layout.addRow("项目描述*:", self.project_desc_edit)
        form_layout.addRow("相关链接:", self.project_link_edit)

        btn_layout = QHBoxLayout()
        self.add_project_btn = QPushButton("添加") # 保存为实例属性
        self.add_project_btn.clicked.connect(self.save_project_entry) # 连接到保存函数
        del_project_btn = QPushButton("删除选中")
        del_project_btn.clicked.connect(self.delete_project)
        self.cancel_edit_proj_btn = QPushButton("取消编辑")
        self.cancel_edit_proj_btn.clicked.connect(self.clear_project_form)
        self.cancel_edit_proj_btn.setVisible(False)

        btn_layout.addWidget(self.add_project_btn)
        btn_layout.addWidget(del_project_btn)
        btn_layout.addWidget(self.cancel_edit_proj_btn)
        btn_layout.addStretch()

        form_layout.addRow(btn_layout)
        project_form.setLayout(form_layout)
        layout.addWidget(project_form)

        return tab

    def create_skills_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        list_group = QGroupBox("已添加的技能 (单击条目进行编辑)")
        list_layout = QVBoxLayout()
        self.skills_list = QListWidget()
        self.skills_list.setStyleSheet("QListWidget::item { padding: 3px; }")
        self.skills_list.itemClicked.connect(self.load_skill_for_edit) # 连接信号
        list_layout.addWidget(self.skills_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group, stretch=1)

        skill_form = QGroupBox("添加/编辑 技能")
        form_layout = QFormLayout()

        self.skill_type_combo = QComboBox()
        self.skill_type_combo.addItems([
            "", "编程语言", "Web前端", "Web后端", "数据库", "移动开发",
            "数据科学/AI", "云计算/DevOps", "测试", "设计工具", "项目管理", "操作系统", "其他"
        ])
        self.skill_name_edit = QLineEdit()
        self.skill_name_edit.setPlaceholderText("例如：Python, JavaScript, React...")
        self.skill_level_combo = QComboBox()
        self.skill_level_combo.addItems(["", "了解", "熟悉", "熟练掌握", "精通"])

        form_layout.addRow("技能类别:", self.skill_type_combo)
        form_layout.addRow("技能名称*:", self.skill_name_edit)
        form_layout.addRow("熟练程度:", self.skill_level_combo)

        btn_layout = QHBoxLayout()
        self.add_skill_btn = QPushButton("添加") # 保存为实例属性
        self.add_skill_btn.clicked.connect(self.save_skill_entry) # 连接到保存函数
        del_skill_btn = QPushButton("删除选中")
        del_skill_btn.clicked.connect(self.delete_skill)
        self.cancel_edit_skill_btn = QPushButton("取消编辑")
        self.cancel_edit_skill_btn.clicked.connect(self.clear_skill_form)
        self.cancel_edit_skill_btn.setVisible(False)

        btn_layout.addWidget(self.add_skill_btn)
        btn_layout.addWidget(del_skill_btn)
        btn_layout.addWidget(self.cancel_edit_skill_btn)
        btn_layout.addStretch()

        form_layout.addRow(btn_layout)
        skill_form.setLayout(form_layout)
        layout.addWidget(skill_form)

        return tab

    def create_languages_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        list_group = QGroupBox("已添加的语言能力 (单击条目进行编辑)")
        list_layout = QVBoxLayout()
        self.languages_list = QListWidget()
        self.languages_list.setStyleSheet("QListWidget::item { padding: 3px; }")
        self.languages_list.itemClicked.connect(self.load_language_for_edit) # 连接信号
        list_layout.addWidget(self.languages_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group, stretch=1)

        language_form = QGroupBox("添加/编辑 语言")
        form_layout = QFormLayout()

        self.language_name_edit = QLineEdit()
        self.language_name_edit.setPlaceholderText("例如：英语, 日语, 普通话")
        self.language_level_combo = QComboBox()
        self.language_level_combo.addItems([
            "", "基本沟通", "日常会话", "CET-4", "CET-6",
            "TEM-4", "TEM-8", "接近母语", "母语"
        ])

        form_layout.addRow("语言*:", self.language_name_edit)
        form_layout.addRow("水平/证书:", self.language_level_combo)

        btn_layout = QHBoxLayout()
        self.add_language_btn = QPushButton("添加") # 保存为实例属性
        self.add_language_btn.clicked.connect(self.save_language_entry) # 连接到保存函数
        del_language_btn = QPushButton("删除选中")
        del_language_btn.clicked.connect(self.delete_language)
        self.cancel_edit_lang_btn = QPushButton("取消编辑")
        self.cancel_edit_lang_btn.clicked.connect(self.clear_language_form)
        self.cancel_edit_lang_btn.setVisible(False)

        btn_layout.addWidget(self.add_language_btn)
        btn_layout.addWidget(del_language_btn)
        btn_layout.addWidget(self.cancel_edit_lang_btn)
        btn_layout.addStretch()

        form_layout.addRow(btn_layout)
        language_form.setLayout(form_layout)
        layout.addWidget(language_form)

        return tab

    def update_resume_data(self):
        # ... (不变) ...
        self.resume_data["personal_info"] = {
            "name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "linkedin": self.linkedin_edit.text().strip(),
            "github": self.github_edit.text().strip(),
            "summary": self.summary_edit.toPlainText().strip()
        }

    def validate_personal_info(self):
        # ... (不变) ...
        info = self.resume_data["personal_info"]
        if not info["name"] or not info["email"] or not info["phone"]:
            QMessageBox.warning(self, "信息不完整", "请确保“个人信息”标签页中的姓名、邮箱和电话已填写！")
            self.tabs.setCurrentIndex(0) # 切换到个人信息标签页
            return False
        return True

    # --- 新增：加载条目到表单的函数 ---
    def load_education_for_edit(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.resume_data["education"]):
            data = self.resume_data["education"][index]
            self.school_edit.setText(data.get("school", ""))
            self.major_edit.setText(data.get("major", ""))
            self.degree_combo.setCurrentText(data.get("degree", ""))
            self.start_year_edit.setText(data.get("start_year", ""))
            self.end_year_edit.setText(data.get("end_year", ""))
            self.gpa_edit.setText(data.get("gpa", ""))
            self.edu_desc_edit.setPlainText(data.get("description", ""))

            self.editing_index["education"] = index
            self.add_edu_btn.setText("更新") # 更改按钮文本
            self.cancel_edit_edu_btn.setVisible(True) # 显示取消按钮
            self.status_label.setText(f"正在编辑教育经历: {data.get('school','')}")
        else:
            print(f"Error loading education: Invalid index {index}")
            self.clear_education_form() # 如果索引无效，清空表单

    def load_experience_for_edit(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.resume_data["experience"]):
            data = self.resume_data["experience"][index]
            self.company_edit.setText(data.get("company", ""))
            self.position_edit.setText(data.get("position", ""))
            self.exp_start_edit.setText(data.get("start_date", ""))
            self.exp_end_edit.setText(data.get("end_date", ""))
            self.exp_desc_edit.setPlainText(data.get("description", ""))

            self.editing_index["experience"] = index
            self.add_exp_btn.setText("更新")
            self.cancel_edit_exp_btn.setVisible(True)
            self.status_label.setText(f"正在编辑工作经历: {data.get('company','')}")
        else:
            print(f"Error loading experience: Invalid index {index}")
            self.clear_experience_form()

    def load_project_for_edit(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.resume_data["projects"]):
            data = self.resume_data["projects"][index]
            self.project_name_edit.setText(data.get("name", ""))
            self.project_role_edit.setText(data.get("role", ""))
            self.project_date_edit.setText(data.get("date", ""))
            self.project_desc_edit.setPlainText(data.get("description", ""))
            self.project_link_edit.setText(data.get("link", ""))

            self.editing_index["projects"] = index
            self.add_project_btn.setText("更新")
            self.cancel_edit_proj_btn.setVisible(True)
            self.status_label.setText(f"正在编辑项目: {data.get('name','')}")
        else:
            print(f"Error loading project: Invalid index {index}")
            self.clear_project_form()

    def load_skill_for_edit(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.resume_data["skills"]):
            data = self.resume_data["skills"][index]
            self.skill_name_edit.setText(data.get("name", ""))

            type_index = self.skill_type_combo.findText(data.get("type", ""), Qt.MatchFlag.MatchFixedString)
            if type_index >= 0: self.skill_type_combo.setCurrentIndex(type_index)
            else: self.skill_type_combo.setCurrentIndex(0)

            level_index = self.skill_level_combo.findText(data.get("level", ""), Qt.MatchFlag.MatchFixedString)
            if level_index >= 0: self.skill_level_combo.setCurrentIndex(level_index)
            else: self.skill_level_combo.setCurrentIndex(0)

            self.editing_index["skills"] = index
            self.add_skill_btn.setText("更新")
            self.cancel_edit_skill_btn.setVisible(True)
            self.status_label.setText(f"正在编辑技能: {data.get('name','')}")
        else:
            print(f"Error loading skill: Invalid index {index}")
            self.clear_skill_form()

    def load_language_for_edit(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.resume_data["languages"]):
            data = self.resume_data["languages"][index]
            self.language_name_edit.setText(data.get("name", ""))

            level_index = self.language_level_combo.findText(data.get("level", ""), Qt.MatchFlag.MatchFixedString)
            if level_index >= 0: self.language_level_combo.setCurrentIndex(level_index)
            else: self.language_level_combo.setCurrentIndex(0)

            self.editing_index["languages"] = index
            self.add_language_btn.setText("更新")
            self.cancel_edit_lang_btn.setVisible(True)
            self.status_label.setText(f"正在编辑语言: {data.get('name','')}")
        else:
            print(f"Error loading language: Invalid index {index}")
            self.clear_language_form()

    # --- 修改：保存函数处理添加和更新 ---
    def save_education_entry(self):
        school = self.school_edit.text().strip()
        major = self.major_edit.text().strip()
        degree = self.degree_combo.currentText()
        start_year = self.start_year_edit.text().strip()
        end_year = self.end_year_edit.text().strip()
        gpa = self.gpa_edit.text().strip()
        description = self.edu_desc_edit.toPlainText().strip()

        if not all([school, major, start_year, end_year]):
            QMessageBox.warning(self, "警告", "请填写教育经历中带*号的必填字段！")
            return
        if not (start_year.isdigit() and len(start_year) == 4) or \
           not ((end_year.isdigit() and len(end_year) == 4) or end_year.lower() == '至今'):
             QMessageBox.warning(self, "格式错误", "年份请输入4位数字 (例如 2020) 或 '至今'")
             return

        edu_item = {
            "school": school, "major": major, "degree": degree,
            "start_year": start_year, "end_year": end_year,
            "gpa": gpa, "description": description
        }

        edit_index = self.editing_index["education"]
        if edit_index is not None: # 更新模式
            if 0 <= edit_index < len(self.resume_data["education"]):
                self.resume_data["education"][edit_index] = edu_item
                self.update_education_list()
                self.clear_education_form() # 清空表单并重置编辑状态
                self.status_label.setText(f"已更新教育经历: {school}")
            else:
                QMessageBox.warning(self, "错误", f"更新教育经历时出错：无效的索引 {edit_index}")
                self.clear_education_form() # 重置状态
        else: # 添加模式
            self.resume_data["education"].append(edu_item)
            self.update_education_list()
            self.clear_education_form()
            self.status_label.setText(f"已添加教育经历: {school}")

    def save_experience_entry(self):
        company = self.company_edit.text().strip()
        position = self.position_edit.text().strip()
        start_date = self.exp_start_edit.text().strip()
        end_date = self.exp_end_edit.text().strip()
        description = self.exp_desc_edit.toPlainText().strip()

        if not all([company, position, start_date, end_date, description]):
            QMessageBox.warning(self, "警告", "请填写工作经历中带*号的必填字段！")
            return
        date_pattern_ok = lambda d: len(d) == 7 and d[4] == '-' and d[:4].isdigit() and d[5:].isdigit()
        if not date_pattern_ok(start_date) or not (date_pattern_ok(end_date) or end_date.lower() == '至今'):
             QMessageBox.warning(self, "格式错误", "时间请输入 YYYY-MM 格式 (例如 2022-08) 或 '至今'")
             return

        exp_item = {
            "company": company, "position": position, "start_date": start_date,
            "end_date": end_date, "description": description
        }

        edit_index = self.editing_index["experience"]
        if edit_index is not None: # 更新模式
             if 0 <= edit_index < len(self.resume_data["experience"]):
                self.resume_data["experience"][edit_index] = exp_item
                self.update_experience_list()
                self.clear_experience_form()
                self.status_label.setText(f"已更新工作经历: {company}")
             else:
                QMessageBox.warning(self, "错误", f"更新工作经历时出错：无效的索引 {edit_index}")
                self.clear_experience_form()
        else: # 添加模式
            self.resume_data["experience"].append(exp_item)
            self.update_experience_list()
            self.clear_experience_form()
            self.status_label.setText(f"已添加工作经历: {company}")

    def save_project_entry(self):
        name = self.project_name_edit.text().strip()
        role = self.project_role_edit.text().strip()
        date = self.project_date_edit.text().strip()
        description = self.project_desc_edit.toPlainText().strip()
        link = self.project_link_edit.text().strip()

        if not all([name, role, description]):
            QMessageBox.warning(self, "警告", "请填写项目中带*号的必填字段！")
            return

        project_item = {
            "name": name, "role": role, "date": date,
            "description": description, "link": link
        }

        edit_index = self.editing_index["projects"]
        if edit_index is not None: # 更新模式
             if 0 <= edit_index < len(self.resume_data["projects"]):
                self.resume_data["projects"][edit_index] = project_item
                self.update_projects_list()
                self.clear_project_form()
                self.status_label.setText(f"已更新项目: {name}")
             else:
                QMessageBox.warning(self, "错误", f"更新项目时出错：无效的索引 {edit_index}")
                self.clear_project_form()
        else: # 添加模式
            self.resume_data["projects"].append(project_item)
            self.update_projects_list()
            self.clear_project_form()
            self.status_label.setText(f"已添加项目: {name}")

    def save_skill_entry(self):
        name = self.skill_name_edit.text().strip()
        skill_type = self.skill_type_combo.currentText()
        level = self.skill_level_combo.currentText()

        if not name:
            QMessageBox.warning(self, "警告", "请输入技能名称！")
            return

        skill_item = {
            "name": name,
            "type": skill_type if skill_type else "未分类",
            "level": level if level else "未指定"
        }

        edit_index = self.editing_index["skills"]
        if edit_index is not None: # 更新模式
            if 0 <= edit_index < len(self.resume_data["skills"]):
                self.resume_data["skills"][edit_index] = skill_item
                self.update_skills_list()
                self.clear_skill_form()
                self.status_label.setText(f"已更新技能: {name}")
            else:
                QMessageBox.warning(self, "错误", f"更新技能时出错：无效的索引 {edit_index}")
                self.clear_skill_form()
        else: # 添加模式
            self.resume_data["skills"].append(skill_item)
            self.update_skills_list()
            self.clear_skill_form()
            self.status_label.setText(f"已添加技能: {name}")

    def save_language_entry(self):
        name = self.language_name_edit.text().strip()
        level = self.language_level_combo.currentText()

        if not name:
            QMessageBox.warning(self, "警告", "请输入语言名称！")
            return

        language_item = { "name": name, "level": level if level else "未指定" }

        edit_index = self.editing_index["languages"]
        if edit_index is not None: # 更新模式
            if 0 <= edit_index < len(self.resume_data["languages"]):
                self.resume_data["languages"][edit_index] = language_item
                self.update_languages_list()
                self.clear_language_form()
                self.status_label.setText(f"已更新语言: {name}")
            else:
                QMessageBox.warning(self, "错误", f"更新语言时出错：无效的索引 {edit_index}")
                self.clear_language_form()
        else: # 添加模式
            self.resume_data["languages"].append(language_item)
            self.update_languages_list()
            self.clear_language_form()
            self.status_label.setText(f"已添加语言: {name}")

    # --- 修改：清空表单函数重置编辑状态 ---
    def clear_education_form(self):
        self.school_edit.clear()
        self.major_edit.clear()
        self.degree_combo.setCurrentIndex(0)
        self.start_year_edit.clear()
        self.end_year_edit.clear()
        self.gpa_edit.clear()
        self.edu_desc_edit.clear()
        # 重置编辑状态
        self.editing_index["education"] = None
        self.add_edu_btn.setText("添加")
        self.cancel_edit_edu_btn.setVisible(False)

    def clear_experience_form(self):
        self.company_edit.clear()
        self.position_edit.clear()
        self.exp_start_edit.clear()
        self.exp_end_edit.clear()
        self.exp_desc_edit.clear()
        # 重置编辑状态
        self.editing_index["experience"] = None
        self.add_exp_btn.setText("添加")
        self.cancel_edit_exp_btn.setVisible(False)

    def clear_project_form(self):
        self.project_name_edit.clear()
        self.project_role_edit.clear()
        self.project_date_edit.clear()
        self.project_desc_edit.clear()
        self.project_link_edit.clear()
        # 重置编辑状态
        self.editing_index["projects"] = None
        self.add_project_btn.setText("添加")
        self.cancel_edit_proj_btn.setVisible(False)

    def clear_skill_form(self):
        self.skill_name_edit.clear()
        self.skill_type_combo.setCurrentIndex(0)
        self.skill_level_combo.setCurrentIndex(0)
        # 重置编辑状态
        self.editing_index["skills"] = None
        self.add_skill_btn.setText("添加")
        self.cancel_edit_skill_btn.setVisible(False)

    def clear_language_form(self):
        self.language_name_edit.clear()
        self.language_level_combo.setCurrentIndex(0)
        # 重置编辑状态
        self.editing_index["languages"] = None
        self.add_language_btn.setText("添加")
        self.cancel_edit_lang_btn.setVisible(False)


    def delete_education(self):
        selected_item = self.education_list.currentItem()
        if selected_item:
            index_to_remove = selected_item.data(Qt.ItemDataRole.UserRole)
            if 0 <= index_to_remove < len(self.resume_data["education"]):
                # 如果删除的是正在编辑的条目，先清空表单
                if self.editing_index["education"] == index_to_remove:
                    self.clear_education_form()

                removed = self.resume_data["education"].pop(index_to_remove)
                # 删除后需要更新所有后续条目的索引
                self.update_education_list()
                # 如果删除了正在编辑的项之前的项，需要调整编辑索引
                if self.editing_index["education"] is not None and index_to_remove < self.editing_index["education"]:
                    self.editing_index["education"] -= 1
                self.status_label.setText(f"已删除教育经历: {removed['school']}")
        else:
            QMessageBox.information(self, "提示", "请先在列表中选择要删除的教育经历。")

    def delete_experience(self):
        selected_item = self.experience_list.currentItem()
        if selected_item:
            index_to_remove = selected_item.data(Qt.ItemDataRole.UserRole)
            if 0 <= index_to_remove < len(self.resume_data["experience"]):
                if self.editing_index["experience"] == index_to_remove:
                    self.clear_experience_form()
                removed = self.resume_data["experience"].pop(index_to_remove)
                self.update_experience_list()
                if self.editing_index["experience"] is not None and index_to_remove < self.editing_index["experience"]:
                    self.editing_index["experience"] -= 1
                self.status_label.setText(f"已删除工作经历: {removed['company']}")
        else:
            QMessageBox.information(self, "提示", "请先在列表中选择要删除的工作经历。")

    def delete_project(self):
        selected_item = self.projects_list.currentItem()
        if selected_item:
            index_to_remove = selected_item.data(Qt.ItemDataRole.UserRole)
            if 0 <= index_to_remove < len(self.resume_data["projects"]):
                if self.editing_index["projects"] == index_to_remove:
                    self.clear_project_form()
                removed = self.resume_data["projects"].pop(index_to_remove)
                self.update_projects_list()
                if self.editing_index["projects"] is not None and index_to_remove < self.editing_index["projects"]:
                    self.editing_index["projects"] -= 1
                self.status_label.setText(f"已删除项目: {removed['name']}")
        else:
            QMessageBox.information(self, "提示", "请先在列表中选择要删除的项目。")

    def delete_skill(self):
        selected_item = self.skills_list.currentItem()
        if selected_item:
            index_to_remove = selected_item.data(Qt.ItemDataRole.UserRole)
            if index_to_remove is not None:
                if 0 <= index_to_remove < len(self.resume_data["skills"]):
                    if self.editing_index["skills"] == index_to_remove:
                        self.clear_skill_form()
                    removed = self.resume_data["skills"].pop(index_to_remove)
                    # 因为技能列表更新会重新生成所有项，所以索引会自动正确
                    self.update_skills_list()
                     # 如果删除了正在编辑的项之前的项，需要调整编辑索引
                    if self.editing_index["skills"] is not None and index_to_remove < self.editing_index["skills"]:
                         self.editing_index["skills"] -= 1 # 虽然列表重建了，但如果还想继续编辑之前的下一项，索引需要调整

                         self.clear_skill_form() # 删除后最好取消编辑状态

                    self.status_label.setText(f"已删除技能: {removed['name']}")
                else:
                     print(f"Error: Invalid index {index_to_remove} for skill deletion.")
            else:
                 print(f"Error: Could not retrieve index from selected skill item.")
        else:
            QMessageBox.information(self, "提示", "请先在列表中选择要删除的技能。")


    def delete_language(self):
        selected_item = self.languages_list.currentItem()
        if selected_item:
            index_to_remove = selected_item.data(Qt.ItemDataRole.UserRole)
            if 0 <= index_to_remove < len(self.resume_data["languages"]):
                if self.editing_index["languages"] == index_to_remove:
                    self.clear_language_form()
                removed = self.resume_data["languages"].pop(index_to_remove)
                self.update_languages_list()
                if self.editing_index["languages"] is not None and index_to_remove < self.editing_index["languages"]:
                    self.editing_index["languages"] -= 1
                self.status_label.setText(f"已删除语言: {removed['name']}")
        else:
            QMessageBox.information(self, "提示", "请先在列表中选择要删除的语言能力。")



    def preview_resume(self):
        """在消息框中预览简历文本"""
        self.update_resume_data() # 更新个人信息等
        if not self.validate_personal_info():
             return

        preview_text = "=========== 简历预览 ===========\n\n"
        personal = self.resume_data["personal_info"]
        preview_text += f"姓名: {personal['name']}\n"
        contact = [f"电话: {personal['phone']}", f"邮箱: {personal['email']}"]
        if personal['address']: contact.append(f"地址: {personal['address']}")
        preview_text += " | ".join(contact) + "\n"
        links = []
        if personal["linkedin"]: links.append(f"LinkedIn: {personal['linkedin']}")
        if personal["github"]: links.append(f"GitHub: {personal['github']}")
        if links: preview_text += " | ".join(links) + "\n"

        if personal["summary"]:
            preview_text += f"\n--- 个人简介 ---\n{personal['summary']}\n"

        if self.resume_data["education"]:
            preview_text += "\n--- 教育经历 ---\n"
            for edu in self.resume_data["education"]:
                degree = f", {edu['degree']}" if edu['degree'] else ""
                gpa = f", GPA: {edu['gpa']}" if edu['gpa'] else ""
                preview_text += f"- {edu['school']}, {edu['major']}{degree} ({edu['start_year']} - {edu['end_year']}){gpa}\n"
                if edu["description"]:
                    lines = edu['description'].split('\n')
                    for i, line in enumerate(lines):
                        line = line.strip()  # 去除行首尾空格
                        if line:  # 只处理非空行
                            preview_text += f"  • {line}\n"  # 每行都加项目符号和缩进
        else: preview_text += "\n--- 教育经历 ---\n (未添加)\n"

        if self.resume_data["experience"]:
            preview_text += "\n--- 工作经历 ---\n"
            for exp in self.resume_data["experience"]:
                preview_text += f"- {exp['company']} | {exp['position']} ({exp['start_date']} 至 {exp['end_date']})\n"
                for line in exp['description'].split('\n'):
                    if line.strip(): preview_text += f"  • {line.strip()}\n"
        else: preview_text += "\n--- 工作经历 ---\n (未添加)\n"

        if self.resume_data["projects"]:
            preview_text += "\n--- 项目经历 ---\n"
            for proj in self.resume_data["projects"]:
                date = f" ({proj['date']})" if proj['date'] else ""
                preview_text += f"- {proj['name']}{date} | 角色: {proj['role']}\n"
                if proj["description"]:
                    lines = proj['description'].split('\n')
                    for line in lines:
                        if line.strip():
                            preview_text += f"  {line}\n"
                if proj["link"]: preview_text += f"  链接: {proj['link']}\n"
        else: preview_text += "\n--- 项目经历 ---\n (未添加)\n"

        if self.resume_data["skills"]:
            preview_text += "\n--- 技能 ---\n"
            skills_by_type = {}
            for skill in self.resume_data["skills"]:
                stype = skill.get("type", "未分类")
                level = f" ({skill['level']})" if skill['level'] != '未指定' else ""
                if stype not in skills_by_type: skills_by_type[stype] = []
                skills_by_type[stype].append(f"{skill['name']}{level}")
            for stype in sorted(skills_by_type.keys()):
                preview_text += f"- {stype}: {', '.join(skills_by_type[stype])}\n"
        else: preview_text += "\n--- 技能 ---\n (未添加)\n"

        if self.resume_data["languages"]:
            preview_text += "\n--- 语言能力 ---\n"
            langs = [f"{lang['name']} ({lang['level']})" if lang['level'] != '未指定' else lang['name']
                     for lang in self.resume_data["languages"]]
            preview_text += "- " + " | ".join(langs) + "\n"
        else: preview_text += "\n--- 语言能力 ---\n (未添加)\n"

        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("简历预览")
        msgBox.setTextFormat(Qt.TextFormat.PlainText)
        msgBox.setText(preview_text)
        msgBox.setStyleSheet("QTextEdit{ min-width: 600px; min-height: 500px; font-size: 13px; }")
        msgBox.exec()
        self.status_label.setText("简历预览已生成")

    def add_section_title(self, pdf, title, line_height):
        """辅助函数：添加带样式的章节标题"""
        COLOR_PRIMARY = (41, 128, 185) # 主题蓝
        COLOR_LINE = (200, 200, 200)  # 浅灰线条

        pdf.ln(6)
        pdf.set_chinese_font('B', 14)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell_chinese(0, line_height + 2, title.upper(), 0, 1, 'L')
        pdf.set_draw_color(*COLOR_PRIMARY)
        pdf.set_line_width(0.5)
        pdf.cell(w=0, h=0.1, border='T', ln=1)
        pdf.set_line_width(0.2)
        pdf.set_text_color(51, 51, 51)
        pdf.ln(4)
        pdf.set_chinese_font(size=10.5)

    def export_to_pdf(self):
        """导出简历为PDF文件"""
        self.update_resume_data()
        if not self.validate_personal_info():
            return

        COLOR_PRIMARY = (41, 128, 185);
        COLOR_TEXT = (51, 51, 51)
        COLOR_LIGHT_TEXT = (100, 100, 100);
        COLOR_LINK = (41, 128, 185)
        COLOR_LINE = (220, 220, 220)

        pdf = PDF()
        if not pdf.font_added:
            QMessageBox.critical(self, "错误", f"无法加载中文字体 '{CHINESE_FONT_PATH}'. PDF导出失败。")
            return
        pdf.add_page();
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(15, 15, 15);
        pdf.set_text_color(*COLOR_TEXT)
        line_height = 5.5

        available_width = pdf.w - pdf.l_margin - pdf.r_margin

        # --- 个人信息 (页眉区域) ---

        personal = self.resume_data["personal_info"]
        pdf.set_chinese_font('B', 22);
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell_chinese(0, line_height + 8, personal["name"], 0, 1, 'C')
        pdf.set_text_color(*COLOR_TEXT);
        pdf.ln(1)
        pdf.set_chinese_font(size=9.5)
        contact_items = [f"电话: {p}" for p in [personal.get("phone")] if p] + \
                        [f"邮箱: {e}" for e in [personal.get("email")] if e] + \
                        [f"地址: {a}" for a in [personal.get("address")] if a]
        pdf.cell_chinese(0, line_height - 1, "  |  ".join(contact_items), 0, 1, 'C')
        link_items = [f"LinkedIn: {l}" for l in [personal.get("linkedin")] if l] + \
                     [f"GitHub: {g}" for g in [personal.get("github")] if g]
        if link_items:
            pdf.set_text_color(*COLOR_LINK)
            pdf.cell_chinese(0, line_height - 1, "  |  ".join(link_items), 0, 1, 'C', link=' '.join(link_items))
            pdf.set_text_color(*COLOR_TEXT)
        pdf.ln(4);
        pdf.set_draw_color(*COLOR_LINE);
        pdf.set_line_width(0.3)
        pdf.cell(w=0, h=0.1, border='T', ln=1);
        pdf.ln(5)

        # --- 个人简介 ---
        if personal["summary"]:
            self.add_section_title(pdf, "个人简介", line_height)

            pdf.multi_cell_chinese(available_width, line_height, personal["summary"])

        # --- 教育经历 ---
        if self.resume_data["education"]:
            self.add_section_title(pdf, "教育经历", line_height)
            for edu in self.resume_data["education"]:
                pdf.set_chinese_font('B', 11)
                date_info = f"{edu['start_year']} - {edu['end_year']}"
                date_width = pdf.get_string_width(date_info) + 2
                pdf.cell_chinese(0, line_height, f"* {edu['school']}", 0, 0)
                pdf.set_text_color(*COLOR_LIGHT_TEXT);
                pdf.set_chinese_font(size=9.5)
                pdf.cell(0, line_height, date_info, 0, 1, 'R')
                pdf.set_text_color(*COLOR_TEXT);
                pdf.set_chinese_font(size=10.5)
                degree_info = f"{edu['major']}" + (f" - {edu['degree']}" if edu['degree'] else "") + \
                              (f" (GPA: {edu['gpa']})" if edu['gpa'] else "")
                pdf.cell_chinese(0, line_height, f"  {degree_info}", 0, 1)
                if edu["description"]:
                    pdf.set_text_color(*COLOR_LIGHT_TEXT)
                    for line in edu['description'].split('\n'):
                        line = line.strip()
                        if line:

                            pdf.multi_cell_chinese(available_width, line_height - 1, f"- {line}")
                    pdf.set_text_color(*COLOR_TEXT)
                pdf.ln(3)

        # --- 工作经历 ---
        if self.resume_data["experience"]:
            self.add_section_title(pdf, "工作经历", line_height)
            for exp in self.resume_data["experience"]:
                pdf.set_chinese_font('B', 11)
                date_info = f"{exp['start_date']} - {exp['end_date']}"
                date_width = pdf.get_string_width(date_info) + 2
                pdf.cell_chinese(0, line_height, f"* {exp['company']}", 0, 0)
                pdf.set_text_color(*COLOR_LIGHT_TEXT);
                pdf.set_chinese_font(size=9.5)
                pdf.cell(0, line_height, date_info, 0, 1, 'R')
                pdf.set_text_color(*COLOR_TEXT);
                pdf.set_chinese_font(size=10.5)
                pdf.set_chinese_font('I');
                pdf.cell_chinese(0, line_height, f"> {exp['position']}", 0, 1);
                pdf.set_chinese_font()
                for line in exp['description'].split('\n'):
                    line = line.strip()
                    if line:

                        pdf.multi_cell_chinese(available_width, line_height - 0.5, f"- {line}")
                pdf.ln(3)

        # --- 项目经历 ---
        if self.resume_data["projects"]:
            self.add_section_title(pdf, "项目经历", line_height)
            for proj in self.resume_data["projects"]:
                pdf.set_chinese_font('B', 11)
                date_info = f"({proj['date']})" if proj['date'] else ""
                date_width = pdf.get_string_width(date_info) + 2
                pdf.cell_chinese(0, line_height, f"* {proj['name']}", 0, 0)
                pdf.set_text_color(*COLOR_LIGHT_TEXT);
                pdf.set_chinese_font(size=9.5)
                pdf.cell(0, line_height, date_info, 0, 1, 'R')
                pdf.set_text_color(*COLOR_TEXT);
                pdf.set_chinese_font(size=10.5)
                pdf.cell_chinese(0, line_height, f"角色: {proj['role']}", 0, 1)
                if proj["description"]:
                    for line in proj['description'].split('\n'):
                        line = line.strip()
                        if line:

                            pdf.multi_cell_chinese(available_width, line_height - 0.5, f"{line}")
                if proj["link"]:
                    pdf.ln(1);
                    pdf.set_text_color(*COLOR_LINK)
                    pdf.cell_chinese(0, line_height - 1, f"> 链接: {proj['link']}", 0, 1, link=proj['link'])
                    pdf.set_text_color(*COLOR_TEXT)
                pdf.ln(3)

        # --- 技能 ---

        if self.resume_data["skills"]:
            self.add_section_title(pdf, "技能", line_height)

            skills_by_type = {}
            for skill in self.resume_data["skills"]:
                skill_type = skill.get("type", "未分类")
                if skill_type not in skills_by_type: skills_by_type[skill_type] = []
                level = f" ({skill['level']})" if skill.get('level') and skill['level'] != '未指定' else ""
                skills_by_type[skill_type].append(f"{skill['name']}{level}")

            x_pos_label = pdf.l_margin;
            x_pos_skills = pdf.l_margin + 35
            for skill_type in sorted(skills_by_type.keys()):
                pdf.set_x(x_pos_label);
                pdf.set_chinese_font('B')
                pdf.cell_chinese(x_pos_skills - x_pos_label - 2, line_height, f"{skill_type}:", 0, 0, 'R')
                pdf.set_chinese_font();
                pdf.set_x(x_pos_skills)
                # multi_cell 这里已经有显式宽度，不需要改
                pdf.multi_cell_chinese(pdf.w - pdf.r_margin - x_pos_skills, line_height,
                                       ", ".join(skills_by_type[skill_type]), border=0, align='L')
                pdf.ln(1)

        # --- 检查页面空间 ---

        estimated_section_height = (line_height + 2) + line_height + (6 / pdf.k) + (4 / pdf.k)
        remaining_page_space = pdf.h - pdf.b_margin - pdf.get_y()
        if self.resume_data["languages"] and remaining_page_space < estimated_section_height * 1.2:
            print("DEBUG: Adding page break before Languages section")
            pdf.add_page()

        # --- 语言能力 ---
        if self.resume_data["languages"]:
            self.add_section_title(pdf, "语言能力", line_height)
            lang_list = [
                f"{lang['name']}" + (f" ({lang['level']})" if lang.get('level') and lang['level'] != '未指定' else "")
                for lang in self.resume_data["languages"]]

            pdf.multi_cell_chinese(available_width, line_height, " | ".join(lang_list))

        # --- 保存PDF ---

        try:
            safe_name = "".join(c for c in personal['name'] if c.isalnum() or c in (' ', '_')).rstrip() or "未命名"
            default_filename = f"{safe_name}_简历.pdf"  # 文件名加后缀
            filepath, _ = QFileDialog.getSaveFileName(self, "导出PDF简历", default_filename, "PDF 文件 (*.pdf)")
            if filepath:
                pdf.output(filepath)
                QMessageBox.information(self, "导出成功", f"简历已成功导出为:\n{filepath}")
                self.status_label.setText(f"简历已导出")
            else:
                self.status_label.setText("导出已取消")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出PDF时发生错误: {str(e)}\n请检查文件权限或路径。")
            self.status_label.setText("导出PDF时出错")

    def save_resume(self):
        """保存简历数据到JSON文件"""
        self.update_resume_data()
        if not self.validate_personal_info():
             return
        personal_name = self.resume_data['personal_info']['name']
        safe_name = "".join(c for c in personal_name if c.isalnum() or c in (' ', '_')).rstrip() or "未命名"
        default_filename = f"{safe_name}_简历.json"
        filepath, _ = QFileDialog.getSaveFileName(self, "保存简历数据", default_filename, "JSON 文件 (*.json)")
        if not filepath:
            self.status_label.setText("保存已取消"); return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.resume_data, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "保存成功", f"简历数据已保存到:\n{filepath}")
            self.status_label.setText(f"简历已保存")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存简历时出错: {str(e)}")
            self.status_label.setText("保存简历时出错")

    def load_resume(self):
        """从JSON文件加载简历数据"""
        filepath, _ = QFileDialog.getOpenFileName(self, "加载简历数据", "", "JSON 文件 (*.json)")
        if not filepath:
            self.status_label.setText("加载已取消"); return
        try:
            reply = QMessageBox.question(self, '确认加载', '加载新简历将覆盖当前内容，确定要加载吗？',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                self.status_label.setText("加载已取消"); return
            with open(filepath, 'r', encoding='utf-8') as f: loaded_data = json.load(f)
            if isinstance(loaded_data, dict) and "personal_info" in loaded_data:
                 self.resume_data = loaded_data; self.ensure_data_structure()
            else: raise ValueError("无效的简历文件格式")
            self.update_ui_from_data(); self.clear_all_edit_states() # 加载后清除所有编辑状态
            QMessageBox.information(self, "加载成功", f"简历数据已从:\n{filepath} 加载")
            self.status_label.setText(f"已加载简历"); self.tabs.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"加载简历时出错: {str(e)}")
            self.status_label.setText("加载简历时出错")

    def ensure_data_structure(self):
        """确保 self.resume_data 包含所有预期的键和列表"""
        defaults = {
            "personal_info": {"name": "", "email": "", "phone": "", "address": "", "linkedin": "", "github": "", "summary": ""},
            "education": [], "experience": [], "projects": [], "skills": [], "languages": []
        }
        for key, default_value in defaults.items():
            if key not in self.resume_data: self.resume_data[key] = default_value
            elif isinstance(default_value, dict):
                if not isinstance(self.resume_data.get(key), dict): self.resume_data[key] = default_value.copy()
                else:
                    for sub_key, sub_default in default_value.items():
                        if sub_key not in self.resume_data[key]: self.resume_data[key][sub_key] = sub_default
            elif isinstance(default_value, list) and not isinstance(self.resume_data.get(key), list):
                 self.resume_data[key] = []

    def update_ui_from_data(self):
        """根据 self.resume_data 中的数据更新整个UI界面"""
        personal = self.resume_data.get("personal_info", {})
        self.name_edit.setText(personal.get("name", ""))
        self.email_edit.setText(personal.get("email", ""))
        self.phone_edit.setText(personal.get("phone", ""))
        self.address_edit.setText(personal.get("address", ""))
        self.linkedin_edit.setText(personal.get("linkedin", ""))
        self.github_edit.setText(personal.get("github", ""))
        self.summary_edit.setPlainText(personal.get("summary", ""))
        self.update_education_list(); self.update_experience_list()
        self.update_projects_list(); self.update_skills_list()
        self.update_languages_list()
        print("UI 已根据加载的数据更新。")

    def clear_all_edit_states(self):
        """清除所有标签页的编辑状态和表单"""
        self.clear_education_form()
        self.clear_experience_form()
        self.clear_project_form()
        self.clear_skill_form()
        self.clear_language_form()

    def clear_all(self):
        """清空所有输入和列表"""
        reply = QMessageBox.question(self, '确认清空', '确定要清空所有已输入的内容吗？此操作不可撤销。',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.reset_resume_data()
            self.update_ui_from_data() # 更新列表（现在是空的）
            self.clear_all_edit_states() # 清空所有表单和编辑状态
            self.status_label.setText("所有内容已清空")
            self.tabs.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not os.path.exists(CHINESE_FONT_PATH):
         msg = QMessageBox()
         msg.setIcon(QMessageBox.Icon.Warning); msg.setWindowTitle("字体文件缺失")
         msg.setText(f"警告：未找到中文字体文件:\n'{CHINESE_FONT_PATH}'。\n\n请配置正确路径。")
         msg.setStandardButtons(QMessageBox.StandardButton.Ok); msg.exec()
    window = ResumeApp()
    window.show()
    sys.exit(app.exec())