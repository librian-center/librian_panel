import os
import sys
import copy
import json
import shutil
import logging
import datetime
import threading
import subprocess
from pathlib import Path

import yaml
import dulwich.repo
from rimo_utils.cef_tools.vue_ob import vue_ob
try:
    import wx
    import rimo_utils.cef_tools.wxcef as wxcef
except ModuleNotFoundError:
    logging.warning('沒能import wx，改爲使用pyside2。')
    import rimo_utils.cef_tools.fake_wx as wx
    import rimo_utils.cef_tools.qtcef as wxcef

from . import 更新器


此處 = Path(__file__).parent


def 查詢文件打開方式(文件名):
    import win32api
    import win32con
    ext = os.path.splitext(文件名)[-1]
    try:
        key = win32api.RegOpenKey(win32con.HKEY_CLASSES_ROOT, ext, 0, win32con.KEY_READ)
    except:
        return None
    q = win32api.RegQueryValue(key, '')
    key = win32api.RegOpenKey(win32con.HKEY_CLASSES_ROOT, f'{q}\\shell\\open\\command', 0, win32con.KEY_READ)
    q = win32api.RegQueryValue(key, '')
    return q


class 山彥(vue_ob):
    def __init__(self, 窗口):
        super().__init__()
        self.窗口 = 窗口
        self.vue.存檔資料 = []
        self.當前工程配置 = None
        if (此處/'存檔資料/存檔資料.yaml').is_file():
            with open(此處/'存檔資料/存檔資料.yaml') as f:
                self.vue.存檔資料 = yaml.safe_load(f)
        repo = dulwich.repo.Repo('.')
        最後提交unix時間 = repo[repo.head()].author_time
        self.vue.最後提交時間 = datetime.datetime.fromtimestamp(最後提交unix時間).strftime('%y-%m-%d')

    def js(self, x):
        self.窗口.browser.ExecuteJavascript(x)

    def alert(self, title, icon=None, text=None):
        msg = {'title': title, 'icon': icon, 'text': text}
        self.js(f'Swal.fire({json.dumps(msg)})')

    def vue更新(self, 內容):
        t = self.vue.用戶設置 if '用戶設置' in self.vue._內容 else None
        if t != 內容['存檔資料']:
            os.makedirs(此處 / '存檔資料', exist_ok=True)
            with open(此處 / '存檔資料/存檔資料.yaml', 'w', encoding='utf8') as f:
                f.write(yaml.dump(內容['存檔資料']))
        super().vue更新(內容)

    def 讀取工程信息(self, 工程路徑):
        self.當前工程配置 = {'工程路徑': 工程路徑}
        with open((工程路徑) / '工程配置.yaml', encoding='utf8') as f:
            a = yaml.safe_load(f)
            for v in a.values():
                self.當前工程配置.update(v)
        if self.當前工程配置['圖標']:
            圖標路徑 = Path(工程路徑) / self.當前工程配置['圖標']
        else:
            圖標路徑 = 此處 / 'librian.ico'
        主解析度 = self.當前工程配置['主解析度']
        標題 = self.當前工程配置['標題']
        self.vue.存檔資料 = [{'工程路徑': 工程路徑, '圖標路徑': 圖標路徑, '標題': 標題}] + \
            [工程信息 for 工程信息 in self.vue.存檔資料 if not 工程路徑.samefile(工程信息['工程路徑'])]
        return 圖標路徑, 主解析度, 標題

    def 同調(self, 工程路徑):
        工程路徑 = Path(工程路徑)
        v = self.vue
        try:
            v.工程路徑 = 工程路徑
            v.圖標路徑, v.主解析度, v.標題 = self.讀取工程信息(工程路徑)
        except Exception as e:
            logging.exception(e)
            self.alert('工程配置文件不正確。', 'error')
        self.js('進入工程()')

    def 開啓工程(self, 工程路徑=None):
        if 工程路徑:
            self.同調(工程路徑)
        else:
            with wx.DirDialog(self.窗口, '选择文件夹') as dlg:
                dlg.SetPath(str(此處.resolve()))
                if dlg.ShowModal() == wx.ID_OK:
                    self.同調(dlg.GetPath())

    def 建立工程(self, 新工程名, 使用潘大爺的模板):
        新工程路徑 = (此處 / '../../project' / 新工程名).resolve()
        if 新工程路徑.is_dir():
            self.alert('已經有這個工程了。', 'error')
            return
        if 使用潘大爺的模板:
            shutil.copytree(此處 / '../模板/潘大爺的模板', 新工程路徑)
        else:
            shutil.copytree(此處 / '../模板/默認模板', 新工程路徑)
        self.同調(新工程路徑)

    def 運行(self):
        if wxcef.WINDOWS:
            subprocess.Popen(
                [sys.executable, '-m', 'librian', '--project', self.vue.工程路徑],
                shell=True,
            )
        else:
            env = copy.copy(os.environ)
            env['LD_LIBRARY_PATH'] = wxcef.ld_library_path
            subprocess.Popen(
                [sys.executable, '-m', 'librian', '--project', self.vue.工程路徑],
                shell=False,
                env=env
            )

    def 運行同時編寫(self):
        if wxcef.WINDOWS:
            subprocess.Popen(
                [sys.executable, '-m', 'librian', '--project', self.vue.工程路徑, '--編寫模式', 'True'],
                shell=True
            )
            劇本文件名 = self.vue.工程路徑 / self.當前工程配置['劇本入口']
            if 查詢文件打開方式(劇本文件名):
                os.system(f'"{劇本文件名}"')
            else:
                os.system(f'notepad "{劇本文件名}"')
        else:
            env = dict()
            env.update(os.environ)
            env['LD_LIBRARY_PATH'] = wxcef.ld_library_path
            subprocess.Popen(
                [sys.executable, '-m', 'librian', '--project', self.vue.工程路徑, '--編寫模式', 'True'],
                shell=False,
                env=env)
            if wxcef.MAC:
                subprocess.Popen(['open', f'{self.vue.工程路徑}/{self.當前工程配置["劇本入口"]}'],
                                 shell=False)
            elif wxcef.LINUX:
                subprocess.Popen(
                    ['xdg-open', f'{self.vue.工程路徑}/{self.當前工程配置["劇本入口"]}'],
                    shell=False)

    def 打開文件夾(self):
        if wxcef.WINDOWS:
            subprocess.Popen(['start', self.vue.工程路徑], shell=True)
        elif wxcef.MAC:
            subprocess.Popen(['open', self.vue.工程路徑], shell=False)
        elif wxcef.LINUX:
            subprocess.Popen(['xdg-open', self.vue.工程路徑], shell=False)

    def 生成exe(self):
        from librian面板.雜物 import 構建exe
        if self.當前工程配置["圖標"]:
            構建exe.構建工程(self.vue.工程路徑, self.當前工程配置["標題"], f'{self.vue.工程路徑}/{self.當前工程配置["圖標"]}')
        else:
            構建exe.構建工程(self.vue.工程路徑, self.當前工程配置["標題"])
        self.alert('好了', 'success')

    # def 生成html(self, 目標路徑):
    #     from librian.librian本體 import 幻象
    #     目標路徑 = Path(目標路徑)
    #     if 目標路徑.is_dir():
    #         self.alert('目录已经存在', 'error')
    #     else:
    #         幻象.幻象化(目標路徑)
    #         self.alert('好了', 'success')

    def 瀏覽器打開(self, s):
        import webbrowser
        webbrowser.open(s)
    
    def 自我更新(self, callback):
        def t():
            try:
                更新器.自我更新()
            except subprocess.CalledProcessError as e:
                callback.Call([e.returncode, e.stderr.decode('gbk')])
            except Exception as e:
                callback.Call([1, e.__repr__()])
            callback.Call([0, ''])
        threading.Thread(target=t).start()

    def 退出(self):
        exit()


app, 瀏覽器 = wxcef.group(
    title='librian面板', 
    url=f'file:///{(此處/"面板前端/面板.html").resolve()}',
    icon=此處 / 'librian.ico', 
    size=(960, 540),
)
真山彥 = 山彥(app.frame)
app.frame.set_browser_object('山彥', 真山彥)
app.MainLoop()
