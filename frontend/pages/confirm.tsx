import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'

interface VideoData {
  video_id: string
  video_url: string
  thumbnail_url?: string
  club_type?: string
  swing_form?: string
  swing_note?: string
  upload_date: string
}

interface MediaUrlResponse {
  url: string
}

export default function Confirm() {
  const router = useRouter()
  const [videoData, setVideoData] = useState<VideoData | null>(null)
  const [loading, setLoading] = useState(true)
  const [videoSasUrl, setVideoSasUrl] = useState<string>('')
  const [thumbnailSasUrl, setThumbnailSasUrl] = useState<string>('')

  useEffect(() => {
    // URLパラメータからvideo_idを取得
    const { video_id } = router.query
    
    if (video_id && typeof video_id === 'string') {
      fetchVideoData(video_id)
    } else {
      // video_idがない場合はプレイヤーページにリダイレクト
      router.push('/player')
    }
  }, [router.query])

  const fetchVideoData = async (videoId: string) => {
    try {
      const response = await fetch(`/api/v1/upload-status/${videoId}`)
      if (response.ok) {
        const data = await response.json()
        setVideoData(data)
        
        // SAS付きURLを取得
        await fetchMediaUrls(data.video_url, data.thumbnail_url)
      } else {
        console.error('Failed to fetch video data')
        router.push('/player')
      }
    } catch (error) {
      console.error('Error fetching video data:', error)
      router.push('/player')
    } finally {
      setLoading(false)
    }
  }

  const fetchMediaUrls = async (videoUrl: string, thumbnailUrl?: string) => {
    try {
      // 動画のSAS URLを取得
      if (videoUrl) {
        const videoResponse = await fetch(`/api/v1/media-url?blob_url=${encodeURIComponent(videoUrl)}`)
        if (videoResponse.ok) {
          const videoData: MediaUrlResponse = await videoResponse.json()
          setVideoSasUrl(videoData.url)
        }
      }

      // サムネイルのSAS URLを取得
      if (thumbnailUrl) {
        const thumbnailResponse = await fetch(`/api/v1/media-url?blob_url=${encodeURIComponent(thumbnailUrl)}`)
        if (thumbnailResponse.ok) {
          const thumbnailData: MediaUrlResponse = await thumbnailResponse.json()
          setThumbnailSasUrl(thumbnailData.url)
        }
      }
    } catch (error) {
      console.error('Error fetching media URLs:', error)
    }
  }

  const handleConfirm = () => {
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">動画情報を読み込み中...</p>
        </div>
      </div>
    )
  }

  if (!videoData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">動画データが見つかりません</p>
          <Link href="/player" className="text-blue-500 hover:text-blue-700">
            プレイヤーページに戻る
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-green-500 text-white p-6 text-center">
            <div className="text-4xl mb-2">✓</div>
            <h1 className="text-2xl font-bold">アップロード完了</h1>
            <p className="text-green-100 mt-2">動画のアップロードが正常に完了しました</p>
          </div>

          <div className="p-8">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Video Section */}
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-800">アップロードされた動画</h2>
                <div className="bg-gray-50 rounded-lg p-4">
                  {videoSasUrl ? (
                    <video
                      controls
                      className="w-full rounded-lg"
                      style={{ maxHeight: '300px' }}
                      src={videoSasUrl}
                    >
                      お使いのブラウザは動画の再生に対応していません。
                    </video>
                  ) : (
                    <div className="flex items-center justify-center h-48 text-gray-400">
                      <div className="text-center">
                        <div className="text-4xl mb-2">📹</div>
                        <p>動画を読み込み中...</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Thumbnail Section */}
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-800">サムネイル</h2>
                <div className="bg-gray-50 rounded-lg p-4">
                  {thumbnailSasUrl ? (
                    <img
                      src={thumbnailSasUrl}
                      alt="動画サムネイル"
                      className="w-full rounded-lg"
                      style={{ maxHeight: '300px', objectFit: 'contain' }}
                    />
                  ) : videoData?.thumbnail_url ? (
                    <div className="flex items-center justify-center h-48 text-gray-400">
                      <div className="text-center">
                        <div className="text-4xl mb-2">🖼️</div>
                        <p>サムネイル読み込み中...</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-48 text-gray-400">
                      <div className="text-center">
                        <div className="text-4xl mb-2">📹</div>
                        <p>サムネイルが生成されませんでした</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Video Information */}
            <div className="mt-8 bg-gray-50 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">動画情報</h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-gray-600 mb-1">動画ID</p>
                  <p className="font-mono text-sm bg-white px-3 py-2 rounded border text-gray-800">
                    {videoData.video_id}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">アップロード日時</p>
                  <p className="text-gray-800">
                    {new Date(videoData.upload_date).toLocaleString('ja-JP')}
                  </p>
                </div>
                {videoData.club_type && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">使用クラブ</p>
                    <p className="text-gray-800">
                      {videoData.club_type === 'driver' && 'ドライバー'}
                      {videoData.club_type === 'fairway_wood' && 'フェアウェイウッド'}
                      {videoData.club_type === 'hybrid' && 'ハイブリッド'}
                      {videoData.club_type === 'iron' && 'アイアン'}
                      {videoData.club_type === 'wedge' && 'ウェッジ'}
                      {videoData.club_type === 'putter' && 'パター'}
                    </p>
                  </div>
                )}
                {videoData.swing_form && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">スイング種類</p>
                    <p className="text-gray-800">
                      {videoData.swing_form === 'full_swing' && 'フルスイング'}
                      {videoData.swing_form === 'half_swing' && 'ハーフスイング'}
                      {videoData.swing_form === 'chip' && 'チップ'}
                      {videoData.swing_form === 'pitch' && 'ピッチ'}
                      {videoData.swing_form === 'bunker' && 'バンカー'}
                      {videoData.swing_form === 'putting' && 'パッティング'}
                    </p>
                  </div>
                )}
              </div>
              {videoData.swing_note && (
                <div className="mt-4">
                  <p className="text-sm text-gray-600 mb-1">メモ・補足</p>
                  <p className="text-gray-800 bg-white px-3 py-2 rounded border">
                    {videoData.swing_note}
                  </p>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="mt-8 text-center">
              <button
                onClick={handleConfirm}
                className="bg-blue-500 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-600 transition-colors duration-200"
              >
                確認
              </button>
              <p className="text-sm text-gray-500 mt-4">
                確認ボタンを押すとトップページに戻ります
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}