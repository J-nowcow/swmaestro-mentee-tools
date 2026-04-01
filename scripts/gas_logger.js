/**
 * SW마에스트로 Q&A 챗봇 로그 수집기 (Google Apps Script)
 *
 * 시트 구조:
 * - 시트1 (queries): timestamp | question | answer | answer_length
 * - feedback: timestamp | question | answer | feedback_type
 *
 * 설정 방법:
 * 1. Google Sheets에서 시트1 헤더: timestamp | question | answer | answer_length
 * 2. "feedback" 시트 추가 후 헤더: timestamp | question | answer | feedback_type
 * 3. 확장 프로그램 → Apps Script → 이 코드 붙여넣기
 * 4. 배포 → 새 배포 → 웹 앱 (모든 사용자)
 * 5. Streamlit Secrets에 LOG_WEBHOOK_URL = "배포 URL"
 */

function doPost(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var data = JSON.parse(e.postData.contents);

    if (data.type === "feedback") {
      var sheet = ss.getSheetByName("feedback") || ss.insertSheet("feedback");
      sheet.appendRow([
        data.timestamp || new Date().toISOString(),
        data.question || "",
        data.answer || "",
        data.feedback_type || "",
      ]);
    } else {
      var sheet = ss.getSheets()[0];
      sheet.appendRow([
        data.timestamp || new Date().toISOString(),
        data.question || "",
        data.answer || "",
        data.answer_length || 0,
      ]);
    }

    return ContentService.createTextOutput(
      JSON.stringify({ status: "ok" })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ status: "error", message: err.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}
