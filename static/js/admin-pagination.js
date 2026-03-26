// AJAX 分页管理器
class EmailPagination {
    constructor() {
        this.currentPage = 1;
        this.perPage = 20;
        this.init();
    }
    
    init() {
        // 从 URL 读取初始页码
        const urlParams = new URLSearchParams(window.location.search);
        this.currentPage = parseInt(urlParams.get('page')) || 1;
        
        // 加载数据
        this.loadEmails(this.currentPage);
        
        // 监听浏览器前进/后退
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.page) {
                this.loadEmails(e.state.page, false);
            }
        });
    }
    
    async loadEmails(page, updateHistory = true) {
        this.currentPage = page;
        
        // 显示加载状态
        this.showLoading();
        
        try {
            const response = await fetch(`/admin/api/emails?page=${page}&per_page=${this.perPage}`);
            const result = await response.json();
            
            if (result.success) {
                this.renderEmails(result.data);
                this.renderPagination(result.pagination);
                this.updateCountInfo(result.pagination);
                
                // 更新 URL（不刷新页面）
                if (updateHistory) {
                    const newUrl = `${window.location.pathname}?page=${page}`;
                    history.pushState({ page: page }, '', newUrl);
                }
                
                // 滚动到顶部
                const section = document.querySelector('.section');
                if (section) {
                    section.scrollIntoView({ behavior: 'smooth' });
                }
            } else {
                this.showError('加载失败，请刷新页面重试');
            }
        } catch (error) {
            console.error('加载邮箱列表失败:', error);
            this.showError('网络错误，请检查连接');
        } finally {
            this.hideLoading();
        }
    }
    
    renderEmails(emails) {
        const tbody = document.getElementById('email-table-body');
        
        if (!tbody) {
            console.error('找不到表格容器');
            return;
        }
        
        if (emails.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px;">
                        <p style="color: #999;">暂无邮箱数据，请上传邮箱文件。</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = emails.map(item => `
            <tr>
                <td>${this.escapeHtml(item.email)}</td>
                <td><span class="small-text">${this.escapeHtml(item.client_id)}</span></td>
                <td>
                    <span class="status-${item.status === 'valid' ? 'online' : item.status === 'expiring_soon' ? 'warning' : 'offline'}">
                        ${this.escapeHtml(item.status_text)}
                    </span>
                </td>
                <td>
                    ${item.expire_time ? 
                        `<span title="${this.escapeHtml(item.expire_time_full)}">${this.escapeHtml(item.expire_time)}</span>` : 
                        '<span class="small-text">未设置</span>'
                    }
                </td>
                <td>${this.escapeHtml(item.created_at)}</td>
                <td>
                    <div class="btn-group">
                        <form method="POST" action="/admin/refresh/${item.id}" class="inline-form">
                            <button type="submit" class="btn btn-success btn-sm">刷新令牌</button>
                        </form>
                        <button type="button" class="btn btn-info btn-sm" 
                                onclick="window.open('/api?email=${encodeURIComponent(item.email)}', '_blank')">查看邮箱</button>
                        <form method="POST" action="/admin/delete/${item.id}" 
                              class="inline-form" onsubmit="return confirm('确定删除这个邮箱吗？')">
                            <button type="submit" class="btn btn-danger btn-sm">删除</button>
                        </form>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    renderPagination(pagination) {
        const container = document.getElementById('email-pagination');
        
        if (!container) {
            console.error('找不到分页容器');
            return;
        }
        
        if (pagination.pages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        const start = (pagination.page - 1) * pagination.per_page + 1;
        const end = Math.min(pagination.page * pagination.per_page, pagination.total);
        
        let html = `
            <div class="pagination-info">
                显示 ${start} 到 ${end} 条，共 ${pagination.total} 条
            </div>
            <div class="pagination-controls">
        `;
        
        // 首页、上一页
        if (pagination.has_prev) {
            html += `
                <button class="btn btn-sm" onclick="emailPagination.loadEmails(1)">首页</button>
                <button class="btn btn-sm" onclick="emailPagination.loadEmails(${pagination.prev_num})">上一页</button>
            `;
        } else {
            html += `
                <span class="btn btn-sm disabled">首页</span>
                <span class="btn btn-sm disabled">上一页</span>
            `;
        }
        
        // 页码按钮
        const pages = this.getPageNumbers(pagination.page, pagination.pages);
        pages.forEach(pageNum => {
            if (pageNum === '...') {
                html += `<span class="ellipsis">...</span>`;
            } else if (pageNum === pagination.page) {
                html += `<span class="btn btn-sm active">${pageNum}</span>`;
            } else {
                html += `<button class="btn btn-sm" onclick="emailPagination.loadEmails(${pageNum})">${pageNum}</button>`;
            }
        });
        
        // 下一页、末页
        if (pagination.has_next) {
            html += `
                <button class="btn btn-sm" onclick="emailPagination.loadEmails(${pagination.next_num})">下一页</button>
                <button class="btn btn-sm" onclick="emailPagination.loadEmails(${pagination.pages})">末页</button>
            `;
        } else {
            html += `
                <span class="btn btn-sm disabled">下一页</span>
                <span class="btn btn-sm disabled">末页</span>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    getPageNumbers(current, total) {
        const pages = [];
        const showPages = 5; // 显示的页码数量
        
        if (total <= showPages + 2) {
            // 总页数较少，显示所有页码
            for (let i = 1; i <= total; i++) {
                pages.push(i);
            }
        } else {
            // 总页数较多，智能显示部分页码
            pages.push(1);
            
            let start = Math.max(2, current - 1);
            let end = Math.min(total - 1, current + 1);
            
            if (start > 2) pages.push('...');
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            if (end < total - 1) pages.push('...');
            
            pages.push(total);
        }
        
        return pages;
    }
    
    updateCountInfo(pagination) {
        const info = document.getElementById('email-count-info');
        if (info) {
            info.textContent = `(${pagination.total} 个，第 ${pagination.page} / ${pagination.pages} 页)`;
        }
    }
    
    showLoading() {
        const loadingEl = document.getElementById('email-loading');
        const containerEl = document.getElementById('email-list-container');
        
        if (loadingEl) loadingEl.style.display = 'block';
        if (containerEl) containerEl.style.opacity = '0.5';
    }
    
    hideLoading() {
        const loadingEl = document.getElementById('email-loading');
        const containerEl = document.getElementById('email-list-container');
        
        if (loadingEl) loadingEl.style.display = 'none';
        if (containerEl) containerEl.style.opacity = '1';
    }
    
    showError(message) {
        alert(message);
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 页面加载完成后初始化
let emailPagination;
document.addEventListener('DOMContentLoaded', function() {
    emailPagination = new EmailPagination();
});
