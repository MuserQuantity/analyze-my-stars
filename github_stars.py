import os
import re
import requests
import base64
from dotenv import load_dotenv


class GitHubStarList:
    """
    处理GitHub星标仓库列表的工具类，
    用于获取用户的星标仓库列表。
    
    Attributes:
        HOST (str): GitHub的基础URL。
        CSRF_TOKEN_PATTERN (str): 用于在HTML中查找CSRF令牌的正则表达式。
        debug_mode (bool): 启用调试模式的标志。
        user (str): GitHub用户名。
        cookies (dict): 用于身份验证的解析后的cookies。
    """
    def __init__(self, user=None, cookie=None, debug_mode=False):
        """
        初始化GitHubStarList实例。
        
        Args:
            user (str, optional): GitHub用户名。如果为None，则从.env文件加载。
            cookie (str, optional): GitHub cookie字符串。如果为None，则从.env文件加载。
            debug_mode (bool, optional): 是否启用调试模式。默认为False。
        """
        self.HOST = "https://github.com"
        self.CSRF_TOKEN_PATTERN = r'<input type="hidden" name="authenticity_token" value="(.+?)" autocomplete="off" />'
        self.debug_mode = debug_mode
        
        # 如果未提供用户名或cookie，尝试从.env文件加载
        if user is None or cookie is None:
            self._load_from_env()
        else:
            self.user = user
            self.cookies = self._parse_cookie(cookie)
        
        # 初始化请求方法
        self._get, self._post = self._init_requests()

    def _load_from_env(self):
        """从.env文件加载用户名和cookie"""
        load_dotenv()
        self.user = os.getenv('GITHUB_USERNAME')
        cookie_str = os.getenv('GITHUB_COOKIE')
        print(self.user, cookie_str)
        if not self.user or not cookie_str:
            raise ValueError("GITHUB_USERNAME 和 GITHUB_COOKIE 必须在.env文件中设置或直接提供")
        
        self.cookies = self._parse_cookie(cookie_str)

    def _debug(self, *args):
        """如果启用了调试模式，则打印调试信息"""
        if self.debug_mode:
            print("[github-starred-list]", *args)

    def _parse_cookie(self, s):
        """将cookie字符串解析为字典"""
        cookies = {}
        for c in s.split(';'):
            try:
                name, value = c.strip().split('=', 1)  # 最多分割一次，以处理值中可能包含的等号
            except ValueError:
                self._debug(f"解析cookie时出错: {c}, 格式应为 'name=value'")
                continue
            cookies[name] = value
        return cookies

    def _init_requests(self):
        """初始化GET和POST请求方法，使用默认的headers和cookies"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36",
            "Accept": "text/html, application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://github.com"
        }

        def get(path, *args, **kwargs):
            self._debug('get', path, args, kwargs)
            return requests.get(self.HOST + path, *args, **kwargs, cookies=self.cookies)

        def post(path, *args, **kwargs):
            self._debug('post', path, args, kwargs)
            return requests.post(self.HOST + path, *args, **kwargs, headers=headers, cookies=self.cookies)

        return get, post

    def _search_before_text(self, s, pattern, text):
        """在指定文本之前的字符串中搜索模式"""
        ind = s.find(text)
        if ind != -1:
            s = s[:ind]

        found = re.findall(pattern, s)
        if len(found) == 0:
            return None

        return found[-1]

    def _preprocess(self, s):
        """预处理字符串，用于格式化list名称"""
        s = s.replace('&amp;', '&')
        s = re.sub(r'[^\w\s]', ' ', s)  # 将特殊字符替换为空格
        s = s.lower().strip()  # 小写并删除前导/尾随空格
        s = re.sub(r'\s+', ' ', s)  # 将多个空格合并为一个
        s = s.replace(' ', '-')  # 将空格替换为破折号
        return s

    def get_star_lists(self, raw=True):
        """
        获取用户的星标仓库列表
        
        Args:
            raw (bool, optional): 是否返回原始列表名称。默认为True。
                                 如果为False，将返回预处理后的列表名称。
        
        Returns:
            list: 星标仓库列表名称
        """
        mapping = self._get_lists_mapping(raw=raw)
        return list(mapping.keys())

    def get_starred_repos(self, page=1, per_page=30, show_progress=False, auto_paging=True, max_pages=None, delay=0, sort="created", direction="desc", filter="all"):
        """
        获取用户所有已标星的仓库
        
        Args:
            page (int, optional): 起始页码。默认为1。
            per_page (int, optional): 每页显示的仓库数量，0表示获取全部。默认为30。
            show_progress (bool, optional): 是否显示进度信息。默认为False。
            auto_paging (bool, optional): 是否自动翻页获取所有仓库。默认为True。
            max_pages (int, optional): 最大翻页数量，None表示不限制。默认为None。
            delay (float, optional): 每次翻页之间的延迟时间(秒)。默认为0。
            sort (str, optional): 排序方式，可选值：'created'(创建时间), 'updated'(更新时间), 'stars'(星标数)。默认为'created'。
            direction (str, optional): 排序方向，可选值：'desc'(降序), 'asc'(升序)。默认为'desc'。
            filter (str, optional): 过滤方式，可选值：'all'(全部), 'owner'(自己创建的), 'member'(成员)。默认为'all'。
            
        Returns:
            list: 包含仓库信息的字典列表，每个字典包含仓库名称、描述、语言等信息
        """
        all_repos = []
        current_page = page
        total_repos = 0
        
        if show_progress:
            print(f"开始获取标星仓库，从第 {page} 页开始...")
            if max_pages:
                print(f"最大翻页数量设置为 {max_pages} 页")
        
        try:
            import tqdm # type: ignore
            has_tqdm = True
        except ImportError:
            has_tqdm = False
            if show_progress:
                print("提示: 安装 tqdm 库可以显示更友好的进度条 (pip install tqdm)")
        
        pbar = None
        
        while True:
            # 检查是否达到最大翻页数量
            if max_pages and (current_page - page + 1) > max_pages:
                if show_progress:
                    print(f"已达到最大翻页数量 {max_pages}，停止获取")
                break
                
            # 获取当前页的星标仓库
            if show_progress and not has_tqdm:
                print(f"正在获取第 {current_page} 页的仓库...")
            
            # 使用新版的GitHub星标页面URL
            stars_url = f"/stars/{self.user}/repositories?direction={direction}&filter={filter}&page={current_page}&sort={sort}"
            r = self._get(stars_url)
            
            # 使用更新的正则表达式来匹配新的HTML结构
            # 匹配仓库列表项 - 查找每个仓库的li元素
            repo_items_pattern = r'<li class="py-4 border-bottom.*?</li>'
            repo_items = re.findall(repo_items_pattern, r.text, re.DOTALL)
            
            if not repo_items:
                # 没有更多仓库，跳出循环
                if show_progress:
                    print(f"没有更多仓库，共获取到 {total_repos} 个仓库")
                break
            
            page_repos = []
            for repo_item in repo_items:
                # 匹配仓库全名（用户名/仓库名）
                full_name_pattern = r'<a href="/([^"/]+/[^"/]+)"[^>]*>'
                full_name_match = re.search(full_name_pattern, repo_item, re.DOTALL)
                if not full_name_match:
                    continue
                
                full_name = full_name_match.group(1).strip()
                url = f"https://github.com/{full_name}"
                
                # 匹配描述
                desc_pattern = r'<p class="col-9 d-inline-block color-fg-muted m-0 pr-4">(.*?)</p>'
                desc_match = re.search(desc_pattern, repo_item, re.DOTALL)
                description = desc_match.group(1).strip() if desc_match else ""
                
                # 匹配星标数
                stars_pattern = r'<svg aria-label="star"[^>]*>.*?</svg>\s*(\d+(?:,\d+)*)'
                stars_match = re.search(stars_pattern, repo_item, re.DOTALL)
                stars = stars_match.group(1).replace(',', '') if stars_match else "0"
                
                # 匹配编程语言
                language_pattern = r'<span class="repo-language-color"[^>]*></span>\s*<span itemprop="programmingLanguage">([^<]+)</span>'
                language_match = re.search(language_pattern, repo_item, re.DOTALL)
                language = language_match.group(1).strip() if language_match else ""
                
                # 匹配标星时间
                starred_pattern = r'Starred <relative-time datetime="([^"]+)"[^>]*>(.*?)</relative-time>'
                starred_match = re.search(starred_pattern, repo_item, re.DOTALL)
                starred_at = ""
                starred_datetime = ""
                if starred_match:
                    starred_datetime = starred_match.group(1)
                    starred_at = starred_match.group(2).strip()
                
                repo_info = {
                    "full_name": full_name,
                    "url": url,
                    "description": description.replace('\n', ' ').strip(),
                    "stars": stars,
                    "language": language,
                    "starred_at": starred_at,
                    "starred_datetime": starred_datetime,
                    "page": current_page
                }
                page_repos.append(repo_info)
            
            # 添加本页获取的仓库
            all_repos.extend(page_repos)
            total_repos += len(page_repos)
            
            if show_progress and not has_tqdm:
                print(f"第 {current_page} 页: 获取到 {len(page_repos)} 个仓库")
            
            # 检查是否有下一页 (新的分页格式)
            if "Next" in r.text and f"page={current_page + 1}" in r.text:
                has_next_page = True
            else:
                has_next_page = False
                
            if not has_next_page:
                if show_progress:
                    print(f"已到达最后一页，共获取到 {total_repos} 个仓库")
                break
                
            if not auto_paging:
                # 如果不自动翻页，则停止获取
                if show_progress:
                    print(f"自动翻页已关闭，停止在第 {current_page} 页")
                break
                
            current_page += 1
            
            # 初始化或更新进度条
            if show_progress and has_tqdm:
                if pbar is None:
                    # 尝试估计总页数
                    last_page_match = re.search(r'page=(\d+)[^>]*aria-label=[\'"]Page (\d+)[\'"]', r.text)
                    if last_page_match:
                        estimated_total = int(last_page_match.group(2))
                    else:
                        estimated_total = max_pages if max_pages else 100
                    
                    pbar = tqdm.tqdm(total=estimated_total, desc="翻页进度", initial=current_page-page)
                else:
                    pbar.update(1)
                    pbar.set_description(f"翻页进度 (已获取 {total_repos} 个仓库)")
            
            # 如果指定了每页数量，并且已获取足够多的仓库，则停止
            if per_page > 0 and len(all_repos) >= per_page:
                all_repos = all_repos[:per_page]
                if show_progress:
                    print(f"已达到指定的获取数量 {per_page}，停止获取")
                break
                
            # 延迟一段时间再获取下一页
            if delay > 0:
                if show_progress and not has_tqdm:
                    print(f"等待 {delay} 秒后获取下一页...")
                import time
                time.sleep(delay)
        
        # 关闭进度条
        if pbar is not None:
            pbar.close()
                
        return all_repos

    def _get_lists_mapping(self, repo='octocat/Hello-World', raw=True):
        """
        获取列表ID映射
        
        Args:
            repo (str, optional): 用于获取列表的仓库名称。默认为'octocat/Hello-World'。
            raw (bool, optional): 是否使用原始列表名称。默认为True。
        
        Returns:
            dict: 列表名称到列表ID的映射
        """
        mapping = {}
        r = self._get(f'/{repo}/lists')

        pattern = r"""<input
                    type="checkbox"
                    class="mx-0 js-user-list-menu-item"
                    name="list_ids\[\]"
                    value="([0-9]+)"
                    (?:checked)?
                  >
                  <span data-view-component="true" class="Truncate ml-2 text-normal f5">
    <span data-view-component="true" class="Truncate-text">(.+?)</span>"""
        found = re.findall(pattern, r.text, re.MULTILINE)
        for l in found:
            list_name = l[1] if raw else self._preprocess(l[1])
            mapping[list_name] = l[0]

        return mapping

def get_github_star_lists(user=None, cookie=None, raw=True):
    """
    获取GitHub用户的星标仓库列表的便捷函数
    
    Args:
        user (str, optional): GitHub用户名。如果为None，则从.env文件加载。
        cookie (str, optional): GitHub cookie字符串。如果为None，则从.env文件加载。
        raw (bool, optional): 是否返回原始列表名称。默认为True。
    
    Returns:
        list: 星标仓库列表名称
    """
    handler = GitHubStarList(user=user, cookie=cookie)
    return handler.get_star_lists(raw=raw)

def get_github_starred_repos(user=None, cookie=None, page=1, per_page=0, show_progress=False, 
                           auto_paging=True, max_pages=None, delay=0, sort="created", direction="desc", filter="all"):
    """
    获取GitHub用户所有已标星的仓库的便捷函数
    
    Args:
        user (str, optional): GitHub用户名。如果为None，则从.env文件加载。
        cookie (str, optional): GitHub cookie字符串。如果为None，则从.env文件加载。
        page (int, optional): 起始页码。默认为1。
        per_page (int, optional): 每页显示的仓库数量，0表示获取全部。默认为0。
        show_progress (bool, optional): 是否显示进度信息。默认为False。
        auto_paging (bool, optional): 是否自动翻页获取所有仓库。默认为True。
        max_pages (int, optional): 最大翻页数量，None表示不限制。默认为None。
        delay (float, optional): 每次翻页之间的延迟时间(秒)。默认为0。
        sort (str, optional): 排序方式，可选值：'created'(创建时间), 'updated'(更新时间), 'stars'(星标数)。默认为'created'。
        direction (str, optional): 排序方向，可选值：'desc'(降序), 'asc'(升序)。默认为'desc'。
        filter (str, optional): 过滤方式，可选值：'all'(全部), 'owner'(自己创建的), 'member'(成员)。默认为'all'。
    
    Returns:
        list: 包含仓库信息的字典列表
    """
    handler = GitHubStarList(user=user, cookie=cookie)
    return handler.get_starred_repos(page=page, per_page=per_page, show_progress=show_progress,
                                    auto_paging=auto_paging, max_pages=max_pages, delay=delay,
                                    sort=sort, direction=direction, filter=filter)

def get_readme_content(full_name):
    """
    通过GitHub API获取仓库的README内容
    
    Args:
        full_name (str): 仓库全名 (格式: '用户名/仓库名')
        
    Returns:
        str: README的内容，解码后的文本，如果获取失败则返回空字符串
    """
    url = f"https://api.github.com/repos/{full_name}/readme"
    headers = {
        "Accept": "application/vnd.github+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            encoding = data.get("encoding", "")
            if encoding == "base64":
                decoded_bytes = base64.b64decode(content)
                # 将二进制数据解码为字符串，处理可能的解码错误
                try:
                    return decoded_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        return decoded_bytes.decode("latin-1")
                    except Exception:
                        return "README内容包含无法解码的字符"
            else:
                return f"未知的编码格式: {encoding}"
        else:
            return f"获取README失败 ({response.status_code}): {response.text}"
    except Exception as e:
        return f"获取README时出错: {str(e)}"

def export_starred_repos(repos, export_path, format="json", include_readme=False):
    """
    将仓库数据导出到文件
    
    Args:
        repos (list): 仓库数据列表
        export_path (str): 导出文件路径
        format (str, optional): 导出格式，支持'json'和'csv'。默认为'json'。
        include_readme (bool, optional): 是否包含README内容。默认为False。
        
    Returns:
        bool: 导出是否成功
    """
    if not repos:
        print("没有数据可导出")
        return False
        
    # 标准化格式名称
    format = format.lower()
    
    # 为每个仓库添加README相关字段
    for repo in repos:
        if 'full_name' in repo:
            # 添加README URL
            repo['readme_url'] = f"https://github.com/{repo['full_name']}/raw/refs/heads/main/README.md"
            
            # 如果需要获取README内容
            if include_readme:
                print(f"正在获取 {repo['full_name']} 的README内容...")
                readme_content = get_readme_content(repo['full_name'])
                
                # 处理README内容，移除可能导致JSON解析问题的字符
                if readme_content:
                    # 替换控制字符和其他可能导致问题的字符
                    readme_content = ''.join(ch if ord(ch) >= 32 else ' ' for ch in readme_content)
                    # 限制长度，防止过大
                    if len(readme_content) > 100000:  # 限制为约100KB的文本
                        readme_content = readme_content[:100000] + "... [内容过长已截断]"
                
                repo['readme_content'] = readme_content
    
    try:
        if format == 'json':
            # 导出为JSON格式
            import json
            
            # 自定义JSON编码器，处理特殊字符
            class CustomJSONEncoder(json.JSONEncoder):
                def encode(self, obj):
                    if isinstance(obj, str):
                        # 确保字符串是有效的JSON
                        return super().encode(obj)
                    return super().encode(obj)
                    
                def default(self, obj):
                    # 处理其他类型的对象
                    try:
                        return super().default(obj)
                    except TypeError:
                        return str(obj)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(repos, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
            print(f"已将结果导出到 {export_path}")
            return True
                
        elif format == 'csv':
            # 导出为CSV格式
            import csv
            with open(export_path, 'w', encoding='utf-8-sig', newline='') as f:
                # 确保所有可能的字段都包含在内
                all_fields = set()
                for repo in repos:
                    all_fields.update(repo.keys())
                
                # 将常用字段放在前面，其他字段按字母顺序排序
                priority_fields = ['full_name', 'description', 'url', 'stars', 'language', 
                                  'starred_at', 'starred_datetime', 'readme_url']
                if include_readme:
                    priority_fields.append('readme_content')
                    
                other_fields = sorted(list(all_fields - set(priority_fields)))
                fieldnames = priority_fields + other_fields
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for repo in repos:
                    # 确保所有字段都是字符串类型，并处理特殊字符
                    sanitized_repo = {}
                    for key, value in repo.items():
                        if value is None:
                            sanitized_repo[key] = ''
                        elif key == 'readme_content' and isinstance(value, str):
                            # 处理README内容中的CSV特殊字符
                            sanitized_value = value.replace('\r', ' ').replace('\0', '')
                            sanitized_repo[key] = sanitized_value
                        else:
                            sanitized_repo[key] = str(value)
                    writer.writerow(sanitized_repo)
            print(f"已将结果导出到 {export_path}")
            return True
                
        else:
            print(f"不支持的导出格式: {format}，支持的格式有: json, csv")
            return False
            
    except Exception as e:
        print(f"导出过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='获取GitHub星标仓库和列表')
    parser.add_argument('--user', help='GitHub用户名，如未指定则从.env文件加载')
    parser.add_argument('--cookie', help='GitHub cookie字符串，如未指定则从.env文件加载')
    parser.add_argument('--page', type=int, default=1, help='起始页码，默认为1')
    parser.add_argument('--per-page', type=int, default=0, help='每页显示的仓库数量，0表示获取全部，默认为0')
    parser.add_argument('--lists-only', action='store_true', help='仅获取星标列表，不获取仓库')
    parser.add_argument('--repos-only', action='store_true', help='仅获取星标仓库，不获取列表')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--no-auto-paging', action='store_true', help='关闭自动翻页，只获取指定页面')
    parser.add_argument('--max-pages', type=int, help='最大翻页数量，不指定则不限制')
    parser.add_argument('--delay', type=float, default=0, help='每次翻页之间的延迟时间(秒)，默认为0')
    parser.add_argument('--export', help='将结果导出到指定文件(支持json, csv格式)')
    parser.add_argument('--include-readme', action='store_true', help='在导出文件中包含README内容')
    parser.add_argument('--sort', default='created', choices=['created', 'updated', 'stars'], 
                       help='排序方式：created(创建时间), updated(更新时间), stars(星标数)，默认为created')
    parser.add_argument('--direction', default='desc', choices=['desc', 'asc'],
                       help='排序方向：desc(降序), asc(升序)，默认为desc')
    parser.add_argument('--filter', default='all', choices=['all', 'owner', 'member'],
                       help='过滤方式：all(全部), owner(自己创建的), member(成员)，默认为all')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 创建处理器
    handler = GitHubStarList(user=args.user, cookie=args.cookie, debug_mode=args.debug)
    
    try:
        # 根据参数决定要获取的内容
        if not args.repos_only:
            # 获取并打印星标列表
            print("星标列表:")
            star_lists = handler.get_star_lists()
            for lst in star_lists:
                print(f"- {lst}")
        
        if not args.lists_only:
            # 获取并打印已标星的仓库
            print("\n已标星的仓库:")
            starred_repos = handler.get_starred_repos(
                page=args.page, 
                per_page=args.per_page, 
                show_progress=True,
                auto_paging=not args.no_auto_paging,
                max_pages=args.max_pages,
                delay=args.delay,
                sort=args.sort,
                direction=args.direction,
                filter=args.filter
            )
            
            # 如果没有获取到仓库
            if not starred_repos:
                print("未获取到任何标星仓库")
                sys.exit(0)
            
            # 按页面分组显示仓库
            repos_by_page = {}
            for repo in starred_repos:
                page = repo.get('page', 0)
                if page not in repos_by_page:
                    repos_by_page[page] = []
                repos_by_page[page].append(repo)
            
            # 显示每一页的仓库
            for page in sorted(repos_by_page.keys()):
                print(f"\n第 {page} 页的仓库:")
                for repo in repos_by_page[page]:
                    stars_info = f"⭐ {int(repo['stars']):,}" if 'stars' in repo and repo['stars'] else ""
                    starred_at = f"Starred {repo['starred_at']}" if 'starred_at' in repo and repo['starred_at'] else ""
                    print(f"- {repo['full_name']}: {repo['description']} [{repo['language']}] {stars_info} {starred_at}")
            
            # 显示统计信息
            print(f"\n总共获取到 {len(starred_repos)} 个标星仓库，共 {len(repos_by_page)} 页")
            
            # 如果指定了导出文件
            if args.export:
                export_path = args.export
                export_format = export_path.lower().split('.')[-1]
                
                if export_format in ['json', 'csv']:
                    # 导出为JSON或CSV格式
                    export_starred_repos(
                        starred_repos, 
                        export_path, 
                        format=export_format,
                        include_readme=args.include_readme
                    )
                else:
                    print(f"不支持的导出格式: {export_format}，支持的格式有: json, csv")
            
    except Exception as e:
        print(f"发生错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)