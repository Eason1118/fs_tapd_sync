from tapd.tapd_api import TapdHandle
from fs.fs_api import FSExcelHandle
from conf.common import ACT_DEPM_ID
import logging
log_format = '%(asctime)s|%(levelname)s|%(message)s'
logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)


def get_docid_sheetid(doc_url):
    """根据url提取文档ID和表ID"""
    doc_id = doc_url.split("?")[0].split("/")[-1]
    sheet_id = doc_url.split("?")[-1].split("=")[-1]
    return doc_id, sheet_id


if __name__ == '__main__':
    import sys
    wksp_id = sys.argv[1]
    doc_id, sheet_id = get_docid_sheetid(sys.argv[2])
    tapd_type = sys.argv[3]
    sync_dest = sys.argv[4]

    if tapd_type not in ["bug", "stories"]:
        raise Exception(f"tapd_type:{tapd_type} not in (bug, stories)")

    if sync_dest == "tapd":
        Fsobj = FSExcelHandle(doc_id=doc_id, sheet_id=sheet_id, tapd_type=tapd_type)
        Fsobj.sync_tapd(wksp_id=wksp_id)

    elif sync_dest == "fs":
        TAPD_API = TapdHandle(wksp_id=wksp_id, tapd_type=tapd_type)
        TAPD_API.sync_to_fs(doc_id=doc_id, sheet_id=sheet_id, depm_id=ACT_DEPM_ID)
    else:
        raise Exception(f"sync_dest:{sync_dest} not in (tapd, fs)")