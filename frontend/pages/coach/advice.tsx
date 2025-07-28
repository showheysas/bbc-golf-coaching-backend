import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'

interface VideoData {
  video_id: string
  video_url: string
  thumbnail_url?: string
  upload_date: string
  club_type?: string
  swing_form?: string
  swing_note?: string
  user_id: string
}

interface MediaUrlResponse {
  url: string
}

export default function CoachAdviceInput() {
  const router = useRouter()
  const { video_id } = router.query
  const videoRef = useRef<HTMLVideoElement>(null)
  
  const [videoData, setVideoData] = useState<VideoData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [videoSasUrl, setVideoSasUrl] = useState<string>('')
  const [thumbnailSasUrl, setThumbnailSasUrl] = useState<string>('')
  
  // Video player states
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  
  // Swing phase and advice input states
  const [selectedPhase, setSelectedPhase] = useState<string>('')
  const [showAdviceInput, setShowAdviceInput] = useState(false)
  const [adviceText, setAdviceText] = useState('')
  const [savedAdvices, setSavedAdvices] = useState<Array<{
    phase: string
    phaseCode: string
    text: string
    captureUrl?: string
    captureSasUrl?: string
    timestamp: number
  }>>([])
  const [isCapturing, setIsCapturing] = useState(false)
  
  // Form states (keeping existing for compatibility)
  const [advice, setAdvice] = useState('')
  const [practiceMethod, setPracticeMethod] = useState('')
  const [evaluation, setEvaluation] = useState('')
  
  // UI states for advice editing
  const [isAdviceEditing, setIsAdviceEditing] = useState(true)
  const [savedGeneralAdvice, setSavedGeneralAdvice] = useState({
    advice: '',
    practiceMethod: '',
    evaluation: ''
  })
  
  // Voice recording states
  const [isRecordingAdvice, setIsRecordingAdvice] = useState(false)
  const [isRecordingPractice, setIsRecordingPractice] = useState(false)
  const [isRecordingPhaseAdvice, setIsRecordingPhaseAdvice] = useState(false)
  const [adviceTranscription, setAdviceTranscription] = useState('')
  const [practiceTranscription, setPracticeTranscription] = useState('')
  const [phaseAdviceTranscription, setPhaseAdviceTranscription] = useState('')
  const [isEditingAdviceTranscription, setIsEditingAdviceTranscription] = useState(false)
  const [isEditingPracticeTranscription, setIsEditingPracticeTranscription] = useState(false)
  const [isEditingPhaseAdviceTranscription, setIsEditingPhaseAdviceTranscription] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [recordingType, setRecordingType] = useState<'advice' | 'practice' | 'phase_advice' | null>(null)

  useEffect(() => {
    if (video_id && typeof video_id === 'string') {
      fetchVideoData(video_id)
      loadSavedAdvices(video_id)
      loadSavedGeneralAdvice(video_id)
    }
  }, [video_id])

  // Load saved advices from localStorage
  const loadSavedAdvices = (videoId: string) => {
    try {
      const saved = localStorage.getItem(`advices_${videoId}`)
      if (saved) {
        const parsedAdvices = JSON.parse(saved)
        setSavedAdvices(parsedAdvices)
      }
    } catch (error) {
      console.error('Error loading saved advices:', error)
    }
  }

  // Load saved general advice from localStorage
  const loadSavedGeneralAdvice = (videoId: string) => {
    try {
      const saved = localStorage.getItem(`general_advice_${videoId}`)
      if (saved) {
        const parsedAdvice = JSON.parse(saved)
        setSavedGeneralAdvice(parsedAdvice)
        setAdvice(parsedAdvice.advice || '')
        setPracticeMethod(parsedAdvice.practiceMethod || '')
        setEvaluation(parsedAdvice.evaluation || '')
        setIsAdviceEditing(false) // Switch to display mode if there's saved content
      }
    } catch (error) {
      console.error('Error loading saved general advice:', error)
    }
  }

  // Save general advice to localStorage
  const saveGeneralAdviceToStorage = (videoId: string, adviceData: typeof savedGeneralAdvice) => {
    try {
      localStorage.setItem(`general_advice_${videoId}`, JSON.stringify(adviceData))
    } catch (error) {
      console.error('Error saving general advice to storage:', error)
    }
  }

  // Save advices to localStorage
  const saveAdvicesToStorage = (videoId: string, advices: typeof savedAdvices) => {
    try {
      localStorage.setItem(`advices_${videoId}`, JSON.stringify(advices))
    } catch (error) {
      console.error('Error saving advices to storage:', error)
    }
  }

  const fetchVideoData = async (videoId: string) => {
    try {
      setLoading(true)
      const response = await fetch(`/api/v1/upload-status/${videoId}`)
      if (response.ok) {
        const data = await response.json()
        setVideoData(data)
        
        // SAS付きURLを取得
        await fetchMediaUrls(data.video_url, data.thumbnail_url)
      } else if (response.status === 404) {
        setError('動画が見つかりません')
      } else {
        setError('動画データの取得に失敗しました')
      }
    } catch (err) {
      console.error('Error fetching video data:', err)
      setError('動画データの取得に失敗しました')
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

  // Video player event handlers
  const handleVideoLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
    }
  }

  const handleVideoTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
    }
  }

  const handleVideoPlay = () => {
    setIsPlaying(true)
  }

  const handleVideoPause = () => {
    setIsPlaying(false)
  }

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value)
    setCurrentTime(newTime)
    if (videoRef.current) {
      videoRef.current.currentTime = newTime
    }
  }

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
    }
  }

  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const extractUserNumber = (url: string): string => {
    const filename = url.split('/').pop() || ''
    const match = filename.match(/_U(\d+)/)
    return match ? `U${match[1]}` : 'U-----'
  }

  // Component for displaying capture images with SAS URL refresh
  const CaptureImage = ({ advice }: { advice: { phase: string, captureUrl?: string, captureSasUrl?: string } }) => {
    const [currentSasUrl, setCurrentSasUrl] = useState(advice.captureSasUrl || '')
    const [imageLoading, setImageLoading] = useState(false)
    const [imageError, setImageError] = useState(false)

    useEffect(() => {
      // If we have a capture URL but no SAS URL or the SAS URL fails, get a fresh one
      if (advice.captureUrl && (!currentSasUrl || imageError)) {
        refreshSasUrl()
      }
    }, [advice.captureUrl, imageError])

    const refreshSasUrl = async () => {
      if (!advice.captureUrl) return
      
      try {
        setImageLoading(true)
        setImageError(false)
        const sasUrl = await getSasUrlForImage(advice.captureUrl)
        if (sasUrl) {
          setCurrentSasUrl(sasUrl)
        }
      } catch (error) {
        console.error('Error refreshing SAS URL:', error)
        setImageError(true)
      } finally {
        setImageLoading(false)
      }
    }

    const handleImageError = () => {
      setImageError(true)
    }

    if (imageLoading) {
      return (
        <div className="flex-shrink-0">
          <div className="w-24 h-16 bg-gray-200 rounded border flex items-center justify-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
          </div>
        </div>
      )
    }

    return (
      <div className="flex-shrink-0">
        {currentSasUrl && !imageError ? (
          <img
            src={currentSasUrl}
            alt={`${advice.phase}キャプチャ`}
            className="w-24 h-16 object-cover rounded border"
            onError={handleImageError}
          />
        ) : advice.captureUrl ? (
          <img
            src={`/api/v1/proxy-file/${encodeURIComponent(advice.captureUrl)}`}
            alt={`${advice.phase}キャプチャ`}
            className="w-24 h-16 object-cover rounded border"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-24 h-16 bg-gray-300 rounded border flex items-center justify-center">
            <span className="text-xs text-gray-500">画像なし</span>
          </div>
        )}
      </div>
    )
  }

  const getClubTypeLabel = (clubType?: string): string => {
    const labels: {[key: string]: string} = {
      'driver': 'ドライバー',
      'fairway_wood': 'フェアウェイウッド',
      'hybrid': 'ハイブリッド',
      'iron': 'アイアン',
      'wedge': 'ウェッジ',
      'putter': 'パター'
    }
    return clubType ? labels[clubType] || clubType : '未指定'
  }

  const getSwingFormLabel = (swingForm?: string): string => {
    const labels: {[key: string]: string} = {
      'full_swing': 'フルスイング',
      'half_swing': 'ハーフスイング',
      'chip': 'チップ',
      'pitch': 'ピッチ',
      'bunker': 'バンカー',
      'putting': 'パッティング'
    }
    return swingForm ? labels[swingForm] || swingForm : '未指定'
  }

  // Swing phases with identification codes
  const swingPhases = [
    { name: 'アドレス', code: 'AD' },
    { name: 'テイクバック', code: 'TB' }, 
    { name: 'バックスイング', code: 'BS' },
    { name: 'トップ', code: 'TP' },
    { name: 'トランジション', code: 'TR' },
    { name: 'ダウンスイング', code: 'DS' },
    { name: 'インパクト', code: 'IM' },
    { name: 'フォロー', code: 'FO' },
    { name: 'フィニッシュ１', code: 'F1' },
    { name: 'フィニッシュ２', code: 'F2' },
    { name: 'その他', code: 'OT' }
  ]

  const getPhaseCode = (phaseName: string): string => {
    const phase = swingPhases.find(p => p.name === phaseName)
    return phase ? phase.code : 'OT'
  }

  const handlePhaseSelect = (phase: string) => {
    setSelectedPhase(phase)
    setShowAdviceInput(false) // Reset advice input when phase changes
    setAdviceText('')
  }

  const handleAdviceInputStart = () => {
    setShowAdviceInput(true)
  }

  // Voice recording functions
  const startRecording = async (type: 'advice' | 'practice' | 'phase_advice') => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      const chunks: BlobPart[] = []

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' })
        await transcribeAudio(audioBlob, type)
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop())
      }

      setMediaRecorder(recorder)
      setRecordingType(type)
      
      if (type === 'advice') {
        setIsRecordingAdvice(true)
      } else if (type === 'practice') {
        setIsRecordingPractice(true)
      } else if (type === 'phase_advice') {
        setIsRecordingPhaseAdvice(true)
      }
      
      recorder.start()
    } catch (error) {
      console.error('Error starting recording:', error)
      alert('マイクへのアクセスに失敗しました。ブラウザの設定を確認してください。')
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop()
      setMediaRecorder(null)
      setIsRecordingAdvice(false)
      setIsRecordingPractice(false)
      setIsRecordingPhaseAdvice(false)
      setRecordingType(null)
    }
  }

  const transcribeAudio = async (audioBlob: Blob, type: 'advice' | 'practice' | 'phase_advice') => {
    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.wav')
      formData.append('type', type)

      const response = await fetch('/api/v1/transcribe-audio', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        if (type === 'advice') {
          setAdviceTranscription(data.transcription)
        } else if (type === 'practice') {
          setPracticeTranscription(data.transcription)
        } else if (type === 'phase_advice') {
          setPhaseAdviceTranscription(data.transcription)
        }
      } else {
        console.error('Transcription failed:', await response.text())
        alert('音声の文字起こしに失敗しました。')
      }
    } catch (error) {
      console.error('Error transcribing audio:', error)
      alert('音声の文字起こし中にエラーが発生しました。')
    }
  }

  const handleVoiceInput = () => {
    // Start recording for phase advice
    startRecording('phase_advice')
  }

  const getSasUrlForImage = async (imageUrl: string): Promise<string | null> => {
    try {
      const response = await fetch(`/api/v1/media-url?blob_url=${encodeURIComponent(imageUrl)}`)
      if (response.ok) {
        const data: MediaUrlResponse = await response.json()
        return data.url
      }
    } catch (error) {
      console.error('Error fetching image SAS URL:', error)
    }
    return null
  }

  const captureVideoFrame = async (): Promise<{url: string, sasUrl: string} | null> => {
    if (!videoData || !videoSasUrl) return null

    try {
      setIsCapturing(true)
      
      // Extract base filename from video URL
      const videoUrl = videoData.video_url
      const videoFilename = videoUrl.split('/').pop() || ''
      const baseName = videoFilename.replace(/\.[^/.]+$/, '') // Remove extension
      const phaseCode = getPhaseCode(selectedPhase)
      const captureFilename = `${baseName}_${phaseCode}.jpg`

      // Capture frame using backend API
      const response = await fetch('/api/v1/capture-video-frame', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          video_url: videoSasUrl,
          time_seconds: currentTime.toString(),
          filename: captureFilename
        })
      })

      if (response.ok) {
        const data = await response.json()
        const sasUrl = await getSasUrlForImage(data.image_url)
        return {
          url: data.image_url,
          sasUrl: sasUrl || data.image_url
        }
      } else {
        console.error('Frame capture failed:', await response.text())
        return null
      }
    } catch (error) {
      console.error('Error capturing frame:', error)
      return null
    } finally {
      setIsCapturing(false)
    }
  }

  // Remove old handleSaveAdvice function - now handled inline

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">動画データを読み込み中...</p>
        </div>
      </div>
    )
  }

  if (error || !videoData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <p className="text-red-600 mb-4">{error || '動画データが見つかりません'}</p>
          <Link href="/coach" className="text-blue-500 hover:text-blue-700">
            ← コーチ画面に戻る
          </Link>
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
              <h1 className="text-3xl font-bold text-gray-900">アドバイス入力</h1>
              <p className="text-gray-600 mt-1">
                ユーザー: {extractUserNumber(videoData.video_url)} | 
                アップロード: {new Date(videoData.upload_date).toLocaleString('ja-JP')}
              </p>
            </div>
            <Link href="/coach" className="text-blue-600 hover:text-blue-700">
              ← コーチ画面に戻る
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Video Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">動画分析</h2>
            
            {/* Video Player */}
            <div className="aspect-video bg-gray-200 rounded-lg mb-4 overflow-hidden">
              {videoSasUrl ? (
                <video
                  ref={videoRef}
                  className="w-full h-full"
                  src={videoSasUrl}
                  onLoadedMetadata={handleVideoLoadedMetadata}
                  onTimeUpdate={handleVideoTimeUpdate}
                  onPlay={handleVideoPlay}
                  onPause={handleVideoPause}
                  controls
                >
                  お使いのブラウザは動画の再生に対応していません。
                </video>
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <div className="text-center">
                    <div className="text-4xl mb-2">📹</div>
                    <p>動画を読み込み中...</p>
                  </div>
                </div>
              )}
            </div>

            {/* Video Timeline Slider */}
            {duration > 0 && (
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">再生位置</span>
                  <span className="text-sm text-gray-600">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <button
                    onClick={togglePlayPause}
                    className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                  >
                    {isPlaying ? '⏸️' : '▶️'}
                  </button>
                  <input
                    type="range"
                    min="0"
                    max={duration}
                    step="0.1"
                    value={currentTime}
                    onChange={handleSliderChange}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  スライダーで動画の任意の位置にジャンプできます
                </div>
              </div>
            )}

            {/* Swing Phase Selection */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-800 mb-3">スイング段階選択</h3>
              <div className="grid grid-cols-2 gap-2 mb-4">
                {swingPhases.map((phase) => (
                  <button
                    key={phase.name}
                    onClick={() => handlePhaseSelect(phase.name)}
                    className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                      selectedPhase === phase.name
                        ? 'bg-blue-500 text-white border-blue-500'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {phase.name}
                  </button>
                ))}
              </div>

              {/* Advice Input Button */}
              <button
                onClick={handleAdviceInputStart}
                disabled={!selectedPhase}
                className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                  selectedPhase
                    ? 'bg-green-500 text-white hover:bg-green-600'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                アドバイス入力
              </button>

              {/* Advice Input Section */}
              {showAdviceInput && selectedPhase && (
                <div className="mt-4 p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <div className="mb-3">
                    <span className="text-sm font-medium text-gray-700">
                      選択中: <span className="text-blue-600">{selectedPhase}</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-4 mb-3">
                    {!isRecordingPhaseAdvice ? (
                      <button
                        onClick={() => startRecording('phase_advice')}
                        className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors text-sm"
                      >
                        🎤 音声入力
                      </button>
                    ) : (
                      <button
                        onClick={stopRecording}
                        className="bg-red-700 text-white px-4 py-2 rounded-lg hover:bg-red-800 transition-colors text-sm animate-pulse"
                      >
                        ⏹️ 録音終了
                      </button>
                    )}
                    <span className="text-sm text-gray-600">テキスト入力</span>
                  </div>

                  <textarea
                    value={adviceText}
                    onChange={(e) => setAdviceText(e.target.value)}
                    placeholder={`${selectedPhase}についてのアドバイスを入力してください...`}
                    className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm text-gray-800"
                  />
                  
                  {/* Transcription Result for Phase Advice */}
                  {phaseAdviceTranscription && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-gray-700">
                          文字起こし結果
                        </label>
                        <button
                          onClick={() => setIsEditingPhaseAdviceTranscription(!isEditingPhaseAdviceTranscription)}
                          className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 transition-colors"
                        >
                          {isEditingPhaseAdviceTranscription ? '修正完了' : '文字起こしテキスト修正'}
                        </button>
                      </div>
                      {isEditingPhaseAdviceTranscription ? (
                        <textarea
                          value={phaseAdviceTranscription}
                          onChange={(e) => setPhaseAdviceTranscription(e.target.value)}
                          className="w-full h-20 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800 text-sm"
                        />
                      ) : (
                        <div className="w-full min-h-[5rem] px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-800 whitespace-pre-wrap text-sm">
                          {phaseAdviceTranscription}
                        </div>
                      )}
                      <button
                        onClick={() => {
                          setAdviceText(phaseAdviceTranscription)
                          setPhaseAdviceTranscription('')
                        }}
                        className="mt-2 bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 transition-colors"
                      >
                        テキスト入力欄に反映
                      </button>
                    </div>
                  )}

                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={async () => {
                        if (!adviceText.trim()) return

                        // Capture video frame
                        const captureResult = await captureVideoFrame()
                        
                        // Save advice with capture
                        const newAdvice = {
                          phase: selectedPhase,
                          phaseCode: getPhaseCode(selectedPhase),
                          text: adviceText,
                          captureUrl: captureResult?.url,
                          captureSasUrl: captureResult?.sasUrl,
                          timestamp: currentTime
                        }

                        const updatedAdvices = [...savedAdvices, newAdvice]
                        setSavedAdvices(updatedAdvices)
                        
                        // Save to localStorage
                        if (video_id && typeof video_id === 'string') {
                          saveAdvicesToStorage(video_id, updatedAdvices)
                        }
                        
                        console.log('Saving phase advice:', newAdvice)
                        
                        alert(`${selectedPhase}のアドバイスを保存しました`)
                        setShowAdviceInput(false)
                        setAdviceText('')
                      }}
                      disabled={!adviceText.trim() || isCapturing}
                      className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                        adviceText.trim() && !isCapturing
                          ? 'bg-blue-500 text-white hover:bg-blue-600'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      {isCapturing ? 'キャプチャ中...' : '保存'}
                    </button>
                    <button
                      onClick={() => {
                        setShowAdviceInput(false)
                        setAdviceText('')
                      }}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded text-sm hover:bg-gray-50 transition-colors"
                    >
                      キャンセル
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Swing Phase Advices Section */}
            {savedAdvices.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-800 mb-4">スイング段階別アドバイス</h3>
                <div className="space-y-4">
                  {savedAdvices.map((advice, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="flex items-start gap-4">
                        {/* Capture Image */}
                        <CaptureImage advice={advice} />

                        {/* Advice Content */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="bg-blue-500 text-white px-2 py-1 rounded text-xs font-medium">
                              {advice.phase}
                            </span>
                            <span className="text-xs text-gray-500">
                              {Math.floor(advice.timestamp / 60)}:{Math.floor(advice.timestamp % 60).toString().padStart(2, '0')}
                            </span>
                          </div>
                          <p className="text-sm text-gray-800">{advice.text}</p>
                        </div>

                        {/* Delete Button */}
                        <button
                          onClick={() => {
                            const updatedAdvices = savedAdvices.filter((_, i) => i !== index)
                            setSavedAdvices(updatedAdvices)
                            
                            // Update localStorage
                            if (video_id && typeof video_id === 'string') {
                              saveAdvicesToStorage(video_id, updatedAdvices)
                            }
                          }}
                          className="text-red-500 hover:text-red-700 text-sm"
                        >
                          削除
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Video Info */}
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">動画ID</p>
                <p className="font-mono text-sm bg-gray-100 px-3 py-2 rounded text-gray-800">
                  {videoData.video_id}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">使用クラブ</p>
                  <p className="text-gray-800">{getClubTypeLabel(videoData.club_type)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">スイング種類</p>
                  <p className="text-gray-800">{getSwingFormLabel(videoData.swing_form)}</p>
                </div>
              </div>
              {videoData.swing_note && (
                <div>
                  <p className="text-sm text-gray-600">プレイヤーのメモ</p>
                  <p className="text-gray-800 bg-gray-100 px-3 py-2 rounded">
                    {videoData.swing_note}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Advice Input Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">コーチングアドバイス</h2>
            
            {/* Thumbnail */}
            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-2">サムネイル</p>
              <div className="w-48 h-32 bg-gray-200 rounded-lg overflow-hidden">
                {thumbnailSasUrl ? (
                  <img
                    src={thumbnailSasUrl}
                    alt="動画サムネイル"
                    className="w-full h-full object-cover"
                  />
                ) : videoData.thumbnail_url ? (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <div className="text-center">
                      <div className="text-2xl mb-1">🖼️</div>
                      <p className="text-xs">読み込み中...</p>
                    </div>
                  </div>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <div className="text-center">
                      <div className="text-2xl mb-1">📹</div>
                      <p className="text-xs">サムネイルなし</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Advice Form or Display */}
            <div className="space-y-4">
              {isAdviceEditing ? (
                // Editing Mode - Input Form
                <>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-gray-700">
                        総評
                      </label>
                      <div className="flex items-center gap-2">
                        {!isRecordingAdvice ? (
                          <button
                            onClick={() => startRecording('advice')}
                            className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 transition-colors"
                          >
                            🎤 音声入力
                          </button>
                        ) : (
                          <button
                            onClick={stopRecording}
                            className="bg-red-700 text-white px-3 py-1 rounded text-sm hover:bg-red-800 transition-colors animate-pulse"
                          >
                            ⏹️ 録音終了
                          </button>
                        )}
                        <span className="text-sm text-gray-600">テキスト入力</span>
                      </div>
                    </div>
                    <textarea
                      value={advice}
                      onChange={(e) => setAdvice(e.target.value)}
                      className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800"
                      placeholder="プレイヤーへの総評を入力してください..."
                    />
                    
                    {/* Transcription Result for Advice */}
                    {adviceTranscription && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-gray-700">
                            文字起こし結果
                          </label>
                          <button
                            onClick={() => setIsEditingAdviceTranscription(!isEditingAdviceTranscription)}
                            className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 transition-colors"
                          >
                            {isEditingAdviceTranscription ? '修正完了' : '文字起こしテキスト修正'}
                          </button>
                        </div>
                        {isEditingAdviceTranscription ? (
                          <textarea
                            value={adviceTranscription}
                            onChange={(e) => setAdviceTranscription(e.target.value)}
                            className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800"
                          />
                        ) : (
                          <div className="w-full min-h-[6rem] px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-800 whitespace-pre-wrap">
                            {adviceTranscription}
                          </div>
                        )}
                        <button
                          onClick={() => {
                            setAdvice(adviceTranscription)
                            setAdviceTranscription('')
                          }}
                          className="mt-2 bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 transition-colors"
                        >
                          テキスト入力欄に反映
                        </button>
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-gray-700">
                        おすすめ練習方法
                      </label>
                      <div className="flex items-center gap-2">
                        {!isRecordingPractice ? (
                          <button
                            onClick={() => startRecording('practice')}
                            className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 transition-colors"
                          >
                            🎤 音声入力
                          </button>
                        ) : (
                          <button
                            onClick={stopRecording}
                            className="bg-red-700 text-white px-3 py-1 rounded text-sm hover:bg-red-800 transition-colors animate-pulse"
                          >
                            ⏹️ 録音終了
                          </button>
                        )}
                        <span className="text-sm text-gray-600">テキスト入力</span>
                      </div>
                    </div>
                    <textarea
                      value={practiceMethod}
                      onChange={(e) => setPracticeMethod(e.target.value)}
                      className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800"
                      placeholder="具体的な練習方法やドリルがあれば記入してください..."
                    />
                    
                    {/* Transcription Result for Practice Method */}
                    {practiceTranscription && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-gray-700">
                            文字起こし結果
                          </label>
                          <button
                            onClick={() => setIsEditingPracticeTranscription(!isEditingPracticeTranscription)}
                            className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 transition-colors"
                          >
                            {isEditingPracticeTranscription ? '修正完了' : '文字起こしテキスト修正'}
                          </button>
                        </div>
                        {isEditingPracticeTranscription ? (
                          <textarea
                            value={practiceTranscription}
                            onChange={(e) => setPracticeTranscription(e.target.value)}
                            className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800"
                          />
                        ) : (
                          <div className="w-full min-h-[6rem] px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-800 whitespace-pre-wrap">
                            {practiceTranscription}
                          </div>
                        )}
                        <button
                          onClick={() => {
                            setPracticeMethod(practiceTranscription)
                            setPracticeTranscription('')
                          }}
                          className="mt-2 bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 transition-colors"
                        >
                          テキスト入力欄に反映
                        </button>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      総合評価
                    </label>
                    <select 
                      value={evaluation}
                      onChange={(e) => setEvaluation(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-800"
                    >
                      <option value="">選択してください</option>
                      <option value="excellent">優秀</option>
                      <option value="good">良好</option>
                      <option value="average">普通</option>
                      <option value="needs_improvement">要改善</option>
                    </select>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => {
                        const adviceData = {
                          advice,
                          practiceMethod,
                          evaluation
                        }
                        setSavedGeneralAdvice(adviceData)
                        
                        // Save to localStorage
                        if (video_id && typeof video_id === 'string') {
                          saveGeneralAdviceToStorage(video_id, adviceData)
                        }
                        
                        setIsAdviceEditing(false)
                      }}
                      disabled={!advice.trim()}
                      className={`flex-1 py-3 px-6 rounded-lg font-medium transition-colors ${
                        advice.trim()
                          ? 'bg-blue-500 text-white hover:bg-blue-600'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      アドバイスを保存
                    </button>
                    <button
                      onClick={() => router.push('/coach')}
                      className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      キャンセル
                    </button>
                  </div>
                </>
              ) : (
                // Display Mode - Show Saved Content
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      総評
                    </label>
                    <div className="w-full min-h-[8rem] px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-800 whitespace-pre-wrap">
                      {savedGeneralAdvice.advice || '未入力'}
                    </div>
                  </div>

                  {savedGeneralAdvice.practiceMethod && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        おすすめ練習方法
                      </label>
                      <div className="w-full min-h-[6rem] px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-800 whitespace-pre-wrap">
                        {savedGeneralAdvice.practiceMethod}
                      </div>
                    </div>
                  )}

                  {savedGeneralAdvice.evaluation && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        総合評価
                      </label>
                      <div className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-800">
                        {{
                          excellent: '優秀',
                          good: '良好',
                          average: '普通',
                          needs_improvement: '要改善'
                        }[savedGeneralAdvice.evaluation] || savedGeneralAdvice.evaluation}
                      </div>
                    </div>
                  )}

                  {/* Edit Button */}
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => setIsAdviceEditing(true)}
                      className="flex-1 bg-green-500 text-white py-3 px-6 rounded-lg hover:bg-green-600 transition-colors font-medium"
                    >
                      アドバイスを変更
                    </button>
                    <button
                      onClick={() => router.push('/coach')}
                      className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      コーチ画面に戻る
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }
        
        .slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }
      `}</style>
    </div>
  )
}