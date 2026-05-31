"""批量生成测试用户并写入数据库。"""
import random
import string

from app import create_app
from models import db, User

DEPARTMENTS = ['2030成品', '装焊区', '冲压区', '涂装区', '总装区']
GROUPS = [f'{c}班' for c in 'ABCDEFGHIJ']
PASSWORD = '123456'


def existing_usernames():
    return {u.username for u in User.query.all()}


def main():
    app = create_app()
    with app.app_context():
        taken = existing_usernames()

        def unique_username(prefix, length=6):
            chars = string.ascii_lowercase + string.digits
            while True:
                suffix = ''.join(random.choices(chars, k=length))
                username = f'{prefix}{suffix}'
                if username not in taken:
                    taken.add(username)
                    return username

        def add_users(role, count, prefix, name_tpl, department=None, group_list=None):
            created = []
            for i in range(1, count + 1):
                username = unique_username(prefix)
                if role == 'group_leader' and group_list:
                    grp = group_list[i - 1]
                    dept = department or random.choice(DEPARTMENTS)
                elif role == 'leader':
                    grp = None
                    dept = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
                else:
                    grp = random.choice(GROUPS)
                    dept = random.choice(DEPARTMENTS)

                user = User(
                    username=username,
                    name=name_tpl.format(i=i),
                    role=role,
                    department=dept,
                    group=grp,
                    enabled=True,
                )
                user.set_password(PASSWORD)
                db.session.add(user)
                created.append((username, user.name, dept, grp or ''))
            return created

        workers = add_users('worker', 100, 'wk', '员工{i:03d}')
        group_leaders = add_users(
            'group_leader', 10, 'gl', '班组长{i:02d}',
            department='装焊区', group_list=GROUPS,
        )
        leaders = add_users('leader', 3, 'ld', '作业长{i}')

        db.session.commit()

        print(f'已创建 {len(workers)} 名普通员工')
        print(f'已创建 {len(group_leaders)} 名班组长')
        print(f'已创建 {len(leaders)} 名作业长')
        print(f'初始密码均为: {PASSWORD}')
        print()
        print('--- 班组长 ---')
        for row in group_leaders:
            print(f'{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}')
        print('--- 作业长 ---')
        for row in leaders:
            print(f'{row[0]}\t{row[1]}\t{row[2]}')
        print('--- 普通员工（前10条示例）---')
        for row in workers[:10]:
            print(f'{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}')
        print(f'... 共 {len(workers)} 条，完整列表见 seed_users_output.txt')

        out_path = 'seed_users_output.txt'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f'初始密码: {PASSWORD}\n\n')
            f.write('[班组长 x10]\n')
            for row in group_leaders:
                f.write(f'{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\n')
            f.write('\n[作业长 x3]\n')
            for row in leaders:
                f.write(f'{row[0]}\t{row[1]}\t{row[2]}\n')
            f.write('\n[普通员工 x100]\n')
            for row in workers:
                f.write(f'{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\n')
        print(f'完整账号列表已写入 {out_path}')


if __name__ == '__main__':
    main()
