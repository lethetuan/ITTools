"""
Folder Size Module (like TreeSize / WizTree)
Shows folder sizes with treemap-like visualization
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import threading
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


def get_folder_size(path):
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                try:
                    fp = os.path.join(dirpath, f)
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return total


def fmt_size(b):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f'{b:.1f} {unit}'
        b /= 1024
    return f'{b:.1f} PB'


class FolderSize:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('900x650')
        self.parent.configure(bg=COLORS['bg'])
        self.scan_queue = queue.Queue()
        self.scanning = False
        self.item_data = {}
        self.setup_ui()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='📁  Folder Size Analyzer', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Path bar
        path_frame = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        path_frame.pack(fill='x', padx=0)
        tk.Label(path_frame, text='Path:', font=FONTS['normal'],
                  bg=COLORS['bg_dark']).pack(side='left', padx=10, pady=6)
        self.path_var = tk.StringVar(value='C:\\')
        path_entry = tk.Entry(path_frame, textvariable=self.path_var,
                               font=FONTS['normal'], width=50)
        path_entry.pack(side='left', padx=5, pady=5)
        tk.Button(path_frame, text='📂 Browse', font=FONTS['small'],
                   bg=COLORS['info'], fg='white', relief='flat',
                   padx=8, cursor='hand2',
                   command=self.browse_folder).pack(side='left', padx=3)
        self.btn_scan = tk.Button(path_frame, text='🔍 Scan', font=FONTS['subtitle'],
                                   bg=COLORS['accent'], fg='white', relief='flat',
                                   padx=15, pady=4, cursor='hand2',
                                   command=self.start_scan)
        self.btn_scan.pack(side='left', padx=5)
        self.btn_stop = tk.Button(path_frame, text='⏹ Stop', font=FONTS['subtitle'],
                                   bg=COLORS['danger'], fg='white', relief='flat',
                                   padx=15, pady=4, cursor='hand2', state='disabled',
                                   command=self.stop_scan)
        self.btn_stop.pack(side='left', padx=3)

        # Quick access
        qa_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        qa_frame.pack(fill='x', padx=10, pady=3)
        tk.Label(qa_frame, text='Quick:', font=FONTS['small'],
                  bg=COLORS['bg']).pack(side='left', padx=3)
        drives = [d + ':\\' for d in 'CDEFGHIJKLMNOPQRSTUVWXYZ'
                   if os.path.exists(d + ':\\')]
        for drive in drives:
            tk.Button(qa_frame, text=drive, font=FONTS['small'],
                       bg=COLORS['btn_bg'], fg=COLORS['text'],
                       relief='groove', padx=5, cursor='hand2',
                       command=lambda d=drive: self._quick_scan(d)
                       ).pack(side='left', padx=2)

        special = [
            ('🏠 Desktop', os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'Desktop')),
            ('📄 Documents', os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'Documents')),
            ('⬇️ Downloads', os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'Downloads')),
            ('🖼️ Pictures', os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'Pictures')),
        ]
        for name, path in special:
            tk.Button(qa_frame, text=name, font=FONTS['small'],
                       bg=COLORS['btn_bg'], fg=COLORS['text'],
                       relief='groove', padx=5, cursor='hand2',
                       command=lambda p=path: self._quick_scan(p)
                       ).pack(side='left', padx=2)

        # Main split
        paned = tk.PanedWindow(self.parent, orient='horizontal',
                                bg=COLORS['bg'], sashwidth=4)
        paned.pack(fill='both', expand=True, padx=5, pady=3)

        # Tree pane
        tree_frame = tk.Frame(paned, bg=COLORS['bg'])

        cols = ('Name', 'Size', 'Files', '%', 'Bar')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings tree',
                                  selectmode='browse')
        self.tree['columns'] = ('Size', 'Files', '%', 'Bar')
        self.tree.heading('#0', text='Folder / File', anchor='w')
        self.tree.column('#0', width=280, minwidth=150)
        widths = [100, 70, 50, 150]
        for col, w in zip(('Size', 'Files', '%', 'Bar'), widths):
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=w, minwidth=40)

        vsb = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)

        self.tree.tag_configure('folder', foreground='#F39C12')
        self.tree.tag_configure('large', foreground='#E74C3C')
        self.tree.tag_configure('medium', foreground='#E67E22')
        self.tree.tag_configure('small', foreground='#27AE60')

        self.tree.bind('<Double-1>', self.on_expand)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        paned.add(tree_frame, minsize=400)

        # Detail pane
        detail_frame = tk.Frame(paned, bg=COLORS['bg'])
        tk.Label(detail_frame, text='Details', font=FONTS['subtitle'],
                  bg=COLORS['bg_dark'], pady=3).pack(fill='x')

        self.detail_text = tk.Text(detail_frame, font=FONTS['mono'],
                                    bg='#1E1E1E', fg='#D4D4D4',
                                    width=30, relief='flat', padx=10, pady=5)
        self.detail_text.pack(fill='both', expand=True)
        paned.add(detail_frame, minsize=200)

        # Status bar
        status_frame = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        status_frame.pack(fill='x', side='bottom')
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress.pack(side='left', padx=5, pady=3)
        self.status_var = tk.StringVar(value='Ready')
        tk.Label(status_frame, textvariable=self.status_var,
                  font=FONTS['small'], bg=COLORS['bg_dark'],
                  fg=COLORS['text_light']).pack(side='left', padx=5)

        # Context menu
        ctx = tk.Menu(self.parent, tearoff=0)
        ctx.add_command(label='📂 Open Folder', command=self.open_folder)
        ctx.add_command(label='🔍 Scan Subfolder', command=self.scan_subfolder)
        ctx.add_command(label='🗑️ Delete (Careful!)', command=self.delete_item)
        self.tree.bind('<Button-3>',
                        lambda e: ctx.post(e.x_root, e.y_root))

    def _quick_scan(self, path):
        self.path_var.set(path)
        self.start_scan()

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def start_scan(self):
        path = self.path_var.get().strip()
        if not os.path.exists(path):
            messagebox.showerror('Error', f'Đường dẫn không tồn tại: {path}')
            return
        self.tree.delete(*self.tree.get_children())
        self.item_data = {}
        self.scanning = True
        self.btn_scan.configure(state='disabled')
        self.btn_stop.configure(state='normal')
        self.progress.start()
        self.status_var.set(f'Scanning {path}...')
        threading.Thread(target=self._scan, args=(path,), daemon=True).start()

    def _scan(self, root_path):
        try:
            items = []
            try:
                entries = list(os.scandir(root_path))
            except PermissionError:
                entries = []

            for i, entry in enumerate(entries):
                if not self.scanning:
                    break
                self.status_var.set(f'Scanning: {entry.name}')
                try:
                    if entry.is_dir(follow_symlinks=False):
                        size = get_folder_size(entry.path)
                        file_count = self._count_files(entry.path)
                        items.append(('folder', entry.name, entry.path, size, file_count))
                    else:
                        size = entry.stat().st_size
                        items.append(('file', entry.name, entry.path, size, 1))
                except:
                    pass

            # Sort by size
            items.sort(key=lambda x: x[3], reverse=True)
            total_size = sum(x[3] for x in items)

            self.scan_queue.put(('clear',))
            for item_type, name, path, size, count in items:
                pct = (size / total_size * 100) if total_size > 0 else 0
                bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
                self.scan_queue.put((
                    'insert', item_type, name, path, size, count, pct, bar
                ))

            self.scan_queue.put(('done', total_size, len(items)))
        except Exception as e:
            self.scan_queue.put(('error', str(e)))
        finally:
            self.scanning = False
            self.parent.after(0, self._finish_scan)

    def _count_files(self, path):
        count = 0
        try:
            for _, _, files in os.walk(path):
                count += len(files)
                if count > 10000:
                    break
        except:
            pass
        return count

    def _finish_scan(self):
        self._process_queue()
        self.progress.stop()
        self.btn_scan.configure(state='normal')
        self.btn_stop.configure(state='disabled')

    def _process_queue(self):
        try:
            while True:
                item = self.scan_queue.get_nowait()
                if item[0] == 'insert':
                    _, itype, name, path, size, count, pct, bar = item
                    if size > 1024 * 1024 * 100:  # >100MB
                        tag = 'large'
                    elif size > 1024 * 1024 * 10:  # >10MB
                        tag = 'medium'
                    else:
                        tag = 'small'
                    if itype == 'folder':
                        tag = 'folder'

                    prefix = '📁 ' if itype == 'folder' else '📄 '
                    iid = self.tree.insert('', 'end', text=prefix + name,
                                           values=(fmt_size(size), count,
                                                   f'{pct:.1f}%', bar),
                                           tags=(tag,))
                    self.item_data[iid] = {'path': path, 'type': itype}

                elif item[0] == 'done':
                    total = item[1]
                    count = item[2]
                    self.status_var.set(
                        f'✅ Done! {count} items, Total: {fmt_size(total)}')
                elif item[0] == 'error':
                    self.status_var.set(f'Error: {item[1]}')
        except queue.Empty:
            pass

    def stop_scan(self):
        self.scanning = False

    def on_expand(self, event):
        sel = self.tree.selection()
        if sel:
            data = self.item_data.get(sel[0])
            if data and data['type'] == 'folder':
                self._quick_scan(data['path'])

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        data = self.item_data.get(sel[0])
        if not data:
            return
        path = data['path']

        self.detail_text.configure(state='normal')
        self.detail_text.delete('1.0', 'end')
        try:
            stat = os.stat(path)
            import datetime
            info = [
                f'Path:\n  {path}\n\n',
                f'Type: {"Folder" if data["type"] == "folder" else "File"}\n',
                f'Size: {fmt_size(stat.st_size)}\n',
                f'Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}\n',
                f'Created: {datetime.datetime.fromtimestamp(stat.st_ctime)}\n',
            ]
            self.detail_text.insert('1.0', ''.join(info))
        except:
            pass
        self.detail_text.configure(state='disabled')

    def open_folder(self):
        sel = self.tree.selection()
        if sel:
            data = self.item_data.get(sel[0])
            if data:
                path = data['path']
                if data['type'] == 'file':
                    path = os.path.dirname(path)
                os.startfile(path)

    def scan_subfolder(self):
        sel = self.tree.selection()
        if sel:
            data = self.item_data.get(sel[0])
            if data and data['type'] == 'folder':
                self._quick_scan(data['path'])

    def delete_item(self):
        sel = self.tree.selection()
        if not sel:
            return
        data = self.item_data.get(sel[0])
        if not data:
            return
        path = data['path']
        if messagebox.askyesno('⚠️ Confirm Delete',
                                f'Xóa vĩnh viễn?\n\n{path}\n\n'
                                'Thao tác này KHÔNG THỂ HOÀN TÁC!',
                                icon='warning'):
            try:
                import shutil
                if data['type'] == 'folder':
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.tree.delete(sel[0])
                messagebox.showinfo('Deleted', f'Đã xóa: {path}')
            except Exception as e:
                messagebox.showerror('Error', str(e))


def get_system_drives():
    drives = []
    import string
    import ctypes
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            try:
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(drive_path),
                    None,
                    ctypes.byref(total_bytes),
                    ctypes.byref(free_bytes)
                )
                t_size = total_bytes.value
                f_size = free_bytes.value
                u_size = t_size - f_size
                drives.append({
                    "drive": drive_path,
                    "total": fmt_size(t_size),
                    "free": fmt_size(f_size),
                    "used": fmt_size(u_size),
                    "pct": round((u_size / t_size * 100), 1) if t_size > 0 else 0
                })
            except Exception:
                drives.append({"drive": drive_path, "total": "N/A", "free": "N/A", "used": "N/A", "pct": 0})
    return drives


def _count_files_helper(path):
    count = 0
    try:
        for _, _, files in os.walk(path):
            count += len(files)
            if count > 10000:
                break
    except Exception:
        pass
    return count


def scan_node_recursive(entry_path, current_depth=1, max_depth=2, prefix="node"):
    if not os.path.exists(entry_path):
        return None

    try:
        entries = list(os.scandir(entry_path))
    except Exception:
        return None

    items = []
    total_files = 0
    total_subfolders = 0

    for idx, entry in enumerate(entries, 1):
        node_id = f"{prefix}_{idx}"
        try:
            if entry.is_dir(follow_symlinks=False):
                total_subfolders += 1
                size = get_folder_size(entry.path)
                file_cnt = _count_files_helper(entry.path)

                children = []
                if current_depth < max_depth:
                    sub_res = scan_node_recursive(entry.path, current_depth + 1, max_depth, node_id)
                    if sub_res and sub_res.get("items"):
                        children = sub_res["items"]

                items.append({
                    "id": node_id,
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": True,
                    "size_bytes": size,
                    "formatted_size": fmt_size(size),
                    "file_count": file_cnt,
                    "has_children": True,
                    "children": children
                })
            else:
                total_files += 1
                size = entry.stat().st_size
                items.append({
                    "id": node_id,
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": False,
                    "size_bytes": size,
                    "formatted_size": fmt_size(size),
                    "file_count": 1,
                    "has_children": False,
                    "children": []
                })
        except Exception:
            pass

    items.sort(key=lambda x: x["size_bytes"], reverse=True)
    total_size = sum(x["size_bytes"] for x in items)

    for item in items:
        pct = (item["size_bytes"] / total_size * 100) if total_size > 0 else 0
        item["pct"] = round(pct, 1)

    return {
        "items": items,
        "total_bytes": total_size,
        "total_files": total_files,
        "total_subfolders": total_subfolders
    }


def scan_directory_sizes(root_path, max_items=250, max_depth=2):
    if not root_path or not os.path.exists(root_path):
        return {"success": False, "message": f"Đường dẫn không tồn tại: {root_path}"}

    res = scan_node_recursive(root_path, current_depth=1, max_depth=max_depth, prefix="node")
    if not res:
        return {"success": False, "message": f"Không thể truy cập thư mục: {root_path}"}

    items = res["items"]
    total_size = res["total_bytes"]

    return {
        "success": True,
        "path": root_path,
        "total_size": fmt_size(total_size),
        "total_bytes": total_size,
        "item_count": len(items),
        "file_count": res["total_files"],
        "subfolder_count": res["total_subfolders"],
        "items": items[:max_items]
    }


def get_system_drives_info():
    import shutil
    import string
    import os
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            try:
                total, used, free = shutil.disk_usage(drive_path)
                drives.append({
                    "drive": drive_path,
                    "total": fmt_size(total),
                    "total_bytes": total,
                    "used": fmt_size(used),
                    "used_bytes": used,
                    "free": fmt_size(free),
                    "free_bytes": free,
                    "pct": round((used / total * 100), 1) if total > 0 else 0
                })
            except Exception:
                pass
    return drives


def select_folder_dialog():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory(title="Chọn Thư Mục Phân Tích Dung Lượng")
        root.destroy()
        return path or ""
    except Exception:
        return ""


def open_in_explorer(path):
    if not path or not os.path.exists(path):
        return {"success": False, "message": "Đường dẫn không tồn tại."}
    try:
        if os.path.isfile(path):
            subprocess.run(f'explorer.exe /select,"{path}"', shell=True)
        else:
            os.startfile(path)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


def delete_path_item(path):
    if not path or not os.path.exists(path):
        return {"success": False, "message": "Đường dẫn không tồn tại!"}
    try:
        import shutil
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return {"success": True, "message": f"Đã xóa thành công: {path}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

