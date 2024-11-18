import datetime

# 不需要同步飞书表格的字段 : {"description": "详细描述"}
NOT_TO_EXCEL_FILED = {}

# TAPD 固定headers
TAPD_HEADERS = {
        'Authorization': 'Basic xxxxxxxxxxxxxxxxxxxxx',
        'Cookie': 'tapdsession=xxxxxxxxxxxxxxxxxxxx'
    }

# 飞书
APP_ID = "cli_xxxxxxxxxxxxxx"
APP_SECRET = "xxxxxxxxxxxxxxxxxxxxxx"
# ACT部门ID
ACT_DEPM_ID = "od-xxxxxxxxxxxx"

STORY = "stories"
BUG = "bug"


def datetime_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_success():
    return f"最新同步时间: {datetime_now()}"


def log_error(error):
    return f"ERROR: {error} 时间:{datetime_now()}"



