import request from './request'

export function getLatestAnnouncement() {
  return request.get('/maintenance/announcement/latest')
}

export function snoozeAnnouncementWeek(announcementId) {
  return request.post('/maintenance/announcement/snooze-week', {
    announcement_id: announcementId
  })
}

export function createFeedback(data) {
  return request.post('/maintenance/feedback/', data)
}

export function listMyFeedback(params) {
  return request.get('/maintenance/feedback/mine', { params })
}

export function listAllFeedback(params) {
  return request.get('/maintenance/feedback/all', { params })
}

export function replyFeedback(feedbackId, adminReply) {
  return request.post(`/maintenance/feedback/${feedbackId}/reply`, {
    admin_reply: adminReply
  })
}
