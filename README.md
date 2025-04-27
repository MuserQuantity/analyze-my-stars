# 我的GitHub星标分析工具

这是一个用于分析个人GitHub星标仓库的工具，可以帮助您了解自己的兴趣偏好、技术关注点以及星标习惯。

## 功能特点

- 分析星标仓库的编程语言分布
- 展示星标随时间的增长趋势
- 生成热门主题的词云图
- 分析仓库描述中的常见词汇
- 生成包含可视化图表的Markdown格式报告

## 安装依赖

确保您已安装Python 3.6或更高版本，然后安装所需依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 获取GitHub星标数据

首先，您需要下载您的GitHub星标数据。可以使用GitHub API或其他工具导出。

例如，使用GitHub API获取星标：

```bash
curl -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  "https://api.github.com/users/YOUR_USERNAME/starred?per_page=100&page=1" > stars.json
```

注意：如果您有超过100个星标，需要获取多页数据并合并。

### 2. 运行分析脚本

```bash
python analyze.py --input stars.json --output-dir output
```

参数说明：
- `--input`：您的星标数据JSON文件路径
- `--output-dir`：分析结果输出目录，默认为"output"

### 3. 查看分析结果

分析完成后，将在输出目录中生成以下文件：
- `report.md`：包含分析结果和可视化图表的Markdown报告
- `language_distribution.png`：编程语言分布图
- `stars_over_time.png`：星标增长趋势图
- `topics_wordcloud.png`：主题词云图
- `descriptions_wordcloud.png`：描述词云图

## 示例输出

![编程语言分布](example/language_distribution.png)
![星标增长趋势](example/stars_over_time.png)

## 自定义分析

您可以修改`analyze.py`文件，根据自己的需求调整分析内容和可视化方式。

## 许可证

MIT
