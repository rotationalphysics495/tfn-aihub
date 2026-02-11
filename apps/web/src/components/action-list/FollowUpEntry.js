// CJS-compatible exports for require() in tests.
// ESM imports resolve to FollowUpEntry.tsx (preferred by Vite resolve.extensions).

function formatRelativeTime(isoString) {
  var diff = Date.now() - new Date(isoString).getTime()
  var minutes = Math.floor(diff / 60000)
  if (minutes < 60) return minutes + 'm ago'
  var hours = Math.floor(minutes / 60)
  if (hours < 24) return hours + 'h ago'
  var days = Math.floor(hours / 24)
  return days + 'd ago'
}

exports.formatRelativeTime = formatRelativeTime
