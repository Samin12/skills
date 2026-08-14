#!/bin/bash

set -u

VOLUME_NAME="Samin Razer NVME"
EXPECTED_UUID="552D84FE-28A5-4812-8BED-4FD1DD5972F2"
VOLUME_ROOT="/Volumes/${VOLUME_NAME}"
DEST_ROOT="${VOLUME_ROOT}/Mac Air Offload/Downloads"
CHROME_DOMAIN="com.google.Chrome"
CHROME_APP="/Applications/Google Chrome.app"
STATE_DIR="${HOME}/Library/Application Support/NVME Offload"
ORIGINAL_SETTING="${STATE_DIR}/chrome-download-directory.original"
ACTIVE_MARKER="${STATE_DIR}/chrome-route-active"
LOG_FILE="${HOME}/Library/Logs/NVME Offload.log"

mkdir -p "${STATE_DIR}" "$(dirname "${LOG_FILE}")"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "${LOG_FILE}"
}

snapshot_original() {
  if [ -f "${ORIGINAL_SETTING}" ]; then
    return
  fi
  if original_value="$(defaults read "${CHROME_DOMAIN}" DownloadDirectory 2>/dev/null)"; then
    printf 'value\n%s\n' "${original_value}" > "${ORIGINAL_SETTING}"
  else
    printf 'absent\n' > "${ORIGINAL_SETTING}"
  fi
}

restore_original() {
  if [ ! -f "${ACTIVE_MARKER}" ]; then
    printf 'ROUTE_RESULT=clean-no-op\nROUTE_DESTINATION=%s\n' "${HOME}/Downloads"
    return 0
  fi

  if [ "$(sed -n '1p' "${ORIGINAL_SETTING}" 2>/dev/null)" = "value" ]; then
    original_value="$(sed -n '2,$p' "${ORIGINAL_SETTING}")"
    defaults write "${CHROME_DOMAIN}" DownloadDirectory -string "${original_value}"
  else
    defaults delete "${CHROME_DOMAIN}" DownloadDirectory >/dev/null 2>&1 || true
  fi
  rm -f "${ACTIVE_MARKER}"
  log "Chrome download route restored to its original local setting."
  printf 'ROUTE_RESULT=restored-local\nROUTE_DESTINATION=%s\n' "${HOME}/Downloads"
}

if [ ! -d "${CHROME_APP}" ]; then
  log "Blocked: Google Chrome is not installed."
  printf 'ROUTE_RESULT=blocked\nROUTE_DESTINATION=%s\n' "${DEST_ROOT}"
  exit 1
fi

if [ ! -d "${VOLUME_ROOT}" ]; then
  restore_original
  exit $?
fi

actual_uuid="$(diskutil info "${VOLUME_ROOT}" 2>/dev/null | awk -F: '/Volume UUID/{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2; exit}')"
if [ "${actual_uuid}" != "${EXPECTED_UUID}" ]; then
  log "Blocked: volume UUID mismatch while routing Chrome downloads."
  printf 'ROUTE_RESULT=blocked\nROUTE_DESTINATION=%s\n' "${DEST_ROOT}"
  exit 1
fi

if ! mkdir -p "${DEST_ROOT}"; then
  log "Blocked: external Downloads destination is not writable."
  printf 'ROUTE_RESULT=blocked\nROUTE_DESTINATION=%s\n' "${DEST_ROOT}"
  exit 1
fi

snapshot_original
defaults write "${CHROME_DOMAIN}" DownloadDirectory -string "${DEST_ROOT}"
current_value="$(defaults read "${CHROME_DOMAIN}" DownloadDirectory 2>/dev/null || true)"
if [ "${current_value}" != "${DEST_ROOT}" ]; then
  log "Blocked: Chrome DownloadDirectory policy did not persist."
  printf 'ROUTE_RESULT=blocked\nROUTE_DESTINATION=%s\n' "${DEST_ROOT}"
  exit 1
fi

touch "${ACTIVE_MARKER}"
log "Chrome downloads routed to ${DEST_ROOT}."
printf 'ROUTE_RESULT=routed-external\nROUTE_DESTINATION=%s\n' "${DEST_ROOT}"
