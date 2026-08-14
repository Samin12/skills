---
name: nvme-offload
description: Safely offload completed Downloads items and video files larger than 500 MB from approved Mac folders to the Samin Razer NVME, verify transfers, inspect logs, or troubleshoot the mount-aware automation. Use when the user asks to free Mac storage with the NVMe, move large videos or Downloads to the external drive, run the NVMe offload, or check whether automatic offloading worked.
---

# NVMe Offload

Use the bundled scripts to move completed Downloads items and approved large videos to `Mac Air Offload` on the expected NVMe. Verify the volume UUID, never overwrite a destination item, skip open or recently changed files, and remove a source file only after `rsync` reports a successful transfer.

## Run the bounded loop

1. Observe the current state with `df -h / /Volumes/Samin\ Razer\ NVME` and confirm the volume UUID is `552D84FE-28A5-4812-8BED-4FD1DD5972F2`.
2. Run `scripts/nvme-offload.sh` once for completed Downloads items.
3. Run `scripts/nvme-large-video-offload.sh` once for videos larger than 500 MB in `Movies`, `Downloads`, `Desktop`, `Documents`, and `Pictures`.
4. Verify each script's emitted result, moved count, moved size, skipped count, and destination.
5. Read `~/Library/Logs/NVME Offload.log` when troubleshooting.
6. Stop after the current finite worklist. Treat an absent drive or no eligible files as a clean no-op.

## Safety boundaries

- Keep the large-video scope limited to `Movies`, `Downloads`, `Desktop`, `Documents`, and `Pictures`.
- Move only regular video files larger than 500,000,000 bytes.
- Do not move partial downloads, dotfiles, symlinks, files open by a process, or files modified in the last two minutes.
- Exclude application bundles, photo libraries, Final Cut/iMovie libraries, Borumi project bundles, and other package directories.
- Preserve each source folder's relative path under `Mac Air Offload/Large Videos`.
- Do not change the expected volume name, UUID, threshold, or source folders without explicit user approval.
- Do not delete destination data. A transfer failure must leave the remaining source item in place and return `RESULT=blocked`.

## Automation

The LaunchAgent `~/Library/LaunchAgents/com.saminyasar.nvme-offload.plist` runs `scripts/nvme-download-route.sh` at login, after a volume mount, and every two minutes. While the expected NVMe is mounted, it applies Google Chrome's `DownloadDirectory` policy so new browser downloads go directly to the external folder. When the drive is absent, it restores Chrome's original setting. This routing avoids the macOS privacy restriction that prevents background LaunchAgents from reading `~/Downloads`.

Run `scripts/nvme-offload.sh` manually through Codex to move any files staged locally by other apps. Treat `RESULT=blocked` as a real blocker and inspect the log; never report it as a clean no-op.

Run `scripts/nvme-large-video-offload.sh` through Codex or the configured recurring Codex automation. Ordinary LaunchAgents cannot scan the protected source folders because of macOS privacy controls.
