import { useRouter } from 'next/router';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Video } from '@/types/video'

export default function VideoDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [videoUrl, setVideoUrl] = useState('');
  const [videoDuration, setVideoDuration] = useState(0);
  const [sliderTime, setSliderTime] = useState(0);
  const [isCapturing, setIsCapturing] = useState(false);
  const [lastCapturedImage, setLastCapturedImage] = useState('');

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (id) {
      axios.get<Video>(`/api/v1/video/${id}/with-sections`).then((res) => {
        setVideoUrl(res.data.video_url);
      });
    }
  }, [id]);

  const handleSliderChange = (value: number) => {
    setSliderTime(value);
    if (videoRef.current) {
      videoRef.current.currentTime = value;
    }
  };

  const handleCapture = async () => {
    try {
      setIsCapturing(true);
      const video = videoRef.current;
      if (!video) throw new Error("動画が見つかりません");

      if (Math.abs(video.currentTime - sliderTime) > 0.05) {
        video.currentTime = sliderTime;
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(() => reject("seek timeout"), 3000);
          const onSeeked = () => {
            clearTimeout(timeout);
            video.removeEventListener("seeked", onSeeked);
            resolve();
          };
          video.addEventListener("seeked", onSeeked);
        });
      }

      const canvas = canvasRef.current || document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);

      const blob: Blob = await new Promise((resolve, reject) =>
        canvas.toBlob(
          (b) => (b ? resolve(b) : reject("Blob生成失敗")),
          "image/jpeg",
          0.9
        )
      );

      const timestamp = Date.now();
      const filename = `slider_capture_${timestamp}_${sliderTime.toFixed(1)}s.jpg`;

      const formData = new FormData();
      formData.append("image_file", blob, filename);

      const res = await fetch("http://localhost:8000/upload-section-image", {
        method: "POST",
        body: formData,
      });
      const result = await res.json();
      if (!result.success) throw new Error("アップロードに失敗");

      setLastCapturedImage(result.image_url);
      alert("キャプチャして保存しました！");
    } catch (err: any) {
      console.error("キャプチャエラー:", err);
      alert(`キャプチャ失敗: ${err.message || err}`);
    } finally {
      setIsCapturing(false);
    }
  };

  return (
    <main style={{ padding: 20 }}>
      <h1>🎞 動画スライダーキャプチャ & 保存</h1>

      <video
        ref={videoRef}
        src={videoUrl}
        controls
        width={640}
        onLoadedMetadata={(e) => setVideoDuration(e.currentTarget.duration)}
        onTimeUpdate={(e) => setSliderTime(e.currentTarget.currentTime)}
        className="rounded border"
      />

      <div className="mt-6">
        <label className="block mb-2 text-sm font-medium text-gray-700">
          キャプチャ時間：{sliderTime.toFixed(1)}秒
        </label>
        <input
          type="range"
          min={0}
          max={videoDuration}
          step={0.1}
          value={sliderTime}
          onChange={(e) => handleSliderChange(parseFloat(e.target.value))}
          className="w-full"
        />
      </div>

      <button
        onClick={handleCapture}
        disabled={isCapturing}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        {isCapturing ? "キャプチャ中..." : "この時間でキャプチャして保存"}
      </button>

      {lastCapturedImage && (
        <div className="mt-4">
          <p className="text-sm text-gray-500">最後に保存した画像:</p>
          <img
            src={lastCapturedImage}
            alt="キャプチャ画像"
            className="mt-2 border rounded w-full max-w-md"
          />
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: "none" }} />
    </main>
  );
}
