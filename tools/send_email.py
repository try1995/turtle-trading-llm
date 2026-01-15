import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

smtp_user, smtp_password, smtp_server = os.environ.get("smtp_user"), os.environ.get("smtp_password"), os.environ.get("smtp_server")

def send_message(toaddrs, subject, content, subtype="html"):
    msg = EmailMessage()
    msg.set_content('''
<!DOCTYPE html>
<html lang="en">
<body style="color: #666; font-size: 14px; font-family: 'Open Sans',Helve=
tica,Arial,sans-serif;">
<div class="box-content" style="width: 80%%; margin: 20px auto; max-widt=
h: 80%%; min-width: 600px;">
    <div class="info-top" style="padding: 15px 25px;
                                 border-top-left-radius: 10px;
                                 border-top-right-radius: 10px;
                                 background: #3e6499;
                                 color: #fff;
                                 overflow: hidden;
                                 line-height: 32px;">
        <div style="color:#ffffff"><strong>完成通知</stro=
ng></div>
    </div>
    <div class="info-wrap" style="border-bottom-left-radius: 10px;
                                  border-bottom-right-radius: 10px;
                                  border:1px solid #ddd;
                                  overflow: hidden;
                                  padding: 15px 15px 20px;">
        <div class="tips" style="padding:15px;">
            <p style=" list-style: 160%%; margin: 10px 0;"><strong><b>尊敬的汤总：</b><br><br>
        <b>您发财</b><br/> </strong></p >
        </div>
        %s
        <div class="tips" style="padding:15px;">
            <p style=" list-style: 160%%; margin: 10px 0;"><strong style="color:red">温馨提示：此邮件由系统发送，若有疑问请联系帅哥汤</strong></p >
        </div>
    </div>
</div>
</body>
</html>
'''%content, subtype=subtype,cte="quoted-printable")
    msg["subject"] = subject
    msg["From"] = formataddr(("盘后自动跑批", smtp_user))
    msg["To"] = toaddrs

    # with open(smtp_file_name, "rb") as f:
    #     data = f.read()
    # msg.add_attachment(data, maintype="excel", subtype="csv", filename="daily_report.csv")

    server = smtplib.SMTP_SSL(smtp_server, 465)
    server.login(user=smtp_user, password=smtp_password)
    server.set_debuglevel(1)
    # server.sendmail(toaddrs, toaddrs, msg)
    server.send_message(msg)
    server.quit()
