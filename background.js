const BACKEND_URL = "http://localhost:8080/check-url";

const STATUS_MAP = {
  LEGITIMATE: { text: "SAFE", color: "#2E7D32" },
  SUSPICIOUS: { text: "WARN", color: "#F9A825" },
  PHISHING: { text: "RISK", color: "#C62828" },
  OFFLINE: { text: "OFF", color: "#616161" },
};

const cache = new Map();

function setBadge(statusKey) {
  const badge = STATUS_MAP[statusKey] || STATUS_MAP.OFFLINE;
  chrome.action.setBadgeText({ text: badge.text });
  chrome.action.setBadgeBackgroundColor({ color: badge.color });
}

async function checkUrl(tabId, url) {
  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    cache.set(tabId, { data, ts: Date.now(), offline: false });

    const verdict = data.finalVerdict || "SUSPICIOUS";
    if (STATUS_MAP[verdict]) {
      setBadge(verdict);
    } else {
      setBadge("OFFLINE");
    }

    return { data, offline: false };
  } catch (error) {
    cache.set(tabId, { data: null, ts: Date.now(), offline: true });
    setBadge("OFFLINE");
    return { data: null, offline: true, error: String(error) };
  }
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete") {
    return;
  }

  const url = tab.url || "";
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    return;
  }

  checkUrl(tabId, url);
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === "GET_STATUS") {
    const tabId = message.tabId;
    const cached = cache.get(tabId);
    if (cached) {
      sendResponse({ ok: true, ...cached });
      return true;
    }

    if (message.url) {
      checkUrl(tabId, message.url).then((result) => sendResponse({ ok: true, ...result }));
      return true;
    }

    sendResponse({ ok: false, offline: true, error: "No URL available" });
    return true;
  }

  return false;
});
