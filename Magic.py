import requests
import multitasking
import os
headers = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36 Edg/89.0.774.77',
    'Accept': '*/*',
    'Referer': 'http://fundf10.eastmoney.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}


@multitasking.task
def download_file(fund_code: str, url: str, filename: str, file_type='.pdf'):
    '''
    根据文件名、文件直链等参数下载文件
    '''
    fund_code = str(fund_code)
    if not os.path.exists(fund_code):
        os.mkdir(fund_code)
    response = requests.get(url, headers=headers)
    path = f'{fund_code}/{filename}{file_type}'
    with open(path, 'wb') as f:
        f.write(response.content)
    if os.path.getsize(path) == 0:
        os.remove(path)
        return
    print(filename+file_type, '下载完毕')


def get_pdf_by_fund_code(fund_code: str):
    '''
    根据基金代码获取其全部 pdf 报告

    Parameters
    ----------
    fund_code :6 位基金代码

    '''

    params = (
        ('fundcode', fund_code),
        ('pageIndex', '1'),
        ('pageSize', '20000'),
        ('type', '3'),
    )

    response = requests.get(
        'http://api.fund.eastmoney.com/f10/JJGG', headers=headers, params=params)

    base_link = 'http://pdf.dfcfw.com/pdf/H2_{}_1.pdf'
    for item in response.json()['Data']:
        title = item['TITLE']
        download_url = base_link.format(item['ID'])
        download_file(fund_code, download_url, title)
    multitasking.wait_for_tasks()
    print(f'{fund_code} 的 pdf 全部下载完毕并存储在文件夹 {fund_code} 里面')


if "__main__" == __name__:
    # 基金代码列表
    fund_codes = ['110011', '161725']
    for fund_code in fund_codes:
        get_pdf_by_fund_code(fund_code)