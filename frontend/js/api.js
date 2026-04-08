// 后端基础地址（和Flask启动地址一致）
const BASE_URL = "http://127.0.0.1:5000";

// 注册接口
async function registerUser(username, email, password) {
    try {
        const response = await fetch(`${BASE_URL}/api/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, email, password }),
        });
        return await response.json();
    } catch (error) {
        console.error("注册失败：", error);
        return { success: false, message: "网络错误" };
    }
}

// 登录接口
async function loginUser(username, password) {
    try {
        const response = await fetch(`${BASE_URL}/api/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });
        return await response.json();
    } catch (error) {
        console.error("登录失败：", error);
        return { success: false, message: "网络错误" };
    }
}

// 获取文章列表接口
async function getPostList() {
    try {
        const response = await fetch(`${BASE_URL}/api/posts`);
        return await response.json();
    } catch (error) {
        console.error("获取文章失败：", error);
        return { success: false, message: "网络错误" };
    }
}

// 发布文章接口
async function publishPost(title, content, userId) {
    try {
        const response = await fetch(`${BASE_URL}/api/posts`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ title, content, user_id: userId }),
        });
        return await response.json();
    } catch (error) {
        console.error("发布文章失败：", error);
        return { success: false, message: "网络错误" };
    }
}