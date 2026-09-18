const commentsForm = document.querySelector("#comments-form");
const commentsList = document.querySelector("#comments-list");
const commentsStatus = document.querySelector("#comments-status");
const commentsSubmit = document.querySelector("#comments-submit");
const commentsHeading = document.querySelector(".comments-heading");

const COMMENTS_API_BASE = "https://acts-comments-api-production.up.railway.app";
const adminModeEnabled = new URLSearchParams(window.location.search).get("admin") === "1";
let adminToken = sessionStorage.getItem("actsAdminToken") || "";

function setStatus(message, isError = false) {
  if (!commentsStatus) return;
  commentsStatus.textContent = message;
  commentsStatus.classList.toggle("error", isError);
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("zh-Hant", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function showEmpty(message) {
  if (!commentsList) return;
  commentsList.replaceChildren();
  const empty = document.createElement("p");
  empty.className = "comments-empty";
  empty.textContent = message;
  commentsList.append(empty);
}

function setupAdminControls() {
  if (!adminModeEnabled || !commentsHeading) return;

  let adminBar = document.querySelector("#comments-admin-bar");
  if (!adminBar) {
    adminBar = document.createElement("div");
    adminBar.id = "comments-admin-bar";
    adminBar.className = "comments-admin-bar";

    const badge = document.createElement("span");
    badge.textContent = "管理模式";

    const button = document.createElement("button");
    button.type = "button";
    button.id = "comments-admin-toggle";
    button.className = "comments-admin-toggle";

    adminBar.append(badge, button);
    commentsHeading.append(adminBar);

    button.addEventListener("click", async () => {
      if (adminToken) {
        adminToken = "";
        sessionStorage.removeItem("actsAdminToken");
        updateAdminControls();
        await loadComments();
        setStatus("已退出管理模式。 ");
        return;
      }

      const supplied = window.prompt("輸入留言管理密碼：");
      if (!supplied) return;

      adminToken = supplied.trim();
      sessionStorage.setItem("actsAdminToken", adminToken);
      updateAdminControls();
      await loadComments();
      setStatus("管理模式已啟用。 ");
    });
  }

  updateAdminControls();
}

function updateAdminControls() {
  const button = document.querySelector("#comments-admin-toggle");
  if (!button) return;
  button.textContent = adminToken ? "退出管理" : "管理登入";
  button.classList.toggle("active", Boolean(adminToken));
}

async function deleteComment(comment) {
  if (!adminToken) return;

  const confirmed = window.confirm(`確定刪除「${comment.name || "訪客"}」的這則留言？`);
  if (!confirmed) return;

  try {
    const response = await fetch(`${COMMENTS_API_BASE}/api/comments/${comment.id}`, {
      method: "DELETE",
      headers: {
        "Accept": "application/json",
        "Authorization": `Bearer ${adminToken}`
      }
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 401) {
      adminToken = "";
      sessionStorage.removeItem("actsAdminToken");
      updateAdminControls();
      throw new Error("管理密碼錯誤，請重新登入。 ");
    }

    if (!response.ok) {
      throw new Error(data.error || "刪除留言失敗。 ");
    }

    setStatus("留言已刪除。 ");
    await loadComments();
  } catch (error) {
    setStatus(error.message || "刪除留言失敗。", true);
  }
}

function renderComments(comments) {
  if (!commentsList) return;
  commentsList.replaceChildren();

  if (!comments.length) {
    showEmpty("目前還沒有留言。成為第一個留下足跡的人。");
    return;
  }

  comments.forEach((comment) => {
    const article = document.createElement("article");
    article.className = "comment-card";

    const header = document.createElement("div");
    header.className = "comment-card-header";

    const name = document.createElement("strong");
    name.textContent = comment.name || "訪客";

    const time = document.createElement("time");
    time.dateTime = comment.created_at || "";
    time.textContent = formatDate(comment.created_at);

    const body = document.createElement("p");
    body.textContent = comment.message || "";

    header.append(name, time);
    article.append(header, body);

    if (adminModeEnabled && adminToken) {
      const actions = document.createElement("div");
      actions.className = "comment-admin-actions";

      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "comment-delete-btn";
      deleteButton.textContent = "刪除";
      deleteButton.addEventListener("click", () => deleteComment(comment));

      actions.append(deleteButton);
      article.append(actions);
    }

    commentsList.append(article);
  });
}

async function loadComments() {
  if (!commentsList) return;
  showEmpty("正在載入留言……");

  try {
    const response = await fetch(`${COMMENTS_API_BASE}/api/comments`, {
      headers: { "Accept": "application/json" },
      cache: "no-store"
    });
    if (!response.ok) throw new Error(`留言服務暫時不可用 (${response.status})`);
    const data = await response.json();
    renderComments(Array.isArray(data.comments) ? data.comments : []);
  } catch (error) {
    console.error(error);
    showEmpty("暫時無法載入留言，請稍後再試。");
  }
}

commentsForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(commentsForm);
  const name = String(formData.get("name") || "").trim();
  const message = String(formData.get("message") || "").trim();

  if (!name || !message) {
    setStatus("請填寫暱稱和留言內容。", true);
    return;
  }

  commentsSubmit.disabled = true;
  setStatus("正在送出……");

  try {
    const response = await fetch(`${COMMENTS_API_BASE}/api/comments`, {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name, message })
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "留言送出失敗。 ");

    commentsForm.reset();
    setStatus("留言已送出。 ");
    await loadComments();
  } catch (error) {
    setStatus(error.message || "留言送出失敗。", true);
  } finally {
    commentsSubmit.disabled = false;
  }
});

setupAdminControls();
loadComments();
