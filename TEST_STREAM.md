# Test Stream URLs

## Working RTSP URLs to try:

1. **Big Buck Bunny (Most reliable)**
```
rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4
```

2. **RTSP.me Test Pattern**
```
rtsp://rtsp.stream/pattern
```

3. **RTSP.me Movie**
```
rtsp://rtsp.stream/movie
```

## Test if FFmpeg is working:

Open PowerShell and run:
```powershell
cd backend
ffmpeg -i rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4 -t 10 -c copy test.mp4
```

If this works, FFmpeg can access RTSP streams.

## Check stream directory:

After starting a stream, check if files are being created:
```powershell
dir backend\streams\
```

You should see a folder with UUID name, and inside it should be `index.m3u8` and `.ts` files.

## Backend logs to look for:

```
🎥 Stream started: <id> from rtsp://...
📁 HLS output: <path>
⏳ Please wait 10-15 seconds...
```

If you see FFmpeg errors, it means the RTSP URL is not accessible or there's a network issue.
