import pyquery
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pyquery import PyQuery as pq


save_folder = "诡秘之主"
if not os.path.exists(save_folder):
    os.mkdir(save_folder)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
}
def getnovel(i):

    novel = ""
    chapter_url = f"https://8450c878381e76357b.751a01a17.icu/book/64813/{i}.html"
    try:
        content_html = requests.get(chapter_url, headers=headers)
        doc = pyquery.PyQuery(content_html.text)
        raw_header = doc(".header")(".title").text()
        if raw_header and '）' in raw_header:
            header = raw_header.split('）', 1)[1]  # 只分割第一个
        else:
            header = raw_header or f"第{i}章"

        for j in range(1,3):
            chapter_url = f"https://8450c878381e76357b.751a01a17.icu/book/64813/{i}_{j}.html"
            content_html = requests.get(chapter_url,headers=headers)
            doc = pyquery.PyQuery(content_html.text)
            chapter_div = doc("#chaptercontent")
            chapter_div.find('p.noshow').remove()
            chapter_div.find('a[href*="3f3e6900e.cfd"]').remove()
            texts = []
            for child in pq(chapter_div).contents():
                if isinstance(child, str):
                    stripped_text = child.strip()
                    if stripped_text and "请收藏"not in stripped_text:
                        texts.append(stripped_text)
                elif pq(child).is_('br'):
                    continue
            novel += "\n".join(texts) + "\n"
        file_path = os.path.join(save_folder, f"{header}.txt")
        with open(file_path, "w", encoding="utf-8")  as f:
            f.write(novel)
        print(f"成功保存{header}章")
    except:
        print(f"获取第{i}章失败")
def main():
    total_chapters = 1430
    max_workers = 10
    with ThreadPoolExecutor(max_workers= max_workers) as executor:
        futures = [executor.submit(getnovel,i) for i in range(1, total_chapters+1) ]
        for future in as_completed(futures):
            future.result()
if __name__ == "__main__":
    main()