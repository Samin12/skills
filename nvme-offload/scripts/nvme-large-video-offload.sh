#!/bin/bash

set -u

VOLUME_NAME="Samin Razer NVME"
EXPECTED_UUID="552D84FE-28A5-4812-8BED-4FD1DD5972F2"
VOLUME_ROOT="/Volumes/${VOLUME_NAME}"
DEST_ROOT="${VOLUME_ROOT}/Mac Air Offload/Large Videos"
THRESHOLD_BYTES=500000000
MIN_AGE_SECONDS=120
STATE_DIR="${HOME}/Library/Application Support/NVME Offload"
LOG_FILE="${HOME}/Library/Logs/NVME Offload.log"
LOCK_DIR="${STATE_DIR}/large-video.lock"
CANDIDATES_FILE="${STATE_DIR}/large-video-candidates.$$"
SOURCE_ROOTS=(
  "${HOME}/Movies"
  "${HOME}/Downloads"
  "${HOME}/Desktop"
  "${HOME}/Documents"
  "${HOME}/Pictures"
)

mkdir -p "${STATE_DIR}" "$(dirname "${LOG_FILE}")"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "${LOG_FILE}"
}

emit_result() {
  printf 'LARGE_VIDEO_RESULT=%s\nMOVED_ITEMS=%s\nMOVED_BYTES=%s\nSKIPPED_ITEMS=%s\nFAILED_ITEMS=%s\nDESTINATION=%s\n' \
    "$1" "$2" "$3" "$4" "$5" "${DEST_ROOT}"
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

cleanup() {
  rm -f "${CANDIDATES_FILE}"
  find "${LOCK_DIR}" -mindepth 1 -maxdepth 1 -delete 2>/dev/null || true
  rmdir "${LOCK_DIR}" 2>/dev/null || true
}

is_video() {
  local file_path="$1"
  local content_types extension
  content_types="$(mdls -raw -name kMDItemContentTypeTree "${file_path}" 2>/dev/null || true)"
  case "${content_types}" in
    *public.movie*) return 0 ;;
  esac

  extension="$(printf '%s' "${file_path##*.}" | tr '[:upper:]' '[:lower:]')"
  case "${extension}" in
    mp4|mov|m4v|mkv|avi|webm|mpg|mpeg|mts|m2ts|mxf|3gp|3g2|wmv|flv) return 0 ;;
  esac
  return 1
}

unique_destination() {
  local desired="$1"
  local directory filename stem extension stamp counter candidate
  if [ ! -e "${desired}" ] && [ ! -L "${desired}" ]; then
    printf '%s\n' "${desired}"
    return
  fi

  directory="$(dirname "${desired}")"
  filename="$(basename "${desired}")"
  if [ "${filename#*.}" != "${filename}" ]; then
    stem="${filename%.*}"
    extension=".${filename##*.}"
  else
    stem="${filename}"
    extension=""
  fi
  stamp="$(date '+%Y-%m-%d %H%M%S')"
  counter=1
  while :; do
    candidate="${directory}/${stem} (offloaded ${stamp}-${counter})${extension}"
    if [ ! -e "${candidate}" ] && [ ! -L "${candidate}" ]; then
      printf '%s\n' "${candidate}"
      return
    fi
    counter=$((counter + 1))
  done
}

if ! acquire_lock; then
  log "Large-video clean no-op: another run is active."
  emit_result "clean-no-op" 0 0 0 0
  exit 0
fi
trap cleanup EXIT HUP INT TERM

if [ ! -d "${VOLUME_ROOT}" ]; then
  log "Large-video clean no-op: expected NVMe is not mounted."
  emit_result "clean-no-op" 0 0 0 0
  exit 0
fi

actual_uuid="$(diskutil info "${VOLUME_ROOT}" 2>/dev/null | awk -F: '/Volume UUID/{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2; exit}')"
if [ "${actual_uuid}" != "${EXPECTED_UUID}" ]; then
  log "Large-video blocked: volume UUID mismatch."
  emit_result "blocked" 0 0 0 1
  exit 1
fi

if ! mkdir -p "${DEST_ROOT}"; then
  log "Large-video blocked: destination is not writable."
  emit_result "blocked" 0 0 0 1
  exit 1
fi

: > "${CANDIDATES_FILE}"
scan_failures=0
for source_root in "${SOURCE_ROOTS[@]}"; do
  [ -d "${source_root}" ] || continue
  if ! find "${source_root}" \
    \( -type d \( -name '.*' -o -name '*.app' -o -name '*.bundle' -o -name '*.framework' -o -name '*.photoslibrary' -o -name '*.photolibrary' -o -name '*.imovielibrary' -o -name '*.fcpbundle' -o -name '*.bmprojbundle' \) -prune \) -o \
    \( -type f -size +500000000c -print0 \) >> "${CANDIDATES_FILE}" 2>>"${LOG_FILE}"; then
    scan_failures=$((scan_failures + 1))
  fi
done

if [ "${scan_failures}" -gt 0 ]; then
  log "Large-video blocked: macOS denied one or more approved source folders."
  emit_result "blocked" 0 0 0 "${scan_failures}"
  exit 1
fi

moved_items=0
moved_bytes=0
skipped_items=0
failed_items=0
now_epoch="$(date '+%s')"

while IFS= read -r -d '' file_path; do
  if [ -L "${file_path}" ] || ! is_video "${file_path}"; then
    skipped_items=$((skipped_items + 1))
    continue
  fi

  modified_epoch="$(stat -f '%m' "${file_path}" 2>/dev/null || printf '0')"
  if [ $((now_epoch - modified_epoch)) -lt "${MIN_AGE_SECONDS}" ]; then
    skipped_items=$((skipped_items + 1))
    continue
  fi

  if lsof "${file_path}" >/dev/null 2>&1; then
    skipped_items=$((skipped_items + 1))
    log "Large-video skipped open file: ${file_path}."
    continue
  fi

  source_root=""
  source_label=""
  for approved_root in "${SOURCE_ROOTS[@]}"; do
    case "${file_path}" in
      "${approved_root}"/*)
        source_root="${approved_root}"
        source_label="$(basename "${approved_root}")"
        break
        ;;
    esac
  done
  if [ -z "${source_root}" ]; then
    failed_items=$((failed_items + 1))
    log "Large-video blocked: candidate escaped approved roots: ${file_path}."
    continue
  fi

  relative_path="${file_path#"${source_root}/"}"
  desired_destination="${DEST_ROOT}/${source_label}/${relative_path}"
  destination="$(unique_destination "${desired_destination}")"
  file_bytes="$(stat -f '%z' "${file_path}" 2>/dev/null || printf '0')"

  if ! mkdir -p "$(dirname "${destination}")"; then
    failed_items=$((failed_items + 1))
    log "Large-video blocked: could not create destination for ${file_path}."
    continue
  fi

  if rsync -a --remove-source-files -- "${file_path}" "${destination}" && [ ! -e "${file_path}" ] && [ -f "${destination}" ]; then
    destination_bytes="$(stat -f '%z' "${destination}" 2>/dev/null || printf '0')"
    if [ "${destination_bytes}" = "${file_bytes}" ]; then
      moved_items=$((moved_items + 1))
      moved_bytes=$((moved_bytes + file_bytes))
      log "Large-video moved: ${file_path} -> ${destination} (${file_bytes} bytes)."
    else
      failed_items=$((failed_items + 1))
      log "Large-video blocked: destination size mismatch after move: ${destination}."
    fi
  else
    failed_items=$((failed_items + 1))
    log "Large-video blocked: transfer failed: ${file_path}."
  fi
done < "${CANDIDATES_FILE}"

if [ "${failed_items}" -gt 0 ]; then
  log "Large-video blocked: ${failed_items} item(s) failed."
  emit_result "blocked" "${moved_items}" "${moved_bytes}" "${skipped_items}" "${failed_items}"
  exit 1
fi

if [ "${moved_items}" -eq 0 ]; then
  log "Large-video clean no-op: no eligible video files over ${THRESHOLD_BYTES} bytes."
  emit_result "clean-no-op" 0 0 "${skipped_items}" 0
  exit 0
fi

log "Large-video success: moved ${moved_items} item(s), ${moved_bytes} bytes."
emit_result "success" "${moved_items}" "${moved_bytes}" "${skipped_items}" 0
