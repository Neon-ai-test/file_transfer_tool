#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件转移工具
扫描指定文件夹中的常用文件，并按照文件类型进行分类转移
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from pathlib import Path
import time


class FileTransferTool:
    """文件转移工具主类"""
    
    # 定义常用文件类型
    FILE_TYPES = {
        '图片': ['.jpg', '.jpeg', '.png', '.gif'],
        '音乐': ['.mp3'],
        '视频': ['.mp4'],
        '文档': ['.pdf', '.doc', '.docx', '.txt'],
        '表格': ['.xls', '.xlsx', '.csv'],
        '演示': ['.ppt', '.pptx'],
        '压缩': ['.zip', '.rar', '.7z'],
        
    }
    
    # 程序类文件扩展名，需要跳过
    PROGRAM_FILE_EXTENSIONS = [
        '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.apk', '.app', '.command',
        '.appimage', '.snap', '.flatpak', '.bin', '.run', '.out', '.jar', '.war'
    ]
    
    # 代码格式文件扩展名，需要跳过
    CODE_FILE_EXTENSIONS = [
        '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.cs', '.php',
        '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r', '.m', '.sh', '.bat',
        '.ps1', '.sql', '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
        '.conf', '.log', '.md', '.tex', '.less', '.sass', '.scss', '.vue', '.jsx',
        '.tsx', '.ts', '.dart', '.lua', '.pl', '.vb', '.asm', '.s', '.dockerfile'
    ]
    
    # 系统和缓存文件目录，需要跳过
    SKIP_DIRS = [
        '$Recycle.Bin', 'System Volume Information', 'RECYCLER',
        'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
        'AppData', 'Temp', 'tmp', 'cache', 'Cache', '.cache',
        '__pycache__', 'node_modules', '.git', '.svn'
    ]
    
    def __init__(self, root):
        """初始化文件转移工具"""
        self.root = root
        self.root.title("文件转移工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        # 设置窗口默认最大化
        self.root.state('zoomed')  # Windows系统最大化窗口
        
        # 变量
        self.source_path = tk.StringVar()
        self.target_path = tk.StringVar()
        self.organize_by_type = tk.BooleanVar(value=True)
        self.custom_extensions = tk.StringVar()  # 用户自定义扩展名
        self.is_running = False
        self.scanned_files = []  # 存储扫描到的文件信息
        
        # 文件类型选择变量
        self.file_type_vars = {}
        for file_type in self.FILE_TYPES:
            self.file_type_vars[file_type] = tk.BooleanVar(value=True)
        
        # 创建UI
        self.create_ui()
    
    def create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 源文件夹选择
        source_frame = ttk.LabelFrame(main_frame, text="源文件夹", padding="10")
        source_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(source_frame, textvariable=self.source_path, width=70).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(source_frame, text="浏览", command=self.browse_source_folder).pack(side=tk.RIGHT)
        
        # 目标文件夹选择
        target_frame = ttk.LabelFrame(main_frame, text="目标文件夹", padding="10")
        target_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(target_frame, textvariable=self.target_path, width=70).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(target_frame, text="浏览", command=self.browse_target_folder).pack(side=tk.RIGHT)
        
        # 选项框架
        options_frame = ttk.LabelFrame(main_frame, text="选项", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # 其他选项
        ttk.Checkbutton(options_frame, text="按文件类型分类", variable=self.organize_by_type).pack(anchor=tk.W, pady=2)
        
        # 文件类型选择
        file_type_frame = ttk.LabelFrame(options_frame, text="文件类型选择")
        file_type_frame.pack(fill=tk.X, pady=5)
        
        # 创建文件类型复选框
        checkbox_frame = ttk.Frame(file_type_frame)
        checkbox_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 每行显示3个复选框
        col = 0
        for file_type in self.FILE_TYPES:
            if col % 3 == 0:
                row_frame = ttk.Frame(checkbox_frame)
                row_frame.pack(fill=tk.X, pady=2)
            
            ttk.Checkbutton(row_frame, text=file_type, variable=self.file_type_vars[file_type]).pack(side=tk.LEFT, padx=5)
            col += 1
        
        # 全选/全不选按钮
        button_frame = ttk.Frame(file_type_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="全选", command=self.select_all_file_types).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全不选", command=self.deselect_all_file_types).pack(side=tk.LEFT, padx=5)
        
        # 临时扫描类型选项
        custom_frame = ttk.Frame(options_frame)
        custom_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(custom_frame, text="临时扫描类型:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(custom_frame, textvariable=self.custom_extensions, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(custom_frame, text="(输入扩展名，用逗号分隔，如: .xyz,.abc)").pack(side=tk.LEFT)
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.scan_button = ttk.Button(button_frame, text="扫描文件", command=self.scan_files_button)
        self.scan_button.pack(side=tk.LEFT, padx=5)
        
        self.copy_button = ttk.Button(button_frame, text="复制到目标文件夹", command=lambda: self.start_transfer("copy"), state=tk.DISABLED)
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        self.move_button = ttk.Button(button_frame, text="移动到目标文件夹", command=lambda: self.start_transfer("move"), state=tk.DISABLED)
        self.move_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_transfer, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # 状态标签
        self.status_label = ttk.Label(progress_frame, text="就绪")
        self.status_label.pack(anchor=tk.W)
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="扫描结果", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建Treeview显示文件信息
        columns = ("文件名", "扩展名", "大小", "路径")
        self.file_tree = ttk.Treeview(log_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def select_all_file_types(self):
        """全选所有文件类型"""
        for file_type in self.file_type_vars:
            self.file_type_vars[file_type].set(True)
    
    def deselect_all_file_types(self):
        """全不选所有文件类型"""
        for file_type in self.file_type_vars:
            self.file_type_vars[file_type].set(False)
    
    def browse_source_folder(self):
        """浏览源文件夹"""
        folder = filedialog.askdirectory(title="选择源文件夹")
        if folder:
            self.source_path.set(folder)
            self.log(f"已选择源文件夹: {folder}")
    
    def browse_target_folder(self):
        """浏览目标文件夹"""
        folder = filedialog.askdirectory(title="选择目标文件夹")
        if folder:
            self.target_path.set(folder)
            self.log(f"已选择目标文件夹: {folder}")
    
    def log(self, message):
        """添加日志信息"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")  # 在控制台输出日志
    
    def update_status(self, status):
        """更新状态标签"""
        self.status_label.config(text=status)
    
    def scan_files_button(self):
        """扫描文件按钮点击事件"""
        if self.is_running:
            return
            
        source = self.source_path.get()
        if not source or not os.path.exists(source):
            messagebox.showerror("错误", "请选择有效的源文件夹")
            return
            
        self.is_running = True
        self.scan_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 清空之前的扫描结果
        self.file_tree.delete(*self.file_tree.get_children())
        self.scanned_files = []
        
        # 在新线程中执行扫描
        threading.Thread(target=self.scan_files_thread, args=(source,), daemon=True).start()
        
    def scan_files_thread(self, source):
        """在后台线程中扫描文件"""
        try:
            self.scan_files(source)
            
            # 扫描完成后更新UI
            self.root.after(0, self.scan_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"扫描过程中发生错误: {str(e)}"))
            self.root.after(0, self.reset_ui)
            
    def scan_complete(self):
        """扫描完成后的UI更新"""
        self.is_running = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 如果有扫描结果，启用复制和移动按钮
        if self.scanned_files:
            self.copy_button.config(state=tk.NORMAL)
            self.move_button.config(state=tk.NORMAL)
            messagebox.showinfo("扫描完成", f"共扫描到 {len(self.scanned_files)} 个文件")
        else:
            messagebox.showinfo("扫描完成", "未找到符合条件的文件")
            
    def reset_ui(self):
        """重置UI状态"""
        self.is_running = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def start_transfer(self, mode):
        """开始转移文件"""
        if self.is_running:
            return
            
        source = self.source_path.get()
        target = self.target_path.get()
        
        if not source or not os.path.exists(source):
            messagebox.showerror("错误", "请选择有效的源文件夹")
            return
            
        if not target:
            messagebox.showerror("错误", "请选择目标文件夹")
            return
            
        if not self.scanned_files:
            messagebox.showerror("错误", "没有可转移的文件，请先扫描文件")
            return
            
        # 确认对话框
        mode_text = "复制" if mode == "copy" else "移动"
        confirm_msg = f"确定要{mode_text}文件吗？\n\n"
        confirm_msg += f"源文件夹: {source}\n"
        confirm_msg += f"目标文件夹: {target}\n"
        confirm_msg += f"操作模式: {mode_text}\n"
        confirm_msg += f"文件数量: {len(self.scanned_files)}\n"
        
        if not messagebox.askyesno("确认", confirm_msg):
            return
            
        self.is_running = True
        self.copy_button.config(state=tk.DISABLED)
        self.move_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 在新线程中执行转移
        threading.Thread(target=self.transfer_files_thread, args=(source, target, mode), daemon=True).start()
        
    def transfer_files_thread(self, source, target, mode):
        """在后台线程中转移文件"""
        try:
            self.transfer_files(source, target, mode)
            # 转移完成后更新UI
            self.root.after(0, self.transfer_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"转移过程中发生错误: {str(e)}"))
            self.root.after(0, self.reset_transfer_ui)
            
    def transfer_complete(self):
        """转移完成后的UI更新"""
        self.is_running = False
        self.copy_button.config(state=tk.NORMAL if self.scanned_files else tk.DISABLED)
        self.move_button.config(state=tk.NORMAL if self.scanned_files else tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        messagebox.showinfo("转移完成", "文件转移操作已完成")
        
    def reset_transfer_ui(self):
        """重置转移UI状态"""
        self.is_running = False
        self.copy_button.config(state=tk.NORMAL if self.scanned_files else tk.DISABLED)
        self.move_button.config(state=tk.NORMAL if self.scanned_files else tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        
    def stop_transfer(self):
        """停止文件转移"""
        self.is_running = False
        self.copy_button.config(state=tk.NORMAL if self.scanned_files else tk.DISABLED)
        self.move_button.config(state=tk.NORMAL if self.scanned_files else tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.log("用户取消了文件转移操作")
        self.update_status("已取消")
    
    def transfer_files(self, source, target, mode):
        """转移文件"""
        try:
            organize = self.organize_by_type.get()
            
            # 创建带时间戳的备份文件夹
            current_time = time.strftime("%Y%m%d_%H%M%S")
            backup_folder = os.path.join(target, f"备份_{current_time}")
            os.makedirs(backup_folder, exist_ok=True)
            
            self.log(f"已创建备份文件夹: {backup_folder}")
            
            # 获取已扫描的文件列表
            files = self.scanned_files
            if not files:
                self.log("没有找到符合条件的文件")
                self.update_status("没有找到符合条件的文件")
                return
            
            self.log(f"找到 {len(files)} 个文件")
            self.update_status(f"找到 {len(files)} 个文件，准备转移...")
            
            # 按类型组织文件
            if organize:
                # 创建分类文件夹
                file_types = set()
                for file_info in files:
                    file_type = file_info['type']
                    file_types.add(file_type)
                
                for file_type in file_types:
                    type_folder = os.path.join(backup_folder, file_type)
                    os.makedirs(type_folder, exist_ok=True)
            
            # 转移文件
            success_count = 0
            fail_count = 0
            
            for i, file_info in enumerate(files):
                if not self.is_running:
                    break
                
                try:
                    file_path = file_info['path']
                    filename = os.path.basename(file_path)
                    file_type = file_info['type']
                    
                    # 确定目标路径
                    if organize:
                        target_dir = os.path.join(backup_folder, file_type)
                    else:
                        target_dir = backup_folder
                    
                    target_path = os.path.join(target_dir, filename)
                    
                    # 如果目标文件已存在，添加序号
                    if os.path.exists(target_path):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(os.path.join(target_dir, f"{base}_{counter}{ext}")):
                            counter += 1
                        target_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    
                    # 执行转移
                    if mode == "copy":
                        shutil.copy2(file_path, target_path)
                        operation = "复制"
                    else:
                        shutil.move(file_path, target_path)
                        operation = "移动"
                    
                    success_count += 1
                    self.log(f"{operation}成功: {filename} -> {os.path.relpath(target_path, target)}")
                    
                    # 更新进度条
                    progress = int((i + 1) / len(files) * 100)
                    self.progress.config(value=progress)
                    self.update_status(f"处理中... {i+1}/{len(files)} ({progress}%)")
                    
                except Exception as e:
                    fail_count += 1
                    self.log(f"处理失败: {file_path} - {str(e)}")
            
            # 完成
            if self.is_running:
                self.log(f"转移完成! 成功: {success_count}, 失败: {fail_count}")
                self.update_status(f"转移完成! 成功: {success_count}, 失败: {fail_count}")
            else:
                self.log("转移已停止")
                self.update_status("转移已停止")
                
        except Exception as e:
            self.log(f"转移过程中发生错误: {str(e)}")
            self.update_status(f"转移失败: {str(e)}")
            raise
    
    def scan_files(self, source_dir):
        """扫描源文件夹中的文件"""
        self.scanned_files = []  # 清空之前的扫描结果
        
        # 检查是否是微信目录，如果是，只扫描msg文件夹
        if "wechat" in source_dir.lower() or "weixin" in source_dir.lower():
            # 查找msg文件夹
            msg_dir = None
            for root, dirs, filenames in os.walk(source_dir):
                for dirname in dirs:
                    if dirname.lower() == "msg":
                        msg_dir = os.path.join(root, dirname)
                        break
                if msg_dir:
                    break
            
            # 如果找到msg文件夹，只扫描该文件夹
            if msg_dir:
                self.log(f"检测到微信目录，只扫描msg文件夹: {msg_dir}")
                source_dir = msg_dir
            else:
                self.log("在微信目录中未找到msg文件夹，将扫描整个目录")
        
        # 获取目标文件夹路径
        target_dir = self.target_path.get()
        
        for root, dirs, filenames in os.walk(source_dir):
            # 跳过系统目录
            dirs[:] = [d for d in dirs if not self.should_skip_dir(d)]
            
            # 检查当前目录是否是目标文件夹或其子目录
            if target_dir and (root == target_dir or root.startswith(target_dir + os.sep)):
                self.log(f"跳过目标文件夹及其子目录: {root}")
                continue
            
            for filename in filenames:
                if not self.is_running:
                    break
                
                file_path = os.path.join(root, filename)
                
                # 跳过系统文件和隐藏文件
                if self.should_skip_file(filename):
                    continue
                
                # 确定文件类型
                file_type = self.get_file_type(filename)
                
                # 严格按照常用文件类型进行筛选，只处理FILE_TYPES中定义的文件类型和用户自定义的临时类型
                if file_type == '其他':
                    continue
                
                # 获取文件大小
                try:
                    file_size = os.path.getsize(file_path)
                    # 格式化文件大小
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.2f} KB"
                    elif file_size < 1024 * 1024 * 1024:
                        size_str = f"{file_size / (1024 * 1024):.2f} MB"
                    else:
                        size_str = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
                except:
                    size_str = "未知"
                
                # 获取文件名和扩展名
                file_name = os.path.splitext(filename)[0]
                file_ext = os.path.splitext(filename)[1].lower()
                
                # 添加到扫描结果
                file_info = {
                    'path': file_path,
                    'name': file_name,
                    'ext': file_ext,
                    'size': file_size,
                    'type': file_type
                }
                self.scanned_files.append(file_info)
                
                # 在UI中添加到Treeview
                self.root.after(0, lambda fn=file_name, fe=file_ext, fs=size_str, fp=file_path: 
                               self.file_tree.insert("", tk.END, values=(fn, fe, fs, fp)))
        
        self.log(f"扫描完成，共找到 {len(self.scanned_files)} 个文件")
        return self.scanned_files
    
    def should_skip_dir(self, dirname):
        """检查是否应该跳过目录"""
        dirname_lower = dirname.lower()
        return any(skip.lower() in dirname_lower for skip in self.SKIP_DIRS)
    
    def should_skip_file(self, filename):
        """检查是否应该跳过文件"""
        # 跳过隐藏文件
        if filename.startswith('.'):
            return True
        
        # 跳过系统文件
        if filename.lower() in ['thumbs.db', 'desktop.ini', 'ds_store']:
            return True
        
        # 跳过代码格式文件
        _, ext = os.path.splitext(filename)
        if ext.lower() in self.CODE_FILE_EXTENSIONS:
            return True
        
        # 跳过程序类文件
        if ext.lower() in self.PROGRAM_FILE_EXTENSIONS:
            return True
        
        return False
    
    def get_file_type(self, filename):
        """根据文件扩展名确定文件类型"""
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # 首先检查是否匹配用户自定义的扩展名
        custom_exts = self.custom_extensions.get()
        if custom_exts:
            # 分割用户输入的扩展名列表
            custom_list = [e.strip().lower() for e in custom_exts.split(',') if e.strip()]
            if ext in custom_list:
                return '临时类型'
        
        # 然后检查预定义的文件类型，但只返回用户选择的类型
        for file_type, extensions in self.FILE_TYPES.items():
            if ext in extensions and self.file_type_vars[file_type].get():
                return file_type
        
        return '其他'


def main():
    """主函数"""
    root = tk.Tk()
    app = FileTransferTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()