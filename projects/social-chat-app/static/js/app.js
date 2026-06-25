/**
 * 社交聊天应用前端
 */

class ChatApp {
    constructor() {
        this.ws = null;
        this.token = localStorage.getItem('token');
        this.currentUser = null;
        this.currentChat = null; // { type: 'user'|'group', id: number, name: string }
        this.friends = [];
        this.groups = [];
        this.messages = {};
        this.unreadCounts = {};

        this.init();
    }

    init() {
        this.bindEvents();

        // 检查是否已登录
        if (this.token) {
            this.connectWebSocket();
        }
    }

    bindEvents() {
        // 认证相关
        document.querySelectorAll('.auth-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchAuthTab(e.target.dataset.tab));
        });

        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });

        document.getElementById('register-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.register();
        });

        // 侧边栏标签
        document.querySelectorAll('.tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchSidebarTab(e.target.dataset.tab));
        });

        // 发送消息
        document.getElementById('btn-send').addEventListener('click', () => this.sendMessage());
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // 输入状态
        document.getElementById('message-input').addEventListener('input', () => {
            this.sendTypingStatus(true);
        });

        // 搜索
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });

        // 模态框
        document.getElementById('btn-add-friend').addEventListener('click', () => {
            this.showModal('add-friend-modal');
        });

        document.getElementById('btn-create-group').addEventListener('click', () => {
            this.showModal('create-group-modal');
        });

        document.querySelectorAll('.btn-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeModals());
        });

        // 搜索用户
        document.getElementById('search-user-input').addEventListener('input', (e) => {
            this.searchUsers(e.target.value);
        });

        // 创建群组
        document.getElementById('btn-confirm-create').addEventListener('click', () => {
            this.createGroup();
        });
    }

    // ==================== 认证相关 ====================

    switchAuthTab(tab) {
        document.querySelectorAll('.auth-tabs .tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });

        document.getElementById('login-form').classList.toggle('active', tab === 'login');
        document.getElementById('register-form').classList.toggle('active', tab === 'register');
        document.getElementById('auth-error').textContent = '';
    }

    async login() {
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.token;
                this.currentUser = data.user;
                localStorage.setItem('token', this.token);
                localStorage.setItem('user', JSON.stringify(this.currentUser));
                this.connectWebSocket();
            } else {
                this.showAuthError(data.error);
            }
        } catch (error) {
            this.showAuthError('登录失败，请重试');
        }
    }

    async register() {
        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const nickname = document.getElementById('reg-nickname').value;

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password, nickname })
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.token;
                this.currentUser = data.user;
                localStorage.setItem('token', this.token);
                localStorage.setItem('user', JSON.stringify(this.currentUser));
                this.connectWebSocket();
            } else {
                this.showAuthError(data.error);
            }
        } catch (error) {
            this.showAuthError('注册失败，请重试');
        }
    }

    showAuthError(message) {
        document.getElementById('auth-error').textContent = message;
    }

    // ==================== WebSocket相关 ====================

    connectWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws?token=${this.token}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket连接成功');
            this.showChatPage();
            this.loadFriends();
            this.loadGroups();
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket连接关闭');
            // 尝试重连
            setTimeout(() => {
                if (this.token) {
                    this.connectWebSocket();
                }
            }, 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
        };
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'new_message':
                this.handleNewMessage(data.message);
                break;
            case 'message_sent':
                this.handleMessageSent(data.message);
                break;
            case 'message_history':
                this.handleMessageHistory(data);
                break;
            case 'friends_list':
                this.handleFriendsList(data.friends);
                break;
            case 'online_users':
                this.handleOnlineUsers(data.users);
                break;
            case 'user_online':
                this.handleUserOnline(data);
                break;
            case 'user_offline':
                this.handleUserOffline(data);
                break;
            case 'typing':
                this.handleTyping(data);
                break;
            case 'read_receipt':
                this.handleReadReceipt(data);
                break;
            case 'friend_request':
                this.handleFriendRequest(data);
                break;
            case 'friend_request_sent':
                alert('好友请求已发送');
                this.closeModals();
                break;
            case 'friend_request_accepted':
                alert('好友请求已接受');
                this.loadFriends();
                break;
            case 'group_created':
                alert('群组创建成功');
                this.loadGroups();
                this.closeModals();
                break;
            case 'group_joined':
                this.loadGroups();
                break;
            case 'search_results':
                this.handleSearchResults(data);
                break;
            case 'error':
                alert(data.message);
                break;
        }
    }

    // ==================== UI相关 ====================

    showChatPage() {
        document.getElementById('auth-page').classList.remove('active');
        document.getElementById('chat-page').classList.add('active');

        if (this.currentUser) {
            document.getElementById('current-user').textContent =
                this.currentUser.nickname || this.currentUser.username;
        }
    }

    switchSidebarTab(tab) {
        document.querySelectorAll('.tabs .tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });

        document.getElementById('contacts-list').classList.toggle('active', tab === 'contacts');
        document.getElementById('groups-list').classList.toggle('active', tab === 'groups');
    }

    showModal(id) {
        document.getElementById(id).classList.remove('hidden');
    }

    closeModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    // ==================== 联系人相关 ====================

    loadFriends() {
        this.send({ type: 'get_friends' });
    }

    handleFriendsList(friends) {
        this.friends = friends;
        this.renderContacts();
    }

    renderContacts() {
        const container = document.getElementById('contacts-list');
        container.innerHTML = '';

        this.friends.forEach(friend => {
            const item = document.createElement('div');
            item.className = 'contact-item';
            item.dataset.userId = friend.id;

            if (this.currentChat && this.currentChat.type === 'user' && this.currentChat.id === friend.id) {
                item.classList.add('active');
            }

            const initial = (friend.nickname || friend.username).charAt(0).toUpperCase();
            const statusClass = friend.is_online ? 'online' : 'offline';
            const statusText = friend.is_online ? '在线' : '离线';

            item.innerHTML = `
                <div class="avatar">${initial}</div>
                <div class="contact-info">
                    <div class="contact-name">${friend.nickname || friend.username}</div>
                    <div class="contact-status ${statusClass}">${statusText}</div>
                </div>
                ${this.unreadCounts[friend.id] ? `<span class="unread-badge">${this.unreadCounts[friend.id]}</span>` : ''}
            `;

            item.addEventListener('click', () => this.openChat('user', friend.id, friend.nickname || friend.username));
            container.appendChild(item);
        });
    }

    // ==================== 群组相关 ====================

    loadGroups() {
        // 群组数据会在连接建立后通过其他方式获取
    }

    renderGroups() {
        const container = document.getElementById('groups-list');
        container.innerHTML = '';

        this.groups.forEach(group => {
            const item = document.createElement('div');
            item.className = 'group-item';
            item.dataset.groupId = group.id;

            if (this.currentChat && this.currentChat.type === 'group' && this.currentChat.id === group.id) {
                item.classList.add('active');
            }

            const initial = group.name.charAt(0).toUpperCase();

            item.innerHTML = `
                <div class="avatar">${initial}</div>
                <div class="group-info">
                    <div class="group-name">${group.name}</div>
                    <div class="contact-status">${group.member_count} 成员</div>
                </div>
            `;

            item.addEventListener('click', () => this.openChat('group', group.id, group.name));
            container.appendChild(item);
        });
    }

    // ==================== 聊天相关 ====================

    openChat(type, id, name) {
        this.currentChat = { type, id, name };

        // 更新UI
        document.getElementById('chat-placeholder').classList.add('hidden');
        document.getElementById('chat-container').classList.remove('hidden');
        document.getElementById('chat-target-name').textContent = name;

        // 高亮选中的联系人/群组
        document.querySelectorAll('.contact-item, .group-item').forEach(item => {
            item.classList.remove('active');
        });

        if (type === 'user') {
            document.querySelector(`.contact-item[data-user-id="${id}"]`)?.classList.add('active');
            this.send({ type: 'get_messages', receiver_id: id });
        } else {
            document.querySelector(`.group-item[data-group-id="${id}"]`)?.classList.add('active');
            this.send({ type: 'get_messages', group_id: id });
            this.send({ type: 'join_group', group_id: id });
        }

        // 清除未读计数
        delete this.unreadCounts[id];
        this.renderContacts();
    }

    sendMessage() {
        const input = document.getElementById('message-input');
        const content = input.value.trim();

        if (!content || !this.currentChat) return;

        const message = {
            type: 'send_message',
            content: content
        };

        if (this.currentChat.type === 'user') {
            message.receiver_id = this.currentChat.id;
        } else {
            message.group_id = this.currentChat.id;
        }

        this.send(message);
        input.value = '';

        // 发送输入状态
        this.sendTypingStatus(false);
    }

    handleNewMessage(message) {
        const chatId = message.group_id || message.receiver_id;
        const isGroup = !!message.group_id;

        // 存储消息
        if (!this.messages[chatId]) {
            this.messages[chatId] = [];
        }
        this.messages[chatId].push(message);

        // 如果是当前聊天，渲染消息
        if (this.currentChat) {
            const currentId = this.currentChat.type === 'group' ? message.group_id : message.receiver_id;
            if (currentId === this.currentChat.id || message.sender_id === this.currentChat.id) {
                this.renderMessage(message);
                this.scrollToBottom();
            }
        }

        // 更新未读计数
        if (!this.currentChat || this.currentChat.id !== chatId) {
            this.unreadCounts[chatId] = (this.unreadCounts[chatId] || 0) + 1;
            this.renderContacts();
        }
    }

    handleMessageSent(message) {
        // 消息已发送确认
        console.log('消息已发送:', message);
    }

    handleMessageHistory(data) {
        const chatId = data.receiver_id || data.group_id;
        this.messages[chatId] = data.messages;
        this.renderMessages(data.messages);
    }

    renderMessages(messages) {
        const container = document.getElementById('messages-container');
        container.innerHTML = '';

        messages.forEach(msg => this.renderMessage(msg));
        this.scrollToBottom();
    }

    renderMessage(message) {
        const container = document.getElementById('messages-container');
        const isSent = message.sender_id === this.currentUser.id;

        const div = document.createElement('div');
        div.className = `message ${isSent ? 'sent' : 'received'}`;

        const senderName = isSent ? '' : `<div class="message-sender">${message.sender?.nickname || message.sender?.username || '未知用户'}</div>`;
        const time = new Date(message.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

        let contentHtml = '';
        if (message.message_type === 'text') {
            contentHtml = `<div class="message-bubble">${this.escapeHtml(message.content)}</div>`;
        } else if (message.message_type === 'file' || message.message_type === 'image') {
            contentHtml = `
                <div class="message-bubble">
                    <div class="message-file">
                        <span class="message-file-icon">${message.message_type === 'image' ? '🖼️' : '📄'}</span>
                        <div class="message-file-info">
                            <div class="message-file-name">${message.file_name || '文件'}</div>
                            <div class="message-file-size">${this.formatFileSize(message.file_size)}</div>
                        </div>
                    </div>
                </div>
            `;
        }

        div.innerHTML = `
            ${senderName}
            ${contentHtml}
            <div class="message-time">${time}</div>
        `;

        container.appendChild(div);
    }

    scrollToBottom() {
        const container = document.getElementById('messages-container');
        container.scrollTop = container.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatFileSize(bytes) {
        if (!bytes) return '';
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }

    // ==================== 输入状态 ====================

    sendTypingStatus(isTyping) {
        if (!this.currentChat) return;

        const data = {
            type: 'typing',
            is_typing: isTyping
        };

        if (this.currentChat.type === 'user') {
            data.receiver_id = this.currentChat.id;
        } else {
            data.group_id = this.currentChat.id;
        }

        this.send(data);
    }

    handleTyping(data) {
        const indicator = document.getElementById('typing-indicator');
        if (data.is_typing) {
            indicator.classList.remove('hidden');
            // 3秒后自动隐藏
            setTimeout(() => {
                indicator.classList.add('hidden');
            }, 3000);
        } else {
            indicator.classList.add('hidden');
        }
    }

    // ==================== 已读回执 ====================

    handleReadReceipt(data) {
        console.log(`用户 ${data.reader_id} 已读 ${data.count} 条消息`);
    }

    // ==================== 用户状态 ====================

    handleUserOnline(data) {
        const friend = this.friends.find(f => f.id === data.user_id);
        if (friend) {
            friend.is_online = true;
            this.renderContacts();
        }
    }

    handleUserOffline(data) {
        const friend = this.friends.find(f => f.id === data.user_id);
        if (friend) {
            friend.is_online = false;
            this.renderContacts();
        }
    }

    handleOnlineUsers(users) {
        console.log('在线用户:', users);
    }

    // ==================== 好友请求 ====================

    handleFriendRequest(data) {
        const request = data.request;
        const accept = confirm(`${request.from_user.nickname || request.from_user.username} 请求添加你为好友。${request.message ? '\n留言: ' + request.message : ''}\n\n是否接受？`);

        if (accept) {
            this.send({ type: 'accept_friend_request', request_id: request.id });
        } else {
            this.send({ type: 'reject_friend_request', request_id: request.id });
        }
    }

    // ==================== 搜索 ====================

    handleSearch(query) {
        if (query.length < 2) return;

        // 搜索消息
        this.send({ type: 'search_messages', query });
    }

    handleSearchResults(data) {
        console.log('搜索结果:', data);
        // 可以在这里显示搜索结果
    }

    async searchUsers(query) {
        if (query.length < 2) {
            document.getElementById('search-results').innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`, {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            const data = await response.json();
            this.renderSearchResults(data.users);
        } catch (error) {
            console.error('搜索用户失败:', error);
        }
    }

    renderSearchResults(users) {
        const container = document.getElementById('search-results');
        container.innerHTML = '';

        users.forEach(user => {
            if (user.id === this.currentUser.id) return;

            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.innerHTML = `
                <div>
                    <strong>${user.nickname || user.username}</strong>
                    <div style="font-size: 12px; color: #666;">${user.email}</div>
                </div>
                <button class="btn-add" data-user-id="${user.id}">添加</button>
            `;

            item.querySelector('.btn-add').addEventListener('click', () => {
                this.sendFriendRequest(user.id);
            });

            container.appendChild(item);
        });
    }

    sendFriendRequest(userId) {
        this.send({
            type: 'send_friend_request',
            to_user_id: userId,
            message: '请求添加好友'
        });
    }

    // ==================== 创建群组 ====================

    createGroup() {
        const name = document.getElementById('group-name').value.trim();
        const description = document.getElementById('group-desc').value.trim();

        if (!name) {
            alert('请输入群组名称');
            return;
        }

        this.send({
            type: 'create_group',
            name,
            description
        });
    }
}

// 启动应用
const app = new ChatApp();
