import time  # 导入时间模块，用于添加延迟
from selenium.webdriver import Chrome  # 导入Chrome浏览器驱动
from selenium.webdriver.chrome.options import Options  # 导入Chrome选项配置
from selenium.webdriver.common.by import By  # 导入元素定位方式
from selenium.common.exceptions import NoSuchElementException, TimeoutException  # 导入异常处理
from selenium.webdriver.support.ui import WebDriverWait  # 导入等待机制
from selenium.webdriver.support import expected_conditions as EC  # 导入预期条件
import re  # 导入正则表达式模块
import os  # 导入操作系统接口模块
from concurrent.futures import ThreadPoolExecutor, as_completed  # 导入线程池和完成状态检查
import threading  # 导入线程模块
from queue import Queue  # 导入队列模块，用于线程间通信
import requests  # 导入HTTP请求库
from bs4 import BeautifulSoup  # 导入HTML解析库

def create_driver():
    """创建优化的Chrome驱动实例"""
    # 创建Chrome选项对象
    options = Options()
    options.add_argument('--headless')  # 无头模式，不显示浏览器界面
    options.add_argument('--no-sandbox')  # 禁用沙盒模式
    options.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
    options.add_argument('--disable-gpu')  # 禁用GPU加速
    options.add_argument('--disable-images')  # 禁用图片加载
    options.add_argument('--disable-javascript')  # 禁用JavaScript（如果不需要）
    options.add_argument('--window-size=1920,1080')  # 设置窗口大小
    options.add_argument('--blink-settings=imagesEnabled=false')  # 禁用图片
    options.add_argument('--disable-plugins')  # 禁用插件
    options.add_argument('--disable-extensions')  # 禁用扩展
    options.page_load_strategy = 'eager'  # 页面加载策略，不等待所有资源加载完成
    
    # 创建Chrome浏览器实例
    driver = Chrome(options=options)
    driver.implicitly_wait(5)  # 设置隐式等待时间为5秒
    return driver

def fetch_chapter_content_fast(chapter_url, chapter_title, chapter_index):
    """
    使用 requests 快速获取章节内容
    :param chapter_url: 章节URL
    :param chapter_title: 章节标题
    :param chapter_index: 章节索引
    :return: 章节索引和内容元组
    """
    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # 初始化完整章节内容
        full_chapter_content = ""
        
        # 处理分页情况，通常每章有1-2页
        for j in range(1, 3):
            # 构造页面URL
            if j == 1:
                page_url = chapter_url[:-5] + '.html'  # 第一页
            else:
                page_url = chapter_url[:-5] + '_2.html'  # 第二页
            
            # 重试机制，最多重试3次
            for retry in range(3):
                try:
                    # 发送HTTP GET请求
                    response = requests.get(page_url, headers=headers, timeout=10)
                    response.encoding = 'utf-8'  # 设置编码
                    break  # 成功获取则跳出重试循环
                except Exception as e:
                    # 如果重试3次都失败，则抛出异常
                    if retry == 2:
                        raise e
                    time.sleep(1)  # 等待1秒后重试
            
            # 使用BeautifulSoup解析HTML内容
            soup = BeautifulSoup(response.text, 'html.parser')
            # 查找章节内容元素
            content_element = soup.find('div', id='chaptercontent')
            
            # 如果找到内容元素
            if content_element:
                # 提取文本内容
                chapter_content = content_element.get_text()
                
                # 清理内容，移除"请收藏"相关信息
                collection_pattern = r'请收藏[：:]\s*https?://[^\s]+'
                cleaned_content = re.sub(collection_pattern, '', chapter_content)
                
                # 去除多余空白行
                lines = cleaned_content.split('\n')
                cleaned_lines = [line for line in lines if line.strip()]
                chapter_content = '\n'.join(cleaned_lines)
                
                # 将内容添加到完整章节内容中
                full_chapter_content += chapter_content + "\n\n"
            else:
                # 如果未找到内容元素，打印警告信息
                print(f"第{chapter_index}章 {chapter_title} 第{j}页内容未找到")

        # 打印完成信息
        print(f"第{chapter_index}章 {chapter_title} 内容获取完成")
        # 返回章节索引和格式化后的内容
        return chapter_index, f"\n第{chapter_index}章 {chapter_title}\n" + "-" * 30 + "\n" + full_chapter_content

    except Exception as e:
        # 捕获异常并打印错误信息
        print(f"获取第{chapter_index}章 {chapter_title} 内容失败: {e}")
        # 返回失败信息
        return chapter_index, f"\n第{chapter_index}章 {chapter_title}\n" + "-" * 30 + "\n" + f"获取失败: {e}\n\n"

def fetch_chapter_content(chapter_url, chapter_title, chapter_index):
    """
    优化的 Selenium 获取单章内容
    :param chapter_url: 章节URL
    :param chapter_title: 章节标题
    :param chapter_index: 章节索引
    :return: 章节索引和内容元组
    """
    # 初始化浏览器驱动为None
    driver = None
    try:
        # 创建浏览器驱动实例
        driver = create_driver()
        # 初始化完整章节内容
        full_chapter_content = ""

        # 处理分页情况
        for j in range(1, 3):
            # 构造页面URL
            if j == 1:
                page_url = chapter_url[:-5] + '.html'  # 第一页
            else:
                page_url = chapter_url[:-5] + '_2.html'  # 第二页

            # 访问页面URL
            driver.get(page_url)
            
            # 设置显式等待，等待内容元素加载完成
            wait = WebDriverWait(driver, 5)  # 等待时间5秒
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="chaptercontent"]')))
            
            # 提取章节内容文本
            chapter_content = driver.find_element(By.XPATH, '//*[@id="chaptercontent"]').text

            # 清理内容，移除"请收藏"相关信息
            collection_pattern = r'请收藏[：:]\s*https?://[^\s]+'
            cleaned_content = re.sub(collection_pattern, '', chapter_content)

            # 去除多余空白行
            lines = cleaned_content.split('\n')
            cleaned_lines = [line for line in lines if line.strip()]
            chapter_content = '\n'.join(cleaned_lines)

            # 将内容添加到完整章节内容中
            full_chapter_content += chapter_content + "\n\n"

        # 打印完成信息
        print(f"第{chapter_index}章 {chapter_title} 内容获取完成")
        # 返回章节索引和格式化后的内容
        return chapter_index, f"\n第{chapter_index}章 {chapter_title}\n" + "-" * 30 + "\n" + full_chapter_content

    except TimeoutException:
        # 处理超时异常
        print(f"获取第{chapter_index}章 {chapter_title} 内容超时")
        return chapter_index, f"\n第{chapter_index}章 {chapter_title}\n" + "-" * 30 + "\n" + f"获取失败: 页面加载超时\n\n"
    except NoSuchElementException as e:
        # 处理元素未找到异常
        print(f"获取第{chapter_index}章 {chapter_title} 内容失败: 未找到元素 {e}")
        return chapter_index, f"\n第{chapter_index}章 {chapter_title}\n" + "-" * 30 + "\n" + f"获取失败: 页面元素未找到\n\n"
    except Exception as e:
        # 处理其他异常
        print(f"获取第{chapter_index}章 {chapter_title} 内容失败: {e}")
        return chapter_index, f"\n第{chapter_index}章 {chapter_title}\n" + "-" * 30 + "\n" + f"获取失败: {e}\n\n"
    finally:
        # 确保浏览器驱动被关闭
        if driver:
            driver.quit()

def save_chapters_in_order(novel_file_path, results_queue, total_chapters):
    """
    按顺序保存章节内容
    :param novel_file_path: 小说文件保存路径
    :param results_queue: 结果队列
    :param total_chapters: 总章节数
    """
    # 用于存储已获取但未保存的章节内容
    saved_chapters = {}
    # 下一个需要保存的章节编号
    next_chapter = 1

    # 打开文件进行追加写入
    with open(novel_file_path, "a", encoding="utf-8") as f:
        # 循环直到所有章节都保存完成
        while next_chapter <= total_chapters:
            # 检查队列中是否有当前需要的章节
            try:
                # 从队列中获取章节内容，超时时间120秒
                chapter_index, content = results_queue.get(timeout=120)
                # 将章节内容存储到字典中
                saved_chapters[chapter_index] = content

                # 保存连续的章节
                while next_chapter in saved_chapters:
                    # 写入章节内容到文件
                    f.write(saved_chapters[next_chapter])
                    f.flush()  # 立即写入文件
                    # 打印保存完成信息
                    print(f"第{next_chapter}章内容已保存")
                    # 从字典中删除已保存的章节
                    del saved_chapters[next_chapter]
                    # 更新下一个需要保存的章节编号
                    next_chapter += 1

            except Exception as e:
                # 处理保存过程中的异常
                print(f"保存过程出现异常: {e}")
                # 即使出现异常也继续处理其他章节
                continue

def get_all_chapters(web, chapter_list_url):
    """
    获取所有章节链接和标题
    :param web: 浏览器实例
    :param chapter_list_url: 章节列表URL
    :return: 章节标题列表和章节链接列表
    """
    # 初始化章节标题和链接列表
    novel_chapter_titles = []
    novel_list = []
    
    try:
        # 访问章节列表页面
        web.get(chapter_list_url)
        time.sleep(1)  # 等待1秒让页面加载完成
        
        # 尝试多种定位方式获取章节元素
        chapter_elements = []
        
        # 方法1: 通过章节列表容器定位
        try:
            chapter_elements = web.find_elements(By.CSS_SELECTOR, "div#list dl dd a")
        except:
            pass  # 如果失败则跳过
            
        # 方法2: 通过XPath定位
        if not chapter_elements:
            try:
                chapter_elements = web.find_elements(By.XPATH, "//div[@id='list']//dd/a")
            except:
                pass  # 如果失败则跳过
                
        # 方法3: 通用定位方式
        if not chapter_elements:
            try:
                chapter_elements = web.find_elements(By.XPATH, "//dd/a[contains(@href, '.html')]")
            except:
                pass  # 如果失败则跳过
        
        # 如果没有找到章节元素
        if not chapter_elements:
            print("无法找到章节列表元素")
            return novel_chapter_titles, novel_list  # 返回空列表
            
        # 打印找到的章节链接数量
        print(f"找到 {len(chapter_elements)} 个章节链接")
        
        # 遍历所有章节元素
        for idx, element in enumerate(chapter_elements, 1):
            try:
                # 获取章节链接和标题
                chapter_url_href = element.get_attribute('href')
                chapter_title = element.text.strip()
                
                # 验证链接和标题有效性
                if chapter_url_href and chapter_title and '.html' in chapter_url_href:
                    # 添加到列表中
                    novel_chapter_titles.append(chapter_title)
                    novel_list.append(chapter_url_href)
                    # 每100章显示一次进度（前10章也显示）
                    if idx <= 10 or idx % 100 == 0:
                        print(f"第{idx}章: {chapter_title}")
                else:
                    # 只在前几章显示警告信息
                    if idx <= 10:
                        print(f"第{idx}章信息不完整，跳过")
                    
            except Exception as e:
                # 只在前几章显示错误信息
                if idx <= 10:
                    print(f"处理第{idx}章信息失败: {e}")
                continue  # 继续处理下一章
                
    except Exception as e:
        # 处理获取章节列表时的异常
        print(f"获取章节列表失败: {e}")
    
    # 返回章节标题和链接列表
    return novel_chapter_titles, novel_list

def main():
    """主函数"""
    # 获取用户输入的小说名称
    novel_name = input("请输入小说名称：")

    # 创建以小说名称命名的文件夹
    save_folder = novel_name
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)  # 如果文件夹不存在则创建

    # 获取小说URL
    web = Chrome()  # 创建浏览器实例
    web.implicitly_wait(5)  # 设置隐式等待时间为5秒
    
    try:
        # 构造搜索URL并访问
        bqg_url = 'https://m.bqgl.cc/s?q=' + novel_name
        web.get(bqg_url)
        
        # 等待搜索结果加载完成
        wait = WebDriverWait(web, 5)
        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div/div[1]/div/a')))
        
        # 获取小说链接
        find_novel_href = web.find_element(By.XPATH, '/html/body/div[3]/div/div/div[1]/div/a')
        novel_href = find_novel_href.get_attribute('href')
        novel_url = novel_href

        # 访问小说主页获取章节列表URL
        web.get(novel_url)
        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[5]/a')))
        find_chapter_list_href = web.find_element(By.XPATH, '/html/body/div[4]/div[5]/a')
        chapter_list_url = find_chapter_list_href.get_attribute('href')
        print(f"章节列表URL: {chapter_list_url}")

        # 访问章节列表页面获取章节数量
        web.get(chapter_list_url)
        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/span[@class="title"]')))
        chapters_number_element = web.find_element(By.XPATH, '/html/body/div[2]/span[@class="title"]')
        match = re.search(r'\((\d+)章\)', chapters_number_element.text)

        # 解析章节数量
        if match:
            chapter_count = match.group(1)
            chapters_number = int(chapter_count)
            print(f"章节数量: {chapter_count}")
        else:
            print("未找到章节数量，使用默认值")
            chapters_number = 1000

        # 获取所有章节标题和链接
        print("正在获取所有章节链接...")
        novel_chapter_titles, novel_list = get_all_chapters(web, chapter_list_url)

    except TimeoutException:
        # 处理页面加载超时异常
        print("页面加载超时，请检查网络连接")
        return
    except NoSuchElementException as e:
        # 处理元素未找到异常
        print(f"页面元素未找到: {e}")
        return
    except Exception as e:
        # 处理其他异常
        print(f"获取小说信息时发生错误: {e}")
        return
    finally:
        # 确保浏览器被关闭
        web.quit()

    # 如果没有获取到章节信息
    if not novel_chapter_titles:
        print("未能获取任何章节信息")
        return

    # 打印获取到的章节数量
    print(f"共获取到 {len(novel_chapter_titles)} 个章节")

    # 创建保存文件路径
    novel_file_path = os.path.join(save_folder, f"{novel_name}.txt")

    # 初始化文件（清空旧内容）
    with open(novel_file_path, "w", encoding="utf-8") as f:
        f.write(f"{novel_name}\n\n")

    # 使用多线程爬取章节内容 - 设置线程数为8
    max_workers = 8  # 增加线程数提高速度
    results_queue = Queue()  # 创建结果队列

    # 启动保存线程
    save_thread = threading.Thread(target=save_chapters_in_order,
                                  args=(novel_file_path, results_queue, len(novel_list)))
    save_thread.daemon = True  # 设置为守护线程
    save_thread.start()  # 启动保存线程

    # 使用线程池执行爬取任务
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务 - 使用更快的requests方法
        future_to_chapter = {
            executor.submit(fetch_chapter_content_fast, url, title, idx): idx  # 使用更快的方法
            for idx, (url, title) in enumerate(zip(novel_list, novel_chapter_titles), 1)
        }

        # 处理完成的任务
        completed_count = 0  # 已完成任务计数
        total_chapters = len(novel_list)  # 总章节数
        
        # 遍历已完成的任务
        for future in as_completed(future_to_chapter):
            try:
                # 获取任务结果
                chapter_index, content = future.result()
                # 将结果放入队列
                results_queue.put((chapter_index, content))
                completed_count += 1
                # 每10章显示一次进度或在完成时显示
                if completed_count % 10 == 0 or completed_count == total_chapters:
                    print(f"已完成 {completed_count}/{total_chapters} 个章节")
            except Exception as e:
                # 处理任务异常
                chapter_index = future_to_chapter[future]
                print(f"第{chapter_index}章处理异常: {e}")
                results_queue.put((chapter_index, f"\n第{chapter_index}章 获取失败\n"))
                completed_count += 1

    # 等待所有章节保存完成，超时时间300秒
    save_thread.join(timeout=300)
    print("小说爬取完成！")

# 程序入口点
if __name__ == "__main__":
    main()
