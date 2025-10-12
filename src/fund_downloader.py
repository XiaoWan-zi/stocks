"""基金 PDF 报告下载工具。

基于东方财富接口批量下载基金报告。
"""

import os
try:
    import requests
    import multitasking
    _HAS_DEPS = True
except ImportError:
    requests = None
    multitasking = None
    _HAS_DEPS = False

HEADERS = {
    'Connection': 'keep-alive',
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/89.0.4389.128 Safari/537.36 Edg/89.0.774.77'),
    'Accept': '*/*',
    'Referer': 'http://fundf10.eastmoney.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}


@multitasking.task
def download_file(code: str, url: str, filename: str, file_type: str = '.pdf') -> None:
    """根据文件名、文件直链等参数下载文件。"""
    if not _HAS_DEPS:
        print("缺少依赖 requests/multitasking，跳过下载")
        return
    code = str(code)
    if not os.path.exists(code):
        os.mkdir(code)
    response = requests.get(url, headers=HEADERS, timeout=30)
    path = f'{code}/{filename}{file_type}'
    with open(path, 'wb') as f:
        f.write(response.content)
    if os.path.getsize(path) == 0:
        os.remove(path)
        return
    print(filename + file_type, '下载完毕')


def get_pdf_by_fund_code(code: str) -> None:
    """根据基金代码获取其全部 PDF 报告。

    Parameters
    ----------
    code : str
        6 位基金代码
    """
    if not _HAS_DEPS:
        print("缺少依赖 requests/multitasking，跳过下载")
        return

    params = (
        ('fundcode', code),
        ('pageIndex', '1'),
        ('pageSize', '20000'),
        ('type', '3'),
    )

    response = requests.get(
        'http://api.fund.eastmoney.com/f10/JJGG', headers=HEADERS, params=params, timeout=30)

    base_link = 'http://pdf.dfcfw.com/pdf/H2_{}_1.pdf'
    for item in response.json()['Data']:
        title = item['TITLE']
        download_url = base_link.format(item['ID'])
        download_file(code, download_url, title)
    multitasking.wait_for_tasks()
    print(f'{code} 的 pdf 全部下载完毕并存储在文件夹 {code} 里面')


def main() -> None:
    """演示下载指定基金代码的 PDF 报告。"""
    fund_codes = ['110011', '161725']
    for code in fund_codes:
        get_pdf_by_fund_code(code)


if "__main__" == __name__:
    main()
