"""
启动Redis服务的管理命令（不使用Docker）
支持Windows/Linux/Mac的Redis启动
用法: python manage.py start_redis
"""
from django.core.management.base import BaseCommand
import subprocess
import sys
import os
import socket
import time
import platform
from pathlib import Path


class Command(BaseCommand):
    help = '启动Redis服务（不使用Docker）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='仅检查Redis是否运行，不启动'
        )

    def check_redis_connection(self, host='localhost', port=6379, timeout=1):
        """检查Redis连接"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def check_redis_installed(self):
        """检查Redis是否已安装"""
        try:
            result = subprocess.run(
                ['redis-server', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_redis_install_instructions(self):
        """获取Redis安装说明"""
        system = platform.system().lower()
        
        if system == 'windows':
            return {
                'title': 'Windows Redis 安装',
                'steps': [
                    '1. 下载Redis for Windows:',
                    '   https://github.com/microsoftarchive/redis/releases',
                    '2. 解压到任意目录（如 C:\\Redis）',
                    '3. 运行: C:\\Redis\\redis-server.exe',
                    '',
                    '或者使用WSL:',
                    '  wsl --install',
                    '  wsl',
                    '  sudo apt update && sudo apt install redis-server',
                    '  redis-server'
                ]
            }
        elif system == 'darwin':  # macOS
            return {
                'title': 'macOS Redis 安装',
                'steps': [
                    '使用Homebrew安装:',
                    '  brew install redis',
                    '',
                    '启动Redis:',
                    '  brew services start redis',
                    '  或直接运行: redis-server'
                ]
            }
        else:  # Linux
            return {
                'title': 'Linux Redis 安装',
                'steps': [
                    'Ubuntu/Debian:',
                    '  sudo apt update',
                    '  sudo apt install redis-server',
                    '  sudo systemctl start redis',
                    '',
                    'CentOS/RHEL:',
                    '  sudo yum install redis',
                    '  sudo systemctl start redis',
                    '',
                    '启动Redis:',
                    '  redis-server',
                    '  或: sudo systemctl start redis'
                ]
            }

    def start_redis_windows(self):
        """Windows下启动Redis"""
        # 常见Redis安装路径
        possible_paths = [
            r'C:\Redis\redis-server.exe',
            r'C:\Program Files\Redis\redis-server.exe',
            r'C:\tools\Redis\redis-server.exe',
        ]
        
        for redis_path in possible_paths:
            if os.path.exists(redis_path):
                self.stdout.write(self.style.SUCCESS(f'找到Redis: {redis_path}'))
                try:
                    # 在后台启动Redis
                    subprocess.Popen([redis_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    self.stdout.write(self.style.SUCCESS('Redis服务已启动'))
                    return True
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'启动Redis失败: {e}'))
                    return False
        
        return False

    def start_redis_unix(self):
        """Unix系统（Linux/Mac）下启动Redis"""
        try:
            # 尝试启动Redis
            process = subprocess.Popen(
                ['redis-server'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # 等待一下看是否启动成功
            time.sleep(1)
            if process.poll() is None:
                self.stdout.write(self.style.SUCCESS('Redis服务已启动（后台运行）'))
                return True
            else:
                # 进程已退出，可能启动失败
                stderr = process.stderr.read().decode('utf-8', errors='ignore')
                if 'Address already in use' in stderr:
                    self.stdout.write(self.style.SUCCESS('Redis已在运行'))
                    return True
                else:
                    self.stdout.write(self.style.ERROR(f'Redis启动失败: {stderr}'))
                    return False
        except FileNotFoundError:
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'启动Redis失败: {e}'))
            return False

    def handle(self, *args, **options):
        check_only = options['check_only']
        
        # 检查Redis是否已运行
        if self.check_redis_connection():
            self.stdout.write(self.style.SUCCESS('✓ Redis服务已在运行 (localhost:6379)'))
            return
        
        if check_only:
            self.stdout.write(self.style.WARNING('✗ Redis服务未运行'))
            self.stdout.write(self.style.WARNING('请运行: python manage.py start_redis'))
            return
        
        # 检查Redis是否已安装
        if not self.check_redis_installed():
            self.stdout.write(self.style.ERROR('✗ Redis未安装'))
            self.stdout.write(self.style.WARNING('\n' + '='*60))
            
            instructions = self.get_redis_install_instructions()
            self.stdout.write(self.style.WARNING(instructions['title'] + ':'))
            for step in instructions['steps']:
                self.stdout.write(self.style.WARNING('  ' + step))
            
            self.stdout.write(self.style.WARNING('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('\n提示: 如果不想安装Redis，可以使用SQLite作为broker:'))
            self.stdout.write(self.style.SUCCESS('  设置环境变量: export CELERY_BROKER_URL=sqla+sqlite:///celery_broker.db'))
            self.stdout.write(self.style.SUCCESS('  或直接使用默认配置（已使用SQLite）'))
            return
        
        # 尝试启动Redis
        self.stdout.write(self.style.SUCCESS('正在启动Redis服务...'))
        
        system = platform.system().lower()
        if system == 'windows':
            success = self.start_redis_windows()
        else:
            success = self.start_redis_unix()
        
        if success:
            # 等待Redis就绪
            self.stdout.write('等待Redis服务就绪...')
            for i in range(10):
                if self.check_redis_connection():
                    self.stdout.write(self.style.SUCCESS('\n✓ Redis已成功启动！'))
                    self.stdout.write(self.style.SUCCESS('现在可以启动Celery Worker: python manage.py start_celery_worker'))
                    return
                time.sleep(0.5)
            
            self.stdout.write(self.style.WARNING('\nRedis可能已启动，但连接检查超时'))
            self.stdout.write(self.style.WARNING('请手动检查Redis是否正常运行'))
        else:
            self.stdout.write(self.style.ERROR('\n✗ Redis启动失败'))
            self.stdout.write(self.style.WARNING('请手动启动Redis服务'))

