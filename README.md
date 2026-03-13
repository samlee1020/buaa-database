# 使用说明

这是samlee1020的北航大三上数据库作业，一个简单的门诊管理系统。
前端由ai基于我写的命令行程序对应生成，后端由flask+pymysql实现。

## 代码文件说明

- main.py: 命令行程序入口（可能功能略少于web端）
- app.py: web端程序入口(包含web端前端代码)
- setup.py: 数据库建表相关函数
- frontend: 命令行程序前端代码
- templates: web端模板文件
- entity: 数据库七个实体的相关函数

## 云服务器设置：

位于config.py文件中，统一管理数据库连接信息。

由于课程已经结束，故其填写的数据库已经失效。

## web的本地运行链接

<http://127.0.0.1:8080>

## 环境要求

- python 3
- flask
- pymysql

## web端运行命令：

```
python app.py
```

## 命令行运行命令：

```
python main.py
```

