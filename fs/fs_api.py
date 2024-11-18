import requests
import json
import datetime
import logging
import traceback
from conf.common import log_error, log_success, APP_ID, APP_SECRET


class FSAPI(object):

    def __init__(self, doc_id, sheet_id):
        self.doc_id = doc_id
        self.sheet_id = sheet_id
        self.headers = self.get_headers()

    def get_headers(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {"app_id": APP_ID, "app_secret": APP_SECRET}
        ret = requests.post(url, data=json.dumps(data), headers=headers).json()
        headers = {"Authorization": "Bearer " + ret["tenant_access_token"],
                   "Content-Type": "application/json; charset=utf-8"}
        return headers

    def get_sheet_info(self, range=None):
        """获取飞书表格指定sheet和范围的数据"""
        range = "" if range is None else range
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.doc_id}/values/{self.sheet_id}{range}"
        return requests.get(url, headers=self.headers).json()

    def update_excel(self, values, range=None):
        """向单个范围写入数据，若范围内有数据，将被更新覆盖, 单次写入不超过5000行，100列，每个格子不超过5万字符"""
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.doc_id}/values"
        data = {
            "valueRange": {
                "range": f"{self.sheet_id}!{range}" if range else self.sheet_id,
                "values": values
            }
        }
        logging.debug(data)
        ret = requests.put(url, data=json.dumps(data), headers=self.headers)
        logging.debug(ret.text)
        return ret

    def append_excel(self, values=None):
        """向单个范围写入数据，若范围内有数据，将被更新覆盖, 单次写入不超过5000行，100列，每个格子不超过5万字符"""
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.doc_id}/values_append"
        data = {
            "valueRange": {
                "range": self.sheet_id,
                "values": values
            }
        }
        ret = requests.post(url, data=json.dumps(data), headers=self.headers)
        logging.debug(ret.text)
        return ret

    def get_sclect_info(self, range=None):
        """查询下拉列表"""
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.doc_id}/dataValidation?&range={self.sheet_id}{range}"
        ret = requests.get(url, headers=self.headers)
        logging.debug(ret.text)
        return ret

    def set_sclect_info(self, range=None):
        """设置下拉列表"""
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.doc_id}/dataValidation"
        data = {
            "range":f"{self.sheet_id}!B2:B100",
            "dataValidationType":"list",
            "dataValidation":{
                "conditionValues":["2", "89", "3","2"],
                "options":{
                    "multipleValues": True,
                    "highlightValidData":True
                }
            }
        }
        logging.debug(data)
        ret = requests.post(url, data=json.dumps(data), headers=self.headers)
        logging.debug(ret.text)
        return ret

    def department_children(self, department_id):
        url = f"https://open.feishu.cn/open-apis/contact/v3/departments/{department_id}/children"
        logging.debug(url)
        ret = requests.get(url, headers=self.headers)
        logging.debug(ret.text)
        return ret.json()

    def find_by_department(self, **kwargs):
        url = f"https://open.feishu.cn/open-apis/contact/v3/users/find_by_department"
        logging.debug(url)
        params = {
            "department_id": "",
            "department_id_type": "department_id",
            "page_size": 50,
            "user_id_type": "union_id"
        }
        if kwargs:
            params.update(kwargs)
        ret = requests.get(url, headers=self.headers, params=params)
        logging.debug(ret.text)
        return ret.json()


class FSExcelHandle(FSAPI):

    def __init__(self, doc_id, sheet_id, tapd_type=None, depm_id=None):
        self.tapd_type = tapd_type
        self.depm_id = depm_id
        super().__init__(doc_id, sheet_id)
        self.email_unionid_all = self.get_email_unionid_all()

    def get_depm_child_id(self, depmt_id, depmt_list):
        """ 递归获取所有子部门"""
        ret = self.department_children(depmt_id)
        if "data" in ret and "items" in ret["data"] and ret["data"]["items"]:
            for item in ret["data"]["items"]:
                depmt_list.append(item["department_id"])
                self.get_depm_child_id(item["department_id"], depmt_list)
        return

    def get_email_unionid_all(self):
        """获取所有的子部门ID，去查询部门直属用户列表"""
        all_depm_child_id, email_user = list(), dict()
        self.get_depm_child_id(self.depm_id, all_depm_child_id)
        logging.info(f"all_depm_child_id: {all_depm_child_id}")
        for depm_id in all_depm_child_id:
            ret = self.find_by_department(department_id=depm_id)
            if "data" in ret and "items" in ret["data"] and ret["data"]["items"]:
                for item in ret["data"]["items"]:
                    enterprise_email = item["enterprise_email"]
                    union_id = item["union_id"]
                    email_user[enterprise_email] = union_id
        logging.info(f"FS email_user: {email_user}")
        return email_user

    def fs_date(self, date_num):
        """飞书时间戳转换"""
        if isinstance(date_num, int) or isinstance(date_num, float):
            return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=date_num)).strftime("%Y-%m-%d %H:%M")
        return date_num

    def get_titel_list(self):
        """获取52列的第一行字段"""
        sheet_info = self.get_sheet_info(range="!A1:ZZ1")
        titel_list = sheet_info["data"]["valueRange"]["values"][0]
        end_index = -1
        for vla in titel_list[::-1]:
            end_index += 1
            if vla:
                break
        return titel_list[:(len(titel_list) - end_index)]

    def fs_to_tapd_filds(self, values):
        new_values = []
        for item in values:
            name = None
            if isinstance(item, list):
                name_list = []
                for info in item:
                    if "en_name" in info and "name" in info:
                        name_list.append(info["name"])
                    elif "text" in info and "link" in info:
                        name = info["text"]
                        break
                if name_list:
                    name = ";".join(name_list)
            elif isinstance(item, dict):
                name = item["name"]
            elif isinstance(item, (str, bool, int, float)) or not item:
                name = item
            else:
                raise Exception(f"invalid filed item: {item}")
            new_values.append(name)
        return new_values

    def num_to_abc(self, num):
        """数字转字母"""
        row_26 = [chr(i).upper() for i in range(97, 123)]
        return row_26[num]

    def convert_fs_filed(self, map_data):
        """对飞书表格读取的值需要额外处理"""
        time_convert_filed = ["预计开始", "预计结束"]
        for item in time_convert_filed:
            if item in map_data:
                map_data[item] = self.fs_date(map_data[item])
        return

    def get_sheet_map_data(self):
        """获取飞书表格所有数据，并已标题为key进行拼接map"""
        sheet_info = self.get_sheet_info()
        values = sheet_info["data"]["valueRange"]["values"]
        title_list = [i.strip() for i in values[0]]
        map_list = list()
        for i, v in enumerate(values):
            if i == 0:
                continue
            map_data = dict(zip(title_list, self.fs_to_tapd_filds(v)))
            self.convert_fs_filed(map_data)
            map_list.append(map_data)
        return map_list

    def sync_tapd(self, wksp_id):
        from tapd.tapd_api import TapdHandle
        title_list = self.get_titel_list()
        # 获取飞书表格所有数据，并已标题为key进行拼接map
        map_list = self.get_sheet_map_data()

        # 查询TAPD字段列表
        tapd_fileds_map = dict()
        TAPD_API = TapdHandle(wksp_id=wksp_id, tapd_type=self.tapd_type)
        tapd_fileds = TAPD_API.get_fileds()
        for item in TAPD_API.get_fileds().values():
            if item["label"] in title_list:
                tapd_fileds_map[item["label"]] = item["name"]

        # 循环创建Tapd单
        for index, fs_item in enumerate(map_list):
            error, fs_id, create_data = None, None, dict()
            try:
                if fs_item["ID"]:
                    # 如果此条数据创建，则不更新《详细描述》字段
                    fs_item.pop("详细描述")
                logging.info(f"fs_item:{fs_item}")
                # 只将匹配需要创建TAPD单的字段

                for key, val in fs_item.items():
                    if key not in tapd_fileds_map:
                        continue
                    # 如果是多选，则找到value对应的label
                    filed = tapd_fileds_map[key]
                    if filed in tapd_fileds and tapd_fileds[filed]["html_type"] in ["checkbox", "select"]:
                        options = tapd_fileds[filed]["options"]
                        if isinstance(options, list):
                            for item in options:
                                if val == item["label"]:
                                    create_data[filed] = item["value"]
                        else:
                            for k, v in options.items():
                                if v == val:
                                    create_data[filed] = k
                    else:
                        create_data[filed] = val

                logging.info(f"====create_data:{create_data}")
                if self.tapd_type == "bug":
                    data_id = TAPD_API.create_bug(**create_data)["data"]["Bug"]["id"]
                else:
                    data_id = TAPD_API.create_stories(**create_data)["data"]["Story"]["id"]

                fs_id = {
                    'cellPosition': None,
                    'link': TAPD_API.get_id_link(data_id),
                    'text': data_id,
                    'type': 'url'
                }

            except Exception as e:
                traceback.print_exc()
                error = log_error(e)
            finally:
                row = 2 + index
                if error:
                    table_id_index = self.num_to_abc(title_list.index("日志"))
                    self.update_excel(values=[[error]], range=f"{table_id_index}{row}:{table_id_index}{row}")
                else:
                    table_id_index = self.num_to_abc(title_list.index("日志"))
                    msg = log_success()
                    self.update_excel(values=[[msg]], range=f"{table_id_index}{row}:{table_id_index}{row}")
                if not fs_item["ID"]:
                    table_id_index = self.num_to_abc(title_list.index("ID"))
                    self.update_excel(values=[[fs_id]], range=f"{table_id_index}{row}:{table_id_index}{row}")


if __name__ == '__main__':
    OBJ = FSExcelHandle(doc_id="xx", sheet_id="xxx")
    OBJ.sync_tapd(wksp_id="xxx")
