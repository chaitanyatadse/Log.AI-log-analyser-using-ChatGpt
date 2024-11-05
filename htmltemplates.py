# CSS Styling
css = """
<style>
body {
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    color: #333;
}
h3 {
    font-size: 24px;
    color: #4CAF50;
}
button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 8px;
}
button:hover {
    background-color: #45a049;
}
.chat-container {
    max-width: 800px; /* Adjusted max-width */
    margin: 0 auto;
    padding: 20px;
    background-color: #f0f0f0; /* Changed background color */
    border-radius: 20px; /* Increased border radius */
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
 
.chat-message {
    padding: 1rem;
    border-radius: 1rem; /* Increased border radius */
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
}
 
.chat-message.user {
    background-color: #ffffff; /* Changed background color */
    border: 1px solid #dddddd; /* Changed border color */
}
 
.chat-message.bot {
    background-color: #e0e0e0; /* Changed background color */
}
 
.chat-message .avatar {
    flex: 0 0 auto;
    margin-right: 1rem;
    width: 60px;
    height: 60px;
    overflow: hidden;
    border-radius: 50%;
}
 
.chat-message .avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
 
.chat-message .message {
    flex: 1;
    padding: 0 1.5rem;
    color: #333333; /* Changed text color */
}
</style>
"""

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        🤖
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        🧑🏻‍💻
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''