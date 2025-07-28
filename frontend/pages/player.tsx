import { useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'

export default function Player() {
  const router = useRouter()
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoUrl, setVideoUrl] = useState<string>('')
  const [isUploading, setIsUploading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)

  const handleFile = (file: File) => {
    if (file && file.type.startsWith('video/')) {
      setVideoFile(file)
      // Create blob URL for preview
      const url = URL.createObjectURL(file)
      setVideoUrl(url)
    }
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleFile(file)
    }
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragging(false)
    
    const file = event.dataTransfer.files[0]
    if (file) {
      handleFile(file)
    }
  }

  const uploadVideo = async () => {
    if (!videoFile) return

    setIsUploading(true)
    
    try {
      const formData = new FormData()
      formData.append('video_file', videoFile)

      const response = await fetch('/api/v1/upload-video', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        console.log('Video uploaded successfully:', data)
        console.log('Video ID:', data.video_id)
        
        if (data.video_id) {
          // アップロード成功時に確認ページに遷移
          console.log('Navigating to confirm page with video_id:', data.video_id)
          
          // フォームをリセット
          setVideoFile(null)
          setVideoUrl('')
          
          // 確認ページに遷移
          router.push(`/confirm?video_id=${data.video_id}`)
        } else {
          console.error('No video_id in response:', data)
          alert('アップロードは成功しましたが、動画IDが取得できませんでした')
        }
      } else {
        const errorData = await response.text()
        console.error('Upload failed:', response.status, errorData)
        alert(`アップロードに失敗しました: ${response.status}`)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('アップロードエラーが発生しました')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto">
        <Link href="/" className="text-blue-500 hover:text-blue-700 mb-8 inline-block">
          ← トップに戻る
        </Link>

        <div className="bg-white p-8 rounded-lg shadow">
          <h1 className="text-2xl font-bold mb-8 text-center">動画アップロード</h1>

          {!videoFile ? (
            <div 
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                isDragging 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                className="hidden"
                id="video-upload"
              />
              <div className="space-y-4">
                <p className="text-gray-600">
                  動画ファイルをドラッグ&ドロップするか
                </p>
                <label
                  htmlFor="video-upload"
                  className="bg-blue-500 text-white px-6 py-3 rounded-lg cursor-pointer hover:bg-blue-600 transition-colors duration-200 inline-block"
                >
                  動画ファイルを選択
                </label>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center">
                <p className="text-gray-600 mb-4">選択された動画: {videoFile.name}</p>
                <video
                  src={videoUrl}
                  controls
                  className="max-w-full h-64 mx-auto rounded"
                />
              </div>
              
              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => {
                    setVideoFile(null)
                    setVideoUrl('')
                  }}
                  className="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 transition-colors duration-200"
                >
                  別の動画を選択
                </button>
                
                <button
                  onClick={uploadVideo}
                  disabled={isUploading}
                  className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors duration-200 disabled:bg-gray-400"
                >
                  {isUploading ? 'アップロード中...' : 'アップロード'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}