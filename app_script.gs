function sendDailyEmails() {

  var SPREADSHEET_ID = "g_sheet_id";
  var SHEET_NAME = "Sheet1"; // change only if your sheet tab name is different

  var sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
  var data = sheet.getDataRange().getValues();

  var today = new Date();
  today.setHours(0, 0, 0, 0);

  for (var i = 1; i < data.length; i++) {

    var rowDate = new Date(data[i][0]);
    rowDate.setHours(0, 0, 0, 0);

    var email = data[i][1];

    if (rowDate.getTime() === today.getTime() && email) {

      var htmlBody =

        // ✅ Yellow note at top
        "<p style='color:#DAA520; font-weight:bold;'>" +
        "Note: This is an automated mail. For more information, please connect." +
        "</p>" +

        "<p>Dear Sir,</p>" +

        "<p>I’m a Sr. Analyst with 10+ years in supply chain analytics and an MBA in Operations and Research Management from Amity University.<br>" +
        "I’m skilled in SQL, Python, Power BI, and AWS, and have built forecasting models, automated reporting pipelines, and optimized delivery costs.</p>" +

        "<p>Seeking Data Analyst / Sr. Data Analyst / Analytics Engineer / BI roles and available to join immediately.</p>" +

        "<p>I’d be glad to connect for any current or future opportunities.</p>" +

        "<p><b>CV Link:</b><br>" +
        "cv link</p>" +

        "<p><b>Cover Letter:</b><br>" +
        "cover letter</p>" +

        "<p><b>Project Profile GitHub:</b><br>" +
        "https://github.com/MohitRajput717<br>" +
        "https://github.com/MohitRajput717/Data-Analyst-Business-Analyst-Portfolio-Project<br>" +
        "https://github.com/MohitRajput717/Sparkguide/blob/main/Spark_playlist1.ipynb<br>" +
        "https://github.com/MohitRajput717/Mongodb<br>" +
        "https://github.com/MohitRajput717/Project_Mysql<br>" +
        "https://github.com/MohitRajput717/MS-SQL-SERVER</p>" +

        "<p><b>More Details:</b><br>" +
        "ECTC - Negotiable  <br>" +
        "Notice Period - 30 Days<br>" +
        "Location - Delhi NCR</p>" +
        "Expereience - 10 Years</p>" +

        "<p>Regards,<br><br>" +
        "Mohit Singh<br>" +
        "mobile no</p>";

      MailApp.sendEmail({
        to: email,
        subject: "Resume for Data Analyst | Business Analyst | Analytics Engineer | Operation Analyst",
        htmlBody: htmlBody
      });
    }
  }
}
