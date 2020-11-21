import logging
import subprocess
from pathlib import Path

from . import release信息


此處 = Path(__file__).parent

librian面板外層 = 此處 / '../..'

嵌入的python路徑 = librian面板外層 / 'python36/python.exe'

嵌入的git路徑 = librian面板外層 / 'MinGit-2.25.0-busybox-64-bit/cmd/git.exe'


def 自我更新():
    if release信息.是release:
        git路徑 = 嵌入的git路徑
    else:
        try:
            git路徑 = 'git'
            subprocess.check_call('git --version', stdout=subprocess.DEVNULL)
        except FileNotFoundError:
            raise FileNotFoundError('需要一個Git。更新功能需要你有Git命令可用，或者使用release版本中嵌入的Git。')
    subprocess.run(
        [str(git路徑), 'pull', 'origin', 'slave'],
        shell=True,
        check=True,
        stderr=subprocess.PIPE,
        cwd=librian面板外層,
    )

    if release信息.是release:
        subprocess.run(
            [str(嵌入的python路徑), '-m', 'pip', 'install', '-r', 'requirements.txt'],
            shell=True,
            check=True,
            stderr=subprocess.PIPE,
            cwd=librian面板外層,
        )
