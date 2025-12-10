# coding=utf-8
"""
    @project: MaxKB
    @Author：虎
    @file： function_code.py
    @date：2024/8/7 16:11
    @desc:
"""
import os
import pickle
import subprocess
import sys
import uuid
import logging
import platform
from textwrap import dedent

from smartdoc.const import BASE_DIR
from smartdoc.const import PROJECT_DIR

python_directory = sys.executable
logger = logging.getLogger(__name__)


class FunctionExecutor:
    def __init__(self, sandbox=False):
        # 是否启用沙箱执行（容器内使用 /opt 路径与 sandbox 用户）
        self.sandbox = sandbox
        if sandbox:
            # Windows 开发环境下退化为项目 data 目录；非 Windows 使用固定沙箱目录
            if platform.system() == "Windows":
                self.sandbox_path = os.path.join(PROJECT_DIR, 'data', 'sandbox')
            else:
                self.sandbox_path = '/opt/maxkb/app/sandbox'
            # 沙箱执行使用的低权限用户名称
            self.user = 'root'
        else:
            # 非沙箱模式使用项目本地 data/sandbox 目录
            self.sandbox_path = os.path.join(PROJECT_DIR, 'data', 'sandbox')
            self.user = None
        self._createdir()
        if self.sandbox and platform.system() != "Windows":
            # 仅在类 Unix 系统下调整目录属主，确保沙箱用户可读写
            os.system(f"chown -R {self.user}:root {self.sandbox_path}")
        logger.info(f"函数执行器初始化完成 sandbox={self.sandbox} 路径={self.sandbox_path} 用户={self.user}")

    def _createdir(self):
        # 严格的权限掩码，避免结果/代码文件被其他用户读取
        old_mask = os.umask(0o077)
        try:
            # 沙箱根目录
            os.makedirs(self.sandbox_path, 0o700, exist_ok=True)
            # 运行时生成的 Python 代码目录
            os.makedirs(os.path.join(self.sandbox_path, 'execute'), 0o700, exist_ok=True)
            # 结果文件目录（通过 pickle 写入/读取）
            os.makedirs(os.path.join(self.sandbox_path, 'result'), 0o700, exist_ok=True)
        finally:
            os.umask(old_mask)

    def exec_code(self, code_str, keywords):
        # 生成一次性执行 ID 与对应结果文件路径
        _id = str(uuid.uuid1())
        success = '{"code":200,"msg":"成功","data":exec_result}'
        err = '{"code":500,"msg":str(e),"data":None}'
        result_path = f'{self.sandbox_path}/result/{_id}.result'
        logger.info(f"开始执行函数 任务ID={_id} 沙箱={self.sandbox} 结果文件={result_path}")
        _exec_code = f"""
try:
    import os
    import pickle
    # 清理敏感环境变量，避免被执行代码滥用
    env = dict(os.environ)
    for key in list(env.keys()):
        if key in os.environ and (key.startswith('MAXKB') or key.startswith('POSTGRES') or key.startswith('PG')):
            del os.environ[key]
    # 注入参数与函数代码，执行后将结果通过 pickle 写入 result 文件
    locals_v={'{}'}
    keywords={keywords}
    globals_v=globals()
    exec({dedent(code_str)!a}, globals_v, locals_v)
    f_name, f = locals_v.popitem()
    for local in locals_v:
        globals_v[local] = locals_v[local]
    exec_result=f(**keywords)
    with open({result_path!a}, 'wb') as file:
        file.write(pickle.dumps({success}))
except Exception as e:
    with open({result_path!a}, 'wb') as file:
        file.write(pickle.dumps({err}))
"""
        if self.sandbox:
            # 沙箱模式：以 sandbox 用户执行生成的代码文件
            subprocess_result = self._exec_sandbox(_exec_code, _id)
        else:
            # 本地模式：直接以当前 Python 进程子进程执行
            subprocess_result = self._exec(_exec_code)
        # 子进程返回码为 1 代表 Python 解释器层面错误（非业务错误）
        logger.info(f"子进程执行完成 任务ID={_id} 返回码={subprocess_result.returncode}")
        if subprocess_result.stdout:
            logger.debug(f"子进程标准输出 任务ID={_id}: {subprocess_result.stdout}")
        if subprocess_result.stderr:
            logger.warning(f"子进程错误输出 任务ID={_id}: {subprocess_result.stderr}")
        if subprocess_result.returncode == 1:
            raise Exception(subprocess_result.stderr)
        # 读取结果文件并反序列化为 dict
        if not os.path.exists(result_path):
            logger.error(f"未找到结果文件 任务ID={_id} 路径={result_path}")
            raise Exception("函数执行失败：结果文件不存在")
        with open(result_path, 'rb') as file:
            result = pickle.loads(file.read())
        os.remove(result_path)
        logger.info(f"函数执行结束 任务ID={_id} 结果码={result.get('code') if isinstance(result, dict) else 'N/A'}")
        # 业务成功返回 data，否则抛出错误信息
        if result.get('code') == 200:
            return result.get('data')
        raise Exception(result.get('msg'))

    def _exec_sandbox(self, _code, _id):
        # 将待执行代码写入沙箱 execute 目录下的临时 .py 文件
        exec_python_file = f'{self.sandbox_path}/execute/{_id}.py'
        with open(exec_python_file, 'w') as file:
            file.write(_code)
            # 确保文件属主为 sandbox，属组 root，便于 su 切换执行
            os.system(f"chown {self.user}:root {exec_python_file}")
        kwargs = {'cwd': BASE_DIR}
        logger.debug(f"沙箱执行启动 任务ID={_id} 脚本={exec_python_file} 工作目录={BASE_DIR}")
        subprocess_result = subprocess.run(
            ['su', '-s', '/bin/sh', '-c', f"exec {python_directory} {exec_python_file}", self.user],
            text=True,
            capture_output=True, **kwargs)
        os.remove(exec_python_file)
        return subprocess_result

    @staticmethod
    def _exec(_code):
        # 非沙箱模式通过 -c 执行内联代码
        logger.debug("本地执行启动（非沙箱模式）")
        return subprocess.run([python_directory, '-c', _code], text=True, capture_output=True)
