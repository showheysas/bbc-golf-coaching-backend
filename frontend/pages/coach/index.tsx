import { useState, useEffect } from 'react'
import Link from 'next/link'
import axios from 'axios'

interface Video {
  video_id: string
  user_id: string
  video_url: string
  thumbnail_url?: string
  upload_date: string
  club_type?: string
  swing_form?: string
  swing_note?: string
  section_group?: {
    section_group_id: string
    created_at: string
  }
  sections: Array<{
    section_id: string
    start_sec: number
    end_sec: number
    coach_comment?: string
  }>
}

export default function CoachDashboard() {
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sasUrls, setSasUrls] = useState<{[key: string]: {thumbnail?: string, video?: string}}>({}) // SAS URL管理

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/v1/videos')
      setVideos(response.data)
      
      // 各動画のSAS URLを取得
      await fetchAllSasUrls(response.data)
    } catch (err: any) {
      console.error('Error fetching videos:', err)
      setError('動画一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const getSasUrl = async (blobUrl: string): Promise<string> => {
    try {
      // Azure Blob URLからファイル名を抽出
      const urlParts = blobUrl.split('/')
      const filename = urlParts[urlParts.length - 1]
      
      const response = await fetch(`http://localhost:8000/media-url?filename=${filename}`)
      const data = await response.json()
      return data.url
    } catch (err) {
      console.error('SAS URL取得エラー:', err)
      throw err
    }
  }

  const fetchAllSasUrls = async (videoList: Video[]) => {
    const newSasUrls: {[key: string]: {thumbnail?: string, video?: string}} = {}
    
    for (const video of videoList) {
      const videoUrls: {thumbnail?: string, video?: string} = {}
      
      // サムネイルのSAS URL取得
      if (video.thumbnail_url) {
        try {
          videoUrls.thumbnail = await getSasUrl(video.thumbnail_url)
        } catch (err) {
          console.error(`サムネイルSAS URL取得失敗 (${video.video_id}):`, err)
        }
      }
      
      // 動画のSAS URL取得
      if (video.video_url) {
        try {
          videoUrls.video = await getSasUrl(video.video_url)
        } catch (err) {
          console.error(`動画SAS URL取得失敗 (${video.video_id}):`, err)
        }
      }
      
      newSasUrls[video.video_id] = videoUrls
    }
    
    setSasUrls(newSasUrls)
  }

  const clearAllData = async () => {
    const confirmMessage = 'すべての動画データとファイルを完全に削除します。この操作は取り消せません。本当に実行しますか？'
    
    if (!window.confirm(confirmMessage)) {
      return
    }
    
    const doubleConfirmMessage = '最終確認：すべてのデータが失われます。本当によろしいですか？'
    
    if (!window.confirm(doubleConfirmMessage)) {
      return
    }

    try {
      setLoading(true)
      await axios.post('/api/v1/clear-all-data')
      setVideos([])
      alert('すべてのデータとファイルがクリアされました')
    } catch (err: any) {
      console.error('Error clearing data:', err)
      alert('データクリアに失敗しました: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">動画一覧を読み込んでいます...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="card max-w-md mx-auto text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">エラーが発生しました</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button 
            onClick={fetchVideos}
            className="btn-primary"
          >
            再試行
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">コーチダッシュボード</h1>
              <p className="text-gray-600 mt-1">アップロードされた動画を分析してフィードバックを提供</p>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-blue-600 hover:text-blue-700">
                ← ユーザー画面へ
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        {videos.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-gray-400 text-6xl mb-4">📹</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              まだ動画がアップロードされていません
            </h3>
            <p className="text-gray-600">
              ユーザーが動画をアップロードするまでお待ちください。
            </p>
          </div>
        ) : (
          <div className="grid gap-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-semibold text-gray-800">
                動画一覧 ({videos.length}件)
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={fetchVideos}
                  className="btn-secondary"
                >
                  🔄 更新
                </button>
                <button
                  onClick={clearAllData}
                  className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors"
                  title="全てのデータとファイルを削除します"
                >
                  🗑️ 全データクリア
                </button>
              </div>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videos.map((video) => (
                <div key={video.video_id} className="card hover:shadow-lg transition-shadow">
                  {/* Thumbnail */}
                  <div className="aspect-video bg-gray-200 rounded-lg mb-4 overflow-hidden">
                    {sasUrls[video.video_id]?.thumbnail ? (
                      <img 
                        src={sasUrls[video.video_id].thumbnail} 
                        alt="Video thumbnail" 
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          console.error('サムネイル読み込みエラー:', video.video_id)
                        }}
                      />
                    ) : video.thumbnail_url ? (
                      <div className="w-full h-full flex items-center justify-center text-gray-500">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400 mx-auto mb-2"></div>
                          <p className="text-xs">読み込み中...</p>
                        </div>
                      </div>
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-500">
                        <div className="text-center">
                          <div className="text-4xl mb-2">📹</div>
                          <p className="text-sm">サムネイルなし</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Video Info */}
                  <div className="space-y-3">
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-1">
                        動画ID: {video.video_id.substring(0, 8)}...
                      </h3>
                      <p className="text-sm text-gray-600">
                        {new Date(video.upload_date).toLocaleString('ja-JP')}
                      </p>
                    </div>

                    {(video.club_type || video.swing_form) && (
                      <div className="flex flex-wrap gap-2">
                        {video.club_type && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                            {video.club_type}
                          </span>
                        )}
                        {video.swing_form && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            {video.swing_form}
                          </span>
                        )}
                      </div>
                    )}

                    {video.swing_note && (
                      <p className="text-sm text-gray-600 line-clamp-2">
                        📝 {video.swing_note}
                      </p>
                    )}

                    {/* Analysis Status */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {video.sections.length > 0 ? (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            ✓ 分析済み ({video.sections.length}セクション)
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                            ⏳ 未分析
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      <Link 
                        href={`/coach/videos/${video.video_id}`}
                        className="btn-primary flex-1 text-center text-sm py-2"
                      >
                        {video.sections.length > 0 ? '編集' : 'コーチング開始'}
                      </Link>
                      {sasUrls[video.video_id]?.video ? (
                        <a 
                          href={sasUrls[video.video_id].video}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-secondary px-3 py-2 text-sm"
                          title="動画を開く"
                        >
                          👁️
                        </a>
                      ) : (
                        <button
                          className="btn-secondary px-3 py-2 text-sm opacity-50 cursor-not-allowed"
                          title="動画URL準備中..."
                          disabled
                        >
                          ⏳
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}