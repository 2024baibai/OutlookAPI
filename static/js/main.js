// 主要JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initializeFormHandlers();
    initializeTableFeatures();
    initializeAlerts();
    initializeFileUpload();
});

// 表单处理器初始化
function initializeFormHandlers() {
    // 为所有表单添加加载状态
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // 3秒后恢复按钮状态（防止用户等待过久）
                setTimeout(() => {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    });
}

// 表格功能初始化
function initializeTableFeatures() {
    // 添加表格排序功能
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            if (index < headers.length - 1) { // 不对操作列添加排序
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => sortTable(table, index));
            }
        });
    });
    
    // 添加行高亮功能
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', function() {
            // 移除其他行的高亮
            tableRows.forEach(r => r.classList.remove('row-selected'));
            // 添加当前行高亮
            this.classList.add('row-selected');
        });
    });
}

// 提示框自动消失
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // 5秒后自动消失
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }, 5000);
        
        // 添加关闭按钮
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = `
            position: absolute;
            top: 10px;
            right: 15px;
            font-size: 20px;
            cursor: pointer;
            color: inherit;
            opacity: 0.7;
        `;
        closeBtn.addEventListener('click', () => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        });
        alert.style.position = 'relative';
        alert.appendChild(closeBtn);
    });
}

// 文件上传功能增强
function initializeFileUpload() {
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // 显示文件信息
                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';
                fileInfo.innerHTML = `
                    <small class="small-text">
                        已选择文件: ${file.name} (${formatFileSize(file.size)})
                    </small>
                `;
                
                // 移除之前的文件信息
                const existingInfo = fileInput.parentNode.querySelector('.file-info');
                if (existingInfo) {
                    existingInfo.remove();
                }
                
                fileInput.parentNode.appendChild(fileInfo);
                
                // 验证文件类型
                const allowedTypes = ['.txt', '.csv'];
                const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
                if (!allowedTypes.includes(fileExtension)) {
                    showNotification('请选择 .txt 或 .csv 格式的文件', 'warning');
                }
            }
        });
    }
}

// 表格排序功能
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // 获取当前排序方向
    const header = table.querySelectorAll('th')[columnIndex];
    const currentSort = header.getAttribute('data-sort') || 'asc';
    const newSort = currentSort === 'asc' ? 'desc' : 'asc';
    
    // 清除所有排序标记
    table.querySelectorAll('th').forEach(th => {
        th.removeAttribute('data-sort');
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // 设置新的排序标记
    header.setAttribute('data-sort', newSort);
    header.classList.add(`sort-${newSort}`);
    
    // 排序行
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        // 尝试数字排序
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return newSort === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // 文本排序
        return newSort === 'asc' 
            ? aText.localeCompare(bText)
            : bText.localeCompare(aText);
    });
    
    // 重新排列行
    rows.forEach(row => tbody.appendChild(row));
}

// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;
    
    document.body.appendChild(notification);
    
    // 自动消失
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 工具函数：格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 确认对话框增强
window.confirm = function(message) {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        `;
        
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            max-width: 400px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        `;
        
        dialog.innerHTML = `
            <p style="margin-bottom: 20px; font-size: 16px; color: #333;">${message}</p>
            <button id="confirmYes" class="btn btn-danger" style="margin-right: 10px;">确定</button>
            <button id="confirmNo" class="btn">取消</button>
        `;
        
        modal.appendChild(dialog);
        document.body.appendChild(modal);
        
        document.getElementById('confirmYes').onclick = () => {
            document.body.removeChild(modal);
            resolve(true);
        };
        
        document.getElementById('confirmNo').onclick = () => {
            document.body.removeChild(modal);
            resolve(false);
        };
        
        modal.onclick = (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
                resolve(false);
            }
        };
    });
};

// 添加CSS样式
const style = document.createElement('style');
style.textContent = `
    .row-selected {
        background-color: #e3f2fd !important;
    }
    
    .sort-asc::after {
        content: ' ↑';
        color: #007bff;
    }
    
    .sort-desc::after {
        content: ' ↓';
        color: #007bff;
    }
    
    .file-info {
        margin-top: 5px;
    }
`;
document.head.appendChild(style);
