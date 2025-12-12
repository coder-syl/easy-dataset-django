# 1. 前置条件

## 安装PostgreSQL

已经安装 PostgreSQL，没有安装的可以去以下官网下载安装包进行安装：

[EDB: Open-Source, Enterprise Postgres Database Management](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads "EDB: Open-Source, Enterprise Postgres Database Management")

选择合适的版本，点击按钮进行下载

![](https://i-blog.csdnimg.cn/direct/925b3f43851b4e618e374f1f759a40b8.png)

下载完成后，双击安装即可。如果遇到安装路径选择，可以使用默认安装在C盘，或者自定义路径，这块会影响到后面的安装扩展，我这里安装的目录是 

```
D:/Postgressql
```



## 安装Microsoft Visual Studio

1. 勾选 **“使用 C++ 的桌面开发”**（Desktop development with C++）。
2. 确保如下子组件已安装：
   - Windows 10 或 11 SDK（比如 10.0.xxxxx）
   - MSVC v14.x C++ 编译工具集

# 2. 环境变量设置PGroot

设置在环境变量下方中。

```
PGROOT = D:/Postgressql
```

# 3. 环境变量设置nmake

![image-20250522083804863](C:\Users\18523\AppData\Roaming\Typora\typora-user-images\image-20250522083804863.png)

把下面的路径放到环境变量的下方的path中：

```
C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.43.34808\bin\Hostx64\x86
```

# 4. 下载vector并解压

[https://pgxn.org/dist/vector/](https://pgxn.org/dist/vector/)

# 5.  管理员权限打开cmd命令行

![image-20250522084450926](C:\Users\18523\AppData\Roaming\Typora\typora-user-images\image-20250522084450926.png)

# 6. 激活visual studio环境

在上面打开的cmd中执行：

```
call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64\vcvars64.bat"
```

![image-20250522084608491](C:\Users\18523\AppData\Roaming\Typora\typora-user-images\image-20250522084608491.png)



# 6. nmake

进入vector目录中

依次执行下面两个命令

```
nmake /F Makefile.win

nmake /F Makefile.win install
```



![image-20250522084910889](C:\Users\18523\AppData\Roaming\Typora\typora-user-images\image-20250522084910889.png)

![image-20250522085017186](C:\Users\18523\AppData\Roaming\Typora\typora-user-images\image-20250522085017186.png)

# 7. 登录数据库增加扩展

## 登录

这里可以使用其他第三方工具，例如navicate,dbeaver

```
psql -U postgres
```

并输入密码

识别不了的话，记得将安装目录/bin 加环境变量

## 下面进入需要安装vector的库：

![](https://i-blog.csdnimg.cn/direct/2858e7794773415587c1899b1c745285.png)

```
\c maxkb
```

## 创建扩展：

![](https://i-blog.csdnimg.cn/direct/f60905487644458abb6c8bca8f1a1081.png)

```
 CREATE EXTENSION IF NOT EXISTS vector;
```

## 确认扩展：

```
\dx vector
```

![](https://i-blog.csdnimg.cn/direct/0b5570bbfabe410586861f4bfa8ad16a.png)

## 退出命令行 exit