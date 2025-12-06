# 使用说明

## 功能说明

用户在前端输入框中上传一张 JPG/PNG 格式的图片，MCP 工具会自动搜索图谱库中最相似的病例切片，并返回分析结果。

## 前端集成示例

### JavaScript/TypeScript 示例

```javascript
// 方式1：使用文件输入框
async function searchSimilarCases(fileInput) {
    const file = fileInput.files[0];
    if (!file) return;
    
    // 将文件转换为Base64（data URL格式）
    const base64Image = await fileToBase64(file);
    
    // 调用MCP工具
    const result = await mcpClient.callTool('search_similar_cases', {
        query_image: base64Image,  // Base64编码的图片
        top_k: 5  // 返回最相似的5个病例
    });
    
    // 解析结果
    const data = JSON.parse(result);
    console.log('找到相似病例:', data.cases);
}

// 文件转Base64辅助函数
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result); // 已经是 data:image/... 格式
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
```

### Python 客户端示例

```python
import base64
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def search_similar_cases_from_file(image_path: str, top_k: int = 5):
    """从图片文件搜索相似病例"""
    
    # 读取图片并转换为Base64
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        # 添加data URL前缀
        data_url = f"data:image/jpeg;base64,{base64_string}"
    
    # 连接MCP服务器
    async with stdio_client(StdioServerParameters(
        command="python",
        args=["/path/to/server.py"]
    )) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 调用工具
            result = await session.call_tool(
                "search_similar_cases",
                {
                    "query_image": data_url,
                    "top_k": top_k
                }
            )
            
            return result.content[0].text

# 使用示例
result = await search_similar_cases_from_file("pathology_image.jpg", top_k=5)
print(result)
```

## MCP 工具参数

### `search_similar_cases`

**参数：**
- `query_image` (string, 必需): 
  - Base64编码的图片字符串（推荐使用 `data:image/jpeg;base64,...` 格式）
  - 或者服务器可访问的图片文件路径
- `top_k` (int, 可选, 默认5): 返回最相似的病例数量

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
    },
    ...
  ]
}
```

## 支持的图片格式

- JPEG/JPG
- PNG
- TIFF/TIF
- 其他 PIL/Pillow 支持的格式

## 工作流程

1. **用户上传图片** → 前端接收文件对象
2. **转换为Base64** → 使用 `FileReader.readAsDataURL()` 或类似方法
3. **调用MCP工具** → 传入Base64字符串和top_k参数
4. **MCP处理** → 
   - 解码图片
   - 使用PLIP模型提取特征向量
   - 在ChromaDB中搜索最相似的病例
5. **返回结果** → JSON格式的相似病例列表

## 注意事项

1. **Base64编码大小**：Base64编码会使文件大小增加约33%，大图片可能需要较长时间传输
2. **图片尺寸**：建议图片尺寸不要过大（如超过10MB），会影响处理速度
3. **网络传输**：如果图片很大，考虑先压缩或调整尺寸
4. **错误处理**：确保处理可能的错误情况（文件格式不支持、网络错误等）

## 示例：完整的前端集成

```html
<!DOCTYPE html>
<html>
<head>
    <title>病理图谱搜索</title>
</head>
<body>
    <input type="file" id="imageInput" accept="image/jpeg,image/png,image/tiff">
    <button onclick="search()">搜索相似病例</button>
    <div id="results"></div>

    <script>
        async function search() {
            const fileInput = document.getElementById('imageInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('请选择一张图片');
                return;
            }
            
            // 转换为Base64
            const base64Image = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
            
            // 调用MCP工具（这里需要根据你的MCP客户端实现）
            try {
                const result = await callMCPTool('search_similar_cases', {
                    query_image: base64Image,
                    top_k: 5
                });
                
                // 显示结果
                const data = JSON.parse(result);
                displayResults(data);
            } catch (error) {
                console.error('搜索失败:', error);
                alert('搜索失败: ' + error.message);
            }
        }
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            if (data.query_status === 'success') {
                let html = `<h3>找到 ${data.total_results} 个相似病例：</h3>`;
                data.cases.forEach(case => {
                    html += `
                        <div>
                            <h4>排名 ${case.rank}: ${case.diagnosis}</h4>
                            <p>相似度: ${case.similarity_score}</p>
                            <p>文件: ${case.filename}</p>
                        </div>
                    `;
                });
                resultsDiv.innerHTML = html;
            } else {
                resultsDiv.innerHTML = `<p>错误: ${data.error}</p>`;
            }
        }
    </script>
</body>
</html>
```

