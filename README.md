# University Job Board Crawler

这是一个用于抓取各大高校就业信息网站的爬虫项目，支持RSS订阅功能。

## 支持的学校

- 复旦大学 (fudan)
- 上海交通大学 (sjtu)
- 同济大学 (tongji)
- 华中科技大学 (hust)
- 南开大学 (nankai)
- 大连理工大学 (dlut)

## 功能特点

- 自动抓取各校就业信息
- 支持增量更新
- 输出标准RSS格式
- 提供RSS订阅服务
- 支持多页面爬取
- 错误重试机制
- 日志记录


## 使用方法

1. 启动RSS服务器：
```bash
python rss_server.py
```

2. 访问RSS订阅链接：
- 单个学校：`http://localhost:5001/rss/<school_code>`
  例如：`http://localhost:5001/rss/fudan`
- 所有学校：`http://localhost:5001/rss/all`

3. 使用RSS阅读器订阅相应的URL

## 学校代码对照表

| 学校 | 代码 |
|------|------|
| 复旦大学 | fudan |
| 上海交通大学 | sjtu |
| 同济大学 | tongji |
| 华中科技大学 | hust |
| 南开大学 | nankai |
| 大连理工大学 | dlut |

## 配置说明

- 默认端口：5001
- 数据保存路径：data/xml/
- 日志保存路径：src/logs/

## 开发说明

1. 添加新学校支持：
   - 在 src/ 下创建新的爬虫文件
   - 在 rss_server.py 中添加学校代码映射
   - 实现相应的解析逻辑

2. 修改输出格式：
   - 修改 src/utils/format_utils.py 中的 save_jobs_to_xml 函数

## 注意事项

- 建议适当设置请求延迟，避免对目标网站造成压力
- 定期检查网站结构变化，及时更新解析逻辑
- 遵守目标网站的robots.txt规则

## License

MIT License

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。
