function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function setHidden(id, hidden) {
  document.getElementById(id).style.display = hidden ? "none" : "block";
}

function setStatusBadge(verdict) {
  const dot = document.getElementById("statusDot");
  const text = document.getElementById("statusText");

  if (verdict === "LEGITIMATE") {
    dot.className = "dot green";
    text.textContent = "SAFE";
  } else if (verdict === "SUSPICIOUS") {
    dot.className = "dot yellow";
    text.textContent = "WARN";
  } else if (verdict === "PHISHING") {
    dot.className = "dot red";
    text.textContent = "RISK";
  } else {
    dot.className = "dot gray";
    text.textContent = "OFF";
  }
}

function renderReasons(reasons) {
  const list = document.getElementById("reasonsList");
  list.innerHTML = "";
  if (!reasons || reasons.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No reasons provided";
    list.appendChild(li);
    return;
  }

  reasons.forEach((reason) => {
    const li = document.createElement("li");
    li.textContent = reason;
    list.appendChild(li);
  });
}

async function loadStatus() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) {
    setStatusBadge("OFFLINE");
    setHidden("offline", false);
    return;
  }

  chrome.runtime.sendMessage(
    { type: "GET_STATUS", tabId: tab.id, url: tab.url },
    (response) => {
      if (!response || response.offline) {
        setStatusBadge("OFFLINE");
        setHidden("offline", false);
        setHidden("fallbackWarning", true);
        setText("urlValue", tab.url || "-");
        setText("riskScore", "-");
        setText("finalVerdict", "-");
        setText("level2Status", "-");
        setHidden("level2ScoreRow", true);
        renderReasons([]);
        return;
      }

      const data = response.data;
      setHidden("offline", true);
      setText("urlValue", data.url || tab.url || "-");
      setText("riskScore", typeof data.riskScore === "number" ? data.riskScore.toFixed(3) : "-");
      setText("finalVerdict", data.finalVerdict || "-");
      setText("level2Status", data.level2Status || "-");

      if (typeof data.level2Score === "number") {
        setHidden("level2ScoreRow", false);
        setText("level2Score", data.level2Score.toFixed(3));
      } else {
        setHidden("level2ScoreRow", true);
        setText("level2Score", "-");
      }

      setStatusBadge(data.finalVerdict);
      renderReasons(data.reasons || []);

      if (data.level2Status === "FALLBACK") {
        setHidden("fallbackWarning", false);
      } else {
        setHidden("fallbackWarning", true);
      }
    }
  );
}

document.addEventListener("DOMContentLoaded", loadStatus);
