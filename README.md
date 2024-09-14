# 课件重排工具

某免费 PDF 转换站点 API 逆向，用于将 PPT 课件重排为无边距的 A4 幅面 PDF 文件用于在 iPad Pro 上批注（支持定制）。

## 安装依赖

在使用本工具前，请确保已安装`requests`库。

## 使用方法

调用方式如下：

#### 1. 使用 Terminal 命令

```
python reformatter.py filename [outputfilename]
```

其中，`filename`为待处理的PDF文件名，`outputfilename`为可选参数，表示输出文件名。如果不提供`outputfilename`，则会使用默认的输出文件名。

#### 2. 使用 macOS Finder 中的 PDF 文件右键菜单（基于 Automator 应用）

2.1 新建 `Quick Action` 类型项目

2.2 从 `Actions` 列表中检索并添加 `Run Shell Script` 项目

2.3 修改 `Workflow receives current` 为 `PDF Files`

2.4 在已添加的 `Run Shell Script` 项目中添加命令 `/path/to/python /path/to/local/repo/reformatter.py "$@"`

2.5 修改该项目的 `Pass input` 参数为 `as arguments`

2.6 保存项目并命名为 `PDF3合1`。在 Finder 中选择一个 PDF 文件打开右键文件菜单，选择 `Quick Actions` -> `PDF3合1` 即可开始转换，转换结果保存为同一目录下的 `converted_<original_pdf_filename>`

## 格式化选项

要自定义格式化选项，请参考`request_body.json`文件内的参数。

以下是已定义的参数及其解释：

- `'layout_border': 0`: PDF页面布局：无边框
- `'layout_mode_multiple_pages_per_sheet': 3`: PDF页面布局：每页显示的幻灯片数量
- `'layout_page_orientation': 'portrait'`: 页面布局：PDF页面的方向（纵向）
- `'layout_inner_margin': 0`: 内边距：页面之间的间距
- `'layout_outer_margin': 0`: 外边距：内容与页面边缘之间的间距

效果预览：

![](./example.png)
