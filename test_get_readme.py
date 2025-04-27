import requests
import base64

def get_readme(full_name, token=None):
    url = f"https://api.github.com/repos/{full_name}/readme"
    headers = {
        "Accept": "application/vnd.github+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        if encoding == "base64":
            decoded_bytes = base64.b64decode(content)
            return decoded_bytes.decode("utf-8")
        else:
            raise ValueError(f"未知的编码格式: {encoding}")
    else:
        raise Exception(f"请求失败: {response.status_code} - {response.text}")

# 示例用法
if __name__ == "__main__":
    full_name = "facebook/react"
    # 如果访问私有仓库或需要更高的请求频率，请提供你的 GitHub 个人访问令牌
    token = None  # 或者设置为你的 token，例如 "ghp_xxx"
    try:
        readme_content = get_readme(full_name, token)
        print(readme_content)
    except Exception as e:
        print(f"发生错误: {e}")
