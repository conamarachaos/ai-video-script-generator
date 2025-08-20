// Debug version with extensive logging
$(document).ready(function() {
    let currentConversationId = null;
    let isProcessing = false;
    let lastFailedAction = null;
    
    console.log('App initialized');
    
    // Global event handler for all option buttons
    $(document).on('click', '.option-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('Option button clicked!');
        console.log('Button element:', this);
        console.log('Is processing?', isProcessing);
        console.log('Is disabled?', $(this).prop('disabled'));
        console.log('Has opacity-50?', $(this).hasClass('opacity-50'));
        
        // Check if we should process
        if (isProcessing) {
            console.log('Already processing, skipping');
            return false;
        }
        
        if ($(this).prop('disabled') || $(this).hasClass('opacity-50')) {
            console.log('Button is disabled, skipping');
            return false;
        }
        
        const optionValue = $(this).data('option-value');
        const optionId = $(this).data('option-id');
        const optionText = $(this).text();
        
        console.log('Option details:');
        console.log('  Value:', optionValue);
        console.log('  ID:', optionId);
        console.log('  Text:', optionText);
        
        // Visual feedback
        $(this).addClass('bg-violet-600 scale-95');
        
        // Disable all option buttons
        $('.option-btn').each(function() {
            $(this).prop('disabled', true)
                   .addClass('opacity-50 cursor-not-allowed');
            console.log('Disabled button:', $(this).data('option-id'));
        });
        
        // Send the message
        console.log('About to send message with option value:', optionValue);
        sendMessage(null, optionValue);
        
        return false;
    });
    
    // Load conversations on start
    loadConversations();
    
    // New chat button
    $('#newChatBtn').click(function() {
        console.log('New chat button clicked');
        currentConversationId = null;
        $('#messagesList').html('');
        $('.conversation-item').removeClass('bg-slate-800');
        sendInitialMessage();
    });
    
    function sendInitialMessage() {
        console.log('Sending initial message');
        const typingId = 'typing-' + Date.now();
        $('#messagesList').append(`
            <div id="${typingId}" class="flex gap-3">
                <div class="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-robot text-xs"></i>
                </div>
                <div class="flex-1 bg-slate-800 rounded-2xl px-4 py-3">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `);
        
        $.ajax({
            url: '/api/chat',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                message: '',
                conversation_id: null
            }),
            success: function(response) {
                console.log('Initial response received:', response);
                $('#' + typingId).remove();
                currentConversationId = response.conversation_id;
                addMessage('assistant', response.response, response.options);
                loadConversations();
            },
            error: function(xhr) {
                console.error('Initial message error:', xhr);
                $('#' + typingId).remove();
                addMessage('assistant', 'Welcome! Type /help to see available commands or click Start New Script to begin.');
            }
        });
    }
    
    // Auto-send initial message on page load
    setTimeout(function() {
        if ($('#messagesList').find('.text-center').length > 0) {
            $('#messagesList').html('');
            sendInitialMessage();
        }
    }, 500);
    
    // Send button
    $('#sendBtn').click(function() {
        console.log('Send button clicked');
        sendMessage();
    });
    
    // Enter key to send
    $('#messageInput').keydown(function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            console.log('Enter key pressed');
            sendMessage();
        }
    });
    
    function sendMessage(message = null, optionValue = null) {
        console.log('sendMessage called:', { message, optionValue, isProcessing });
        
        if (isProcessing) {
            console.log('Already processing, returning');
            return;
        }
        
        if (!message) {
            message = $('#messageInput').val().trim();
            if (!message && !optionValue) {
                console.log('No message or option value, returning');
                return;
            }
        }
        
        isProcessing = true;
        $('#sendBtn').prop('disabled', true);
        
        console.log('Sending to server:', { message, optionValue });
        
        // Clear welcome message if present
        if ($('#messagesList').find('.text-center').length > 0) {
            $('#messagesList').html('');
        }
        
        // Add user message
        if (message && !optionValue) {
            addMessage('user', message);
        } else if (optionValue) {
            const selectedText = $(`[data-option-value="${optionValue}"]`).text() || optionValue;
            console.log('Selected text:', selectedText);
            addMessage('user', `Selected: ${selectedText}`);
        }
        
        $('#messageInput').val('').css('height', 'auto');
        
        // Add typing indicator
        const typingId = 'typing-' + Date.now();
        $('#messagesList').append(`
            <div id="${typingId}" class="flex gap-3">
                <div class="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-robot text-xs"></i>
                </div>
                <div class="flex-1 bg-slate-800 rounded-2xl px-4 py-3">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `);
        scrollToBottom(true);
        
        // Send to server
        const requestData = {
            message: message || '',
            option_selected: optionValue,
            conversation_id: currentConversationId
        };
        
        console.log('Sending AJAX request:', requestData);
        
        $.ajax({
            url: '/api/chat',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(requestData),
            success: function(response) {
                console.log('Response received:', response);
                $('#' + typingId).remove();
                
                if (response.error) {
                    console.error('Server returned error:', response.error);
                    lastFailedAction = { message: message, optionValue: optionValue };
                    
                    Swal.fire({
                        title: 'AI Agent Error',
                        text: response.error,
                        icon: 'error',
                        confirmButtonText: '🔄 Retry',
                        background: '#1e293b',
                        color: '#f1f5f9',
                        confirmButtonColor: '#8b5cf6'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            setTimeout(() => {
                                sendMessage(message, optionValue);
                            }, 500);
                        }
                    });
                    
                    isProcessing = false;
                    $('#sendBtn').prop('disabled', false);
                    return;
                }
                
                lastFailedAction = null;
                addMessage('assistant', response.response, response.options);
                
                if (response.conversation_id && !currentConversationId) {
                    currentConversationId = response.conversation_id;
                    loadConversations();
                }
                
                isProcessing = false;
                $('#sendBtn').prop('disabled', false);
                $('#messageInput').focus();
                console.log('Message processing complete');
            },
            error: function(xhr) {
                console.error('AJAX error:', xhr);
                $('#' + typingId).remove();
                
                lastFailedAction = { message: message, optionValue: optionValue };
                
                let errorMessage = 'Unable to connect to the server.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }
                
                Swal.fire({
                    title: 'Connection Error',
                    text: errorMessage,
                    icon: 'error',
                    confirmButtonText: '🔄 Retry',
                    background: '#1e293b',
                    color: '#f1f5f9',
                    confirmButtonColor: '#8b5cf6'
                });
                
                isProcessing = false;
                $('#sendBtn').prop('disabled', false);
            }
        });
    }
    
    function addMessage(role, content, options = []) {
        console.log('Adding message:', { role, content, optionsCount: options.length });
        
        let messageHtml;
        const messageId = 'msg-' + Date.now();
        
        if (role === 'user') {
            messageHtml = `
                <div id="${messageId}" class="flex gap-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-violet-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-user text-xs"></i>
                    </div>
                    <div class="flex-1">
                        <div class="bg-slate-800 rounded-2xl px-4 py-3 inline-block">
                            <div>${escapeHtml(content)}</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            let optionsHtml = '';
            if (options && options.length > 0) {
                console.log('Creating option buttons for:', options);
                const optionButtons = options.map((opt, index) => {
                    console.log('Creating button:', opt);
                    const description = opt.description ? `<span class="text-xs text-slate-400 block pointer-events-none">${opt.description}</span>` : '';
                    return `
                        <button type="button" 
                                class="option-btn w-full text-left bg-slate-700 hover:bg-slate-600 transition-all rounded-lg px-4 py-3 group cursor-pointer"
                                data-option-value="${opt.value}"
                                data-option-id="${opt.id}">
                            <span class="block font-medium group-hover:text-violet-400 transition-colors pointer-events-none">${opt.label}</span>
                            ${description}
                        </button>
                    `;
                }).join('');
                
                optionsHtml = `
                    <div class="mt-4 space-y-2">
                        ${optionButtons}
                    </div>
                `;
            }
            
            messageHtml = `
                <div id="${messageId}" class="flex gap-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-robot text-xs"></i>
                    </div>
                    <div class="flex-1">
                        <div class="bg-slate-800/50 rounded-2xl px-4 py-3">
                            <div>${formatContent(content)}</div>
                            ${optionsHtml}
                        </div>
                    </div>
                </div>
            `;
        }
        
        $('#messagesList').append(messageHtml);
        
        // Log button status after adding to DOM
        setTimeout(() => {
            $('.option-btn').each(function() {
                console.log('Button in DOM:', {
                    id: $(this).data('option-id'),
                    value: $(this).data('option-value'),
                    disabled: $(this).prop('disabled'),
                    text: $(this).text()
                });
            });
        }, 100);
        
        scrollToBottom(true);
    }
    
    function loadConversations() {
        $.get('/api/conversations', function(conversations) {
            const html = conversations.map(conv => `
                <div class="conversation-item cursor-pointer hover:bg-slate-800 rounded-lg p-3 transition-colors ${conv.id === currentConversationId ? 'bg-slate-800' : ''}" 
                     data-id="${conv.id}">
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex-1 min-w-0">
                            <div class="text-sm font-medium truncate">${escapeHtml(conv.title)}</div>
                            <div class="text-xs text-slate-500">${formatDate(conv.updated_at)}</div>
                        </div>
                        <button class="delete-conv opacity-0 hover:opacity-100 text-slate-500 hover:text-red-400 transition-all" data-id="${conv.id}">
                            <i class="fas fa-trash text-xs"></i>
                        </button>
                    </div>
                </div>
            `).join('');
            
            $('#conversationsList').html(html || '<div class="text-center text-slate-500 text-sm">No conversations yet</div>');
            
            $('.conversation-item').click(function(e) {
                if ($(e.target).closest('.delete-conv').length) return;
                const convId = $(this).data('id');
                loadConversation(convId);
            });
            
            $('.delete-conv').click(function(e) {
                e.stopPropagation();
                const convId = $(this).data('id');
                
                Swal.fire({
                    title: 'Delete Conversation?',
                    text: "This action cannot be undone!",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#ef4444',
                    cancelButtonColor: '#64748b',
                    confirmButtonText: 'Yes, delete it',
                    background: '#1e293b',
                    color: '#f1f5f9'
                }).then((result) => {
                    if (result.isConfirmed) {
                        $.ajax({
                            url: `/api/conversation/${convId}`,
                            method: 'DELETE',
                            success: function() {
                                if (convId === currentConversationId) {
                                    $('#newChatBtn').click();
                                }
                                loadConversations();
                            }
                        });
                    }
                });
            });
        });
    }
    
    function loadConversation(conversationId) {
        currentConversationId = conversationId;
        $('.conversation-item').removeClass('bg-slate-800');
        $(`.conversation-item[data-id="${conversationId}"]`).addClass('bg-slate-800');
        
        $.get(`/api/conversation/${conversationId}/messages`, function(messages) {
            $('#messagesList').html('');
            messages.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
        });
    }
    
    function scrollToBottom(smooth = false) {
        const container = $('#messagesContainer');
        if (smooth) {
            container.animate({
                scrollTop: container[0].scrollHeight
            }, 400);
        } else {
            container.scrollTop(container[0].scrollHeight);
        }
    }
    
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
    
    function formatContent(content) {
        let formatted = escapeHtml(content);
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/`(.*?)`/g, '<code class="bg-slate-700 px-1 py-0.5 rounded">$1</code>');
        formatted = formatted.replace(/\n/g, '<br>');
        return formatted;
    }
    
    function formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return Math.floor(diff / 60000) + ' min ago';
        if (diff < 86400000) return Math.floor(diff / 3600000) + ' hours ago';
        if (diff < 604800000) return Math.floor(diff / 86400000) + ' days ago';
        
        return date.toLocaleDateString();
    }
});