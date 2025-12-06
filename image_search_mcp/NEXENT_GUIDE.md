# Nexent 平台使用指南

## 概述

本MCP服务已优化以兼容Nexent平台的文件处理方式。**无需修改前端代码**，MCP工具会自动识别和处理Nexent平台传递的图片数据。

## Nexent平台的文件处理方式

Nexent平台在处理文件上传时，通常会：

1. **自动转换为Base64编码**：前端上传文件后，Nexent会自动转换为 `data:image/jpeg;base64,...` 格式
2. **或提供文件路径**：上传后返回服务器上的文件路径
3. **或提供文件URL**：上传后返回可访问的HTTP/HTTPS URL

## MCP工具自动适配

`search_similar_cases` 工具已支持**自动识别**以下格式：

✅ **Base64编码**（Nexent最常用）
- `data:image/jpeg;base64,/9j/4AAQSkZJRg...`
- `data:image/png;base64,iVBORw0KGgo...`
- 纯Base64字符串（无前缀）

✅ **文件路径**
- `/path/to/uploaded/image.jpg`
- `./uploads/image.png`

✅ **HTTP/HTTPS URL**
- `https://nexent-server.com/uploads/image.jpg`
- `http://localhost:8000/files/image.tif`

## 在Nexent平台中使用

### 1. 配置MCP服务器

在Nexent平台中添加MCP服务器：

- **服务器URL**: `http://172.17.0.1:18930/sse` （如果Nexent在Docker中）
- **或**: `http://localhost:18930/sse` （如果Nexent在同一主机）

### 2. 使用工具

在Nexent的对话界面中，直接调用工具：

```
请使用 search_similar_cases 工具分析这张图片：[上传图片]
```

或者：

```
搜索与这张病理切片相似的病例：[上传图片]
```

### 3. Nexent自动处理流程

1. **用户上传图片** → Nexent前端接收文件
2. **Nexent转换格式** → 自动转换为Base64或提供路径/URL
3. **调用MCP工具** → Nexent自动调用 `search_similar_cases`，传入图片数据
4. **MCP自动识别** → 工具自动识别输入格式（Base64/路径/URL）
5. **返回结果** → MCP返回相似病例的JSON结果
6. **Nexent展示** → 平台自动解析并展示结果

## 工具参数

### `search_similar_cases`

**参数：**
- `query_image` (string, 必需): 
  - Nexent会自动传递Base64编码、文件路径或URL
  - 工具会自动识别格式，无需手动指定
- `top_k` (int, 可选, 默认5): 
  - 返回最相似的病例数量
  - 范围：1-20

**返回格式：**
```json
{
  "query_status": "success",
  "total_results": 5,
  "cases": [
    {
      "rank": 1,
      "diagnosis": "TUM",
      "similarity_score": "92.34%",
      "distance": "0.0766",
      "image_path": "/path/to/similar_case.tif",
      "filename": "TUM_001.tif",
      "source": "Internal Atlas",
      "note": "Visual match based on tissue architecture and morphological features."
    }
  ]
}
```

## 示例对话

### 示例1：直接上传图片

**用户：**
```
请分析这张病理切片图片，找出相似的病例：[上传 image.jpg]
```

**Nexent自动调用：**
```json
{
  "tool": "search_similar_cases",
  "parameters": {
    "query_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "top_k": 5
  }
}
```

**MCP返回：**
```json
{
  "query_status": "success",
  "total_results": 5,
  "cases": [...]
}
```

### 示例2：指定返回数量

**用户：**
```
找出与这张图片最相似的前10个病例：[上传图片]
```

**Nexent自动调用：**
```json
{
  "tool": "search_similar_cases",
  "parameters": {
    "query_image": "data:image/png;base64,iVBORw0KGgo...",
    "top_k": 10
  }
}
```

## 故障排除

### 问题1：图片格式不支持

**错误信息：**
```json
{
  "query_status": "error",
  "error": "图片解码失败: ..."
}
```

**解决方案：**
- 确保上传的是JPG、PNG或TIF格式
- 检查图片文件是否损坏

### 问题2：Base64格式错误

**错误信息：**
```
Base64解码失败
```

**解决方案：**
- Nexent通常会自动处理，如果出错请联系平台管理员
- 确保图片数据完整传输

### 问题3：URL无法访问

**错误信息：**
```
无法从URL下载图片
```

**解决方案：**
- 确保URL可公开访问
- 检查网络连接
- 如果URL需要认证，可能需要先下载到本地再使用文件路径

## 技术细节

### 自动格式识别逻辑

1. **检查URL格式**：如果以 `http://` 或 `https://` 开头 → 从URL下载
2. **检查文件路径**：如果路径存在 → 从文件读取
3. **否则**：按Base64编码处理

### 支持的图片格式

- JPEG/JPG
- PNG
- TIFF/TIF
- 其他PIL/Pillow支持的格式

### 性能优化

- 使用GPU加速（如果可用）
- 批量处理优化
- 缓存模型实例

## 注意事项

1. **无需修改前端**：MCP工具已完全适配Nexent平台的处理方式
2. **自动格式识别**：工具会自动识别Base64、文件路径或URL
3. **错误处理**：如果格式识别失败，会返回清晰的错误信息
4. **性能考虑**：大图片（>10MB）可能需要较长时间处理

## 验证工具是否正常工作

在Nexent平台中测试：

```
请使用 search_similar_cases 工具，分析这张测试图片：[上传任意病理切片图片]
```

如果返回相似病例列表，说明工具配置正确。

