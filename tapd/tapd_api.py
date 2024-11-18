import requests
import json
import logging
import time
from conf.common import log_error, log_success, NOT_TO_EXCEL_FILED, TAPD_HEADERS


class TapdAPI(object):

    def __init__(self, wksp_id):
        self.workspace_id = wksp_id
        self.limit = 200
        self.headers = self.get_headers()
        pass

    def get_headers(self):
        return TAPD_HEADERS

    def get_bugs_count(self):
        url = f"https://api.tapd.cn/bugs/count?workspace_id={self.workspace_id}"
        return requests.get(url, headers=self.headers).json()["data"]["count"]

    def get_bugs_fields(self, params=None):
        url = f"https://api.tapd.cn/bugs/get_fields_info?workspace_id={self.workspace_id}"
        ret = requests.get(url, headers=self.headers, params=params)
        if ret.status_code != 200:
            raise Exception(f"get_bugs_fields API fail; code:{ret.status_code}  resutl: {ret.text}")
        logging.debug(ret.text)
        return ret.json()

    def get_bugs(self, params):
        url = f"https://api.tapd.cn/bugs?workspace_id={self.workspace_id}"
        ret = requests.get(url, headers=self.headers, params=params)
        if ret.status_code != 200:
            if ret.status_code == 429 and "Too Many Requests" in ret.text:
                time.sleep(3)
            else:
                raise Exception(f"get bugs API fail; code:{ret.status_code}  resutl: {ret.text}")
        logging.debug(ret.text)
        return ret.json()

    def create_bug(self, **kwargs):
        """新建缺陷: https://www.tapd.cn/help/show#1120003271001000119"""
        url = "https://api.tapd.cn/bugs"
        data = {
                "workspace_id": self.workspace_id
                }
        if kwargs:
            data.update(kwargs)

        ret = requests.post(url, data=data, headers=self.headers)
        if ret.status_code != 200:
            raise Exception(f"get bugs fail error:{ret.text}")
        logging.debug(ret.text)
        response = ret.json()
        return response

    def get_stories_count(self):
        url = f"https://api.tapd.cn/stories/count?workspace_id={self.workspace_id}"
        return requests.get(url, headers=self.headers).json()["data"]["count"]

    def get_stories_fields(self, params=None):
        url = f"https://api.tapd.cn/stories/get_fields_info?workspace_id={self.workspace_id}"
        ret = requests.get(url, headers=self.headers, params=params)
        if ret.status_code != 200:
            raise Exception(f"get_stories_fields API fail; code:{ret.status_code}  resutl: {ret.text}")
        logging.debug(ret.text)
        return ret.json()

    def get_stories(self, params):
        url = f"https://api.tapd.cn/stories?workspace_id={self.workspace_id}"
        ret = requests.get(url, headers=self.headers, params=params)
        if ret.status_code != 200:
            if ret.status_code == 429 and "Too Many Requests" in ret.text:
                time.sleep(3)
            else:
                raise Exception(f"get stories API fail; code:{ret.status_code}  resutl: {ret.text}")
        logging.debug(ret.text)
        return ret.json()

    def create_stories(self, **kwargs):
        """新建需求: https://www.tapd.cn/help/show#1120003271001000057"""
        url = "https://api.tapd.cn/stories"
        data = {
                "workspace_id": self.workspace_id
                }
        if kwargs:
            data.update(kwargs)
        logging.debug(data)
        ret = requests.post(url, data=data, headers=self.headers)
        if ret.status_code != 200:
            raise Exception(f"create stories fail error:{ret.text}")
        logging.debug(ret.text)
        response = ret.json()
        return response

    def get_user_email(self):
        url = f"https://api.tapd.cn/workspaces/users?workspace_id={self.workspace_id}&fields=user,email"
        ret = requests.get(url, headers=self.headers)
        if ret.status_code != 200:
            raise Exception(f"get fields fail error:{ret.text}")
        logging.debug(ret.text)
        return ret.json()


class TapdHandle(TapdAPI):
    def __init__(self, wksp_id, tapd_type=None):
        self.tapd_type = tapd_type
        super().__init__(wksp_id)
        self.email_user_map = self.get_email_user_map()
        self.fsapi = None

    def get_fsapi(self, doc_id, sheet_id, depm_id):
        from fs.fs_api import FSExcelHandle
        self.fsapi = FSExcelHandle(doc_id=doc_id, sheet_id=sheet_id, depm_id=depm_id)

    def get_bugs_all(self, count=None):
        bugs_data = dict()
        count = count if count else self.get_bugs_count()
        for page in range(count//self.limit + 1):
            data = self.get_bugs(params={"page": page + 1, "limit": self.limit})
            if "data" in data and data["data"]:
                for bug in data["data"]:
                    bugid = bug["Bug"]["id"]
                    bugs_data[bugid] = bug["Bug"]
            else:
                logging.error(f"get_bugs data: {data}")
        logging.info(f"bugs count:{count}, get_count:{len(bugs_data.keys())}")
        return bugs_data

    def get_stories_all(self, count=None):
        stories_data = dict()
        count = count if count else self.get_stories_count()
        for page in range(count//self.limit + 1):
            data = self.get_stories(params={"page": page + 1, "limit": self.limit})
            if "data" in data and data["data"]:
                for item in data["data"]:
                    storyid = item["Story"]["id"]
                    stories_data[storyid] = item["Story"]
            else:
                logging.error(f"stories data: {data}")
        logging.info(f"stories count:{count}, get_count:{len(stories_data.keys())}")
        return stories_data

    def get_all_data(self, count=None):
        if self.tapd_type == "bug":
            return self.get_bugs_all(count)
        elif self.tapd_type == "stories":
            return self.get_stories_all(count)
        return

    def get_fileds(self):
        tapd_fileds = dict()
        if self.tapd_type == "bug":
            return self.get_bugs_fields()["data"]
        elif self.tapd_type == "stories":
            return self.get_stories_fields()["data"]
        return tapd_fileds

    def get_id_link(self, tapd_id):
        """获取tapd单链接"""
        if self.tapd_type == "stories":
            url = f"https://www.tapd.cn/{self.workspace_id}/prong/stories/view/{tapd_id}"
        elif self.tapd_type == "bug":
            url = f'https://www.tapd.cn/{self.workspace_id}/bugtrace/bugs/view/{tapd_id}'
        else:
            raise Exception(f"TAPD type error, tapd_type:{self.tapd_type}")
        return url

    def get_email_user_map(self):
        """获取tapd通讯录；邮箱作为key，用户名作为val"""
        user_email = dict()
        data = self.get_user_email()
        for i in data["data"]:
            user = i["UserWorkspace"]["user"]
            email = i["UserWorkspace"]["email"]
            if user not in user_email:
                user_email[user] = [email]
            else:
                user_email[user].append(email)
        email_user_map = {i["UserWorkspace"]["user"]: i["UserWorkspace"]["email"] for i in data["data"]}
        logging.info(f"email_user_map: {email_user_map}")
        return email_user_map

    def user_convert(self, user_str):
        """将用户转换飞书用户数据结构"""
        # 通过邮箱进行匹配飞书对应的人员
        error_list, data_list = list(), list()
        for user in user_str.split(";"):
            if not user:
                continue
            user = user.strip()
            if user in self.email_user_map:
                email = self.email_user_map.get(user)
                if email in self.fsapi.email_unionid_all:
                    union_id = self.fsapi.email_unionid_all.get(email)
                    data_list.append({
                        "type": "mention",
                        "text": union_id,
                        "textType": "unionId",
                        "notify": False,
                        "grantReadPermission": True
                    })
                else:
                    error_list.append(f"飞书没有匹配到该用户或者应用没有权限:{user}TAPD的邮箱:{email}")
            else:
                error_list.append(f"用户:{user}没有在TAPD找到")
        logging.info(f"user_str:{user_str};  error_list: {error_list}; data_list:{data_list}")
        return error_list, data_list

    def convert_fs_filed_type(self, value):
        """转换飞书表格字段类型"""
        for key, val in value.items():
            if "ID" == key:
                value[key] = [{'link': self.get_id_link(val), 'text': val, 'type': 'url'}]
            if key in ["创建人", "处理人"]:
                error_list, data_list = self.user_convert(val)
                if error_list:
                    value["日志"] += log_error(";".join(error_list))
                if data_list:
                    value[key] = data_list
        return value

    def sync_to_fs(self, doc_id=None, sheet_id=None, depm_id=None):
        self.get_fsapi(doc_id, sheet_id, depm_id)
        # 读取当前表数据
        all_sheet_values = self.fsapi.get_sheet_map_data()
        # 获取所有ID
        fs_tapdid_all = [i["ID"] for i in all_sheet_values]
        # 获取第一行字段
        fs_values = self.fsapi.get_titel_list()
        fs_title_list = self.fsapi.fs_to_tapd_filds(fs_values)
        tapd_files_all = self.get_fileds()

        all_data = self.get_all_data()
        logging.info(f"=========fs_tapdid_all: {fs_tapdid_all} ")
        insert_list = list()
        tapd_insert_list = list()

        # 获取所有bugs，循环读取表格数据
        for data in all_sheet_values:
            tapd_id = data["ID"]
            if not tapd_id: continue
            # 如有匹配到bugs的数据，则以tapd数据为准将表格数据更新掉
            if tapd_id in all_data:
                tapd_data = all_data[tapd_id]
                # 将TAPD的数据转为飞书数据格式
                tapd_row = dict()
                for key, val in tapd_data.items():
                    if not val: continue

                    if key in tapd_files_all:
                        # 如果是多选，则找到value对应的label
                        if tapd_files_all[key]["html_type"] in ["checkbox", "select"]:
                            options = tapd_files_all[key]["options"]
                            if isinstance(options, list):
                                for item in options:
                                    if val == item["value"]:
                                        val = item["label"]
                            else:
                                for k, v in options.items():
                                    if k == val:
                                        val = v

                        label = tapd_files_all[key]["label"]
                        tapd_row[label] = val

                    # 不需要被TADP数据覆盖的字段
                    if key in NOT_TO_EXCEL_FILED:
                        fs_feled = NOT_TO_EXCEL_FILED[key]
                        tapd_row[fs_feled] = data[fs_feled]

                    tapd_row["日志"] = log_success()
                insert_list.append(tapd_row)
                tapd_insert_list.append(tapd_row)
            else:
                insert_list.append(data)

        logging.info(f"======insert_list : {insert_list}")
        logging.info(f"======tapd_insert_list: {tapd_insert_list}")

        # 开始批量插入
        insert_all_list = []
        for item in insert_list:
            # 转换飞书表格字段类型
            self.convert_fs_filed_type(item)
            # 将TAPD字段顺序处理为对应飞书表格的字段的顺序 并更新到表格中
            values = []
            for filed in fs_title_list:
                val = item[filed] if filed in item else ""
                values.append(val)
            insert_all_list.append(values)

        insert_all_list.insert(0, fs_title_list)
        logging.info(f"===insert_all_list : {insert_all_list}")
        self.fsapi.update_excel(values=insert_all_list)


if __name__ == '__main__':
    TAPD_API = TapdHandle(wksp_id="xxx", tapd_type="bug")
    a = TAPD_API.get_bugs_count()
    logging.info(a)




