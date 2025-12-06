# 故障排除指南

## 问题：文件解析已停止

### 症状
在Nexent平台上传图片后，提示"文件解析已停止"，对话结束。

### 原因分析

根据日志分析，问题可能出现在以下几个环节：

1. **Nexent文件预处理失败**（最常见）
   - 日志显示：`POST /api/file/preprocess?conversation_id=22 HTTP/1.1" 404 Not Found`
   - Nexent平台在文件上传后，会先尝试预处理文件（OCR、图像识别等）
   - 如果预处理接口返回404，会导致流程中断

2. **MCP工具未被调用**
   - 如果预处理阶段失败，MCP工具可能根本没有被调用
   - 需要检查MCP服务器日志确认

3. **网络连接问题**
   - Nexent容器无法访问MCP服务器（端口18930）
   - 需要确保网络配置正确

### 解决方案

#### 方案1：检查Nexent文件预处理配置

文件预处理404错误是Nexent平台的问题，可能需要：

1. **检查Nexent配置**
   ```bash
   # 查看Nexent配置文件
   ls ~/nexent/backend/config/
   ```

2. **检查文件预处理服务**
   ```bash
   # 查看data-process容器日志
   docker logs nexent-data-process --tail 50
   ```

3. **临时解决方案**：如果预处理不是必需的，可以尝试：
   - 直接在对话中上传图片，而不是通过文件上传功能
   - 或者等待Nexent平台修复预处理接口

#### 方案2：验证MCP服务器连接

1. **从Nexent容器测试连接**
   ```bash
   docker exec nexent-runtime curl -v http://172.17.0.1:18930/sse
   ```

2. **检查MCP服务器日志**
   ```bash
   tail -f ~/mcp/image_search_mcp/server.log
   ```

3. **确认MCP服务器正在运行**
   ```bash
   ps aux | grep "python.*server.py"
   netstat -tlnp | grep 18930
   ```

#### 方案3：使用文件路径而非Base64

如果Nexent上传文件后提供了文件路径，可以：

1. **查找上传的文件位置**
   ```bash
   # Nexent通常会将文件存储在MinIO或本地存储
   docker exec nexent-minio ls -la /data/
   ```

2. **修改MCP工具调用方式**
   - 如果Nexent提供了文件路径，可以直接使用路径
   - MCP工具已支持自动识别文件路径

#### 方案4：添加详细日志

已优化MCP工具，添加了详细的日志输出：

- 输入数据预览
- 图片解码过程
- 特征提取过程
- 错误详情

查看日志：
```bash
tail -f ~/mcp/image_search_mcp/server.log
```

### 调试步骤

1. **检查MCP服务器状态**
   ```bash
   cd ~/mcp/image_search_mcp
   ps aux | grep server.py
   tail -50 server.log
   ```

2. **测试MCP工具**
   ```bash
   # 使用Base64测试
   python -c "
   import base64
   from server import search_similar_cases
   # 创建一个小的测试图片Base64
   test_img = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
   result = search_similar_cases(test_img, top_k=3)
   print(result)
   "
   ```

3. **检查Nexent日志**
   ```bash
   docker logs nexent-runtime --tail 100 | grep -i "mcp\|18930\|search_similar\|error"
   docker logs nexent-mcp --tail 100 | grep -i "error\|18930"
   ```

4. **验证网络连接**
   ```bash
   # 从主机测试
   curl http://localhost:18930/sse
   
   # 从Nexent容器测试
   docker exec nexent-runtime curl http://172.17.0.1:18930/sse
   ```

### 常见错误及解决方法

#### 错误1：Base64解码失败
**原因**：输入不是有效的Base64编码
**解决**：确保Nexent正确传递了Base64数据

#### 错误2：图片格式不支持
**原因**：图片格式不是JPG/PNG/TIF
**解决**：转换图片格式或更新代码支持更多格式

#### 错误3：特征提取失败
**原因**：PLIP模型未加载或GPU内存不足
**解决**：
- 检查模型是否正确加载
- 检查GPU内存
- 尝试使用CPU模式

#### 错误4：数据库连接失败
**原因**：ChromaDB数据库不存在或损坏
**解决**：重新运行 `indexer.py` 构建索引

### 联系支持

如果问题持续存在，请提供以下信息：

1. MCP服务器日志：`~/mcp/image_search_mcp/server.log`
2. Nexent运行时日志：`docker logs nexent-runtime --tail 200`
3. Nexent MCP日志：`docker logs nexent-mcp --tail 200`
4. 错误截图或错误消息

