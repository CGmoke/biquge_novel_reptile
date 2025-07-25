import threading
import pyquery
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pyquery import PyQuery as pq
import json

novel_name= str(input("请输入小说名："))
save_folder =novel_name
if not os.path.exists(save_folder):
    os.mkdir(save_folder)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
}
search_url= f"https://m.bqgl.cc/user/search.html?q={novel_name}"
print(search_url)
file_lock = threading.Lock()
def search_novel_url(search_url):
    try:
        novel_html = requests.get(search_url, headers=headers)
        
        data = novel_html.json()
        print("=== 使用JSON解析 ===")
        if data:
            first_item = data[0]
            url_list = first_item.get('url_list', None)
            if url_list:
                clean_url = url_list.replace('\\/', '/')
                novel_url = "https://m.bqgl.cc" + clean_url
                print(f"小说名: {first_item.get('articlename', '')}")
                print(f"完整URL: {novel_url}")
                print("-" * 50)
                return novel_url
    except :
        print(f"JSON解析失败")
    return None

def search_chapters_url(search_url):
    try:

        chapters_url = search_novel_url(search_url)+"list.html"
        print(f"目录URL: {chapters_url}")
        return chapters_url
    except Exception as e:
        print(f"获取章节URL失败: {e}")
    return  None


def get_novel(chapters_url,i,file_path):
    novel = ""
    try:
        texts = []
        chapter_url = f"{chapters_url.rstrip('/list.html')}/{i}.html"
        print(f"正在爬取第{i}章{chapter_url}")
        content_html = requests.get(chapter_url, headers=headers)
        #print(chapter_url)
        doc = pyquery.PyQuery(content_html.text)
        raw_header = doc(".header .title").text()
        if raw_header and '）' in raw_header:
            header = raw_header.split('）', 1)[1]  # 只分割第一个
        else:
            header = raw_header or f"第{i}章"

        texts.append(f"{header}")
        for j in range(1,3):
            chapter_url = f"{chapters_url.rstrip('/list.html')}/{i}_{j}.html"
            content_html = requests.get(chapter_url, headers=headers)
            doc = pyquery.PyQuery(content_html.text)
            chapter_div = doc("#chaptercontent")
            chapter_div.find('p.noshow').remove()#删除无关内容
            chapter_div.find('a[href*="3f3e6900e.cfd"]').remove()
            for child in pq(chapter_div).contents():
                if isinstance(child, str):
                    stripped_text = child.strip()
                    if stripped_text and "请收藏"not in stripped_text:
                        texts.append(stripped_text)
                elif pq(child).is_('br'):
                    continue
            novel += "\n".join(texts)+"\n"
        with file_lock:
            with open(file_path, "a", encoding="utf-8")  as f:
                f.write(novel)
        print(f"成功保存{header}")
    except:
        print(f"获取第{i}章失败")
def main():
    chapters_url = search_chapters_url(search_url)
    if not chapters_url:
        print("未找到小说")
        return
    file_path = os.path.join(save_folder, f"{novel_name}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"{novel_name}\n")
    print(f"开始爬取《{novel_name}》，保存到: {file_path}")
    max_workers = 5
    total_chapters =int(input("请输入总章节数："))
    success_count = 0
    """#with ThreadPoolExecutor(max_workers= max_workers) as executor:
            futures = [executor.submit(get_novel,chapters_url,i,file_path) for i in range(1, total_chapters+1) ]
            for future in as_completed(futures):
                future.result()
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i in range(1, total_chapters + 1):
            future = executor.submit(get_novel, chapters_url, i, file_path)
            futures[future] = i

        for future in as_completed(futures):
            chapter_num = futures[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                print(f"进度: {chapter_num}/{total_chapters}")
            except Exception as e:
                print(f"章节{chapter_num}处理出错: {e}")

    print(f"\n 爬取完成!")
    print(f"成功保存 {success_count} 章到文件: {file_path}")
if __name__ == "__main__":
    main()
