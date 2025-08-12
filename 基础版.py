
import time
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
import re
import os


novel_name = input("请输入小说名称：")
#创建文件夹
save_folder =novel_name
if not os.path.exists(save_folder):
    os.mkdir(save_folder)

#获取小说url
web = Chrome()
bqg_url = 'https://m.bqgl.cc/s?q=' + novel_name
time.sleep(0.5)
web.get(bqg_url)
find_novel_href = web.find_element(By.XPATH, '/html/body/div[3]/div/div/div[1]/div/a')
novel_href = find_novel_href.get_attribute('href')
novel_url = novel_href

#获取章节url
time.sleep(0.5)
web.get(novel_url)
find_chapter_list_href = web.find_element(By.XPATH, '/html/body/div[4]/div[5]/a')
chapter_list_url = find_chapter_list_href.get_attribute('href')
print(chapter_list_url)
time.sleep(0.5)


#获取章节数
web.get(chapter_list_url)
chapters_number = web.find_element(By.XPATH, '/html/body/div[2]/span[@class="title"]')
match = re.search(r'\((\d+)章\)', chapters_number.text)
#运用正则匹配章节数
if match:
    chapter_count = match.group(1)
    chapters_number = int(chapter_count)
    print(f"章节数量: {chapter_count}")
else:
    print("未找到章节数量")

#获取章节标题
#获取章节url
novel_chapter_titles = []
novel_list = []
for i in range(2,chapters_number):
    chapter_url = web.find_element(By.XPATH, f'/html/body/div[3]/dl/dd[{i}]/a')
    chapter_url_href = chapter_url.get_attribute('href')
    chapter_title = chapter_url.text
    novel_chapter_titles.append(chapter_title)
    novel_list.append(chapter_url_href)
    print(f"第{i-1}章链接: {chapter_title}:{chapter_url_href}")


#创建保存目录
novel_file_path = os.path.join(save_folder, f"{novel_name}.txt")

chapter_number = 0
for i,chapter_title in zip(novel_list,novel_chapter_titles):
    full_chapter_content = ""
    chapter_number +=1
    for  j in range(1,3):
        if j == 1:
            page_url = i[:-5] + f'.html'
        else:
            page_url = i[:-5] + f'_2.html'
        web.get(page_url)
        chapter_content = web.find_element(By.XPATH, '//*[@id="chaptercontent"]').text
        #cleaned_content = chapter_content.replace('请收藏：https://m.e16c8d.cfd', '')
        # 提取收藏信息
        collection_pattern = r'请收藏[：:]\s*https?://[^\s]+'
        collection_matches = re.findall(collection_pattern, chapter_content)

        # 移除收藏信息
        cleaned_content = re.sub(collection_pattern, '', chapter_content)
        # 去除多余的空白行
        lines = cleaned_content.split('\n')
        cleaned_lines = [line for line in lines if line.strip()]
        chapter_content = '\n'.join(cleaned_lines)
        # 添加到完整章节内容
        full_chapter_content += chapter_content + "\n\n"
        # 保存章节内容到文件

    try:
        with open(novel_file_path, "a", encoding="utf-8") as f:
            #f.write(f"\n第{chapter_number}章 {chapter_title}\n")
            #f.write("-" * 30 + "\n")
            f.write(full_chapter_content)

        print(f"第{chapter_number}章内容已保存")

    except Exception as e:
        print(f"保存第{chapter_number}章内容失败: {e}")
web.close()