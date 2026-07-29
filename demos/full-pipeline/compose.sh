#!/bin/bash
# Cut the recorded segments into demos/rendered/full-pipeline.mp4.
# Time-compresses the waiting (the live supervise stretch and the
# Mission Control capture), never the acts. Requires ffmpeg + node
# with Playwright resolvable (for the title/end cards).
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
SEG=$REPO/demos/rendered/segments
WORK=$REPO/demos/rendered/work
OUT=$REPO/demos/rendered/full-pipeline.mp4
mkdir -p "$WORK"

dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1" | cut -d. -f1; }

norm() { # norm <in> <out> [setpts-divisor]
  local f=${3:-1}
  ffmpeg -y -v error -i "$1" \
    -vf "setpts=PTS/$f,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p" \
    -an -c:v libx264 -preset medium -crf 20 "$2"
}

# 0. Title and end cards.
[ -f "$HERE/title.png" ] && [ -f "$HERE/end.png" ] || (cd "$HERE" && node shoot-cards.mjs)
ffmpeg -y -v error -loop 1 -i "$HERE/title.png" -t 4.5 -r 30 -vf format=yuv420p -c:v libx264 "$WORK/00-title.mp4"
ffmpeg -y -v error -loop 1 -i "$HERE/end.png" -t 5 -r 30 -vf format=yuv420p -c:v libx264 "$WORK/99-end.mp4"

# 1-4. Terminal segments at natural speed; browser review gently sped up.
norm "$SEG/01-init.mp4"      "$WORK/01.mp4"
norm "$SEG/02-intake.mp4"    "$WORK/02.mp4"
norm "$SEG/review.webm"      "$WORK/03-review.mp4" 1.3
norm "$SEG/03-lease.mp4"     "$WORK/04.mp4"
norm "$SEG/04-grant.mp4"     "$WORK/05.mp4"

# 5. The live stretch: keep the first 18s and last 30s honest,
#    timelapse the middle down to ~30s; Mission Control to ~25s.
D=$(dur "$SEG/05-live.mp4")
if [ "$D" -gt 90 ]; then
  MID_END=$((D - 30)); MID_LEN=$((MID_END - 18))
  F=$(echo "scale=4; $MID_LEN / 30" | bc)
  ffmpeg -y -v error -i "$SEG/05-live.mp4" -filter_complex \
    "[0:v]trim=0:18,setpts=PTS-STARTPTS[a];[0:v]trim=18:$MID_END,setpts=(PTS-STARTPTS)/$F[b];[a][b]concat=n=2,fps=30,format=yuv420p" \
    -an -c:v libx264 -preset medium -crf 20 "$WORK/06-live-a.mp4"
  ffmpeg -y -v error -ss "$MID_END" -i "$SEG/05-live.mp4" \
    -vf "fps=30,format=yuv420p" -an -c:v libx264 -preset medium -crf 20 "$WORK/08-live-b.mp4"
else
  norm "$SEG/05-live.mp4" "$WORK/06-live-a.mp4"
  ffmpeg -y -v error -f lavfi -i "color=c=0x282a36:s=1280x720:d=0.1:r=30" -vf format=yuv420p -c:v libx264 "$WORK/08-live-b.mp4"
fi
MC=$(dur "$SEG/mission-control.webm")
norm "$SEG/mission-control.webm" "$WORK/07-mc.mp4" "$(echo "scale=4; $MC / 25" | bc)"

# 6. Certified handoff, integration, evidence, the gated ship.
norm "$SEG/06-certified.mp4" "$WORK/09.mp4"
if [ -f "$SEG/mission-control-final.webm" ]; then
  norm "$SEG/mission-control-final.webm" "$WORK/09b-mc-final.mp4"
fi

# 7. Two browser clients, one page, one clock.
norm "$SEG/gameplay.webm" "$WORK/10-gameplay.mp4"

# 8. One film.
: > "$WORK/list.txt"
for f in 00-title 01 02 03-review 04 05 06-live-a 07-mc 08-live-b 09 10-gameplay 99-end; do
  [ -f "$WORK/$f.mp4" ] || continue
  echo "file '$WORK/$f.mp4'" >> "$WORK/list.txt"
done
ffmpeg -y -v error -f concat -safe 0 -i "$WORK/list.txt" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" | xargs -I{} echo "full-pipeline.mp4: {}s"
