class MCPChat {
    constructor() {
        this.apiUrl = '/chat';
        this.clearUrl = '/clear';
        this.modelsUrl = '/api/models';
        this.selectModelUrl = '/api/models/select';
        this.onlineModeUrl = '/api/online-mode';
        this.responseModeUrl = '/api/response-mode';
        this.filesUrl = '/api/files';
        this.previewUrl = '/api/files/preview';
        this.downloadUrl = '/api/files';
        this.isLoading = false;
        
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.providerSelect = document.getElementById('providerSelect');
        this.modelSelect = document.getElementById('modelSelect');
        this.onlineModeToggle = document.getElementById('onlineModeToggle');
        this.onlineModeStatus = document.getElementById('onlineModeStatus');
        this.onlineModeToggleSidebar = document.getElementById('onlineModeToggleSidebar');
        this.onlineModeStatusSidebar = document.getElementById('onlineModeStatusSidebar');
        this.sidebar = document.getElementById('sidebar');
        this.toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
        this.historyList = document.getElementById('historyList');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.collapseBtn = document.getElementById('collapseBtn');
        this.themeToggleBtn = document.getElementById('themeToggleBtn');
        this.themeIcon = document.getElementById('themeIcon');
        this.responseModeSelect = document.getElementById('responseModeSelect');
        
        this.providers = [];
        this.currentProvider = '';
        this.currentModel = '';
        this.conversations = [];
        this.currentConversationId = null;
        this.currentTheme = 'light'; // 'light' 或 'dark'
        this.currentResponseMode = 'fast'; // 'fast' 或 'deep'
        this.files = []; // 存储文件列表
        
        this.init();
    }
    
    async init() {
        this.loadConversationsFromStorage();
        this.loadThemeFromStorage();
        this.loadResponseModeFromStorage();
        this.bindEvents();
        await this.loadModels();
        await this.loadOnlineMode();
        await this.loadResponseMode();
        this.renderHistoryList();
        
        if (this.conversations.length === 0) {
            this.createNewConversation();
        } else {
            this.loadConversation(this.conversations[0].id);
        }
    }

    bindEvents() {
        // 安全地添加事件监听器
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        if (this.messageInput) {
            this.messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearChat());
        }

        if (this.providerSelect) {
            this.providerSelect.addEventListener('change', () => this.onProviderChange());
        }
        if (this.modelSelect) {
            this.modelSelect.addEventListener('change', () => this.onModelChange());
        }
        
        if (this.onlineModeToggle) {
            this.onlineModeToggle.addEventListener('change', () => this.onOnlineModeChange());
        }
        if (this.onlineModeToggleSidebar) {
            this.onlineModeToggleSidebar.addEventListener('change', () => this.onOnlineModeChange());
        }
        
        if (this.toggleSidebarBtn) {
            this.toggleSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        }
        if (this.newChatBtn) {
            this.newChatBtn.addEventListener('click', () => this.createNewConversation());
        }
        if (this.collapseBtn) {
            this.collapseBtn.addEventListener('click', () => this.collapseSidebar());
        }
        
        if (this.themeToggleBtn) {
            this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
        }
        
        if (this.responseModeSelect) {
            this.responseModeSelect.addEventListener('change', () => this.onResponseModeChange());
        }
    }

    async loadModels() {
        try {
            const response = await fetch(this.modelsUrl);
            const data = await response.json();
            this.providers = data.providers || [];
            this.currentProvider = data.current?.provider || '';
            this.currentModel = data.current?.model || '';
            
            this.renderProviders();
        } catch (error) {
            console.error('加载模型失败:', error);
        }
    }
    
    async loadOnlineMode() {
        try {
            const response = await fetch(this.onlineModeUrl);
            const data = await response.json();
            this.onlineModeToggle.checked = data.enabled;
            this.updateOnlineModeStatus(data.enabled);
        } catch (error) {
            console.error('加载联网模式失败:', error);
        }
    }
    
    async loadResponseMode() {
        try {
            const response = await fetch(this.responseModeUrl);
            const data = await response.json();
            if (this.responseModeSelect) {
                this.responseModeSelect.value = data.current;
            }
            this.currentResponseMode = data.current;
        } catch (error) {
            console.error('加载响应模式失败:', error);
        }
    }
    
    async onOnlineModeChange() {
        try {
            const enabled = this.onlineModeToggle.checked;
            const response = await fetch(this.onlineModeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    enabled: enabled
                })
            });
            const data = await response.json();
            this.updateOnlineModeStatus(data.enabled);
        } catch (error) {
            console.error('切换联网模式失败:', error);
        }
    }
    
    updateOnlineModeStatus(enabled) {
        if (this.onlineModeStatus) {
            this.onlineModeStatus.textContent = enabled ? '启用' : '禁用';
            this.onlineModeStatus.style.color = enabled ? '#4ade80' : '#ef4444';
        }
        if (this.onlineModeToggleSidebar) {
            this.onlineModeToggleSidebar.checked = enabled;
        }
        if (this.onlineModeStatusSidebar) {
            this.onlineModeStatusSidebar.textContent = enabled ? '启用' : '禁用';
            this.onlineModeStatusSidebar.style.color = enabled ? '#4ade80' : '#ef4444';
        }
    }
    
    createNewConversation() {
        const conversationId = Date.now().toString();
        const conversation = {
            id: conversationId,
            title: '新对话',
            messages: [],
            createdAt: new Date().toISOString()
        };
        
        this.conversations.unshift(conversation);
        this.saveConversationsToStorage();
        this.loadConversation(conversationId);
        this.renderHistoryList();
    }
    
    loadConversation(conversationId) {
        const conversation = this.conversations.find(c => c.id === conversationId);
        if (!conversation) return;
        
        this.currentConversationId = conversationId;
        
        // 安全检查
        if (!this.messagesContainer) {
            console.error('messagesContainer 未找到');
            return;
        }
        
        this.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="message assistant">
                    <div class="avatar">🤖</div>
                    <div class="message-content">
                        <p>你好！我是 MCP 智能体助手。</p>
                        <p>我可以帮你查询天气、搜索网络、写文件等。</p>
                        <p>试试看：说 "天气 上海" 或 "搜索 人工智能"</p>
                    </div>
                </div>
            </div>
        `;
        
        conversation.messages.forEach(msg => {
            this.addMessageToDOM(msg.text, msg.role, msg.toolUsed);
        });
        
        this.renderHistoryList();
    }
    
    saveMessage(text, role, toolUsed) {
        if (!this.currentConversationId) {
            this.createNewConversation();
        }
        
        const conversation = this.conversations.find(c => c.id === this.currentConversationId);
        if (conversation) {
            conversation.messages.push({
                text,
                role,
                toolUsed,
                timestamp: new Date().toISOString()
            });
            
            if (conversation.messages.length <= 2 && role === 'user') {
                conversation.title = text.substring(0, 30) + (text.length > 30 ? '...' : '');
            }
            
            this.saveConversationsToStorage();
            this.renderHistoryList();
        }
    }
    
    renderHistoryList() {
        this.historyList.innerHTML = '';
        
        this.conversations.forEach(conversation => {
            const item = document.createElement('div');
            item.className = `history-item ${conversation.id === this.currentConversationId ? 'active' : ''}`;
            
            const content = document.createElement('div');
            content.className = 'history-item-content';
            
            const title = document.createElement('div');
            title.className = 'history-item-title';
            title.textContent = conversation.title;
            
            const preview = document.createElement('div');
            preview.className = 'history-item-preview';
            const lastUserMessage = [...conversation.messages].reverse().find(m => m.role === 'user');
            preview.textContent = lastUserMessage ? lastUserMessage.text.substring(0, 40) + (lastUserMessage.text.length > 40 ? '...' : '') : '新对话';
            
            content.appendChild(title);
            content.appendChild(preview);
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.textContent = '🗑️';
            deleteBtn.title = '删除对话';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteConversation(conversation.id);
            });
            
            item.appendChild(content);
            item.appendChild(deleteBtn);
            
            content.addEventListener('click', () => this.loadConversation(conversation.id));
            
            this.historyList.appendChild(item);
        });
    }
    
    saveConversationsToStorage() {
        try {
            localStorage.setItem('mcp_conversations', JSON.stringify(this.conversations));
        } catch (error) {
            console.error('保存对话历史失败:', error);
        }
    }
    
    loadConversationsFromStorage() {
        try {
            const stored = localStorage.getItem('mcp_conversations');
            if (stored) {
                this.conversations = JSON.parse(stored);
            }
        } catch (error) {
            console.error('加载对话历史失败:', error);
            this.conversations = [];
        }
    }
    
    toggleSidebar() {
        this.sidebar.classList.toggle('collapsed');
    }
    
    collapseSidebar() {
        this.sidebar.classList.toggle('collapsed');
    }
    
    deleteConversation(conversationId) {
        if (!confirm('确定要删除这个对话吗？')) {
            return;
        }
        
        this.conversations = this.conversations.filter(c => c.id !== conversationId);
        this.saveConversationsToStorage();
        
        if (this.currentConversationId === conversationId) {
            if (this.conversations.length > 0) {
                this.loadConversation(this.conversations[0].id);
            } else {
                this.createNewConversation();
            }
        } else {
            this.renderHistoryList();
        }
    }
    
    // 主题切换功能
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        this.saveThemeToStorage();
    }
    
    applyTheme() {
        if (this.currentTheme === 'dark') {
            document.body.classList.add('dark-theme');
            if (this.themeIcon) {
                this.themeIcon.textContent = '☀️';
            }
        } else {
            document.body.classList.remove('dark-theme');
            if (this.themeIcon) {
                this.themeIcon.textContent = '🌙';
            }
        }
    }
    
    saveThemeToStorage() {
        try {
            localStorage.setItem('mcp_theme', this.currentTheme);
        } catch (error) {
            console.error('保存主题失败:', error);
        }
    }
    
    loadThemeFromStorage() {
        try {
            const stored = localStorage.getItem('mcp_theme');
            if (stored) {
                this.currentTheme = stored;
                this.applyTheme();
            }
        } catch (error) {
            console.error('加载主题失败:', error);
        }
    }
    
    // 响应模式切换功能
    async onResponseModeChange() {
        if (this.responseModeSelect) {
            this.currentResponseMode = this.responseModeSelect.value;
            this.saveResponseModeToStorage();
            
            // 同步到后端
            try {
                await fetch(this.responseModeUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        mode: this.currentResponseMode
                    })
                });
            } catch (error) {
                console.error('保存响应模式到服务器失败:', error);
            }
        }
    }
    
    saveResponseModeToStorage() {
        try {
            localStorage.setItem('mcp_response_mode', this.currentResponseMode);
        } catch (error) {
            console.error('保存响应模式失败:', error);
        }
    }
    
    loadResponseModeFromStorage() {
        try {
            const stored = localStorage.getItem('mcp_response_mode');
            if (stored) {
                this.currentResponseMode = stored;
                if (this.responseModeSelect) {
                    this.responseModeSelect.value = stored;
                }
            }
        } catch (error) {
            console.error('加载响应模式失败:', error);
        }
    }
    
    copyMessage(text) {
        navigator.clipboard.writeText(text).then(() => {
            // 可以添加一个提示，比如显示"已复制"
            console.log('消息已复制到剪贴板');
        }).catch(err => {
            console.error('复制失败:', err);
        });
    }
    
    editMessage(text) {
        if (this.messageInput) {
            this.messageInput.value = text;
            this.messageInput.focus();
            this.messageInput.scrollTop = this.messageInput.scrollHeight;
        }
    }

    renderProviders() {
        this.providerSelect.innerHTML = '';
        
        this.providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider.name;
            option.textContent = provider.display_name || provider.name;
            this.providerSelect.appendChild(option);
        });
        
        this.providerSelect.value = this.currentProvider;
        this.renderModels();
    }

    renderModels() {
        this.modelSelect.innerHTML = '';
        
        const provider = this.providers.find(p => p.name === this.providerSelect.value);
        if (provider && provider.models) {
            provider.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.display_name || model.id;
                option.title = model.description || '';
                this.modelSelect.appendChild(option);
            });
        }
        
        this.modelSelect.value = this.currentModel;
    }

    onProviderChange() {
        this.currentProvider = this.providerSelect.value;
        this.renderModels();
        this.onModelChange();
    }

    async onModelChange() {
        this.currentModel = this.modelSelect.value;
        
        if (this.currentProvider && this.currentModel) {
            try {
                await fetch(this.selectModelUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        provider: this.currentProvider,
                        model: this.currentModel
                    })
                });
            } catch (error) {
                console.error('切换模型失败:', error);
            }
        }
    }

    async sendMessage() {
        const text = this.messageInput.value.trim();
        if (!text || this.isLoading) {
            return;
        }

        this.addMessage(text, 'user');
        this.saveMessage(text, 'user', null);
        this.messageInput.value = '';
        this.isLoading = true;
        this.sendBtn.disabled = true;

        let thinkingDiv = null;
        
        try {
            // 如果是深度思考模式，先显示思考过程
            if (this.currentResponseMode === 'deep') {
                thinkingDiv = this.showThinkingProcess();
            } else {
                this.showLoading();
            }

            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    text,
                    response_mode: this.currentResponseMode 
                })
            });

            const data = await response.json();
            
            // 更新思考过程
            if (thinkingDiv && data.thinking_process) {
                this.updateThinkingProcess(thinkingDiv, data.thinking_process);
            }
            
            this.hideLoading();
            this.addMessage(data.response, 'assistant', data.toolUsed, data.tool_result, data.thinking_process);
            this.saveMessage(data.response, 'assistant', data.toolUsed);
            
            // 如果使用了文件相关工具，刷新文件列表
            if (data.toolUsed === 'word' || data.toolUsed === 'writer') {
                await this.refreshFiles();
            }
        } catch (error) {
            this.hideLoading();
            const errorMsg = '抱歉，发生错误，请稍后重试。';
            this.addMessage(errorMsg, 'assistant');
            this.saveMessage(errorMsg, 'assistant', null);
        } finally {
            this.isLoading = false;
            this.sendBtn.disabled = false;
        }
    }

    showThinkingProcess() {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.id = 'thinkingProcess';
        thinkingDiv.className = 'message assistant thinking-process';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = '🤖';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const thinkingHeader = document.createElement('div');
        thinkingHeader.className = 'thinking-header';
        thinkingHeader.innerHTML = '🧠 深度思考中...';
        
        const stepsContainer = document.createElement('div');
        stepsContainer.className = 'thinking-steps';
        stepsContainer.id = 'thinkingSteps';
        
        contentDiv.appendChild(thinkingHeader);
        contentDiv.appendChild(stepsContainer);
        
        thinkingDiv.appendChild(avatar);
        thinkingDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(thinkingDiv);
        this.scrollToBottom();
        
        return thinkingDiv;
    }

    updateThinkingProcess(thinkingDiv, steps) {
        const stepsContainer = document.getElementById('thinkingSteps');
        if (!stepsContainer) return;
        
        stepsContainer.innerHTML = '';
        
        steps.forEach((step, index) => {
            setTimeout(() => {
                const stepDiv = document.createElement('div');
                stepDiv.className = 'thinking-step';
                stepDiv.textContent = step;
                stepDiv.style.opacity = '0';
                stepDiv.style.transform = 'translateX(-10px)';
                stepDiv.style.transition = 'all 0.3s ease';
                stepsContainer.appendChild(stepDiv);
                
                // 触发动画
                requestAnimationFrame(() => {
                    stepDiv.style.opacity = '1';
                    stepDiv.style.transform = 'translateX(0)';
                });
                
                this.scrollToBottom();
            }, index * 200);
        });
    }

    addMessage(text, role, toolUsed, toolResult, thinkingProcess) {
        // 移除临时的思考过程展示
        const tempThinking = document.getElementById('thinkingProcess');
        if (tempThinking) {
            tempThinking.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = role === 'user' ? '👤' : '🤖';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // 如果是assistant且有思考过程，先展示思考过程
        if (role === 'assistant' && thinkingProcess && thinkingProcess.length > 0) {
            const thinkingSection = document.createElement('div');
            thinkingSection.className = 'thinking-section';
            
            const thinkingToggle = document.createElement('div');
            thinkingToggle.className = 'thinking-toggle';
            thinkingToggle.innerHTML = '🧠 查看思考过程';
            
            const thinkingContent = document.createElement('div');
            thinkingContent.className = 'thinking-content';
            thinkingContent.style.display = 'none';
            
            thinkingProcess.forEach(step => {
                const stepDiv = document.createElement('div');
                stepDiv.className = 'thinking-step';
                stepDiv.textContent = step;
                thinkingContent.appendChild(stepDiv);
            });
            
            thinkingToggle.addEventListener('click', () => {
                const isVisible = thinkingContent.style.display !== 'none';
                thinkingContent.style.display = isVisible ? 'none' : 'block';
                thinkingToggle.innerHTML = isVisible ? '🧠 查看思考过程' : '🧠 收起思考过程';
            });
            
            thinkingSection.appendChild(thinkingToggle);
            thinkingSection.appendChild(thinkingContent);
            contentDiv.appendChild(thinkingSection);
        }

        if (typeof text === 'string') {
            // 智能格式化文本
            const formattedContent = this.formatText(text);
            contentDiv.appendChild(formattedContent);
        } else {
            const pTag = document.createElement('p');
            pTag.textContent = JSON.stringify(text, null, 2);
            contentDiv.appendChild(pTag);
        }

        if (toolUsed) {
            const toolTag = document.createElement('span');
            toolTag.className = 'tool-used';
            toolTag.textContent = `🔧 使用工具: ${toolUsed}`;
            contentDiv.appendChild(toolTag);
        }
        
        // 如果是word或writer工具，添加文件信息
        if (toolResult && (toolUsed === 'word' || toolUsed === 'writer')) {
            const fileInfo = this.extractFileInfo(text, toolResult);
            if (fileInfo) {
                const fileCard = this.createFileCard(fileInfo);
                contentDiv.appendChild(fileCard);
            }
        }
        
        // 添加操作按钮
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        // 复制按钮
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.textContent = '📋';
        copyBtn.title = '复制';
        copyBtn.addEventListener('click', () => this.copyMessage(text));
        actionsDiv.appendChild(copyBtn);
        
        // 编辑按钮（只对用户消息显示）
        if (role === 'user') {
            const editBtn = document.createElement('button');
            editBtn.className = 'action-btn';
            editBtn.textContent = '✏️';
            editBtn.title = '重新编辑';
            editBtn.addEventListener('click', () => this.editMessage(text));
            actionsDiv.appendChild(editBtn);
        }
        
        contentDiv.appendChild(actionsDiv);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addMessageToDOM(text, role, toolUsed) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = role === 'user' ? '👤' : '🤖';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (typeof text === 'string') {
            // 智能格式化文本
            const formattedContent = this.formatText(text);
            contentDiv.appendChild(formattedContent);
        } else {
            const pTag = document.createElement('p');
            pTag.textContent = JSON.stringify(text, null, 2);
            contentDiv.appendChild(pTag);
        }

        if (toolUsed) {
            const toolTag = document.createElement('span');
            toolTag.className = 'tool-used';
            toolTag.textContent = `🔧 使用工具: ${toolUsed}`;
            contentDiv.appendChild(toolTag);
        }
        
        // 添加操作按钮
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        // 复制按钮
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.textContent = '📋';
        copyBtn.title = '复制';
        copyBtn.addEventListener('click', () => this.copyMessage(text));
        actionsDiv.appendChild(copyBtn);
        
        // 编辑按钮（只对用户消息显示）
        if (role === 'user') {
            const editBtn = document.createElement('button');
            editBtn.className = 'action-btn';
            editBtn.textContent = '✏️';
            editBtn.title = '重新编辑';
            editBtn.addEventListener('click', () => this.editMessage(text));
            actionsDiv.appendChild(editBtn);
        }
        
        contentDiv.appendChild(actionsDiv);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
    }

    showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingMessage';
        loadingDiv.className = 'message assistant';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = '🤖';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = '<div class="loading"><span></span><span></span><span></span></div>';
        
        loadingDiv.appendChild(avatar);
        loadingDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(loadingDiv);
        this.scrollToBottom();
    }

    hideLoading() {
        const loadingDiv = document.getElementById('loadingMessage');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    async clearChat() {
        try {
            await fetch(this.clearUrl, {
                method: 'POST'
            });
            this.createNewConversation();
        } catch (error) {
            console.error('清空失败:', error);
        }
    }

    scrollToBottom() {
        requestAnimationFrame(() => {
            const chatContainer = document.getElementById('chatContainer');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        });
    }
    
    formatText(text) {
        const container = document.createElement('div');
        
        // 先处理数字编号的列表 (1. 2. 3. 或 一、二、三等)
        let processedText = text
            .replace(/(\d+[.、]\s)/g, '\n$1')  // 确保数字编号前有换行
            .replace(/([一二三四五六七八九十]+[.、]\s)/g, '\n$1'); // 中文数字编号
        
        // 按行处理
        const lines = processedText.split('\n');
        let inList = false;
        let listElement = null;
        
        lines.forEach(line => {
            line = line.trim();
            if (!line) return;
            
            // 匹配数字编号 (1. 2. 等)
            const numberedMatch = line.match(/^(\d+)[.、]\s*(.+)$/);
            // 匹配中文数字编号 (一、 二、 等)
            const chineseNumberedMatch = line.match(/^([一二三四五六七八九十]+)[.、]\s*(.+)$/);
            // 匹配无序列表 (- 开头)
            const bulletMatch = line.match(/^[-*]\s*(.+)$/);
            // 匹配标题 (# 开头)
            const headingMatch = line.match(/^(#{1,3})\s*(.+)$/);
            
            if (headingMatch) {
                // 结束之前的列表
                if (listElement) {
                    container.appendChild(listElement);
                    listElement = null;
                    inList = false;
                }
                
                const headingLevel = headingMatch[1].length;
                const heading = document.createElement(`h${headingLevel}`);
                heading.textContent = headingMatch[2];
                container.appendChild(heading);
            } else if (numberedMatch || chineseNumberedMatch) {
                const content = numberedMatch ? numberedMatch[2] : chineseNumberedMatch[2];
                
                if (!inList) {
                    listElement = document.createElement('ol');
                    inList = true;
                }
                
                const li = document.createElement('li');
                li.textContent = content;
                listElement.appendChild(li);
            } else if (bulletMatch) {
                if (!inList) {
                    listElement = document.createElement('ul');
                    inList = true;
                }
                
                const li = document.createElement('li');
                li.textContent = bulletMatch[1];
                listElement.appendChild(li);
            } else {
                // 普通段落
                if (listElement) {
                    container.appendChild(listElement);
                    listElement = null;
                    inList = false;
                }
                
                // 处理文本中的加粗和斜体
                const formattedParagraph = this.formatParagraph(line);
                container.appendChild(formattedParagraph);
            }
        });
        
        // 添加最后一个列表
        if (listElement) {
            container.appendChild(listElement);
        }
        
        return container;
    }
    
    formatParagraph(text) {
        const p = document.createElement('p');
        let currentText = text;
        
        // 简单的格式化: **粗体**, *斜体*
        const boldRegex = /\*\*(.*?)\*\*/g;
        const italicRegex = /\*(.*?)\*/g;
        
        let lastIndex = 0;
        let match;
        
        // 处理粗体
        let parts = [];
        while ((match = boldRegex.exec(currentText)) !== null) {
            if (match.index > lastIndex) {
                parts.push({ type: 'text', content: currentText.slice(lastIndex, match.index) });
            }
            parts.push({ type: 'bold', content: match[1] });
            lastIndex = match.index + match[0].length;
        }
        if (lastIndex < currentText.length) {
            parts.push({ type: 'text', content: currentText.slice(lastIndex) });
        }
        
        // 处理斜体并构建DOM
        parts.forEach(part => {
            if (part.type === 'text') {
                let italicMatch;
                let italicLastIndex = 0;
                let italicParts = [];
                while ((italicMatch = italicRegex.exec(part.content)) !== null) {
                    if (italicMatch.index > italicLastIndex) {
                        italicParts.push({ type: 'text', content: part.content.slice(italicLastIndex, italicMatch.index) });
                    }
                    italicParts.push({ type: 'italic', content: italicMatch[1] });
                    italicLastIndex = italicMatch.index + italicMatch[0].length;
                }
                if (italicLastIndex < part.content.length) {
                    italicParts.push({ type: 'text', content: part.content.slice(italicLastIndex) });
                }
                
                italicParts.forEach(italicPart => {
                    if (italicPart.type === 'text') {
                        p.appendChild(document.createTextNode(italicPart.content));
                    } else if (italicPart.type === 'italic') {
                        const em = document.createElement('em');
                        em.textContent = italicPart.content;
                        p.appendChild(em);
                    }
                });
            } else if (part.type === 'bold') {
                const strong = document.createElement('strong');
                strong.textContent = part.content;
                p.appendChild(strong);
            }
        });
        
        return p;
    }

    // 文件相关函数
    extractFileInfo(text, toolResult) {
        let filename = null;
        
        // 尝试从工具结果中获取文件名
        if (toolResult) {
            if (typeof toolResult === 'object') {
                filename = toolResult.filename || toolResult.name || null;
                if (!filename && toolResult.filepath) {
                    filename = toolResult.filepath.split(/[\/\\]/).pop();
                }
            } else if (typeof toolResult === 'string') {
                // 尝试从字符串中提取文件名
                const match = toolResult.match(/(?:文件名|文件|文档)[:：]\s*([^\s，。]+)/i);
                if (match) {
                    filename = match[1];
                }
            }
        }
        
        // 如果没有找到，尝试从文本中提取
        if (!filename) {
            const docxMatch = text.match(/(\w+\.docx)/i);
            const txtMatch = text.match(/(\w+\.txt)/i);
            if (docxMatch) {
                filename = docxMatch[1];
            } else if (txtMatch) {
                filename = txtMatch[1];
            }
        }
        
        if (filename) {
            return {
                name: filename,
                type: filename.endsWith('.docx') ? 'docx' : 'text'
            };
        }
        
        return null;
    }

    createFileCard(fileInfo) {
        const card = document.createElement('div');
        card.className = 'file-card';
        
        const icon = document.createElement('span');
        icon.className = 'file-icon';
        icon.textContent = fileInfo.type === 'docx' ? '📄' : '📝';
        
        const nameDiv = document.createElement('div');
        nameDiv.className = 'file-name';
        nameDiv.textContent = fileInfo.name;
        
        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'file-buttons';
        
        const previewBtn = document.createElement('button');
        previewBtn.className = 'file-btn preview-btn';
        previewBtn.textContent = '👁️ 预览';
        previewBtn.addEventListener('click', () => this.previewFile(fileInfo.name));
        
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'file-btn download-btn';
        downloadBtn.textContent = '⬇️ 下载';
        downloadBtn.addEventListener('click', () => this.downloadFile(fileInfo.name));
        
        buttonsDiv.appendChild(previewBtn);
        buttonsDiv.appendChild(downloadBtn);
        
        card.appendChild(icon);
        card.appendChild(nameDiv);
        card.appendChild(buttonsDiv);
        
        return card;
    }

    async refreshFiles() {
        try {
            const response = await fetch(this.filesUrl);
            const data = await response.json();
            this.files = data.files || [];
        } catch (error) {
            console.error('刷新文件列表失败:', error);
        }
    }

    async previewFile(filename) {
        try {
            const response = await fetch(`${this.previewUrl}/${encodeURIComponent(filename)}`);
            const data = await response.json();
            
            // 创建预览模态框
            this.showPreviewModal(data);
        } catch (error) {
            console.error('预览文件失败:', error);
            alert('预览文件失败，请尝试下载查看');
        }
    }

    showPreviewModal(data) {
        // 检查是否已存在模态框
        let modal = document.getElementById('preview-modal');
        if (modal) {
            modal.remove();
        }
        
        modal = document.createElement('div');
        modal.id = 'preview-modal';
        modal.className = 'preview-modal';
        
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.addEventListener('click', () => modal.remove());
        
        const content = document.createElement('div');
        content.className = 'modal-content';
        
        const header = document.createElement('div');
        header.className = 'modal-header';
        
        const title = document.createElement('h3');
        title.textContent = `预览: ${data.name}`;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'modal-close';
        closeBtn.textContent = '✕';
        closeBtn.addEventListener('click', () => modal.remove());
        
        header.appendChild(title);
        header.appendChild(closeBtn);
        
        const body = document.createElement('div');
        body.className = 'modal-body';
        
        const previewContent = document.createElement('div');
        previewContent.className = 'preview-content';
        
        if (data.type === 'text' || data.type === 'docx') {
            const pre = document.createElement('pre');
            pre.textContent = data.content;
            previewContent.appendChild(pre);
        } else {
            const p = document.createElement('p');
            p.textContent = data.content || '该文件类型不支持预览';
            previewContent.appendChild(p);
        }
        
        body.appendChild(previewContent);
        
        const footer = document.createElement('div');
        footer.className = 'modal-footer';
        
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn-primary';
        downloadBtn.textContent = '下载文件';
        downloadBtn.addEventListener('click', () => {
            this.downloadFile(data.name);
            modal.remove();
        });
        
        footer.appendChild(downloadBtn);
        
        content.appendChild(header);
        content.appendChild(body);
        content.appendChild(footer);
        
        modal.appendChild(overlay);
        modal.appendChild(content);
        
        document.body.appendChild(modal);
    }

    downloadFile(filename) {
        window.location.href = `${this.downloadUrl}/${encodeURIComponent(filename)}`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new MCPChat();
});
