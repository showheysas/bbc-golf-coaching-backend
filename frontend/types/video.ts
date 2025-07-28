export interface Video {
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
    overall_feedback?: string
    overall_feedback_summary?: string
    next_training_menu?: string
    next_training_menu_summary?: string
    feedback_created_at?: string
  }
  sections: Array<{
    section_id: string
    start_sec: number
    end_sec: number
    image_url?: string
    tags?: string[]
    coach_comment?: string
    coach_comment_summary?: string
    created_at: string
  }>
}
