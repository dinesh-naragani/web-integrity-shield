// Content script - shows notification on page when URL is checked

let notificationTimeout = null;

function showNotification(verdict, riskScore, reasons) {
  // Remove existing notification
  const existing = document.getElementById('wis-notification');
  if (existing) {
    existing.remove();
  }

  // Create notification element
  const notification = document.createElement('div');
  notification.id = 'wis-notification';
  notification.className = `wis-notification wis-${verdict.toLowerCase()}`;

  const icon = verdict === 'LEGITIMATE' ? '✓' : verdict === 'PHISHING' ? '⚠' : '●';
  const status = verdict === 'LEGITIMATE' ? 'SAFE' : verdict === 'PHISHING' ? 'PHISHING RISK' : 'SUSPICIOUS';
  const score = typeof riskScore === 'number' ? ` (${(riskScore * 100).toFixed(0)}%)` : '';
  
  let reasonText = '';
  if (reasons && reasons.length > 0 && reasons[0]) {
    reasonText = `<div class="wis-reason">${reasons[0]}</div>`;
  }

  notification.innerHTML = `
    <div class="wis-content">
      <div class="wis-header">
        <span class="wis-icon">${icon}</span>
        <span class="wis-title">Web Integrity Shield</span>
        <button class="wis-close" onclick="this.parentElement.parentElement.parentElement.remove()">×</button>
      </div>
      <div class="wis-status">${status}${score}</div>
      ${reasonText}
    </div>
  `;

  document.body.appendChild(notification);

  // Auto-hide after 5 seconds
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
  }
  notificationTimeout = setTimeout(() => {
    notification.classList.add('wis-fade-out');
    setTimeout(() => notification.remove(), 300);
  }, 5000);
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'URL_CHECK_RESULT') {
    if (!message.offline && message.data) {
      showNotification(
        message.data.finalVerdict || 'SUSPICIOUS',
        message.data.riskScore,
        message.data.reasons
      );
    }
  }
});
