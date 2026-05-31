from functools import wraps
from flask import abort
from flask_login import current_user
import openpyxl
from io import BytesIO

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def export_excel(columns, data, sheet_name='Sheet1', col_widths=None):
    """通用导出函数，columns为表头列表，data为二维列表，col_widths为列宽列表"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(columns)
    if col_widths:
        for i, width in enumerate(col_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    for row in data:
        ws.append(row)
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output