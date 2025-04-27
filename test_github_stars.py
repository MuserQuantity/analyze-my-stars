#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试脚本，用于验证GitHub星标仓库获取功能
"""

import os
import json
from github_stars import GitHubStarList

def main():
    # 从环境变量或.env文件加载GitHub用户名和cookie
    user = "MuserQuantity"
    cookie = ""
    
    if not user or not cookie:
        print("请设置环境变量GITHUB_USERNAME和GITHUB_COOKIE，或者在.env文件中配置")
        return
    
    print(f"使用GitHub用户: {user}")
    
    # 初始化GitHubStarList类
    handler = GitHubStarList(user=user, cookie=cookie, debug_mode=True)
    
    # 获取第一页星标仓库，不自动翻页
    print("获取第一页星标仓库...")
    repos = handler.get_starred_repos(
        page=1, 
        per_page=5,  # 只获取前5个仓库
        auto_paging=False,
        show_progress=True
    )
    
    # 打印获取到的结果
    if repos:
        print(f"\n成功获取到 {len(repos)} 个仓库:")
        for i, repo in enumerate(repos, 1):
            print(f"\n仓库 {i}:")
            for key, value in repo.items():
                print(f"  {key}: {value}")
    else:
        print("未获取到任何仓库，请检查用户名和cookie是否正确")
    
    # 可选：将结果保存到JSON文件
    with open('github_stars_test.json', 'w', encoding='utf-8') as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
        print(f"\n已将结果保存到 github_stars_test.json")

if __name__ == "__main__":
    main() 