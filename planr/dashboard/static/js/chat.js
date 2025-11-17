const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const loading = document.getElementById('loading');
const saveChatBtn = document.getElementById('saveChatBtn');

let chatLog = [];

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

    let avatar;
    if (isUser) {
        avatar = document.createElement('img');
        avatar.className = 'message-avatar';
        avatar.src = window.USER_PROFILE_PIC;
        avatar.alt = 'Profile';
        avatar.style.width = '40px';
        avatar.style.height = '40px';
        avatar.style.objectFit = 'cover';
        avatar.style.borderRadius = '50%';
        avatar.style.border = '2px solid #eee';
    } else {
        avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🏛️';
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content;

    // Save chat log for export
    chatLog.push({
        role: isUser ? 'user' : 'assistant',
        content: content.replace(/<br>/g, '\n')
    });

    if (isUser) {
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(avatar);
    } else {
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
    }

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

async function sendMessage() {
    const query = userInput.value.trim();
    if (!query) return;
    addMessage(query, true);
    userInput.value = '';
    sendButton.disabled = true;
    loading.classList.add('show');
    try {
        const response = await fetch(window.CHAT_API_URL, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: query})
        });
        const data = await response.json();
        let formatted = data.answer.replace(/\n/g, '<br>');
        addMessage(formatted, false);
    } catch (error) {
        addMessage('Connection Failed. This is because the free tier of PythonAnywhere cannot handle an active LLM', false);
    } finally {
        sendButton.disabled = false;
        loading.classList.remove('show');
        userInput.focus();
    }
}

function askQuestion(question) {
    userInput.value = question;
    sendMessage();
}

if (userInput) userInput.focus();

// Save chat: export as text file
if (saveChatBtn) {
    saveChatBtn.addEventListener('click', function() {
        let text = chatLog.map(msg =>
            (msg.role === 'user' ? "You: " : "Planr AI: ") + msg.content + "\n"
        ).join('');
        let blob = new Blob([text], {type: "text/plain"});
        let url = URL.createObjectURL(blob);

        let a = document.createElement("a");
        a.href = url;
        a.download = "chat_session.txt";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}
