# iron

车间综合信息管理平台，基于 Flask 开发。

## 功能角色

- **普通员工 (worker)**：加班/请假填报
- **班组长 (group_leader)**：班组批量加班/请假
- **作业长 (leader)**：审批、代报、奖金分配
- **管理员 (admin)**：账号与全量数据管理

## 环境要求

- Python 3.10+

## 安装与运行

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

set FLASK_APP=app:create_app
flask db upgrade
python init_db.py

python app.py
```

访问 http://127.0.0.1:5000

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| gl01 | 123456 | 班组长 |
| 000003 | 123456 | 作业长 |
| 000001 / 000002 | 123456 | 普通员工 |

管理员重置密码后默认为 `123456`。
