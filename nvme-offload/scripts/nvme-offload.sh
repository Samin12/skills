#!/bin/bash

set -u

VOLUME_NAME="Samin Razer NVME"
EXPECTED_UUID="552D84FE-28A5-4812-8BED-4FD1DD5972F2"
VOLUME_ROOT="/Volumes/${VOLUME_NAME}"
SOURCE_ROOT="${HOME}/Downloads"
DEST_ROOT="${VOLUME_ROOT}/Mac Air Offload/Downloads"
STATE_DIR="${HOME}/Library/Application Support/NVME Offload"
LOG_FILE="${HOME}/Library/Logs/NVME Offload.log"
LOCK_DIR="${STATE_DIR}/run.lock"
AGE_MARKER="${STATE_DIR}/eligible-before"

mkdir -p "${STATE_DIR}" "$(dirname "${LOG_FILE}")"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "${LOG_FILE}"
}

emit_result() {
  printf 'RESULT=%s\nMOVED_ITEMS=%s\nMOVED_KIB=%s\nSKIPPED_ITEMS=%s\nDESTINATION=%s\n' \
    "$1" "$2" "$3" "$4" "${DEST_ROOT}"
}

acquire_lock() {
  if mkdir "${LOCK_DIR}" 2>/dev/null; then
    printf '%s\n' "$$" > "${LOCK_DIR}/pid"
    return 0
  fi

  local old_pid=""
  if [ -f "${LOCK_DIR}/pid" ]; then
    old_pid="$(cat "${LOCK_DIR}/pid" 2>/dev/null || true)"
  fi
  if [ -n "${old_pid}" ] && kill -0 "${old_pid}" 2>/dev/null; then
    return 1
  fi

  find "${LOCK_DIR}" -mindepth 1 -maxdepth 1 -delete 2>/dev/null || true
  rmdir "${LOCK_DIR}" 2>/dev/null || true
  mkdir "${LOCK_DIR}" 2>/dev/null || return 1
  printf '%s\n' "$$" > "${LOCK_DIR}/pid"
}

release_lock() {
  find "${LOCK_DIR}" -mindepth 1 -maxdepth 1 -delete 2>/dev/null || true
  rmdir "${LOCK_DIR}" 2>/dev/null || true
}

unique_destination() {
  local source_name="$1"
  local candidate="${DEST_ROOT}/${source_name}"
  local stamp counter
  if [ ! -e "${candidate}" ] && [ ! -L "${candidate}" ]; then
    printf '%s\n' "${candidate}"
    return
  fi

  stamp="$(date '+%Y-%m-%d %H%M%S')"
  counter=1
  while :; do
    candidate="${DEST_ROOT}/${source_name} (offloaded ${stamp}-${counter})"
    if [ ! -e "${candidate}" ] && [ ! -L "${candidate}" ]; then
      printf '%s\n' "${candidate}"
      return
    fi
    counter=$((counter + 1))
  done
}

if ! acquire_lock; then
  log "Clean no-op: another offload run is active."
  emit_result "clean-no-op" 0 0 0
  exit 0
fi
trap release_lock EXIT HUP INT TERM

if [ ! -d "${VOLUME_ROOT}" ]; then
  log "Clean no-op: expected NVMe is not mounted."
  emit_result "clean-no-op" 0 0 0
  exit 0
fi

actual_uuid="$(diskutil info "${VOLUME_ROOT}" 2>/dev/null | awk -F: '/Volume UUID/{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2; exit}')"
if [ "${actual_uuid}" != "${EXPECTED_UUID}" ]; then
  log "Blocked: volume UUID mismatch for ${VOLUME_ROOT}."
  emit_result "blocked" 0 0 0
  exit 1
fi

if [ ! -d "${SOURCE_ROOT}" ] || [ -L "${SOURCE_ROOT}" ]; then
  log "Blocked: Downloads is missing or is a symbolic link."
  emit_result "blocked" 0 0 0
  exit 1
fi

if ! find "${SOURCE_ROOT}" -mindepth 1 -maxdepth 1 -print -quit >/dev/null 2>>"${LOG_FILE}"; then
  log "Blocked: macOS denied access to Downloads. Run this skill interactively in Codex."
  emit_result "blocked" 0 0 0
  exit 1
fi

if ! mkdir -p "${DEST_ROOT}"; then
  log "Blocked: destination is not writable."
  emit_result "blocked" 0 0 0
  exit 1
fi

touch -t "$(date -v-2M '+%Y%m%d%H%M.%S')" "${AGE_MARKER}"

moved_items=0
moved_kib=0
skipped_items=0
failed_items=0

while IFS= read -r -d '' item; do
  item_name="$(basename "${item}")"

  case "${item_name}" in
    .*|*.crdownload|*.CRDOWNLOAD|*.download|*.DOWNLOAD|*.part|*.PART|*.tmp|*.TMP)
      skipped_items=$((skipped_items + 1))
      continue
      ;;
  esac

  if [ -L "${item}" ]; then
    skipped_items=$((skipped_items + 1))
    continue
  fi

  if [ -n "$(find "${item}" -type f \( -newer "${AGE_MARKER}" -o -iname '*.crdownload' -o -iname '*.download' -o -iname '*.part' -o -iname '*.tmp' \) -print -quit 2>/dev/null)" ]; then
    skipped_items=$((skipped_items + 1))
    continue
  fi

  item_kib="$(du -sk "${item}" 2>/dev/null | awk '{print $1}')"
  item_kib="${item_kib:-0}"
  destination="$(unique_destination "${item_name}")"

  if [ -d "${item}" ]; then
    if mkdir -p "${destination}" && rsync -a --remove-source-files -- "${item}/" "${destination}/"; then
      find "${item}" -depth -type d -empty -delete 2>/dev/null || true
      if [ ! -e "${item}" ]; then
        moved_items=$((moved_items + 1))
        moved_kib=$((moved_kib + item_kib))
        log "Moved directory: ${item_name} (${item_kib} KiB)."
      else
        failed_items=$((failed_items + 1))
        log "Blocked: directory transfer left source entries: ${item_name}."
      fi
    else
      failed_items=$((failed_items + 1))
      log "Blocked: directory transfer failed: ${item_name}."
    fi
  elif [ -f "${item}" ]; then
    if rsync -a --remove-source-files -- "${item}" "${destination}" && [ ! -e "${item}" ]; then
      moved_items=$((moved_items + 1))
      moved_kib=$((moved_kib + item_kib))
      log "Moved file: ${item_name} (${item_kib} KiB)."
    else
      failed_items=$((failed_items + 1))
      log "Blocked: file transfer failed: ${item_name}."
    fi
  else
    skipped_items=$((skipped_items + 1))
  fi
done < <(find "${SOURCE_ROOT}" -mindepth 1 -maxdepth 1 -print0)

if [ "${failed_items}" -gt 0 ]; then
  log "Blocked: ${failed_items} item(s) did not complete."
  emit_result "blocked" "${moved_items}" "${moved_kib}" "${skipped_items}"
  exit 1
fi

if [ "${moved_items}" -eq 0 ]; then
  log "Clean no-op: no eligible completed Downloads items."
  emit_result "clean-no-op" 0 0 "${skipped_items}"
  exit 0
fi

log "Success: moved ${moved_items} item(s), ${moved_kib} KiB."
emit_result "success" "${moved_items}" "${moved_kib}" "${skipped_items}"
