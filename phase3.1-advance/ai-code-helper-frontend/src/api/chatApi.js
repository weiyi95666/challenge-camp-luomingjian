import axios from 'axios'

// 配置axios基础URL
const API_BASE_URL = 'http://localhost:8081/api'

/**
 * 与 AI 进行流式对话（支持多模态多文件）
 * @param {number} memoryId 会话ID
 * @param {string} message 消息内容
 * @param {Array<File>} files 文件列表（可选）
 * @param {function} onMessage 收到消息的回调
 * @param {function} onError 出错的回调
 * @param {function} onClose 连接关闭的回调
 */
export function chatWithMultimodal(memoryId, message, files, onMessage, onError, onClose) {
    if (!files || files.length === 0) {
        // 如果没有文件，降级使用普通的 SSE GET 请求
        return chatWithSSE(memoryId, message, onMessage, onError, onClose)
    }

    // 如果有文件，使用 POST 请求处理多模态数据
    const formData = new FormData()
    formData.append('memoryId', memoryId)
    formData.append('message', message)
    files.forEach(file => {
        formData.append('images', file)
    })

    const controller = new AbortController()
    
    fetch(`${API_BASE_URL}/ai/chat/multimodal`, {
        method: 'POST',
        body: formData,
        signal: controller.signal
    }).then(async response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        
        try {
            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                
                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                
                // 保留最后一行，因为它可能是不完整的
                buffer = lines.pop() || ''
                
                for (const line of lines) {
                    const trimmedLine = line.trim()
                    if (trimmedLine.startsWith('data:')) {
                        const data = trimmedLine.substring(5).trim()
                        if (data) onMessage(data)
                    }
                }
            }
            onClose && onClose()
        } catch (e) {
            if (e.name !== 'AbortError') {
                onError && onError(e)
            }
        }
    }).catch(err => {
        onError && onError(err)
    })

    return {
        close: () => controller.abort()
    }
}

/**
 * 使用 SSE 方式调用聊天接口
 * @param {number} memoryId 聊天室ID
 * @param {string} message 用户消息
 * @param {Function} onMessage 接收消息的回调函数
 * @param {Function} onError 错误处理回调函数
 * @param {Function} onClose 连接关闭回调函数
 * @returns {EventSource} 返回 EventSource 对象，用于手动关闭连接
 */
export function chatWithSSE(memoryId, message, onMessage, onError, onClose) {
    // 构建URL参数
    const params = new URLSearchParams({
        memoryId: memoryId,
        message: message
    })
    
    // 创建 EventSource 连接
    const eventSource = new EventSource(`${API_BASE_URL}/ai/chat?${params}`)
    
    // 处理接收到的消息
    eventSource.onmessage = function(event) {
        try {
            const data = event.data
            if (data && data.trim() !== '') {
                onMessage(data)
            }
        } catch (error) {
            console.error('解析消息失败:', error)
            onError && onError(error)
        }
    }
    
    // 处理错误
    eventSource.onerror = function(error) {
        // SSE 规范：当连接中断时，浏览器会自动尝试重新连接
        // 这会触发 onerror 事件，但 readyState 会变为 CONNECTING
        // 在 AI 聊天场景中，通常后端发送完数据就会关闭连接，导致触发此事件
        if (eventSource.readyState === EventSource.CONNECTING) {
            console.log('SSE 连接正常结束（尝试重连中，手动关闭）')
            eventSource.close()
            onClose && onClose()
        } else {
            console.error('SSE 连接发生错误:', error)
            onError && onError(error)
            eventSource.close()
        }
    }
    
    // 处理连接关闭
    eventSource.onclose = function() {
        console.log('SSE 连接已关闭')
        onClose && onClose()
    }
    
    return eventSource
}

/**
 * 检查后端服务是否可用
 * @returns {Promise<boolean>} 返回服务是否可用
 */
export async function checkServiceHealth() {
    try {
        const response = await axios.get(`${API_BASE_URL}/health`, {
            timeout: 5000
        })
        return response.status === 200
    } catch (error) {
        console.error('服务健康检查失败:', error)
        return false
    }
} 