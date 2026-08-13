import datetime
import os
import sys
import subprocess


# Determine BGM based on the day of the week
weekday = datetime.date.today().weekday()
bgm_map = {
    0: "TechLive.mp3",
    1: "Tuesday.mp3",
    2: "Wednesday.mp3",
    3: "Thursday.mp3",
    4: "Friday.mp3",
    5: "Saturday.mp3",
    6: "Sunday.mp3"
}
bgm_filename = bgm_map.get(weekday, "TechLive.mp3")
bgm_path = f"/Users/smithkwon/.openclaw/workspace/dailypriceup/data/{bgm_filename}"
print(f"Today is {datetime.date.today().strftime('%A')}, using BGM: {bgm_filename}")

print("Generating 16-second Shorts video (including Top 10)...")
ffmpeg_cmd = [
    "/opt/homebrew/bin/ffmpeg", "-y",
    "-loop", "1", "-t", "4", "-i", "/Users/smithkwon/.openclaw/workspace/dailypriceup/data/daily_shorts_amount.png",
    "-loop", "1", "-t", "4", "-i", "/Users/smithkwon/.openclaw/workspace/dailypriceup/data/daily_shorts_rate.png",
    "-loop", "1", "-t", "4", "-i", "/Users/smithkwon/.openclaw/workspace/dailypriceup/data/daily_shorts_lowest.png",
    "-loop", "1", "-t", "4", "-i", "/Users/smithkwon/.openclaw/workspace/dailypriceup/data/daily_shorts_top10.png",
    "-i", bgm_path,
    "-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v];[4:a]afade=t=out:st=14:d=2[a]",
    "-map", "[v]", "-map", "[a]",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
    "-c:a", "aac", "-b:a", "192k", "-shortest",
    "/Users/smithkwon/.openclaw/workspace/dailypriceup/data/daily_shorts_final.mp4"
]

subprocess.run(ffmpeg_cmd, capture_output=True)
print("Video generation complete: daily_shorts_final.mp4")
