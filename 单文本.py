import pyquery
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pyquery import PyQuery as pq
import threading

save_folder = "诡秘之主"
if not os.path.exists(save_folder):
    os.mkdir(save_folder)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
}

# 创建一个线程锁，用于保护文件写入操作
file_lock = threading.Lock()

def get_novel(i, output_file):
    novel_content = ""
    try:
        # 构造章节URL
        chapter_url = f"https://8450c878381e76357b.751a01a17.icu/book/64813/{i}.html"
        print(f"正在爬取第{i}章: {chapter_url}")

        # 获取章节页面
        content_html = requests.get(chapter_url, headers=headers, timeout=10)
        doc = pyquery.PyQuery(content_html.text)

        # 提取章节标题
        raw_header = doc(".header .title").text()  # 修正选择器语法
        if raw_header and '）' in raw_header:
            header = raw_header.split('）', 1)[1]  # 只分割第一个
        else:
            header = raw_header or f"第{i}章"

        # 收集章节内容
        texts = []
        # 添加章节标题和分隔符
        texts.append(f"\n\n{'='*60}")
        texts.append(f"{header}")
        texts.append('='*60 + '\n')

        # 处理分页内容
        for j in range(1, 3):
            # 构造分页URL
            page_url = f"https://8450c878381e76357b.751a01a17.icu/book/64813/{i}_{j}.html"
            print(f"  正在爬取第{i}章第{j}页: {page_url}")

            try:
                page_html = requests.get(page_url, headers=headers, timeout=10)
                doc = pyquery.PyQuery(page_html.text)
                chapter_div = doc("#chaptercontent")

                # 移除无关内容
                chapter_div.find('p.noshow').remove()
                chapter_div.find('a[href*="3f3e6900e.cfd"]').remove()

                # 提取正文内容
                for child in pq(chapter_div).contents():
                    if isinstance(child, str):
                        stripped_text = child.strip()
                        if stripped_text and "请收藏" not in stripped_text:
                            texts.append(stripped_text)
                    elif pq(child).is_('br'):
                        continue

            except Exception as page_e:
                print(f"    处理第{i}章第{j}页时出错: {page_e}")
                continue

        novel_content = "\n".join(texts) + "\n"

        # 使用线程锁保护文件写入操作
        with file_lock:
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(novel_content)

        print(f"成功保存第{i}章: {header}")
        return True

    except Exception as e:
        print(f"获取第{i}章失败: {e}")
        return False

def main():
    total_chapters = 1430
    max_workers = 10
    # 创建统一输出文件
    output_file = os.path.join(save_folder, "诡秘之主.txt")
    # 初始化文件（写入小说名和标题）
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("诡秘之主\n")
        f.write("="*60 + "\n\n")

    print(f"开始爬取《诡秘之主》，共{total_chapters}章")
    print(f"保存到文件: {output_file}")

    success_count = 0


    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i in range(1, total_chapters + 1):
            future = executor.submit(get_novel, i, output_file)
            futures[future] = i

        for future in as_completed(futures):
            chapter_num = futures[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                if chapter_num % 50 == 0:
                    print(f"进度: {chapter_num}/{total_chapters}章")
            except Exception as e:
                print(f"章节{chapter_num}处理出错: {e}")

    print(f"\n 爬取完成!")
    print(f"成功保存 {success_count}/{total_chapters} 章到文件: {output_file}")

if __name__ == "__main__":
    main()
