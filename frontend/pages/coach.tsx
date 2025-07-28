import { useState, useEffect } from 'react'
import Link from 'next/link'

interface VideoItem {
  video_id: string
  video_url: string
  thumbnail_url?: string
  upload_date: string
  club_type?: string
  swing_form?: string
  swing_note?: string
  status: 'pending' | 'in_progress' | 'completed'
}

interface MediaUrlResponse {
  url: string
}

export default function CoachDashboard() {
  const [videos, setVideos] = useState<VideoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v1/videos')
      if (response.ok) {
        const data = await response.json()
        const videosWithStatus = data.map((video: any) => ({
          ...video,
          status: getVideoStatus(video)
        }))
        setVideos(videosWithStatus)
      } else {
        setError('動画一覧の取得に失敗しました')
      }
    } catch (err) {
      console.error('Error fetching videos:', err)
      setError('動画一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const getVideoStatus = (video: any): 'pending' | 'in_progress' | 'completed' => {
    // セクションの存在をチェックして状態を判定
    if (video.sections && video.sections.length > 0) {
      const hasComments = video.sections.some((section: any) => section.coach_comment)
      return hasComments ? 'completed' : 'in_progress'
    }
    return 'pending'
  }

  const extractUserNumber = (url: string): string => {
    // URLからファイル名を抽出
    const filename = url.split('/').pop() || ''
    // ファイル名から_U99999の部分を抽出
    const match = filename.match(/_U(\d+)/)
    return match ? `U${match[1]}` : 'U-----'
  }

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'pending':
        return (
          <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
            未入力
          </span>
        )
      case 'in_progress':
        return (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
            入力中
          </span>
        )
      case 'completed':
        return (
          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
            完了
          </span>
        )
      default:
        return (
          <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
            未入力
          </span>
        )
    }
  }

  const getThumbnailSasUrl = async (thumbnailUrl: string): Promise<string> => {
    try {
      const response = await fetch(`/api/v1/media-url?blob_url=${encodeURIComponent(thumbnailUrl)}`)
      if (response.ok) {
        const data: MediaUrlResponse = await response.json()
        return data.url
      }
    } catch (error) {
      console.error('Error fetching thumbnail SAS URL:', error)
    }
    return ''
  }

  const ThumbnailImage = ({ video }: { video: VideoItem }) => {
    const [sasUrl, setSasUrl] = useState<string>('')
    const [imageLoading, setImageLoading] = useState(true)

    useEffect(() => {
      if (video.thumbnail_url) {
        getThumbnailSasUrl(video.thumbnail_url)
          .then(setSasUrl)
          .finally(() => setImageLoading(false))
      } else {
        setImageLoading(false)
      }
    }, [video.thumbnail_url])

    if (imageLoading) {
      return (
        <div className="w-24 h-16 bg-gray-200 rounded flex items-center justify-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
        </div>
      )
    }

    if (sasUrl) {
      return (
        <img
          src={sasUrl}
          alt="サムネイル"
          className="w-24 h-16 object-cover rounded"
          onError={() => setSasUrl('')}
        />
      )
    }

    return (
      <div className="w-24 h-16 bg-gray-200 rounded flex items-center justify-center text-gray-400">
        <div className="text-xs">📹</div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">動画一覧を読み込み中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchVideos}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            再試行
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">コーチ画面</h1>
              <p className="text-gray-600 mt-1">アップロードされた動画一覧</p>
            </div>
            <Link href="/" className="text-blue-600 hover:text-blue-700">
              ← トップに戻る
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {videos.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-gray-400 text-6xl mb-4">📹</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              まだ動画がアップロードされていません
            </h3>
            <p className="text-gray-600">
              プレイヤーが動画をアップロードするまでお待ちください。
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow">
            {/* Table Header */}
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                動画一覧 ({videos.length}件)
              </h2>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      サムネイル
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      アップロード日時
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ユーザーナンバー
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      状態
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      アクション
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {videos.map((video) => (
                    <tr key={video.video_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <ThumbnailImage video={video} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(video.upload_date).toLocaleString('ja-JP')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {extractUserNumber(video.video_url)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusTag(video.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => {
                            window.location.href = `/coach/advice?video_id=${video.video_id}`
                          }}
                          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
                        >
                          入力開始
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}