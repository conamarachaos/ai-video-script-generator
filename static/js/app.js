$(document).ready(function() {
    let currentConversationId = null;
    let isProcessing = false;
    let lastFailedAction = null; // Store last failed action for retry
    
    // Set up global event delegation for option buttons
    // This ensures all dynamically added buttons work
    $(document).on('click', '.option-btn:not(:disabled)', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Check if already processing
        if (isProcessing) {
            console.log('Already processing, ignoring option click');
            return;
        }
        
        // Check if button is disabled
        if ($(this).prop('disabled') || $(this).hasClass('opacity-50')) {
            console.log('Button disabled, ignoring click');
            return;
        }
        
        const optionValue = $(this).data('option-value');
        const optionId = $(this).data('option-id');
        
        console.log('Global handler - Option clicked:', optionValue, 'ID:', optionId);
        
        // Visual feedback
        $(this).addClass('transform scale-95 bg-violet-600');
        
        // Disable all option buttons
        $('.option-btn').prop('disabled', true)
                       .addClass('opacity-50 cursor-not-allowed');
        
        // Send the option
        setTimeout(() => {
            sendMessage(null, optionValue);
        }, 150);
    });
    
    // Load conversations on start
    loadConversations();
    
    // New chat button
    $('#newChatBtn').click(function() {
        currentConversationId = null;
        $('#messagesList').html('');
        $('.conversation-item').removeClass('bg-slate-800');
        
        // Send initial message to get welcome screen
        sendInitialMessage();
    });
    
    // Send initial message when starting
    function sendInitialMessage() {
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
        
        // Send empty message to get initial greeting
        $.ajax({
            url: '/api/chat',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                message: '',
                conversation_id: null
            }),
            success: function(response) {
                $('#' + typingId).remove();
                currentConversationId = response.conversation_id;
                addMessage('assistant', response.response, response.options);
                loadConversations();
            },
            error: function() {
                $('#' + typingId).remove();
                addMessage('assistant', 'Welcome! Type /help to see available commands or click Start New Script to begin.');
            }
        });
    }
    
    // Auto-send initial message on page load if no conversations
    setTimeout(function() {
        if ($('#messagesList').find('.text-center').length > 0) {
            $('#messagesList').html('');
            sendInitialMessage();
        }
    }, 500);
    
    // Keyboard shortcut for retry (R key)
    $(document).keydown(function(e) {
        // Check if R key is pressed and no input is focused
        if (e.key === 'r' || e.key === 'R') {
            if (!$('#messageInput').is(':focus') && lastFailedAction && !isProcessing) {
                e.preventDefault();
                // Close any open alert first
                Swal.close();
                // Show retry confirmation
                Swal.fire({
                    title: 'Retry Last Action?',
                    text: 'Retrying the failed operation...',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonText: '🔄 Yes, Retry',
                    cancelButtonText: 'Cancel',
                    background: '#1e293b',
                    color: '#f1f5f9',
                    confirmButtonColor: '#8b5cf6',
                    cancelButtonColor: '#64748b',
                    timer: 3000,
                    timerProgressBar: true
                }).then((result) => {
                    if (result.isConfirmed || result.dismiss === Swal.DismissReason.timer) {
                        sendMessage(lastFailedAction.message, lastFailedAction.optionValue);
                    }
                });
            }
        }
    });
    
    // Send message
    $('#sendBtn').click(sendMessage);
    
    // Enter key to send (Shift+Enter for new line)
    $('#messageInput').keydown(function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea
    $('#messageInput').on('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });
    
    function sendMessage(message = null, optionValue = null) {
        if (isProcessing) {
            console.log('Already processing, skipping...');
            return;
        }
        
        // Use provided message or get from input
        if (!message) {
            message = $('#messageInput').val().trim();
            if (!message && !optionValue) return;
        }
        
        isProcessing = true;
        $('#sendBtn').prop('disabled', true);
        console.log('Sending message:', message, 'Option:', optionValue);
        
        // Clear welcome message if present
        if ($('#messagesList').find('.text-center').length > 0) {
            $('#messagesList').html('');
        }
        
        // Add user message (only if it's text, not an option click)
        if (message && !optionValue) {
            addMessage('user', message);
        } else if (optionValue) {
            // Show which option was selected
            const selectedText = $(`[data-option-value="${optionValue}"]`).text() || optionValue;
            addMessage('user', `Selected: ${selectedText}`);
        }
        
        // Clear input
        $('#messageInput').val('').css('height', 'auto');
        
        // Add typing indicator with fade in
        const typingId = 'typing-' + Date.now();
        $('#messagesList').append(`
            <div id="${typingId}" class="flex gap-3 message-animate">
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
        $.ajax({
            url: '/api/chat',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                message: message || '',
                option_selected: optionValue,
                conversation_id: currentConversationId
            }),
            success: function(response) {
                console.log('Response received:', response);
                // Remove typing indicator
                $('#' + typingId).remove();
                
                // Check for agent errors in response
                if (response.error) {
                    // Store failed action for retry
                    lastFailedAction = { message: message, optionValue: optionValue };
                    
                    Swal.fire({
                        title: 'AI Agent Error',
                        text: response.error,
                        icon: 'error',
                        showCancelButton: true,
                        confirmButtonText: '🔄 Retry',
                        cancelButtonText: 'Cancel',
                        background: '#1e293b',
                        color: '#f1f5f9',
                        confirmButtonColor: '#8b5cf6',
                        cancelButtonColor: '#64748b',
                        footer: '<span style="color: #94a3b8">Press R to retry</span>'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            // Retry the last action
                            setTimeout(() => {
                                sendMessage(message, optionValue);
                            }, 500);
                        }
                    });
                    
                    isProcessing = false;
                    $('#sendBtn').prop('disabled', false);
                    return;
                }
                
                // Clear failed action on success
                lastFailedAction = null;
                
                // Add assistant message with options
                addMessage('assistant', response.response, response.options);
                
                // Update conversation ID
                if (response.conversation_id && !currentConversationId) {
                    currentConversationId = response.conversation_id;
                    loadConversations();
                }
                
                isProcessing = false;
                $('#sendBtn').prop('disabled', false);
                $('#messageInput').focus();
                console.log('Processing complete');
            },
            error: function(xhr) {
                $('#' + typingId).remove();
                
                // Store failed action for retry
                lastFailedAction = { message: message, optionValue: optionValue };
                
                let errorMessage = 'Unable to connect to the server. Please try again.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }
                
                Swal.fire({
                    title: 'Connection Error',
                    text: errorMessage,
                    icon: 'error',
                    showCancelButton: true,
                    confirmButtonText: '🔄 Retry',
                    cancelButtonText: 'Cancel',
                    background: '#1e293b',
                    color: '#f1f5f9',
                    confirmButtonColor: '#8b5cf6',
                    cancelButtonColor: '#64748b',
                    footer: '<span style="color: #94a3b8">Press R to retry</span>'
                }).then((result) => {
                    if (result.isConfirmed) {
                        // Retry the last action
                        setTimeout(() => {
                            sendMessage(message, optionValue);
                        }, 500);
                    }
                });
                
                isProcessing = false;
                $('#sendBtn').prop('disabled', false);
                console.log('Error handling complete');
            }
        });
    }
    
    function addMessage(role, content, options = []) {
        let messageHtml;
        const messageId = 'msg-' + Date.now();
        
        if (role === 'user') {
            messageHtml = `
                <div id="${messageId}" class="flex gap-3 message-animate" style="opacity: 0;">
                    <div class="w-8 h-8 bg-gradient-to-br from-violet-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 new-message-indicator">
                        <i class="fas fa-user text-xs"></i>
                    </div>
                    <div class="flex-1">
                        <div class="bg-slate-800 rounded-2xl px-4 py-3 inline-block message-bubble">
                            <div class="message-content">${escapeHtml(content)}</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Build options HTML if provided
            let optionsHtml = '';
            if (options && options.length > 0) {
                const optionButtons = options.map((opt, index) => {
                    const description = opt.description ? `<span class="text-xs text-slate-400 block">${opt.description}</span>` : '';
                    return `
                        <button class="option-btn w-full text-left bg-slate-700 hover:bg-slate-600 transition-all rounded-lg px-4 py-3 group cursor-pointer"
                                type="button"
                                data-option-value="${opt.value}"
                                data-option-id="${opt.id}"
                                style="opacity: 0; animation-delay: ${0.1 * (index + 1)}s;">
                            <span class="block font-medium group-hover:text-violet-400 transition-colors pointer-events-none">${opt.label}</span>
                            ${description ? `<span class="pointer-events-none">${description}</span>` : ''}
                        </button>
                    `;
                }).join('');
                
                optionsHtml = `
                    <div class="mt-4 space-y-2 option-container" id="options-${messageId}">
                        ${optionButtons}
                    </div>
                `;
            }
            
            messageHtml = `
                <div id="${messageId}" class="flex gap-3 message-animate" style="opacity: 0;">
                    <div class="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center flex-shrink-0 new-message-indicator">
                        <i class="fas fa-robot text-xs"></i>
                    </div>
                    <div class="flex-1">
                        <div class="bg-slate-800/50 rounded-2xl px-4 py-3 message-bubble new-message-glow">
                            <div class="message-content">${formatContent(content)}</div>
                            ${optionsHtml}
                        </div>
                    </div>
                </div>
            `;
        }
        
        $('#messagesList').append(messageHtml);
        
        // Animate the message in
        setTimeout(() => {
            $('#' + messageId).css('opacity', '1');
            
            // Animate option buttons
            if (options && options.length > 0) {
                $('#' + messageId + ' .option-btn').each(function(index) {
                    const btn = $(this);
                    setTimeout(() => {
                        btn.css('opacity', '1').addClass('message-animate');
                    }, 100 * (index + 1));
                });
            }
        }, 50);
        
        // No need for additional handlers since we have global delegation
        // Just make sure buttons are visible after animation
        
        // Smooth scroll to bottom
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
            
            // Conversation click handler
            $('.conversation-item').click(function(e) {
                if ($(e.target).closest('.delete-conv').length) return;
                
                const convId = $(this).data('id');
                loadConversation(convId);
            });
            
            // Delete conversation handler with SweetAlert2
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
                    cancelButtonText: 'Cancel',
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
                                
                                Swal.fire({
                                    title: 'Deleted!',
                                    text: 'Conversation has been deleted.',
                                    icon: 'success',
                                    timer: 1500,
                                    showConfirmButton: false,
                                    background: '#1e293b',
                                    color: '#f1f5f9'
                                });
                            },
                            error: function() {
                                Swal.fire({
                                    title: 'Error!',
                                    text: 'Failed to delete conversation.',
                                    icon: 'error',
                                    background: '#1e293b',
                                    color: '#f1f5f9'
                                });
                            }
                        });
                    }
                });
            });
            
            // Show delete button on hover
            $('.conversation-item').hover(
                function() { $(this).find('.delete-conv').removeClass('opacity-0'); },
                function() { $(this).find('.delete-conv').addClass('opacity-0'); }
            );
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
            }, 400, 'swing');
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
        // Basic formatting for better display
        let formatted = escapeHtml(content);
        
        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* to <em> (but not if it's part of **bold**)
        formatted = formatted.replace(/(?<!\*)\*(?!\*)(.*?)\*(?!\*)/g, '<em>$1</em>');
        
        // Convert `code` to <code>
        formatted = formatted.replace(/`(.*?)`/g, '<code class="bg-slate-700 px-1 py-0.5 rounded">$1</code>');
        
        // Convert bullet points
        formatted = formatted.replace(/^\u2022 /gm, '<span class="ml-4">• </span>');
        formatted = formatted.replace(/^• /gm, '<span class="ml-4">• </span>');
        
        // Convert emoji codes if any
        formatted = formatted.replace(/:(\w+):/g, function(match, emoji) {
            const emojiMap = {
                'rocket': '🚀',
                'star': '⭐',
                'fire': '🔥',
                'heart': '❤️',
                'check': '✅',
                'bulb': '💡'
            };
            return emojiMap[emoji] || match;
        });
        
        // Convert line breaks
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